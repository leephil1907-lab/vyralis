from __future__ import annotations

import json
import os
import ipaddress
import socket
from urllib.parse import urlsplit
import shutil
import sqlite3
import subprocess
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(os.getenv("VYRALIS_DATA_DIR", "./data")).resolve()
MEDIA, OUTPUTS = ROOT / "media", ROOT / "outputs"
MEDIA.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "vyralis.sqlite3"
MAX_UPLOAD = int(os.getenv("VYRALIS_MAX_UPLOAD_BYTES", str(5 * 1024**3)))
POOL = ThreadPoolExecutor(max_workers=max(1, int(os.getenv("VYRALIS_WORKERS", "1"))))

app = FastAPI(title="VYRALIS Processing API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("VYRALIS_CORS_ORIGINS", "http://localhost:5173").split(","), allow_credentials=False, allow_methods=["GET", "POST", "PATCH"], allow_headers=["*"])


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY,filename TEXT NOT NULL,size INTEGER NOT NULL,content_type TEXT NOT NULL,path TEXT NOT NULL,created_at TEXT NOT NULL,duration_seconds REAL,width INTEGER,height INTEGER);
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,asset_id TEXT NOT NULL REFERENCES assets(id),title TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),status TEXT NOT NULL,stage TEXT NOT NULL,progress INTEGER NOT NULL,message TEXT NOT NULL,options TEXT NOT NULL,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS clips(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),rank INTEGER NOT NULL,start_seconds REAL NOT NULL,end_seconds REAL NOT NULL,score INTEGER NOT NULL,score_breakdown TEXT NOT NULL,reason TEXT NOT NULL,transcript TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL,output_path TEXT,created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status,created_at);
        CREATE INDEX IF NOT EXISTS idx_clips_project ON clips(project_id,rank);
        """)


def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)


def probe(path: Path) -> dict[str, Any]:
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe is not installed on the processing server.")
    data = json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(path)],120).stdout)
    duration = float(data.get("format",{}).get("duration") or 0)
    video = next((s for s in data.get("streams",[]) if s.get("codec_type")=="video"),{})
    if duration <= 0:
        raise RuntimeError("The uploaded file has no readable media duration.")
    return {"duration_seconds":duration,"width":video.get("width"),"height":video.get("height")}


def update_job(job_id: str, **values: Any) -> None:
    values["updated_at"] = now()
    fields = ", ".join(f"{key}=?" for key in values)
    with connect() as db:
        db.execute(f"UPDATE jobs SET {fields} WHERE id=?",(*values.values(),job_id))


def transcribe(audio_path: Path) -> list[dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Transcription engine is missing. Install backend/requirements.txt and restart the worker.") from exc
    model = WhisperModel(os.getenv("VYRALIS_WHISPER_MODEL","base"),device=os.getenv("VYRALIS_WHISPER_DEVICE","cpu"),compute_type=os.getenv("VYRALIS_WHISPER_COMPUTE","int8"))
    segments, _ = model.transcribe(str(audio_path),word_timestamps=True,vad_filter=True)
    result=[]
    for segment in segments:
        words=[{"start":float(w.start),"end":float(w.end),"text":w.word} for w in (segment.words or [])]
        result.append({"start":float(segment.start),"end":float(segment.end),"text":segment.text.strip(),"words":words})
    if not result:
        raise RuntimeError("Speech recognition returned no transcript segments.")
    return result


def score_candidate(text: str, duration: float) -> tuple[int,dict[str,int],str]:
    lower=text.lower()
    parts={
      "hook":min(100,35+12*sum(x in lower for x in ("why","how","secret","never","imagine","what","because"))),
      "emotion":min(100,30+15*sum(x in lower for x in ("amazing","shocking","love","hate","fail","win","danger","incredible"))),
      "clarity":min(100,45+min(35,len(text.split())//3)),
      "story":75 if any(x in lower for x in ("because","but","so","therefore","then")) else 55,
      "pacing":max(35,min(95,int(100-abs(duration-35)*1.5)))
    }
    return round(sum(parts.values())/len(parts)),parts,"Heuristic score from transcript hook cues, emotional language, clarity, narrative transitions and duration. Not a prediction of virality."


def make_clips(project_id: str, transcript: list[dict[str,Any]], clip_min: int, clip_max: int, clip_count: int) -> int:
    candidates=[]
    for i,first in enumerate(transcript):
        start=max(0.0,first["start"]); end=first["end"]; text=[first["text"]]
        for seg in transcript[i+1:]:
            if seg["end"]-start>clip_max: break
            end=seg["end"]; text.append(seg["text"])
            if end-start>=clip_min: break
        if clip_min<=end-start<=clip_max:
            candidates.append((start,end," ".join(text)))
    selected=[]
    for item in sorted(candidates,key=lambda c:score_candidate(c[2],c[1]-c[0])[0],reverse=True):
        if all(item[1]<=old[0]+2 or item[0]>=old[1]-2 for old in selected):
            selected.append(item)
        if len(selected)>=clip_count: break
    if not selected:
        raise RuntimeError("No transcript windows fit the selected duration. Try a shorter minimum duration.")
    with connect() as db:
        for rank,(start,end,text) in enumerate(selected,1):
            score,parts,reason=score_candidate(text,end-start)
            db.execute("INSERT INTO clips(id,project_id,rank,start_seconds,end_seconds,score,score_breakdown,reason,transcript,title,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
              (str(uuid.uuid4()),project_id,rank,start,end,score,json.dumps(parts),reason,text," ".join(text.split()[:9]).strip(".,!?") or f"Clip {rank}","ready",now()))
    return len(selected)


def process_job(job_id: str) -> None:
    work=ROOT/"work"/job_id; work.mkdir(parents=True,exist_ok=True)
    try:
        with connect() as db:
            job=db.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
            project=db.execute("SELECT * FROM projects WHERE id=?",(job["project_id"],)).fetchone()
            asset=db.execute("SELECT * FROM assets WHERE id=?",(project["asset_id"],)).fetchone()
        source=Path(asset["path"])
        update_job(job_id,status="processing",stage="probing",progress=5,message="Checking media stream")
        meta=probe(source)
        with connect() as db:
            db.execute("UPDATE assets SET duration_seconds=?,width=?,height=? WHERE id=?",(meta["duration_seconds"],meta["width"],meta["height"],asset["id"]))
            db.execute("UPDATE projects SET status='processing',updated_at=? WHERE id=?",(now(),project["id"]))
        audio=work/"audio.wav"
        update_job(job_id,stage="audio",progress=15,message="Extracting audio for transcription")
        run(["ffmpeg","-y","-i",str(source),"-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(audio)])
        update_job(job_id,stage="transcription",progress=30,message="Transcribing speech and aligning words")
        transcript=transcribe(audio)
        update_job(job_id,stage="highlight_analysis",progress=65,message="Finding and ranking self-contained moments")
        options=json.loads(job["options"])
        count=make_clips(project["id"],transcript,int(options.get("min_duration",15)),int(options.get("max_duration",60)),int(options.get("clip_count",8)))
        update_job(job_id,status="completed",stage="complete",progress=100,message=f"Analysis complete. {count} ranked clip candidates are ready.")
        with connect() as db: db.execute("UPDATE projects SET status='review',updated_at=? WHERE id=?",(now(),project["id"]))
    except Exception as exc:
        update_job(job_id,status="failed",stage="failed",error=str(exc),message="Processing failed. Review the error and retry.")
        with connect() as db: db.execute("UPDATE projects SET status='failed',updated_at=? WHERE id=(SELECT project_id FROM jobs WHERE id=?)",(now(),job_id))
    finally:
        shutil.rmtree(work,ignore_errors=True)



def process_export_job(job_id: str, clip_id: str) -> None:
    try:
        with connect() as db:
            clip=db.execute("SELECT c.*,a.path FROM clips c JOIN projects p ON p.id=c.project_id JOIN assets a ON a.id=p.asset_id WHERE c.id=?",(clip_id,)).fetchone()
        if not clip:
            raise RuntimeError("Clip disappeared before rendering.")
        update_job(job_id,status="processing",stage="rendering",progress=10,message="Rendering vertical MP4 with FFmpeg")
        output=OUTPUTS/f"{clip_id}.mp4"
        duration=clip["end_seconds"]-clip["start_seconds"]
        run(["ffmpeg","-y","-ss",str(clip["start_seconds"]),"-i",clip["path"],"-t",str(duration),"-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output)])
        with connect() as db:
            db.execute("UPDATE clips SET output_path=?,status='exported' WHERE id=?",(str(output),clip_id))
        update_job(job_id,status="completed",stage="complete",progress=100,message="MP4 export is ready to download")
    except Exception as exc:
        update_job(job_id,status="failed",stage="failed",error=str(exc),message="MP4 rendering failed")


def enqueue(job_id: str) -> None:
    with connect() as db:
        row=db.execute("SELECT options FROM jobs WHERE id=?",(job_id,)).fetchone()
    if not row:
        return
    options=json.loads(row["options"])
    if options.get("kind")=="export":
        POOL.submit(process_export_job,job_id,options["clip_id"])
    elif options.get("kind")=="url_ingest":
        POOL.submit(process_ingest_job,job_id,options["source_url"])
    else:
        POOL.submit(process_job,job_id)


class URLIngestRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    rights_confirmed: bool
    clip_count: int = Field(default=8, ge=1, le=20)
    min_duration: int = Field(default=15, ge=5, le=120)
    max_duration: int = Field(default=60, ge=10, le=180)


ALLOWED_SOURCE_HOSTS = {"youtube.com", "youtu.be", "twitch.tv", "clips.twitch.tv", "kick.com"}


def validate_source_url(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Enter a valid video URL.") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or port not in (None, 443):
        raise HTTPException(status_code=422, detail="Use a public HTTPS video URL without embedded credentials or a custom port.")
    allowed = any(host == domain or host.endswith("." + domain) for domain in ALLOWED_SOURCE_HOSTS)
    if not allowed:
        raise HTTPException(status_code=422, detail="Supported link sources are YouTube, Twitch and Kick.")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise HTTPException(status_code=422, detail="This source host does not resolve to a public internet address.")
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="The source host could not be resolved.") from exc
    return value.strip()


def process_ingest_job(job_id: str, source_url: str) -> None:
    work = ROOT / "work" / job_id
    work.mkdir(parents=True, exist_ok=True)
    try:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("Link ingestion is unavailable: install backend/requirements.txt with yt-dlp.") from exc
        with connect() as db:
            job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            project = db.execute("SELECT * FROM projects WHERE id=?", (job["project_id"],)).fetchone()
            asset = db.execute("SELECT * FROM assets WHERE id=?", (project["asset_id"],)).fetchone()
        update_job(job_id, status="processing", stage="source_download", progress=3, message="Resolving the permitted public video source")
        output_template = str(work / "source.%(ext)s")
        options = {
            "outtmpl": output_template,
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "nocheckcertificate": False,
            "max_filesize": MAX_UPLOAD,
            "socket_timeout": 30,
            "retries": 2,
            "fragment_retries": 2,
            "restrictfilenames": True,
        }
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(source_url, download=True)
        if not info:
            raise RuntimeError("The provider did not return a downloadable video.")
        candidates = [p for p in work.glob("source.*") if p.is_file() and not p.name.endswith((".part", ".ytdl"))]
        if not candidates:
            raise RuntimeError("The provider did not produce a complete video file.")
        source = max(candidates, key=lambda p: p.stat().st_size)
        size = source.stat().st_size
        if size <= 0 or size > MAX_UPLOAD:
            raise RuntimeError("The downloaded source is empty or exceeds the configured media limit.")
        update_job(job_id, stage="source_validation", progress=10, message="Validating the downloaded media with FFprobe")
        metadata = probe(source)
        suffix = ".mp4" if source.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"} else source.suffix.lower()
        target = MEDIA / f"{asset['id']}{suffix}"
        shutil.move(str(source), target)
        title = str(info.get("title") or asset["filename"])[:240]
        with connect() as db:
            db.execute("UPDATE assets SET filename=?,size=?,content_type=?,path=?,duration_seconds=?,width=?,height=? WHERE id=?",
                       (title + suffix, size, "video/" + suffix.lstrip("."), str(target), metadata["duration_seconds"], metadata["width"], metadata["height"], asset["id"]))
            db.execute("UPDATE projects SET title=?,status='queued',updated_at=? WHERE id=?", (title, now(), project["id"]))
        update_job(job_id, status="queued", stage="queued", progress=12, message="Source imported. Starting transcription and clip analysis.")
        process_job(job_id)
    except Exception as exc:
        update_job(job_id, status="failed", stage="failed", error=str(exc), message="Source ingestion failed. Check the link, provider access and source permissions.")
        with connect() as db:
            db.execute("UPDATE projects SET status='failed',updated_at=? WHERE id=(SELECT project_id FROM jobs WHERE id=?)", (now(), job_id))
    finally:
        shutil.rmtree(work, ignore_errors=True)


class ProjectRequest(BaseModel):
    asset_id: str
    clip_count: int = Field(default=8,ge=1,le=20)
    min_duration: int = Field(default=15,ge=5,le=120)
    max_duration: int = Field(default=60,ge=10,le=180)


class ClipEdit(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    title: str | None = Field(default=None,max_length=120)


@app.on_event("startup")
def startup() -> None:
    init_db()
    with connect() as db:
        rows=db.execute("SELECT id FROM jobs WHERE status IN ('queued','processing')").fetchall()
        db.execute("UPDATE jobs SET status='queued',stage='queued',message='Resuming after worker restart',updated_at=? WHERE status='processing'",(now(),))
    for row in rows: enqueue(row["id"])


@app.get("/api/health")
def health() -> dict[str,Any]:
    return {"status":"ok","version":"0.2.0","capabilities":["persistent-sqlite","media-upload","ffprobe-validation","ffmpeg-audio-extraction","faster-whisper-transcription","ranked-clip-candidates","mp4-export","youtube-twitch-kick-url-ingestion"]}


@app.get("/api/assets")
def list_assets() -> list[dict[str,Any]]:
    with connect() as db: rows=db.execute("SELECT id,filename,size,content_type,created_at,duration_seconds FROM assets ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/assets")
async def upload_asset(file: UploadFile = File(...)) -> dict[str,Any]:
    if not file.filename: raise HTTPException(status_code=400,detail="A filename is required.")
    suffix=Path(file.filename).suffix.lower()
    if suffix not in {".mp4",".mov",".mkv",".webm",".avi"}:
        raise HTTPException(status_code=415,detail="Unsupported media format.")
    asset_id=str(uuid.uuid4()); target=MEDIA/f"{asset_id}{suffix}"; size=0
    try:
        with target.open("wb") as output:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_UPLOAD: raise HTTPException(status_code=413,detail="Upload exceeds configured size limit.")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True); raise
    finally: await file.close()
    try: meta=probe(target)
    except Exception as exc:
        target.unlink(missing_ok=True); raise HTTPException(status_code=422,detail=f"Media validation failed: {exc}") from exc
    asset={"id":asset_id,"filename":Path(file.filename).name,"size":size,"content_type":file.content_type or "application/octet-stream","created_at":now(),"duration_seconds":meta["duration_seconds"]}
    with connect() as db:
        db.execute("INSERT INTO assets(id,filename,size,content_type,path,created_at,duration_seconds,width,height) VALUES(?,?,?,?,?,?,?,?,?)",(asset_id,asset["filename"],size,asset["content_type"],str(target),asset["created_at"],meta["duration_seconds"],meta["width"],meta["height"]))
    return asset


@app.post("/api/ingest/url")
def ingest_url(payload: URLIngestRequest) -> dict[str, Any]:
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you have permission to download and process this video.")
    source_url = validate_source_url(payload.url)
    project_id, asset_id, job_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    timestamp = now()
    placeholder_name = "Linked video " + asset_id[:8]
    options = payload.model_dump() | {"kind": "url_ingest", "source_url": source_url}
    with connect() as db:
        db.execute("INSERT INTO assets(id,filename,size,content_type,path,created_at) VALUES(?,?,?,?,?,?)",
                   (asset_id, placeholder_name, 0, "video/unknown", "", timestamp))
        db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)", (project_id, asset_id, placeholder_name, "queued", timestamp, timestamp))
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (job_id, project_id, "queued", "queued", 0, "Waiting for source ingestion", json.dumps(options), None, timestamp, timestamp))
    enqueue(job_id)
    return {"id": project_id, "title": placeholder_name, "status": "queued", "job_id": job_id, "created_at": timestamp}


@app.post("/api/projects")
def create_project(payload: ProjectRequest) -> dict[str,Any]:
    with connect() as db:
        asset=db.execute("SELECT * FROM assets WHERE id=?",(payload.asset_id,)).fetchone()
        if not asset: raise HTTPException(status_code=404,detail="Uploaded media asset not found.")
        project_id,job_id=str(uuid.uuid4()),str(uuid.uuid4()); timestamp=now(); title=Path(asset["filename"]).stem
        db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)",(project_id,asset["id"],title,"queued",timestamp,timestamp))
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",(job_id,project_id,"queued","queued",0,"Waiting for a processing worker",json.dumps(payload.model_dump()),None,timestamp,timestamp))
    enqueue(job_id)
    return {"id":project_id,"title":title,"status":"queued","job_id":job_id,"created_at":timestamp}


@app.get("/api/projects")
def list_projects() -> list[dict[str,Any]]:
    with connect() as db:
        rows=db.execute("SELECT p.*,a.filename,a.duration_seconds,(SELECT COUNT(*) FROM clips c WHERE c.project_id=p.id) AS clip_count FROM projects p JOIN assets a ON a.id=p.asset_id ORDER BY p.created_at DESC").fetchall()
    return [dict(r) for r in rows]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str,Any]:
    with connect() as db: row=db.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
    if not row: raise HTTPException(status_code=404,detail="Processing job not found.")
    result=dict(row); result["options"]=json.loads(result["options"]); return result


@app.get("/api/projects/{project_id}/clips")
def list_clips(project_id: str) -> list[dict[str,Any]]:
    with connect() as db: rows=db.execute("SELECT * FROM clips WHERE project_id=? ORDER BY score DESC,rank ASC",(project_id,)).fetchall()
    result=[]
    for row in rows:
        item=dict(row); item["score_breakdown"]=json.loads(item["score_breakdown"]); result.append(item)
    return result


@app.patch("/api/clips/{clip_id}")
def edit_clip(clip_id: str,payload: ClipEdit) -> dict[str,Any]:
    if payload.end_seconds<=payload.start_seconds: raise HTTPException(status_code=422,detail="End time must be after start time.")
    with connect() as db:
        row=db.execute("SELECT * FROM clips WHERE id=?",(clip_id,)).fetchone()
        if not row: raise HTTPException(status_code=404,detail="Clip not found.")
        db.execute("UPDATE clips SET start_seconds=?,end_seconds=?,title=?,status='edited',output_path=NULL WHERE id=?",(payload.start_seconds,payload.end_seconds,payload.title or row["title"],clip_id))
        updated=db.execute("SELECT * FROM clips WHERE id=?",(clip_id,)).fetchone()
    item=dict(updated); item["score_breakdown"]=json.loads(item["score_breakdown"]); return item


@app.post("/api/clips/{clip_id}/export")
def export_clip(clip_id: str) -> dict[str,Any]:
    with connect() as db:
        clip=db.execute("SELECT * FROM clips WHERE id=?",(clip_id,)).fetchone()
        if not clip:
            raise HTTPException(status_code=404,detail="Clip not found.")
        job_id=str(uuid.uuid4()); timestamp=now()
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",(job_id,clip["project_id"],"queued","queued",0,"Waiting for a render worker",json.dumps({"kind":"export","clip_id":clip_id}),None,timestamp,timestamp))
    enqueue(job_id)
    return {"clip_id":clip_id,"job_id":job_id,"status":"queued"}


@app.get("/api/clips/{clip_id}/download")
def download_clip(clip_id: str) -> FileResponse:
    with connect() as db: row=db.execute("SELECT output_path,title FROM clips WHERE id=?",(clip_id,)).fetchone()
    if not row or not row["output_path"] or not Path(row["output_path"]).is_file(): raise HTTPException(status_code=404,detail="Export this clip before downloading it.")
    return FileResponse(row["output_path"],media_type="video/mp4",filename=f"{row['title']}.mp4")


@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict[str,Any]:
    with connect() as db:
        row=db.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
        if not row: raise HTTPException(status_code=404,detail="Processing job not found.")
        if row["status"]!="failed": raise HTTPException(status_code=409,detail="Only failed jobs can be retried.")
        db.execute("DELETE FROM clips WHERE project_id=?",(row["project_id"],))
        db.execute("UPDATE jobs SET status='queued',stage='queued',progress=0,error=NULL,message='Retry queued',updated_at=? WHERE id=?",(now(),job_id))
        db.execute("UPDATE projects SET status='queued',updated_at=? WHERE id=?",(now(),row["project_id"]))
    enqueue(job_id); return {"id":job_id,"status":"queued"}


@app.get("/api/projects/{project_id}/source")
def project_source(project_id: str) -> FileResponse:
    with connect() as db:
        row = db.execute("SELECT a.path,a.filename FROM projects p JOIN assets a ON a.id=p.asset_id WHERE p.id=?", (project_id,)).fetchone()
    if not row or not Path(row["path"]).is_file():
        raise HTTPException(status_code=404, detail="Source media is unavailable.")
    return FileResponse(row["path"], media_type="video/mp4", filename=row["filename"])
