"""
AgentQuest HQ - Runner
Inicializa o servidor FastAPI e abre o navegador automaticamente.
"""

import webbrowser
import threading
import uvicorn

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser():
    """Abre o navegador apos um breve delay para o servidor subir."""
    import time
    time.sleep(1.5)
    webbrowser.open(URL)
    print(f"\n[OK] Navegador aberto em {URL}")


if __name__ == "__main__":
    print("=" * 60)
    print("  AgentQuest HQ - Servidor Local")
    print("=" * 60)
    print(f"  API:      {URL}/api/stats")
    print(f"  Painel:   {URL}")
    print(f"  Docs:     {URL}/docs")
    print("=" * 60)
    print("  Pressione Ctrl+C para encerrar.\n")

    # Abrir navegador em thread separada
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
