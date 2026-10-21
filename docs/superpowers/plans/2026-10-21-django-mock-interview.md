# Django Mock Interview Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local HackerRank-style practice harness (`harness.py`) plus one full-length Django REST Framework mock exercise with planted bugs, a missing feature, visible tests and hidden tests.

**Architecture:** `harness.py` is a thin entry point over a stdlib-only package, `harnesslib/`, with one module per job: clock, results (JUnit parsing and scoring), config, state, system (filesystem and subprocess helpers), workspace, grading, verify, commands, and cli. Grading copies the user's workspace into a temp sandbox, restores the original visible tests, adds the hidden tests, runs pytest with a JUnit report, and scores against fixed counts. Exercise 01 is written by a background agent so its content never appears in the main session.

**Tech Stack:** Python 3.11+ (stdlib only for the harness; developed on 3.13), Django 5.2, Django REST Framework 3.16, pytest 8, pytest-django 4, git, VS Code, GitHub Actions. Licensed under AGPL-3.0-or-later.

**Spec:** `docs/superpowers/specs/2026-10-21-django-mock-interview-design.md`

## Global Constraints

- `harness.py` and `harnesslib/` import only the Python standard library; they must run on Python 3.11+.
- Windows is the primary platform: use `pathlib` everywhere, pass subprocess arguments as lists, and never use `shell=True`.
- Run every command from the project root in Git Bash unless a step says PowerShell. The venv interpreter is `.venv/Scripts/python`.
- Exit codes: `0` success, `1` user error (`HarnessError`, or a declined prompt), `2` unexpected internal error.
- `submit` never prints raw pytest output, hidden test names, or hidden test code.
- **Spoiler rule:** the main session never reads, greps, or prints anything under `exercises/01-*/` or `.grader/01-*/`. Only the Task 9 background agent touches them.
- **Open source:** the project is licensed AGPL-3.0-or-later. Public docs never claim affiliation with HackerRank or any employer, and never name a specific company's assessment. Every exercise is original.
- **Harness portability:** the harness must work on Windows, macOS and Linux with Python 3.11 and 3.13 (the CI matrix).
- Text files use LF line endings (enforced by `.gitattributes`) so fix patches apply cleanly on Windows.
- Pinned dependencies: Django 5.x, djangorestframework 3.x, pytest, pytest-django (exact versions in `requirements.txt`).
- Every commit message ends with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Workspace files locked on Windows.** A VS Code window or terminal holding `workspace/` open during `start` or `reset` should produce a clear "Close VS Code…" error with exit 1, not a traceback. Tests: Task 3 (`remove_tree`) and Task 4 (`reset`).
2. **Candidate changes the tests.** Deleting, editing or adding files in `workspace/tests/`, or adding test files elsewhere in the workspace, should leave the score unchanged. Test: Task 5.
3. **App code that hangs or can't import.** `submit` should finish, score 0, and explain why; it must never hang. Tests: Task 5.
4. **Non-ASCII output from child Pythons on Windows.** Output such as `café ✓` should decode cleanly, without `UnicodeDecodeError` or mojibake. Test: Task 3.
5. **Hand-edited or corrupt `.state/*.json`.** The error message should name the file and say to fix or delete it, with exit 1. Test: Task 3.

---

### Task 1: Project scaffolding and clock helpers

**Files:**
- Create: `.gitignore`, `.gitattributes`, `requirements.txt`, `pytest.ini`
- Create: `harnesslib/__init__.py`, `harnesslib/clock.py`
- Test: `harness_tests/test_clock.py`

**Interfaces:**
- Consumes: nothing.
- Produces (`harnesslib.clock`): `now_utc() -> datetime`, `to_iso(moment: datetime) -> str`, `elapsed_seconds(started_at: str, now: datetime) -> int`, `format_duration(seconds: int) -> str`, `is_overtime(elapsed: int, limit_minutes: int) -> bool`.

- [ ] **Step 1: Create a working branch**

Run: `git checkout -b build/harness-v1`
Expected: `Switched to a new branch 'build/harness-v1'`

- [ ] **Step 2: Write the project config files**

`.gitignore`:
```
/.venv/
/workspace/
/.state/
__pycache__/
*.pyc
.pytest_cache/
db.sqlite3
```

`.gitattributes`:
```
# Keep LF everywhere so fix patches apply cleanly on Windows.
* text=auto eol=lf
```

`requirements.txt` (ranges for now; Step 4 pins them):
```
Django>=5.2,<6.0
djangorestframework>=3.16,<4.0
pytest>=8.3,<9.0
pytest-django>=4.9,<5.0
```

`pytest.ini`:
```ini
[pytest]
testpaths = harness_tests
pythonpath = .
norecursedirs = .* fixtures __pycache__
```

- [ ] **Step 3: Create the venv and install**

Run: `python -m venv .venv && .venv/Scripts/python -m pip install -q -r requirements.txt && .venv/Scripts/python -m pip freeze`
Expected: the freeze output includes `Django==5.2.*`, `djangorestframework==3.*`, `pytest==8.*`, `pytest-django==4.*`.

- [ ] **Step 4: Pin exact versions**

Replace `requirements.txt` with exactly four lines: the `Django==…`, `djangorestframework==…`, `pytest==…` and `pytest-django==…` lines printed by `pip freeze` in Step 3, in that order and with the exact versions shown. Then run:

Run: `.venv/Scripts/python -m pip install -q -r requirements.txt && echo ok`
Expected: `ok`

- [ ] **Step 5: Write the failing clock tests**

`harness_tests/test_clock.py`:
```python
from datetime import datetime, timedelta, timezone

from harnesslib.clock import elapsed_seconds, format_duration, is_overtime, to_iso

START = datetime(2026, 10, 21, 14, 0, 0, tzinfo=timezone.utc)


def test_to_iso_is_utc_with_seconds():
    assert to_iso(START) == "2026-10-21T14:00:00+00:00"


def test_elapsed_seconds_counts_from_start():
    assert elapsed_seconds(to_iso(START), START + timedelta(minutes=72, seconds=10)) == 4330


def test_elapsed_seconds_never_negative():
    assert elapsed_seconds(to_iso(START), START - timedelta(seconds=5)) == 0


def test_format_duration_pads_seconds():
    assert format_duration(4330) == "72m 10s"
    assert format_duration(63) == "1m 03s"
    assert format_duration(0) == "0m 00s"


def test_overtime_only_after_limit():
    assert not is_overtime(90 * 60, 90)
    assert is_overtime(90 * 60 + 1, 90)
```

- [ ] **Step 6: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_clock.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'harnesslib'`

- [ ] **Step 7: Implement the clock helpers**

`harnesslib/__init__.py`:
```python
"""Library behind harness.py: the HackerRank-style mock interview runner."""
```

`harnesslib/clock.py`:
```python
"""Time helpers for attempts: UTC timestamps, elapsed time, and formatting."""
from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def elapsed_seconds(started_at: str, now: datetime) -> int:
    started = datetime.fromisoformat(started_at)
    return max(0, int((now - started).total_seconds()))


def format_duration(seconds: int) -> str:
    minutes, secs = divmod(max(0, int(seconds)), 60)
    return f"{minutes}m {secs:02d}s"


def is_overtime(elapsed: int, limit_minutes: int) -> bool:
    return elapsed > limit_minutes * 60
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest harness_tests/test_clock.py -v`
Expected: `5 passed`

- [ ] **Step 9: Commit**

```bash
git add .gitignore .gitattributes requirements.txt pytest.ini harnesslib harness_tests
git commit -F - <<'EOF'
Add project scaffolding and clock helpers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 2: JUnit parsing and scoring

**Files:**
- Create: `harnesslib/results.py`
- Test: `harness_tests/test_results.py`

**Interfaces:**
- Consumes: nothing.
- Produces (`harnesslib.results`):
  - `HIDDEN_PREFIX = "tests.hidden."`
  - `CaseResult(test_id: str, hidden: bool, passed: bool, is_test: bool)`: a frozen dataclass. `is_test` is `False` for pytest's collection-error entries (empty `classname`).
  - `Score(visible_passed, visible_total, hidden_passed, hidden_total, failed_visible: tuple[str, ...] = (), load_errors: int = 0)`: a frozen dataclass with properties `passed`, `total`, and `percent` (a float rounded to 1 decimal; `0.0` when `total == 0`).
  - `parse_junit(path: Path) -> list[CaseResult]`
  - `score_cases(cases: Sequence[CaseResult], expected_visible: int, expected_hidden: int) -> Score`

- [ ] **Step 1: Write the failing tests**

`harness_tests/test_results.py`:
```python
from harnesslib.results import CaseResult, Score, parse_junit, score_cases

REPORT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="2" failures="1" skipped="1" tests="6">
<testcase classname="tests.test_api" name="test_list" time="0.01" />
<testcase classname="tests.test_api" name="test_create" time="0.01"><failure message="assert 400 == 201">trace</failure></testcase>
<testcase classname="tests.test_api.TestOrders" name="test_total" time="0.01"><error message="fixture error">trace</error></testcase>
<testcase classname="tests.test_api" name="test_later" time="0.0"><skipped message="todo" /></testcase>
<testcase classname="tests.hidden.test_hidden_api" name="test_edge" time="0.01" />
<testcase classname="" name="tests.hidden.test_hidden_broken" time="0.0"><error message="collection failure">ImportError</error></testcase>
</testsuite></testsuites>
"""


def write_report(tmp_path, text=REPORT):
    path = tmp_path / "report.xml"
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_junit_reads_every_case(tmp_path):
    cases = parse_junit(write_report(tmp_path))
    assert [c.test_id for c in cases] == [
        "tests.test_api::test_list",
        "tests.test_api::test_create",
        "tests.test_api.TestOrders::test_total",
        "tests.test_api::test_later",
        "tests.hidden.test_hidden_api::test_edge",
        "tests.hidden.test_hidden_broken",
    ]
    assert [c.passed for c in cases] == [True, False, False, False, True, False]
    assert [c.hidden for c in cases] == [False, False, False, False, True, True]
    assert [c.is_test for c in cases] == [True, True, True, True, True, False]


def test_hidden_needs_the_exact_prefix(tmp_path):
    report = REPORT.replace(
        'classname="tests.test_api" name="test_list"', 'classname="tests.hiddenfoo" name="test_list"'
    )
    first = parse_junit(write_report(tmp_path, report))[0]
    assert first.test_id == "tests.hiddenfoo::test_list"
    assert first.hidden is False


def test_score_uses_expected_counts(tmp_path):
    score = score_cases(parse_junit(write_report(tmp_path)), expected_visible=4, expected_hidden=3)
    assert (score.visible_passed, score.visible_total) == (1, 4)
    assert (score.hidden_passed, score.hidden_total) == (1, 3)
    assert (score.passed, score.total) == (2, 7)
    assert score.percent == 28.6
    assert score.load_errors == 1
    assert score.failed_visible == (
        "tests.test_api::test_create",
        "tests.test_api.TestOrders::test_total",
        "tests.test_api::test_later",
    )


def test_missing_tests_count_as_failed():
    score = score_cases([], expected_visible=3, expected_hidden=2)
    assert (score.passed, score.total, score.percent) == (0, 5, 0.0)


def test_extra_passes_never_exceed_expected():
    cases = [CaseResult(f"tests.test_a::t{i}", False, True, True) for i in range(5)]
    assert score_cases(cases, expected_visible=3, expected_hidden=0).visible_passed == 3


def test_percent_rounding_and_empty_total():
    assert Score(2, 3, 0, 0).percent == 66.7
    assert Score(0, 0, 0, 0).percent == 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_results.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'harnesslib.results'`

