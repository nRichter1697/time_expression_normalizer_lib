"""Core normalization logic.

The clock is injected so tests never touch the wall clock.
"""

from __future__ import annotations

import re
from calendar import timegm
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional


class NormalizationError(ValueError):
    """Raised when a time expression cannot be parsed."""


class TimeNormalizer:
    """Normalize a small set of natural-language time expressions.

    Supported expressions:
      - "now"
      - "today"
      - "today at HH:MM"
      - "today at HH"
      - "tomorrow"
      - "tomorrow at HH:MM"
      - "tomorrow at HH"
      - "in N unit" where unit is s/sec/secs/second/seconds,
        m/min/mins/minute/minutes, h/hr/hrs/hour/hours,
        d/day/days
      - "yesterday"

    All returned datetimes are in UTC (timezone-aware). The reference
    point is supplied by a clock callable so tests can pin it; production
    code passes ``datetime.now(timezone.utc)``.

    We deliberately scope the grammar tight: a fixed, testable surface
    rather than a vague "understand English" promise we cannot keep.
    """

    _TIME_PART = r"(\d{1,2})(?::(\d{2}))?"
    _TODAY_AT = re.compile(r"^today at " + _TIME_PART + r"$")
    _TOMORROW_AT = re.compile(r"^tomorrow at " + _TIME_PART + r"$")
    _IN_OFFSET = re.compile(
        r"^in (\d+)\s+(second|seconds|sec|secs|s|"
        r"minute|minutes|min|mins|m|"
        r"hour|hours|hr|hrs|h|"
        r"day|days|d)$"
    )
    _UNIT_SECONDS = {
        "second": 1, "seconds": 1, "sec": 1, "secs": 1, "s": 1,
        "minute": 60, "minutes": 60, "min": 60, "mins": 60, "m": 60,
        "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600, "h": 3600,
        "day": 86400, "days": 86400, "d": 86400,
    }

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        # Default clock is real UTC so production usage needs no args.
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def normalize(self, expression: str) -> datetime:
        """Parse a single expression into a UTC datetime.

        Raises NormalizationError on anything outside the grammar.
        """
        if not isinstance(expression, str):
            raise NormalizationError("expression must be a string")

        text = expression.strip().lower()
        if not text:
            raise NormalizationError("empty expression")

        now = self._clock()
        if now.tzinfo is None:
            # Treat naive clocks as UTC so behaviour stays defined; tests
            # pass tz-aware clocks anyway.
            now = now.replace(tzinfo=timezone.utc)

        if text == "now":
            return now

        if text == "today":
            return self._midnight(now)

        if text == "tomorrow":
            return self._midnight(now + timedelta(days=1))

        if text == "yesterday":
            return self._midnight(now + timedelta(days=-1))

        m = self._TODAY_AT.match(text)
        if m:
            return self._at_time(now, m.group(1), m.group(2))

        m = self._TOMORROW_AT.match(text)
        if m:
            return self._at_time(now + timedelta(days=1), m.group(1), m.group(2))

        m = self._IN_OFFSET.match(text)
        if m:
            qty = int(m.group(1))
            unit = m.group(2)
            return now + timedelta(seconds=qty * self._UNIT_SECONDS[unit])

        raise NormalizationError(f"unrecognized expression: {expression!r}")

    @staticmethod
    def _midnight(dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _at_time(day: datetime, hour_str: str, minute_str: Optional[str]) -> datetime:
        hour = int(hour_str)
        minute = int(minute_str) if minute_str else 0
        if hour > 23 or minute > 59:
            raise NormalizationError(f"invalid clock time: {hour}:{minute:02d}")
        return day.replace(hour=hour, minute=minute, second=0, microsecond=0)
