"""
Cliente de IA compartilhado — AgentQuest HQ

Ponto único de chamada à IA para os módulos que não herdam de BaseAgent
(Oráculo, Minerador de Memória, Aprendiz de Feedback e Hermes/Nous).

Antes, cada um desses módulos montava seu próprio cliente e falhava direto
quando o provedor de nuvem estava fora do ar ou sem cota — sem tentar a IA
Local, mesmo com o fallback ligado nas configurações. Agora todos passam pela
mesma contingência usada pelos 8 agentes do pipeline.
"""

import json


def chat(system_prompt: str, user_message: str) -> tuple[str | None, str | None]:
    """Chama o provedor ativo com contingência para a IA Local.

    Retorna (texto, erro): em caso de falha total, texto vem None e erro traz
    o motivo, para o chamador decidir o que exibir.
    """
    from backend.agents.base_agent import BaseAgent

    agente = BaseAgent("IA", system_prompt)
    return agente.invoke_raw(user_message)


def chat_json(system_prompt: str, user_message: str) -> tuple[dict | list | None, str | None]:
    """Igual a chat(), mas já converte a resposta em JSON.

    Modelos costumam devolver JSON embrulhado em bloco markdown, então a cerca
    de código é removida antes do parse.
    """
    texto, erro = chat(system_prompt, user_message)
    if erro or not texto:
        return None, erro or "resposta vazia"

    limpo = texto.strip()
    if "```json" in limpo:
        limpo = limpo.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in limpo:
        partes = limpo.split("```")
        if len(partes) >= 2:
            limpo = partes[1]

    try:
        return json.loads(limpo.strip()), None
    except json.JSONDecodeError as e:
        return None, f"resposta não era JSON válido ({e}): {texto[:120]}"
