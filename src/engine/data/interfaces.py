from __future__ import annotations

from abc import ABC, abstractmethod


class BaseDataSource(ABC):
    @abstractmethod
    def load_prices(self, symbols: list[str]) -> dict[str, list[float]]:
        raise NotImplementedError