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
