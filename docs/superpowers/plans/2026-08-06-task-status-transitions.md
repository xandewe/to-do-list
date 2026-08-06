# Task 09 — Conclusão e reabertura de tarefas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Cobrir e documentar conclusão, repetição idempotente e reabertura usando o PATCH existente.

**Architecture:** Nenhuma regra nova de produção será necessária: `TaskDetailView.patch` já limita o queryset, aplica owner/editor/viewer e delega a validação de status ao `TaskSerializer`/choices do model. O trabalho adiciona testes de integração e documentação do contrato.

**Tech Stack:** Django 5.2, Django REST Framework 3.17, pytest-django, PostgreSQL via Docker.

## Global Constraints

- Não modificar models, URLs, settings ou requirements.
- Criar exatamente dois testes em `backend/apps/tasks/tests/api/test_task_status.py`.
- Não criar endpoint `/complete/` ou `/reopen/`, `completed_at`, migration, service, repository ou dependência.

### Task 1: Definir transições de status e autorização

**Files:**
- Create: `backend/apps/tasks/tests/api/test_task_status.py`

- [ ] Escrever `test_owner_can_complete_and_reopen_task`: criar owner e tarefa pending; autenticar; enviar completed e verificar 200/persistência; repetir completed e verificar 200/mesma tarefa; enviar pending e verificar 200/persistência, owner/título/descrição/prioridade inalterados e nenhum registro adicional.
- [ ] Escrever `test_view_only_user_cannot_change_task_status`: criar owner, viewer, tarefa pending e share view; autenticar viewer; enviar completed; verificar 403, status e demais campos inalterados e ausência de dados do owner na resposta.
- [ ] Executar `docker compose run --rm api pytest apps/tasks/tests/api/test_task_status.py -v` e confirmar duas falhas RED antes de qualquer mudança de produção.

### Task 2: Documentar e validar o contrato

**Files:**
- Modify: `README.md`

- [ ] Adicionar exemplos curl para completed e pending.
- [ ] Documentar que o PATCH é idempotente, owner/share edit podem alterar status, viewer recebe 403, usuário privado recebe 404, não há endpoints dedicados nem `completed_at`.
- [ ] Executar `docker compose run --rm api pytest apps/tasks/tests/api/test_task_status.py -v`.
- [ ] Executar os testes de criação, leitura, atualização e status.
- [ ] Executar `docker compose run --rm api pytest -v`.
- [ ] Executar `docker compose run --rm api python manage.py check`.
- [ ] Executar `docker compose run --rm api python manage.py makemigrations --check --dry-run`.
- [ ] Revisar `git diff --check` e confirmar somente os arquivos previstos.
