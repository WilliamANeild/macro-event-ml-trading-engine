# Macro Data Series Reference

Comprehensive catalog of all macro economic data series for the geopolitical/macro event-driven trading engine. Data is sourced via FRED API (free tier) and Yahoo Finance (`yfinance`).

**System context**: The engine routes data through `FREDDataSource` and `YahooDataSource` into `FeatureBuilder` and `EventFeatureBuilder`, which feed expert models, the `RegimeDetector`, the `MetaStacker`, and ultimately the `PortfolioOptimizer` and `DerivativesOverlay`.

---

## 1. Volatility & Risk Metrics

### 1.1 VIX and VIX Term Structure

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `VIXCLS` | FRED | CBOE VIX index (close) | Daily | T+0 (same-day close) |
| `^VIX` | Yahoo | VIX intraday / real-time proxy | Daily | T+0 |
| `^VIX3M` | Yahoo | CBOE 3-month VIX (VIX3M) | Daily | T+0 |
| `^VIX9D` | Yahoo | CBOE 9-day VIX | Daily | T+0 |
| `^VIX1Y` | Yahoo | CBOE 1-year VIX | Daily | T+0 |

**Why it matters**: VIX is the primary input to `RegimeDetector` (vol_z score drives crisis/euphoria classification). VIX term structure (VIX3M / VIXCLS ratio) signals whether markets are pricing near-term stress vs. complacency. A ratio > 1 (backwardation) flags acute stress; < 1 (contango) is normal.

**Transformation needed**:
- Compute `VIX_TERM_SLOPE = VIX3M / VIXCLS` (ratio)
- Compute rolling z-score of VIXCLS over 60-day window
- Compute daily change in VIX (vol-of-vol proxy)

**Currently in system**: `VIXCLS` is in `DEFAULT_SERIES` in `fred_loader.py` as `"VIX"`.

---

### 1.2 Credit Spreads (ICE BofA Indices)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `BAMLH0A0HYM2` | FRED | ICE BofA US High Yield Option-Adjusted Spread | Daily | T+1 |
| `BAMLC0A0CM` | FRED | ICE BofA US Corporate Master OAS | Daily | T+1 |
| `BAMLH0A0HYM2EY` | FRED | ICE BofA US HY Effective Yield | Daily | T+1 |
| `BAMLC0A4CBBB` | FRED | ICE BofA BBB Corporate OAS | Daily | T+1 |
| `BAMLHE00EHYIEY` | FRED | ICE BofA Euro High Yield Effective Yield | Daily | T+1 |
| `BAMLH0A1HYBB` | FRED | ICE BofA BB US HY OAS | Daily | T+1 |
| `BAMLH0A3HYC` | FRED | ICE BofA CCC & Lower US HY OAS | Daily | T+1 |
| `BAMLC0A1CAAA` | FRED | ICE BofA AAA Corporate OAS | Daily | T+1 |

**Why it matters**: Credit spreads are the single best real-time measure of systemic financial stress. HY OAS widening predicts risk-off cascades. The `CCC - BB` spread differential captures credit quality rotation, a leading indicator of recession. Used by the regime detector and the portfolio risk estimator.

**Transformation needed**:
- `HY_IG_SPREAD = BAMLH0A0HYM2 - BAMLC0A0CM` (excess HY premium over IG)
- `CCC_BB_SPREAD = BAMLH0A3HYC - BAMLH0A1HYBB` (credit quality stress)
- Rolling z-scores (60-day) of all OAS series
- 5-day rate of change (momentum of spread widening)

---

### 1.3 MOVE Index (Bond Volatility)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `^MOVE` | Yahoo | ICE BofA MOVE Index (Treasury vol) | Daily | T+0 |

**Why it matters**: MOVE is the bond market equivalent of VIX. Spikes in MOVE precede liquidity crises and forced selling. The VIX/MOVE ratio is a cross-asset stress indicator. Used by the derivatives overlay activation rule (crisis/transition regimes).

**Transformation needed**:
- `VIX_MOVE_RATIO = VIXCLS / MOVE` (cross-asset vol comparison)
- Rolling z-score (60-day)
- Note: Yahoo ticker `^MOVE` may have limited free history. Alternative: proxy via `BAMLH0A0HYM2` + yield curve vol.

---

### 1.4 Cross-Asset Correlation Proxies

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `SPY` | Yahoo | S&P 500 ETF | Daily | T+0 |
| `TLT` | Yahoo | iShares 20+ Year Treasury ETF | Daily | T+0 |
| `GLD` | Yahoo | SPDR Gold ETF | Daily | T+0 |
| `HYG` | Yahoo | iShares High Yield Corporate Bond ETF | Daily | T+0 |
| `LQD` | Yahoo | iShares Investment Grade Bond ETF | Daily | T+0 |

