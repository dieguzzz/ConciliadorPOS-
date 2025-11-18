FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js* ./
COPY --from=builder /app/package.json ./
# Crear directorio public si no existe y copiar si hay contenido
RUN mkdir -p ./public
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "run", "start"]
