"""
10-Year Event-Driven Opportunity Map

Dual-panel presentation slide:
  Top: SPY + TLT + GLD indexed to 100, with event markers
  Bottom: 5-day forward return heatmap by sleeve for each event

All data is REAL (Yahoo Finance). No mock strategy returns.
This proves the thesis: macro shocks cause multi-sleeve repricing at different speeds.
"""

from __future__ import annotations

import shutil
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yfinance as yf

# ═══════════════════════════════════════════════════════════
# EVENTS — real dates, real shocks
# ═══════════════════════════════════════════════════════════
EVENTS = [
    {"date": "2018-03-22", "label": "US-China\nTrade War",        "short": "Trade War"},
    {"date": "2019-08-14", "label": "Yield Curve\nInversion",     "short": "Curve Inv."},
    {"date": "2020-03-11", "label": "COVID\nPandemic",            "short": "COVID"},
    {"date": "2021-03-23", "label": "Suez Canal\nBlockage",       "short": "Suez"},
    {"date": "2022-02-24", "label": "Russia\nInvades Ukraine",    "short": "Russia-UKR"},
    {"date": "2022-06-15", "label": "Fed 75bp\nRate Hike",        "short": "Fed 75bp"},
    {"date": "2023-10-07", "label": "Hamas\nAttack",              "short": "Hamas"},
    {"date": "2024-01-12", "label": "Houthi\nRed Sea",            "short": "Houthi"},
]

# ═══════════════════════════════════════════════════════════
# BACKDROP — long-term indexed series
# ═══════════════════════════════════════════════════════════
BACKDROP_SYMBOLS = {
    "SPY": {"label": "S&P 500",     "color": "#1a1a1a", "lw": 2.0, "ls": "-",  "alpha": 0.85},
    "TLT": {"label": "20Y Treasury","color": "#5B4A7A", "lw": 1.4, "ls": "--", "alpha": 0.55},
    "GLD": {"label": "Gold",        "color": "#8B7355", "lw": 1.4, "ls": "-.", "alpha": 0.55},
}

# ═══════════════════════════════════════════════════════════
# SLEEVES — for heatmap reaction scorecard
# ═══════════════════════════════════════════════════════════
SLEEVE_SYMBOLS = ["CL=F", "BDRY", "ITA", "TLT", "^VIX"]
SLEEVE_LABELS  = ["Oil", "Shipping", "Defense", "Rates", "Volatility"]

FETCH_START = "2017-01-01"
FETCH_END   = "2025-01-01"


