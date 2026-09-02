"""
Baixa o Node.js portatil usado pela ponte de WhatsApp (Baileys).

O node.exe tem ~90 MB e por isso nao e versionado no git — este script o
obtem sob demanda, deixando o build reprodutivel em qualquer clone.

Uso:
    python scripts/fetch_node.py
"""

import io
import os
import shutil
import sys
import urllib.request
import zipfile

NODE_VERSION = "v24.20.0"  # LTS
NODE_ZIP_URL = f"https://nodejs.org/dist/{NODE_VERSION}/node-{NODE_VERSION}-win-x64.zip"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR_DIR = os.path.join(PROJECT_ROOT, "build", "vendor", "node")
NODE_EXE = os.path.join(VENDOR_DIR, "node.exe")
VERSION_STAMP = os.path.join(VENDOR_DIR, "VERSION")


def node_ja_baixado() -> bool:
    if not os.path.isfile(NODE_EXE):
        return False
    if not os.path.isfile(VERSION_STAMP):
        return False
    with open(VERSION_STAMP, encoding="utf-8") as f:
        return f.read().strip() == NODE_VERSION


def fetch_node(force: bool = False) -> str:
    """Garante o node.exe em build/vendor/node/ e devolve o caminho."""
    if node_ja_baixado() and not force:
        print(f"[Node] {NODE_VERSION} ja disponivel em {NODE_EXE}")
        return NODE_EXE

    os.makedirs(VENDOR_DIR, exist_ok=True)
    print(f"[Node] Baixando {NODE_VERSION} (~36 MB)...")

    with urllib.request.urlopen(NODE_ZIP_URL, timeout=300) as resp:
        dados = resp.read()

    print("[Node] Extraindo node.exe...")
    with zipfile.ZipFile(io.BytesIO(dados)) as zf:
        nome_interno = f"node-{NODE_VERSION}-win-x64/node.exe"
        if nome_interno not in zf.namelist():
            raise RuntimeError(f"node.exe nao encontrado no zip ({nome_interno}).")
        with zf.open(nome_interno) as origem, open(NODE_EXE, "wb") as destino:
            shutil.copyfileobj(origem, destino)

    with open(VERSION_STAMP, "w", encoding="utf-8") as f:
        f.write(NODE_VERSION)

    tamanho_mb = os.path.getsize(NODE_EXE) / (1024 * 1024)
    print(f"[Node] Pronto: {NODE_EXE} ({tamanho_mb:.0f} MB)")
    return NODE_EXE


if __name__ == "__main__":
    fetch_node(force="--force" in sys.argv)
