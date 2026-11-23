# VYRALIS API Contract — Target v1

This is the target contract, not a claim that these routes already exist. The current local foundation uses unversioned /api routes. Maintain compatibility during migration.

## Conventions
JSON UTF-8; UTC ISO-8601; stable errors with code, message, optional details and request_id; cursor pagination; Idempotency-Key for consequential writes. Long-running work returns 202 with job_id, status and status_url.

## Authentication and workspace
- POST /api/v1/auth/register, /login, /logout, /refresh
- POST /api/v1/auth/password/forgot and /reset
- GET /api/v1/me
- GET|POST /api/v1/workspaces
- GET|PATCH|DELETE /api/v1/workspaces/{workspace_id}
- GET|POST /api/v1/workspaces/{workspace_id}/members
- PATCH|DELETE /api/v1/workspaces/{workspace_id}/members/{member_id}

## Media and projects
- POST /api/v1/uploads; PUT /uploads/{upload_id}/parts/{part_number}; POST /uploads/{upload_id}/complete
- GET /api/v1/assets; GET /assets/{asset_id}; DELETE /assets/{asset_id}
- POST /api/v1/projects; GET /api/v1/projects; GET|PATCH|DELETE /api/v1/projects/{project_id}
- GET /api/v1/projects/{project_id}/source

## Analysis and jobs
- POST /api/v1/projects/{project_id}/analysis
- GET /api/v1/jobs/{job_id}; GET /api/v1/jobs/{job_id}/events
- POST /api/v1/jobs/{job_id}/retry and /cancel
- GET /api/v1/projects/{project_id}/transcript
- GET /api/v1/projects/{project_id}/candidates
- POST /api/v1/candidates/{candidate_id}/feedback

## Editing and rendering
- POST /api/v1/clips; GET|PATCH /api/v1/clips/{clip_id}
- POST /api/v1/clips/{clip_id}/versions, /split and /merge
- GET|PUT /api/v1/clips/{clip_id}/edit-decision-list
- POST /api/v1/clips/{clip_id}/renders
- GET /api/v1/renders/{render_id}; GET /api/v1/renders/{render_id}/download

## Captions, brand and repurposing
- GET|POST /api/v1/caption-presets
- GET|POST /api/v1/brand-kits; GET|PATCH|DELETE /api/v1/brand-kits/{brand_kit_id}
- POST /api/v1/clips/{clip_id}/metadata and /repurpose

## Publishing and analytics
- GET /api/v1/publishing/providers
- POST /api/v1/connections/{provider}/authorize; GET /api/v1/connections; DELETE /api/v1/connections/{connection_id}
- POST /api/v1/posts/drafts; GET /api/v1/posts; PATCH /api/v1/posts/{post_id}
- POST /api/v1/posts/{post_id}/schedule and /publish
- GET /api/v1/posts/{post_id}/attempts
- GET /api/v1/analytics/overview; GET /api/v1/analytics/posts/{post_id}
- GET /api/v1/trends/signals; GET /api/v1/niches; POST /api/v1/niches/compare

## StoryLab and workflow canvas
- POST /api/v1/storyboards; GET|PATCH /api/v1/storyboards/{storyboard_id}
- POST /api/v1/storyboards/{storyboard_id}/research
- GET|POST /api/v1/workflows; GET|PATCH|DELETE /api/v1/workflows/{workflow_id}
- POST /api/v1/workflows/{workflow_id}/runs
- GET /api/v1/workflow-runs/{run_id}; GET /api/v1/workflow-runs/{run_id}/events

## Settings and operations
- GET|PATCH /api/v1/settings; GET /api/v1/providers/health
- GET /api/v1/usage and /usage/records
- GET /api/v1/notifications; PATCH /api/v1/notifications/{notification_id}
- GET /api/v1/audit-events

## Existing local API (implemented today)
- `GET /api/health`
- `GET|POST /api/assets`
- `POST|GET /api/projects`; `GET /api/projects/{project_id}/clips`; `GET /api/projects/{project_id}/source`
- `GET /api/jobs/{job_id}`; `POST /api/jobs/{job_id}/retry`; `POST /api/jobs/{job_id}/cancel`
- `PATCH /api/clips/{clip_id}`; `GET /api/clips/{clip_id}/download`
- `GET /api/export-presets`; `GET /api/destinations`
- `POST /api/clips/{clip_id}/export` (optional `{ "preset": "9:16" | "1:1" | "16:9" }`, idempotent while a matching render is active)
- `GET /api/clips/{clip_id}/exports`; `GET /api/exports/{export_id}/download`
- `GET|PUT /api/clips/{clip_id}/packaging`; `POST /api/clips/{clip_id}/packaging/approval`
- `GET /api/publish/packages`

These are the only routes that exist. Everything else in this document is a target. Add tests and a deprecation plan before removing or renaming them.
