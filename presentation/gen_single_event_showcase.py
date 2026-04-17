"""
Single-event showcase: Russia-Ukraine invasion (2022-02-24)
Shows uneven cross-asset repricing across 5 sleeves after one geopolitical shock.

Thesis: one macro shock forces multiple sleeves to reprice, but not all at the same speed.
"""

from __future__ import annotations

import shutil
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yfinance as yf

# ── Event definition ──
EVENT_DATE = "2022-02-24"
EVENT_LABEL = "Russia Invades Ukraine"
WINDOW_BEFORE = 5
WINDOW_AFTER = 10

# ── Assets: one per sleeve ──
ASSETS = {
    "CL=F":    {"label": "Oil (WTI Crude)",       "color": "#0B2545", "lw": 2.8, "ls": "-",  "zorder": 6},
    "BDRY":    {"label": "Shipping (Dry Bulk)",    "color": "#13497B", "lw": 2.4, "ls": "--", "zorder": 5},
    "ITA":     {"label": "Defense (A&D ETF)",      "color": "#2C5F8A", "lw": 2.4, "ls": "-.", "zorder": 4},
    "TLT":     {"label": "Rates (20Y Treasury)",   "color": "#5B4A7A", "lw": 2.4, "ls": ":",  "zorder": 3},
    "^VIX":    {"label": "Volatility (VIX)",       "color": "#8B1A1A", "lw": 2.6, "ls": "-",  "zorder": 7},
}

CALENDAR_PAD = 25  # extra calendar days to ensure enough trading days


def fetch_normalized(symbol: str, event_date: str) -> pd.Series | None:
    evt = pd.Timestamp(event_date)
    start = (evt - timedelta(days=CALENDAR_PAD)).strftime("%Y-%m-%d")
    end = (evt + timedelta(days=CALENDAR_PAD)).strftime("%Y-%m-%d")

    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        prices = df["Close"].dropna()
    except Exception as exc:
        print(f"  WARN: Could not fetch {symbol}: {exc}")
        return None

    if prices.empty:
        return None

    prices.index = prices.index.tz_localize(None)

    # Find T0: first trading day on or after event date
    valid = prices.index[prices.index >= evt]
    if valid.empty:
        valid = prices.index[prices.index <= evt]
        if valid.empty:
            return None
        t0_loc = prices.index.get_loc(valid[-1])
    else:
        t0_loc = prices.index.get_loc(valid[0])

    i_start = max(t0_loc - WINDOW_BEFORE, 0)
    i_end = min(t0_loc + WINDOW_AFTER + 1, len(prices))

    window = prices.iloc[i_start:i_end].copy()
    t0_price = prices.iloc[t0_loc]
    if t0_price == 0:
        return None

    # Rebase to 100 at T0
    normalized = (window / t0_price) * 100.0
    relative_days = list(range(i_start - t0_loc, i_end - t0_loc))
    normalized.index = relative_days
    return normalized


def main() -> None:
    # ── Fetch all series ──
    series_data: dict[str, pd.Series] = {}
    for symbol in ASSETS:
        print(f"Fetching {symbol}...")
        s = fetch_normalized(symbol, EVENT_DATE)
        if s is not None:
            series_data[symbol] = s
            print(f"  OK: {len(s)} days, range [{s.index.min()}, {s.index.max()}]")
        else:
            print(f"  FAILED")

    if not series_data:
        print("No data fetched. Exiting.")
        return

    # ── Build figure ──
    fig, ax = plt.subplots(figsize=(18, 5.5), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    for symbol, s in series_data.items():
        cfg = ASSETS[symbol]
        ax.plot(
            s.index, s.values,
            color=cfg["color"],
            linewidth=cfg["lw"],
            linestyle=cfg["ls"],
            label=cfg["label"],
            zorder=cfg["zorder"],
            alpha=0.92,
        )

    # ── T0 vertical line ──
    ax.axvline(x=0, color="#1a1a1a", linestyle="--", linewidth=1.0, alpha=0.4, zorder=1)
    ax.text(0.15, ax.get_ylim()[1] * 0.995, "T₀: Feb 24, 2022",
            fontsize=9, color="#1a1a1a", alpha=0.6, va="top", zorder=1)

    # ── Baseline at 100 ──
    ax.axhline(y=100, color="#cccccc", linestyle="-", linewidth=0.7, alpha=0.5, zorder=0)

    # ── Shaded event zone (T0 to T+2) ──
    ax.axvspan(0, 2, color="#0B2545", alpha=0.04, zorder=0)

    # ── Labels and title ──
    ax.set_xlabel("Trading Days Relative to Event", fontsize=12, color="#333333", labelpad=10)
    ax.set_ylabel("Normalized Price (T₀ = 100)", fontsize=12, color="#333333", labelpad=10)

    ax.set_title(
        f"Cross-Asset Repricing: {EVENT_LABEL}",
        fontsize=20, fontweight="bold", color="#0B2545", pad=18,
    )

    # Subtitle
    fig.text(
        0.5, 0.91,
        "One shock, five sleeves, five different repricing speeds",
        ha="center", fontsize=13, color="#555555", style="italic",
    )

    # ── Grid ──
    ax.grid(True, alpha=0.2, linewidth=0.5, color="#888888")
    ax.tick_params(colors="#555555", labelsize=10)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(1))

    # ── Spines ──
    for spine in ax.spines.values():
        spine.set_color("#dddddd")
        spine.set_linewidth(0.6)

    # ── Legend ──
    legend = ax.legend(
        loc="upper left",
        fontsize=11,
        frameon=True,
        fancybox=True,
        shadow=False,
        edgecolor="#cccccc",
        facecolor="#fafafa",
        framealpha=0.95,
    )
    legend.get_frame().set_linewidth(0.6)

    plt.tight_layout(rect=[0, 0, 1, 0.90])

    # ── Save ──
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "single_event_showcase.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    print(f"\nSaved: {out_path}")

    desktop = Path.home() / "Desktop" / "single_event_showcase.png"
    shutil.copy2(out_path, desktop)
    print(f"Copied: {desktop}")

    # ── Print interpretation ──
    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    for symbol, s in series_data.items():
        label = ASSETS[symbol]["label"]
        t0_val = s.get(0, 100)
        t1_val = s.get(1, None)
        t5_val = s.get(5, None)
        t10_val = s.get(10, None)
        parts = [f"T0={t0_val:.1f}"]
        if t1_val is not None:
            parts.append(f"T+1={t1_val:.1f}")
        if t5_val is not None:
            parts.append(f"T+5={t5_val:.1f}")
        if t10_val is not None:
            parts.append(f"T+10={t10_val:.1f}")
        print(f"  {label:30s} {', '.join(parts)}")

    plt.close(fig)


if __name__ == "__main__":
    main()
