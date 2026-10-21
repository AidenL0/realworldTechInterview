"""Parse pytest JUnit XML reports and turn them into a HackerRank-style score."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

HIDDEN_PREFIX = "tests.hidden."
_NOT_PASSED_TAGS = {"failure", "error", "skipped"}


@dataclass(frozen=True)
class CaseResult:
    test_id: str
    hidden: bool
    passed: bool
    is_test: bool


@dataclass(frozen=True)
class Score:
    visible_passed: int
    visible_total: int
    hidden_passed: int
    hidden_total: int
    failed_visible: tuple[str, ...] = ()
    load_errors: int = 0

    @property
    def passed(self) -> int:
        return self.visible_passed + self.hidden_passed

    @property
    def total(self) -> int:
        return self.visible_total + self.hidden_total

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 0.0
        return round(100 * self.passed / self.total, 1)


def parse_junit(path: Path) -> list[CaseResult]:
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        # pytest reports a module that failed to import as a case with an empty classname.
        is_test = bool(classname)
        test_id = f"{classname}::{name}" if is_test else name
        failed = any(child.tag in _NOT_PASSED_TAGS for child in case)
        cases.append(
            CaseResult(
                test_id=test_id,
                hidden=test_id.startswith(HIDDEN_PREFIX),
                passed=is_test and not failed,
                is_test=is_test,
            )
        )
    return cases


def score_cases(cases: Sequence[CaseResult], expected_visible: int, expected_hidden: int) -> Score:
    visible_passed = sum(1 for c in cases if c.passed and not c.hidden)
    hidden_passed = sum(1 for c in cases if c.passed and c.hidden)
    return Score(
        visible_passed=min(visible_passed, expected_visible),
        visible_total=expected_visible,
        hidden_passed=min(hidden_passed, expected_hidden),
        hidden_total=expected_hidden,
        failed_visible=tuple(c.test_id for c in cases if c.is_test and not c.hidden and not c.passed),
        load_errors=sum(1 for c in cases if not c.is_test),
    )
