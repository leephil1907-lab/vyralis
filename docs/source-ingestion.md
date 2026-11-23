# VYRALIS Source Link Ingestion

## Current implementation
The local FastAPI API exposes:

- `POST /api/sources/preview` — resolves metadata with `yt-dlp --dump-single-json --skip-download` (no media fetched) so the creator can see the title, uploader and duration first. It returns 503 when yt-dlp is missing and 504 when the provider times out.
- `POST /api/projects/from-link` — the primary import. Requires `rights_attested: true`, creates the project, asset placeholder, source record and a persistent job of kind `ingest`, then returns the job id.
- `POST /api/ingest/url` — the earlier contract (`rights_confirmed`), kept for compatible clients. It validates the same way and queues the same worker path.
- `GET /api/projects/{id}/transcript` — the stored segments plus a word count, for review and caption verification.

The worker downloads the source with yt-dlp into the media store, settles whatever extension the downloader produced (remux or normalise to MP4, remove leftovers), checks size and duration, validates the media with FFprobe, updates the asset and then runs the existing transcription, ranking, caption and render pipeline on it.

The current UI exposes the paste-link field, shows the resolved source, and blocks import until the creator confirms they own the video or have permission to process it and that the use is permitted by the source platform.

## Supported source families
- YouTube: youtube.com and youtu.be
- Twitch: twitch.tv and clips.twitch.tv
- Kick: kick.com

These are extractor-supported public source families, not official platform download APIs. Actual availability varies by provider, content, region, age restrictions, account requirements and extractor compatibility. A platform may prohibit or restrict a particular download even when a URL is public.

## Safeguards
- HTTPS only; approved host allowlist (lookalike domains such as `youtube.com.evil.example` are rejected); reject embedded credentials, IP literals and custom ports.
- Resolve the initial host and reject private/non-public IP results (applies to the legacy endpoint, which resolves DNS itself).
- Reject YouTube ids that are not a well-formed 11-character id, so junk never reaches the downloader.
- Reject live/upcoming broadcasts and sources over `VYRALIS_MAX_SOURCE_DURATION` (default 4 hours) before download; cap the download at `VYRALIS_MAX_SOURCE_HEIGHT` (default 1080p) and `VYRALIS_MAX_SOURCE_BYTES` (default 4 GiB).
- The downloader's output name is sanitised (`safe_stem`) so a crafted title cannot change the destination path.
- No browser cookies, account session import, DRM bypass, paywall bypass or private-content access.
- No playlists; bounded retries, network timeout and configured maximum media size.
- Downloaded media must pass FFprobe before being added to the project.
- User must confirm ownership or permission and platform-permitted use.
- Never expose this unauthenticated local API as a public multi-user service.

## Known limitations
- The extractor is a third-party dependency, not a guarantee of platform availability.
- Provider page changes can break extraction; keep yt-dlp updated and monitor job failures.
- The DNS check protects the submitted hostname; hosted deployment still needs worker egress controls and redirect/CDN destination restrictions.
- No provider-specific official API, OAuth connection or selective segment retrieval is implemented yet. Metadata preview exists, but it is extractor metadata, not a platform API response.
- A provider download can fail even for a public URL. The job records the exact tool error and marks the project failed; nothing is simulated.
- This path imports a complete eligible source before transcription; it does not stream a live broadcast.
- Link ingestion still needs an end-to-end integration test against a rights-cleared sample from each provider.

## Local setup
Install backend/requirements.txt, which includes yt-dlp. Ensure FFmpeg (with libass for captions) and FFprobe are installed. Set VYRALIS_MAX_UPLOAD_BYTES for local uploads, and VYRALIS_MAX_SOURCE_DURATION, VYRALIS_MAX_SOURCE_HEIGHT and VYRALIS_MAX_SOURCE_BYTES for link imports. Submit a supported HTTPS URL to /api/projects/from-link with rights_attested=true (or /api/ingest/url with rights_confirmed=true). Poll the returned job_id through /api/jobs/{job_id}; when processing completes, review clips through /api/projects/{project_id}/clips, download captions from /api/clips/{clip_id}/captions, and render with caption style and framing options through /api/clips/{clip_id}/export.

## Error behavior
The API rejects unsupported hosts and invalid URLs before creating a project. Provider extraction, media validation and processing failures are persisted as failed job states with an explanatory error. A failed source import can be retried after the source or provider issue is corrected.
