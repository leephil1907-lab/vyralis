import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  AlertTriangle, ArrowUpRight, Check, Copy, Link2, Plug, RefreshCw,
  ShieldCheck, Unplug, XCircle,
} from "lucide-react";
import { api, type ConnectedAccount, type ConnectionProvider } from "../lib/api";
import { PlatformMark } from "../components/PlatformMark";

const METRIC_LABELS: Record<string, string> = {
  subscribers: "Subscribers",
  views: "Channel views",
  videos: "Videos",
  followers: "Followers",
  following: "Following",
  likes: "Likes",
  media: "Posts",
  posts: "Posts",
};

const number = (value: number | null | undefined) =>
  value === null || value === undefined ? "—" : value.toLocaleString();

function syncedAgo(value?: string | null) {
  if (!value) return "never synced";
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return "never synced";
  const minutes = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (minutes < 1) return "synced just now";
  if (minutes < 60) return `synced ${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `synced ${hours} h ago`;
  return `synced ${new Date(value).toLocaleDateString()}`;
}

export default function ConnectionsPage() {
  const [params, setParams] = useSearchParams();
  const [providers, setProviders] = useState<ConnectionProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [copied, setCopied] = useState("");

  const connected = params.get("connected") || "";
  const callbackError = params.get("error") || "";

  const load = useCallback(async () => {
    try {
      const data = await api.connections();
      setProviders(data.providers);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load connections.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!connected && !callbackError) return;
    if (connected) {
      const label = providers.find(p => p.key === connected)?.label || connected;
      setNotice(`${label} connected. Live account details were read from the platform.`);
    }
    if (callbackError) setError(callbackError);
    const next = new URLSearchParams(params);
    next.delete("connected");
    next.delete("error");
    next.delete("platform");
    setParams(next, { replace: true });
    // Only react to the redirect parameters; providers fill in asynchronously.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected, callbackError]);

  async function connect(provider: ConnectionProvider) {
    setBusy(provider.key); setError(""); setNotice("");
    try {
      const result = await api.startConnection(provider.key);
      window.location.assign(result.authorize_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : `Could not start the ${provider.label} connection.`);
      setBusy("");
    }
  }

  async function sync(account: ConnectedAccount) {
    setBusy(account.id); setError(""); setNotice("");
    try {
      const updated = await api.syncConnection(account.id);
      setProviders(old => old.map(provider => ({
        ...provider,
        accounts: provider.accounts.map(item => (item.id === updated.id ? updated : item)),
      })));
      setNotice(`${updated.display_name}: metrics refreshed from ${updated.platform}.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not refresh this account.");
    } finally {
      setBusy("");
    }
  }

  async function disconnect(account: ConnectedAccount) {
    if (!window.confirm(`Disconnect ${account.display_name}? You can reconnect it later.`)) return;
    setBusy(account.id); setError(""); setNotice("");
    try {
      await api.disconnectConnection(account.id);
      setProviders(old => old.map(provider => ({
        ...provider,
        accounts: provider.accounts.filter(item => item.id !== account.id),
      })));
      setNotice(`${account.display_name} disconnected. Tokens were deleted from this server.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not disconnect this account.");
    } finally {
      setBusy("");
    }
  }

  async function copy(value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(value);
      window.setTimeout(() => setCopied(""), 1600);
    } catch {
      setError("Your browser blocked clipboard access. Select the URL and copy it manually.");
    }
  }

  const configuredCount = useMemo(() => providers.filter(p => p.configured).length, [providers]);
  const accountCount = useMemo(() => providers.reduce((n, p) => n + p.accounts.length, 0), [providers]);

  return <div className="page-content">
    <div className="page-heading">
      <div>
        <div className="eyebrow"><Plug size={13}/> CONNECTIONS</div>
        <h1>Connect your <em>channels.</em></h1>
        <p>
          Authorise a platform and VYRALIS reads the account and its current public numbers straight from the
          provider API. Tokens are encrypted on this server, and disconnecting deletes them.
        </p>
      </div>
      <button className="button-secondary" onClick={() => void load()}><RefreshCw size={15}/> Refresh</button>
    </div>

    {notice && <div className="notice"><Check size={15}/> {notice}</div>}
    {error && <div className="notice error"><AlertTriangle size={15}/> {error}</div>}

    <div className="connection-summary">
      <span><b>{accountCount}</b> connected account{accountCount === 1 ? "" : "s"}</span>
      <span><b>{configuredCount}</b> of {providers.length || 4} platforms configured on this server</span>
      <span className="connection-hint">Posts are still not published automatically — see the note below.</span>
    </div>

    {loading
      ? <div className="connection-grid">{Array.from({ length: 4 }).map((_, index) => <div className="glass connection-card skeleton" key={index}/>)}</div>
      : <div className="connection-grid">
          {providers.map(provider => <section className="glass connection-card" key={provider.key}>
            <div className="connection-head">
              <PlatformMark platform={provider.key} px={42}/>
              <div>
                <h3>{provider.label}</h3>
                <span className={"connection-state " + (provider.configured ? (provider.accounts.length ? "connected" : "ready") : "unconfigured")}>
                  {!provider.configured ? "Not configured" : provider.accounts.length ? "Connected" : "Ready to connect"}
                </span>
              </div>
            </div>

            {provider.accounts.map(account => <div className="account-block" key={account.id}>
              <div className="account-row">
                {account.avatar_url
                  ? <img className="account-avatar" src={account.avatar_url} alt="" referrerPolicy="no-referrer"/>
                  : <span className="account-avatar fallback">{(account.display_name || "?").slice(0, 1).toUpperCase()}</span>}
                <div className="account-meta">
                  <b>{account.display_name}</b>
                  <small>{account.status === "error" ? "Last sync failed — reconnect or retry" : syncedAgo(account.metrics_synced_at)}</small>
                </div>
              </div>
              <div className="account-metrics">
                {Object.keys(account.metrics).length === 0
                  ? <span className="account-empty">The provider returned no public metrics for this account.</span>
                  : Object.entries(account.metrics).map(([key, value]) => <div key={key}>
                      <span>{METRIC_LABELS[key] || key}</span>
                      <b>{number(value)}</b>
                    </div>)}
              </div>
              <div className="account-actions">
                <button className="button-secondary small" disabled={busy === account.id} onClick={() => void sync(account)}>
                  <RefreshCw size={13}/> Refresh metrics
                </button>
                <button className="text-button danger" disabled={busy === account.id} onClick={() => void disconnect(account)}>
                  <Unplug size={13}/> Disconnect
                </button>
              </div>
            </div>)}

            {provider.configured
              ? <button className="button-primary" disabled={busy === provider.key} onClick={() => void connect(provider)}>
                  <Link2 size={15}/> {busy === provider.key ? "Opening provider…" : provider.accounts.length ? `Connect another ${provider.label} account` : `Connect ${provider.label}`}
                  <ArrowUpRight size={14}/>
                </button>
              : <div className="connection-setup">
                  <p>{provider.setup_note}</p>
                  <div className="setup-line">
                    <code>{provider.client_id_env}</code>
                    <code>{provider.client_secret_env}</code>
                  </div>
                  <div className="setup-line">
                    <span>Redirect URI</span>
                    <code className="setup-copy" onClick={() => void copy(provider.callback_url)}>
                      {provider.callback_url}
                      {copied === provider.callback_url ? <Check size={12}/> : <Copy size={12}/>}
                    </code>
                  </div>
                </div>}

            <div className="connection-scopes">
              <ShieldCheck size={12}/>
              <span>{provider.scopes.length} scopes: {provider.scopes.join(" · ")}</span>
            </div>
          </section>)}
        </div>}

    <section className="glass connection-note">
      <div>
        <span className="micro-label"><ShieldCheck size={12}/> WHAT A CONNECTION DOES AND DOES NOT DO</span>
        <p>
          A connection proves which account you control and lets the server read that account's public numbers.
          Publishing a rendered clip still requires per-platform app approval (YouTube audit, TikTok content-posting
          review, Instagram business verification). Until an adapter for a platform is finished and approved, the
          delivery flow stays a validated download — this page never claims a post was made.
        </p>
        <p className="connection-warning">
          <XCircle size={13}/> Tokens are stored encrypted with a key from <code>VYRALIS_AUTH_SECRET</code> (or a
          local 0600 key file). Set that variable in production so the key is not kept beside the data.
        </p>
      </div>
    </section>
  </div>;
}
