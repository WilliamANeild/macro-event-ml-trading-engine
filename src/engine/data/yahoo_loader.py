from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from .cache import CacheManager
from .interfaces import BaseDataSource


class YahooDataSource(BaseDataSource):
    def __init__(self, cache: CacheManager | None = None) -> None:
        self.cache = cache or CacheManager()

    def load_prices(
        self,
        symbols: list[str],
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        end = end or str(date.today())
        frames = {}
        for sym in symbols:
            df = self._fetch(sym, start, end)
            frames[sym] = df["Close"]
        return pd.DataFrame(frames).ffill()

    def load_returns(
        self,
        symbols: list[str],
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        prices = self.load_prices(symbols, start, end)
        return prices.pct_change().dropna()

    def _fetch(
        self,
        symbol: str,
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        end = end or str(date.today())
        end_week = (
            pd.Timestamp(end)
            .to_period("W")
            .start_time.strftime("%Y-%m-%d")
        )
        cache_key = f"yahoo_{symbol}_{start}_{end_week}"
        if self.cache.has(cache_key):
            return self.cache.load(cache_key)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        df = df.ffill()
        self.cache.save(cache_key, df)
        return df