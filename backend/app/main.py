from __future__ import annotations

import json
import os
import ipaddress
import re
import socket
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

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from .captions import CAPTION_STYLES, DEFAULT_STYLE, build_ass, build_srt, build_vtt
from .delivery import (
    DESTINATIONS,
    PRESETS,
    approval_gate,
    evaluate_export,
    preset_geometry,
    preset_list,
    validate_packaging,
)
from .hooks import extract_hook, extract_title, suggest_hashtags
from .ingest import (
    DEFAULT_MAX_DURATION,
    SourceRejected,
    enforce_duration,
    parse_metadata,
    parse_source_url,
    safe_stem,
    ytdlp_download_cmd,
    ytdlp_metadata_cmd,
)
from .reframe import DEFAULT_LAYOUT, LAYOUTS, build_filter, detect_focus_points, layout_report, plan_focus

ROOT = Path(os.getenv("VYRALIS_DATA_DIR", "./data")).resolve()
MEDIA, OUTPUTS = ROOT / "media", ROOT / "outputs"
MEDIA.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "vyralis.sqlite3"
MAX_UPLOAD = int(os.getenv("VYRALIS_MAX_UPLOAD_BYTES", str(5 * 1024**3)))
POOL = ThreadPoolExecutor(max_workers=max(1, int(os.getenv("VYRALIS_WORKERS", "1"))))

