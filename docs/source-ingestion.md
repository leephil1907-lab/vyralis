# VYRALIS Source Link Ingestion

## Current implementation
The local FastAPI API exposes POST /api/ingest/url. The request includes a source URL and an explicit rights confirmation. It creates a project, asset placeholder and persistent job, then downloads the source in a background worker using yt-dlp. Once downloaded, the worker checks file size, validates the media with FFprobe, stores the source in the same media library and hands the project to the existing transcription/highlight pipeline.

The current UI exposes the paste-link field and requires the user to confirm that they own the video or have permission to process it and that the use is permitted by the source platform.

## Supported source families
- YouTube: youtube.com and youtu.be
- Twitch: twitch.tv and clips.twitch.tv
- Kick: kick.com

These are extractor-supported public source families, not official platform download APIs. Actual availability varies by provider, content, region, age restrictions, account requirements and extractor compatibility. A platform may prohibit or restrict a particular download even when a URL is public.

## Safeguards
- HTTPS only; approved host allowlist; reject embedded credentials and custom ports.
- Resolve the initial host and reject private/non-public IP results.
- No browser cookies, account session import, DRM bypass, paywall bypass or private-content access.
- No playlists; bounded retries, network timeout and configured maximum media size.
- Downloaded media must pass FFprobe before being added to the project.
- User must confirm ownership or permission and platform-permitted use.
- Never expose this unauthenticated local API as a public multi-user service.

## Known limitations
- The extractor is a third-party dependency, not a guarantee of platform availability.
- Provider page changes can break extraction; keep yt-dlp updated and monitor job failures.
- The DNS check protects the submitted hostname; hosted deployment still needs worker egress controls and redirect/CDN destination restrictions.
- No provider-specific official API, OAuth connection, metadata preview or selective segment retrieval is implemented yet.
- This path imports a complete eligible source before transcription; it does not stream a live broadcast.
- Link ingestion still needs an end-to-end integration test against a rights-cleared sample from each provider.

## Local setup
Install backend/requirements.txt, which includes yt-dlp. Ensure FFmpeg and FFprobe are installed. Set VYRALIS_MAX_UPLOAD_BYTES to the maximum source size. Submit a supported HTTPS URL to /api/ingest/url with rights_confirmed=true. Poll the returned job_id through /api/jobs/{job_id}; when processing completes, review clips through /api/projects/{project_id}/clips.

## Error behavior
The API rejects unsupported hosts and invalid URLs before creating a project. Provider extraction, media validation and processing failures are persisted as failed job states with an explanatory error. A failed source import can be retried after the source or provider issue is corrected.
