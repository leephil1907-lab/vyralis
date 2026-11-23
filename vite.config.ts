import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // The sandbox preview proxies requests through a generated *.e2b.app host,
    // so the dev server must not reject unknown Host headers.
    allowedHosts: true,
  },
  preview: { host: "0.0.0.0", port: 4173, allowedHosts: true },
});
