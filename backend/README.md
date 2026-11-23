# VYRALIS Local Engine

The local FastAPI service currently provides health checks and local media ingestion.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The React app runs separately with `npm install && npm run dev` from the repository root.

## Current implementation boundary

Media upload is implemented. Transcription, highlight discovery, diarization, scene analysis, smart reframing and final rendering are not yet wired into the API. Those will be added as independently testable engine adapters after dependency, licence and hardware validation.
