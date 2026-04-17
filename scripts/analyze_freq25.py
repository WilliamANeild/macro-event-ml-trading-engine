"""Deep analysis of freq=25 configuration — per-instrument, per-year,
per-trade, regime, and monthly breakdown."""
from __future__ import annotations

import sys
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.backtest.metrics import compute_sharpe, compute_max_drawdown
from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator

CACHE_DIR = Path("data/real_cache")

prices_df = pd.read_parquet(CACHE_DIR / "prices_2022-06-01_2025-04-01.parquet")
for sym in ["XAR", "BOAT", "XLE"]:
    if sym in prices_df.columns:
        prices_df = prices_df.drop(columns=[sym])

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

# Run backtest
backtester = WalkForwardBacktester(data_gen=SyntheticDataGenerator(), rebalance_freq=25)
result = backtester.run(returns=returns, prices_df=prices_df, macro_df=macro_df, event_history=event_history)

daily_dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
rets = np.array(result.returns)

# ═══════════════════════════════════════════════════════
# 1. PER-INSTRUMENT P&L ATTRIBUTION
# ═══════════════════════════════════════════════════════
print("=" * 80)
print("1. PER-INSTRUMENT P&L ATTRIBUTION")
print("=" * 80)

instrument_pnl = defaultdict(float)
instrument_gross_weight = defaultdict(float)
instrument_trade_count = defaultdict(int)

for i, trade in enumerate(result.trades):
    trade_date = trade["date"]
    weights = trade["weights"]
    trade_idx = None
    for idx, d in enumerate(daily_dates):
        if str(d) == trade_date:
            trade_idx = idx
            break
    if trade_idx is None:
        continue

    if i + 1 < len(result.trades):
        next_date = result.trades[i + 1]["date"]
        next_idx = None
        for idx, d in enumerate(daily_dates):
            if str(d) == next_date:
                next_idx = idx
                break
        if next_idx is None:
            next_idx = len(daily_dates)
    else:
        next_idx = len(daily_dates)

    for sym, w in weights.items():
        if sym not in returns.columns:
            continue
        period_ret = float(returns[sym].iloc[trade_idx:next_idx].sum())
        contrib = w * period_ret
        instrument_pnl[sym] += contrib
        instrument_gross_weight[sym] += abs(w)
        instrument_trade_count[sym] += 1

sorted_pnl = sorted(instrument_pnl.items(), key=lambda x: x[1], reverse=True)
total_pnl = sum(v for v in instrument_pnl.values())

print(f"\n  {'Symbol':8s} {'Contrib':>10s} {'AvgWt':>8s} {'Trades':>7s} {'PnL/Trade':>10s}")
print(f"  {'-'*46}")
for sym, contrib in sorted_pnl:
    avg_wt = instrument_gross_weight[sym] / max(instrument_trade_count[sym], 1)
    pnl_per = contrib / max(instrument_trade_count[sym], 1)
    flag = " ***" if contrib < -0.01 else (" ++++" if contrib > 0.05 else "")
    print(f"  {sym:8s} {contrib*100:>+9.2f}% {avg_wt:>7.3f} {instrument_trade_count[sym]:>7d} {pnl_per*100:>+9.3f}%{flag}")
print(f"  {'TOTAL':8s} {total_pnl*100:>+9.2f}%")

# ═══════════════════════════════════════════════════════
# 2. PER-YEAR BREAKDOWN
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("2. PER-YEAR BREAKDOWN")
print("=" * 80)

for year in [2022, 2023, 2024, 2025]:
    yr_rets = []
    yr_spy = []
    yr_bal = []
    for i, d in enumerate(daily_dates):
        if hasattr(d, 'year') and d.year == year and i < len(result.returns):
            yr_rets.append(result.returns[i])
            if "SPY" in returns.columns and i < len(returns):
                yr_spy.append(float(returns["SPY"].iloc[i]))
            if "TLT" in returns.columns and "SPY" in returns.columns and i < len(returns):
                yr_bal.append(0.6 * float(returns["SPY"].iloc[i]) + 0.4 * float(returns["TLT"].iloc[i]))
    if yr_rets:
        cum = float(np.prod([1 + r for r in yr_rets]) - 1)
        spy_cum = float(np.prod([1 + r for r in yr_spy]) - 1) if yr_spy else 0
        bal_cum = float(np.prod([1 + r for r in yr_bal]) - 1) if yr_bal else 0
        yr_sharpe = compute_sharpe(yr_rets)
        eq_curve = [1.0]
        for r in yr_rets:
            eq_curve.append(eq_curve[-1] * (1 + r))
        yr_dd = compute_max_drawdown(eq_curve)
        print(f"\n  {year}:")
        print(f"    Strategy:  {cum*100:>+7.2f}%  Sharpe={yr_sharpe:.2f}  MaxDD={yr_dd:.3f}  Days={len(yr_rets)}")
        print(f"    SPY:       {spy_cum*100:>+7.2f}%")
        print(f"    60/40:     {bal_cum*100:>+7.2f}%")
        print(f"    vs SPY:    {(cum-spy_cum)*100:>+7.2f}%")

