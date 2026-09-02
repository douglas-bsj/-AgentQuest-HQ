"""
AgentQuest HQ - Runner
Inicializa o servidor FastAPI e abre o navegador automaticamente em uma porta livre.
"""

import json
import socket
import webbrowser
import threading
import urllib.request
import uvicorn
import os
import time

# Host de escuta: 0.0.0.0 aceita conexões de qualquer interface (permite acessar
# o painel de outro dispositivo da rede local).
DEFAULT_HOST = "0.0.0.0"
# Host de navegação: 0.0.0.0 NÃO é um endereço navegável — o navegador responde
# ERR_ADDRESS_INVALID. Toda URL exibida ou aberta usa este host.
BROWSE_HOST = "localhost"
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


def find_running_instance(start_port=8000, max_attempts=5):
    """Procura uma instancia do AgentQuest HQ ja no ar e retorna a porta dela.

    Evita subir um segundo servidor quando o atalho e clicado com o app ja
    rodando (por exemplo, iniciado junto com o Windows) — duas instancias
    disputariam o mesmo banco e o mesmo cofre.
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with urllib.request.urlopen(f"http://{BROWSE_HOST}:{port}/api/stats", timeout=1) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    if all(k in payload for k in ("pending", "approved", "rejected")):
                        return port
        except Exception:
            continue
    return None


def start_backend(host=DEFAULT_HOST, preferred_port=DEFAULT_PREFERRED_PORT, open_browser_tab=True):
    """Inicia o servidor FastAPI, escolhendo uma porta livre e abrindo o painel no navegador."""
    ja_rodando = find_running_instance(preferred_port)
    if ja_rodando:
        url = f"http://{BROWSE_HOST}:{ja_rodando}"
        print("=" * 60)
        print("  AgentQuest HQ ja esta em execucao")
        print("=" * 60)
        print(f"  Abrindo o painel existente em {url}")
        print("=" * 60)
        if open_browser_tab:
            webbrowser.open(url)
        return

    port = find_free_port(host, preferred_port)
    url = f"http://{BROWSE_HOST}:{port}"

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
