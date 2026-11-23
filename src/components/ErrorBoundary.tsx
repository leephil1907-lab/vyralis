import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

type Props = { children: ReactNode };
type State = { error: Error | null };

/**
 * Last-resort boundary so a render error shows a readable panel instead of a blank page.
 * It intentionally does not swallow the error: the message is shown for reporting.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Keep the trace in the console for the person debugging the deployment.
    console.error("VYRALIS render error:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="page-content">
        <div className="glass" style={{ padding: 28, maxWidth: 640, margin: "40px auto" }}>
          <div className="eyebrow"><AlertTriangle size={13} /> SOMETHING BROKE</div>
          <h1 style={{ font: "600 26px 'Space Grotesk'", margin: "12px 0 8px" }}>This screen hit an error.</h1>
          <p style={{ fontSize: 11, lineHeight: 1.7, color: "#94a0ba" }}>
            The rest of the studio is still running. Reload this screen, or head back to the dashboard. Nothing was
            published or deleted by this error.
          </p>
          <pre style={{
            marginTop: 14, padding: 12, borderRadius: 10, overflowX: "auto",
            background: "rgba(0,0,0,.35)", border: "1px solid rgba(255,120,120,.2)",
            color: "#ffc9c9", fontSize: 10,
          }}>{this.state.error.message}</pre>
          <div style={{ display: "flex", gap: 10, marginTop: 16, flexWrap: "wrap" }}>
            <button className="button-primary" onClick={() => window.location.reload()}>
              <RefreshCw size={15} /> Reload
            </button>
            <button className="button-secondary" onClick={() => window.location.assign("/studio")}>
              Back to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }
}
