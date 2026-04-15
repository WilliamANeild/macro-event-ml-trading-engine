from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .schemas import ExpertContext, ExpertPrediction, ExpertFamily


class BaseExpert(ABC):
    """Base class for all experts. Each expert is localized to a specific domain."""
    
    expert_name: str = "base_expert"
    expert_family: ExpertFamily = ExpertFamily.MARKET_PRICING
    model_version: str = "v0.1"
    
    def __init__(self) -> None:
        self.model: RandomForestClassifier | RandomForestRegressor | None = None
        self._fitted = False

    @abstractmethod
    def predict(self, context: ExpertContext) -> ExpertPrediction:
        """Core prediction method. Must return standardized ExpertPrediction."""
        raise NotImplementedError

    def fit(
        self,
        X: pd.DataFrame | np.ndarray,
        y: np.ndarray,
        task: str = "classification",
        **kwargs: Any,
    ) -> None:
        """
        Fit the expert's random forest model.
        
        Args:
            X: Feature matrix
            y: Target labels
            task: "classification" or "regression"
            **kwargs: Additional parameters for RandomForest (n_estimators, max_depth, etc.)
        """
        if task == "classification":
            self.model = RandomForestClassifier(
                n_estimators=kwargs.get("n_estimators", 100),
                max_depth=kwargs.get("max_depth", 15),
                min_samples_split=kwargs.get("min_samples_split", 5),
                min_samples_leaf=kwargs.get("min_samples_leaf", 2),
                random_state=kwargs.get("random_state", 42),
                n_jobs=-1,
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=kwargs.get("n_estimators", 100),
                max_depth=kwargs.get("max_depth", 15),
                min_samples_split=kwargs.get("min_samples_split", 5),
                min_samples_leaf=kwargs.get("min_samples_leaf", 2),
                random_state=kwargs.get("random_state", 42),
                n_jobs=-1,
            )
        self.model.fit(X, y)
        self._fitted = True

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray | None:
        """
        Get probability predictions from the model.
        
        Returns:
            Probability array or None if model not fitted or is regression.
        """
        if not self._fitted or self.model is None:
            return None
        if isinstance(self.model, RandomForestClassifier):
            return self.model.predict_proba(X)
        return None

    def predict_values(self, X: pd.DataFrame | np.ndarray) -> np.ndarray | None:
        """Get point predictions from the model."""
        if not self._fitted or self.model is None:
            return None
        return self.model.predict(X)

    def feature_importance(self) -> dict[str, float]:
        """
        Get per-feature importances from the trained model.
        
        Returns:
            Dictionary mapping feature indices/names to importance values (0-1).
            Empty dict if model not fitted or doesn't support feature importance.
        """
        if not self._fitted or self.model is None:
            return {}
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            # Return normalized feature importances with feature_N names
            # This enables auditing of which specific features drove predictions
            return {
                f"feature_{i}": float(importance)
                for i, importance in enumerate(importances)
            }
        return {}
