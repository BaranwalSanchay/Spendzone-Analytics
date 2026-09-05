# syntax=docker/dockerfile:1

# --- deps: install once, reused by dev/build so `docker compose up` stays fast on rebuilds ---
FROM oven/bun:1 AS deps
WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# --- dev (default): live-reloading Vite dev server for local/Docker testing ---
FROM deps AS dev
WORKDIR /app
COPY . .
# Port is fixed by vite.config.ts (server.port: 8080), not Vite's 5173 default.
EXPOSE 8080
CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0"]

# --- build: production bundle, used by the `preview` stage below ---
FROM deps AS build
WORKDIR /app
COPY . .
RUN bun run build

# --- preview: serve the production bundle in a container, for smoke-testing the real
# Vercel build output locally. Not used for actual deployment — Vercel builds from the repo. ---
FROM deps AS preview
WORKDIR /app
COPY --from=build /app/dist ./dist
EXPOSE 4173
CMD ["bun", "run", "preview", "--", "--host", "0.0.0.0"]
