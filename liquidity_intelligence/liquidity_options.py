from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from .asset_registry import AssetRecord
from .continuous_valuation import ValuationReport
from .models import clamp, money, score


class LiquidityMethod(str, Enum):
    SECURED_LOAN = "secured_loan"
    LINE_OF_CREDIT = "line_of_credit"
    REVENUE_FINANCING = "revenue_financing"
    PREFERRED_EQUITY = "preferred_equity"
    FRACTIONAL_OWNERSHIP_SALE = "fractional_ownership_sale"
    SECURITIZATION = "securitization"
    INVESTOR_SYNDICATION = "investor_syndication"
    REFINANCE = "refinance"
    HOLD_AND_DEFER = "hold_and_defer"


class LiquidityOption(BaseModel):
    method: LiquidityMethod
    estimated_proceeds: Decimal = Field(ge=0)
    ownership_dilution: Decimal = Field(ge=0, le=100)
    cost_of_capital: Decimal = Field(ge=0, le=1)
    time_to_funding_days: int = Field(ge=0)
    risk_score: Decimal = Field(ge=0, le=1)
    liquidity_score: Decimal = Field(ge=0, le=1)
    confidence_score: Decimal = Field(ge=0, le=1)
    required_evidence: list[str]
    preserves_control: bool


_TERMS = {
    LiquidityMethod.SECURED_LOAN: ("0.65", "0", "0.075", 30, "0.28", True),
    LiquidityMethod.LINE_OF_CREDIT: ("0.45", "0", "0.095", 21, "0.32", True),
    LiquidityMethod.REVENUE_FINANCING: ("0.40", "0", "0.14", 24, "0.38", True),
    LiquidityMethod.PREFERRED_EQUITY: ("0.35", "12", "0.12", 60, "0.42", True),
    LiquidityMethod.FRACTIONAL_OWNERSHIP_SALE: ("0.25", "25", "0.04", 45, "0.35", True),
    LiquidityMethod.SECURITIZATION: ("0.70", "0", "0.065", 90, "0.44", True),
    LiquidityMethod.INVESTOR_SYNDICATION: ("0.50", "20", "0.08", 75, "0.48", False),
    LiquidityMethod.REFINANCE: ("0.60", "0", "0.07", 40, "0.30", True),
    LiquidityMethod.HOLD_AND_DEFER: ("0", "0", "0", 0, "0.08", True),
}


def generate_liquidity_options(
    asset: AssetRecord, valuation: ValuationReport
) -> list[LiquidityOption]:
    annual_revenue = asset.cash_flow.annual_income
    existing_debt = sum(
        (debt.outstanding_principal for debt in asset.existing_debt), Decimal("0")
    )
    options: list[LiquidityOption] = []
    for method in LiquidityMethod:
        advance, dilution, cost, days, risk, control = _TERMS[method]
        proceeds_base = valuation.risk_adjusted_value
        if method == LiquidityMethod.REVENUE_FINANCING:
            proceeds = min(
                proceeds_base * Decimal(advance), annual_revenue * Decimal("1.5")
            )
        elif method == LiquidityMethod.REFINANCE:
            proceeds = max(
                Decimal("0"), proceeds_base * Decimal(advance) - existing_debt
            )
        else:
            proceeds = proceeds_base * Decimal(advance)
        liquidity = (
            Decimal("0")
            if valuation.risk_adjusted_value == 0
            else clamp(proceeds / valuation.risk_adjusted_value)
        )
        evidence = ["current_valuation", "ownership_record", "trust_evidence"]
        if method in {
            LiquidityMethod.REVENUE_FINANCING,
            LiquidityMethod.SECURITIZATION,
        }:
            evidence.append("revenue_history")
        if method in {
            LiquidityMethod.SECURED_LOAN,
            LiquidityMethod.LINE_OF_CREDIT,
            LiquidityMethod.REFINANCE,
        }:
            evidence.extend(["insurance", "existing_debt"])
        options.append(
            LiquidityOption(
                method=method,
                estimated_proceeds=money(proceeds),
                ownership_dilution=score(dilution),
                cost_of_capital=score(cost),
                time_to_funding_days=days,
                risk_score=score(risk),
                liquidity_score=score(liquidity),
                confidence_score=valuation.confidence_score,
                required_evidence=sorted(evidence),
                preserves_control=control,
            )
        )
    return options
