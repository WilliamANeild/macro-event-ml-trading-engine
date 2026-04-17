import matplotlib.pyplot as plt

groups = [
    ("FRED Macro Series", [
        "VIXCLS — VIX implied volatility",
        "DGS2 — 2-year Treasury yield",
        "DGS5 — 5-year Treasury yield",
        "DGS10 — 10-year Treasury yield",
        "DGS30 — 30-year Treasury yield",
        "T10Y2Y — 10Y-2Y curve spread",
        "T10Y3M — 10Y-3M curve spread",
        "DFF — Fed funds effective rate",
        "DFII10 — 10Y TIPS real yield",
        "T5YIE — 5Y breakeven inflation",
        "T10YIE — 10Y breakeven inflation",
        "T5YIFR — 5Y5Y forward inflation",
        "BAMLH0A0HYM2 — HY bond spread",
        "BAMLC0A0CM — IG bond spread",
        "BAMLH0A3HYC — CCC bond spread",
        "BAMLH0A1HYBB — BB bond spread",
        "T10YFF — 10Y-fed funds spread",
        "DCOILWTICO — WTI crude price",
        "DCOILBRENTEU — Brent crude price",
        "DTWEXBGS — Trade-weighted USD",
        "WALCL — Fed balance sheet",
        "WTREGEN — Treasury general acct",
        "RRPONTSYD — Overnight reverse repo",
        "NFCI — Financial Conditions Idx",
        "STLFSI4 — Financial Stress Idx",
        "ICSA — Initial jobless claims",
        "CCSA — Continuing claims",
        "M2SL — M2 money supply",
        "SOFR — Secured overnight rate",
        "NAPM — ISM Manufacturing PMI",
        "UMCSENT — Consumer sentiment",
        "DHHNGSP — Henry Hub natgas",
    ]),
    ("Benchmarks & Volatility", [
        "SPY — S&P 500 ETF",
        "QQQ — Nasdaq 100 ETF",
        "IWM — Russell 2000 ETF",
        "DIA — Dow Jones ETF",
        "TLT — 20+ yr Treasury ETF",
        "HYG — High-yield bond ETF",
        "LQD — Investment-grade ETF",
        "EEM — Emerging market ETF",
        "EFA — Developed intl ETF",
        "^VIX — S&P 500 vol index",
        "^VIX3M — 3-month VIX",
        "^MOVE — Treasury vol index",
    ]),
    ("Commodities & Futures", [
        "GLD — Gold ETF",
        "SLV — Silver ETF",
        "DBC — Commodity basket ETF",
        "USL — Rolling crude oil ETF",
        "UNG — Natural gas ETF",
        "DBA — Agriculture ETF",
        "DBB — Base metals ETF",
        "COPX — Copper miners ETF",
        "BDRY — Baltic Dry ETF",
        "CL=F — WTI crude futures",
        "GC=F — Gold futures",
        "SI=F — Silver futures",
        "HG=F — Copper futures",
        "NG=F — Natural gas futures",
        "ZW=F — Wheat futures",
        "ZC=F — Corn futures",
        "ZS=F — Soybean futures",
    ]),
    ("Foreign Exchange", [
        "EURUSD=X — Euro / USD",
        "USDJPY=X — USD / Yen",
        "GBPUSD=X — Pound / USD",
        "USDMXN=X — USD / Peso",
        "USDZAR=X — USD / Rand",
        "USDCNY=X — USD / Yuan",
    ]),
    ("Defense Equities", [
        "ITA — Aerospace & Defense ETF",
        "XAR — Equal-Weight A&D ETF",
        "PPA — Invesco A&D ETF",
        "LMT — Lockheed Martin",
        "RTX — Raytheon",
        "NOC — Northrop Grumman",
        "GD — General Dynamics",
        "BA — Boeing",
        "HII — Huntington Ingalls",
        "LDOS — Leidos",
        "AXON — Axon Enterprise",
        "KTOS — Kratos Defense",
        "TXT — Textron",
    ]),
    ("Shipping Equities", [
        "ZIM — Zim Integrated",
        "DAC — Danaos Corp",
        "GOGL — Golden Ocean",
        "EGLE — Eagle Bulk",
        "FRO — Frontline (tankers)",
        "INSW — Intl Seaways",
        "STNG — Scorpio Tankers",
        "MATX — Matson (Pacific)",
        "KEX — Kirby Corp (barges)",
        "SBLK — Star Bulk",
        "GSL — Global Ship Lease",
    ]),
    ("Energy Equities", [
        "XOM — ExxonMobil",
        "CVX — Chevron",
        "COP — ConocoPhillips",
        "SLB — Schlumberger",
        "EOG — EOG Resources",
        "ENPH — Enphase (solar)",
        "NEE — NextEra (renewables)",
        "XLE — Energy Sector SPDR",
    ]),
    ("Rates-Sensitive Equities", [
        "JPM — JPMorgan Chase",
        "BAC — Bank of America",
        "GS — Goldman Sachs",
        "AGNC — AGNC Investment",
        "VGIT — Vanguard Mid Tsy",
        "XLF — Financial SPDR",
    ]),
    ("Crypto Sleeve", [
        "BTC-USD — Bitcoin",
        "ETH-USD — Ethereum",
        "COIN — Coinbase",
        "RIOT — Riot Platforms",
        "MARA — Marathon Digital",
        "SQ — Block / Square",
    ]),
    ("GDELT Event Features", [
        "event_count — volume",
        "event_intensity — weighted vol",
        "event_intensity_z — vs 52wk",
        "event_novelty — new headlines",
        "event_acceleration — wk/wk chg",
        "event_source_diversity",
        "event_tone — sentiment",
        "event_goldstein_mean",
        "event_goldstein_min",
        "event_cameo_severity",
    ]),
    ("Cross-Theme & Regime", [
        "coactivation_conflict_shipping",
        "coactivation_conflict_energy",
        "coactivation_sanctions_shipping",
        "coactivation_rates_fx",
        "coactivation_count",
        "already_priced_score",
        "regime_state (4 states)",
    ]),
    ("GPS-Fenced Chokepoints", [
        "SHP_HRM_010 — Strait of Hormuz",
        "SHP_BAB_011 — Bab el-Mandeb",
        "SHP_SUE_012 — Suez Canal",
        "SHP_PAN_016 — Panama Canal",
        "SHP_MAL_015 — Malacca Strait",
        "SHP_TWN_014 — Taiwan Strait",
        "SHP_TRK_070 — Turkish Straits",
        "SHP_GIB_071 — Strait of Gibraltar",
        "SHP_CGH_072 — Cape of Good Hope",
        "SHP_DAN_073 — Danish Straits",
    ]),
]

