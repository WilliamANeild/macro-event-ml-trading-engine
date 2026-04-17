"""Generate a cross-sleeve heatmap of average 5-day forward returns
by macro event type and asset sleeve."""

from __future__ import annotations

import sys, os, shutil
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ── project imports ──────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.engine.data.yahoo_loader import YahooDataSource

# ── configuration ────────────────────────────────────────────────

EVENT_DATES: dict[str, list[str]] = {
    "Military Conflict": ["2022-02-24", "2023-10-07", "2024-04-13"],
    "Sanctions":         ["2022-02-28", "2022-06-03", "2023-02-24"],
    "Rate Decision":     ["2022-06-15", "2022-09-21", "2024-03-20"],
    "Oil Shock":         ["2022-03-08", "2023-04-03", "2024-04-05"],
    "Trade Disruption":  ["2018-06-15", "2019-05-10", "2024-04-02"],
    "Shipping Disruption": ["2024-01-12", "2024-01-26", "2021-03-23"],
    "Crypto Regulation": ["2021-05-19", "2023-06-05", "2024-01-10"],
    "Natural Disaster":  ["2021-08-29", "2023-02-06", "2024-01-01"],
}

SLEEVES: dict[str, str] = {
    "Defense": "ITA",
    "Shipping": "ZIM",
    "Rates": "TLT",
    "Commodities": "DBC",
    "Energy": "XLE",
    "Crypto": "BTC-USD",
}

FORWARD_DAYS = 5

OUT_DIR = os.path.join(os.path.dirname(__file__))
OUT_PATH = os.path.join(OUT_DIR, "cross_sleeve_heatmap.png")
DESKTOP_COPY = os.path.expanduser("~/Desktop/cross_sleeve_heatmap.png")


# ── data fetching ────────────────────────────────────────────────

def _earliest_date(event_dates: dict[str, list[str]]) -> str:
    """Return the earliest event date minus a small buffer."""
    all_dates = [d for dates in event_dates.values() for d in dates]
    earliest = min(all_dates)
    dt = datetime.strptime(earliest, "%Y-%m-%d") - timedelta(days=30)
    return dt.strftime("%Y-%m-%d")


def compute_forward_return(
    prices: pd.DataFrame, symbol: str, event_date: str, days: int = 5
) -> float | None:
    """Compute the forward return over *days* trading days after event_date."""
    try:
        ts = pd.Timestamp(event_date)
        # match timezone awareness of the index
        if prices.index.tz is not None:
            ts = ts.tz_localize(prices.index.tz)
        # find the first available date on or after event_date
        mask = prices.index >= ts
        if mask.sum() < days + 1:
            return None
        future = prices.loc[mask, symbol].iloc[: days + 1]
        if len(future) < days + 1:
            return None
        return float((future.iloc[days] / future.iloc[0]) - 1)
    except Exception:
        return None


def build_matrix(
    prices: pd.DataFrame,
    event_dates: dict[str, list[str]],
    sleeves: dict[str, str],
) -> pd.DataFrame:
    """Build event-type x sleeve matrix of average forward returns."""
    rows = {}
    for event, dates in event_dates.items():
        row = {}
        for sleeve_name, sym in sleeves.items():
            returns = []
            for d in dates:
                r = compute_forward_return(prices, sym, d, FORWARD_DAYS)
                if r is not None:
                    returns.append(r)
            row[sleeve_name] = np.mean(returns) * 100 if returns else np.nan
        rows[event] = row
    return pd.DataFrame(rows).T  # index = event types, columns = sleeves


# ── plotting ─────────────────────────────────────────────────────

def plot_heatmap(matrix: pd.DataFrame, out_path: str) -> None:
    """Plot a red/green diverging heatmap with annotated % values."""
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    data = matrix.values.astype(float)
    vmax = max(abs(np.nanmin(data)), abs(np.nanmax(data)))
    vmax = max(vmax, 0.5)  # floor so colours are visible

    # red-white-green diverging colormap
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "RdGn", ["#d32f2f", "#ffffff", "#2e7d32"], N=256
    )
    cmap.set_bad(color="#eeeeee")

    im = ax.imshow(
        data, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto"
    )

    # axis labels
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=11)

    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    plt.setp(ax.get_xticklabels(), ha="center")

    # annotate cells
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if np.isnan(val):
                txt = "N/A"
                color = "#888888"
            else:
                txt = f"{val:+.2f}%"
                brightness = abs(val) / vmax
                color = "white" if brightness > 0.55 else "black"
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=10, fontweight="bold", color=color)

    # title
    ax.set_title(
        "Average 5-Day Forward Returns by Event Type & Asset Sleeve",
        fontsize=15, fontweight="bold", color="#0d1b2a",
        pad=20,
    )

    # colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Return (%)", fontsize=11)

    # grid lines
    for edge in range(data.shape[0] + 1):
        ax.axhline(edge - 0.5, color="white", linewidth=2)
    for edge in range(data.shape[1] + 1):
        ax.axvline(edge - 0.5, color="white", linewidth=2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved  -> {out_path}")


# ── main ─────────────────────────────────────────────────────────

def main() -> None:
    ds = YahooDataSource()
    symbols = list(SLEEVES.values())
    start = _earliest_date(EVENT_DATES)

    print(f"Fetching prices for {symbols} from {start} ...")
    prices = ds.load_prices(symbols, start=start)
    print(f"  price matrix: {prices.shape[0]} rows x {prices.shape[1]} cols")

    matrix = build_matrix(prices, EVENT_DATES, SLEEVES)
    print("\nHeatmap matrix (%):")
    print(matrix.round(2).to_string())
    print()

    plot_heatmap(matrix, OUT_PATH)

    # copy to desktop
    shutil.copy2(OUT_PATH, DESKTOP_COPY)
    print(f"Copied -> {DESKTOP_COPY}")


if __name__ == "__main__":
    main()
