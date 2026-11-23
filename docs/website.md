# VYRALIS — public website

The Vite app serves two experiences from one build:

| Route | Experience |
|---|---|
| `/` | Public marketing site (`src/pages/LandingPage.tsx`, `src/landing.css`) |
| `/studio` | Studio dashboard (the workspace app in `src/App.tsx`) |
| `/create`, `/projects`, `/editor`, `/publishing`, `/calendar`, `/analytics`, `/growth`, `/trends`, `/storylab`, `/canvas`, `/brand`, `/settings`, `/review/:projectId` | Existing studio surfaces, unchanged |

`App.tsx` returns the landing page for the exact path `/`; every other path renders the studio shell, so the product routes keep working without a second router or a hosting rewrite.

## Design direction

Two directions were supplied for review:

1. **Monochrome brutalist** — black type on grey, heavy grotesque display, sharp collaged tiles.
2. **Creativity in Motion** — cream paper, deep violet display type, coral accents, rounded cards and soft 3D forms.

Direction 2 was chosen:

- It already carries the VYRALIS name and reads as the same brand as the mark in `assets/vyralis-mark.svg`.
- Cream/violet keeps the studio's violet accent, where the monochrome option would have introduced a second, competing identity.
- Soft 3D motion imagery describes the product (moving footage, clips, rhythm) far better than an agency-style collage.
- Warm surfaces suit creator review work; the studio app itself stays dark for video viewing.

## Design tokens

Defined on `.vy-site` in `src/landing.css`:

| Token | Value | Use |
|---|---|---|
| `--cream` | `#FBF6EA` | Page background |
| `--cream-deep` | `#F4E9D5` | Alternating panels, CTA |
| `--paper` | `#FFFCF5` | Cards |
| `--violet` | `#4A1E7A` | Display type, primary buttons |
| `--violet-2` | `#6B3AA7` | Hover, accents |
| `--violet-soft` | `#EADCF7` | Chips, icon tiles |
| `--coral` | `#ED6247` | Accent words, live markers |
| `--coral-soft` | `#FBD9CE` | Soft highlights |
| `--ink` / `--muted` | `#2A1B36` / `#6F5F7C` | Body text |

Fonts: Poppins (display), DM Sans (body), Instrument Serif (italic accents), Space Grotesk (labels). All are loaded from Google Fonts; system fallbacks are declared.

## Page structure

1. Announcement bar with the current studio version.
2. Sticky navigation, mobile menu, "Open studio" CTA.
3. Hero — headline, positioning copy, and a four-tile 3D collage.
4. Capability marquee.
5. Pipeline — the five real steps (import, listen, rank, review, export) plus a ranked-candidate preview and a score-breakdown panel, both explicitly labelled as interface previews.
6. Capabilities — the working foundation only.
7. Studio surfaces — the six studios (Clip, Edit, Creative, Growth, Publish, Analytics), each labelled live, limited or planned.
8. Roadmap — release-scoped, no dates promised.
9. Principles, closing CTA, footer.

## Copy rules

- A surface is **Live** only when the local pipeline performs it end to end (see `docs/feature-registry.md`).
- Edit Studio is **Limited**, not Planned: caption burn-in (three styles, hooks) and automatic reframing (centre, blurred fill, optional face tracking) ship today from Review; the timeline, split/merge and templates do not exist yet.
- No fabricated reach, RPM, trend ranking or provider connection anywhere on the page.
- Example scores on the preview panel are labelled heuristics, not virality predictions.
- Every link resolves to a real route or a document in this repository.

## Assets

`public/assets/landing/` holds four generated 3D stills (`shapes-hero`, `torus`, `ribbon`, `toys`) as WebP under 45 KB each. They are decorative; alt text describes the shapes rather than implying product screenshots. The studio mark stays at `public/assets/vyralis-mark.svg`.

## Accessibility and motion

- Semantic landmarks, labelled sections, visible focus rings, and a 44 px minimum target for primary actions.
- `prefers-reduced-motion` disables the marquee and transitions.
- Reveal animations use `whileInView` with `once`, so content is present for crawlers and assistive technology.

## Development

```bash
npm install
npm run dev     # site at /, studio at /studio
npm run build   # typecheck + production build
```

The dev server binds `0.0.0.0` and permits proxy hosts (`allowedHosts: true`) so sandbox preview URLs work.
