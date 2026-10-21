import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from harnesslib.cli import main

ROOT = Path(__file__).resolve().parent.parent


def start(capsys):
    assert main(["start", "00", "--no-open"]) == 0
    capsys.readouterr()


def score_line(capsys) -> str:
    assert main(["submit"]) == 0
    return capsys.readouterr().out


def test_piped_stdout_is_utf8(harness_root):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "harness.py"), "list"],
        capture_output=True, env=os.environ.copy(), cwd=harness_root,
    )
    assert proc.returncode == 0
    assert "best: —" in proc.stdout.decode("utf-8")


def test_start_survives_global_gpgsign(harness_root, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "commit.gpgsign")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    assert main(["start", "00", "--no-open"]) == 0


def test_workspace_pytest_ini_cannot_change_grading(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "pytest.ini").write_text(
        "[pytest]\npythonpath = .\naddopts = -x\n", encoding="utf-8")
    assert "(40.0%)" in score_line(capsys)


def test_workspace_conftest_is_removed_for_grading(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "conftest.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
    assert "(40.0%)" in score_line(capsys)


def test_pytest_addopts_env_cannot_change_grading(harness_root, capsys, monkeypatch):
    start(capsys)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-x")
    assert "(40.0%)" in score_line(capsys)


def test_start_asks_before_deleting_workspace_without_attempt(harness_root, monkeypatch):
    workspace = harness_root / "workspace"
    workspace.mkdir()
    (workspace / "mine.txt").write_text("keep", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["start", "00", "--no-open"]) == 1
    assert (workspace / "mine.txt").exists()


def test_malformed_attempt_json_is_a_clean_error(harness_root, capsys):
    state = harness_root / ".state"
    state.mkdir()
    (state / "attempt.json").write_text("{}", encoding="utf-8")
    assert main(["time"]) == 1
    assert "attempt.json" in capsys.readouterr().err


def test_bad_started_at_is_a_clean_error(harness_root, capsys):
    state = harness_root / ".state"
    state.mkdir()
    (state / "attempt.json").write_text(
        '{"exercise_id": "00", "started_at": "yesterday", "time_limit_minutes": 5}', encoding="utf-8")
    assert main(["time"]) == 1
    assert "attempt.json" in capsys.readouterr().err


def test_malformed_history_json_is_a_clean_error(harness_root, capsys):
    state = harness_root / ".state"
    state.mkdir()
    (state / "history.json").write_text("{}", encoding="utf-8")
    assert main(["list"]) == 1
    assert "history.json" in capsys.readouterr().err


def test_hidden_load_errors_are_counted_separately(harness_root, capsys):
    hidden = harness_root / ".grader" / "00-sample" / "hidden_tests"
    (hidden / "test_hidden_broken.py").write_text("def broken(:\n", encoding="utf-8")
    start(capsys)
    out = score_line(capsys)
    assert "1 test file(s) failed to load (1 hidden)" in out
    assert "test_hidden_broken" not in out
    assert "pytest tests -q" not in out.split("failed to load")[1]


def test_verify_requires_answer_key(harness_root, capsys):
    (harness_root / ".grader" / "00-sample" / "ANSWER_KEY.md").unlink()
    assert main(["verify", "00"]) == 1


def test_submit_measures_time_before_grading(harness_root, capsys, monkeypatch):
    start(capsys)
    from harnesslib import clock, grading
    real_grade, real_now = grading.grade_directory, clock.now_utc

    def slow_grade(*args, **kwargs):
        monkeypatch.setattr(clock, "now_utc", lambda: real_now() + timedelta(minutes=500))
        return real_grade(*args, **kwargs)

    monkeypatch.setattr(grading, "grade_directory", slow_grade)
    assert "OVERTIME" not in score_line(capsys)
