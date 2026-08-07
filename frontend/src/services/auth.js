import apiClient from "../lib/apiClient";
import { getRefreshToken } from "../lib/tokenStorage";

// Cadastro público. Não emite tokens (o login é feito em separado).
// Aceita somente email, password, first_name, last_name.
export async function register({ email, password, firstName, lastName }) {
  const { data } = await apiClient.post("/users/", {
    email,
    password,
    first_name: firstName,
    last_name: lastName,
  });
  return data; // { id, email, first_name, last_name }
}

// Login: troca email+senha por { access, refresh }.
export async function login({ email, password }) {
  const { data } = await apiClient.post("/auth/token/", { email, password });
  return data; // { access, refresh }
}

// Dados públicos do usuário autenticado.
export async function getMe() {
  const { data } = await apiClient.get("/users/me/");
  return data; // { id, email, first_name, last_name }
}

// Logout: revoga o refresh atual (blacklist). Não invalida access já emitidos,
// que expiram sozinhos em 15 min. Silencioso: se não houver refresh ou a
// revogação falhar, o cliente segue limpando o estado local mesmo assim.
export async function logout() {
  const refresh = getRefreshToken();
  if (!refresh) {
    return;
  }
  try {
    await apiClient.post("/auth/token/blacklist/", { refresh });
  } catch {
    // Refresh já expirado/inválido: nada a fazer, o estado local é limpo pelo
    // chamador de qualquer forma.
  }
}
