import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  Activity, ArrowDownToLine, ArrowUpRight, AudioLines, BarChart3, Bell, CalendarDays,
  Check, ChevronDown, CircleHelp, Clapperboard, CloudUpload, Command, Compass, Film,
  FolderOpen, Gauge, HardDrive, Layers3, Link2, ListVideo, Menu, MessageSquareText,
  MoreHorizontal, Play, Plus, Search, Settings2, ShieldCheck, Sparkles, Subtitles,
  WandSparkles, X, Youtube, Instagram, Radio, Clock3, SlidersHorizontal, Zap, Palette,
  Scissors, Upload, ExternalLink, Video, Captions, ChartNoAxesCombined
} from "lucide-react";
import { api, type Health, type MediaAsset } from "./lib/api";

const navGroups = [
  { label: "WORKSPACE", items: [
    { to: "/", label: "Dashboard", icon: Layers3 },
    { to: "/projects", label: "Projects", icon: FolderOpen },
    { to: "/create", label: "Create clips", icon: Clapperboard },
    { to: "/editor", label: "Video editor", icon: Scissors },
  ]},
  { label: "GROW & PUBLISH", items: [
    { to: "/publishing", label: "Publishing", icon: Radio },
    { to: "/calendar", label: "Content calendar", icon: CalendarDays },
    { to: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
    { to: "/growth", label: "Growth intelligence", icon: Compass },
  ]},
  { label: "YOUR BRAND", items: [
    { to: "/brand", label: "Brand kit", icon: Palette },
    { to: "/settings", label: "Settings", icon: Settings2 },
  ]},
];
const titles: Record<string,string> = {
  "/":"Dashboard","/projects":"Projects","/create":"Create clips","/editor":"Video editor",
  "/publishing":"Publishing","/calendar":"Content calendar","/analytics":"Analytics",
  "/growth":"Growth intelligence","/brand":"Brand kit","/settings":"Settings"
};
const bytes = (n:number) => n > 1024**3 ? (n/1024**3).toFixed(1)+" GB" : n > 1024**2 ? (n/1024**2).toFixed(1)+" MB" : (n/1024).toFixed(0)+" KB";
const pageMotion = { initial:{opacity:0,y:12,filter:"blur(5px)"}, animate:{opacity:1,y:0,filter:"blur(0px)"}, exit:{opacity:0,y:-8,filter:"blur(4px)"} };

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [assets,setAssets] = useState<MediaAsset[]>([]);
  const [health,setHealth] = useState<Health|null>(null);
  const [busy,setBusy] = useState(false);
  const [notice,setNotice] = useState("");
  const [query,setQuery] = useState("");
  const [sourceUrl,setSourceUrl] = useState("");
  const [mobileNav,setMobileNav] = useState(false);

  async function refresh() {
    try { const [h,a] = await Promise.all([api.health(),api.assets()]); setHealth(h); setAssets(a); }
    catch { setHealth(null); }
  }
  useEffect(()=>{ void refresh(); },[]);
  async function upload(files:FileList|null) {
    if(!files?.length) return;
    setBusy(true); setNotice("Importing media to this workspace…");
    try { for(const file of Array.from(files)) await api.upload(file); await refresh(); setNotice("Media imported."); }
    catch(e){ setNotice(e instanceof Error?e.message:"Import failed."); }
    finally { setBusy(false); if(input.current) input.current.value=""; }
  }
  const filtered = useMemo(()=>assets.filter(a=>a.filename.toLowerCase().includes(query.toLowerCase())),[assets,query]);
  const title = titles[location.pathname] || "Dashboard";
  const totalBytes = assets.reduce((n,a)=>n+a.size,0);

  function beginLinkFlow() {
    const value=sourceUrl.trim();
    if(!value){setNotice("Paste a YouTube, Twitch or Kick video link first.");return;}
    let url:URL;
    try { url=new URL(value); } catch { setNotice("Enter a valid video URL."); return; }
    const host=url.hostname.toLowerCase().replace(/^www\./,"");
    if(!["youtube.com","youtu.be","m.youtube.com","twitch.tv","clips.twitch.tv","kick.com"].includes(host)){
      setNotice("Supported sources: YouTube, Twitch and Kick links."); return;
    }
    setNotice("Link accepted by the interface. Source resolution and clipping are not connected to the backend yet, so no job has been created.");
  }

  const page = (node:React.ReactNode) => <motion.div className="page-content" key={location.pathname} {...pageMotion} transition={{duration:.24,ease:[.22,1,.36,1]}}>{node}</motion.div>;
  const PageHeader = ({eyebrow,heading,description,action}:{eyebrow:string;heading:string;description:string;action?:React.ReactNode}) => <div className="page-heading"><div><div className="eyebrow"><Sparkles size={13}/>{eyebrow}</div><h1>{heading}</h1><p>{description}</p></div>{action&&<div className="heading-action">{action}</div>}</div>;
  const Glass = ({children,className=""}:{children:React.ReactNode;className?:string}) => <section className={"glass "+className}>{children}</section>;
  const Empty = ({icon:Icon=Film,title:heading,copy,action}:{icon?:any;title:string;copy:string;action?:React.ReactNode}) => <div className="empty-panel"><div className="empty-icon"><Icon size={23}/></div><h3>{heading}</h3><p>{copy}</p>{action}</div>;

  function Dashboard(){
    return page(<>
      <PageHeader eyebrow="YOUR CREATOR WORKSPACE" heading={<>Make every moment <em>worth watching.</em></>} description="One place to turn long-form footage into clips, publish everywhere and learn what works." action={<button className="button-primary" onClick={()=>navigate("/create")}><Plus size={16}/> Create clips</button>}/>
      <div className="dashboard-grid">
        <Glass className="welcome-card"><div className="welcome-copy"><span className="micro-label">START WITH A SOURCE</span><h2>Your next standout clip<br/>starts with a moment.</h2><p>Drop in a video link or upload footage. VYRALIS is designed to take it from source to social-ready content.</p><button className="button-primary" onClick={()=>navigate("/create")}>Open clip studio <ArrowUpRight size={15}/></button></div><div className="visual-stack"><div className="visual-orbit orbit-a"/><div className="visual-orbit orbit-b"/><div className="visual-core"><img src="/assets/vyralis-mark.svg" alt="VYRALIS"/></div><span className="float-chip chip-one"><AudioLines size={14}/> Moments</span><span className="float-chip chip-two"><Captions size={14}/> Captions</span></div></Glass>
        <Glass className="quick-card"><div className="card-top"><div><span className="micro-label">QUICK CREATE</span><h3>Bring a video in</h3></div><Zap size={18}/></div><button className="quick-option" onClick={()=>navigate("/create")}><span className="quick-icon"><Link2 size={18}/></span><span><b>Paste a video link</b><small>YouTube · Twitch · Kick</small></span><ArrowUpRight size={16}/></button><button className="quick-option" onClick={()=>input.current?.click()}><span className="quick-icon"><Upload size={18}/></span><span><b>Upload from device</b><small>MP4, MOV, WebM and more</small></span><ArrowUpRight size={16}/></button><input ref={input} type="file" accept="video/*,audio/*" multiple hidden onChange={e=>void upload(e.target.files)}/></Glass>
      </div>
      <div className="section-title"><div><span className="micro-label">AT A GLANCE</span><h2>Your workspace</h2></div><button className="text-button" onClick={()=>navigate("/projects")}>View projects <ArrowUpRight size={14}/></button></div>
      <div className="metric-grid">
        <Glass className="metric-card"><span>MEDIA ASSETS <Film size={15}/></span><strong>{assets.length}</strong><small>Files imported to this workspace</small></Glass>
        <Glass className="metric-card"><span>STORAGE USED <HardDrive size={15}/></span><strong>{bytes(totalBytes)}</strong><small>Indexed local media</small></Glass>
        <Glass className="metric-card"><span>PROCESSING ENGINE <Activity size={15}/></span><strong className="metric-status">{health?"Connected":"Offline"}</strong><small>{health?"Local API responding":"Start the backend to import media"}</small></Glass>
      </div>
      <div className="section-title"><div><span className="micro-label">RECENT WORK</span><h2>Recently imported</h2></div><button className="text-button" onClick={()=>navigate("/projects")}>All media <ArrowUpRight size={14}/></button></div>
      {assets.length ? <Glass className="asset-list">{assets.slice(0,5).map(a=><div className="asset-row" key={a.id}><div className="asset-art"><Film size={18}/></div><div className="asset-meta"><b>{a.filename}</b><small>{a.content_type||"Media"} · {bytes(a.size)}</small></div><span className="status-tag"><Check size={12}/> Imported</span></div>)}</Glass>:<Empty title="Your projects will show up here" copy="Import a video or paste a source link to start building your first project." action={<button className="button-secondary" onClick={()=>navigate("/create")}><Plus size={15}/> Start a project</button>}/>}
    </>);
  }

  function Create(){
    return page(<><PageHeader eyebrow="CLIP STUDIO" heading={<>Find the moments that <em>move people.</em></>} description="Start with a source. VYRALIS will be built around highlight discovery, vertical clips, captions and publishing."/>
      <Glass className="create-panel"><div className="source-tabs"><span className="source-tab active"><Link2 size={15}/> Paste video link</span><button className="source-tab" onClick={()=>input.current?.click()}><Upload size={15}/> Upload video</button></div><div className="source-input-wrap"><Link2 size={18}/><input value={sourceUrl} onChange={e=>setSourceUrl(e.target.value)} onKeyDown={e=>e.key==="Enter"&&beginLinkFlow()} placeholder="Paste a YouTube, Twitch or Kick video URL"/><button className="button-primary" onClick={beginLinkFlow}>Continue <ArrowUpRight size={15}/></button></div><div className="source-support"><span><Youtube size={14}/> YouTube</span><span><Radio size={14}/> Twitch</span><span><Zap size={14}/> Kick</span><span className="source-note">Video link or local upload</span></div><input ref={input} type="file" accept="video/*" hidden onChange={e=>void upload(e.target.files)}/>{notice&&<div className="notice"><ShieldCheck size={15}/>{notice}</div>}</Glass>
      <div className="section-title"><div><span className="micro-label">YOUR CLIPPING WORKFLOW</span><h2>From source to shareable</h2></div></div><div className="workflow-grid">{[{n:"01",icon:Compass,title:"Discover highlights",desc:"Audio energy, transcript context, scene changes and standout moments."},{n:"02",icon:Scissors,title:"Shape every clip",desc:"Trim, split, reframe and refine your strongest moments."},{n:"03",icon:Captions,title:"Style your story",desc:"Word-timed captions, hooks, titles and reusable brand presets."},{n:"04",icon:Radio,title:"Publish & learn",desc:"Prepare platform versions, schedule posts and review performance."}].map(item=><Glass className="workflow-card" key={item.n}><span className="workflow-number">{item.n}</span><item.icon size={20}/><h3>{item.title}</h3><p>{item.desc}</p></Glass>)}</div>
      <div className="integration-note"><Sparkles size={16}/><div><b>Processing integrations are being connected</b><p>The product architecture is mapped for FFmpeg, WhisperX/faster-whisper, PySceneDetect, MediaPipe/YOLO and NeonClipping-style source adapters. This screen does not claim those engines are running yet.</p></div></div>
    </>);
  }

  function Projects(){
    return page(<><PageHeader eyebrow="PROJECT LIBRARY" heading={<>Everything you’re <em>working on.</em></>} description="Your imported source footage and project assets, together in one workspace." action={<button className="button-primary" onClick={()=>navigate("/create")}><Plus size={15}/> New project</button>}/><div className="toolbar"><div className="search-box"><Search size={15}/><input placeholder="Search your media" value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="quiet-count">{filtered.length} assets</span></div>{filtered.length?<Glass className="asset-list">{filtered.map(a=><div className="asset-row" key={a.id}><div className="asset-art"><Film size={18}/></div><div className="asset-meta"><b>{a.filename}</b><small>{a.content_type||"Media"} · {bytes(a.size)} · {new Date(a.created_at).toLocaleDateString()}</small></div><span className="status-tag"><Check size={12}/> Imported</span><MoreHorizontal size={18}/></div>)}</Glass>:<Empty icon={FolderOpen} title={query?"No matching assets":"No projects yet"} copy={query?"Try another search term.":"Start with a YouTube, Twitch or Kick link, or upload a local video."} action={<button className="button-primary" onClick={()=>navigate("/create")}><Plus size={15}/> Create project</button>}/>}</>);
  }

  function Editor(){return page(<><PageHeader eyebrow="VIDEO EDITOR" heading={<>Make the cut <em>your own.</em></>} description="A focused editing workspace for timing, framing, captions and finishing."/><Glass className="editor-shell"><div className="editor-toolbar"><span><Scissors size={15}/> Untitled sequence</span><span className="editor-pill">No clip selected</span><button className="button-secondary" onClick={()=>navigate("/create")}>Choose source</button></div><Empty icon={Video} title="Your editing canvas is ready" copy="Create or import a clip first. The timeline editor, transcript-linked trimming, split/merge and smart reframing are not connected yet."/></Glass><div className="feature-row">{[{icon:ListVideo,title:"Transcript timeline",copy:"Navigate by spoken words and timestamps."},{icon:Subtitles,title:"Caption styling",copy:"Word timing, emphasis and language variants."},{icon:Compass,title:"Smart framing",copy:"Face and speaker-aware vertical composition."}].map(x=><Glass className="mini-feature" key={x.title}><x.icon size={19}/><b>{x.title}</b><small>{x.copy}</small></Glass>)}</div></>);}

  function Publishing(){return page(<><PageHeader eyebrow="PUBLISHING STUDIO" heading={<>One clip. Every <em>channel.</em></>} description="Prepare platform-ready versions and manage your connected destinations."/><div className="platform-grid">{[{name:"YouTube",detail:"Shorts and video publishing",icon:Youtube},{name:"Instagram",detail:"Reels and feed publishing",icon:Instagram},{name:"TikTok",detail:"Content Posting API",icon:Video},{name:"Facebook",detail:"Pages and Reels",icon:MessageSquareText}].map(p=><Glass className="platform-card" key={p.name}><div className="platform-icon"><p.icon size={22}/></div><div><b>{p.name}</b><small>{p.detail}</small></div><span className="status-tag muted">Not connected</span><button className="button-secondary" onClick={()=>setNotice(p.name+" authorization is not configured yet. No account has been connected.")}>Connect</button></Glass>)}</div>{notice&&<div className="notice"><ShieldCheck size={15}/>{notice}</div>}<div className="integration-note"><ShieldCheck size={16}/><div><b>Official authorization only</b><p>Publishing will use platform OAuth and approved APIs. Password collection, simulated delivery and unsupported auto-posting are excluded.</p></div></div></>);}

  function Calendar(){return page(<><PageHeader eyebrow="CONTENT PLANNER" heading={<>Make consistency <em>feel effortless.</em></>} description="Plan your publishing rhythm and keep upcoming content in view."/><Glass className="calendar-shell"><div className="calendar-top"><div><span className="micro-label">PUBLISHING SCHEDULE</span><h2>Schedule overview</h2></div><span className="editor-pill">No scheduled posts</span></div><Empty icon={CalendarDays} title="Your calendar is clear" copy="Once a clip is approved and a channel is connected, scheduled posts will appear here." action={<button className="button-secondary" onClick={()=>navigate("/publishing")}>Connect a channel <ArrowUpRight size={14}/></button>}/></Glass></>);}

  function Analytics(){return page(<><PageHeader eyebrow="PERFORMANCE STUDIO" heading={<>Know what’s <em>resonating.</em></>} description="Understand post performance and turn real results into stronger creative decisions."/><div className="analytics-grid">{[{label:"VIEWS",icon:Play},{label:"ENGAGEMENT",icon:Activity},{label:"AUDIENCE RETENTION",icon:BarChart3},{label:"TOP CONTENT",icon:Gauge}].map(m=><Glass className="metric-card" key={m.label}><span>{m.label}<m.icon size={15}/></span><strong className="metric-placeholder">—</strong><small>Waiting for connected channel data</small></Glass>)}</div><Glass className="chart-placeholder"><div className="card-top"><div><span className="micro-label">PERFORMANCE OVER TIME</span><h3>Content insights</h3></div><SlidersHorizontal size={17}/></div><Empty icon={ChartNoAxesCombined} title="Your insights will build here" copy="Connect a supported social account and publish content to see verified metrics. No sample analytics are being shown."/></Glass></>);}

  function Growth(){return page(<><PageHeader eyebrow="GROWTH INTELLIGENCE" heading={<>Create with <em>intention.</em></>} description="A creative strategy layer inspired by creator-audit and content-intelligence workflows."/><div className="growth-grid">{[{icon:Compass,title:"Channel & profile audit",copy:"Review positioning, profile clarity, niche signals and content consistency."},{icon:Sparkles,title:"Ideas & hooks",copy:"Generate audience-aware concepts, opening hooks, scripts and calls to action."},{icon:Activity,title:"Video quality review",copy:"Evaluate pacing, clarity, audio, visual structure and opening strength."},{icon:Layers3,title:"Repurpose planner",copy:"Turn one source into tailored formats, captions and metadata for each channel."}].map(x=><Glass className="growth-card" key={x.title}><div className="growth-icon"><x.icon size={19}/></div><h3>{x.title}</h3><p>{x.copy}</p><span className="feature-state">PLANNED FEATURE</span></Glass>)}</div><div className="integration-note"><Sparkles size={16}/><div><b>Built around your real content</b><p>Growth recommendations are intended to connect to your actual clips and publishing results—not generic AI prompts or invented performance statistics.</p></div></div></>);}

  function Brand(){return page(<><PageHeader eyebrow="BRAND STUDIO" heading={<>Make every frame <em>feel like you.</em></>} description="Keep your visual identity consistent across captions, overlays and exports."/><div className="brand-layout"><Glass className="brand-preview"><span className="micro-label">BRAND PREVIEW</span><div className="brand-swatch"><img src="/assets/vyralis-mark.svg" alt="VYRALIS mark"/><div><b>Your brand identity</b><small>Preview canvas · 9:16</small></div></div><div className="swatches"><span/><span/><span/><span/></div><p>VYRALIS palette · Midnight · Violet · Electric blue · Cyan</p></Glass><Glass className="brand-options"><h3>Brand assets</h3>{[{icon:Palette,label:"Color palette",detail:"Primary and accent colors"},{icon:Captions,label:"Caption presets",detail:"Typography and emphasis styles"},{icon:Layers3,label:"Logo & watermark",detail:"Brand marks and safe placement"},{icon:Video,label:"Intro & outro",detail:"Reusable motion templates"}].map(x=><div className="brand-option" key={x.label}><x.icon size={18}/><div><b>{x.label}</b><small>{x.detail}</small></div><span className="feature-state">COMING</span></div>)}</Glass></div></>);}

  function Settings(){return page(<><PageHeader eyebrow="PREFERENCES" heading={<>Your studio, <em>your setup.</em></>} description="Manage workspace preferences, processing mode and connected services."/><div className="settings-stack"><Glass className="settings-card"><div><h3>Processing status</h3><p>Local engine connection and available capabilities.</p></div><span className={health?"status-tag":"status-tag muted"}>{health?"Connected":"Offline"}</span><button className="button-secondary" onClick={()=>void refresh()}>Refresh status</button></Glass><Glass className="settings-card"><div><h3>Processing engines</h3><p>FFmpeg · WhisperX / faster-whisper · PySceneDetect · MediaPipe / YOLO · Remotion</p><small>Integration targets. Availability is not yet verified in this environment.</small></div><span className="feature-state">NOT INSTALLED</span></Glass><Glass className="settings-card"><div><h3>Source adapters</h3><p>YouTube · Twitch · Kick · Local media</p><small>Link validation UI is present; source resolution is pending backend implementation.</small></div><span className="feature-state">IN PROGRESS</span></Glass><Glass className="settings-card"><div><h3>Workspace storage</h3><p>{assets.length} assets · {bytes(totalBytes)} indexed locally</p></div><span className="editor-pill">Local</span></Glass></div></>);}

  return <div className="app-shell">
    <aside className={"sidebar "+(mobileNav?"sidebar-open":"")}><a className="brand" href="/"><img src="/assets/vyralis-mark.svg" alt=""/><span>VYRALIS<small>STUDIO</small></span></a><div className="workspace-switch"><div className="workspace-avatar">V</div><div><b>Creator workspace</b><small>Personal studio</small></div><ChevronDown size={14}/></div>
      {navGroups.map(group=><div className="nav-group" key={group.label}><div className="nav-label">{group.label}</div><nav>{group.items.map(({to,label,icon:Icon})=><NavLink end={to==="/"} to={to} key={to} onClick={()=>setMobileNav(false)} className={({isActive})=>"nav-item"+(isActive?" active":"")}><Icon size={17}/><span>{label}</span>{to==="/create"&&<span className="nav-shortcut">⌘ K</span>}</NavLink>)}</nav></div>)}
      <div className="sidebar-bottom"><div className="engine-card"><div className="engine-top"><span className={"status-dot "+(health?"online":"")}/><b>{health?"Local engine connected":"Local engine offline"}</b></div><p>{health?"Media API is responding.":"Start the local backend to import and list media."}</p><button onClick={()=>void refresh()}>Check connection <ArrowUpRight size={13}/></button></div><div className="profile"><div className="profile-avatar">V</div><div><b>VYRALIS Creator</b><small>Personal workspace</small></div><MoreHorizontal size={17}/></div></div>
    </aside>
    {mobileNav&&<button className="mobile-scrim" aria-label="Close navigation" onClick={()=>setMobileNav(false)}/>}
    <main className="main"><header className="topbar"><div className="topbar-left"><button className="mobile-menu" onClick={()=>setMobileNav(v=>!v)} aria-label="Toggle menu"><Menu size={19}/></button><div className="breadcrumb">Workspace <span>/</span> {title}</div></div><div className="top-actions"><div className="engine-pill"><span className={"status-dot "+(health?"online":"")}/>{health?"ENGINE ONLINE":"ENGINE OFFLINE"}</div><button className="top-icon" aria-label="Help"><CircleHelp size={17}/></button><button className="top-icon" aria-label="Notifications"><Bell size={17}/></button><div className="avatar-mini">V</div></div></header>
      <div className="content"><AnimatePresence mode="wait"><Routes location={location} key={location.pathname}><Route path="/" element={<Dashboard/>}/><Route path="/projects" element={<Projects/>}/><Route path="/create" element={<Create/>}/><Route path="/editor" element={<Editor/>}/><Route path="/publishing" element={<Publishing/>}/><Route path="/calendar" element={<Calendar/>}/><Route path="/analytics" element={<Analytics/>}/><Route path="/growth" element={<Growth/>}/><Route path="/brand" element={<Brand/>}/><Route path="/settings" element={<Settings/>}/><Route path="*" element={<Dashboard/>}/></Routes></AnimatePresence><footer className="footer"><span>VYRALIS STUDIO <i>· Every moment has a story.</i></span><span className="footer-status"><span className={"status-dot "+(health?"online":"")}/>{health?"Local engine responding":"Local engine not connected"}</span><span>STUDIO / 0.2</span></footer></div>
    </main>
    {notice&&!location.pathname.includes("create")&&!location.pathname.includes("publishing")&&<div className="toast" onClick={()=>setNotice("")}>{notice}<X size={14}/></div>}
  </div>;
}
export default App;
