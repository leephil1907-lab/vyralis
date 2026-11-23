import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ArrowRight, ArrowUpRight, AudioLines, ChartNoAxesCombined,
  Clapperboard, Film, Layers3, ListChecks, Menu, Network, Palette, Play,
  Compass, Radio, RotateCcw, Scissors, ShieldCheck, Sparkles, Upload, X,
} from "lucide-react";
import "../landing.css";

const navLinks = [
  { label: "Workflow", href: "#workflow" },
  { label: "Capabilities", href: "#capabilities" },
  { label: "Studio", href: "#studio" },
  { label: "Roadmap", href: "#roadmap" },
];

const pipeline = [
  {
    icon: Upload, title: "Import", status: "live" as const,
    copy: "Upload MP4, MOV, MKV, WebM or AVI, or paste an eligible YouTube, Twitch or Kick link. FFprobe validates the media before anything runs.",
  },
  {
    icon: AudioLines, title: "Listen", status: "live" as const,
    copy: "FFmpeg extracts 16 kHz mono audio and faster-whisper returns segment and word-level timestamps.",
  },
  {
    icon: ListChecks, title: "Rank", status: "live" as const,
    copy: "Transcript windows become candidates with a readable score breakdown — never a black-box virality number.",
  },
  {
    icon: Scissors, title: "Review", status: "live" as const,
    copy: "Compare candidates, read the transcript, then set start, end and title yourself — the final cut stays yours.",
  },
  {
    icon: Film, title: "Render & check", status: "live" as const,
    copy: "Pick 9:16, 1:1 or 16:9, burn in word-timed captions and a hook line, choose centre, blurred or face-tracked framing. FFmpeg renders it, then duration, frame size, codecs, black/frozen frames and loudness are verified before download.",
  },
];

const candidates = [
  { title: "The ninety-second pivot that changed everything", time: "00:42 — 01:18", score: "86", cls: "s1" },
  { title: "Nobody tells you this about first drafts", time: "12:05 — 12:41", score: "74", cls: "s2" },
  { title: "Why the third attempt is the real one", time: "24:10 — 24:52", score: "61", cls: "s3" },
];

const capabilities = [
  {
    icon: ShieldCheck, title: "Import from disk or a link",
    copy: "Uploads stream to disk and links resolve through yt-dlp with a host allowlist, a rights confirmation, duration caps and a public-DNS check. FFprobe then confirms container, duration and streams; failed sources never enter a project.",
  },
  {
    icon: AudioLines, title: "Word-level transcription",
    copy: "Segment and word timestamps let you search the transcript, jump to a moment and cut against the spoken line.",
  },
  {
    icon: ListChecks, title: "Explainable candidate ranking",
    copy: "Every candidate carries its reasons: hook strength, context completeness, speech density and payoff signal.",
  },
  {
    icon: Clapperboard, title: "You keep the final cut",
    copy: "Adjust in and out points, rewrite the title, re-render. Nothing is exported behind your back.",
  },
  {
    icon: Film, title: "Captioned, reframed render",
    copy: "Word-timed captions in three styles, an optional hook overlay, and a deterministic H.264/AAC export with progress you can follow — plus SRT, VTT and ASS sidecars.",
  },
  {
    icon: RotateCcw, title: "Jobs that survive interruption",
    copy: "Projects, jobs and clips live in SQLite, so queued work is recovered when a worker restarts, and cancellation is honoured at checkpoints.",
  },
];

const surfaces = [
  { icon: Clapperboard, label: "Clip Studio", copy: "Import, transcribe, rank candidates and trim the cut", state: "Live" },
  { icon: Scissors, label: "Edit Studio", copy: "Burn-in captions and automatic reframing today; timeline editing and templates next", state: "Limited" },
  { icon: Palette, label: "Creative Studio", copy: "StoryLab planning, brand kits and the workflow canvas", state: "Planned" },
  { icon: Compass, label: "Growth Intelligence", copy: "Profile audits, hooks and ideas once authorized data is connected", state: "Planned" },
  { icon: Radio, label: "Publish Studio", copy: "Validated packaging, approved delivery packages and real account connections; posting awaits platform approval", state: "Limited" },
  { icon: ChartNoAxesCombined, label: "Analytics Studio", copy: "Performance learning from authorized platform metrics only", state: "Planned" },
];