- [ ] **Step 3: Implement**

`harnesslib/results.py`:
```python
"""Parse pytest JUnit XML reports and turn them into a HackerRank-style score."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

HIDDEN_PREFIX = "tests.hidden."
_NOT_PASSED_TAGS = {"failure", "error", "skipped"}


@dataclass(frozen=True)
class CaseResult:
    test_id: str
    hidden: bool
    passed: bool
    is_test: bool


@dataclass(frozen=True)
class Score:
    visible_passed: int
    visible_total: int
    hidden_passed: int
    hidden_total: int
    failed_visible: tuple[str, ...] = ()
    load_errors: int = 0

    @property
    def passed(self) -> int:
        return self.visible_passed + self.hidden_passed

    @property
    def total(self) -> int:
        return self.visible_total + self.hidden_total

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 0.0
        return round(100 * self.passed / self.total, 1)


def parse_junit(path: Path) -> list[CaseResult]:
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        # pytest reports a module that failed to import as a case with an empty classname.
        is_test = bool(classname)
        test_id = f"{classname}::{name}" if is_test else name
        failed = any(child.tag in _NOT_PASSED_TAGS for child in case)
        cases.append(
            CaseResult(
                test_id=test_id,
                hidden=test_id.startswith(HIDDEN_PREFIX),
                passed=is_test and not failed,
                is_test=is_test,
            )
        )
    return cases


def score_cases(cases: Sequence[CaseResult], expected_visible: int, expected_hidden: int) -> Score:
    visible_passed = sum(1 for c in cases if c.passed and not c.hidden)
    hidden_passed = sum(1 for c in cases if c.passed and c.hidden)
    return Score(
        visible_passed=min(visible_passed, expected_visible),
        visible_total=expected_visible,
        hidden_passed=min(hidden_passed, expected_hidden),
        hidden_total=expected_hidden,
        failed_visible=tuple(c.test_id for c in cases if c.is_test and not c.hidden and not c.passed),
        load_errors=sum(1 for c in cases if not c.is_test),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest harness_tests/test_results.py -v`
Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add harnesslib/results.py harness_tests/test_results.py
git commit -F - <<'EOF'
Add JUnit report parsing and scoring

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 3: Config, state, system helpers, CLI skeleton, `list`, and the sample fixture

**Files:**
- Create: `harnesslib/config.py`, `harnesslib/state.py`, `harnesslib/system.py`, `harnesslib/commands.py`, `harnesslib/cli.py`, `harness.py`
- Create the fixture tree under `harness_tests/fixtures/sample_root/` (files listed in Step 1)
- Create: `harness_tests/conftest.py`
- Test: `harness_tests/test_foundation.py`

