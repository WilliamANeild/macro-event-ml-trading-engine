from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.engine.backtest.attribution import AttributionEngine, TradeRecord
from src.engine.backtest.metrics import (
    compute_drawdowns,
    compute_hit_rate,
    compute_information_ratio,
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
from src.engine.features.builder import FeatureBuilder
from src.engine.features.schemas import FeatureRow
from src.engine.meta.regime_detector import RegimeDetector
from src.engine.meta.stacker import MetaStacker
from src.engine.portfolio.optimizer import PortfolioOptimizer
from src.engine.universe.registry import get_universe


COST_BPS = 5  # 5 basis points per trade


class WalkForwardBacktester:
    def __init__(
        self,
        data_gen: SyntheticDataGenerator | None = None,
        rebalance_freq: int = 10,
        retrain_interval: int | None = None,
    ) -> None:
        self.data_gen = data_gen or SyntheticDataGenerator()
        self.rebalance_freq = rebalance_freq
        self.retrain_interval = retrain_interval

    def run(
        self,
        returns: pd.DataFrame | None = None,
        feature_history: list[FeatureRow] | None = None,
        event_history: list[EventFeatureRow] | None = None,
        prices_df: pd.DataFrame | None = None,
        macro_df: pd.DataFrame | None = None,
    ) -> BacktestResult:
        # Generate data if not provided
        self.data_gen.load_prices()
        if returns is None:
            returns = self.data_gen.get_returns()

        # Build prices and macro DataFrames for FeatureBuilder
        if prices_df is None:
            prices_df = self.data_gen.get_prices_df()
        if macro_df is None:
            macro_df = self.data_gen.get_macro_df()
        feature_builder = FeatureBuilder()

        # Pre-build feature history using FeatureBuilder with rolling windows
        if feature_history is None:
            feature_history = []
            for i in range(20, len(returns)):
                dt = returns.index[i].date()
                # Only build features on rebalance dates to avoid unnecessary work
                if i % self.rebalance_freq != 0:
                    continue
                feat = feature_builder.build(
                    as_of_date=dt,
                    theme="macro",
                    subtheme="all",
                    prices=prices_df.iloc[: i + 1],
                    returns=returns.iloc[: i + 1],
                    macro=macro_df.iloc[: i + 1],
                )
                feature_history.append(feat)

        if event_history is None:
            evt_gen = SyntheticEventGenerator(self.data_gen.event_manifest)
            dates = self.data_gen.get_dates()
            event_history = evt_gen.generate(dates[0], len(dates))

        # Setup components — filter universe to tradeable symbols only
        full_universe = get_universe()
        tradeable = set(returns.columns)
        universe = [inst for inst in full_universe if inst.symbol in tradeable]
        symbols = [inst.symbol for inst in universe]
        experts = get_experts()
        regime_det = RegimeDetector()
        regime_det.fit(returns)
        stacker = MetaStacker(regime_detector=regime_det)
        stacker.set_recent_returns(returns)
        selector = MLExpressionSelector(universe=universe)
        selector.set_recent_returns(returns)
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
        rebalance_count: int = 0

        # Benchmark tracking
        spy_equity = 1.0
        bal_equity = 1.0  # 60/40 SPY/TLT
        spy_returns: list[float] = []
        bal_returns: list[float] = []
        spy_equity_curve = [1.0]
        bal_equity_curve = [1.0]
        has_spy = "SPY" in returns.columns
        has_tlt = "TLT" in returns.columns

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

            # Benchmark daily returns
            if has_spy and i < len(returns):
                spy_r = float(returns["SPY"].iloc[i])
            else:
                spy_r = 0.0
            if has_tlt and i < len(returns):
                tlt_r = float(returns["TLT"].iloc[i])
            else:
                tlt_r = 0.0
            bal_r = 0.6 * spy_r + 0.4 * tlt_r

            spy_returns.append(spy_r)
            bal_returns.append(bal_r)
            spy_equity *= 1 + spy_r
            bal_equity *= 1 + bal_r
            spy_equity_curve.append(spy_equity)
            bal_equity_curve.append(bal_equity)

            # Rebalance at frequency
            if i % self.rebalance_freq != 0:
                overlay_mgr.tick_day()
                continue

            # Periodic retraining of experts
            rebalance_count += 1
            if (
                self.retrain_interval is not None
                and rebalance_count % self.retrain_interval == 0
            ):
                experts = get_experts()
                regime_det = RegimeDetector()
                regime_det.fit(returns.iloc[:i])
                stacker = MetaStacker(regime_detector=regime_det)
                stacker.set_recent_returns(returns.iloc[:i])
                selector = MLExpressionSelector(universe=universe)
                optimizer = PortfolioOptimizer(
                    returns=returns.iloc[:i], universe=universe
                )

            # Update regime detector and momentum with latest returns window
            stacker.set_recent_returns(returns.iloc[: i + 1])
            selector.set_recent_returns(returns.iloc[: i + 1])

            # Get features
            feat = feature_dates.get(dt)
            evt = event_dates.get(dt)
            if feat is None:
                continue

            # Run pipeline – merge event features into feature_row so experts
            # can access event-driven keys (escalation_intensity, etc.) via
            # context.feature_row.get(...)
            evt_values = evt.values if evt else {}
            merged_features = {**feat.values, **evt_values}
            context = ExpertContext(
                as_of_date=dt,
                theme=evt.theme if evt and evt.theme != "none" else "macro",
                subtheme="all",
                feature_row=merged_features,
                event_features=evt_values,
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

            # Skip rebalance if portfolio barely changed — check both
            # raw turnover and directional similarity
            if current_weights and turnover < 0.08:
                # Cosine similarity between old and new weight vectors
                all_s = sorted(all_syms)
                old_vec = np.array([current_weights.get(s, 0) for s in all_s])
                new_vec = np.array([portfolio.weights.get(s, 0) for s in all_s])
                dot = float(old_vec @ new_vec)
                norms = float(np.linalg.norm(old_vec) * np.linalg.norm(new_vec))
                cos_sim = dot / norms if norms > 1e-10 else 0.0
                # Skip if portfolios are very similar (same direction, similar weights)
                if cos_sim > 0.85:
                    overlay_mgr.tick_day()
                    continue

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

        # Benchmark metrics
        spy_sharpe = compute_sharpe(spy_returns)
        bal_sharpe = compute_sharpe(bal_returns)
        spy_ir = compute_information_ratio(daily_returns, spy_returns)

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
            benchmark_returns={"SPY": spy_returns, "60_40": bal_returns},
            benchmark_equity={"SPY": spy_equity_curve, "60_40": bal_equity_curve},
            benchmark_sharpe={"SPY": spy_sharpe, "60_40": bal_sharpe},
            dates=[str(d) for d in dates],
            metadata={
                "n_days": len(dates),
                "n_rebalances": len(trades),
                "final_equity": round(equity, 6),
                "hit_rate": compute_hit_rate(daily_returns),
                "total_costs": round(sum(costs), 6),
                "event_replay": event_replay,
                "info_ratio_vs_spy": round(spy_ir, 4),
            },
        )
