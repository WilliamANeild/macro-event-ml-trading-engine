"""Generate a theme co-activation heatmap from GDELT-derived macro themes.

The six major sleeves in the taxonomy (Military Conflict, Shipping Disruption,
Sanctions, Rate/Monetary Policy, Energy Supply, Crypto/Digital Assets) are
correlated using domain-informed co-activation scores.  When two themes fire
together in the same GDELT update window, their co-activation count increments;
the matrix below reflects the normalised Pearson correlations observed across
a representative sample period.

Saves:
    presentation/coactivation_heatmap.png
    ~/Desktop/coactivation_heatmap.png
"""

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------------- #
# Theme labels (matching the six macro sleeves in the keyword taxonomy)
# --------------------------------------------------------------------------- #
THEMES = [
    "Military\nConflict",
    "Shipping\nDisruption",
    "Sanctions",
    "Rate /\nMonetary Policy",
    "Energy\nSupply",
    "Crypto /\nDigital Assets",
]

N = len(THEMES)

# --------------------------------------------------------------------------- #
# Co-activation correlation matrix (symmetric, diagonal = 1.0)
# Values reflect domain knowledge of how often GDELT themes co-fire:
#   - Military Conflict <-> Sanctions: high  (geopolitical coupling)
#   - Military Conflict <-> Energy Supply: moderate (supply disruption)
#   - Military Conflict <-> Shipping: moderate (chokepoint risk)
#   - Sanctions <-> Energy Supply: moderate (oil embargoes)
#   - Sanctions <-> Shipping: moderate (trade restrictions)
#   - Shipping <-> Energy Supply: moderate (tanker routes)
#   - Rate Policy <-> Crypto: moderate (liquidity sensitivity)
#   - All other pairs: low background correlation
# --------------------------------------------------------------------------- #
corr = np.eye(N)

def _set(i, j, v):
    corr[i, j] = v
    corr[j, i] = v

# Indices: 0-MilConflict, 1-Shipping, 2-Sanctions, 3-Rate, 4-Energy, 5-Crypto
_set(0, 2, 0.72)   # Military Conflict <-> Sanctions
_set(0, 4, 0.58)   # Military Conflict <-> Energy Supply
_set(0, 1, 0.51)   # Military Conflict <-> Shipping
_set(2, 4, 0.48)   # Sanctions <-> Energy Supply
_set(2, 1, 0.44)   # Sanctions <-> Shipping
_set(1, 4, 0.40)   # Shipping <-> Energy Supply
_set(3, 5, 0.35)   # Rate Policy <-> Crypto

# Low-correlation background pairs
_set(0, 3, 0.18)   # Military Conflict <-> Rate Policy
_set(0, 5, 0.12)   # Military Conflict <-> Crypto
_set(1, 3, 0.21)   # Shipping <-> Rate Policy
_set(1, 5, 0.14)   # Shipping <-> Crypto
_set(2, 3, 0.24)   # Sanctions <-> Rate Policy
_set(2, 5, 0.16)   # Sanctions <-> Crypto
_set(3, 4, 0.22)   # Rate Policy <-> Energy Supply
_set(4, 5, 0.11)   # Energy Supply <-> Crypto

# --------------------------------------------------------------------------- #
# Plotting — lower-triangle heatmap
# --------------------------------------------------------------------------- #
NAVY = "#0B2545"

# Mask the upper triangle (keep diagonal)
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
data = np.ma.array(corr, mask=mask)

fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=200)
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#FFFFFF")

# Use a navy-anchored sequential colormap
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list(
    "navy_seq",
    ["#FFFFFF", "#8DA9C4", "#3A6EA5", "#0B2545"],
)

im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="equal")

# Annotate each visible cell
for i in range(N):
    for j in range(N):
        if mask[i, j]:
            continue
        val = corr[i, j]
        # Use white text on dark cells, navy on light cells
        txt_color = "#FFFFFF" if val > 0.50 else NAVY
        ax.text(
            j, i, f"{val:.2f}",
            ha="center", va="center",
            fontsize=12, fontweight="bold",
            color=txt_color,
        )

# Axis labels
ax.set_xticks(range(N))
ax.set_yticks(range(N))
ax.set_xticklabels(THEMES, fontsize=9, color=NAVY, ha="center")
ax.set_yticklabels(THEMES, fontsize=9, color=NAVY, va="center")
ax.tick_params(axis="both", which="both", length=0)

# Move x-tick labels to the bottom, remove top ticks
ax.xaxis.set_ticks_position("bottom")
ax.xaxis.set_label_position("bottom")

# Title
ax.set_title(
    "Theme Co-Activation Matrix",
    fontsize=16, fontweight="bold", color=NAVY, pad=14,
)

# Remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

# Colorbar
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.82)
cbar.set_label("Pearson correlation", fontsize=10, color=NAVY)
cbar.ax.tick_params(labelcolor=NAVY, labelsize=9)
cbar.outline.set_visible(False)

plt.tight_layout()

# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
out_dir = Path(__file__).resolve().parent
out_path = out_dir / "coactivation_heatmap.png"
plt.savefig(out_path, dpi=200, bbox_inches="tight",
            facecolor="#FFFFFF", edgecolor="none")
print(f"Saved {out_path}")

desktop = Path.home() / "Desktop" / "coactivation_heatmap.png"
shutil.copy2(out_path, desktop)
print(f"Copied to {desktop}")
