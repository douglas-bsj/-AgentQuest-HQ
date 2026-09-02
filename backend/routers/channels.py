"""
Channels Router — AgentQuest HQ

Endpoints usados pela aba "Canais" do painel de configurações para dar
visibilidade e controle sobre a conexão do WhatsApp, qualquer que seja o
provedor escolhido:

  baileys       — ponte local em Node (sem Docker), pareamento por QR Code
  meta_official — WhatsApp Cloud API oficial da Meta (nada instalado)
  evolution     — Evolution API via Docker
  mock          — apenas gera link wa.me para envio manual
"""

from fastapi import APIRouter

from backend.tools.settings_manager import settings_manager
from backend.tools import baileys_manager, meta_cloud_manager
from backend.tools.evolution_manager import (
    get_whatsapp_status as evolution_status,
    request_qr_code as evolution_qr,
    start_evolution_stack,
)

router = APIRouter(prefix="/api/channels", tags=["channels"])


def _provider() -> str:
    return (
        settings_manager.get_settings()
        .get("channels", {})
        .get("whatsapp", {})
        .get("provider", "baileys")
    )


@router.get("/whatsapp/status")
def whatsapp_status():
    """Status consolidado da conexão, conforme o provedor configurado."""
    settings = settings_manager.get_settings()
    provider = _provider()

    if provider == "baileys":
        return baileys_manager.get_whatsapp_status(settings)
    if provider == "meta_official":
        return meta_cloud_manager.get_whatsapp_status(settings)
    if provider == "evolution":
        return evolution_status(settings)

    # mock / wa.me: não há conexão a manter
    return {
        "enabled": settings.get("channels", {}).get("whatsapp", {}).get("enabled", False),
        "provider": provider,
        "instance_state": "manual",
        "docker_installed": True,
        "docker_running": True,
        "evolution_reachable": True,
        "last_error": None,
    }


@router.post("/whatsapp/connect")
def whatsapp_connect():
    """Inicia o pareamento: devolve QR Code (Baileys/Evolution) ou valida
    credenciais (Meta)."""
    settings = settings_manager.get_settings()
    provider = _provider()

    if provider == "baileys":
        return baileys_manager.request_qr_code(settings)

    if provider == "meta_official":
        status = meta_cloud_manager.get_whatsapp_status(settings)
        if status.get("instance_state") == "open":
            return {
                "status": "already_connected",
                "message": f"Número {status.get('connected_number')} conectado via Meta Cloud API.",
            }
        return {"status": "error", "message": status.get("last_error", "Credenciais inválidas.")}

    if provider == "evolution":
        stack = start_evolution_stack(settings)
        if stack["status"] in ("docker_missing", "docker_not_running", "compose_failed"):
            return {"status": "error", "message": stack["message"]}
        return evolution_qr(settings)

    return {
        "status": "manual",
        "message": "No modo link wa.me não há conexão a parear — o envio é feito com um clique.",
    }


@router.post("/whatsapp/disconnect")
def whatsapp_disconnect():
    """Encerra a sessão local (aplicável ao Baileys)."""
    if _provider() != "baileys":
        return {"status": "error", "message": "Desconexão disponível apenas no provedor Baileys."}
    return baileys_manager.logout()


@router.post("/whatsapp/restart-stack")
def whatsapp_restart_stack():
    """Reinicia a infraestrutura do provedor atual."""
    settings = settings_manager.get_settings()
    provider = _provider()

    if provider == "baileys":
        return baileys_manager.start_bridge(
            ignore_groups=settings.get("channels", {}).get("whatsapp", {}).get("ignore_groups", True)
        )
    if provider == "evolution":
        return start_evolution_stack(settings)

    return {"status": "not_applicable", "message": "Este provedor não mantém infraestrutura local."}
