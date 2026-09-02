"""
Meta Cloud Manager — AgentQuest HQ

Integracao com a WhatsApp Cloud API oficial da Meta. Nao exige nada instalado
na maquina: o WhatsApp roda na infraestrutura da Meta.

O que precisa ser configurado na aba Canais:
  - Phone Number ID  (Meta for Developers > WhatsApp > API Setup)
  - Access Token     (token permanente do App/System User)
  - Verify Token     (string escolhida por voce, usada ao registrar o webhook)

Atencao ao recebimento: a Meta precisa alcancar o AgentQuest por HTTPS publico
para entregar as mensagens. Numa instalacao local isso exige expor a porta
(por exemplo com um tunel). O envio funciona sem nenhuma exposicao.
"""

import httpx

GRAPH_BASE = "https://graph.facebook.com"


def _cfg(settings: dict) -> dict:
    return settings.get("channels", {}).get("whatsapp", {})


def is_configured(settings: dict) -> bool:
    cfg = _cfg(settings)
    return bool(cfg.get("meta_phone_number_id")) and bool(cfg.get("meta_access_token"))


def get_whatsapp_status(settings: dict) -> dict:
    """Valida as credenciais consultando o proprio numero na Graph API."""
    cfg = _cfg(settings)
    phone_id = cfg.get("meta_phone_number_id", "")
    token = cfg.get("meta_access_token", "")
    versao = cfg.get("meta_api_version", "v21.0")

    base = {
        "enabled": cfg.get("enabled", False),
        "provider": "meta_official",
        # Campos mantidos para a UI compartilhada nao quebrar
        "docker_installed": True,
        "docker_running": True,
        "node_installed": True,
        "bridge_running": True,
    }

    if not phone_id or not token:
        return {
            **base,
            "evolution_reachable": False,
            "instance_state": "not_created",
            "last_error": "Informe o Phone Number ID e o Access Token da Meta.",
        }

    try:
        resp = httpx.get(
            f"{GRAPH_BASE}/{versao}/{phone_id}",
            params={"fields": "display_phone_number,verified_name,quality_rating"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            dados = resp.json()
            return {
                **base,
                "evolution_reachable": True,
                "instance_state": "open",
                "connected_number": dados.get("display_phone_number"),
                "verified_name": dados.get("verified_name"),
                "quality_rating": dados.get("quality_rating"),
                "last_error": None,
            }

        detalhe = ""
        try:
            detalhe = resp.json().get("error", {}).get("message", "")
        except Exception:
            detalhe = resp.text[:200]

        return {
            **base,
            "evolution_reachable": False,
            "instance_state": "not_created",
            "last_error": f"A Meta recusou as credenciais ({resp.status_code}): {detalhe}",
        }
    except Exception as e:
        return {
            **base,
            "evolution_reachable": False,
            "instance_state": "not_created",
            "last_error": f"Falha ao falar com a Graph API: {e}",
        }


def send_text(settings: dict, numero: str, texto: str) -> dict:
    """Envia mensagem de texto pela Cloud API oficial."""
    cfg = _cfg(settings)
    phone_id = cfg.get("meta_phone_number_id", "")
    token = cfg.get("meta_access_token", "")
    versao = cfg.get("meta_api_version", "v21.0")

    if not phone_id or not token:
        return {"status": "error", "message": "Credenciais da Meta nao configuradas."}

    try:
        resp = httpx.post(
            f"{GRAPH_BASE}/{versao}/{phone_id}/messages",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero,
                "type": "text",
                "text": {"preview_url": False, "body": texto},
            },
            timeout=20,
        )
        if resp.status_code in (200, 201):
            return {"status": "sent", "method": "WhatsApp Cloud API (Meta)"}

        detalhe = ""
        try:
            erro = resp.json().get("error", {})
            detalhe = erro.get("message", "")
            # Fora da janela de 24h a Meta exige template aprovado — erro comum
            if erro.get("code") == 131047:
                detalhe += (
                    " (fora da janela de 24h: para reabrir a conversa e preciso "
                    "usar um template aprovado)"
                )
        except Exception:
            detalhe = resp.text[:200]

        return {"status": "error", "message": f"Meta retornou {resp.status_code}: {detalhe}"}
    except Exception as e:
        return {"status": "error", "message": f"Falha no envio pela Meta: {e}"}


def parse_incoming(payload: dict) -> list[dict]:
    """Extrai mensagens de texto do formato de webhook da Meta.

    Retorna uma lista de {numero, nome, texto} — o webhook da Meta pode
    entregar varias mensagens numa unica chamada.
    """
    mensagens = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            contatos = {
                c.get("wa_id"): c.get("profile", {}).get("name", "")
                for c in value.get("contacts", [])
            }

            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                numero = msg.get("from", "")
                texto = msg.get("text", {}).get("body", "")
                if not texto.strip():
                    continue
                mensagens.append({
                    "numero": numero,
                    "nome": contatos.get(numero) or numero,
                    "texto": texto,
                })

    return mensagens