**Why it matters**: Rolling correlations between SPY-TLT, SPY-GLD, SPY-HYG reveal regime shifts. When SPY-TLT correlation turns positive, the traditional 60/40 hedge breaks down -- this is a critical input for portfolio construction and hedge activation.

**Transformation needed**:
- 20-day and 60-day rolling correlations between all pairs
- These are derived features, not direct inputs. Computed in `FeatureBuilder`.

---

## 2. US Rates & Yield Curve

### 2.1 Treasury Yields (All Major Tenors)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `DGS1MO` | FRED | 1-Month Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS3MO` | FRED | 3-Month Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS6MO` | FRED | 6-Month Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS1` | FRED | 1-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS2` | FRED | 2-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS3` | FRED | 3-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS5` | FRED | 5-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS7` | FRED | 7-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS10` | FRED | 10-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS20` | FRED | 20-Year Treasury Constant Maturity Rate | Daily | T+1 |
| `DGS30` | FRED | 30-Year Treasury Constant Maturity Rate | Daily | T+1 |

**Why it matters**: The full yield curve is essential for rates experts and curve-based regime detection. Short-end yields reflect Fed expectations; long-end yields reflect term premium and inflation expectations. `DGS10` is already in `DEFAULT_SERIES` as `"10Y_yield"`.

**Transformation needed**:
- Daily changes (dYield) for all tenors
- Butterfly: `2*DGS5 - DGS2 - DGS10` (curvature)
- Slope: see pre-computed FRED spreads below
- Level/slope/curvature PCA decomposition (optional, advanced)

---

### 2.2 Yield Curve Spreads (Pre-Computed on FRED)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `T10Y2Y` | FRED | 10-Year minus 2-Year Treasury spread | Daily | T+1 |
| `T10Y3M` | FRED | 10-Year minus 3-Month Treasury spread | Daily | T+1 |
| `T10YFF` | FRED | 10-Year Treasury minus Fed Funds Rate | Daily | T+1 |
| `T5YFF` | FRED | 5-Year Treasury minus Fed Funds Rate | Daily | T+1 |

**Why it matters**: `T10Y2Y` inversion is the most-cited recession predictor (100% hit rate post-WWII with 6-18 month lead). `T10Y3M` is the Fed's preferred near-term recession indicator. These are direct features for economic-regime experts.

**Transformation needed**:
- Direct input (already a spread)
- Binary inversion flags: `T10Y2Y < 0`, `T10Y3M < 0`
- Days-since-inversion counter
- Rolling z-scores

---

### 2.3 Policy Rates

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `DFF` | FRED | Effective Federal Funds Rate | Daily | T+1 |
| `DFEDTARU` | FRED | Fed Funds Target Rate Upper Bound | Irregular (at FOMC) | T+0 |
| `DFEDTARL` | FRED | Fed Funds Target Rate Lower Bound | Irregular (at FOMC) | T+0 |
| `SOFR` | FRED | Secured Overnight Financing Rate | Daily | T+1 |
| `OBFR` | FRED | Overnight Bank Funding Rate | Daily | T+1 |
| `IORB` | FRED | Interest Rate on Reserve Balances | Daily | T+1 |

**Why it matters**: Fed policy rate is the anchor for all risk-free rates. The spread between DFF and SOFR/OBFR reveals plumbing stress. Rate-change expectations (DFF vs. DFEDTARU gap) inform how close the market is to a pivot.

**Transformation needed**:
- `DFF_TARGET_SPREAD = DFF - (DFEDTARU + DFEDTARL) / 2` (measures plumbing stress)
- Direct input for level; delta for rate changes

---

### 2.4 Real Rates / TIPS Yields

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `DFII5` | FRED | 5-Year TIPS Yield (real rate) | Daily | T+1 |
| `DFII7` | FRED | 7-Year TIPS Yield | Daily | T+1 |
| `DFII10` | FRED | 10-Year TIPS Yield (real rate) | Daily | T+1 |
| `DFII20` | FRED | 20-Year TIPS Yield | Daily | T+1 |
| `DFII30` | FRED | 30-Year TIPS Yield | Daily | T+1 |

**Why it matters**: Real rates are the true "cost of money" and arguably the most important single variable for asset prices. Rising real rates crush long-duration assets (growth stocks, gold). Falling real rates fuel risk-on. Used as direct input to equity and commodity experts.

**Transformation needed**:
- Daily changes
- Rolling z-score
- `REAL_RATE_MOMENTUM = 20-day change in DFII10`

---

## 3. Inflation

### 3.1 Breakeven Inflation Rates

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `T5YIE` | FRED | 5-Year Breakeven Inflation Rate | Daily | T+1 |
| `T10YIE` | FRED | 10-Year Breakeven Inflation Rate | Daily | T+1 |
| `T5YIFR` | FRED | 5-Year, 5-Year Forward Inflation Expectation | Daily | T+1 |

