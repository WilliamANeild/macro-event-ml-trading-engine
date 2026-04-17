"""Generate a stacked horizontal bar chart of instrument coverage by sleeve."""

from __future__ import annotations

import sys
import os
import shutil
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# ---------------------------------------------------------------------------
# Import universe registry
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from engine.universe.registry import get_universe  # noqa: E402

# ---------------------------------------------------------------------------
# Map asset_class -> display category
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "equity_etf":       "ETFs",
    "commodity_etf":    "ETFs",
    "crypto_etf":      "ETFs",
    "currency_etf":    "ETFs",
    "fixed_income_etf": "ETFs",
    "volatility_etp":  "ETFs",
    "equity_stock":    "Stocks",
    "crypto_stock":    "Stocks",
    "commodity_future": "Futures",
    "rate_future":     "Futures",
    "currency_future": "FX",
    "index":           "Indices",
}

# Display category order and colours (navy/blue/purple palette)
CATEGORIES = ["ETFs", "Stocks", "Futures", "FX", "Crypto", "Indices"]
COLORS = {
    "ETFs":     "#0B2545",
    "Stocks":   "#13497B",
    "Futures":  "#2C5F8A",
    "FX":       "#5B4A7A",
    "Crypto":   "#3A6B96",
    "Indices":  "#4A7FAA",
}

# Sleeve display names
SLEEVE_LABELS = {
    "defense":     "Defense",
    "shipping":    "Shipping",
    "commodities": "Commodities",
    "rates_us":    "Rates (US)",
    "rates_ex_us": "Rates (ex-US)",
    "crypto":      "Crypto",
    "hedge":       "Hedge",
    "derivatives": "Derivatives",
}

# ---------------------------------------------------------------------------
# Build counts: sleeve -> category -> count
# ---------------------------------------------------------------------------
universe = get_universe()
counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

for inst in universe:
    sleeve = inst.theme
    cat = CATEGORY_MAP.get(inst.asset_class, "Other")
    counts[sleeve][cat] += 1

# Order sleeves: specified first, then alphabetical remainder
SLEEVE_ORDER = ["defense", "shipping", "commodities", "rates_us",
                "rates_ex_us", "crypto", "hedge", "derivatives"]
extra = sorted(set(counts.keys()) - set(SLEEVE_ORDER))
ordered_sleeves = [s for s in SLEEVE_ORDER if s in counts] + extra

labels = [SLEEVE_LABELS.get(s, s.replace("_", " ").title()) for s in ordered_sleeves]

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 11,
})

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

y = np.arange(len(ordered_sleeves))
bar_height = 0.55
lefts = np.zeros(len(ordered_sleeves))

for cat in CATEGORIES:
    widths = np.array([counts[s].get(cat, 0) for s in ordered_sleeves], dtype=float)
    if widths.sum() == 0:
        continue
    bars = ax.barh(y, widths, left=lefts, height=bar_height,
                   color=COLORS[cat], label=cat, edgecolor="white", linewidth=0.5)
    # Add count labels on each segment
    for i, (bar, w) in enumerate(zip(bars, widths)):
        if w > 0:
            cx = lefts[i] + w / 2
            ax.text(cx, y[i], str(int(w)),
                    ha="center", va="center", color="white",
                    fontsize=9, fontweight="bold")
    lefts += widths

ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=11)
ax.invert_yaxis()
ax.set_xlabel("Number of Instruments", fontsize=12, labelpad=8)
ax.set_title("Instrument Universe by Sleeve", fontsize=15, fontweight="bold", pad=14)

# Clean up spines
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")
ax.spines["left"].set_color("#CCCCCC")
ax.tick_params(axis="x", colors="#666666")
ax.tick_params(axis="y", colors="#333333", length=0)

# Legend at top-right, horizontal
ax.legend(loc="upper right", frameon=False, ncol=len(CATEGORIES), fontsize=9)

plt.tight_layout()

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = os.path.dirname(__file__)
out_path = os.path.join(out_dir, "instrument_coverage.png")
fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
print(f"Saved: {out_path}")

desktop_path = os.path.expanduser("~/Desktop/instrument_coverage.png")
shutil.copy2(out_path, desktop_path)
print(f"Copied: {desktop_path}")

plt.close(fig)
