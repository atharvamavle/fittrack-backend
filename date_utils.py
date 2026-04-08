from datetime import date, datetime, timedelta, timezone

AEST = timezone(timedelta(hours=10))


def today_in_aest() -> date:
    """Calendar 'today' in Australian Eastern Standard Time (UTC+10, no DST)."""
    return datetime.now(AEST).date()
