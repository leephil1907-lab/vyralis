# VYRALIS technical architecture

## Product shape

VYRALIS is a browser-based studio backed by a local-first processing service. The browser is the control surface; source media and model inference remain on the user's machine in the default local deployment.

## Engine boundaries

- **Ingestion service:** validates, stores and indexes source assets.
- **Transcription adapter:** WhisperX or another evaluated speech-to-text backend; returns transcript segments, word timestamps and optional speaker labels.
- **Scene adapter:** PySceneDetect; returns scene boundaries and visual change metadata.
- **Vision adapter:** MediaPipe and/or a validated detector/tracker; returns face/object tracks and confidence values.
- **Highlight engine:** combines transcript semantics, scene boundaries, speaker turns, audio energy and visual evidence into candidate clips. Scores must be explainable and user-adjustable.
- **Composition engine:** generates 9:16, 1:1 and 16:9 layouts, speaker-aware crops, caption tracks and editable overlays.
- **Render engine:** FFmpeg for media operations; Remotion may provide React-based motion-graphics templates where its runtime and licence are suitable.
- **Job service:** persistent job state, cancellation, progress events, retry policy and per-project isolation.

## Candidate upstream projects

ShortsFlow, AutoClip, ClippyMe, Clippy, Cutroom, VideoHighlighter, WhisperX, PySceneDetect, Ultralytics, MediaPipe, Remotion, FFmpeg and Auto-Editor are candidates for evaluation—not assumed dependencies. Before adoption, inspect repository ownership, maintenance, source quality, licence, model terms, installation path, resource profile and reproducible output quality.

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

## Quality gates

- Unit tests for timecode conversion, clip boundary logic and crop geometry.
- Integration tests with short, licensed sample media.
- Golden-output tests for subtitle timing and render dimensions.
- Performance benchmarks on CPU and supported GPU configurations.
- Explicit failure states when optional models or accelerators are unavailable.