**Why it matters**: Breakevens are the market's real-time inflation expectations. `T5YIE` captures near-term inflation expectations; `T5YIFR` (5y5y forward) captures long-term inflation anchoring. De-anchoring of `T5YIFR` above 2.5% or below 1.5% is a major regime signal. `T5YIE` is already in `DEFAULT_SERIES` as `"breakeven_inflation"`.

**Transformation needed**:
- `INFLATION_TERM_STRUCTURE = T10YIE - T5YIE`
- Rolling z-scores
- 5y5y forward deviation from 2.0% target
- Direct input plus delta

---

### 3.2 CPI Series

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `CPIAUCSL` | FRED | CPI for All Urban Consumers (seasonally adjusted) | Monthly | ~2 weeks |
| `CPILFESL` | FRED | Core CPI (ex food and energy, SA) | Monthly | ~2 weeks |
| `CPIAUCNS` | FRED | CPI for All Urban Consumers (not SA) | Monthly | ~2 weeks |
| `CUSR0000SETA01` | FRED | CPI: Used Cars and Trucks | Monthly | ~2 weeks |
| `CUSR0000SEHA` | FRED | CPI: Shelter (Rent of Shelter) | Monthly | ~2 weeks |
| `CPIENGSL` | FRED | CPI: Energy | Monthly | ~2 weeks |

**Why it matters**: CPI prints are the single highest-impact scheduled macro events for the system. CPI surprise (actual vs. Cleveland Fed Nowcast) drives same-day repricing across all assets. Shelter and used-cars components are watched for inflection points.

**Transformation needed**:
- YoY change: `(CPIAUCSL / CPIAUCSL.shift(12) - 1) * 100`
- MoM change: `(CPIAUCSL / CPIAUCSL.shift(1) - 1) * 100`
- MoM annualized: `MoM * 12`
- Core vs. headline divergence
- **Revision risk**: CPI is revised. Use "final" values for backtest; "advance" for live signals.

---

### 3.3 PCE (Fed's Preferred Measure)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `PCEPI` | FRED | PCE Price Index | Monthly | ~4 weeks |
| `PCEPILFE` | FRED | Core PCE Price Index (ex food and energy) | Monthly | ~4 weeks |
| `DPCERD3Q086SBEA` | FRED | Real PCE (quantity, quarterly) | Quarterly | ~4 weeks |

**Why it matters**: Core PCE is the Fed's official target metric (2% target). Divergence between CPI and PCE signals methodological vs. real inflation shifts. Higher lag than CPI, but PCE releases still move markets.

**Transformation needed**:
- Same YoY/MoM as CPI
- `CPI_PCE_GAP = CPI_YoY - PCE_YoY`
- **Revision risk**: PCE is heavily revised; use vintage data for proper backtesting.

---

### 3.4 Inflation Expectations (Survey-Based)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `MICH` | FRED | University of Michigan 1-Year Inflation Expectations | Monthly | ~2 weeks |
| `EXPINF1YR` | FRED | Cleveland Fed 1-Year Expected Inflation | Monthly | T+1 month |
| `EXPINF10YR` | FRED | Cleveland Fed 10-Year Expected Inflation | Monthly | T+1 month |

**Why it matters**: Survey-based expectations diverging from market-based breakevens signals a sentiment/positioning mismatch. UMich expectations spiking is a political signal (consumer anxiety) as much as an inflation signal. Used by inflation-theme experts.

**Transformation needed**:
- `SURVEY_MARKET_GAP = MICH - T5YIE` (survey vs. market disagreement)
- MoM change
- Direct input

---

## 4. FX / USD

### 4.1 Dollar Indices (FRED)

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `DTWEXBGS` | FRED | Trade-Weighted USD Index: Broad, Goods and Services | Daily | T+1 |
| `DTWEXAFEGS` | FRED | Trade-Weighted USD Index: Advanced Foreign Economies | Daily | T+1 |
| `DTWEXEMEGS` | FRED | Trade-Weighted USD Index: Emerging Market Economies | Daily | T+1 |

**Why it matters**: `DTWEXBGS` is the FRED proxy for DXY. Dollar strength is the master variable for global macro -- a strong dollar tightens global financial conditions, pressures EM debt, depresses commodity prices, and hurts US multinational earnings. `DTWEXBGS` is already in `DEFAULT_SERIES` as `"usd_index"`.

**Transformation needed**:
- Daily returns / log returns
- Rolling z-score (20-day, 60-day)
- `EM_DM_FX_DIVERGENCE = DTWEXEMEGS / DTWEXAFEGS` (EM stress relative to DM)
- 5-day momentum

---

### 4.2 Major FX Pairs (Yahoo Finance)

