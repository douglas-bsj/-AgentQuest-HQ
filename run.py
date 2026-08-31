"""
AgentQuest HQ - Runner
Inicializa o servidor FastAPI e abre o navegador automaticamente em uma porta livre.
"""

import socket
import webbrowser
import threading
import uvicorn
import os
import time

HOST = "0.0.0.0"
PREFERRED_PORT = 8000


def find_free_port(start_port=8000, max_attempts=50):
    """Encontra uma porta TCP disponivel, evitando conflitos com outros servicos do Windows."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    return start_port


PORT = find_free_port(PREFERRED_PORT)
URL = f"http://{HOST}:{PORT}"


def open_browser():
    """Abre o navegador apos um breve delay para o servidor subir."""
    time.sleep(1.2)
    webbrowser.open(URL)
    print(f"\n[OK] Navegador aberto com sucesso em {URL}")


if __name__ == "__main__":
    print("=" * 60)
    print("  AgentQuest HQ - Servidor Local")
    print("=" * 60)
    print(f"  Painel Web:   {URL}")
    print(f"  API:          {URL}/api/stats")
    print(f"  Docs:         {URL}/docs")
    print("=" * 60)
    print("  Pressione Ctrl+C para encerrar.\n")

    # Abrir navegador em thread separada
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor FastAPI
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
