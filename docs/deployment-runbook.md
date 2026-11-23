# VYRALIS Deployment and Operations Runbook

## Current repository reality
The root Dockerfile builds the FastAPI API and installs FFmpeg; it does not build or serve the React frontend. The current SQLite API is a single-workspace foundation without authentication or tenant isolation. Do not expose it publicly as a multi-user production service.

## Local development
Requirements: Python 3.11, Node.js 20+, FFmpeg and FFprobe.
1. Create and activate a Python virtual environment.
2. Install backend/requirements.txt.
3. Set VYRALIS_DATA_DIR to a persistent local directory.
4. Start FastAPI on loopback.
5. Install npm dependencies and run the Vite development server.
6. Set VITE_API_BASE_URL to the local API.
7. Upload a rights-cleared test video and complete the core workflow.

## Render deployment (single instance, current codebase)

The blueprint in `render.yaml` builds the Docker image (Debian FFmpeg with libass,
yt-dlp from requirements) and mounts a 20 GB disk at `/var/lib/vyralis`.

1. Push the repository to GitHub and create a Render **Blueprint** from it.
2. Set the required values: `VYRALIS_PUBLIC_URL` (this service's URL),
   `VYRALIS_FRONTEND_URL` (the Vercel/static studio URL), `VYRALIS_CORS_ORIGINS`
   (same frontend URL), and `VYRALIS_BASIC_AUTH` as `user:password`.
3. Deploy the frontend separately: `npm run build`, publish `dist/` on Vercel, and set
   `VITE_API_BASE_URL=https://<api-host>` in the Vercel project.
4. Open the API's `/api/health` to confirm it is live, then the studio URL and connect a
   platform (see `docs/oauth-setup.md`). The OAuth redirect URI is
   `https://<api-host>/api/oauth/<platform>/callback`.

Operational notes:

- **One instance only.** The queue is an in-process thread pool and the database is SQLite
  on the mounted disk. Scaling to two instances would double-run jobs and corrupt state.
- **Disk, not object storage.** Media lives on the disk; redeploys keep it because the disk
  is persistent, but a lost disk loses media. Back up `/var/lib/vyralis` or move to object
  storage before relying on it.
- **First job is slow.** faster-whisper downloads the configured model on first use unless
  you bake it into the image. Expect a minute or two on the first transcription.
- **Cost.** Starter + 20 GB disk is roughly the minimum viable size; Whisper "base" on CPU
  handles short clips but long videos are slow. Use a bigger plan or a smaller model.
- **Access control.** Set `VYRALIS_BASIC_AUTH` before making the service public: the API is
  still single-workspace and has no per-user accounts. Each browser session prompts once
  and reuses the credentials for the studio's API calls.
- **HTTPS is mandatory** for provider redirect URIs; Render provides it on `*.onrender.com`.

## Hosted deployment target (multi-tenant, not built yet)
Separate services:
- Frontend: static React build on a CDN/static host.
- API: FastAPI container behind HTTPS reverse proxy.
- Worker: separate process/container with FFmpeg and model dependencies.
- Database: managed PostgreSQL with migrations and automated backups.
- Queue: durable Redis-compatible queue or equivalent.
- Object storage: private bucket with signed URLs.
- Secrets: host-managed environment variables or secret manager.

## Configuration
VYRALIS_DATA_DIR, VYRALIS_CORS_ORIGINS, VYRALIS_MAX_UPLOAD_BYTES, VYRALIS_WORKERS,
VYRALIS_WHISPER_MODEL/DEVICE/COMPUTE, VYRALIS_PUBLIC_URL, VYRALIS_FRONTEND_URL,
VYRALIS_AUTH_SECRET (token encryption) and VYRALIS_BASIC_AUTH (hosted access gate).
Social platform clients: GOOGLE_CLIENT_ID/SECRET, TIKTOK_CLIENT_KEY/SECRET, META_APP_ID/SECRET,
X_CLIENT_ID/SECRET. Never commit real values; `.env.example` lists the full set.

## Release checklist
- [ ] Frontend build and typecheck pass.
- [ ] Backend compile and unit tests pass.
- [ ] Migrations apply on empty and existing databases.
- [ ] Worker restart recovery and retry tested.
- [ ] Upload and output checks pass on representative test media.
- [ ] Auth and tenant isolation verified before public exposure.
- [ ] HTTPS, CORS, rate limits, storage privacy and backups verified.
- [ ] Health/readiness checks distinguish API, database, queue, storage and worker.
- [ ] Logs redact tokens and private media URLs.
- [ ] Rollback image and migration plan documented.

## Operations
Monitor queue age, worker utilization, failure rate, processing time per media minute, upload rejection, render validation failures, storage and provider limits. Alert on stuck jobs, repeated retries, worker crashes, database exhaustion and storage thresholds.
