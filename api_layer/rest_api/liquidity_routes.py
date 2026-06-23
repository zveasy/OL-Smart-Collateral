from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, Header, HTTPException

from liquidity_intelligence.asset_registry import AssetRecord
from liquidity_intelligence.auction_book import OrderRequest, OrderSide
from liquidity_intelligence.fractionalization import FractionRequest
from liquidity_intelligence.revenue_streams import RevenueStreamRequest
from liquidity_intelligence.service import AnalyzeRequest, LiquidityIntelligenceService

from .auth import verify_api_key


router = APIRouter(tags=["Liquidity Intelligence"])


@lru_cache(maxsize=1)
def get_liquidity_service() -> LiquidityIntelligenceService:
    return LiquidityIntelligenceService()


def tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> str:
    value = x_tenant_id.strip()
    if not value or len(value) > 128:
        raise HTTPException(422, "Invalid X-Tenant-ID")
    return value


Auth = Depends(verify_api_key)
Tenant = Depends(tenant_id)
Service = Depends(get_liquidity_service)


@router.post("/liquidity/assets", dependencies=[Auth])
def create_asset(
    request: AssetRecord,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        return service.assets.register(tenant, request)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/liquidity/assets", dependencies=[Auth])
def list_assets(tenant: str = Tenant, service: LiquidityIntelligenceService = Service):
    return service.assets.list(tenant)


@router.post("/liquidity/analyze", dependencies=[Auth])
def analyze(
    request: AnalyzeRequest,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        return service.analyze(tenant, request)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/liquidity/recommendations/{recommendation_id}", dependencies=[Auth])
def recommendation(
    recommendation_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    result = service.get_recommendation(tenant, recommendation_id)
    if result is None:
        raise HTTPException(404, "Recommendation not found")
    return result


@router.get("/liquidity/explanations/{recommendation_id}", dependencies=[Auth])
def explanation(
    recommendation_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    result = service.get_recommendation(tenant, recommendation_id)
    if result is None:
        raise HTTPException(404, "Recommendation not found")
    return result.explanation


@router.get("/liquidity/audit-bundle", dependencies=[Auth])
def audit_bundle(tenant: str = Tenant, service: LiquidityIntelligenceService = Service):
    return service.audit_bundle(tenant)


@router.get("/collateral/health/{asset_id}", dependencies=[Auth])
def collateral_health(
    asset_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        return service.collateral_report(tenant, asset_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/collateral/borrowing-capacity/{asset_id}", dependencies=[Auth])
def borrowing_capacity(
    asset_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        report = service.collateral_report(tenant, asset_id)
        return {
            "asset_id": asset_id,
            "borrowing_capacity": report.borrowing_capacity,
            "loan_to_value_ratio": report.loan_to_value_ratio,
        }
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/fractionalization/create", dependencies=[Auth])
def create_fraction(
    request: FractionRequest,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        asset = service.require_asset(tenant, request.asset_id)
        return service.fractions.create(tenant, asset, request)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/fractionalization/{fraction_id}", dependencies=[Auth])
def get_fraction(
    fraction_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    fraction = service.fractions.get(tenant, fraction_id)
    if fraction is None:
        raise HTTPException(404, "Fraction not found")
    return fraction


def _add_order(
    side: OrderSide,
    request: OrderRequest,
    tenant: str,
    service: LiquidityIntelligenceService,
):
    service.require_asset(tenant, request.asset_id)
    order = service.auctions.add(tenant, side, request)
    service.auctions.record_simulation(tenant, request.asset_id)
    return order


@router.post("/auction/bids", dependencies=[Auth])
def add_bid(
    request: OrderRequest,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        return _add_order(OrderSide.BID, request, tenant, service)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/auction/asks", dependencies=[Auth])
def add_ask(
    request: OrderRequest,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        return _add_order(OrderSide.ASK, request, tenant, service)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/auction/book/{asset_id}", dependencies=[Auth])
def auction_book(
    asset_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        service.require_asset(tenant, asset_id)
        return service.auctions.book(tenant, asset_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/revenue-streams", dependencies=[Auth])
def create_revenue_stream(
    request: RevenueStreamRequest,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    try:
        service.require_asset(tenant, request.asset_id)
        return service.revenue_streams.create(tenant, request)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/revenue-streams/{stream_id}", dependencies=[Auth])
def get_revenue_stream(
    stream_id: str,
    tenant: str = Tenant,
    service: LiquidityIntelligenceService = Service,
):
    stream = service.revenue_streams.get(tenant, stream_id)
    if stream is None:
        raise HTTPException(404, "Revenue stream not found")
    return stream
