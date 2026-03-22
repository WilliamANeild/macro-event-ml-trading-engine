from src.engine.backtest.metrics import (
    compute_drawdowns,
    compute_hit_rate,
    compute_max_drawdown,
    compute_sharpe,
    compute_turnover,
)
from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.data.synthetic import SyntheticConfig, SyntheticDataGenerator


def test_sharpe():
    returns = [0.01, -0.005, 0.008, -0.003, 0.012, 0.002]
    s = compute_sharpe(returns)
    assert isinstance(s, float)


def test_max_drawdown():
    curve = [1.0, 1.05, 1.02, 0.95, 0.93, 0.98, 1.01]
    mdd = compute_max_drawdown(curve)
    assert mdd < 0  # Drawdown is negative


def test_drawdowns():
    curve = [1.0, 1.05, 1.02, 0.95]
    dd = compute_drawdowns(curve)
    assert len(dd) == len(curve)
    assert dd[0] == 0.0  # First point is peak


def test_hit_rate():
    returns = [0.01, -0.005, 0.008, -0.003, 0.012]
    hr = compute_hit_rate(returns)
    assert hr == 3 / 5


def test_turnover():
    history = [{"A": 0.5, "B": 0.5}, {"A": 0.3, "B": 0.7}, {"A": 0.6, "B": 0.4}]
    t = compute_turnover(history)
    assert t > 0


def test_walk_forward_backtest():
    cfg = SyntheticConfig(n_days=120, n_shocks=2, seed=42)
    gen = SyntheticDataGenerator(config=cfg)
    backtester = WalkForwardBacktester(data_gen=gen, rebalance_freq=10)
    result = backtester.run()
    assert len(result.equity_curve) > 0
    assert len(result.returns) > 0
    assert isinstance(result.sharpe, float)
    assert result.max_drawdown <= 0
    assert result.metadata.get("n_days", 0) > 0
