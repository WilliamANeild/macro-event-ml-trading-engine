import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(1, 1, figsize=(22, 4), dpi=200)
ax.set_xlim(0, 22)
ax.set_ylim(0, 4)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# Color palette (matching hierarchy diagram)
NAVY_DEEP    = '#0B2545'
NAVY_MID     = '#13497B'
SLATE_BLUE   = '#2C5F8A'
MUTED_PURPLE = '#5B4A7A'
WHITE        = '#FFFFFF'

steps = [
    ("Meta-Learner\nSignal Output",        "Aggregated direction, severity,\nand confidence from expert models", NAVY_DEEP),
    ("Trade Expression\nSelection",        "Maps signal to ETF basket,\nsingle-name equity, or blend",         NAVY_MID),
    ("Portfolio Position\nSizing",         "Converts conviction scores\ninto constrained portfolio weights",   SLATE_BLUE),
    ("Derivatives\nConvexity Overlay",     "Adds option hedges only\nin extreme macro regimes",               MUTED_PURPLE),
]

n = len(steps)
box_w = 3.8
box_h = 2.8
gap = 1.2
total_w = n * box_w + (n - 1) * gap
start_x = (22 - total_w) / 2
y_center = 2.0

for i, (title, sub, color) in enumerate(steps):
    x = start_x + i * (box_w + gap)
    y = y_center - box_h / 2

    # Shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.05, y - 0.05), box_w, box_h,
        boxstyle="round,pad=0.15",
        facecolor='#0000000A',
        edgecolor='none',
        zorder=1,
    )
    ax.add_patch(shadow)

    # Box
    rect = patches.FancyBboxPatch(
        (x, y), box_w, box_h,
        boxstyle="round,pad=0.15",
        facecolor=color,
        edgecolor='none',
        zorder=2,
    )
    ax.add_patch(rect)

    # Title
    ax.text(
        x + box_w / 2, y_center + 0.45,
        title,
        ha='center', va='center',
        fontsize=17, fontweight='bold',
        color=WHITE,
        zorder=3,
        linespacing=1.25,
    )

    # Subtitle
    ax.text(
        x + box_w / 2, y_center - 0.55,
        sub,
        ha='center', va='center',
        fontsize=12.5,
        color='#ffffffcc',
        zorder=3,
        linespacing=1.4,
    )

    # Arrow to next box
    if i < n - 1:
        arrow_x_start = x + box_w + 0.15
        arrow_x_end = x + box_w + gap - 0.15
        ax.annotate(
            '',
            xy=(arrow_x_end, y_center),
            xytext=(arrow_x_start, y_center),
            arrowprops=dict(
                arrowstyle='-|>',
                color='#1a1a1a',
                lw=2.2,
                mutation_scale=20,
            ),
            zorder=4,
        )

plt.tight_layout(pad=0.3)
plt.savefig(
    'presentation/signal_flowchart.png',
    dpi=200,
    bbox_inches='tight',
    facecolor='#FFFFFF',
    edgecolor='none',
)
print("Saved presentation/signal_flowchart.png")
