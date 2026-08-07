# To-do List AH

O To-do List AH é uma aplicação para criar, organizar e acompanhar tarefas de forma simples e eficiente. Com ela, os usuários podem criar e gerenciar categorias, manter suas atividades organizadas e compartilhar tarefas com outras pessoas, facilitando a colaboração e o acompanhamento das responsabilidades.

## Tecnologias

| Categoria | Tecnologia | Versão |
| --- | --- | --- |
| Linguagem | Python | 3.14 |
| Framework web | Django | 5.2.17 LTS |
| Framework de API | Django REST Framework | 3.17.1 |
| Autenticação | Simple JWT | 5.5.1 |
| Banco de dados | PostgreSQL | 18.4 |
| Driver PostgreSQL | Psycopg | 3.3.4 |
| Containerização | Docker | Utiliza a versão instalada no ambiente |
| Orquestração | Docker Compose | Utiliza a versão instalada no ambiente |

## Variáveis de ambiente

O arquivo `.env.example` contém os valores padrão do desenvolvimento local. No Git Bash, copie-o para `.env` caso queira personalizar as configurações sem alterar o Compose:

```bash
cp .env.example .env
```

| Variável | Valor padrão | Finalidade |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | `django-insecure-development-only` | Assina sessões, tokens e demais operações criptográficas do Django |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Lista de hosts permitidos, separada por vírgula |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Origens autorizadas a chamar a API pelo navegador (CORS), separadas por vírgula |
| `POSTGRES_DB` | `todo_list_ah` | Nome do banco e do volume Docker |
| `POSTGRES_USER` | `admin` | Usuário administrativo local |
| `POSTGRES_PASSWORD` | `admin` | Senha administrativa local |
| `POSTGRES_HOST` | `db` | Nome do serviço PostgreSQL no Compose |
| `POSTGRES_PORT` | `5432` | Porta interna do PostgreSQL |
| `POSTGRES_CONNECT_TIMEOUT` | `3` | Tempo máximo de conexão, em segundos |
| `JWT_SIGNING_KEY` | `django-insecure-jwt-development-only` | Assina os tokens JWT no desenvolvimento |

A `DJANGO_SECRET_KEY` é obrigatória: sem ela definida no ambiente, a aplicação não inicia. O Compose e o `.env.example` já fornecem um valor de desenvolvimento, então o fluxo local funciona sem configuração extra.

As credenciais `admin` e as chaves de exemplo são exclusivas para desenvolvimento. Em ambientes reais, defina uma `DJANGO_SECRET_KEY` forte e secreta e uma `JWT_SIGNING_KEY` também forte, secreta e diferente da `DJANGO_SECRET_KEY`. Ajuste `DJANGO_ALLOWED_HOSTS` para os domínios reais da aplicação e `DJANGO_CORS_ALLOWED_ORIGINS` para as origens do frontend.

O valor padrão de `DJANGO_CORS_ALLOWED_ORIGINS` corresponde ao servidor de desenvolvimento do Vite. A API só aceita requisições do navegador vindas das origens listadas; a autenticação é feita pelo header `Authorization: Bearer`, sem cookies, então o CORS não habilita credenciais.

## Executar com Docker Compose

Os comandos devem ser executados na raiz do projeto, com o Docker Desktop em funcionamento.

### 1. Construir e iniciar a aplicação

```bash
docker compose up --build --detach
```

O Compose constrói a imagem da API, inicia o PostgreSQL, aguarda o banco ficar saudável, aplica as migrações e inicia o servidor Django na porta `8000`.

Sempre reconstrua a imagem depois de alterar `backend/requirements.txt`:

```bash
docker compose build api
```

### 2. Consultar o estado dos serviços

```bash
docker compose ps
```

Os serviços `api` e `db` devem aparecer como `healthy`.

### 3. Acompanhar os logs da API

```bash
docker compose logs --follow api
```

Mostra as migrações e os logs do servidor em tempo real. Pressione `Ctrl+C` para sair dos logs sem interromper os containers.

### 4. Validar a configuração Django

```bash
docker compose exec api python manage.py check
```

Executa as verificações internas no container da API que já está em execução.

### 5. Executar os testes com PostgreSQL

```bash
docker compose run --rm api python manage.py test --verbosity 2
```

