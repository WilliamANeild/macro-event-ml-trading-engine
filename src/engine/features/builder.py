from __future__ import annotations

from datetime import date

from .schemas import FeatureRow


class FeatureBuilder:
    def build(
        self,
        as_of_date: date,
        theme: str,
        subtheme: str,
        prices: dict[str, list[float]],
    ) -> FeatureRow:
        values: dict[str, float] = {}

        for symbol, series in prices.items():
            if len(series) >= 2:
                values[f"{symbol}_return_1"] = (series[-1] / series[-2]) - 1.0

        return FeatureRow(
            as_of_date=as_of_date,
            theme=theme,
            subtheme=subtheme,
            values=values,
        )