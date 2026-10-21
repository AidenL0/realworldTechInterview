"""The current attempt and submission history, stored as JSON in .state/."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime

from .config import HarnessError, Paths, read_json, write_json


@dataclass(frozen=True)
class Attempt:
    exercise_id: str
    started_at: str
    time_limit_minutes: int


def load_attempt(paths: Paths) -> Attempt | None:
    data = read_json(paths.attempt_file, None)
    if data is None:
        return None
    problem = _attempt_problem(data)
    if problem:
        raise HarnessError(f"{paths.attempt_file} is not a valid attempt file ({problem}). Fix or delete it and try again.")
    return Attempt(**data)


def _attempt_problem(data: object) -> str | None:
    names = {field.name for field in fields(Attempt)}
    if not isinstance(data, dict) or set(data) != names:
        return "expected exactly the keys " + ", ".join(sorted(names))
    if not isinstance(data["exercise_id"], str) or type(data["time_limit_minutes"]) is not int:
        return "wrong value types"
    try:
        started = datetime.fromisoformat(data["started_at"])
    except (TypeError, ValueError):
        return "started_at is not an ISO timestamp"
    if started.tzinfo is None:
        return "started_at has no timezone"
    return None


def save_attempt(paths: Paths, attempt: Attempt) -> None:
    write_json(paths.attempt_file, asdict(attempt))


def clear_attempt(paths: Paths) -> None:
    paths.attempt_file.unlink(missing_ok=True)


def load_history(paths: Paths) -> list[dict]:
    history = read_json(paths.history_file, [])
    if not isinstance(history, list) or not all(isinstance(entry, dict) for entry in history):
        raise HarnessError(f"{paths.history_file} is not a list of submissions. Fix or delete it and try again.")
    return history


def append_history(paths: Paths, entry: dict) -> None:
    history = load_history(paths)
    history.append(entry)
    write_json(paths.history_file, history)


def best_score(history: list[dict], exercise_id: str) -> float | None:
    scores = [entry["score_pct"] for entry in history if entry["exercise_id"] == exercise_id]
    return max(scores) if scores else None
