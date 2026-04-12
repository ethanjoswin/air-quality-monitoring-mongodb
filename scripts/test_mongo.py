import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

env_candidates = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]

for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

MONGO_URI = os.getenv("MONGO_URI")

print("URI loaded:", "Yes" if MONGO_URI else "No")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)

try:
    print(client.admin.command("ping"))
    print("MongoDB connection successful")
except Exception as e:
    print("MongoDB connection failed")
    print(e)