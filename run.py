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

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PREFERRED_PORT = 8000


def find_free_port(host, start_port=8000, max_attempts=50):
    """Encontra uma porta TCP disponivel, evitando conflitos com outros servicos do Windows."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    return start_port


def _open_browser(url):
    """Abre o navegador apos um breve delay para o servidor subir."""
    time.sleep(1.2)
    webbrowser.open(url)
    print(f"\n[OK] Navegador aberto com sucesso em {url}")


def start_backend(host=DEFAULT_HOST, preferred_port=DEFAULT_PREFERRED_PORT, open_browser_tab=True):
    """Inicia o servidor FastAPI, escolhendo uma porta livre e abrindo o painel no navegador."""
    port = find_free_port(host, preferred_port)
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("  AgentQuest HQ - Servidor Local")
    print("=" * 60)
    print(f"  Painel Web:   {url}")
    print(f"  API:          {url}/api/stats")
    print(f"  Docs:         {url}/docs")
    print("=" * 60)
    print("  Pressione Ctrl+C para encerrar.\n")

    if open_browser_tab:
        threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    # O app é passado como objeto, não como string "backend.main:app": no
    # executável congelado o uvicorn não consegue resolver o módulo por nome.
    # loop/http explícitos evitam a autodetecção de uvloop/httptools (libs
    # opcionais, ausentes do requirements.txt), que também falha no pacote.
    from backend.main import app
    uvicorn.run(app, host=host, port=port, reload=False, loop="asyncio", http="h11")


if __name__ == "__main__":
    start_backend()
