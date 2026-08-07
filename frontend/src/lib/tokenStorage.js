// Persistência dos tokens JWT no localStorage.
//
// Decisão consciente do MVP: localStorage é simples e não exige mudança no
// backend, ao custo de exposição a XSS. Se no futuro migrarmos para refresh em
// cookie HttpOnly, apenas este módulo (e o refresh do apiClient) muda.
//
// A API rotaciona o refresh a cada renovação (BLACKLIST_AFTER_ROTATION), então
// sempre gravamos o par {access, refresh} de uma vez em setTokens().

const ACCESS_KEY = "todo_ah_access";
const REFRESH_KEY = "todo_ah_refresh";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens({ access, refresh }) {
  if (access) {
    localStorage.setItem(ACCESS_KEY, access);
  }
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh);
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function hasTokens() {
  return Boolean(getAccessToken() && getRefreshToken());
}
