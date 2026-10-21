from datetime import datetime, timedelta, timezone

from harnesslib.clock import elapsed_seconds, format_duration, is_overtime, to_iso

START = datetime(2026, 10, 21, 14, 0, 0, tzinfo=timezone.utc)


def test_to_iso_is_utc_with_seconds():
    assert to_iso(START) == "2026-10-21T14:00:00+00:00"


def test_elapsed_seconds_counts_from_start():
    assert elapsed_seconds(to_iso(START), START + timedelta(minutes=72, seconds=10)) == 4330


def test_elapsed_seconds_never_negative():
    assert elapsed_seconds(to_iso(START), START - timedelta(seconds=5)) == 0


def test_format_duration_pads_seconds():
    assert format_duration(4330) == "72m 10s"
    assert format_duration(63) == "1m 03s"
    assert format_duration(0) == "0m 00s"


def test_overtime_only_after_limit():
    assert not is_overtime(90 * 60, 90)
    assert is_overtime(90 * 60 + 1, 90)
