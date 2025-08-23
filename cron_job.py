import json, os
from dotenv import load_dotenv
from scraper import fetch_to_dataframe, dataframe_to_records
from storage import init_db, save_snapshot

load_dotenv()
init_db()

SOURCES = json.loads(os.getenv("DATA_SOURCES", "[]"))

for src in SOURCES:
    df = fetch_to_dataframe(src["url"])
    save_snapshot(src["name"], dataframe_to_records(df))
    print(f"OK {src['name']}: {len(df)} rows")