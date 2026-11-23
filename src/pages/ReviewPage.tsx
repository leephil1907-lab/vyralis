import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  AlertTriangle, ArrowLeft, Ban, Check, CheckCircle2, Download, Hash,
  RefreshCw, Scissors, ShieldCheck, Sparkles, Video, XCircle,
} from "lucide-react";
import {
  api, type Clip, type ClipExport, type ExportPreset, type Packaging,
  type PresetInfo, type ProcessingJob,
} from "../lib/api";

const clock = (value: number) => {
  const total = Math.max(0, Math.floor(value));
  return `${Math.floor(total / 60).toString().padStart(2, "0")}:${(total % 60).toString().padStart(2, "0")}`;
};
const splitTags = (value: string) => value.split(/[,\s]+/).map(token => token.trim()).filter(Boolean);
const statusIcon = { pass: CheckCircle2, warn: AlertTriangle, fail: XCircle } as const;

export default function ReviewPage() {
  const { projectId = "" } = useParams();
  const [params] = useSearchParams();
  const jobId = params.get("job") || "";
  const navigate = useNavigate();

  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [renderJobId, setRenderJobId] = useState("");
  const [renderMessage, setRenderMessage] = useState("");

  const [presets, setPresets] = useState<PresetInfo[]>([]);
  const [preset, setPreset] = useState<ExportPreset>("9:16");
  const [exports, setExports] = useState<ClipExport[]>([]);
  const [packaging, setPackaging] = useState<Packaging[]>([]);
  const [destination, setDestination] = useState("tiktok");
  const [draft, setDraft] = useState({ title: "", description: "", hashtags: "" });
  const [packagingBusy, setPackagingBusy] = useState(false);
  const [packagingNotice, setPackagingNotice] = useState("");

  const active = clips.find(clip => clip.id === selected) || clips[0];
  const activePackaging = useMemo(() => packaging.find(item => item.destination === destination), [packaging, destination]);
  const latestExport = exports[0];

  const refresh = useCallback(async () => {
    if (!jobId) return;
    try {
      const current = await api.job(jobId);
      setJob(current);
      if (current.status === "completed") {
        const rows = await api.clips(projectId);
        setClips(rows);
        setSelected(old => old || rows[0]?.id || "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load project.");
    }
  }, [jobId, projectId]);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled"].includes(job.status)) return;
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => window.clearInterval(timer);
  }, [job, refresh]);

  useEffect(() => {
    void api.exportPresets().then(result => setPresets(result.presets)).catch(() => setPresets([]));
  }, []);

  const syncPackaging = useCallback((rows: Packaging[], which: string) => {
    setPackaging(rows);
    const match = rows.find(item => item.destination === which);
    if (match) setDraft({ title: match.title, description: match.description, hashtags: match.hashtags.join(", ") });
  }, []);

  const loadClipDetail = useCallback(async (clipId: string, which: string) => {
    if (!clipId) return;
    try {
      const [exportRows, packagingRows] = await Promise.all([api.clipExports(clipId), api.packaging(clipId)]);
      setExports(exportRows);
      syncPackaging(packagingRows, which);
    } catch {
      setExports([]);
      setPackaging([]);
    }
  }, [syncPackaging]);

  useEffect(() => {
    if (active) void loadClipDetail(active.id, destination);
  }, [active?.id, destination, loadClipDetail]);

  useEffect(() => {
    if (!renderJobId) return;
    let stopped = false;
    const check = async () => {
      try {
        const current = await api.job(renderJobId);
        if (stopped) return;
        setRenderMessage(current.message);
        if (current.status === "completed") {
          stopped = true;
          setRenderJobId("");
          setNotice(current.message);
          if (active) await loadClipDetail(active.id, destination);
          await refresh();
        } else if (current.status === "failed" || current.status === "cancelled") {
          stopped = true;
          setError(current.error || current.message);
          setRenderJobId("");
          if (active) await loadClipDetail(active.id, destination);
        }
      } catch (e) {
        if (!stopped) setError(e instanceof Error ? e.message : "Render status unavailable.");
      }
    };
    void check();
    const timer = window.setInterval(() => void check(), 1500);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [renderJobId, active, destination, loadClipDetail, refresh]);

  async function save() {
    if (!active) return;
    setBusy(true); setError("");
    try {
      await api.editClip(active);
      setClips(await api.clips(projectId));
      setNotice("Clip edit saved. Re-render to validate the new cut.");
      await loadClipDetail(active.id, destination);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save edit.");
    } finally { setBusy(false); }
  }

  async function exportClip() {
    if (!active) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await api.exportClip(active.id, preset);
      setRenderJobId(result.job_id);
      setRenderMessage(result.idempotent ? "A render for this preset is already running…" : "Render queued…");
      await loadClipDetail(active.id, destination);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed.");
    } finally { setBusy(false); }
  }

  async function cancelJob() {
    if (!job) return;
    setBusy(true);
    try {
      const result = await api.cancelJob(job.id);
      setNotice(result.status === "cancelled" ? "Job cancelled." : "Cancellation requested — the worker stops at its next checkpoint.");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cancel failed.");
    } finally { setBusy(false); }
  }

  async function retry() {
    if (!job) return;
    setBusy(true);
    try {
      await fetch(api.fileUrl(`/api/jobs/${job.id}/retry`), { method: "POST" });
      setError("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Retry failed.");
    } finally { setBusy(false); }
  }

  async function savePackaging() {
    if (!active) return;
    setPackagingBusy(true); setPackagingNotice("");
    try {
      const updated = await api.savePackaging(active.id, {
        destination,
        title: draft.title,
        description: draft.description,
        hashtags: splitTags(draft.hashtags),
      });
      syncPackaging(packaging.map(item => item.destination === destination ? updated : item), destination);
      setPackagingNotice(updated.validation.valid ? "Packaging saved." : "Saved, but fix the blocking errors before approval.");
    } catch (e) {
      setPackagingNotice(e instanceof Error ? e.message : "Could not save packaging.");
    } finally { setPackagingBusy(false); }
  }

  async function toggleApproval(approved: boolean) {
    if (!active) return;
    setPackagingBusy(true); setPackagingNotice("");
    try {
      const updated = await api.approvePackaging(active.id, destination, approved);
      syncPackaging(packaging.map(item => item.destination === destination ? updated : item), destination);
      setPackagingNotice(approved ? "Approved. It now appears in Publish Studio as a delivery package." : "Approval withdrawn.");
    } catch (e) {
      setPackagingNotice(e instanceof Error ? e.message : "Approval failed.");
    } finally { setPackagingBusy(false); }
  }

  return <div className="page-content">
    <div className="page-heading">
      <div>
        <div className="eyebrow"><Sparkles size={13}/> CLIP REVIEW</div>
        <h1>Review your <em>best moments.</em></h1>
        <p>Inspect ranked highlights, edit the cut, render a preset, then read the automated quality report before anything leaves the studio.</p>
      </div>
      <button className="button-secondary" onClick={() => navigate("/projects")}><ArrowLeft size={15}/> Projects</button>
    </div>

    {job && <section className="glass" style={{ padding: 22, marginBottom: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
        <div>
          <span className="micro-label">PROCESSING STATUS · {job.status.toUpperCase()}</span>
          <h3 style={{ margin: "8px 0 4px" }}>{job.stage.replaceAll("_", " ")}</h3>
          <p style={{ margin: 0 }}>{job.message}</p>
        </div>
        <strong style={{ fontSize: 24 }}>{job.progress}%</strong>
      </div>
      <div style={{ height: 7, background: "rgba(255,255,255,.09)", borderRadius: 20, marginTop: 18, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${job.progress}%`, background: "linear-gradient(90deg,#a855f7,#397bff)", transition: "width .4s" }}/>
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
        {job.status === "failed" && <button className="button-secondary" onClick={() => void retry()} disabled={busy}><RefreshCw size={14}/> Retry analysis</button>}
        {["queued", "processing", "cancelling"].includes(job.status) && <button className="button-secondary" onClick={() => void cancelJob()} disabled={busy}><Ban size={14}/> Cancel job</button>}
      </div>
      {job.status === "failed" && <p style={{ color: "#ff9b9b", margin: "12px 0 0" }}>{job.error}</p>}
    </section>}

    {error && <div className="notice"><AlertTriangle size={15}/> {error}</div>}
    {notice && !error && <div className="notice"><Check size={15}/> {notice}</div>}

    {clips.length > 0 && active
      ? <div className="review-layout">
          <section className="glass review-card">
            <div className="card-top">
              <div>
                <span className="micro-label">SOURCE PREVIEW</span>
                <h3>{active.title}</h3>
              </div>
              <span className="status-tag">#{active.rank} · {active.score}/100</span>
            </div>
            <video
              controls
              preload="metadata"
              key={active.id}
              src={api.fileUrl(`/api/projects/${projectId}/source#t=${active.start_seconds},${active.end_seconds}`)}
              style={{ width: "100%", maxHeight: 520, background: "#05060b", borderRadius: 14, marginTop: 12 }}
            />

            <div className="preset-row">
              {(presets.length ? presets : [{ preset: "9:16" as ExportPreset, label: "Vertical 9:16", width: 1080, height: 1920, use: "" }]).map(item => (
                <button
                  key={item.preset}
                  className={"preset-chip" + (preset === item.preset ? " active" : "")}
                  onClick={() => setPreset(item.preset)}
                  title={item.use}
                >
                  <span>{item.label}</span>
                  <small>{item.width}×{item.height}</small>
                </button>
              ))}
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
              <button className="button-primary" onClick={() => void exportClip()} disabled={busy || !!renderJobId}>
                <Download size={15}/> Render {preset} &amp; validate
              </button>
              <button className="button-secondary" onClick={() => void save()} disabled={busy}><Scissors size={15}/> Save edits</button>
              {latestExport?.download_url && (
                <a className="button-secondary" href={api.fileUrl(latestExport.download_url)}><Download size={15}/> Download {latestExport.preset}</a>
              )}
            </div>
            {renderJobId && <p className="notice"><RefreshCw size={14}/> {renderMessage}</p>}
            {latestExport?.status && latestExport.status !== "ready" && <p className="micro-label" style={{ marginTop: 14 }}>RENDER · {latestExport.status.toUpperCase()}</p>}

            {latestExport?.quality_report && (
              <div className={"quality-panel " + latestExport.quality_report.status}>
                <div className="quality-head">
                  <div>
                    <span className="micro-label"><ShieldCheck size={12}/> AUTOMATED QUALITY REPORT</span>
                    <b>{latestExport.quality_report.summary}</b>
                  </div>
                  <span className={"quality-pill " + latestExport.quality_report.status}>{latestExport.quality_report.status}</span>
                </div>
                <div className="quality-list">
                  {latestExport.quality_report.checks.map(check => {
                    const Icon = statusIcon[check.status];
                    return <div className={"quality-item " + check.status} key={check.id}>
                      <Icon size={14}/>
                      <div><b>{check.label}</b><span>{check.detail}</span></div>
                    </div>;
                  })}
                </div>
                <p className="quality-note">
                  Checks are measured from the rendered file: duration, frame size, codecs, black frames, frozen frames and loudness.
                  A failed check blocks the download; warnings remain your call.
                </p>
              </div>
            )}
          </section>

          <section className="glass review-card">
            <span className="micro-label">RANKED CLIPS</span>
            <div className="clip-list">
              {clips.map(clip => (
                <button
                  key={clip.id}
                  onClick={() => setSelected(clip.id)}
                  className={"quick-option" + (selected === clip.id ? " selected" : "")}
                >
                  <span className="quick-icon"><Video size={16}/></span>
                  <span>
                    <b>{clip.title}</b>
                    <small>{clock(clip.start_seconds)}–{clock(clip.end_seconds)} · Score {clip.score}</small>
                  </span>
                </button>
              ))}
            </div>

            <span className="micro-label">CLIP EDITS</span>
            <label style={{ display: "block", marginTop: 10 }}>Title
              <input
                value={active.title}
                onChange={e => setClips(old => old.map(clip => clip.id === active.id ? { ...clip, title: e.target.value } : clip))}
              />
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 12 }}>
              <label>Start (seconds)
                <input type="number" min="0" step=".1" value={active.start_seconds}
                  onChange={e => setClips(old => old.map(clip => clip.id === active.id ? { ...clip, start_seconds: Number(e.target.value) } : clip))}/>
              </label>
              <label>End (seconds)
                <input type="number" min="0" step=".1" value={active.end_seconds}
                  onChange={e => setClips(old => old.map(clip => clip.id === active.id ? { ...clip, end_seconds: Number(e.target.value) } : clip))}/>
              </label>
            </div>

            <div style={{ marginTop: 18 }}>
              <span className="micro-label">WHY THIS MOMENT RANKED</span>
              <p style={{ fontSize: 13, lineHeight: 1.6 }}>{active.reason}</p>
              <div style={{ display: "grid", gap: 8 }}>
                {Object.entries(active.score_breakdown).map(([name, value]) => (
                  <div key={name} className="score-row">
                    <span>{name}</span>
                    <div><i style={{ width: `${value}%` }}/></div>
                    <b>{value}</b>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginTop: 18 }}>
              <span className="micro-label">TRANSCRIPT</span>
              <p style={{ fontSize: 13, lineHeight: 1.7 }}>{active.transcript}</p>
            </div>

            <div className="packaging-block">
              <span className="micro-label"><Hash size={12}/> PACKAGING &amp; APPROVAL</span>
              <p className="packaging-lede">
                Copy is validated against real destination limits. Approval only produces a delivery package — no platform
                account is connected, so nothing is posted automatically.
              </p>
              <div className="destination-tabs">
                {packaging.map(item => (
                  <button
                    key={item.destination}
                    className={"source-tab" + (destination === item.destination ? " active" : "")}
                    onClick={() => setDestination(item.destination)}
                  >
                    {item.destination_label}
                    {item.approved && <Check size={12}/>}
                  </button>
                ))}
              </div>
              <label>Title
                <input value={draft.title} maxLength={300} onChange={e => setDraft({ ...draft, title: e.target.value })}/>
              </label>
              <label>Description
                <textarea rows={3} value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })}/>
              </label>
              <label>Hashtags
                <input placeholder="startup, founder, behindthescenes" value={draft.hashtags} onChange={e => setDraft({ ...draft, hashtags: e.target.value })}/>
              </label>
              {activePackaging && (
                <div className="packaging-feedback">
                  <span className="counter">
                    {activePackaging.validation.counts.title}/{activePackaging.validation.counts.title_max} title ·{" "}
                    {activePackaging.validation.counts.hashtags}/{activePackaging.validation.counts.hashtag_max} hashtags
                  </span>
                  {activePackaging.validation.errors.map(message => <span className="field-error" key={message}>{message}</span>)}
                  {activePackaging.validation.warnings.map(message => <span className="field-warning" key={message}>{message}</span>)}
                  {!activePackaging.approval_gate.allowed && activePackaging.approval_gate.blockers.map(message => (
                    <span className="field-error" key={message}>{message}</span>
                  ))}
                </div>
              )}
              <div className="approval-row">
                <button className="button-secondary" onClick={() => void savePackaging()} disabled={packagingBusy}>Save packaging</button>
                {activePackaging?.approved
                  ? <button className="button-secondary" onClick={() => void toggleApproval(false)} disabled={packagingBusy}>Withdraw approval</button>
                  : <button className="button-primary" onClick={() => void toggleApproval(true)} disabled={packagingBusy || !activePackaging?.approval_gate.allowed}>
                      <Check size={14}/> Approve for delivery
                    </button>}
              </div>
              {packagingNotice && <p className="notice">{packagingNotice}</p>}
            </div>
          </section>
        </div>
      : job?.status === "cancelled"
        ? <div className="empty-panel"><div className="empty-icon"><Ban size={23}/></div><h3>This job was cancelled</h3><p>Start a new project from the clip studio to analyse another recording.</p></div>
        : job?.status === "completed"
          ? <div className="empty-panel"><div className="empty-icon"><Video size={23}/></div><h3>No clip candidates were returned</h3><p>Try a longer source or adjust clip duration settings.</p></div>
          : <div className="empty-panel"><div className="empty-icon"><RefreshCw size={23}/></div><h3>Preparing your clip review</h3><p>Keep this page open. The worker will update this project as each processing stage completes.</p></div>}
  </div>;
}
