from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017/")
db = client["test_db"]
collection = db["test_collection"]

data = {"name": "test Entry", "timestamp": datetime.now(timezone.utc)}
collection.insert_one(data)

print("Data Inserted: ", data)