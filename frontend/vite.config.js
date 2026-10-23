import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

// Modul bur uuriin frontend-iig modules/<modul>/frontend/src dotor bichne.
// Shell (ene app) tedgeeriig alias-aar import hiine: import("@finance/FinanceModule").
const mod = (name) => fileURLToPath(new URL(`../modules/${name}/frontend/src`, import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@finance": mod("finance"),
      "@orders": mod("orders"),
      "@masterdata": mod("masterdata"),
      "@warehouse": mod("warehouse"),
      "@transport": mod("transport"),
      "@routing": mod("routing"),
      "@notifications": mod("notifications"),
    },
    // modules/*/frontend dotor node_modules baihgui: react-iig shell-iin neg huvilbaraas avna.
    dedupe: ["react", "react-dom", "react/jsx-runtime"],
  },
  server: {
    port: 5173,
    fs: { allow: [".."] },
    proxy: { "/api": "http://localhost:8000" },
  },
});
