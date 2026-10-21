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
