# Training Label Definitions

Reference for the macro-event ML trading engine. Defines how supervised training labels are constructed for each expert family, plus the unsupervised clustering alternative for regime discovery.

**Core principle (from design doc Section 3.4):** Experts are trained on measurable market outcomes, not subjective "war week" or "crisis week" labels. We care about consistency and actionable probability, not storytelling.

**Two supported approaches:**

1. Cross-asset response patterns -- define shock weeks using unusual combinations of asset returns.
2. Unsupervised regime clustering -- cluster response vectors to discover regimes, then train experts to predict the cluster.

Both approaches share the same anti-leakage discipline: labels are constructed from forward returns relative to the prediction date, and features use only data available at prediction time.

---

## Table of Contents

1. [General Label Construction Rules](#1-general-label-construction-rules)
2. [Conflict Escalation Expert Labels](#2-conflict-escalation-expert-labels)
3. [Shipping / Chokepoint Expert Labels](#3-shipping--chokepoint-expert-labels)
4. [Sanctions Expert Labels](#4-sanctions-expert-labels)
5. [Rates / Policy Expert Labels](#5-rates--policy-expert-labels)
6. [Commodity Shock Expert Labels](#6-commodity-shock-expert-labels)
7. [Crypto Regime Expert Labels](#7-crypto-regime-expert-labels)
8. [Market Pricing / Complacency Expert Labels](#8-market-pricing--complacency-expert-labels)
9. [Unsupervised Clustering Approach](#9-unsupervised-clustering-approach)
10. [Walk-Forward and Anti-Leakage Protocol](#10-walk-forward-and-anti-leakage-protocol)

---

## 1. General Label Construction Rules

### 1.1 Timing Convention

All labels follow a **Friday-close to Friday-close** weekly cadence to align with the portfolio rebalance cycle described in the design doc.

| Term | Definition |
|------|-----------|
| **Prediction date (t)** | Friday close of the current week. All features must be computable from data available at or before this timestamp. |
| **Label window** | The forward period over which the outcome is measured. Default: t+1 through t+5 trading days (next week's Monday open through Friday close). |
| **Sigma reference window** | Trailing 52-week (260 trading days) rolling window ending at t, used to compute z-scores and thresholds for "unusual" returns. Updated weekly. |

### 1.2 Label Types

Each expert family defines labels using one or both of the following:

| Type | Schema | When to use |
|------|--------|-------------|
| **Binary classification** | `label in {0, 1}` | "Is this shock active next week?" -- used for `probability_active` output. |
| **Regression target** | `label in R` | Continuous severity measure -- used for `severity_score` output. Typically a z-scored return or composite score. |

The binary label drives the primary expert output (`probability_active`). The regression target, when available, trains a secondary head or a separate regressor for `severity_score`.

### 1.3 Threshold Calibration

All sigma-based thresholds use **rolling robust statistics** to avoid contamination by outliers:

- **Robust mean**: 10% trimmed mean over the sigma reference window.
- **Robust std**: Median absolute deviation (MAD) scaled by 1.4826, or interquartile range / 1.35.
- **Robust z-score**: `(x - trimmed_mean) / mad_std`.

This prevents a single extreme week (e.g., COVID March 2020) from compressing thresholds for years afterward.

### 1.4 Response Vector Definition

Each expert family defines a **response vector** -- a set of asset returns over the label window that collectively characterize the shock type. The response vector serves two purposes:

1. Its individual components are combined via AND/OR logic to create the binary label (Approach 1).
2. It is fed into the unsupervised clustering pipeline to discover regime labels (Approach 2).

Response vectors always use **log returns** over the 5-day forward window: `ln(price[t+5] / price[t])`.

---

## 2. Conflict Escalation Expert Labels

### 2.1 What the Label Represents

**Binary**: Is next week a "conflict-escalation week" where defense-adjacent assets outperform and risk-off assets rally, consistent with a geopolitical shock?

**Regression**: Severity of the conflict-driven market response, measured as a composite z-score.

### 2.2 Response Vector

| Component | Ticker(s) | Return | Description |
|-----------|-----------|--------|-------------|
| `defense_return_5d` | ITA (iShares US Aerospace & Defense ETF) | 5d log return | Defense sector response |
| `gold_return_5d` | GC=F or GLD | 5d log return | Safe-haven bid |
| `oil_return_5d` | CL=F | 5d log return | Energy risk premium |
| `vix_change_5d` | VIXCLS | 5d arithmetic change (points) | Fear gauge |
| `spy_return_5d` | SPY | 5d log return | Broad equity stress |
| `eem_return_5d` | EEM | 5d log return | EM contagion |
| `tlt_return_5d` | TLT | 5d log return | Flight to quality |

### 2.3 Binary Label Construction

```
conflict_label = 1 when ALL of:
  (a) defense_return_5d_z > 1.0        -- defense sector outperforms meaningfully
  (b) gold_return_5d_z > 0.5           -- gold catches a safe-haven bid
  (c) vix_change_5d > 2.0 points       -- vol picks up
  (d) spy_return_5d_z < -0.5           -- equities weaken

OR when ALL of:
  (a) oil_return_5d_z > 1.5            -- oil spikes on supply fear
  (b) gold_return_5d_z > 1.0           -- strong safe-haven move
  (c) eem_return_5d_z < -1.0           -- EM sells off (contagion)
```

The two OR branches capture distinct conflict signatures: the first is a "standard escalation" pattern (defense up, equities down, vol up); the second is a "supply-chain-linked conflict" pattern (oil spike with EM contagion).

Z-scores are computed against the 52-week trailing robust statistics.

### 2.4 Regression Target

```
conflict_severity = 0.30 * defense_return_5d_z
                  + 0.20 * gold_return_5d_z
                  + 0.20 * abs(spy_return_5d_z) * sign(-spy_return_5d)
                  + 0.15 * vix_change_5d / mad_std(vix_change_5d)
                  + 0.15 * oil_return_5d_z
```

Clipped to [0, 5] and re-normalized to [0, 1] via `severity / 5.0` for the `severity_score` field.

### 2.5 Localization

Labels are computed globally (one label series). The expert's localization metadata (region = middle_east, eastern_europe, east_asia, etc.) is determined by which event features are elevated, not by the label itself. This prevents the need to construct region-specific outcome labels, which would be too sparse for training.

---

## 3. Shipping / Chokepoint Expert Labels

### 3.1 What the Label Represents

**Binary**: Is next week a "shipping shock week" where freight proxies, energy, and risk-off assets move in a pattern consistent with a maritime disruption?

**Regression**: Magnitude of the shipping-disruption market footprint.

### 3.2 Response Vector

| Component | Ticker(s) | Return | Description |
|-----------|-----------|--------|-------------|
| `bdry_return_5d` | BDRY | 5d log return | Dry bulk freight proxy |
| `oil_return_5d` | CL=F | 5d log return | Energy supply premium |
| `brent_wti_spread_chg_5d` | DCOILBRENTEU - DCOILWTICO | 5d change in spread | Logistics/geopolitical premium |
| `xle_return_5d` | XLE | 5d log return | Energy equity proxy |
| `gld_return_5d` | GLD | 5d log return | Risk-off confirmation |
| `vix_change_5d` | VIXCLS | 5d change (points) | Broader risk aversion |
| `eem_return_5d` | EEM | 5d log return | EM trade-flow sensitivity |

### 3.3 Binary Label Construction

```
shipping_label = 1 when ALL of:
  (a) bdry_return_5d_z > 2.0           -- freight proxy spikes abnormally
  (b) xle_return_5d_z > 1.0            -- energy sector rallies
  (c) vix_change_5d > 0 points         -- vol does not decline

OR when ALL of:
  (a) brent_wti_spread_chg_5d_z > 1.5  -- geopolitical oil premium widens
  (b) oil_return_5d_z > 1.5            -- oil spikes
  (c) gld_return_5d_z > 0.5            -- safe-haven bid present
  (d) bdry_return_5d_z > 1.0           -- freight proxy confirms
```

The first branch captures pure shipping disruption (freight spike + energy confirmation). The second captures supply-route disruption where oil leads (e.g., Hormuz threat) with freight confirming.

### 3.4 Regression Target

```
shipping_severity = 0.30 * bdry_return_5d_z
                  + 0.25 * oil_return_5d_z
                  + 0.20 * brent_wti_spread_chg_5d_z
                  + 0.15 * xle_return_5d_z
                  + 0.10 * gld_return_5d_z
```

Clipped to [0, 5], normalized to [0, 1].

### 3.5 Localization

Same global label approach as conflict. Chokepoint-specific routing (Hormuz vs. Bab el-Mandeb vs. Suez vs. Panama vs. Malacca vs. Taiwan Strait) is determined by which event features (chokepoint intensity, incident counts per region) are elevated, not by constructing separate label series per chokepoint.

---

## 4. Sanctions Expert Labels

### 4.1 What the Label Represents

**Binary**: Is next week a "sanctions-impact week" where sanctioned-sector proxies, FX, and commodity markets move in a pattern consistent with new or escalating trade restrictions?

**Regression**: Magnitude of sanctions-driven market dislocation.

### 4.2 Response Vector

| Component | Ticker(s) | Return | Description |
|-----------|-----------|--------|-------------|
| `oil_return_5d` | CL=F | 5d log return | Energy sanctions proxy |
| `usd_return_5d` | DTWEXBGS | 5d log return | Dollar strength on sanctions |
| `eem_return_5d` | EEM | 5d log return | EM equity stress |
| `em_fx_stress_5d` | Equal-weighted USD return vs. (USDMXN, USDZAR, USDCNY, USDKRW) | 5d composite | EM FX weakness |
| `hy_spread_chg_5d` | BAMLH0A0HYM2 | 5d change (bps) | Credit stress |
| `gold_return_5d` | GC=F | 5d log return | Safe-haven / sanctions-evasion proxy |
| `copper_return_5d` | HG=F | 5d log return | Industrial demand disruption |

### 4.3 Binary Label Construction

```
sanctions_label = 1 when ALL of:
  (a) oil_return_5d_z > 1.0            -- energy prices spike (supply restriction)
  (b) em_fx_stress_5d_z > 1.0          -- EM currencies weaken vs. USD
  (c) hy_spread_chg_5d > 10 bps        -- credit markets tighten

OR when ALL of:
  (a) eem_return_5d_z < -1.5           -- EM equities sell off hard
  (b) usd_return_5d_z > 1.0            -- dollar strengthens
  (c) copper_return_5d_z < -1.0        -- industrial demand proxy drops
```

First branch captures energy-sanctions events (Iran, Russia). Second branch captures broader trade-restriction events (tariffs, export controls) where industrial metals and EM equities lead.

### 4.4 Regression Target

```
sanctions_severity = 0.25 * oil_return_5d_z
                   + 0.20 * em_fx_stress_5d_z
                   + 0.20 * abs(eem_return_5d_z) * sign(-eem_return_5d)
                   + 0.15 * hy_spread_chg_5d / mad_std(hy_spread_chg_5d)
                   + 0.10 * usd_return_5d_z
                   + 0.10 * abs(copper_return_5d_z) * sign(-copper_return_5d)
```

Clipped to [0, 5], normalized to [0, 1].

---

## 5. Rates / Policy Expert Labels

### 5.1 What the Label Represents

**Binary**: Is next week a "rates shock week" -- either a hawkish shock (yields spike, curve flattens, risk assets sell) or an easing shock (yields drop, curve steepens, risk assets rally)?

**Direction**: Unlike other experts, this one produces a **directional** binary label: `+1` for hawkish shock, `-1` for easing shock, `0` for no shock. The `probability_active` output is trained on `abs(label) in {0, 1}`, and the `direction` output is trained separately on the sign.

### 5.2 Response Vector

| Component | Ticker(s) | Return/Change | Description |
|-----------|-----------|---------------|-------------|
| `yield_2y_chg_5d` | DGS2 | 5d change (bps) | Short-end rate move |
| `yield_10y_chg_5d` | DGS10 | 5d change (bps) | Long-end rate move |
| `curve_10y2y_chg_5d` | T10Y2Y | 5d change (bps) | Slope change |
| `real_rate_chg_5d` | DFII10 | 5d change (bps) | Real rate move |
| `breakeven_5y_chg_5d` | T5YIE | 5d change (bps) | Inflation expectations |
| `tlt_return_5d` | TLT | 5d log return | Bond price confirmation |
| `spy_return_5d` | SPY | 5d log return | Equity response |
| `xlf_return_5d` | XLF | 5d log return | Bank sector (benefits from steepening) |
| `usdjpy_return_5d` | USDJPY=X | 5d log return | Carry trade / rate differential proxy |

### 5.3 Binary Label Construction

```
hawkish_shock_label = 1 when ALL of:
  (a) yield_2y_chg_5d_z > 1.5          -- short-end yields spike
  (b) tlt_return_5d_z < -1.0           -- bonds sell off
  (c) real_rate_chg_5d > 5 bps         -- real rates rise (not just inflation)

easing_shock_label = 1 when ALL of:
  (a) yield_2y_chg_5d_z < -1.5         -- short-end yields plunge
  (b) tlt_return_5d_z > 1.0            -- bonds rally
  (c) curve_10y2y_chg_5d > 5 bps       -- curve steepens (front-end led)

rates_active_label = max(hawkish_shock_label, easing_shock_label)
rates_direction = +1 if hawkish_shock_label else (-1 if easing_shock_label else 0)
```

### 5.4 Regression Target

```
rates_severity = 0.30 * abs(yield_2y_chg_5d_z)
               + 0.25 * abs(tlt_return_5d_z)
               + 0.20 * abs(real_rate_chg_5d) / mad_std(real_rate_chg_5d)
               + 0.15 * abs(curve_10y2y_chg_5d_z)
               + 0.10 * abs(breakeven_5y_chg_5d_z)
```

Clipped to [0, 5], normalized to [0, 1].

---

## 6. Commodity Shock Expert Labels

### 6.1 What the Label Represents

**Binary**: Is next week a "commodity shock week" where the energy complex, industrial metals, or agricultural commodities exhibit abnormal price moves with cross-asset confirmation?

**Direction**: `+1` for supply-shock (prices spike), `-1` for demand-destruction (prices crash).

### 6.2 Response Vector

| Component | Ticker(s) | Return | Description |
|-----------|-----------|--------|-------------|
| `oil_return_5d` | CL=F | 5d log return | Energy complex anchor |
| `brent_return_5d` | BZ=F | 5d log return | International oil benchmark |
| `natgas_return_5d` | NG=F | 5d log return | Natural gas |
| `copper_return_5d` | HG=F | 5d log return | Industrial demand proxy |
| `gold_return_5d` | GC=F | 5d log return | Inflation / safe-haven |
| `wheat_return_5d` | ZW=F | 5d log return | Agricultural supply disruption |
| `xle_return_5d` | XLE | 5d log return | Energy equity confirmation |
| `breakeven_5y_chg_5d` | T5YIE | 5d change (bps) | Inflation expectations confirmation |

### 6.3 Binary Label Construction

```
supply_shock_label = 1 when ALL of:
  (a) oil_return_5d_z > 1.5            -- oil spikes
  (b) xle_return_5d_z > 0.5            -- energy equities confirm
  (c) breakeven_5y_chg_5d > 3 bps      -- inflation expectations rise

OR when ALL of:
  (a) any 2 of {oil_z > 1.5, natgas_z > 2.0, copper_z > 1.5, wheat_z > 2.0}
  (b) gold_return_5d_z > 0.5           -- safe-haven / inflation confirmation

demand_destruction_label = 1 when ALL of:
  (a) oil_return_5d_z < -1.5           -- oil collapses
  (b) copper_return_5d_z < -1.5        -- copper confirms demand weakness
  (c) breakeven_5y_chg_5d < -3 bps     -- inflation expectations fall

commodity_active_label = max(supply_shock_label, demand_destruction_label)
commodity_direction = +1 if supply_shock_label else (-1 if demand_destruction_label else 0)
```

### 6.4 Regression Target

```
commodity_severity = 0.25 * max(abs(oil_return_5d_z), abs(brent_return_5d_z))
                   + 0.20 * abs(copper_return_5d_z)
                   + 0.15 * abs(natgas_return_5d_z)
                   + 0.15 * abs(xle_return_5d_z)
                   + 0.15 * abs(breakeven_5y_chg_5d) / mad_std(breakeven_5y_chg_5d)
                   + 0.10 * abs(wheat_return_5d_z)
```

Clipped to [0, 5], normalized to [0, 1].

---

## 7. Crypto Regime Expert Labels

### 7.1 What the Label Represents

**Binary**: Is next week a "crypto regime shift week" where crypto behaves differently from its recent correlation structure with equities and risk assets?

**Direction**: `+1` for "risk-on beta" regime (crypto up with equities), `-1` for "stress hedge" regime (crypto diverges from equities), `0` for neutral / no regime shift.

### 7.2 Response Vector

| Component | Ticker(s) | Return | Description |
|-----------|-----------|--------|-------------|
| `btc_return_5d` | BTC-USD | 5d log return | Bitcoin core |
| `eth_return_5d` | ETH-USD | 5d log return | Ethereum (optional, may use BTC only) |
| `spy_return_5d` | SPY | 5d log return | Equity benchmark |
| `vix_change_5d` | VIXCLS | 5d change (points) | Vol regime |
| `usd_return_5d` | DTWEXBGS | 5d log return | Dollar strength |
| `net_liquidity_chg_5d` | WALCL - WTREGEN - RRPONTSYD | 5d change ($B) | Liquidity conditions |
| `hy_spread_chg_5d` | BAMLH0A0HYM2 | 5d change (bps) | Credit / risk appetite |

### 7.3 Derived Features for Label Construction

Before constructing the label, compute a trailing correlation metric:

```
btc_spy_corr_20d = rolling 20-day correlation of daily BTC-USD returns and SPY returns, as of t
btc_spy_corr_60d = rolling 60-day correlation of daily BTC-USD returns and SPY returns, as of t
```

These are **features available at prediction time** -- they describe the current regime, not the label.

### 7.4 Binary Label Construction

```
crypto_regime_shift_label = 1 when:
  (a) abs(btc_return_5d_z) > 2.0       -- BTC moves abnormally
  AND (b) one of:
    -- risk_on_flag: btc_return_5d > 0 AND spy_return_5d > 0 AND btc_return_5d_z > spy_return_5d_z + 1.0
    -- stress_hedge_flag: btc_return_5d > 0 AND spy_return_5d < 0   (crypto decouples up)
    -- risk_off_flag: btc_return_5d_z < -2.0 AND spy_return_5d_z < -1.5  (correlated crash)

crypto_direction:
  +1 if risk_on_flag (crypto outperforms in risk-on)
  -1 if stress_hedge_flag (crypto decouples -- treated as anomalous regime to monitor)
   0 if risk_off_flag or no shift
```

### 7.5 Regression Target

```
crypto_severity = 0.40 * abs(btc_return_5d_z)
                + 0.20 * abs(btc_return_5d_z - spy_return_5d_z)   -- decorrelation magnitude
                + 0.15 * abs(usd_return_5d_z)
                + 0.15 * abs(hy_spread_chg_5d) / mad_std(hy_spread_chg_5d)
                + 0.10 * abs(vix_change_5d) / mad_std(vix_change_5d)
```

Clipped to [0, 5], normalized to [0, 1].

---

## 8. Market Pricing / Complacency Expert Labels

### 8.1 What the Label Represents

**Binary**: Is next week a "market dislocation week" where volatility, correlation, or dispersion shifts indicate the market is repricing risk? This expert is unique: it detects when the market is **already moving** so that other experts can be dampened (the "already priced" indicator from design doc Section 3.3).

**Regression**: Magnitude of the repricing event.

### 8.2 Response Vector

| Component | Ticker(s) | Return/Metric | Description |
|-----------|-----------|---------------|-------------|
| `vix_change_5d` | VIXCLS | 5d change (points) | Vol spike |
| `vix_term_slope_chg_5d` | VIX3M / VIXCLS | 5d change in ratio | Term structure inversion |
| `move_change_5d` | ^MOVE | 5d change (points) | Bond vol |
| `hy_spread_chg_5d` | BAMLH0A0HYM2 | 5d change (bps) | Credit repricing |
| `spy_tlt_corr_chg` | 20d rolling corr of SPY, TLT returns | Change in correlation from t-5 to t+5 | Correlation regime shift |
| `sector_dispersion_5d` | Std dev of 5d returns across {XLE, XLF, XLU, IWM, QQQ, EEM} | Cross-sector dispersion | Dispersion spike |
| `spy_return_5d` | SPY | 5d log return | Equity level move |

### 8.3 Binary Label Construction

```
market_dislocation_label = 1 when ANY of:
  (a) vix_change_5d > 5 points AND hy_spread_chg_5d > 20 bps
      -- vol AND credit both spike (genuine stress, not a VIX blip)
  (b) vix_term_slope drops below 0.9 (backwardation)
      AND vix_change_5d_z > 1.5
      -- acute near-term stress inverts the vol curve
  (c) sector_dispersion_5d_z > 2.0
      AND abs(spy_return_5d_z) > 1.5
      -- high dispersion with big directional move = repricing, not noise
```

### 8.4 "Already Priced" Indicator Construction

This is a derived signal, not a training label. It is computed as a feature for other experts:

```
already_priced_score = weighted average of:
  0.30 * vol_compression:  1 if VIX rose > 3 pts in trailing 5d then declined in trailing 2d, else 0
  0.25 * spread_reversion: 1 if HY OAS widened > 15bps in trailing 5d then narrowed in trailing 2d, else 0
  0.25 * corr_normalization: 1 if abs(SPY-TLT 10d corr - SPY-TLT 60d corr) < 0.1, else 0
  0.20 * dispersion_decay:  1 if sector_dispersion 5d-trailing z < sector_dispersion 10d-trailing z, else 0
```

When `already_priced_score > 0.6`, the expression selector should bias toward ETF/hedge expression and reduce single-name aggression, per design doc Section 5.2.

### 8.5 Regression Target

```
market_dislocation_severity = 0.25 * abs(vix_change_5d) / mad_std(vix_change_5d)
                            + 0.20 * abs(hy_spread_chg_5d) / mad_std(hy_spread_chg_5d)
                            + 0.20 * sector_dispersion_5d_z
                            + 0.15 * abs(move_change_5d) / mad_std(move_change_5d)
                            + 0.10 * abs(spy_return_5d_z)
                            + 0.10 * abs(spy_tlt_corr_chg) / mad_std(spy_tlt_corr_chg)
```

Clipped to [0, 5], normalized to [0, 1].

---

## 9. Unsupervised Clustering Approach

### 9.1 Motivation

The binary label definitions above embed human judgment about what constitutes a "shock week." The unsupervised approach discovers regime clusters directly from market data, then labels each week with its cluster assignment. Experts are trained to predict which cluster next week will belong to.

This is complementary, not a replacement. Both approaches should be tested in walk-forward evaluation, and the better-performing label set (or a blend) should be used per expert.

### 9.2 Response Vector for Clustering

Combine all individual expert response vectors into a single master response vector per week. Use the union of all components defined above, de-duplicated:

| # | Column | Source |
|---|--------|--------|
| 1 | `spy_return_5d_z` | SPY 5d log return, z-scored |
| 2 | `tlt_return_5d_z` | TLT 5d log return, z-scored |
| 3 | `gld_return_5d_z` | GLD 5d log return, z-scored |
| 4 | `oil_return_5d_z` | CL=F 5d log return, z-scored |
| 5 | `copper_return_5d_z` | HG=F 5d log return, z-scored |
| 6 | `bdry_return_5d_z` | BDRY 5d log return, z-scored |
| 7 | `eem_return_5d_z` | EEM 5d log return, z-scored |
| 8 | `xle_return_5d_z` | XLE 5d log return, z-scored |
| 9 | `btc_return_5d_z` | BTC-USD 5d log return, z-scored |
| 10 | `vix_change_5d_z` | VIX 5d change, z-scored |
| 11 | `hy_spread_chg_5d_z` | HY OAS 5d change, z-scored |
| 12 | `yield_2y_chg_5d_z` | DGS2 5d change, z-scored |
| 13 | `curve_10y2y_chg_5d_z` | T10Y2Y 5d change, z-scored |
| 14 | `usd_return_5d_z` | DTWEXBGS 5d log return, z-scored |
| 15 | `sector_dispersion_5d_z` | Cross-sector dispersion, z-scored |
| 16 | `brent_wti_spread_chg_5d_z` | Brent-WTI spread change, z-scored |

All values are z-scored using the same 52-week trailing robust statistics as the binary labels.

### 9.3 Clustering Methods

Test three methods; select based on silhouette score stability across walk-forward folds:

#### 9.3.1 Gaussian Mixture Model (GMM) -- Recommended Starting Point

- **Why**: Produces soft cluster probabilities, which align naturally with the expert's `probability_active` output. Handles elliptical clusters (different vol regimes will have different shapes).
- **Parameters**: `n_components` in {4, 5, 6, 7, 8}. Select via BIC on training data.
- **Covariance type**: `"full"` if sample size > 500 weeks; `"tied"` otherwise.
- **Implementation**: `sklearn.mixture.GaussianMixture`.

#### 9.3.2 K-Means

- **Why**: Simple baseline. Forces spherical clusters, which may miss regime shape but is robust with small samples.
- **Parameters**: `n_clusters` in {4, 5, 6, 7, 8}. Select via silhouette score.
- **Implementation**: `sklearn.cluster.KMeans(n_init=20, random_state=42)`.

#### 9.3.3 HDBSCAN

- **Why**: Does not require specifying cluster count; can identify noise points (weeks that do not cleanly belong to any regime).
- **Parameters**: `min_cluster_size` in {10, 15, 20}. `min_samples=5`.
- **Caveat**: May produce too many or too few clusters. Noise-labeled points must be handled (assign to nearest cluster centroid or treat as a separate "uncertain" regime).
- **Implementation**: `hdbscan.HDBSCAN`.

### 9.4 Making Clusters Stable Across Time

Cluster assignments are inherently unstable: re-running k-means on a slightly different training window can produce a different label permutation or different cluster count. This breaks walk-forward training.

**Stabilization protocol:**

1. **Anchor clusters on an expanding window.** Fit the clustering model on the first 3 years of data (the "anchor fit"). For subsequent walk-forward folds, re-fit on the expanding training window but initialize centroids from the previous fold's centroids (`init=previous_centroids` for k-means; warm-start for GMM).

2. **Hungarian matching.** After each re-fit, align new cluster labels to the anchor labels using the Hungarian algorithm on centroid distances. This prevents label permutation across folds.

3. **Centroid drift monitoring.** Track the Euclidean distance between each re-fit's centroids and the anchor centroids. If any centroid drifts more than 2 standard deviations from its anchor position, flag for manual review -- the regime structure may have genuinely changed (e.g., post-COVID).

4. **Minimum cluster stability threshold.** A cluster must contain at least 5% of the training samples to be considered valid. Clusters below this threshold are merged with their nearest neighbor.

### 9.5 Mapping Clusters to Actionable Regime Labels

After clustering, each cluster must be interpreted and mapped to an actionable label. This is a one-time manual step per anchor fit, validated at each re-fit.

**Procedure:**

1. Compute the cluster centroid (mean response vector per cluster).
2. For each cluster, identify the dominant asset response pattern:
   - Which components have the largest absolute centroid values?
   - Do they match a known regime archetype?
3. Assign a human-readable regime name from this taxonomy:

| Cluster Archetype | Dominant Signature | Maps to Expert(s) |
|-------------------|--------------------|--------------------|
| `risk_off_broad` | SPY down, TLT up, GLD up, VIX up | Conflict, Market Pricing |
| `energy_supply_shock` | Oil up, XLE up, inflation expectations up, SPY flat/down | Shipping, Commodity, Sanctions |
| `rates_hawkish_shock` | Yields up, TLT down, SPY down, USD up | Rates |
| `rates_easing_rally` | Yields down, TLT up, SPY up, USD down | Rates |
| `em_contagion` | EEM down, EM FX weak, USD up, HY spreads wide | Sanctions, Conflict |
| `crypto_divergence` | BTC decouples from SPY correlation structure | Crypto |
| `low_vol_grind` | All z-scores near zero, VIX declining | Market Pricing (complacency) |
| `dispersion_spike` | High sector dispersion, mixed directional signals | Market Pricing |

4. For each expert, the relevant cluster labels become the training target. For example, the Shipping expert trains on `P(cluster = energy_supply_shock | features)`.

### 9.6 Label Construction from Clusters

```
For expert E with relevant cluster set C_E:
  cluster_label_E[t] = 1  if cluster_assignment[t] in C_E
                       0  otherwise

  cluster_severity_E[t] = max over c in C_E of: P(cluster = c | response_vector[t])
                          (using GMM soft probabilities)
```

---

## 10. Walk-Forward and Anti-Leakage Protocol

### 10.1 Timeline Separation

```
|--- Training window (expanding) ---|-- Gap --|--- Label window ---|
                                     ^t (prediction date)

Features: computed from data [t-W, t]  where W is the feature lookback window
Labels:   computed from data [t+1, t+5] (next-week forward returns)
Gap:      0 trading days for features-to-label (features end at t, labels start at t+1)
          5 trading days between train and test in walk-forward splits (ExpertTrainer gap=5)
```

### 10.2 Anti-Leakage Checklist for Labels

| # | Rule | Rationale |
|---|------|-----------|
| 1 | Labels use ONLY forward returns from [t+1, t+5] | The label must represent the outcome we are trying to predict |
| 2 | Z-score reference windows for label thresholds end at t, never at t+5 | The sigma thresholds must be known at prediction time |
| 3 | Rolling statistics for z-scores use an expanding or trailing window ending at t | No future data in the normalization denominator |
| 4 | Cluster model is fitted only on training-window data | Cluster centroids must not see test-period response vectors |
| 5 | Hungarian matching for cluster alignment uses only training-window centroids | Cluster label semantics must be stable without test data |
| 6 | "Already priced" indicator uses only trailing data ending at t | This is a feature, not a label; no forward information allowed |
| 7 | Monthly macro series (CPI, NFP, PCE) are lagged by their publication delay | A CPI print released on the 12th of month M cannot be used as a feature before that date |
| 8 | Expert OOS predictions for the meta-combiner are generated from walk-forward folds where the expert never trained on the fold's test set | Prevents double-dipping at the stacking layer (design doc Section 4.4) |

### 10.3 Walk-Forward Configuration

Matches `ExpertTrainer` defaults from `src/engine/experts/trainer.py`:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `min_train` | 60 weeks | Minimum training window before first prediction |
| `test_size` | 20 weeks | Each fold predicts 20 weeks ahead |
| `gap` | 5 weeks | 5-week gap between training and test to prevent label leakage from overlapping return windows |
| `expanding` | True | Training window grows over time (more stable); set False for rolling window (more adaptive) |

### 10.4 Label Freshness and Staleness

Labels must be re-computed whenever new price data arrives. The z-score reference window advances weekly, so thresholds evolve. A label computed with a 52-week reference ending 2024-01-05 is slightly different from the same label re-computed with a reference ending 2024-01-12.

**Rule:** Always compute labels fresh at each walk-forward fold using the rolling reference window ending at that fold's training cutoff. Never pre-compute labels once and reuse them across folds.

### 10.5 Label Quality Monitoring

Track these diagnostics per expert per walk-forward fold:

| Metric | Acceptable Range | Action if Out of Range |
|--------|-----------------|----------------------|
| Positive label rate | 5-25% | If < 5%, thresholds are too strict -- relax by 0.25 sigma. If > 25%, thresholds are too loose -- tighten by 0.25 sigma. |
| Label autocorrelation (lag-1) | < 0.4 | High autocorrelation means shock "weeks" cluster into multi-week episodes. This is fine for the system (impulse continuation) but may inflate apparent accuracy. Track it. |
| Label correlation across experts | < 0.5 pairwise | If two experts have highly correlated labels, their independent value in the stacker is limited. Consider merging or differentiating their response vectors. |
