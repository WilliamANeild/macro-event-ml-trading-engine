from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioConstraints:
    max_position: float = 0.55
    min_position: float = -0.55
    max_gross_exposure: float = 3.0
    max_net_exposure: float = 2.0
    max_turnover: float = 1.2
    risk_target: float = 0.35


REGIME_CONSTRAINTS = {
    "normal": PortfolioConstraints(),
    "crisis": PortfolioConstraints(
        max_position=0.35,
        min_position=-0.35,
        max_gross_exposure=1.5,
        max_net_exposure=0.8,
        max_turnover=0.72,
        risk_target=0.20,
    ),
    "euphoria": PortfolioConstraints(
        max_position=0.55,
        min_position=-0.55,
        max_gross_exposure=2.55,
        max_net_exposure=1.7,
        max_turnover=1.02,
        risk_target=0.30,
    ),
    "transition": PortfolioConstraints(
        max_position=0.47,
        min_position=-0.47,
        max_gross_exposure=2.1,
        max_net_exposure=1.3,
        max_turnover=0.9,
        risk_target=0.245,
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
