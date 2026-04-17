from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseDataSource(ABC):
    @abstractmethod
    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        raise NotImplementedError

    @abstractmethod
    def load_returns(
        self,
        symbols: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError