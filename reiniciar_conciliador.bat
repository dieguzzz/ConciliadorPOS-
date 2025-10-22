@echo off
title 🔁 Reiniciar Conciliador POS
color 0E
echo =====================================================
echo         REINICIANDO SISTEMA CONCILIADOR POS
echo =====================================================

:: === 1. Cerrar procesos en puertos 8000 y 3000 ===
echo Buscando procesos activos...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo 🔴 Cerrando proceso %%a (Backend)
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo 🔴 Cerrando proceso %%a (Frontend)
    taskkill /F /PID %%a >nul 2>&1
)
echo ✅ Procesos anteriores cerrados.
echo.

:: === 2. Verifica rutas ===
cd /d "%~dp0"
if not exist backend (
    echo ❌ No se encontró la carpeta "backend"
    pause
    exit
)
if not exist frontend (
    echo ❌ No se encontró la carpeta "frontend"
    pause
    exit
)

:: === 3. Iniciar BACKEND ===
echo Iniciando BACKEND (FastAPI)...
cd backend
start cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..
echo ✅ Backend corriendo en http://localhost:8000
echo.

:: === 4. Iniciar FRONTEND ===
echo Iniciando FRONTEND (Next.js)...
cd frontend
set NEXT_PUBLIC_API_BASE=http://localhost:8000
start cmd /k "npm run dev"
cd ..
echo ✅ Frontend corriendo en http://localhost:3000
echo.

:: === 5. Mensaje final ===
echo =====================================================
echo ✅ Conciliador POS listo para usar
echo    - Backend:  http://localhost:8000/docs
echo    - Frontend: http://localhost:3000/conciliacion
echo =====================================================
pause
