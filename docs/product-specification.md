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


## Product experience rule — this is an application, not a tool directory

VYRALIS must be presented and built as one cohesive clipping, editing and automated publishing application. Open-source projects, models and processing engines are internal implementation dependencies. They must not be exposed as a public catalogue, marketplace, plugin directory or collection of unrelated tools.

The primary navigation and product hierarchy must centre on creator work:
- Dashboard
- Projects
- Create clips
- Editor
- Publishing calendar
- Connected channels
- Analytics
- Brand kit
- Settings

The primary user journey is import video → analyse → generate clips → edit/review → approve → schedule/publish → measure results. The user should not need to understand which model or upstream repository performs each step.

The dashboard should prioritize active projects, recent clips, processing progress, drafts awaiting approval, scheduled posts, connected-channel status and publishing outcomes. Engine diagnostics belong under Settings or an advanced system status panel.

Publishing automation is a first-class workflow, not an afterthought. Users must be able to connect supported channels using official authorization flows, prepare platform-specific post metadata, select destinations, schedule publication, monitor delivery, retry recoverable failures and inspect published post links. Unsupported platform capabilities must be clearly unavailable rather than simulated.

Do not show dead navigation, fake metrics, placeholder controls, mock posting states or sample clips as real user content. Each screen must be backed by a working workflow or clearly marked as not yet released. The interface should feel like a premium, unified creator studio rather than a technical dashboard for developers.


## First-class link ingestion — required core capability

Importing is not limited to local uploads. A source URL field is a primary entry point on the Create Clips screen, equal in importance to the file picker. Users can paste supported YouTube video/VOD URLs, Twitch VOD URLs, Kick VOD URLs, and supported live-stream URLs. The system resolves and validates the source, displays title/channel/duration/thumbnail when available, lets the user choose clip count, duration range, language, analysis mode and output layout, then starts a durable clipping job.

The link workflow must not force users to download a full long-form video before analysis. Use a source adapter:
- Fetch permitted platform captions/transcripts and timestamps when available.
- Extract or stream audio for audio-first analysis where supported.
- Score loudness changes, raised-voice energy, speech/context and silence-to-energy transitions.
- Optionally run deeper visual analysis using sampled frames, optical flow and scene changes.
- Rank candidate windows, then fetch only selected video ranges when the source provider supports reliable section downloads.
- Align selected video ranges to audio timestamps and render vertical clips.
- Fall back to full source download only when necessary and permitted.

For live sources, a separate live-capture workflow records or buffers an authorized stream, monitors available audio/chat signals, detects spikes and creates reviewable clips. Live capture must expose recording status, disk use, stop controls, source connectivity and retention settings. Never imply that a live platform link can be clipped when its stream cannot be accessed by the selected adapter.

Each source adapter must implement URL parsing, domain allowlisting, canonicalization, availability checks, metadata lookup, caption access, audio extraction, range download, live capabilities, rate-limit handling and actionable errors. Do not accept arbitrary URLs as shell commands or fetch arbitrary internal/private network destinations. Revalidate every redirect and resolved IP to prevent SSRF. Respect platform terms, rights and applicable restrictions; do not bypass authentication, DRM, paywalls or access controls.

The UI must clearly distinguish source processing location:
- **Local mode:** link resolution, analysis, downloads, source files and renders run on the user's installed desktop agent; media stays on that device.
- **Hosted mode:** source media is processed on VYRALIS infrastructure and stored privately; clearly disclose this and apply account isolation, retention and deletion controls.
A normal hosted browser cannot truthfully promise that processing runs on the creator's PC. A desktop companion/agent is required for true local processing. The browser website can be the control panel for that local agent.

NeonClipping is an evaluated upstream reference for the link-first audio-first pipeline and local processing experience. Its public repository is MIT licensed. If code is reused, preserve its copyright and licence notices, pin the exact commit, audit dependencies/security, isolate it behind a VYRALIS adapter, and run regression tests. Prefer reimplementing interoperable capabilities when that produces a cleaner and safer architecture. Do not represent NeonClipping as already integrated.

