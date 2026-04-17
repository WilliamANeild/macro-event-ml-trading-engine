import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict

fig, ax = plt.subplots(1, 1, figsize=(26, 14), dpi=300)
ax.set_xlim(0, 26)
ax.set_ylim(0, 14)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# ── Color palette ──
NAVY_DEEP    = '#0B2545'
NAVY_MID     = '#13497B'
SLATE_BLUE   = '#2C5F8A'
SLATE_PURPLE = '#5B4A7A'
BLUE_GRAY_1  = '#3A6B96'
BLUE_GRAY_2  = '#4A7FAA'
MUTED_PURPLE = '#6B5B8A'
LIGHT_SLATE  = '#D5DCE4'
PILL_BG      = '#F0F2F5'
PILL_BORDER  = '#A8B2BF'
TEXT_DARK     = '#1A1A2E'
TEXT_MED      = '#3A3A50'
CONNECTOR    = '#8A95A3'
WHITE        = '#FFFFFF'


def draw_box(x, y, w, h, fill, label, text_color=WHITE,
             font_size=12, shadow=True, border=None, border_w=1.5):
    cx, cy = x + w/2, y + h/2
    if shadow:
        s = patches.FancyBboxPatch(
            (x + 0.05, y - 0.05), w, h,
            boxstyle="round,pad=0.12", facecolor='#0000000A',
            edgecolor='none', zorder=1)
        ax.add_patch(s)
    ec = border if border else 'none'
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.12", facecolor=fill,
        edgecolor=ec, linewidth=border_w, zorder=2)
    ax.add_patch(rect)
    ax.text(cx, cy, label, ha='center', va='center',
            fontsize=font_size, fontweight='bold', color=text_color,
            zorder=3, linespacing=1.2, multialignment='center')
    return cx, y, y + h


def draw_pill(x, y, text):
    w, h = 1.45, 0.42
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.06", facecolor=PILL_BG,
        edgecolor=PILL_BORDER, linewidth=0.7, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center',
            fontsize=7.5, color=TEXT_MED, zorder=3)


def vline(x, y1, y2):
    ax.plot([x, x], [y1, y2], color=CONNECTOR, lw=1.3, zorder=1, solid_capstyle='round')


def hline(x1, x2, y):
    ax.plot([x1, x2], [y, y], color=CONNECTOR, lw=1.3, zorder=1, solid_capstyle='round')


# ════════════════════════════════════════
# ROW 0 — Master box
# ════════════════════════════════════════
mw, mh = 4.2, 1.4
mx = (26 - mw) / 2
my = 11.8
mcx, mbot, mtop = draw_box(mx, my, mw, mh, NAVY_DEEP,
                            "Macro Event\nTheme Hierarchy", font_size=22,
                            border=NAVY_MID, border_w=2.5)

# ════════════════════════════════════════
# ROW 1 — Major sleeves
# ════════════════════════════════════════
sw, sh = 3.0, 1.1
sy = 7.0
sleeves = [
    ("Shipping",              SLATE_BLUE),
    ("Defense",               NAVY_MID),
    ("Rates",                 BLUE_GRAY_1),
    ("Commodities",           MUTED_PURPLE),
    ("Sanctions &\nTrade",    SLATE_PURPLE),
    ("Crypto\nRegimes",       BLUE_GRAY_2),
]
ns = len(sleeves)
margin = 1.5
avail = 26 - 2 * margin
sleeve_gap = (avail - ns * sw) / (ns - 1)

sleeve_cx = []
bus_y1 = sy + sh + 0.6  # horizontal bus between master and sleeves

vline(mcx, mbot, bus_y1)

for i, (label, color) in enumerate(sleeves):
    sx = margin + i * (sw + sleeve_gap)
    cx, sbot, stop = draw_box(sx, sy, sw, sh, color, label, font_size=17)
    sleeve_cx.append(cx)
    vline(cx, stop, bus_y1)

hline(sleeve_cx[0], sleeve_cx[-1], bus_y1)

# ════════════════════════════════════════
# ROW 2 — Subthemes (with example details as subtitles)
# ════════════════════════════════════════
sub_w, sub_h = 1.5, 1.2
sub_y = 1.2

# (parent_sleeve_idx, label)
all_subs = [
    (0, "Chokepoints"),
    (0, "Port Clusters"),
    (1, "Regional\nConflict"),
    (1, "Defense\nSupply Chain"),
    (2, "Inflation\nShock"),
    (2, "Flight to\nSafety"),
    (2, "Policy Regime\nShift"),
    (3, "Energy\nShock"),
    (3, "Industrial\nInputs"),
    (4, "Export\nControls"),
    (4, "Trade Flow\nDisruption"),
    (5, "Risk\nSentiment"),
    (5, "Liquidity\nStress"),
]

n_subs = len(all_subs)
sub_margin = 1.5
sub_avail = 26 - 2 * sub_margin
sub_gap = (sub_avail - n_subs * sub_w) / (n_subs - 1)

sub_positions = {}
sub_cx_list = []

for i, (pidx, label) in enumerate(all_subs):
    bx = sub_margin + i * (sub_w + sub_gap)
    cx, sbot, stop = draw_box(bx, sub_y, sub_w, sub_h, LIGHT_SLATE,
                               label, text_color=TEXT_DARK, font_size=13,
                               shadow=False, border=PILL_BORDER, border_w=0.8)
    sub_positions[label] = cx
    sub_cx_list.append((pidx, cx, stop))

# Draw tree connectors: vertical from sleeve, horizontal bar at midpoint, verticals to children
groups = defaultdict(list)
for pidx, label in all_subs:
    groups[pidx].append(sub_positions[label])

# Bar at midpoint between sleeve bottom and subtheme top
mid_y = sub_y + sub_h + (sy - sub_y - sub_h) / 2

for pidx, cxs in groups.items():
    pcx = sleeve_cx[pidx]
    # Vertical from sleeve bottom to midpoint
    vline(pcx, sy, mid_y)
    # Horizontal segments from parent center to each child (T-junction, not cross)
    all_x = sorted(cxs)
    if len(all_x) > 1:
        hline(min(pcx, all_x[0]), max(pcx, all_x[-1]), mid_y)
    elif all_x[0] != pcx:
        hline(min(pcx, all_x[0]), max(pcx, all_x[0]), mid_y)
    # Verticals from midpoint down to each subtheme
    for scx in cxs:
        vline(scx, sub_y + sub_h, mid_y)


# ════════════════════════════════════════
plt.tight_layout(pad=0.5)
plt.savefig(
    'presentation/hierarchy_diagram.png',
    dpi=200,
    bbox_inches='tight',
    facecolor='#FFFFFF',
    edgecolor='none',
)
print("Saved presentation/hierarchy_diagram.png")
