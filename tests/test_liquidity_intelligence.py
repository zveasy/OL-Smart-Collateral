from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from api_layer.rest_api import auth, liquidity_routes
from api_layer.rest_api.server import app
from liquidity_intelligence.asset_registry import (
    AssetClass,
    AssetRecord,
    CashFlowCharacteristics,
    DebtObligation,
    InsuranceInformation,
    MaintenanceRecord,
    RevenuePoint,
    ValuationPoint,
)
from liquidity_intelligence.auction_book import OrderRequest, OrderSide
from liquidity_intelligence.fractionalization import FractionRequest, FractionType
from liquidity_intelligence.liquidity_optimizer import OptimizationPolicy
from liquidity_intelligence.revenue_streams import FutureCashFlow, RevenueStreamRequest
from liquidity_intelligence.service import AnalyzeRequest, LiquidityIntelligenceService
from liquidity_intelligence.trust import TrustPolicy


@pytest.fixture
def service(tmp_path):
    return LiquidityIntelligenceService(store_path=tmp_path / "events.jsonl")


def sample_asset(value: str = "1000000") -> AssetRecord:
    return AssetRecord(
        asset_class=AssetClass.REAL_ESTATE,
        ownership_percentage=100,
        current_valuation=value,
        historical_valuations=[
            ValuationPoint(period="2025-Q4", value="900000", confidence="0.8")
        ],
        cash_flow=CashFlowCharacteristics(
            annual_income="120000",
            annual_expenses="30000",
            stability="0.9",
            utilization="0.95",
        ),
        insurance=InsuranceInformation(active=True, coverage_amount=value),
        maintenance_history=[
            MaintenanceRecord(period="2026-Q1", status="current", cost="5000")
        ],
        existing_debt=[
            DebtObligation(
                creditor="Example Bank",
                outstanding_principal="150000",
                annual_rate="0.06",
            )
        ],
        revenue_history=[
            RevenuePoint(period="2025", amount="115000"),
            RevenuePoint(period="2026", amount="120000"),
        ],
        evidence_references=["evidence://valuation/1", "evidence://title/1"],
    )


def registered(service, tenant="tenant-a"):
    return service.assets.register(tenant, sample_asset())


def test_tenant_isolation(service):
    asset = registered(service, "tenant-a")
    assert service.assets.get("tenant-a", asset.asset_id) is not None
    assert service.assets.get("tenant-b", asset.asset_id) is None
    assert service.assets.list("tenant-b") == []


def test_deterministic_replay_and_recommendation(service):
    asset = registered(service)
    request = AnalyzeRequest(asset_id=asset.asset_id)
    first = service.analyze("tenant-a", request)
    second = service.analyze("tenant-a", request)
    assert first == second
    assert first.recommendation_id == second.recommendation_id
    assert service.replay_state("tenant-a")["recommendations"] == [
        first.model_dump(mode="json")
    ]


def test_valuation_changes_are_evented_and_replayed(service):
    asset = registered(service)
    updated = service.assets.update_valuation(
        "tenant-a", asset.asset_id, "2026-Q2", Decimal("1050000"), Decimal("0.9")
    )
    replayed = service.replay_state("tenant-a")["assets"][0]
    assert updated.current_valuation == Decimal("1050000")
    assert replayed["current_valuation"] == "1050000"
    assert service.store.read("tenant-a")[-1]["event_type"] == "asset.valuation_updated"


def test_optimization_honors_policy_and_preserves_control(service):
    asset = registered(service)
    result = service.analyze(
        "tenant-a",
        AnalyzeRequest(
            asset_id=asset.asset_id,
            policy=OptimizationPolicy(
                max_ownership_dilution=0,
                max_cost_of_capital="0.10",
                require_control=True,
            ),
        ),
    )
    eligible = [item for item in result.optimization.recommendations if item.eligible]
    assert eligible
    assert all(item.option.ownership_dilution == 0 for item in eligible)
    assert all(item.option.preserves_control for item in eligible)
    assert (
        result.explanation.summary
        == service.get_recommendation(
            "tenant-a", result.recommendation_id
        ).explanation.summary
    )


