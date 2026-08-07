import axios from "axios";

import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "./tokenStorage";

// Origem base da API. Sem barra final; os services montam os caminhos a partir
// daqui. O health check vive fora do /api/v1 e é tratado no service dele.
//
// - undefined (sem env): default de dev, chama http://localhost:8000 direto.
// - "" (build Docker): caminhos relativos (/api/v1, /api/health), servidos pelo
//   reverse proxy do nginx na mesma origem — sem CORS.
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
const API_BASE_URL = rawBaseUrl === undefined ? "http://localhost:8000" : rawBaseUrl;

export const API_ROOT = API_BASE_URL;
const API_V1 = `${API_BASE_URL}/api/v1`;

// Instância principal, usada por todos os services funcionais.
const apiClient = axios.create({
  baseURL: API_V1,
  headers: { "Content-Type": "application/json" },
});

// Instância "crua" só para renovar o token: NÃO tem interceptor, para não cair
// em loop de refresh quando o próprio refresh retornar 401.
const refreshClient = axios.create({
  baseURL: API_V1,
  headers: { "Content-Type": "application/json" },
});

// --- Callback de "sessão expirou" -----------------------------------------
// A camada de UI (AuthContext, na Task 19) registra aqui o que fazer quando o
// refresh falha em definitivo — tipicamente limpar o estado e mandar pro login.
// Mantido desacoplado para o apiClient não depender do React nem do router.
let onSessionExpired = null;

export function setOnSessionExpired(handler) {
  onSessionExpired = handler;
}

function handleSessionExpired() {
  clearTokens();
  if (onSessionExpired) {
    onSessionExpired();
  }
}

// --- Request interceptor: injeta o Bearer ---------------------------------
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Refresh com fila para 401 concorrentes -------------------------------
// Se várias requisições tomarem 401 ao mesmo tempo, disparamos UM único
// refresh e enfileiramos as demais até ele resolver.
let isRefreshing = false;
let pendingQueue = [];

function flushQueue(error, newAccessToken) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(newAccessToken);
    }
  });
  pendingQueue = [];
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error("no_refresh_token");
  }
  // A API rotaciona: devolve novos access E refresh, e blacklista o antigo.
  const { data } = await refreshClient.post("/auth/token/refresh/", { refresh });
  setTokens({ access: data.access, refresh: data.refresh });
  return data.access;
}

// --- Response interceptor: 401 -> refresh -> retry ------------------------
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const code = error.response?.data?.code;

    const isAuthError = status === 401 && code === "token_not_valid";

    // Só tenta refresh uma vez por request, e nunca no próprio refresh.
    if (!isAuthError || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    // Sem refresh guardado: nem tenta, encerra a sessão.
    if (!getRefreshToken()) {
      handleSessionExpired();
      return Promise.reject(error);
    }

    // Um refresh já está em andamento: entra na fila e espera.
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      })
        .then((newAccessToken) => {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        })
        .catch((queueError) => Promise.reject(queueError));
    }

    isRefreshing = true;
    try {
      const newAccessToken = await refreshAccessToken();
      flushQueue(null, newAccessToken);
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      flushQueue(refreshError, null);
      handleSessionExpired();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
