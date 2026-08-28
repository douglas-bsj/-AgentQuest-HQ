"""
AgentQuest HQ - Base Agent
Classe base que encapsula a chamada ao Google Gemini API.
Todos os 8 agentes especialistas herdam desta classe.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Tenta importar a SDK do Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configurar a API Key
API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if GEMINI_AVAILABLE and API_KEY and API_KEY != "sua_chave_aqui":
    genai.configure(api_key=API_KEY)
    GEMINI_READY = True
else:
    GEMINI_READY = False


class BaseAgent:
    """
    Classe base para todos os agentes do AgentQuest HQ.

    Cada agente recebe:
    - name: Nome do agente (ex: "Atendente")
    - system_prompt: Instrucoes de comportamento do agente
    """

    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt
        self._model = None

        if GEMINI_READY:
            self._model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                system_instruction=self.system_prompt,
            )

    def invoke(self, user_message, expect_json=False):
        """
        Envia uma mensagem ao Gemini e retorna a resposta.

        Args:
            user_message: Texto para o agente processar
            expect_json: Se True, tenta parsear a resposta como JSON

        Returns:
            str ou dict dependendo de expect_json
        """
        if not GEMINI_READY or not self._model:
            return self._fallback(user_message, expect_json)

        try:
            response = self._model.generate_content(user_message)
            text = response.text.strip()

            if expect_json:
                return self._parse_json(text)

            return text

        except Exception as e:
            print(f"[ERRO] Agente {self.name}: {e}")
            return self._fallback(user_message, expect_json)

    def _parse_json(self, text):
        """Tenta extrair JSON de uma resposta que pode conter markdown."""
        # Remove blocos de codigo markdown se presentes
        clean = text
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]

        try:
            return json.loads(clean.strip())
        except json.JSONDecodeError:
            # Se nao conseguir parsear, retorna como dict simples
            return {"raw": text}

    def _fallback(self, user_message, expect_json):
        """
        Resposta de fallback quando a API nao esta disponivel.
        Gera uma resposta simulada para que o sistema continue funcionando.
        """
        if expect_json:
            return {
                "info": f"[DEMO] Agente {self.name} processou a mensagem (API Gemini nao configurada)",
                "input_preview": user_message[:100]
            }
        return (
            f"[DEMO - {self.name}] Resposta simulada. "
            f"Configure GEMINI_API_KEY no .env para respostas reais.\n\n"
            f"Entrada recebida: {user_message[:200]}..."
        )