Cria um container temporário da API. O Django cria o banco `test_todo_list_ah` no PostgreSQL, executa os testes e remove esse banco ao terminar.

### 6. Acessar o PostgreSQL

```bash
docker compose exec db psql -U admin -d todo_list_ah
```

Abre o cliente `psql` dentro do container do banco. Digite `\q` para sair.

### 7. Parar e reiniciar os serviços

```bash
docker compose stop
docker compose start
```

`stop` interrompe os containers sem removê-los. `start` inicia novamente os mesmos containers.

### 8. Remover os containers

```bash
docker compose down
```

Remove os containers e a rede do projeto, preservando o volume `todo_list_ah` e seus dados. Na próxima execução, use novamente `docker compose up --detach`.

## Volume do PostgreSQL

O volume recebe o mesmo nome definido em `POSTGRES_DB`:

```bash
docker volume inspect todo_list_ah
```

Volumes nomeados são globais no Docker. Use um valor de `POSTGRES_DB` diferente em cada projeto para evitar compartilhamento acidental de dados.

Para remover também o volume e apagar permanentemente o banco local:

```bash
docker compose down --volumes
```

Use esse comando com cuidado: os dados removidos não podem ser recuperados sem um backup.

## Convenções da API

As rotas funcionais da API usam o prefixo versionado `/api/v1/`. O healthcheck é uma rota de infraestrutura e permanece fora do versionamento em `/api/health/`.

Endpoints de coleção usarão paginação no formato padrão do Django REST Framework:

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/tasks/?page=2",
  "previous": null,
  "results": []
}
```

O parâmetro `page` seleciona a página. O parâmetro `page_size` controla a quantidade de registros, com padrão de 20 e máximo de 100.

Para executar os testes da infraestrutura da API, a partir de `backend/`, use:

```bash
pytest config/tests health/tests -v
```

## Cadastro de usuário

O cadastro é público e cria uma conta sem autenticar automaticamente o cliente:

```text
POST /api/v1/users/
```

O e-mail é o identificador da conta. A senha deve atender aos validadores configurados pelo Django, é armazenada somente como hash e nunca aparece na resposta. O cadastro não emite tokens; eles são obtidos separadamente pela rota de login JWT.

Exemplo de requisição:

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "person@example.com",
    "password": "uma-senha-segura-123",
    "first_name": "Alex",
    "last_name": "Silva"
  }'
```

Um cadastro válido retorna HTTP `201 Created` apenas com os dados públicos:

```json
{
  "id": "3eab1028-c17c-4e90-8d11-457445c7e88a",
  "email": "person@example.com",
  "first_name": "Alex",
  "last_name": "Silva"
}
```

E-mail já cadastrado retorna HTTP `400 Bad Request`:

```json
{
  "email": ["Já existe uma conta com este e-mail."]
}
```

Senha reprovada pelos validadores retorna o erro associado a `password`:

```json
{
  "password": ["Esta senha é muito curta."]
}
```

Quando um campo obrigatório não é informado, a resposta também é HTTP `400 Bad Request`:

```json
{
  "email": ["Este campo é obrigatório."],
  "password": ["Este campo é obrigatório."]
}
```

Somente `email`, `password`, `first_name` e `last_name` são aceitos. Campos desconhecidos ou administrativos são rejeitados, e o cadastro não disponibiliza listagem pública de usuários.

## Autenticação JWT

A API usa Simple JWT 5.5.1 por fornecer emissão, validação, rotação e blacklist de tokens sem manter uma implementação JWT própria. Login, refresh e logout são públicos; as demais rotas da API exigem um access token por padrão. Cadastro e healthcheck também permanecem públicos.

### Login

Envie e-mail e senha para receber um access token e um refresh token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "person@example.com",
    "password": "uma-senha-segura-123"
  }'
```

Credenciais válidas retornam HTTP `200 OK`:

```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

O access token expira em 15 minutos. Envie-o somente no header Bearer de rotas protegidas:

```bash
curl http://localhost:8000/api/v1/recurso-protegido/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

O caminho acima representa uma rota protegida genérica; não é um endpoint implementado nesta task. Credenciais inválidas ou um usuário inativo retornam HTTP `401` com mensagem genérica, sem revelar se o e-mail existe.

### Renovação

O refresh token expira em sete dias e serve apenas para renovação ou logout:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "REFRESH_TOKEN"}'
```

