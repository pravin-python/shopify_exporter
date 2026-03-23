"""
Timezone utility for converting UTC datetimes to America/Los_Angeles (Pacific Time).
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PT_ZONE = ZoneInfo("America/Los_Angeles")


def utc_to_pt(dt):
    """
    Convert a UTC datetime to America/Los_Angeles (Pacific Time).
    Returns a naive datetime in PT. Returns None if input is None.
    """
    if dt is None:
        return None

    # If naive (no tzinfo), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(PT_ZONE).replace(tzinfo=None)


def now_pt():
    """Return the current time in Pacific Time as a naive datetime."""
    return datetime.now(timezone.utc).astimezone(PT_ZONE).replace(tzinfo=None)
