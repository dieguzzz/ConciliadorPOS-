# Guía de Despliegue en Render

## ✅ Revisión del Proyecto

He revisado tu proyecto y he corregido los siguientes problemas:

### Problemas Corregidos:

1. **✅ Dockerfile del Backend**: Eliminado `--reload` para producción
2. **✅ Dockerfile del Frontend**: Configurado para producción con build multi-stage
3. **✅ URLs hardcodeadas**: Reemplazadas por variables de entorno en todos los archivos
4. **✅ Dependencias**: Agregado `numpy` que faltaba en `requirements.txt`
5. **✅ Ruta de datos**: Mejorada la búsqueda del archivo `Lista_Punto_Venta.xlsx`
6. **✅ render.yaml**: Creado con configuración completa para los 3 servicios

## 📋 Archivos Modificados

- `backend/Dockerfile` - Configurado para producción
- `frontend/Dockerfile` - Configurado para producción con build
- `frontend/next.config.js` - Creado para Next.js
- `frontend/src/pages/index.jsx` - URLs dinámicas
- `frontend/src/pages/conciliacion.tsx` - URLs dinámicas
- `frontend/src/pages/preview_cierre.jsx` - URLs dinámicas
- `frontend/src/components/ConciliacionCompleta.tsx` - URLs dinámicas
- `backend/app/api_banco.py` - Mejorada búsqueda de archivo Excel
- `backend/requirements.txt` - Agregado numpy
- `render.yaml` - Configuración completa para Render

## 🚀 Pasos para Desplegar en Render

### Opción 1: Despliegue Automático con Blueprint (Recomendado) ✅

1. **Sube tu código a GitHub/GitLab/Bitbucket**
   ```bash
   git push origin main
   ```

2. **Crea un nuevo Blueprint en Render**
   - Ve a [render.com](https://render.com)
   - Inicia sesión o crea una cuenta
   - Click en **"New"** → **"Blueprint"** (o "New Blueprint")
   - Conecta tu repositorio de GitHub/GitLab/Bitbucket
   - Selecciona el repositorio `ConciliadorPOS`
   - Render detectará automáticamente el archivo `render.yaml` en la raíz

3. **Revisa la configuración del Blueprint**
   - Render mostrará una vista previa de los 3 servicios que se crearán:
     - ✅ Base de datos PostgreSQL (`conciliador-db`)
     - ✅ Backend FastAPI (`conciliador-backend`)
     - ✅ Frontend Next.js (`conciliador-frontend`)
   - Verifica que los nombres y configuraciones sean correctos

4. **Aplica el Blueprint**
   - Click en **"Apply"** o **"Create"**
   - Render comenzará a crear los servicios automáticamente

5. **Actualiza las Variables de Entorno** (después del primer despliegue)
   - Una vez que los servicios estén creados, ve a cada servicio y actualiza:
   - **Frontend**: `NEXT_PUBLIC_API_BASE` → `https://conciliador-backend.onrender.com`
   - **Backend**: `CORS_ORIGINS` → `https://conciliador-frontend.onrender.com`
   - ⚠️ **Nota**: Los nombres de los servicios en Render pueden tener un sufijo aleatorio (ej: `conciliador-backend-abc123`). Usa la URL real que Render te asigne.

6. **Espera a que se complete el despliegue**
   - El primer despliegue puede tardar 5-10 minutos
   - Render construirá automáticamente:
     - Base de datos PostgreSQL
     - Backend FastAPI (desde `backend/Dockerfile`)
     - Frontend Next.js (desde `frontend/Dockerfile`)

### Opción 2: Despliegue Manual

Si prefieres crear los servicios manualmente:

#### 1. Base de Datos PostgreSQL
- Tipo: PostgreSQL
- Nombre: `conciliador-db`
- Plan: Free (o el que prefieras)

#### 2. Backend FastAPI
- Tipo: Web Service
- Nombre: `conciliador-backend`
- Environment: Docker
- Dockerfile Path: `./backend/Dockerfile`
- Docker Context: `./backend`
- Variables de entorno:
  - `POSTGRES_USER`: (desde la base de datos)
  - `POSTGRES_PASSWORD`: (desde la base de datos)
  - `POSTGRES_DB`: (desde la base de datos)
  - `POSTGRES_HOST`: (desde la base de datos)
  - `POSTGRES_PORT`: (desde la base de datos)
  - `CORS_ORIGINS`: `https://tu-frontend.onrender.com`

#### 3. Frontend Next.js
- Tipo: Web Service
- Nombre: `conciliador-frontend`
- Environment: Docker
- Dockerfile Path: `./frontend/Dockerfile`
- Docker Context: `./frontend`
- Variables de entorno:
  - `NEXT_PUBLIC_API_BASE`: `https://tu-backend.onrender.com`

## ⚠️ Notas Importantes

1. **URLs en render.yaml**: He usado nombres de ejemplo (`conciliador-backend`, `conciliador-frontend`). **Debes actualizar estos nombres** en `render.yaml` con los nombres reales que uses en Render, o actualizar las variables de entorno después del despliegue.

2. **Archivo Excel**: El archivo `Lista_Punto_Venta.xlsx` debe estar en `backend/data/` para que se copie correctamente al contenedor.

3. **Primera ejecución**: El primer despliegue puede tardar varios minutos mientras Render construye las imágenes Docker.

4. **Plan Free**: Los servicios en plan free se "duermen" después de 15 minutos de inactividad. La primera petición después de dormir puede tardar ~30 segundos.

5. **Base de datos**: Aunque el proyecto tiene configuración de base de datos, actualmente no parece usarse activamente. Si no la necesitas, puedes eliminar el servicio de PostgreSQL del `render.yaml`.

## 🔍 Verificación Post-Despliegue

1. Verifica que el backend responda: `https://tu-backend.onrender.com/`
2. Verifica que el frontend cargue: `https://tu-frontend.onrender.com/`
3. Verifica la conexión entre frontend y backend en la consola del navegador

## 📝 Comandos Útiles

```bash
# Ver logs del backend
render logs --service conciliador-backend

# Ver logs del frontend
render logs --service conciliador-frontend

# Verificar estado de servicios
render services list
```

## 🐛 Solución de Problemas

- **Error 503**: El servicio puede estar iniciando, espera unos minutos
- **CORS errors**: Verifica que `CORS_ORIGINS` en el backend incluya la URL del frontend
- **404 en API**: Verifica que `NEXT_PUBLIC_API_BASE` esté configurado correctamente
- **Error al leer Excel**: Verifica que `Lista_Punto_Venta.xlsx` esté en `backend/data/`

---

**¡Tu proyecto está listo para desplegarse en Render!** 🎉

