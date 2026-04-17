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


# Per-instrument weight caps: noisy or low-signal instruments get tighter limits
INSTRUMENT_WEIGHT_CAPS: dict[str, float] = {
    "SLV": 0.005,  # silver — high vol, poor signal-to-noise
    "ITA": 0.005,  # defense ETF — consistent drag
    "LMT": 0.005,  # Lockheed — low signal, negative contribution
    "SH": 0.005,   # inverse S&P — not useful as a long position
}


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

        # Expected returns from historical mean + decision signal
        hist_mu = np.array([float(ret_data[s].mean()) for s in available])
        decision_w = np.array([decision.weights.get(s, 0.0) for s in available])
        mu = hist_mu + decision_w * 0.01

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

        # Per-instrument trend adjustment: scale weights based on whether
        # price is above/below its 50-day moving average
        if len(ret_data) >= 50:
            cum_prices = (1 + ret_data).cumprod()
            ma50 = cum_prices.rolling(50).mean().iloc[-1]
            current = cum_prices.iloc[-1]
            for i, sym in enumerate(available):
                if sym in ma50.index and ma50[sym] > 0:
                    trend_ratio = current[sym] / ma50[sym]
                    trend_scale = 0.7 + 0.6 * min(max(trend_ratio - 0.95, 0) / 0.10, 1.0)
                    opt_w[i] *= trend_scale

        # Rebalance state multiplier
        state = self.rebalance_sm.update(decision.theme, signal_score)
        multiplier = self.rebalance_sm.position_multiplier(decision.theme)
        opt_w = opt_w * multiplier

        # Signal conviction scaling with floor: weak signals still produce
        # testable positions (minimum 10% of optimized size)
        conviction_floor = 0.70
        conviction_scale = max(signal_score, conviction_floor)
        opt_w = opt_w * conviction_scale

        # Turnover clipping
        opt_w = self._clip_turnover(available, opt_w, constraints.max_turnover)

        # Enforce hard position limits after all scaling
        for i in range(len(opt_w)):
            opt_w[i] = np.clip(opt_w[i], constraints.min_position, constraints.max_position)

        # Per-instrument weight caps for noisy assets
        for i, sym in enumerate(available):
            if sym in INSTRUMENT_WEIGHT_CAPS:
                cap = INSTRUMENT_WEIGHT_CAPS[sym]
                opt_w[i] = np.clip(opt_w[i], -cap, cap)

        # Enforce minimum position size floor: if a weight is nonzero but
        # below the floor, bump it up so weak signals remain testable.
        # Skip instruments with explicit caps — they should stay at their cap.
        min_weight_floor = 0.005  # 50 bps
        for i in range(len(opt_w)):
            sym = available[i]
            if sym in INSTRUMENT_WEIGHT_CAPS:
                continue
            if abs(opt_w[i]) > 1e-10 and abs(opt_w[i]) < min_weight_floor:
                opt_w[i] = np.sign(opt_w[i]) * min_weight_floor

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
