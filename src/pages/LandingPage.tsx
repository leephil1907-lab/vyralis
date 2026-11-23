import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight, ArrowUpRight, AudioLines, ChartNoAxesCombined, Check,
  ChevronDown, Clapperboard, Compass, Film, Layers3, Link2, ListChecks,
  Menu, Network, Palette, Play, Plus, Radio, RotateCcw, Scissors,
  ShieldCheck, Sparkles, Upload, X,
} from "lucide-react";
import "../landing.css";

const navLinks = [
  { label: "Pipeline", href: "#workflow" },
  { label: "Capabilities", href: "#capabilities" },
  { label: "Studio", href: "#studio" },
  { label: "Pricing", href: "#pricing" },
];

const resourceLinks = [
  { label: "Documentation", copy: "Every document, in the app", to: "/docs" },
  { label: "Feature registry", copy: "What is live, limited or planned", to: "/docs/feature-registry" },
  { label: "Deployment runbook", copy: "Docker and the Render setup", to: "/docs/deployment-runbook" },
  { label: "Connecting accounts", copy: "OAuth apps and redirect URIs", to: "/docs/oauth-setup" },
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

const ledger = [
  { term: "Runs on", detail: "Your machine or your own server", note: "FFmpeg, FFprobe and faster-whisper do the work locally" },
  { term: "Exports", detail: "9:16 · 1:1 · 16:9", note: "H.264/AAC with burned captions, hook and reframing" },
  { term: "Sidecars", detail: "SRT · VTT · ASS", note: "Word-timed, in clean, karaoke and impact styles" },
  { term: "Quality report", detail: "Measured, not claimed", note: "Duration, dimensions, codecs, black and frozen frames, loudness" },
  { term: "Accounts", detail: "YouTube · TikTok · Instagram · X", note: "Real OAuth with your own provider apps; nothing simulated" },
  { term: "Data", detail: "Stays on the host", note: "SQLite on disk, tokens encrypted at rest, no third-party upload" },
];

const faqs = [
  {
    q: "Does my footage get uploaded anywhere?",
    a: "No. Media is written to the host running the studio. Imports, transcription, ranking and rendering all happen there, and the only outbound requests are the ones you start: resolving a source link, or an OAuth call to a platform you connected.",
  },
  {
    q: "What does the score actually mean?",
    a: "It is a transcript heuristic with a visible breakdown: hook strength, context completeness, speech density and payoff signal. It is a way to order candidates for review, not a virality prediction, and the interface says so wherever the number appears.",
  },
  {
    q: "Can it post to TikTok or YouTube for me?",
    a: "Not yet. Account connections are real — OAuth, encrypted tokens, live account metrics — but publishing needs approved platform apps and a posting adapter, so the studio stops at validated packaging and an approved delivery package. It will not pretend a post went out.",
  },
  {
    q: "Which sources can I import?",
    a: "Local files (MP4, MOV, MKV, WebM, AVI) and eligible public YouTube, Twitch and Kick links through yt-dlp, with a host allowlist and a rights confirmation. Region locks, age gates and provider restrictions can still block an import, and the job reports why.",
  },
  {
    q: "Is there a subscription?",
    a: "No. The studio is self-hosted and there is no billing layer anywhere in the code. If a hosted version ever ships, it will be priced and stated here first — you will not find a fake checkout on this site.",
  },
  {
    q: "Who owns the clips I make?",
    a: "You do — subject to your rights in the source footage. The studio asks you to confirm you own or have permission to clip the material, and it does not strip attribution or quietly re-upload anything.",
  },
];

const SAMPLE = {
  clips: [
    { start: 6, end: 34, score: 86, label: "Hook" },
    { start: 41, end: 62, score: 74, label: "Story" },
    { start: 68, end: 90, score: 61, label: "Payoff" },
  ],
  words: [
    "So we", "shipped", "the", "first", "version", "on", "a", "Friday,", "and",
    "nobody", "expected", "what", "happened", "next.",
  ],
};

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
      <span>VYRALIS<small>Studio</small></span>
    </a>
  );
}

/* ---------------------------------------------------------------- signature
   The scrubber is the one memorable interaction on the page. It is a real
   timeline over a sample project: dragging or using the arrow keys moves the
   playhead, and the phone preview follows with the spoken words highlighted.
   The sample label is deliberate — these numbers are a demo, not a promise.
   -------------------------------------------------------------------------- */
