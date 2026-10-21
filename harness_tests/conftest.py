import json
import shutil
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from harnesslib import clock

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "sample_root"


@pytest.fixture
def harness_root(tmp_path, monkeypatch):
    """A throwaway project root holding the 00-sample exercise, run with this venv's Python."""
    root = tmp_path / "root"
    shutil.copytree(FIXTURE_ROOT, root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    monkeypatch.setenv("HARNESS_ROOT", str(root))
    monkeypatch.setenv("HARNESS_PYTHON", sys.executable)
    return root


@pytest.fixture
def backdate(harness_root):
    """Move the current attempt's start time back by the given number of minutes."""

    def _backdate(minutes: int) -> None:
        path = harness_root / ".state" / "attempt.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["started_at"] = clock.to_iso(clock.now_utc() - timedelta(minutes=minutes))
        path.write_text(json.dumps(data), encoding="utf-8")

    return _backdate
