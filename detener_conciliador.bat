@echo off
title 🛑 Detener Conciliador POS
color 0C
echo =====================================================
echo          CERRANDO SISTEMA CONCILIADOR POS
echo =====================================================

:: === Cerrar puerto 8000 (Backend) ===
echo Buscando procesos en puerto 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo 🔴 Cerrando proceso %%a (Backend)
    taskkill /F /PID %%a >nul 2>&1
)

:: === Cerrar puerto 3000 (Frontend) ===
echo Buscando procesos en puerto 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo 🔴 Cerrando proceso %%a (Frontend)
    taskkill /F /PID %%a >nul 2>&1
)

:: === Confirmación final ===
echo.
echo =====================================================
echo ✅ Todos los servicios del Conciliador POS fueron detenidos.
echo =====================================================
pause
