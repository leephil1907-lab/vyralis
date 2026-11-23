# VYRALIS technical architecture

## Product shape

VYRALIS is a browser-based studio backed by a local-first processing service. The browser is the control surface; source media and model inference remain on the user's machine in the default local deployment.

## Engine boundaries

- **Ingestion service:** validates, stores and indexes source assets — local uploads, plus allowlisted links resolved by yt-dlp (`backend/app/ingest.py`). The URL policy (hosts, schemes, ports, credentials, IP literals, duration and size caps) is the only place a link becomes trusted.
- **Transcription adapter:** WhisperX or another evaluated speech-to-text backend; returns transcript segments, word timestamps and optional speaker labels.
- **Scene adapter:** PySceneDetect; returns scene boundaries and visual change metadata.
- **Vision adapter:** MediaPipe and/or a validated detector/tracker; returns face/object tracks and confidence values.
- **Highlight engine:** combines transcript semantics, scene boundaries, speaker turns, audio energy and visual evidence into candidate clips. Scores must be explainable and user-adjustable.
- **Composition engine:** generates 9:16, 1:1 and 16:9 layouts, centre/blur/face-tracked crops, word-timed caption tracks and hook overlays. Delivered as `backend/app/reframe.py` (filter graph) and `backend/app/captions.py` (ASS/SRT/VTT).
- **Render engine:** FFmpeg for media operations; Remotion may provide React-based motion-graphics templates where its runtime and licence are suitable.
- **Job service:** persistent job state, cancellation, progress events, retry policy and per-project isolation.

## Candidate upstream projects

The current, evidence-based evaluation lives in [docs/upstream-evaluation.md](upstream-evaluation.md). It records stars, licence, last push, manifests and README claims for each candidate as of 2026-11-23, plus the licence traps found (a 4k-star "open-source" clipper is noncommercial, a 6.5k-star clipper is a paid-API client, and the most complete auto-publishing implementation is AGPL).

Adoption rule: components with permissive licences (yt-dlp, faster-whisper, PySceneDetect, auto-editor, MediaPipe, Ollama) can be integrated behind adapters; entire clipper applications are references only. Never copy code from an AGPL or noncommercial project into this repository, and re-verify licences before each dependency is added.

Do not copy entire upstream applications into this repository. Prefer isolated adapters, subprocess boundaries or documented integration interfaces. Preserve upstream attribution and licence notices.

## Data and job model

A project owns media assets, transcripts, analysis runs, candidate clips, edit decisions and rendered outputs. Each job records input asset IDs, engine/version configuration, progress, timestamps, logs and terminal status. Never expose arbitrary local filesystem paths to browser clients.

## Local-first and hosted modes

- **Local mode:** browser talks to a loopback API; files and model inference stay on the user's machine.
- **Hosted mode:** a separate authenticated deployment with object storage, worker isolation, quotas and explicit user consent for upload. Hosted processing must not be presented as local processing.

## Delivery pipeline (implemented)

Renders are deterministic and inspectable:

1. **Preset geometry** — `backend/app/delivery.py` owns the only source of truth for 9:16,
   1:1 and 16:9 frame sizes; FFmpeg scales to cover and crops to the preset.
2. **Inspection** — the rendered file is probed for duration, frame size, codecs and size,
   then measured with `blackdetect`, `freezedetect` and `volumedetect`.
3. **Decision** — `evaluate_export` produces a `pass` / `warn` / `fail` report with one entry
   per check. A `fail` deletes the file, marks the export failed and blocks download; `warn`
   keeps the file and explains the risk. Reports are stored with the export, not regenerated
   from guesswork.
4. **Packaging** — copy is validated against published destination limits. Approval requires a
   non-failing render and valid copy; editing the copy revokes approval.
5. **Delivery** — approved packages are listed with their validated file for manual upload.
   No platform adapter exists, so no publishing call is ever simulated.

## Captions, framing and link ingestion (implemented)

**Link ingestion.** `POST /api/sources/preview` resolves metadata with `yt-dlp --dump-single-json`
(no download) so the creator can see what the link is; `POST /api/projects/from-link` requires
`rights_attested: true`, then queues a normal processing job whose first stage downloads the
source into the media store, re-probes it with FFprobe and continues through transcription and
ranking. Live streams and sources over `VYRALIS_MAX_SOURCE_DURATION` are rejected before any
bytes are fetched. Nothing is downloaded unless the request carries the attestation.

**Word-timed captions.** Whisper word timestamps are persisted once per project in `transcripts`
and reused for every export. `build_ass` writes a real ASS document sized to the export frame
(`PlayResX/Y` = render dimensions, font size and margins scaled from the 1080×1920 reference),
with a karaoke `\k` sweep per word for the karaoke/impact styles, a separate `Hook` style pinned
to the top, text sanitised against ASS override injection, and the hook font shrunk until the
line fits the frame. The file is burned in with the `subtitles` filter, so FFmpeg must be built
with libass. SRT, VTT and ASS sidecars are served from the same timings via
`GET /api/clips/{id}/captions`.

**Framing.** `build_filter` emits a filter graph ending in `[vout]` for three layouts:
`center` (cover-scale + crop), `blur` (split → blurred cover background + contained foreground
overlay) and `face` (cover-scale around a damped focus point). Face detection is optional
(`opencv-python-headless`, Haar cascade); when it is missing or finds nothing, the crop falls
back to centre and the export report says so instead of claiming tracking. Crop offsets are
always clamped inside the scaled frame and dimensions are forced even for H.264.

**Honest reporting.** `report["render"]` records captions on/off, the style actually burned in,
whether the hook overlay was drawn, the layout used, whether tracking ran and a framing note.
The UI renders that next to the measured metrics, so a viewer can tell what was applied.

## Quality gates

- Unit tests for timecode conversion, clip boundary logic and crop geometry
  (`tests/test_captions.py`, `tests/test_reframe.py`, `tests/test_ingest.py`, `tests/test_hooks.py`
  — 109 tests, no FFmpeg, model or network required).
- Integration tests with short, licensed sample media.
- Golden-output tests for subtitle timing and render dimensions.
- Performance benchmarks on CPU and supported GPU configurations.
- Explicit failure states when optional models or accelerators are unavailable.
