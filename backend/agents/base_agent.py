"""
AgentQuest HQ - Base Agent
Classe base com suporte dinâmico a múltiplos provedores (Gemini, OpenRouter, Local Ollama/LM Studio)
e sistema inteligente de Fallback Automático para IA Local caso a cota do Gemini expire.
"""

import os
import json
from backend.tools.settings_manager import settings_manager

# Tenta importar SDKs
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class BaseAgent:
    """
    Classe base para todos os agentes especialistas do AgentQuest HQ.
    Gerencia chamadas de IA com tolerância a falhas e contingência local automática.
    """

    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt

    def invoke_raw(self, user_message):
        """Chama o provedor ativo e, se ele falhar, cai automaticamente na IA Local.

        Retorna (texto, erro) sem aplicar a resposta heurística — para que quem
        chama decida o que fazer na falha. É esta a função reaproveitada pelos
        módulos que não herdam de BaseAgent (Oráculo, Minerador de Memória,
        Aprendiz de Feedback e Hermes/Nous), garantindo que todos tenham a mesma
        contingência para o Ollama.
        """
        cfg = settings_manager.get_settings().get("ai_providers", {})
        active_provider = cfg.get("active_provider", "gemini")
        auto_fallback_local = cfg.get("auto_fallback_local", True)

        chamadas = {
            "gemini": self._call_gemini,
            "nous_openrouter": self._call_openrouter,
            "openai": self._call_openai,
            "local": self._call_local,
        }

        chamada = chamadas.get(active_provider)
        if not chamada:
            return None, f"Provedor '{active_provider}' não suportado"

        text, err = chamada(user_message, cfg)
        if text and not err:
            return text, None

        if auto_fallback_local and active_provider != "local":
            print(f"[CONTINGÊNCIA ATIVA] Agente {self.name}: Provedor '{active_provider}' falhou ({str(err)[:80]}). Alternando automaticamente para IA Local (Ollama/LM Studio)...")
            local_text, local_err = self._call_local(user_message, cfg)
            if local_text and not local_err:
                print(f"[CONTINGÊNCIA SUCESSO] Agente {self.name} respondido com sucesso pela IA Local!")
                return local_text, None
            return None, f"provedor '{active_provider}': {err} | IA local: {local_err}"

        return None, err

    def invoke(self, user_message, expect_json=False):
        """Executa a chamada à IA com fallback automático para IA Local e, em
        último caso, resposta heurística."""
        text, err = self.invoke_raw(user_message)

        if text and not err:
            if expect_json:
                return self._parse_json(text)
            return text

        print(f"[AVISO] Agente {self.name}: Todos os modelos de IA falharam ({str(err)[:120]}). Acionando resposta heurística de emergência.")
        return self._fallback(user_message, expect_json)

    def _call_gemini(self, user_message, cfg):
        """Chama Google Gemini com os modelos suportados."""
        api_key = cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")
        if not GENAI_AVAILABLE or not api_key:
            return None, "Google GenAI SDK ou API Key indisponível"

        model_name = cfg.get("gemini_model", "gemini-3.6-flash")
        # Alternativas para quando o modelo escolhido responde 503 (alta demanda).
        # Os antigos gemini-2.0-flash e gemini-1.5-flash foram retirados: hoje
        # devolvem 404 e só gastavam tentativas antes de cair na IA Local.
        candidate_models = [
            model_name,
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ]
        models_to_try = list(dict.fromkeys([m for m in candidate_models if m]))

        last_error = ""
        try:
            client = genai.Client(api_key=api_key)
            for model in models_to_try:
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=0.3,
                    )
                    response = client.models.generate_content(
                        model=model,
                        contents=user_message,
                        config=config
                    )
                    if response and response.text:
                        return response.text.strip(), None
                except Exception as e:
                    last_error = str(e)
                    print(f"[ERRO GEMINI] {self.name} com {model}: {last_error[:90]}")
                    if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                        # Cota diária/minuto esgotada, não adianta tentar outros modelos na mesma chave
                        return None, f"429 Quota Exceeded: {last_error}"
                    continue
        except Exception as e:
            last_error = str(e)

        return None, last_error or "Falha geral no Gemini"

    def _call_local(self, user_message, cfg):
        """Chama a IA Local (Ollama, LM Studio ou Hermes Gateway compatível com OpenAI API)."""
        if not OPENAI_AVAILABLE:
            return None, "Biblioteca OpenAI não instalada"

        base_url = cfg.get("local_base_url") or "http://localhost:11434/v1"
        model = cfg.get("local_model") or "qwen2.5:7b"
        api_key = cfg.get("local_api_key") or "ollama"

        try:
            client = OpenAI(base_url=base_url, api_key=api_key, timeout=25)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=800
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip(), None
        except Exception as e:
            return None, f"Falha na IA Local ({base_url} - {model}): {str(e)}"

        return None, "IA Local retornou resposta vazia"

    def _call_openrouter(self, user_message, cfg):
        """Chama OpenRouter / Nous Research."""
        if not OPENAI_AVAILABLE:
            return None, "Biblioteca OpenAI não instalada"

        api_key = cfg.get("nous_api_key") or os.getenv("NOUS_API_KEY", "")
        base_url = cfg.get("nous_base_url") or "https://openrouter.ai/api/v1"
        model = cfg.get("nous_model_name") or "nousresearch/hermes-3-llama-3.1-405b"

        if not api_key:
            return None, "OpenRouter API Key não informada"

        try:
            client = OpenAI(base_url=base_url, api_key=api_key, timeout=20)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip(), None
        except Exception as e:
            return None, f"Falha no OpenRouter: {str(e)}"

        return None, "OpenRouter retornou vazio"

    def _call_openai(self, user_message, cfg):
        """Chama a OpenAI oficial."""
        if not OPENAI_AVAILABLE:
            return None, "Biblioteca OpenAI não instalada"

        api_key = cfg.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        model = cfg.get("openai_model") or "gpt-4o-mini"

        if not api_key:
            return None, "OpenAI API Key não informada"

        try:
            client = OpenAI(api_key=api_key, timeout=20)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip(), None
        except Exception as e:
            return None, f"Falha na OpenAI: {str(e)}"

        return None, "OpenAI retornou vazio"

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
        """Resposta de fallback heurístico caso todas as IAs falhem."""
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

