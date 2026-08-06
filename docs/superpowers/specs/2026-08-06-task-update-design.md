# Task 08 — Atualização parcial de tarefas

## Objetivo

Adicionar `PATCH /api/v1/tasks/{task_id}/` para atualização parcial de tarefas acessíveis, preservando os limites de propriedade e compartilhamento definidos na Task 7.

## Design aprovado

- Reutilizar `TaskDetailView`, `TaskSerializer` e `get_accessible_tasks`.
- Adicionar somente `TaskDetailView.patch`; nenhuma URL, model, migration, service, repository ou permission class nova.
- O owner pode atualizar `category_id`, `title`, `description`, `status`, `priority` e `due_date`.
- Compartilhado com `edit` pode atualizar `title`, `description`, `status`, `priority` e `due_date`, mas não `category_id`.
- Compartilhado com `view` recebe `403`; usuário sem acesso recebe `404` pelo queryset acessível.
- O serializer rejeita PATCH vazio e mantém a validação existente para campos desconhecidos, campos imutáveis e categorias do usuário autenticado.
- A resposta usa o serializer existente e preserva o campo `access` calculado para o solicitante.

## Testes e documentação

Criar exatamente dois testes de endpoint: sucesso do editor compartilhado e bloqueio do viewer. Atualizar o README com exemplos, matriz de permissões, PATCH parcial, payload vazio e ausência de controle otimista de concorrência.
