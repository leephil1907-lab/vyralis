import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight, Check, Download, Info, Link2, Package, RefreshCw, ShieldCheck, Sparkles,
} from "lucide-react";
import { api, type PublishPackages } from "../lib/api";

export default function PublishPage() {
  const [data, setData] = useState<PublishPackages | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setData(await api.publishPackages()); }
    catch (e) { setError(e instanceof Error ? e.message : "The local engine did not respond."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const packages = data?.packages ?? [];
  const eligible = packages.filter(item => item.eligible);
  const blocked = packages.filter(item => !item.eligible);

  return <div className="page-content">
    <div className="page-heading">
      <div>
        <div className="eyebrow"><Sparkles size={13}/> PUBLISH STUDIO</div>
        <h1>Approved <em>delivery</em> packages.</h1>
        <p>Clips you approved, with validated renders and platform-ready copy. This build produces files for manual upload — no platform account is connected, so nothing is posted for you.</p>
      </div>
      <button className="button-secondary" onClick={() => void load()} disabled={loading}><RefreshCw size={15}/> Refresh</button>
    </div>

    <div className="publish-summary">
      <section className="glass metric-card"><span>APPROVED PACKAGES <Package size={15}/></span><strong>{eligible.length}</strong><small>Ready for manual upload</small></section>
      <section className="glass metric-card"><span>BLOCKED <ShieldCheck size={15}/></span><strong className="metric-status">{blocked.length}</strong><small>Missing a passing render or valid copy</small></section>
      <section className="glass metric-card"><span>PLATFORM CONNECTIONS <Link2 size={15}/></span><strong className="metric-status">None</strong><small>OAuth adapters are not built yet</small></section>
      <section className="glass metric-card"><span>VALIDATED RENDERS <Check size={15}/></span><strong>{packages.filter(item => item.export).length}</strong><small>Passed automated quality inspection</small></section>
    </div>

    {error && <div className="notice"><Info size={15}/> {error}</div>}

    {loading
      ? <div className="empty-panel"><div className="empty-icon"><RefreshCw size={23}/></div><h3>Reading approved packages</h3><p>Loading the packages recorded in this workspace.</p></div>
      : packages.length === 0
        ? <div className="empty-panel">
            <div className="empty-icon"><Package size={23}/></div>
            <h3>No approved packages yet</h3>
            <p>Render a clip, review its quality report, fill in the packaging copy and approve it in Clip Review. Approved packages appear here with their validated file.</p>
            <Link className="button-primary" to="/create">Start with a clip <ArrowUpRight size={14}/></Link>
          </div>
        : <>
            <div className="section-title"><div><span className="micro-label">READY TO UPLOAD</span><h2>Approved packages</h2></div><span className="editor-pill">{eligible.length} eligible</span></div>
            <div className="package-list">
              {packages.map(item => (
                <section className="glass package-card" key={`${item.clip_id}-${item.destination}`}>
                  <div>
                    <span className="micro-label">{item.destination_label.toUpperCase()}</span>
                    <h3>{item.title || item.clip_title}</h3>
                    <p style={{ margin: 0, fontSize: 10, lineHeight: 1.6, color: "#8d98b3" }}>
                      {item.description ? item.description.slice(0, 160) + (item.description.length > 160 ? "…" : "") : "No description yet."}
                    </p>
                    <div className="package-meta">
                      <span><Package size={11}/> {item.export?.preset ?? "no render"}</span>
                      <span><ShieldCheck size={11}/> quality: {item.export?.quality_status ?? "not rendered"}</span>
                      <span><Check size={11}/> approved {item.approved_at ? new Date(item.approved_at).toLocaleString() : "yes"}</span>
                    </div>
                    {item.hashtags.length > 0 && <div className="package-tags">{item.hashtags.map(tag => <span key={tag}>#{tag}</span>)}</div>}
                    {!item.eligible && item.approval_gate.blockers.length > 0 && (
                      <p style={{ margin: "10px 0 0", fontSize: 10, color: "#ff9b9b" }}>{item.approval_gate.blockers.join(" ")}</p>
                    )}
                  </div>
                  <div className="package-actions">
                    {item.export?.download_url
                      ? <a className="button-primary" href={api.fileUrl(item.export.download_url)}><Download size={14}/> Download MP4</a>
                      : <span className="feature-state">NO VALID RENDER</span>}
                  </div>
                </section>
              ))}
            </div>

            <div className="integration-note">
              <ShieldCheck size={16}/>
              <div>
                <b>Why there is no “Publish now” button</b>
                <p>{data?.note} Connecting YouTube, TikTok or Instagram requires OAuth apps, approved scopes and delivery receipts; those adapters are planned, not simulated. Every package here is a file plus validated copy that you upload yourself.</p>
              </div>
            </div>
          </>}
  </div>;
}
