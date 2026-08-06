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
| `POSTGRES_DB` | `todo_list_ah` | Nome do banco e do volume Docker |
| `POSTGRES_USER` | `admin` | Usuário administrativo local |
| `POSTGRES_PASSWORD` | `admin` | Senha administrativa local |
| `POSTGRES_HOST` | `db` | Nome do serviço PostgreSQL no Compose |
| `POSTGRES_PORT` | `5432` | Porta interna do PostgreSQL |
| `POSTGRES_CONNECT_TIMEOUT` | `3` | Tempo máximo de conexão, em segundos |
| `JWT_SIGNING_KEY` | `django-insecure-jwt-development-only` | Assina os tokens JWT no desenvolvimento |

As credenciais `admin` e a chave JWT de exemplo são exclusivas para desenvolvimento. Em ambientes reais, use uma `JWT_SIGNING_KEY` forte, secreta e diferente da `SECRET_KEY` do Django.

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
