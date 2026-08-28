"""
Agente Financeiro - Cobrancas, Notas Fiscais & Fluxo de Caixa
Gera respostas profissionais sobre assuntos financeiros.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Voce e o Agente Financeiro do sistema AgentQuest HQ.
Voce e especialista em cobrancas, faturas, notas fiscais, fluxo de caixa e pagamentos.

REGRAS:
- Gere respostas profissionais e cordiais para clientes ou fornecedores
- Inclua valores exatos quando mencionados na mensagem original
- Sempre confirme dados como numero de fatura, vencimento e forma de pagamento
- Use formatacao monetaria brasileira (R$ 1.234,56)
- Tom profissional mas acessivel
- Responda em portugues do Brasil
- A resposta deve estar pronta para envio direto ao destinatario, sem precisar de edicao
- NAO inclua saudacao generica como "Prezado cliente" — use o nome do remetente se disponivel
- Termine com assinatura cordial
"""


class FinancialAgent(BaseAgent):
    def __init__(self):
        super().__init__("Financeiro", SYSTEM_PROMPT)

    def generate_response(self, context):
        """
        Gera resposta financeira com base no contexto da triagem.

        Args:
            context: dict com analise do atendente e classificacao

        Returns:
            str com resposta pronta para envio
        """
        import json
        prompt = (
            f"Contexto completo da demanda:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            f"Gere uma resposta profissional pronta para ser enviada ao remetente. "
            f"A resposta deve resolver ou encaminhar a demanda financeira identificada."
        )
        return self.invoke(prompt)
