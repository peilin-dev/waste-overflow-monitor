from datetime import datetime, timezone, timedelta

_MYT = timezone(timedelta(hours=8))


def now_myt() -> datetime:
    """Current time in Malaysia Time (UTC+8), stored as naive datetime."""
    return datetime.now(_MYT).replace(tzinfo=None)
