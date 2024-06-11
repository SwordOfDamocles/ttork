import unittest

from ._time import format_age


class TestFormatAge(unittest.TestCase):

    def test_format_age_days(self):
        self.assertEqual(
            format_age(90061), "1d:01h"
        )  # 1 day, 1 hour, 1 second

    def test_format_age_hours(self):
        self.assertEqual(
            format_age(3661), "1h:01m"
        )  # 1 hour, 1 minute, 1 second

    def test_format_age_minutes(self):
        self.assertEqual(format_age(305), "5m:05s")  # 5 minutes, 5 seconds

    def test_format_age_seconds(self):
        self.assertEqual(format_age(45), "45s")  # 45 seconds

    def test_format_age_zero(self):
        self.assertEqual(format_age(0), "00s")  # 0 seconds

    def test_format_age_exact_days(self):
        self.assertEqual(format_age(86400), "1d:00h")  # 1 day

    def test_format_age_exact_hours(self):
        self.assertEqual(format_age(3600), "1h:00m")  # 1 hour

    def test_format_age_exact_minutes(self):
        self.assertEqual(format_age(60), "1m:00s")  # 1 minute


if __name__ == "__main__":
    unittest.main()
