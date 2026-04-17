"""Tests for data loading infrastructure (cache, mock source, synthetic generator)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.engine.data.cache import CacheManager
from src.engine.data.loader import MockDataSource
from src.engine.data.synthetic import SyntheticConfig, SyntheticDataGenerator


# ---------------------------------------------------------------------------
# CacheManager
# ---------------------------------------------------------------------------


class TestCacheManager:
    def test_has_returns_false_when_empty(self, tmp_path):
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        assert cm.has("nonexistent") is False

    def test_save_and_load_roundtrip(self, tmp_path):
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        cm.save("test_key", df)
        assert cm.has("test_key") is True
        loaded = cm.load("test_key")
        pd.testing.assert_frame_equal(df, loaded)

    def test_clear_removes_cached_files(self, tmp_path):
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        df = pd.DataFrame({"x": [1]})
        cm.save("key1", df)
        cm.save("key2", df)
        assert cm.has("key1") and cm.has("key2")
        cm.clear()
        assert cm.has("key1") is False
        assert cm.has("key2") is False

    def test_creates_cache_directory(self, tmp_path):
        cache_dir = tmp_path / "deep" / "nested" / "cache"
        assert not cache_dir.exists()
        CacheManager(cache_dir=str(cache_dir))
        assert cache_dir.exists()

    def test_different_keys_are_independent(self, tmp_path):
        cm = CacheManager(cache_dir=str(tmp_path / "cache"))
        df1 = pd.DataFrame({"v": [10]})
        df2 = pd.DataFrame({"v": [20]})
        cm.save("alpha", df1)
        cm.save("beta", df2)
        pd.testing.assert_frame_equal(cm.load("alpha"), df1)
        pd.testing.assert_frame_equal(cm.load("beta"), df2)


# ---------------------------------------------------------------------------
# MockDataSource
# ---------------------------------------------------------------------------


class TestMockDataSource:
    def test_load_prices_returns_dict(self):
        src = MockDataSource()
        result = src.load_prices(["AAPL", "GOOG"])
        assert isinstance(result, dict)

    def test_load_prices_contains_requested_symbols(self):
        src = MockDataSource()
        symbols = ["SPY", "QQQ", "IWM"]
        result = src.load_prices(symbols)
        assert set(result.keys()) == set(symbols)

    def test_load_prices_values_are_float_lists(self):
        src = MockDataSource()
        result = src.load_prices(["XLE"])
        prices = result["XLE"]
        assert isinstance(prices, list)
        assert all(isinstance(p, float) for p in prices)
        assert len(prices) > 0

    def test_load_prices_empty_symbols(self):
        src = MockDataSource()
        result = src.load_prices([])
        assert result == {}


# ---------------------------------------------------------------------------
# SyntheticDataGenerator
# ---------------------------------------------------------------------------


class TestSyntheticDataGenerator:
    @pytest.fixture()
    def gen(self):
        cfg = SyntheticConfig(symbols=["A", "B"], n_days=100, seed=7)
        return SyntheticDataGenerator(config=cfg)

    def test_load_prices_returns_all_symbols(self, gen):
        prices = gen.load_prices()
        assert set(prices.keys()) == {"A", "B"}

    def test_load_prices_length_matches_n_days(self, gen):
        prices = gen.load_prices()
        for sym, vals in prices.items():
            assert len(vals) == 100

    def test_prices_are_positive(self, gen):
        prices = gen.load_prices()
        for vals in prices.values():
            assert all(v > 0 for v in vals)

    def test_get_returns_shape(self, gen):
        returns = gen.get_returns()
        assert isinstance(returns, pd.DataFrame)
        assert returns.shape == (100, 2)
        assert list(returns.columns) == ["A", "B"]

    def test_returns_are_reasonable(self, gen):
        returns = gen.get_returns()
        # Daily returns should mostly be within -20% to 20%
        assert (returns.abs() < 0.5).all().all()

    def test_deterministic_with_same_seed(self):
        cfg = SyntheticConfig(symbols=["X"], n_days=200, seed=99)
        g1 = SyntheticDataGenerator(config=cfg)
        g2 = SyntheticDataGenerator(config=SyntheticConfig(symbols=["X"], n_days=200, seed=99))
        p1 = g1.load_prices()
        p2 = g2.load_prices()
        assert p1["X"] == p2["X"]

    def test_event_manifest_populated(self, gen):
        gen.load_prices()
        assert len(gen.event_manifest) > 0
        shock = gen.event_manifest[0]
        assert shock.symbol in ("A", "B")

    def test_get_dates_length(self, gen):
        dates = gen.get_dates()
        assert len(dates) == 100

    def test_caching_returns_same_object(self, gen):
        p1 = gen.load_prices()
        p2 = gen.load_prices()
        assert p1 is p2


# ---------------------------------------------------------------------------
# Yahoo / FRED — instantiation only (no network)
# ---------------------------------------------------------------------------


class TestLoaderInstantiation:
    def test_yahoo_data_source_can_be_created(self, tmp_path):
        from src.engine.data.yahoo_loader import YahooDataSource

        src = YahooDataSource(cache=CacheManager(cache_dir=str(tmp_path / "yc")))
        assert src is not None

    def test_fred_data_source_can_be_created(self, tmp_path):
        from src.engine.data.fred_loader import FREDDataSource

        src = FREDDataSource(api_key="fake", cache=CacheManager(cache_dir=str(tmp_path / "fc")))
        assert src is not None
