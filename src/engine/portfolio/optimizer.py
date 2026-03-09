from __future__ import annotations

from src.engine.expression.schemas import ExpressionDecision

from .schemas import PortfolioTarget


class PortfolioOptimizer:
    def build_target(self, decision: ExpressionDecision) -> PortfolioTarget:
        gross_exposure = sum(abs(weight) for weight in decision.weights.values())
        net_exposure = sum(decision.weights.values())

        return PortfolioTarget(
            as_of_date=decision.as_of_date,
            weights=decision.weights,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            metadata={"note": "mock portfolio target from expression decision"},
        )