const roadmap = [
  {
    icon: Scissors, title: "Professional editor & caption lab",
    copy: "Timeline editing, split and merge, caption templates, brand kits and version history. Caption burn-in and auto-reframing already ship; this release adds the editing surface around them.",
    stage: "Release 2",
  },
  {
    icon: Radio, title: "Publishing & calendar",
    copy: "Account connections and token handling ship today; direct posting needs approved platform apps, then timezone-aware scheduling, approval steps and delivery receipts. No simulated posting.",
    stage: "Release 4",
  },
  {
    icon: ChartNoAxesCombined, title: "Analytics & growth intelligence",
    copy: "Only metrics exposed by authorized platforms, compared by hook, format and length — never invented reach or earnings.",
    stage: "Release 5",
  },
  {
    icon: Network, title: "StoryLab & workflow canvas",
    copy: "Research-backed storyboards plus a typed workflow engine with previews, retries and cancellation.",
    stage: "Release 6",
  },
];

const principles = [
  { n: "01", title: "Real workflows, not demo screens", copy: "If a surface is not connected end to end, it says so on the screen." },
  { n: "02", title: "Creator approval by default", copy: "Nothing renders, publishes or overwrites without your say." },
  { n: "03", title: "Evidence, not virality promises", copy: "Scores show their reasons, their weights and their limits." },
  { n: "04", title: "Authorized integrations only", copy: "Official APIs, explicit scopes and access you can revoke." },
];

const docsBase = "https://github.com/leephil1907-lab/vyralis/blob/main/docs";

