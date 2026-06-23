from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .event_store import EventStore
from .models import clamp, deterministic_id, money, score


class FutureCashFlow(BaseModel):
    period: str
    amount: Decimal = Field(ge=0)
    probability: Decimal = Field(default=Decimal("1"), ge=0, le=1)


class RevenueStreamRequest(BaseModel):
    asset_id: str
    cash_flows: list[FutureCashFlow] = Field(min_length=1)
    participation_percentage: Decimal = Field(gt=0, le=100)
    time_horizon_months: int = Field(gt=0)
    expected_annual_yield: Decimal = Field(ge=0, le=1)
    risk_score: Decimal = Field(ge=0, le=1)


class RevenueStream(BaseModel):
    stream_id: str
    tenant_id: str
    asset_id: str
    cash_flows: list[FutureCashFlow]
    participation_percentage: Decimal
    time_horizon_months: int
    expected_annual_yield: Decimal
    risk_score: Decimal
    expected_cash_flow: Decimal
    present_value: Decimal
    risk_adjusted_value: Decimal


class RevenueStreamService:
    def __init__(self, store: EventStore) -> None:
        self.store = store

    def create(self, tenant_id: str, request: RevenueStreamRequest) -> RevenueStream:
        ordinal = (
            len(
                [
                    event
                    for event in self.store.read(tenant_id)
                    if event["event_type"] == "revenue_stream.created"
                ]
            )
            + 1
        )
        expected = (
            sum(
                (flow.amount * flow.probability for flow in request.cash_flows),
                Decimal("0"),
            )
            * request.participation_percentage
            / Decimal("100")
        )
        years = Decimal(request.time_horizon_months) / Decimal("12")
        discount = Decimal("1") + (request.expected_annual_yield * years)
        present_value = expected / discount
        risk_adjusted = present_value * (Decimal("1") - clamp(request.risk_score))
        stream_id = deterministic_id(
            "stream",
            {"tenant_id": tenant_id, "request": request, "ordinal": ordinal},
        )
        stream = RevenueStream(
            stream_id=stream_id,
            tenant_id=tenant_id,
            asset_id=request.asset_id,
            cash_flows=request.cash_flows,
            participation_percentage=score(request.participation_percentage),
            time_horizon_months=request.time_horizon_months,
            expected_annual_yield=score(request.expected_annual_yield),
            risk_score=score(request.risk_score),
            expected_cash_flow=money(expected),
            present_value=money(present_value),
            risk_adjusted_value=money(risk_adjusted),
        )
        self.store.append(tenant_id, "revenue_stream.created", stream_id, stream)
        return stream

    def get(self, tenant_id: str, stream_id: str) -> RevenueStream | None:
        return next(
            (
                RevenueStream.model_validate(event["payload"])
                for event in self.store.read(tenant_id)
                if event["event_type"] == "revenue_stream.created"
                and event["aggregate_id"] == stream_id
            ),
            None,
        )