app = FastAPI(title="VYRALIS Processing API", version="0.3.0")
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
        CREATE TABLE IF NOT EXISTS clip_exports(id TEXT PRIMARY KEY,clip_id TEXT NOT NULL REFERENCES clips(id),preset TEXT NOT NULL,status TEXT NOT NULL,job_id TEXT,output_path TEXT,width INTEGER,height INTEGER,duration_seconds REAL,quality_report TEXT,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_exports_clip ON clip_exports(clip_id,created_at);
        CREATE TABLE IF NOT EXISTS clip_packaging(clip_id TEXT NOT NULL REFERENCES clips(id),destination TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,hashtags TEXT NOT NULL,approved INTEGER NOT NULL DEFAULT 0,approved_at TEXT,updated_at TEXT NOT NULL,PRIMARY KEY(clip_id,destination));
        CREATE TABLE IF NOT EXISTS transcripts(project_id TEXT PRIMARY KEY REFERENCES projects(id),segments TEXT NOT NULL,words TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sources(project_id TEXT PRIMARY KEY REFERENCES projects(id),platform TEXT NOT NULL,url TEXT NOT NULL,title TEXT NOT NULL,uploader TEXT,metadata TEXT,rights_attested_at TEXT,created_at TEXT NOT NULL);
        """)
    ensure_column("clips", "hook", "TEXT")
    ensure_column("clip_exports", "options", "TEXT")
    ensure_column("clip_exports", "layout", "TEXT")


def ensure_column(table: str, column: str, ddl: str) -> None:
    """Small forward-only migration for SQLite databases created by an older build."""
    with connect() as db:
        columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


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
            hook=extract_hook(text)
            title=extract_title(text) or f"Clip {rank}"
            db.execute("INSERT INTO clips(id,project_id,rank,start_seconds,end_seconds,score,score_breakdown,reason,transcript,title,status,created_at,hook) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (str(uuid.uuid4()),project_id,rank,start,end,score,json.dumps(parts),reason,text,title,"ready",now(),hook))
    return len(selected)


def save_transcript(project_id: str, transcript: list[dict[str, Any]]) -> None:
    words = [word for segment in transcript for word in segment.get("words", [])]
    with connect() as db:
        db.execute(
            "INSERT INTO transcripts(project_id,segments,words,created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(project_id) DO UPDATE SET segments=excluded.segments,words=excluded.words,created_at=excluded.created_at",
            (project_id, json.dumps(transcript), json.dumps(words), now()),
        )


def load_words(project_id: str) -> list[dict[str, Any]]:
    with connect() as db:
        row = db.execute("SELECT words FROM transcripts WHERE project_id=?", (project_id,)).fetchone()
    return json.loads(row["words"]) if row else []


def stop_if_cancelled(job_id: str) -> bool:
    """Terminal states for a job whose creator asked to cancel it."""
    if not cancel_requested(job_id):
        return False
    with connect() as db:
        db.execute("UPDATE jobs SET status='cancelled',stage='cancelled',message='Cancelled by the creator',updated_at=? WHERE id=?", (now(), job_id))
        db.execute("UPDATE projects SET status='cancelled',updated_at=? WHERE id=(SELECT project_id FROM jobs WHERE id=?)", (now(), job_id))
    return True


MAX_SOURCE_BYTES = int(os.getenv("VYRALIS_MAX_SOURCE_BYTES", str(4 * 1024**3)))


def download_source(job_id: str, asset: sqlite3.Row, options: dict[str, Any]) -> Path:
    """Fetch a link through yt-dlp into the media store, then re-probe it."""
    if not shutil.which("yt-dlp"):
        raise RuntimeError("yt-dlp is not installed on the processing server. Install it with: pip install yt-dlp")
    url = str(options.get("source_url") or "")
    target = Path(asset["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    update_job(job_id, status="processing", stage="download", progress=4, message="Downloading the source with yt-dlp")
    # yt-dlp may keep or add an extension, so download beside the target and settle it afterwards.
    template = target.with_name(f"{target.stem}.%(ext)s")
    run(ytdlp_download_cmd(url, template), timeout=60 * 60 * 4)
    produced = [path for path in target.parent.glob(f"{target.stem}.*") if path.is_file() and path != target]
    if target.exists() and target.stat().st_size > 0:
        produced.append(target)
    if not produced:
        raise RuntimeError("yt-dlp finished without producing a media file.")
    chosen = max(produced, key=lambda path: path.stat().st_size)
    if chosen != target:
        if chosen.suffix.lower() != ".mp4":
            run(["ffmpeg", "-y", "-i", str(chosen), "-c", "copy", "-movflags", "+faststart", str(target)])
            chosen.unlink(missing_ok=True)
        else:
            chosen.replace(target)
    for leftover in target.parent.glob(f"{target.stem}.*"):
        if leftover != target and leftover.is_file():
            leftover.unlink(missing_ok=True)
    if not target.exists() or target.stat().st_size == 0:
        raise RuntimeError("yt-dlp finished without producing a readable media file.")
    if target.stat().st_size > MAX_SOURCE_BYTES:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded source exceeds the {MAX_SOURCE_BYTES / 1024**3:.0f} GB limit.")
    return target


def process_job(job_id: str) -> None:
    work=ROOT/"work"/job_id; work.mkdir(parents=True,exist_ok=True)
    try:
        if stop_if_cancelled(job_id):
            return
        with connect() as db:
            job=db.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
            project=db.execute("SELECT * FROM projects WHERE id=?",(job["project_id"],)).fetchone()
            asset=db.execute("SELECT * FROM assets WHERE id=?",(project["asset_id"],)).fetchone()
        options=json.loads(job["options"])
        if options.get("kind") in {"ingest","url_ingest"}:
            download_source(job_id, asset, options)
            with connect() as db:
                kind_meta=probe(Path(asset["path"]))
                db.execute("UPDATE assets SET size=?,duration_seconds=?,width=?,height=? WHERE id=?",
                    (Path(asset["path"]).stat().st_size,kind_meta["duration_seconds"],kind_meta["width"],kind_meta["height"],asset["id"]))
        if stop_if_cancelled(job_id): return
        source=Path(asset["path"])
        update_job(job_id,status="processing",stage="probing",progress=8,message="Checking media stream")
        meta=probe(source)
        with connect() as db:
            db.execute("UPDATE assets SET duration_seconds=?,width=?,height=? WHERE id=?",(meta["duration_seconds"],meta["width"],meta["height"],asset["id"]))
            db.execute("UPDATE projects SET status='processing',updated_at=? WHERE id=?",(now(),project["id"]))
        if stop_if_cancelled(job_id): return
        audio=work/"audio.wav"
        update_job(job_id,stage="audio",progress=15,message="Extracting audio for transcription")
        run(["ffmpeg","-y","-i",str(source),"-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(audio)])
        if stop_if_cancelled(job_id): return
        update_job(job_id,stage="transcription",progress=30,message="Transcribing speech and aligning words")
        transcript=transcribe(audio)
        save_transcript(project["id"], transcript)
        if stop_if_cancelled(job_id): return
        update_job(job_id,stage="highlight_analysis",progress=65,message="Finding and ranking self-contained moments")
        count=make_clips(project["id"],transcript,int(options.get("min_duration",15)),int(options.get("max_duration",60)),int(options.get("clip_count",8)))
        update_job(job_id,status="completed",stage="complete",progress=100,message=f"Analysis complete. {count} ranked clip candidates are ready.")
        with connect() as db: db.execute("UPDATE projects SET status='review',updated_at=? WHERE id=?",(now(),project["id"]))
    except Exception as exc:
        update_job(job_id,status="failed",stage="failed",error=str(exc),message="Processing failed. Review the error and retry.")
        with connect() as db: db.execute("UPDATE projects SET status='failed',updated_at=? WHERE id=(SELECT project_id FROM jobs WHERE id=?)",(now(),job_id))
    finally:
        shutil.rmtree(work,ignore_errors=True)



def probe_render(path: Path) -> dict[str, Any]:
    """Inspect a rendered file. Separate from probe() so exports can be checked independently."""
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe is not installed on the processing server.")
    data = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height", "-of", "json", str(path)], 180).stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return {
        "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        "size_bytes": int(float(path.stat().st_size if path.exists() else 0)),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "has_video": bool(video),
        "has_audio": bool(audio),
    }


def filter_probe(path: Path, vf: str, pattern: str) -> list[float]:
    """Run a measurement filter (blackdetect/freezedetect) and return the reported durations."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", vf, "-an", "-f", "null", "-"],
        capture_output=True, text=True, timeout=900,
    )
    return [float(match) for match in re.findall(pattern, result.stderr)]


