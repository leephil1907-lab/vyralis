import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Read the target from the environment without pulling in Node typings.
const apiTarget = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env?.VYRALIS_API_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // The sandbox preview proxies requests through a generated *.e2b.app host,
    // so the dev server must not reject unknown Host headers.
    allowedHosts: true,
    // Keep the browser on one origin: /api is proxied to the local FastAPI engine.
    proxy: { "/api": { target: apiTarget, changeOrigin: true } },
  },
  preview: { host: "0.0.0.0", port: 4173, allowedHosts: true, proxy: { "/api": { target: apiTarget, changeOrigin: true } } },
});
