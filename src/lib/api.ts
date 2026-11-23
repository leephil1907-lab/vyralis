const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Health = { status: string; version: string; capabilities: string[] };
export type MediaAsset = { id: string; filename: string; size: number; content_type: string; created_at: string; duration_seconds?: number | null };
export type Project = { id: string; title: string; status: string; job_id?: string; filename?: string; duration_seconds?: number; clip_count?: number };
export type ProcessingJob = { id: string; project_id: string; status: string; stage: string; progress: number; message: string; error?: string | null };
export type Clip = { id: string; project_id: string; rank: number; start_seconds: number; end_seconds: number; score: number; score_breakdown: Record<string,number>; reason: string; transcript: string; title: string; status: string; output_path?: string | null };

export type ExportPreset = "9:16" | "1:1" | "16:9";
export type PresetInfo = { preset: ExportPreset; label: string; width: number; height: number; use: string };
export type QualityCheck = { id: string; label: string; status: "pass" | "warn" | "fail"; detail: string };
export type QualityReport = { status: "pass" | "warn" | "fail"; summary: string; checks: QualityCheck[]; metrics: Record<string, number | null> };
export type ClipExport = { id: string; clip_id: string; preset: ExportPreset; status: string; job_id?: string | null; width?: number | null; height?: number | null; duration_seconds?: number | null; quality_report?: QualityReport | null; download_url?: string | null; error?: string | null; created_at: string };
export type Packaging = {
  clip_id: string; clip_title: string; project_id: string; destination: string; destination_label: string;
  title: string; description: string; hashtags: string[]; approved: boolean; approved_at?: string | null;
  eligible: boolean;
  validation: { valid: boolean; errors: string[]; warnings: string[]; counts: { title: number; description: number; hashtags: number; title_max: number; description_max: number; hashtag_max: number } };
  approval_gate: { allowed: boolean; blockers: string[] };
  export: { id: string; preset: string; quality_status: string | null; quality_summary: string | null; download_url: string } | null;
};
export type PublishPackages = { packages: Packaging[]; note: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try { const body = await response.json(); message = body.detail || message; } catch { /* non-JSON error */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  assets: () => request<MediaAsset[]>("/api/assets"),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<MediaAsset>("/api/assets", { method: "POST", body });
  },
  createProject: (assetId: string) => request<Project>("/api/projects", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ asset_id: assetId, clip_count: 8, min_duration: 15, max_duration: 60 })
  }),
  job: (id: string) => request<ProcessingJob>(`/api/jobs/${id}`),
  projects: () => request<Project[]>("/api/projects"),
  clips: (projectId: string) => request<Clip[]>(`/api/projects/${projectId}/clips`),
  editClip: (clip: Clip) => request<Clip>(`/api/clips/${clip.id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start_seconds: clip.start_seconds, end_seconds: clip.end_seconds, title: clip.title })
  }),
  exportPresets: () => request<{ presets: PresetInfo[] }>("/api/export-presets"),
  exportClip: (id: string, preset: ExportPreset = "9:16") => request<{ clip_id: string; export_id: string; job_id: string; preset: string; status: string; idempotent?: boolean }>(`/api/clips/${id}/export`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ preset }) }),
  clipExports: (id: string) => request<ClipExport[]>(`/api/clips/${id}/exports`),
  packaging: (id: string) => request<Packaging[]>(`/api/clips/${id}/packaging`),
  savePackaging: (id: string, payload: { destination: string; title: string; description: string; hashtags: string[] }) => request<Packaging>(`/api/clips/${id}/packaging`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  approvePackaging: (id: string, destination: string, approved: boolean) => request<Packaging>(`/api/clips/${id}/packaging/approval`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ destination, approved }) }),
  publishPackages: () => request<PublishPackages>("/api/publish/packages"),
  cancelJob: (id: string) => request<{ id: string; status: string }>(`/api/jobs/${id}/cancel`, { method: "POST" }),
  fileUrl: (path: string) => `${API_BASE}${path}`
};