from datetime import datetime, timezone

from blog_agent.tools.dates import months_ago


def test_simple_subtraction():
    frm = datetime(2026, 6, 10, tzinfo=timezone.utc)
    assert months_ago(6, frm) == datetime(2025, 12, 10, tzinfo=timezone.utc)


def test_year_rollover():
    frm = datetime(2026, 1, 15, tzinfo=timezone.utc)
    assert months_ago(2, frm) == datetime(2025, 11, 15, tzinfo=timezone.utc)


def test_day_clamped_to_month_end():
    # Mar 31 minus one month -> Feb 28 (2025 is not a leap year).
    frm = datetime(2025, 3, 31, tzinfo=timezone.utc)
    assert months_ago(1, frm) == datetime(2025, 2, 28, tzinfo=timezone.utc)
