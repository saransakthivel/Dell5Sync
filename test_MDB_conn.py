from pymongo import MongoClient
from datetime import datetime, timezone

try:
    client = MongoClient("mongodb+srv://test_db:test@datasync.0ptzw.mongodb.net/?retryWrites=true&w=majority&appName=DataSync")
    db = client["test_db"]
    collection = db["test_collection"]

    data = {"name": "test Entry", "timestamp": datetime.now(timezone.utc)}
    collection.insert_one(data)

    print("Data Inserted: ", data)

except Exception as e:
    print("Error occurred: ", str(e))
