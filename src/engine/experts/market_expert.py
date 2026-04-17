from __future__ import annotations

import numpy as np

from .base import BaseExpert
from .schemas import ExpertContext, ExpertFamily, ExpertPrediction, LocalizationMetadata, LocalizationType


class MarketPricingExpert(BaseExpert):
    """
    Market complacency and pricing signals.
    Detects extremes: realized vol spikes, vol-of-vol, correlation changes, dispersion.
    """
    
    expert_name = "market_pricing"
    expert_family = ExpertFamily.MARKET_PRICING
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """
        Predict market repricing risk and complacency.
        
        Key features:
        - realized_volatility: Recent realized vol (normalized 0-1)
        - vol_of_vol: Volatility of volatility (spikes = regime change risk)
        - cross_asset_correlation_spike: Unusual correlation between commodities/equities
        - dispersion_commodities: Dispersion among commodity returns (0-1)
        - dispersion_single_names: Dispersion within defense sector names (0-1)
        - already_priced_indicator: Market has baked in shock (0-1)
        - market_depth: Liquidity stress indicator (0-1)
        """
        
        features = context.feature_row
        event_features = context.event_features
        
        # Localization to commodity or theme-wide
        localization_data = event_features.get("localization", {})
        if localization_data:
            localization = LocalizationMetadata.from_dict(localization_data)
        else:
            localization = LocalizationMetadata(
                location_type=LocalizationType.COMMODITY,
                location_value=context.subtheme,
            )
        
        # Market pricing features
        realized_volatility = features.get("realized_volatility", 0.0)
        vol_of_vol = features.get("vol_of_vol", 0.0)
        cross_asset_correlation_spike = features.get("cross_asset_correlation_spike", 0.0)
        dispersion_commodities = features.get("dispersion_commodities", 0.0)
        dispersion_single_names = features.get("dispersion_single_names", 0.0)
        already_priced_indicator = features.get("already_priced_indicator", 0.0)
        market_depth = features.get("market_depth", 0.5)
        
        # Use model if fitted
        if self._fitted and self.model is not None:
            try:
                feature_vector = np.array([[
                    realized_volatility,
                    vol_of_vol,
                    cross_asset_correlation_spike,
                    dispersion_commodities,
                    dispersion_single_names,
                    already_priced_indicator,
                    market_depth,
                ]])
                proba = self.predict_proba(feature_vector)
                if proba is not None:
                    probability_active = float(proba[0, 1])
                    values = self.predict_values(feature_vector)
                    severity = float(np.clip(values[0] if values is not None else realized_volatility, 0, 1))
                else:
                    probability_active, severity = self._heuristic_predict(
                        realized_volatility, vol_of_vol, already_priced_indicator, features
                    )
            except Exception:
                probability_active, severity = self._heuristic_predict(
                    realized_volatility, vol_of_vol, already_priced_indicator
                )
        else:
            probability_active, severity = self._heuristic_predict(
                realized_volatility, vol_of_vol, already_priced_indicator, features
            )
        
        # Confidence: high vol consistency + correlation coherence + VIX fallback
        vix = features.get("vix_close_w", 0.0)
        vix_conf = max(0.0, min(1.0, (vix - 14.0) / 25.0)) if vix > 0 else 0.0
        rvol_or_vix = max(realized_volatility, vix_conf)
        confidence = min(
            1.0,
            0.2 + 0.3 * rvol_or_vix
            + 0.3 * max(vol_of_vol, vix_conf * 0.5)
            + 0.2 * cross_asset_correlation_spike,
        )
        
        # Direction: depends on whether shocked is already priced
        # If already priced, reduce aggressiveness (neutral or hedge)
        # If not priced but vol high, signal mean reversion or tail hedge demand
        if already_priced_indicator > 0.6:
            direction = "neutral"  # Already baked in, shift to ETF/hedge expression
        elif probability_active > 0.6:
            direction = "short"  # Complacency correction risk = short
        else:
            direction = "neutral"
        
        # Tags
        tags = ["market_pricing"]
        if realized_volatility > 0.7:
            tags.append("high_realized_vol")
        if vol_of_vol > 0.6:
            tags.append("vol_regime_change")
        if cross_asset_correlation_spike > 0.6:
            tags.append("correlation_breakdown")
        if dispersion_commodities > dispersion_single_names:
            tags.append("commodity_dispersion_wide")
        if already_priced_indicator > 0.6:
            tags.append("already_priced")
        if market_depth < 0.4:
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
                "realized_volatility": realized_volatility,
                "vol_of_vol": vol_of_vol,
                "cross_asset_correlation_spike": cross_asset_correlation_spike,
                "dispersion_commodities": dispersion_commodities,
                "dispersion_single_names": dispersion_single_names,
                "already_priced_indicator": already_priced_indicator,
                "market_depth": market_depth,
            },
            model_version=self.model_version,
        )

    def _heuristic_predict(
        self,
        realized_volatility: float,
        vol_of_vol: float,
        already_priced_indicator: float,
        features: dict,
    ) -> tuple[float, float]:
        """Fallback heuristic when model not fitted."""
        # If realized_volatility is 0 (SPY not in universe), fall back to VIX
        rvol = realized_volatility
        vov = vol_of_vol
        if rvol < 0.01:
            vix = features.get("vix_close_w", 0.0)
            # Map VIX to 0-1: VIX 12=0.1, 20=0.33, 35=0.67, 50+=1.0
            rvol = max(0.0, min(1.0, (vix - 10.0) / 40.0)) if vix > 0 else 0.0
            # Also scan for any available symbol rvol
            for key, val in features.items():
                if key.endswith("_rvol_20d") and isinstance(val, (int, float)) and val > 0:
                    candidate = min(1.0, val / 0.60)
                    rvol = max(rvol, candidate)
                    break
            # Estimate vol_of_vol from VIX level deviation
            if vix > 0:
                vov = max(0.0, min(1.0, (vix - 18.0) / 20.0))

        # Vol spikes without regime change = repricing risk
        repricing_risk = min(
            1.0,
            0.5 * rvol + 0.4 * vov + 0.1 * (1.0 - already_priced_indicator),
        )

        probability_active = repricing_risk * (1.0 - already_priced_indicator * 0.5)
        severity = rvol

        return probability_active, severity
