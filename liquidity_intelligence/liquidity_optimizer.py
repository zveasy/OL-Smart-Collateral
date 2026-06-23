from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .liquidity_options import LiquidityOption
from .models import score


class OptimizationPolicy(BaseModel):
    max_ownership_dilution: Decimal = Field(default=Decimal("25"), ge=0, le=100)
    max_cost_of_capital: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    max_risk_score: Decimal = Field(default=Decimal("0.70"), ge=0, le=1)
    require_control: bool = True
    minimum_proceeds: Decimal = Field(default=Decimal("0"), ge=0)


class RankedRecommendation(BaseModel):
    rank: int
    option: LiquidityOption
    total_score: Decimal
    eligible: bool
    policy_violations: list[str]
    rationale: list[str]


class OptimizationResult(BaseModel):
    recommendations: list[RankedRecommendation]
    policy: OptimizationPolicy


class LiquidityOptimizer:
    @staticmethod
    def optimize(
        options: list[LiquidityOption], policy: OptimizationPolicy
    ) -> OptimizationResult:
        evaluated: list[RankedRecommendation] = []
        for option in options:
            violations: list[str] = []
            if option.ownership_dilution > policy.max_ownership_dilution:
                violations.append("ownership dilution exceeds policy")
            if option.cost_of_capital > policy.max_cost_of_capital:
                violations.append("cost of capital exceeds policy")
            if option.risk_score > policy.max_risk_score:
                violations.append("risk score exceeds policy")
            if policy.require_control and not option.preserves_control:
                violations.append("option does not preserve control")
            if option.estimated_proceeds < policy.minimum_proceeds:
                violations.append("estimated proceeds are below policy minimum")

            dilution_penalty = option.ownership_dilution / Decimal("100")
            time_score = max(
                Decimal("0"),
                Decimal("1") - (Decimal(option.time_to_funding_days) / Decimal("180")),
            )
            total = (
                option.liquidity_score * Decimal("0.35")
                + (Decimal("1") - dilution_penalty) * Decimal("0.20")
                + (Decimal("1") - option.cost_of_capital) * Decimal("0.15")
                + (Decimal("1") - option.risk_score) * Decimal("0.10")
                + option.confidence_score * Decimal("0.10")
                + time_score * Decimal("0.05")
                + (Decimal("0.05") if option.preserves_control else Decimal("0"))
            )
            if violations:
                total -= Decimal("1")
            evaluated.append(
                RankedRecommendation(
                    rank=0,
                    option=option,
                    total_score=score(total),
                    eligible=not violations,
                    policy_violations=violations,
                    rationale=[
                        f"Liquidity contribution: {score(option.liquidity_score * Decimal('0.35'))}.",
                        f"Ownership dilution: {option.ownership_dilution}%.",
                        f"Annual cost of capital: {score(option.cost_of_capital * 100)}%.",
                        "Control is preserved."
                        if option.preserves_control
                        else "Control may be shared.",
                    ],
                )
            )

        evaluated.sort(
            key=lambda item: (
                not item.eligible,
                -item.total_score,
                item.option.method.value,
            )
        )
        ranked = [
            item.model_copy(update={"rank": index})
            for index, item in enumerate(evaluated, 1)
        ]
        return OptimizationResult(recommendations=ranked, policy=policy)