function TimelineScrubber() {
  const [position, setPosition] = useState(43);
  const [dragging, setDragging] = useState(false);
  const track = useRef<HTMLDivElement>(null);

  const at = useCallback((clientX: number) => {
    const box = track.current?.getBoundingClientRect();
    if (!box) return;
    const pct = ((clientX - box.left) / box.width) * 100;
    setPosition(Math.min(99, Math.max(1, pct)));
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const move = (event: PointerEvent) => at(event.clientX);
    const stop = () => setDragging(false);
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
    return () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
    };
  }, [dragging, at]);

  const activeIndex = Math.min(
    SAMPLE.words.length - 1,
    Math.floor((position / 100) * SAMPLE.words.length),
  );
  const clip = SAMPLE.clips.find((c) => position >= c.start && position <= c.end) ?? SAMPLE.clips[0];
  const stamp = (pct: number) => {
    const total = 108;
    const seconds = Math.round((pct / 100) * total);
    return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  };

  return (
    <div className="vy-scrub">
      <div className="vy-timeline">
        <div className="vy-tl-top">
          <b>Sample project · “Launch week, raw”</b>
          <span>{stamp(position)} / 01:48</span>
        </div>
        <div
          className="vy-tl-track"
          ref={track}
          role="slider"
          tabIndex={0}
          aria-label="Sample project timeline"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(position)}
          aria-valuetext={`${stamp(position)} — caption: ${SAMPLE.words[activeIndex]}`}
          onPointerDown={(event) => { setDragging(true); at(event.clientX); }}
          onKeyDown={(event) => {
            const step = event.shiftKey ? 10 : 3;
            if (event.key === "ArrowRight" || event.key === "ArrowUp") {
              event.preventDefault(); setPosition((p) => Math.min(99, p + step));
            } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
              event.preventDefault(); setPosition((p) => Math.max(1, p - step));
            } else if (event.key === "Home") {
              event.preventDefault(); setPosition(1);
            } else if (event.key === "End") {
              event.preventDefault(); setPosition(99);
            }
          }}
        >
          {SAMPLE.clips.map((c) => (
            <div
              key={c.label}
              className="vy-tl-clip"
              style={{ left: `${c.start}%`, width: `${c.end - c.start}%` }}
            >
              <span>{c.label}</span>
              <div className="vy-tl-clip-wave" />
            </div>
          ))}
          <div className="vy-tl-playhead" style={{ left: `${position}%` }} />
        </div>
        <div className="vy-tl-scale">
          {[0, 25, 50, 75, 100].map((tick) => <span key={tick}>{stamp(tick)}</span>)}
        </div>
        <div className="vy-tl-words" aria-hidden="true">
          {SAMPLE.words.map((word, index) => (
            <span key={word + index} className={"vy-tl-word" + (index === activeIndex ? " on" : "")}>{word}</span>
          ))}
        </div>
        <p className="vy-tl-hint">
          Drag the playhead, or focus it and use the arrow keys. The caption follows the spoken
          word, exactly as it does in the studio.
        </p>
      </div>

      <div>
        <div className="vy-phone">
          <div className="vy-phone-screen">
            <div className="vy-phone-frame" aria-hidden="true" />
            <span className="vy-phone-hook">Nobody expected this</span>
            <span className="vy-phone-caption">{SAMPLE.words.slice(Math.max(0, activeIndex - 2), activeIndex + 2).join(" ")}</span>
            <div className="vy-phone-meta">
              <span className="vy-phone-chip">9:16</span>
              <span className="vy-phone-chip">Karaoke</span>
              <span className="vy-phone-chip">Score {clip.score}</span>
            </div>
          </div>
        </div>
        <p className="vy-scrub-note">
          <Sparkles size={13} style={{ marginTop: 2, flex: "none" }} />
          Sample timeline from a demo project, not a claim about your footage.
        </p>
      </div>
    </div>
  );
}

