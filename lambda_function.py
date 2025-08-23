import json, os
from datetime import datetime, timezone
from scraper import fetch_to_dataframe, dataframe_to_records

BUCKET = os.getenv("S3_BUCKET")
PREFIX = os.getenv("S3_PREFIX", "gse/")

# Lazy import to reduce cold start
import boto3
s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))


def _ts():
    return datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")


def handler(event, context):
    sources = json.loads(os.getenv("DATA_SOURCES", "[]"))
    out = []
    for src in sources:
        df = fetch_to_dataframe(src["url"])  # auto‑detect JSON/CSV/XLSX
        records = dataframe_to_records(df)
        snapshot = {
            "source": src["name"],
            "as_of": datetime.now(timezone.utc).isoformat(),
            "rowcount": len(records),
            "data": records,
        }
        key = f"{PREFIX}{src['name']}/{_ts()}.json"
        s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(snapshot).encode("utf-8"), ContentType="application/json")
        out.append({"source": src["name"], "s3_key": key, "rows": len(records)})
    return {"ok": True, "written": out}

