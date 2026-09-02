@echo off
title AgentQuest HQ - Inicializador Unificado
color 0A
cd /d "%~dp0"

echo ============================================================
echo      AGENTQUEST HQ - INICIANDO SISTEMA COMPLETO
echo ============================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY=python"
    goto :START
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY=py"
    goto :START
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :START
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :START
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START
)

echo [ERRO] Python nao encontrado! Instale o Python 3.11+ antes de continuar.
pause
exit /b

:START
echo [1/2] Verificando dependencias...
"%PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Iniciando AgentQuest HQ (WhatsApp + IA local + Backend + Painel)...
echo.
"%PY%" start_system.py

pause
