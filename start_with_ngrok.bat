@echo off
title AgentQuest HQ ? Servidor + Ngrok
color 0A
echo.
echo  =============================================
echo   AgentQuest HQ - Iniciando servidor + Ngrok
echo  =============================================
echo.

REM Verifica se o arquivo .env existe
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado!
    echo Copie o .env.example para .env e preencha suas chaves.
    copy .env.example .env
    echo.
    echo Arquivo .env criado. Por favor, edite-o com suas chaves antes de continuar.
    pause
    notepad .env
    pause
)

echo [1/2] Iniciando servidor backend...
start "AgentQuest HQ - Backend" cmd /k "python run.py"

timeout /t 3 /nobreak >nul

echo [2/2] Iniciando tunel Ngrok...
echo.
echo Aguarde o Ngrok gerar a URL publica...
echo Copie a URL "Forwarding" e envie para os testadores!
echo.
echo IMPORTANTE: Mantenha esta janela aberta enquanto os testadores estiverem usando.
echo.
ngrok http 8000

pause
