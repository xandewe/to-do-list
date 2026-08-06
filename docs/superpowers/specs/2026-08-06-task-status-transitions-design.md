# Task 09 — Conclusão e reabertura de tarefas

## Objetivo

Formalizar o uso do PATCH existente para concluir (`pending → completed`) e reabrir (`completed → pending`) tarefas.

## Design aprovado

- Reutilizar `TaskDetailView.patch`, `TaskSerializer` e as choices de status do model já existentes.
- Não criar endpoint, URL, serializer, service, repository, migration, campo `completed_at` ou dependência.
- Criar exatamente dois testes de endpoint: owner conclui/repete/reabre; viewer recebe 403 sem alteração.
- Atualizar o README com os exemplos e as regras de idempotência, permissões e ausência de endpoints dedicados.
- Não modificar `views.py` ou `serializers.py` quando o contrato existente já atender à Task 9.
