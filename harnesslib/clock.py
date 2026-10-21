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
