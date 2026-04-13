import os
from pathlib import Path
import requests
import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
from utils import get_aqi_category, to_dublin_hour

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

pollution_collection = db["pollution_data"]
alerts_collection = db["alerts"]

pollution_collection.create_index([("datetime", ASCENDING)], unique=True)




def save_alert(dt_value, alert_type, value, message):
    alert_doc = {
        "datetime": dt_value,
        "type": alert_type,
        "value": value,
        "message": message
    }
    try:
        alerts_collection.insert_one(alert_doc)
        print("Alert saved:", message)
    except DuplicateKeyError:
        print("Duplicate alert skipped")


def fetch_live_pollution():
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"
    response = requests.get(url, timeout=30)

    print("Pollution Status Code:", response.status_code)

    data = response.json()

    if "list" not in data:
        raise ValueError(f"Pollution API Error: {data}")

    item = data["list"][0]

    dt_value = to_dublin_hour(item["dt"])

    return {
        "datetime": dt_value,
        "pm2_5": item["components"].get("pm2_5"),
        "pm10": item["components"].get("pm10"),
        "no2": item["components"].get("no2"),
        "o3": item["components"].get("o3"),
        "co": item["components"].get("co"),
        "aqi": item["main"].get("aqi")
    }


def fetch_live_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    response = requests.get(url, timeout=30)

    print("Weather Status Code:", response.status_code)

    data = response.json()

    if "main" not in data:
        raise ValueError(f"Weather API Error: {data}")

    return {
        "temperature": data["main"].get("temp"),
        "humidity": data["main"].get("humidity"),
        "pressure": data["main"].get("pressure"),
        "wind_speed": data["wind"].get("speed")
    }


def collect_live_data():
    pollution = fetch_live_pollution()
    weather = fetch_live_weather()

    document = {
        "datetime": pollution["datetime"],
        "pm2_5": pollution["pm2_5"],
        "pm10": pollution["pm10"],
        "no2": pollution["no2"],
        "o3": pollution["o3"],
        "co": pollution["co"],
        "aqi": pollution["aqi"],
        "aqi_category": get_aqi_category(pollution["aqi"]),
        "temperature": weather["temperature"],
        "humidity": weather["humidity"],
        "pressure": weather["pressure"],
        "wind_speed": weather["wind_speed"],
        "source": "live"
    }

    try:
        pollution_collection.insert_one(document)
        print("Live pollution + weather data inserted successfully")
        print(document)

        if document["pm2_5"] is not None and document["pm2_5"] > 35:
            save_alert(document["datetime"], "actual", document["pm2_5"], "High PM2.5 level detected")

        if document["aqi"] is not None and document["aqi"] >= 4:
            save_alert(document["datetime"], "actual", document["aqi"], "Poor air quality detected")

    except DuplicateKeyError:
        print("This hour already exists. Skipped duplicate insert.")


if __name__ == "__main__":
    collect_live_data()