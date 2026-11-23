# VYRALIS Local Engine

FastAPI service for the local (single-workspace) processing pipeline: media validation,
transcription, candidate discovery, preset rendering, automated render inspection and
delivery packaging.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
VYRALIS_DATA_DIR=../data uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

FFmpeg and FFprobe must be on `PATH`. The first faster-whisper run downloads the configured
model. The React app runs separately with `npm install && npm run dev` from the repository root.

## What is implemented (0.3)

- Health and capability reporting (`GET /api/health`).
- Streamed local upload with FFprobe validation and a configurable size ceiling.
- Projects, jobs, clips, exports and packaging persisted in SQLite with restart recovery.
- FFmpeg audio extraction and faster-whisper transcription with word timestamps.
- Transcript-window candidates with an explainable score breakdown.
- Clip edit (start, end, title) and re-render.
- Render presets: 9:16 (1080×1920), 1:1 (1080×1080), 16:9 (1920×1080).
- Automated render inspection: duration, frame size, codecs, black frames, frozen frames,
  loudness and file integrity. A failed inspection blocks the download.
- Destination packaging validation, approval gate with revocation on copy edits, and
  approved delivery packages for manual upload.
- Job cancellation at worker checkpoints; idempotent export requests.

## What is not implemented

Link ingestion (YouTube/Twitch/Kick), diarization, scene/vision analysis, caption generation,
timeline editing, platform OAuth publishing, analytics import, StoryLab execution and the
workflow engine. Those routes in `docs/api-contract.md` are targets; no route exists for them
and the UI labels them as planned.

## Tests

```bash
python -m unittest discover -s tests -v
```

Unit and persistence tests run without FFmpeg or a whisper model. Media-dependent acceptance
(real render digits, golden outputs) still needs licensed fixtures in CI.
