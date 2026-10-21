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
