from __future__ import annotations

from .interfaces import BaseDataSource


class MockDataSource(BaseDataSource):
    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        prices: dict[str, list[float]] = {}

        for symbol in symbols:
            prices[symbol] = [100.0, 101.0, 102.5, 101.5, 103.0]

        return prices