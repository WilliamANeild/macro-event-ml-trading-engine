from __future__ import annotations

import numpy as np

from .base import BaseExpert
from .schemas import ExpertContext, ExpertFamily, ExpertPrediction, LocalizationMetadata, LocalizationType


class RatesPolicyExpert(BaseExpert):
    """
    Rates, policy, and monetary regime detection.
    Signals: yield/curve changes, central bank language intensity, regime classification.
    """
    
    expert_name = "rates_policy"
    expert_family = ExpertFamily.RATES_POLICY
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """
        Predict rates/policy shock and regime classification.
        
        Key features:
        - yield_change: Change in 10Y yield (normalized, e.g., +0.02 = 2bp)
        - curve_slope_change: Change in yield curve slope (10Y - 2Y)
        - inflation_proxy_drift: Change in inflation expectations or breakeven rate
        - cb_language_intensity: Central bank hawkishness intensity (0-1)
        - cb_language_shift: Change in CB tone from prior week
        - hawkish_shock_flag: Detected hawkish surprise (0-1)
        - easing_shock_flag: Detected easing surprise (0-1)
        """
        
        features = context.feature_row
        event_features = context.event_features
        
        # Localization by country if specified
        localization_data = event_features.get("localization", {})
        if localization_data:
            localization = LocalizationMetadata.from_dict(localization_data)
        else:
            localization = LocalizationMetadata(
                location_type=LocalizationType.COUNTRY,
                location_value=context.subtheme,
            )
        
        # Rates and policy features
        yield_change = features.get("yield_change", 0.0)
        curve_slope_change = features.get("curve_slope_change", 0.0)
        inflation_proxy_drift = features.get("inflation_proxy_drift", 0.0)
        cb_language_intensity = features.get("cb_language_intensity", 0.5)
        cb_language_shift = features.get("cb_language_shift", 0.0)
        hawkish_shock_flag = features.get("hawkish_shock_flag", 0.0)
        easing_shock_flag = features.get("easing_shock_flag", 0.0)
        
        # Use model if fitted
        if self._fitted and self.model is not None:
            try:
                feature_vector = np.array([[
                    yield_change,
                    curve_slope_change,
                    inflation_proxy_drift,
                    cb_language_intensity,
                    cb_language_shift,
                    hawkish_shock_flag,
                    easing_shock_flag,
                ]])
                proba = self.predict_proba(feature_vector)
                if proba is not None:
                    probability_active = float(proba[0, 1])
                    values = self.predict_values(feature_vector)
                    severity = float(np.clip(values[0] if values is not None else abs(yield_change), 0, 1))
                else:
                    probability_active, severity, regime = self._heuristic_predict(
                        yield_change, cb_language_intensity, hawkish_shock_flag, easing_shock_flag
                    )
            except Exception:
                probability_active, severity, regime = self._heuristic_predict(
                    yield_change, cb_language_intensity, hawkish_shock_flag, easing_shock_flag
                )
        else:
            probability_active, severity, regime = self._heuristic_predict(
                yield_change, cb_language_intensity, hawkish_shock_flag, easing_shock_flag
            )
        
        # Confidence from CB language shift consistency and shock flags
        confidence = min(
            1.0,
            0.3 + 0.3 * abs(cb_language_shift)
            + 0.2 * (hawkish_shock_flag + easing_shock_flag)
            + 0.2 * abs(yield_change) * 10,  # Higher yield moves = more confident
        )
        
        # Direction based on regime and yield move
        if probability_active > 0.6:
            # Shock active: hawkish = short (risk-off), easing = long (risk-on)
            direction = "short" if hawkish_shock_flag > easing_shock_flag else "long"
        else:
            direction = "neutral"
        
        # Tags
        tags = ["rates", "policy"]
        if hawkish_shock_flag > 0.5:
            tags.append("hawkish_shock")
        if easing_shock_flag > 0.5:
            tags.append("easing_shock")
        if abs(curve_slope_change) > 0.01:
            tags.append("curve_inversion_risk" if curve_slope_change < 0 else "curve_steepening")
        
        return ExpertPrediction(
            expert_name=self.expert_name,
            as_of_date=context.as_of_date,
            theme=context.theme,
            subtheme=context.subtheme,
            probability_active=probability_active,
            severity_score=severity,
            confidence_score=confidence,
            direction=direction,
            tags=tags,
            localization=localization,
            metadata={
                "yield_change": yield_change,
                "curve_slope_change": curve_slope_change,
                "inflation_proxy_drift": inflation_proxy_drift,
                "cb_language_intensity": cb_language_intensity,
                "regime": regime,
            },
            model_version=self.model_version,
        )

    def _heuristic_predict(
        self,
        yield_change: float,
        cb_language_intensity: float,
        hawkish_shock_flag: float,
        easing_shock_flag: float,
    ) -> tuple[float, float, str]:
        """Fallback heuristic when model not fitted."""
        # Probability active if shock or yield move
        probability_active = min(
            1.0,
            0.3 * (hawkish_shock_flag + easing_shock_flag)
            + 0.4 * min(1.0, abs(yield_change) * 50)  # Normalize: 2bp = 0.1
            + 0.3 * cb_language_intensity,
        )
        
        # Severity from yield move
        severity = min(1.0, abs(yield_change) * 50)
        
        # Regime classification
        if hawkish_shock_flag > easing_shock_flag and cb_language_intensity > 0.6:
            regime = "hawkish_shock"
        elif easing_shock_flag > hawkish_shock_flag and cb_language_intensity < 0.4:
            regime = "easing_shock"
        else:
            regime = "stable"
        
        return probability_active, severity, regime
