"""Sweep underweighting levels for drag instruments (SLV, XAR, BOAT, XLE).
Tests scaling their weights down by various factors post-optimization."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.backtest.metrics import compute_sharpe
from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator
from src.engine.portfolio import constraints as constraints_mod
from src.engine.portfolio import rebalance as rebalance_mod

CACHE_DIR = Path("data/real_cache")

prices_df = pd.read_parquet(CACHE_DIR / "prices_2022-06-01_2025-04-01.parquet")
returns = prices_df.pct_change().dropna()
macro_df = pd.read_parquet(CACHE_DIR / "macro_2022-06-01_2025-04-01.parquet")
macro_df = macro_df.reindex(returns.index).ffill().bfill()
prices_df = prices_df.reindex(returns.index).ffill()

dummy_config = SyntheticConfig(n_days=len(returns), n_shocks=12, shock_vol_mult=5.0, shock_mean_shift=-0.05)
dummy_gen = SyntheticDataGenerator(config=dummy_config)
dummy_gen.load_prices()
evt_gen = SyntheticEventGenerator(dummy_gen.event_manifest)
dates_list = [d.date() if hasattr(d, "date") else d for d in returns.index]
event_history = evt_gen.generate(dates_list[0], len(dates_list))

DRAG_SYMBOLS = {"SLV", "XAR", "BOAT", "XLE"}


def set_sizing(level="5"):
    """Set Level 5 sizing."""
    constraints_mod.PortfolioConstraints.__init__.__defaults__ = (
        0.55, -0.55, 3.0, 2.0, 1.2, 0.35,
    )
    constraints_mod.REGIME_CONSTRAINTS["normal"] = constraints_mod.PortfolioConstraints()
    constraints_mod.REGIME_CONSTRAINTS["crisis"] = constraints_mod.PortfolioConstraints(
        max_position=0.35, min_position=-0.35,
        max_gross_exposure=1.5, max_net_exposure=0.8,
        max_turnover=0.72, risk_target=0.20,
    )
    constraints_mod.REGIME_CONSTRAINTS["euphoria"] = constraints_mod.PortfolioConstraints(
        max_position=0.55, min_position=-0.55,
        max_gross_exposure=2.55, max_net_exposure=1.7,
        max_turnover=1.02, risk_target=0.30,
    )
    constraints_mod.REGIME_CONSTRAINTS["transition"] = constraints_mod.PortfolioConstraints(
        max_position=0.47, min_position=-0.47,
        max_gross_exposure=2.1, max_net_exposure=1.3,
        max_turnover=0.9, risk_target=0.245,
    )
    rebalance_mod.STATE_MULTIPLIER["IDLE"] = 0.95
    rebalance_mod.STATE_MULTIPLIER["IMPULSE_ONSET"] = 0.85
    rebalance_mod.STATE_MULTIPLIER["ACTIVE"] = 1.0
    rebalance_mod.STATE_MULTIPLIER["DECAY"] = 0.8
    rebalance_mod.STATE_MULTIPLIER["UNWIND"] = 0.4


def per_instrument_pnl(result, returns_df):
    instrument_pnl = {}
    dates = [d.date() if hasattr(d, "date") else d for d in returns_df.index]
    for i, trade in enumerate(result.trades):
        trade_date = trade["date"]
        weights = trade["weights"]
        trade_idx = None
        for idx, d in enumerate(dates):
            if str(d) == trade_date:
                trade_idx = idx
                break
        if trade_idx is None:
            continue
        if i + 1 < len(result.trades):
            next_trade_date = result.trades[i + 1]["date"]
            next_idx = None
            for idx, d in enumerate(dates):
                if str(d) == next_trade_date:
                    next_idx = idx
                    break
            if next_idx is None:
                next_idx = len(dates)
        else:
            next_idx = len(dates)
        for sym, w in weights.items():
            if sym not in returns_df.columns:
                continue
            period_ret = float(returns_df[sym].iloc[trade_idx:next_idx].sum())
            contrib = w * period_ret
            instrument_pnl[sym] = instrument_pnl.get(sym, 0.0) + contrib
    return instrument_pnl


# ── Underweight configurations ──
# Scale factor applied to drag instruments: 1.0 = no change, 0.0 = removed
CONFIGS = [
    {"name": "No underweight (baseline)", "drag_scale": 1.0},
    {"name": "10% underweight",           "drag_scale": 0.90},
    {"name": "20% underweight",           "drag_scale": 0.80},
    {"name": "30% underweight",           "drag_scale": 0.70},
    {"name": "40% underweight",           "drag_scale": 0.60},
    {"name": "50% underweight",           "drag_scale": 0.50},
    {"name": "60% underweight",           "drag_scale": 0.40},
    {"name": "70% underweight",           "drag_scale": 0.30},
    {"name": "80% underweight",           "drag_scale": 0.20},
    {"name": "Remove entirely",           "drag_scale": 0.00},
]

# We also test per-instrument removal to see which drag matters most
INDIVIDUAL_TESTS = [
    {"name": "Remove SLV only",  "remove": {"SLV"}},
    {"name": "Remove XAR only",  "remove": {"XAR"}},
    {"name": "Remove BOAT only", "remove": {"BOAT"}},
    {"name": "Remove XLE only",  "remove": {"XLE"}},
    {"name": "Remove SLV+XAR",  "remove": {"SLV", "XAR"}},
    {"name": "Remove SLV+XAR+BOAT", "remove": {"SLV", "XAR", "BOAT"}},
]

# Test at both freq=35 (beats SPY) and freq=40 (best Sharpe)
for freq in [35, 40]:
    print(f"\n{'='*95}")
    print(f"REBALANCE FREQ = {freq}")
    print(f"{'='*95}")
    print(f"  {'Config':30s} {'Sharpe':>8s} {'Equity':>8s} {'MaxDD':>8s} {'AnnRet':>8s} {'AnnVol':>8s} {'vsSPY':>8s}")
    print(f"  {'-'*82}")

    for cfg in CONFIGS:
        set_sizing()
        scale = cfg["drag_scale"]

        # Modify returns: scale drag instrument returns to simulate underweighting
        # Actually, we need to modify the portfolio weights, not returns.
        # The cleanest way: post-process trades to scale drag weights.
        # But since the optimizer is integrated, let's modify the returns df
        # to reduce the available signal for drag instruments.
        # Better approach: create modified returns where drag columns are kept
        # but we'll monkey-patch the portfolio optimizer to scale them down.

        # Simplest approach: scale the drag instruments' columns in the
        # prices/returns passed to the expression selector / optimizer.
        # This won't actually work cleanly. Instead, let's just remove
        # them from the returns df if scale=0, or pass a modified returns.

        if scale == 0.0:
            mod_returns = returns.drop(columns=[c for c in DRAG_SYMBOLS if c in returns.columns])
            mod_prices = prices_df.drop(columns=[c for c in DRAG_SYMBOLS if c in prices_df.columns])
        elif scale < 1.0:
            # Keep them in universe but scale their allocation weight in
            # expression selector output. We'll monkey-patch the walk_forward
            # to apply weight scaling after portfolio construction.
            mod_returns = returns.copy()
            mod_prices = prices_df.copy()
        else:
            mod_returns = returns
            mod_prices = prices_df

        backtester = WalkForwardBacktester(
            data_gen=SyntheticDataGenerator(), rebalance_freq=freq)

        if 0.0 < scale < 1.0:
            # Patch: after each portfolio is built, scale drag weights
            orig_run = backtester.run

            def make_patched_run(bt, sc):
                def patched_run(**kwargs):
                    result = orig_run(**kwargs)
                    # Scale drag weights in trade records (for display)
                    # The actual P&L is already computed, so we need a deeper patch.
                    return result
                return patched_run

            # Actually, the cleanest way to underweight is to reduce these
            # instruments' exposure scores in the expression selector.
            # Let's just cap their max position in the optimizer.
            # Monkey-patch constraints to have lower caps for drags.
            from src.engine.portfolio.optimizer import PortfolioOptimizer
            orig_build = PortfolioOptimizer.build_target

            def make_patched_build(sc):
                def patched_build(self, decision, regime="normal", signal_score=0.5):
                    # Scale drag instrument weights in the decision
                    new_weights = {}
                    for sym, w in decision.weights.items():
                        if sym in DRAG_SYMBOLS:
                            new_weights[sym] = w * sc
                        else:
                            new_weights[sym] = w
                    from src.engine.expression.schemas import ExpressionDecision
                    mod_decision = ExpressionDecision(
                        as_of_date=decision.as_of_date,
                        theme=decision.theme,
                        subtheme=decision.subtheme,
                        expression_type=decision.expression_type,
                        target_symbols=decision.target_symbols,
                        weights=new_weights,
                        confidence=decision.confidence,
                        hedge_fraction=decision.hedge_fraction,
                        regime=decision.regime,
                    )
                    return orig_build(self, mod_decision, regime=regime, signal_score=signal_score)
                return patched_build

            PortfolioOptimizer.build_target = make_patched_build(scale)

        result = backtester.run(
            returns=mod_returns, prices_df=mod_prices,
            macro_df=macro_df, event_history=event_history,
        )

        # Restore original
        if 0.0 < scale < 1.0:
            PortfolioOptimizer.build_target = orig_build

        rets = np.array(result.returns)
        spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
        eq = result.metadata["final_equity"]
        vs_spy = eq - spy_eq

        print(f"  {cfg['name']:30s} {result.sharpe:>8.4f} {eq:>8.4f} "
              f"{result.max_drawdown:>8.4f} {rets.mean()*252*100:>7.2f}% "
              f"{rets.std()*np.sqrt(252)*100:>7.2f}% {vs_spy:>+8.4f}")

    # Individual instrument removal tests
    print(f"\n  {'--- Individual removals ---':30s}")
    print(f"  {'Config':30s} {'Sharpe':>8s} {'Equity':>8s} {'MaxDD':>8s} {'AnnRet':>8s} {'AnnVol':>8s} {'vsSPY':>8s}")
    print(f"  {'-'*82}")

    for cfg in INDIVIDUAL_TESTS:
        set_sizing()
        remove_set = cfg["remove"]
        mod_returns = returns.drop(columns=[c for c in remove_set if c in returns.columns])
        mod_prices = prices_df.drop(columns=[c for c in remove_set if c in prices_df.columns])

        backtester = WalkForwardBacktester(
            data_gen=SyntheticDataGenerator(), rebalance_freq=freq)
        result = backtester.run(
            returns=mod_returns, prices_df=mod_prices,
            macro_df=macro_df, event_history=event_history,
        )

        rets = np.array(result.returns)
        spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
        eq = result.metadata["final_equity"]
        vs_spy = eq - spy_eq

        print(f"  {cfg['name']:30s} {result.sharpe:>8.4f} {eq:>8.4f} "
              f"{result.max_drawdown:>8.4f} {rets.mean()*252*100:>7.2f}% "
              f"{rets.std()*np.sqrt(252)*100:>7.2f}% {vs_spy:>+8.4f}")

    # Per-instrument P&L for best underweight config
    print(f"\n  Per-instrument P&L (50% underweight, freq={freq}):")
    set_sizing()
    from src.engine.portfolio.optimizer import PortfolioOptimizer
    orig_build2 = PortfolioOptimizer.build_target

    def make_pb2(sc):
        def pb(self, decision, regime="normal", signal_score=0.5):
            new_weights = {}
            for sym, w in decision.weights.items():
                if sym in DRAG_SYMBOLS:
                    new_weights[sym] = w * sc
                else:
                    new_weights[sym] = w
            from src.engine.expression.schemas import ExpressionDecision
            mod_decision = ExpressionDecision(
                as_of_date=decision.as_of_date, theme=decision.theme,
                subtheme=decision.subtheme, expression_type=decision.expression_type,
                target_symbols=decision.target_symbols, weights=new_weights,
                confidence=decision.confidence, hedge_fraction=decision.hedge_fraction,
                regime=decision.regime,
            )
            return orig_build2(self, mod_decision, regime=regime, signal_score=signal_score)
        return pb

    PortfolioOptimizer.build_target = make_pb2(0.5)
    backtester = WalkForwardBacktester(data_gen=SyntheticDataGenerator(), rebalance_freq=freq)
    result = backtester.run(returns=returns, prices_df=prices_df, macro_df=macro_df, event_history=event_history)
    PortfolioOptimizer.build_target = orig_build2

    pnl = per_instrument_pnl(result, returns)
    sorted_pnl = sorted(pnl.items(), key=lambda x: x[1], reverse=True)
    for sym, contrib in sorted_pnl:
        print(f"    {sym:8s} {contrib*100:>+8.2f}%")
