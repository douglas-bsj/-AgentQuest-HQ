"""
AgentQuest HQ - Nous Hermes Agent
Conecta-se à API compatível com OpenAI (como OpenRouter) para rodar os modelos da Nous Research.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

NOUS_API_KEY = os.getenv("NOUS_API_KEY", "")
NOUS_BASE_URL = os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1")
NOUS_MODEL_NAME = os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b")

if OPENAI_AVAILABLE and NOUS_API_KEY and NOUS_API_KEY != "sua_chave_openrouter_aqui":
    client = OpenAI(
        base_url=NOUS_BASE_URL,
        api_key=NOUS_API_KEY,
    )
    NOUS_READY = True
else:
    client = None
    NOUS_READY = False


class NousHermesAgent:
    """
    Agente que utiliza os modelos da família Hermes da Nous Research.
    """
    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt

    def invoke(self, user_message, expect_json=False):
        """
        Envia uma mensagem ao Nous Hermes via OpenRouter / OpenAI API compatível.
        """
        if not NOUS_READY or not client:
            return self._fallback(user_message, expect_json)

        try:
            # Alguns provedores não suportam response_format="json_object" para todos os modelos,
            # então adicionamos uma instrução extra no prompt se precisarmos de JSON.
            sys_msg = self.system_prompt
            if expect_json and "json" not in sys_msg.lower():
                sys_msg += "\n\nCRITICAL: Return ONLY valid JSON."

            response = client.chat.completions.create(
                model=NOUS_MODEL_NAME,
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
