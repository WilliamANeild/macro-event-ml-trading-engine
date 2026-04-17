import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(1, 1, figsize=(20, 4), dpi=200)
ax.set_xlim(0, 20)
ax.set_ylim(0, 4)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#ffffff')

# Steps: (title, subtitle, color)
steps = [
    ("Event + Market\nInputs",       "News, macro, and\nprice data",           "#0B2545"),
    ("Feature\nLayer",               "Regime, stress, and\nevent features",     "#13497B"),
    ("Localized\nExperts",           "Theme-specific\nsignal models",           "#1B6AAF"),
    ("Meta\nLayer",                  "Combines expert\noutputs",                "#6B4C9A"),
    ("Trade\nExpression",            "ETF, single-name,\nor blend",             "#2180C7"),
    ("Portfolio\nConstruction",      "Sizing, caps, and\nconstraints",          "#1565A8"),
    ("Optional\nOverlay",           "Convexity in\nextreme regimes",            "#0D3B66"),
]

n = len(steps)
box_w = 1.9
box_h = 2.6
gap = 0.9
total_w = n * box_w + (n - 1) * gap
start_x = (20 - total_w) / 2
y_center = 2.0

for i, (title, sub, color) in enumerate(steps):
    x = start_x + i * (box_w + gap)
    y = y_center - box_h / 2

    # Shadow
    shadow = patches.FancyBboxPatch(
        (x + 0.04, y - 0.04), box_w, box_h,
        boxstyle="round,pad=0.15",
        facecolor='#00000010',
        edgecolor='none',
        zorder=1,
    )
    ax.add_patch(shadow)

    # Rounded rectangle
    rect = patches.FancyBboxPatch(
        (x, y), box_w, box_h,
        boxstyle="round,pad=0.15",
        facecolor=color,
        edgecolor='none',
        zorder=2,
    )
    ax.add_patch(rect)

    # Title text
    ax.text(
        x + box_w / 2, y_center + 0.35,
        title,
        ha='center', va='center',
        fontsize=11, fontweight='bold',
        color='#ffffff',
        zorder=3,
        linespacing=1.25,
    )

    # Subtitle text
    ax.text(
        x + box_w / 2, y_center - 0.5,
        sub,
        ha='center', va='center',
        fontsize=8,
        color='#ffffffcc',
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
                color='#1a1a1a',
                lw=2.0,
                mutation_scale=18,
            ),
            zorder=4,
        )

plt.tight_layout(pad=0.3)
plt.savefig(
    'presentation/pipeline_flowchart.png',
    dpi=200,
    bbox_inches='tight',
    facecolor='#ffffff',
    edgecolor='none',
)
print("Saved presentation/pipeline_flowchart.png")
