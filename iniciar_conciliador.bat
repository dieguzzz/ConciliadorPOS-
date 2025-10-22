@echo off
title 🚀 Conciliador POS - Black Dog
color 0E
echo =====================================================
echo          INICIANDO SISTEMA CONCILIADOR POS
echo =====================================================
echo.

:: === Verifica si ya existe puerto 8000 o 3000 ocupados ===
echo Verificando puertos en uso...
netstat -ano | findstr :8000 >nul
if %errorlevel%==0 (
    echo ⚠ Puerto 8000 en uso (Backend). Cerrando proceso...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
)
netstat -ano | findstr :3000 >nul
if %errorlevel%==0 (
    echo ⚠ Puerto 3000 en uso (Frontend). Cerrando proceso...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /F /PID %%a >nul 2>&1
)
echo ✅ Puertos libres.
echo.

:: === Abre Backend ===
echo Iniciando BACKEND (FastAPI)...
cd backend
start cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo Backend ejecutándose en http://localhost:8000
cd ..

:: === Abre Frontend ===
echo Iniciando FRONTEND (Next.js)...
cd frontend
set NEXT_PUBLIC_API_BASE=http://localhost:8000
start cmd /k "npm run dev"
cd ..
echo Frontend ejecutándose en http://localhost:3000
echo.

echo =====================================================
echo ✅ El sistema Conciliador POS está en marcha
echo    - Backend: http://localhost:8000/docs
echo    - Frontend: http://localhost:3000/conciliacion
echo =====================================================
pause
