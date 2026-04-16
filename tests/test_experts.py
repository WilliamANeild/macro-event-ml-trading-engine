"""Comprehensive tests for the Experts feature including training, localization, and stacking."""

import sys
from pathlib import Path

# Add workspace root to path for direct execution
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.engine.experts import (
    BaseExpert,
    ConflictEscalationExpert,
    CryptoRegimeExpert,
    ExpertContext,
    ExpertFamily,
    ExpertPrediction,
    ExpertTrainer,
    LocalizationMetadata,
    LocalizationType,
    MarketPricingExpert,
    RatesPolicyExpert,
    ShippingChokePointExpert,
    get_available_experts,
    get_expert_by_family,
    get_experts,
)
from src.engine.meta.combiner import MetaCombiner
from src.engine.meta.stacker import MetaStacker


class TestExpertSchemas:
    """Test expert schemas and localization."""

    def test_localization_metadata_from_dict(self):
        """Test LocalizationMetadata creation from dict."""
        data = {
            "location_type": "chokepoint",
            "location_value": "suez",
            "region": "africa",
        }
        loc = LocalizationMetadata.from_dict(data)
        assert loc.location_type == LocalizationType.CHOKEPOINT
        assert loc.location_value == "suez"
        assert loc.region == "africa"

    def test_expert_prediction_validation(self):
        """Test that ExpertPrediction validates fields."""
        # Valid prediction
        pred = ExpertPrediction(
            expert_name="test",
            as_of_date=date(2024, 1, 1),
            theme="energy",
            subtheme="oil",
            probability_active=0.7,
            severity_score=0.6,
            confidence_score=0.8,
            direction="long",
        )
        assert pred.probability_active == 0.7

        # Invalid probability
        with pytest.raises(ValueError):
            ExpertPrediction(
                expert_name="test",
                as_of_date=date(2024, 1, 1),
                theme="energy",
                subtheme="oil",
                probability_active=1.5,  # Out of bounds
                severity_score=0.6,
                confidence_score=0.8,
                direction="long",
            )

        # Invalid direction
        with pytest.raises(ValueError):
            ExpertPrediction(
                expert_name="test",
                as_of_date=date(2024, 1, 1),
                theme="energy",
                subtheme="oil",
                probability_active=0.5,
                severity_score=0.6,
                confidence_score=0.8,
                direction="invalid",
            )

    def test_expert_prediction_with_localization(self):
        """Test ExpertPrediction with localization metadata."""
        loc = LocalizationMetadata(
            location_type=LocalizationType.PORT_CLUSTER,
            location_value="west_coast",
        )
        pred = ExpertPrediction(
            expert_name="shipping",
            as_of_date=date(2024, 1, 1),
            theme="shipping",
            subtheme="ports",
            probability_active=0.6,
            severity_score=0.5,
            confidence_score=0.7,
            direction="long",
            localization=loc,
        )
        assert pred.localization.location_type == LocalizationType.PORT_CLUSTER


