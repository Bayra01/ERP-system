import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// FastAPI backend (main.py) runs on :8000 — proxy /api to it in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
