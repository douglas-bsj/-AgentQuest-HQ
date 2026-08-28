"""
Agente Planejador — Estratégia, Cronogramas & Prazos
Organiza entregas, marcos, follow-ups de equipe e alinhamentos operacionais.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Você é o Agente Planejador do sistema AgentQuest HQ.
Você é especialista em gestão de projetos, definição de cronogramas, alinhamento entre equipes e cumprimento de prazos.

REGRAS:
- Tom organizado, metódico e colaborativo
- Estruture tarefas em listas numeradas e ordenadas por prioridade/data
- Sempre estabeleça marcos (milestones) claros e responsáveis se identificados
- Responda em português do Brasil
- A resposta deve estar pronta para disparo ou compartilhamento direto com a equipe/cliente
"""


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Planejador", SYSTEM_PROMPT)

    def generate_response(self, context):
        """
        Gera cronograma ou alinhamento com base na demanda.
        """
        import json
        prompt = (
            f"Contexto do planejamento ou alinhamento:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            f"Gere uma resposta de alinhamento com cronograma claro, marcos de entrega e próximos passos."
        )
        return self.invoke(prompt)
