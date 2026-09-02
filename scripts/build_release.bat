@echo off
title AgentQuest HQ - Build de Release
color 0B
cd /d "%~dp0.."

echo ============================================================
echo      AGENTQUEST HQ - GERANDO INSTALADOR DE DISTRIBUICAO
echo ============================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit /b
)

echo [1/2] Instalando dependencias de build...
python -m pip install -r requirements-build.txt --quiet --disable-pip-version-check

echo [2/2] Rodando pipeline de build...
echo.
python scripts\build_release.py %*

echo.
pause