**Interfaces:**
- Consumes: `harnesslib.clock` (Task 1).
- Produces:
  - `harnesslib.config`:
    - `HarnessError(Exception)`
    - `Paths(root: Path)` with properties `exercises`, `grader`, `workspace`, `state`, `attempt_file`, `history_file`, `venv_python`. `venv_python` honours the `HARNESS_PYTHON` override.
    - `get_paths() -> Paths`, which honours the `HARNESS_ROOT` override.
    - `Exercise(id, title, time_limit_minutes, setup_commands: tuple[tuple[str, ...], ...], check_command: tuple[str, ...] | None, source_dir: Path, grader_dir: Path)`
    - `load_exercises(paths) -> dict[str, Exercise]`, `get_exercise(paths, exercise_id) -> Exercise`, `require_venv(paths) -> None`, `load_expected(exercise) -> tuple[int, int]`, `read_json(path, default)`, `write_json(path, data)`.
  - `harnesslib.state`: `Attempt(exercise_id: str, started_at: str, time_limit_minutes: int)`, `load_attempt(paths) -> Attempt | None`, `save_attempt(paths, attempt)`, `clear_attempt(paths)`, `load_history(paths) -> list[dict]`, `append_history(paths, entry: dict)`, `best_score(history, exercise_id) -> float | None`.
  - `harnesslib.system`: `child_env() -> dict[str, str]`, `remove_tree(path: Path) -> None`, `run_python(paths, args: Sequence[str], cwd: Path, timeout: float | None = None) -> tuple[bool, str]`, `run_git(args: list[str], cwd: Path) -> None`.
  - `harnesslib.commands`: `confirm(question: str) -> bool`, `cmd_list(paths) -> int`.
  - `harnesslib.cli`: `main(argv: list[str] | None = None) -> int`. It dispatches by attribute lookup to `commands.cmd_setup/cmd_list/cmd_start/cmd_time/cmd_submit/cmd_reset/cmd_answers/cmd_verify`; later tasks add the commands that don't exist yet.
  - Test fixtures: `harness_root` (a temp project root with `00-sample`, where `HARNESS_ROOT` and `HARNESS_PYTHON=sys.executable` are set) and `backdate(minutes)` (moves the attempt's start time back).

- [ ] **Step 1: Create the sample fixture (two bugs; the second is caught only by hidden tests)**

`harness_tests/fixtures/sample_root/exercises/00-sample/exercise.json`:
```json
{
  "id": "00",
  "title": "Sample calculator",
  "time_limit_minutes": 30,
  "setup_commands": [],
  "check_command": ["-c", "import calc"]
}
```

`harness_tests/fixtures/sample_root/exercises/00-sample/pytest.ini`:
```ini
[pytest]
pythonpath = .
```

`harness_tests/fixtures/sample_root/exercises/00-sample/README.md`:
```markdown
# Sample calculator

`calc.py` must provide:

- `add(a, b)`: the sum of `a` and `b`.
- `average(values)`: the mean of `values`, or `0.0` for an empty list.
- `clamp(value, low, high)`: `value` limited to the range `low..high`.
```

`harness_tests/fixtures/sample_root/exercises/00-sample/calc.py` (exactly 12 lines, ending with a newline):
```python
def add(a, b):
    return a + b


def average(values):
    if not values:
        return 0.0
    return sum(values) / (len(values) - 1)


def clamp(value, low, high):
    return max(low, min(value, low))
```

`harness_tests/fixtures/sample_root/exercises/00-sample/tests/test_calc.py`:
```python
from calc import add, average


def test_add():
    assert add(2, 3) == 5


def test_average():
    assert average([2, 4, 6]) == 4
```

`harness_tests/fixtures/sample_root/.grader/00-sample/hidden_tests/test_hidden_calc.py`:
```python
from calc import average, clamp


def test_average_empty_list():
    assert average([]) == 0.0


def test_average_single():
    assert average([5]) == 5


def test_clamp_inside_range():
    assert clamp(5, 0, 10) == 5
```

`harness_tests/fixtures/sample_root/.grader/00-sample/expected.json`:
```json
{"visible": 2, "hidden": 3}
```

`harness_tests/fixtures/sample_root/.grader/00-sample/ANSWER_KEY.md`:
```markdown
# Sample answer key

1. `average` divides by `len(values) - 1`; it should divide by `len(values)`.
   Caught by `test_average` (visible) and `test_average_single` (hidden).
2. `clamp` uses `low` as the upper bound; it should use `high`.
   Caught only by `test_clamp_inside_range` (hidden).
```

`harness_tests/fixtures/sample_root/.grader/00-sample/fixes/fix_01.patch` (blank context lines are a single space):
```diff
diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -5,7 +5,7 @@ def add(a, b):
 def average(values):
     if not values:
         return 0.0
-    return sum(values) / (len(values) - 1)
+    return sum(values) / len(values)
 
 
 def clamp(value, low, high):
```

`harness_tests/fixtures/sample_root/.grader/00-sample/fixes/fix_02.patch`:
```diff
diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -9,4 +9,4 @@ def average(values):
 
 
 def clamp(value, low, high):
-    return max(low, min(value, low))
+    return max(low, min(value, high))
```

`harness_tests/fixtures/sample_root/.grader/00-sample/solution.patch`:
```diff
diff --git a/calc.py b/calc.py
--- a/calc.py
+++ b/calc.py
@@ -5,8 +5,8 @@ def add(a, b):
 def average(values):
     if not values:
         return 0.0
-    return sum(values) / (len(values) - 1)
+    return sum(values) / len(values)
 
 
 def clamp(value, low, high):
-    return max(low, min(value, low))
+    return max(low, min(value, high))
```

- [ ] **Step 2: Check the fixture patches apply**

Run:
```bash
T="$(mktemp -d)" && cp -r harness_tests/fixtures/sample_root/exercises/00-sample/. "$T" && for p in fixes/fix_01.patch fixes/fix_02.patch solution.patch; do (cd "$T" && git apply --check "$OLDPWD/harness_tests/fixtures/sample_root/.grader/00-sample/$p" && echo "$p ok"); done
```
Expected: `fixes/fix_01.patch ok`, `fixes/fix_02.patch ok`, `solution.patch ok`

- [ ] **Step 3: Write the shared test fixtures**

`harness_tests/conftest.py`:
```python
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
```

- [ ] **Step 4: Write the failing tests**

`harness_tests/test_foundation.py`:
```python
import os
import stat
import sys
from pathlib import Path

import pytest

from harnesslib import system
from harnesslib.cli import main
from harnesslib.config import HarnessError, get_paths, load_exercises
from harnesslib.state import (
    Attempt,
    append_history,
    best_score,
    clear_attempt,
    load_attempt,
    load_history,
    save_attempt,
)


def test_paths_follow_environment_overrides(harness_root):
    paths = get_paths()
    assert paths.root == harness_root.resolve()
    assert paths.venv_python == Path(sys.executable)


def test_default_venv_python_is_inside_root(harness_root, monkeypatch):
    monkeypatch.delenv("HARNESS_PYTHON")
    paths = get_paths()
    folder, exe = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    assert paths.venv_python == paths.root / ".venv" / folder / exe


def test_load_exercises_reads_metadata(harness_root):
    exercise = load_exercises(get_paths())["00"]
    assert exercise.title == "Sample calculator"
    assert exercise.time_limit_minutes == 30
    assert exercise.setup_commands == ()
    assert exercise.check_command == ("-c", "import calc")
    assert exercise.grader_dir == harness_root.resolve() / ".grader" / "00-sample"


def test_attempt_round_trip(harness_root):
    paths = get_paths()
    assert load_attempt(paths) is None
    save_attempt(paths, Attempt("00", "2026-10-21T14:00:00+00:00", 30))
    assert load_attempt(paths) == Attempt("00", "2026-10-21T14:00:00+00:00", 30)
    clear_attempt(paths)
    clear_attempt(paths)
    assert load_attempt(paths) is None


def test_history_and_best_score(harness_root):
    paths = get_paths()
    assert best_score(load_history(paths), "00") is None
    append_history(paths, {"exercise_id": "00", "score_pct": 40.0})
    append_history(paths, {"exercise_id": "00", "score_pct": 80.0})
    append_history(paths, {"exercise_id": "01", "score_pct": 95.0})
    assert best_score(load_history(paths), "00") == 80.0


def test_corrupt_state_file_gives_clear_error(harness_root, capsys):
    state = harness_root / ".state"
    state.mkdir()
    (state / "history.json").write_text("{", encoding="utf-8")
    assert main(["list"]) == 1
    err = capsys.readouterr().err
    assert "history.json is not valid JSON" in err
    assert "Fix or delete it" in err


def test_remove_tree_handles_read_only_files(tmp_path):
    target = tmp_path / "repo"
    (target / "objects").mkdir(parents=True)
    locked = target / "objects" / "pack"
    locked.write_text("x", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    system.remove_tree(target)
    assert not target.exists()


def test_remove_tree_missing_path_is_a_no_op(tmp_path):
    system.remove_tree(tmp_path / "missing")


def test_remove_tree_explains_locked_files(tmp_path, monkeypatch):
    target = tmp_path / "workspace"
    target.mkdir()

    def locked(*_args, **_kwargs):
        raise PermissionError(13, "The process cannot access the file", str(target / "calc.py"))

    monkeypatch.setattr(system.shutil, "rmtree", locked)
    with pytest.raises(HarnessError, match="Close VS Code"):
        system.remove_tree(target)


def test_run_python_decodes_non_ascii_output(harness_root, tmp_path):
    ok, output = system.run_python(get_paths(), ["-c", "print('caf\\u00e9 \\u2713')"], tmp_path)
    assert ok
    assert "café ✓" in output


def test_list_shows_exercises(harness_root, capsys):
    assert main(["list"]) == 0
    assert "00  Sample calculator  (30m)  best: —" in capsys.readouterr().out


def test_list_marks_attempt_in_progress_and_best_score(harness_root, capsys):
    paths = get_paths()
    save_attempt(paths, Attempt("00", "2026-10-21T14:00:00+00:00", 30))
    append_history(paths, {"exercise_id": "00", "score_pct": 40.0})
    assert main(["list"]) == 0
    assert "best: 40.0%  IN PROGRESS" in capsys.readouterr().out
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_foundation.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'harnesslib.system'` (or `harnesslib.cli`)

- [ ] **Step 6: Implement `config.py`**

`harnesslib/config.py`:
```python
"""Project paths, exercise metadata, and JSON helpers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class HarnessError(Exception):
    """A problem the user can fix. The CLI prints it and exits with code 1."""


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def exercises(self) -> Path:
        return self.root / "exercises"

    @property
    def grader(self) -> Path:
        return self.root / ".grader"

    @property
    def workspace(self) -> Path:
        return self.root / "workspace"

    @property
    def state(self) -> Path:
        return self.root / ".state"

    @property
    def attempt_file(self) -> Path:
        return self.state / "attempt.json"

    @property
    def history_file(self) -> Path:
        return self.state / "history.json"

    @property
    def venv_python(self) -> Path:
        override = os.environ.get("HARNESS_PYTHON")
        if override:
            return Path(override)
        if os.name == "nt":
            return self.root / ".venv" / "Scripts" / "python.exe"
        return self.root / ".venv" / "bin" / "python"


def get_paths() -> Paths:
    override = os.environ.get("HARNESS_ROOT")
    root = Path(override) if override else Path(__file__).resolve().parent.parent
    return Paths(root.resolve())


@dataclass(frozen=True)
class Exercise:
    id: str
    title: str
    time_limit_minutes: int
    setup_commands: tuple[tuple[str, ...], ...]
    check_command: tuple[str, ...] | None
    source_dir: Path
    grader_dir: Path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise HarnessError(f"{path} is not valid JSON ({error}). Fix or delete it and try again.") from error


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_exercises(paths: Paths) -> dict[str, Exercise]:
    exercises: dict[str, Exercise] = {}
    for meta in sorted(paths.exercises.glob("*/exercise.json")):
        data = read_json(meta, {})
        check = data.get("check_command")
        exercise = Exercise(
            id=str(data["id"]),
            title=data["title"],
            time_limit_minutes=int(data["time_limit_minutes"]),
            setup_commands=tuple(tuple(command) for command in data.get("setup_commands", [])),
            check_command=tuple(check) if check else None,
            source_dir=meta.parent,
            grader_dir=paths.grader / meta.parent.name,
        )
        exercises[exercise.id] = exercise
    return exercises


def get_exercise(paths: Paths, exercise_id: str) -> Exercise:
    exercises = load_exercises(paths)
    if exercise_id not in exercises:
        available = ", ".join(sorted(exercises)) or "(none)"
        raise HarnessError(f"Unknown exercise '{exercise_id}'. Available: {available}")
    return exercises[exercise_id]


def require_venv(paths: Paths) -> None:
    if not paths.venv_python.exists():
        raise HarnessError("Virtual environment not found. Run `python harness.py setup` first.")


def load_expected(exercise: Exercise) -> tuple[int, int]:
    path = exercise.grader_dir / "expected.json"
    data = read_json(path, None)
    if data is None:
        raise HarnessError(f"Missing {path}")
    return int(data["visible"]), int(data["hidden"])
```

- [ ] **Step 7: Implement `state.py`**

`harnesslib/state.py`:
```python
"""The current attempt and submission history, stored as JSON in .state/."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import Paths, read_json, write_json


@dataclass(frozen=True)
class Attempt:
    exercise_id: str
    started_at: str
    time_limit_minutes: int


def load_attempt(paths: Paths) -> Attempt | None:
    data = read_json(paths.attempt_file, None)
    return Attempt(**data) if data else None


def save_attempt(paths: Paths, attempt: Attempt) -> None:
    write_json(paths.attempt_file, asdict(attempt))


def clear_attempt(paths: Paths) -> None:
    paths.attempt_file.unlink(missing_ok=True)


def load_history(paths: Paths) -> list[dict]:
    return read_json(paths.history_file, [])


def append_history(paths: Paths, entry: dict) -> None:
    history = load_history(paths)
    history.append(entry)
    write_json(paths.history_file, history)


def best_score(history: list[dict], exercise_id: str) -> float | None:
    scores = [entry["score_pct"] for entry in history if entry["exercise_id"] == exercise_id]
    return max(scores) if scores else None
```

- [ ] **Step 8: Implement `system.py`**

`harnesslib/system.py`:
```python
"""Filesystem and subprocess helpers shared by the commands."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .config import HarnessError, Paths


def child_env() -> dict[str, str]:
    """Environment for child Pythons: force UTF-8 so non-ASCII output survives Windows pipes."""
    return {**os.environ, "PYTHONUTF8": "1"}


def _clear_readonly_and_retry(func, path, _exc) -> None:
    # git marks object files read-only, which makes rmtree fail on Windows.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    try:
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_clear_readonly_and_retry)
        else:
            shutil.rmtree(path, onerror=_clear_readonly_and_retry)
    except PermissionError as error:
        in_use = error.filename or path
        raise HarnessError(
            f"Could not delete {path}: {in_use} is in use. "
            "Close VS Code windows and terminals that use it, then try again."
        ) from error


def run_python(paths: Paths, args: Sequence[str], cwd: Path, timeout: float | None = None) -> tuple[bool, str]:
    proc = subprocess.run(
        [str(paths.venv_python), *args],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=child_env(),
        timeout=timeout,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def run_git(args: list[str], cwd: Path) -> None:
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as error:
        raise HarnessError("git is not installed or not on PATH.") from error
    if proc.returncode != 0:
        raise HarnessError(f"git {' '.join(args)} failed:\n{proc.stdout}{proc.stderr}")
```

- [ ] **Step 9: Implement `commands.py` (`confirm` and `list`), `cli.py` and `harness.py`**

`harnesslib/commands.py`:
```python
"""Implementations of the harness CLI commands."""
from __future__ import annotations

from .config import Paths, load_exercises
from .state import best_score, load_attempt, load_history


def confirm(question: str) -> bool:
    try:
        answer = input(f"{question} [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


def cmd_list(paths: Paths) -> int:
    exercises = load_exercises(paths)
    if not exercises:
        print("No exercises found in exercises/.")
        return 0
    history = load_history(paths)
    attempt = load_attempt(paths)
    for exercise in exercises.values():
        best = best_score(history, exercise.id)
        best_text = "—" if best is None else f"{best:.1f}%"
        marker = "  IN PROGRESS" if attempt and attempt.exercise_id == exercise.id else ""
        print(f"{exercise.id}  {exercise.title}  ({exercise.time_limit_minutes}m)  best: {best_text}{marker}")
    return 0
```

`harnesslib/cli.py`:
```python
"""Argument parsing and top-level error handling for harness.py."""
from __future__ import annotations

import argparse
import sys
import traceback

from . import commands
from .config import HarnessError, Paths, get_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness.py", description="HackerRank-style mock interview runner.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="create .venv and install the pinned packages")
    sub.add_parser("list", help="show exercises and your best scores")
    start = sub.add_parser("start", help="copy an exercise into workspace/ and start the clock")
    start.add_argument("exercise_id")
    start.add_argument("--force", action="store_true", help="overwrite an attempt in progress without asking")
    start.add_argument("--no-open", action="store_true", help="don't open VS Code")
    sub.add_parser("time", help="show how much time is left")
    sub.add_parser("submit", help="grade your workspace with the visible and hidden tests")
    reset = sub.add_parser("reset", help="delete workspace/ and the current attempt")
    reset.add_argument("--force", action="store_true", help="don't ask for confirmation")
    answers = sub.add_parser("answers", help="show the answer key (after at least one submit)")
    answers.add_argument("exercise_id")
    verify = sub.add_parser("verify", help="maintainers: check an exercise is fair (numbers only)")
    verify.add_argument("exercise_id")
    return parser


def _dispatch(args: argparse.Namespace, paths: Paths) -> int:
    if args.command == "setup":
        return commands.cmd_setup(paths)
    if args.command == "list":
        return commands.cmd_list(paths)
    if args.command == "start":
        return commands.cmd_start(paths, args.exercise_id, force=args.force, no_open=args.no_open)
    if args.command == "time":
        return commands.cmd_time(paths)
    if args.command == "submit":
        return commands.cmd_submit(paths)
    if args.command == "reset":
        return commands.cmd_reset(paths, force=args.force)
    if args.command == "answers":
        return commands.cmd_answers(paths, args.exercise_id)
    if args.command == "verify":
        return commands.cmd_verify(paths, args.exercise_id)
    raise HarnessError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args, get_paths())
    except HarnessError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception:
        traceback.print_exc()
        return 2
```

`harness.py`:
```python
"""HackerRank-style mock interview runner. Run `python harness.py --help`."""
import sys

from harnesslib.cli import main

if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
    sys.exit(main())
```

- [ ] **Step 10: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all of `test_clock.py`, `test_results.py` and `test_foundation.py` pass (`23 passed`).

- [ ] **Step 11: Smoke-test the real CLI**

Run: `.venv/Scripts/python harness.py list`
Expected: `No exercises found in exercises/.`

- [ ] **Step 12: Commit**

```bash
git add harness.py harnesslib harness_tests
git commit -F - <<'EOF'
Add config, state, system helpers, CLI skeleton and list command

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 4: Workspace creation with `start`, `time` and `reset`

**Files:**
- Create: `harnesslib/workspace.py`
- Modify: `harnesslib/commands.py` (replace the import block, then append functions)
- Test: `harness_tests/test_start.py`

**Interfaces:**
- Consumes: `config.*`, `state.*`, `system.remove_tree/run_git/run_python`, `clock.*`, `commands.confirm`.
- Produces:
  - `harnesslib.workspace`: `WORKSPACE_GITIGNORE: str`, `create_workspace(paths, exercise) -> None`, `write_vscode_config(paths) -> None`.
  - `harnesslib.commands`: `cmd_start(paths, exercise_id, force: bool, no_open: bool) -> int`, `cmd_time(paths) -> int`, `cmd_reset(paths, force: bool) -> int`, `_require_attempt(paths) -> Attempt`.

- [ ] **Step 1: Write the failing tests**

`harness_tests/test_start.py`:
```python
import json
import subprocess
import sys
from pathlib import Path

from harnesslib import system
from harnesslib.cli import main


def test_start_copies_exercise_and_records_attempt(harness_root):
    assert main(["start", "00", "--no-open"]) == 0
    workspace = harness_root / "workspace"
    assert (workspace / "calc.py").exists()
    assert (workspace / "tests" / "test_calc.py").exists()
    attempt = json.loads((harness_root / ".state" / "attempt.json").read_text(encoding="utf-8"))
    assert attempt["exercise_id"] == "00"
    assert attempt["time_limit_minutes"] == 30


def test_start_never_copies_grader_files(harness_root):
    main(["start", "00", "--no-open"])
    names = {p.name for p in (harness_root / "workspace").rglob("*")}
    assert "test_hidden_calc.py" not in names
    assert "ANSWER_KEY.md" not in names


def test_start_writes_vscode_config_for_venv(harness_root):
    main(["start", "00", "--no-open"])
    vscode = harness_root / "workspace" / ".vscode"
    settings = json.loads((vscode / "settings.json").read_text(encoding="utf-8"))
    assert settings["python.defaultInterpreterPath"] == str(Path(sys.executable))
    tasks = json.loads((vscode / "tasks.json").read_text(encoding="utf-8"))["tasks"]
    assert [task["label"] for task in tasks] == ["Run Tests", "Submit", "Time Left"]
    assert tasks[0]["group"] == {"kind": "test", "isDefault": True}


def test_start_makes_clean_git_baseline(harness_root):
    main(["start", "00", "--no-open"])
    workspace = harness_root / "workspace"
    log = subprocess.run(["git", "log", "--oneline"], cwd=workspace, capture_output=True, text=True, check=True)
    assert "baseline" in log.stdout
    status = subprocess.run(["git", "status", "--porcelain"], cwd=workspace, capture_output=True, text=True, check=True)
    assert status.stdout.strip() == ""


def test_start_unknown_exercise_lists_available(harness_root, capsys):
    assert main(["start", "99", "--no-open"]) == 1
    assert "Available: 00" in capsys.readouterr().err


def test_start_requires_setup_first(harness_root, monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HARNESS_PYTHON", str(tmp_path / "missing" / "python.exe"))
    assert main(["start", "00", "--no-open"]) == 1
    assert "harness.py setup" in capsys.readouterr().err


def test_start_asks_before_overwriting_attempt(harness_root, monkeypatch):
    main(["start", "00", "--no-open"])
    marker = harness_root / "workspace" / "my_work.txt"
    marker.write_text("keep me", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["start", "00", "--no-open"]) == 1
    assert marker.exists()
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert main(["start", "00", "--no-open"]) == 0
    assert not marker.exists()


def test_start_force_skips_prompt(harness_root, monkeypatch):
    main(["start", "00", "--no-open"])

    def no_prompt(_prompt):
        raise AssertionError("start --force must not prompt")

    monkeypatch.setattr("builtins.input", no_prompt)
    assert main(["start", "00", "--no-open", "--force"]) == 0


def test_time_shows_time_left(harness_root, capsys):
    main(["start", "00", "--no-open"])
    capsys.readouterr()
    assert main(["time"]) == 0
    out = capsys.readouterr().out
    assert "/ 30m" in out
    assert "left" in out


def test_time_shows_overtime(harness_root, capsys, backdate):
    main(["start", "00", "--no-open"])
    backdate(31)
    capsys.readouterr()
    assert main(["time"]) == 0
    assert "OVERTIME by 1m" in capsys.readouterr().out


def test_time_without_attempt(harness_root, capsys):
    assert main(["time"]) == 1
    assert "No attempt in progress" in capsys.readouterr().err


def test_reset_clears_workspace_and_attempt(harness_root):
    main(["start", "00", "--no-open"])
    assert main(["reset", "--force"]) == 0
    assert not (harness_root / "workspace").exists()
    assert not (harness_root / ".state" / "attempt.json").exists()


def test_reset_cancelled_keeps_workspace(harness_root, monkeypatch):
    main(["start", "00", "--no-open"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["reset"]) == 1
    assert (harness_root / "workspace").exists()


def test_reset_reports_locked_files_clearly(harness_root, monkeypatch, capsys):
    main(["start", "00", "--no-open"])

    def locked(*_args, **_kwargs):
        raise PermissionError(13, "The process cannot access the file", "calc.py")

    monkeypatch.setattr(system.shutil, "rmtree", locked)
    assert main(["reset", "--force"]) == 1
    assert "Close VS Code" in capsys.readouterr().err
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_start.py -v`
Expected: the tests FAIL. `main` returns `2`, with `AttributeError: module 'harnesslib.commands' has no attribute 'cmd_start'` printed in the traceback.

- [ ] **Step 3: Implement `workspace.py`**

`harnesslib/workspace.py`:
```python
"""Create the candidate's workspace: a fresh copy of the exercise with VS Code and git set up."""
from __future__ import annotations

import json
import shutil

from .config import Exercise, Paths
from .system import remove_tree, run_git

WORKSPACE_GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\ndb.sqlite3\n.vscode/\n"
_COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "db.sqlite3")


def create_workspace(paths: Paths, exercise: Exercise) -> None:
    remove_tree(paths.workspace)
    shutil.copytree(exercise.source_dir, paths.workspace, ignore=_COPY_IGNORE)
    write_vscode_config(paths)
    (paths.workspace / ".gitignore").write_text(WORKSPACE_GITIGNORE, encoding="utf-8")
    run_git(["init", "-q"], paths.workspace)
    run_git(["add", "-A"], paths.workspace)
    run_git(
        ["-c", "user.name=practice", "-c", "user.email=practice@localhost", "commit", "-q", "-m", "baseline"],
        paths.workspace,
    )


def write_vscode_config(paths: Paths) -> None:
    python = str(paths.venv_python)
    harness = str(paths.root / "harness.py")
    tasks = [
        _task("Run Tests", python, ["-m", "pytest", "tests", "-q"], group={"kind": "test", "isDefault": True}),
        _task("Submit", python, [harness, "submit"]),
        _task("Time Left", python, [harness, "time"]),
    ]
    if (paths.workspace / "manage.py").exists():
        tasks.append(_task("Run Server", python, ["manage.py", "runserver"]))
    settings = {
        "python.defaultInterpreterPath": python,
        "python.testing.pytestEnabled": True,
        "python.testing.unittestEnabled": False,
        "python.testing.pytestArgs": ["tests"],
    }
    vscode = paths.workspace / ".vscode"
    vscode.mkdir(parents=True, exist_ok=True)
    (vscode / "settings.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    (vscode / "tasks.json").write_text(json.dumps({"version": "2.0.0", "tasks": tasks}, indent=2) + "\n", encoding="utf-8")


def _task(label: str, command: str, args: list[str], group: dict | None = None) -> dict:
    task = {
        "label": label,
        "type": "process",
        "command": command,
        "args": args,
        "options": {"cwd": "${workspaceFolder}"},
        "problemMatcher": [],
    }
    if group is not None:
        task["group"] = group
    return task
```

- [ ] **Step 4: Extend `commands.py`**

Replace the import block at the top of `harnesslib/commands.py`. The current block:
```python
from __future__ import annotations

from .config import Paths, load_exercises
from .state import best_score, load_attempt, load_history
```
becomes:
```python
from __future__ import annotations

import shutil
import subprocess

from . import clock
from .config import HarnessError, Paths, get_exercise, load_exercises, require_venv
from .state import Attempt, best_score, clear_attempt, load_attempt, load_history, save_attempt
from .system import remove_tree, run_python
from .workspace import create_workspace
```

Append to `harnesslib/commands.py`:
```python


def _require_attempt(paths: Paths) -> Attempt:
    attempt = load_attempt(paths)
    if attempt is None or not paths.workspace.exists():
        raise HarnessError("No attempt in progress. Start one with `python harness.py start <id>`.")
    return attempt


def _open_in_vscode(paths: Paths) -> None:
    code = shutil.which("code")
    if code is None:
        print(f"VS Code's `code` command was not found. Open this folder yourself: {paths.workspace}")
        return
    subprocess.Popen([code, str(paths.workspace)])


def cmd_start(paths: Paths, exercise_id: str, force: bool, no_open: bool) -> int:
    require_venv(paths)
    exercise = get_exercise(paths, exercise_id)
    current = load_attempt(paths)
    if current and paths.workspace.exists() and not force:
        if not confirm(f"Attempt for {current.exercise_id} in progress. Overwrite?"):
            print("Kept your current attempt.")
            return 1
    create_workspace(paths, exercise)
    for command in exercise.setup_commands:
        ok, output = run_python(paths, command, paths.workspace)
        if not ok:
            raise HarnessError(f"Setup command failed: {' '.join(command)}\n{output}")
    save_attempt(paths, Attempt(exercise.id, clock.to_iso(clock.now_utc()), exercise.time_limit_minutes))
    print(f"Started {exercise.id} · {exercise.title}")
    print(f"Time limit: {exercise.time_limit_minutes}m. The clock is running.")
    print(f"Workspace: {paths.workspace}")
    print("Read README.md first, then run the visible tests: pytest tests -q")
    if not no_open:
        _open_in_vscode(paths)
    return 0


def cmd_time(paths: Paths) -> int:
    attempt = _require_attempt(paths)
    elapsed = clock.elapsed_seconds(attempt.started_at, clock.now_utc())
    limit_seconds = attempt.time_limit_minutes * 60
    line = f"Elapsed {clock.format_duration(elapsed)} / {attempt.time_limit_minutes}m"
    if clock.is_overtime(elapsed, attempt.time_limit_minutes):
        print(f"{line}  OVERTIME by {clock.format_duration(elapsed - limit_seconds)}")
    else:
        print(f"{line}  ({clock.format_duration(limit_seconds - elapsed)} left)")
    return 0


def cmd_reset(paths: Paths, force: bool) -> int:
    if not paths.workspace.exists() and load_attempt(paths) is None:
        print("Nothing to reset.")
        return 0
    if not force and not confirm("Delete workspace/ and your current attempt? Your history is kept."):
        print("Reset cancelled.")
        return 1
    remove_tree(paths.workspace)
    clear_attempt(paths)
    print("Workspace cleared.")
    return 0
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass (`37 passed`).

- [ ] **Step 6: Commit**

```bash
git add harnesslib harness_tests/test_start.py
git commit -F - <<'EOF'
Add start, time and reset commands with VS Code and git setup

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 5: Grading with `submit` and `answers`

**Files:**
- Create: `harnesslib/grading.py`
- Modify: `harnesslib/commands.py` (replace the import block, then append functions)
- Test: `harness_tests/test_submit.py`

**Interfaces:**
- Consumes: `config.Exercise/HarnessError/Paths/load_expected/get_exercise/require_venv/load_exercises`, `results.parse_junit/score_cases/CaseResult/Score`, `system.child_env/remove_tree/run_python`, `state.append_history/load_history`, `commands._require_attempt/confirm`.
- Produces:
  - `harnesslib.grading`:
    - `PYTEST_TIMEOUT_SECONDS = 120` (tests monkeypatch it)
    - `GradeResult(score: Score, cases: tuple[CaseResult, ...], timed_out: bool, ran_any: bool, check_output: str | None)`
    - `prepare_sandbox(source: Path, exercise, sandbox: Path) -> None`
    - `run_tests(paths, exercise, sandbox: Path) -> GradeResult`
    - `grade_directory(paths, exercise, source: Path) -> GradeResult`
  - `harnesslib.commands`: `cmd_submit(paths) -> int`, `cmd_answers(paths, exercise_id) -> int`.

- [ ] **Step 1: Write the failing tests**

`harness_tests/test_submit.py`:
```python
import json

from harnesslib import grading
from harnesslib.cli import main

FIXED_CALC = '''def add(a, b):
    return a + b


def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def clamp(value, low, high):
    return max(low, min(value, high))
'''
SYNTAX_ERROR_CALC = "def add(a, b)\n    return a + b\n"
HANGING_CALC = FIXED_CALC.replace("    return a + b\n", "    while True:\n        pass\n", 1)


def start(capsys):
    assert main(["start", "00", "--no-open"]) == 0
    capsys.readouterr()


def submit(capsys) -> str:
    assert main(["submit"]) == 0
    return capsys.readouterr().out


def history(root):
    return json.loads((root / ".state" / "history.json").read_text(encoding="utf-8"))


def test_submit_scores_starting_code(harness_root, capsys):
    start(capsys)
    out = submit(capsys)
    assert "00 · Sample calculator" in out
    assert "Visible  1/2   Hidden  1/3" in out
    assert "Score    2/5  (40.0%)" in out
    assert "tests.test_calc::test_average" in out
    entry = history(harness_root)[-1]
    assert entry["score_pct"] == 40.0
    assert (entry["visible_passed"], entry["visible_total"]) == (1, 2)
    assert (entry["hidden_passed"], entry["hidden_total"]) == (1, 3)
    assert entry["overtime"] is False


def test_submit_never_reveals_hidden_tests(harness_root, capsys):
    start(capsys)
    out = submit(capsys)
    for secret in ("test_hidden_calc", "test_average_single", "test_average_empty_list", "clamp"):
        assert secret not in out


def test_submit_full_marks_after_fixing(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(FIXED_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "Score    5/5  (100.0%)" in out
    assert "Failing visible tests" not in out


def test_editing_or_adding_tests_does_not_change_score(harness_root, capsys):
    start(capsys)
    workspace = harness_root / "workspace"
    (workspace / "tests" / "test_calc.py").unlink()
    (workspace / "tests" / "test_free_points.py").write_text("def test_free():\n    assert True\n", encoding="utf-8")
    (workspace / "test_extra.py").write_text("def test_extra():\n    assert True\n", encoding="utf-8")
    out = submit(capsys)
    assert "Score    2/5  (40.0%)" in out


def test_broken_code_scores_zero_and_explains(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(SYNTAX_ERROR_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "Score    0/5  (0.0%)" in out
    assert "No tests could run" in out
    assert "SyntaxError" in out


def test_hanging_code_times_out(harness_root, capsys, monkeypatch):
    monkeypatch.setattr(grading, "PYTEST_TIMEOUT_SECONDS", 5)
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(HANGING_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "timed out after 5s" in out
    assert "Score    0/5  (0.0%)" in out


def test_overtime_submit_is_flagged(harness_root, capsys, backdate):
    start(capsys)
    backdate(31)
    out = submit(capsys)
    assert "/ 30m  OVERTIME" in out
    assert history(harness_root)[-1]["overtime"] is True


def test_submit_without_attempt(harness_root, capsys):
    assert main(["submit"]) == 1
    assert "No attempt in progress" in capsys.readouterr().err


def test_answers_locked_until_first_submit(harness_root, capsys):
    assert main(["answers", "00"]) == 1
    assert "Submit exercise 00 at least once" in capsys.readouterr().err


def test_answers_after_submit_and_confirm(harness_root, capsys, monkeypatch):
    start(capsys)
    submit(capsys)
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert main(["answers", "00"]) == 0
    out = capsys.readouterr().out
    assert "Sample answer key" in out
    assert "fix_01.patch" in out


def test_answers_declined_stays_locked(harness_root, capsys, monkeypatch):
    start(capsys)
    submit(capsys)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["answers", "00"]) == 1
    assert "Sample answer key" not in capsys.readouterr().out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_submit.py -v`
Expected: collection error `ImportError: cannot import name 'grading' from 'harnesslib'`

- [ ] **Step 3: Implement `grading.py`**

`harnesslib/grading.py`:
```python
"""Grade a directory: copy it to a sandbox, add the original and hidden tests, run pytest."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .config import Exercise, HarnessError, Paths, load_expected
from .results import CaseResult, Score, parse_junit, score_cases
from .system import child_env, remove_tree, run_python

PYTEST_TIMEOUT_SECONDS = 120
REPORT_NAME = ".harness-report.xml"
_SANDBOX_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "db.sqlite3", ".vscode", ".pytest_cache")
_TESTS_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache")


@dataclass(frozen=True)
class GradeResult:
    score: Score
    cases: tuple[CaseResult, ...]
    timed_out: bool
    ran_any: bool
    check_output: str | None


def prepare_sandbox(source: Path, exercise: Exercise, sandbox: Path) -> None:
    hidden = exercise.grader_dir / "hidden_tests"
    if not hidden.is_dir():
        raise HarnessError(f"Missing hidden tests: {hidden}")
    shutil.copytree(source, sandbox, ignore=_SANDBOX_IGNORE)
    # Grade against the original visible tests, never the candidate's edited copy.
    tests = sandbox / "tests"
    remove_tree(tests)
    shutil.copytree(exercise.source_dir / "tests", tests, ignore=_TESTS_IGNORE)
    shutil.copytree(hidden, tests / "hidden", ignore=_TESTS_IGNORE)


def _read_report(report: Path) -> tuple[CaseResult, ...]:
    if not report.exists():
        return ()
    try:
        return tuple(parse_junit(report))
    except ET.ParseError:
        return ()


def run_tests(paths: Paths, exercise: Exercise, sandbox: Path) -> GradeResult:
    expected_visible, expected_hidden = load_expected(exercise)
    report = sandbox / REPORT_NAME
    command = [
        str(paths.venv_python), "-m", "pytest", "tests", "-q",
        "-p", "no:cacheprovider", "--continue-on-collection-errors", f"--junitxml={report}",
    ]
    try:
        subprocess.run(command, cwd=sandbox, capture_output=True, env=child_env(), timeout=PYTEST_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return GradeResult(score_cases((), expected_visible, expected_hidden), (), True, False, None)
    cases = _read_report(report)
    ran_any = any(case.is_test for case in cases)
    check_output = None
    if not ran_any and exercise.check_command:
        _ok, check_output = run_python(paths, exercise.check_command, sandbox)
    return GradeResult(score_cases(cases, expected_visible, expected_hidden), cases, False, ran_any, check_output)


def grade_directory(paths: Paths, exercise: Exercise, source: Path) -> GradeResult:
    with tempfile.TemporaryDirectory(prefix="harness-", ignore_cleanup_errors=True) as tmp:
        sandbox = Path(tmp) / "app"
        prepare_sandbox(source, exercise, sandbox)
        return run_tests(paths, exercise, sandbox)
```

- [ ] **Step 4: Extend `commands.py`**

Replace the import block at the top of `harnesslib/commands.py`. The current block:
```python
from __future__ import annotations

import shutil
import subprocess

from . import clock
from .config import HarnessError, Paths, get_exercise, load_exercises, require_venv
from .state import Attempt, best_score, clear_attempt, load_attempt, load_history, save_attempt
from .system import remove_tree, run_python
from .workspace import create_workspace
```
becomes:
```python
from __future__ import annotations

import shutil
import subprocess

from . import clock, grading
from .config import HarnessError, Paths, get_exercise, load_exercises, require_venv
from .state import Attempt, append_history, best_score, clear_attempt, load_attempt, load_history, save_attempt
from .system import remove_tree, run_python
from .workspace import create_workspace
```

Append to `harnesslib/commands.py`:
```python


def cmd_submit(paths: Paths) -> int:
    require_venv(paths)
    attempt = _require_attempt(paths)
    exercise = get_exercise(paths, attempt.exercise_id)
    print("Grading your workspace with the visible and hidden tests ...")
    result = grading.grade_directory(paths, exercise, paths.workspace)
    elapsed = clock.elapsed_seconds(attempt.started_at, clock.now_utc())
    overtime = clock.is_overtime(elapsed, attempt.time_limit_minutes)
    score = result.score

    print()
    print(f"{exercise.id} · {exercise.title}")
    print(f"Visible  {score.visible_passed}/{score.visible_total}   Hidden  {score.hidden_passed}/{score.hidden_total}")
    print(f"Score    {score.passed}/{score.total}  ({score.percent:.1f}%)")
    time_line = f"Time     {clock.format_duration(elapsed)} / {attempt.time_limit_minutes}m"
    print(time_line + ("  OVERTIME" if overtime else ""))

    if result.timed_out:
        print(f"\nTests timed out after {grading.PYTEST_TIMEOUT_SECONDS}s (infinite loop?). Score recorded as 0.")
    elif not result.ran_any:
        print("\nNo tests could run, so the score is 0. Your app probably fails to start or import.")
        if result.check_output:
            print(result.check_output.rstrip())
        print("Run `pytest tests -q` in your workspace to see the errors.")
    else:
        if score.failed_visible:
            print("\nFailing visible tests:")
            for test_id in score.failed_visible:
                print(f"  - {test_id}")
        if score.load_errors:
            print(f"\n{score.load_errors} test file(s) failed to load. Run `pytest tests -q` in your workspace to see why.")

    append_history(
        paths,
        {
            "exercise_id": exercise.id,
            "submitted_at": clock.to_iso(clock.now_utc()),
            "visible_passed": score.visible_passed,
            "visible_total": score.visible_total,
            "hidden_passed": score.hidden_passed,
            "hidden_total": score.hidden_total,
            "score_pct": score.percent,
            "elapsed_seconds": elapsed,
            "overtime": overtime,
        },
    )
    return 0


def cmd_answers(paths: Paths, exercise_id: str) -> int:
    exercise = get_exercise(paths, exercise_id)
    if not any(entry["exercise_id"] == exercise.id for entry in load_history(paths)):
        raise HarnessError(f"Submit exercise {exercise.id} at least once before viewing the answers.")
    if not confirm("This shows every bug and fix. Continue?"):
        print("Answers stay locked.")
        return 1
    print((exercise.grader_dir / "ANSWER_KEY.md").read_text(encoding="utf-8"))
    fixes = sorted((exercise.grader_dir / "fixes").glob("*.patch"))
    if fixes:
        print("Fix patches (compare them with `git diff` in your workspace):")
        for patch in fixes:
            print(f"  {patch}")
    return 0
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass (`48 passed`). The timeout test takes about 5 seconds.

- [ ] **Step 6: Commit**

```bash
git add harnesslib harness_tests/test_submit.py
git commit -F - <<'EOF'
Add sandboxed grading, submit and answers commands

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 6: `verify` (maintainer fairness checks)

**Files:**
- Create: `harnesslib/verify.py`
- Modify: `harnesslib/commands.py` (one import line, then append a function)
- Test: `harness_tests/test_verify.py`

**Interfaces:**
- Consumes: `grading.grade_directory/GradeResult`, `config.load_expected/HarnessError`, `system.run_python`.
- Produces:
  - `harnesslib.verify`: `Check(name: str, passed: bool, detail: str)`, `compare_outcomes(before: dict[str, bool], after: dict[str, bool]) -> tuple[set[str], set[str]]`, `run_checks(paths, exercise) -> list[Check]`, `print_checks(exercise, checks) -> bool`.
  - `harnesslib.commands`: `cmd_verify(paths, exercise_id) -> int`.

- [ ] **Step 1: Write the failing tests**

`harness_tests/test_verify.py`:
```python
import shutil

from harnesslib.cli import main
from harnesslib.verify import compare_outcomes


def grader(root):
    return root / ".grader" / "00-sample"


def test_compare_outcomes_finds_fixed_and_broken():
    before = {"a": False, "b": True, "c": False}
    after = {"a": True, "b": False, "c": False, "d": True}
    fixed, broken = compare_outcomes(before, after)
    assert fixed == {"a", "d"}
    assert broken == {"b"}


def test_verify_passes_for_fair_sample(harness_root, capsys):
    assert main(["verify", "00"]) == 0
    out = capsys.readouterr().out
    assert "[PASS] clean start" in out
    assert "40.0% (2/5)" in out
    assert "[PASS] full solution" in out
    assert "[PASS] fix_01" in out
    assert "fixes 2 test(s) · breaks 0" in out
    assert "[PASS] fix_02" in out
    assert "[PASS] hidden-only bug" in out
    assert "[PASS] test counts" in out
    assert "Result: 6/6 checks passed" in out


def test_verify_fails_without_hidden_only_bug(harness_root, capsys):
    fixes = grader(harness_root) / "fixes"
    shutil.copyfile(fixes / "fix_01.patch", fixes / "fix_02.patch")
    assert main(["verify", "00"]) == 1
    assert "[FAIL] hidden-only bug" in capsys.readouterr().out


def test_verify_fails_when_counts_are_wrong(harness_root, capsys):
    (grader(harness_root) / "expected.json").write_text('{"visible": 3, "hidden": 3}', encoding="utf-8")
    assert main(["verify", "00"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] test counts" in out
    assert "visible 2/3" in out


def test_verify_reports_patch_that_does_not_apply(harness_root, capsys):
    (grader(harness_root) / "fixes" / "fix_02.patch").write_text("not a patch\n", encoding="utf-8")
    assert main(["verify", "00"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] fix_02" in out
    assert "patch does not apply" in out
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_verify.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'harnesslib.verify'`

- [ ] **Step 3: Implement `verify.py`**

`harnesslib/verify.py`:
```python
"""`verify`: maintainer checks that an exercise is fair. Prints numbers only, never test names."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import Exercise, HarnessError, Paths, load_expected
from .grading import GradeResult, grade_directory
from .system import run_python

TARGET_LOW, TARGET_HIGH = 30.0, 50.0
_COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "db.sqlite3")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def compare_outcomes(before: dict[str, bool], after: dict[str, bool]) -> tuple[set[str], set[str]]:
    fixed = {test for test, ok in after.items() if ok and not before.get(test, False)}
    broken = {test for test, ok in before.items() if ok and not after.get(test, False)}
    return fixed, broken


def _outcomes(result: GradeResult) -> dict[str, bool]:
    return {case.test_id: case.passed for case in result.cases if case.is_test}


def _fresh_copy(exercise: Exercise, tmp: str) -> Path:
    copy = Path(tmp) / "app"
    shutil.copytree(exercise.source_dir, copy, ignore=_COPY_IGNORE)
    return copy


def _apply_patch(patch: Path, target: Path) -> bool:
    proc = subprocess.run(["git", "apply", "--whitespace=nowarn", str(patch)], cwd=target, capture_output=True)
    return proc.returncode == 0


def _grade_with_patch(paths: Paths, exercise: Exercise, patch: Path | None) -> GradeResult | None:
    with tempfile.TemporaryDirectory(prefix="harness-verify-", ignore_cleanup_errors=True) as tmp:
        copy = _fresh_copy(exercise, tmp)
        if patch is not None and not _apply_patch(patch, copy):
            return None
        return grade_directory(paths, exercise, copy)


def _setup_succeeds(paths: Paths, exercise: Exercise) -> bool:
    commands = ([exercise.check_command] if exercise.check_command else []) + list(exercise.setup_commands)
    with tempfile.TemporaryDirectory(prefix="harness-verify-", ignore_cleanup_errors=True) as tmp:
        copy = _fresh_copy(exercise, tmp)
        return all(run_python(paths, command, copy)[0] for command in commands)


def run_checks(paths: Paths, exercise: Exercise) -> list[Check]:
    fixes = sorted((exercise.grader_dir / "fixes").glob("fix_*.patch"))
    solution = exercise.grader_dir / "solution.patch"
    if not solution.exists() or not fixes:
        raise HarnessError(f"{exercise.grader_dir} needs solution.patch and fixes/fix_*.patch")

    checks: list[Check] = []
    baseline = _grade_with_patch(paths, exercise, None)
    setup_ok = _setup_succeeds(paths, exercise)
    pct = baseline.score.percent
    checks.append(Check(
        "clean start",
        setup_ok and TARGET_LOW <= pct <= TARGET_HIGH,
        f"setup {'ok' if setup_ok else 'FAILED'} · score {pct:.1f}% "
        f"({baseline.score.passed}/{baseline.score.total}) · target 30–50%",
    ))

    solved = _grade_with_patch(paths, exercise, solution)
    if solved is None:
        checks.append(Check("full solution", False, "patch does not apply"))
    else:
        checks.append(Check(
            "full solution",
            solved.score.percent == 100.0,
            f"{solved.score.percent:.1f}% ({solved.score.passed}/{solved.score.total})",
        ))

    before = _outcomes(baseline)
    hidden_ids = {case.test_id for case in baseline.cases if case.hidden}
    hidden_only = 0
    for patch in fixes:
        result = _grade_with_patch(paths, exercise, patch)
        if result is None:
            checks.append(Check(patch.stem, False, "patch does not apply"))
            continue
        fixed, broken = compare_outcomes(before, _outcomes(result))
        checks.append(Check(patch.stem, bool(fixed) and not broken, f"fixes {len(fixed)} test(s) · breaks {len(broken)}"))
        if fixed and fixed <= hidden_ids:
            hidden_only += 1
    checks.append(Check("hidden-only bug", hidden_only >= 1, f"{hidden_only} fix(es) flip only hidden tests"))

    expected_visible, expected_hidden = load_expected(exercise)
    visible_found = sum(1 for case in baseline.cases if case.is_test and not case.hidden)
    hidden_found = sum(1 for case in baseline.cases if case.is_test and case.hidden)
    checks.append(Check(
        "test counts",
        (visible_found, hidden_found) == (expected_visible, expected_hidden) and baseline.score.load_errors == 0,
        f"visible {visible_found}/{expected_visible} · hidden {hidden_found}/{expected_hidden}",
    ))
    return checks


def print_checks(exercise: Exercise, checks: list[Check]) -> bool:
    print(f"verify {exercise.id}")
    width = max(len(check.name) for check in checks)
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.name.ljust(width)}  {check.detail}")
    passed = sum(check.passed for check in checks)
    print(f"Result: {passed}/{len(checks)} checks passed")
    return passed == len(checks)
```

- [ ] **Step 4: Extend `commands.py`**

In `harnesslib/commands.py`, add this line directly after `from .system import remove_tree, run_python`:
```python
from .verify import print_checks, run_checks
```

Append to `harnesslib/commands.py`:
```python


def cmd_verify(paths: Paths, exercise_id: str) -> int:
    require_venv(paths)
    exercise = get_exercise(paths, exercise_id)
    return 0 if print_checks(exercise, run_checks(paths, exercise)) else 1
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass (`53 passed`).

- [ ] **Step 6: Commit**

```bash
git add harnesslib harness_tests/test_verify.py
git commit -F - <<'EOF'
Add verify command for exercise fairness checks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 7: The `setup` command and the root README

**Files:**
- Modify: `harnesslib/commands.py` (one import line, then append a function)
- Create: `README.md`
- Test: `harness_tests/test_setup.py`

**Interfaces:**
- Consumes: `config.HarnessError/Paths`.
- Produces: `harnesslib.commands.cmd_setup(paths) -> int`.

- [ ] **Step 1: Write the failing tests**

`harness_tests/test_setup.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python -m pytest harness_tests/test_setup.py -v`
Expected: the tests FAIL. `main` returns `2` with `AttributeError: ... no attribute 'cmd_setup'`.

- [ ] **Step 3: Implement**

In `harnesslib/commands.py`, add `import sys` directly after `import subprocess`.

Append to `harnesslib/commands.py`:
```python


def cmd_setup(paths: Paths) -> int:
    venv_dir = paths.root / ".venv"
    if not paths.venv_python.exists():
        print(f"Creating virtual environment in {venv_dir} ...")
        if subprocess.run([sys.executable, "-m", "venv", str(venv_dir)]).returncode != 0:
            raise HarnessError("Could not create the virtual environment (see output above).")
    print("Installing packages from requirements.txt ...")
    install = [str(paths.venv_python), "-m", "pip", "install", "-r", str(paths.root / "requirements.txt")]
    if subprocess.run(install).returncode != 0:
        raise HarnessError("pip install failed (see output above).")
    print("Setup complete. Next: python harness.py list")
    return 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass (`56 passed`).

- [ ] **Step 5: Write the root README**

`README.md`:
````markdown
# Real-world tech interview practice

Free, open-source practice for "real-world" project questions, the kind of HackerRank-style
task used in many entry-level software engineering assessments. You get a small app with planted
bugs and one missing feature, then fix it against the clock. Your score comes from visible tests
plus hidden tests you never see.

> This project is not affiliated with or endorsed by HackerRank or any employer. Every exercise
> is original and is not a copy of any real assessment question.

## One-time setup

```
python harness.py setup
```

## The practice loop

Run these from this folder, not from `workspace/`.

| Step | Command |
|---|---|
| See exercises and your best scores | `python harness.py list` |
| Start an exercise (copies it into `workspace/`, starts the clock, opens VS Code) | `python harness.py start 01` |
| Check the time | `python harness.py time` |
| Grade your work with visible and hidden tests | `python harness.py submit` |
| See the answer key (after at least one submit) | `python harness.py answers 01` |
| Throw your work away and start fresh | `python harness.py reset` |

Inside VS Code:

- **Read `README.md` first.** It is the spec. A bug is anywhere the app disagrees with it.
- **Run the visible tests:** `pytest tests -q` in the terminal, or **Terminal → Run Task → Run Tests**.
- **Submit or check the time** with the **Submit** and **Time Left** tasks, or with `python ../harness.py submit`.
- **Try the API by hand:** run `python manage.py runserver` (or the **Run Server** task) and open
  `http://127.0.0.1:8000/` for DRF's browsable API.
- **Review your changes** with `git diff` (your starting point is the `baseline` commit).

## How scoring works

- Score = tests passed ÷ total tests (visible + hidden), with every test counting the same.
- Grading uses the original tests. Editing or deleting tests in `workspace/` doesn't change your score.
- Hidden tests are reported as a count only, as on HackerRank.
- The timer doesn't cut you off. Submits after the limit are marked **OVERTIME** in your history.
- You can submit as often as you like. Every submit is logged in `.state/history.json`.

## Tips for HackerRank-style tasks

1. Read the whole README before you open any code. List every rule it states.
2. Run the visible tests, then group the failures by endpoint.
3. Reproduce a bug before you fix it, with a failing test or a request in the browsable API.
4. Fix one thing at a time, rerun the tests, and check `git diff`.
5. Hidden tests check the README's rules too. Test the edge cases the visible tests skip.
6. Submit early, then keep improving. Don't leave the missing feature for the last five minutes.

## Don't peek

`exercises/` holds the starting code and `.grader/` holds the hidden tests and answers. Both are
plain files, so it works on the honor system: practice in `workspace/` only, and open the answers
with `python harness.py answers <id>` after you submit.

## Contributing

New exercises, fixes and docs are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to set up a
dev environment, write an exercise, and check it with `python harness.py verify <id>`.

## License

Copyright (C) 2026 the Real-World Tech Interview Practice contributors.

Licensed under the [GNU Affero General Public License v3.0 or later](LICENSE). You may use,
share and modify this project. If you distribute a modified version, or let people use one over a
network (for example, as a hosted practice site), you must publish its source code under the same
license.
````

- [ ] **Step 6: Run the real `setup` and `list`**

Run: `python harness.py setup && python harness.py list`
Expected: pip reports the requirements as already satisfied, then `Setup complete. Next: python harness.py list`, then `No exercises found in exercises/.`

- [ ] **Step 7: Commit**

```bash
git add harnesslib/commands.py harness_tests/test_setup.py README.md
git commit -F - <<'EOF'
Add setup command and practice README

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 8: Open-source files (license, contributing guide, spoiler notice, CI)

**Files:**
- Create: `LICENSE`, `CONTRIBUTING.md`, `.grader/README.md`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `harness.py setup/verify` (Tasks 3–7) and the harness test suite.
- Produces: the files a public repo needs. CI runs the harness tests and `verify` for every exercise.

- [ ] **Step 1: Add the official AGPL-3.0 text**

Run: `curl -fsSL https://www.gnu.org/licenses/agpl-3.0.txt -o LICENSE && head -3 LICENSE && wc -l LICENSE`
Expected: the first lines contain `GNU AFFERO GENERAL PUBLIC LICENSE` and `Version 3, 19 November 2007`; about 660 lines. Do not edit the text. If the download fails, report BLOCKED. Don't write the license from memory.

- [ ] **Step 2: Write the spoiler notice**

`.grader/README.md`:
```markdown
# Spoilers ahead

This folder holds the hidden tests, answer keys and fixes for every exercise. Reading it before
you practice spoils the exercise, like reading the hidden test cases on HackerRank.

Practice first with `python harness.py start <id>`. After you submit, `python harness.py answers <id>`
shows the answer key.
```

- [ ] **Step 3: Write the contributing guide**

`CONTRIBUTING.md`:
````markdown
# Contributing

Thanks for helping people practice for real-world coding assessments. Contributions of every size
are welcome: bug reports, harness fixes, docs, and especially new exercises.

## Ground rules

- **Exercises must be original.** Never reproduce a real assessment question, including one you
  saw in your own interview. Those questions are usually confidential under the candidate
  agreement. Invent your own domain and bugs.
- **No spoilers outside `.grader/`.** Don't put hidden tests, answer keys or fixes in issue titles,
  pull request titles or descriptions, or discussions.
- **No affiliation claims.** This project is not affiliated with HackerRank or any employer. Don't
  add their logos or text copied from their sites.
- **License.** By contributing, you agree your contribution is licensed under the project's
  license, the GNU Affero General Public License v3.0 or later.

## Development setup

```
python harness.py setup
.venv/Scripts/python -m pytest      # Windows
.venv/bin/python -m pytest          # macOS / Linux
```

The harness (`harness.py` and `harnesslib/`) uses only the Python standard library and supports
Python 3.11+. Keep it that way. Every harness change needs tests in `harness_tests/` (write them
first), and CI must pass on Windows, macOS and Linux.

## Adding an exercise

An exercise is two folders:

```
exercises/<NN>-<slug>/   what the candidate gets: README.md, exercise.json, pytest.ini, app code, tests/
.grader/<NN>-<slug>/     hidden_tests/, expected.json, ANSWER_KEY.md, fixes/fix_NN.patch, solution.patch
```

Exercises currently need a pytest test suite. The reference stack is Django + Django REST
Framework. Supporting other test runners would be a welcome harness change.

### exercise.json

```json
{
  "id": "02",
  "title": "Library Loans API",
  "time_limit_minutes": 90,
  "setup_commands": [["manage.py", "migrate"], ["manage.py", "seed"]],
  "check_command": ["manage.py", "check"]
}
```

Each command runs as `<venv python> <args...>` inside the candidate's workspace. `setup_commands`
can be empty. `check_command` is optional; when no tests can run, `submit` shows its output.

### What makes a good exercise

- **The README is the whole spec:** every endpoint with its request and response examples,
  status codes and validation rules, plus one "Feature to implement" section. It never hints at
  the bugs.
- **Defects:** 5–6 planted bugs plus one missing feature.
  - Each bug breaks something the README states explicitly.
  - Use natural-looking code: no giveaway comments or suspicious names.
  - Bugs live in app code, never in tests, and no fix may depend on another.
  - Most bugs should be entry-level; 1–2 can be harder.
- **The app starts cleanly:** `check`, migrations and `seed` succeed. A bug may cause a 500 on a
  specific request, but not an import error.
- **Tests:**
  - 20–30 in total, about 60% visible (`tests/test_*.py`) and 40% hidden
    (`.grader/<NN>-<slug>/hidden_tests/test_hidden_*.py`, so basenames stay unique).
  - Every bug and the feature are covered by at least one test.
  - At least one bug is caught *only* by hidden tests.
  - Each test builds its own data; none rely on `seed`.
- **The starting score is 30–50%.**
- **Files use LF line endings.**

### Recommended method (it guarantees the patches apply)

1. In a scratch git repo, build the **correct** app with every test: visible tests in `tests/`,
   hidden tests in `tests/hidden/`. All tests pass. Commit `correct`.
2. Remove the feature and leave a stub that points to the README section. Commit.
3. Plant each bug in its own commit. Keep every planted change at least 7 lines away from the other
   planted changes in the same file.
4. From the scratch repo root, for each commit `C` after `correct`, run
   `git diff C C~1 > fix_NN.patch`. Then run `git diff HEAD <correct-sha> > solution.patch`.
5. Export the files:
   - `HEAD` without `tests/hidden/` goes to `exercises/<NN>-<slug>/`.
   - `tests/hidden/*` goes to `.grader/<NN>-<slug>/hidden_tests/`.
   - Write `expected.json` as `{"visible": V, "hidden": H}`, counting with `pytest --collect-only -q`.
   - Write `ANSWER_KEY.md`. For each fix, give its location, the symptom, the README rule it
     breaks, the tests that catch it, the fix, and the skill it tests.

### Check it

`python harness.py verify <NN>` must print `Result: N/N checks passed`. It prints only numbers and
`fix_NN` labels, so it's safe to paste into a pull request.

## Pull request checklist

- [ ] Harness tests pass locally.
- [ ] For exercises: `python harness.py verify <NN>` passes, and the exercise is original.
- [ ] No spoilers in the pull request title or description.
````

- [ ] **Step 4: Write the CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11", "3.13"]
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        shell: bash
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Set up the harness
        run: python harness.py setup
      - name: Harness tests
        run: |
          if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=.venv/Scripts/python; fi
          "$PY" -m pytest -q
      - name: Verify every exercise
        run: |
          ids=$(python -c "import glob, json; print(' '.join(json.load(open(p, encoding='utf-8'))['id'] for p in sorted(glob.glob('exercises/*/exercise.json'))))")
          for id in $ids; do python harness.py verify "$id"; done
```

- [ ] **Step 5: Run the CI steps locally**

Run each `run:` block from Step 4 in order in Git Bash: `python harness.py setup`, then the harness-tests block, then the verify block.
Expected: setup completes and the harness tests pass (`56 passed`). The verify block prints nothing, because no exercises exist yet, and exits 0.

- [ ] **Step 6: Commit**

```bash
git add LICENSE CONTRIBUTING.md .grader/README.md .github/workflows/ci.yml
git commit -F - <<'EOF'
Add AGPL-3.0 license, contributing guide, spoiler notice and CI

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```

---

### Task 9: Exercise 01, authored by a background agent (spoiler-safe)

This task contains no exercise code **on purpose**. The user asked not to see the bugs, so the
content is designed and written by a background agent, and the acceptance gate is
`harness.py verify 01` plus an end-to-end run. The main session follows the spoiler rule in
Global Constraints throughout.

**Files (written by the agent; the main session must not open them):**
- Create: `exercises/01-<slug>/` (README.md, exercise.json, pytest.ini, manage.py, the Django project package, the app package, tests/)
- Create: `.grader/01-<slug>/` (hidden_tests/, expected.json, ANSWER_KEY.md, fixes/fix_NN.patch, solution.patch)

**Interfaces:**
- Consumes: the finished harness (Tasks 1–8), especially `harness.py verify`, `start`, `submit` and `reset`, and the exercise rules in `CONTRIBUTING.md`.
- Produces: an exercise that passes `verify 01` with every check green.

- [ ] **Step 1: Dispatch the background agent**

Use the Agent tool with `subagent_type: "general-purpose"` and `run_in_background: true`, with exactly this prompt:

````text
You are building exercise 01 for a HackerRank-style practice harness in
the project root. The person practicing must not learn anything
about the exercise from your final message, so follow the REPORT rules at the end exactly.

Read first: docs/superpowers/specs/2026-10-21-django-mock-interview-design.md (sections 5, 6, 7, 9),
README.md, harnesslib/grading.py, harnesslib/verify.py. Don't modify harness.py, harnesslib/ or
harness_tests/. If a harness bug blocks you, stop and report only the harness file, line and symptom.

WHAT TO BUILD (all requirements from spec §5–§6 apply; summary):
- A Django 5.2 + DRF project using the pinned versions in requirements.txt and SQLite. One project
  package, one app, about 3 related models, serializers, views/viewsets, URLs and a small
  business-logic module. 600–900 lines of app code, not counting tests and migrations. 6–10
  endpoints, including list/detail/create/update, at least one query-parameter filter, and at least
  one computed field or business rule. Include migrations.
- Pick a realistic business domain the person would see in an enterprise interview. <slug> is a short
  lowercase-hyphenated name for it.
- This project is public and open source (AGPL-3.0-or-later). The exercise must be ORIGINAL. Don't base
  it on any real company's assessment question, and don't name real companies or products in it.
  Follow every rule in CONTRIBUTING.md's "Adding an exercise" section.
- A `seed` management command that is idempotent (clears and reloads realistic sample data).
- exercise.json: {"id": "01", "title": "<Domain> API", "time_limit_minutes": 90,
  "setup_commands": [["manage.py", "migrate"], ["manage.py", "seed"]],
  "check_command": ["manage.py", "check"]}
- pytest.ini: [pytest] with DJANGO_SETTINGS_MODULE = <project>.settings and python_files = test_*.py
- README.md: a HackerRank-style problem statement with an overview, the data model fields, every
  endpoint (method, path, request body, response example, status codes), validation rules, and a
  "Feature to implement" section for the missing feature. Add an "Environment" section covering
  `pytest tests -q`, `python manage.py runserver` and `python manage.py seed`. Never list or hint at
  bugs.
- 5–6 planted bugs plus 1 missing feature, following every rule in spec §5 ("Planted defects"). Each
  bug must contradict an explicit README statement. No giveaway comments or names. The app must pass
  `manage.py check`, `migrate` and `seed`. Bugs go in app code only. No fix may depend on another.
  Most are entry-level; 1–2 are harder.
- Tests: pytest-django with DRF's APIClient and @pytest.mark.django_db. Each test builds its own data.
  20–30 tests in total, about 60% visible in tests/test_*.py and 40% hidden. Hidden test files are
  named test_hidden_*.py so basenames stay unique. Every bug and the feature have at least one test.
  At least one bug is caught ONLY by hidden tests. The feature has visible and hidden tests. The
  starting score must be 30–50%.

METHOD (this guarantees the patches are correct):
1. Work in a scratch git repo outside the project (your scratchpad directory), e.g. <scratch>/ex01/.
   Put the visible tests in tests/ and the hidden tests in tests/hidden/.
2. Build the CORRECT app plus all tests first. `pytest tests -q` must pass 100%. Commit "correct".
3. Remove the feature (leave a stub with a TODO pointing at the README section, as HackerRank does).
   Commit "feature removed".
4. Plant each bug in its own commit ("bug 1", "bug 2", ...). Keep every planted change at least 7
   lines away from every other planted change in the same file, so each fix applies on its own.
5. Generate patches from the scratch repo root (paths must be relative to the exercise root):
   - for each commit C after "correct", in order: `git diff C C~1 > fix_NN.patch` (01, 02, ...)
   - `git diff HEAD <correct-sha> > solution.patch`
6. Export:
   - HEAD's files except tests/hidden/ go to exercises/01-<slug>/ (no __pycache__ or db.sqlite3)
   - tests/hidden/* goes to .grader/01-<slug>/hidden_tests/
   - the patches go to .grader/01-<slug>/fixes/ and .grader/01-<slug>/solution.patch
   - .grader/01-<slug>/expected.json = {"visible": V, "hidden": H}, counted with
     `pytest --collect-only -q` (V = test cases in tests/ excluding tests/hidden/; H = test cases in
     tests/hidden/)
   - .grader/01-<slug>/ANSWER_KEY.md: for each fix_NN, give the location (file and function), the
     symptom, the README rule it breaks, the tests that catch it (visible/hidden), the fix, and the
     skill it tests. Explain the feature's reference implementation too.
   All files use LF line endings.

ACCEPTANCE (all must hold before you finish):
A. From the project root: `.venv/Scripts/python harness.py verify 01` prints "Result: N/N checks
   passed". Iterate until it does.
B. `.venv/Scripts/python -m pytest` (the harness tests) still passes.
C. End-to-end in a COPY of the project, so the person's real history and workspace stay untouched.
   Run this in one PowerShell call from the project root:
     $e2e = Join-Path $env:TEMP "harness-e2e-01"
     if (Test-Path $e2e) { Remove-Item -Recurse -Force $e2e }
     New-Item -ItemType Directory $e2e | Out-Null
     Copy-Item -Recurse harness.py, harnesslib, exercises, .grader, requirements.txt $e2e
     $env:HARNESS_ROOT = $e2e
     $env:HARNESS_PYTHON = (Resolve-Path .venv\Scripts\python.exe).Path
     .venv\Scripts\python.exe harness.py start 01 --no-open --force
     .venv\Scripts\python.exe harness.py submit
     $patch = (Get-ChildItem "$e2e\.grader\01-*\solution.patch").FullName
     git -C "$e2e\workspace" apply $patch
     .venv\Scripts\python.exe harness.py submit
     .venv\Scripts\python.exe harness.py reset --force
   The first submit is 30–50%, and the second submit is "(100.0%)".
D. Commit only the exercise and grader:
     git add exercises/01-* .grader/01-*
     git commit with the message "Add exercise 01" followed by a blank line and
     "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"

REPORT (your final message). Use only this template. Do NOT mention the domain, slug, model or
endpoint names, bug descriptions, file names inside the exercise, or test names:
  EXERCISE 01 BUILD REPORT
  verify output: <paste the verify output verbatim; it only has numbers and fix_NN labels>
  tests: visible <V>, hidden <H>
  e2e: first submit <X.X>%, after solution <Y.Y>%, reset <ok|failed>
  harness tests: <N> passed
  commit: <short sha>
  problems: <none, or harness-only issues with no exercise details>
````

- [ ] **Step 2: Wait for the agent's report**

You'll be notified when the agent finishes; don't poll. Read **only** the report. If any line shows a failure, send the agent the failing line through SendMessage and ask it to fix the problem and report again in the same template.

- [ ] **Step 3: Independently confirm the gate (numbers only)**

Run: `.venv/Scripts/python harness.py verify 01 && .venv/Scripts/python -m pytest -q && git log --oneline -1`
Expected: `Result: N/N checks passed`, the harness tests pass, and the last commit is `Add exercise 01`. Do **not** run `git show`, `git log --stat` or anything else that prints exercise files.

- [ ] **Step 4: Tell the user it's ready**

Share only: the verify summary line, the starting score range, the time limit, and the commands `python harness.py start 01` and `python harness.py submit`.

---

## After all tasks

- The final branch review must **exclude** `exercises/01-*` and `.grader/01-*`. Give the reviewer this
  instruction: "Do not open, quote or summarize anything under exercises/01-* or .grader/01-*;
  review only harness.py, harnesslib/, harness_tests/, README.md and the config files."
- Then finish the branch with superpowers:finishing-a-development-branch.
