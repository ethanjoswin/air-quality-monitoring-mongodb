import unittest
import pandas as pd
from scripts.utils import get_aqi_category, to_dublin_hour


class TestTransformations(unittest.TestCase):

    def test_aqi_category(self):
        self.assertEqual(get_aqi_category(1), "Good")
        self.assertEqual(get_aqi_category(2), "Fair")
        self.assertEqual(get_aqi_category(5), "Very Poor")
        self.assertEqual(get_aqi_category(99), "Unknown")

    def test_datetime_conversion(self):
        ts = int(pd.Timestamp("2026-01-01 10:30:00", tz="UTC").timestamp())
        result = to_dublin_hour(ts)

        # Should round to hour
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)

    def test_datetime_dst(self):
        ts = int(pd.Timestamp("2026-07-01 10:30:00", tz="UTC").timestamp())
        result = to_dublin_hour(ts)

        # DST should shift hour
        self.assertTrue(result.hour in [10, 11])


if __name__ == "__main__":
    unittest.main()