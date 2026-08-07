# Frontend — To-do List AH

SPA em Vite + React que consome a API Django do diretório `../backend`.

## Stack

| Categoria | Tecnologia |
| --- | --- |
| Build/dev server | Vite 6 |
| UI | React 19 |
| Roteamento | React Router 7 |
| Cliente HTTP | Axios |
| Estado global | Context API |

## Pré-requisitos

- Node.js 20+ (desenvolvido com Node 22)
- Backend rodando em `http://localhost:8000` (ver README na raiz do projeto)

## Configuração

```bash
cp .env.example .env
```

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Origem base da API (sem barra final) |

A porta `5173` do dev server já está liberada no CORS do backend
(`DJANGO_CORS_ALLOWED_ORIGINS`), então o frontend fala com a API direto, sem proxy.

## Executar

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # gera dist/
npm run preview  # serve o build de produção localmente
```

## Docker

O frontend é dockerizado como parte do `compose.yaml` na raiz do projeto. A
imagem builda o SPA e o serve com o próprio Vite (`vite preview`), que também faz
**proxy** de `/api/` para o serviço `api` (mesma origem, sem CORS).

A partir da raiz do projeto:

```bash
docker compose up --build --detach
```

Sobe `db` + `api` + `frontend`. A aplicação fica em `http://localhost:8080`
(configurável por `FRONTEND_PORT`). Como o SPA é servido na mesma origem da API,
o build usa caminhos relativos (`VITE_API_BASE_URL` vazio); para apontar a uma
API externa, defina `FRONTEND_API_BASE_URL` antes do build.

## Estrutura

```
src/
├── main.jsx        # bootstrap: router + providers
├── App.jsx         # definição de rotas
├── lib/
│   ├── apiClient.js    # Axios + interceptor de refresh (rotação + fila de 401)
│   └── tokenStorage.js # persistência dos tokens JWT no localStorage
├── services/       # chamadas à API por domínio (health, auth, ...)
├── context/        # providers de estado (AuthContext, ...)
├── pages/          # telas
└── components/     # UI reutilizável
```

## Autenticação (visão geral)

A API usa JWT (Simple JWT) com access de 15 min e refresh de 7 dias com rotação.
O `apiClient` injeta `Authorization: Bearer <access>` e, ao receber `401`
(`token_not_valid`), renova o token via `/auth/token/refresh/` uma única vez,
enfileirando requisições concorrentes, e substitui o par de tokens (a API
blacklista o refresh antigo). O logout revoga o refresh em
`/auth/token/blacklist/`. As telas de login/registro chegam na Task 19.
