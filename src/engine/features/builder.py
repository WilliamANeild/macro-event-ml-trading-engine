from __future__ import annotations

import math
from datetime import date

import pandas as pd

from .schemas import FeatureRow


CORR_PAIRS = [
    ("SPY", "TLT"),
    ("SPY", "GLD"),
    ("SPY", "HYG"),
    ("SPY", "EEM"),
    ("SPY", "CL=F"),
    ("TLT", "GLD"),
    ("CL=F", "GLD"),
    ("SPY", "BTC-USD"),
    ("HYG", "TLT"),
]

RETURN_WINDOWS  = {"1d": 1, "5d": 5, "20d": 20, "60d": 60}

DYNAMICS_FEATURES = [
    "vix_close",
    "hy_oas",
    "curve_10y2y",
    "real_rate_10y",
    "breakeven_5y",
    "usd_broad",
    "oil_wti",
]


class FeatureBuilder:

    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        prices: pd.DataFrame,
        returns: pd.DataFrame,
        macro: pd.DataFrame,
        sleeve_map: dict[str, list[str]] | None = None,
    ) -> FeatureRow:
        values: dict[str, float] = {}

        weekly_prices  = self.weekly(prices, agg="last")
        weekly_returns = self.weekly(returns, agg="sum")
        weekly_macro   = self.weekly(macro,   agg="last")

        values.update(self.returns(returns, weekly_returns))
        values.update(self.volatility(returns))
        values.update(self.drawdown(prices))
        values.update(self.cross_asset_corr(returns))
        values.update(self.dispersion(weekly_returns, sleeve_map or {}))
        values.update(self.macro_features(weekly_macro))
        values.update(self.robust_zscores(values, returns, weekly_returns, weekly_macro))
        values.update(self.dynamics(weekly_macro))
        values.update(self.derive_expert_features(values))

        return FeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            values=values,
        )

    @staticmethod
    def from_dict(
        prices_dict: dict[str, list[float]],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        prices_df  = pd.DataFrame(prices_dict)
        returns_df = prices_df.pct_change().dropna()
        return prices_df, returns_df

    
    

    def returns(
        self,
        returns: pd.DataFrame,
        weekly_returns: pd.DataFrame,
    ) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(returns)

        for symbol in returns.columns:
            s = returns[symbol]

            # Daily window returns
            for label, window in RETURN_WINDOWS.items():
                key = f"{symbol}_ret_{label}"
                values[key] = float(s.iloc[-window:].sum()) if n >= window else 0.0

            # Weekly returns
            nw = len(weekly_returns)
            values[f"{symbol}_ret_1w"] = (
                float(weekly_returns[symbol].iloc[-1]) if nw >= 1 else 0.0
            )
            values[f"{symbol}_ret_4w"] = (
                float(weekly_returns[symbol].iloc[-4:].sum()) if nw >= 4 else 0.0
            )

            # Percentile rank of 1w return vs trailing 52 weeks
            ret_1w = values[f"{symbol}_ret_1w"]
            if nw >= 52 and not math.isnan(ret_1w):
                hist = weekly_returns[symbol].iloc[-52:].tolist()
                values[f"{symbol}_ret_1w_rank"] = sum(1 for v in hist if v <= ret_1w) / len(hist)
            else:
                values[f"{symbol}_ret_1w_rank"] = 0.0

        return values


    def volatility(self, returns: pd.DataFrame) -> dict[str, float]:
        
        values: dict[str, float] = {}
        n = len(returns)

        for symbol in returns.columns:
            s = returns[symbol]

            rvol_20d = float(s.iloc[-20:].std() * math.sqrt(252)) if n >= 20 else 0.0
            rvol_60d = float(s.iloc[-60:].std() * math.sqrt(252)) if n >= 60 else 0.0

            values[f"{symbol}_rvol_20d"] = rvol_20d
            values[f"{symbol}_rvol_60d"] = rvol_60d


            # Vol of vol — std of rolling 20d vol over last 60 days
            if n >= 80:
                rolling_vols = [
                    float(s.iloc[i - 20 : i].std() * math.sqrt(252))
                    for i in range(20, n + 1)
                ]
                values[f"{symbol}_vol_of_vol"] = float(pd.Series(rolling_vols).iloc[-60:].std())
            else:
                values[f"{symbol}_vol_of_vol"] = 0.0

        return values

    
    def drawdown(self, prices: pd.DataFrame) -> dict[str, float]:
       
        values: dict[str, float] = {}
        n = len(prices)

        for symbol in prices.columns:
            p = prices[symbol]

            if n >= 2:
                window = min(252, n)
                rolling_max = p.iloc[-window:].cummax()
                current = float(p.iloc[-1])
                peak = float(rolling_max.iloc[-1])
                dd = (current / peak) - 1.0 if peak > 1e-10 else 0.0
                values[f"{symbol}_drawdown"]  = dd

                #drawdown days
                below = (p.iloc[-window:] < rolling_max).tolist()
                days  = 0
                for b in reversed(below):
                    if b:
                        days += 1
                    else:
                        break
                values[f"{symbol}_drawdown_days"] = float(days)
            else:
                values[f"{symbol}_drawdown"] = 0.0
                values[f"{symbol}_drawdown_days"]  = 0.0

        return values

   
    def cross_asset_corr(self, returns: pd.DataFrame) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(returns)

        for a, b in CORR_PAIRS:
            missing = a not in returns.columns or b not in returns.columns

            corr_20d = 0.0
            corr_60d = 0.0

            if not missing and n >= 20:
                corr_20d = float(returns[[a, b]].iloc[-20:].corr().iloc[0, 1])
            if not missing and n >= 60:
                corr_60d = float(returns[[a, b]].iloc[-60:].corr().iloc[0, 1])

            values[f"corr_{a}_{b}_20d"]  = corr_20d
            values[f"corr_{a}_{b}_60d"]  = corr_60d
            values[f"corr_{a}_{b}_delta"] = (
                corr_20d - corr_60d
                if not any(math.isnan(v) for v in [corr_20d, corr_60d])
                else 0.0
            )

        return values


    def dispersion(
        self,
        weekly_returns: pd.DataFrame,
        sleeve_map: dict[str, list[str]],
    ) -> dict[str, float]:
       
        values: dict[str, float] = {}

        if len(weekly_returns) < 1:
            return values

        last_20d = weekly_returns.iloc[-4:]
        sleeve_means: list[float] = []

        for sleeve, symbols in sleeve_map.items():
            available = [s for s in symbols if s in weekly_returns.columns]
            if len(available) >= 2:
                rets = last_20d[available].sum().tolist()
                values[f"dispersion_{sleeve}_20d"] = self._std(rets)
                sleeve_means.append(sum(rets) / len(rets))
            else:
                values[f"dispersion_{sleeve}_20d"] = 0.0

        values["dispersion_cross_sleeve_20d"] = (
            self._std(sleeve_means) if len(sleeve_means) >= 2 else 0.0
        )

        # broad sector
        sector_syms = ["XLE", "XLF", "XLU", "QQQ", "IWM", "EEM"]
        avail = [s for s in sector_syms if s in weekly_returns.columns]
        values["dispersion_sectors"] = (
            self._std(last_20d[avail].sum().tolist()) if len(avail) >= 2 else 0.0
        )

        # commodity
        commodity_syms = ["CL=F", "GC=F", "HG=F", "NG=F", "ZW=F"]
        avail = [s for s in commodity_syms if s in weekly_returns.columns]
        values["dispersion_commodities"] = (
            self._std(last_20d[avail].sum().tolist()) if len(avail) >= 2 else 0.0
        )

        return values


    def macro_features(self, wm: pd.DataFrame) -> dict[str, float]:
        values: dict[str, float] = {}

        def last(col: str) -> float:
            return float(wm[col].iloc[-1]) if col in wm.columns and len(wm) >= 1 else 0.0

        def chg_1w(col: str) -> float:
            return float(wm[col].iloc[-1] - wm[col].iloc[-2]) if col in wm.columns and len(wm) >= 2 else 0.0

        def chg_4w(col: str) -> float:
            return float(wm[col].iloc[-1] - wm[col].iloc[-5]) if col in wm.columns and len(wm) >= 5 else 0.0

        # VIX
        values["vix_close_w"] = last("vix_close")

        # Yields
        values["yield_2y_level"]   = last("yield_2y")
        values["yield_10y_level"]  = last("yield_10y")
        values["yield_2y_chg_1w"]  = chg_1w("yield_2y")
        values["yield_10y_chg_1w"] = chg_1w("yield_10y")

        #yield curve
        c = last("curve_10y2y")
        values["curve_10y2y_level"]    = c
        values["curve_10y2y_chg_1w"]   = chg_1w("curve_10y2y")
        values["curve_10y2y_inverted"] = float(0 if math.isnan(c) else int(c < 0))
        c3m = last("curve_10y3m")
        values["curve_10y3m_level"]    = c3m
        values["curve_10y3m_inverted"] = float(0 if math.isnan(c3m) else int(c3m < 0))

        #curve butterfly: 2*5y - 2y - 10y
        y2, y5, y10 = last("yield_2y"), last("yield_5y"), last("yield_10y")
        values["curve_butterfly"] = (
            2 * y5 - y2 - y10
            if not any(math.isnan(v) for v in [y2, y5, y10]) else 0.0
        )

        #real rates and inflation
        values["real_rate_10y"] = last("real_rate_10y")
        values["real_rate_10y_chg_1w"] = chg_1w("real_rate_10y")
        values["real_rate_10y_chg_4w"]  = chg_4w("real_rate_10y")
        values["breakeven_5y"] = last("breakeven_5y")
        values["breakeven_10y"] = last("breakeven_10y")
        values["fwd_inflation_5y5y"] = last("fwd_inflation_5y5y")
        fwd = last("fwd_inflation_5y5y")
        values["fwd_inflation_5y5y_dev"] = fwd - 2.0 if not math.isnan(fwd) else 0.0
        b5, b10 = last("breakeven_5y"), last("breakeven_10y")
        values["inflation_term_structure"] = (
            b10 - b5 if not any(math.isnan(v) for v in [b5, b10]) else 0.0
        )
        values["fed_funds_level"] = last("fed_funds")

        #credit
        hy, ig = last("hy_oas"), last("ig_oas")
        values["hy_oas_level"] = hy
        values["hy_oas_chg_1w"] = chg_1w("hy_oas")
        values["ig_oas_level"] = ig
        values["hy_ig_spread"] = (
            hy - ig if not any(math.isnan(v) for v in [hy, ig]) else 0.0
        )

        #oil
        wti, brent = last("oil_wti"), last("oil_brent")
        values["oil_wti_ret_1w"] = chg_1w("oil_wti")
        values["brent_wti_spread"] = (
            brent - wti if not any(math.isnan(v) for v in [brent, wti]) else 0.0
        )
        values["brent_wti_spread_chg_1w"]  = (
            chg_1w("oil_brent") - chg_1w("oil_wti")
            if not any(math.isnan(v) for v in [chg_1w("oil_brent"), chg_1w("oil_wti")])
            else 0.0
        )

        # USD
        values["usd_broad_ret_1w"] = chg_1w("usd_broad")
        values["usd_broad_ret_4w"] = chg_4w("usd_broad")

        return values


    def robust_zscores(
        self,
        values: dict[str, float],
        returns: pd.DataFrame,
        weekly_returns: pd.DataFrame,
        weekly_macro: pd.DataFrame,
    ) -> dict[str, float]:
       
       #macro z-scores
        zscores: dict[str, float] = {}
        nw = len(weekly_macro)

        def macro_z(col: str, out_key: str) -> None:
            if col in weekly_macro.columns and nw >= 12:
                hist = weekly_macro[col].iloc[-12:].tolist()
                current = float(weekly_macro[col].iloc[-1])
                zscores[out_key] = self.robust_z(current, hist)
            else:
                zscores[out_key] = 0.0

        macro_z("vix_close", "vix_close_w_z")
        macro_z("hy_oas", "hy_oas_z")
        macro_z("curve_10y2y", "curve_10y2y_z")
        macro_z("real_rate_10y", "real_rate_10y_z")
        macro_z("breakeven_5y", "breakeven_5y_z")
        macro_z("usd_broad", "usd_broad_ret_1w_z")
        macro_z("oil_wti", "oil_wti_ret_1w_z")

        #vol and return z-scores
        n = len(returns)
        nwr = len(weekly_returns)

        for symbol in returns.columns:
            # Vol z-score
            current_rvol = values.get(f"{symbol}_rvol_60d", 0.0)
            if not math.isnan(current_rvol) and n >= 72:
                hist_vols = [
                    float(returns[symbol].iloc[i - 60 : i].std() * math.sqrt(252))
                    for i in range(20, n)
                ]
                zscores[f"{symbol}_rvol_60d_z"] = self.robust_z(
                    current_rvol, hist_vols[-12:]
                )
            else:
                zscores[f"{symbol}_rvol_60d_z"] = 0.0

            # Return z-scores
            for label in ["ret_1w", "ret_4w"]:
                current_ret = values.get(f"{symbol}_{label}", 0.0)
                if not math.isnan(current_ret) and nwr >= 52 and symbol in weekly_returns.columns:
                    hist = weekly_returns[symbol].iloc[-52:].tolist()
                    zscores[f"{symbol}_{label}_z"] = self.robust_z(current_ret, hist)
                else:
                    zscores[f"{symbol}_{label}_z"] = 0.0

        return zscores


    def dynamics(self, weekly_macro: pd.DataFrame) -> dict[str, float]:
        dynamics: dict[str, float] = {}
        wm = weekly_macro

        for feat in DYNAMICS_FEATURES:
            if feat not in wm.columns:
                dynamics[f"{feat}_wow_chg"] = float("nan")
                dynamics[f"{feat}_wow_accel"] = float("nan")
                dynamics[f"{feat}_4w_momentum"] = float("nan")
                continue

            n = len(wm)
            current = float(wm[feat].iloc[-1]) if n >= 1 else float("nan")

            # WoW change
            wow = float(wm[feat].iloc[-1] - wm[feat].iloc[-2]) if n >= 2 else float("nan")
            dynamics[f"{feat}_wow_chg"] = wow

            # Acceleration
            if n >= 3:
                prior_wow = float(wm[feat].iloc[-2] - wm[feat].iloc[-3])
                dynamics[f"{feat}_wow_accel"] = wow - prior_wow if not math.isnan(wow) else float("nan")
            else:
                dynamics[f"{feat}_wow_accel"] = float("nan")

            # 4-week momentum
            dynamics[f"{feat}_4w_momentum"] = (
                float(wm[feat].iloc[-1] - wm[feat].iloc[-5]) if n >= 5 else float("nan")
            )

        return dynamics

    def weekly(
        self,
        df: pd.DataFrame,
        agg: str = "last",
    ) -> pd.DataFrame:
        if df.empty:
            return df
        if agg == "sum":
            return df.resample("W-FRI").sum().dropna(how="all")
        return df.resample("W-FRI").last().dropna(how="all")

    def robust_z(self, current: float, history: list[float]) -> float:
        #z-score: (current - median) / MAD."""
        if math.isnan(current) or len(history) < 4:
            return 0.0
        median = self._median(history)
        mad    = self._median([abs(v - median) for v in history])
        if mad < 1e-10:
            return 0.0
        return (current - median) / mad

    # ------------------------------------------------------------------
    # Expert feature bridge
    # ------------------------------------------------------------------
    def derive_expert_features(self, values: dict[str, float]) -> dict[str, float]:
        """Map builder-computed features to the keys each expert expects.

        For features that genuinely cannot be derived from market data
        (they come from the event pipeline), we default to 0.0 or 0.5 as
        appropriate and leave a comment.
        """
        ef: dict[str, float] = {}

        # --- helpers ---------------------------------------------------
        def _get(key: str, default: float = 0.0) -> float:
            v = values.get(key, default)
            return default if math.isnan(v) else v

        def _normalize_vol(raw: float, floor: float = 0.0, cap: float = 1.0) -> float:
            """Rough 0-1 normalization for annualized realized vol.

            Typical SPY rvol is 0.10–0.40; we map [0, 0.60] -> [0, 1].
            """
            return max(floor, min(cap, raw / 0.60))

        # ---------------------------------------------------------------
        # MarketPricingExpert
        # ---------------------------------------------------------------
        ef["realized_volatility"] = _normalize_vol(_get("SPY_rvol_20d"))
        ef["vol_of_vol"] = min(1.0, _get("SPY_vol_of_vol") / 0.15)  # 0.15 annualized std-of-vol is extreme
        # Cross-asset correlation spike: use max absolute delta across key pairs
        corr_deltas = [
            abs(_get(f"corr_{a}_{b}_delta"))
            for a, b in CORR_PAIRS
        ]
        ef["cross_asset_correlation_spike"] = min(1.0, max(corr_deltas) / 0.30) if corr_deltas else 0.0
        ef["dispersion_commodities"] = min(1.0, _get("dispersion_commodities") / 0.10)
        # dispersion_single_names: use sector dispersion as proxy
        ef["dispersion_single_names"] = min(1.0, _get("dispersion_sectors") / 0.10)
        # already_priced_indicator: VIX elevated + drawdown recovering → already priced
        vix_z = _get("vix_close_w_z")
        ef["already_priced_indicator"] = max(0.0, min(1.0, vix_z / 3.0)) if vix_z > 0 else 0.0
        # market_depth: proxy via HY OAS z-score (wider spread → lower depth)
        hy_z = _get("hy_oas_z")
        ef["market_depth"] = max(0.0, min(1.0, 1.0 - hy_z / 4.0))

        # ---------------------------------------------------------------
        # CryptoRegimeExpert
        # ---------------------------------------------------------------
        ef["crypto_volatility"] = _normalize_vol(_get("BTC-USD_rvol_20d"), cap=1.0)
        # crypto-equity correlation: use the builder's 20d corr of SPY vs BTC-USD
        ef["crypto_equity_correlation"] = max(0.0, min(1.0,
            (_get("corr_SPY_BTC-USD_20d", 0.5) + 1.0) / 2.0  # map [-1,1] -> [0,1]
        ))
        # usd_strength: map weekly USD return to 0-1 (positive = strong)
        usd_ret = _get("usd_broad_ret_1w")
        ef["usd_strength"] = max(0.0, min(1.0, 0.5 + usd_ret * 50))  # ±1% → 0/1
        # liquidity_stress: proxy from HY OAS level z-score
        ef["liquidity_stress"] = max(0.0, min(1.0, _get("hy_oas_z") / 3.0))
        # risk_on_signal: equity + commodity momentum
        ef["risk_on_signal"] = max(0.0, min(1.0,
            0.5
            + _get("SPY_ret_1w") * 20   # ~2.5% weekly move → 1.0
            + _get("CL=F_ret_1w", 0.0) * 10
        ))
        # risk_off_signal: bond + gold demand
        ef["risk_off_signal"] = max(0.0, min(1.0,
            0.5
            + _get("TLT_ret_1w", 0.0) * 20
            + _get("GLD_ret_1w", 0.0) * 10
        ))

        # ---------------------------------------------------------------
        # RatesPolicyExpert
        # ---------------------------------------------------------------
        ef["yield_change"] = _get("yield_10y_chg_1w")
        ef["curve_slope_change"] = _get("curve_10y2y_chg_1w")
        # inflation_proxy_drift: use breakeven 5y wow change
        ef["inflation_proxy_drift"] = _get("breakeven_5y_wow_chg", 0.0)
        # cb_language_intensity — event pipeline feature, not derivable from market data
        ef["cb_language_intensity"] = 0.5  # event pipeline
        # cb_language_shift — event pipeline feature
        ef["cb_language_shift"] = 0.0  # event pipeline
        # hawkish_shock_flag — event pipeline feature
        ef["hawkish_shock_flag"] = 0.0  # event pipeline
        # easing_shock_flag — event pipeline feature
        ef["easing_shock_flag"] = 0.0  # event pipeline

        # ---------------------------------------------------------------
        # ShippingChokePointExpert
        # ---------------------------------------------------------------
        # chokepoint_intensity — event pipeline feature (shipping incident data)
        ef["chokepoint_intensity"] = 0.0  # event pipeline
        # incident_novelty — event pipeline feature
        ef["incident_novelty"] = 0.0  # event pipeline
        # incident_count — event pipeline feature
        ef["incident_count"] = 0.0  # event pipeline
        # port_stress — event pipeline feature
        ef["port_stress"] = 0.0  # event pipeline
        # energy_move: oil WTI weekly return magnitude, normalized
        ef["energy_move"] = min(1.0, abs(_get("oil_wti_ret_1w")) * 20)
        # freight_proxy_move: not directly available; default to 0
        ef["freight_proxy_move"] = 0.0  # event pipeline / freight index
        # correlation_change: use CL=F-GLD correlation delta as shipping proxy
        ef["correlation_change"] = min(1.0, abs(_get("corr_CL=F_GLD_delta")) / 0.25)

        # ---------------------------------------------------------------
        # ConflictEscalationExpert
        # ---------------------------------------------------------------
        # escalation_intensity — event pipeline feature (NLP / incident scoring)
        ef["escalation_intensity"] = 0.0  # event pipeline
        # escalation_acceleration — event pipeline feature
        ef["escalation_acceleration"] = 0.0  # event pipeline
        # sanctions_mentions — event pipeline feature (news count)
        ef["sanctions_mentions"] = 0.0  # event pipeline
        # sanctions_direction — event pipeline feature; 0.5 = neutral default
        ef["sanctions_direction"] = 0.5  # event pipeline
        # spillover_flag — event pipeline feature
        ef["spillover_flag"] = 0.0  # event pipeline
        # region_volatility: proxy from EEM realized vol
        ef["region_volatility"] = _normalize_vol(_get("EEM_rvol_20d", 0.0))

        return ef

    @staticmethod
    def _std(values: list[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        return math.sqrt(variance)

    @staticmethod
    def _median(values: list[float]) -> float:
        s = sorted(values)
        n = len(s)
        mid = n // 2
        return (s[mid - 1] + s[mid]) / 2 if n % 2 == 0 else s[mid]