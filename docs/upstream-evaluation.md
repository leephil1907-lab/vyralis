# Upstream evaluation — automatic clipping and publishing

**Evaluated:** 2026-11-23 · **Method:** GitHub REST API only (repo metadata, licence metadata,
README contents, manifest files and top-level tree listings). Every entry below was fetched and
read; nothing is inferred from star counts alone. Re-verify before adoption — licences and
maturity move.

Scope: projects that turn long video into vertical clips (highlight detection, reframing,
captions, titles/hooks, export) and projects that can deliver clips to platforms automatically.

---

## 1. Short answer

| Rank | Project | Best at | Licence | Verdict for VYRALIS |
|---|---|---|---|---|
| 1 | [Clips Kitty / clips-studio](https://github.com/ColinGPT9/clips-studio) | Complete loop including **OAuth publishing to YouTube, TikTok and Instagram** (per its README) | AGPL-3.0 | **Reference architecture only.** Study the publishing flow; do not vendor the code. |
| 2 | [opensource-clipping](https://github.com/NaufalRizqullah/opensource-clipping) | Richest render feature set: karaoke ASS captions, MediaPipe framing, hooks, B-roll, thumbnails | MIT | **Best code to learn from.** Permissive licence; needs a paid LLM key for curation. |
| 3 | [NeonClipping](https://github.com/iamajmeena/neonclipping) | Efficiency engineering: audio-first moment discovery, YouTube-caption fast path, downloads only chosen sections, feedback-weighted ranking | MIT | **Best ideas per line of code.** 4 days old at evaluation — treat as unproven. |
| 4 | [AutoClip](https://github.com/artbyjazi/autoclip) | Clean local-first loop with honest scope statements; Whisper + Ollama, speaker-tracked reframe, 3 aspect ratios | MIT | **Use as the review-UX reference.** Explicitly pre-1.0. |
| 5 | [yt-short-clipper](https://github.com/jipraks/yt-short-clipper) | Desktop UX (Tauri) and word-level captions taken from existing YouTube subtitles — no speech model needed | MIT | Good UX reference; Windows beta, YouTube-only, uploads via third-party Repliz. |
| 6 | [SupoClip](https://github.com/FujiwaraChoki/supoclip) | Polished product surface (hosted + iOS + Docker) | **SupoClip Noncommercial Source License** | **Do not use.** Commercial/agency use requires written permission from Shiori LLC. |
| 7 | [AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | Nothing local — it is a thin client for the paid **MuAPI** cloud | MIT | **Avoid as a reference.** 6.5k stars overstate the open-source substance. |
| 8 | [auto-editor](https://github.com/WyattBlue/auto-editor) | Silence/dead-air cutting, extremely mature | Unlicense | **Adopt as a component**, not as a clipper. |

**Bottom line for the question "can something do link → clip → auto-post?"** Yes — Clips Kitty
publishes to YouTube, TikTok and Instagram through OAuth, on a schedule, including an
auto-watch mode for a channel; opensource-clipping ships scheduled YouTube/Facebook uploaders.
Everything else stops at "export an MP4". But the only projects with real auto-posting are
AGPL-licensed (Clips Kitty), noncommercial (SupoClip), or dependent on third-party paid
scheduling (Repliz in yt-short-clipper) — so this remains something we implement ourselves.

---

## 2. Full clipping applications

Facts as published in each repository at evaluation time.

### 2.1 Clips Kitty — `ColinGPT9/clips-studio`

- ★619 · 130 forks · 88 open issues · created 2026-06-11 · pushed 2026-11-22 · 45 MB · AGPL-3.0
- Sources: YouTube, Twitch VOD, Kick VOD, local file. Channel-watch mode spots a new upload
  through YouTube's RSS feed and processes it hands-off.
- Stack: Python engine + Windows installer (Microsoft Store build), Docker for contributors,
  `faster-whisper` word-level timestamps, local **Ollama** by default or **OpenRouter** over OAuth.
- Features: LLM transcript scoring, gaming/esports layouts (facecam + gameplay), captions,
  clip campaigns, `ROADMAP.md` / `KNOWN-ISSUES.md` / `ARCHITECTURE.md` maintained.
- **Publishing (README claim):** YouTube, TikTok and Instagram — now, scheduled, or hands-off
  for a watched channel. This is the only inspected project with a full, in-app publishing loop.
- Risks: AGPL-3.0 (network-service copyleft obligations), Windows-first runtime, 45 MB with
  vendored assets, 88 open issues.

### 2.2 opensource-clipping — `NaufalRizqullah/opensource-clipping`

- ★519 · 210 forks · created 2026-04-04 · pushed 2026-11-22 · 77 MB · MIT · v1.12.0
- Stack (pinned in `requirements.txt` / `pyproject.toml`): `yt-dlp[default]`, `faster-whisper`
  large-v3, `mediapipe`, `opencv-python`, `ultralytics`, `pyannote.audio`, `google-genai`,
  `openai`, `edge-tts`, `google-api-python-client`/`google-auth-oauthlib`, FastAPI + Docker.
- Features: LLM curation via Gemini, NVIDIA NIM or self-hosted vLLM; MediaPipe BlazeFace
  framing with smooth pan, deadzone and anti-jitter; karaoke `.ASS` word-highlighted subtitles;
  kinetic typography; 3-second hook teaser with glitch transitions; Pexels B-roll with Ken Burns;
  auto thumbnail; watermark engine; per-platform metadata.
- Uploaders present in-tree: `facebook_uploader/`, scheduled YouTube uploads.
- Risks: needs a paid/own-hosted LLM for curation; `ultralytics` is AGPL-3.0 (corporate
  licensing if you ship it), `pyannote` and `mediapipe` add heavy model downloads.

### 2.3 NeonClipping — `iamajmeena/neonclipping`

- ★2,177 · 127 forks · 30 open issues · **created 2026-11-19** · pushed 2026-11-21 · MIT
- Stack: FastAPI, `yt-dlp[default]`, `streamlink`, `pytchat`, `faster-whisper`, `opencv-python-headless`,
  `static-ffmpeg`, `numpy`, `Pillow`; modules include `curation.py`, `captions.py`,
  `captions_yt.py`, `camfx.py`, `creators.py`, `brands.py`, `cover.py`, `action.py`.
- Approach worth stealing: **audio-first** candidate discovery (extract audio only, ~79 MB for
  an 85-minute stream), take word-timed captions free from YouTube when available, score moments
  with a **local LLM (Ollama)**, snap cut points to sentence boundaries, then download **only the
  chosen sections** and match them back to the audio track. "Deep mode" adds optical-flow motion
  (Farneback) and cut-density signals.
- Also: 11 speaker layouts with automatic facecam finder, 5 caption styles + 52 languages +
  Hinglish, editable word-level captions, SRT/WebVTT/ASS import-export, live-chat-spike clipping,
  local feedback-based ranking weights (`data/feedback.jsonl`).
- **Publishing:** none visible in the README or top-level tree.
- Risks: created four days before this evaluation; single primary author; bold performance
  claims measured by the author; no external test-fixture evidence yet. MIT makes it safe to
  read and adapt with attribution.

### 2.4 AutoClip — `artbyjazi/autoclip`

- ★532 · 195 forks · 9 open issues · created 2026-07-31 · pushed 2026-08-01 · MIT
- Stack: Python `backend/` + React `frontend/`, `tests/`, Docker; Whisper + Ollama, or
  Anthropic/OpenAI/Gemini/OpenAI-compatible endpoints (text-only is sent to providers).
- Features: ingest (YouTube link or file) → transcription → highlight detection across four
  providers → speaker-tracked reframing → four caption styles → export at three aspect ratios →
  full review UI.
- Honesty signal: the README states the reframe quality bar has not been validated against a
  fixed golden set, which is why it is still pre-1.0.
- Risks: no pushes since 2026-08-01; no golden-output test set; no publishing.

### 2.5 yt-short-clipper — `jipraks/yt-short-clipper`

- ★1,106 · 313 forks · created 2026-01-15 · pushed 2026-09-20 · MIT · beta
- Stack: React 19 + TypeScript + Vite, Tauri v2 (Rust), Python sidecar (`openai`, `yt-dlp`,
  `opencv-python`, `mediapipe`, `Pillow`, `requests`).
- Features: LLM highlight segmentation (58–120 s default), free-text "direction" per video,
  three reframe modes (face tracking / black bars / blurred fill), word-by-word captions from
  YouTube's own subtitle track, hook overlays, watermark, direct upload through **Repliz**.
- Risks: Windows-only (PowerShell build, reads `C:\Windows\Fonts`), requires `cookies.txt` for
  YouTube, uploads depend on a third-party paid scheduling API, in-app wallet top-ups.

### 2.6 SupoClip - `FujiwaraChoki/supoclip`

- ★4,089 · 976 forks · 127 open issues · created 2025-07-28 · pushed 2026-11-23 · 508 MB
- **Licence: SupoClip Noncommercial Source License.** Self-hosting is free for noncommercial use
  and individual creators; companies, agencies, team use and paid hosting require written
  permission. GitHub reports the licence as `NOASSERTION`.
- This is the most-starred "open-source OpusClip alternative" and the one most likely to be
  recommended to you. It is **not** open source in the OSI sense and cannot be embedded in a
  commercial VYRALIS without a licence. Use only as a product/UX benchmark.

### 2.7 AI-Youtube-Shorts-Generator — `Anil-matcha/AI-Youtube-Shorts-Generator`

- ★6,486 · 1,191 forks · MIT · created 2024-06-28 · pushed 2026-11-21
- `requirements.txt` contains only `requests` and `python-dotenv`; the README leads with
  "Powered by MuAPI" and sells the "AI Clipping API" and "Auto-Crop API". Highlight detection,
  cropping and rendering happen in a paid cloud service.
- **Conclusion:** not a local clipper. Its star count reflects marketing of an API product, not
  open-source video processing. Do not use it to justify architectural decisions.

### 2.8 Also observed (metadata only, not deep-inspected)

| Repo | ★ | Licence | Last push | Note |
|---|---|---|---|---|
| `zhouxiaoka/autoclip_mvp` | 1,278 | MIT | 2025-09-15 | Stale ~14 months |
| `RafaelGodoyEbert/ViralCutter` | 520 | GPL-3.0 | 2026-09-10 | YouTube-only |
| `linzzzzzz/openclip` | 584 | MIT | 2026-08-24 | Highlight extraction, smaller scope |
| `louisedesadeleer/clipify` | 695 | MIT | 2026-08-24 | Claude Code *skill*, not an app |
| `nmbrthirteen/podcli` | 95 | AGPL-3.0 | 2026-11-19 | Face tracking, AGPL |
| `osbytes/reelsaw` | 26 | AGPL-3.0 | 2026-11-23 | Very new |
| `0jc1/py-autovod` | 32 | MIT | 2026-11-01 | Live: download → clip → upload loop |

---

## 3. Best-in-class components (adopt these rather than a monolith)

| Component | Repo | ★ | Licence | Role in VYRALIS |
|---|---|---|---|---|
| yt-dlp | `yt-dlp/yt-dlp` | 210,073 | Unlicense | Link ingestion adapter (subprocess) |
| faster-whisper | `SYSTRAN/faster-whisper` | 26,955 | MIT | Already our transcription engine |
| WhisperX | `m-bain/whisperX` | 25,608 | BSD-2-Clause | Word alignment + diarization upgrade path |
| pyannote-audio | `pyannote/pyannote-audio` | 10,834 | MIT | Speaker diarization (model terms apply) |
| PySceneDetect | `Breakthrough/PySceneDetect` | 5,624 | BSD-3-Clause | Shot boundaries, cut density |
| auto-editor | `WyattBlue/auto-editor` | 6,063 | Unlicense | Dead-air removal, silence trimming |
| MediaPipe | `google-ai-edge/mediapipe` | 37,790 | Apache-2.0 | Face/subject tracking for 9:16 reframing |
| Ollama | `ollama/ollama` | 187,899 | MIT | Local LLM for moment scoring and titles |
| Remotion | `remotion-dev/remotion` | 75,047 | **Company licence** | Programmatic overlays/captions — check licensing before shipping |
| yutu | `eat-pray-ai/yutu` | 732 | Apache-2.0 | Reference for YouTube Data API upload flows |
| FFmpeg | — | — | LGPL/GPL depending on build | Rendering, probing, filters (already used) |

Notes:
- `ultralytics` (YOLO) is **AGPL-3.0**; shipping it inside a hosted product triggers copyleft
  unless you hold a commercial licence. Prefer MediaPipe (Apache-2.0) for tracking.
- Remotion is source-available with a company licence fee above a small-team threshold — verify
  before depending on it for commercial templates.

## 4. Licence and risk traps found

1. **"Open source" with a noncommercial licence** — SupoClip (4k★). Needs written permission.
2. **Thin cloud wrappers presented as local tools** — Anil-matcha's 6.5k★ repo is a MuAPI client.
3. **AGPL in the delivery path** — Clips Kitty, reelsaw, podcli, and `ultralytics` as a dependency
   in opensource-clipping. Fine to read, risky to link into a hosted VYRALIS.
4. **Star counts reward marketing, not engineering** — the two most-starred "OpusClip
   alternatives" are a noncommercial product and an API wrapper.
5. **Legal, not technical, ceiling on ingestion** — every clipper relies on `yt-dlp`; downloading
   third-party VODs conflicts with YouTube/Twitch/Kick terms in many cases. Same for reposting
   someone else's stream. VYRALIS needs an explicit rights attestation on the import step.
6. **Auto-posting is gated by platform approval, not code** — YouTube OAuth verification,
   TikTok Content Posting audit, Instagram Graph for Business accounts. No amount of
   open-source code removes that queue.

## 5. Recommended VYRALIS stack

| Layer | Choice | Why |
|---|---|---|
| Ingestion | `yt-dlp` (+ `streamlink` for live) behind our own adapter | Unlicense, battle-tested; we keep SSRF allowlist, size/time caps and a rights checkbox |
| Speech | `faster-whisper` now, WhisperX when diarization lands | Already integrated; MIT/BSD |
| Candidate discovery | Audio-first energy + transcript LLM scoring (Ollama local, BYO key optional) + PySceneDetect + auto-editor | Mirrors NeonClipping's efficiency and Clips Kitty's scoring without their licences |
| Ranking explainability | Keep our score breakdown; add the "signals + reasons" payload LLMs return | Already a product principle |
| Reframing | MediaPipe face/subject detection with smoothing, deadzone and 11 layout presets | Apache-2.0; proven by three inspected projects |
| Captions | Word-timed ASS/SRT/VTT, karaoke styles, editable words | opensource-clipping and NeonClipping both prove the format |
| Render | Existing preset engine + quality gate (already built here) | No upstream dependency, already tested |
| Publishing | Our own official-API adapters: YouTube Data API v3 → TikTok Content Posting → Instagram Graph | Clips Kitty proves the flow; their code is AGPL |

Sequencing against `docs/roadmap.md`:

1. **Release 3** — link ingestion adapter (yt-dlp/streamlink), rights attestation, duration/size caps.
2. **Release 2** — captions (ASS + SRT/VTT), MediaPipe reframing, 11 layout presets.
3. **Release 4** — packaging export already exists; add YouTube OAuth upload, then TikTok after audit.
4. **Release 1** — audio-energy and scene signals alongside the transcript heuristic.

## 6. What not to do

- Do not vendor Clips Kitty, SupoClip or opensource-clipping as the VYRALIS engine; different
  stacks, heavy dependencies and licence conflicts.
- Do not call any of this "proven quality" on our behalf — none of the inspected projects
  publishes a golden-set reframe or caption accuracy benchmark.
- Do not promise "no watermark, automatic everywhere" publishing until the platform reviews in
  section 4.6 are actually completed for our own developer accounts.
