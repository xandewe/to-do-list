import apiClient from "../lib/apiClient";

// Tamanho de página usado na listagem (o backend aceita até 100).
export const PAGE_SIZE = 10;

function buildQuery({ page, status, category, pageSize }) {
  const params = new URLSearchParams();
  params.set("page", String(page || 1));
  params.set("page_size", String(pageSize || PAGE_SIZE));
  // status "all" => não filtra; valores inválidos são ignorados pela API.
  if (status && status !== "all") params.set("status", status);
  if (category) params.set("category", category);
  return `?${params.toString()}`;
}

// Lista tarefas acessíveis (próprias + compartilhadas), paginada e filtrável.
export async function listTasks({ page = 1, status = "all", category = "" } = {}) {
  const { data } = await apiClient.get(`/tasks/${buildQuery({ page, status, category })}`);
  return data; // { count, next, previous, results }
}

// Conta tarefas de um status (independente do filtro de categoria).
// page_size=1 minimiza o payload — só interessa o `count`.
export async function countTasks(status) {
  const params = new URLSearchParams({ page_size: "1" });
  if (status && status !== "all") params.set("status", status);
  const { data } = await apiClient.get(`/tasks/?${params.toString()}`);
  return data.count;
}

export async function getTask(id) {
  const { data } = await apiClient.get(`/tasks/${id}/`);
  return data;
}

export async function createTask(payload) {
  const { data } = await apiClient.post("/tasks/", payload);
  return data;
}

export async function updateTask(id, payload) {
  const { data } = await apiClient.patch(`/tasks/${id}/`, payload);
  return data;
}

export async function deleteTask(id) {
  await apiClient.delete(`/tasks/${id}/`);
}
