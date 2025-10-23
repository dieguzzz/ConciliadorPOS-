# 🐳 **ConciliadorPOS — Guía de Inicio y Apagado con Docker Compose**

Esta guía explica **cómo levantar, apagar y mantener** el entorno completo del proyecto **ConciliadorPOS** usando **Docker Compose**.

---

## 🧩 **Servicios que Docker levanta**

| Servicio | Descripción | Puerto |
|-----------|--------------|--------|
| 🐍 **backend** | FastAPI + Uvicorn (procesa archivos, conciliaciones, API REST) | `8000` |
| 💜 **frontend** | Next.js (interfaz web de ConciliadorPOS) | `3000` |
| 🐘 **db** | PostgreSQL 15 (base de datos interna) | `5432` |

---

## 🚀 **Cómo INICIAR todo**

### 🔹 Paso 1 — Abrir Docker Desktop
1. Abre **Docker Desktop** desde el menú Inicio.  
2. Espera hasta que diga:  
   > **“Docker Desktop is running”**  
   (icono de la ballena en la bandeja del sistema debe estar estable).

---

### 🔹 Paso 2 — Abrir el proyecto
1. Abre **VS Code** o PowerShell en:
   ```bash
   C:\Users\Diegu\ConciliadorPOS
   ```
2. Abre la terminal integrada (Ctrl + `).

---

### 🔹 Paso 3 — Levantar todos los servicios
Ejecuta:
```bash
docker compose up --build
```

🔸 Esto:
- Construye las imágenes (`build`) del backend, frontend y base de datos.
- Inicia los tres contenedores conectados entre sí.
- Muestra los logs en tiempo real.

---

### 🔹 Paso 4 — Esperar hasta ver los mensajes de arranque
Cuando aparezcan estas líneas:
```
backend  | Application startup complete.
frontend | Ready on http://localhost:3000
db       | database system is ready to accept connections
```

✅ Todo está corriendo correctamente.

---

### 🔹 Paso 5 — Abrir en el navegador

| Servicio | URL |
|-----------|-----|
| 🖥️ Frontend (app web) | [http://localhost:3000](http://localhost:3000) |
| ⚙️ API FastAPI (docs) | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 🛑 **Cómo APAGAR todo correctamente**

### 🔹 Paso 1 — Detener ejecución
En la misma terminal donde está corriendo Docker Compose, presiona:
```
CTRL + C
```

Deberías ver:
```
Gracefully stopping... done
```

---

### 🔹 Paso 2 — Apagar contenedores
Ejecuta:
```bash
docker compose down
```

Esto detiene y elimina los contenedores activos sin borrar tus datos persistentes.

---

### 🔹 Paso 3 — (Opcional) limpiar basura vieja
Para liberar espacio (imágenes o redes no usadas):
```bash
docker system prune -f
```

---

### 🔹 Paso 4 — Cerrar Docker Desktop
Haz clic derecho en el icono de la ballena → **Quit Docker Desktop**.

---

## 🧠 **Comandos útiles**

| Acción | Comando | Descripción |
|--------|----------|-------------|
| 🔍 Ver logs en tiempo real | `docker compose logs -f` | Muestra actividad de todos los servicios |
| 🔁 Reiniciar rápido | `docker compose restart` | Reinicia sin rebuild |
| 🚫 Forzar cierre | `docker compose stop` | Detiene sin borrar |
| 🧱 Ver contenedores activos | `docker ps` | Lista contenedores en ejecución |

---

## ⚙️ **Notas adicionales**

- El contenedor `backend` usa **Python 3.10** y `openpyxl`, `pandas`, `fastapi`, etc.
- El contenedor `frontend` ejecuta **Next.js 15.5.6** con `npm run dev`.
- Si ves advertencias tipo `Workbook contains no default style` o `dayfirst=False`, son **avisos inofensivos** de pandas y openpyxl.
- El contenedor `db` mantiene los datos en el volumen persistente definido en `docker-compose.yml`.

---

## ✅ **Checklist de inicio rápido**

1. 🐳 Docker Desktop abierto y corriendo.  
2. 📂 Terminal en carpeta del proyecto (`ConciliadorPOS`).  
3. ▶️ Ejecutar `docker compose up --build`.  
4. 🌐 Abrir [http://localhost:3000](http://localhost:3000).  
5. 💾 Para apagar → `CTRL + C` → `docker compose down`.
