from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.engine.backtest.attribution import AttributionEngine, TradeRecord
from src.engine.backtest.metrics import (
    compute_drawdowns,
    compute_hit_rate,
    compute_max_drawdown,
    compute_sharpe,
)
from src.engine.backtest.schemas import BacktestResult
from src.engine.data.synthetic import SyntheticDataGenerator
from src.engine.data.synthetic_events import SyntheticEventGenerator
from src.engine.derivatives.overlay import DerivativesOverlayManager
from src.engine.events.schemas import EventFeatureRow
from src.engine.experts.registry import get_experts
from src.engine.experts.schemas import ExpertContext
from src.engine.expression.ml_selector import MLExpressionSelector
from src.engine.features.schemas import FeatureRow
from src.engine.meta.stacker import MetaStacker
from src.engine.portfolio.optimizer import PortfolioOptimizer
from src.engine.universe.registry import get_universe


COST_BPS = 5  # 5 basis points per trade


class WalkForwardBacktester:
    def __init__(
        self,
        data_gen: SyntheticDataGenerator | None = None,
        rebalance_freq: int = 5,
    ) -> None:
        self.data_gen = data_gen or SyntheticDataGenerator()
        self.rebalance_freq = rebalance_freq

    def run(
        self,
        returns: pd.DataFrame | None = None,
        feature_history: list[FeatureRow] | None = None,
        event_history: list[EventFeatureRow] | None = None,
    ) -> BacktestResult:
        # Generate data if not provided
        self.data_gen.load_prices()
        if returns is None:
            returns = self.data_gen.get_returns()
        if feature_history is None:
            feature_history = self.data_gen.generate_feature_history()
        if event_history is None:
            evt_gen = SyntheticEventGenerator(self.data_gen.event_manifest)
            dates = self.data_gen.get_dates()
            event_history = evt_gen.generate(dates[0], len(dates))

        # Setup components
        universe = get_universe()
        symbols = [inst.symbol for inst in universe]
        experts = get_experts()
        stacker = MetaStacker()
        selector = MLExpressionSelector(universe=universe)
        optimizer = PortfolioOptimizer(returns=returns, universe=universe)
        overlay_mgr = DerivativesOverlayManager()
        attribution = AttributionEngine()

        # Align dates
        dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
        feature_dates = {f.as_of_date: f for f in feature_history}
        event_dates = {e.as_of_date: e for e in event_history}

        # Walk-forward simulation
        equity = 1.0
        equity_curve = [equity]
        daily_returns: list[float] = []
        trades: list[dict] = []
        costs: list[float] = []
        current_weights: dict[str, float] = {}
        event_log: list[dict] = []

        for i, dt in enumerate(dates):
            if isinstance(dt, pd.Timestamp):
                dt = dt.date()

            # Daily P&L from held positions
            if current_weights:
                day_pnl = 0.0
                for sym, w in current_weights.items():
                    if sym in returns.columns and i < len(returns):
                        day_pnl += w * float(returns[sym].iloc[i])
                equity *= 1 + day_pnl
                daily_returns.append(day_pnl)
                equity_curve.append(equity)
            else:
                daily_returns.append(0.0)
                equity_curve.append(equity)

            # Rebalance at frequency
            if i % self.rebalance_freq != 0:
                overlay_mgr.tick_day()
                continue

            # Get features
            feat = feature_dates.get(dt)
            evt = event_dates.get(dt)
            if feat is None:
                continue

            # Run pipeline
            context = ExpertContext(
                as_of_date=dt,
                theme="macro",
                subtheme="all",
                feature_row=feat.values,
                event_features=evt.values if evt else {},
                universe=symbols,
            )

            predictions = [expert.predict(context) for expert in experts]
            meta_signal = stacker.combine(predictions)
            expression = selector.select(meta_signal)
            portfolio = optimizer.build_target(
                expression,
                regime=meta_signal.regime,
                signal_score=meta_signal.score,
            )
            overlay = overlay_mgr.build_overlay(meta_signal, portfolio)

            # Compute turnover cost
            all_syms = set(list(current_weights.keys()) + list(portfolio.weights.keys()))
            turnover = sum(
                abs(portfolio.weights.get(s, 0) - current_weights.get(s, 0))
                for s in all_syms
            )
            cost = turnover * COST_BPS / 10000
            costs.append(cost)
            equity -= cost

            # Record trade
            trade_record = {
                "date": str(dt),
                "weights": dict(portfolio.weights),
                "hedge_weights": dict(portfolio.hedge_weights),
                "overlay_type": overlay.overlay_type,
                "turnover": turnover,
                "cost": cost,
                "regime": meta_signal.regime,
            }
            trades.append(trade_record)

            attribution.log_trade(TradeRecord(
                date=str(dt),
                theme=meta_signal.theme,
                weights=dict(portfolio.weights),
                hedge_weights=dict(portfolio.hedge_weights),
                overlay_type=overlay.overlay_type,
                daily_pnl=daily_returns[-1] if daily_returns else 0.0,
                cost=cost,
            ))

            current_weights = dict(portfolio.weights)

            # Log events
            if evt and evt.values.get("event_intensity", 0) > 0.1:
                event_log.append({
                    "date": str(dt),
                    "intensity": evt.values.get("event_intensity", 0),
                    "theme": evt.theme,
                    "weights_after": dict(portfolio.weights),
                })

        # Compute final metrics
        sharpe = compute_sharpe(daily_returns)
        max_dd = compute_max_drawdown(equity_curve)
        drawdowns = compute_drawdowns(equity_curve)
        attr_decomp = attribution.decompose_returns()
        event_replay = attribution.event_replay(self.data_gen.event_manifest)

        return BacktestResult(
            returns=daily_returns,
            trades=trades,
            costs=costs,
            equity_curve=equity_curve,
            drawdowns=drawdowns,
            sharpe=sharpe,
            max_drawdown=max_dd,
            attribution=attr_decomp,
            event_log=event_log,
            metadata={
                "n_days": len(dates),
                "n_rebalances": len(trades),
                "final_equity": round(equity, 6),
                "hit_rate": compute_hit_rate(daily_returns),
                "total_costs": round(sum(costs), 6),
                "event_replay": event_replay,
            },
        )
