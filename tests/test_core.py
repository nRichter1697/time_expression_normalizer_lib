"""Deterministic tests for the normalizer.

The clock is always faked; no test reads the wall clock.
"""

import unittest
from datetime import datetime, timedelta, timezone

from time_expression_normalizer_lib import TimeNormalizer, NormalizationError


def fixed_clock(year, month, day, hour, minute, second=0):
    return lambda: datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


class TestTimeNormalizer(unittest.TestCase):

    def _norm(self, expr, clock):
        return TimeNormalizer(clock).normalize(expr)

    def test_now(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(self._norm("now", now), now())

    def test_today(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("today", now),
            fixed_clock(2024, 3, 15, 0, 0)(),
        )

    def test_tomorrow(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("tomorrow", now),
            fixed_clock(2024, 3, 16, 0, 0)(),
        )

    def test_yesterday(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("yesterday", now),
            fixed_clock(2024, 3, 14, 0, 0)(),
        )

    def test_today_at_hh_mm(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("today at 14:30", now),
            fixed_clock(2024, 3, 15, 14, 30)(),
        )

    def test_today_at_hh(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("today at 9", now),
            fixed_clock(2024, 3, 15, 9, 0)(),
        )

    def test_tomorrow_at_hh_mm(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("tomorrow at 8:15", now),
            fixed_clock(2024, 3, 16, 8, 15)(),
        )

    def test_in_5_minutes(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 5 minutes", now),
            now() + timedelta(minutes=5),
        )

    def test_in_2_hours(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 2 hours", now),
            now() + timedelta(hours=2),
        )

    def test_in_3_days(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 3 days", now),
            now() + timedelta(days=3),
        )

    def test_in_seconds(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 10 seconds", now),
            now() + timedelta(seconds=10),
        )

    def test_minute_short_form(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 5 m", now),
            now() + timedelta(minutes=5),
        )

    def test_hour_short_form(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 1 h", now),
            now() + timedelta(hours=1),
        )

    def test_day_short_form(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 1 d", now),
            now() + timedelta(days=1),
        )

    def test_second_short_form(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 1 s", now),
            now() + timedelta(seconds=1),
        )

    def test_today_at_invalid_hour(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        with self.assertRaises(NormalizationError):
            self._norm("today at 25", now)

    def test_today_at_invalid_minute(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        with self.assertRaises(NormalizationError):
            self._norm("today at 10:60", now)

    def test_unrecognized(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        with self.assertRaises(NormalizationError):
            self._norm("next week", now)

    def test_empty_raises(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        with self.assertRaises(NormalizationError):
            self._norm("", now)

    def test_whitespace_stripped(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("   now   ", now),
            now(),
        )

    def test_case_insensitive(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("NOW", now),
            now(),
        )
        self.assertEqual(
            self._norm("Today at 9", now),
            fixed_clock(2024, 3, 15, 9, 0)(),
        )
        self.assertEqual(
            self._norm("In 5 Minutes", now),
            now() + timedelta(minutes=5),
        )

    def test_month_boundary_tomorrow(self):
        now = fixed_clock(2024, 1, 31, 23, 59)
        self.assertEqual(
            self._norm("tomorrow", now),
            fixed_clock(2024, 2, 1, 0, 0)(),
        )

    def test_year_boundary_yesterday(self):
        now = fixed_clock(2024, 1, 1, 0, 0)
        self.assertEqual(
            self._norm("yesterday", now),
            fixed_clock(2023, 12, 31, 0, 0)(),
        )

    def test_zero_offset(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        self.assertEqual(
            self._norm("in 0 minutes", now),
            now(),
        )

    def test_returns_utc(self):
        now = fixed_clock(2024, 3, 15, 10, 30)
        result = self._norm("today", now)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_naive_clock_treated_as_utc(self):
        naive = datetime(2024, 3, 15, 10, 30, 0)
        result = TimeNormalizer(lambda: naive).normalize("now")
        self.assertEqual(result, naive.replace(tzinfo=timezone.utc))
        self.assertEqual(result.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