def measure_mean_volume(path: Path) -> float | None:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"],
        capture_output=True, text=True, timeout=900,
    )
    match = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", result.stderr)
    return float(match.group(1)) if match else None


def inspect_render(path: Path, expected_duration: float, preset: str) -> dict[str, Any]:
    """Probe the render and run the automated quality checks used before a file is offered."""
    meta = probe_render(path)
    black_seconds = round(sum(filter_probe(path, "blackdetect=d=0.1:pix_th=0.10", r"black_duration:([0-9.]+)")), 3)
    frozen_seconds = round(sum(filter_probe(path, "freezedetect=n=0.003:d=1", r"freeze_duration: ([0-9.]+)")), 3)
    mean_volume = measure_mean_volume(path) if meta.get("has_audio") else None
    return evaluate_export(
        expected_duration=expected_duration,
        preset=preset,
        probe=meta,
        black_seconds=black_seconds,
        frozen_seconds=frozen_seconds,
        mean_volume_db=mean_volume,
    )


def update_export(export_id: str, **values: Any) -> None:
    values["updated_at"] = now()
    fields = ", ".join(f"{key}=?" for key in values)
    with connect() as db:
        db.execute(f"UPDATE clip_exports SET {fields} WHERE id=?", (*values.values(), export_id))


def cancel_requested(job_id: str) -> bool:
    with connect() as db:
        row = db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    return bool(row) and row["status"] in {"cancelling", "cancelled"}


def process_export_job(job_id: str, export_id: str) -> None:
    output: Path | None = None
    work = OUTPUTS / "work" / export_id
    try:
        work.mkdir(parents=True, exist_ok=True)
        with connect() as db:
            export = db.execute(
                "SELECT e.*, c.start_seconds, c.end_seconds, c.title, c.hook, c.id AS clip_id, c.project_id, "
                "a.path AS source_path, a.width AS src_w, a.height AS src_h "
                "FROM clip_exports e JOIN clips c ON c.id=e.clip_id JOIN projects p ON p.id=c.project_id "
                "JOIN assets a ON a.id=p.asset_id WHERE e.id=?",
                (export_id,),
            ).fetchone()
        if not export:
            raise RuntimeError("Export record disappeared before rendering.")

        options: dict[str, Any] = json.loads(export["options"]) if export["options"] else {}
        captions_on = bool(options.get("captions", True))
        caption_style = options.get("caption_style") or DEFAULT_STYLE
        if caption_style not in CAPTION_STYLES:
            caption_style = DEFAULT_STYLE
        layout = options.get("layout") or DEFAULT_LAYOUT
        if layout not in LAYOUTS:
            layout = DEFAULT_LAYOUT
        hook_overlay = bool(options.get("hook_overlay", True))

        if cancel_requested(job_id):
            update_export(export_id, status="cancelled", error="Cancelled before rendering")
            update_job(job_id, status="cancelled", stage="cancelled", message="Export cancelled")
            return

        width, height = preset_geometry(export["preset"])
        duration = max(0.1, export["end_seconds"] - export["start_seconds"])
        output = OUTPUTS / f"{export['clip_id']}-{export['preset'].replace(':', 'x')}-{export_id[:8]}.mp4"

        update_export(export_id, status="rendering", error=None)
        update_job(job_id, status="processing", stage="rendering", progress=10, message=f"Rendering {export['preset']} MP4 with FFmpeg")

        ass_path: Path | None = None
        if captions_on:
            words = load_words(export["project_id"])
            if words:
                ass_path = work / "captions.ass"
                ass_path.write_text(
                    build_ass(
                        words, float(export["start_seconds"]), float(export["end_seconds"]),
                        width=width, height=height, style=caption_style,
                        hook=export["hook"] if hook_overlay else None,
                    ),
                    encoding="utf-8",
                )

        focus_points: list[float] = []
        if layout == "face":
            update_job(job_id, stage="framing", progress=8, message="Sampling frames to follow the subject")
            focus_points = detect_focus_points(Path(export["source_path"]))
        focus = plan_focus(focus_points)
        src_w = int(export["src_w"] or 1920)
        src_h = int(export["src_h"] or 1080)
        graph = build_filter(
            layout=layout, src_w=src_w, src_h=src_h, out_w=width, out_h=height,
            focus_x=focus, focus_y=0.5, ass_path=ass_path,
        )

        run([
            "ffmpeg", "-y", "-ss", str(export["start_seconds"]), "-i", export["source_path"], "-t", str(duration),
            "-filter_complex", graph, "-map", "[vout]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output),
        ])

        update_export(export_id, status="validating")
        update_job(job_id, stage="quality_check", progress=70, message="Checking the render for broken frames, silence and size")
        report = inspect_render(output, duration, export["preset"])
        frame = layout_report(layout, focus_points)
        report["render"] = {
            "captions": bool(ass_path),
            "caption_style": caption_style if ass_path else None,
            "hook_overlay": bool(hook_overlay and export["hook"]),
            "layout": frame["layout"],
            "tracked": frame["tracked"],
            "framing_note": frame["note"],
        }

        if cancel_requested(job_id):
            output.unlink(missing_ok=True)
            update_export(export_id, status="cancelled", error="Cancelled after rendering")
            update_job(job_id, status="cancelled", stage="cancelled", message="Export cancelled")
            return

        rendered = report["metrics"]
        if report["status"] == "fail":
            output.unlink(missing_ok=True)
            update_export(export_id, status="failed", quality_report=json.dumps(report), error=report["summary"], layout=frame["layout"])
            update_job(job_id, status="failed", stage="quality_check", error=report["summary"], message="The render failed automated quality inspection")
            with connect() as db:
                db.execute("UPDATE clips SET status='export_failed' WHERE id=?", (export["clip_id"],))
            return

        with connect() as db:
            db.execute(
                "UPDATE clip_exports SET status='ready',output_path=?,width=?,height=?,duration_seconds=?,quality_report=?,error=NULL,layout=? WHERE id=?",
                (str(output), rendered["width"], rendered["height"], rendered["duration_seconds"], json.dumps(report), frame["layout"], export_id),
            )
            db.execute("UPDATE clips SET output_path=?,status='exported' WHERE id=?", (str(output), export["clip_id"]))
        update_job(job_id, status="completed", stage="complete", progress=100, message=report["summary"] + " Ready to download.")
    except Exception as exc:
        if output is not None:
            output.unlink(missing_ok=True)
        update_export(export_id, status="failed", error=str(exc))
        update_job(job_id, status="failed", stage="failed", error=str(exc), message="MP4 rendering failed")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def enqueue(job_id: str) -> None:
    with connect() as db:
        row=db.execute("SELECT options FROM jobs WHERE id=?",(job_id,)).fetchone()
    if not row:
        return
    options=json.loads(row["options"])
    if options.get("kind")=="export":
        POOL.submit(process_export_job,job_id,options["export_id"])
    else:
        POOL.submit(process_job,job_id)


