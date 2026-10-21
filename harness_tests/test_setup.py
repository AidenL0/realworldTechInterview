import subprocess
import sys

from harnesslib import commands
from harnesslib.cli import main


def test_setup_creates_venv_then_installs(harness_root, monkeypatch, tmp_path):
    monkeypatch.setenv("HARNESS_PYTHON", str(tmp_path / "missing-python"))
    calls = []

    def fake_run(command, *args, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    assert main(["setup"]) == 0
    assert calls[0][1:3] == ["-m", "venv"]
    assert calls[1][1:4] == ["-m", "pip", "install"]
    assert calls[1][-1].endswith("requirements.txt")


def test_setup_skips_venv_when_present(harness_root, monkeypatch):
    monkeypatch.setenv("HARNESS_PYTHON", sys.executable)
    calls = []
    monkeypatch.setattr(
        commands.subprocess, "run", lambda command, *a, **k: calls.append(command) or subprocess.CompletedProcess(command, 0)
    )
    assert main(["setup"]) == 0
    assert len(calls) == 1
    assert calls[0][1:4] == ["-m", "pip", "install"]


def test_setup_reports_pip_failure(harness_root, monkeypatch, capsys):
    monkeypatch.setenv("HARNESS_PYTHON", sys.executable)
    monkeypatch.setattr(commands.subprocess, "run", lambda command, *a, **k: subprocess.CompletedProcess(command, 1))
    assert main(["setup"]) == 1
    assert "pip install failed" in capsys.readouterr().err
