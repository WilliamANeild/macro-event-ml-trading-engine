from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class TradeRecord:
    date: str
    theme: str
    weights: dict[str, float]
    hedge_weights: dict[str, float]
    overlay_type: str
    daily_pnl: float
    cost: float


class AttributionEngine:
    def __init__(self) -> None:
        self.trade_log: list[TradeRecord] = []

    def log_trade(self, record: TradeRecord) -> None:
        self.trade_log.append(record)

    def decompose_returns(self) -> dict[str, Any]:
        if not self.trade_log:
            return {}

        theme_pnl: dict[str, float] = {}
        hedge_pnl: float = 0.0
        overlay_pnl: float = 0.0
        total_costs: float = 0.0

        for rec in self.trade_log:
            theme_pnl[rec.theme] = theme_pnl.get(rec.theme, 0.0) + rec.daily_pnl
            if rec.hedge_weights:
                # Defensive hedges move inversely to the portfolio.
                # Compute hedge P&L as dot(hedge_weights, -portfolio_return)
                # where portfolio_return is approximated from daily_pnl and
                # the sum of core position weights (notional-weighted return).
                core_exposure = sum(abs(w) for w in rec.weights.values()) if rec.weights else 1.0
                portfolio_return = rec.daily_pnl / core_exposure if core_exposure else 0.0
                hedge_return = -portfolio_return  # defensive hedge proxy
                hedge_pnl += sum(
                    w * hedge_return for w in rec.hedge_weights.values()
                )
            if rec.overlay_type not in ("none", "unwind"):
                overlay_pnl -= rec.cost  # actual premium / cost drag
            total_costs += rec.cost

        return {
            "by_theme": theme_pnl,
            "hedge_contribution": round(hedge_pnl, 6),
            "overlay_contribution": round(overlay_pnl, 6),
            "total_cost_drag": round(total_costs, 6),
            "n_trades": len(self.trade_log),
        }

    def event_replay(
        self, event_manifest: list[Any]
    ) -> list[dict[str, Any]]:
        replay: list[dict[str, Any]] = []
        for event in event_manifest:
            event_date = str(event.date)
            matching = [t for t in self.trade_log if t.date == event_date]
            replay.append({
                "event_date": event_date,
                "event_theme": getattr(event, "theme", "unknown"),
                "trades_on_date": len(matching),
                "pnl_on_date": sum(t.daily_pnl for t in matching),
            })
        return replay
