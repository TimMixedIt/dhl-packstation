"""Summarize actual fresh observations by local weekday."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import median

HISTORY_DAYS = 56


def record_sample(
    days: dict[str, dict[str, int]],
    timestamp: datetime,
    total: int,
    today: date,
) -> None:
    """Retain one observation per local hour over the last eight weeks."""
    cutoff = (today - timedelta(days=HISTORY_DAYS - 1)).isoformat()
    for day in list(days):
        if day < cutoff:
            del days[day]
    if timestamp.date().isoformat() >= cutoff:
        samples = days.setdefault(timestamp.date().isoformat(), {})
        samples.setdefault(str(timestamp.hour), total)


def weekday_totals(days: dict[str, dict[str, int]], today: date) -> list[dict]:
    """Use equally weighted daily medians and require two dates per weekday."""
    cutoff = today - timedelta(days=HISTORY_DAYS - 1)
    by_weekday = defaultdict(list)
    for key, hours in days.items():
        day = date.fromisoformat(key)
        if cutoff <= day <= today and hours:
            by_weekday[day.weekday()].append(median(hours.values()))
    return [
        {
            "days": len(values := by_weekday[weekday]),
            "typical": median(values) if len(values) >= 2 else None,
        }
        for weekday in range(7)
    ]
