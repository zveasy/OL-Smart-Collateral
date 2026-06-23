from __future__ import annotations

from pydantic import BaseModel

from .liquidity_optimizer import OptimizationResult


class LiquidityExplanation(BaseModel):
    summary: str
    ownership_impact: str
    cost_of_capital: str
    confidence: str
    key_assumptions: list[str]


class LiquidityExplainer:
    @staticmethod
    def explain(result: OptimizationResult) -> LiquidityExplanation:
        eligible = [item for item in result.recommendations if item.eligible]
        selected = eligible[0] if eligible else result.recommendations[0]
        option = selected.option
        summary = (
            f"{option.method.value.replace('_', ' ').title()} is ranked first because "
            f"its deterministic score is {selected.total_score} while satisfying "
            f"{'all policy constraints' if selected.eligible else 'the fewest available policy constraints'}."
        )
        return LiquidityExplanation(
            summary=summary,
            ownership_impact=(
                f"Estimated ownership dilution is {option.ownership_dilution}% and "
                f"control is {'preserved' if option.preserves_control else 'not fully preserved'}."
            ),
            cost_of_capital=(
                f"Estimated annual cost of capital is {option.cost_of_capital * 100}%."
            ),
            confidence=(
                f"Recommendation confidence is {option.confidence_score * 100}%."
            ),
            key_assumptions=[
                "Inputs and policy weights remain unchanged.",
                "No external market execution or settlement is performed.",
                "Valuation and trust evidence accurately represent persisted state.",
                "All outputs are advisory simulations.",
            ],
        )
