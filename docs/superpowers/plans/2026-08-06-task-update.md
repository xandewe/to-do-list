# Task 08 — Atualização parcial de tarefas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar a atualização parcial de tarefas com autorização por owner/share e documentação da API.

**Architecture:** O endpoint será adicionado ao `TaskDetailView` existente. O queryset acessível da Task 7 continuará ocultando tarefas privadas, enquanto a view decide entre owner, editor e viewer usando o prefetch `current_user_shares`; o serializer existente fará validação e persistência parcial.

**Tech Stack:** Django 5.2, Django REST Framework 3.17, pytest-django, PostgreSQL via Docker.

## Global Constraints

- Não modificar models, URLs, settings ou requirements.
- Criar exatamente dois testes em `backend/apps/tasks/tests/api/test_task_update.py`.
- Não criar service, repository, permission class, serializer ou endpoint adicional.
- Não criar migration.

### Task 1: Definir o contrato de atualização compartilhada

**Files:**
- Create: `backend/apps/tasks/tests/api/test_task_update.py`

- [ ] Escrever `test_shared_editor_updates_task`, criando owner, editor, categoria, tarefa e share `edit`; autenticar o editor; enviar title, description, status, priority e due_date; afirmar HTTP 200, campos atualizados, owner/categoria/created_at preservados, updated_at alterado e `access` com `shared/edit`.
- [ ] Escrever `test_shared_viewer_cannot_update_task`, criando owner, viewer, tarefa e share `view`; autenticar o viewer; enviar novo title; afirmar HTTP 403, title e updated_at preservados e ausência de dados do owner na resposta.
- [ ] Executar `docker compose run --rm api pytest apps/tasks/tests/api/test_task_update.py -v` e confirmar que os dois testes falham por ausência do método PATCH.

### Task 2: Implementar validação e autorização do PATCH

**Files:**
- Modify: `backend/apps/tasks/serializers.py`
- Modify: `backend/apps/tasks/views.py`

- [ ] Adicionar em `TaskSerializer.run_validation` a rejeição de mapping vazio quando `self.partial` com `detail` igual a `Informe ao menos um campo para atualização.`.
- [ ] Adicionar `TaskDetailView.patch`: buscar por `get_accessible_tasks`, identificar owner/share pré-carregado, retornar 403 para viewer, bloquear `category_id` para editor, instanciar `TaskSerializer(instance=task, data=request.data, partial=True, context={"request": request})`, validar, salvar e retornar 200.
- [ ] Executar os dois testes da Task 1 e confirmar aprovação.
- [ ] Executar os testes de criação e leitura para garantir compatibilidade.

### Task 3: Documentar e validar o contrato completo

**Files:**
- Modify: `README.md`

- [ ] Documentar exemplos PATCH de owner/editor e a matriz owner/edit/view, incluindo 404 privado, PATCH vazio 400 e ausência de concorrência otimista.
- [ ] Executar `docker compose run --rm api pytest apps/tasks/tests -v`.
- [ ] Executar `docker compose run --rm api pytest -v`.
- [ ] Executar `docker compose run --rm api python manage.py check`.
- [ ] Executar `docker compose run --rm api python manage.py makemigrations --check --dry-run` e confirmar `No changes detected`.
- [ ] Revisar `git diff`, confirmar somente os arquivos previstos e fazer commit separado por contrato, implementação e documentação.