function ProductFrame() {
  return (
    <div className="vy-product" aria-hidden="true">
      <div className="vy-product-bar">
        <i /><i /><i />
        <span>Interface preview</span>
      </div>
      <div className="vy-product-body">
        {candidates.map((c) => (
          <div className="vy-prod-row" key={c.title}>
            <div className="vy-prod-thumb" />
            <div className="vy-prod-meta">
              <b>{c.title}</b>
              <small>{c.time}</small>
            </div>
            <span className="vy-prod-score">{c.score}</span>
          </div>
        ))}
        <div className="vy-prod-export">
          <Check size={12} /> 9:16 · captions burned in · QC <em>pass</em>
        </div>
        <p className="vy-prod-note"><ShieldCheck size={11} /> Rendered locally · quality report attached</p>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const [menu, setMenu] = useState(false);
  const [resources, setResources] = useState(false);
  const [stuck, setStuck] = useState(false);
  const [link, setLink] = useState("");
  const [linkError, setLinkError] = useState("");
  const navigate = useNavigate();
  const resourcesRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    document.body.style.overflow = menu ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menu]);

  useEffect(() => {
    // The studio shell paints html/body near-black. While the public site is
    // mounted, the document itself has to be cream or overscroll shows dark.
    const root = document.documentElement;
    const previous = {
      html: root.style.background,
      body: document.body.style.background,
      scheme: root.style.colorScheme,
    };
    root.style.background = "#FAF5E9";
    document.body.style.background = "#FAF5E9";
    root.style.colorScheme = "light";
    return () => {
      root.style.background = previous.html;
      document.body.style.background = previous.body;
      root.style.colorScheme = previous.scheme;
    };
  }, []);

  useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 90);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!resources) return;
    const click = (event: MouseEvent) => {
      if (!resourcesRef.current?.contains(event.target as Node)) setResources(false);
    };
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") setResources(false); };
    document.addEventListener("mousedown", click);
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("mousedown", click);
      document.removeEventListener("keydown", key);
    };
  }, [resources]);

  function startFromLink(event: React.FormEvent) {
    event.preventDefault();
    const value = link.trim();
    if (!value) { setLinkError("Paste a link first, or upload a file in the studio."); return; }
    try {
      const parsed = new URL(value);
      if (!/^https?:$/.test(parsed.protocol)) throw new Error("bad protocol");
    } catch {
      setLinkError("That doesn’t look like a full URL — include https://");
      return;
    }
    navigate(`/create?url=${encodeURIComponent(value)}&focus=url`);
  }

  const year = new Date().getFullYear();

  return (
    <div className="vy-site" id="top">
      <div className="vy-announce">
        <span>
          <i className="vy-dot" /> <b>Studio 0.3</b> — the local clipping pipeline is live: import, transcribe, rank, review, render, package.
          <Link to="/studio">Open the studio <ArrowUpRight size={11} style={{ display: "inline", verticalAlign: "-1px" }} /></Link>
        </span>
      </div>

      <div className={"vy-nav-wrap" + (stuck ? " is-stuck" : "")}>
        <div className="vy-shell">
          <nav className="vy-nav" aria-label="Primary">
            <Brand />
            <ul className="vy-nav-links">
              {navLinks.map((l) => <li key={l.href}><a href={l.href}>{l.label}</a></li>)}
              <li className="vy-has-menu" ref={resourcesRef}>
                <button
                  type="button"
                  aria-expanded={resources}
                  aria-haspopup="true"
                  onClick={() => setResources((v) => !v)}
                >
                  Resources <ChevronDown size={13} />
                </button>
                <AnimatePresence>
                  {resources && (
                    <motion.div
                      className="vy-dropdown"
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.16 }}
                    >
                      {resourceLinks.map((item) => (
                        <Link key={item.to} to={item.to} onClick={() => setResources(false)}>
                          <b>{item.label}</b>
                          <small>{item.copy}</small>
                        </Link>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
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
              <div className="vy-mobile-sub">Resources</div>
              {resourceLinks.map((item) => (
                <Link className="vy-mobile-link" key={item.to} to={item.to} onClick={() => setMenu(false)}>
                  {item.label}
                </Link>
              ))}
              <Link className="vy-btn vy-btn-primary" to="/studio" onClick={() => setMenu(false)}>
                Open the studio <ArrowRight size={15} />
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <header className="vy-hero">
        <div className="vy-shell">
          <div className="vy-hero-grid">
            <div className="vy-hero-copy">
              <Reveal>
                <span className="vy-eyebrow"><i className="vy-dot" />Video studio · local-first processing</span>
              </Reveal>
              <Reveal delay={0.05}>
                <h1 className="vy-display">
                  <span className="vy-hero-line">Creativity</span>
                  <span className="vy-hero-line">in <em>Motion.</em></span>
                </h1>
              </Reveal>
              <Reveal delay={0.1}>
                <p className="vy-lede">
                  Turn long recordings into ranked, reviewable, social-ready clips — transcribed,
                  explained and rendered on your own machine.
                </p>
              </Reveal>
              <Reveal delay={0.14}>
                <form className="vy-quickstart" onSubmit={startFromLink}>
                  <Link2 size={15} />
                  <input
                    value={link}
                    onChange={(e) => { setLink(e.target.value); setLinkError(""); }}
                    placeholder="Paste a YouTube, Twitch or Kick link"
                    aria-label="Paste a video link"
                    inputMode="url"
                  />
                  <button className="vy-btn vy-btn-primary vy-btn-sm" type="submit">
                    Start clipping <ArrowRight size={13} />
                  </button>
                </form>
                {linkError && <p className="vy-quickstart-error">{linkError}</p>}
              </Reveal>
              <Reveal delay={0.18}>
                <div className="vy-hero-actions">
                  <Link className="vy-btn vy-btn-ghost" to="/studio">
                    Open the studio <ArrowUpRight size={15} />
                  </Link>
                  <a className="vy-link" href="#signature">See the workspace <ArrowUpRight size={14} /></a>
                </div>
              </Reveal>
              <Reveal delay={0.22}>
                <div className="vy-hero-facts">
                  <span className="vy-fact"><Clapperboard size={12} /> MP4 · MOV · WebM</span>
                  <span className="vy-fact"><Film size={12} /> 9:16 export</span>
                  <span className="vy-fact"><ShieldCheck size={12} /> No sign-up</span>
                </div>
              </Reveal>
            </div>

            <Reveal delay={0.12} className="vy-hero-media">
              <ProductFrame />
            </Reveal>
          </div>

          <Reveal delay={0.08}>
            <div className="vy-shelf">
              <figure className="vy-tile" style={{ margin: 0 }}>
                <img src="/assets/landing/shapes-hero.webp" alt="Soft 3D clay shapes in lilac, coral and pale blue" loading="eager" />
              </figure>
              <figure className="vy-tile" style={{ margin: 0 }}>
                <img src="/assets/landing/torus.webp" alt="Glossy pastel rings knotted together" loading="lazy" />
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

      <section className="vy-sheet" id="signature">
        <div className="vy-shell">
          <div className="vy-sheet-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />The workspace</span></Reveal>
              <Reveal delay={0.05}>
                <h2 className="vy-h2">Drag the timeline.<br />Watch the caption land.</h2>
              </Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                Word timings are not decoration here — they drive the cut, the caption and the
                export. Scrub this sample and you are looking at the same surface the studio gives you.
              </p>
            </Reveal>
          </div>
          <Reveal delay={0.08}><TimelineScrubber /></Reveal>
        </div>
      </section>

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
                <span className="vy-micro"><i />Working foundation · Studio 0.3</span>
                <span className="vy-chip vy-chip-live"><Play size={9} fill="currentColor" strokeWidth={0} />Live today</span>
              </div>
              <div className="vy-steps">
                {pipeline.map((step, i) => (
                  <div className="vy-step" key={step.title}>
                    <div className="vy-step-num">STEP {String(i + 1).padStart(2, "0")}</div>
                    <div className="vy-step-icon"><step.icon size={17} /></div>
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
                    <div className="vy-feature-icon"><f.icon size={17} /></div>
                    <span className="vy-chip vy-chip-live">Live</span>
                  </div>
                  <h3>{f.title}</h3>
                  <p>{f.copy}</p>
                </article>
              </Reveal>
            ))}
          </div>

          <Reveal>
            <dl className="vy-ledger" style={{ marginTop: 34 }}>
              {ledger.map((row) => (
                <div className="vy-ledger-row" key={row.term}>
                  <dt>{row.term}</dt>
                  <dd>{row.detail}<small>{row.note}</small></dd>
                </div>
              ))}
            </dl>
          </Reveal>
        </div>
      </section>

      <section className="vy-section" id="studio" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-surfaces">
            <Reveal>
              <div>
                <span className="vy-eyebrow"><i className="vy-dot" />Inside the studio</span>
                <h2 className="vy-h2">A workspace that<br />tells you the truth.</h2>
                <p className="vy-lede">
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
                      <div className="vy-surface-icon"><s.icon size={15} /></div>
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
                <div className="vy-art-frame" style={{ marginTop: 16, aspectRatio: "16 / 7" }}>
                  <img src="/assets/landing/toys.webp" alt="Pastel 3D geometric shapes on a cream backdrop" loading="lazy" />
                  <div className="vy-art-card">
                    <div className="vy-art-icon"><Layers3 size={15} /></div>
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

      <section className="vy-section" id="pricing" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-section-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />What it costs</span></Reveal>
              <Reveal delay={0.05}><h2 className="vy-h2">Self-hosted, and<br />stated plainly.</h2></Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                There is no billing layer in this codebase. The studio runs on hardware you
                already have, and the source is in the open.
              </p>
            </Reveal>
          </div>
          <div className="vy-plans">
            <Reveal>
              <div className="vy-plan featured">
                <div className="vy-plan-head">
                  <h3>Self-hosted</h3>
                  <span className="vy-chip vy-chip-live">Available now</span>
                </div>
                <div className="vy-plan-price">Free<small>your hardware</small></div>
                <ul>
                  {[
                    "Unlimited imports, clips and renders",
                    "Word-timed captions plus SRT, VTT and ASS sidecars",
                    "Auto-reframing and measured quality reports",
                    "Real OAuth connections with your own provider apps",
                    "Documentation, runbook and source in the repo",
                  ].map((line) => <li key={line}><Check size={14} />{line}</li>)}
                </ul>
                <Link className="vy-btn vy-btn-coral" to="/docs/deployment-runbook">
                  Read the deployment runbook <ArrowUpRight size={14} />
                </Link>
              </div>
            </Reveal>
            <Reveal delay={0.06}>
              <div className="vy-plan">
                <div className="vy-plan-head">
                  <h3>Hosted</h3>
                  <span className="vy-chip vy-chip-next">Not offered</span>
                </div>
                <div className="vy-plan-price">—<small>no fake checkout</small></div>
                <ul>
                  {[
                    "No plan, no trial and no card form on this site",
                    "A managed version needs per-tenant isolation first",
                    "When it exists, pricing will be published here before sign-up",
                  ].map((line) => <li key={line}><Plus size={14} />{line}</li>)}
                </ul>
                <Link className="vy-btn vy-btn-ghost" to="/docs/roadmap">
                  See the release roadmap <ArrowRight size={14} />
                </Link>
              </div>
              <p className="vy-plan-note">
                Costs you control: your electricity, disk and any provider API quota. The studio
                makes no outbound calls you did not start.
              </p>
            </Reveal>
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
                    <Link className="vy-btn vy-btn-coral vy-btn-sm" to="/docs/feature-registry">
                      Read the feature registry <ArrowRight size={14} />
                    </Link>
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

      <section className="vy-section" id="faq" style={{ paddingTop: 0 }}>
        <div className="vy-shell">
          <div className="vy-section-head">
            <div>
              <Reveal><span className="vy-eyebrow"><i className="vy-dot" />Straight answers</span></Reveal>
              <Reveal delay={0.05}><h2 className="vy-h2">Questions people<br />actually ask.</h2></Reveal>
            </div>
            <Reveal delay={0.1}>
              <p className="vy-lede">
                If an answer here ever stops being true, it gets changed in the same commit
                as the code.
              </p>
            </Reveal>
          </div>
          <div className="vy-faq">
            {faqs.map((item, i) => (
              <Reveal delay={0.02 * i} key={item.q}>
                <details className="vy-faq-item" open={i === 0}>
                  <summary>
                    <h3>{item.q}</h3>
                    <span aria-hidden="true"><Plus size={14} /></span>
                  </summary>
                  <p>{item.a}</p>
                </details>
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
                <span className="vy-eyebrow"><i className="vy-dot" />Start where you are</span>
                <h2>Your footage is already<br />full of <em>moments.</em></h2>
                <p>Bring a recording in, let the pipeline find the moments, and keep the final cut in your hands.</p>
                <div className="vy-cta-actions">
                  <Link className="vy-btn vy-btn-primary" to="/studio">
                    Open the studio <ArrowRight size={15} />
                  </Link>
                  <Link className="vy-btn vy-btn-ghost" to="/docs/deployment-runbook">
                    Run it locally <ArrowRight size={14} />
                  </Link>
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
              <a href="#pricing">Pricing</a>
              <a href="#faq">FAQ</a>
            </div>
            <div className="vy-footer-col">
              <b>Workspace</b>
              <Link to="/studio">Dashboard</Link>
              <Link to="/create">Clip studio</Link>
              <Link to="/projects">Projects</Link>
              <Link to="/connections">Connections</Link>
            </div>
            <div className="vy-footer-col">
              <b>Documentation</b>
              <Link to="/docs">All documentation</Link>
              <Link to="/docs/feature-registry">Feature registry</Link>
              <Link to="/docs/security-and-privacy">Security &amp; privacy</Link>
              <Link to="/docs/deployment-runbook">Deployment runbook</Link>
            </div>
          </div>
          <div className="vy-footer-bottom">
            <span>© {year} VYRALIS Studio · Every moment has a story.</span>
            <span className="vy-footer-status"><i />Local engine · Studio 0.3</span>
            <span>
              <a href="https://github.com/leephil1907-lab/vyralis" target="_blank" rel="noreferrer">GitHub</a>
              <i style={{ opacity: 0.4, padding: "0 6px" }}>·</i>
              <a href="#top">Back to top</a>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
