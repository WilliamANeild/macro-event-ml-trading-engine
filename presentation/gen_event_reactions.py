"""
Generate presentation-quality chart showing normalized market reactions
around major geopolitical and macro events.

Uses YahooDataSource to fetch real historical price data, then normalizes
each asset to 100 at the event date (T=0) and plots T-10 to T+15.
"""

from __future__ import annotations

import logging
import shutil
import sys
from datetime import timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.engine.data.yahoo_loader import YahooDataSource

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Color palette (matches other presentation charts)
# ---------------------------------------------------------------------------
COLORS = {
    "CL=F":    "#0B2545",   # NAVY_DEEP  - Oil
    "ITA":     "#13497B",   # NAVY_MID   - Defense
    "TLT":     "#2C5F8A",   # SLATE_BLUE - Bonds
    "^VIX":    "#5B4A7A",   # MUTED_PURPLE - Volatility
    "BTC-USD": "#3A6B96",   # BLUE_GRAY  - Crypto
}

LABELS = {
    "CL=F":    "Oil (CL=F)",
    "ITA":     "Defense (ITA)",
    "TLT":     "Bonds (TLT)",
    "^VIX":    "Volatility (VIX)",
    "BTC-USD": "Crypto (BTC)",
}

LINE_STYLES = {
    "CL=F":    "-",
    "ITA":     "--",
    "TLT":     "-.",
    "^VIX":    ":",
    "BTC-USD": "-",
}

SYMBOLS = list(COLORS.keys())

# ---------------------------------------------------------------------------
# Events: (date_str, title)
# ---------------------------------------------------------------------------
EVENTS = [
    ("2022-02-24", "Russia Invades Ukraine"),
    ("2023-10-07", "Hamas Attack on Israel"),
    ("2024-01-12", "Houthi Red Sea Escalation"),
    ("2024-03-20", "FOMC March 2024 Meeting"),
    ("2022-06-15", "Fed 75bp Rate Hike"),
]

WINDOW_BEFORE = 10   # trading days before event
WINDOW_AFTER = 15    # trading days after event
CALENDAR_PAD = 30    # calendar-day buffer for fetching


def fetch_event_window(
    ds: YahooDataSource,
    symbol: str,
    event_date: str,
) -> pd.Series | None:
    """Fetch prices around an event and return normalized series indexed by
    relative trading days (-WINDOW_BEFORE .. +WINDOW_AFTER)."""
    evt = pd.Timestamp(event_date)
    start = (evt - timedelta(days=CALENDAR_PAD)).strftime("%Y-%m-%d")
    end = (evt + timedelta(days=CALENDAR_PAD)).strftime("%Y-%m-%d")

    try:
        prices = ds.load_prices([symbol], start=start, end=end)[symbol].dropna()
    except Exception as exc:
        logger.warning("Could not fetch %s for event %s: %s", symbol, event_date, exc)
        return None

    if prices.empty:
        logger.warning("Empty data for %s around %s", symbol, event_date)
        return None

    # Make index tz-naive so comparisons work
    prices.index = prices.index.tz_localize(None)

    # Find the trading day closest to (on or after) event date
    valid_dates = prices.index[prices.index >= evt]
    if valid_dates.empty:
        # Try on-or-before if market was closed on event day
        valid_dates = prices.index[prices.index <= evt]
        if valid_dates.empty:
            logger.warning("No trading day near %s for %s", event_date, symbol)
            return None
        t0_idx = len(prices.index) - len(prices.index[prices.index > valid_dates[-1]]) - 1
    else:
        t0_idx = prices.index.get_loc(valid_dates[0])

    start_idx = max(t0_idx - WINDOW_BEFORE, 0)
    end_idx = min(t0_idx + WINDOW_AFTER + 1, len(prices))

    window = prices.iloc[start_idx:end_idx].copy()
    t0_price = prices.iloc[t0_idx]
    if t0_price == 0:
        logger.warning("Zero price at T=0 for %s on %s", symbol, event_date)
        return None

    # Normalize to 100 at T=0
    normalized = (window / t0_price) * 100.0

    # Re-index to relative trading days
    relative_days = list(range(start_idx - t0_idx, end_idx - t0_idx))
    normalized.index = relative_days

    return normalized


def main() -> None:
    ds = YahooDataSource()

    fig, axes = plt.subplots(2, 3, figsize=(20, 11), dpi=200)
    fig.patch.set_facecolor("#ffffff")

    # Flatten axes; last cell will be used for legend
    axes_flat = axes.flatten()

    for i, (event_date, event_title) in enumerate(EVENTS):
        ax = axes_flat[i]
        ax.set_facecolor("#ffffff")

        for symbol in SYMBOLS:
            logger.info("Fetching %s for %s ...", symbol, event_title)
            series = fetch_event_window(ds, symbol, event_date)
            if series is None:
                continue
            ax.plot(
                series.index,
                series.values,
                color=COLORS[symbol],
                linestyle=LINE_STYLES[symbol],
                linewidth=2.2,
                label=LABELS[symbol],
                alpha=0.9,
            )

        # Vertical dashed line at T=0
        ax.axvline(x=0, color="#1a1a1a", linestyle="--", linewidth=1.2, alpha=0.5)

        # Horizontal reference at 100
        ax.axhline(y=100, color="#cccccc", linestyle="-", linewidth=0.8, alpha=0.5)

        # Titles and labels
        ax.set_title(
            f"{event_title}\n{event_date}",
            fontsize=12,
            fontweight="bold",
            color="#0B2545",
            pad=10,
        )
        ax.set_xlabel("Trading Days Relative to Event", fontsize=9, color="#333333")
        ax.set_ylabel("Normalized Price (T=0 = 100)", fontsize=9, color="#333333")

        # Grid
        ax.grid(True, alpha=0.25, linewidth=0.6, color="#888888")
        ax.tick_params(colors="#555555", labelsize=8)

        # Clean spines
        for spine in ax.spines.values():
            spine.set_color("#cccccc")
            spine.set_linewidth(0.6)

    # Use the 6th subplot cell for a shared legend
    legend_ax = axes_flat[5]
    legend_ax.axis("off")

    # Build legend handles from first subplot that has lines
    handles, labels = [], []
    for a in axes_flat[:5]:
        h, l = a.get_legend_handles_labels()
        if h:
            handles, labels = h, l
            break

    if handles:
        legend_ax.legend(
            handles,
            labels,
            loc="center",
            fontsize=13,
            frameon=True,
            fancybox=True,
            shadow=False,
            edgecolor="#cccccc",
            facecolor="#f9f9f9",
            title="Asset Classes",
            title_fontsize=14,
            ncol=1,
        )

    # Suptitle
    fig.suptitle(
        "Normalized Market Reactions Around Major Events",
        fontsize=18,
        fontweight="bold",
        color="#0B2545",
        y=0.98,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Save
    out_dir = Path(__file__).resolve().parent
    out_path = out_dir / "event_reactions.png"
    plt.savefig(
        out_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="#ffffff",
        edgecolor="none",
    )
    logger.info("Saved %s", out_path)

    # Copy to Desktop
    desktop_path = Path.home() / "Desktop" / "event_reactions.png"
    shutil.copy2(out_path, desktop_path)
    logger.info("Copied to %s", desktop_path)

    plt.close(fig)


if __name__ == "__main__":
    main()