| Ticker | Source | Description | Frequency | Lag |
|--------|--------|-------------|-----------|-----|
| `EURUSD=X` | Yahoo | EUR/USD | Daily | T+0 |
| `USDJPY=X` | Yahoo | USD/JPY | Daily | T+0 |
| `GBPUSD=X` | Yahoo | GBP/USD | Daily | T+0 |
| `USDCHF=X` | Yahoo | USD/CHF | Daily | T+0 |
| `AUDUSD=X` | Yahoo | AUD/USD | Daily | T+0 |
| `USDCAD=X` | Yahoo | USD/CAD | Daily | T+0 |
| `NZDUSD=X` | Yahoo | NZD/USD | Daily | T+0 |

**Why it matters**: Individual pairs carry distinct macro information. USDJPY is the global carry trade proxy (JPY strengthening = carry unwind = risk-off). AUDUSD is a China/commodities proxy. USDCHF is a safe-haven proxy. These feed geopolitical/regional expert models.

**Transformation needed**:
- Daily returns
- Rolling realized vol (20-day)
- Cross-pair correlations for regime detection

---

### 4.3 EM FX Stress Proxies (Yahoo Finance)

| Ticker | Source | Description | Frequency | Lag |
|--------|--------|-------------|-----------|-----|
| `USDMXN=X` | Yahoo | USD/MXN (Mexico Peso) | Daily | T+0 |
| `USDZAR=X` | Yahoo | USD/ZAR (South Africa Rand) | Daily | T+0 |
| `USDBRL=X` | Yahoo | USD/BRL (Brazil Real) | Daily | T+0 |
| `USDTRY=X` | Yahoo | USD/TRY (Turkish Lira) | Daily | T+0 |
| `USDCNY=X` | Yahoo | USD/CNY (Chinese Yuan) | Daily | T+0 |
| `USDINR=X` | Yahoo | USD/INR (Indian Rupee) | Daily | T+0 |
| `USDKRW=X` | Yahoo | USD/KRW (Korean Won) | Daily | T+0 |

**Why it matters**: EM FX weakness (USD strengthening vs. EM) is the canary in the coal mine for global financial stress. A composite EM FX weakness index feeds the geopolitical/contagion expert. MXN is particularly liquid and acts as a global risk proxy.

**Transformation needed**:
- Composite `EM_FX_STRESS = equal-weighted average return of USD vs. EM basket`
- Individual pair returns and vol
- Divergence from DXY (idiosyncratic EM stress)

---

## 5. Commodities

### 5.1 Energy

| Series ID / Ticker | Source | Description | Frequency | Lag |
|---------------------|--------|-------------|-----------|-----|
| `DCOILWTICO` | FRED | WTI Crude Oil Spot Price ($/barrel) | Daily | T+1 |
| `DCOILBRENTEU` | FRED | Brent Crude Oil Spot Price ($/barrel) | Daily | T+1 |
| `CL=F` | Yahoo | WTI Crude Oil Futures (front month) | Daily | T+0 |
| `BZ=F` | Yahoo | Brent Crude Oil Futures (front month) | Daily | T+0 |
| `DHHNGSP` | FRED | Henry Hub Natural Gas Spot Price ($/MMBtu) | Daily | T+1 |
| `NG=F` | Yahoo | Natural Gas Futures (front month) | Daily | T+0 |
| `GASREGW` | FRED | US Regular Gasoline Price (weekly avg) | Weekly | T+1 week |

**Why it matters**: Oil is the most geopolitically sensitive commodity. Brent-WTI spread reflects logistics/sanctions dynamics. Nat gas (Henry Hub) is the European energy crisis proxy when combined with TTF (not on free FRED). Oil price spikes feed directly into inflation expectations and consumer sentiment. `DCOILWTICO` is already in `DEFAULT_SERIES` as `"oil_price"`.

**Transformation needed**:
- `BRENT_WTI_SPREAD = DCOILBRENTEU - DCOILWTICO` (geopolitical premium)
- Daily returns and rolling vol
- Rolling z-score
- Backwardation/contango from futures curves (requires multiple contract months via Yahoo)

---

### 5.2 Precious Metals

| Ticker | Source | Description | Frequency | Lag |
|--------|--------|-------------|-----------|-----|
| `GC=F` | Yahoo | Gold Futures (front month) | Daily | T+0 |
| `SI=F` | Yahoo | Silver Futures (front month) | Daily | T+0 |
| `GLD` | Yahoo | SPDR Gold ETF | Daily | T+0 |
| `PA=F` | Yahoo | Palladium Futures | Daily | T+0 |

**Why it matters**: Gold is the ultimate safe-haven and inflation hedge. Gold strength relative to real rates (DFII10) reveals demand for safety beyond rate fundamentals. Gold/Silver ratio is a risk-on/off indicator (high ratio = defensive positioning).

