# VYRALIS implementation roadmap

## Phase 0 — Foundation
- [x] Establish product identity and repository documentation.
- [x] Create React + TypeScript + Vite application shell.
- [x] Create local FastAPI service and health endpoint.
- [x] Implement local media ingestion endpoint and asset listing.
- [ ] Add persistent metadata database and safe media lifecycle management.
- [ ] Add automated tests and CI build checks.

## Phase 1 — Reliable media intelligence
- [ ] Probe media metadata and validate codecs with FFprobe.
- [ ] Integrate transcription with word-level timestamps.
- [ ] Add speaker diarization and scene detection.
- [ ] Store analysis outputs as versioned artifacts.
- [ ] Add reviewable transcript and timeline UI.

## Phase 2 — Highlight discovery
- [ ] Build candidate-window generation.
- [ ] Score clips using semantic coherence, hook strength, story completeness, speaker/audio signals and scene boundaries.
- [ ] Explain why each candidate was selected.
- [ ] Allow manual trim, merge, split and exclusion.

## Phase 3 — Editing and composition
- [ ] Add subject-aware reframing and manual crop controls.
- [ ] Add caption themes and word-level emphasis.
- [ ] Add title/hook overlays, safe zones and optional B-roll.
- [ ] Save edits as non-destructive project data.

## Phase 4 — Rendering and delivery
- [ ] Build durable render queue with cancellation and retries.
- [ ] Add FFmpeg export presets for Shorts, Reels and TikTok.
- [ ] Evaluate Remotion for advanced motion-graphics templates.
- [ ] Add render previews, downloadable exports and output validation.

## Phase 5 — Production readiness
- [ ] Authentication and project isolation for hosted mode.
- [ ] Local installer and model/dependency manager.
- [ ] GPU capability detection and CPU fallback.
- [ ] Security review, dependency licence review and performance benchmarks.
- [ ] End-to-end tests on representative, rights-cleared media.
