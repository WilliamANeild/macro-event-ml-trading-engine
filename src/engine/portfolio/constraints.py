from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioConstraints:
    max_position: float = 0.30
    min_position: float = -0.30
    max_gross_exposure: float = 1.5
    max_net_exposure: float = 0.80
    max_turnover: float = 0.50
    risk_target: float = 0.10


REGIME_CONSTRAINTS = {
    "normal": PortfolioConstraints(),
    "crisis": PortfolioConstraints(
        max_position=0.15,
        min_position=-0.15,
        max_gross_exposure=0.8,
        max_net_exposure=0.3,
        max_turnover=0.3,
        risk_target=0.05,
    ),
    "euphoria": PortfolioConstraints(
        max_position=0.25,
        min_position=-0.25,
        max_gross_exposure=1.2,
        max_net_exposure=0.7,
        max_turnover=0.4,
        risk_target=0.08,
    ),
    "transition": PortfolioConstraints(
        max_position=0.20,
        min_position=-0.20,
        max_gross_exposure=1.0,
        max_net_exposure=0.5,
        max_turnover=0.35,
        risk_target=0.07,
    ),
}


class DynamicConstraintAdjuster:
    def get_constraints(self, regime: str, confidence: float) -> PortfolioConstraints:
        base = REGIME_CONSTRAINTS.get(regime, PortfolioConstraints())
        # Lower confidence -> tighter turnover
        turnover_scale = 0.5 + 0.5 * confidence
        return PortfolioConstraints(
            max_position=base.max_position,
            min_position=base.min_position,
            max_gross_exposure=base.max_gross_exposure,
            max_net_exposure=base.max_net_exposure,
            max_turnover=base.max_turnover * turnover_scale,
            risk_target=base.risk_target,
        )
