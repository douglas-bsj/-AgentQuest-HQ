@echo off
chcp 65001 >nul
echo ============================================================
echo   AgentQuest HQ - Inicialização Híbrida
echo ============================================================
echo.
echo Iniciando o Servidor API do Hermes Agent em segundo plano...
start "Hermes API Server" cmd /k "%LOCALAPPDATA%\hermes\bin\hermes.exe gateway"

echo.
echo Aguardando 5 segundos para o Hermes preparar a porta 8642...
timeout /t 5 /nobreak >nul

echo.
echo Iniciando o Painel do AgentQuest HQ...
start "AgentQuest HQ" cmd /k "python run.py"

echo.
echo Tudo iniciado! 
echo O painel abrirá automaticamente no navegador em http://127.0.0.1:8000
echo.
echo Pode fechar esta janela principal, as janelas dos servidores continuarão rodando.
pause