function Reveal({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function Brand({ onClick }: { onClick?: () => void }) {
  return (
    <a className="vy-brand" href="#top" onClick={onClick} aria-label="VYRALIS Studio home">
      <img src="/assets/vyralis-mark.svg" alt="" />
      <span>
        <b>VYRALIS</b>
        <small>STUDIO</small>
      </span>
    </a>
  );
}

export default function LandingPage() {
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const previousScroll = root.style.scrollBehavior;
    const previousRootBg = root.style.backgroundColor;
    const previousBodyBg = document.body.style.backgroundColor;
    root.style.scrollBehavior = "smooth";
    root.style.backgroundColor = "#FBF6EA";
    document.body.style.backgroundColor = "#FBF6EA";
    return () => {
      root.style.scrollBehavior = previousScroll;
      root.style.backgroundColor = previousRootBg;
      document.body.style.backgroundColor = previousBodyBg;
    };
  }, []);

  useEffect(() => {
    document.body.style.overflow = menu ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menu]);

  return (
    <div className="vy-site" id="top">
      <div className="vy-announce">
        <span>
          <i className="vy-dot" /> <b>Studio 0.3</b> — the local clipping pipeline is live: import, transcribe, rank, review, render, package.
          <a href="/studio">Open the studio <ArrowUpRight size={11} style={{ display: "inline", verticalAlign: "-1px" }} /></a>
        </span>
      </div>

      <div className="vy-nav-wrap">
        <div className="vy-shell">
          <nav className="vy-nav" aria-label="Primary">
            <Brand />
            <ul className="vy-nav-links">
              {navLinks.map((l) => <li key={l.href}><a href={l.href}>{l.label}</a></li>)}
              <li><a href={docsBase + "/feature-registry.md"} target="_blank" rel="noreferrer">Docs</a></li>
            </ul>
            <div className="vy-nav-right">
              <span className="vy-nav-status"><i />Local-first</span>
              <Link className="vy-btn vy-btn-primary vy-btn-sm" to="/studio">
                Open studio <ArrowRight size={14} />
              </Link>
              <button className="vy-burger" onClick={() => setMenu(true)} aria-label="Open menu" aria-expanded={menu}>
                <Menu size={19} />
              </button>
            </div>
          </nav>
        </div>
      </div>

      <AnimatePresence>
        {menu && (
          <motion.div
            className="vy-mobile-menu"
            initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.24 }}
          >
            <div className="vy-mobile-inner">
              <div className="vy-mobile-head">
                <Brand onClick={() => setMenu(false)} />
                <button className="vy-close" onClick={() => setMenu(false)} aria-label="Close menu"><X size={20} /></button>
              </div>
              {navLinks.map((l) => (
                <a className="vy-mobile-link" key={l.href} href={l.href} onClick={() => setMenu(false)}>{l.label}</a>
              ))}
              <a className="vy-mobile-link" href={docsBase + "/feature-registry.md"} target="_blank" rel="noreferrer">Docs</a>
              <Link className="vy-btn vy-btn-primary" to="/studio" onClick={() => setMenu(false)}>
                Open the studio <ArrowRight size={15} />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <header className="vy-hero">
        <div className="vy-hero-glow" aria-hidden="true" />
        <div className="vy-shell">
          <div className="vy-hero-grid">
            <div>
              <Reveal>
                <span className="vy-eyebrow"><i className="vy-dot" />Video studio · local-first processing</span>
              </Reveal>
              <Reveal delay={0.06}>
                <h1 className="vy-display">
                  <span className="vy-hero-line">Creativity</span>
                  <span className="vy-hero-line">in <em>Motion.</em></span>
                </h1>
              </Reveal>
            </div>
            <Reveal delay={0.14} className="vy-hero-right">
              <p className="vy-lede">
                VYRALIS Studio turns long recordings into ranked, reviewable, social-ready clips —
                transcribed, explained and rendered on your own machine.
              </p>
              <div className="vy-hero-actions">
                <Link className="vy-btn vy-btn-primary" to="/studio">
                  Open the studio <ArrowRight size={15} />
                </Link>
                <a className="vy-link" href="#workflow">See the pipeline <ArrowUpRight size={14} /></a>
              </div>
              <div className="vy-hero-facts">
                <span className="vy-fact"><Clapperboard size={12} /> MP4 · MOV · WebM</span>
                <span className="vy-fact"><Film size={12} /> 9:16 export</span>
                <span className="vy-fact"><ShieldCheck size={12} /> No sign-up</span>
              </div>
            </Reveal>
          </div>

          <Reveal delay={0.1}>
            <div className="vy-collage">
              <figure className="vy-tile vy-tile-tall" style={{ margin: 0 }}>
                <img src="/assets/landing/shapes-hero.webp" alt="Soft 3D clay shapes in lilac, coral and pale blue" loading="eager" />
                <a className="vy-play" href="/studio" aria-label="Open the studio and review clips">
                  <Play size={20} fill="currentColor" strokeWidth={0} />
                </a>
                <span className="vy-tile-badge"><Sparkles size={10} /> The studio</span>
              </figure>

              <figure className="vy-tile vy-tile-wide" style={{ margin: 0 }}>
                <img src="/assets/landing/torus.webp" alt="Glossy pastel rings knotted together" loading="lazy" />
                <figcaption>Motion, modeled</figcaption>
              </figure>

              <figure className="vy-tile" style={{ margin: 0 }}>
                <img src="/assets/landing/ribbon.webp" alt="Coral and tangerine ribbon petals" loading="lazy" />
                <figcaption>Every frame, in rhythm</figcaption>
              </figure>

              <div className="vy-tile vy-tile-quote">
                <span className="vy-quote-mark" aria-hidden="true">“</span>
                <p>Every moment has a story. We help you find the ones worth cutting.</p>
                <small>The VYRALIS promise</small>
              </div>
            </div>
          </Reveal>
        </div>

        <div className="vy-marquee" aria-hidden="true">
          <div className="vy-marquee-track">
            {[0, 1].map((copy) => (
              <div className="vy-marquee-group" key={copy}>
                {["Import", "Transcribe", "Rank", "Review", "Edit", "Render", "Download"].map((word) => (
                  <span key={copy + word}>{word}<i>◆</i></span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </header>

      <section className="vy-section" id="workflow">
        <div className="vy-shell">
          <div className="vy-section-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />The pipeline</span></Reveal>
              <Reveal delay={0.05}>
                <h2 className="vy-h2">One honest path from<br />footage to a finished clip.</h2>
              </Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                Five steps, each one inspectable. No hidden queue, no invented score,
                no clip exported without a human decision in the middle.
              </p>
            </Reveal>
          </div>

          <Reveal>
            <div className="vy-pipeline-card">
              <div className="vy-pipeline-top">
                <span className="vy-micro"><i />Working foundation · Studio 0.2</span>
                <span className="vy-chip vy-chip-live"><Play size={9} fill="currentColor" strokeWidth={0} />Live today</span>
              </div>
              <div className="vy-steps">
                {pipeline.map((step, i) => (
                  <div className={"vy-step " + (step.status === "live" ? "vy-step-live" : "")} key={step.title}>
                    <div className="vy-step-num">STEP {String(i + 1).padStart(2, "0")}</div>
                    <div className="vy-step-icon"><step.icon size={18} /></div>
                    <h3>{step.title}</h3>
                    <p>{step.copy}</p>
                    <span className="vy-chip vy-chip-live">{step.status === "live" ? "Live" : "Next"}</span>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>

          <div className="vy-preview">
            <Reveal>
              <div className="vy-mock">
                <div className="vy-mock-bar">
                  <b>Ranked candidates</b>
                  <span>Example project</span>
                </div>
                {candidates.map((c) => (
                  <div className="vy-mock-row" key={c.title}>
                    <div className="vy-mock-thumb" />
                    <div className="vy-mock-meta">
                      <b>{c.title}</b>
                      <small>{c.time}</small>
                    </div>
                    <div className={"vy-score " + c.cls}>
                      <b>{c.score}</b>
                      <i />
                    </div>
                  </div>
                ))}
                <p className="vy-mock-note"><Sparkles size={11} /> Interface preview. Scores are transcript heuristics, not virality predictions.</p>
              </div>
            </Reveal>
            <Reveal delay={0.08}>
              <div className="vy-explain">
                <span className="vy-micro">Explainable by design</span>
                <h3>“Why did this clip rank first?”</h3>
                <p>
                  Because you can read the answer. Each candidate keeps its own score breakdown,
                  so a weak “payoff” signal is visible before you spend time editing.
                </p>
                <div className="vy-bars">
                  <div className="vy-bar-row"><span>Hook</span><i /></div>
                  <div className="vy-bar-row"><span>Context</span><i /></div>
                  <div className="vy-bar-row"><span>Density</span><i /></div>
                  <div className="vy-bar-row"><span>Payoff</span><i /></div>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="vy-section" id="capabilities" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-section-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />What is real today</span></Reveal>
              <Reveal delay={0.05}><h2 className="vy-h2">Small surface.<br />Working all the way through.</h2></Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                Every capability below is connected to a real API and storage layer. Planned
                surfaces stay labelled until they earn a test.
              </p>
            </Reveal>
          </div>
          <div className="vy-features">
            {capabilities.map((f, i) => (
              <Reveal delay={0.03 * i} key={f.title}>
                <article className="vy-feature">
                  <div className="vy-feature-top">
                    <div className="vy-feature-icon"><f.icon size={18} /></div>
                    <span className="vy-chip vy-chip-live">Live</span>
                  </div>
                  <h3 className="vy-h3">{f.title}</h3>
                  <p>{f.copy}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="vy-section" id="studio" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-surfaces">
            <Reveal>
              <div>
                <span className="vy-eyebrow"><i className="vy-dot" />Inside the studio</span>
                <h2 className="vy-h2" style={{ margin: "16px 0 18px" }}>A workspace that<br />tells you the truth.</h2>
                <p className="vy-lede" style={{ maxWidth: 400, marginBottom: 26 }}>
                  Six studios, one workspace. Each one declares whether it is live, limited or planned —
                  the app never dresses a preview up as a finished feature.
                </p>
                <Link className="vy-btn vy-btn-ghost" to="/studio">
                  Enter the workspace <ArrowUpRight size={15} />
                </Link>
              </div>
            </Reveal>
            <div>
              <div className="vy-surface-list">
                {surfaces.map((s, i) => (
                  <Reveal delay={0.03 * i} key={s.label}>
                    <div className="vy-surface">
                      <div className="vy-surface-icon"><s.icon size={16} /></div>
                      <div>
                        <b>{s.label}</b>
                        <small>{s.copy}</small>
                      </div>
                      <span className={"vy-chip " + (s.state === "Live" ? "vy-chip-live" : s.state === "Limited" ? "vy-chip-limited" : "vy-chip-next")}>{s.state}</span>
                    </div>
                  </Reveal>
                ))}
              </div>
              <Reveal delay={0.12}>
                <div className="vy-art-frame" style={{ marginTop: 18, aspectRatio: "16 / 8" }}>
                  <img src="/assets/landing/toys.webp" alt="Pastel 3D geometric shapes on a cream backdrop" loading="lazy" />
                  <div className="vy-art-card">
                    <div className="vy-art-icon"><Layers3 size={17} /></div>
                    <div>
                      <b>Foundations first</b>
                      <small>Import → transcript → ranked candidates → export. Everything else is on the roadmap, in public.</small>
                    </div>
                  </div>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      <section className="vy-section" id="roadmap" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <Reveal>
            <div className="vy-roadmap">
              <div className="vy-roadmap-inner">
                <div>
                  <span className="vy-eyebrow"><i className="vy-dot" />The road ahead</span>
                  <h2>Built in releases,<br /><em>not in promises.</em></h2>
                  <p>
                    VYRALIS is being built in the open, release by release. Editor, publishing,
                    analytics and generation are scoped — and they will stay labelled until their
                    integrations and end-to-end tests exist.
                  </p>
                  <div className="vy-roadmap-foot">
                    <a className="vy-btn vy-btn-coral vy-btn-sm" href={docsBase + "/feature-registry.md"} target="_blank" rel="noreferrer">
                      Read the feature registry <ArrowUpRight size={14} />
                    </a>
                    <small>Status vocabulary: working foundation · in progress · planned · blocked by provider.</small>
                  </div>
                </div>
                <div className="vy-road-list">
                  {roadmap.map((r) => (
                    <div className="vy-road-item" key={r.title}>
                      <r.icon size={16} />
                      <div>
                        <b>{r.title}</b>
                        <small>{r.copy}</small>
                      </div>
                      <span className="vy-chip">{r.stage}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="vy-section" id="principles" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-section-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />How we build</span></Reveal>
              <Reveal delay={0.05}><h2 className="vy-h2">Principles over<br />performance.</h2></Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                No fake metrics, no simulated publishing, no dead controls.
                If it is not real yet, the interface says so.
              </p>
            </Reveal>
          </div>
          <div className="vy-principles">
            {principles.map((p, i) => (
              <Reveal delay={0.04 * i} key={p.n}>
                <div className="vy-principle">
                  <span>{p.n}</span>
                  <b>{p.title}</b>
                  <p>{p.copy}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="vy-section" style={{ paddingTop: 0, paddingBottom: 0 }}>
        <div className="vy-shell">
          <Reveal>
            <div className="vy-cta">
              <div className="vy-cta-inner">
                <span className="vy-eyebrow"><i className="vy-dot" />Start where the story is</span>
                <h2>Your footage is already<br />full of <em>moments.</em></h2>
                <p>Bring a recording in, let the pipeline find the moments, and keep the final cut in your hands.</p>
                <div className="vy-cta-actions">
                  <Link className="vy-btn vy-btn-primary" to="/studio">
                    Open the studio <ArrowRight size={15} />
                  </Link>
                  <a className="vy-btn vy-btn-ghost" href={docsBase + "/deployment-runbook.md"} target="_blank" rel="noreferrer">
                    Run it locally <ArrowUpRight size={14} />
                  </a>
                </div>
                <span className="vy-cta-note">Local processing · FFmpeg + faster-whisper · your files stay on your disk</span>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="vy-footer">
        <div className="vy-shell">
          <div className="vy-footer-top">
            <div className="vy-footer-brand">
              <Brand />
              <p>Every moment has a story. VYRALIS Studio helps creators find, review and export
                the ones worth sharing — with the receipts attached.</p>
            </div>
            <div className="vy-footer-col">
              <b>Product</b>
              <a href="#workflow">Pipeline</a>
              <a href="#capabilities">Capabilities</a>
              <a href="#studio">Studio surfaces</a>
              <a href="#roadmap">Roadmap</a>
            </div>
            <div className="vy-footer-col">
              <b>Workspace</b>
              <Link to="/studio">Dashboard</Link>
              <Link to="/create">Clip studio</Link>
              <Link to="/projects">Projects</Link>
              <Link to="/settings">Settings</Link>
            </div>
            <div className="vy-footer-col">
              <b>Documentation</b>
              <a href={docsBase + "/feature-registry.md"} target="_blank" rel="noreferrer">Feature registry</a>
              <a href={docsBase + "/architecture.md"} target="_blank" rel="noreferrer">Architecture</a>
              <a href={docsBase + "/security-and-privacy.md"} target="_blank" rel="noreferrer">Security &amp; privacy</a>
              <a href={docsBase + "/roadmap.md"} target="_blank" rel="noreferrer">Release roadmap</a>
            </div>
          </div>
          <div className="vy-footer-bottom">
            <span>© {new Date().getFullYear()} VYRALIS Studio · Every moment has a story.</span>
            <span>
              <a href="https://github.com/leephil1907-lab/vyralis" target="_blank" rel="noreferrer">GitHub</a>
              <i style={{ opacity: 0.4 }}>·</i> STUDIO / 0.3
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