def test_fractionalization_valuation_and_dilution(service):
    asset = registered(service)
    fraction = service.fractions.create(
        "tenant-a",
        asset,
        FractionRequest(
            asset_id=asset.asset_id,
            fraction_type=FractionType.OWNERSHIP_SLICE,
            percentage=20,
        ),
    )
    assert fraction.estimated_value == Decimal("200000.00")
    assert fraction.ownership_remaining == Decimal("80.0000")
    with pytest.raises(ValueError):
        service.fractions.create(
            "tenant-a",
            asset,
            FractionRequest(
                asset_id=asset.asset_id,
                fraction_type=FractionType.PREFERRED_SHARE,
                percentage=90,
            ),
        )


def test_revenue_stream_modeling(service):
    asset = registered(service)
    stream = service.revenue_streams.create(
        "tenant-a",
        RevenueStreamRequest(
            asset_id=asset.asset_id,
            cash_flows=[
                FutureCashFlow(period="2027", amount=100000, probability="0.9"),
                FutureCashFlow(period="2028", amount=120000, probability="0.8"),
            ],
            participation_percentage=25,
            time_horizon_months=24,
            expected_annual_yield="0.10",
            risk_score="0.20",
        ),
    )
    assert stream.expected_cash_flow == Decimal("46500.00")
    assert stream.present_value == Decimal("38750.00")
    assert stream.risk_adjusted_value == Decimal("31000.00")


def test_auction_book_deterministic_matching(service):
    asset = registered(service)
    ask = service.auctions.add(
        "tenant-a",
        OrderSide.ASK,
        OrderRequest(
            asset_id=asset.asset_id,
            ownership_percentage=10,
            price_per_percentage_point=9000,
        ),
    )
    bid = service.auctions.add(
        "tenant-a",
        OrderSide.BID,
        OrderRequest(
            asset_id=asset.asset_id,
            ownership_percentage=6,
            price_per_percentage_point=11000,
        ),
    )
    book = service.auctions.book("tenant-a", asset.asset_id)
    assert book.simulated_matches[0].bid_id == bid.order_id
    assert book.simulated_matches[0].ask_id == ask.order_id
    assert book.simulated_matches[0].ownership_percentage == Decimal("6.0000")
    assert book.simulated_matches[0].total_price == Decimal("60000.00")
    service.auctions.record_simulation("tenant-a", asset.asset_id)
    history = service.auctions.book("tenant-a", asset.asset_id).historical_transactions
    assert history == book.simulated_matches


def test_dynamic_collateral_scoring_and_event(service):
    asset = registered(service)
    report = service.collateral_report("tenant-a", asset.asset_id)
    assert Decimal("0") < report.collateral_health_score <= Decimal("100")
    assert report.borrowing_capacity > 0
    event_types = [event["event_type"] for event in service.store.read("tenant-a")]
    assert "collateral.calculated" in event_types


def test_fail_closed_trust_in_production(tmp_path):
    service = LiquidityIntelligenceService(
        store_path=tmp_path / "prod-events.jsonl",
        trust_policy=TrustPolicy(adapter=None, environment="production"),
    )
    asset = registered(service)
    with pytest.raises(PermissionError):
        service.analyze("tenant-a", AnalyzeRequest(asset_id=asset.asset_id))


def test_audit_bundle_is_tenant_scoped_and_reproducible(service):
    asset = registered(service)
    service.analyze("tenant-a", AnalyzeRequest(asset_id=asset.asset_id))
    registered(service, "tenant-b")
    first = service.audit_bundle("tenant-a")
    second = service.audit_bundle("tenant-a")
    assert first == second
    assert first["event_count"] == 3
    assert {event["tenant_id"] for event in first["events"]} == {"tenant-a"}


def test_api_authorization_and_tenant_boundary(service, monkeypatch):
    app.dependency_overrides[liquidity_routes.get_liquidity_service] = lambda: service
    monkeypatch.setattr(auth, "get_api_key", lambda: "secret")
    client = TestClient(app)
    payload = sample_asset().model_dump(mode="json", exclude_none=True)
    try:
        unauthorized = client.post(
            "/liquidity/assets", headers={"X-Tenant-ID": "tenant-a"}, json=payload
        )
        assert unauthorized.status_code == 401
        created = client.post(
            "/liquidity/assets",
            headers={"X-Tenant-ID": "tenant-a", "X-API-Key": "secret"},
            json=payload,
        )
        assert created.status_code == 200
        asset_id = created.json()["asset_id"]
        hidden = client.get(
            f"/collateral/health/{asset_id}",
            headers={"X-Tenant-ID": "tenant-b", "X-API-Key": "secret"},
        )
        assert hidden.status_code == 404
    finally:
        app.dependency_overrides.clear()
