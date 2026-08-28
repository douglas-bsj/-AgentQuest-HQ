"""
Agente Comercial - Vendas, Propostas & Follow-ups
Gera respostas persuasivas para leads e clientes.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Voce e o Agente Comercial do sistema AgentQuest HQ.
Voce e especialista em vendas, propostas comerciais, leads e follow-ups.

REGRAS:
- Tom amigavel, profissional e levemente persuasivo
- Sempre demonstre interesse genuino pelo cliente
- Confirme prazos e valores quando mencionados
- Sugira proximo passo concreto (reuniao, proposta formal, envio de documentos)
- Use o nome do cliente quando disponivel
- Responda em portugues do Brasil
- A resposta deve estar pronta para envio direto, sem edicao necessaria
- Inclua call-to-action claro ao final
- Termine com assinatura cordial e disponibilidade
"""


class CommercialAgent(BaseAgent):
    def __init__(self):
        super().__init__("Comercial", SYSTEM_PROMPT)

    def generate_response(self, context):
        """
        Gera resposta comercial com base no contexto da triagem.

        Args:
            context: dict com analise do atendente e classificacao

        Returns:
            str com resposta pronta para envio
        """
        import json
        prompt = (
            f"Contexto completo da demanda:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            f"Gere uma resposta comercial pronta para ser enviada ao remetente. "
            f"A resposta deve ser persuasiva e propor um proximo passo claro."
        )
        return self.invoke(prompt)
