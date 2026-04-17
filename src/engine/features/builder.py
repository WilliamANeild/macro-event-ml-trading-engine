'''from __future__ import annotations

import math
from pandas import pd
from datetime import date

from .schemas import FeatureRow



_WEEK = 5  # trading days in a week
class FeatureBuilder:
    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        prices: pd.DataFrame,        # daily closes, index=date, columns=symbols
        returns: pd.DataFrame,       # daily returns, index=date, columns=symbols
        macro: pd.DataFrame,         # daily macro, index=date, columns=series names
) -> FeatureRow:
        values: dict[str, float] = {}
        n_days = min(len(s) for s in prices.values())
        n_weeks = n_days // _WEEK

        rows: dict[int, dict[str, float]] = {}  # week_index → feature dict

        for w in range(n_weeks):
            week_values: dict[str, float] = {}
            sliced = {sym: series[: (w + 1) * _WEEK] for sym, series in prices.items()}

            for symbol, series in sliced.items():
                self.returns(returns)
                self.volatility(returns)
                self.drawdown(prices)
                self.cross_asset_corr(returns)
                self.dispersion(returns, registry)
                self.macro_features(macro)
                self.dynamics(values)

            week_values.update(self.cross_asset(sliced))
            rows[w] = week_values

        # Most recent week is the canonical FeatureRow returned to callers
        latest = rows.get(n_weeks - 1, {})
        return FeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            values=latest,
        )
    def weekly(daily: list[float]) -> list[float]:
    # Take every 5th close starting from index 4 (end of first week)
        return daily[4::5]
    
    @staticmethod
    def returns(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}

        weekly_prices = FeatureBuilder.weekly(series)
        n = len(weekly_prices)

        if n < 2:
            return values

        for label, window in _RETURN_WINDOWS.items():
            if n >= window + 1:
                values[f"{symbol}_return_{label}"] = (
                    weekly_prices[-1] / weekly_prices[-(window + 1)]
                ) - 1.0
            else:
                values[f"{symbol}_return_{label}"] = float("nan")

        return values
        

    def returns(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}

        weekly_prices = FeatureBuilder.weekly(series)
        n = len(weekly_prices)

        if n < 2:
            return values

        # w1 = most recent week's return, w2 = prior week, etc.
        for week in range(1, n):
            values[f"{symbol}_return_w{week}"] = (
                weekly_prices[n - week] / weekly_prices[n - week - 1]
            ) - 1.0

        return values

        
         for label, week in return_windows.items():
            key = f"{symbol}_return_{label}"
            if n >= week + 1:
                values[key] = (series[-1] / series[-(week + 1)]) - 1.0
            else:
                values[key] = float("nan")
    
        return values
    def volatility(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(series)
        n_weeks = n // _WEEK

        if n_weeks == 0:
            return values
        for week in range(1, n_weeks + 1):
            week_end = n_weeks * _WEEK - (week - 1) * _WEEK  # exclusive
            week_prices = series[week_end - _WEEK : week_end]
            values[f"{symbol}_vol_w{week}"] = (FeatureBuilder.std(week_prices) * math.sqrt(252))

            vol_4w = series[week - 3*_WEEK : week: _WEEK]
            values[f"{symbol}_volvol_w{week}"] = FeatureBuilder.std(vol_4w)
    
        return values
    
    #vol of vol over 1 month or 4 weeks
    def vol_of_vol(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}
        vol = FeatureBuilder.volatility(series) 
        #n_weeks = n // _WEEK

        if len(vol) < 4:
            return values
        
        else:
            for week in range(4, len(vol) + 1):
                vol_4w = vol[week - 3 *_WEEK : week: _WEEK]
                values[f"{symbol}_volvol_w{week}"] = self.std(vol_4w)
        
            return values

 
 

 
    def drawdown(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(series)
        
        n_weeks = n // _WEEK

        if n_weeks == 0:
            return values
        for week in range(1, n_weeks + 1):
            week_end = n_weeks * _WEEK - (week - 1) * _WEEK  # exclusive
            week_prices = series[week_end - _WEEK : week_end]
            running_max = 0
            running_min = series[0]
            for i in week_prices:
                running_max = (max(running_max, i))
                running_min = (min(running_min, i))
            # drawdown (price - peak) / peak
                values[f"{symbol}_drawdown_w{week}"] = [(running_max - running_min) / running_max]
        return values

        
    
        # Need at least 2 prices to compute any drawdown
        if n < 2:
            values[max_dd_key]      = float("nan")
            values[curr_dd_key]     = float("nan")
            values[weeks_since_key] = float("nan")
            return values
    
        # Running maximum up to each point in the series
        running_max = 0
        running_min = 0
        for i in range(1, n):
            running_max = (max(running_max, series[i]))
            running_min = (min(running_min, series[i]))
        # Drawdown at each point: (price - peak) / peak
        drawdowns = [
            (running_max - running_min) / running_max
        ]
    
        values[max_dd_key]  = min(drawdowns)
        values[curr_dd_key] = drawdowns[-1]
    
        # Weeks since peak — scan backwards for last time price matched running max
        peak = running_max[-1]
        weeks_since = 0
        for i in range(n - 1, -1, -1):
            if series[i] >= peak:
                weeks_since = (n - 1 - i) // _WEEK
                break
    
        values[weeks_since_key] = float(weeks_since)
        return values
        
    
    
    def std(series: list[float]) -> float:
        n = len(series)
        variance = 0
        if n<2:
            return 0.0
        mean = sum(series)/n
        for v in series:
            variance = variance + (v-mean)**2
        return math.sqrt(variance/(n-1))

    #@staticmethod
    def normalize(symbol: str, series: list[float]) -> dict[str, float]:
        #z-scores for returns and vol
        values: dict[str, float] = {}
        n = len(series)
        n_weeks = n // _WEEK

        if n_weeks < 2:
            return values

        weekly_returns: list[float] = []
        weekly_vols: list[float] = []

        for w in range(n_weeks):
            start = w * _WEEK
            end = start + _WEEK
            week_slice = series[start:end]
            prev_close = series[start - 1] if start > 0 else series[0]
            weekly_returns.append((week_slice[-1] / prev_close) - 1.0)
            weekly_vols.append(FeatureBuilder.std(week_slice) * math.sqrt(252))

        ret_mean = sum(weekly_returns) / n_weeks
        ret_std = FeatureBuilder.std(weekly_returns)
        vol_mean = sum(weekly_vols) / n_weeks
        vol_std = FeatureBuilder.std(weekly_vols)

        for k, (r, v) in enumerate(zip(weekly_returns, weekly_vols), start=1):
            values[f"{symbol}_return_z_w{k}"] = ((r - ret_mean) / ret_std if ret_std > 1e-10 else 0.0)
            values[f"{symbol}_vol_z_w{k}"] = ((v - vol_mean) / vol_std if vol_std > 1e-10 else 0.0)

        #week_over_week change
        for i in range(1, n_weeks + 1):
            idx = n_weeks - i  # w1 = most recent week

            if idx > 0:
                ret_wow = weekly_returns[idx] - weekly_returns[idx - 1]
                vol_wow = weekly_vols[idx] - weekly_vols[idx - 1]
            else:
                ret_wow = 0.0
                vol_wow = 0.0

            values[f"{symbol}_return_wow_w{i}"] = ret_wow
            values[f"{symbol}_vol_wow_w{i}"] = vol_wow

            #acceleration: second derivative of returns and vol
            if idx > 1:
                prior_ret_wow = weekly_returns[idx - 1] - weekly_returns[idx - 2]
                prior_vol_wow = weekly_vols[idx - 1] - weekly_vols[idx - 2]
                values[f"{symbol}_return_acc_w{i}"] = ret_wow - prior_ret_wow
                values[f"{symbol}_vol_acc_w{i}"] = vol_wow - prior_vol_wow
            else:
                values[f"{symbol}_return_acc_w{i}"] = 0.0
                values[f"{symbol}_vol_acc_w{i}"] = 0.0
    

        return values
    #@staticmethod
    def wow_and_acceleration(symbol: str, series: list[float]) -> dict[str, float]:
   
        Compute week-over-week change and acceleration (change-in-change) for
        weekly returns and realised vol directly from the price series.
        No history parameter required.

        Keys produced:
            {symbol}_return_wow_w{k}  — return WoW change at week k (w1 = most recent)
            {symbol}_return_acc_w{k}  — return acceleration at week k
            {symbol}_vol_wow_w{k}     — vol WoW change at week k
            {symbol}_vol_acc_w{k}     — vol acceleration at week k
 
        values: dict[str, float] = {}
        n = len(series)
        n_weeks = n // _WEEK

        if n_weeks < 2:
            return values

        weekly_returns: list[float] = []
        weekly_vols: list[float] = []

        for w in range(n_weeks):
            start = w * _WEEK
            end = start + _WEEK
            week_slice = series[start:end]
            prev_close = series[start - 1] if start > 0 else series[0]
            weekly_returns.append((week_slice[-1] / prev_close) - 1.0)
            weekly_vols.append(FeatureBuilder.std(week_slice) * math.sqrt(252))

        for i in range(1, n_weeks + 1):
            idx = n_weeks - i  # w1 = most recent week

            # week-over-week change: needs a prior week
            if idx > 0:
                ret_wow = weekly_returns[idx] - weekly_returns[idx - 1]
                vol_wow = weekly_vols[idx] - weekly_vols[idx - 1]
            else:
                ret_wow = float("nan")
                vol_wow = float("nan")

            values[f"{symbol}_return_wow_w{k}"] = ret_wow
            values[f"{symbol}_vol_wow_w{k}"] = vol_wow

            # acceleration: change in the wow change; needs two prior weeks
            if idx > 1:
                prior_ret_wow = weekly_returns[idx - 1] - weekly_returns[idx - 2]
                prior_vol_wow = weekly_vols[idx - 1] - weekly_vols[idx - 2]
                values[f"{symbol}_return_acc_w{k}"] = ret_wow - prior_ret_wow
                values[f"{symbol}_vol_acc_w{k}"] = vol_wow - prior_vol_wow
            else:
                values[f"{symbol}_return_acc_w{k}"] = float("nan")
                values[f"{symbol}_vol_acc_w{k}"] = float("nan")

        return values

    def wk_over_wk (symbol: str, series: dict[str, float]):

            # ---- Week-over-week change ----
            # Need at least 1 history entry
            if n_history >= 1:
                prior = history[-1].get(key, float("nan"))
                values[f"{key}_wow"] = (
                    current_val - prior if not _is_nan(prior) else float("nan")
                )
            else:
                values[f"{key}_wow"] = float("nan")
    
            # ---- Acceleration (change in the change) ----
            # Need at least 2 history entries
            if n_history >= 2:
                prior       = history[-1].get(key, float("nan"))
                prior_prior = history[-2].get(key, float("nan"))
                if not _is_nan(prior) and not _is_nan(prior_prior):
                    prior_wow   = prior - prior_prior
                    current_wow = values.get(f"{key}_wow", float("nan"))
                    values[f"{key}_acc"] = (
                        current_wow - prior_wow
                        if not _is_nan(current_wow) else float("nan")
                    )
                else:
                    values[f"{key}_acc"] = float("nan")
            else:
                values[f"{key}_acc"] = float("nan")
    
        return values
    
    

    
    def cross_asset(prices: dict[str, list[float]]) -> dict[str, float]:
        # Average pairwise correlation and cross-sectional dispersion metrics.
        # Keys are only emitted when there is sufficient data — no nan padding.
        values: dict[str, float] = {}
        symbols = list(prices.keys())

        if len(symbols) < 2:
            return values

        # Align all series to the shortest length, then build daily return matrix
        min_len = min(len(prices[s]) for s in symbols)
        ret_matrix: list[list[float]] = []
        for s in symbols:
            series = prices[s][-min_len:]
            ret_matrix.append([(series[i] / series[i - 1]) - 1.0 for i in range(1, len(series))])

        n_periods = len(ret_matrix[0])

        def _pearson(x: list[float], y: list[float]) -> float:
            n = len(x)
            if n < 2:
                return 0.0
            mx = sum(x) / n
            my = sum(y) / n
            cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
            sx = math.sqrt(sum((v - mx) ** 2 for v in x))
            sy = math.sqrt(sum((v - my) ** 2 for v in y))
            if sx < 1e-12 or sy < 1e-12:
                return 0.0
            return cov / (sx * sy)

        def _avg_pairwise_corr(matrix: list[list[float]]) -> float:
            total, pairs = 0.0, 0
            for i in range(len(matrix)):
                for j in range(i + 1, len(matrix)):
                    total += _pearson(matrix[i], matrix[j])
                    pairs += 1
            return total / pairs if pairs else 0.0

        # Average pairwise correlation over 1w / 4w / 13w windows
        for label, window in [("1w", _WEEK), ("4w", 4 * _WEEK), ("13w", 13 * _WEEK)]:
            if n_periods >= window:
                sliced = [rets[-window:] for rets in ret_matrix]
                values[f"cross_avg_corr_{label}"] = _avg_pairwise_corr(sliced)

        # Cross-sectional return dispersion: std of cumulative returns across assets
        for label, window in [("1w", _WEEK), ("4w", 4 * _WEEK)]:
            if n_periods >= window:
                asset_rets = [sum(rets[-window:]) for rets in ret_matrix]
                values[f"cross_dispersion_{label}"] = FeatureBuilder.std(asset_rets)

        # Cross-sectional vol dispersion: std of realised vol across assets
        for label, window in [("1w", _WEEK), ("4w", 4 * _WEEK)]:
            if n_periods >= window:
                asset_vols = [
                    FeatureBuilder.std(rets[-window:]) * math.sqrt(252)
                    for rets in ret_matrix
                ]
                values[f"cross_vol_dispersion_{label}"] = FeatureBuilder.std(asset_vols)

        # Return spread: max minus min cumulative return over 1w / 4w (regime width)
        for label, window in [("1w", _WEEK), ("4w", 4 * _WEEK)]:
            if n_periods >= window:
                asset_rets = [sum(rets[-window:]) for rets in ret_matrix]
                values[f"cross_return_spread_{label}"] = max(asset_rets) - min(asset_rets)

        return values
        
    
    
        values[f"{symbol}_return_1"] = (series[-1] / series[-2]) - 1.0

            if n >= _WEEK + 1:
                values[f"{symbol}_return_5"] = (series[-1] / series[-(_WEEK + 1)]) - 1.0
                daily_rets = [
                    (series[i] / series[i - 1]) - 1.0
                    for i in range(n - _WEEK, n)
                ]
                mean = sum(daily_rets) / _WEEK
                variance = sum((r - mean) ** 2 for r in daily_rets) / (_WEEK - 1)
                values[f"{symbol}_vol_5"] = math.sqrt(variance)
                '''
        
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