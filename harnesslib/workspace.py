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
        [
            "-c", "user.name=practice", "-c", "user.email=practice@localhost", "-c", "commit.gpgsign=false",
            "commit", "-q", "--no-verify", "-m", "baseline",
        ],
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
