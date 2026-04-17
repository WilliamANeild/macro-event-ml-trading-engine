from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BacktestResult:
    returns: list[float] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    costs: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    equity_curve: list[float] = field(default_factory=list)
    drawdowns: list[float] = field(default_factory=list)
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    attribution: dict[str, Any] = field(default_factory=dict)
    event_log: list[dict[str, Any]] = field(default_factory=list)
    benchmark_returns: dict[str, list[float]] = field(default_factory=dict)
    benchmark_equity: dict[str, list[float]] = field(default_factory=dict)
    benchmark_sharpe: dict[str, float] = field(default_factory=dict)
    dates: list[str] = field(default_factory=list)