## Create Clips screen interaction
The initial create screen must offer two equally clear source methods:
- Paste a video or stream link.
- Upload a video from this device.

After source validation, show source details and a clear "Generate clips" action. Advanced settings are optional and collapsed by default. The default workflow should require only a link and a click. Show job progress and generated clips as they become available. Never fabricate clip results or progress.


## Niche Intelligence, StoryLab and visual workflow canvas

VYRALIS includes a strategy-to-production layer that feeds the clipper and publishing studio. It is not a separate tool directory.

### Trend & Niche Radar
- Discover broad categories and narrower sub-niches by platform and target audience.
- Rank opportunities only when supported by current data: trend velocity, search interest, creator/channel activity, content saturation, audience engagement, clip density, evergreen potential and monetization fit.
- Show evidence, data source, retrieval time, confidence and geography for each signal.
- Distinguish measured platform metrics from modeled estimates. RPM/revenue estimates must show assumptions and ranges; never promise earnings.
- Save niche watchlists, compare candidate niches, identify content gaps and convert a selected niche into a recurring series plan.
- Data adapters may include YouTube Data API, authorized creator analytics, Google Trends or a licensed trend provider, and other approved public/authorized sources. Respect quotas and platform terms; no fake live metrics or unsupported scraping.

### StoryLab — storyline and scene illustration
- Convert a topic, source transcript or selected niche into a structured story arc: hook, setup, development, turning point, payoff and CTA.
- Build a scene-by-scene storyboard with narration, duration estimate, visual direction, shot/illustration prompt, on-screen text, transition and source/citation notes.
- Support documentary, explainer, illustrated story, product story, case study and creator-led formats.
- Keep factual claims traceable to sources and flag details requiring verification.
- Generate image references, visual consistency guides and optional video shots through provider adapters. Support user-supplied reference images and persistent character/style references when permitted.
- Voice generation and sound design are optional nodes; creators can use their own recordings.
- Storyboards are editable and can be sent into the workflow canvas, clip editor and render pipeline.

### Creative Workflow Canvas
Vidnance (https://vidnance.com/) was evaluated as a product reference for a visual node-based creative canvas that chains text, image, video and audio operations, supports multi-reference inputs, templates and conversational revisions. VYRALIS should adopt the workflow concept, not copy Vidnance's branding, proprietary UI or code.

Canvas nodes should include Brief/Input → Research → Script → Storyboard → Image/Video assets → Voice/Sound → Clip/Compose → Captions → Quality Check → Export/Publish. Nodes have typed inputs/outputs, provider and model configuration, cost/credit estimate where known, run status, retries, preview, logs and version history. Support reusable templates, branching, parallel generation, autosave and rerunning downstream nodes when an upstream input changes.

### Additional integration candidates
- Trend and audience research: YouTube Data API, Google Trends or licensed trend intelligence, plus approved creator analytics APIs.
- Story/script/research: LLM provider adapters with structured output, retrieval/citations and fact-check workflow.
- Image generation and visual consistency: image model adapters; optional reference image/character/style management.
- Video generation and editing: video model adapters, FFmpeg and Remotion; provider terms, watermarking, commercial-use and output restrictions must be surfaced.
- Voice and sound: ElevenLabs or other authorized TTS/voice providers, plus local audio tools; voice cloning requires explicit rights/consent.
- Workflow orchestration: durable DAG execution, job queue, event stream, retries, caching, cost accounting and artifact lineage.
- Research inputs: official APIs and licensed sources only; cache within terms and label freshness.

Provider availability, model versions, prices, licenses, and regional access change. Maintain an adapter registry with capability metadata and verify each provider before enabling a feature. Never imply a third-party model or API is integrated until credentials, server-side adapter, tests and end-to-end outputs are working.

### Strategy-to-publish journey
Discover niche → choose audience and series angle → create story outline → illustrate scenes → generate or import voice/footage → assemble vertical video → review/edit → export or schedule → measure actual performance → feed learning back into niche and format recommendations.
