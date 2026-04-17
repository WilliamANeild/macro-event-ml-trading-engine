from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.engine.expression.schemas import ExpressionDecision
from src.engine.universe.schemas import Instrument

from .constraints import DynamicConstraintAdjuster, PortfolioConstraints
from .hedge import HedgeSleeveManager
from .rebalance import RebalanceStateMachine
from .risk import RiskEstimator
from .schemas import PortfolioTarget


class PortfolioOptimizer:
    def __init__(
        self,
        returns: pd.DataFrame | None = None,
        universe: list[Instrument] | None = None,
        risk_lambda: float = 1.0,
    ) -> None:
        self.returns = returns
        self.universe = universe or []
        self.risk_lambda = risk_lambda
        self.risk_estimator = RiskEstimator()
        self.constraint_adjuster = DynamicConstraintAdjuster()
        self.rebalance_sm = RebalanceStateMachine()
        self.hedge_manager = HedgeSleeveManager()
        self._prev_weights: dict[str, float] = {}

    def build_target(
        self,
        decision: ExpressionDecision,
        regime: str = "normal",
        signal_score: float = 0.5,
    ) -> PortfolioTarget:
        # Simple pass-through if no returns data (mock mode)
        if self.returns is None:
            return self._simple_target(decision)

        symbols = list(decision.weights.keys())
        available = [s for s in symbols if s in self.returns.columns]
        if not available:
            return self._simple_target(decision)

        # Get constraints
        constraints = self.constraint_adjuster.get_constraints(regime, decision.confidence)

        # Compute covariance
        ret_data = self.returns[available]
        cov = self.risk_estimator.estimate(ret_data)
        n = len(available)

        # Expected returns from decision weights (signal-based)
        mu = np.array([decision.weights.get(s, 0.0) for s in available])

        # Optimize: max w'mu - lambda * w'Σw
        def objective(w: np.ndarray) -> float:
            return -(w @ mu - self.risk_lambda * w @ cov @ w)

        # Constraints for scipy
        opt_constraints = [
            {"type": "ineq", "fun": lambda w: constraints.max_gross_exposure - np.sum(np.abs(w))},
            {"type": "ineq", "fun": lambda w: constraints.max_net_exposure - abs(np.sum(w))},
        ]

        bounds = [(constraints.min_position, constraints.max_position)] * n
        x0 = mu / (np.sum(np.abs(mu)) + 1e-8) * 0.5

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=opt_constraints,
            options={"maxiter": 200},
        )

        opt_w = result.x if result.success else x0

        # Risk scaling
        opt_w = self.risk_estimator.risk_scale_weights(opt_w, cov, constraints.risk_target)

        # Rebalance state multiplier
        state = self.rebalance_sm.update(decision.theme, signal_score)
        multiplier = self.rebalance_sm.position_multiplier(decision.theme)
        opt_w = opt_w * multiplier

        # Turnover clipping
        opt_w = self._clip_turnover(available, opt_w, constraints.max_turnover)

        # Build weights dict
        weights = {sym: round(float(opt_w[i]), 6) for i, sym in enumerate(available)}

        # Hedges
        hedge_weights = self.hedge_manager.compute_hedges(
            weights, regime, decision.confidence, self.universe
        )

        gross = sum(abs(v) for v in weights.values())
        net = sum(weights.values())
        old_weights = dict(self._prev_weights)
        turnover = sum(
            abs(weights.get(s, 0) - old_weights.get(s, 0))
            for s in set(list(weights.keys()) + list(old_weights.keys()))
        )
        self._prev_weights = dict(weights)

        return PortfolioTarget(
            as_of_date=decision.as_of_date,
            weights=weights,
            gross_exposure=round(gross, 6),
            net_exposure=round(net, 6),
            turnover=round(turnover, 6),
            risk_target=constraints.risk_target,
            regime=regime,
            hedge_weights=hedge_weights,
            metadata={
                "rebalance_state": state,
                "optimizer_success": result.success,
            },
        )

    def _simple_target(self, decision: ExpressionDecision) -> PortfolioTarget:
        gross_exposure = sum(abs(weight) for weight in decision.weights.values())
        net_exposure = sum(decision.weights.values())
        return PortfolioTarget(
            as_of_date=decision.as_of_date,
            weights=decision.weights,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            metadata={"note": "mock portfolio target from expression decision"},
        )

    def _clip_turnover(
        self, symbols: list[str], new_w: np.ndarray, max_turnover: float
    ) -> np.ndarray:
        prev = np.array([self._prev_weights.get(s, 0.0) for s in symbols])
        delta = new_w - prev
        total_turnover = float(np.sum(np.abs(delta)))
        if total_turnover > max_turnover and total_turnover > 0:
            scale = max_turnover / total_turnover
            new_w = prev + delta * scale
        return new_w