# ═══════════════════════════════════════════════════════
# 3. PER-TRADE ANALYSIS
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("3. PER-TRADE P&L")
print("=" * 80)

trade_pnls = []
for i, trade in enumerate(result.trades):
    trade_date = trade["date"]
    trade_idx = None
    for idx, d in enumerate(daily_dates):
        if str(d) == trade_date:
            trade_idx = idx
            break
    if trade_idx is None:
        continue

    if i + 1 < len(result.trades):
        next_date = result.trades[i + 1]["date"]
        next_idx = None
        for idx, d in enumerate(daily_dates):
            if str(d) == next_date:
                next_idx = idx
                break
        if next_idx is None:
            next_idx = len(daily_dates)
    else:
        next_idx = len(daily_dates)

    holding_days = next_idx - trade_idx
    period_pnl = sum(result.returns[j] for j in range(trade_idx, min(next_idx, len(result.returns))))
    trade_pnls.append({
        "date": trade_date,
        "regime": trade["regime"],
        "turnover": trade["turnover"],
        "cost": trade["cost"],
        "holding_days": holding_days,
        "period_pnl": period_pnl,
        "top_weights": {k: v for k, v in sorted(trade["weights"].items(), key=lambda x: abs(x[1]), reverse=True)[:5]},
    })

print(f"\n  {'Date':12s} {'Regime':12s} {'Days':>5s} {'PnL':>8s} {'Turnover':>9s} {'Cost':>8s} {'Top Positions'}")
print(f"  {'-'*90}")
for t in trade_pnls:
    top = ", ".join(f"{k}:{v:+.2f}" for k, v in t["top_weights"].items())
    flag = " <-- LOSS" if t["period_pnl"] < -0.005 else ""
    print(f"  {t['date']:12s} {t['regime']:12s} {t['holding_days']:>5d} {t['period_pnl']*100:>+7.2f}% {t['turnover']:>9.3f} {t['cost']*100:>7.3f}% {top}{flag}")

winners = sum(1 for t in trade_pnls if t["period_pnl"] > 0)
losers = len(trade_pnls) - winners
avg_win = np.mean([t["period_pnl"] for t in trade_pnls if t["period_pnl"] > 0]) if winners else 0
avg_loss = np.mean([t["period_pnl"] for t in trade_pnls if t["period_pnl"] <= 0]) if losers else 0
print(f"\n  Winners: {winners}/{len(trade_pnls)} ({winners/len(trade_pnls)*100:.0f}%)")
print(f"  Avg win:  {avg_win*100:+.3f}%")
print(f"  Avg loss: {avg_loss*100:+.3f}%")
print(f"  Win/loss ratio: {abs(avg_win/avg_loss):.2f}x" if avg_loss != 0 else "")

# ═══════════════════════════════════════════════════════
# 4. REGIME ANALYSIS
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("4. REGIME PERFORMANCE")
print("=" * 80)

regime_pnls = defaultdict(list)
for t in trade_pnls:
    regime_pnls[t["regime"]].append(t["period_pnl"])

print(f"\n  {'Regime':15s} {'Trades':>7s} {'TotalPnL':>10s} {'AvgPnL':>10s} {'WinRate':>9s}")
print(f"  {'-'*53}")
for regime, pnls in sorted(regime_pnls.items()):
    total = sum(pnls)
    avg = np.mean(pnls)
    wr = sum(1 for p in pnls if p > 0) / len(pnls)
    print(f"  {regime:15s} {len(pnls):>7d} {total*100:>+9.2f}% {avg*100:>+9.3f}% {wr*100:>8.0f}%")

# ═══════════════════════════════════════════════════════
# 5. MONTHLY RETURNS HEATMAP
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("5. MONTHLY RETURNS")
print("=" * 80)

monthly = defaultdict(float)
for i, d in enumerate(daily_dates):
    if i < len(result.returns):
        key = (d.year, d.month)
        monthly[key] += result.returns[i]

