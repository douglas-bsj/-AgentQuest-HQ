import os
import json
from openai import OpenAI
from backend.tools.obsidian_bridge import obsidian_bridge
from backend.tools.settings_manager import settings_manager

def process_feedback_rule(mission_title: str, mission_response: str, feedback: str):
    """
    Extrai uma regra geral a partir do feedback de rejeição, usando o provedor de IA
    configurado (OpenRouter/Nous se disponível, senão Gemini) — a mesma cadeia de
    fallback usada pelo Oráculo, para não depender só de NOUS_API_KEY quando a
    maioria das instalações só configura a chave Gemini no onboarding.
    """
    cfg = settings_manager.get_settings().get("ai_providers", {})

    api_key = cfg.get("nous_api_key") or os.getenv("NOUS_API_KEY")
    base_url = cfg.get("nous_base_url") or os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = cfg.get("nous_model_name") or os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b")

    if not api_key:
        api_key = cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        model_name = cfg.get("gemini_model") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        print("[FEEDBACK] Erro: nenhuma chave de IA configurada (Nous/OpenRouter ou Gemini).")
        return

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    prompt = f"""
Você é o Orquestrador de Inteligência (Hermes) de um Time de Agentes.
Um usuário humano rejeitou uma resposta elaborada pelo time.

Missão Original: {mission_title}
Resposta Gerada Anteriormente: {mission_response}
Motivo da Rejeição (Feedback do Humano): {feedback}

Sua tarefa: Converta esse feedback em uma regra estrita de negócio, clara e atemporal, para ser adicionada à nossa Base de Conhecimento, garantindo que nenhum agente cometa o mesmo erro no futuro.

Responda APENAS com um objeto JSON no formato:
{{
    "rule_title": "Um titulo curto para a regra",
    "rule_content": "O texto detalhado da regra."
}}
"""

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        result_text = completion.choices[0].message.content.strip()
        
        # Limpar markdown ```json ... ``` se houver
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        data = json.loads(result_text.strip())
        
        title = data.get("rule_title", "Regra de Feedback")
        content = data.get("rule_content", "Conteúdo extraído.")
        
        # Salva a regra no Obsidian
        obsidian_bridge.save_feedback_rule(title, content)
        print(f"[FEEDBACK] Regra extraída e salva com sucesso: {title}")
        
    except Exception as e:
        print(f"[FEEDBACK] Erro ao processar extração de regra: {e}")
