# Backend package

# Configura o console em UTF-8 no import do pacote — cobre todas as formas de
# entrada (start_system.py, run.py, uvicorn direto) num unico ponto, evitando
# que mensagens com emoji quebrem os logs e, com eles, o processamento.
from backend.utils.console import configurar_console_utf8

configurar_console_utf8()
