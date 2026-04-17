"""Slide 3: Event Timeline — strategy vs S&P with major event annotations."""
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

backtester = WalkForwardBacktester(data_gen=SyntheticDataGenerator(), rebalance_freq=25)
result = backtester.run(returns=returns, prices_df=prices_df, macro_df=macro_df, event_history=event_history)

# Extract data
dates = pd.to_datetime(result.dates)
strategy_eq = np.array(result.equity_curve)
spy_eq = np.array(result.benchmark_equity["SPY"])

n = min(len(dates), len(strategy_eq) - 1, len(spy_eq) - 1)
plot_dates = dates[:n]
strategy_eq = strategy_eq[:n + 1]
spy_eq = spy_eq[:n + 1]

# Colors
STRAT_COLOR = '#1e3a5f'
SPY_COLOR = '#6366f1'

# Major events — (date, label, y_frac, crash_start, crash_end)
# crash windows define the red shading period around each event
events = [
    ("2022-09-21", "Fed 75bps Hike", 0.95, "2022-08-15", "2022-10-15"),
    ("2022-11-15", "UK Gilt Crisis", 0.72, "2022-09-20", "2022-11-01"),
    ("2023-03-10", "SVB Collapse", 0.95, "2023-02-20", "2023-03-25"),
    ("2023-10-07", "Israel-Hamas", 0.72, "2023-09-15", "2023-11-01"),
    ("2024-01-12", "Red Sea Crisis", 0.95, "2024-01-02", "2024-02-01"),
    ("2024-08-05", "Carry Trade Unwind", 0.72, "2024-07-15", "2024-08-20"),
    ("2025-02-19", "Trump Tariffs", 0.95, "2025-02-10", "2025-04-01"),
]

# ── Build the chart ──
fig, ax = plt.subplots(figsize=(20, 6.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Plot equity curves
ax.plot(plot_dates, strategy_eq[1:], color=STRAT_COLOR, linewidth=2.8, label='Macro Event Strategy', zorder=3)
ax.plot(plot_dates, spy_eq[1:], color=SPY_COLOR, linewidth=2, alpha=0.75, label='S&P 500 (SPY)', zorder=2)

# Fill between
ax.fill_between(plot_dates, strategy_eq[1:], spy_eq[1:],
                where=strategy_eq[1:] >= spy_eq[1:],
                color=STRAT_COLOR, alpha=0.06, zorder=1)

# Set y limits with headroom for labels
y_min = min(np.min(strategy_eq[1:]), np.min(spy_eq[1:])) - 0.02
y_max = max(np.max(strategy_eq[1:]), np.max(spy_eq[1:])) + 0.15
ax.set_ylim(y_min, y_max)

# Event annotations with red crash shading
for event_date_str, label, y_frac, crash_start, crash_end in events:
    event_date = pd.Timestamp(event_date_str)
    idx = np.argmin(np.abs(plot_dates - event_date))
    actual_date = plot_dates[idx]

    # Red shading for the crash window
    ax.axvspan(pd.Timestamp(crash_start), pd.Timestamp(crash_end),
               color='#ef4444', alpha=0.08, zorder=0)

    # Red vertical line at event date
    ax.axvline(x=actual_date, color='#ef4444', linewidth=1.2, linestyle='-', alpha=0.4, zorder=1)

    # Label
    ax.annotate(label, xy=(actual_date, y_min + y_frac * (y_max - y_min)),
                fontsize=8.5, fontweight='bold', color='#991b1b',
                ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef2f2',
                         edgecolor='#ef4444', alpha=0.9, linewidth=0.8))

# Final annotations
final_strat = strategy_eq[-1]
final_spy = spy_eq[-1]
ax.annotate(f'+{(final_strat-1)*100:.1f}%', xy=(plot_dates[-1], final_strat),
            xytext=(15, 5), textcoords='offset points',
            color=STRAT_COLOR, fontsize=13, fontweight='bold')
ax.annotate(f'+{(final_spy-1)*100:.1f}%', xy=(plot_dates[-1], final_spy),
            xytext=(15, -5), textcoords='offset points',
            color=SPY_COLOR, fontsize=12, fontweight='bold')

# Formatting
ax.set_ylabel('Portfolio Value ($1 invested)', color='#333', fontsize=12)
ax.set_title('Navigating Macro Shocks: Strategy Performance Through Major Events',
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
ax.grid(True, alpha=0.15, color='#999')

legend = ax.legend(loc='upper left', fontsize=11, framealpha=0.95,
                   facecolor='white', edgecolor='#cccccc', labelcolor='#333',
                   bbox_to_anchor=(0.0, 0.82))

plt.tight_layout()
out = Path.home() / "Desktop" / "event_timeline.png"
plt.savefig(str(out), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('presentation/event_timeline.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved {out} and presentation/event_timeline.png")
