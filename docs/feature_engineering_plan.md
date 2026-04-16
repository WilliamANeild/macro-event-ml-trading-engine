# Feature Engineering Plan

Complete specification for the feature engineering pipeline of the macro-event ML trading engine. Covers raw data aggregation, market state features (Part 2 / Rayna), event features (Part 3 / Logan), expert-specific feature sets (Part 4 / Joe), confirmation features, and anti-leakage rules.

**Pipeline cadence (from design doc Section 0):** Signals update daily. Features are aggregated weekly (Friday close to Friday close). Portfolio weights update weekly, except when the event state machine triggers intraweek action.

**Data sources:** All tickers and FRED series referenced here are defined in `docs/data_series_reference.md`.

---

## Table of Contents

1. [Raw Daily to Weekly Aggregation](#1-raw-daily-to-weekly-aggregation)
2. [Market State Features](#2-market-state-features)
3. [Event Features](#3-event-features)
4. [Expert-Specific Feature Sets](#4-expert-specific-feature-sets)
5. [Already-Priced Confirmation Features](#5-already-priced-confirmation-features)
6. [Anti-Leakage Checklist](#6-anti-leakage-checklist)
7. [Feature Schema Reference](#7-feature-schema-reference)

---

## 1. Raw Daily to Weekly Aggregation

### 1.1 Weekly Calendar

Weeks run **Monday through Friday**. The feature snapshot date is **Friday close** (the `as_of_date` in `FeatureRow`). All features for week W are computed from data up to and including the Friday close of week W.

For data that publishes with a lag (e.g., FRED T+1 series), use the value available as of Friday close. A FRED series with T+1 lag published on Thursday covers Wednesday's value; Friday's value becomes available Monday. Conservative rule: for T+1 FRED series, the latest usable value on Friday is Thursday's publication (reflecting Wednesday's data point). This is already handled by the existing `ffill()` logic in `FREDDataSource`.

### 1.2 Aggregation Methods by Data Type

| Data Type | Daily Frequency | Weekly Aggregation | Column Naming Convention |
|-----------|----------------|--------------------|--------------------------|
| **Equity/ETF/commodity prices** | Close prices | Friday close (point-in-time) | `{ticker}_close_w` |
| **Equity/ETF returns** | Daily log returns | Sum of daily log returns Mon-Fri = weekly log return | `{ticker}_ret_1w` |
| **Yield levels** (DGS2, DGS10, etc.) | Daily level | Friday close level | `{ticker}_level_w` |
| **Yield changes** | Daily delta | Sum of daily changes Mon-Fri = weekly change | `{ticker}_chg_1w` |
| **Spread levels** (T10Y2Y, HY OAS) | Daily level | Friday close level | `{ticker}_level_w` |
| **Spread changes** | Daily delta | Sum of daily changes Mon-Fri | `{ticker}_chg_1w` |
| **VIX-family** | Daily level | Friday close level + weekly high + weekly mean | `vix_close_w`, `vix_high_w`, `vix_mean_w` |
| **Volume** | Daily volume | Sum of daily volume Mon-Fri | `{ticker}_volume_w` |
| **Monthly macro** (CPI, NFP, etc.) | Monthly | Forward-filled to daily, then take Friday value | `{series}_level_w` |
| **Weekly macro** (WALCL, ICSA, etc.) | Weekly | Take latest available value as of Friday | `{series}_level_w` |
| **Event counts** | Daily event counts | Sum of daily counts Mon-Fri | `{theme}_count_1w` |
| **Event intensity** | Daily intensity scores | See Section 3 | `{theme}_intensity_1w` |

### 1.3 Robust Statistics for Weekly Features

Per the design doc (Layer A, "Weekly feature aggregation"), we prefer robust statistics over simple means:

| Statistic | Formula | When to Use |
|-----------|---------|-------------|
| **Median** | `np.median(daily_values)` | Default center estimate for noisy daily series |
| **Trimmed mean** | `scipy.stats.trim_mean(daily_values, proportiontocut=0.1)` | Center estimate when daily outliers are common (e.g., VIX intraweek spikes) |
| **MAD (Median Absolute Deviation)** | `1.4826 * np.median(abs(x - np.median(x)))` | Robust spread estimate |
| **Robust z-score** | `(x - trimmed_mean_trailing) / mad_trailing` | Normalization for all features fed to expert models |

The trailing window for robust z-scores defaults to **52 weeks** (260 trading days) unless otherwise specified.

### 1.4 Multi-Period Returns

For each instrument, compute returns over multiple horizons using Friday-close to Friday-close:

| Column Name | Formula | Window |
|-------------|---------|--------|
| `{ticker}_ret_1w` | `ln(close[t] / close[t-5])` | 1 week (5 trading days) |
| `{ticker}_ret_4w` | `ln(close[t] / close[t-20])` | 4 weeks (20 trading days) |
| `{ticker}_ret_13w` | `ln(close[t] / close[t-65])` | 13 weeks (65 trading days, ~1 quarter) |

These are always computed from daily close prices, not from pre-aggregated weekly data, to avoid alignment issues.

---

## 2. Market State Features

This section defines Rayna's Part 2 scope: the feature store and market state layer.

### 2.1 Returns Features

Computed per instrument in the tradable universe, plus benchmark instruments (SPY, TLT, GLD, HYG, EEM).

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `{ticker}_ret_1d` | `ln(close[t] / close[t-1])` | Most recent day's return (Friday) |
| `{ticker}_ret_1w` | `ln(close[t] / close[t-5])` | 1-week return |
| `{ticker}_ret_4w` | `ln(close[t] / close[t-20])` | 4-week return |
| `{ticker}_ret_1w_z` | `(ret_1w - trimmed_mean_52w(ret_1w)) / mad_52w(ret_1w)` | Z-scored 1-week return |
| `{ticker}_ret_4w_z` | Same z-score formula applied to ret_4w | Z-scored 4-week return |
| `{ticker}_ret_1w_rank` | Percentile rank of ret_1w within trailing 52w | Rank-based normalization, [0, 1] |

### 2.2 Volatility Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `{ticker}_rvol_20d` | `std(daily_log_returns[-20:]) * sqrt(252)` | 20-day annualized realized vol |
| `{ticker}_rvol_60d` | `std(daily_log_returns[-60:]) * sqrt(252)` | 60-day annualized realized vol |
| `{ticker}_rvol_ratio` | `rvol_20d / rvol_60d` | Vol regime indicator: >1 means vol expanding, <1 means contracting |
| `{ticker}_rvol_20d_z` | Robust z-score of rvol_20d over 52w trailing | Normalized vol level |
| `{ticker}_vol_of_vol` | `std(rolling_5d_std(daily_returns)[-20:])` | Volatility of volatility: instability of vol itself |
| `vix_close_w` | Friday close of VIXCLS | Direct VIX level |
| `vix_close_w_z` | Robust z-score of vix_close_w over 52w | Normalized VIX |
| `vix_term_slope` | `VIX3M_close / VIXCLS_close` | >1 = contango (normal), <1 = backwardation (stress) |
| `vix_term_slope_z` | Robust z-score of vix_term_slope over 52w | Normalized term structure |
| `move_close_w` | Friday close of ^MOVE | Bond vol level |
| `move_close_w_z` | Robust z-score over 52w | Normalized MOVE |
| `vix_move_ratio` | `VIXCLS / MOVE` | Cross-asset vol comparison |

### 2.3 Drawdown Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `{ticker}_drawdown` | `(close[t] / rolling_max(close, 252)) - 1` | Current drawdown from 252-day high, always <= 0 |
| `{ticker}_drawdown_depth` | `abs(drawdown)` | Positive measure of drawdown magnitude |
| `{ticker}_days_in_drawdown` | Count of consecutive days where close < rolling_max | Duration of current drawdown |
| `{ticker}_drawdown_z` | Robust z-score of drawdown_depth over 52w | How unusual is the current drawdown? |

### 2.4 Cross-Asset Correlation Features

Computed from daily log returns of benchmark instruments: SPY, TLT, GLD, HYG, EEM, CL=F, BTC-USD.

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `corr_{A}_{B}_20d` | `rolling_corr(ret_A, ret_B, window=20)` | Short-term pairwise correlation |
| `corr_{A}_{B}_60d` | `rolling_corr(ret_A, ret_B, window=60)` | Medium-term pairwise correlation |
| `corr_{A}_{B}_delta` | `corr_20d - corr_60d` | Correlation regime shift: positive = recent correlation increase |
| `corr_{A}_{B}_delta_z` | Robust z-score of corr_delta over 52w | How unusual is the correlation shift? |

**Key pairs to compute** (7 instruments = 21 pairs; prioritize these 10):

| Pair | Why It Matters |
|------|----------------|
| SPY-TLT | Stock-bond correlation; positive = 60/40 hedge broken |
| SPY-GLD | Risk-on vs. safe-haven |
| SPY-HYG | Equity-credit correlation; divergence = warning |
| SPY-EEM | DM-EM correlation; breakdown = contagion risk |
| SPY-CL=F | Equity-oil; depends on whether oil is supply or demand driven |
| TLT-GLD | Bond-gold; both up = flight to quality |
| CL=F-GLD | Oil-gold; both up = inflation/geopolitical premium |
| SPY-BTC | Crypto beta to equities |
| EEM-DTWEXBGS | EM equity vs. USD; inverse correlation expected |
| HYG-TLT | Credit vs. duration; spread = risk appetite |

### 2.5 Dispersion Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `dispersion_within_sleeve_{sleeve}` | `std([ret_1w for instruments in sleeve])` | How much do instruments within a sleeve diverge? High = opportunity for single-name expression |
| `dispersion_cross_sleeve` | `std([mean_ret_1w for each sleeve])` | How much do sleeves diverge from each other? High = differentiated themes |
| `dispersion_sectors` | `std([ret_1w for XLE, XLF, XLU, QQQ, IWM, EEM])` | Cross-sector dispersion (broad market) |
| `dispersion_sectors_z` | Robust z-score of dispersion_sectors over 52w | Normalized sector dispersion |
| `dispersion_commodities` | `std([ret_1w for CL=F, GC=F, HG=F, NG=F, ZW=F])` | Commodity complex dispersion |
| `dispersion_commodities_z` | Robust z-score over 52w | Normalized commodity dispersion |

### 2.6 Yield Curve and Rates Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `yield_2y_level` | DGS2 Friday close | 2Y Treasury yield |
| `yield_10y_level` | DGS10 Friday close | 10Y Treasury yield |
| `yield_2y_chg_1w` | DGS2 weekly change (bps) | Short-end movement |
| `yield_10y_chg_1w` | DGS10 weekly change (bps) | Long-end movement |
| `curve_10y2y_level` | T10Y2Y Friday close | Yield curve slope |
| `curve_10y2y_chg_1w` | T10Y2Y weekly change | Flattening/steepening |
| `curve_10y2y_inverted` | `1 if T10Y2Y < 0 else 0` | Binary inversion flag |
| `curve_10y3m_level` | T10Y3M Friday close | Fed-preferred recession indicator |
| `curve_10y3m_inverted` | `1 if T10Y3M < 0 else 0` | Binary inversion flag |
| `curve_butterfly` | `2 * DGS5 - DGS2 - DGS10` | Curvature measure |
| `real_rate_10y` | DFII10 Friday close | Real rate level |
| `real_rate_10y_chg_1w` | DFII10 weekly change | Real rate momentum |
| `real_rate_10y_chg_4w` | DFII10 4-week change | Real rate trend |
| `breakeven_5y` | T5YIE Friday close | Near-term inflation expectations |
| `breakeven_10y` | T10YIE Friday close | Medium-term inflation expectations |
| `fwd_inflation_5y5y` | T5YIFR Friday close | Long-term inflation anchoring |
| `fwd_inflation_5y5y_dev` | `T5YIFR - 2.0` | Deviation from Fed 2% target |
| `inflation_term_structure` | `T10YIE - T5YIE` | Inflation expectation curve |
| `fed_funds_level` | DFF Friday close | Policy rate |

### 2.7 Credit and Liquidity Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `hy_oas_level` | BAMLH0A0HYM2 Friday close | HY spread level |
| `hy_oas_chg_1w` | Weekly change in HY OAS | Credit momentum |
| `hy_oas_z` | Robust z-score over 52w | Normalized credit stress |
| `ig_oas_level` | BAMLC0A0CM Friday close | IG spread level |
| `hy_ig_spread` | `BAMLH0A0HYM2 - BAMLC0A0CM` | Excess HY premium over IG |
| `ccc_bb_spread` | `BAMLH0A3HYC - BAMLH0A1HYBB` | Credit quality stress |
| `ccc_bb_spread_z` | Robust z-score over 52w | Normalized quality stress |
| `net_liquidity` | `WALCL - WTREGEN - RRPONTSYD` | Fed liquidity proxy |
| `net_liquidity_chg_4w` | 4-week change in net_liquidity ($B) | Liquidity impulse |
| `nfci_level` | NFCI latest value | Financial conditions |
| `nfci_tight` | `1 if NFCI > 0 else 0` | Binary tight-conditions flag |
| `modern_ted` | `RIFSPPFAAD90NB - DGS3MO` | Modern TED spread proxy |
| `modern_ted_z` | Robust z-score over 52w | Normalized money market stress |

### 2.8 FX Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `usd_broad_ret_1w` | DTWEXBGS weekly log return | USD strength |
| `usd_broad_ret_1w_z` | Robust z-score over 52w | Normalized USD move |
| `usd_broad_ret_4w` | DTWEXBGS 4-week log return | USD trend |
| `usdjpy_ret_1w` | USDJPY=X weekly log return | Carry trade proxy |
| `eurusd_ret_1w` | EURUSD=X weekly log return | EUR leg |
| `em_fx_stress` | Equal-weighted USD return vs. (USDMXN, USDZAR, USDCNY, USDKRW) weekly | EM FX composite weakness |
| `em_fx_stress_z` | Robust z-score over 52w | Normalized EM FX stress |
| `em_dm_fx_divergence` | `DTWEXEMEGS / DTWEXAFEGS` ratio change 1w | EM stress relative to DM |

### 2.9 Commodity Derived Features

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `oil_wti_ret_1w` | CL=F weekly log return | WTI crude |
| `oil_wti_ret_1w_z` | Robust z-score over 52w | Normalized oil move |
| `brent_wti_spread` | `DCOILBRENTEU - DCOILWTICO` | Geopolitical oil premium |
| `brent_wti_spread_chg_1w` | Weekly change in spread | Spread momentum |
| `gold_ret_1w` | GC=F weekly log return | Gold |
| `gold_ret_1w_z` | Robust z-score over 52w | Normalized gold |
| `copper_gold_ratio` | `HG=F / GC=F` | Growth vs. safety ratio |
| `copper_gold_ratio_chg_1w` | Weekly change in ratio | Growth sentiment momentum |
| `gold_silver_ratio` | `GC=F / SI=F` | Risk-on/off positioning |
| `food_price_index_ret_1w` | Equal-weighted (ZW=F, ZC=F, ZS=F) weekly log return | Agricultural stress |
| `bdry_ret_1w` | BDRY weekly log return | Dry bulk freight proxy |
| `bdry_ret_1w_z` | Robust z-score over 52w | Normalized shipping activity |

### 2.10 Dynamics Features (Week-over-Week)

For any weekly feature `X_w`, compute the following dynamics:

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `{X}_wow_chg` | `X_w[t] - X_w[t-1]` | Week-over-week change |
| `{X}_wow_accel` | `wow_chg[t] - wow_chg[t-1]` | Acceleration (second derivative) |
| `{X}_4w_momentum` | `X_w[t] - X_w[t-4]` | 4-week momentum |

Apply dynamics to these key features:
- `vix_close_w`, `hy_oas_level`, `curve_10y2y_level`, `real_rate_10y`, `breakeven_5y`
- `usd_broad_ret_1w`, `oil_wti_ret_1w`, `bdry_ret_1w`
- `net_liquidity`, `nfci_level`
- `dispersion_sectors`, `dispersion_commodities`

---

## 3. Event Features

This section defines Logan's Part 3 scope: the event and news signal pipeline. Event features are produced by `EventFeatureBuilder` (currently a stub) and stored in `EventFeatureRow`.

### 3.1 Raw Event Data Sources

| Source | Granularity | Fields Used |
|--------|-------------|-------------|
| GDELT GKG (Global Knowledge Graph) | 15-minute batches | Themes, locations, tone, GCAM scores, source URLs |
| GDELT Events | 15-minute batches | CAMEO codes, Goldstein scale, actors, geo coordinates |
| RSS feeds (curated) | Varies | Headline text, source, timestamp |
| Central bank calendars | Static + scrape | Meeting dates, statement text |

### 3.2 Event-to-Theme Classification

Each incoming event record is classified against the theme taxonomy defined in `docs/keyword_taxonomy.md`. The classification produces:

| Field | Type | Description |
|-------|------|-------------|
| `theme` | str | Primary theme ID (e.g., `SHIP_CHOKE_001`) |
| `subtheme` | str | Sub-theme if applicable |
| `region` | str | Geographic region from GDELT geolocation |
| `match_score` | float [0, 1] | Confidence of theme assignment (keyword + semantic) |
| `cameo_code` | str | CAMEO event code if from GDELT Events table |
| `goldstein_scale` | float [-10, 10] | CAMEO Goldstein conflict/cooperation score |
| `tone` | float | Average tone from GDELT GKG |
| `source_url` | str | For deduplication and source diversity |

### 3.3 Weekly Event Feature Aggregation

For each (theme, region) pair, aggregate daily event records into weekly features:

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `{theme}_count_1w` | Count of unique events with match_score > 0.3 in the week | Raw event volume |
| `{theme}_intensity_1w` | `sum(match_score * abs(goldstein_scale))` for all events in the week | Weighted intensity combining confidence and severity |
| `{theme}_intensity_median_1w` | Median of `match_score * abs(goldstein_scale)` per event | Robust center -- less sensitive to a single extreme event |
| `{theme}_intensity_trimmed_1w` | 10% trimmed mean of per-event intensity | Robust center |
| `{theme}_intensity_z` | Robust z-score of `intensity_1w` over trailing 52w | Normalized intensity |
| `{theme}_novelty_1w` | See Section 3.4 | Fraction of events that are genuinely new |
| `{theme}_acceleration_1w` | `intensity_1w[t] - intensity_1w[t-1]` | Week-over-week intensity change |
| `{theme}_acceleration_z` | Robust z-score of acceleration over 52w | Normalized acceleration |
| `{theme}_source_diversity_1w` | Count of unique source domains / total event count | Higher diversity = more credible signal |
| `{theme}_tone_mean_1w` | Mean tone across events in the week | Positive = cooperative, negative = conflictual |
| `{theme}_tone_z` | Robust z-score of tone over 52w | Normalized tone |
| `{theme}_goldstein_mean_1w` | Mean Goldstein scale value | Cooperation/conflict average |
| `{theme}_goldstein_min_1w` | Min Goldstein scale value (most conflictual event) | Worst-case severity |
| `{theme}_cameo_severity_max_1w` | Max CAMEO severity score from mapping in `gdelt_cameo_mapping.md` | Most severe event type |

### 3.4 Novelty Score Computation

Novelty distinguishes fresh news from recycled coverage of the same story. This is critical because repeated headlines about an ongoing situation should not generate new impulse signals.

```
For each event e in week W for theme T:
  1. Compute text hash (headline or first 100 chars of description)
  2. Check against deduplication cache of hashes from weeks [W-4, W-1]
  3. If hash matches a previous event: novelty(e) = 0
     If hash is new but source_url domain matches a previous event's domain on same story: novelty(e) = 0.3
     If hash is new and source is new: novelty(e) = 1.0

{theme}_novelty_1w = mean(novelty(e) for all events in week for this theme)
```

A novelty score near 0 means all coverage is recycled. A novelty score near 1 means the events are genuinely new information.

### 3.5 Theme Co-Activation Features

Some expert models benefit from knowing when multiple related themes fire simultaneously:

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `coactivation_conflict_shipping` | `min(conflict_intensity_z, shipping_intensity_z)` | Conflict spilling into maritime routes |
| `coactivation_conflict_energy` | `min(conflict_intensity_z, energy_intensity_z)` | Conflict affecting energy supply |
| `coactivation_sanctions_shipping` | `min(sanctions_intensity_z, shipping_intensity_z)` | Sanctions causing shipping disruption |
| `coactivation_rates_fx` | `min(rates_intensity_z, fx_intensity_z)` | Central bank actions affecting FX |
| `coactivation_count` | Count of themes where intensity_z > 1.5 in the same week | How many domains are active simultaneously |

Co-activation features use the minimum (not the product or sum) because we want to measure the *overlap* -- both themes must be elevated for the signal to be meaningful.

### 3.6 CAMEO Severity Score

Map CAMEO event codes to a numeric severity scale per `docs/gdelt_cameo_mapping.md`:

| CAMEO Range | Description | Severity Score |
|-------------|-------------|----------------|
| 01-05 | Statements, appeals, cooperation | 0.0 - 0.2 |
| 06-09 | Protests, demands, threats | 0.3 - 0.5 |
| 10-13 | Demands with sanctions, posturing | 0.5 - 0.7 |
| 14-17 | Protests with violence, coercion | 0.7 - 0.8 |
| 18-19 | Assault, armed conflict | 0.8 - 0.9 |
| 20 | Unconventional mass violence | 1.0 |

The `cameo_severity_max_1w` feature uses this mapping to capture the worst-case event type for the week.

---

## 4. Expert-Specific Feature Sets

Each expert consumes a subset of market and event features. Per the design doc Section 3.1, inputs are domain-specific: shipping does not borrow defense signals, rates does not borrow shipping signals.

The `ExpertContext.feature_row` dictionary should contain exactly the features listed for that expert. The `FeatureBuilder` and `EventFeatureBuilder` produce the full feature table; expert-specific subsetting happens at prediction time in the expert's `predict()` method.

### 4.1 Conflict Escalation Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `spy_ret_1w_z` | 2.1 |
| `eem_ret_1w_z` | 2.1 |
| `gld_ret_1w_z` | 2.1 |
| `oil_wti_ret_1w_z` | 2.9 |
| `vix_close_w_z` | 2.2 |
| `vix_close_w_wow_chg` | 2.10 |
| `hy_oas_z` | 2.7 |
| `hy_oas_chg_1w` | 2.7 |
| `usd_broad_ret_1w_z` | 2.8 |
| `em_fx_stress_z` | 2.8 |
| `corr_SPY_TLT_delta_z` | 2.4 |
| `corr_SPY_GLD_delta_z` | 2.4 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `conflict_intensity_z` (aggregated across all conflict themes) | 3.3 |
| `conflict_acceleration_z` | 3.3 |
| `conflict_novelty_1w` | 3.4 |
| `conflict_source_diversity_1w` | 3.3 |
| `conflict_goldstein_min_1w` | 3.3 |
| `conflict_cameo_severity_max_1w` | 3.6 |
| `sanctions_intensity_z` | 3.3 |
| `coactivation_conflict_energy` | 3.5 |
| `coactivation_conflict_shipping` | 3.5 |

**Localization context:** `region` from `ExpertContext` (middle_east, eastern_europe, east_asia, etc.). Event features should be filtered to the relevant region before aggregation.

### 4.2 Shipping / Chokepoint Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `bdry_ret_1w_z` | 2.9 |
| `bdry_ret_1w_wow_chg` | 2.10 |
| `oil_wti_ret_1w_z` | 2.9 |
| `brent_wti_spread` | 2.9 |
| `brent_wti_spread_chg_1w` | 2.9 |
| `xle_ret_1w_z` | 2.1 (computed for XLE) |
| `gld_ret_1w_z` | 2.1 |
| `vix_close_w_z` | 2.2 |
| `eem_ret_1w_z` | 2.1 |
| `corr_CL_GLD_delta_z` | 2.4 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `shipping_intensity_z` (aggregated across SHIP_CHOKE_* themes) | 3.3 |
| `shipping_acceleration_z` | 3.3 |
| `shipping_novelty_1w` | 3.4 |
| `shipping_source_diversity_1w` | 3.3 |
| `shipping_cameo_severity_max_1w` | 3.6 |
| `port_stress_intensity_z` (aggregated across SHIP_PORT_* themes) | 3.3 |
| `coactivation_conflict_shipping` | 3.5 |
| `coactivation_sanctions_shipping` | 3.5 |

**Localization context:** `chokepoint` or `port_cluster` from `ExpertContext`. Event features are filtered by the specific chokepoint (Hormuz, Bab el-Mandeb, Suez, Panama, Malacca, Taiwan Strait) or port cluster (India west coast, India east coast, Singapore, Rotterdam, Shanghai).

### 4.3 Sanctions Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `oil_wti_ret_1w_z` | 2.9 |
| `usd_broad_ret_1w_z` | 2.8 |
| `eem_ret_1w_z` | 2.1 |
| `em_fx_stress_z` | 2.8 |
| `hy_oas_z` | 2.7 |
| `hy_oas_chg_1w` | 2.7 |
| `copper_gold_ratio_chg_1w` | 2.9 |
| `food_price_index_ret_1w` | 2.9 |
| `corr_SPY_EEM_delta_z` | 2.4 |
| `corr_EEM_DTWEXBGS_delta_z` | 2.4 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `sanctions_intensity_z` (aggregated across DEF_SANC_*, SHIP_SANC_* themes) | 3.3 |
| `sanctions_acceleration_z` | 3.3 |
| `sanctions_novelty_1w` | 3.4 |
| `sanctions_source_diversity_1w` | 3.3 |
| `sanctions_tone_z` | 3.3 |
| `coactivation_sanctions_shipping` | 3.5 |
| `coactivation_conflict_energy` | 3.5 |

### 4.4 Rates / Policy Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `yield_2y_level` | 2.6 |
| `yield_2y_chg_1w` | 2.6 |
| `yield_10y_chg_1w` | 2.6 |
| `curve_10y2y_level` | 2.6 |
| `curve_10y2y_chg_1w` | 2.6 |
| `curve_10y2y_inverted` | 2.6 |
| `curve_10y3m_inverted` | 2.6 |
| `curve_butterfly` | 2.6 |
| `real_rate_10y` | 2.6 |
| `real_rate_10y_chg_1w` | 2.6 |
| `real_rate_10y_chg_4w` | 2.6 |
| `breakeven_5y` | 2.6 |
| `fwd_inflation_5y5y_dev` | 2.6 |
| `inflation_term_structure` | 2.6 |
| `fed_funds_level` | 2.6 |
| `tlt_ret_1w_z` | 2.1 (computed for TLT) |
| `xlf_ret_1w_z` | 2.1 (computed for XLF) |
| `usdjpy_ret_1w` | 2.8 |
| `move_close_w_z` | 2.2 |
| `vix_move_ratio` | 2.2 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `rates_intensity_z` (aggregated across MACRO_RATE_*, MACRO_CB_* themes) | 3.3 |
| `rates_acceleration_z` | 3.3 |
| `rates_novelty_1w` | 3.4 |
| `rates_tone_z` (hawkish tone = negative, dovish = positive) | 3.3 |
| `coactivation_rates_fx` | 3.5 |

**Additional context:** Binary flag `fomc_week` (1 if an FOMC meeting falls in the current or next week, from static calendar).

### 4.5 Commodity Shock Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `oil_wti_ret_1w_z` | 2.9 |
| `oil_wti_ret_1w_wow_chg` | 2.10 |
| `brent_wti_spread` | 2.9 |
| `brent_wti_spread_chg_1w` | 2.9 |
| `gold_ret_1w_z` | 2.9 |
| `copper_gold_ratio` | 2.9 |
| `copper_gold_ratio_chg_1w` | 2.9 |
| `gold_silver_ratio` | 2.9 |
| `food_price_index_ret_1w` | 2.9 |
| `bdry_ret_1w_z` | 2.9 |
| `breakeven_5y` | 2.6 |
| `breakeven_5y_wow_chg` | 2.10 |
| `xle_ret_1w_z` | 2.1 (computed for XLE) |
| `dispersion_commodities_z` | 2.5 |
| `vix_close_w_z` | 2.2 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `commodity_intensity_z` (aggregated across COM_* themes) | 3.3 |
| `commodity_acceleration_z` | 3.3 |
| `commodity_novelty_1w` | 3.4 |
| `coactivation_conflict_energy` | 3.5 |
| `coactivation_sanctions_shipping` | 3.5 |

### 4.6 Crypto Regime Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `btc_ret_1w_z` | 2.1 (computed for BTC-USD) |
| `btc_ret_4w_z` | 2.1 |
| `btc_rvol_20d_z` | 2.2 (computed for BTC-USD) |
| `btc_rvol_ratio` | 2.2 |
| `corr_SPY_BTC_20d` | 2.4 |
| `corr_SPY_BTC_60d` | 2.4 |
| `corr_SPY_BTC_delta` | 2.4 |
| `spy_ret_1w_z` | 2.1 |
| `usd_broad_ret_1w_z` | 2.8 |
| `net_liquidity_chg_4w` | 2.7 |
| `hy_oas_z` | 2.7 |
| `vix_close_w_z` | 2.2 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `crypto_intensity_z` (aggregated across CRYPTO_* themes) | 3.3 |
| `crypto_novelty_1w` | 3.4 |
| `coactivation_count` | 3.5 |

**Derived features (computed within expert):**

| Feature | Formula |
|---------|---------|
| `btc_spy_corr_regime` | `1 if corr_SPY_BTC_20d > 0.6 else (-1 if corr_SPY_BTC_20d < 0.1 else 0)` |
| `btc_usd_sensitivity` | Rolling 20d beta of BTC daily returns on DTWEXBGS daily returns |

### 4.7 Market Pricing / Complacency Expert

**Market features consumed:**

| Feature | Source Section |
|---------|---------------|
| `vix_close_w_z` | 2.2 |
| `vix_close_w_wow_chg` | 2.10 |
| `vix_close_w_wow_accel` | 2.10 |
| `vix_term_slope` | 2.2 |
| `vix_term_slope_z` | 2.2 |
| `move_close_w_z` | 2.2 |
| `vix_move_ratio` | 2.2 |
| `hy_oas_z` | 2.7 |
| `hy_oas_chg_1w` | 2.7 |
| `ccc_bb_spread_z` | 2.7 |
| `corr_SPY_TLT_20d` | 2.4 |
| `corr_SPY_TLT_delta_z` | 2.4 |
| `dispersion_sectors_z` | 2.5 |
| `dispersion_sectors_wow_chg` | 2.10 |
| `dispersion_commodities_z` | 2.5 |
| `spy_ret_1w_z` | 2.1 |
| `spy_rvol_20d_z` | 2.2 (computed for SPY) |
| `spy_rvol_ratio` | 2.2 |
| `spy_vol_of_vol` | 2.2 |
| `spy_drawdown_depth` | 2.3 |
| `spy_days_in_drawdown` | 2.3 |
| `nfci_level` | 2.7 |
| `modern_ted_z` | 2.7 |

**Event features consumed:**

| Feature | Source Section |
|---------|---------------|
| `coactivation_count` | 3.5 |

This expert is primarily market-data-driven. Event features are minimal -- the `coactivation_count` tells the expert how many event domains are active, which modulates the "already priced" assessment.

**Derived features (computed within expert):**

| Feature | Formula |
|---------|---------|
| `already_priced_score` | See Section 5.1 |
| `vol_regime` | `"crisis" if vix_close_w_z > 2.0 else ("elevated" if vix_close_w_z > 1.0 else ("suppressed" if vix_close_w_z < -1.0 else "normal"))` |

---

## 5. Already-Priced Confirmation Features

These features detect when the market has already moved in response to an event, so that the system can dampen signal aggressiveness and bias toward ETF/hedge expression (design doc Section 5.2).

### 5.1 Already-Priced Score

A composite score in [0, 1] where higher values indicate the market has already repriced:

```
already_priced_score = weighted average of:

  0.25 * vol_spike_then_compress:
    1.0 if vix_close_w[t-1] - vix_close_w[t-2] > 3 pts AND vix_close_w[t] < vix_close_w[t-1]
    0.5 if vix_close_w[t-1] - vix_close_w[t-2] > 2 pts AND vix_close_w[t] < vix_close_w[t-1]
    0.0 otherwise

  0.25 * spread_spike_then_revert:
    1.0 if hy_oas_chg[t-1] > 15 bps AND hy_oas_chg[t] < 0
    0.5 if hy_oas_chg[t-1] > 10 bps AND hy_oas_chg[t] < 0
    0.0 otherwise

  0.25 * correlation_normalization:
    Score = 1.0 - abs(corr_SPY_TLT_20d - corr_SPY_TLT_60d)
    Clipped to [0, 1]
    High score means short-term and long-term correlations have converged (initial
    shock-driven correlation spike has normalized)

  0.25 * dispersion_decay:
    1.0 if dispersion_sectors_z[t] < dispersion_sectors_z[t-1] AND dispersion_sectors_z[t-1] > 1.0
    0.5 if dispersion_sectors_z[t] < dispersion_sectors_z[t-1]
    0.0 otherwise
```

### 5.2 Vol Compression After Initial Spike

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `vix_spike_then_compress` | `1 if vix peaked in [t-2, t-1] and declined by > 1 pt at t` | Binary flag |
| `vix_compression_magnitude` | `max(vix in trailing 5d) - vix_close_w[t]` | How much vol has already come off |
| `vix_compression_ratio` | `vix_close_w[t] / max(vix in trailing 10d)` | <1 means vol has compressed from recent peak |

### 5.3 Correlation Normalization

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `corr_spy_tlt_convergence` | `1 - abs(corr_SPY_TLT_20d - corr_SPY_TLT_60d)` | 1 = correlations normal, 0 = correlation regime break |
| `corr_spy_gld_convergence` | Same for SPY-GLD pair | Gold safe-haven correlation normalization |
| `corr_convergence_mean` | Mean of all convergence scores | Aggregate correlation normalization |

### 5.4 Dispersion Reduction

| Column Name | Formula | Notes |
|-------------|---------|-------|
| `dispersion_sectors_decay` | `dispersion_sectors_z[t] - dispersion_sectors_z[t-1]` | Negative = dispersion declining (repricing complete) |
| `dispersion_decay_streak` | Count of consecutive weeks where dispersion_sectors_z declined | Longer streak = more confident that repricing is done |

### 5.5 Using Already-Priced Features

These features feed into two downstream decisions:

1. **Expression selector (Section 5.2 of design doc):** When `already_priced_score > 0.6`, bias toward ETF expression and increase hedge fraction. When `already_priced_score < 0.3`, single-name expression is preferred if dispersion is also high.

2. **Expert severity dampening:** The `MarketPricingExpert` passes `already_priced_score` as part of its `ExpertPrediction.metadata`, and the `MetaCombiner` can use it to scale down the combined severity signal.

---

## 6. Anti-Leakage Checklist

### 6.1 Feature Computation Rules

| # | Rule | Violation Example | Correct Approach |
|---|------|-------------------|------------------|
| 1 | All features at prediction time t use data from [t-W, t] only | Computing VIX z-score using future VIX values | Rolling z-score window ends at t |
| 2 | Return features use close[t] and close[t-N], never close[t+K] | 5-day forward return used as a feature | Forward returns are labels, not features |
| 3 | Rolling statistics (mean, std, MAD) use only trailing data | 52-week z-score computed over centered window | Rolling window ends at t, lookback starts at t-260 |
| 4 | Monthly macro series are lagged by publication delay | Using January CPI (released ~Feb 12) as a feature on Feb 1 | Apply publication lag: CPI available only after release date |
| 5 | Weekly FRED series are lagged by 1 business day minimum | Using Wednesday's WALCL value on Wednesday | WALCL published Thursday for Wednesday; usable Friday |
| 6 | Event features use only events with timestamps <= t | Including a Saturday GDELT event in Friday's feature row | Filter events to timestamps <= Friday market close |
| 7 | Novelty deduplication cache uses only past hashes | Deduplicating against future week's events | Hash cache covers [t-4w, t] only |
| 8 | Cross-asset correlations use trailing windows ending at t | 20-day rolling correlation window extends into the future | Window is [t-19, t] for 20-day correlation |
| 9 | Cluster models for unsupervised labels are fitted on training data only | GMM fitted on full dataset including test period | Re-fit cluster model at each walk-forward fold using only train data |
| 10 | Expert OOS predictions for meta-combiner do not overlap with expert training data | Expert trained on weeks 1-100, then its predictions on weeks 1-100 are used to train the combiner | Expert must produce OOS predictions via walk-forward; combiner trains only on those OOS predictions |

### 6.2 Walk-Forward Feature Computation Protocol

```
For each walk-forward fold with training cutoff at week T:

  1. Compute all features for weeks [1, T] using only data available at each week's Friday close.
  2. Compute labels for weeks [1, T-gap] using forward returns (labels for week t use returns [t+1, t+5]).
     The gap ensures label computation does not require returns beyond the training cutoff.
  3. Train expert models on features[1:T-gap] and labels[1:T-gap].
  4. Generate OOS predictions for weeks [T-gap+1, T+test_size] using the trained model.
  5. Features for OOS weeks must NOT use any rolling statistics computed beyond their own Friday close.

  Critical: step 5 means you cannot pre-compute features for all weeks in one batch if your
  rolling statistics have an expanding window. Either:
    (a) Use a fixed trailing window (e.g., 52 weeks) so features are locally computable, OR
    (b) Recompute features at each fold with the expanding window ending at that fold's cutoff.

  Recommended: option (a) with 52-week trailing window for all z-scores and robust statistics.
```

### 6.3 Feature Validation Checks

Run these checks after feature computation, before training:

| Check | Expected | Action if Failed |
|-------|----------|-----------------|
| No NaN in feature matrix after warmup period (first 52 weeks) | All finite | Fill with 0 or drop row; log warning |
| No feature has > 20% missing values | <= 20% missing | Review data source; consider dropping feature |
| No feature has zero variance | Variance > 0 | Drop feature (constant column provides no information) |
| No feature has correlation > 0.95 with another feature in the same expert's feature set | Correlation < 0.95 | Keep one, drop the other (prevents multicollinearity in linear combiner) |
| Feature magnitudes are bounded | abs(z-score) < 10 after winsorization | Winsorize at [-5, 5] for z-scored features |
| Feature timestamps align with label timestamps | 1:1 mapping | Debug alignment issue |
| No feature value changes when re-computed with vs. without future data | Exact match | Leakage detected; fix computation |

### 6.4 Revision-Safe Macro Data Handling

For monthly macro series that are revised (CPI, NFP, PCE, GDP):

| Series | Publication Lag | Revision Window | Approach |
|--------|----------------|-----------------|----------|
| CPI (CPIAUCSL) | ~2 weeks after month-end | Minor revisions for 2 months | Use first-release value; add 15-day lag |
| NFP (PAYEMS) | ~5 weeks after month-end | Major revisions for 3 months | Use first-release value; add 35-day lag |
| PCE (PCEPILFE) | ~4 weeks after month-end | Major revisions for 3+ months | Use first-release value; add 30-day lag |
| GDP | ~4 weeks after quarter-end | Advance, preliminary, final over 3 months | Use advance estimate; add 30-day lag |
| JOLTS | ~6 weeks after month-end | Minor revisions | Use first-release value; add 40-day lag |

For backtesting, ideally use ALFRED (Archival FRED) vintage data to get point-in-time values. If ALFRED is not available, apply the publication lag buffer above to the final revised values as an approximation.

---

## 7. Feature Schema Reference

### 7.1 FeatureRow Schema Extension

The current `FeatureRow` schema in `src/engine/features/schemas.py` stores features as a flat `dict[str, float]`. The keys in that dictionary should follow the naming conventions defined in this document:

```
{source}_{metric}_{window}_{transform}

Examples:
  spy_ret_1w_z         -- SPY, 1-week return, z-scored
  vix_close_w          -- VIX, Friday close, raw
  hy_oas_chg_1w        -- HY OAS, 1-week change, raw
  corr_SPY_TLT_20d     -- SPY-TLT, 20-day rolling correlation, raw
  dispersion_sectors_z -- sector dispersion, z-scored
  conflict_intensity_z -- conflict theme intensity, z-scored
```

### 7.2 EventFeatureRow Schema Extension

The current `EventFeatureRow` schema in `src/engine/events/schemas.py` adds `region` and `metadata` fields. The `values` dictionary should contain the event features defined in Section 3 above:

```
{theme}_{metric}_{window}

Examples:
  conflict_intensity_1w       -- conflict intensity, 1-week sum
  conflict_intensity_z        -- conflict intensity, z-scored
  shipping_novelty_1w         -- shipping novelty score, 1-week
  coactivation_conflict_energy -- conflict-energy co-activation
```

### 7.3 Full Feature Count Estimate

| Category | Approximate Count | Notes |
|----------|-------------------|-------|
| Returns (per instrument, 3 windows + z + rank) | ~5 per instrument x ~30 instruments = 150 | Most are used only by their relevant expert |
| Volatility | ~20 | VIX family, MOVE, realized vol for key instruments |
| Drawdowns | ~12 | Depth + duration for SPY, EEM, key commodities |
| Cross-asset correlations | ~40 | 10 key pairs x 4 (20d, 60d, delta, delta_z) |
| Dispersion | ~10 | Within-sleeve, cross-sleeve, sectors, commodities |
| Yield curve and rates | ~20 | Levels, changes, flags, butterfly, real rates, inflation |
| Credit and liquidity | ~15 | HY/IG spreads, net liquidity, NFCI, modern TED |
| FX | ~10 | USD, USDJPY, EUR, EM FX stress |
| Commodity derived | ~15 | Spreads, ratios, freight |
| Dynamics (wow, accel, momentum) | ~40 | Applied to ~13 base features x 3 dynamics |
| Event features | ~70 | ~7 theme groups x 10 features each |
| Co-activation | ~6 | Pairwise and count |
| Already-priced | ~10 | Composite + components |
| **Total** | **~420** | Per expert: 20-35 features (domain-specific subset) |

The full feature table is wide (~420 columns) but each expert consumes only 20-35 columns. The `MetaCombiner` consumes the standardized expert outputs (probability_active, severity, confidence, direction per expert), not the raw features.
