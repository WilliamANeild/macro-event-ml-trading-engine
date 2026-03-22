from src.engine.expression.audit import ExposureAuditor
from src.engine.expression.exposure_mapper import ExposureMapper
from src.engine.universe.registry import get_universe


def test_exposure_matrix():
    mapper = ExposureMapper()
    universe = get_universe()
    themes = ["energy", "defense", "shipping"]
    matrix = mapper.build_exposure_matrix(universe, themes)
    assert len(matrix) == 3
    for theme in themes:
        assert theme in matrix
        weights = matrix[theme]
        assert len(weights) > 0
        # Weights should sum to ~1
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01


def test_exposure_energy_concentrated():
    mapper = ExposureMapper()
    universe = get_universe()
    matrix = mapper.build_exposure_matrix(universe, ["energy"])
    energy = matrix["energy"]
    # XLE should have highest weight for energy theme
    assert energy["XLE"] >= energy.get("ITA", 0)
    assert energy["XLE"] >= energy.get("SEA", 0)


def test_auditor():
    mapper = ExposureMapper()
    universe = get_universe()
    matrix = mapper.build_exposure_matrix(universe, ["energy", "defense"])
    auditor = ExposureAuditor()
    top = auditor.audit(matrix)
    assert "energy" in top
    assert len(top["energy"]) > 0


def test_auditor_report():
    mapper = ExposureMapper()
    universe = get_universe()
    matrix = mapper.build_exposure_matrix(universe, ["energy"])
    auditor = ExposureAuditor()
    report = auditor.generate_report(matrix)
    assert "Exposure Matrix Report" in report
