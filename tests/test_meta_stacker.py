from datetime import date

import numpy as np
import pandas as pd

from src.engine.experts.schemas import ExpertPrediction
from src.engine.meta.combiner import MetaCombiner
from src.engine.meta.regime_detector import RegimeDetector
from src.engine.meta.stacker import MetaStacker
from src.engine.meta.walk_forward import WalkForwardSplitter


def _make_prediction(prob=0.7, sev=0.6, conf=0.8, direction="long"):
    return ExpertPrediction(
        expert_name="test",
        as_of_date=date(2024, 1, 1),
        theme="energy",
        subtheme="oil",
        probability_active=prob,
        severity_score=sev,
        confidence_score=conf,
        direction=direction,
    )


def test_walk_forward_splitter():
    splitter = WalkForwardSplitter(min_train=30, test_size=10, gap=2)
    splits = splitter.split(100)
    assert len(splits) > 0
    for train, test in splits:
        assert len(test) == 10
        assert train[-1] + 2 < test[0]  # gap preserved


def test_combiner_fallback():
    combiner = MetaCombiner()
    pred = _make_prediction()
    theme_scores, score, conf, direction = combiner.predict([pred])
    assert 0.0 <= score <= 1.0
    assert 0.0 <= conf <= 1.0


def test_combiner_fit_predict():
    combiner = MetaCombiner(method="logistic")
    rng = np.random.default_rng(42)
    preds = []
    labels = []
    for _ in range(100):
        p = rng.random()
        s = rng.random()
        c = rng.random()
        d = "long" if p > 0.5 else "short"
        pred = _make_prediction(prob=p, sev=s, conf=c, direction=d)
        preds.append([pred])
        labels.append(1 if p * s > 0.3 else 0)
    combiner.fit(preds, np.array(labels))
    assert combiner._fitted
    theme_scores, score, conf, direction = combiner.predict([_make_prediction()])
    assert 0.0 <= score <= 1.0


def test_regime_detector():
    detector = RegimeDetector()
    rng = np.random.default_rng(42)
    # Normal returns
    returns = pd.DataFrame(rng.normal(0.0005, 0.01, (100, 3)), columns=["A", "B", "C"])
    detector.fit(returns)
    regime = detector.detect(returns)
    assert regime in ("normal", "crisis", "euphoria", "transition")


def test_regime_crisis():
    detector = RegimeDetector()
    rng = np.random.default_rng(42)
    normal = pd.DataFrame(rng.normal(0.0005, 0.01, (200, 3)), columns=["A", "B", "C"])
    detector.fit(normal)
    # High vol + negative momentum -> crisis
    crisis = pd.DataFrame(rng.normal(-0.05, 0.08, (30, 3)), columns=["A", "B", "C"])
    regime = detector.detect(crisis)
    assert regime in ("crisis", "transition")


def test_stacker_no_args():
    stacker = MetaStacker()
    pred = _make_prediction()
    signal = stacker.combine([pred])
    assert signal.regime == "normal"
    assert signal.score > 0


def test_stacker_with_regime():
    rng = np.random.default_rng(42)
    returns = pd.DataFrame(rng.normal(0.0005, 0.01, (100, 3)), columns=["A", "B", "C"])
    detector = RegimeDetector()
    detector.fit(returns)
    stacker = MetaStacker(regime_detector=detector)
    stacker.set_recent_returns(returns)
    pred = _make_prediction()
    signal = stacker.combine([pred])
    assert signal.regime in ("normal", "crisis", "euphoria", "transition")