class URLIngestRequest(BaseModel):
    """Legacy /api/ingest/url contract kept for compatible clients."""

    url: str = Field(min_length=8, max_length=2048)
    rights_confirmed: bool
    clip_count: int = Field(default=8, ge=1, le=20)
    min_duration: int = Field(default=15, ge=5, le=120)
    max_duration: int = Field(default=60, ge=10, le=180)


def validate_source_url(value: str) -> str:
    """Validate a public provider link for the legacy ingestion endpoint.

    Combines the shared URL policy in ``ingest.parse_source_url`` (scheme, host allowlist,
    credentials, ports) with a DNS resolution check, so a provider hostname that resolves
    to a private or link-local address is rejected before any worker sees it.
    """
    try:
        parsed = parse_source_url(value)
    except SourceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    host = parsed["host"]
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError) as exc:
        raise HTTPException(status_code=422, detail="The source host could not be resolved.") from exc
    if not addresses:
        raise HTTPException(status_code=422, detail="The source host could not be resolved.")
    for entry in addresses:
        try:
            address = ipaddress.ip_address(entry[4][0])
        except (ValueError, IndexError) as exc:
            raise HTTPException(status_code=422, detail="The source host resolved to an invalid address.") from exc
        if not address.is_global:
            raise HTTPException(status_code=422, detail="This source host does not resolve to a public internet address.")
    return parsed["url"]


class ProjectRequest(BaseModel):
    asset_id: str
    clip_count: int = Field(default=8,ge=1,le=20)
    min_duration: int = Field(default=15,ge=5,le=120)
    max_duration: int = Field(default=60,ge=10,le=180)


class ClipEdit(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    title: str | None = Field(default=None,max_length=120)
    hook: str | None = Field(default=None,max_length=160)


class ExportRequest(BaseModel):
    preset: str = "9:16"
    captions: bool = True
    caption_style: str = DEFAULT_STYLE
    layout: str = DEFAULT_LAYOUT
    hook_overlay: bool = True


class SourceRequest(BaseModel):
    url: str = Field(max_length=2048)


class LinkRequest(SourceRequest):
    rights_attested: bool = False
    clip_count: int = Field(default=8, ge=1, le=20)
    min_duration: int = Field(default=15, ge=5, le=120)
    max_duration: int = Field(default=60, ge=10, le=180)


class PackagingRequest(BaseModel):
    destination: str
    title: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=6000)
    hashtags: list[str] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    destination: str
    approved: bool = True