**Transformation needed**:
- `GOLD_SILVER_RATIO = GC=F / SI=F`
- Gold return adjusted for real rate moves: `Gold_return - beta * DFII10_change`
- Rolling z-score of gold returns

---

### 5.3 Industrial Metals & Commodities

| Ticker | Source | Description | Frequency | Lag |
|--------|--------|-------------|-----------|-----|
| `HG=F` | Yahoo | Copper Futures (front month) | Daily | T+0 |
| `CHRIS/CME_HG1` | Yahoo | Copper (alternate ticker, try `HG=F`) | Daily | T+0 |
| `ALI=F` | Yahoo | Aluminum Futures | Daily | T+0 |
| `COPX` | Yahoo | Global X Copper Miners ETF (copper proxy) | Daily | T+0 |
| `DBB` | Yahoo | Invesco DB Base Metals Fund | Daily | T+0 |

**Why it matters**: Copper ("Dr. Copper") is the classic global growth indicator. Copper/Gold ratio is a market-implied growth/safety ratio that tracks the 10Y yield closely. Industrial metals broadly reflect China demand and global manufacturing health.

**Transformation needed**:
- `COPPER_GOLD_RATIO = HG=F / GC=F` (growth vs. safety signal)
- Correlation of copper/gold ratio with DGS10 (should track closely; divergence is a signal)
- Daily returns

---

### 5.4 Agriculture & Freight

| Ticker / Series | Source | Description | Frequency | Lag |
|------------------|--------|-------------|-----------|-----|
| `ZW=F` | Yahoo | Wheat Futures | Daily | T+0 |
| `ZC=F` | Yahoo | Corn Futures | Daily | T+0 |
| `ZS=F` | Yahoo | Soybean Futures | Daily | T+0 |
| `BDIY` | Yahoo | Baltic Dry Index (try `^BDI` or use ETF `BDRY`) | Daily | T+0 |
| `BDRY` | Yahoo | Breakwave Dry Bulk Shipping ETF (Baltic Dry proxy) | Daily | T+0 |

**Why it matters**: Grain prices spike on geopolitical events (Black Sea conflict, export bans). Baltic Dry Index is a pure supply/demand indicator for global trade volumes, uncontaminated by financial speculation. BDI collapse = global trade slowdown.

**Transformation needed**:
- Daily returns
- `FOOD_PRICE_INDEX = equal-weighted wheat + corn + soy returns`
- Note: Baltic Dry via Yahoo is unreliable. `BDRY` ETF is the best free proxy.

---

## 6. Liquidity & Financial Conditions

### 6.1 Fed Balance Sheet

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `WALCL` | FRED | Federal Reserve Total Assets (balance sheet) | Weekly (Wed) | T+1 day |
| `WTREGEN` | FRED | Treasury General Account (TGA) balance | Weekly (Wed) | T+1 day |
| `RRPONTSYD` | FRED | Overnight Reverse Repo Facility (ON RRP) | Daily | T+1 |
| `WRESBAL` | FRED | Reserve Balances with Fed | Weekly (Wed) | T+1 day |

**Why it matters**: `WALCL` (Fed balance sheet) expansion/contraction is the most powerful liquidity signal. QT reduces WALCL, draining reserves. `WTREGEN` (TGA) drawdowns inject liquidity; rebuilds drain it. `RRPONTSYD` (ON RRP) decline means money is leaving the facility and entering the banking system (bullish for risk). Net liquidity proxy: `WALCL - WTREGEN - RRPONTSYD`.

**Transformation needed**:
- `NET_LIQUIDITY = WALCL - WTREGEN - RRPONTSYD` (the "liquidity proxy" that tracks SPX)
- Weekly change in each component
- Rolling 4-week change in NET_LIQUIDITY
- Interpolate weekly to daily (forward-fill)

---

### 6.2 Financial Conditions Indices

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `NFCI` | FRED | Chicago Fed National Financial Conditions Index | Weekly (Wed) | T+1 week |
| `ANFCI` | FRED | Chicago Fed Adjusted NFCI (removes business cycle) | Weekly (Wed) | T+1 week |
| `STLFSI4` | FRED | St. Louis Fed Financial Stress Index | Weekly (Fri) | T+1 week |
| `KCFSI` | FRED | Kansas City Fed Financial Stress Index | Monthly | T+1 month |

**Why it matters**: NFCI > 0 means financial conditions are tighter than average; < 0 means looser. The adjusted version (ANFCI) removes business cycle effects, isolating pure financial stress. These are composite indices that summarize dozens of underlying series into one number. Direct input to the regime detector.

**Transformation needed**:
- Direct input (already composite)
- Weekly change (delta)
- Interpolate to daily (forward-fill)
- `NFCI > 0` binary flag for "tight conditions"

---

