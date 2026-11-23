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

## Hosted deployment target
Separate services:
- Frontend: static React build on a CDN/static host.
- API: FastAPI container behind HTTPS reverse proxy.
- Worker: separate process/container with FFmpeg and model dependencies.
- Database: managed PostgreSQL with migrations and automated backups.
- Queue: durable Redis-compatible queue or equivalent.
- Object storage: private bucket with signed URLs.
- Secrets: host-managed environment variables or secret manager.

## Configuration
VYRALIS_ENV, VYRALIS_DATA_DIR (local mode), VYRALIS_DATABASE_URL (hosted mode), VYRALIS_CORS_ORIGINS, VYRALIS_MAX_UPLOAD_BYTES, VYRALIS_WORKERS, VYRALIS_WHISPER_MODEL, VYRALIS_WHISPER_DEVICE and VYRALIS_WHISPER_COMPUTE. Provider credentials are added only when their integration exists; never commit real values.

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
