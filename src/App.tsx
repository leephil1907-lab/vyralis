import { useEffect, useRef, useState } from "react";
import { Activity, ArrowUpRight, AudioLines, CheckCircle2, ChevronDown, Clapperboard, CloudUpload, Command, Film, FolderOpen, Gauge, HardDrive, Layers3, Play, Plus, Search, Settings2, Sparkles, WandSparkles, Zap } from "lucide-react";
import { motion } from "framer-motion";
import { api, type Health, type MediaAsset } from "./lib/api";

const nav = [
  { label: "Overview", icon: Layers3 },
  { label: "Projects", icon: FolderOpen },
  { label: "Clip studio", icon: Clapperboard },
  { label: "Render queue", icon: Activity },
];
const bytes = (n: number) => n > 1024 ** 3 ? `${(n / 1024 ** 3).toFixed(1)} GB` : n > 1024 ** 2 ? `${(n / 1024 ** 2).toFixed(1)} MB` : `${(n / 1024).toFixed(0)} KB`;

export default function App() {
  const input = useRef<HTMLInputElement>(null);
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Connect the local processing engine to begin.");
  const [query, setQuery] = useState("");

  async function refresh() {
    try {
      const [h, a] = await Promise.all([api.health(), api.assets()]);
      setHealth(h); setAssets(a); setMessage("Local engine connected.");
    } catch {
      setHealth(null);
      setMessage("Local engine offline. Start the VYRALIS backend to import and process media.");
    }
  }
  useEffect(() => { void refresh(); }, []);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true); setMessage(`Importing ${files.length} file(s)…`);
    try {
      for (const file of Array.from(files)) await api.upload(file);
      await refresh(); setMessage("Media imported successfully.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Import failed.");
    } finally { setBusy(false); if (input.current) input.current.value = ""; }
  }

  const filtered = assets.filter((a) => a.filename.toLowerCase().includes(query.toLowerCase()));
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#"><img src="/assets/vyralis-mark.svg" alt="" /><span>VYRALIS<small>STUDIO</small></span></a>
      <div className="workspace-switch"><div className="workspace-avatar">V</div><div><b>Personal studio</b><small>Local workspace</small></div><ChevronDown size={15}/></div>
      <div className="nav-label">WORKSPACE</div>
      <nav>{nav.map(({label, icon: Icon}, i) => <button className={i === 0 ? "nav-item active" : "nav-item"} key={label}><Icon size={17}/>{label}{i === 3 && <span className="nav-count">0</span>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="engine-card"><div className="engine-top"><span className={health ? "status-dot online" : "status-dot"}/><b>{health ? "Engine connected" : "Engine offline"}</b></div><p>{health ? "Local processing is ready." : "Start the local engine to enable media processing."}</p><button onClick={() => void refresh()}>Check connection <ArrowUpRight size={13}/></button></div><button className="nav-item"><Settings2 size={17}/>Settings</button><div className="profile"><div className="profile-avatar">V</div><div><b>VYRALIS Creator</b><small>Local account</small></div><ChevronDown size={15}/></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> Overview</div><div className="top-actions"><div className="local-pill"><span className="status-dot online"/> LOCAL-FIRST</div><button className="icon-button" aria-label="Search"><Search size={17}/></button><button className="avatar-mini">V</button></div></header>
      <div className="content">
        <section className="welcome"><div><div className="eyebrow"><Sparkles size={13}/> YOUR CREATIVE WORKSPACE</div><h1>Make every moment<br/><span>worth watching.</span></h1><p>Turn long-form footage into sharp, story-driven social content.</p></div><div className="welcome-mark"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><img src="/assets/vyralis-mark.svg" alt="VYRALIS"/></div></section>
        <section className="action-grid">
          <button className="import-card" onClick={() => input.current?.click()} disabled={busy}><div className="action-icon"><CloudUpload size={21}/></div><div><b>{busy ? "Importing media…" : "Import your footage"}</b><p>Bring in a video from your device</p></div><Plus size={18} className="action-plus"/><input ref={input} type="file" accept="video/*,audio/*" multiple hidden onChange={(e) => void upload(e.target.files)}/></button>
          <div className="feature-card"><div className="action-icon purple"><WandSparkles size={21}/></div><div><b>Discover highlights</b><p>AI-assisted moment discovery</p></div><span className="coming">ENGINE SETUP</span></div>
        </section>
        <section className="stats-grid">
          <div className="stat-card"><div className="stat-heading">MEDIA ASSETS <Film size={16}/></div><strong>{assets.length}</strong><small>Imported to this workspace</small></div>
          <div className="stat-card"><div className="stat-heading">PROCESSING JOBS <Gauge size={16}/></div><strong>—</strong><small>Job queue module pending</small></div>
          <div className="stat-card"><div className="stat-heading">LOCAL STORAGE <HardDrive size={16}/></div><strong>{bytes(assets.reduce((n, a) => n + a.size, 0))}</strong><small>Media indexed by this engine</small></div>
        </section>
        <section className="section-head"><div><h2>Your media</h2><p>Source footage imported into your local workspace.</p></div><div className="media-tools"><div className="search-field"><Search size={15}/><input placeholder="Search media" value={query} onChange={(e) => setQuery(e.target.value)}/></div><button className="filter-button"><Command size={14}/> Recent</button></div></section>
        {filtered.length ? <div className="media-list">{filtered.map((asset) => <div className="media-row" key={asset.id}><div className="media-thumb"><Film size={20}/></div><div className="media-name"><b>{asset.filename}</b><small>{asset.content_type || "Media"} · {bytes(asset.size)}</small></div><span className="asset-status"><CheckCircle2 size={14}/> Imported</span><button className="icon-button"><ArrowUpRight size={16}/></button></div>)}</div> : <div className="empty-state"><div className="empty-art"><div className="empty-ring"/><Film size={28}/><Play size={12} className="play-overlay"/></div><h3>{query ? "No matching media" : "Your next great clip starts here."}</h3><p>{query ? "Try another search term." : "Import a recording to create your first VYRALIS project. Your source media stays in your local workspace."}</p><button className="primary-button" onClick={() => input.current?.click()}><Plus size={16}/> Import video</button></div>}
        <footer className="footer"><span>VYRALIS STUDIO <span className="footer-muted">· Every moment has a story.</span></span><span className="engine-message"><AudioLines size={14}/>{message}</span><span>v0.1.0 FOUNDATION</span></footer>
      </div>
    </main>
  </div>;
}