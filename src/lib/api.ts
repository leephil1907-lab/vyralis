const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Health = { status: string; version: string; capabilities: string[] };
export type MediaAsset = { id: string; filename: string; size: number; content_type: string; created_at: string; duration_seconds?: number | null };
export type Project = { id: string; title: string; status: string; job_id?: string; filename?: string; duration_seconds?: number; clip_count?: number };
export type ProcessingJob = { id: string; project_id: string; status: string; stage: string; progress: number; message: string; error?: string | null };
export type Clip = { id: string; project_id: string; rank: number; start_seconds: number; end_seconds: number; score: number; score_breakdown: Record<string,number>; reason: string; transcript: string; title: string; status: string; output_path?: string | null };

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
  ingestUrl: (url: string, rightsConfirmed: boolean) => request<Project>("/api/ingest/url", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, rights_confirmed: rightsConfirmed, clip_count: 8, min_duration: 15, max_duration: 60 })
  }),
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
  exportClip: (id: string) => request<{ job_id: string; status: string }>(`/api/clips/${id}/export`, { method: "POST" }),
  fileUrl: (path: string) => `${API_BASE}${path}`
};