@app.on_event("startup")
def startup() -> None:
    init_db()
    with connect() as db:
        rows=db.execute("SELECT id FROM jobs WHERE status IN ('queued','processing')").fetchall()
        db.execute("UPDATE jobs SET status='queued',stage='queued',message='Resuming after worker restart',updated_at=? WHERE status='processing'",(now(),))
    for row in rows: enqueue(row["id"])


@app.get("/api/health")
def health() -> dict[str,Any]:
    return {"status":"ok","version":"0.3.0","capabilities":["persistent-sqlite","media-upload","ffprobe-validation","ffmpeg-audio-extraction","faster-whisper-transcription","ranked-clip-candidates","mp4-export","export-presets","render-quality-inspection","packaging-approval","job-cancellation","link-ingestion","youtube-twitch-kick-url-ingestion","word-timed-captions","hook-titles","subject-framing"]}


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
    """Compatibility endpoint: same queue and worker path as /api/projects/from-link."""
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you have permission to download and process this video.")
    source_url = validate_source_url(payload.url)
    platform = parse_source_url(source_url)["platform"]
    project_id, asset_id, job_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    timestamp = now()
    title = "Linked video " + asset_id[:8]
    target = MEDIA / f"{asset_id}.mp4"
    options = {
        "kind": "ingest",
        "source_url": source_url,
        "platform": platform,
        "clip_count": payload.clip_count,
        "min_duration": payload.min_duration,
        "max_duration": payload.max_duration,
    }
    with connect() as db:
        db.execute("INSERT INTO assets(id,filename,size,content_type,path,created_at,duration_seconds,width,height) VALUES(?,?,?,?,?,?,?,?,?)",
                   (asset_id, title + ".mp4", 0, "video/mp4", str(target), timestamp, None, None, None))
        db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)", (project_id, asset_id, title, "queued", timestamp, timestamp))
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (job_id, project_id, "queued", "queued", 0, "Waiting for source ingestion", json.dumps(options), None, timestamp, timestamp))
        db.execute("INSERT INTO sources(project_id,platform,url,title,uploader,metadata,rights_attested_at,created_at) VALUES(?,?,?,?,?,?,?,?)",
                   (project_id, platform, source_url, title, "", "{}", timestamp, timestamp))
    enqueue(job_id)
    return {"id": project_id, "title": title, "status": "queued", "job_id": job_id, "created_at": timestamp}


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
        db.execute("UPDATE clips SET start_seconds=?,end_seconds=?,title=?,hook=?,status='edited',output_path=NULL WHERE id=?",(payload.start_seconds,payload.end_seconds,payload.title or row["title"],payload.hook if payload.hook is not None else row["hook"],clip_id))
        updated=db.execute("SELECT * FROM clips WHERE id=?",(clip_id,)).fetchone()
    item=dict(updated); item["score_breakdown"]=json.loads(item["score_breakdown"]); return item


@app.get("/api/export-presets")
def list_export_presets() -> dict[str,Any]:
    return {"presets":preset_list()}


@app.get("/api/destinations")
def list_destinations() -> list[dict[str,Any]]:
    return [{"destination":key,**value} for key,value in DESTINATIONS.items()]


