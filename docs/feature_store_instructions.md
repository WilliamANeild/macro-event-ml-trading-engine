# Feature Store and Market State Layer — Build Guide

This is for whoever is working on the feature store. The schema and basic builder exist but almost everything else needs to be built. The experts are currently running on nearly empty feature vectors, so this is blocking the whole system from producing real signals.

---

## What's Already Done

- `src/engine/features/schemas.py` — `FeatureRow` dataclass is good to go. Has as_of_date, theme, subtheme, and a values dict for all features.
- `src/engine/features/builder.py` — `FeatureBuilder` exists but only computes 1-day returns per symbol. Needs to be expanded significantly.
- FRED loader (`src/engine/data/fred_loader.py`) already pulls macro series from FRED. Currently only 5 series but the expansion is documented.
- Yahoo loader (`src/engine/data/yahoo_loader.py`) pulls price data for any ticker. Works fine.
- Full feature engineering plan already written at `docs/feature_engineering_plan.md` — has exact column names, formulas, and window sizes for everything below.

---

## What Needs to Be Built

### 1. Expand FeatureBuilder with Return Features

Right now it only does 1-day returns. Add:
- **5-day return** per symbol: `returns.iloc[-5:].sum()`
- **20-day return** (momentum): `returns.iloc[-20:].sum()`
- **60-day return**: `returns.iloc[-60:].sum()`

Name them like `{symbol}_return_1d`, `{symbol}_return_5d`, `{symbol}_return_20d`, `{symbol}_return_60d`.

### 2. Volatility Features

For each symbol:
- **20-day realized vol**: `returns.iloc[-20:].std() * sqrt(252)` (annualized)
- **60-day realized vol**: `returns.iloc[-60:].std() * sqrt(252)`
- **Vol of vol**: std of rolling 20-day vol over the last 60 days
- **Vol z-score**: `(current_20d_vol - 60d_mean_vol) / 60d_std_vol`

Name them `{symbol}_vol_20d`, `{symbol}_vol_60d`, `{symbol}_vol_of_vol`, `{symbol}_vol_zscore`.

### 3. Drawdown Features

For each symbol:
- **Current drawdown**: how far the price is below its rolling 60-day high. `price / rolling_max - 1`
- **Days in drawdown**: count of consecutive days below the rolling high

Name them `{symbol}_drawdown`, `{symbol}_drawdown_days`.

### 4. Cross-Asset Correlation Features

These are computed across pairs of key instruments, not per-symbol:
- **20-day rolling correlation** between SPY-TLT, SPY-GLD, SPY-HYG, SPY-EEM
- **60-day rolling correlation** for the same pairs
- When SPY-TLT correlation turns positive, the 60/40 hedge breaks down — that's a critical regime signal

Name them like `corr_SPY_TLT_20d`, `corr_SPY_GLD_60d`, etc.

### 5. Dispersion Features

Measures how much instruments within a sleeve are diverging from each other:
- **Within-sleeve dispersion**: std of returns across all instruments in a sleeve (defense, shipping, etc.)
- **Cross-sleeve dispersion**: std of sleeve-average returns

High dispersion within a sleeve = single-name alpha opportunity. Low dispersion = use ETFs.

Name them `dispersion_defense_20d`, `dispersion_shipping_20d`, `dispersion_cross_sleeve_20d`.

### 6. Macro Features from FRED

The FRED loader needs its `DEFAULT_SERIES` expanded. The current 5 series should become at least 17. Here's the Tier 1 set to add:

```python
DEFAULT_SERIES = {
    "VIXCLS": "vix",
    "DGS2": "yield_2y",
    "DGS5": "yield_5y",
    "DGS10": "yield_10y",
    "DGS30": "yield_30y",
    "T10Y2Y": "curve_10y2y",
    "T10Y3M": "curve_10y3m",
    "DFF": "fed_funds",
    "DFII10": "real_rate_10y",
    "T5YIE": "breakeven_5y",
    "T10YIE": "breakeven_10y",
    "T5YIFR": "fwd_inflation_5y5y",
    "BAMLH0A0HYM2": "hy_oas",
    "BAMLC0A0CM": "ig_oas",
    "DCOILWTICO": "oil_wti",
    "DCOILBRENTEU": "oil_brent",
    "DTWEXBGS": "usd_broad",
}
```

Then compute features from these:
- **Yield curve slope**: `T10Y2Y` direct, plus binary inversion flag (`T10Y2Y < 0`)
- **Credit spread**: `hy_oas - ig_oas` (HY premium over IG)
- **Real rate momentum**: 20-day change in `DFII10`
- **Oil spread**: `oil_brent - oil_wti` (geopolitical premium)
- **USD momentum**: 5-day and 20-day change in `usd_broad`
- **VIX z-score**: rolling 60-day z-score of VIX

### 7. Z-Scores and Normalization

For all features, compute robust z-scores:
- `z = (value - rolling_median) / rolling_MAD` where MAD = median absolute deviation
- Use 60-day rolling window
- This makes features comparable across different scales

### 8. Weekly Aggregation

The system runs on weekly features (daily signals update, but portfolio rebalances weekly). Convert daily features to weekly using:
- **Returns**: sum over the week
- **Volatility**: last day's value (already a rolling stat)
- **Correlations**: last day's value
- **Macro levels**: last day's value
- **Macro changes**: sum of daily changes over the week

---

## Build Order

1. **Return features** (1d, 5d, 20d, 60d) — easiest, extend existing code
2. **Volatility features** — straightforward rolling stats
3. **Expand FRED series** — just update the dict in `fred_loader.py`
4. **Macro derived features** — spreads, z-scores from FRED data
5. **Drawdown features** — rolling max tracking
6. **Cross-asset correlations** — rolling pairwise correlations
7. **Dispersion features** — within-sleeve and cross-sleeve
8. **Z-score normalization** — wrap everything in robust z-scores
9. **Weekly aggregation** — temporal rollup

## Where to Put Things

- All feature computation goes in `src/engine/features/builder.py` — expand the `FeatureBuilder.build()` method
- FRED series expansion goes in `src/engine/data/fred_loader.py`
- The output format stays the same — just put more keys in the `FeatureRow.values` dict
- Naming convention: `{symbol}_{metric}_{window}` for per-instrument, `{metric}_{window}` for cross-asset

## Testing

- The existing tests should still pass (they don't check specific feature names)
- Add tests that verify feature count increases, values are finite, z-scores have mean ~0
- Test with synthetic data first (`SyntheticDataGenerator` produces enough history for rolling windows)

## Key Reference

- `docs/feature_engineering_plan.md` — the complete spec with all ~330 features, exact formulas, and which experts consume which features
- `docs/data_series_reference.md` — all FRED series with descriptions and transformation notes
