from __future__ import annotations

import os
from datetime import date

import pandas as pd

from .cache import CacheManager

DEFAULT_SERIES = {
    "VIXCLS": "VIX",
    "DGS10": "10Y_yield",
    "DCOILWTICO": "oil_price",
    "DTWEXBGS": "usd_index",
    "T5YIE": "breakeven_inflation",
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