@app.post("/api/clips/{clip_id}/export")
def export_clip(clip_id: str, payload: ExportRequest | None = Body(default=None)) -> dict[str,Any]:
    preset=(payload.preset if payload else "9:16") or "9:16"
    try:
        width,height=preset_geometry(preset)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    options={"captions":bool(payload.captions) if payload else True,
             "caption_style":(payload.caption_style if payload and payload.caption_style in CAPTION_STYLES else DEFAULT_STYLE),
             "layout":(payload.layout if payload and payload.layout in LAYOUTS else DEFAULT_LAYOUT),
             "hook_overlay":bool(payload.hook_overlay) if payload else True}
    with connect() as db:
        clip=db.execute("SELECT * FROM clips WHERE id=?",(clip_id,)).fetchone()
        if not clip:
            raise HTTPException(status_code=404,detail="Clip not found.")
        existing=db.execute("SELECT * FROM clip_exports WHERE clip_id=? AND preset=? AND status IN ('queued','rendering','validating') ORDER BY created_at DESC LIMIT 1",(clip_id,preset)).fetchone()
        if existing and existing["options"] and json.loads(existing["options"])!=options:
            existing=None
        if existing:
            return {"clip_id":clip_id,"export_id":existing["id"],"job_id":existing["job_id"],"preset":preset,"status":existing["status"],"idempotent":True}
        export_id,job_id=str(uuid.uuid4()),str(uuid.uuid4()); timestamp=now()
        db.execute("INSERT INTO clip_exports(id,clip_id,preset,status,job_id,output_path,width,height,duration_seconds,quality_report,error,created_at,updated_at,options,layout) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (export_id,clip_id,preset,"queued",job_id,None,width,height,None,None,None,timestamp,timestamp,json.dumps(options),options.get("layout")))
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",(job_id,clip["project_id"],"queued","queued",0,f"Waiting for a render worker ({preset})",json.dumps({"kind":"export","clip_id":clip_id,"export_id":export_id,"preset":preset}),None,timestamp,timestamp))
    enqueue(job_id)
    return {"clip_id":clip_id,"export_id":export_id,"job_id":job_id,"preset":preset,"status":"queued","idempotent":False}


def serialize_export(row: sqlite3.Row) -> dict[str,Any]:
    item=dict(row)
    report=item.get("quality_report")
    item["quality_report"]=json.loads(report) if report else None
    raw_options=item.get("options")
    item["options"]=json.loads(raw_options) if raw_options else None
    item["download_url"]=f"/api/exports/{item['id']}/download" if item["status"]=="ready" else None
    return item


@app.get("/api/clips/{clip_id}/exports")
def list_clip_exports(clip_id: str) -> list[dict[str,Any]]:
    with connect() as db:
        rows=db.execute("SELECT * FROM clip_exports WHERE clip_id=? ORDER BY created_at DESC",(clip_id,)).fetchall()
    return [serialize_export(row) for row in rows]


@app.get("/api/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    with connect() as db:
        row=db.execute("SELECT e.*,c.title FROM clip_exports e JOIN clips c ON c.id=e.clip_id WHERE e.id=?",(export_id,)).fetchone()
    if not row or row["status"]!="ready" or not row["output_path"] or not Path(row["output_path"]).is_file():
        raise HTTPException(status_code=404,detail="This export is not available for download.")
    report=json.loads(row["quality_report"]) if row["quality_report"] else None
    if report and report.get("status")=="fail":
        raise HTTPException(status_code=409,detail="This export failed quality inspection and cannot be downloaded.")
    return FileResponse(row["output_path"],media_type="video/mp4",filename=f"{row['title']}-{row['preset'].replace(':','x')}.mp4")


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
    return FileResponse(row["path"], media_type=("video/mp4"), filename=row["filename"])


def default_copy(clip: sqlite3.Row) -> tuple[str, str, list[str]]:
    """Start packaging from what the transcript actually says, never from invented claims."""
    words = " ".join(str(clip["transcript"]).split())
    description = (words[:260] + "…") if len(words) > 260 else words
    return clip["title"], description, []


def latest_ready_export(db: sqlite3.Connection, clip_id: str) -> sqlite3.Row | None:
    return db.execute(
        "SELECT id,preset,status,quality_report,created_at FROM clip_exports "
        "WHERE clip_id=? AND status='ready' ORDER BY created_at DESC LIMIT 1",
        (clip_id,),
    ).fetchone()


def packaging_payload(db: sqlite3.Connection, clip: sqlite3.Row, destination: str) -> dict[str, Any]:
    row = db.execute("SELECT * FROM clip_packaging WHERE clip_id=? AND destination=?", (clip["id"], destination)).fetchone()
    if row:
        title, description = row["title"], row["description"]
        tags = json.loads(row["hashtags"])
        approved, approved_at = bool(row["approved"]), row["approved_at"]
    else:
        title, description, tags = default_copy(clip)
        approved, approved_at = False, None
    validation = validate_packaging(destination=destination, title=title, description=description, hashtags=tags)
    export = latest_ready_export(db, clip["id"])
    quality = json.loads(export["quality_report"]) if export and export["quality_report"] else None
    gate = approval_gate(
        quality_status=quality["status"] if quality else None,
        packaging_valid=validation["valid"],
        destination=destination,
    )
    return {
        "clip_id": clip["id"],
        "clip_title": clip["title"],
        "project_id": clip["project_id"],
        "destination": destination,
        "destination_label": DESTINATIONS[destination]["label"],
        "title": title,
        "description": description,
        "hashtags": validation["hashtags"],
        "approved": approved,
        "approved_at": approved_at,
        "validation": validation,
        "approval_gate": gate,
        "eligible": approved and gate["allowed"],
        "export": {
            "id": export["id"],
            "preset": export["preset"],
            "quality_status": quality["status"] if quality else None,
            "quality_summary": quality["summary"] if quality else None,
            "download_url": f"/api/exports/{export['id']}/download",
        } if export else None,
    }


@app.get("/api/clips/{clip_id}/packaging")
def get_packaging(clip_id: str) -> list[dict[str, Any]]:
    with connect() as db:
        clip = db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")
        return [packaging_payload(db, clip, destination) for destination in DESTINATIONS]


@app.put("/api/clips/{clip_id}/packaging")
def save_packaging(clip_id: str, payload: PackagingRequest) -> dict[str, Any]:
    if payload.destination not in DESTINATIONS:
        raise HTTPException(status_code=422, detail=f"Unknown destination '{payload.destination}'.")
    with connect() as db:
        clip = db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")
        existing = db.execute("SELECT * FROM clip_packaging WHERE clip_id=? AND destination=?", (clip_id, payload.destination)).fetchone()
        tags = validate_packaging(destination=payload.destination, title=payload.title, description=payload.description, hashtags=payload.hashtags)["hashtags"]
        changed = bool(existing) and (
            existing["title"] != payload.title.strip()
            or existing["description"] != payload.description.strip()
            or json.loads(existing["hashtags"]) != tags
        )
        stamp = now()
        db.execute(
            "INSERT INTO clip_packaging(clip_id,destination,title,description,hashtags,approved,approved_at,updated_at) VALUES(?,?,?,?,?,0,NULL,?) "
            "ON CONFLICT(clip_id,destination) DO UPDATE SET title=excluded.title,description=excluded.description,hashtags=excluded.hashtags,updated_at=excluded.updated_at",
            (clip_id, payload.destination, payload.title.strip(), payload.description.strip(), json.dumps(tags), stamp),
        )
        if changed:
            # Approval applies to the exact copy the creator reviewed, so editing revokes it.
            db.execute("UPDATE clip_packaging SET approved=0,approved_at=NULL WHERE clip_id=? AND destination=?", (clip_id, payload.destination))
        return packaging_payload(db, clip, payload.destination)


@app.post("/api/clips/{clip_id}/packaging/approval")
def approve_packaging(clip_id: str, payload: ApprovalRequest) -> dict[str, Any]:
    if payload.destination not in DESTINATIONS:
        raise HTTPException(status_code=422, detail=f"Unknown destination '{payload.destination}'.")
    with connect() as db:
        clip = db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found.")
        current = packaging_payload(db, clip, payload.destination)
        if payload.approved and not current["approval_gate"]["allowed"]:
            raise HTTPException(status_code=409, detail=" ".join(current["approval_gate"]["blockers"]))
        stamp = now()
        db.execute(
            "INSERT OR IGNORE INTO clip_packaging(clip_id,destination,title,description,hashtags,approved,approved_at,updated_at) VALUES(?,?,?,?,?,0,NULL,?)",
            (clip_id, payload.destination, current["title"], current["description"], json.dumps(current["hashtags"]), stamp),
        )
        db.execute(
            "UPDATE clip_packaging SET approved=?,approved_at=?,updated_at=? WHERE clip_id=? AND destination=?",
            (1 if payload.approved else 0, stamp if payload.approved else None, stamp, clip_id, payload.destination),
        )
        return packaging_payload(db, clip, payload.destination)


@app.get("/api/publish/packages")
def publish_packages() -> dict[str, Any]:
    """Approved delivery packages.

    This deliberately returns files and copy for a manual upload. No platform connection
    exists in this build, so nothing is scheduled or posted on the creator's behalf.
    """
    packages: list[dict[str, Any]] = []
    with connect() as db:
        rows = db.execute(
            "SELECT p.clip_id,p.destination,p.approved_at,c.title AS clip_title,c.project_id,c.start_seconds,c.end_seconds "
            "FROM clip_packaging p JOIN clips c ON c.id=p.clip_id WHERE p.approved=1 ORDER BY p.approved_at DESC"
        ).fetchall()
        for row in rows:
            clip = db.execute("SELECT * FROM clips WHERE id=?", (row["clip_id"],)).fetchone()
            payload = packaging_payload(db, clip, row["destination"])
            payload["clip_title"] = row["clip_title"]
            payload["approved_at"] = row["approved_at"]
            packages.append(payload)
    return {
        "packages": packages,
        "note": "Approved export packages for manual upload. No platform account is connected in this build, so nothing is posted automatically.",
    }


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Processing job not found.")
        if row["status"] in {"completed", "failed", "cancelled"}:
            raise HTTPException(status_code=409, detail=f"This job is already {row['status']}.")
        stamp = now()
        if row["status"] == "queued":
            db.execute("UPDATE jobs SET status='cancelled',stage='cancelled',message='Cancelled before it started',updated_at=? WHERE id=?", (stamp, job_id))
            db.execute("UPDATE projects SET status='cancelled',updated_at=? WHERE id=?", (stamp, row["project_id"]))
            return {"id": job_id, "status": "cancelled"}
        db.execute("UPDATE jobs SET status='cancelling',message='Cancellation requested — the worker stops at the next checkpoint',updated_at=? WHERE id=?", (stamp, job_id))
        return {"id": job_id, "status": "cancelling"}


def require_ytdlp() -> None:
    if not shutil.which("yt-dlp"):
        raise HTTPException(
            status_code=503,
            detail="Link ingestion needs yt-dlp on the processing server. Install it with: pip install yt-dlp (or pkg install yt-dlp in Termux).",
        )


def resolve_source(url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    parsed = parse_source_url(url)
    require_ytdlp()
    try:
        completed = run(ytdlp_metadata_cmd(parsed["url"]), timeout=180)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="The source did not respond in time. Try again or upload the file.") from exc
    except subprocess.CalledProcessError as exc:
        tail = (exc.stderr or "").strip().splitlines()[-3:]
        raise HTTPException(status_code=422, detail="yt-dlp could not read that link. " + " ".join(tail)[:280]) from exc
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="yt-dlp returned an unreadable response.") from exc
    metadata = parse_metadata(payload)
    try:
        enforce_duration(metadata)
    except SourceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return parsed, metadata


@app.post("/api/sources/preview")
def preview_source(payload: SourceRequest) -> dict[str, Any]:
    try:
        parsed, metadata = resolve_source(payload.url)
    except SourceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**metadata, "platform": parsed["platform"], "url": parsed["url"]}


