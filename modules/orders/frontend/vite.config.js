import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// FastAPI backend (main.py) runs on :8000 — proxy /api (and the warehouse/transport UI) to it in dev.
// Port 5174 so it can run next to the finance frontend (5173).
// `npm run build` -> dist/, served by FastAPI at /orders/ (same origin, shared login token).
const BACKEND = "http://127.0.0.1:8000";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? "/orders/" : "/",
  server: {
    port: 5174,
    proxy: { "/api": BACKEND, "/erp-ui": BACKEND, "/erp_frontend": BACKEND, "/login": BACKEND },
  },
}));
