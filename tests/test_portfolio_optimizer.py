from datetime import date

import numpy as np
import pandas as pd

from src.engine.expression.schemas import ExpressionDecision
from src.engine.portfolio.constraints import DynamicConstraintAdjuster
from src.engine.portfolio.hedge import HedgeSleeveManager
from src.engine.portfolio.optimizer import PortfolioOptimizer
from src.engine.portfolio.rebalance import RebalanceStateMachine
from src.engine.portfolio.risk import RiskEstimator


def _make_decision(weights=None):
    weights = weights or {"XLE": 0.5, "ITA": 0.3, "SEA": 0.2}
    return ExpressionDecision(
        as_of_date=date(2024, 1, 1),
        theme="energy",
        subtheme="oil",
        expression_type="single_name",
        target_symbols=list(weights.keys()),
        weights=weights,
        confidence=0.7,
    )


def test_simple_target():
    optimizer = PortfolioOptimizer()
    decision = _make_decision()
    target = optimizer.build_target(decision)
    assert target.gross_exposure > 0
    assert len(target.weights) == 3


def test_optimized_target():
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(
        rng.normal(0.0005, 0.015, (200, 3)),
        columns=["XLE", "ITA", "SEA"],
    )
    optimizer = PortfolioOptimizer(returns=returns)
    decision = _make_decision()
    target = optimizer.build_target(decision, regime="normal", signal_score=0.6)
    assert target.gross_exposure > 0
    assert all(abs(w) <= 0.55 for w in target.weights.values())


def test_crisis_constraints():
    adjuster = DynamicConstraintAdjuster()
    normal = adjuster.get_constraints("normal", 0.8)
    crisis = adjuster.get_constraints("crisis", 0.5)
    assert crisis.max_position < normal.max_position
    assert crisis.risk_target < normal.risk_target


def test_rebalance_state_machine():
    sm = RebalanceStateMachine()
    state = sm.update("energy", 0.0)
    assert state == "IDLE"
    state = sm.update("energy", 0.5)
    assert state == "IMPULSE_ONSET"
    state = sm.update("energy", 0.7)
    assert state == "ACTIVE"
    assert sm.position_multiplier("energy") == 1.0


def test_risk_estimator():
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(rng.normal(0, 0.01, (100, 3)), columns=["A", "B", "C"])
    estimator = RiskEstimator()
    cov = estimator.sample_covariance(returns)
    assert cov.shape == (3, 3)
    w = np.array([0.33, 0.33, 0.34])
    scaled = estimator.risk_scale_weights(w, cov, 0.10)
    assert len(scaled) == 3


def test_hedge_manager():
    mgr = HedgeSleeveManager()
    hedges = mgr.compute_hedges({"XLE": 0.5, "ITA": 0.3}, regime="crisis", confidence=0.3)
    assert "SPY" in hedges  # equity beta hedge
    assert "TLT" in hedges  # duration hedge in crisis
    assert "UUP" in hedges  # USD hedge for low confidence
