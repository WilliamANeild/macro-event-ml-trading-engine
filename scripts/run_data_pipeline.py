"""
Run this script to pull all live data and populate the local cache.
Usage: python scripts/run_data_pipeline.py
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine.universe.registry import get_symbols
from src.engine.data.yahoo_loader import YahooDataSource
from src.engine.data.fred_loader import FREDDataSource
from src.engine.data.cache import CacheManager

START_DATE = "2020-01-01"
BATCH_SIZE = 50


def run():
    cache = CacheManager(cache_dir="data/cache")
    yahoo = YahooDataSource(cache=cache)
    fred = FREDDataSource(cache=cache)

    all_symbols = get_symbols()
    tradable = [s for s in all_symbols if not s.startswith("^")]

    print(f"Pulling prices for {len(tradable)} instruments...")

    failed = []
    for i in range(0, len(tradable), BATCH_SIZE):
        batch = tradable[i : i + BATCH_SIZE]
        print(f"  Batch {i // BATCH_SIZE + 1}: {batch[0]} ... {batch[-1]}")
        for sym in batch:
            try:
                yahoo._fetch(sym, start=START_DATE)
                print(f"    OK {sym}")
            except Exception as e:
                print(f"    FAILED {sym}: {e}")
                failed.append(sym)

    print(f"\nPulling macro series from FRED...")
    try:
        macro = fred.load_macro(start=START_DATE)
        print(f"  OK FRED: {list(macro.columns)}")
    except Exception as e:
        print(f"  FAILED FRED: {e}")
        print("  Make sure FRED_API_KEY is set and retry")

    print(f"\nDone.")
    if failed:
        print(f"Failed tickers ({len(failed)}): {failed}")
    else:
        print("All tickers pulled successfully.")


if __name__ == "__main__":
    run()