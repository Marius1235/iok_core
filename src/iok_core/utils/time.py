from __future__ import annotations

from datetime import datetime, timezone
from typing import Final



UTC: Final = timezone.utc
"""The canonical timezone.utc singleton"""


def utcnow() -> datetime:
    """Return a timezone-aware datetime in UTC."""
    return datetime.now(UTC)


def utcnow_timestamp() -> float:
    """Return current Unix timestamp (seconds since epoch) as float"""
    return utcnow().timestamp()


def iso_utcnow() -> str:
    """Return current time as an ISO-8601 string with UTC offset (e.g., 2025-11-24T12:34:56.789123+00:00)."""
    return utcnow().isoformat()