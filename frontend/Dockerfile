FROM node:18-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./
# Instalar todas las dependencias (necesarias para el build)
RUN npm ci

# Copiar el resto del código
COPY . .
# Construir la aplicación Next.js
RUN npm run build

# Etapa de producción
FROM node:18-alpine

WORKDIR /app

ENV NODE_ENV=production

# Copiar package.json para instalar dependencias de producción
COPY package*.json ./
# Instalar todas las dependencias (Next.js necesita algunas devDependencies en runtime)
RUN npm ci

# Copiar archivos compilados desde el builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js* ./
COPY --from=builder /app/package.json ./

# Crear y copiar directorio public si existe
RUN mkdir -p ./public
COPY --from=builder /app/public ./public

EXPOSE 3000

# Iniciar el servidor Next.js en modo producción
CMD ["npm", "run", "start"]
