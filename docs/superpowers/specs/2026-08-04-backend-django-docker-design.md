# Fundação do backend com Django REST Framework e Docker

## Objetivo

Criar a fundação executável do backend do To-do List AH dentro do diretório `backend`, usando versões estáveis e priorizando suporte prolongado. A etapa deve permitir construir uma imagem Docker, validar o projeto Django e iniciar o servidor de desenvolvimento.

## Tecnologias

- Python 3.14, série estável com suporte de segurança previsto até outubro de 2030.
- Django 5.2.17 LTS, com suporte estendido previsto até abril de 2028.
- Django REST Framework 3.17.1.
- pip e `requirements.txt` para gerenciamento inicial das dependências.
- Docker com uma imagem oficial `python:3.14-slim`.
- SQLite como banco temporário da fundação.

## Estrutura

```text
backend/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .dockerignore
├── Dockerfile
├── manage.py
└── requirements.txt
```

O pacote `config` concentra a configuração global do projeto. Aplicações de domínio, como tarefas, categorias e usuários, serão adicionadas em etapas posteriores.

## Dependências

O `requirements.txt` fixará as versões diretas de Django e Django REST Framework. As dependências transitivas continuarão sendo resolvidas pelo pip nesta primeira etapa.

## Imagem Docker

O `Dockerfile` usará `python:3.14-slim`, desabilitará a geração de bytecode e habilitará saída de logs sem buffer. As dependências serão copiadas e instaladas antes do código para aproveitar o cache de camadas.

A aplicação será executada por um usuário sem privilégios administrativos. O container exporá a porta `8000` e iniciará o servidor de desenvolvimento em `0.0.0.0:8000`.

O `.dockerignore` excluirá caches, ambientes virtuais, banco SQLite local, metadados do Git, arquivos do editor e segredos, reduzindo o contexto enviado ao Docker.

## Configuração Django

O projeto terá a configuração padrão mínima do Django, com `rest_framework` registrado em `INSTALLED_APPS`. O SQLite será usado apenas para permitir migrações e validação local sem introduzir um serviço de banco nesta etapa.

A chave secreta de desenvolvimento terá um valor inseguro e explicitamente identificado como temporário. A parametrização por variáveis de ambiente será tratada junto da configuração dos ambientes em uma etapa posterior.

## Documentação

O `README.md` receberá uma seção de tecnologias com linguagem, framework e versões. Também receberá instruções numeradas para:

1. construir a imagem;
2. validar a configuração Django;
3. aplicar migrações;
4. executar o container;
5. acessar o servidor;
6. interromper e remover o container.

Cada comando terá uma explicação breve de sua finalidade. O relatório final da implementação repetirá o que foi concluído, os comandos efetivamente executados e o propósito de cada um.

## Validação e critérios de aceite

- A imagem Docker deve ser construída sem erros.
- `python manage.py check` deve terminar sem problemas reportados.
- As migrações iniciais devem ser aplicáveis dentro do container.
- O container deve iniciar o servidor Django na porta `8000`.
- O README deve refletir exatamente as versões fixadas no projeto.
- Nenhum segredo real deve ser adicionado ao repositório ou à imagem.

## Fora do escopo

- Docker Compose.
- PostgreSQL ou outro banco externo.
- Endpoints e regras de negócio.
- Modelos de tarefas, categorias ou usuários.
- Configuração de produção e servidor WSGI/ASGI de produção.
- Autenticação, autorização e documentação OpenAPI.
