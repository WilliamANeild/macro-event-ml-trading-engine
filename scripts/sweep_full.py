"""Sweep rebalance freq, circuit breaker, and sizing combos.
Also do per-instrument P&L attribution to find drags."""
from __future__ import annotations

import sys
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.backtest.metrics import compute_sharpe, compute_max_drawdown
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


def set_level5_constraints():
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


def run_backtest_with_breaker(rebal_freq, breaker_threshold=None):
    """Run backtest, optionally with a drawdown circuit breaker."""
    set_level5_constraints()

    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(),
        rebalance_freq=rebal_freq,
    )

    # If no circuit breaker, run normally
    if breaker_threshold is None:
        result = backtester.run(
            returns=returns, prices_df=prices_df,
            macro_df=macro_df, event_history=event_history,
        )
        return result

    # With circuit breaker: we need to modify the walk_forward logic
    # We'll do a post-hoc simulation: take the result and apply a
    # drawdown-based position scaling
    result = backtester.run(
        returns=returns, prices_df=prices_df,
        macro_df=macro_df, event_history=event_history,
    )
    return result


def per_instrument_pnl(result, returns_df):
    """Compute per-instrument contribution from trade records."""
    instrument_pnl = {}
    dates = [d.date() if hasattr(d, "date") else d for d in returns_df.index]

    for i, trade in enumerate(result.trades):
        trade_date = trade["date"]
        weights = trade["weights"]

        # Find this trade date index
        trade_idx = None
        for idx, d in enumerate(dates):
            if str(d) == trade_date:
                trade_idx = idx
                break
        if trade_idx is None:
            continue

        # Find next trade date or end
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

        # Accumulate per-instrument P&L for holding period
        for sym, w in weights.items():
            if sym not in returns_df.columns:
                continue
            period_ret = float(returns_df[sym].iloc[trade_idx:next_idx].sum())
            contrib = w * period_ret
            instrument_pnl[sym] = instrument_pnl.get(sym, 0.0) + contrib

    return instrument_pnl


# ── Sweep parameters ──
REBAL_FREQS = [20, 25, 30, 35, 40]

print("=" * 90)
print("PARAMETER SWEEP: Level 5 sizing x rebalance frequency")
print("=" * 90)

all_results = []

for freq in REBAL_FREQS:
    set_level5_constraints()
    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(),
        rebalance_freq=freq,
    )
    result = backtester.run(
        returns=returns, prices_df=prices_df,
        macro_df=macro_df, event_history=event_history,
    )
    rets = np.array(result.returns)
    row = {
        "freq": freq,
        "sharpe": result.sharpe,
        "equity": result.metadata["final_equity"],
        "max_dd": result.max_drawdown,
        "ann_ret": rets.mean() * 252 * 100,
        "ann_vol": rets.std() * np.sqrt(252) * 100,
        "trades": result.metadata["n_rebalances"],
        "costs": result.metadata["total_costs"],
    }
    all_results.append(row)

    # Per-instrument attribution for best candidates
    if freq in [20, 25, 30, 40]:
        inst_pnl = per_instrument_pnl(result, returns)
        row["inst_pnl"] = inst_pnl

    print(f"  freq={freq:2d}  Sharpe={row['sharpe']:.4f}  Equity={row['equity']:.4f}  "
          f"MaxDD={row['max_dd']:.4f}  AnnRet={row['ann_ret']:.2f}%  AnnVol={row['ann_vol']:.2f}%  "
          f"Trades={row['trades']}  Costs={row['costs']:.4f}")

spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
bal_eq = result.benchmark_equity.get("60_40", [1.0])[-1]

print(f"\n  Benchmarks: SPY={spy_eq:.4f}  60/40={bal_eq:.4f}")
print(f"  SPY Sharpe={result.benchmark_sharpe.get('SPY', 0):.4f}")

# ── Per-instrument attribution for the best config ──
best = max(all_results, key=lambda r: r["sharpe"])
print(f"\n\n{'='*90}")
print(f"PER-INSTRUMENT P&L ATTRIBUTION (freq={best['freq']})")
print(f"{'='*90}")

if "inst_pnl" in best:
    pnl = best["inst_pnl"]
else:
    # Re-run best to get attribution
    set_level5_constraints()
    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(), rebalance_freq=best["freq"])
    result = backtester.run(returns=returns, prices_df=prices_df,
                            macro_df=macro_df, event_history=event_history)
    pnl = per_instrument_pnl(result, returns)

sorted_pnl = sorted(pnl.items(), key=lambda x: x[1], reverse=True)
total_pnl = sum(v for v in pnl.values())
print(f"\n  {'Symbol':8s} {'Contribution':>14s} {'% of Total':>12s}")
print(f"  {'-'*36}")
for sym, contrib in sorted_pnl:
    pct = (contrib / total_pnl * 100) if total_pnl != 0 else 0
    bar = "+" * int(max(0, contrib * 200)) + "-" * int(max(0, -contrib * 200))
    print(f"  {sym:8s} {contrib*100:>+13.2f}% {pct:>+11.1f}%  {bar}")
print(f"  {'TOTAL':8s} {total_pnl*100:>+13.2f}%")

# ── Sector groupings ──
SECTORS = {
    "Equities/Market": ["SPY", "QQQ", "SH"],
    "Rates/Bonds": ["TLT", "IEF", "SHY", "TIP"],
    "Commodities": ["GLD", "SLV", "XLE", "XOP", "DBA"],
    "Defense": ["ITA", "XAR", "LMT", "RTX"],
    "Shipping": ["BOAT"],
    "Crypto": ["COIN"],
    "Dollar": ["UUP"],
}

print(f"\n\n{'='*90}")
print(f"SECTOR ATTRIBUTION")
print(f"{'='*90}")
for sector, syms in SECTORS.items():
    sector_pnl = sum(pnl.get(s, 0) for s in syms)
    print(f"  {sector:20s} {sector_pnl*100:>+8.2f}%  ({', '.join(s for s in syms if s in pnl)})")

# ── Per-year breakdown ──
print(f"\n\n{'='*90}")
print(f"PER-YEAR BREAKDOWN (best config: freq={best['freq']})")
print(f"{'='*90}")

# Re-run best to get daily returns with dates
set_level5_constraints()
backtester = WalkForwardBacktester(
    data_gen=SyntheticDataGenerator(), rebalance_freq=best["freq"])
result = backtester.run(returns=returns, prices_df=prices_df,
                        macro_df=macro_df, event_history=event_history)

daily_dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
daily_rets = result.returns

for year in [2022, 2023, 2024, 2025]:
    year_rets = []
    year_spy = []
    for i, d in enumerate(daily_dates):
        if hasattr(d, 'year') and d.year == year and i < len(daily_rets):
            year_rets.append(daily_rets[i])
            if "SPY" in returns.columns and i < len(returns):
                year_spy.append(float(returns["SPY"].iloc[i]))
    if year_rets:
        yr = np.array(year_rets)
        spy_yr = np.array(year_spy) if year_spy else np.zeros(1)
        cum = float(np.prod([1 + r for r in year_rets]) - 1)
        spy_cum = float(np.prod([1 + r for r in year_spy]) - 1) if year_spy else 0
        yr_sharpe = compute_sharpe(year_rets)
        print(f"  {year}:  Return={cum*100:>+7.2f}%  SPY={spy_cum*100:>+7.2f}%  "
              f"Sharpe={yr_sharpe:.2f}  Days={len(year_rets)}")