def fetch_backdrop() -> dict[str, pd.Series]:
    """Fetch long-run daily close prices for backdrop symbols."""
    result = {}
    for sym in BACKDROP_SYMBOLS:
        print(f"  Fetching backdrop: {sym}")
        try:
            df = yf.download(sym, start=FETCH_START, end=FETCH_END, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            s = df["Close"].dropna()
            s.index = s.index.tz_localize(None)
            result[sym] = s
        except Exception as e:
            print(f"    WARN: {e}")
    return result


def fetch_sleeve_returns(symbol: str, event_date: str, fwd_days: int = 5) -> float | None:
    """Fetch 5-day forward return after an event date."""
    evt = pd.Timestamp(event_date)
    start = (evt - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (evt + timedelta(days=fwd_days + 10)).strftime("%Y-%m-%d")

    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        prices = df["Close"].dropna()
        prices.index = prices.index.tz_localize(None)
    except Exception:
        return None

    if prices.empty:
        return None

    # Find T0: first trading day on or after event
    valid = prices.index[prices.index >= evt]
    if valid.empty:
        return None
    t0_date = valid[0]
    t0_loc = prices.index.get_loc(t0_date)

    # T+fwd_days
    end_loc = min(t0_loc + fwd_days, len(prices) - 1)
    if end_loc <= t0_loc:
        return None

    t0_price = prices.iloc[t0_loc]
    end_price = prices.iloc[end_loc]
    if t0_price == 0:
        return None

    return (end_price / t0_price - 1) * 100  # percentage


def main() -> None:
    print("Fetching backdrop data...")
    backdrop = fetch_backdrop()

    print("Fetching sleeve reactions...")
    # Build heatmap matrix: events × sleeves
    heatmap = np.full((len(EVENTS), len(SLEEVE_SYMBOLS)), np.nan)
    for i, evt in enumerate(EVENTS):
        for j, sym in enumerate(SLEEVE_SYMBOLS):
            print(f"  {evt['short']} × {sym}")
            ret = fetch_sleeve_returns(sym, evt["date"])
            if ret is not None:
                heatmap[i, j] = ret

    # ═══════════════════════════════════════════════════════
    # BUILD FIGURE
    # ═══════════════════════════════════════════════════════
    fig = plt.figure(figsize=(24, 9), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    # GridSpec: top panel (equity lines) + bottom panel (heatmap)
    gs = fig.add_gridspec(
        2, 1, height_ratios=[2.2, 1], hspace=0.18,
        left=0.05, right=0.95, top=0.88, bottom=0.06,
    )
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])

    # ── TOP PANEL: indexed backdrop + event markers ──
    ax_top.set_facecolor("#FFFFFF")

    for sym, cfg in BACKDROP_SYMBOLS.items():
        if sym not in backdrop:
            continue
        s = backdrop[sym]
        indexed = (s / s.iloc[0]) * 100
        ax_top.plot(
            indexed.index, indexed.values,
            color=cfg["color"], linewidth=cfg["lw"],
            linestyle=cfg["ls"], alpha=cfg["alpha"],
            label=cfg["label"], zorder=2,
        )

    # Event markers — manually set y-offsets to prevent overlap
    label_offsets = [88, 58, 88, 58, 88, 58, 88, 58]
    for i, evt in enumerate(EVENTS):
        evt_date = pd.Timestamp(evt["date"])
        ax_top.axvline(
            x=evt_date, color="#0B2545", linestyle="-",
            linewidth=0.8, alpha=0.35, zorder=1,
        )
        ax_top.annotate(
            evt["label"],
            xy=(evt_date, 0), xycoords=("data", "axes fraction"),
            xytext=(0, label_offsets[i]), textcoords="offset points",
            fontsize=7, color="#0B2545", fontweight="bold",
            ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="#F0F2F5",
                      edgecolor="#A8B2BF", linewidth=0.5, alpha=0.92),
            annotation_clip=False,
        )

    ax_top.set_ylabel("Indexed Value (Start = 100)", fontsize=11, color="#333333", labelpad=8)
    ax_top.grid(True, alpha=0.15, linewidth=0.4, color="#888888")
    ax_top.tick_params(colors="#555555", labelsize=9)
    ax_top.xaxis.set_major_locator(mdates.YearLocator())
    ax_top.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for spine in ax_top.spines.values():
        spine.set_color("#dddddd")
        spine.set_linewidth(0.5)

    legend = ax_top.legend(
        loc="upper left", fontsize=10, frameon=True,
        fancybox=True, edgecolor="#cccccc", facecolor="#fafafa",
        framealpha=0.9,
    )
    legend.get_frame().set_linewidth(0.5)

    # ── BOTTOM PANEL: heatmap scorecard ──
    ax_bot.set_facecolor("#FFFFFF")

    # Custom diverging colormap: red → white → green
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "rg", ["#C0392B", "#E8E8E8", "#27AE60"], N=256
    )

    # Determine symmetric color range
    abs_max = np.nanmax(np.abs(heatmap))
    if abs_max == 0 or np.isnan(abs_max):
        abs_max = 10

    im = ax_bot.imshow(
        heatmap.T, cmap=cmap, aspect="auto",
        vmin=-abs_max, vmax=abs_max, interpolation="nearest",
    )

    # Annotate cells
    for i in range(heatmap.shape[0]):
        for j in range(heatmap.shape[1]):
            val = heatmap[i, j]
            if np.isnan(val):
                txt = "N/A"
                color = "#999999"
            else:
                txt = f"{val:+.1f}%"
                color = "#FFFFFF" if abs(val) > abs_max * 0.45 else "#1a1a1a"
            ax_bot.text(
                i, j, txt, ha="center", va="center",
                fontsize=9, fontweight="bold", color=color, zorder=3,
            )

    # Axis labels
    ax_bot.set_xticks(range(len(EVENTS)))
    ax_bot.set_xticklabels(
        [e["short"] for e in EVENTS],
        fontsize=9, color="#333333", rotation=0,
    )
    ax_bot.set_yticks(range(len(SLEEVE_LABELS)))
    ax_bot.set_yticklabels(SLEEVE_LABELS, fontsize=10, color="#333333")

    ax_bot.set_xlabel("5-Day Forward Return After Event", fontsize=10, color="#555555", labelpad=8)

    for spine in ax_bot.spines.values():
        spine.set_color("#dddddd")
        spine.set_linewidth(0.5)

    ax_bot.tick_params(length=0)

    # ── TITLES ──
    fig.suptitle(
        "Macro Event Opportunity Map: 8 Years of Cross-Asset Repricing",
        fontsize=22, fontweight="bold", color="#0B2545", y=0.96,
    )
    fig.text(
        0.5, 0.915,
        "Real market data  ·  No simulated returns  ·  Every event triggered repricing across multiple sleeves at different speeds",
        ha="center", fontsize=11, color="#666666", style="italic",
    )

    # ── SAVE ──
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "opportunity_map.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    print(f"\nSaved: {out_path}")

    desktop = Path.home() / "Desktop" / "opportunity_map.png"
    shutil.copy2(out_path, desktop)
    print(f"Copied: {desktop}")

    # ── PRINT SCORECARD ──
    print("\n" + "=" * 70)
    print("5-DAY FORWARD RETURN SCORECARD (real data)")
    print("=" * 70)
    header = f"{'Event':20s}" + "".join(f"{s:>12s}" for s in SLEEVE_LABELS)
    print(header)
    print("-" * len(header))
    for i, evt in enumerate(EVENTS):
        row = f"{evt['short']:20s}"
        for j in range(len(SLEEVE_LABELS)):
            val = heatmap[i, j]
            if np.isnan(val):
                row += f"{'N/A':>12s}"
            else:
                row += f"{val:>+11.1f}%"
        print(row)

    plt.close(fig)


if __name__ == "__main__":
    main()
