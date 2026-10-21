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
    if not solution.exists() or not fixes or not (exercise.grader_dir / "ANSWER_KEY.md").exists():
        raise HarnessError(f"{exercise.grader_dir} needs solution.patch, ANSWER_KEY.md and fixes/fix_*.patch")

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