print(f"\n  {'':>6s}", end="")
for m in range(1, 13):
    print(f"  {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[m-1]:>6s}", end="")
print(f"  {'Total':>7s}")
print(f"  {'-'*92}")

for year in [2022, 2023, 2024, 2025]:
    print(f"  {year:>5d}", end="")
    yr_total = 0
    for m in range(1, 13):
        val = monthly.get((year, m))
        if val is not None:
            print(f"  {val*100:>+5.1f}%", end="")
            yr_total += val
        else:
            print(f"  {'---':>6s}", end="")
    print(f"  {yr_total*100:>+6.1f}%")

# ═══════════════════════════════════════════════════════
# 6. DIRECTION ANALYSIS
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("6. LONG vs SHORT CONTRIBUTION")
print("=" * 80)

long_pnl = 0.0
short_pnl = 0.0
long_weight = 0.0
short_weight = 0.0

for i, trade in enumerate(result.trades):
    trade_date = trade["date"]
    trade_idx = None
    for idx, d in enumerate(daily_dates):
        if str(d) == trade_date:
            trade_idx = idx
            break
    if trade_idx is None:
        continue
    if i + 1 < len(result.trades):
        next_date = result.trades[i + 1]["date"]
        next_idx = None
        for idx, d in enumerate(daily_dates):
            if str(d) == next_date:
                next_idx = idx
                break
        if next_idx is None:
            next_idx = len(daily_dates)
    else:
        next_idx = len(daily_dates)

    for sym, w in trade["weights"].items():
        if sym not in returns.columns:
            continue
        period_ret = float(returns[sym].iloc[trade_idx:next_idx].sum())
        contrib = w * period_ret
        if w > 0:
            long_pnl += contrib
            long_weight += w
        else:
            short_pnl += contrib
            short_weight += abs(w)

n_trades = len(result.trades) or 1
print(f"\n  Long side:   PnL={long_pnl*100:>+8.2f}%  Avg weight={long_weight/n_trades:.3f}")
print(f"  Short side:  PnL={short_pnl*100:>+8.2f}%  Avg weight={short_weight/n_trades:.3f}")
print(f"  Net:         PnL={(long_pnl+short_pnl)*100:>+8.2f}%")

# ═══════════════════════════════════════════════════════
# 7. COST ANALYSIS
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("7. COST ANALYSIS")
print("=" * 80)
total_costs = sum(t["cost"] for t in trade_pnls)
gross_return = total_pnl + total_costs
print(f"\n  Gross return:  {gross_return*100:>+8.2f}%")
print(f"  Total costs:   {total_costs*100:>8.2f}%")
print(f"  Net return:    {total_pnl*100:>+8.2f}%")
print(f"  Cost drag:     {total_costs/gross_return*100:.1f}% of gross" if gross_return > 0 else "")
print(f"  Avg turnover:  {np.mean([t['turnover'] for t in trade_pnls]):.3f}")

# ═══════════════════════════════════════════════════════
# 8. WORST DRAWDOWN PERIODS
# ═══════════════════════════════════════════════════════
print(f"\n\n{'=' * 80}")
print("8. DRAWDOWN ANALYSIS")
print("=" * 80)

eq = [1.0]
for r in result.returns:
    eq.append(eq[-1] * (1 + r))

peak = eq[0]
drawdowns = []
dd_start = 0
in_dd = False
for i in range(1, len(eq)):
    if eq[i] > peak:
        if in_dd and (peak - eq[i-1]) / peak > 0.005:
            drawdowns.append({
                "start": str(daily_dates[dd_start]) if dd_start < len(daily_dates) else "?",
                "trough": str(daily_dates[i-1]) if i-1 < len(daily_dates) else "?",
                "end": str(daily_dates[i-1]) if i-1 < len(daily_dates) else "?",
                "depth": (min(eq[dd_start:i]) - peak) / peak,
                "duration": i - dd_start,
            })
        peak = eq[i]
        dd_start = i
        in_dd = False
    elif eq[i] < peak:
        in_dd = True

# Check if we end in a drawdown
if in_dd:
    drawdowns.append({
        "start": str(daily_dates[dd_start]) if dd_start < len(daily_dates) else "?",
        "trough": "ongoing",
        "depth": (min(eq[dd_start:]) - peak) / peak,
        "duration": len(eq) - dd_start,
    })

drawdowns.sort(key=lambda x: x["depth"])
print(f"\n  Top drawdown periods:")
for dd in drawdowns[:5]:
    print(f"    Start={dd['start']}  Depth={dd['depth']*100:.2f}%  Duration={dd['duration']} days")
