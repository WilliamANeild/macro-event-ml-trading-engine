import subprocess
import sys


def test_pipeline_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_pipeline.py"],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "."},
    )

    assert result.returncode == 0
    assert "pipeline complete" in result.stdout