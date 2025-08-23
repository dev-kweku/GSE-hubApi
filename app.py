import json, os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from dotenv import load_dotenv

from scraper import fetch_to_dataframe, dataframe_to_records
from storage import init_db, save_snapshot, latest_snapshot, historical_by_date

load_dotenv()

app = FastAPI(title="GSE Feed API", version="1.0")

# Load sources from env JSON
raw_sources = os.getenv("DATA_SOURCES", "[]")
try:
    SOURCES: List[Dict[str, str]] = json.loads(raw_sources)
except Exception:
    SOURCES = []

init_db()

class IngestResponse(BaseModel):
    source: str
    as_of: str
    rowcount: int

@app.get("/health")
def health():
    return {"status": "ok", "sources": [s["name"] for s in SOURCES]}

@app.get("/sources")
def list_sources():
    return SOURCES

@app.post("/ingest", response_model=IngestResponse)
@app.post("/ingest/{source_name}", response_model=IngestResponse)
def ingest(source_name: str | None = None):
    """Manually trigger an ingest for all sources or a single source."""
    targets = SOURCES if not source_name else [s for s in SOURCES if s["name"] == source_name]
    if not targets:
        raise HTTPException(404, detail="Source not found or no sources configured")

    # For simplicity, if multiple targets, just return the last one's stats.
    last = None
    for s in targets:
        df = fetch_to_dataframe(s["url"])  # auto‑detect JSON/CSV/XLSX
        records = dataframe_to_records(df)
        save_snapshot(s["name"], records)
        last = {"source": s["name"], "as_of": "now", "rowcount": len(records)}
    # Reload latest to include the real as_of timestamp
    if last:
        snap = latest_snapshot(last["source"]) or {}
        return IngestResponse(source=snap.get("source", last["source"]), as_of=snap.get("as_of", "now"), rowcount=snap.get("rowcount", 0))

@app.get("/daily")
@app.get("/daily/{source_name}")
def daily(source_name: str | None = None):
    if not SOURCES:
        raise HTTPException(400, detail="No sources configured")
    if not source_name:
        source_name = SOURCES[0]["name"]
    snap = latest_snapshot(source_name)
    if not snap:
        raise HTTPException(404, detail="No snapshot yet; run /ingest or schedule it")
    return JSONResponse(snap)

@app.get("/historical/{date}")
@app.get("/historical/{date}/{source_name}")
def historical(date: str, source_name: str | None = None):
    if not source_name:
        if not SOURCES:
            raise HTTPException(400, detail="No sources configured")
        source_name = SOURCES[0]["name"]
    rows = historical_by_date(source_name, date)
    return JSONResponse({"date": date, "source": source_name, "snapshots": rows})