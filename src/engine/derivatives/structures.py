from __future__ import annotations


class StructureSelector:
    def select_structure(
        self, direction: str, confidence: float, regime: str
    ) -> str:
        if direction == "long" and confidence >= 0.7:
            return "call_spread"
        if direction == "long" and regime == "crisis":
            return "collar"
        if direction == "short":
            return "put_spread"
        return "futures_scaling"

    def compute_notionals(
        self,
        structure: str,
        weights: dict[str, float],
        budget: float,
    ) -> dict[str, float]:
        if not weights:
            return {}
        total_abs = sum(abs(v) for v in weights.values()) or 1.0
        notionals: dict[str, float] = {}
        for sym, w in weights.items():
            proportion = abs(w) / total_abs
            notionals[sym] = round(proportion * budget, 6)
        return notionals
