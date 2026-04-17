"""Slide 4: By the Numbers — clean performance dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

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
all_dates = pd.to_datetime(result.dates)
strategy_eq = np.array(result.equity_curve)
spy_eq = np.array(result.benchmark_equity["SPY"])
bal_eq = np.array(result.benchmark_equity["60_40"])

n = min(len(all_dates), len(strategy_eq) - 1)
all_dates = all_dates[:n]
strategy_eq = strategy_eq[:n + 1]
spy_eq = spy_eq[:n + 1]
bal_eq = bal_eq[:n + 1]

strat_daily = np.diff(strategy_eq) / strategy_eq[:-1]
spy_daily = np.diff(spy_eq) / spy_eq[:-1]

# Colors
STRAT_COLOR = '#1e3a5f'
SPY_COLOR = '#6366f1'
ACCENT = '#ef4444'

# ── Compute stats ──
total_ret = (strategy_eq[-1] / strategy_eq[0] - 1) * 100
spy_total_ret = (spy_eq[-1] / spy_eq[0] - 1) * 100
n_years = len(all_dates) / 252
ann_ret = ((strategy_eq[-1] / strategy_eq[0]) ** (1 / n_years) - 1) * 100
ann_vol = np.std(strat_daily) * np.sqrt(252) * 100
sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
spy_ann_vol = np.std(spy_daily) * np.sqrt(252) * 100

strat_peak = np.maximum.accumulate(strategy_eq)
strat_dd = (strategy_eq - strat_peak) / strat_peak * 100
spy_peak = np.maximum.accumulate(spy_eq)
spy_dd = (spy_eq - spy_peak) / spy_peak * 100
max_dd = np.min(strat_dd)
spy_max_dd = np.min(spy_dd)
win_days = np.sum(strat_daily > 0) / len(strat_daily) * 100

# Monthly returns
monthly_df = pd.DataFrame({"date": all_dates, "strat": strat_daily})
monthly_df["year"] = monthly_df["date"].dt.year
monthly_df["month"] = monthly_df["date"].dt.month
monthly_returns = monthly_df.groupby(["year", "month"])["strat"].sum() * 100

years = sorted(monthly_df["year"].unique())
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
heatmap_data = np.full((len(years), 12), np.nan)
for i, yr in enumerate(years):
    for j in range(12):
        if (yr, j + 1) in monthly_returns.index:
            heatmap_data[i, j] = monthly_returns[(yr, j + 1)]

# ── Figure: 3 clean panels ──
fig = plt.figure(figsize=(20, 7))
fig.patch.set_facecolor('white')
gs = GridSpec(1, 3, width_ratios=[1.3, 1.2, 0.8], wspace=0.35)

# ═══ LEFT: Monthly Returns Heatmap ═══
ax1 = fig.add_subplot(gs[0])
ax1.set_facecolor('white')

from matplotlib.colors import LinearSegmentedColormap
_heatmap_colors = ['#c0392b', '#e74c3c', '#f5b7b1', '#fdfdfd', '#abebc6', '#27ae60', '#1e8449']
_heatmap_cmap = LinearSegmentedColormap.from_list('red_green', _heatmap_colors, N=256)

n_rows, n_cols = heatmap_data.shape
cell_w, cell_h = 1.0, 1.0
gap = 0.08

for i in range(n_rows):
    for j in range(n_cols):
        val = heatmap_data[i, j]
        if np.isnan(val):
            continue  # skip empty cells entirely
        else:
            norm_val = np.clip((val + 5) / 10, 0, 1)
            fc = _heatmap_cmap(norm_val)
        rect = plt.Rectangle(
            (j * (cell_w + gap) + gap / 2, (n_rows - 1 - i) * (cell_h + gap) + gap / 2),
            cell_w, cell_h, facecolor=fc, edgecolor='white', linewidth=2.5
        )
        ax1.add_patch(rect)
        if not np.isnan(val):
            txt_color = 'white' if abs(val) > 2.5 else '#1a1a2e'
            ax1.text(
                j * (cell_w + gap) + gap / 2 + cell_w / 2,
                (n_rows - 1 - i) * (cell_h + gap) + gap / 2 + cell_h / 2,
                f"{val:+.1f}", ha='center', va='center',
                fontsize=9, fontweight='bold', color=txt_color
            )

ax1.set_xlim(-gap, n_cols * (cell_w + gap))
ax1.set_ylim(-gap, n_rows * (cell_h + gap))
ax1.set_aspect('equal')
ax1.set_xticks([j * (cell_w + gap) + gap / 2 + cell_w / 2 for j in range(n_cols)])
ax1.set_xticklabels(month_names, fontsize=9, color='#333', fontweight='bold')
ax1.set_yticks([(n_rows - 1 - i) * (cell_h + gap) + gap / 2 + cell_h / 2 for i in range(n_rows)])
ax1.set_yticklabels(years, fontsize=13, color='#1a1a2e', fontweight='bold')
ax1.set_title('Monthly Returns', color='#1a1a2e', fontsize=14, fontweight='bold', pad=12)
ax1.tick_params(length=0)
for spine in ax1.spines.values():
    spine.set_visible(False)

# ═══ MIDDLE: Drawdown Comparison ═══
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor('#fafafa')

# SPY first (background layer) — light fill shows the deep benchmark drawdown
ax2.fill_between(all_dates, spy_dd[1:], 0, color=SPY_COLOR, alpha=0.10, zorder=1)
ax2.plot(all_dates, spy_dd[1:], color=SPY_COLOR, linewidth=1.2, alpha=0.55, zorder=2)

# Strategy on top — darker fill emphasizes the shallow drawdown
ax2.fill_between(all_dates, strat_dd[1:], 0, color=STRAT_COLOR, alpha=0.35, zorder=3)
ax2.plot(all_dates, strat_dd[1:], color=STRAT_COLOR, linewidth=2.2, zorder=4)

# Zero line
ax2.axhline(0, color='#999999', linewidth=0.6, zorder=0)

# Annotate max drawdowns
strat_dd_idx = np.argmin(strat_dd[1:])
spy_dd_idx = np.argmin(spy_dd[1:])

# Strategy annotation — big badge that pops
ax2.annotate(
    f'{max_dd:.1f}%',
    xy=(all_dates[strat_dd_idx], strat_dd[strat_dd_idx + 1]),
    xytext=(30, 25), textcoords='offset points',
    color='white', fontsize=14, fontweight='black',
    bbox=dict(boxstyle='round,pad=0.35', facecolor=STRAT_COLOR, edgecolor='none', alpha=0.95),
    arrowprops=dict(arrowstyle='->', color=STRAT_COLOR, lw=2, connectionstyle='arc3,rad=-0.15'),
    zorder=10,
)

# SPY annotation — secondary, no badge
ax2.annotate(
    f'{spy_max_dd:.1f}%',
    xy=(all_dates[spy_dd_idx], spy_dd[spy_dd_idx + 1]),
    xytext=(30, -20), textcoords='offset points',
    color=SPY_COLOR, fontsize=11, fontweight='bold',
    arrowprops=dict(arrowstyle='->', color=SPY_COLOR, lw=1.5, connectionstyle='arc3,rad=0.15'),
    zorder=10,
)

ax2.set_title('Drawdown Comparison', color='#1a1a2e', fontsize=14, fontweight='bold', pad=12)
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("'%y"))
ax2.xaxis.set_major_locator(mdates.YearLocator())
ax2.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
ax2.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
ax2.tick_params(axis='x', which='major', colors='#333', labelsize=10, pad=14)
ax2.tick_params(axis='x', which='minor', colors='#888', labelsize=7, pad=2)
ax2.tick_params(axis='y', colors='#333', labelsize=9)
ax2.spines['bottom'].set_color('#cccccc')
ax2.spines['left'].set_color('#cccccc')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.grid(True, alpha=0.08, color='#bbbbbb', linewidth=0.5)
ax2.legend(
    ['S&P 500', 'Strategy'], loc='upper left', fontsize=9, framealpha=0.95,
    facecolor='white', edgecolor='#dddddd', labelcolor=[SPY_COLOR, STRAT_COLOR],
    handlelength=1.5, borderpad=0.6,
)

# ═══ RIGHT: Key Stats Comparison ═══
ax3 = fig.add_subplot(gs[2])
ax3.set_facecolor('white')
ax3.axis('off')

metrics = [
    ("Total Return", f"{total_ret:+.1f}%", f"{spy_total_ret:+.1f}%", False),
    ("Ann. Return", f"{ann_ret:.1f}%", f"{spy_total_ret/n_years:.1f}%", False),
    ("Sharpe", f"{sharpe:.2f}", "~0.65", True),
    ("Max DD", f"{max_dd:.1f}%", f"{spy_max_dd:.1f}%", True),
    ("Ann. Vol", f"{ann_vol:.1f}%", f"{spy_ann_vol:.1f}%", False),
    ("Win Rate", f"{win_days:.0f}%", "~53%", False),
]

# Title
ax3.set_title('Key Metrics', color='#1a1a2e', fontsize=15, fontweight='bold', pad=14)

# Column headers
ax3.text(0.52, 0.95, "Ours", transform=ax3.transAxes, fontsize=12,
         fontweight='bold', color=STRAT_COLOR, ha='center')
ax3.text(0.88, 0.95, "SPY", transform=ax3.transAxes, fontsize=12,
         fontweight='bold', color=SPY_COLOR, ha='center')

# Header underline
ax3.plot([0, 1], [0.92, 0.92], transform=ax3.transAxes, color='#999999', linewidth=1.2)

row_h = 0.145
top_y = 0.84
for i, (metric, strat_val, spy_val, highlight) in enumerate(metrics):
    y = top_y - i * row_h
    # Metric label
    ax3.text(0.0, y, metric, transform=ax3.transAxes,
             fontsize=10, color='#777777', fontweight='medium')
    # Strategy value — highlighted rows are larger and bolder
    strat_fs = 15 if highlight else 13
    ax3.text(0.52, y, strat_val, transform=ax3.transAxes,
             fontsize=strat_fs, color=STRAT_COLOR, fontweight='bold', ha='center')
    # SPY value
    ax3.text(0.88, y, spy_val, transform=ax3.transAxes,
             fontsize=10, color=SPY_COLOR, ha='center')
    # Subtle divider below each row
    div_y = y - 0.055
    ax3.plot([0, 1], [div_y, div_y], transform=ax3.transAxes,
             color='#e5e5e5', linewidth=0.6)

plt.tight_layout()
out = Path.home() / "Desktop" / "dashboard.png"
plt.savefig(str(out), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('presentation/dashboard.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved {out} and presentation/dashboard.png")
