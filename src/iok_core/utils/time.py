from __future__ import annotations
import datetime
from datetime import timezone, timedelta
from typing import Final

UTC: Final = timezone.utc

def utcnow() -> datetime.datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.datetime.now(UTC)

def utcnow_timestamp() -> float:
    """Current Unix timestamp as float."""
    return utcnow().timestamp()

def iso_utcnow() -> str:
    """ISO-8601 string with +00:00."""
    return utcnow().isoformat()

def iso_utcnow_minus_days(days: int) -> str:
    """ISO string of UTC time minus N days."""
    return (utcnow() - timedelta(days=days)).isoformat()

def iso_utcnow_minus_hours(hours: int) -> str:
    return (utcnow() - timedelta(hours=hours)).isoformat()