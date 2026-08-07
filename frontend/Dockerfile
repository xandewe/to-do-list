# syntax=docker/dockerfile:1

# Imagem simples para rodar o frontend no compose: builda o SPA e serve com o
# próprio Vite (`vite preview`), que também faz proxy de /api para o serviço
# `api` (ver preview.proxy em vite.config.js). Sem nginx.
FROM node:22-alpine
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vazio => o SPA usa caminhos relativos (/api/v1, /api/health), servidos pelo
# proxy do vite preview na mesma origem (sem CORS).
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "preview"]
