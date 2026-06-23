from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .asset_registry import AssetRecord, ValuationPoint
from .models import clamp, money, score


class ComparableAsset(BaseModel):
    reference: str
    value: Decimal = Field(gt=0)
    similarity: Decimal = Field(ge=0, le=1)


class ValuationReport(BaseModel):
    base_value: Decimal
    cash_flow_adjustment: Decimal
    comparable_adjustment: Decimal
    risk_adjustment: Decimal
    risk_adjusted_value: Decimal
    confidence_low: Decimal
    confidence_high: Decimal
    confidence_score: Decimal
    drift_detected: bool
    drift_percentage: Decimal
    rationale: list[str]


class ContinuousValuation:
    @staticmethod
    def append_history(
        asset: AssetRecord, period: str, value: Decimal, confidence: Decimal
    ) -> AssetRecord:
        point = ValuationPoint(period=period, value=value, confidence=confidence)
        return asset.model_copy(
            update={
                "current_valuation": value,
                "historical_valuations": [*asset.historical_valuations, point],
            }
        )

    @staticmethod
    def evaluate(
        asset: AssetRecord,
        comparables: list[ComparableAsset] | None = None,
        trust_confidence: Decimal = Decimal("0.8"),
    ) -> ValuationReport:
        comparables = comparables or []
        base = asset.current_valuation
        net_cash_flow = asset.cash_flow.annual_income - asset.cash_flow.annual_expenses
        cash_flow_ratio = clamp(net_cash_flow / base if base else 0, -0.1, 0.2)
        cash_flow_adjustment = base * cash_flow_ratio * Decimal("0.25")

        if comparables:
            weight = sum((item.similarity for item in comparables), Decimal("0"))
            comparable_value = (
                sum(
                    (item.value * item.similarity for item in comparables), Decimal("0")
                )
                / weight
            )
            comparable_adjustment = (comparable_value - base) * Decimal("0.20")
        else:
            comparable_adjustment = Decimal("0")

        debt = sum(
            (item.outstanding_principal for item in asset.existing_debt), Decimal("0")
        )
        debt_ratio = clamp(debt / base if base else 1)
        insurance_penalty = Decimal("0") if asset.insurance.active else Decimal("0.08")
        maintenance_penalty = (
            Decimal("0.05")
            if any(
                record.status.lower() in {"overdue", "poor", "critical"}
                for record in asset.maintenance_history
            )
            else Decimal("0")
        )
        risk_rate = clamp(
            (debt_ratio * Decimal("0.15"))
            + insurance_penalty
            + maintenance_penalty
            + ((Decimal("1") - asset.cash_flow.stability) * Decimal("0.10")),
            0,
            Decimal("0.35"),
        )
        pre_risk = base + cash_flow_adjustment + comparable_adjustment
        risk_adjustment = -(pre_risk * risk_rate)
        risk_adjusted = max(Decimal("0"), pre_risk + risk_adjustment)

        history = asset.historical_valuations
        previous = history[-1].value if history else base
        drift = (base - previous) / previous if previous else Decimal("0")
        confidence = clamp(
            (trust_confidence * Decimal("0.50"))
            + (Decimal("0.20") if history else Decimal("0.05"))
            + (Decimal("0.20") if comparables else Decimal("0.05"))
            + (asset.cash_flow.stability * Decimal("0.10"))
        )
        interval = Decimal("0.05") + ((Decimal("1") - confidence) * Decimal("0.20"))

        return ValuationReport(
            base_value=money(base),
            cash_flow_adjustment=money(cash_flow_adjustment),
            comparable_adjustment=money(comparable_adjustment),
            risk_adjustment=money(risk_adjustment),
            risk_adjusted_value=money(risk_adjusted),
            confidence_low=money(risk_adjusted * (Decimal("1") - interval)),
            confidence_high=money(risk_adjusted * (Decimal("1") + interval)),
            confidence_score=score(confidence),
            drift_detected=abs(drift) >= Decimal("0.10"),
            drift_percentage=score(drift * 100),
            rationale=[
                "Cash-flow adjustment uses annual net cash flow relative to asset value.",
                "Comparable values receive similarity-weighted influence when provided.",
                "Risk adjustment reflects debt, insurance, maintenance, and revenue stability.",
            ],
        )
