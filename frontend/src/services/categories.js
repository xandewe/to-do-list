import apiClient from "../lib/apiClient";

// Lista todas as categorias do usuário, seguindo a paginação do DRF até o fim.
// A listagem é ordenada por nome no backend. Como categorias tendem a ser
// poucas, buscar todas as páginas mantém o grid simples (sem controle de página).
export async function listCategories() {
  const results = [];
  let url = "/categories/?page_size=100";
  while (url) {
    const { data } = await apiClient.get(url);
    results.push(...data.results);
    // `next` é uma URL absoluta; o apiClient tem baseURL, então passamos só o
    // caminho relativo a /api/v1.
    url = data.next ? data.next.replace(/^.*\/api\/v1/, "") : null;
  }
  return results;
}

// Cria uma categoria. `color` deve ser vazio ou hexadecimal #RRGGBB.
export async function createCategory({ name, description, color }) {
  const { data } = await apiClient.post("/categories/", { name, description, color });
  return data;
}

export async function updateCategory(id, { name, description, color }) {
  const { data } = await apiClient.patch(`/categories/${id}/`, { name, description, color });
  return data;
}

export async function deleteCategory(id) {
  await apiClient.delete(`/categories/${id}/`);
}
