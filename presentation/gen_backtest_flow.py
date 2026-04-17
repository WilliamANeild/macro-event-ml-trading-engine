import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(1, 1, figsize=(24, 5), dpi=200)
ax.set_xlim(0, 24)
ax.set_ylim(0, 5)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# Color palette
NAVY_DEEP    = '#0B2545'
NAVY_MID     = '#13497B'
SLATE_PURPLE = '#4E5A80'
COOL_GRAY    = '#3A6B96'
MUTED_PURPLE = '#5B4A7A'
WHITE        = '#FFFFFF'
CONNECTOR    = '#000000'
FOOTER_COLOR = '#6B7280'

steps = [
    ("Historical\nEvent Set",          "Real conflicts, sanctions,\nand macro shocks as inputs",     NAVY_DEEP),
    ("Walk-Forward\nTesting",           "Testing one period at a time,\nnever peeking ahead",        NAVY_MID),
    ("Signal & Trade\nConstruction",    "Turning forecasts into\nactual portfolio positions",        SLATE_PURPLE),
    ("Performance\nAttribution",        "Breaking down returns by\ntheme, cost, and timing",         COOL_GRAY),
    ("Event Replay\nReview",            "Replaying key events to\nsee what drove each trade",        MUTED_PURPLE),
]

n = len(steps)
box_w = 3.4
box_h = 2.8
gap = 1.0
total_w = n * box_w + (n - 1) * gap
start_x = (24 - total_w) / 2
y_center = 2.5

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
        fontsize=16, fontweight='bold',
        color=WHITE,
        zorder=3,
        linespacing=1.25,
    )

    # Subtitle
    ax.text(
        x + box_w / 2, y_center - 0.6,
        sub,
        ha='center', va='center',
        fontsize=12.5,
        color='#ffffffdd',
        zorder=3,
        linespacing=1.4,
    )

    # Arrow to next box
    if i < n - 1:
        arrow_x_start = x + box_w + 0.12
        arrow_x_end = x + box_w + gap - 0.12
        ax.annotate(
            '',
            xy=(arrow_x_end, y_center),
            xytext=(arrow_x_start, y_center),
            arrowprops=dict(
                arrowstyle='-|>',
                color=CONNECTOR,
                lw=2.0,
                mutation_scale=18,
            ),
            zorder=4,
        )


plt.tight_layout(pad=0.3)
plt.savefig(
    'presentation/backtest_flowchart.png',
    dpi=200,
    bbox_inches='tight',
    facecolor='#FFFFFF',
    edgecolor='none',
)
print("Saved presentation/backtest_flowchart.png")
