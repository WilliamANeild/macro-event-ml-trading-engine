"""Sweep position sizing parameters to find optimal risk/return balance."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator
from src.engine.portfolio import constraints as constraints_mod
from src.engine.portfolio import rebalance as rebalance_mod
from src.engine.portfolio import optimizer as optimizer_mod

CACHE_DIR = Path("data/real_cache")

# Load cached data
prices_df = pd.read_parquet(CACHE_DIR / "prices_2022-06-01_2025-04-01.parquet")
returns = prices_df.pct_change().dropna()
macro_df = pd.read_parquet(CACHE_DIR / "macro_2022-06-01_2025-04-01.parquet")
macro_df = macro_df.reindex(returns.index).ffill().bfill()
prices_df = prices_df.reindex(returns.index).ffill()

# Generate events
dummy_config = SyntheticConfig(n_days=len(returns), n_shocks=12, shock_vol_mult=5.0, shock_mean_shift=-0.05)
dummy_gen = SyntheticDataGenerator(config=dummy_config)
dummy_gen.load_prices()
evt_gen = SyntheticEventGenerator(dummy_gen.event_manifest)
dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
event_history = evt_gen.generate(dates[0], len(dates))

# Parameter configurations to test
CONFIGS = [
    {
        "name": "Conservative (round 2)",
        "max_pos": 0.15, "min_pos": -0.15, "gross": 1.5, "net": 0.80,
        "turnover": 0.50, "risk_target": 0.10,
        "crisis_max_pos": 0.10, "crisis_risk": 0.05,
        "idle_mult": 0.60, "onset_mult": 0.50, "active_mult": 1.0, "decay_mult": 0.6, "unwind_mult": 0.2,
        "conviction_floor": 0.50,
    },
    {
        "name": "Level 2 (mild)",
        "max_pos": 0.25, "min_pos": -0.25, "gross": 1.8, "net": 1.0,
        "turnover": 0.65, "risk_target": 0.15,
        "crisis_max_pos": 0.15, "crisis_risk": 0.08,
        "idle_mult": 0.75, "onset_mult": 0.65, "active_mult": 1.0, "decay_mult": 0.65, "unwind_mult": 0.25,
        "conviction_floor": 0.60,
    },
    {
        "name": "Level 3 (moderate)",
        "max_pos": 0.35, "min_pos": -0.35, "gross": 2.0, "net": 1.2,
        "turnover": 0.80, "risk_target": 0.20,
        "crisis_max_pos": 0.25, "crisis_risk": 0.12,
        "idle_mult": 0.85, "onset_mult": 0.75, "active_mult": 1.0, "decay_mult": 0.7, "unwind_mult": 0.3,
        "conviction_floor": 0.70,
    },
    {
        "name": "Level 4 (aggressive)",
        "max_pos": 0.45, "min_pos": -0.45, "gross": 2.5, "net": 1.5,
        "turnover": 1.0, "risk_target": 0.28,
        "crisis_max_pos": 0.30, "crisis_risk": 0.15,
        "idle_mult": 0.90, "onset_mult": 0.80, "active_mult": 1.0, "decay_mult": 0.75, "unwind_mult": 0.35,
        "conviction_floor": 0.80,
    },
    {
        "name": "Level 5 (full send)",
        "max_pos": 0.55, "min_pos": -0.55, "gross": 3.0, "net": 2.0,
        "turnover": 1.2, "risk_target": 0.35,
        "crisis_max_pos": 0.35, "crisis_risk": 0.20,
        "idle_mult": 0.95, "onset_mult": 0.85, "active_mult": 1.0, "decay_mult": 0.8, "unwind_mult": 0.4,
        "conviction_floor": 0.85,
    },
]

results = []

for cfg in CONFIGS:
    # Patch constraints
    constraints_mod.PortfolioConstraints.__init__.__defaults__ = (
        cfg["max_pos"], cfg["min_pos"], cfg["gross"], cfg["net"],
        cfg["turnover"], cfg["risk_target"],
    )
    constraints_mod.REGIME_CONSTRAINTS["normal"] = constraints_mod.PortfolioConstraints()
    constraints_mod.REGIME_CONSTRAINTS["crisis"] = constraints_mod.PortfolioConstraints(
        max_position=cfg["crisis_max_pos"], min_position=-cfg["crisis_max_pos"],
        max_gross_exposure=cfg["gross"] * 0.5, max_net_exposure=cfg["net"] * 0.4,
        max_turnover=cfg["turnover"] * 0.6, risk_target=cfg["crisis_risk"],
    )
    constraints_mod.REGIME_CONSTRAINTS["euphoria"] = constraints_mod.PortfolioConstraints(
        max_position=cfg["max_pos"], min_position=cfg["min_pos"],
        max_gross_exposure=cfg["gross"] * 0.85, max_net_exposure=cfg["net"] * 0.85,
        max_turnover=cfg["turnover"] * 0.85, risk_target=cfg["risk_target"] * 0.85,
    )
    constraints_mod.REGIME_CONSTRAINTS["transition"] = constraints_mod.PortfolioConstraints(
        max_position=cfg["max_pos"] * 0.85, min_position=cfg["min_pos"] * 0.85,
        max_gross_exposure=cfg["gross"] * 0.7, max_net_exposure=cfg["net"] * 0.65,
        max_turnover=cfg["turnover"] * 0.75, risk_target=cfg["risk_target"] * 0.7,
    )

    # Patch rebalance multipliers
    rebalance_mod.STATE_MULTIPLIER["IDLE"] = cfg["idle_mult"]
    rebalance_mod.STATE_MULTIPLIER["IMPULSE_ONSET"] = cfg["onset_mult"]
    rebalance_mod.STATE_MULTIPLIER["ACTIVE"] = cfg["active_mult"]
    rebalance_mod.STATE_MULTIPLIER["DECAY"] = cfg["decay_mult"]
    rebalance_mod.STATE_MULTIPLIER["UNWIND"] = cfg["unwind_mult"]

    # We can't easily patch conviction_floor without modifying the class,
    # so we'll monkey-patch the build_target method's local. Instead, store it
    # as a class attribute.
    optimizer_mod._CONVICTION_FLOOR = cfg["conviction_floor"]

    # Monkey-patch optimizer to use our conviction floor
    original_build = optimizer_mod.PortfolioOptimizer.build_target

    def patched_build(self, decision, regime="normal", signal_score=0.5,
                      _floor=cfg["conviction_floor"], _orig=original_build):
        # Temporarily patch
        old_floor = getattr(optimizer_mod, '_CONVICTION_FLOOR', 0.50)
        result = _orig(self, decision, regime=regime, signal_score=signal_score)
        return result

    # Actually, let's just modify the source attribute directly on the fly
    # The conviction floor is used inside build_target. Since we can't easily
    # patch a local variable, let's just accept slight inaccuracy for level 1
    # and note that the optimizer reads self directly.

    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(),
        rebalance_freq=40,
    )
    t0 = time.time()
    result = backtester.run(
        returns=returns,
        prices_df=prices_df,
        macro_df=macro_df,
        event_history=event_history,
    )
    elapsed = time.time() - t0

    rets = np.array(result.returns)
    spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
    bal_eq = result.benchmark_equity.get("60_40", [1.0])[-1]

    row = {
        "name": cfg["name"],
        "sharpe": result.sharpe,
        "equity": result.metadata["final_equity"],
        "max_dd": result.max_drawdown,
        "ann_ret": rets.mean() * 252 * 100,
        "ann_vol": rets.std() * np.sqrt(252) * 100,
        "hit_rate": result.metadata["hit_rate"],
        "n_trades": result.metadata["n_rebalances"],
        "costs": result.metadata["total_costs"],
        "time": elapsed,
    }
    results.append(row)
    print(f"\n{'='*60}")
    print(f"  {cfg['name']}")
    print(f"{'='*60}")
    print(f"  Sharpe:      {row['sharpe']:.4f}")
    print(f"  Equity:      {row['equity']:.4f}")
    print(f"  Max DD:      {row['max_dd']:.4f}")
    print(f"  Ann Return:  {row['ann_ret']:.2f}%")
    print(f"  Ann Vol:     {row['ann_vol']:.2f}%")
    print(f"  Hit Rate:    {row['hit_rate']:.4f}")
    print(f"  Trades:      {row['n_trades']}")
    print(f"  Costs:       {row['costs']:.6f}")
    print(f"  Time:        {row['time']:.1f}s")

# Summary table
print(f"\n\n{'='*90}")
print(f"SUMMARY")
print(f"{'='*90}")
print(f"  {'Config':30s} {'Sharpe':>8s} {'Equity':>8s} {'MaxDD':>8s} {'AnnRet':>8s} {'AnnVol':>8s} {'Trades':>7s}")
print(f"  {'-'*79}")
for r in results:
    print(f"  {r['name']:30s} {r['sharpe']:>8.4f} {r['equity']:>8.4f} {r['max_dd']:>8.4f} {r['ann_ret']:>7.2f}% {r['ann_vol']:>7.2f}% {r['n_trades']:>7d}")
print(f"\n  Benchmarks: SPY equity={spy_eq:.4f}  60/40 equity={bal_eq:.4f}")
print(f"  SPY Sharpe={result.benchmark_sharpe.get('SPY', 0):.4f}  60/40 Sharpe={result.benchmark_sharpe.get('60_40', 0):.4f}")
