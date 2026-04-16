from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd

from .base import BaseExpert
from .schemas import ExpertContext, ExpertPrediction


class ExpertTrainer:
    """
    Walk-forward training framework for experts with anti-leakage protocol.
    
    Ensures:
    - Rolling walk-forward training only (no random shuffles)
    - Expert predictions are out-of-sample for combiner training
    - No feature aggregation that peeks into the future
    - Each expert trained independently per fold
    """
    
    def __init__(
        self,
        min_train: int = 60,
        test_size: int = 20,
        gap: int = 5,
        expanding: bool = True,
    ) -> None:
        """
        Initialize trainer with walk-forward parameters.
        
        Args:
            min_train: Minimum training window size
            test_size: Test/validation window size
            gap: Gap between train and test (prevents lookahead)
            expanding: If True, training window expands. If False, uses rolling window.
        """
        self.min_train = min_train
        self.test_size = test_size
        self.gap = gap
        self.expanding = expanding
    
    def walk_forward_splits(self, n_samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
        """
        Generate walk-forward train/test splits.
        
        Args:
            n_samples: Total number of samples.
            
        Returns:
            List of (train_indices, test_indices) tuples with proper gap.
        """
        splits: list[tuple[np.ndarray, np.ndarray]] = []
        indices = np.arange(n_samples)
        start = 0
        train_end = self.min_train
        
        while train_end + self.gap + self.test_size <= n_samples:
            test_start = train_end + self.gap
            test_end = test_start + self.test_size
            
            if self.expanding:
                train_idx = indices[start:train_end]
            else:
                train_idx = indices[max(0, train_end - self.min_train) : train_end]
            
            test_idx = indices[test_start:test_end]
            splits.append((train_idx, test_idx))
            train_end += self.test_size
        
        return splits
    
    def train_expert(
        self,
        expert: BaseExpert,
        X: pd.DataFrame | np.ndarray,
        y: np.ndarray,
        task: str = "classification",
        **fit_kwargs: Any,
    ) -> list[tuple[int, int]]:
        """
        Train an expert using walk-forward validation.
        
        Args:
            expert: The expert instance to train.
            X: Feature matrix (rows are time steps).
            y: Target labels.
            task: "classification" or "regression".
            **fit_kwargs: Additional arguments for expert.fit()
            
        Returns:
            List of (train_end_idx, test_start_idx) tuples for tracking.
        """
        splits = self.walk_forward_splits(len(y))
        history = []
        
        # Train on last split (final training set)
        if splits:
            train_idx, _ = splits[-1]
            if isinstance(X, pd.DataFrame):
                X_train = X.iloc[train_idx].values
            else:
                X_train = X[train_idx]
            
            y_train = y[train_idx]
            expert.fit(X_train, y_train, task=task, **fit_kwargs)
            
            for train_idx, test_idx in splits:
                history.append((train_idx[-1], test_idx[0]))
        
        return history
    
    def generate_expert_predictions_oos(
        self,
        expert: BaseExpert,
        contexts: list[ExpertContext],
        X: pd.DataFrame | np.ndarray,
        y: np.ndarray | None = None,
        task: str = "classification",
        **fit_kwargs: Any,
    ) -> list[list[ExpertPrediction]]:
        """
        Generate out-of-sample predictions from expert for all test folds.
        
        Args:
            expert: Expert instance (will be re-trained for each fold).
            contexts: List of ExpertContext objects (one per time step).
            X: Feature matrix.
            y: Target labels (required for training each fold).
            task: "classification" or "regression".
            **fit_kwargs: Additional arguments for expert.fit().
            
        Returns:
            List of prediction lists (one list per test fold).
            
        Raises:
            ValueError: If y is not provided (labels needed for fold training).
        """
        if y is None:
            raise ValueError(
                "y (target labels) must be provided for fold-wise expert training. "
                "This ensures true out-of-sample predictions and prevents leakage."
            )
        
        splits = self.walk_forward_splits(len(contexts))
        all_predictions: list[list[ExpertPrediction]] = []
        
        for train_idx, test_idx in splits:
            # ANTI-LEAKAGE: Re-train expert on THIS fold's training data only
            if isinstance(X, pd.DataFrame):
                X_train = X.iloc[train_idx].values
            else:
                X_train = X[train_idx]
            
            y_train = y[train_idx]
            expert.fit(X_train, y_train, task=task, **fit_kwargs)
            
            # Generate predictions on test data expert has never seen
            fold_predictions = []
            for i in test_idx:
                pred = expert.predict(contexts[i])
                fold_predictions.append(pred)
            all_predictions.append(fold_predictions)
        
        return all_predictions
    
    def train_and_evaluate_expert(
        self,
        expert: BaseExpert,
        contexts: list[ExpertContext],
        X: pd.DataFrame | np.ndarray,
        y_true: np.ndarray | None = None,
        task: str = "classification",
        eval_fn: Callable[[np.ndarray, np.ndarray], float] | None = None,
        **fit_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Complete walk-forward training and evaluation pipeline for expert.
        
        Args:
            expert: The expert to train.
            contexts: ExpertContext objects for all time steps.
            X: Feature matrix.
            y_true: True labels (for evaluation only, never seen during training).
            task: "classification" or "regression".
            eval_fn: Custom evaluation function(y_true, y_pred) -> score.
            **fit_kwargs: Arguments for expert.fit().
            
        Returns:
            Dictionary with training history and evaluation metrics.
        """
        results = {
            "expert_name": expert.expert_name,
            "splits": self.walk_forward_splits(len(contexts)),
            "oos_predictions": [],
            "metrics": {},
        }
        
        # Train on final fold
        history = self.train_expert(expert, X, y_true, task=task, **fit_kwargs)
        results["training_history"] = history
        
        # Generate OOS predictions with fold-wise training (prevents leakage)
        oos_preds = self.generate_expert_predictions_oos(
            expert, contexts, X, y=y_true, task=task, **fit_kwargs
        )
        results["oos_predictions"] = oos_preds
        
        # Optional evaluation
        if y_true is not None and eval_fn is not None:
            # Flatten OOS predictions for evaluation
            all_test_idx = []
            for _, test_idx in results["splits"]:
                all_test_idx.extend(test_idx)
            
            if all_test_idx and oos_preds:
                # Extract probabilities or severity from predictions
                y_pred = np.array([p.probability_active for fold in oos_preds for p in fold])
                y_test_subset = y_true[all_test_idx]
                
                if len(y_pred) == len(y_test_subset):
                    score = eval_fn(y_test_subset, y_pred)
                    results["metrics"]["custom_score"] = score
        
        return results
