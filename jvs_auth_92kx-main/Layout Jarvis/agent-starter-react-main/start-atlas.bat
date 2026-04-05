@echo off
title Atlas Front - Dev Mode
cd /d "%~dp0"

where pnpm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRO: pnpm nao esta instalado ou nao esta no PATH!
    pause
    exit /b
)

echo.
echo ================================
echo Iniciando Frontend Atlas
echo ================================
echo.

if not exist "node_modules" (
    echo Instalando dependencias...
    pnpm install
)

pnpm dev

pause