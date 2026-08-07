// Extrai uma mensagem legível (em pt-br) de um erro do Axios contra a API.
//
// A API responde de duas formas:
//  - Erros de validação por campo: { "email": ["..."], "password": ["..."] }
//  - Erros gerais: { "detail": "...", "code": "..." }
// Sem resposta do servidor, cai numa mensagem de rede.

export function getApiErrorMessage(error, fallback = "Ocorreu um erro. Tente novamente.") {
  const data = error?.response?.data;

  if (!error?.response) {
    return "Não foi possível conectar à API. Verifique se o servidor está no ar.";
  }

  if (!data) {
    return fallback;
  }

  if (typeof data === "string") {
    return data;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  // Primeiro erro de campo encontrado (string ou lista de strings).
  for (const value of Object.values(data)) {
    if (Array.isArray(value) && value.length > 0) {
      return String(value[0]);
    }
    if (typeof value === "string") {
      return value;
    }
  }

  return fallback;
}