class TestExpertPredictions:
    """Test individual expert prediction methods."""

    def test_conflict_escalation_expert_heuristic(self):
        """Test ConflictEscalationExpert heuristic prediction."""
        expert = ConflictEscalationExpert()
        context = ExpertContext(
            as_of_date=date(2024, 1, 1),
            theme="geopolitical",
            subtheme="middle_east",
            feature_row={
                "escalation_intensity": 0.7,
                "escalation_acceleration": 0.2,
                "sanctions_mentions": 5.0,
                "sanctions_direction": 0.8,
                "spillover_flag": 0.4,
                "region_volatility": 0.05,
            },
        )
        pred = expert.predict(context)
        assert pred.expert_name == "conflict_escalation"
        assert 0.0 <= pred.probability_active <= 1.0
        assert "conflict" in pred.tags

    def test_shipping_expert_heuristic(self):
        """Test ShippingChokePointExpert heuristic prediction."""
        expert = ShippingChokePointExpert()
        context = ExpertContext(
            as_of_date=date(2024, 1, 5),
            theme="shipping",
            subtheme="suez",
            feature_row={
                "chokepoint_intensity": 0.6,
                "incident_novelty": 0.5,
                "incident_count": 2.0,
                "port_stress": 0.4,
                "energy_move": 0.7,
                "freight_proxy_move": 0.65,
                "correlation_change": 0.3,
            },
        )
        pred = expert.predict(context)
        assert pred.expert_name == "shipping_chokepoint"
        assert pred.direction in ["long", "short", "neutral"]
        assert pred.localization.location_type == LocalizationType.PORT_CLUSTER

    def test_rates_expert_heuristic(self):
        """Test RatesPolicyExpert heuristic prediction."""
        expert = RatesPolicyExpert()
        context = ExpertContext(
            as_of_date=date(2024, 1, 10),
            theme="macro",
            subtheme="us_rates",
            feature_row={
                "yield_change": 0.02,
                "curve_slope_change": -0.005,
                "inflation_proxy_drift": 0.015,
                "cb_language_intensity": 0.8,
                "cb_language_shift": 0.2,
                "hawkish_shock_flag": 0.7,
                "easing_shock_flag": 0.1,
            },
        )
        pred = expert.predict(context)
        assert pred.expert_name == "rates_policy"
        assert "rates" in pred.tags
        assert "hawkish_shock" in pred.tags

    def test_market_pricing_expert_heuristic(self):
        """Test MarketPricingExpert heuristic prediction."""
        expert = MarketPricingExpert()
        context = ExpertContext(
            as_of_date=date(2024, 1, 15),
            theme="market_structure",
            subtheme="complacency",
            feature_row={
                "realized_volatility": 0.80,
                "vol_of_vol": 0.65,
                "cross_asset_correlation_spike": 0.7,
                "dispersion_commodities": 0.55,
                "dispersion_single_names": 0.3,
                "already_priced_indicator": 0.2,
                "market_depth": 0.3,
            },
        )
        pred = expert.predict(context)
        assert pred.expert_name == "market_pricing"
        assert "high_realized_vol" in pred.tags or "vol_regime_change" in pred.tags

    def test_crypto_regime_expert_heuristic(self):
        """Test CryptoRegimeExpert heuristic prediction."""
        expert = CryptoRegimeExpert()
        context = ExpertContext(
            as_of_date=date(2024, 1, 20),
            theme="crypto",
            subtheme="btc",
            feature_row={
                "crypto_volatility": 0.7,
                "crypto_equity_correlation": 0.75,
                "usd_strength": 0.6,
                "liquidity_stress": 0.3,
                "risk_on_signal": 0.7,
                "risk_off_signal": 0.2,
            },
        )
        pred = expert.predict(context)
        assert pred.expert_name == "crypto_regime"
        assert "crypto" in pred.tags
        assert "risk_on_behavior" in pred.tags or "stress_hedge_behavior" in pred.tags


class TestExpertRegistration:
    """Test expert registry and discovery."""

    def test_get_all_experts(self):
        """Test getting all available experts."""
        experts = get_experts()
        assert len(experts) > 0
        names = [e.expert_name for e in experts]
        assert "conflict_escalation" in names
        assert "shipping_chokepoint" in names
        assert "rates_policy" in names
        assert "market_pricing" in names
        assert "crypto_regime" in names

    def test_get_specific_experts(self):
        """Test getting specific experts by name."""
        experts = get_experts(["conflict_escalation", "crypto_regime"])
        assert len(experts) == 2
        names = [e.expert_name for e in experts]
        assert "conflict_escalation" in names
        assert "crypto_regime" in names

    def test_get_expert_by_family(self):
        """Test getting experts by family."""
        experts = get_expert_by_family(ExpertFamily.SHIPPING_CHOKEPOINT)
        assert len(experts) > 0
        assert experts[0].expert_family == ExpertFamily.SHIPPING_CHOKEPOINT

    def test_get_available_experts_dict(self):
        """Test getting mapping of available experts."""
        mapping = get_available_experts()
        assert isinstance(mapping, dict)
        assert "conflict_escalation" in mapping
        assert mapping["conflict_escalation"] == "conflict_escalation"


