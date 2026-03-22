from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from .cache import CacheManager
from .interfaces import BaseDataSource


class YahooDataSource(BaseDataSource):
    def __init__(self, cache: CacheManager | None = None) -> None:
        self.cache = cache or CacheManager()

    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        result: dict[str, list[float]] = {}
        for sym in symbols:
            df = self._fetch(sym)
            result[sym] = df["Close"].tolist()
        return result

    def load_returns(
        self,
        symbols: list[str],
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        end = end or str(date.today())
        frames = {}
        for sym in symbols:
            df = self._fetch(sym, start, end)
            frames[sym] = df["Close"].pct_change().dropna()
        returns = pd.DataFrame(frames).dropna()
        return returns

    def _fetch(
        self,
        symbol: str,
        start: str = "2020-01-01",
        end: str | None = None,
    ) -> pd.DataFrame:
        end = end or str(date.today())
        cache_key = f"yahoo_{symbol}_{start}_{end}"
        if self.cache.has(cache_key):
            return self.cache.load(cache_key)
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        df = df.ffill()
        self.cache.save(cache_key, df)
        return df
