from __future__ import annotations

import os
from datetime import date

import pandas as pd

from .cache import CacheManager

DEFAULT_SERIES = {
    "VIXCLS": "vix_close",
    "DGS2": "yield_2y",
    "DGS5": "yield_5y",
    "DGS10": "yield_10y",
    "DCOILWTICO": "oil_wti",
    "DTWEXBGS": "usd_broad",
    "T5YIE": "breakeven_5y",
    "T10YIE": "breakeven_10y",
    "T10Y2Y": "curve_10y2y",
    "T10Y3M": "curve_10y3m",
    "DFF": "fed_funds",
    "DFII10": "real_rate_10y",
    "T5YIFR": "fwd_inflation_5y5y",
    "BAMLH0A0HYM2": "hy_oas",
    "BAMLC0A0CM": "ig_oas",
    "DCOILBRENTEU": "oil_brent",
}


class FREDDataSource:
    def __init__(self, api_key: str | None = None, cache: CacheManager | None = None) -> None:
        self.api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self.cache = cache or CacheManager()

    def load_macro(
        self,
        series_ids: list[str] | None = None,
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        from fredapi import Fred

        end = end or str(date.today())
        series_ids = series_ids or list(DEFAULT_SERIES.keys())
        cache_key = f"fred_{'_'.join(series_ids)}_{start}_{end}"
        if self.cache.has(cache_key):
            return self.cache.load(cache_key)

        if not self.api_key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY env var or pass api_key."
            )
        fred = Fred(api_key=self.api_key)
        frames: dict[str, pd.Series] = {}
        for sid in series_ids:
            col_name = DEFAULT_SERIES.get(sid, sid)
            series = fred.get_series(sid, observation_start=start, observation_end=end)
            frames[col_name] = series
        df = pd.DataFrame(frames).ffill().dropna()
        self.cache.save(cache_key, df)
        return df
