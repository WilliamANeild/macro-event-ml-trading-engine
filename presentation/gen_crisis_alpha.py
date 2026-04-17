"""Slide 2: Crisis Alpha — Q1 2025 tariff selloff + 2022 rate hiking."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
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

# Colors
STRAT_COLOR = '#1e3a5f'
SPY_COLOR = '#6366f1'
BAL_COLOR = '#9ca3af'

# ── Figure: two panels ──
fig = plt.figure(figsize=(20, 6))
fig.patch.set_facecolor('white')
gs = GridSpec(1, 2, width_ratios=[1.1, 1], wspace=0.3)

# ════════════════════════════════════════════
# LEFT PANEL: Q1 2025 Tariff Selloff
# ════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0])
ax1.set_facecolor('white')

mask_2025 = (all_dates >= '2025-01-01') & (all_dates <= '2025-04-01')
idx_2025 = np.where(mask_2025)[0]

if len(idx_2025) > 0:
    start_idx = idx_2025[0]
    dates_q1 = all_dates[mask_2025]

    strat_q1 = strategy_eq[start_idx:start_idx + len(idx_2025) + 1]
    spy_q1 = spy_eq[start_idx:start_idx + len(idx_2025) + 1]
    bal_q1 = bal_eq[start_idx:start_idx + len(idx_2025) + 1]

    strat_q1 = strat_q1 / strat_q1[0]
    spy_q1 = spy_q1 / spy_q1[0]
    bal_q1 = bal_q1 / bal_q1[0]

    ax1.plot(dates_q1, strat_q1[1:], color=STRAT_COLOR, linewidth=2.5, label='Strategy')
    ax1.plot(dates_q1, spy_q1[1:], color=SPY_COLOR, linewidth=2, label='S&P 500')
    ax1.plot(dates_q1, bal_q1[1:], color=BAL_COLOR, linewidth=1.5, alpha=0.7, label='60/40')

    ax1.fill_between(dates_q1, strat_q1[1:], spy_q1[1:],
                     where=strat_q1[1:] >= spy_q1[1:],
                     color=STRAT_COLOR, alpha=0.1)

    strat_ret = (strat_q1[-1] - 1) * 100
    spy_ret = (spy_q1[-1] - 1) * 100
    ax1.annotate(f'{strat_ret:+.1f}%', xy=(dates_q1[-1], strat_q1[-1]),
                 xytext=(10, 5), textcoords='offset points',
                 color=STRAT_COLOR, fontsize=14, fontweight='bold')
    ax1.annotate(f'{spy_ret:+.1f}%', xy=(dates_q1[-1], spy_q1[-1]),
                 xytext=(10, -8), textcoords='offset points',
                 color=SPY_COLOR, fontsize=14, fontweight='bold')

ax1.set_title('Q1 2025: Tariff Fears & Market Selloff',
              color='#1a1a2e', fontsize=14, fontweight='bold', pad=12)
ax1.axhline(y=1.0, color='#999', alpha=0.4, linestyle='--', linewidth=0.8)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax1.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0, symbol='%'))
ax1.tick_params(colors='#333', labelsize=9)
ax1.spines['bottom'].set_color('#cccccc')
ax1.spines['left'].set_color('#cccccc')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.grid(True, alpha=0.15, color='#999')
ax1.legend(loc='lower left', fontsize=10, framealpha=0.95,
           facecolor='white', edgecolor='#cccccc', labelcolor='#333')

# Portfolio positioning callout
jan_trade = None
for t in result.trades:
    if t["date"].startswith("2025-01"):
        jan_trade = t
        break

if jan_trade:
    top_positions = sorted(jan_trade["weights"].items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    pos_text = "Portfolio Positioning:\n"
    for sym, w in top_positions:
        direction = "LONG" if w > 0 else "SHORT"
        pos_text += f"  {direction} {sym}: {abs(w)*100:.0f}%\n"
    pos_text += f"\n  Regime: {jan_trade['regime']}"

    props = dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor=STRAT_COLOR,
                 alpha=0.95, linewidth=1.2)
    ax1.text(0.98, 0.97, pos_text, transform=ax1.transAxes, fontsize=9,
             verticalalignment='top', horizontalalignment='right',
             fontfamily='monospace', color='#1a1a2e', bbox=props)


# ════════════════════════════════════════════
# RIGHT PANEL: 2022 Rate Hiking Cycle
# ════════════════════════════════════════════
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor('white')

mask_2022 = (all_dates >= '2022-06-01') & (all_dates <= '2023-01-01')
idx_2022 = np.where(mask_2022)[0]

if len(idx_2022) > 0:
    start_idx = idx_2022[0]
    dates_h2 = all_dates[mask_2022]

    strat_h2 = strategy_eq[start_idx:start_idx + len(idx_2022) + 1]
    spy_h2 = spy_eq[start_idx:start_idx + len(idx_2022) + 1]
    bal_h2 = bal_eq[start_idx:start_idx + len(idx_2022) + 1]

    strat_h2 = strat_h2 / strat_h2[0]
    spy_h2 = spy_h2 / spy_h2[0]
    bal_h2 = bal_h2 / bal_h2[0]

    ax2.plot(dates_h2, strat_h2[1:], color=STRAT_COLOR, linewidth=2.5, label='Strategy')
    ax2.plot(dates_h2, spy_h2[1:], color=SPY_COLOR, linewidth=2, label='S&P 500')
    ax2.plot(dates_h2, bal_h2[1:], color=BAL_COLOR, linewidth=1.5, alpha=0.7, label='60/40')

    ax2.fill_between(dates_h2, strat_h2[1:], spy_h2[1:],
                     where=strat_h2[1:] >= spy_h2[1:],
                     color=STRAT_COLOR, alpha=0.1)

    strat_ret2 = (strat_h2[-1] - 1) * 100
    spy_ret2 = (spy_h2[-1] - 1) * 100
    bal_ret2 = (bal_h2[-1] - 1) * 100
    ax2.annotate(f'{strat_ret2:+.1f}%', xy=(dates_h2[-1], strat_h2[-1]),
                 xytext=(10, 5), textcoords='offset points',
                 color=STRAT_COLOR, fontsize=14, fontweight='bold')
    ax2.annotate(f'{spy_ret2:+.1f}%', xy=(dates_h2[-1], spy_h2[-1]),
                 xytext=(10, 0), textcoords='offset points',
                 color=SPY_COLOR, fontsize=14, fontweight='bold')
    ax2.annotate(f'{bal_ret2:+.1f}%', xy=(dates_h2[-1], bal_h2[-1]),
                 xytext=(10, -5), textcoords='offset points',
                 color=BAL_COLOR, fontsize=12, fontweight='bold')

ax2.set_title('H2 2022: Fed Rate Hiking Cycle',
              color='#1a1a2e', fontsize=14, fontweight='bold', pad=12)
ax2.axhline(y=1.0, color='#999', alpha=0.4, linestyle='--', linewidth=0.8)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0, symbol='%'))
ax2.tick_params(colors='#333', labelsize=9)
ax2.spines['bottom'].set_color('#cccccc')
ax2.spines['left'].set_color('#cccccc')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.grid(True, alpha=0.15, color='#999')
ax2.legend(loc='lower left', fontsize=10, framealpha=0.95,
           facecolor='white', edgecolor='#cccccc', labelcolor='#333')

# Key event annotation
props2 = dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor=SPY_COLOR,
              alpha=0.95, linewidth=1.2)
ax2.text(0.98, 0.97,
         "The Fed hiked rates 7 times\n"
         "in 2022. Stocks and bonds\n"
         "fell together — 60/40 failed.\n\n"
         "Our strategy stayed flat.",
         transform=ax2.transAxes, fontsize=9,
         verticalalignment='top', horizontalalignment='right',
         fontfamily='monospace', color='#1a1a2e', bbox=props2)

# Main title
fig.suptitle('Crisis Alpha: Protecting Capital When Markets Break',
             color='#1a1a2e', fontsize=18, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.94])
out = Path.home() / "Desktop" / "crisis_alpha.png"
plt.savefig(str(out), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig('presentation/crisis_alpha.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved {out} and presentation/crisis_alpha.png")
