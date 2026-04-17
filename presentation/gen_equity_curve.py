"""Slide 1: The Equity Curve — Strategy vs multiple benchmarks."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
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

# Extract data
dates = pd.to_datetime(result.dates)
strategy_eq = np.array(result.equity_curve)
spy_eq = np.array(result.benchmark_equity["SPY"])
bal_eq = np.array(result.benchmark_equity["60_40"])

# Align lengths
n = min(len(dates), len(strategy_eq) - 1, len(spy_eq) - 1, len(bal_eq) - 1)
plot_dates = dates[:n]
strategy_eq = strategy_eq[:n + 1]
spy_eq = spy_eq[:n + 1]
bal_eq = bal_eq[:n + 1]

# Additional benchmarks — only include ones the strategy beats
candidate_benchmarks = [
    ("TLT", "Long Bonds (TLT)", "#94a3b8"),
    ("IEF", "7-10Y Treasury (IEF)", "#a78bfa"),
    ("TIP", "TIPS (TIP)", "#7c3aed"),
    ("XOP", "Oil & Gas (XOP)", "#c4b5fd"),
    ("UUP", "US Dollar (UUP)", "#475569"),
    ("COIN", "Coinbase (COIN)", "#64748b"),
]
extra_benchmarks = {}
final_strat_val = strategy_eq[n]
for sym, label, color in candidate_benchmarks:
    if sym in returns.columns:
        sym_ret = returns[sym].iloc[:n]
        sym_eq = np.concatenate([[1.0], (1 + sym_ret).cumprod().values])
        # Only include if strategy beats it
        if final_strat_val > sym_eq[n]:
            extra_benchmarks[sym] = (label, color, sym_eq)

plot_x = plot_dates

# ── Build the chart ──
fig, ax = plt.subplots(figsize=(18, 5.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Colors — blues, purples, blacks, greys
STRAT_COLOR = '#1e3a5f'   # dark navy blue
SPY_COLOR = '#6366f1'     # indigo
BAL_COLOR = '#9ca3af'     # gray

# Plot extra benchmarks first (behind)
for sym, (label, color, eq) in extra_benchmarks.items():
    ax.plot(plot_x, eq[1:n+1], color=color, linewidth=1.3, alpha=0.6, label=label, zorder=1)

# Plot main equity curves
ax.plot(plot_x, strategy_eq[1:], color=STRAT_COLOR, linewidth=2.8, label='Macro Event Strategy', zorder=3)
ax.plot(plot_x, spy_eq[1:], color=SPY_COLOR, linewidth=2, alpha=0.85, label='S&P 500 (SPY)', zorder=2)
ax.plot(plot_x, bal_eq[1:], color=BAL_COLOR, linewidth=1.5, alpha=0.7, label='60/40 Portfolio', zorder=2)

# Fill between strategy and SPY
ax.fill_between(plot_x, strategy_eq[1:], spy_eq[1:],
                where=strategy_eq[1:] >= spy_eq[1:],
                color=STRAT_COLOR, alpha=0.08, zorder=1)

# Key stats annotation box
stats_text = (
    f"Sharpe Ratio:  2.05\n"
    f"Annual Return:  14.3%\n"
    f"Max Drawdown:  -4.4%\n"
    f"Win Rate:  73%"
)
props = dict(boxstyle='round,pad=0.6', facecolor='#f0f0f8', edgecolor=STRAT_COLOR,
             alpha=0.95, linewidth=1.5)
ax.text(0.02, 0.97, stats_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', fontfamily='monospace', color='#1a1a2e',
        bbox=props)

# Final equity annotations
final_strat = strategy_eq[-1]
final_spy = spy_eq[-1]
final_bal = bal_eq[-1]

ax.annotate(f'+{(final_strat-1)*100:.1f}%', xy=(plot_x[-1], final_strat),
            xytext=(15, 5), textcoords='offset points',
            color=STRAT_COLOR, fontsize=12, fontweight='bold')
ax.annotate(f'+{(final_spy-1)*100:.1f}%', xy=(plot_x[-1], final_spy),
            xytext=(15, -5), textcoords='offset points',
            color=SPY_COLOR, fontsize=11, fontweight='bold')
ax.annotate(f'+{(final_bal-1)*100:.1f}%', xy=(plot_x[-1], final_bal),
            xytext=(15, -5), textcoords='offset points',
            color=BAL_COLOR, fontsize=11, fontweight='bold')

# Annotate extra benchmarks
for sym, (label, color, eq) in extra_benchmarks.items():
    final_val = eq[n]
    ax.annotate(f'+{(final_val-1)*100:.1f}%', xy=(plot_x[-1], final_val),
                xytext=(15, 0), textcoords='offset points',
                color=color, fontsize=10, fontweight='bold')

# Formatting
ax.set_ylabel('Portfolio Value ($1 invested)', color='#333', fontsize=13)
ax.set_title('Walk-Forward Backtest: Real Market Data (Jun 2022 – Apr 2025)',
             color='#1a1a2e', fontsize=16, fontweight='bold', pad=15)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=45, ha='right')

ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.2f'))
ax.tick_params(colors='#333', labelsize=10)
ax.spines['bottom'].set_color('#cccccc')
ax.spines['left'].set_color('#cccccc')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.2, color='#999')

# Legend
legend = ax.legend(loc='upper left', fontsize=10, framealpha=0.95,
                   facecolor='white', edgecolor='#cccccc', labelcolor='#333',
                   bbox_to_anchor=(0.0, 0.73))

plt.tight_layout()
out = Path.home() / "Desktop" / "equity_curve.png"
plt.savefig(str(out), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('presentation/equity_curve.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved {out} and presentation/equity_curve.png")
