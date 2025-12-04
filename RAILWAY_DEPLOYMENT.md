# 🚂 Guía de Deployment en Railway

## ✅ Cambios Realizados

1. ✅ `frontend/package.json` - Script de start compatible con Railway
2. ✅ `docker-compose.yml` - PostgreSQL comentado (no se usa)
3. ✅ `railway.toml` - Configuración para Railway
4. ✅ `.railwayignore` - Archivos a ignorar

---

## 📦 Paso 1: Subir a GitHub (si no está)

```bash
git add .
git commit -m "Preparado para Railway deployment"
git push origin main
```

Si no tienes repositorio:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
# Crea un repo en GitHub y luego:
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

---

## 🚀 Paso 2: Desplegar en Railway

### Opción A: Desde la Web (Más Fácil)

1. Ve a **https://railway.app**
2. Haz clic en **"Login"** → Conecta con **GitHub**
3. Clic en **"New Project"**
4. Selecciona **"Deploy from GitHub repo"**
5. Busca y selecciona tu repositorio **ConciliadorPOS**
6. Railway detectará automáticamente el `docker-compose.yml`

### Opción B: Desde CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar y desplegar
railway init
railway up
```

---

## ⚙️ Paso 3: Configurar Variables de Entorno

Railway creará 2 servicios: `backend` y `frontend`

### Backend (ya está configurado)
- No necesita cambios adicionales
- Anota la URL pública: `https://tu-backend-xxx.up.railway.app`

### Frontend
1. Ve al servicio **frontend** en Railway
2. Click en **"Variables"**
3. Agrega:
   ```
   NEXT_PUBLIC_API_BASE=https://tu-backend-xxx.up.railway.app
   ```
4. Guarda y redeploya

---

## 🎯 Paso 4: Verificar

1. Espera 2-5 minutos mientras se construyen los servicios
2. Ve a la pestaña **"Deployments"**
3. Cuando ambos estén **"Active"** 🟢
4. Haz clic en la URL del frontend
5. ¡Tu app está en línea! 🎉

---

## 📊 Monitoreo de Costos

Railway da **$5 USD gratis cada mes**. Tu app debería costar ~$3-7/mes:

- Backend: ~$2-4/mes
- Frontend: ~$1-3/mes

Puedes ver el consumo en: **Settings → Usage**

---

## 🔧 Comandos Útiles

```bash
# Ver logs del backend
railway logs --service backend

# Ver logs del frontend
railway logs --service frontend

# Forzar redespliegue
railway up --service backend
railway up --service frontend

# Ver variables
railway variables

# Abrir dashboard
railway open
```

---

## ⚠️ Troubleshooting

### El backend no arranca:
- Verifica los logs: `railway logs --service backend`
- Asegúrate que el puerto 8000 esté correcto

### El frontend no conecta al backend:
- Verifica que `NEXT_PUBLIC_API_BASE` esté configurada
- La URL debe ser la pública del backend (sin `/` al final)

### Error de build:
- Verifica que los Dockerfiles estén correctos
- Revisa los logs de build en Railway

---

## 🎓 Recursos

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Blog](https://blog.railway.app)

---

## 🔄 Actualizar la App

Cada vez que hagas push a GitHub, Railway redesplegiará automáticamente:

```bash
git add .
git commit -m "Nueva característica"
git push origin main
# Railway detectará el cambio y redesplegiará automáticamente 🚀
```

---

**¡Listo! Tu app debería estar corriendo en Railway en menos de 10 minutos! 🎉**

