# Experts Feature Implementation

## Overview

Implemented a comprehensive **localized, multi-expert signal system** for the macro-event ML trading engine. This system decomposes macroeconomic and market signals into domain-specific experts that run independently, preventing signal borrowing across unrelated domains and enabling precise, localized risk detection.

## Architecture

### Core Requirements Met

#### 3.1 Localized Experts
- **Every meaningful sub-sleeve has its own expert pipeline**
  - Shipping does not borrow defense signals
  - Rates does not borrow shipping signals
  - Inputs are independent unless logically justified
  
- **Standardized outputs, non-shared inputs**
  - All experts produce `ExpertPrediction` with: `probability_active`, `severity`, `confidence`, `direction`
  - Feature inputs are domain-specific (no cross-domain feature engineering)
  - Localization metadata ensures signal routing integrity

#### 3.2 Expert Output Standard
Each expert produces a weekly output package with:
- **Activation probability**: Is this localized shock active next week? (0-1)
- **Severity**: Expected magnitude of impact (0-1)
- **Confidence**: Reliability of prediction this week (0-1)
- **Direction**: Long/short/neutral signal
- **Localization metadata**: Region, chokepoint, port cluster, event type
- **Tags**: Semantic labels for signal interpretation

#### 3.3 Expert Family Implementations

##### ConflictEscalationExpert
```python
from src.engine.experts import ConflictEscalationExpert

expert = ConflictEscalationExpert()
# Features: escalation_intensity, escalation_acceleration, 
#          sanctions_mentions, sanctions_direction, spillover_flag
prediction = expert.predict(context)
```

Signals:
- Region-specific escalation intensity and acceleration
- Sanctions mentions with "tightening" vs "loosening" language
- Spillover flags (conflict + energy corridor references)
- Localization: Region-specific

##### ShippingChokePointExpert
```python
from src.engine.experts import ShippingChokePointExpert

expert = ShippingChokePointExpert()
# Features: chokepoint_intensity, incident_novelty, incident_count,
#          port_stress, energy_move, freight_proxy_move
prediction = expert.predict(context)
```

Signals:
- Chokepoint-specific intensity and novelty
- Incident keyword clusters (attack, boarding, piracy, port closure)
- Port cluster stress (India west coast vs east coast as distinct nodes)
- Market confirmation via energy/freight moves
- Localization: Port clusters, chokepoints

##### RatesPolicyExpert
```python
from src.engine.experts import RatesPolicyExpert

expert = RatesPolicyExpert()
# Features: yield_change, curve_slope_change, inflation_proxy_drift,
#          cb_language_intensity, hawkish_shock_flag, easing_shock_flag
prediction = expert.predict(context)
```

Signals:
- Yield curve changes and slope adjustments
- Central bank language intensity proxies
- Regime classification: hawkish shock vs easing shock vs stable
- Localization: Country-level

##### MarketPricingExpert
```python
from src.engine.experts import MarketPricingExpert

expert = MarketPricingExpert()
# Features: realized_volatility, vol_of_vol, 
#          cross_asset_correlation_spike, dispersion_commodities,
#          dispersion_single_names, already_priced_indicator
prediction = expert.predict(context)
```

Signals:
- Realized volatility and vol-of-vol spikes
- Cross-asset correlation breakdowns
- Commodity vs single-name dispersion
- "Already priced" indicator (reduces aggressiveness, pushes to ETF/hedge expression)
- Market depth stress indicator
- Localization: Commodity/theme level

##### CryptoRegimeExpert
```python
from src.engine.experts import CryptoRegimeExpert

expert = CryptoRegimeExpert()
# Features: crypto_volatility, crypto_equity_correlation,
#          usd_strength, liquidity_stress, risk_on_signal, risk_off_signal
prediction = expert.predict(context)
```

Signals:
- Crypto volatility and equity correlation structure
- USD moves and liquidity conditions
- Regime output: crypto behaves as "risk_on" vs "stress_hedge" vs "neutral"
- Localization: Global (crypto)

#### 3.4 Training Labels Strategy

Implemented **measurable outcome-based labeling** with two supported approaches:

1. **Cross-asset response patterns**: Define shock weeks using unusual combinations of returns
   - Example: Shipping shock = (energy ↑, risk-off ↑, shipping proxy abnormal)
   
2. **Unsupervised regime clustering**: Discover regimes via clustering, then train experts to predict them

