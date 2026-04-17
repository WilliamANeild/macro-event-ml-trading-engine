from __future__ import annotations

import numpy as np


def compute_sharpe(returns: list[float], risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    r = np.array(returns)
    excess = r - risk_free / 252
    std = float(np.std(excess, ddof=1))
    if std < 1e-10:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(252))


def compute_max_drawdown(equity_curve: list[float]) -> float:
    if len(equity_curve) < 2:
        return 0.0
    ec = np.array(equity_curve)
    peak = np.maximum.accumulate(ec)
    dd = (ec - peak) / np.where(peak > 0, peak, 1.0)
    return float(np.min(dd))


def compute_drawdowns(equity_curve: list[float]) -> list[float]:
    if len(equity_curve) < 2:
        return []
    ec = np.array(equity_curve)
    peak = np.maximum.accumulate(ec)
    dd = (ec - peak) / np.where(peak > 0, peak, 1.0)
    return dd.tolist()


def compute_calmar(returns: list[float], equity_curve: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    ann_return = float(np.mean(returns)) * 252
    mdd = abs(compute_max_drawdown(equity_curve))
    if mdd < 1e-10:
        return 0.0
    return ann_return / mdd


def compute_turnover(weight_history: list[dict[str, float]]) -> float:
    if len(weight_history) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(weight_history)):
        prev = weight_history[i - 1]
        curr = weight_history[i]
        all_syms = set(list(prev.keys()) + list(curr.keys()))
        total += sum(abs(curr.get(s, 0) - prev.get(s, 0)) for s in all_syms)
    return total / (len(weight_history) - 1)


def compute_information_ratio(
    strategy_returns: list[float], benchmark_returns: list[float]
) -> float:
    if len(strategy_returns) < 2 or len(benchmark_returns) < 2:
        return 0.0
    excess = np.array(strategy_returns) - np.array(benchmark_returns)
    te = float(np.std(excess, ddof=1))
    if te < 1e-10:
        return 0.0
    return float(np.mean(excess) / te * np.sqrt(252))


def compute_sortino(returns: list[float], risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    r = np.array(returns)
    excess = r - risk_free / 252
    downside = excess[excess < 0]
    if len(downside) < 1:
        return 0.0
    down_std = float(np.std(downside, ddof=1))
    if down_std < 1e-10:
        return 0.0
    return float(np.mean(excess) / down_std * np.sqrt(252))


def compute_hit_rate(returns: list[float]) -> float:
    if not returns:
        return 0.0
    wins = sum(1 for r in returns if r > 0)
    return wins / len(returns)
