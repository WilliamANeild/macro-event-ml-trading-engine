from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.engine.backtest.schemas import BacktestResult


def plot_equity_curve(result: BacktestResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(result.equity_curve, linewidth=1.5, color="steelblue")
    ax.set_title("Equity Curve")
    ax.set_xlabel("Day")
    ax.set_ylabel("Equity")
    ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_drawdown(result: BacktestResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    dd = result.drawdowns
    ax.fill_between(range(len(dd)), dd, 0, alpha=0.5, color="crimson")
    ax.set_title(f"Drawdown (Max: {result.max_drawdown:.2%})")
    ax.set_xlabel("Day")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_exposure_over_time(result: BacktestResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    dates = []
    gross = []
    net = []
    for trade in result.trades:
        dates.append(trade.get("date", ""))
        w = trade.get("weights", {})
        gross.append(sum(abs(v) for v in w.values()))
        net.append(sum(w.values()))
    x = range(len(dates))
    ax.bar(x, gross, alpha=0.4, label="Gross", color="steelblue")
    ax.plot(x, net, color="orange", linewidth=1.5, label="Net")
    ax.set_title("Exposure Over Time")
    ax.set_xlabel("Rebalance")
    ax.set_ylabel("Exposure")
    ax.legend()
    ax.grid(True, alpha=0.3)
    if len(dates) > 10:
        step = max(1, len(dates) // 10)
        ax.set_xticks(list(x)[::step])
        ax.set_xticklabels(dates[::step], rotation=45)
    fig.tight_layout()
    return fig


def plot_event_impact(result: BacktestResult) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    events = result.event_log
    if events:
        dates = [e.get("date", "") for e in events]
        intensities = [e.get("intensity", 0) for e in events]
        ax.bar(range(len(dates)), intensities, color="coral", alpha=0.7)
        if len(dates) > 10:
            step = max(1, len(dates) // 10)
            ax.set_xticks(list(range(len(dates)))[::step])
            ax.set_xticklabels(dates[::step], rotation=45)
    ax.set_title("Event Intensity Over Time")
    ax.set_xlabel("Event")
    ax.set_ylabel("Intensity")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