Key design: **Consistency over perfection**. We care about actionable probability and direction, not storytelling.

### 4. Stacked Model Architecture

#### 4.1 Why Stacking
Enables multiple specialized experts (base learners) to capture nonlinear domain interactions while maintaining a stable, auditable layer (combiner) that converts expert outputs into portfolio-level decisions.

#### 4.2 Base Learners: Random Forests per Expert
Each expert uses `RandomForestClassifier` or `RandomForestRegressor` because:
- Nonlinear interactions matter in event systems
- Threshold effects are common (e.g., "spillover happens above 0.6 escalation")
- Tolerates messy feature distributions better than linear-only approaches
- Reduces need for manual feature engineering

#### 4.3 Meta-Model: Regularized Linear Combiner
The `MetaCombiner` ingests expert predictions and produces:
- Theme-level attractiveness scores for next week (not direct weights)
- Optional uncertainty estimates for risk engine
- **Regularization is non-negotiable** because expert outputs are correlated

Implementation in [src/engine/meta/combiner.py]:
```python
from src.engine.meta.combiner import MetaCombiner

combiner = MetaCombiner(method="logistic")  # or "ridge"
combiner.fit(expert_predictions, labels)
theme_scores, score, confidence, direction = combiner.predict(predictions)
```

#### 4.4 Anti-Leakage Protocol

**Standard: Rolling walk-forward training only**

The `ExpertTrainer` class enforces:
- ✅ No random shuffles
- ✅ Expert predictions must be out-of-sample for combiner training set
- ✅ No feature aggregation that peeks into the future
- ✅ Expanding or rolling window options

```python
from src.engine.experts import ExpertTrainer

trainer = ExpertTrainer(min_train=60, test_size=20, gap=5, expanding=True)

# Train expert with walk-forward protocol
history = trainer.train_expert(expert, X, y, task="classification", n_estimators=100)

# Generate OOS predictions for combiner
oos_predictions = trainer.generate_expert_predictions_oos(expert, contexts, X)

# Full pipeline with evaluation
results = trainer.train_and_evaluate_expert(
    expert, contexts, X, y_true=labels, task="classification",
    eval_fn=lambda y_true, y_pred: roc_auc_score(y_true, y_pred)
)
```

## File Structure

### Core Expert Implementation
- `src/engine/experts/base.py` - `BaseExpert` abstract class with training/prediction interface
- `src/engine/experts/schemas.py` - `ExpertPrediction`, `ExpertContext`, localization types
- `src/engine/experts/conflict_expert.py` - `ConflictEscalationExpert`
- `src/engine/experts/shipping_expert.py` - `ShippingChokePointExpert`
- `src/engine/experts/rates_expert.py` - `RatesPolicyExpert`
- `src/engine/experts/market_expert.py` - `MarketPricingExpert`
- `src/engine/experts/crypto_expert.py` - `CryptoRegimeExpert`

### Infrastructure
- `src/engine/experts/trainer.py` - `ExpertTrainer` with walk-forward validation
- `src/engine/experts/registry.py` - Expert discovery and instantiation
- `src/engine/experts/__init__.py` - Public API exports

### Integration
- `src/engine/meta/combiner.py` - `MetaCombiner` (already existed, now used as meta-model)
- `src/engine/meta/stacker.py` - `MetaStacker` (orchestrates experts → combiner)

### Testing
- `tests/test_experts.py` - 22 comprehensive tests covering:
  - Localization metadata and validation
  - Individual expert predictions (heuristic and model-based)
  - Expert registry and discovery
  - Walk-forward training with anti-leakage protocol
  - Multi-expert stacking with regime detection
  - Expanding vs rolling windows
  - Domain isolation (no signal borrowing)

## Usage Examples

### Basic Expert Prediction
```python
from datetime import date
from src.engine.experts import ConflictEscalationExpert, ExpertContext

expert = ConflictEscalationExpert()
context = ExpertContext(
    as_of_date=date(2024, 1, 15),
    theme="geopolitical",
    subtheme="middle_east",
    feature_row={
        "escalation_intensity": 0.7,
        "escalation_acceleration": 0.2,
        "sanctions_mentions": 5.0,
        "sanctions_direction": 0.8,
        "spillover_flag": 0.4,
        "region_volatility": 0.05,
    }
)

prediction = expert.predict(context)
print(f"Probability active: {prediction.probability_active}")
print(f"Severity: {prediction.severity_score}")
print(f"Direction: {prediction.direction}")
print(f"Tags: {prediction.tags}")
```

