"""
Agente Atendente - Recepcao & Leitura
Le mensagens brutas e extrai: remetente, assunto, intencao, urgencia e resumo.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Voce e o Atendente do sistema AgentQuest HQ.
Sua funcao e ler mensagens brutas recebidas via WhatsApp, Telegram, E-mail ou documentos
e extrair as informacoes essenciais de forma estruturada.

REGRAS:
- Sempre responda EXCLUSIVAMENTE em formato JSON valido
- Identifique o remetente (nome da pessoa ou empresa)
- Determine o assunto principal em uma frase curta
- Classifique a intencao (pergunta, solicitacao, reclamacao, informacao, proposta, cobranca, etc)
- Determine a urgencia: "alta" (precisa de resposta hoje), "media" (pode esperar 2-3 dias), "baixa"
- Faca um resumo objetivo em no maximo 2 linhas

FORMATO DE RESPOSTA (JSON):
{
  "remetente": "Nome da pessoa ou empresa",
  "assunto": "Assunto principal em frase curta",
  "intencao": "tipo de intencao",
  "urgencia": "alta | media | baixa",
  "resumo": "Resumo em 1-2 linhas do que a pessoa precisa"
}
"""


class AttendantAgent(BaseAgent):
    def __init__(self):
        super().__init__("Atendente", SYSTEM_PROMPT)

    def read_message(self, raw_text, source="whatsapp"):
        """
        Le e analisa uma mensagem bruta.

        Args:
            raw_text: Texto da mensagem
            source: Canal de origem (whatsapp, telegram, email)

        Returns:
            dict com remetente, assunto, intencao, urgencia, resumo
        """
        prompt = f"Canal de origem: {source}\n\nMensagem recebida:\n{raw_text}"
        result = self.invoke(prompt, expect_json=True)

        # Garantir campos minimos
        if isinstance(result, dict) and "remetente" not in result:
            result = {
                "remetente": "Desconhecido",
                "assunto": raw_text[:60],
                "intencao": "solicitacao",
                "urgencia": "media",
                "resumo": raw_text[:120],
            }

        return result
