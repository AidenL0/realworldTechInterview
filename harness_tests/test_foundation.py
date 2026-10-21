import os
import stat
import sys
from pathlib import Path

import pytest

from harnesslib import system
from harnesslib.cli import main
from harnesslib.config import HarnessError, get_paths, load_exercises
from harnesslib.state import (
    Attempt,
    append_history,
    best_score,
    clear_attempt,
    load_attempt,
    load_history,
    save_attempt,
)


def test_paths_follow_environment_overrides(harness_root):
    paths = get_paths()
    assert paths.root == harness_root.resolve()
    assert paths.venv_python == Path(sys.executable)


def test_default_venv_python_is_inside_root(harness_root, monkeypatch):
    monkeypatch.delenv("HARNESS_PYTHON")
    paths = get_paths()
    folder, exe = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    assert paths.venv_python == paths.root / ".venv" / folder / exe


def test_load_exercises_reads_metadata(harness_root):
    exercise = load_exercises(get_paths())["00"]
    assert exercise.title == "Sample calculator"
    assert exercise.time_limit_minutes == 30
    assert exercise.setup_commands == ()
    assert exercise.check_command == ("-c", "import calc")
    assert exercise.grader_dir == harness_root.resolve() / ".grader" / "00-sample"


def test_attempt_round_trip(harness_root):
    paths = get_paths()
    assert load_attempt(paths) is None
    save_attempt(paths, Attempt("00", "2026-10-21T14:00:00+00:00", 30))
    assert load_attempt(paths) == Attempt("00", "2026-10-21T14:00:00+00:00", 30)
    clear_attempt(paths)
    clear_attempt(paths)
    assert load_attempt(paths) is None


def test_history_and_best_score(harness_root):
    paths = get_paths()
    assert best_score(load_history(paths), "00") is None
    append_history(paths, {"exercise_id": "00", "score_pct": 40.0})
    append_history(paths, {"exercise_id": "00", "score_pct": 80.0})
    append_history(paths, {"exercise_id": "01", "score_pct": 95.0})
    assert best_score(load_history(paths), "00") == 80.0


def test_corrupt_state_file_gives_clear_error(harness_root, capsys):
    state = harness_root / ".state"
    state.mkdir()
    (state / "history.json").write_text("{", encoding="utf-8")
    assert main(["list"]) == 1
    err = capsys.readouterr().err
    assert "history.json is not valid JSON" in err
    assert "Fix or delete it" in err


def test_remove_tree_handles_read_only_files(tmp_path):
    target = tmp_path / "repo"
    (target / "objects").mkdir(parents=True)
    locked = target / "objects" / "pack"
    locked.write_text("x", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    system.remove_tree(target)
    assert not target.exists()


def test_remove_tree_missing_path_is_a_no_op(tmp_path):
    system.remove_tree(tmp_path / "missing")


def test_remove_tree_explains_locked_files(tmp_path, monkeypatch):
    target = tmp_path / "workspace"
    target.mkdir()

    def locked(*_args, **_kwargs):
        raise PermissionError(13, "The process cannot access the file", str(target / "calc.py"))

    monkeypatch.setattr(system.shutil, "rmtree", locked)
    with pytest.raises(HarnessError, match="Close VS Code"):
        system.remove_tree(target)


def test_run_python_decodes_non_ascii_output(harness_root, tmp_path):
    ok, output = system.run_python(get_paths(), ["-c", "print('caf\u00e9 \u2713')"], tmp_path)
    assert ok
    assert "café ✓" in output


def test_list_shows_exercises(harness_root, capsys):
    assert main(["list"]) == 0
    assert "00  Sample calculator  (30m)  best: —" in capsys.readouterr().out


def test_list_marks_attempt_in_progress_and_best_score(harness_root, capsys):
    paths = get_paths()
    save_attempt(paths, Attempt("00", "2026-10-21T14:00:00+00:00", 30))
    append_history(paths, {"exercise_id": "00", "score_pct": 40.0})
    assert main(["list"]) == 0
    assert "best: 40.0%  IN PROGRESS" in capsys.readouterr().out
