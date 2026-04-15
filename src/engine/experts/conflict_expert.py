from __future__ import annotations

import numpy as np

from .base import BaseExpert
from .schemas import ExpertContext, ExpertFamily, ExpertPrediction, LocalizationMetadata, LocalizationType


class ConflictEscalationExpert(BaseExpert):
    """
    Region-specific conflict escalation detection.
    Monitors: escalation intensity/acceleration, sanctions language, spillover flags.
    """
    
    expert_name = "conflict_escalation"
    expert_family = ExpertFamily.CONFLICT_ESCALATION
    model_version = "v0.1"

    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """
        Predict conflict escalation probability for a region.
        
        Key features:
        - escalation_intensity: Recent change in conflict severity (0-1)
        - sanctions_mentions: Count of sanctions-related event mentions
        - sanctions_direction: "tightening" (1) vs "loosening" (0)
        - spillover_flag: Conflict + energy corridor references (0-1)
        - region_volatility: Standard deviation of regional indicators
        """
        
        # Extract features from context
        features = context.feature_row
        event_features = context.event_features
        
        # Get localization from event features or default
        localization_data = event_features.get("localization", {})
        if localization_data:
            localization = LocalizationMetadata.from_dict(localization_data)
        else:
            localization = LocalizationMetadata(
                location_type=LocalizationType.REGION,
                location_value=context.subtheme,
            )
        
        # Core escalation indicators
        escalation_intensity = features.get("escalation_intensity", 0.0)
        escalation_acceleration = features.get("escalation_acceleration", 0.0)
        sanctions_mentions = features.get("sanctions_mentions", 0.0)
        sanctions_direction = features.get("sanctions_direction", 0.5)  # 1.0 = tightening
        spillover_flag = features.get("spillover_flag", 0.0)
        region_volatility = features.get("region_volatility", 0.0)
        
        # Use model if fitted, otherwise apply heuristic
        if self._fitted and self.model is not None:
            try:
                feature_vector = np.array([[
                    escalation_intensity,
                    escalation_acceleration,
                    sanctions_mentions,
                    sanctions_direction,
                    spillover_flag,
                    region_volatility,
                ]])
                proba = self.predict_proba(feature_vector)
                if proba is not None:
                    probability_active = float(proba[0, 1])
                    # Model output for severity
                    values = self.predict_values(feature_vector)
                    severity = float(np.clip(values[0] if values is not None else escalation_intensity, 0, 1))
                else:
                    probability_active, severity = self._heuristic_predict(
                        escalation_intensity, escalation_acceleration, sanctions_direction, spillover_flag
                    )
            except Exception:
                probability_active, severity = self._heuristic_predict(
                    escalation_intensity, escalation_acceleration, sanctions_direction, spillover_flag
                )
        else:
            probability_active, severity = self._heuristic_predict(
                escalation_intensity, escalation_acceleration, sanctions_direction, spillover_flag
            )
        
        # Confidence depends on escalation acceleration (trending) and spillover confirmation
        confidence = min(
            1.0,
            0.3
            + 0.4 * abs(escalation_acceleration)  # Trending = higher confidence
            + 0.3 * spillover_flag,  # Multi-indicator confirmation = higher confidence
        )
        
        # Direction: long on escalation
        direction = "long" if probability_active > 0.5 else "neutral"
        
        # Tags
        tags = ["conflict"]
        if sanctions_mentions > 0:
            tags.append("sanctions")
        if sanctions_direction > 0.6:
            tags.append("sanctions_tightening")
        elif sanctions_direction < 0.4:
            tags.append("sanctions_loosening")
        if spillover_flag > 0.5:
            tags.append("spillover_risk")
        
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
                "escalation_intensity": escalation_intensity,
                "escalation_acceleration": escalation_acceleration,
                "sanctions_direction": sanctions_direction,
                "spillover_flag": spillover_flag,
            },
            model_version=self.model_version,
        )

    def _heuristic_predict(
        self,
        escalation_intensity: float,
        escalation_acceleration: float,
        sanctions_direction: float,
        spillover_flag: float,
    ) -> tuple[float, float]:
        """Fallback heuristic when model not fitted."""
        # Weighted combination of signals
        probability_active = min(
            1.0,
            0.4 * escalation_intensity
            + 0.3 * max(0.0, escalation_acceleration)  # Only positive acceleration counts
            + 0.2 * (1.0 - sanctions_direction) * 0.5,  # Sanctions context
        )
        
        severity = min(
            1.0,
            escalation_intensity
            + 0.2 * spillover_flag
            + 0.1 * max(0.0, escalation_acceleration),
        )
        
        return probability_active, severity
