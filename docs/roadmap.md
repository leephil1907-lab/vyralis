# VYRALIS Studio — Implementation Roadmap

The canonical scope is in docs/feature-registry.md. A feature is complete only after the implementation, persistence, security controls and acceptance tests pass. Product screens and documentation alone do not count.

## Release 0 — Local clipping vertical slice
- [x] React + TypeScript + Vite studio foundation.
- [x] FastAPI health and local media API.
- [x] Streamed local upload with FFprobe media validation and upload-size limit.
- [x] SQLite records for assets, projects, jobs and clips.
- [x] FFmpeg audio extraction.
- [x] faster-whisper transcription with segment and word timestamps.
- [x] Transcript-window highlight candidates with explainable heuristic score breakdown.
- [x] Candidate review and source preview.
- [x] Manual clip start/end/title editing.
- [x] FFmpeg vertical MP4 export and download endpoint.
- [x] Startup recovery for queued/processing jobs.
- [ ] Verify the full flow against a representative rights-cleared media test fixture in CI.
- [ ] Add output probing, media-quality checks and render regression tests.
- [ ] Harden MIME sniffing, path isolation, upload quotas and cleanup.
- [ ] Add cancellation, idempotency, bounded queue semantics and job-attempt history.

## Release 1 — Core clipping quality
- [ ] Improve transcript candidate segmentation and context completeness.
- [ ] Language detection and transcript correction.
- [ ] Speaker diarization with optional provider/model adapter.
- [ ] PySceneDetect and audio-energy/silence analysis.
- [ ] Visual-event and subject analysis adapter.
- [ ] Evidence-backed score dimensions, confidence and manual feedback.
- [ ] Candidate deduplication, configurable count and duration presets.
- [ ] 9:16, 1:1 and 16:9 export presets.
- [ ] Word-timed caption generation and subtitle burn-in.
- [ ] Export validation and batch rendering.

## Release 2 — Professional editor
- [ ] Transcript-linked timeline and frame-accurate controls.
- [ ] Split, merge, ripple edits, undo/redo and non-destructive versions.
- [ ] Subject tracking, active-speaker layouts and manual keyframes.
- [ ] Caption Lab, multilingual captions and accessibility checks.
- [ ] Brand kits, watermark, title/hook overlays and templates.
- [ ] Audio cleanup, ducking, licensed music and B-roll controls.
- [ ] Render queue, retries and output quality gate.

## Release 3 — Supported source ingestion
- [ ] Source adapter interface and URL metadata preview.
- [ ] Official/authorized YouTube, Twitch and Kick VOD paths where permitted.
- [ ] Caption/transcript resolution and audio-first analysis where available.
- [ ] Selective segment retrieval when the provider supports it.
- [ ] Live capture only through permitted APIs/providers, with explicit stop/status controls.
- [ ] SSRF protections, redirect validation, source rights and provider capability reporting.

## Release 4 — Repurposing, publishing and calendar
- [ ] Platform-specific dimensions, duration, copy and thumbnail packaging.
- [ ] Official YouTube publishing adapter and OAuth.
- [ ] Approved Instagram/Facebook publishing adapter.
- [ ] TikTok Content Posting API review and capability assessment.
- [ ] Independently assess LinkedIn, X, Threads and Pinterest.
- [ ] Draft preview, human approval, timezone-aware scheduling and calendar.
- [ ] Delivery receipts, logs, retries and published post links.

## Release 5 — Analytics and Growth Intelligence
- [ ] Import verified metrics from authorized connected channels.
- [ ] Compare results by topic, hook, format, length and posting time.
- [ ] Creator/channel audit using authorized data.
- [ ] Niche and trend intelligence with source, freshness, geography and confidence.
- [ ] Content gaps, scripts, hooks, CTAs, metadata and repurpose plans.
- [ ] Feedback loop connecting actual performance to future clip recommendations.

## Release 6 — StoryLab and Workflow Canvas
- [ ] Research-backed storyboard with citations and fact verification.
- [ ] Scene plans, narration, shot direction, prompts and timing.
- [ ] Reference asset continuity and rights metadata.
- [ ] Typed workflow graph, branching, parallel execution and reusable templates.
- [ ] Autosave, versions, previews, durable DAG jobs, retries and cancellation.
- [ ] Image/video/voice/audio providers behind capability-aware adapters.

## Release 7 — Hosted production and collaboration
- [ ] Authentication, email verification, password recovery and secure sessions.
- [ ] Workspace/project roles and tenant isolation.
- [ ] PostgreSQL schema and migrations.
- [ ] Durable hosted queue, isolated workers and private object storage.
- [ ] Encrypted OAuth credentials, quotas, usage metering and billing.
- [ ] Notifications, audit events, data export/deletion and retention controls.
- [ ] Monitoring, backups, restore drills, accessibility and security audits.
- [ ] Desktop/local worker packaging and optional GPU worker pool.

## Release gates
- Frontend typecheck/build and backend tests pass.
- Representative media completes upload → analysis → review → edit → export → download.
- Jobs recover and retry without duplicate outputs or data loss.
- Every output passes FFprobe and media decode validation.
- Public hosted deployment is blocked until authentication, tenant isolation, private storage and rate limits are verified.
- Provider features are labelled unavailable until authorization and real end-to-end tests pass.
