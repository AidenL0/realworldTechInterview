from harnesslib.results import CaseResult, Score, parse_junit, score_cases

REPORT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="2" failures="1" skipped="1" tests="6">
<testcase classname="tests.test_api" name="test_list" time="0.01" />
<testcase classname="tests.test_api" name="test_create" time="0.01"><failure message="assert 400 == 201">trace</failure></testcase>
<testcase classname="tests.test_api.TestOrders" name="test_total" time="0.01"><error message="fixture error">trace</error></testcase>
<testcase classname="tests.test_api" name="test_later" time="0.0"><skipped message="todo" /></testcase>
<testcase classname="tests.hidden.test_hidden_api" name="test_edge" time="0.01" />
<testcase classname="" name="tests.hidden.test_hidden_broken" time="0.0"><error message="collection failure">ImportError</error></testcase>
</testsuite></testsuites>
"""


def write_report(tmp_path, text=REPORT):
    path = tmp_path / "report.xml"
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_junit_reads_every_case(tmp_path):
    cases = parse_junit(write_report(tmp_path))
    assert [c.test_id for c in cases] == [
        "tests.test_api::test_list",
        "tests.test_api::test_create",
        "tests.test_api.TestOrders::test_total",
        "tests.test_api::test_later",
        "tests.hidden.test_hidden_api::test_edge",
        "tests.hidden.test_hidden_broken",
    ]
    assert [c.passed for c in cases] == [True, False, False, False, True, False]
    assert [c.hidden for c in cases] == [False, False, False, False, True, True]
    assert [c.is_test for c in cases] == [True, True, True, True, True, False]


def test_hidden_needs_the_exact_prefix(tmp_path):
    report = REPORT.replace(
        'classname="tests.test_api" name="test_list"', 'classname="tests.hiddenfoo" name="test_list"'
    )
    first = parse_junit(write_report(tmp_path, report))[0]
    assert first.test_id == "tests.hiddenfoo::test_list"
    assert first.hidden is False


def test_score_uses_expected_counts(tmp_path):
    score = score_cases(parse_junit(write_report(tmp_path)), expected_visible=4, expected_hidden=3)
    assert (score.visible_passed, score.visible_total) == (1, 4)
    assert (score.hidden_passed, score.hidden_total) == (1, 3)
    assert (score.passed, score.total) == (2, 7)
    assert score.percent == 28.6
    assert score.load_errors == 1
    assert score.failed_visible == (
        "tests.test_api::test_create",
        "tests.test_api.TestOrders::test_total",
        "tests.test_api::test_later",
    )


def test_missing_tests_count_as_failed():
    score = score_cases([], expected_visible=3, expected_hidden=2)
    assert (score.passed, score.total, score.percent) == (0, 5, 0.0)


def test_extra_passes_never_exceed_expected():
    cases = [CaseResult(f"tests.test_a::t{i}", False, True, True) for i in range(5)]
    assert score_cases(cases, expected_visible=3, expected_hidden=0).visible_passed == 3


def test_percent_rounding_and_empty_total():
    assert Score(2, 3, 0, 0).percent == 66.7
    assert Score(0, 0, 0, 0).percent == 0.0