@app.post("/api/projects/from-link", status_code=202)
def create_project_from_link(payload: LinkRequest) -> dict[str, Any]:
    if not payload.rights_attested:
        raise HTTPException(status_code=422, detail="Confirm that you have the rights to this source before importing it.")
    try:
        parsed, metadata = resolve_source(payload.url)
    except SourceRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    asset_id, project_id, job_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    stamp = now()
    title = safe_stem(metadata)
    target = MEDIA / f"{asset_id}.mp4"
    with connect() as db:
        db.execute(
            "INSERT INTO assets(id,filename,size,content_type,path,created_at,duration_seconds,width,height) VALUES(?,?,?,?,?,?,?,?,?)",
            (asset_id, f"{title}.mp4", 0, "video/mp4", str(target), stamp, metadata["duration_seconds"], None, None),
        )
        db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)", (project_id, asset_id, title, "queued", stamp, stamp))
        options = {
            "kind": "ingest",
            "source_url": parsed["url"],
            "platform": parsed["platform"],
            "clip_count": payload.clip_count,
            "min_duration": payload.min_duration,
            "max_duration": payload.max_duration,
        }
        db.execute(
            "INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",
            (job_id, project_id, "queued", "queued", 0, "Queued: the worker downloads and analyses this link", json.dumps(options), None, stamp, stamp),
        )
        db.execute(
            "INSERT INTO sources(project_id,platform,url,title,uploader,metadata,rights_attested_at,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (project_id, parsed["platform"], parsed["url"], metadata["title"], metadata["uploader"], json.dumps(metadata), stamp, stamp),
        )
    enqueue(job_id)
    return {
        "id": project_id,
        "title": title,
        "status": "queued",
        "job_id": job_id,
        "source": {"platform": parsed["platform"], "url": parsed["url"], "duration_seconds": metadata["duration_seconds"]},
    }


