from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from .asset_registry import AssetRecord
from .event_store import EventStore
from .models import deterministic_id, money, score


class FractionType(str, Enum):
    OWNERSHIP_SLICE = "ownership_slice"
    PREFERRED_SHARE = "preferred_share"
    REVENUE_PARTICIPATION = "revenue_participation"
    APPRECIATION_RIGHT = "appreciation_right"
    TIME_BOUND_PARTICIPATION = "time_bound_participation"


class FractionRequest(BaseModel):
    asset_id: str
    fraction_type: FractionType
    percentage: Decimal = Field(gt=0, le=100)
    preferred_return: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    duration_months: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_duration(self) -> "FractionRequest":
        if (
            self.fraction_type == FractionType.TIME_BOUND_PARTICIPATION
            and self.duration_months is None
        ):
            raise ValueError("duration_months is required for time-bound participation")
        return self


class Fraction(BaseModel):
    fraction_id: str
    tenant_id: str
    asset_id: str
    fraction_type: FractionType
    percentage: Decimal
    preferred_return: Decimal
    duration_months: int | None
    estimated_value: Decimal
    ownership_remaining: Decimal


class FractionalizationService:
    def __init__(self, store: EventStore) -> None:
        self.store = store

    def create(
        self, tenant_id: str, asset: AssetRecord, request: FractionRequest
    ) -> Fraction:
        existing = self.list_for_asset(tenant_id, asset.asset_id or "")
        allocated = sum((item.percentage for item in existing), Decimal("0"))
        if allocated + request.percentage > asset.ownership_percentage:
            raise ValueError("Fraction exceeds available ownership")
        request_data = request.model_dump(mode="python")
        fraction_id = deterministic_id(
            "fraction",
            {
                "tenant_id": tenant_id,
                "request": request_data,
                "ordinal": len(existing) + 1,
            },
        )
        value = asset.current_valuation * request.percentage / Decimal("100")
        fraction = Fraction(
            fraction_id=fraction_id,
            tenant_id=tenant_id,
            asset_id=request.asset_id,
            fraction_type=request.fraction_type,
            percentage=score(request.percentage),
            preferred_return=score(request.preferred_return),
            duration_months=request.duration_months,
            estimated_value=money(value),
            ownership_remaining=score(
                asset.ownership_percentage - allocated - request.percentage
            ),
        )
        self.store.append(tenant_id, "fraction.created", fraction_id, fraction)
        return fraction

    def get(self, tenant_id: str, fraction_id: str) -> Fraction | None:
        return next(
            (
                Fraction.model_validate(event["payload"])
                for event in self.store.read(tenant_id)
                if event["event_type"] == "fraction.created"
                and event["aggregate_id"] == fraction_id
            ),
            None,
        )

    def list_for_asset(self, tenant_id: str, asset_id: str) -> list[Fraction]:
        return [
            Fraction.model_validate(event["payload"])
            for event in self.store.read(tenant_id)
            if event["event_type"] == "fraction.created"
            and event["payload"]["asset_id"] == asset_id
        ]
