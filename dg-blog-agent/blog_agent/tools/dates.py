"""Date helpers — pure, no external deps."""

import calendar
from datetime import datetime, timezone


def months_ago(months: int, frm: datetime | None = None) -> datetime:
    """Return a timezone-aware datetime ``months`` months before ``frm`` (default now).

    Day-of-month is clamped to the target month's last day (e.g. Mar 31 − 1 month
    -> Feb 28/29). Pure and deterministic given ``frm``.
    """
    frm = frm or datetime.now(timezone.utc)
    # Zero-based month index arithmetic handles year rollover cleanly.
    index = frm.month - 1 - months
    year = frm.year + index // 12
    month = index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(frm.day, last_day)
    return frm.replace(year=year, month=month, day=day)
