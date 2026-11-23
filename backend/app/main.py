from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(os.getenv("VYRALIS_DATA_DIR", "./data")).resolve()
MEDIA = ROOT / "media"
MEDIA.mkdir(parents=True, exist_ok=True)
DB: dict[str, dict[str, Any]] = {}

app = FastAPI(title="VYRALIS Local Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("VYRALIS_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "capabilities": ["local-media-ingest"],
    }


@app.get("/api/assets")
def list_assets() -> list[dict[str, Any]]:
    return sorted(DB.values(), key=lambda item: item["created_at"], reverse=True)


@app.post("/api/assets")
async def upload_asset(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    suffix = Path(file.filename).suffix.lower()
    allowed = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".mp3", ".wav", ".m4a", ".aac"}
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported media format.")
    asset_id = str(uuid.uuid4())
    target = MEDIA / f"{asset_id}{suffix}"
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 20 * 1024 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Media exceeds the 20 GB upload limit.")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    asset = {
        "id": asset_id,
        "filename": Path(file.filename).name,
        "size": size,
        "content_type": file.content_type or "application/octet-stream",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": None,
    }
    DB[asset_id] = asset
    return asset


app.mount("/media", StaticFiles(directory=MEDIA), name="media")
