from __future__ import annotations

import numpy as np

from .base import BaseExpert
from .schemas import ExpertContext, ExpertFamily, ExpertPrediction, LocalizationMetadata, LocalizationType


class ShippingChokePointExpert(BaseExpert):
    """
    Chokepoint-specific shipping disruption detection.
    Signals: chokepoint intensity, incident keywords, port cluster stress, market confirmation.
    """
    
    expert_name = "shipping_chokepoint"
    expert_family = ExpertFamily.SHIPPING_CHOKEPOINT
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """
        Predict shipping disruption at a specific chokepoint or port.
        
        Key features:
        - chokepoint_intensity: Activity deviation from normal (0-1)
        - incident_novelty: Ratio of novel incident clusters vs baseline
        - incident_count: Recent incidents (attack, boarding, piracy, etc.)
        - port_stress: Container throughput or vessel queue stress (0-1)
        - energy_move: Energy market confirmation of disruption (0-1)
        - freight_proxy_move: Freight index move confirmation (0-1)
        - correlation_change: Shipping correlation spike (0-1)
        """
        
        features = context.feature_row
        event_features = context.event_features
        
        # Default to PORT_CLUSTER localization
        localization_data = event_features.get("localization", {})
        if localization_data:
            localization = LocalizationMetadata.from_dict(localization_data)
        else:
            localization = LocalizationMetadata(
                location_type=LocalizationType.PORT_CLUSTER,
                location_value=context.subtheme,
            )
        
        # Shipping-specific features
        chokepoint_intensity = features.get("chokepoint_intensity", 0.0)
        incident_novelty = features.get("incident_novelty", 0.0)
        incident_count = features.get("incident_count", 0.0)
        port_stress = features.get("port_stress", 0.0)
        energy_move = features.get("energy_move", 0.0)
        freight_proxy_move = features.get("freight_proxy_move", 0.0)
        correlation_change = features.get("correlation_change", 0.0)
        
        # Use model if fitted, otherwise apply heuristic
        if self._fitted and self.model is not None:
            try:
                feature_vector = np.array([[
                    chokepoint_intensity,
                    incident_novelty,
                    incident_count,
                    port_stress,
                    energy_move,
                    freight_proxy_move,
                    correlation_change,
                ]])
                proba = self.predict_proba(feature_vector)
                if proba is not None:
                    probability_active = float(proba[0, 1])
                    values = self.predict_values(feature_vector)
                    severity = float(np.clip(values[0] if values is not None else chokepoint_intensity, 0, 1))
                else:
                    probability_active, severity = self._heuristic_predict(
                        chokepoint_intensity, incident_novelty, incident_count, port_stress
                    )
            except Exception:
                probability_active, severity = self._heuristic_predict(
                    chokepoint_intensity, incident_novelty, incident_count, port_stress
                )
        else:
            probability_active, severity = self._heuristic_predict(
                chokepoint_intensity, incident_novelty, incident_count, port_stress
            )
        
        # Confidence boosted by market confirmation (energy and freight moves)
        market_confirmation = max(energy_move, freight_proxy_move)
        confidence = min(
            1.0,
            0.3 + 0.4 * (chokepoint_intensity + incident_novelty) / 2.0
            + 0.3 * market_confirmation,
        )
        
        # Direction: long on shipping stress (higher costs, tighter capacity)
        direction = "long" if probability_active > 0.5 else "neutral"
        
        # Tags based on incident characteristics
        tags = ["shipping"]
        if incident_count > 0:
            tags.append("incidents_detected")
        if incident_novelty > 0.6:
            tags.append("novel_incident_pattern")
        if port_stress > 0.6:
            tags.append("port_congestion")
        if energy_move > 0.6 and freight_proxy_move > 0.6:
            tags.append("multi_asset_confirmation")
        
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
                "chokepoint_intensity": chokepoint_intensity,
                "incident_novelty": incident_novelty,
                "incident_count": incident_count,
                "port_stress": port_stress,
                "market_confirmation": market_confirmation,
            },
            model_version=self.model_version,
        )

    def _heuristic_predict(
        self,
        chokepoint_intensity: float,
        incident_novelty: float,
        incident_count: float,
        port_stress: float,
    ) -> tuple[float, float]:
        """Fallback heuristic when model not fitted."""
        # Incident novelty + intensity = signal
        probability_active = min(
            1.0,
            0.4 * chokepoint_intensity
            + 0.3 * incident_novelty
            + 0.2 * min(1.0, incident_count / 5.0),  # Normalize to 0-1
            + 0.1 * port_stress,
        )
        
        severity = min(
            1.0,
            chokepoint_intensity + 0.3 * incident_novelty + 0.2 * port_stress,
        )
        
        return probability_active, severity
