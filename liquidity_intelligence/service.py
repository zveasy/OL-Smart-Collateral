from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .asset_registry import AssetRecord, AssetRegistry
from .auction_book import AuctionBookService
from .continuous_valuation import ComparableAsset, ContinuousValuation, ValuationReport
from .dynamic_collateral import CollateralReport, DynamicCollateral
from .event_store import EventStore
from .fractionalization import FractionalizationService
from .liquidity_explainer import LiquidityExplainer, LiquidityExplanation
from .liquidity_optimizer import (
    LiquidityOptimizer,
    OptimizationPolicy,
    OptimizationResult,
)
from .liquidity_options import generate_liquidity_options
from .models import deterministic_id
from .revenue_streams import RevenueStreamService
from .trust import TrustEvidence, TrustPolicy


class AnalyzeRequest(BaseModel):
    asset_id: str
    policy: OptimizationPolicy = Field(default_factory=OptimizationPolicy)
    comparables: list[ComparableAsset] = Field(default_factory=list)


class RecommendationRecord(BaseModel):
    recommendation_id: str
    tenant_id: str
    asset_id: str
    valuation: ValuationReport
    trust_evidence: TrustEvidence
    optimization: OptimizationResult
    explanation: LiquidityExplanation


class LiquidityIntelligenceService:
    def __init__(
        self,
        store: EventStore | None = None,
        trust_policy: TrustPolicy | None = None,
        store_path: str | Path | None = None,
    ) -> None:
        self.store = store or EventStore(store_path)
        self.trust_policy = trust_policy or TrustPolicy()
        self.assets = AssetRegistry(self.store)
        self.fractions = FractionalizationService(self.store)
        self.auctions = AuctionBookService(self.store)
        self.revenue_streams = RevenueStreamService(self.store)

    def analyze(self, tenant_id: str, request: AnalyzeRequest) -> RecommendationRecord:
        asset = self.require_asset(tenant_id, request.asset_id)
        trust = self.trust_policy.evidence_for(
            tenant_id, request.asset_id, asset.evidence_references
        )
        valuation = ContinuousValuation.evaluate(
            asset, request.comparables, Decimal(str(trust.confidence))
        )
        options = generate_liquidity_options(asset, valuation)
        optimization = LiquidityOptimizer.optimize(options, request.policy)
        explanation = LiquidityExplainer.explain(optimization)
        recommendation_id = deterministic_id(
            "recommendation",
            {
                "tenant_id": tenant_id,
                "asset_id": request.asset_id,
                "valuation": valuation,
                "optimization": optimization,
            },
        )
        existing = self.get_recommendation(tenant_id, recommendation_id)
        if existing:
            return existing
        record = RecommendationRecord(
            recommendation_id=recommendation_id,
            tenant_id=tenant_id,
            asset_id=request.asset_id,
            valuation=valuation,
            trust_evidence=trust,
            optimization=optimization,
            explanation=explanation,
        )
        self.store.append(
            tenant_id, "valuation.calculated", request.asset_id, valuation
        )
        self.store.append(
            tenant_id, "recommendation.created", recommendation_id, record
        )
        return record

    def get_recommendation(
        self, tenant_id: str, recommendation_id: str
    ) -> RecommendationRecord | None:
        return next(
            (
                RecommendationRecord.model_validate(event["payload"])
                for event in self.store.read(tenant_id)
                if event["event_type"] == "recommendation.created"
                and event["aggregate_id"] == recommendation_id
            ),
            None,
        )

    def collateral_report(self, tenant_id: str, asset_id: str) -> CollateralReport:
        asset = self.require_asset(tenant_id, asset_id)
        trust = self.trust_policy.evidence_for(
            tenant_id, asset_id, asset.evidence_references
        )
        valuation = ContinuousValuation.evaluate(
            asset, trust_confidence=Decimal(str(trust.confidence))
        )
        report = DynamicCollateral.evaluate(asset, valuation, trust)
        report_id = deterministic_id(
            "collateral", {"tenant_id": tenant_id, "report": report}
        )
        prior = any(
            event["event_type"] == "collateral.calculated"
            and event["aggregate_id"] == report_id
            for event in self.store.read(tenant_id)
        )
        if not prior:
            self.store.append(tenant_id, "collateral.calculated", report_id, report)
        return report

    def require_asset(self, tenant_id: str, asset_id: str) -> AssetRecord:
        asset = self.assets.get(tenant_id, asset_id)
        if asset is None:
            raise LookupError("Asset not found")
        return asset

    def audit_bundle(self, tenant_id: str) -> dict[str, Any]:
        return self.store.export_bundle(tenant_id)

    def replay_state(self, tenant_id: str) -> dict[str, Any]:
        events = self.store.read(tenant_id)
        return {
            "assets": [
                asset.model_dump(mode="json") for asset in self.assets.list(tenant_id)
            ],
            "recommendations": [
                event["payload"]
                for event in events
                if event["event_type"] == "recommendation.created"
            ],
            "fractions": [
                event["payload"]
                for event in events
                if event["event_type"] == "fraction.created"
            ],
            "revenue_streams": [
                event["payload"]
                for event in events
                if event["event_type"] == "revenue_stream.created"
            ],
            "orders": [
                event["payload"]
                for event in events
                if event["event_type"] == "auction.order_placed"
            ],
        }
