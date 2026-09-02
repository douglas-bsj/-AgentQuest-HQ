"""
Evolution Manager — AgentQuest HQ

Orquestra a stack Docker da Evolution API (WhatsApp): sobe os containers,
verifica status (Docker instalado/rodando, containers, API HTTP) e consulta/
inicia o pareamento da instância. Usado tanto pelo boot (start_system.py)
quanto pelos endpoints da aba Channels do painel.
"""

import shutil
import subprocess
import time

import httpx

from backend.utils.paths import base_path, resource_path

EVOLUTION_COMPOSE_FILE = resource_path("docker-compose.evolution.yml")


def docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_running() -> bool:
    if not docker_available():
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def start_evolution_stack(settings: dict) -> dict:
    """Sobe os containers da Evolution API via Docker Compose, se habilitada nas configurações.

    Retorna um dict estruturado (nunca só print) para ser reaproveitado tanto pelo
    console de boot quanto pelos endpoints HTTP da aba Channels.
    """
    wa_cfg = settings.get("channels", {}).get("whatsapp", {})

    if not wa_cfg.get("enabled") or wa_cfg.get("provider") != "evolution":
        return {"status": "disabled", "message": "Canal Evolution API desabilitado nas configurações."}

    if not docker_available():
        return {"status": "docker_missing", "message": "Docker não encontrado no PATH."}

    if not docker_running():
        return {"status": "docker_not_running", "message": "Docker Desktop não está rodando."}

    result = subprocess.run(
        ["docker", "compose", "-f", EVOLUTION_COMPOSE_FILE, "up", "-d"],
        cwd=base_path(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"status": "compose_failed", "message": result.stderr.strip()}

    return {"status": "started", "message": "Containers da Evolution API iniciados."}


def wait_for_evolution_api(api_url: str, timeout_seconds: int = 20) -> bool:
    """Faz polling HTTP até a Evolution API responder, ou desiste após o timeout."""
    api_url = api_url.rstrip("/")
    for _ in range(timeout_seconds):
        try:
            resp = httpx.get(api_url, timeout=2)
            if resp.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def get_connection_state(api_url: str, instance: str, api_token: str) -> str:
    """Consulta o estado de pareamento da instância na Evolution API.

    Retorna: "open" (conectado), "connecting", "close" (desconectado),
    "not_created" (instância ainda não existe) ou "unreachable".
    """
    try:
        resp = httpx.get(
            f"{api_url.rstrip('/')}/instance/connectionState/{instance}",
            headers={"apikey": api_token},
            timeout=5,
        )
        if resp.status_code == 404:
            return "not_created"
        if resp.status_code == 200:
            data = resp.json()
            return data.get("instance", {}).get("state", "unreachable")
        return "unreachable"
    except Exception:
        return "unreachable"


def get_whatsapp_status(settings: dict) -> dict:
    """Status consolidado para a aba Channels: Docker, containers e pareamento."""
    wa_cfg = settings.get("channels", {}).get("whatsapp", {})
    api_url = wa_cfg.get("api_url", "http://localhost:8080")
    instance = wa_cfg.get("instance_name", "agentquest")
    api_token = wa_cfg.get("api_token", "")

    installed = docker_available()
    running = docker_running()
    evolution_reachable = False
    instance_state = "not_created"

    if running:
        try:
            resp = httpx.get(api_url.rstrip("/"), timeout=2)
            evolution_reachable = resp.status_code < 500
        except Exception:
            evolution_reachable = False

        if evolution_reachable:
            instance_state = get_connection_state(api_url, instance, api_token)

    return {
        "enabled": wa_cfg.get("enabled", False),
        "docker_installed": installed,
        "docker_running": running,
        "evolution_reachable": evolution_reachable,
        "instance_state": instance_state,
    }


def request_qr_code(settings: dict) -> dict:
    """Garante a instância criada e retorna o QR Code em base64 para pareamento."""
    wa_cfg = settings.get("channels", {}).get("whatsapp", {})
    api_url = wa_cfg.get("api_url", "http://localhost:8080").rstrip("/")
    instance = wa_cfg.get("instance_name", "agentquest")
    api_token = wa_cfg.get("api_token", "")
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    state = get_connection_state(api_url, instance, api_token)
    if state == "not_created":
        try:
            httpx.post(
                f"{api_url}/instance/create",
                json={"instanceName": instance, "qrcode": True, "integration": "WHATSAPP-BAILEYS"},
                headers=headers,
                timeout=15,
            )
        except Exception as e:
            return {"status": "error", "message": f"Falha ao criar instância: {e}"}

    try:
        resp = httpx.get(f"{api_url}/instance/connect/{instance}", headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            qr_base64 = data.get("base64")
            if qr_base64:
                return {"status": "qr_ready", "qr_base64": qr_base64}
            return {"status": "already_connected", "message": "Instância já conectada ou sem QR pendente."}
        return {"status": "error", "message": f"Evolution API retornou {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"status": "error", "message": f"Falha ao solicitar QR Code: {e}"}
