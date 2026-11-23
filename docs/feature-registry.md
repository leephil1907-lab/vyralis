# VYRALIS Studio — Complete Feature Registry

This is the canonical product inventory. A feature is implemented only when its UI, API, persistence, security controls and acceptance tests work together. A visible screen or roadmap item is not implementation.

## Status vocabulary
- Working foundation: a real but limited workflow exists.
- In progress: code exists but is incomplete or not verified end to end.
- Planned: defined scope, not available yet.
- Blocked by provider: requires approval, credentials, commercial terms or third-party capability.

## P0 — Core clipping workflow
| Feature | Scope | Current status |
|---|---|---|
| Local media import | MP4, MOV, MKV, WebM, AVI; streamed upload; size limits; FFprobe validation | Working foundation; strengthen MIME sniffing and isolation |
| Video link ingestion | Background import for eligible public YouTube, Twitch and Kick URLs; rights confirmation; source validation; then same analysis pipeline | Implemented foundation; provider availability and permitted access vary; verify on deployment |
| Project creation | Persistent project/source association and processing options | Working foundation |
| Processing jobs | Queued/running/completed/failed, progress and restart recovery | Working foundation; add cancellation, idempotency and durable queue |
| Audio extraction | FFmpeg mono 16 kHz WAV | Working foundation |
| Transcription | faster-whisper segments and word timestamps | Working foundation; language and accuracy QA required |
| Highlight discovery | Transcript-window candidates and score breakdown | Working foundation; heuristic only, not trained virality prediction |
| Candidate review | Ranked candidates, source preview, transcript and timecodes | Working foundation; verify full journey |
| Clip editing | Adjust start/end/title | Working foundation; add split, merge, undo and versions |
| Multi-preset export | FFmpeg H.264/AAC render at 9:16 (1080×1920), 1:1 (1080×1080) and 16:9 (1920×1080) with deterministic scale/crop | Working foundation |
| Render quality inspection | FFprobe duration/size/codec checks plus blackdetect, freezedetect and volumedetect, recorded per export | Working foundation; add caption, framing and frame-sampling checks with licensed fixtures |
| Download | Download a validated render; failed inspections are blocked | Working foundation |
| Packaging validation | Per-destination title/description/hashtag limits, duplicate and character rules | Working foundation |
| Approval gate | Approval requires a passing/warned render and valid packaging; editing copy revokes approval | Working foundation |
| Delivery packages | Approved package + validated file listed in Publish Studio for manual upload | Working foundation; platform adapters remain planned |
| Job cancellation | Queued jobs cancel immediately; running jobs stop at checkpoints | Working foundation; add worker preemption |
| Export idempotency | Repeated export requests for the same clip and preset reuse the active render | Working foundation |
| Link ingestion | YouTube/Twitch/Kick URL policy, yt-dlp metadata preview, rights attestation, duration/live caps, download → transcribe → rank | Working foundation; requires yt-dlp and FFmpeg on the processing host, verified against a local synthetic source only |
| Word-timed captions | ASS burn-in in clean/karaoke/impact styles, per-word sweep, hook layer, SRT/VTT/ASS sidecars | Working foundation; requires libass-enabled FFmpeg |
| Auto-reframe | Centre crop, blurred-fill layout, optional face-tracked focus with damped smoothing | Working foundation; face tracking needs the optional vision extra and is reported honestly when unavailable |
| Platform connections | OAuth 2.0 authorization-code flows for YouTube, TikTok, Instagram and X; PKCE where supported; single-use expiring state; encrypted token storage; automatic refresh; disconnect deletes tokens | Working foundation; needs operator-owned OAuth clients. Request shapes and parsing are tested against a fake transport — each first live connection is unverified |
| Live channel metrics | Account profile and public counts read from the connected platform API, shown with a sync timestamp; missing fields stay empty | Working foundation; depends on a connection |
| Hook lines and titles | Extractive hook/title/hashtag suggestions from the transcript, editable per clip | Working foundation; heuristic, not a virality model |

P0 acceptance: a rights-cleared local upload — or an eligible provider link, subject to platform access, permissions and availability — completes ingestion → source validation → processing → review → edit → export → quality inspection → download → packaging → approval; job recovery, cancellation and retry are safe; clip bounds stay within source duration; output decodes with the requested captions and framing, and has the expected duration, dimensions and audio. Media-dependent acceptance still needs licensed CI fixtures — see the open roadmap items.

