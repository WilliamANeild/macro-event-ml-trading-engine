from __future__ import annotations

import numpy as np

from .base import BaseExpert
from .schemas import ExpertContext, ExpertFamily, ExpertPrediction, LocalizationMetadata, LocalizationType


class CryptoRegimeExpert(BaseExpert):
    """
    Crypto market regime detection and behavior classification.
    Determines: crypto as risk-on vs stress hedge.
    """
    
    expert_name = "crypto_regime"
    expert_family = ExpertFamily.CRYPTO_REGIME
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """
        Predict crypto regime and correlation structure.
        
        Key features:
        - crypto_volatility: BTC/ETH realized vol (normalized 0-1)
        - crypto_equity_correlation: Recent correlation to equity index
        - usd_strength: USD index move (1 = very strong, 0 = weak)
        - liquidity_stress: Money market stress (0-1)
        - risk_on_signal: Equity/commodity momentum (0-1)
        - risk_off_signal: Bond/gold demand (0-1)
        - crypto_behaves_as: Detected regime ("risk_on", "stress_hedge", "neutral")
        """
        
        features = context.feature_row
        event_features = context.event_features
        
        # Localization: crypto is global
        localization_data = event_features.get("localization", {})
        if localization_data:
            localization = LocalizationMetadata.from_dict(localization_data)
        else:
            localization = LocalizationMetadata(
                location_type=LocalizationType.COMMODITY,
                location_value="crypto",
            )
        
        # Crypto features
        crypto_volatility = features.get("crypto_volatility", 0.0)
        crypto_equity_correlation = features.get("crypto_equity_correlation", 0.5)
        usd_strength = features.get("usd_strength", 0.5)
        liquidity_stress = features.get("liquidity_stress", 0.0)
        risk_on_signal = features.get("risk_on_signal", 0.5)
        risk_off_signal = features.get("risk_off_signal", 0.5)
        
        # Default regime before branching (model path may not set it)
        regime = "neutral"

        # Use model if fitted
        if self._fitted and self.model is not None:
            try:
                feature_vector = np.array([[
                    crypto_volatility,
                    crypto_equity_correlation,
                    usd_strength,
                    liquidity_stress,
                    risk_on_signal,
                    risk_off_signal,
                ]])
                proba = self.predict_proba(feature_vector)
                if proba is not None:
                    probability_active = float(proba[0, 1])
                    values = self.predict_values(feature_vector)
                    severity = float(np.clip(values[0] if values is not None else crypto_volatility, 0, 1))
                else:
                    probability_active, severity, regime = self._heuristic_predict(
                        crypto_volatility, crypto_equity_correlation, risk_on_signal, risk_off_signal
                    )
            except Exception:
                probability_active, severity, regime = self._heuristic_predict(
                    crypto_volatility, crypto_equity_correlation, risk_on_signal, risk_off_signal
                )
        else:
            probability_active, severity, regime = self._heuristic_predict(
                crypto_volatility, crypto_equity_correlation, risk_on_signal, risk_off_signal
            )
        
        # Confidence increases with regime consistency
        confidence = min(
            1.0,
            0.3
            + 0.4 * (0.5 + abs(crypto_equity_correlation - 0.5))  # Extreme correlation = confident
            + 0.3 * max(risk_on_signal, risk_off_signal),  # Clear risk signal
        )
        
        # Direction based on regime
        if regime == "risk_on":
            direction = "long"
        elif regime == "stress_hedge":
            direction = "short"  # Crypto as hedge means broader markets are under stress
        else:
            direction = "neutral"
        
        # Tags
        tags = ["crypto"]
        if regime == "risk_on":
            tags.append("risk_on_behavior")
        elif regime == "stress_hedge":
            tags.append("stress_hedge_behavior")
        else:
            tags.append("neutral_regime")
        
        if crypto_volatility > 0.7:
            tags.append("elevated_vol")
        if usd_strength > 0.7:
            tags.append("usd_strong")
        if liquidity_stress > 0.6:
            tags.append("liquidity_stress")
        
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
                "crypto_volatility": crypto_volatility,
                "crypto_equity_correlation": crypto_equity_correlation,
                "usd_strength": usd_strength,
                "liquidity_stress": liquidity_stress,
                "regime": regime,
            },
            model_version=self.model_version,
        )

    def _heuristic_predict(
        self,
        crypto_volatility: float,
        crypto_equity_correlation: float,
        risk_on_signal: float,
        risk_off_signal: float,
    ) -> tuple[float, float, str]:
        """Fallback heuristic when model not fitted."""
        
        # Determine regime: high equity corr + risk-on = risk-on behavior
        # Low/negative equity corr + risk-off = stress hedge
        if crypto_equity_correlation > 0.6 and risk_on_signal > 0.6:
            regime = "risk_on"
            probability_active = min(1.0, 0.6 + 0.2 * crypto_volatility)
        elif crypto_equity_correlation < 0.3 and risk_off_signal > 0.6:
            regime = "stress_hedge"
            probability_active = min(1.0, 0.5 + 0.2 * crypto_volatility)
        else:
            regime = "neutral"
            probability_active = 0.3 + 0.2 * crypto_volatility
        
        severity = crypto_volatility
        
        return probability_active, severity, regime
