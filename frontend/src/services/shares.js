import apiClient from "../lib/apiClient";

// Compartilhamentos de uma tarefa (rotas aninhadas, exclusivas do proprietário).
// A resposta expõe apenas id, user_email, permission e created_at.

export async function listShares(taskId) {
  const { data } = await apiClient.get(`/tasks/${taskId}/shares/?page_size=100`);
  return data.results;
}

// Compartilha por e-mail de uma conta existente. permission: "view" | "edit".
export async function addShare(taskId, { email, permission }) {
  const { data } = await apiClient.post(`/tasks/${taskId}/shares/`, { email, permission });
  return data;
}

export async function updateShare(taskId, shareId, { permission }) {
  const { data } = await apiClient.patch(`/tasks/${taskId}/shares/${shareId}/`, { permission });
  return data;
}

export async function deleteShare(taskId, shareId) {
  await apiClient.delete(`/tasks/${taskId}/shares/${shareId}/`);
}
