import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server na porta 5173, que é a origem já liberada no CORS do backend.
// No dev, o SPA fala com a API direto (VITE_API_BASE_URL=http://localhost:8000).
//
// `preview` é usado na imagem Docker: o próprio Vite serve o build e faz proxy
// de /api para o serviço `api` do compose (mesma origem, sem CORS). No build
// Docker VITE_API_BASE_URL fica vazio, então o SPA usa caminhos relativos.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  preview: {
    host: true,
    port: 8080,
    proxy: {
      // changeOrigin: false preserva o Host do cliente (localhost), que o
      // Django já aceita em ALLOWED_HOSTS. Sem isso, o proxy encaminharia
      // Host: api:8000 e a API responderia DisallowedHost.
      "/api": {
        target: "http://api:8000",
        changeOrigin: false,
      },
    },
  },
});
