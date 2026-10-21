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
    # Pytest config in the workspace must not change how grading runs.
    for name in ("pytest.ini", "conftest.py"):
        original, copied = exercise.source_dir / name, sandbox / name
        if original.is_file():
            shutil.copyfile(original, copied)
        else:
            copied.unlink(missing_ok=True)


def _grading_env() -> dict[str, str]:
    env = child_env()
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        env.pop(name, None)
    return env


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
        subprocess.run(
            command, cwd=sandbox, env=_grading_env(), timeout=PYTEST_TIMEOUT_SECONDS,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return GradeResult(score_cases((), expected_visible, expected_hidden), (), True, False, None)
    cases = _read_report(report)
    ran_any = any(case.is_test for case in cases)
    check_output = None
    if not ran_any and exercise.check_command:
        try:
            _ok, check_output = run_python(paths, exercise.check_command, sandbox, timeout=PYTEST_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            check_output = "The check command timed out."
    return GradeResult(score_cases(cases, expected_visible, expected_hidden), cases, False, ran_any, check_output)


def grade_directory(paths: Paths, exercise: Exercise, source: Path) -> GradeResult:
    with tempfile.TemporaryDirectory(prefix="harness-", ignore_cleanup_errors=True) as tmp:
        sandbox = Path(tmp) / "app"
        prepare_sandbox(source, exercise, sandbox)
        return run_tests(paths, exercise, sandbox)
