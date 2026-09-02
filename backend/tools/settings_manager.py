"""
Settings Manager — AgentQuest HQ
Gerenciador central de configurações do sistema:
- Provedores de IA & Chaves de API
- Status & Autonomia dos Agentes
- Integrações de Canais (WhatsApp, Telegram, E-mail)
- Diretórios e Obsidian
"""

import os
import json
from pathlib import Path

from backend.utils.paths import base_path

SETTINGS_FILE = base_path("settings.json")


DEFAULT_SETTINGS = {
    "ai_providers": {
        "active_provider": "gemini",
        "nous_api_key": os.getenv("NOUS_API_KEY", ""),
        "nous_base_url": os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1"),
        "nous_model_name": os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": "gpt-4o-mini",
        "local_base_url": "http://localhost:11434/v1",
        "local_model": "qwen2.5:7b",
        "local_api_key": "ollama",
        "auto_fallback_local": True
    },
    "agents": [
        {"id": "hermes", "name": "Hermes", "role": "Orquestrador Geral", "status": "ativo", "autonomy": "manual", "tone": "Estratégico & Executivo", "prompt": "Você é o Orquestrador Geral de IA."},
        {"id": "atendente", "name": "Atendente", "role": "Recepção & Leitura", "status": "ativo", "autonomy": "manual", "tone": "Cordial & Ágil", "prompt": "Você faz a recepção e acolhimento dos contatos."},
        {"id": "admin", "name": "Administrativo", "role": "Triagem & Roteamento", "status": "ativo", "autonomy": "manual", "tone": "Pragmático & Organizado", "prompt": "Você organiza demandas e direciona para o setor correto."},
        {"id": "financeiro", "name": "Financeiro", "role": "Cobranças & Notas", "status": "ativo", "autonomy": "manual", "tone": "Formal & Preciso", "prompt": "Você cuida de cobranças, faturas e fluxo de caixa."},
        {"id": "comercial", "name": "Comercial", "role": "Leads & Follow-ups", "status": "ativo", "autonomy": "manual", "tone": "Persuasivo & Comercial", "prompt": "Você conduz negociações, vendas e follow-ups."},
        {"id": "juridico", "name": "Jurídico LGPD", "role": "Contratos & LGPD", "status": "ativo", "autonomy": "manual", "tone": "Técnico & Cauteloso", "prompt": "Você analisa cláusulas, contratos e conformidade LGPD."},
        {"id": "planejador", "name": "Planejador", "role": "Estratégia & Prazos", "status": "ativo", "autonomy": "manual", "tone": "Metódico & Cronológico", "prompt": "Você estima prazos e define etapas de entrega."},
        {"id": "revisor", "name": "Revisor", "role": "Controle de Qualidade", "status": "ativo", "autonomy": "manual", "tone": "Refinado & Exigente", "prompt": "Você revisa ortografia, clareza e adequação antes do envio."}
    ],
    "channels": {
        "whatsapp": {
            "enabled": True,
            # baileys: ponte local Node (sem Docker) — recomendado para testes
            # meta_official: WhatsApp Cloud API oficial da Meta — producao
            # evolution: Evolution API via Docker
            # mock: apenas gera link wa.me para envio manual
            "provider": "baileys",
            "ignore_groups": True,

            # Evolution API (Docker)
            "api_url": "http://localhost:8080",
            "instance_name": "agentquest",
            "api_token": "agentquest-secreto-123",
            "webhook_url": "http://host.docker.internal:8000/api/webhook/whatsapp",

            # WhatsApp Cloud API oficial da Meta
            "meta_phone_number_id": "",
            "meta_access_token": "",
            "meta_verify_token": "agentquest-webhook",
            "meta_api_version": "v21.0",
        },
        "telegram": {
            "enabled": True,
            "bot_token": "",
            "default_chat_id": ""
        },
        "email": {
            "enabled": True,
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "",
            "email_password": "",
            "use_ssl": True
        }
    },
    "storage": {
        "inbox_folder": os.getenv("INBOX_FOLDER", "inbox"),
        "processed_folder": os.getenv("PROCESSED_FOLDER", "processed"),
        "outputs_folder": os.getenv("OUTPUTS_FOLDER", "outputs"),
        "vault_folder": "vault"
    }
}


class SettingsManager:
    def __init__(self):
        self._settings = self._load()
        self.hydrate_environment()

    def _load(self) -> dict:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # Merge with default structure to prevent missing keys
                    merged = DEFAULT_SETTINGS.copy()
                    for k, v in saved.items():
                        if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                            merged[k].update(v)
                        else:
                            merged[k] = v
                    return merged
            except Exception as e:
                print(f"[SETTINGS] Erro ao ler settings.json: {e}")
        return DEFAULT_SETTINGS.copy()

    def get_all(self) -> dict:
        return self._settings

    def get_settings(self) -> dict:
        return self._settings

    def hydrate_environment(self):
        """Sincroniza as chaves de ai_providers de settings.json para os.environ.

        Necessário porque alguns módulos (oracle_agent, memory_miner,
        feedback_learner, nous_hermes_agent) leem a chave via os.getenv
        diretamente em vez de consultar o settings_manager. Chamado no
        __init__ (cobre o boot do processo, quando settings.json já existe
        em disco de uma execução anterior) e no save() (cobre a gravação
        feita pela UI na sessão atual).
        """
        ai = self._settings.get("ai_providers", {})
        if ai.get("nous_api_key"):
            os.environ["NOUS_API_KEY"] = ai["nous_api_key"]
        if ai.get("nous_base_url"):
            os.environ["NOUS_BASE_URL"] = ai["nous_base_url"]
        if ai.get("nous_model_name"):
            os.environ["NOUS_MODEL_NAME"] = ai["nous_model_name"]
        if ai.get("gemini_api_key"):
            os.environ["GEMINI_API_KEY"] = ai["gemini_api_key"]
        if ai.get("gemini_model"):
            os.environ["GEMINI_MODEL"] = ai["gemini_model"]
        if ai.get("openai_api_key"):
            os.environ["OPENAI_API_KEY"] = ai["openai_api_key"]

    def update_partial(self, patch: dict) -> dict:
        """Merge raso de `patch` sobre as configurações atuais (nível 1 e 2),
        sem substituir o objeto inteiro como o save() faz. Usado pelo
        onboarding, que só conhece a chave Gemini e não deve apagar o
        resto das configurações já salvas."""
        merged = self._settings.copy()
        for k, v in patch.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return self.save(merged)

    def save(self, new_settings: dict) -> dict:
        self._settings = new_settings
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)

            self.hydrate_environment()

            print("[SETTINGS] Configurações salvas e sincronizadas com sucesso.")
            return self._settings
        except Exception as e:
            print(f"[SETTINGS] Erro ao salvar settings.json: {e}")
            raise e


settings_manager = SettingsManager()
