import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Download, RefreshCw, Scissors, Sparkles, Video } from "lucide-react";
import { api, type Clip, type ProcessingJob } from "../lib/api";

const clock = (value:number) => {
  const total=Math.max(0,Math.floor(value));
  return `${Math.floor(total/60).toString().padStart(2,"0")}:${(total%60).toString().padStart(2,"0")}`;
};

export default function ReviewPage() {
  const { projectId="" }=useParams();
  const [params]=useSearchParams();
  const jobId=params.get("job") || "";
  const navigate=useNavigate();
  const [job,setJob]=useState<ProcessingJob|null>(null);
  const [clips,setClips]=useState<Clip[]>([]);
  const [selected,setSelected]=useState("");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const refresh=useCallback(async()=>{
    if(!jobId)return;
    try {
      const current=await api.job(jobId); setJob(current);
      if(current.status==="completed"){
        const rows=await api.clips(projectId); setClips(rows);
        setSelected(old=>old||rows[0]?.id||"");
      }
    } catch(e){setError(e instanceof Error?e.message:"Unable to load project.");}
  },[jobId,projectId]);
  useEffect(()=>{void refresh();},[refresh]);
  useEffect(()=>{
    if(!job || ["completed","failed"].includes(job.status))return;
    const timer=window.setInterval(()=>void refresh(),2000);
    return ()=>window.clearInterval(timer);
  },[job,refresh]);
  const active=clips.find(c=>c.id===selected)||clips[0];
  async function save(){
    if(!active)return; setBusy(true);setError("");
    try{await api.editClip(active);setClips(await api.clips(projectId));}
    catch(e){setError(e instanceof Error?e.message:"Could not save edit.");}
    finally{setBusy(false);}
  }
  async function exportClip(){
    if(!active)return;setBusy(true);setError("");
    try{const result=await api.exportClip(active.id);window.location.href=api.fileUrl(result.download_url);setClips(await api.clips(projectId));}
    catch(e){setError(e instanceof Error?e.message:"Export failed.");}
    finally{setBusy(false);}
  }
  async function retry(){
    if(!job)return;setBusy(true);
    try{await fetch(api.fileUrl(`/api/jobs/${job.id}/retry`),{method:"POST"});setError("");await refresh();}
    catch(e){setError(e instanceof Error?e.message:"Retry failed.");}
    finally{setBusy(false);}
  }
  return <div className="page-content">
    <div className="page-heading"><div><div className="eyebrow"><Sparkles size={13}/> CLIP REVIEW</div><h1>Review your <em>best moments.</em></h1><p>Track processing, inspect ranked highlights, make precise edits and export real MP4 clips.</p></div><button className="button-secondary" onClick={()=>navigate("/projects")}><ArrowLeft size={15}/> Projects</button></div>
    {job&&<section className="glass" style={{padding:22,marginBottom:22}}>
      <div style={{display:"flex",justifyContent:"space-between",gap:16,alignItems:"center"}}><div><span className="micro-label">PROCESSING STATUS</span><h3 style={{margin:"8px 0 4px"}}>{job.stage.replaceAll("_"," ")}</h3><p style={{margin:0}}>{job.message}</p></div><strong style={{fontSize:24}}>{job.progress}%</strong></div>
      <div style={{height:7,background:"rgba(255,255,255,.09)",borderRadius:20,marginTop:18,overflow:"hidden"}}><div style={{height:"100%",width:`${job.progress}%`,background:"linear-gradient(90deg,#a855f7,#397bff)",transition:"width .4s"}}/></div>
      {job.status==="failed"&&<div style={{marginTop:14,color:"#ff9b9b"}}>{job.error}<button className="button-secondary" style={{marginLeft:12}} onClick={()=>void retry()} disabled={busy}><RefreshCw size={14}/> Retry</button></div>}
    </section>}
    {error&&<div className="notice">{error}</div>}
    {clips.length>0&&active?<div style={{display:"grid",gridTemplateColumns:"minmax(0,1.25fr) minmax(280px,.75fr)",gap:18}}>
      <section className="glass" style={{padding:18}}>
        <div className="card-top"><div><span className="micro-label">SOURCE PREVIEW</span><h3>{active.title}</h3></div><span className="status-tag">#{active.rank} · {active.score}/100</span></div>
        <video controls preload="metadata" src={api.fileUrl(`/api/projects/${projectId}/source#t=${active.start_seconds},${active.end_seconds}`)} style={{width:"100%",maxHeight:560,background:"#05060b",borderRadius:14,marginTop:12}}/>
        <div style={{display:"flex",gap:10,flexWrap:"wrap",marginTop:16}}><button className="button-primary" onClick={()=>void exportClip()} disabled={busy}><Download size={15}/> Render & download MP4</button><button className="button-secondary" onClick={()=>void save()} disabled={busy}><Scissors size={15}/> Save edits</button></div>
      </section>
      <section className="glass" style={{padding:18}}>
        <span className="micro-label">RANKED CLIPS</span><div style={{display:"grid",gap:8,margin:"12px 0 20px",maxHeight:240,overflowY:"auto"}}>{clips.map(c=><button key={c.id} onClick={()=>setSelected(c.id)} className="quick-option" style={{border:selected===c.id?"1px solid #a855f7":undefined,textAlign:"left"}}><span className="quick-icon"><Video size={16}/></span><span><b>{c.title}</b><small>{clock(c.start_seconds)}–{clock(c.end_seconds)} · Score {c.score}</small></span></button>)}</div>
        <span className="micro-label">CLIP EDITS</span><label style={{display:"block",marginTop:10}}>Title<input value={active.title} onChange={e=>setClips(old=>old.map(c=>c.id===active.id?{...c,title:e.target.value}:c))}/></label>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginTop:12}}><label>Start (seconds)<input type="number" min="0" step=".1" value={active.start_seconds} onChange={e=>setClips(old=>old.map(c=>c.id===active.id?{...c,start_seconds:Number(e.target.value)}:c))}/></label><label>End (seconds)<input type="number" min="0" step=".1" value={active.end_seconds} onChange={e=>setClips(old=>old.map(c=>c.id===active.id?{...c,end_seconds:Number(e.target.value)}:c))}/></label></div>
        <div style={{marginTop:18}}><span className="micro-label">WHY THIS MOMENT RANKED</span><p style={{fontSize:13,lineHeight:1.6}}>{active.reason}</p><div style={{display:"grid",gap:8}}>{Object.entries(active.score_breakdown).map(([name,value])=><div key={name} style={{display:"grid",gridTemplateColumns:"80px 1fr 28px",gap:8,alignItems:"center",fontSize:12}}><span style={{textTransform:"capitalize"}}>{name}</span><div style={{height:5,background:"rgba(255,255,255,.1)",borderRadius:10}}><div style={{width:`${value}%`,height:"100%",background:"#a855f7",borderRadius:10}}/></div><b>{value}</b></div>)}</div></div>
        <div style={{marginTop:18}}><span className="micro-label">TRANSCRIPT</span><p style={{fontSize:13,lineHeight:1.7}}>{active.transcript}</p></div>
      </section>
    </div>:job?.status==="completed"?<div className="empty-panel"><div className="empty-icon"><Video size={23}/></div><h3>No clip candidates were returned</h3><p>Try a longer source or adjust clip duration settings.</p></div>:<div className="empty-panel"><div className="empty-icon"><RefreshCw size={23}/></div><h3>Preparing your clip review</h3><p>Keep this page open. The worker will update this project as each processing stage completes.</p></div>}
  </div>;
}
