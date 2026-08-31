@echo off
title AgentQuest HQ
color 0A
cd /d "%~dp0"

echo ============================================================
echo      INICIANDO AGENTQUEST HQ
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

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :START
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :START
)
if exist "C:\Python311\python.exe" (
    set "PY=C:\Python311\python.exe"
    goto :START
)
if exist "C:\Python312\python.exe" (
    set "PY=C:\Python312\python.exe"
    goto :START
)
if exist "C:\Python313\python.exe" (
    set "PY=C:\Python313\python.exe"
    goto :START
)

echo [ERRO] Python nao encontrado!
pause
exit /b

:START
echo [1/2] Instalando/Verificando dependencias...
"%PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Iniciando servidor e abrindo painel...
"%PY%" run.py

pause
