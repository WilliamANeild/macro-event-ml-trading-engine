from __future__ import annotations

from .schemas import Instrument


def get_universe() -> list[Instrument]:
    return [
        Instrument(
            symbol="XLE",
            name="Energy Select Sector SPDR Fund",
            asset_class="equity_etf",
            theme="energy",
            subtheme="broad_energy",
            region="us",
            tags=["energy", "etf"],
        ),
        Instrument(
            symbol="ITA",
            name="iShares U.S. Aerospace & Defense ETF",
            asset_class="equity_etf",
            theme="defense",
            subtheme="broad_defense",
            region="us",
            tags=["defense", "etf"],
        ),
        Instrument(
            symbol="SEA",
            name="U.S. Global Sea to Sky Cargo ETF",
            asset_class="equity_etf",
            theme="shipping",
            subtheme="broad_shipping",
            region="global",
            tags=["shipping", "etf"],
        ),
    ]