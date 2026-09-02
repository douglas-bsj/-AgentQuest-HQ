"""
AgentQuest HQ - Nous Hermes Agent
Conecta-se à API compatível com OpenAI (como OpenRouter) para rodar os modelos da Nous Research.
"""

import os
import json

from backend.tools.settings_manager import settings_manager

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class NousHermesAgent:
    """
    Agente que utiliza os modelos da família Hermes da Nous Research.
    """
    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt

    def _get_client(self):
        """Monta o cliente a cada chamada, lendo settings.json primeiro (com fallback
        para variáveis de ambiente) — evita ficar preso a uma chave vazia lida uma
        única vez na importação do módulo (que pode acontecer antes do settings.json
        ser carregado, ou antes do usuário configurar a chave pela UI)."""
        cfg = settings_manager.get_settings().get("ai_providers", {})
        api_key = cfg.get("nous_api_key") or os.getenv("NOUS_API_KEY", "")
        base_url = cfg.get("nous_base_url") or os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1")
        model_name = cfg.get("nous_model_name") or os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b")

        if not OPENAI_AVAILABLE or not api_key or api_key == "sua_chave_openrouter_aqui":
            return None, None

        return OpenAI(base_url=base_url, api_key=api_key), model_name

    def invoke(self, user_message, expect_json=False):
        """
        Envia uma mensagem ao Nous Hermes via OpenRouter / OpenAI API compatível.
        """
        client, model_name = self._get_client()
        if not client:
            return self._fallback(user_message, expect_json)

        try:
            # Alguns provedores não suportam response_format="json_object" para todos os modelos,
            # então adicionamos uma instrução extra no prompt se precisarmos de JSON.
            sys_msg = self.system_prompt
            if expect_json and "json" not in sys_msg.lower():
                sys_msg += "\n\nCRITICAL: Return ONLY valid JSON."

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
            )
            
            text = response.choices[0].message.content.strip() if response.choices else ""

            if expect_json:
                return self._parse_json(text)

            return text

        except Exception as e:
            print(f"[ERRO] Agente Nous Hermes {self.name}: {e}")
            return self._fallback(user_message, expect_json)

    def _parse_json(self, text):
        """Tenta extrair JSON de uma resposta que pode conter markdown."""
        clean = text
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]

        try:
            return json.loads(clean.strip())
        except json.JSONDecodeError:
            print(f"[AVISO] Falha ao parsear JSON no Hermes Agent. Raw: {text[:100]}...")
            return {"raw": text}

    def _fallback(self, user_message, expect_json):
        """Fallback caso a API não esteja configurada ou falhe."""
        if expect_json:
            return {
                "error": "true",
                "message": "A API do Nous Hermes não pôde ser conectada."
            }
        return "Desculpe, o orquestrador Hermes está indisponível no momento devido a falha de conexão com a API."
