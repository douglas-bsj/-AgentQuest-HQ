from backend.tools.obsidian_bridge import obsidian_bridge
from backend.agents.ai_client import chat_json


def process_feedback_rule(mission_title: str, mission_response: str, feedback: str):
    """
    Extrai uma regra geral a partir do feedback de rejeição.

    Usa o cliente de IA compartilhado: respeita o provedor configurado e, se ele
    estiver fora do ar ou sem cota, a IA Local (Ollama) assume automaticamente.
    Antes este módulo exigia NOUS_API_KEY e nem tentava outro provedor, então a
    função ficava morta em instalações que só configuram a chave Gemini.
    """
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

    dados, erro = chat_json(
        "Você extrai regras de negócio a partir de feedback. Responda apenas JSON válido.",
        prompt,
    )

    if not dados or erro:
        print(f"[FEEDBACK] Não foi possível extrair a regra: {str(erro)[:150]}")
        return

    try:
        title = dados.get("rule_title", "Regra de Feedback")
        content = dados.get("rule_content", "Conteúdo extraído.")
        obsidian_bridge.save_feedback_rule(title, content)
        print(f"[FEEDBACK] Regra extraída e salva com sucesso: {title}")
    except Exception as e:
        print(f"[FEEDBACK] Erro ao salvar a regra no cofre: {e}")
