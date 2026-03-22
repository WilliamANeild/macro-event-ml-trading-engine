from __future__ import annotations


class ExposureAuditor:
    def audit(
        self, matrix: dict[str, dict[str, float]], top_n: int = 3
    ) -> dict[str, list[tuple[str, float]]]:
        result: dict[str, list[tuple[str, float]]] = {}
        for theme, weights in matrix.items():
            sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            result[theme] = sorted_weights[:top_n]
        return result

    def flag_anomalies(self, matrix: dict[str, dict[str, float]]) -> list[str]:
        flags: list[str] = []
        for theme, weights in matrix.items():
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                flags.append(f"Theme '{theme}' weights sum to {total:.4f}, expected ~1.0")
            max_w = max(weights.values()) if weights else 0
            if max_w > 0.95:
                flags.append(f"Theme '{theme}' has concentration > 95%")
            if all(v < 0.01 for v in weights.values()):
                flags.append(f"Theme '{theme}' has no meaningful exposures")
        return flags

    def generate_report(self, matrix: dict[str, dict[str, float]]) -> str:
        lines = ["Exposure Matrix Report", "=" * 40]
        top = self.audit(matrix)
        anomalies = self.flag_anomalies(matrix)
        for theme, top_syms in top.items():
            lines.append(f"\nTheme: {theme}")
            for sym, w in top_syms:
                lines.append(f"  {sym}: {w:.4f}")
        if anomalies:
            lines.append(f"\nAnomalies ({len(anomalies)}):")
            for a in anomalies:
                lines.append(f"  - {a}")
        return "\n".join(lines)
