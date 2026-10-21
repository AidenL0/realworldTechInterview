"""Implementations of the harness CLI commands."""
from __future__ import annotations

import shutil
import subprocess
import sys

from . import clock, grading
from .config import HarnessError, Paths, get_exercise, load_exercises, require_venv
from .state import Attempt, append_history, best_score, clear_attempt, load_attempt, load_history, save_attempt
from .system import remove_tree, run_python
from .verify import print_checks, run_checks
from .workspace import create_workspace


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
    if paths.workspace.exists() and not force:
        if current:
            question, kept = f"Attempt for {current.exercise_id} in progress. Overwrite?", "Kept your current attempt."
        else:
            question, kept = "workspace/ already exists. Overwrite it?", "Kept your existing workspace/."
        if not confirm(question):
            print(kept)
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


def cmd_submit(paths: Paths) -> int:
    require_venv(paths)
    attempt = _require_attempt(paths)
    exercise = get_exercise(paths, attempt.exercise_id)
    print("Grading your workspace with the visible and hidden tests ...")
    elapsed = clock.elapsed_seconds(attempt.started_at, clock.now_utc())
    overtime = clock.is_overtime(elapsed, attempt.time_limit_minutes)
    result = grading.grade_directory(paths, exercise, paths.workspace)
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
            hidden_errors = sum(1 for case in result.cases if not case.is_test and case.hidden)
            visible_errors = score.load_errors - hidden_errors
            message = f"\n{score.load_errors} test file(s) failed to load ({hidden_errors} hidden)."
            if visible_errors > 0:
                message += " Run `pytest tests -q` in your workspace to see why."
            print(message)

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


def cmd_verify(paths: Paths, exercise_id: str) -> int:
    require_venv(paths)
    exercise = get_exercise(paths, exercise_id)
    return 0 if print_checks(exercise, run_checks(paths, exercise)) else 1


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
