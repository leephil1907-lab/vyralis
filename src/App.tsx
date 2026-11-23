import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  Activity, ArrowUpRight, BarChart3, Bell, CalendarDays,
  Check, ChevronDown, CircleHelp, Clapperboard, Compass, Film,
  FolderOpen, Gauge, HardDrive, Layers3, Link2, ListVideo, Menu,
  MoreHorizontal, Play, Plus, Search, Settings2, ShieldCheck, Sparkles, Subtitles, Network,
  WandSparkles, X, Youtube, Radio, SlidersHorizontal, Zap, Palette,
  Scissors, Upload, Video, Captions, ChartNoAxesCombined, AudioLines
} from "lucide-react";
import { api, type Health, type MediaAsset } from "./lib/api";
import ReviewPage from "./pages/ReviewPage";
import LandingPage from "./pages/LandingPage";
import PublishPage from "./pages/PublishPage";

const navGroups = [
  { label: "WORKSPACE", items: [
    { to: "/studio", label: "Dashboard", icon: Layers3 },
    { to: "/projects", label: "Projects", icon: FolderOpen },
    { to: "/settings", label: "Settings", icon: Settings2 },
  ]},
  { label: "CLIP STUDIO", items: [
    { to: "/create", label: "Create clips", icon: Clapperboard },
  ]},
  { label: "EDIT STUDIO", items: [
    { to: "/editor", label: "Video editor", icon: Scissors },
  ]},
  { label: "CREATIVE STUDIO", items: [
    { to: "/brand", label: "Brand kit", icon: Palette },
    { to: "/storylab", label: "StoryLab", icon: WandSparkles },
    { to: "/canvas", label: "Workflow canvas", icon: Network },
  ]},
  { label: "GROWTH INTELLIGENCE", items: [
    { to: "/growth", label: "Growth intelligence", icon: Compass },
    { to: "/trends", label: "Trend & niche radar", icon: Activity },
    { to: "/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  ]},
  { label: "PUBLISH STUDIO", items: [
    { to: "/publishing", label: "Publishing", icon: Radio },
    { to: "/calendar", label: "Content calendar", icon: CalendarDays },
  ]},
];
const titles: Record<string,string> = {
  "/":"Dashboard","/studio":"Dashboard","/projects":"Projects","/create":"Create clips","/editor":"Video editor",
  "/publishing":"Publishing","/calendar":"Content calendar","/analytics":"Analytics",
  "/growth":"Growth intelligence","/trends":"Trend & niche radar","/storylab":"StoryLab","/canvas":"Workflow canvas","/brand":"Brand kit","/settings":"Settings"
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
  const [rightsAttested,setRightsAttested]=useState(false);
  const [mobileNav,setMobileNav] = useState(false);

  async function refresh() {
    try { const [h,a] = await Promise.all([api.health(),api.assets()]); setHealth(h); setAssets(a); }
    catch { setHealth(null); }
  }
  useEffect(()=>{ void refresh(); },[]);
  async function upload(files:FileList|null) {
    if(!files?.length) return;
    setBusy(true); setNotice("Importing media to this workspace…");
    try { let lastProject: string | null = null; for(const file of Array.from(files)) { const asset = await api.upload(file); const project = await api.createProject(asset.id); lastProject = project.id + "?job=" + project.job_id; } await refresh(); setNotice("Upload complete. Processing has started."); if(lastProject) navigate("/review/" + lastProject); }
    catch(e){ setNotice(e instanceof Error?e.message:"Import failed."); }
    finally { setBusy(false); if(input.current) input.current.value=""; }
  }
  const filtered = useMemo(()=>assets.filter(a=>a.filename.toLowerCase().includes(query.toLowerCase())),[assets,query]);
  const title = titles[location.pathname] || "Dashboard";
  const totalBytes = assets.reduce((n,a)=>n+a.size,0);

  async function beginLinkFlow() {
    const value=sourceUrl.trim();
    if(!value){setNotice("Paste a YouTube, Twitch or Kick video link first.");return;}
    if(!rightsAttested){setNotice("Confirm you have the rights to this video before importing it.");return;}
    setBusy(true);
    setNotice("Resolving the source link…");
    try {
      const preview=await api.previewSource(value);
      const minutes=Math.max(1,Math.round(preview.duration_seconds/60));
      setNotice(`“${preview.title}”${preview.uploader?` by ${preview.uploader}`:""} · about ${minutes} min. Queuing the import…`);
      const project=await api.createProjectFromLink({url:value,rights_attested:true});
      setNotice(`Import queued for “${project.title}”. The engine downloads the source, transcribes it and ranks highlights.`);
      await refresh();
      navigate(`/review/${project.id}?job=${project.job_id}`);
    } catch(error){
      const message=error instanceof Error?error.message:String(error);
      setNotice(`Link import failed: ${message}`);
    } finally { setBusy(false); }
  }

  const page = (node:ReactNode) => <motion.div className="page-content" key={location.pathname} {...pageMotion} transition={{duration:.24,ease:[.22,1,.36,1]}}>{node}</motion.div>;
  const PageHeader = ({eyebrow,heading,description,action}:{eyebrow:string;heading:ReactNode;description:string;action?:ReactNode}) => <div className="page-heading"><div><div className="eyebrow"><Sparkles size={13}/>{eyebrow}</div><h1>{heading}</h1><p>{description}</p></div>{action&&<div className="heading-action">{action}</div>}</div>;
  const Glass = ({children,className=""}:{children:ReactNode;className?:string}) => <section className={"glass "+className}>{children}</section>;
  const Empty = ({icon:Icon=Film,title:heading,copy,action}:{icon?:any;title:string;copy:string;action?:ReactNode}) => <div className="empty-panel"><div className="empty-icon"><Icon size={23}/></div><h3>{heading}</h3><p>{copy}</p>{action}</div>;

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
    return page(<><PageHeader eyebrow="CLIP STUDIO" heading={<>Find the moments that <em>move people.</em></>} description="Import a YouTube, Twitch or Kick link, or upload a file. Transcription, ranked highlights and MP4 exports run on the local engine."/>
      <Glass className="create-panel"><div className="source-tabs"><span className="source-tab active"><Link2 size={15}/> Paste video link</span><button className="source-tab" onClick={()=>input.current?.click()}><Upload size={15}/> Upload video</button></div><div className="source-input-wrap"><Link2 size={18}/><input value={sourceUrl} onChange={e=>setSourceUrl(e.target.value)} onKeyDown={e=>e.key==="Enter"&&beginLinkFlow()} placeholder="Paste a YouTube, Twitch or Kick video URL"/><button className="button-primary" disabled={busy} onClick={()=>void beginLinkFlow()}>{busy?"Importing…":"Import & analyse"} <ArrowUpRight size={15}/></button></div><div className="source-support"><span><Youtube size={14}/> YouTube</span><span><Radio size={14}/> Twitch</span><span><Zap size={14}/> Kick</span><span className="source-note">Video link or local upload</span></div><label className="rights-check"><input type="checkbox" checked={rightsAttested} onChange={e=>setRightsAttested(e.target.checked)}/><span>I own this footage or have permission to clip and publish it.</span></label><input ref={input} type="file" accept="video/*" hidden onChange={e=>void upload(e.target.files)}/>{notice&&<div className="notice"><ShieldCheck size={15}/>{notice}</div>}</Glass>
      <div className="section-title"><div><span className="micro-label">YOUR CLIPPING WORKFLOW</span><h2>From source to shareable</h2></div></div><div className="workflow-grid">{[{n:"01",icon:Compass,title:"Discover highlights",desc:"Audio energy, transcript context, scene changes and standout moments."},{n:"02",icon:Scissors,title:"Shape every clip",desc:"Trim, split, reframe and refine your strongest moments."},{n:"03",icon:Captions,title:"Style your story",desc:"Word-timed captions, hooks, titles and reusable brand presets."},{n:"04",icon:Radio,title:"Publish & learn",desc:"Prepare platform versions, schedule posts and review performance."}].map(item=><Glass className="workflow-card" key={item.n}><span className="workflow-number">{item.n}</span><item.icon size={20}/><h3>{item.title}</h3><p>{item.desc}</p></Glass>)}</div>
      <div className="integration-note"><Sparkles size={16}/><div><b>What runs on your machine</b><p>Eligible public links are resolved with yt-dlp, media is validated with FFprobe, audio is extracted with FFmpeg, speech is transcribed with faster-whisper, and transcript windows are ranked for review. Provider restrictions, age or region locks and unavailable downloads can still block an import, and the job tells you why. If a tool is missing, the job fails with the exact command it needs instead of pretending to work.</p></div></div>
    </>);
  }

  function Projects(){
    return page(<><PageHeader eyebrow="PROJECT LIBRARY" heading={<>Everything you’re <em>working on.</em></>} description="Your imported source footage and project assets, together in one workspace." action={<button className="button-primary" onClick={()=>navigate("/create")}><Plus size={15}/> New project</button>}/><div className="toolbar"><div className="search-box"><Search size={15}/><input placeholder="Search your media" value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="quiet-count">{filtered.length} assets</span></div>{filtered.length?<Glass className="asset-list">{filtered.map(a=><div className="asset-row" key={a.id}><div className="asset-art"><Film size={18}/></div><div className="asset-meta"><b>{a.filename}</b><small>{a.content_type||"Media"} · {bytes(a.size)} · {new Date(a.created_at).toLocaleDateString()}</small></div><span className="status-tag"><Check size={12}/> Imported</span><MoreHorizontal size={18}/></div>)}</Glass>:<Empty icon={FolderOpen} title={query?"No matching assets":"No projects yet"} copy={query?"Try another search term.":"Start with a YouTube, Twitch or Kick link, or upload a local video."} action={<button className="button-primary" onClick={()=>navigate("/create")}><Plus size={15}/> Create project</button>}/>}</>);
  }

  function Editor(){return page(<><PageHeader eyebrow="VIDEO EDITOR" heading={<>Make the cut <em>your own.</em></>} description="A focused editing workspace for timing, framing, captions and finishing."/><Glass className="editor-shell"><div className="editor-toolbar"><span><Scissors size={15}/> Untitled sequence</span><span className="editor-pill">No clip selected</span><button className="button-secondary" onClick={()=>navigate("/create")}>Choose source</button></div><Empty icon={Video} title="Your editing canvas is ready" copy="Create or import a clip first. The timeline editor, transcript-linked trimming and split/merge are not built yet; caption styling and automatic reframing already run from Review on any ranked clip."/></Glass><div className="feature-row">{[{icon:ListVideo,title:"Transcript timeline",copy:"Navigate by spoken words and timestamps."},{icon:Subtitles,title:"Caption styling",copy:"Word timing, emphasis and language variants."},{icon:Compass,title:"Smart framing",copy:"Face and speaker-aware vertical composition."}].map(x=><Glass className="mini-feature" key={x.title}><x.icon size={19}/><b>{x.title}</b><small>{x.copy}</small></Glass>)}</div></>);}

  function Calendar(){return page(<><PageHeader eyebrow="CONTENT PLANNER" heading={<>Make consistency <em>feel effortless.</em></>} description="Plan your publishing rhythm and keep upcoming content in view."/><Glass className="calendar-shell"><div className="calendar-top"><div><span className="micro-label">PUBLISHING SCHEDULE</span><h2>Schedule overview</h2></div><span className="editor-pill">No scheduled posts</span></div><Empty icon={CalendarDays} title="Your calendar is clear" copy="Once a clip is approved and a channel is connected, scheduled posts will appear here." action={<button className="button-secondary" onClick={()=>navigate("/publishing")}>Connect a channel <ArrowUpRight size={14}/></button>}/></Glass></>);}

  function Analytics(){return page(<><PageHeader eyebrow="PERFORMANCE STUDIO" heading={<>Know what’s <em>resonating.</em></>} description="Understand post performance and turn real results into stronger creative decisions."/><div className="analytics-grid">{[{label:"VIEWS",icon:Play},{label:"ENGAGEMENT",icon:Activity},{label:"AUDIENCE RETENTION",icon:BarChart3},{label:"TOP CONTENT",icon:Gauge}].map(m=><Glass className="metric-card" key={m.label}><span>{m.label}<m.icon size={15}/></span><strong className="metric-placeholder">—</strong><small>Waiting for connected channel data</small></Glass>)}</div><Glass className="chart-placeholder"><div className="card-top"><div><span className="micro-label">PERFORMANCE OVER TIME</span><h3>Content insights</h3></div><SlidersHorizontal size={17}/></div><Empty icon={ChartNoAxesCombined} title="Your insights will build here" copy="Connect a supported social account and publish content to see verified metrics. No sample analytics are being shown."/></Glass></>);}

  function Growth(){return page(<><PageHeader eyebrow="GROWTH INTELLIGENCE" heading={<>Create with <em>intention.</em></>} description="A creative strategy layer inspired by creator-audit and content-intelligence workflows."/><div className="growth-grid">{[{icon:Compass,title:"Channel & profile audit",copy:"Review positioning, profile clarity, niche signals and content consistency."},{icon:Sparkles,title:"Ideas & hooks",copy:"Generate audience-aware concepts, opening hooks, scripts and calls to action."},{icon:Activity,title:"Video quality review",copy:"Evaluate pacing, clarity, audio, visual structure and opening strength."},{icon:Layers3,title:"Repurpose planner",copy:"Turn one source into tailored formats, captions and metadata for each channel."}].map(x=><Glass className="growth-card" key={x.title}><div className="growth-icon"><x.icon size={19}/></div><h3>{x.title}</h3><p>{x.copy}</p><span className="feature-state">PLANNED FEATURE</span></Glass>)}</div><div className="integration-note"><Sparkles size={16}/><div><b>Built around your real content</b><p>Growth recommendations are intended to connect to your actual clips and publishing results—not generic AI prompts or invented performance statistics.</p></div></div></>);}


  function Trends(){const [category,setCategory]=useState("All");const [topic,setTopic]=useState("");const groups=[{name:"Education & explainers",sub:["History mysteries","Science in 60 seconds","Psychology & behavior"]},{name:"Business & money",sub:["Founder stories","Personal finance basics","Small business lessons"]},{name:"Entertainment & culture",sub:["Gaming moments","Film & pop culture","Internet stories"]},{name:"Lifestyle & practical",sub:["Food & recipes","Travel discoveries","Home & DIY"]},{name:"Narrative channels",sub:["True crime explainers","Folklore & legends","Motivational stories"]}];return page(<><PageHeader eyebrow="TREND & NICHE RADAR" heading={<>Find your next <em>content lane.</em></>} description="Explore niche directions, evaluate audience demand and competition, then turn a promising angle into a repeatable content series."/><Glass className="trend-intro"><div><span className="micro-label">NICHE DISCOVERY</span><h2>Research before you create.</h2><p>VYRALIS will combine platform trend signals, search interest, channel activity and your own publishing results. Live trend rankings are not connected yet.</p></div><div className="trend-orb"><Compass size={28}/></div></Glass><div className="toolbar"><div className="search-box"><Search size={15}/><input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Search niches or content angles"/></div><div className="category-filter">{["All",...groups.map(g=>g.name)].map(c=><button key={c} className={"source-tab"+(category===c?" active":"")} onClick={()=>setCategory(c)}>{c}</button>)}</div></div><div className="trend-grid">{groups.filter(g=>category==="All"||g.name===category).map(g=><Glass className="trend-card" key={g.name}><div className="trend-card-head"><div className="growth-icon"><Compass size={18}/></div><span className="feature-state">DISCOVERY SEED</span></div><h3>{g.name}</h3><div className="trend-tags">{g.sub.filter(s=>s.toLowerCase().includes(topic.toLowerCase())).map(s=><button key={s} onClick={()=>{setTopic(s);setNotice("Niche selected: "+s+". Connect trend data providers to validate current demand and competition.")}}>{s}<ArrowUpRight size={12}/></button>)}</div><p>Potential angles to validate with current audience and platform data.</p></Glass>)}</div><div className="integration-note"><Activity size={16}/><div><b>Live trend intelligence is a separate data integration</b><p>Planned inputs: YouTube Data API, TikTok/Instagram authorized insights where available, Google Trends or a licensed trend provider, channel growth and keyword signals. No fabricated live rankings, RPM or earnings estimates.</p></div></div><div className="section-title"><div><span className="micro-label">NEXT STEP</span><h2>Turn a niche into a series</h2></div><button className="button-primary" onClick={()=>navigate("/storylab")}>Open StoryLab <ArrowUpRight size={14}/></button></div></>);}
  function StoryLab(){const [topic,setTopic]=useState("");const [audience,setAudience]=useState("Curious general audience");const [style,setStyle]=useState("Cinematic documentary");const [length,setLength]=useState("45 seconds");const [outline,setOutline]=useState(false);const scenes=["The hook — open with a surprising question or tension","The setup — establish the subject and why it matters","The reveal — deliver the central fact, conflict or turning point","The payoff — explain the consequence or emotional insight","The close — finish with a memorable line and clear next action"];return page(<><PageHeader eyebrow="STORYLAB" heading={<>Give every idea a <em>visual story.</em></>} description="Build a scene-by-scene plan with narration direction, visual references and shot prompts before generating assets."/><Glass className="story-form"><div className="story-form-grid"><label>What is the story about?<textarea value={topic} onChange={e=>{setTopic(e.target.value);setOutline(false)}} placeholder="e.g. The forgotten invention that changed how cities work"/></label><div className="story-fields"><label>Audience<select value={audience} onChange={e=>setAudience(e.target.value)}><option>Curious general audience</option><option>Young entrepreneurs</option><option>History enthusiasts</option><option>Tech and science fans</option><option>Existing followers</option></select></label><label>Visual direction<select value={style} onChange={e=>setStyle(e.target.value)}><option>Cinematic documentary</option><option>Illustrated storybook</option><option>Minimal motion graphics</option><option>Photorealistic editorial</option><option>Fast-paced social explainer</option></select></label><label>Target duration<select value={length} onChange={e=>setLength(e.target.value)}><option>30 seconds</option><option>45 seconds</option><option>60 seconds</option><option>90 seconds</option><option>3 minutes</option></select></label><button className="button-primary" onClick={()=>setOutline(true)} disabled={!topic.trim()}>Build storyboard <WandSparkles size={15}/></button></div></div></Glass>{outline?<><div className="section-title"><div><span className="micro-label">STORYBOARD DRAFT</span><h2>{topic}</h2></div><span className="editor-pill">Editable outline · {length}</span></div><div className="storyboard-list">{scenes.map((s,i)=><Glass className="story-scene" key={s}><div className="scene-number">SCENE 0{i+1}</div><div><b>{s}</b><p>Visual direction: {style}. Audience: {audience}. Add a verified detail, narration, and a matching visual before production.</p></div><span className="feature-state">DRAFT</span></Glass>)}</div><div className="integration-note"><Sparkles size={16}/><div><b>Storyboard structure prepared</b><p>This is a structured planning draft, not generated factual research, AI imagery or a rendered video. The next integration will connect script generation, reference images, image/video models and voice synthesis.</p></div></div></>:<Empty icon={WandSparkles} title="Start with a story idea" copy="Describe a topic and choose an audience and visual direction. Your storyboard draft will appear here."/>}</>);}
  function Canvas(){const [selected,setSelected]=useState("Script");const nodes=[{name:"Brief",type:"INPUT",desc:"Topic, niche, audience and brand voice"},{name:"Research",type:"INTELLIGENCE",desc:"Sources, facts, trends and references"},{name:"Script",type:"TEXT",desc:"Hook, narration, scene beats and CTA"},{name:"Visuals",type:"IMAGE / VIDEO",desc:"Scene illustrations, b-roll and motion"},{name:"Voice",type:"AUDIO",desc:"Narration, voice style and timing"},{name:"Compose",type:"RENDER",desc:"Captions, framing, music and export"}];return page(<><PageHeader eyebrow="CREATIVE WORKFLOW CANVAS" heading={<>Connect ideas to <em>finished content.</em></>} description="A node-based creative pipeline inspired by modern generative media canvases. Build repeatable workflows without leaving VYRALIS."/><div className="canvas-toolbar"><span className="editor-pill">WORKFLOW / STORY TO SHORT</span><button className="button-secondary" onClick={()=>setSelected("Script")}>Reset selection</button><span className="feature-state">CANVAS PREVIEW</span></div><Glass className="canvas-board"><div className="canvas-grid">{nodes.map((n,i)=><button className={"canvas-node "+(selected===n.name?"selected":"")} key={n.name} onClick={()=>setSelected(n.name)}><span className="node-index">{String(i+1).padStart(2,"0")} · {n.type}</span><b>{n.name}</b><small>{n.desc}</small><span className="node-port"/>{i<nodes.length-1&&<span className="node-link"/>}</button>)}</div></Glass><div className="canvas-detail"><Glass className="canvas-detail-card"><span className="micro-label">SELECTED NODE</span><h3>{selected}</h3><p>{nodes.find(n=>n.name===selected)?.desc}. Each node will expose provider settings, inputs, outputs, retries and previewable results when the execution engine is connected.</p><span className="feature-state">WORKFLOW ENGINE NOT CONNECTED</span></Glass><Glass className="canvas-detail-card"><span className="micro-label">PLANNED MODEL ADAPTERS</span><p>Text and research · Image generation · Video generation · Voice and sound · FFmpeg composition · Caption and translation.</p><p>Provider selection will be capability-based, with model availability, cost estimates and licensing checked before execution.</p></Glass></div><div className="integration-note"><Network size={16}/><div><b>Reusable workflow templates</b><p>Save a workflow once, then apply it to a new topic, uploaded recording or source link. Execution, autosave and model-provider connections are future backend work; this canvas is currently an interactive interface preview.</p></div></div></>);}
  function Brand(){return page(<><PageHeader eyebrow="BRAND STUDIO" heading={<>Make every frame <em>feel like you.</em></>} description="Keep your visual identity consistent across captions, overlays and exports."/><div className="brand-layout"><Glass className="brand-preview"><span className="micro-label">BRAND PREVIEW</span><div className="brand-swatch"><img src="/assets/vyralis-mark.svg" alt="VYRALIS mark"/><div><b>Your brand identity</b><small>Preview canvas · 9:16</small></div></div><div className="swatches"><span/><span/><span/><span/></div><p>VYRALIS palette · Midnight · Violet · Electric blue · Cyan</p></Glass><Glass className="brand-options"><h3>Brand assets</h3>{[{icon:Palette,label:"Color palette",detail:"Primary and accent colors"},{icon:Captions,label:"Caption presets",detail:"Typography and emphasis styles"},{icon:Layers3,label:"Logo & watermark",detail:"Brand marks and safe placement"},{icon:Video,label:"Intro & outro",detail:"Reusable motion templates"}].map(x=><div className="brand-option" key={x.label}><x.icon size={18}/><div><b>{x.label}</b><small>{x.detail}</small></div><span className="feature-state">COMING</span></div>)}</Glass></div></>);}

  function Settings(){return page(<><PageHeader eyebrow="PREFERENCES" heading={<>Your studio, <em>your setup.</em></>} description="Manage workspace preferences, processing mode and connected services."/><div className="settings-stack"><Glass className="settings-card"><div><h3>Processing status</h3><p>Local engine connection and available capabilities.</p></div><span className={health?"status-tag":"status-tag muted"}>{health?"Connected":"Offline"}</span><button className="button-secondary" onClick={()=>void refresh()}>Refresh status</button></Glass><Glass className="settings-card"><div><h3>Processing engines</h3><p>FFmpeg · WhisperX / faster-whisper · PySceneDetect · MediaPipe / YOLO · Remotion</p><small>Integration targets. Availability is not yet verified in this environment.</small></div><span className="feature-state">NOT INSTALLED</span></Glass><Glass className="settings-card"><div><h3>Source adapters</h3><p>YouTube · Twitch · Kick · Local media</p><small>Link validation UI is present; source resolution is pending backend implementation.</small></div><span className="feature-state">IN PROGRESS</span></Glass><Glass className="settings-card"><div><h3>Workspace storage</h3><p>{assets.length} assets · {bytes(totalBytes)} indexed locally</p></div><span className="editor-pill">Local</span></Glass></div></>);}

  if (location.pathname === "/") return <LandingPage/>;

  return <div className="app-shell">
    <aside className={"sidebar "+(mobileNav?"sidebar-open":"")}><a className="brand" href="/"><img src="/assets/vyralis-mark.svg" alt=""/><span>VYRALIS<small>STUDIO</small></span></a><div className="workspace-switch"><div className="workspace-avatar">V</div><div><b>Creator workspace</b><small>Personal studio</small></div><ChevronDown size={14}/></div>
      {navGroups.map(group=><div className="nav-group" key={group.label}><div className="nav-label">{group.label}</div><nav>{group.items.map(({to,label,icon:Icon})=><NavLink end={to==="/"} to={to} key={to} onClick={()=>setMobileNav(false)} className={({isActive})=>"nav-item"+(isActive?" active":"")}><Icon size={17}/><span>{label}</span>{to==="/create"&&<span className="nav-shortcut">⌘ K</span>}</NavLink>)}</nav></div>)}
      <div className="sidebar-bottom"><div className="engine-card"><div className="engine-top"><span className={"status-dot "+(health?"online":"")}/><b>{health?"Local engine connected":"Local engine offline"}</b></div><p>{health?"Media API is responding.":"Start the local backend to import and list media."}</p><button onClick={()=>void refresh()}>Check connection <ArrowUpRight size={13}/></button></div><div className="profile"><div className="profile-avatar">V</div><div><b>VYRALIS Creator</b><small>Personal workspace</small></div><MoreHorizontal size={17}/></div></div>
    </aside>
    {mobileNav&&<button className="mobile-scrim" aria-label="Close navigation" onClick={()=>setMobileNav(false)}/>}
    <main className="main"><header className="topbar"><div className="topbar-left"><button className="mobile-menu" onClick={()=>setMobileNav(v=>!v)} aria-label="Toggle menu"><Menu size={19}/></button><div className="breadcrumb">Workspace <span>/</span> {title}</div></div><div className="top-actions"><div className="engine-pill"><span className={"status-dot "+(health?"online":"")}/>{health?"ENGINE ONLINE":"ENGINE OFFLINE"}</div><button className="top-icon" aria-label="Help"><CircleHelp size={17}/></button><button className="top-icon" aria-label="Notifications"><Bell size={17}/></button><div className="avatar-mini">V</div></div></header>
      <div className="content"><AnimatePresence mode="wait"><Routes location={location} key={location.pathname}><Route path="/studio" element={<Dashboard/>}/><Route path="/" element={<LandingPage/>}/><Route path="/projects" element={<Projects/>}/><Route path="/create" element={<Create/>}/><Route path="/editor" element={<Editor/>}/><Route path="/review/:projectId" element={<ReviewPage/>}/><Route path="/publishing" element={<PublishPage/>}/><Route path="/calendar" element={<Calendar/>}/><Route path="/analytics" element={<Analytics/>}/><Route path="/growth" element={<Growth/>}/><Route path="/trends" element={<Trends/>}/><Route path="/storylab" element={<StoryLab/>}/><Route path="/canvas" element={<Canvas/>}/><Route path="/brand" element={<Brand/>}/><Route path="/settings" element={<Settings/>}/><Route path="*" element={<Dashboard/>}/></Routes></AnimatePresence><footer className="footer"><span>VYRALIS STUDIO <i>· Every moment has a story.</i></span><span className="footer-status"><span className={"status-dot "+(health?"online":"")}/>{health?"Local engine responding":"Local engine not connected"}</span><span>STUDIO / 0.3</span></footer></div>
    </main>
    {notice&&!location.pathname.includes("create")&&!location.pathname.includes("publishing")&&<div className="toast" onClick={()=>setNotice("")}>{notice}<X size={14}/></div>}
  </div>;
}
export default App;
