from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from .asset_registry import AssetRecord
from .continuous_valuation import ValuationReport
from .models import clamp, money, score
from .trust import TrustEvidence


class CollateralReport(BaseModel):
    asset_id: str
    loan_to_value_ratio: Decimal
    collateral_health_score: Decimal
    borrowing_capacity: Decimal
    components: dict[str, Decimal]
    rationale: list[str]


class DynamicCollateral:
    @staticmethod
    def evaluate(
        asset: AssetRecord,
        valuation: ValuationReport,
        trust: TrustEvidence,
    ) -> CollateralReport:
        value = valuation.risk_adjusted_value
        liabilities = sum(
            (item.outstanding_principal for item in asset.existing_debt), Decimal("0")
        )
        ltv = liabilities / value if value else Decimal("1")
        insurance = (
            Decimal("1")
            if (
                asset.insurance.active
                and asset.insurance.coverage_amount >= value * Decimal("0.5")
            )
            else Decimal("0.35")
            if asset.insurance.active
            else Decimal("0")
        )
        maintenance = Decimal("1")
        if any(
            item.status.lower() in {"overdue", "poor", "critical"}
            for item in asset.maintenance_history
        ):
            maintenance = Decimal("0.4")
        utilization = asset.cash_flow.utilization
        revenue = asset.cash_flow.stability
        leverage = Decimal("1") - clamp(ltv)
        trust_score = Decimal(str(trust.confidence))
        cash_flow_cover = clamp(
            (asset.cash_flow.annual_income - asset.cash_flow.annual_expenses)
            / (value * Decimal("0.08"))
            if value
            else 0
        )
        components = {
            "value_confidence": valuation.confidence_score,
            "cash_flow": score(cash_flow_cover),
            "insurance": score(insurance),
            "maintenance": score(maintenance),
            "leverage": score(leverage),
            "revenue_stability": score(revenue),
            "utilization": score(utilization),
            "trust": score(trust_score),
        }
        health = (
            components["value_confidence"] * Decimal("0.15")
            + components["cash_flow"] * Decimal("0.15")
            + components["insurance"] * Decimal("0.10")
            + components["maintenance"] * Decimal("0.10")
            + components["leverage"] * Decimal("0.20")
            + components["revenue_stability"] * Decimal("0.10")
            + components["utilization"] * Decimal("0.05")
            + components["trust"] * Decimal("0.15")
        )
        advance_rate = clamp(
            Decimal("0.25") + health * Decimal("0.50"), Decimal("0.25"), Decimal("0.75")
        )
        capacity = max(Decimal("0"), value * advance_rate - liabilities)
        return CollateralReport(
            asset_id=asset.asset_id or "",
            loan_to_value_ratio=score(ltv),
            collateral_health_score=score(health * 100),
            borrowing_capacity=money(capacity),
            components=components,
            rationale=[
                "Borrowing capacity applies a health-adjusted advance rate to risk-adjusted value.",
                "Existing liabilities reduce immediately available capacity.",
                "Insurance, maintenance, utilization, revenue stability, and trust affect health.",
            ],
        )
