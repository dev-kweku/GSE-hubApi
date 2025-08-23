import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List

DB_PATH = os.getenv("DB_PATH", "./gse.sqlite")

@contextmanager
def conn():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    try:
        yield con
    finally:
        con.close()


def init_db():
    with conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                as_of TEXT NOT NULL,
                rowcount INTEGER NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        c.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_snapshot(source: str, records: List[Dict[str, Any]]):
    with conn() as c:
        c.execute(
            "INSERT INTO snapshots(source, as_of, rowcount, payload) VALUES(?,?,?,?)",
            (source, now_iso(), len(records), json.dumps(records))
        )
        c.commit()


def latest_snapshot(source: str) -> Dict[str, Any] | None:
    with conn() as c:
        cur = c.execute(
            "SELECT as_of, rowcount, payload FROM snapshots WHERE source=? ORDER BY id DESC LIMIT 1",
            (source,)
        )
        row = cur.fetchone()
        if not row:
            return None
        as_of, rowcount, payload = row
        return {"source": source, "as_of": as_of, "rowcount": rowcount, "data": json.loads(payload)}


def historical_by_date(source: str, date_prefix: str) -> List[Dict[str, Any]]:
    # date_prefix e.g. '2025-08-22' (UTC date portion)
    with conn() as c:
        cur = c.execute(
            "SELECT as_of, rowcount, payload FROM snapshots WHERE source=? AND as_of LIKE ? ORDER BY id DESC",
            (source, f"{date_prefix}%")
        )
        out = []
        for as_of, rowcount, payload in cur.fetchall():
            out.append({"source": source, "as_of": as_of, "rowcount": rowcount, "data": json.loads(payload)})
        return out

# --- Optional: S3 helpers for Lambda ---
try:
    import boto3
except Exception:
    boto3 = None


def s3_put_snapshot(bucket: str, key: str, snapshot: Dict[str, Any]):
    if not boto3:
        raise RuntimeError("boto3 not available")
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(snapshot).encode("utf-8"), ContentType="application/json")