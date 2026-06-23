from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .event_store import EventStore
from .models import deterministic_id


class AssetClass(str, Enum):
    REAL_ESTATE = "real_estate"
    BUSINESS = "business"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    ENERGY_ASSET = "energy_asset"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    FUTURE_REVENUE_STREAM = "future_revenue_stream"


class ValuationPoint(BaseModel):
    period: str
    value: Decimal = Field(gt=0)
    confidence: Decimal = Field(default=Decimal("0.8"), ge=0, le=1)
    source: str = "owner"


class CashFlowCharacteristics(BaseModel):
    annual_income: Decimal = Field(default=Decimal("0"), ge=0)
    annual_expenses: Decimal = Field(default=Decimal("0"), ge=0)
    stability: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    utilization: Decimal = Field(default=Decimal("1"), ge=0, le=1)


class InsuranceInformation(BaseModel):
    active: bool = False
    coverage_amount: Decimal = Field(default=Decimal("0"), ge=0)
    expires_on: str | None = None
    provider: str | None = None


class MaintenanceRecord(BaseModel):
    period: str
    status: str
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    evidence_reference: str | None = None


class DebtObligation(BaseModel):
    creditor: str
    outstanding_principal: Decimal = Field(ge=0)
    annual_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    maturity: str | None = None


class RevenuePoint(BaseModel):
    period: str
    amount: Decimal = Field(ge=0)


class AssetRecord(BaseModel):
    asset_id: str | None = None
    tenant_id: str | None = None
    asset_class: AssetClass
    ownership_percentage: Decimal = Field(gt=0, le=100)
    current_valuation: Decimal = Field(gt=0)
    historical_valuations: list[ValuationPoint] = Field(default_factory=list)
    cash_flow: CashFlowCharacteristics = Field(default_factory=CashFlowCharacteristics)
    insurance: InsuranceInformation = Field(default_factory=InsuranceInformation)
    maintenance_history: list[MaintenanceRecord] = Field(default_factory=list)
    existing_debt: list[DebtObligation] = Field(default_factory=list)
    revenue_history: list[RevenuePoint] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_references: list[str] = Field(default_factory=list)

    @field_validator("evidence_references")
    @classmethod
    def unique_references(cls, values: list[str]) -> list[str]:
        return sorted(set(values))


class AssetRegistry:
    def __init__(self, store: EventStore) -> None:
        self.store = store

    def register(self, tenant_id: str, asset: AssetRecord) -> AssetRecord:
        data = asset.model_dump(mode="python", exclude={"asset_id", "tenant_id"})
        asset_id = asset.asset_id or deterministic_id(
            "asset", {"tenant_id": tenant_id, "asset": data}
        )
        if self.get(tenant_id, asset_id) is not None:
            raise ValueError(f"Asset {asset_id} already exists")
        saved = asset.model_copy(update={"asset_id": asset_id, "tenant_id": tenant_id})
        self.store.append(tenant_id, "asset.registered", asset_id, saved)
        return saved

    def list(self, tenant_id: str) -> list[AssetRecord]:
        assets: dict[str, AssetRecord] = {}
        for event in self.store.read(tenant_id):
            if event["event_type"] in {
                "asset.registered",
                "asset.valuation_updated",
            }:
                assets[event["aggregate_id"]] = AssetRecord.model_validate(
                    event["payload"]
                )
        return list(assets.values())

    def get(self, tenant_id: str, asset_id: str) -> AssetRecord | None:
        return next(
            (asset for asset in self.list(tenant_id) if asset.asset_id == asset_id),
            None,
        )

    def update_valuation(
        self,
        tenant_id: str,
        asset_id: str,
        period: str,
        value: Decimal,
        confidence: Decimal = Decimal("0.8"),
        source: str = "owner",
    ) -> AssetRecord:
        asset = self.get(tenant_id, asset_id)
        if asset is None:
            raise LookupError("Asset not found")
        point = ValuationPoint(
            period=period,
            value=value,
            confidence=confidence,
            source=source,
        )
        updated = asset.model_copy(
            update={
                "current_valuation": value,
                "historical_valuations": [*asset.historical_valuations, point],
            }
        )
        self.store.append(
            tenant_id,
            "asset.valuation_updated",
            asset_id,
            updated,
        )
        return updated
