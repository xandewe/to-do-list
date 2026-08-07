import axios from "axios";

import { API_ROOT } from "../lib/apiClient";

// O health check é uma rota de infraestrutura, fora do versionamento /api/v1/
// e sem autenticação. Por isso usa axios direto (não o apiClient com Bearer).
export async function getHealth() {
  const { data } = await axios.get(`${API_ROOT}/api/health/`);
  return data; // { api: "online", database: "online" }
}
