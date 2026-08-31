@echo off
title Evolution API - WhatsApp Server
color 0A
cd /d "%~dp0"

echo ============================================================
echo      INICIANDO EVOLUTION API (WHATSAPP SERVER)
echo ============================================================
echo.

where docker >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERRO] O Docker Desktop nao esta instalado ou nao esta aberto!
    echo Abra o aplicativo Docker Desktop e tente novamente.
    pause
    exit /b
)

echo [1/2] Iniciando servicos da Evolution API (PostgreSQL + Redis + API)...
docker compose -f docker-compose.evolution.yml up -d

echo.
echo [2/2] Evolution API pronta e online na porta 8080!
echo.
echo ============================================================
echo   Chave Global API (API Key): agentquest-secreto-123
echo   Painel Manager (QR Code):   http://localhost:8080/manager
echo ============================================================
echo.
echo Abrindo o painel no seu navegador...
timeout /t 2 /nobreak >nul
start http://localhost:8080/manager

pause
