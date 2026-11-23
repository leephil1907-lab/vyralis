# VYRALIS implementation roadmap

## Release 0 — Foundation hardening
- [x] Product identity, React + TypeScript + Vite shell, FastAPI health API and initial local media upload/listing.
- [x] Product specification and architecture direction.
- [ ] SQLite local / PostgreSQL hosted persistence and migrations.
- [ ] FFprobe validation, upload limits, MIME sniffing and safe path isolation.
- [ ] Durable job model, worker lifecycle, progress, cancellation and retry.
- [ ] API validation, tests and CI test coverage.

## Release 1 — Real clipping MVP
- [ ] First-class paste-link ingestion for YouTube, Twitch and Kick VODs plus local file upload.
- [ ] Source metadata/caption resolution, audio-first analysis, selective section downloads and live-stream capture where supported.
- [ ] WhisperX/faster-whisper transcription and word timestamps.
- [ ] Speaker diarization with optional backend selection.
- [ ] PySceneDetect and audio energy/silence analysis.
- [ ] Explainable highlight candidate scoring.
- [ ] Candidate review and manual trim/split/merge.
- [ ] FFmpeg 9:16, 1:1 and 16:9 composition and caption rendering.
- [ ] Playable preview and verified MP4 export.

## Release 2 — Professional editor
- [ ] Transcript-linked timeline and word-level edit controls.
- [ ] YOLO/MediaPipe subject tracking and active-speaker layouts.
- [ ] Caption Lab with styles, karaoke emphasis and multilingual workflows.
- [ ] Brand kits, watermark, title/hook overlays and templates.
- [ ] Remotion motion-graphics integration after runtime/licence validation.
- [ ] Render queue, batch processing, retries and quality gate.

## Release 3 — Growth Intelligence (Blow Up-inspired)
- [ ] Authorized creator profile/channel audit.
- [ ] Audience and niche-aware content ideas.
- [ ] Script, hook, CTA and title generation.
- [ ] Video critique for pacing, clarity, audio, visual quality and opening hook.
- [ ] Thumbnail, description, hashtag and chapter generation.
- [ ] Cross-platform repurpose plans and content calendar.
- [ ] Brand voice and creator-specific recommendations.

## Release 4 — Publishing and analytics
- [ ] Official YouTube publishing adapter.
- [ ] Approved Instagram/Facebook publishing adapter.
- [ ] TikTok Content Posting API capability and app-review assessment.
- [ ] Independently assess LinkedIn, X, Threads and Pinterest.
- [ ] OAuth, scopes, destination capability checks and credential management.
- [ ] Draft preview, scheduling, publishing logs and retries.
- [ ] Import available post metrics and build performance reports.
- [ ] Use performance data to improve future recommendations.

## Release 5 — Production quality and scale
- [ ] Local installer, dependency/model manager and hardware diagnostics.
- [ ] Hosted isolated workers, private object storage and quotas.
- [ ] Accessibility, keyboard and responsive review.
- [ ] End-to-end media quality tests and golden output tests.
- [ ] Security, privacy, licence and performance audit.
- [ ] Monitoring, backup, retention and account deletion workflows.

## Release gates
A capability is complete only after implementation, automated tests, manual verification with representative rights-cleared media, and documented hardware/API requirements. UI mockups and placeholder controls do not count as completed features.
