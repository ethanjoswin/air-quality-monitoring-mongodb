import os
from pathlib import Path
from pymongo import MongoClient
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

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env file")

client = MongoClient(MONGO_URI)
db = client["air_quality_db"]
collection = db["pollution_data"]


def clean_incomplete_records():
    result = collection.delete_many({
        "$or": [
            {"no2": {"$exists": False}},
            {"o3": {"$exists": False}},
            {"co": {"$exists": False}}
        ]
    })

    print(f"Deleted {result.deleted_count} incomplete records.")


if __name__ == "__main__":
    clean_incomplete_records()