### 6.3 Interbank / Money Market Stress

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `TEDRATE` | FRED | TED Spread (3M LIBOR - 3M T-bill) | **Discontinued** | N/A |
| `DPRIME` | FRED | Bank Prime Loan Rate | Daily | T+0 |
| `RIFSPPFAAD90NB` | FRED | 90-Day AA Financial Commercial Paper Rate | Daily | T+1 |
| `RIFSPPFAAD01NB` | FRED | Overnight AA Financial Commercial Paper Rate | Daily | T+1 |
| `WDTGAL` | FRED | Discount Window Primary Credit | Weekly | T+1 week |

**Why it matters**: TED spread is discontinued (LIBOR phase-out). The replacement is `SOFR - T-bill` or commercial paper spreads. `RIFSPPFAAD90NB - DGS3MO` serves as a modern TED spread equivalent. Discount window borrowing (`WDTGAL`) spikes signal individual bank stress (e.g., SVB crisis).

**Transformation needed**:
- `MODERN_TED = RIFSPPFAAD90NB - DGS3MO`
- Direct input
- Spike detection (> 2 sigma from 60-day mean)

---

### 6.4 Money Supply

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `M2SL` | FRED | M2 Money Stock (seasonally adjusted) | Monthly | ~3 weeks |
| `WM2NS` | FRED | M2 Money Stock (weekly, not SA) | Weekly | T+1 week |
| `M1SL` | FRED | M1 Money Stock (seasonally adjusted) | Monthly | ~3 weeks |
| `BOGMBASE` | FRED | Monetary Base | Biweekly | ~2 weeks |

**Why it matters**: M2 YoY growth is a long-lead indicator of inflation and nominal GDP. M2 contraction (2022-2023 was first since 1930s) preceded the disinflation. Weekly M2 is noisier but more timely than monthly.

**Transformation needed**:
- YoY change: `(M2SL / M2SL.shift(12) - 1) * 100`
- MoM change
- Interpolate weekly to daily

---

## 7. Economic Activity

### 7.1 Labor Market

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `ICSA` | FRED | Initial Jobless Claims (SA) | Weekly (Thu) | T+5 days |
| `CCSA` | FRED | Continued Claims (SA) | Weekly (Thu) | T+2 weeks |
| `PAYEMS` | FRED | Total Nonfarm Payrolls (SA) | Monthly | ~5 weeks |
| `UNRATE` | FRED | Unemployment Rate | Monthly | ~5 weeks |
| `CIVPART` | FRED | Labor Force Participation Rate | Monthly | ~5 weeks |
| `CES0500000003` | FRED | Average Hourly Earnings (SA) | Monthly | ~5 weeks |
| `JTSJOL` | FRED | JOLTS Job Openings | Monthly | ~6 weeks |
| `SAHM` | FRED | Sahm Rule Real-Time Recession Indicator | Monthly | T+1 month |

**Why it matters**: Initial claims are the highest-frequency hard economic data (weekly). A 4-week moving average crossing above 250K historically signals recession onset. The Sahm Rule (`SAHM >= 0.5`) is a real-time recession indicator. NFP surprises are top-3 market-moving events.

**Transformation needed**:
- `ICSA_4WK_AVG = ICSA.rolling(4).mean()`
- `SAHM >= 0.5` binary recession flag
- YoY change in payrolls
- Interpolate to daily (forward-fill)
- **Revision risk**: NFP and JOLTS are heavily revised. Use first-release vintage for backtesting.

---

### 7.2 PMI / Business Surveys

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `MANEMP` | FRED | Manufacturing Employment (proxy for manufacturing PMI direction) | Monthly | ~5 weeks |
| `AMTMNO` | FRED | Manufacturers' New Orders: Total Manufacturing | Monthly | ~6 weeks |
| `NEWORDER` | FRED | ISM Manufacturing: New Orders Index | Monthly | T+1 day (1st business day) |
| `NAPM` | FRED | ISM Manufacturing PMI Composite | Monthly | T+1 day |
| `NMFCI` | FRED | ISM Non-Manufacturing NMI (Services) | Monthly | T+3 days |
| `RSAFS` | FRED | Advance Retail Sales: Total | Monthly | ~2 weeks |
| `UMCSENT` | FRED | University of Michigan Consumer Sentiment | Monthly (prelim + final) | T+0 (prelim mid-month) |

**Why it matters**: ISM Manufacturing PMI crossing 50 is the expansion/contraction line. New Orders is the most forward-looking PMI sub-component. Consumer sentiment (UMCSENT) diverging from hard data (retail sales) creates contrarian opportunities.

**Transformation needed**:
- `PMI_ABOVE_50 = NAPM > 50` binary flag
- MoM change
- `HARD_SOFT_GAP = z(RSAFS_yoy) - z(UMCSENT)` (hard vs. soft data divergence)
- Direct input for levels

---

### 7.3 Industrial Production & Output

