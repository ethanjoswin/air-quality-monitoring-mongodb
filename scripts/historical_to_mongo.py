import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests
import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

# -----------------------------
# LOAD .env
# -----------------------------
env_candidates = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]

for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

API_KEY = os.getenv("API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

LAT = 53.3498
LON = -6.2603

if not API_KEY:
    raise ValueError("API_KEY not found in .env file")
if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client["air_quality_db"]
collection = db["pollution_data"]
collection.create_index([("datetime", ASCENDING)], unique=True)


def get_aqi_category(aqi):
    mapping = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    return mapping.get(aqi, "Unknown")


def fetch_historical_pollution(days=5):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)

    start_unix = int(start_time.timestamp())
    end_unix = int(end_time.timestamp())

    url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution/history"
        f"?lat={LAT}&lon={LON}&start={start_unix}&end={end_unix}&appid={API_KEY}"
    )

    response = requests.get(url, timeout=60)

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        raise ValueError(f"Historical API failed: {response.text}")

    data = response.json()

    if "list" not in data or len(data["list"]) == 0:
        raise ValueError(f"No historical data returned: {data}")

    inserted = 0
    skipped = 0

    for item in data["list"]:
        dt_value = (
            pd.to_datetime(item["dt"], unit="s", utc=True)
            .tz_convert("Europe/Dublin")
            .tz_localize(None)
            .floor("h")
            .to_pydatetime()
        )

        document = {
            "datetime": dt_value,
            "pm2_5": item["components"].get("pm2_5"),
            "pm10": item["components"].get("pm10"),
            "no2": item["components"].get("no2"),
            "o3": item["components"].get("o3"),
            "co": item["components"].get("co"),
            "aqi": item["main"].get("aqi"),
            "aqi_category": get_aqi_category(item["main"].get("aqi")),
            "source": "historical"
        }

        try:
            collection.insert_one(document)
            inserted += 1
        except DuplicateKeyError:
            skipped += 1

    print(f"Historical load complete. Inserted: {inserted}, Skipped: {skipped}")


if __name__ == "__main__":
    days_input = int(input("Enter how many days of historical data you want: "))
    fetch_historical_pollution(days=days_input)