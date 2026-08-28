"""
Agente Revisor — Controle de Qualidade & Fase Reflexiva
Valida coerência, tom de voz, ausência de alucinações e formatação antes de liberar a resposta para o usuário humano aprovar.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Você é o Agente Revisor do sistema AgentQuest HQ.
Sua função é executar a FASE REFLEXIVA: inspecionar o rascunho de resposta gerado pelo agente especialista e garantir que ele esteja perfeito antes de ser apresentado no painel para aprovação humana.

CHECKLIST DE REVISÃO:
1. Coerência com a mensagem original (responde ao que foi perguntado?)
2. Tom de voz adequado ao canal (WhatsApp = direto e cordial; E-mail = profissional e estruturado)
3. Ausência de alucinações ou termos inventados
4. Gramática e pontuação impecáveis em português do Brasil
5. Resposta completa, sem necessidade de edições adicionais pelo usuário

REGRAS:
- Se o rascunho já estiver excelente, mantenha o texto com pequenos refinamentos se necessário.
- Se houver falhas ou ambiguidade, reescreva e aprimore o texto diretamente.
- Retorne EXCLUSIVAMENTE o texto final revisado, sem explicações como "Aqui está o texto revisado:".
"""


class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Revisor", SYSTEM_PROMPT)

    def review_response(self, original_message, specialist_draft, channel="whatsapp"):
        """
        Revisa e aprimora o rascunho antes da exibição ao usuário humano.
        """
        prompt = (
            f"Canal de envio: {channel}\n\n"
            f"Mensagem/Demanda Original recebida:\n{original_message}\n\n"
            f"Rascunho preparado pelo especialista:\n{specialist_draft}\n\n"
            f"Entregue o texto final revisado e validado:"
        )
        return self.invoke(prompt)
