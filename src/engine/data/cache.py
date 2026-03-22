from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd


class CacheManager:
    def __init__(self, cache_dir: str = "data/cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, name: str) -> Path:
        safe = hashlib.md5(name.encode()).hexdigest()
        return self.cache_dir / f"{safe}.parquet"

    def has(self, name: str) -> bool:
        return self._key(name).exists()

    def load(self, name: str) -> pd.DataFrame:
        return pd.read_parquet(self._key(name))

    def save(self, name: str, df: pd.DataFrame) -> None:
        df.to_parquet(self._key(name))

    def clear(self) -> None:
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