| Series ID | Source | Description | Frequency | Lag |
|-----------|--------|-------------|-----------|-----|
| `INDPRO` | FRED | Industrial Production Index (SA) | Monthly | ~2 weeks |
| `TCU` | FRED | Capacity Utilization: Total Industry | Monthly | ~2 weeks |
| `DGORDER` | FRED | Manufacturers' New Orders: Durable Goods | Monthly | ~4 weeks |
| `HOUST` | FRED | Housing Starts (SAAR) | Monthly | ~3 weeks |
| `PERMIT` | FRED | Building Permits (SAAR) | Monthly | ~3 weeks |

**Why it matters**: Industrial production is the broadest measure of real economic output at monthly frequency. Capacity utilization above 80% historically correlates with inflation pressure. Housing starts/permits are leading indicators (long construction lead times).

**Transformation needed**:
- YoY and MoM changes
- `TCU > 80` inflationary-pressure flag
- Direct input for levels

---

## 8. Central Bank Related

### 8.1 FOMC Meeting Dates & Fed Communications

| Data Point | Source | How to Access | Frequency |
|------------|--------|---------------|-----------|
| FOMC meeting dates | Federal Reserve website | Scrape from `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` or use static calendar (8 meetings/year) | 8x/year |
| Fed dot plot (SEP) | Federal Reserve | Published at 4 of 8 FOMC meetings (Mar, Jun, Sep, Dec) in Summary of Economic Projections. No machine-readable FRED series. Parse from Fed website or use third-party. | 4x/year |
| Fed minutes | Federal Reserve | Released 3 weeks after each FOMC meeting. Text analysis via NLP. | 8x/year |
| Fed funds futures | Yahoo: `ZQ=F` | 30-day Fed Funds Futures (front month). Implied rate = `100 - price`. Use multiple months for term structure. | Daily |
| CME FedWatch proxy | Derived | Compute from Fed funds futures vs. current rate. | Daily |

**Implementation note**: For FOMC dates, maintain a static JSON calendar file updated annually. For dot plot data, no free API exists -- store historical dot plots manually or scrape from the Fed's SEP releases.

---

### 8.2 ECB Rate Decisions

| Data Point | Source | How to Access | Frequency |
|------------|--------|---------------|-----------|
| ECB Main Refinancing Rate | FRED: `ECBMRRFR` or `INTDSREZQ193N` | FRED has ECB policy rates but with lag | ~6 weeks per decision |
| ECB deposit facility rate | FRED: `ECBDFR` | Deposit rate (current policy rate) | Irregular |
| ECB meeting dates | ECB website | `https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html` -- maintain static calendar | ~8x/year |
| EURIBOR 3M | FRED: `IR3TIB01EZM156N` | Interbank rate reflecting ECB expectations | Monthly |

---

### 8.3 BOJ Rate Decisions

| Data Point | Source | How to Access | Frequency |
|------------|--------|---------------|-----------|
| BOJ Policy Rate | FRED: `IRSTCI01JPM156N` | Short-term interest rate, Japan | Monthly |
| BOJ meeting dates | BOJ website | `https://www.boj.or.jp/en/mopo/mpmdeci/` -- maintain static calendar | ~8x/year |
| Japan 10Y yield | FRED: `IRLTLT01JPM156N` | Long-term government bond yield | Monthly |
| USDJPY | Yahoo: `USDJPY=X` | Best real-time BOJ impact proxy | Daily |

**Implementation note**: BOJ data on FRED is monthly and heavily lagged. For real-time BOJ impact, use USDJPY moves and JGB yield (via Yahoo: `^TNX` equivalent does not exist for Japan on Yahoo). The practical approach is to use USDJPY as the real-time BOJ proxy and supplement with FRED monthly data for longer-horizon features.

---

## 9. Equity Market Proxies (for cross-asset context)

These are not macro data per se, but essential for cross-asset regime detection and the `RiskEstimator`.

| Ticker | Source | Description | Frequency | Use Case |
|--------|--------|-------------|-----------|----------|
| `SPY` | Yahoo | S&P 500 ETF | Daily | Benchmark, correlation anchor |
| `QQQ` | Yahoo | Nasdaq 100 ETF | Daily | Growth/tech proxy |
| `IWM` | Yahoo | Russell 2000 ETF | Daily | Small-cap / domestic economy proxy |
| `EEM` | Yahoo | MSCI Emerging Markets ETF | Daily | EM equity stress |
| `EFA` | Yahoo | MSCI EAFE ETF | Daily | DM ex-US equity |
| `XLF` | Yahoo | Financial Select Sector SPDR | Daily | Banking sector stress |
| `XLE` | Yahoo | Energy Select Sector SPDR | Daily | Energy sector / oil equity proxy |
| `XLU` | Yahoo | Utilities Select Sector SPDR | Daily | Defensive/rate-sensitive proxy |
| `VWO` | Yahoo | Vanguard FTSE Emerging Markets | Daily | EM equity (alternate) |

