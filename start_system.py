"""
AgentQuest HQ - Inicializador Unificado

Ponto de entrada unico do sistema: sobe a infraestrutura do WhatsApp
(Evolution API via Docker, se habilitada nas configuracoes), a IA local
de fallback (Ollama, se configurada) e o backend FastAPI, nessa ordem,
e por fim abre o painel no navegador.

Uso:
    python start_system.py
"""

import json
import os
import shutil
import subprocess

from backend.utils.paths import base_path
from backend.tools.evolution_manager import (
    start_evolution_stack,
    wait_for_evolution_api,
)

SETTINGS_PATH = base_path("settings.json")


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        print("[Config] settings.json nao encontrado - usando padroes (WhatsApp/IA local desabilitados).")
        return {}
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def start_evolution_api(settings):
    """Sobe a Evolution API (WhatsApp) via Docker Compose, se habilitada, e aguarda ficar online."""
    result = start_evolution_stack(settings)
    status = result["status"]

    if status == "disabled":
        print(f"[WhatsApp] {result['message']}")
        return
    if status in ("docker_missing", "docker_not_running"):
        print(f"[WhatsApp] AVISO: {result['message']}")
        print("           Instale/abra o Docker Desktop para habilitar o envio automatico de WhatsApp.")
        return
    if status == "compose_failed":
        print(f"[WhatsApp] AVISO: falha ao subir os containers Docker:\n{result['message']}")
        return

    print("[WhatsApp] Subindo Evolution API (PostgreSQL + Redis + API)...")

    api_url = settings.get("channels", {}).get("whatsapp", {}).get("api_url", "http://localhost:8080")
    print(f"[WhatsApp] Aguardando Evolution API responder em {api_url} ...")
    if wait_for_evolution_api(api_url):
        print("[WhatsApp] Evolution API online!")
        print(f"[WhatsApp] Configure e pareie o WhatsApp pela aba Canais do painel, ou acesse {api_url.rstrip('/')}/manager.")
    else:
        print("[WhatsApp] AVISO: Evolution API nao respondeu a tempo (containers foram iniciados mesmo assim).")


def start_ollama_if_configured(settings):
    """Sobe o Ollama local em segundo plano, se o fallback local estiver ativo."""
    provider_cfg = settings.get("ai_providers", {})
    if not provider_cfg.get("auto_fallback_local"):
        return

    if shutil.which("ollama") is None:
        print("[IA Local] Ollama nao encontrado no PATH - fallback local indisponivel.")
        return

    print("[IA Local] Iniciando Ollama serve em segundo plano...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[IA Local] AVISO: nao foi possivel iniciar o Ollama: {e}")


def main():
    print("=" * 60)
    print("  AGENTQUEST HQ - INICIALIZACAO UNIFICADA")
    print("=" * 60)
    print()

    settings = load_settings()
    start_evolution_api(settings)
    start_ollama_if_configured(settings)

    print()
    print("[Backend] Iniciando servidor FastAPI e abrindo o painel...")
    print()

    import run
    run.start_backend()


if __name__ == "__main__":
    main()