## P1 — Analysis intelligence
- Word-level alignment, language detection and transcript correction.
- Speaker diarization with labels and confidence.
- Scene/shot detection, sampled-frame analysis and visual-event cues.
- Audio loudness, silence, speech activity, peaks and clipping analysis.
- Semantic moment detection: hook, setup, payoff, context completeness and repetition.
- Explainable ranking with evidence, confidence and configurable weights.
- Candidate deduplication, duration presets, clip count and language filters.
- Optional permitted stream signals through approved APIs.
- Manual accept/reject and feedback capture.

## P2 — Professional editor and creative finishing
- Multi-track timeline, source/program monitors and frame-accurate seeking.
- Transcript-linked trim, split, merge, ripple edits and undo/redo.
- Non-destructive edit decision lists and version history.
- Auto-reframe for 9:16, 1:1, 16:9 and custom dimensions. (Working foundation: centre, blur and optional face-tracked crops; custom dimensions and manual keyframes are not available.)
- Subject/face tracking, speaker-aware layouts and manual keyframes. (Partial: single-face tracking behind the vision extra.)
- Caption Lab: word timing, templates, karaoke emphasis, speaker colors, safe zones and multilingual variants. (Partial: three burn-in styles with karaoke sweep; no templates UI, speaker colours or multilingual variants.)
- Titles, hooks, lower thirds, transitions, zooms, overlays, stickers and progress indicators.
- Audio gain, ducking, noise reduction and licensed music selection.
- B-roll/image overlays with attribution and usage-rights metadata.
- Brand kits: logo, palette, type, watermark, intro/outro and presets.
- Batch rendering, render presets, output validation and retryable queue.

## P3 — Repurposing and publishing
- Account connections: YouTube, TikTok, Instagram and X OAuth. (Working foundation — see the platform connections row above. Publishing itself is not implemented.)
- Per-destination aspect ratio, duration, title, description, hashtags, thumbnail and accessibility text.
- Draft preview and platform-specific validation.
- Timezone-aware calendar and schedule collision checks.
- Official OAuth, encrypted credentials, scope display and revocation.
- Publishing adapters with capability discovery, resumable uploads, retries, rate limits and delivery receipts.
- Start with officially supported YouTube and approved Meta flows; assess TikTok and other networks independently.
- Human approval by default; no password collection or simulated posting.
- Post history, destination URLs, delivery logs and failure recovery.

## P4 — Analytics and growth intelligence
- Import only metrics exposed by authorized platform APIs.
- Views, watch time, retention, engagement and audience metrics where available.
- Compare content by hook, topic, format, length and publish time.
- Creator/channel audit using authorized profile/account data.
- Niche discovery, trend freshness, geography and source provenance.
- Demand, competition, evergreen potential and monetization-fit estimates with transparent methodology.
- Content gaps, recurring series, ideas, scripts, hooks, CTAs and repurpose plans.
- Thumbnail/title experiments and performance feedback loops.
- Never fabricate live trends, RPM, revenue, reach or guaranteed virality.

## P5 — StoryLab and workflow automation
- Topic brief, audience, objective, format and tone.
- Research-backed outline with source capture and fact verification.
- Scene-by-scene storyboard with narration, visual direction, shot prompts and duration.
- Reference-image/style continuity and asset rights metadata.
- Provider adapters for image, video, voice and sound generation.
- Typed node graph for research, script, storyboard, media, voice, composition, captions, quality gate and publishing.
- Branching, parallel steps, reusable templates, autosave, versions, previews and downstream reruns.
- Durable workflow execution with logs, retries and cancellation.

## P6 — Accounts, collaboration and operations
- Secure authentication, email verification, recovery and sessions.
- Workspace/project authorization and tenant isolation.
- Roles, invitations, teams, comments, review/approval and audit history.
- Private object storage, signed expiring URLs and quotas.
- Data export, retention, deletion and backup/restore.
- Admin diagnostics, queue health, worker capacity and provider health.
- Usage metering, plans, credits, invoices and payment integration.
- Accessibility, keyboard navigation, reduced motion and mobile review.
- Desktop/local worker mode and hosted isolated processing mode.

## Global acceptance rules
1. No dead buttons, fake data or pretend provider connections.
2. Every feature has a real service/API, persisted state where required, useful loading/error/empty states and tests.
3. External integrations document scopes, quotas, regional limits, pricing and approval status.
4. Secrets never enter Git, browser bundles, logs or client-visible errors.
5. Media operations enforce resource limits, safe subprocess arguments, cleanup and observable failure states.
6. AI outputs are estimates with evidence and manual controls.
7. Each release includes tested migrations, rollback notes and an operations runbook.
