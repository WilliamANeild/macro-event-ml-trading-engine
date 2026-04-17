from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator


def test_synthetic_prices_shape():
    gen = SyntheticDataGenerator()
    cfg = gen.config
    prices = gen.load_prices()
    assert len(prices) == len(cfg.symbols)
    for sym in cfg.symbols:
        assert sym in prices
        assert len(prices[sym]) == cfg.n_days


def test_synthetic_returns():
    gen = SyntheticDataGenerator()
    cfg = gen.config
    gen.load_prices()
    returns = gen.get_returns()
    assert returns.shape == (cfg.n_days, len(cfg.symbols))
    assert list(returns.columns) == cfg.symbols


def test_event_manifest():
    gen = SyntheticDataGenerator()
    cfg = gen.config
    gen.load_prices()
    assert len(gen.event_manifest) == cfg.n_shocks
    for shock in gen.event_manifest:
        assert shock.symbol in cfg.symbols


def test_feature_history():
    gen = SyntheticDataGenerator()
    gen.load_prices()
    features = gen.generate_feature_history()
    assert len(features) > 0
    row = features[0]
    assert "SPY_return_1d" in row.values
    assert "SPY_vol_20d" in row.values


def test_synthetic_events():
    gen = SyntheticDataGenerator()
    gen.load_prices()
    evt_gen = SyntheticEventGenerator(gen.event_manifest)
    dates = gen.get_dates()
    events = evt_gen.generate(dates[0], len(dates))
    assert len(events) == len(dates)
    # At least some events should have nonzero intensity
    intensities = [e.values["event_intensity"] for e in events]
    assert any(i > 0.01 for i in intensities)


def test_custom_config():
    cfg = SyntheticConfig(n_days=100, n_shocks=2, seed=123)
    gen = SyntheticDataGenerator(config=cfg)
    prices = gen.load_prices()
    assert len(prices[cfg.symbols[0]]) == 100
    assert len(gen.event_manifest) == 2


def test_reproducibility():
    gen1 = SyntheticDataGenerator(config=SyntheticConfig(seed=42))
    gen2 = SyntheticDataGenerator(config=SyntheticConfig(seed=42))
    p1 = gen1.load_prices()
    p2 = gen2.load_prices()
    assert p1["SPY"] == p2["SPY"]