class TestExpertTraining:
    """Test expert training with walk-forward anti-leakage."""

    def test_trainer_walk_forward_splits(self):
        """Test walk-forward split generation."""
        trainer = ExpertTrainer(min_train=30, test_size=10, gap=2)
        splits = trainer.walk_forward_splits(100)
        assert len(splits) > 0
        
        # Verify gap between train and test
        for train_idx, test_idx in splits:
            assert max(train_idx) + 2 < min(test_idx)

    def test_trainer_expanding_vs_rolling(self):
        """Test expanding vs rolling window."""
        trainer_exp = ExpertTrainer(min_train=30, test_size=10, gap=2, expanding=True)
        trainer_roll = ExpertTrainer(min_train=30, test_size=10, gap=2, expanding=False)
        
        splits_exp = trainer_exp.walk_forward_splits(100)
        splits_roll = trainer_roll.walk_forward_splits(100)
        
        # Expanding should have growing train windows
        if len(splits_exp) > 1:
            assert len(splits_exp[0][0]) < len(splits_exp[-1][0])
        
        # Rolling should have constant train window size
        if len(splits_roll) > 1:
            assert len(splits_roll[0][0]) == len(splits_roll[-1][0])

    def test_expert_fit_and_predict(self):
        """Test fitting expert model and making predictions."""
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (100, 5))
        y = rng.binomial(1, 0.5, 100)
        
        expert = ConflictEscalationExpert()
        expert.fit(X, y, task="classification", n_estimators=10)
        assert expert._fitted
        
        # Test prediction
        X_test = rng.normal(0, 1, (10, 5))
        proba = expert.predict_proba(X_test)
        assert proba is not None
        assert proba.shape == (10, 2)

    def test_trainer_train_expert_walk_forward(self):
        """Test training expert with walk-forward protocol."""
        rng = np.random.default_rng(42)
        X = pd.DataFrame(rng.normal(0, 1, (100, 5)), columns=[f"f{i}" for i in range(5)])
        y = rng.binomial(1, 0.5, 100)
        
        # Create contexts
        contexts = [
            ExpertContext(
                as_of_date=date(2024, 1, 1),
                theme="test",
                subtheme="test",
                feature_row={f"f{i}": X.iloc[i, i % 5] for i in range(5)},
            )
            for _ in range(100)
        ]
        
        expert = ConflictEscalationExpert()
        trainer = ExpertTrainer(min_train=30, test_size=10, gap=2)
        
        history = trainer.train_expert(expert, X, y, task="classification", n_estimators=10)
        assert expert._fitted
        assert len(history) > 0

    def test_trainer_generate_oos_predictions(self):
        """Test OOS prediction generation with fold-wise training."""
        rng = np.random.default_rng(42)
        X = pd.DataFrame(rng.normal(0, 1, (100, 5)), columns=[f"f{i}" for i in range(5)])
        y = rng.binomial(1, 0.5, 100)
        
        contexts = [
            ExpertContext(
                as_of_date=date(2024, 1, 1),
                theme="test",
                subtheme="test",
                feature_row={},
            )
            for _ in range(100)
        ]
        
        expert = ConflictEscalationExpert()
        trainer = ExpertTrainer(min_train=30, test_size=10, gap=2)
        
        # Generate OOS predictions with fold-wise training (prevents leakage)
        oos_preds = trainer.generate_expert_predictions_oos(
            expert, contexts, X, y=y, task="classification", n_estimators=10
        )
        assert len(oos_preds) > 0
        assert all(isinstance(fold, list) for fold in oos_preds)


