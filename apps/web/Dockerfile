# apps/web — Next.js (App Router, output: standalone).
# Build a partir da raiz do monorepo? Não: contexto = apps/web + packages/api-types.
# Para simplicidade, este Dockerfile assume contexto = raiz do repo e copia o web.
# (O workflow de deploy passa --build-context conforme necessário.)
FROM node:22-slim AS base
ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

FROM base AS deps
WORKDIR /repo
COPY pnpm-workspace.yaml package.json ./
COPY packages/api-types ./packages/api-types
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --filter @setes/web... --frozen-lockfile=false

FROM base AS build
WORKDIR /repo
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY pnpm-workspace.yaml package.json ./
COPY packages ./packages
COPY apps/web ./apps/web
WORKDIR /repo/apps/web
# NEXT_PUBLIC_* é resolvido em build-time pelo Next.js e embutido no bundle
# servido ao browser -- precisa estar disponível antes do `pnpm build`.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8080
# Next standalone: copia o servidor autossuficiente + estáticos.
COPY --from=build /repo/apps/web/.next/standalone ./
COPY --from=build /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=build /repo/apps/web/public ./apps/web/public
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://127.0.0.1:'+(process.env.PORT||8080)+'/api/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"
CMD ["node", "apps/web/server.js"]
