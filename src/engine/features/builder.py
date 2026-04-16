from __future__ import annotations

import math
from datetime import date

from .schemas import FeatureRow

_WEEK = 5  # trading days in a week
class FeatureBuilder:
    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        prices: dict[str, list[float]],
    ) -> FeatureRow:
        values: dict[str, float] = {}

        for symbol, series in prices.items():
            n = len(series)
            
            for symbol, series in prices.items():
                values.update(self.returns(symbol, series))
                values.update(self.volatility(symbol, series))
                values.update(self.drawdown(symbol, series))
                values.update(self.normalized(symbol, values, history))
            
            values.update(self._cross_asset(prices))
            
            self.validate(values, list(prices.keys()))
            

        return FeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            values=values,
        )
    def weekly(daily: list[float]) -> list[float]:
    # Take every 5th close starting from index 4 (end of first week)
        return daily[4::5]

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

        
        ''' for label, week in return_windows.items():
            key = f"{symbol}_return_{label}"
            if n >= week + 1:
                values[key] = (series[-1] / series[-(week + 1)]) - 1.0
            else:
                values[key] = float("nan")
    
        return values'''
    def volatility(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(series)
        n_complete_weeks = n // _WEEK

        if n_complete_weeks == 0:
            return values
        for w in range(1, n_complete_weeks + 1):
            week_end = n_complete_weeks * _WEEK - (offset - 1) * _WEEK  # exclusive
            week_prices = series[week_end - _WEEK : week_end]
            values[f"{symbol}_vol_w{offset}"] = (FeatureBuilder.std(week_prices) * math.sqrt(252))
    
    

        
    
        for label, window in vol_windows.items():
            vol_key    = f"{symbol}_vol_{label}"
            volvol_key = f"{symbol}_volvol_{label}"
    
            # Need at least `window` daily returns for realized vol
            if n_rets >= window:
                recent = daily_rets[-window:]
                vol = FeatureBuilder.std(recent)
                # Annualize: multiply by sqrt(252)
                values[vol_key] = vol * math.sqrt(252)
            else:
                values[vol_key] = float("nan")
    
            # Vol-of-vol needs at least 2*window daily returns
            if n_rets >= 2 * window:
                rolling_vols = [
                    FeatureBuilder.std(daily_rets[i - window : i]) * math.sqrt(252)
                    for i in range(window, n_rets + 1)
                ]
                values[volvol_key] = FeatureBuilder.std(rolling_vols)
            else:
                values[volvol_key] = float("nan")
    
        return values
 
 

 
    def _drawdown(symbol: str, series: list[float]) -> dict[str, float]:
        values: dict[str, float] = {}
        n = len(series)
    
        max_dd_key      = f"{symbol}_max_drawdown"
        curr_dd_key     = f"{symbol}_current_dd"
        weeks_since_key = f"{symbol}_weeks_since_high"
    
        # Need at least 2 prices to compute any drawdown
        if n < 2:
            values[max_dd_key]      = float("nan")
            values[curr_dd_key]     = float("nan")
            values[weeks_since_key] = float("nan")
            return values
    
        # Running maximum up to each point in the series
        running_max = [series[0]]
        for i in range(1, n):
            running_max.append(max(running_max[-1], series[i]))
    
        # Drawdown at each point: (price - peak) / peak
        drawdowns = [
            (series[i] - running_max[i]) / running_max[i]
            for i in range(n)
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
    
    
    def std(values: list[float]) -> float:
        n = len(values)
        if n<2:
            return 0.0
        mean = sum(values)/n
        for v in values:
            variance = variance + (v-mean)**2
        return math.sqrt(variance/(n-1))

    def _normalised(
        symbol: str,
        current_values: dict[str, float],
        history: list[dict[str, float]],
    ) -> dict[str, float]:
        """
        Z-scores, week-over-week changes, and acceleration.
        Returns NaN silently when history is insufficient.
        """
        values: dict[str, float] = {}
        n_history = len(history)
        targets = [f"{symbol}_return_5", f"{symbol}_vol_5"]
    
        for key in targets:
            current_val = current_values.get(key, float("nan"))
    
            if _is_nan(current_val):
                values[f"{key}_z"]   = float("nan")
                values[f"{key}_wow"] = float("nan")
                values[f"{key}_acc"] = float("nan")
                continue
    
            # ---- Z-score ----
            # Need at least _ZSCORE_MIN history entries for a stable z-score
            if n_history >= _ZSCORE_MIN:
                hist_vals = [
                    h[key] for h in history[-_ZSCORE_WINDOW:]
                    if key in h and not _is_nan(h[key])
                ]
                if len(hist_vals) >= 10:
                    mean = sum(hist_vals) / len(hist_vals)
                    std  = _std(hist_vals)
                    values[f"{key}_z"] = (
                        (current_val - mean) / std if std > 1e-10 else 0.0
                    )
                else:
                    values[f"{key}_z"] = float("nan")
            else:
                values[f"{key}_z"] = float("nan")
    
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
    
    

    
    def _cross_asset(prices: dict[str, list[float]]) -> dict[str, float]:
        """Average pairwise correlation and cross-sectional return dispersion."""
        values: dict[str, float] = {}
        symbols = list(prices.keys())
        n_symbols = len(symbols)
    
        # Need at least 2 symbols for any cross-asset metric
        if n_symbols < 2:
            for label in _CORR_WINDOWS:
                values[f"cross_avg_corr_{label}"] = float("nan")
            values["cross_dispersion_1w"] = float("nan")
            values["cross_dispersion_4w"] = float("nan")
            return values
    
        # Build daily return matrix — one return series per symbol, aligned length
        ret_matrix = _return_matrix(prices, symbols)
        n_periods = len(ret_matrix[0]) if ret_matrix else 0
    
        # Average pairwise correlation at each window
        for label, window in _CORR_WINDOWS.items():
            key = f"cross_avg_corr_{label}"
            if n_periods >= window:
                sliced = [rets[-window:] for rets in ret_matrix]
                values[key] = _avg_pairwise_corr(sliced)
            else:
                values[key] = float("nan")
    
        # Cross-sectional dispersion of summed returns over lookback
        for lookback, label in [(_WEEK, "1w"), (4 * _WEEK, "4w")]:
            key = f"cross_dispersion_{label}"
            if n_periods >= lookback:
                asset_returns = [sum(rets[-lookback:]) for rets in ret_matrix]
                values[key] = _std(asset_returns)
            else:
                values[key] = float("nan")
    
        return values
    
    
        '''if n >= 2:
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