### Train Expert with Walk-Forward Protocol
```python
import numpy as np
import pandas as pd
from src.engine.experts import ShippingChokePointExpert, ExpertTrainer

# Prepare data
X = pd.DataFrame(np.random.randn(200, 7), columns=[f"feature_{i}" for i in range(7)])
y = np.random.binomial(1, 0.5, 200)
contexts = [ExpertContext(...) for _ in range(200)]

# Train expert
expert = ShippingChokePointExpert()
trainer = ExpertTrainer(min_train=60, test_size=20, gap=5)
trainer.train_expert(expert, X, y, task="classification", n_estimators=100)

# Generate OOS predictions for combiner training
oos_preds = trainer.generate_expert_predictions_oos(expert, contexts, X)
```

### Multi-Expert Signal Combination
```python
from src.engine.experts import get_experts
from src.engine.meta.combiner import MetaCombiner
from src.engine.meta.stacker import MetaStacker

# Get all experts
experts = get_experts()  # Returns all 5 expert types + mock

# Create stacker
combiner = MetaCombiner(method="logistic")
stacker = MetaStacker(combiner=combiner)

# Get expert predictions (already pre-trained)
predictions = [expert.predict(context) for expert in experts]

# Combine into meta signal
signal = stacker.combine(predictions)
print(f"Combined score: {signal.score}")
print(f"Regime: {signal.regime}")
print(f"Theme scores: {signal.theme_scores}")
```

### Enforce Domain Isolation
```python
from src.engine.experts import (
    get_expert_by_family, 
    ExpertFamily, 
    LocalizationType
)

# Get only shipping experts (don't borrow from rates)
shipping_experts = get_expert_by_family(ExpertFamily.SHIPPING_CHOKEPOINT)

# Each prediction has localization metadata ensuring correct routing
for expert in shipping_experts:
    pred = expert.predict(context)
    assert pred.localization.location_type in [
        LocalizationType.PORT_CLUSTER,
        LocalizationType.CHOKEPOINT
    ]
```

## Key Design Decisions

### 1. Heuristic Fallback
Each expert includes a `_heuristic_predict()` method for immediate signal generation when models aren't fitted yet. This enables:
- Quick signal generation without waiting for training
- Reasonable defaults based on domain knowledge
- Smooth transition from heuristic to ML-based predictions

### 2. Flexible Localization
`LocalizationMetadata` supports:
- `REGION` - conflict experts (geopolitical)
- `CHOKEPOINT` - shipping routes (Suez, Panama)
- `PORT_CLUSTER` - shipping port groupings
- `COMMODITY` - price signal sources
- `COUNTRY` - policy/rates signals

Prevents accidental signal borrowing across incompatible domains.

### 3. Walk-Forward Anti-Leakage
The `ExpertTrainer` ensures:
- Test data never used during training
- Configurable gap between train/test (default=5) prevents lookahead
- Optional expanding window (larger training = more stability)
- Built-in evaluation during walk-forward folds

### 4. Standardized Expert Interface
All experts inherit from `BaseExpert` with:
- Mandatory `predict(context) -> ExpertPrediction` method
- Optional `fit(X, y, task, **kwargs)` for model training
- Optional `predict_proba()` and `predict_values()` for model access
- Consistent feature importance tracking

## Testing Coverage (22 tests)

✅ Schema validation (localization, predictions)
✅ Heuristic predictions for all 5 experts
✅ Expert registration and discovery
✅ Walk-forward train/test split generation
✅ Expanding vs rolling windows
✅ Model fitting and prediction
✅ OOS prediction generation
✅ Multi-expert stacking with combiner
✅ Regime detection integration
✅ Domain isolation verification
✅ Anti-leakage protocol enforcement

All tests pass. Backward compatibility with existing `test_meta_stacker.py` confirmed.

## Next Steps (Optional Enhancements)

1. **Feature Engineering Pipelines**: Automated feature computation from raw data feeds
2. **Hyperparameter Tuning**: Bayesian optimization per expert within walk-forward folds
3. **Ensemble Methods**: Weighted stacking instead of simple linear combiner
4. **Real-time Streaming**: Incremental model updates with new weekly data
5. **Explainability Dashboard**: SHAP values and feature contributions per expert
6. **Backtesting Integration**: Direct connection to backtest engine for strategy evaluation