@app.get("/api/projects/{project_id}/transcript")
def project_transcript(project_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM transcripts WHERE project_id=?", (project_id,)).fetchone()
        project = db.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not row:
        return {"project_id": project_id, "segments": [], "word_count": 0, "created_at": None}
    words = json.loads(row["words"])
    return {
        "project_id": project_id,
        "segments": json.loads(row["segments"]),
        "word_count": len(words),
        "created_at": row["created_at"],
    }


@app.get("/api/clips/{clip_id}/captions")
def clip_captions(clip_id: str, format: str = "srt", style: str = DEFAULT_STYLE) -> Response:
    if format not in {"srt", "vtt", "ass"}:
        raise HTTPException(status_code=422, detail="Caption format must be srt, vtt or ass.")
    if style not in CAPTION_STYLES:
        raise HTTPException(status_code=422, detail=f"Caption style must be one of: {', '.join(CAPTION_STYLES)}.")
    with connect() as db:
        clip = db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")
    words = load_words(clip["project_id"])
    if not words:
        raise HTTPException(status_code=409, detail="This project has no word-level transcript yet.")
    start, end = float(clip["start_seconds"]), float(clip["end_seconds"])
    slug = re.sub(r"[^A-Za-z0-9]+", "-", clip["title"] or "clip").strip("-").lower() or "clip"
    if format == "ass":
        body, media, extension = build_ass(words, start, end, style=style, hook=clip["hook"]), "text/plain", "ass"
    elif format == "vtt":
        body, media, extension = build_vtt(words, start, end, style=style), "text/vtt", "vtt"
    else:
        body, media, extension = build_srt(words, start, end, style=style), "application/x-subrip", "srt"
    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{slug}-{style}.{extension}"'},
    )
