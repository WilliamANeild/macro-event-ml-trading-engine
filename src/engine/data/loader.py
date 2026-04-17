from __future__ import annotations

import pandas as pd

from .interfaces import BaseDataSource


class MockDataSource(BaseDataSource):
    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        prices: dict[str, list[float]] = {}

        for symbol in symbols:
            prices[symbol] = [100.0, 101.0, 102.5, 101.5, 103.0]

        return prices

    def load_returns(
        self,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        prices = pd.DataFrame(self.load_prices(symbols))
        return prices.pct_change().dropna()