Cada renovação retorna um novo access e um novo refresh. O cliente deve substituir imediatamente o refresh armazenado, pois o anterior entra na blacklist e uma nova tentativa com ele retorna HTTP `401`.

### Logout

Revogue o refresh atual para impedir novas renovações:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/blacklist/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "REFRESH_TOKEN"}'
```

A resposta oficial é HTTP `200 OK` com `{}`. O logout não revoga access tokens já emitidos: eles continuam válidos até o limite de 15 minutos.

### Erros e armazenamento

Campo obrigatório ausente retorna HTTP `400`. Credenciais inválidas, access expirado e refresh inválido, expirado ou revogado retornam HTTP `401`, por exemplo:

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

Não coloque tokens em URLs nem os registre em logs. Em aplicações web, a escolha entre memória, armazenamento do navegador ou cookies exige uma análise específica de XSS e CSRF; `localStorage` não deve ser considerado seguro de forma genérica. Cookies HttpOnly não fazem parte deste contrato.

## Usuário autenticado

As operações abaixo exigem um access token JWT válido no header `Authorization`. A rota identifica o usuário exclusivamente pelo token e nunca recebe um ID de usuário.

Consulte os dados públicos da conta autenticada:

```bash
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Uma consulta válida retorna HTTP `200 OK`:

```json
{
  "id": "3eab1028-c17c-4e90-8d11-457445c7e88a",
  "email": "person@example.com",
  "first_name": "Alex",
  "last_name": "Silva"
}
```

Atualize parcialmente o primeiro nome e/ou o sobrenome:

```bash
curl -X PATCH http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alexandre"
  }'
```

Somente `first_name` e `last_name` podem ser alterados. O e-mail e o ID são somente leitura, campos omitidos são preservados e um payload vazio retorna HTTP `400`. Campos desconhecidos, de identidade ou administrativos também retornam HTTP `400` sem aplicar alterações parciais. Token ausente, inválido ou inadequado retorna HTTP `401`.

## Categorias

Todas as operações de categorias exigem um access token JWT. Cada categoria pertence ao usuário autenticado; o proprietário não é aceito no payload nem retornado pela API. O nome é único por usuário, enquanto usuários diferentes podem reutilizar o mesmo nome.

A cor é opcional e deve ser vazia ou usar o formato hexadecimal completo `#RRGGBB`. A listagem é ordenada por nome e usa os parâmetros de paginação `page` e `page_size` descritos nas convenções da API.

Liste as categorias do usuário autenticado:

```bash
curl http://localhost:8000/api/v1/categories/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Crie uma categoria:

```bash
curl -X POST http://localhost:8000/api/v1/categories/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trabalho",
    "description": "Atividades profissionais",
    "color": "#336699"
  }'
```

Consulte uma categoria própria:

```bash
curl http://localhost:8000/api/v1/categories/CATEGORY_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Atualize parcialmente uma categoria:

```bash
curl -X PATCH http://localhost:8000/api/v1/categories/CATEGORY_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Projetos"
  }'
```

Exclua uma categoria:

```bash
curl -X DELETE http://localhost:8000/api/v1/categories/CATEGORY_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Consultar, alterar ou excluir uma categoria de outro usuário retorna HTTP `404`. A exclusão é física, mas não remove tarefas associadas: elas permanecem existentes com `category` igual a `null`.

## Tarefas

A criação de tarefas exige um access token JWT. O proprietário vem exclusivamente do token e campos gerenciados pelo sistema, como `id`, `owner_id`, `created_at` e `updated_at`, são somente leitura.

Crie uma tarefa com o payload mínimo:

```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Preparar relatório"
  }'
```

Crie uma tarefa com todos os campos opcionais:

```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "CATEGORY_UUID",
    "title": "Preparar relatório",
    "description": "Consolidar resultados do mês",
    "status": "pending",
    "priority": "high",
    "due_date": "2026-08-10T18:00:00-03:00"
  }'
```

A categoria é opcional e, quando informada, deve pertencer ao usuário autenticado. O status padrão é `pending`, a prioridade padrão é `medium` e o prazo é opcional, inclusive podendo estar no passado.

Liste as tarefas próprias e as compartilhadas com permissão `view` ou `edit`:

```bash
curl http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

