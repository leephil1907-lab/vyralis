# VYRALIS Studio

<p align="center"><img src="assets/vyralis-mark.svg" width="112" alt="VYRALIS symbol" /></p>
<h1 align="center">VYRALIS STUDIO</h1>
<p align="center"><strong>Every moment has a story.</strong></p>
<p align="center">An ambitious, local-first video intelligence and short-form production studio.</p>

---

## What VYRALIS is

VYRALIS is being developed as a complete video production workflow—not just an automatic clip cutter. Its goal is to turn long-form recordings into carefully selected, editable, social-ready video assets while keeping media processing local wherever practical.

## Product workflow

- **Discover:** analyse speech, scenes, visual events and pacing to identify promising moments.
- **Understand:** evaluate context, story completeness, speaker turns, hooks and clip boundaries.
- **Reframe:** create portrait, landscape and square compositions with subject-aware framing.
- **Edit:** build captions, titles, transitions, zooms, layouts and optional supporting visuals.
- **Render:** produce platform-ready exports with reliable, repeatable media processing.
- **Review:** let creators inspect, adjust and approve every suggested clip before publishing.

## Product principles

1. **Local-first media** — keep source footage on the creator's machine by default.
2. **Creator control** — AI suggestions are editable; the creator makes the final call.
3. **Evidence-led highlights** — recommendations should be traceable to transcript, scene and timing evidence.
4. **No fake capabilities** — integrations are labelled accurately as planned, experimental or production-ready.
5. **Composable architecture** — use specialised tools behind clear interfaces rather than coupling the product to one model.
6. **Respect source rights** — users are responsible for having permission to process and publish supplied media.

## Planned capabilities

| Area | Direction |
|---|---|
| Media intake | Local files and supported public video sources |
| Transcription | Accurate transcription with word-level timestamps |
| Speaker analysis | Speaker diarization and active-speaker cues |
| Visual analysis | Scene changes, faces, objects and visual events |
| Highlight discovery | Context-aware candidate clips with explainable scores |
| Reframing | 9:16, 1:1 and 16:9 subject-aware layouts |
| Captions | Editable, word-timed caption styles |
| Creative editing | Hooks, titles, overlays, zooms and optional B-roll |
| Rendering | Reproducible exports from a dedicated media pipeline |
| Workflow | Project history, clip review and batch processing |

These are product goals, not a claim that every capability is implemented today. The repository now contains the first React + TypeScript studio interface and a local FastAPI media-ingestion service. The advanced AI analysis and editing engines are still being integrated.

## Design identity

- **Name:** VYRALIS Studio
- **Tagline:** Every moment has a story.
- **Category:** Intelligent Video Production
- **Visual direction:** cinematic, minimal, premium and technically precise
- **Palette:** Midnight `#090B18`, violet `#A855F7`, electric blue `#397BFF`, cyan `#26E5E1`
- **Typography direction:** Space Grotesk or Sora
- **Symbol:** an abstract V-shaped frame with an integrated play motif

## Architecture direction

VYRALIS will use modular adapters for specialised capabilities. Candidate technologies for evaluation include:

- **Transcription and alignment:** Whisper / WhisperX
- **Scene analysis:** PySceneDetect
- **Face and object analysis:** MediaPipe and compatible detection/tracking models
- **Video rendering:** FFmpeg
- **Programmatic motion graphics:** Remotion
- **Local model runtime:** configurable local inference backends

Every dependency will be evaluated for maintenance, hardware requirements, security, licence compatibility and redistribution terms before adoption. No external project is assumed to be integrated merely because it appears in this list.

## Development status

**Status: Foundation / architecture and implementation in progress.**

The first application foundation is committed: responsive studio dashboard, backend health endpoint, local media upload and asset listing. There is not yet an end-to-end AI clipping workflow or production installer. Features will be marked complete only after implementation and verification.

## Contributing

The project structure, development setup, coding standards and contribution workflow will be documented as implementation is established. Early contributors should open an issue to discuss substantial changes before submitting a pull request.

## Licence

A project licence will be selected after reviewing the intended dependencies, model licences and distribution strategy.