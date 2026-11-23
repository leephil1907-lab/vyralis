const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Health = { status: string; version: string; capabilities: string[] };
export type MediaAsset = { id: string; filename: string; size: number; content_type: string; created_at: string; duration_seconds?: number | null };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`);
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
};