A listagem usa os parâmetros `page` e `page_size`, é ordenada por `created_at` e `id` decrescentes e exclui tarefas privadas de outros usuários antes da paginação. Cada tarefa aparece uma única vez e informa a forma de acesso:

```json
{
  "type": "owned",
  "permission": "owner"
}
```

Para uma tarefa compartilhada, `type` é `shared` e `permission` é `view` ou `edit` conforme o compartilhamento.

Consulte o detalhe de uma tarefa própria ou compartilhada:

```bash
curl http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Usuários sem acesso recebem HTTP `404`. Remover um compartilhamento revoga a leitura. As respostas expõem apenas `owner_id` e `category_id`; dados pessoais do proprietário e a lista de compartilhamentos não são retornados.

### Atualização parcial de tarefas

Use `PATCH /api/v1/tasks/TASK_UUID/` para alterar somente os campos enviados. O proprietário pode atualizar todos os campos funcionais da tarefa: `category_id`, `title`, `description`, `status`, `priority` e `due_date`.

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": "CATEGORY_UUID",
    "title": "Preparar relatório final",
    "status": "completed",
    "priority": "high",
    "due_date": "2026-08-12T18:00:00-03:00"
  }'
```

Um usuário com compartilhamento `edit` pode alterar o conteúdo e o andamento, mas nunca a categoria. Por exemplo:

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer EDITOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Resultados consolidados e revisados",
    "status": "completed",
    "priority": "high",
    "due_date": "2026-08-12T18:00:00-03:00"
  }'
```

| Acesso | Ler | Alterar via `PATCH` |
| --- | --- | --- |
| Proprietário (`owner`) | Sim | `category_id`, `title`, `description`, `status`, `priority` e `due_date` |
| Compartilhado (`edit`) | Sim | `title`, `description`, `status`, `priority` e `due_date` |
| Compartilhado (`view`) | Sim | Não; retorna HTTP `403 Forbidden` |
| Sem compartilhamento | Não | Não; consulta e atualização retornam HTTP `404 Not Found` |

`category_id` é exclusivamente do proprietário: se um editor o enviar, a API responde HTTP `403 Forbidden` e não aplica nenhuma alteração. Identificadores e metadados (`id`, `owner_id`, `created_at`, `updated_at` e `access`) são somente leitura e campos desconhecidos retornam HTTP `400 Bad Request`.

O payload é sempre parcial: campos omitidos permanecem inalterados. Um corpo vazio (`{}`) retorna HTTP `400 Bad Request`. A atualização não utiliza concorrência otimista: a API não aceita versão, ETag ou `If-Match`; em atualizações concorrentes, a última gravação bem-sucedida prevalece.

### Exclusão de tarefas

Somente o proprietário pode excluir uma tarefa. Envie `DELETE` para o detalhe usando o token do proprietário:

```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN"
```

Uma exclusão bem-sucedida retorna HTTP `204 No Content`, sem corpo de resposta. A exclusão é física; não há *soft delete*. Os registros `TaskShare` associados são removidos em cascata, enquanto a categoria da tarefa e as demais tarefas (inclusive as da mesma categoria ou do mesmo proprietário) são preservadas.

Uma tarefa compartilhada pode ser lida ou editada conforme a permissão, mas usuários compartilhados — inclusive com permissão `edit` — não podem excluí-la: a tentativa retorna HTTP `404 Not Found`, sem revelar uma rota de exclusão separada. Depois da exclusão, a tarefa também deixa de estar acessível aos usuários compartilhados e retorna HTTP `404`; uma segunda tentativa de excluir a mesma tarefa retorna igualmente HTTP `404`.

### Conclusão e reabertura

O status é alterado no mesmo endpoint de atualização parcial; não há endpoints dedicados para concluir ou reabrir tarefas. Para concluir uma tarefa, envie somente `status` com o valor `completed`:

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

Para reabri-la, envie `status` com o valor `pending`:

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_UUID/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'
```

Essas transições são idempotentes: repetir um `PATCH` com o status já definido retorna HTTP `200 OK` e mantém a tarefa naquele estado. O proprietário e um usuário compartilhado com permissão `edit` podem alterar o status. Um usuário com permissão `view` recebe HTTP `403 Forbidden`; sem compartilhamento, uma tarefa privada não é revelada e a atualização retorna HTTP `404 Not Found`. A API não mantém nem retorna o campo `completed_at`.

