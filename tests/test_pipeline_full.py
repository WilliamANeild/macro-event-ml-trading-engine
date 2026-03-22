import subprocess
import sys


def test_pipeline_mock_mode():
    result = subprocess.run(
        [sys.executable, "scripts/run_pipeline.py", "--mode", "mock"],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "."},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "pipeline complete" in result.stdout


def test_pipeline_full_mode():
    result = subprocess.run(
        [sys.executable, "scripts/run_pipeline.py", "--mode", "full"],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "."},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "pipeline complete" in result.stdout
