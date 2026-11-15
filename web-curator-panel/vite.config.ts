import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em desenvolvimento, /api e /fotos são repassados para o backend na porta 8000.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/fotos": "http://localhost:8000",
    },
  },
});
