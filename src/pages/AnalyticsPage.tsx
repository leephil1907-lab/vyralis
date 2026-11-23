import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, BarChart3, CheckCircle2, Clapperboard, Gauge,
  HardDrive, Layers3, RefreshCw,
} from "lucide-react";
import { api, type StudioMetrics } from "../lib/api";
import { PlatformMark } from "../components/PlatformMark";

const bytes = (n: number) =>
  n > 1024 ** 3 ? `${(n / 1024 ** 3).toFixed(1)} GB`
    : n > 1024 ** 2 ? `${(n / 1024 ** 2).toFixed(1)} MB`
    : `${(n / 1024).toFixed(0)} KB`;

const metricLabels: Record<string, string> = {
  subscribers: "Subscribers", views: "Views", videos: "Videos", followers: "Followers",
  following: "Following", likes: "Likes", media: "Posts", posts: "Posts",
};

const ago = (value?: string | null) => {
  if (!value) return "not synced yet";
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return "not synced yet";
  const minutes = Math.round((Date.now() - then) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `${hours} h ago` : new Date(value).toLocaleDateString();
};

export default function AnalyticsPage() {
  const [data, setData] = useState<StudioMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.metrics());
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not read studio metrics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const studio = data?.studio;
  const quality = studio?.quality ?? { pass: 0, warn: 0, fail: 0 };
  const reports = quality.pass + quality.warn + quality.fail;
  const passRate = reports ? Math.round((quality.pass / reports) * 100) : null;

  const cards = [
    {
      label: "RANKED CLIPS", icon: Clapperboard,
      value: studio ? studio.clips.toLocaleString() : null,
      detail: studio && studio.clips > 0 ? "Ranked candidates stored in this workspace" : "No clips ranked yet",
    },
    {
      label: "PROJECTS", icon: Layers3,
      value: studio ? studio.projects.toLocaleString() : null,
      detail: studio && studio.projects > 0 ? `${studio.assets.toLocaleString()} source asset(s) · ${bytes(studio.storage_bytes)}` : "Nothing imported yet",
    },
    {
      label: "READY EXPORTS", icon: CheckCircle2,
      value: studio ? studio.exports.ready.toLocaleString() : null,
      detail: studio
        ? `${studio.exports.total} render(s) total · ${studio.exports.failed} failed · ${studio.exports.active} running`
        : "No renders yet",
    },
    {
      label: "QUALITY PASS RATE", icon: Gauge,
      value: passRate === null ? null : `${passRate}%`,
      detail: reports ? `${quality.pass} pass · ${quality.warn} warn · ${quality.fail} fail` : "Measured from rendered files only",
    },
  ];

  return <div className="page-content">
    <div className="page-heading">
      <div>
        <div className="eyebrow"><BarChart3 size={13}/> PERFORMANCE STUDIO</div>
        <h1>Know what’s <em>actually happening.</em></h1>
        <p>
          Studio numbers are counted from this workspace's database. Channel numbers come from the platform APIs of
          accounts you connected — never from samples.
        </p>
      </div>
      <button className="button-secondary" onClick={() => void load()} disabled={loading}>
        <RefreshCw size={15}/> {loading ? "Reading…" : "Refresh"}
      </button>
    </div>

    {error && <div className="notice error"><AlertTriangle size={15}/> {error}</div>}

    <div className="analytics-grid">
      {cards.map(card => <section className="glass metric-card" key={card.label}>
        <span>{card.label}<card.icon size={15}/></span>
        {card.value === null
          ? <strong className="metric-placeholder">—</strong>
          : <strong className="metric-real">{card.value}</strong>}
        <small>{card.detail}</small>
      </section>)}
    </div>

    <div className="dashboard-grid" style={{ marginTop: 14 }}>
      <section className="glass chart-placeholder">
        <div className="card-top">
          <div>
            <span className="micro-label">RENDER QUALITY</span>
            <h3>Every export is measured</h3>
          </div>
          <Activity size={17}/>
        </div>
        {reports === 0
          ? <div className="empty-panel" style={{ minHeight: 150 }}>
              <div className="empty-icon"><Gauge size={22}/></div>
              <h3>No renders measured yet</h3>
              <p>Render a clip and its duration, frame size, black frames, frozen frames and loudness appear here.</p>
            </div>
          : <div className="quality-bars">
              {(["pass", "warn", "fail"] as const).map(key => <div className={"quality-bar " + key} key={key}>
                <span>{key.toUpperCase()}</span>
                <div className="track"><div className="fill" style={{ width: `${Math.round((quality[key] / reports) * 100)}%` }}/></div>
                <b>{quality[key]}</b>
              </div>)}
            </div>}
        <p className="quality-note" style={{ marginTop: 14 }}>
          Counts read the stored report on each export. A failed inspection deletes the file and blocks download, so
          these numbers cannot be prettied up after the fact.
        </p>
      </section>

      <section className="glass chart-placeholder">
        <div className="card-top">
          <div>
            <span className="micro-label">CONNECTED CHANNELS</span>
            <h3>Live platform numbers</h3>
          </div>
          <HardDrive size={17}/>
        </div>
        {!data || data.accounts.length === 0
          ? <div className="empty-panel" style={{ minHeight: 150 }}>
              <div className="empty-icon"><Activity size={22}/></div>
              <h3>No channel connected</h3>
              <p>Connect YouTube, TikTok, Instagram or X to read your real subscriber and follower counts.</p>
              <Link className="button-primary" to="/connections">Open connections</Link>
            </div>
          : <div className="analytics-accounts">
              {data.accounts.map(account => <div className="analytics-account" key={account.id}>
                <PlatformMark platform={account.platform} px={26}/>
                <div>
                  <b>{account.display_name}</b>
                  <small style={{ display: "block", fontSize: 9, color: "#8b96b1", marginTop: 2 }}>
                    {account.status === "error" ? "last sync failed" : `updated ${ago(account.metrics_synced_at)}`}
                  </small>
                </div>
                <div className="account-metrics">
                  {Object.keys(account.metrics).length === 0
                    ? <span className="account-empty">No public metrics returned</span>
                    : Object.entries(account.metrics).map(([key, value]) => <div key={key}>
                        <span>{metricLabels[key] || key}</span>
                        <b>{value === null ? "—" : value.toLocaleString()}</b>
                      </div>)}
                </div>
              </div>)}
            </div>}
        <p className="quality-note" style={{ marginTop: 14 }}>
          Nothing here is a projection. Views, retention and per-post performance need published posts and platform
          analytics scopes, so those charts stay empty until a post actually exists.
        </p>
      </section>
    </div>
  </div>;
}
