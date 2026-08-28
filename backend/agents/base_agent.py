"""
AgentQuest HQ - Base Agent
Classe base que encapsula a chamada ao Google Gemini API via novo SDK google.genai.
Todos os 8 agentes especialistas herdam desta classe.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Tenta importar o SDK moderno google.genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if GENAI_AVAILABLE and API_KEY and API_KEY != "sua_chave_aqui":
    client = genai.Client(api_key=API_KEY)
    GEMINI_READY = True
else:
    client = None
    GEMINI_READY = False


class BaseAgent:
    """
    Classe base para todos os agentes do AgentQuest HQ.

    Cada agente recebe:
    - name: Nome do agente (ex: "Atendente")
    - system_prompt: Instruções de comportamento do agente
    """

    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt

    def invoke(self, user_message, expect_json=False):
        """
        Envia uma mensagem ao Gemini e retorna a resposta.

        Args:
            user_message: Texto para o agente processar
            expect_json: Se True, tenta parsear a resposta como JSON

        Returns:
            str ou dict dependendo de expect_json
        """
        if not GEMINI_READY or not client:
            return self._fallback(user_message, expect_json)

        try:
            config = types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.3,
            )
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_message,
                config=config
            )
            text = response.text.strip() if response and response.text else ""

            if expect_json:
                return self._parse_json(text)

            return text

        except Exception as e:
            print(f"[ERRO] Agente {self.name}: {e}")
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
            return {"raw": text}

    def _fallback(self, user_message, expect_json):
        """Resposta de fallback caso a API falhe ou não esteja pronta."""
        if expect_json:
            return {
                "remetente": "Remetente Externo",
                "assunto": user_message[:60],
                "intencao": "solicitacao",
                "urgencia": "media",
                "resumo": user_message[:120],
                "setor": "financeiro" if any(w in user_message.lower() for w in ["fatura", "boleto", "pix", "pagamento"]) else "comercial"
            }
        return (
            f"Olá! Confirmamos o recebimento de sua solicitação referente a: {user_message[:100]}...\n\n"
            f"Nossa equipe já está providenciando o atendimento. Qualquer dúvida, estamos à disposição!"
        )
