import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server na porta 5173, que é a origem já liberada no CORS do backend
// (DJANGO_CORS_ALLOWED_ORIGINS). O frontend fala com a API direto, sem proxy.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