---

## 10. Summary: Priority Data Series for Initial Implementation

The current `DEFAULT_SERIES` in `fred_loader.py` contains only 5 series. Below is the recommended expansion, organized by implementation priority.

### Tier 1 -- Core (implement immediately)

These are essential for the regime detector, basic expert models, and portfolio risk.

**FRED (17 series)**:
`VIXCLS`, `DGS2`, `DGS5`, `DGS10`, `DGS30`, `T10Y2Y`, `T10Y3M`, `DFF`, `DFII10`, `T5YIE`, `T10YIE`, `T5YIFR`, `BAMLH0A0HYM2`, `BAMLC0A0CM`, `DCOILWTICO`, `DCOILBRENTEU`, `DTWEXBGS`

**Yahoo (12 tickers)**:
`^VIX`, `^VIX3M`, `GC=F`, `HG=F`, `CL=F`, `EURUSD=X`, `USDJPY=X`, `SPY`, `TLT`, `HYG`, `EEM`, `BDRY`

### Tier 2 -- Enhanced (implement next)

Add richer feature set for expert models and liquidity monitoring.

**FRED (15 series)**:
`WALCL`, `WTREGEN`, `RRPONTSYD`, `NFCI`, `STLFSI4`, `ICSA`, `CCSA`, `M2SL`, `SOFR`, `NAPM`, `UMCSENT`, `DHHNGSP`, `BAMLH0A3HYC`, `BAMLH0A1HYBB`, `T10YFF`

**Yahoo (10 tickers)**:
`^MOVE`, `GBPUSD=X`, `USDMXN=X`, `USDZAR=X`, `USDCNY=X`, `SI=F`, `NG=F`, `QQQ`, `IWM`, `XLF`

### Tier 3 -- Full Coverage (implement for production)

Complete the data universe for all expert sleeves and advanced regime detection.

**FRED (remaining)**:
All remaining series listed in sections 1-7 above, plus ECB/BOJ rates.

**Yahoo (remaining)**:
All remaining FX pairs, commodity futures, sector ETFs, and agriculture futures.

---

## 11. Implementation Notes

### FRED API Rate Limits
- Free tier: 120 requests per minute
- Each series is one request
- Use the existing `CacheManager` aggressively -- most FRED series update daily or weekly
- Batch requests by fetching all series in one loop (already done in `FREDDataSource.load_macro`)

### Yahoo Finance Reliability
- `yfinance` scrapes Yahoo Finance; no API key needed
- Rate limiting is informal -- keep requests under ~2000/hour
- Some tickers (e.g., `^MOVE`, `^BDI`) may have limited or no history
- FX pairs (`=X` suffix) sometimes have gaps on weekends/holidays -- forward-fill
- Futures (`=F` suffix) roll over; historical data is continuous front-month

### Forward-Fill and Alignment
- The current `FREDDataSource.load_macro` already does `.ffill().dropna()`, which is correct
- Weekly/monthly FRED series need forward-fill to align with daily data
- All series should be aligned to a common daily business-day index before feature computation
- Be aware that `dropna()` after `ffill()` will drop leading rows where monthly data has not yet started

### Backtest Considerations
- **Point-in-time**: Monthly series (CPI, NFP, etc.) must be lagged by their publication delay to avoid look-ahead bias. A CPI print released on the 12th of month M covers month M-1.
- **Revisions**: NFP, GDP, PCE are revised multiple times. Ideal: use ALFRED (Archival FRED) vintage data. Practical: add 1-month lag buffer for monthly series.
- **Survivorship**: FRED series get discontinued (e.g., TEDRATE). Check series end dates during data loading.

### Suggested `DEFAULT_SERIES` Update

The current `DEFAULT_SERIES` dict in `fred_loader.py` should be expanded to at minimum the Tier 1 FRED series:

```python
DEFAULT_SERIES = {
    # Volatility
    "VIXCLS": "vix",
    # Rates
    "DGS2": "yield_2y",
    "DGS5": "yield_5y",
    "DGS10": "yield_10y",
    "DGS30": "yield_30y",
    "T10Y2Y": "curve_10y2y",
    "T10Y3M": "curve_10y3m",
    "DFF": "fed_funds",
    # Real rates
    "DFII10": "real_rate_10y",
    # Inflation
    "T5YIE": "breakeven_5y",
    "T10YIE": "breakeven_10y",
    "T5YIFR": "fwd_inflation_5y5y",
    # Credit
    "BAMLH0A0HYM2": "hy_oas",
    "BAMLC0A0CM": "ig_oas",
    # Commodities
    "DCOILWTICO": "oil_wti",
    "DCOILBRENTEU": "oil_brent",
    # FX
    "DTWEXBGS": "usd_broad",
}
```
