"""
Baileys Manager — AgentQuest HQ

Gerencia a ponte local de WhatsApp (whatsapp-bridge, Node.js + Baileys):
sobe o processo, consulta status, obtem o QR Code de pareamento e envia
mensagens. Nao depende de Docker, Postgres, Redis nem virtualizacao — a
sessao do WhatsApp fica em arquivos locais.

Expoe a mesma forma de retorno do evolution_manager, para que a aba Canais
e o dispatcher tratem os dois provedores do mesmo jeito.
"""

import os
import shutil
import subprocess
import time

import httpx

from backend.utils.paths import base_path, resource_path

BRIDGE_DIR = resource_path("whatsapp-bridge")
BRIDGE_PORT = 8765
BRIDGE_URL = f"http://127.0.0.1:{BRIDGE_PORT}"

# Node portatil embarcado no instalador; se ausente, cai no Node do sistema.
NODE_EMBUTIDO = resource_path("node", "node.exe")

_processo = None


def node_executable() -> str | None:
    if os.path.isfile(NODE_EMBUTIDO):
        return NODE_EMBUTIDO
    return shutil.which("node")


def node_disponivel() -> bool:
    return node_executable() is not None


def bridge_respondendo(timeout: float = 1.5) -> bool:
    try:
        resp = httpx.get(f"{BRIDGE_URL}/status", timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def start_bridge(agentquest_port: int = 8000, ignore_groups: bool = True) -> dict:
    """Sobe a ponte Node se ela ainda nao estiver respondendo."""
    global _processo

    if bridge_respondendo():
        return {"status": "already_running", "message": "Ponte de WhatsApp ja esta ativa."}

    node = node_executable()
    if not node:
        return {
            "status": "node_missing",
            "message": "Node.js nao encontrado (nem embutido, nem no sistema).",
        }

    entrada = os.path.join(BRIDGE_DIR, "index.js")
    if not os.path.isfile(entrada):
        return {"status": "bridge_missing", "message": f"Ponte nao encontrada em {BRIDGE_DIR}."}

    if not os.path.isdir(os.path.join(BRIDGE_DIR, "node_modules")):
        return {
            "status": "deps_missing",
            "message": "Dependencias da ponte ausentes (node_modules).",
        }

    env = os.environ.copy()
    env["BRIDGE_PORT"] = str(BRIDGE_PORT)
    env["AGENTQUEST_URL"] = f"http://localhost:{agentquest_port}"
    # A sessao fica junto dos dados do usuario, nao dentro dos arquivos do app,
    # para sobreviver a reinstalacoes e atualizacoes.
    env["AUTH_DIR"] = base_path("whatsapp_session")
    env["IGNORE_GROUPS"] = "true" if ignore_groups else "false"

    # O log da ponte vai para arquivo em vez de ser descartado: sem ele nao ha
    # como diagnosticar o que o WhatsApp entregou (JIDs, tipos de remetente,
    # falhas de conexao).
    log_path = base_path("whatsapp-bridge.log")
    try:
        log_file = open(log_path, "a", encoding="utf-8")
        _processo = subprocess.Popen(
            [node, entrada],
            cwd=BRIDGE_DIR,
            env=env,
            stdout=log_file,
            stderr=log_file,
        )
    except Exception as e:
        return {"status": "error", "message": f"Falha ao iniciar a ponte: {e}"}

    for _ in range(20):
        if bridge_respondendo():
            return {"status": "started", "message": "Ponte de WhatsApp iniciada."}
        time.sleep(0.5)

    return {"status": "timeout", "message": "A ponte foi iniciada, mas ainda nao respondeu."}


def get_whatsapp_status(settings: dict) -> dict:
    """Status consolidado no mesmo formato usado pela aba Canais."""
    wa_cfg = settings.get("channels", {}).get("whatsapp", {})

    ponte_ativa = bridge_respondendo()
    estado = "not_created"
    numero = None
    erro = None

    if ponte_ativa:
        try:
            resp = httpx.get(f"{BRIDGE_URL}/status", timeout=3)
            if resp.status_code == 200:
                dados = resp.json()
                bridge_state = dados.get("state", "close")
                # Traduz para os mesmos estados que a UI ja entende
                estado = {
                    "open": "open",
                    "connecting": "connecting",
                    "close": "not_created",
                }.get(bridge_state, "not_created")
                numero = dados.get("number")
                erro = dados.get("last_error")
        except Exception as e:
            erro = str(e)

    return {
        "enabled": wa_cfg.get("enabled", False),
        "provider": "baileys",
        "node_installed": node_disponivel(),
        "bridge_running": ponte_ativa,
        "instance_state": estado,
        "connected_number": numero,
        "last_error": erro,
        # Campos mantidos para compatibilidade com a UI compartilhada
        "docker_installed": True,
        "docker_running": True,
        "evolution_reachable": ponte_ativa,
    }


def request_qr_code(settings: dict) -> dict:
    """Garante a ponte no ar e devolve o QR Code para pareamento."""
    wa_cfg = settings.get("channels", {}).get("whatsapp", {})

    resultado = start_bridge(ignore_groups=wa_cfg.get("ignore_groups", True))
    if resultado["status"] in ("node_missing", "bridge_missing", "deps_missing", "error"):
        return {"status": "error", "message": resultado["message"]}

    # O QR pode levar alguns segundos para ser gerado apos o boot da ponte
    for _ in range(20):
        try:
            resp = httpx.get(f"{BRIDGE_URL}/qr", timeout=3)
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("qr_base64"):
                    return {"status": "qr_ready", "qr_base64": dados["qr_base64"]}
            elif resp.status_code == 404:
                if resp.json().get("status") == "already_connected":
                    return {"status": "already_connected", "message": "WhatsApp ja esta conectado."}
        except Exception:
            pass
        time.sleep(1)

    return {"status": "error", "message": "A ponte nao gerou o QR Code a tempo."}


def peek_qr_code() -> dict:
    """Le o QR atual sem tentar iniciar nada — usado no polling da tela.

    O QR do WhatsApp expira em poucos segundos e a ponte gera um novo; a UI
    precisa reler com frequencia, e por isso esta consulta e barata.
    """
    try:
        resp = httpx.get(f"{BRIDGE_URL}/qr", timeout=3)
        if resp.status_code == 200:
            dados = resp.json()
            if dados.get("qr_base64"):
                return {"status": "qr_ready", "qr_base64": dados["qr_base64"]}
        elif resp.status_code == 404:
            return {"status": resp.json().get("status", "no_qr")}
        return {"status": "no_qr"}
    except Exception:
        return {"status": "bridge_offline"}


def send_text(numero: str, texto: str) -> dict:
    """Envia mensagem pela ponte. Retorna dict no formato do dispatcher."""
    try:
        resp = httpx.post(
            f"{BRIDGE_URL}/send",
            json={"number": numero, "text": texto},
            timeout=20,
        )
        if resp.status_code == 200:
            return {"status": "sent", "method": "Baileys (ponte local)"}
        return {"status": "error", "message": f"Ponte retornou {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao falar com a ponte: {e}"}


def logout() -> dict:
    """Desconecta a conta e apaga a sessao local."""
    try:
        resp = httpx.post(f"{BRIDGE_URL}/logout", timeout=15)
        if resp.status_code == 200:
            return {"status": "logged_out", "message": "Sessao do WhatsApp encerrada."}
        return {"status": "error", "message": f"Ponte retornou {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao encerrar sessao: {e}"}
