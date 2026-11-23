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

## Readability pass

The first build set labels at 9px and body copy at 10–11px, which is too small to read at
100% zoom on a laptop. The studio now uses a 10.5 / 11.5 / 12.5px scale for micro labels,
helper text and body copy respectively, with mirrored selector overrides at the end of
`src/styles.css` so the minified rules above stay untouched and auditable. Muted colour
(`#99a4bf`) replaces the darker greys those sizes previously used, which keeps small text
above 4.5:1 contrast on the card background.

Form controls in Review and Publish previously fell back to the browser's white default
inputs because only the source bar and search box were styled. `label > input/textarea/select`
now share the dark control style, with checkboxes excluded so toggle rows stay compact.

## Accessibility and motion

- Semantic landmarks, labelled sections, visible focus rings, and a 44 px minimum target for primary actions.
- `prefers-reduced-motion` disables the marquee and transitions.
- Reveal animations use `whileInView` with `once`, so content is present for crawlers and assistive technology.

## Information architecture

The public site is a single narrative page (`/`) plus a documentation section and the
studio. Reference tools in the category (Klap, Vizard, Eklipse, WayinVideo) all run the
same shape: a tool/page cluster for search, a hero that takes an input, and a prose
library behind it. VYRALIS now matches the parts that earn their keep without
publishing invented statistics, fake reviews or comparison claims.

### Landing hero

The hero leads with the work rather than a promise. A live input takes a YouTube, Twitch
or Kick URL, validates it, and hands it to `/create?url=…&focus=url`, where the field is
prefilled and the rights confirmation still has to be ticked. Invalid input returns an
inline message instead of navigating. "Open the studio" remains for people who want to
upload a file first.

### Documentation section

`/docs` is an index of the eleven documents in `docs/`, grouped into *Start here*,
*Engineering*, *Running it* and *Reference*. `/docs/<slug>` renders the markdown with:

- a sticky grouped sidebar with a filter box;
- an on-page outline built from the document's `##`/`###` headings, skipping fenced code;
- GFM tables and code blocks styled for the dark surface;
- relative `.md` cross-links rewritten to in-app routes, external links opened in a new tab;
- previous/next paging in manifest order and a real not-found state for unknown slugs.

Documents are loaded through `import.meta.glob` with a lazy loader, so the markdown
renderer and each document live in their own chunk; the main bundle is unaffected apart
from the manifest.

### Command palette

`⌘K` / `Ctrl+K` opens a real palette (the hint on *Create clips* previously had no
handler behind it). It searches pages, documents and actions — import from a link,
upload a file, check engine status, open the public site — with arrow keys, `Enter` to
run and `Escape` to close. The top bar exposes the same entry point for pointer users.

### Navigation contract

- Public site nav: Workflow, Capabilities, Studio, **Docs** (internal route, not a raw
  `.md` link on GitHub), then Open studio.
- Studio sidebar groups: Workspace, Clip studio, Edit studio, Creative studio, Growth
  intelligence, Publish studio, **Resources → Documentation**.
- Footer: Product anchors, Workspace routes, Documentation (index plus three documents),
  GitHub, version.

## Testing

`npm test` runs Vitest with jsdom (`src/test/setup.ts` supplies the browser features
jsdom lacks). The suite covers the documentation manifest against the real files, the
markdown outline extraction, the landing entry point and its validation, the docs index,
a real document rendering, the unknown-slug state, and the studio shell including the
palette shortcut, filtering, navigation and Escape handling, plus the `?url=` handoff.

## Development

```bash
npm install
npm run dev     # site at /, studio at /studio
npm test        # frontend regression suite
npm run build   # typecheck + production build
```

The dev server binds `0.0.0.0` and permits proxy hosts (`allowedHosts: true`) so sandbox preview URLs work.
