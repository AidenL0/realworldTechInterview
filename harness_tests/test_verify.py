import shutil

from harnesslib.cli import main
from harnesslib.verify import compare_outcomes


def grader(root):
    return root / ".grader" / "00-sample"


def test_compare_outcomes_finds_fixed_and_broken():
    before = {"a": False, "b": True, "c": False}
    after = {"a": True, "b": False, "c": False, "d": True}
    fixed, broken = compare_outcomes(before, after)
    assert fixed == {"a", "d"}
    assert broken == {"b"}


def test_verify_passes_for_fair_sample(harness_root, capsys):
    assert main(["verify", "00"]) == 0
    out = capsys.readouterr().out
    assert "[PASS] clean start" in out
    assert "40.0% (2/5)" in out
    assert "[PASS] full solution" in out
    assert "[PASS] fix_01" in out
    assert "fixes 2 test(s) · breaks 0" in out
    assert "[PASS] fix_02" in out
    assert "[PASS] hidden-only bug" in out
    assert "[PASS] test counts" in out
    assert "Result: 6/6 checks passed" in out


def test_verify_fails_without_hidden_only_bug(harness_root, capsys):
    fixes = grader(harness_root) / "fixes"
    shutil.copyfile(fixes / "fix_01.patch", fixes / "fix_02.patch")
    assert main(["verify", "00"]) == 1
    assert "[FAIL] hidden-only bug" in capsys.readouterr().out


def test_verify_fails_when_counts_are_wrong(harness_root, capsys):
    (grader(harness_root) / "expected.json").write_text('{"visible": 3, "hidden": 3}', encoding="utf-8")
    assert main(["verify", "00"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] test counts" in out
    assert "visible 2/3" in out


def test_verify_reports_patch_that_does_not_apply(harness_root, capsys):
    (grader(harness_root) / "fixes" / "fix_02.patch").write_text("not a patch\n", encoding="utf-8")
    assert main(["verify", "00"]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] fix_02" in out
    assert "patch does not apply" in out
