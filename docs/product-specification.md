# VYRALIS Studio — Product and build specification

## Product promise
VYRALIS is a creator operating studio: turn long recordings into reviewed, polished short-form assets, package them for each destination, schedule and publish with permission, and learn from real performance. It must not claim a clip is viral or guarantee reach. Recommendations are evidence-based estimates and creators retain approval control.

## Product areas
1. Home / Command Center — projects, processing queue, scheduled posts, connected accounts, engine health and next steps.
2. Clipper — local file import and supported YouTube, Twitch, Kick and local media intake through validated, rights-compliant adapters.
3. Moment Intelligence — transcript, scene, speaker, audio energy, visual events and optional permitted stream signals; ranked clips with explainable scores, hook, timecodes and source evidence.
4. Clip Editor — source/program monitors, transcript-linked timeline, word-level trim, split/merge, crop/reframe, speaker layout, captions, titles, overlays, safe zones, audio, B-roll and brand kit.
5. Caption Lab — word-timed captions, translation, typography, karaoke emphasis, speaker colors and accessibility preview.
6. Brand Studio — logos, fonts, colors, watermarks, intros/outros and reusable presets.
7. Repurpose Studio — per-platform aspect ratio, duration, copy, title, description, hashtags and thumbnail variants.
8. Publish & Calendar — official OAuth/API connections, destination validation, drafts, scheduled posts, retries, publishing logs and status.
9. Growth Intelligence (Blow Up-inspired) — profile/channel audit, niche and audience positioning, content ideas, scripts and hooks, video quality analysis, cross-platform repurpose and repost planning, performance-informed recommendations.
10. Analytics & Learning — permitted metrics, retention/views/engagement where exposed by APIs, winning topics/hooks/formats and evidence-backed recommendations.
11. Library & Projects — searchable media, versions, attribution, clip collections, export history and safe deletion.
12. Settings — local/hosted mode, model providers, hardware diagnostics, privacy, API credentials, connected channels and accessibility.

## Blow Up research
The identified app is Blow Up: Go Viral With AI by Mountains Studio LLC, listed on Google Play and the Apple App Store. Its public store descriptions identify profile analysis, audience/niche-aware content ideas, automatic video scripts, video analysis for performance and engagement, and cross-platform auto-reposting. These are useful product patterns for VYRALIS Growth Intelligence. They are not evidence of an API or permission to copy its code, UI, branding, prompts or proprietary implementation.

References:
- Google Play: https://play.google.com/store/apps/details?id=com.blowup.app
- Apple App Store: https://apps.apple.com/ng/app/blow-up-go-viral-with-ai/id6739003582

VYRALIS differentiation: connect growth workflows directly to actual clips, edit decisions, publishing schedule and measurable post results in the same project. Profile analysis uses authorized public/account data; never ask for platform passwords or rely on unsupported scraping.

## Open-source integration research
Candidate projects: ShortsFlow, AutoClip, ClippyMe, Clippy, Cutroom, AutoShorts, VideoHighlighter, Reelsaw, ClipForge, OpenShorts, WhisperX, PySceneDetect, Ultralytics YOLO, MediaPipe, Remotion, FFmpeg and Auto-Editor. Additional workflow references: NovaClip for modular clipping/editing/repurposing/packaging/publishing; OpenShorts for transcript-linked editing, crop modes, scheduling and analytics; ClipFlow for browser/API/worker separation; PeakCut for combining replay heatmaps, chat signals and audio peaks.

These are evaluation references, not code to blindly merge. Before adoption, record repository URL, exact version/commit, licence and model terms, attribution, security review, installation path, CPU/GPU needs, test media and measured quality. Prefer adapters or subprocess services over copying entire applications. Preserve upstream licence notices.

