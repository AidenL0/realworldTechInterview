import json

from harnesslib import grading
from harnesslib.cli import main

FIXED_CALC = '''def add(a, b):
    return a + b


def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def clamp(value, low, high):
    return max(low, min(value, high))
'''
SYNTAX_ERROR_CALC = "def add(a, b)\n    return a + b\n"
HANGING_CALC = FIXED_CALC.replace("    return a + b\n", "    while True:\n        pass\n", 1)


def start(capsys):
    assert main(["start", "00", "--no-open"]) == 0
    capsys.readouterr()


def submit(capsys) -> str:
    assert main(["submit"]) == 0
    return capsys.readouterr().out


def history(root):
    return json.loads((root / ".state" / "history.json").read_text(encoding="utf-8"))


def test_submit_scores_starting_code(harness_root, capsys):
    start(capsys)
    out = submit(capsys)
    assert "00 · Sample calculator" in out
    assert "Visible  1/2   Hidden  1/3" in out
    assert "Score    2/5  (40.0%)" in out
    assert "tests.test_calc::test_average" in out
    entry = history(harness_root)[-1]
    assert entry["score_pct"] == 40.0
    assert (entry["visible_passed"], entry["visible_total"]) == (1, 2)
    assert (entry["hidden_passed"], entry["hidden_total"]) == (1, 3)
    assert entry["overtime"] is False


def test_submit_never_reveals_hidden_tests(harness_root, capsys):
    start(capsys)
    out = submit(capsys)
    for secret in ("test_hidden_calc", "test_average_single", "test_average_empty_list", "clamp"):
        assert secret not in out


def test_submit_full_marks_after_fixing(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(FIXED_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "Score    5/5  (100.0%)" in out
    assert "Failing visible tests" not in out


def test_editing_or_adding_tests_does_not_change_score(harness_root, capsys):
    start(capsys)
    workspace = harness_root / "workspace"
    (workspace / "tests" / "test_calc.py").unlink()
    (workspace / "tests" / "test_free_points.py").write_text("def test_free():\n    assert True\n", encoding="utf-8")
    (workspace / "test_extra.py").write_text("def test_extra():\n    assert True\n", encoding="utf-8")
    out = submit(capsys)
    assert "Score    2/5  (40.0%)" in out


def test_broken_code_scores_zero_and_explains(harness_root, capsys):
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(SYNTAX_ERROR_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "Score    0/5  (0.0%)" in out
    assert "No tests could run" in out
    assert "SyntaxError" in out


def test_hanging_code_times_out(harness_root, capsys, monkeypatch):
    monkeypatch.setattr(grading, "PYTEST_TIMEOUT_SECONDS", 5)
    start(capsys)
    (harness_root / "workspace" / "calc.py").write_text(HANGING_CALC, encoding="utf-8")
    out = submit(capsys)
    assert "timed out after 5s" in out
    assert "Score    0/5  (0.0%)" in out


def test_overtime_submit_is_flagged(harness_root, capsys, backdate):
    start(capsys)
    backdate(31)
    out = submit(capsys)
    assert "/ 30m  OVERTIME" in out
    assert history(harness_root)[-1]["overtime"] is True


def test_submit_without_attempt(harness_root, capsys):
    assert main(["submit"]) == 1
    assert "No attempt in progress" in capsys.readouterr().err


def test_answers_locked_until_first_submit(harness_root, capsys):
    assert main(["answers", "00"]) == 1
    assert "Submit exercise 00 at least once" in capsys.readouterr().err


def test_answers_after_submit_and_confirm(harness_root, capsys, monkeypatch):
    start(capsys)
    submit(capsys)
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    assert main(["answers", "00"]) == 0
    out = capsys.readouterr().out
    assert "Sample answer key" in out
    assert "fix_01.patch" in out


def test_answers_declined_stays_locked(harness_root, capsys, monkeypatch):
    start(capsys)
    submit(capsys)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["answers", "00"]) == 1
    assert "Sample answer key" not in capsys.readouterr().out