# Flatten
all_items = []
for title, entries in groups:
    all_items.append(("section", title))
    for e in entries:
        all_items.append(("entry", e))

# 5 columns, ~33 visual lines each (entries + 2 per header)
# Col 1: FRED(32+2) = 34
# Col 2: Benchmarks(12+2) + Commodities(17+2) = 33
# Col 3: Defense(13+2) + Shipping(11+2) + FX(6+2) = 36
# Col 4: Energy(8+2) + Rates(6+2) + Crypto(6+2) + CrossTheme(7+2) = 35
# Col 5: GDELT(10+2) + Chokepoints(10+2) = 24... add more
# Better:
# Col 1: FRED(32+2) = 34
# Col 2: Benchmarks(12+2) + FX(6+2) + Crypto(6+2) = 30
# Col 3: Commodities(17+2) + Energy(8+2) + Rates(6+2) = 37...
# Let me just do:
# Col 1: FRED(32+2) = 34
# Col 2: Benchmarks(12+2) + Defense(13+2) = 29
# Col 3: Commodities(17+2) + FX(6+2) = 27
# Col 4: Shipping(11+2) + Energy(8+2) + Crypto(6+2) = 31
# Col 5: Rates(6+2) + GDELT(10+2) + CrossTheme(7+2) + Chokepoints(10+2) = 41
# Still uneven. Try:
# Col 1: FRED(32+2) = 34
# Col 2: Benchmarks(12+2) + Defense(13+2) + FX(6+2) = 35
# Col 3: Commodities(17+2) + Shipping(11+2) = 32
# Col 4: Energy(8+2) + Rates(6+2) + Crypto(6+2) + CrossTheme(7+2) = 34
# Col 5: GDELT(10+2) + Chokepoints(10+2) = 24
# FRED is forcing col1 to 34. Split FRED across cols?
# No, keep groups intact. Accept slight unevenness.
col1_groups = [0]               # FRED = 34
col2_groups = [1, 4, 3]         # Benchmarks, Defense, FX = 35
col3_groups = [2, 5]            # Commodities, Shipping = 32
col4_groups = [6, 7, 8, 10]     # Energy, Rates, Crypto, CrossTheme = 35
col5_groups = [9, 11]           # GDELT, Chokepoints = 24

def build_col(indices):
    items = []
    for idx in indices:
        title, entries = groups[idx]
        items.append(("section", title))
        for e in entries:
            items.append(("entry", e))
    return items

cols = [build_col(col1_groups), build_col(col2_groups), build_col(col3_groups), build_col(col4_groups), build_col(col5_groups)]

def col_height(items):
    return sum(2.0 if t == "section" else 1 for t, _ in items)

max_h = max(col_height(c) for c in cols)

# Square figure
size = 18
fig_h = 10
fig, ax = plt.subplots(1, 1, figsize=(size, fig_h), dpi=200)
ax.set_xlim(0, size)
ax.set_ylim(0, fig_h)
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

NAVY = '#0B2545'
BLACK = '#1A1A1A'

col_w = size / 5
col_x = [0.3, 3.8, 7.3, 10.8, 14.3]
line_h = (fig_h - 1.0) / max_h

for col_idx, col_items in enumerate(cols):
    x = col_x[col_idx]
    y = fig_h - 0.4

    for item_type, text in col_items:
        if item_type == "section":
            y -= line_h * 0.5
            ax.text(x, y, text.upper(), fontsize=10, fontweight='bold',
                    color=NAVY, va='top', zorder=3)
            ax.plot([x, x + 2.8], [y - 0.15, y - 0.15],
                    color=NAVY, lw=0.8, zorder=1)
            y -= line_h * 1.0
        else:
            ax.text(x + 0.1, y, text, fontsize=8.5,
                    color=BLACK, va='top', zorder=3, family='monospace')
            y -= line_h

plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
plt.savefig(
    'presentation/signal_map.png',
    dpi=200,
    bbox_inches='tight',
    facecolor='#FFFFFF',
    edgecolor='none',
)
print("Saved presentation/signal_map.png")
