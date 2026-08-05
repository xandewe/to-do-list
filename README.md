# To-do List AH

O To-do List AH é uma aplicação para criar, organizar e acompanhar tarefas de forma simples e eficiente. Com ela, os usuários podem criar e gerenciar categorias, manter suas atividades organizadas e compartilhar tarefas com outras pessoas, facilitando a colaboração e o acompanhamento das responsabilidades.

## Tecnologias

| Categoria | Tecnologia | Versão |
| --- | --- | --- |
| Linguagem | Python | 3.14 |
| Framework web | Django | 5.2.17 LTS |
| Framework de API | Django REST Framework | 3.17.1 |
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

As credenciais `admin` são exclusivas para desenvolvimento. Não utilize esses valores em produção.

## Executar com Docker Compose

Os comandos devem ser executados na raiz do projeto, com o Docker Desktop em funcionamento.

### 1. Construir e iniciar a aplicação

```bash
docker compose up --build --detach
```

O Compose constrói a imagem da API, inicia o PostgreSQL, aguarda o banco ficar saudável, aplica as migrações e inicia o servidor Django na porta `8000`.

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
