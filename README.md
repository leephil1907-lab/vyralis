# VYRALIS Studio

<p align="center"><img src="assets/vyralis-mark.svg" width="112" alt="VYRALIS symbol" /></p>
<h1 align="center">VYRALIS STUDIO</h1>
<p align="center"><strong>Every moment has a story.</strong></p>
<p align="center">An ambitious, local-first video intelligence and short-form production studio.</p>

---

## What VYRALIS is

VYRALIS is being developed as a complete video production workflow—not just an automatic clip cutter. Its goal is to turn long-form recordings into carefully selected, editable, social-ready video assets while keeping media processing local wherever practical.

## Product workflow

- **Discover:** analyse speech, scenes, visual events and pacing to identify promising moments.
- **Understand:** evaluate context, story completeness, speaker turns, hooks and clip boundaries.
- **Reframe:** create portrait, landscape and square compositions with subject-aware framing.
- **Edit:** build captions, titles, transitions, zooms, layouts and optional supporting visuals.
- **Render:** produce platform-ready exports with reliable, repeatable media processing.
- **Review:** let creators inspect, adjust and approve every suggested clip before publishing.

## Product principles

1. **Local-first media** — keep source footage on the creator's machine by default.
2. **Creator control** — AI suggestions are editable; the creator makes the final call.
3. **Evidence-led highlights** — recommendations should be traceable to transcript, scene and timing evidence.
4. **No fake capabilities** — integrations are labelled accurately as planned, experimental or production-ready.
5. **Composable architecture** — use specialised tools behind clear interfaces rather than coupling the product to one model.
6. **Respect source rights** — users are responsible for having permission to process and publish supplied media.

## Planned capabilities

| Area | Direction |
|---|---|
| Media intake | Local files and supported public video sources |
| Transcription | Accurate transcription with word-level timestamps |
| Speaker analysis | Speaker diarization and active-speaker cues |
| Visual analysis | Scene changes, faces, objects and visual events |
| Highlight discovery | Context-aware candidate clips with explainable scores |
| Reframing | 9:16, 1:1 and 16:9 subject-aware layouts |
| Captions | Editable, word-timed caption styles |
| Creative editing | Hooks, titles, overlays, zooms and optional B-roll |
| Rendering | Reproducible exports from a dedicated media pipeline |
| Workflow | Project history, clip review and batch processing |

These are product goals, not a claim that every capability is implemented today. The repository now contains the first React + TypeScript studio interface and a local FastAPI media-ingestion service. The advanced AI analysis and editing engines are still being integrated.

## Design identity

- **Name:** VYRALIS Studio
- **Tagline:** Every moment has a story.
- **Category:** Intelligent Video Production
- **Visual direction:** cinematic, minimal, premium and technically precise
- **Palette:** Midnight `#090B18`, violet `#A855F7`, electric blue `#397BFF`, cyan `#26E5E1`
- **Typography direction:** Space Grotesk or Sora
- **Symbol:** an abstract V-shaped frame with an integrated play motif

## Architecture direction

VYRALIS will use modular adapters for specialised capabilities. Candidate technologies for evaluation include:

- **Transcription and alignment:** Whisper / WhisperX
- **Scene analysis:** PySceneDetect
- **Face and object analysis:** MediaPipe and compatible detection/tracking models
- **Video rendering:** FFmpeg
- **Programmatic motion graphics:** Remotion
- **Local model runtime:** configurable local inference backends

Every dependency will be evaluated for maintenance, hardware requirements, security, licence compatibility and redistribution terms before adoption. No external project is assumed to be integrated merely because it appears in this list.

## Development status

**Status: Foundation / architecture and implementation in progress.**

The first application foundation is committed: responsive studio dashboard, backend health endpoint, local media upload and asset listing. There is not yet an end-to-end AI clipping workflow or production installer. Features will be marked complete only after implementation and verification.

## Contributing

The project structure, development setup, coding standards and contribution workflow will be documented as implementation is established. Early contributors should open an issue to discuss substantial changes before submitting a pull request.

## Licence

A project licence will be selected after reviewing the intended dependencies, model licences and distribution strategy.
## Working upload-to-clip workflow (current implementation)

The repository now includes a first real processing vertical slice:

1. Upload a local video file. The API streams it to disk, checks the extension and validates its media streams with FFprobe.
2. Create a project and durable SQLite job record.
3. A background worker extracts mono 16 kHz audio with FFmpeg.
4. faster-whisper transcribes the audio with segment and word timestamps.
5. Transcript windows are ranked with an explainable heuristic breakdown (hook, emotion, clarity, story and pacing).
6. The review page displays processing progress, ranked candidates, transcript text and editable start/end/title values.
7. Export renders an actual 1080×1920 H.264/AAC MP4 with FFmpeg.

The score is a transparent transcript heuristic, not a trained virality model. Speaker diarization, face tracking, word-by-word caption rendering, music controls, URL source adapters and social publishing are not included in this first vertical slice.

### Local setup

Requirements: Python 3.11, Node.js 20+, and FFmpeg/FFprobe available on PATH.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Open the Vite URL, choose **Create clips**, and upload an MP4, MOV, MKV, WebM or AVI file. The first faster-whisper run downloads the configured model; set `VYRALIS_WHISPER_MODEL` (default `base`), `VYRALIS_WHISPER_DEVICE` (default `cpu`) and `VYRALIS_WHISPER_COMPUTE` (default `int8`) to tune the worker.

### Container and persistence

The root Dockerfile installs FFmpeg and the Python API. Set `VYRALIS_DATA_DIR` to a persistent mounted volume. The SQLite database, original media and exports are stored under that directory. Configure `VYRALIS_CORS_ORIGINS` with the exact frontend origin and `VYRALIS_MAX_UPLOAD_BYTES` to your upload policy. A persistent disk is required for restart recovery; ephemeral container storage is not durable.

This initial API is a single-workspace processing foundation. It does not yet provide user authentication, per-account authorization or private multi-tenant media access. Keep it on localhost or behind an authenticated private gateway until those controls are implemented; do not expose this API publicly as a multi-user service.