## Processing pipeline
1. Ingest and validate source; probe with FFprobe, checksum, store and create project.
2. Extract audio, thumbnails, scene frames and analysis proxies.
3. Understand speech, word timestamps, speakers, scene cuts, audio energy/silence, subject tracks and optional permitted stream signals.
4. Discover candidates; score semantic completeness, hook clarity, emotional/energy change, speaker context, visual quality, duration and repetition. Store evidence and score breakdown.
5. Review ranked suggestions; creator accepts, rejects, trims, splits, merges and records attribution.
6. Compose aspect ratio, subject/speaker framing, captions and title layers with face/text safe zones.
7. Edit non-destructively using saved edit decision lists.
8. Quality gate duration, black/frozen frames, audio clipping, missing media, subtitle timing, safe zones, aspect ratio and decode.
9. Package platform-specific metadata and thumbnail variants.
10. Publish using official supported APIs or a vetted provider, with explicit approval.
11. Learn from permitted metrics and provide evidence-backed recommendations.

## Engineering architecture
- Frontend: React 18, TypeScript, Vite, Tailwind, Framer Motion, React Router and Lucide.
- API: FastAPI with versioned routes, typed schemas and OpenAPI.
- Persistence: SQLite local mode; PostgreSQL hosted mode; migrations required.
- Queue: durable jobs, retries, cancellation, idempotency, progress events and bounded concurrency. Redis/Celery or an evaluated alternative for hosted workers; local mode must not require cloud infrastructure.
- Media: FFmpeg/FFprobe worker processes, safe argument construction, resource limits and isolated temporary directories.
- Models: adapters for local Whisper/faster-whisper/WhisperX and optional remote providers; capability detection and fallback.
- Storage: local filesystem in local mode; private object storage and expiring signed URLs in hosted mode.
- Realtime: SSE or WebSocket progress with polling fallback.
- Auth: secure hosted sessions, OAuth and project-level authorization; local mode binds to loopback with origin protections.
- Observability: structured logs, job traces, failure categories, timing and resource metrics.

## Publishing requirements
Platform support varies by account type, app review, API permissions and quota. Implement only destinations with official API access that is tested. Start with YouTube Data API and approved Meta Instagram/Facebook publishing flows; assess TikTok Content Posting API, LinkedIn, X, Threads and Pinterest independently. Each adapter must expose capability status, scopes, media constraints, review status, quotas, upload progress, resumability and result URL. Do not claim universal one-click publishing until each integration is verified.

## Quality and acceptance gates
- A feature is not ready until its end-to-end test passes.
- No demo data in production views; label fixtures in development.
- Uploads are size-limited, MIME/extension checked, safely named, streamed and isolated by user/project.
- Treat URLs and media metadata as untrusted; prevent SSRF, path traversal, command injection and unsafe archive extraction.
- Keep secrets out of source control; use server-side or local secret storage.
- Jobs are durable, observable, cancellable and recoverable after restart.
- Every generated clip must decode and pass automated media quality checks.
- Every AI decision has manual controls.
- Test CPU mode and supported GPU modes; document hardware needs.
- Test multi-speaker podcasts, screen recordings, low-light, vertical footage and noisy audio.
- Provide accessible responsive layouts, keyboard controls and useful empty/loading/error states.
- Publishing is previewable and requires human approval by default.
- Provide opt-in analytics and retention/deletion controls.

## Release sequence
### Release 0 — Foundation hardening
Persist projects/assets, validate media with FFprobe, tests, migrations, secure upload, durable jobs and developer setup.

### Release 1 — Real clipping MVP
Local and permitted source intake, transcription, diarization, scene detection, explainable candidate scoring, review, vertical crop, captions and MP4 export.

### Release 2 — Professional editor
Transcript timeline, word-level edits, speaker tracking, caption themes, brand kit, quality gate and batch rendering.

### Release 3 — Growth Intelligence
Profile/channel audit, audience/niche ideas, scripts/hooks, video critique, metadata/thumbnails, repurpose plans and content calendar.

### Release 4 — Publishing and analytics
Official platform OAuth, destination adapters, scheduling, publish logs, metrics and performance learning.

### Release 5 — Scale and polish
Hosted worker fleet, team collaboration, desktop packaging, GPU acceleration, reliability and accessibility audit.
