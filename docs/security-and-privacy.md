# VYRALIS Security, Privacy and Rights Requirements

## Release-blocking controls
- Do not expose the current unauthenticated single-workspace API as a public multi-user service.
- Bind local API to loopback by default. Restrict CORS to explicit origins.
- Hosted APIs require authentication, workspace membership and resource ownership checks on every route.
- Never return filesystem paths, internal stack traces, secrets or provider tokens.
- Encrypt OAuth refresh tokens and API credentials at rest; redact logs and support revocation.
- Use secure HttpOnly SameSite cookies or a reviewed token design; add CSRF protection for cookie-authenticated writes.
- Rate-limit login, upload, URL resolution, job creation, export and provider callbacks.
- Validate size, extension, detected MIME, media probe and stream count. Generate server-side names.
- Isolate worker temp directories; constrain CPU, memory, disk, duration and concurrency.
- Use subprocess argument arrays; never interpolate untrusted input into shell commands.
- Prevent SSRF in URL ingestion: allowlist provider hosts, resolve DNS safely, block private/link-local/loopback ranges, revalidate redirects and enforce egress policy.
- Do not bypass DRM, paywalls, account controls or platform restrictions. Use official APIs or permitted provider methods.
- Keep media private; define retention, deletion, export and backup policies.
- Audit account connections, publication approvals and destructive changes.

## Rights and consent
Require users to confirm processing rights. Track source URL, creator/owner, license/permission and attribution. Require explicit consent and rights checks for cloned voices, likenesses and generated assets. Music, B-roll, fonts and templates need documented commercial-use terms. Publishing requires preview and human approval by default.

## Privacy
Disclose local vs third-party processing and provider retention/training terms before sending media externally. Provide opt-in analytics where required and account export/deletion. Avoid unnecessary personal data. Set configurable retention for source, proxies, transcripts, renders and logs.

## Security verification
Test authorization boundaries, path traversal, upload limits, malformed media, SSRF, retries and signed URL expiry. Add dependency/container scanning, secret scanning, backup restore drills and deletion verification before hosted production.
