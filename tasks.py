import os
import dramatiq
from pymongo import MongoClient
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dramatiq.brokers.redis import RedisBroker
from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging
from logging.handlers import RotatingFileHandler
import pytz

logging.basicConfig(level=logging.INFO)

log_directory = "C:\\Users\\admin\\OneDrive - E 4 Energy Solutions\\Saturn Pyro Files\\Documents\\Dell5Sync\\logs"
log_file = os.path.join(log_directory, "service_debug.log")

os.makedirs(log_directory, exist_ok=True)

log_handler = RotatingFileHandler(
    log_file, maxBytes=1 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)

logging.getLogger().addHandler(log_handler)

logging.info("program started.")

broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(broker)

client = MongoClient("mongodb://localhost:27017")
db = client["test_db"]
collection = db["test_collection"]

script_dir = os.path.abspath(os.path.dirname(__file__))
url_file = os.path.join(script_dir, "urls.txt")


@dramatiq.actor
def fetch_data():
    try:
        with open(url_file, "r") as file:
            urls = [line.strip() for line in file if line.strip()]
        logging.info(f"Extracted URLs: {urls}")
        print(f"Extracted URLs: {urls}")

        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        dateTime_str = now_ist.strftime("%Y-%m-%d %H:%M:%S")
        date_str = now_ist.date().strftime("%Y-%m-%d")
        time_str = now_ist.time().strftime("%H:%M:%S")

        logging.info(f"Timestamp for this fetch cycle: {dateTime_str}")
        print(f"Timestamp for this fetch cycle: {dateTime_str}")

        for url in urls:
            try:
                logging.info(f"Fetching data from {url}")
                print(f"Fetching data from {url}")

                response = requests.get(url)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    variable_elements = root.findall(".//variable")

                    data_records = []

                    for variable_element in variable_elements:
                        try:
                            d_name = variable_element.find("id").text
                            d_value = float(variable_element.find("value").text)

                            data_records.append({
                                "id": d_name,
                                "value": d_value,
                                "date_time": dateTime_str,
                                "date": date_str,
                                "time": time_str,
                                "datetime_obj": now_ist
                            })
                        except (AttributeError, ValueError) as e:
                            logging.error(f"Skipping malformed data from {url}: {e}")
                            print(f"Skipping malformed data from {url}: {e}")
                            continue

                    if data_records:
                        collection.insert_many(data_records)
                        logging.info(f"Stored data from {url}: {len(data_records)} records")
                        print(f"Stored data from {url}: {len(data_records)} records")
                    else:
                        logging.warning(f"No valid data found in {url}")
                        print(f"No valid data found in {url}")


                else:
                    logging.error(f"Failed to fetch XML data from {url}, status code: {response.status_code}")
                    print(f"Failed to fetch XML data from {url}, status code: {response.status_code}")
            except Exception as e:
                logging.error(f"Error fetching data from {url}: {e}", exc_info=True)
                print(f"Error fetching data from {url}: {e}")
    except Exception as e:
        logging.error(f"Error reading URLs or processing data: {e}", exc_info=True)
        print(f"Error reading URLs or processing data: {e}")


@dramatiq.actor
def delete_old_data():
    try:
        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        expiration_time = now_ist - timedelta(minutes=5)
        logging.info(f"Deleting records older than {expiration_time}")
        print(f"Deleting records older than {expiration_time}")

        result = collection.delete_many({"datetime_obj": {"$lte": expiration_time}})
        logging.info(f"Deleted {result.deleted_count} old records.")
        print(f"Deleted {result.deleted_count} old records.")

    except Exception as e:
        logging.error(f"Error deleting old data: {e}", exc_info=True)
        print(f"Error deleting old data: {e}")


def schedule_periodic_tasks():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_data.send, "interval", seconds=10)  # Runs every 10 seconds
    scheduler.add_job(delete_old_data.send, "interval", seconds=60)  # Runs every 60 seconds
    scheduler.start()


if __name__ == "__main__":
    schedule_periodic_tasks()
    while True:
        time.sleep(1)