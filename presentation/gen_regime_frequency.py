"""
Generate presentation-quality chart showing the historical distribution
of market regimes (crisis, euphoria, transition, normal) from 2018-2024.

Fetches real VIX and HYG data via YahooDataSource, applies the
RegimeDetector classification, and produces:
  - A donut chart showing % of days in each regime
  - A horizontal timeline bar showing regime states color-coded over time
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.engine.data.yahoo_loader import YahooDataSource
from src.engine.meta.regime_detector import RegimeDetector

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Color palette (matches other presentation charts)
# ---------------------------------------------------------------------------
REGIME_COLORS = {
    "crisis":     "#0B2545",  # NAVY_DEEP
    "euphoria":   "#5B4A7A",  # MUTED_PURPLE
    "transition": "#2C5F8A",  # SLATE_BLUE
    "normal":     "#13497B",  # NAVY_MID
}

REGIME_ORDER = ["normal", "transition", "euphoria", "crisis"]

START = "2018-01-01"
END = "2024-12-31"
PROXY_SYMBOLS = ["SPY", "TLT", "GLD", "HYG", "EEM"]


def classify_regimes(ds: YahooDataSource) -> pd.Series:
    """Fetch proxy data, fit the regime detector, and classify every day."""
    logger.info("Fetching proxy returns for %s ...", PROXY_SYMBOLS)
    returns = ds.load_returns(PROXY_SYMBOLS, start_date=START, end_date=END)
    logger.info("Got %d trading days of returns.", len(returns))

    detector = RegimeDetector(proxy_symbols=PROXY_SYMBOLS)
    detector.fit(returns)

    # Classify each day using an expanding window (min = vol_window)
    regimes: list[str] = []
    dates: list[pd.Timestamp] = []
    win = detector.vol_window

    for i in range(win, len(returns)):
        window = returns.iloc[: i + 1]
        regime = detector.detect(window)
        regimes.append(regime)
        dates.append(returns.index[i])

    series = pd.Series(regimes, index=pd.DatetimeIndex(dates), name="regime")
    logger.info("Classified %d days into regimes.", len(series))
    return series


def main() -> None:
    ds = YahooDataSource()
    regimes = classify_regimes(ds)

    # ----- Counts and percentages -----
    counts = regimes.value_counts()
    # Ensure all 4 regimes present
    for r in REGIME_ORDER:
        if r not in counts.index:
            counts[r] = 0
    counts = counts[REGIME_ORDER]
    pcts = counts / counts.sum() * 100

    # ----- Figure -----
    fig, (ax_donut, ax_timeline) = plt.subplots(
        1, 2,
        figsize=(16, 5.5),
        dpi=200,
        gridspec_kw={"width_ratios": [1, 2.2]},
    )
    fig.patch.set_facecolor("#ffffff")

    # ==================== Donut chart ====================
    colors = [REGIME_COLORS[r] for r in REGIME_ORDER]
    wedges, texts, autotexts = ax_donut.pie(
        counts.values,
        labels=None,
        colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
        startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor="#ffffff", linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight("bold")
        at.set_color("#ffffff")

    # Center label
    ax_donut.text(
        0, 0,
        f"{int(counts.sum())}\nTrading\nDays",
        ha="center", va="center",
        fontsize=12, fontweight="bold", color="#0B2545",
    )

    # Legend beside donut
    legend_labels = [
        f"{r.capitalize()}  ({pcts[r]:.1f}%,  {counts[r]} days)"
        for r in REGIME_ORDER
    ]
    patches = [mpatches.Patch(facecolor=REGIME_COLORS[r], edgecolor="#ffffff") for r in REGIME_ORDER]
    ax_donut.legend(
        patches,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        fontsize=9,
        frameon=True,
        fancybox=True,
        edgecolor="#cccccc",
        facecolor="#f9f9f9",
        ncol=2,
    )
    ax_donut.set_title(
        "Regime Distribution",
        fontsize=13, fontweight="bold", color="#0B2545", pad=14,
    )

    # ==================== Timeline bar ====================
    ax_timeline.set_facecolor("#ffffff")

    # Map regimes to numeric for coloring
    regime_map = {r: i for i, r in enumerate(REGIME_ORDER)}
    numeric = regimes.map(regime_map).values.astype(float)
    dates_arr = mdates.date2num(regimes.index.to_pydatetime())

    # Draw thin vertical bars for each day
    for j in range(len(dates_arr)):
        ax_timeline.axvspan(
            dates_arr[j],
            dates_arr[j + 1] if j + 1 < len(dates_arr) else dates_arr[j] + 1,
            facecolor=REGIME_COLORS[REGIME_ORDER[int(numeric[j])]],
            alpha=0.85,
            edgecolor="none",
        )

    ax_timeline.set_xlim(dates_arr[0], dates_arr[-1])
    ax_timeline.set_ylim(0, 1)
    ax_timeline.set_yticks([])

    ax_timeline.xaxis.set_major_locator(mdates.YearLocator())
    ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_timeline.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax_timeline.tick_params(axis="x", colors="#555555", labelsize=9)

    for spine in ax_timeline.spines.values():
        spine.set_color("#cccccc")
        spine.set_linewidth(0.6)
    ax_timeline.spines["left"].set_visible(False)
    ax_timeline.spines["right"].set_visible(False)
    ax_timeline.spines["top"].set_visible(False)

    ax_timeline.set_title(
        "Regime Timeline  (2018 \u2013 2024)",
        fontsize=13, fontweight="bold", color="#0B2545", pad=14,
    )
    ax_timeline.set_xlabel("Date", fontsize=9, color="#333333")

    # Add event annotations
    annotations = [
        ("2020-03-11", "COVID\nCrash"),
        ("2022-02-24", "Ukraine\nInvasion"),
        ("2022-06-15", "Fed 75bp\nHike"),
        ("2023-10-27", "S&P\nRally"),
    ]
    for date_str, label in annotations:
        dt = mdates.date2num(pd.Timestamp(date_str))
        if dates_arr[0] <= dt <= dates_arr[-1]:
            ax_timeline.annotate(
                label,
                xy=(dt, 0.92),
                fontsize=7,
                fontweight="bold",
                color="#0B2545",
                ha="center",
                va="top",
                bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec="#cccccc", alpha=0.85),
            )

    # Suptitle
    fig.suptitle(
        "Historical Market Regime Frequency",
        fontsize=17, fontweight="bold", color="#0B2545", y=1.02,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "regime_frequency.png"
    plt.savefig(
        out_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="#ffffff",
        edgecolor="none",
    )
    logger.info("Saved %s", out_path)

    # Copy to Desktop
    desktop_path = Path.home() / "Desktop" / "regime_frequency.png"
    shutil.copy2(out_path, desktop_path)
    logger.info("Copied to %s", desktop_path)

    plt.close(fig)


if __name__ == "__main__":
    main()
