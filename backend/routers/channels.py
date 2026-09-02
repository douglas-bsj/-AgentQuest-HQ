"""
Channels Router — AgentQuest HQ

Endpoints usados pela aba "Canais" do painel de configurações para dar
visibilidade e controle sobre a conexão do WhatsApp (Evolution API):
status consolidado (Docker + containers + pareamento), disparo de conexão
com QR Code, e reinício da stack Docker.
"""

from fastapi import APIRouter

from backend.tools.settings_manager import settings_manager
from backend.tools.evolution_manager import (
    get_whatsapp_status,
    request_qr_code,
    start_evolution_stack,
)

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("/whatsapp/status")
def whatsapp_status():
    """Status consolidado: Docker instalado/rodando e estado de pareamento da instância."""
    settings = settings_manager.get_settings()
    return get_whatsapp_status(settings)


@router.post("/whatsapp/connect")
def whatsapp_connect():
    """Garante a stack no ar e retorna o QR Code (base64) para pareamento."""
    settings = settings_manager.get_settings()

    stack_result = start_evolution_stack(settings)
    if stack_result["status"] in ("docker_missing", "docker_not_running", "compose_failed"):
        return {"status": "error", "message": stack_result["message"]}

    return request_qr_code(settings)


@router.post("/whatsapp/restart-stack")
def whatsapp_restart_stack():
    """Força um novo `docker compose up -d` da stack da Evolution API."""
    settings = settings_manager.get_settings()
    return start_evolution_stack(settings)
