# To-do List AH

O To-do List AH é uma aplicação para criar, organizar e acompanhar tarefas de forma simples e eficiente. Com ela, os usuários podem criar e gerenciar categorias, manter suas atividades organizadas e compartilhar tarefas com outras pessoas, facilitando a colaboração e o acompanhamento das responsabilidades.

## Tecnologias

| Categoria | Tecnologia | Versão |
| --- | --- | --- |
| Linguagem | Python | 3.14 |
| Framework web | Django | 5.2.17 LTS |
| Framework de API | Django REST Framework | 3.17.1 |
| Containerização | Docker | Utiliza a versão instalada no ambiente |

## Backend com Docker

Os comandos abaixo devem ser executados na raiz do projeto, com o Docker Desktop em funcionamento.

### 1. Construir a imagem

```powershell
docker build --tag todo-list-ah-backend ./backend
```

Lê o `backend/Dockerfile`, instala as dependências e cria uma imagem chamada `todo-list-ah-backend`. A opção `--tag` atribui esse nome à imagem, enquanto `./backend` define o contexto enviado ao Docker.

### 2. Conferir as versões instaladas

```powershell
docker run --rm todo-list-ah-backend python -c "import django, rest_framework, sys; print(sys.version.split()[0], django.get_version(), rest_framework.VERSION)"
```

Cria um container temporário e exibe as versões do Python, Django e DRF presentes na imagem. A opção `--rm` remove o container automaticamente após o comando.

### 3. Validar a configuração do Django

```powershell
docker run --rm todo-list-ah-backend python manage.py check
```

Executa as verificações internas do Django para identificar erros na configuração do projeto.

### 4. Executar os testes

```powershell
docker run --rm todo-list-ah-backend python manage.py test config.tests --verbosity 2
```

Executa os testes do pacote `config`. A opção `--verbosity 2` mostra informações detalhadas sobre a descoberta e o resultado de cada teste.

### 5. Validar as migrações

```powershell
docker run --rm todo-list-ah-backend python manage.py migrate --noinput
```

Aplica as migrações iniciais em um banco SQLite temporário. A opção `--noinput` impede perguntas interativas. Como o container usa `--rm`, esse banco é descartado ao término; este comando serve para validar que as migrações podem ser aplicadas.

### 6. Iniciar o backend

```powershell
docker run --name todo-list-ah-backend --publish 8000:8000 todo-list-ah-backend sh -c "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"
```

Cria um container chamado `todo-list-ah-backend`, aplica as migrações no banco interno e inicia o servidor de desenvolvimento. A opção `--publish 8000:8000` conecta a porta `8000` do Windows à porta `8000` do container.

Com o servidor em execução, acesse [http://localhost:8000/admin/](http://localhost:8000/admin/).

### 7. Interromper o backend

Em outro terminal, execute:

```powershell
docker stop todo-list-ah-backend
```

Envia o sinal de encerramento ao container em execução.

### 8. Remover o container

```powershell
docker rm todo-list-ah-backend
```

Remove o container parado. A imagem `todo-list-ah-backend` permanece disponível e pode ser utilizada novamente.

> Esta configuração utiliza o servidor de desenvolvimento do Django e SQLite. Ela serve apenas para desenvolvimento local e será evoluída antes de um uso em produção.