class TestMultiExpertStacking:
    """Test stacking and combining multiple experts."""

    def test_combiner_with_multiple_experts(self):
        """Test MetaCombiner with predictions from multiple experts."""
        combiner = MetaCombiner(method="logistic")
        
        # Generate test predictions from different experts
        pred1 = ExpertPrediction(
            expert_name="conflict",
            as_of_date=date(2024, 1, 1),
            theme="energy",
            subtheme="oil",
            probability_active=0.7,
            severity_score=0.6,
            confidence_score=0.8,
            direction="long",
        )
        pred2 = ExpertPrediction(
            expert_name="shipping",
            as_of_date=date(2024, 1, 1),
            theme="energy",
            subtheme="oil",
            probability_active=0.5,
            severity_score=0.4,
            confidence_score=0.7,
            direction="neutral",
        )
        
        theme_scores, score, conf, direction = combiner.predict([pred1, pred2])
        assert 0.0 <= score <= 1.0
        assert isinstance(theme_scores, dict)

    def test_stacker_with_regime_detection(self):
        """Test MetaStacker combining experts with regime detection."""
        rng = np.random.default_rng(42)
        
        # Create synthetic return data
        returns = pd.DataFrame(
            rng.normal(0.0005, 0.01, (100, 3)),
            columns=["energy", "shipping", "rates"],
        )
        
        combiner = MetaCombiner()
        stacker = MetaStacker(combiner=combiner)
        stacker.set_recent_returns(returns)
        
        # Test signal combination
        pred = ExpertPrediction(
            expert_name="test",
            as_of_date=date(2024, 1, 1),
            theme="energy",
            subtheme="oil",
            probability_active=0.6,
            severity_score=0.7,
            confidence_score=0.8,
            direction="long",
        )
        
        signal = stacker.combine([pred])
        assert signal.score > 0
        assert signal.regime in ("normal", "crisis", "euphoria", "transition")

    def test_expert_localization_prevents_borrowing(self):
        """Test that experts respect domain localization."""
        # Shipping expert should have port/chokepoint localization
        shipping_expert = ShippingChokePointExpert()
        context_shipping = ExpertContext(
            as_of_date=date(2024, 1, 1),
            theme="shipping",
            subtheme="suez",
            feature_row={
                "chokepoint_intensity": 0.6,
                "incident_novelty": 0.5,
                "incident_count": 2.0,
                "port_stress": 0.4,
                "energy_move": 0.7,
                "freight_proxy_move": 0.65,
                "correlation_change": 0.3,
            },
        )
        
        pred_shipping = shipping_expert.predict(context_shipping)
        assert pred_shipping.localization.location_type in [
            LocalizationType.PORT_CLUSTER,
            LocalizationType.CHOKEPOINT,
        ]
        
        # Conflict expert should have region localization
        conflict_expert = ConflictEscalationExpert()
        context_conflict = ExpertContext(
            as_of_date=date(2024, 1, 1),
            theme="geopolitical",
            subtheme="middle_east",
            feature_row={
                "escalation_intensity": 0.7,
                "escalation_acceleration": 0.2,
                "sanctions_mentions": 5.0,
                "sanctions_direction": 0.8,
                "spillover_flag": 0.4,
                "region_volatility": 0.05,
            },
        )
        
        pred_conflict = conflict_expert.predict(context_conflict)
        assert pred_conflict.localization.location_type == LocalizationType.REGION


class TestAntiLeakageProtocol:
    """Test anti-leakage protocol implementation."""

    def test_no_future_peeking_in_walk_forward(self):
        """Verify that test set is never used during training."""
        rng = np.random.default_rng(42)
        X = pd.DataFrame(rng.normal(0, 1, (100, 5)), columns=[f"f{i}" for i in range(5)])
        y = rng.binomial(1, 0.5, 100)
        
        trainer = ExpertTrainer(min_train=30, test_size=10, gap=2)
        splits = trainer.walk_forward_splits(100)
        
        # Verify each split respects the gap
        for train_idx, test_idx in splits:
            train_max = train_idx.max() if len(train_idx) > 0 else -1
            test_min = test_idx.min() if len(test_idx) > 0 else float("inf")
            # Gap should be at least 2
            assert test_min - train_max >= 3  # 1 for >= and 2 for gap

    def test_expanding_window_maintains_consistency(self):
        """Test that expanding window doesn't mix train and test."""
        trainer = ExpertTrainer(min_train=20, test_size=5, gap=2, expanding=True)
        splits = trainer.walk_forward_splits(50)
        
        for i, (train_idx, test_idx) in enumerate(splits):
            # No overlap between train and test in same fold
            assert not any(x in test_idx for x in train_idx)
            
            # Expanding: each train window should be at least as large as previous
            if i > 0:
                prev_train_idx, _ = splits[i - 1]
                assert len(train_idx) >= len(prev_train_idx)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