### Filtros da listagem

A listagem de tarefas aceita filtros opcionais por status e por categoria, combináveis entre si e com a paginação. Os filtros atuam apenas sobre as tarefas acessíveis ao usuário (próprias e compartilhadas).

| Parâmetro | Valores aceitos | Efeito |
| --- | --- | --- |
| `status` | `pending`, `completed` | Retorna apenas as tarefas naquele status |
| `category` | UUID de uma categoria | Retorna apenas as tarefas daquela categoria |

Filtre as tarefas concluídas de uma categoria específica:

```bash
curl "http://localhost:8000/api/v1/tasks/?status=completed&category=CATEGORY_UUID" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

A categoria é filtrada pelo seu UUID, o mesmo identificador usado em `category_id`, garantindo um filtro sem ambiguidade mesmo entre usuários que reutilizam o mesmo nome de categoria. Um valor inválido é ignorado sem gerar erro: um `status` fora das opções ou um `category` que não seja um UUID válido não altera a listagem nem retorna HTTP `400`.

### Compartilhamento de tarefas

Cada tarefa pode ser compartilhada pelo proprietário com outros usuários já cadastrados, concedendo acesso de leitura (`view`) ou de edição (`edit`). As rotas de compartilhamento são aninhadas na tarefa e exclusivas do proprietário: um usuário apenas compartilhado recebe HTTP `403 Forbidden` e um usuário sem acesso recebe HTTP `404 Not Found`, sem revelar a existência da tarefa. Isso também impede que um usuário com permissão `edit` redistribua a tarefa.

Liste os acessos concedidos a uma tarefa própria (resposta paginada):

```bash
curl http://localhost:8000/api/v1/tasks/TASK_UUID/shares/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN"
```

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "share-uuid",
      "user_email": "colega@example.com",
      "permission": "edit",
      "created_at": "2026-08-06T12:00:00-03:00"
    }
  ]
}
```

Compartilhe uma tarefa informando o e-mail do usuário. A permissão é opcional e assume `view` por padrão:

```bash
curl -X POST http://localhost:8000/api/v1/tasks/TASK_UUID/shares/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "colega@example.com",
    "permission": "edit"
  }'
```

Um compartilhamento válido retorna HTTP `201 Created` e expõe apenas o e-mail do usuário, a permissão e os metadados do compartilhamento:

```json
{
  "id": "share-uuid",
  "user_email": "colega@example.com",
  "permission": "edit",
  "created_at": "2026-08-06T12:00:00-03:00"
}
```

O compartilhamento exige uma conta existente. Alguns erros comuns:

| Situação | Status |
| --- | --- |
| E-mail sem conta cadastrada | `404 Not Found` |
| Compartilhar a tarefa consigo mesmo | `400 Bad Request` |
| Tarefa já compartilhada com o mesmo usuário | `400 Bad Request` |
| `permission` diferente de `view`/`edit` | `400 Bad Request` |

Altere a permissão de um compartilhamento existente:

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_UUID/shares/SHARE_UUID/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission": "view"}'
```

Somente `permission` pode ser alterado; um corpo vazio retorna HTTP `400 Bad Request`. Revogue um compartilhamento:

```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/TASK_UUID/shares/SHARE_UUID/ \
  -H "Authorization: Bearer OWNER_ACCESS_TOKEN"
```

A revogação retorna HTTP `204 No Content` e tem efeito imediato: o usuário afetado deixa de listar e de acessar a tarefa, passando a receber HTTP `404` nas consultas e atualizações seguintes.

## Health check

Com os serviços em execução, consulte:

```bash
curl http://localhost:8000/api/health/
```

Quando a API e o banco estão disponíveis, o endpoint responde com HTTP `200`:

```json
{
  "api": "online",
  "database": "online"
}
```

Quando a API está ativa, mas o banco não responde, retorna HTTP `503`:

```json
{
  "api": "online",
  "database": "offline"
}
```

Métodos diferentes de `GET` retornam HTTP `405 Method Not Allowed`.

> Esta configuração utiliza o servidor de desenvolvimento do Django e serve apenas para desenvolvimento local.
