import unittest
import pandas as pd
from scripts.utils import get_aqi_category


class TestIntegration(unittest.TestCase):

    def test_backend_to_dashboard_flow(self):

        # Simulate backend document
        mock_data = [
            {
                "datetime": "2026-01-01 10:00:00",
                "pm2_5": 10,
                "pm10": 20,
                "no2": 5,
                "o3": 15,
                "co": 1,
                "aqi": 2,
                "aqi_category": get_aqi_category(2),
                "temperature": 10,
                "humidity": 70,
                "pressure": 1000,
                "wind_speed": 5,
                "source": "live"
            }
        ]

        df = pd.DataFrame(mock_data)

        # Convert datetime like dashboard
        df["datetime"] = pd.to_datetime(df["datetime"])

        # Check transformation works
        self.assertFalse(df.empty)
        self.assertIn("pm2_5", df.columns)
        self.assertEqual(df["aqi_category"][0], "Fair")


if __name__ == "__main__":
    unittest.main()