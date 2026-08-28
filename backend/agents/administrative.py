"""
Agente Administrativo - Triagem & Roteamento
Classifica demandas e direciona para o setor correto.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Voce e o Administrativo do sistema AgentQuest HQ.
Sua funcao e analisar a ficha de triagem gerada pelo Atendente e classificar
a demanda para o setor correto da empresa.

SETORES DISPONIVEIS:
- "financeiro": Cobrancas, faturas, pagamentos, notas fiscais, fluxo de caixa
- "comercial": Vendas, propostas, leads, follow-ups, negociacoes
- "juridico": Contratos, clausulas, LGPD, termos, compliance, risco legal
- "planejador": Cronogramas, prazos, reunioes, estrategia, alinhamento de equipe

REGRAS:
- Responda EXCLUSIVAMENTE em formato JSON valido
- Escolha apenas UM setor
- Justifique em 1 frase curta
- Determine o canal de resposta mais adequado: "whatsapp", "telegram", "email" ou "interno"

FORMATO DE RESPOSTA (JSON):
{
  "setor": "financeiro | comercial | juridico | planejador",
  "justificativa": "Frase curta explicando o roteamento",
  "canal_resposta": "whatsapp | telegram | email | interno"
}
"""


class AdministrativeAgent(BaseAgent):
    def __init__(self):
        super().__init__("Administrativo", SYSTEM_PROMPT)

    def classify(self, attendant_analysis):
        """
        Classifica a demanda com base na analise do Atendente.

        Args:
            attendant_analysis: dict com remetente, assunto, intencao, urgencia, resumo

        Returns:
            dict com setor, justificativa, canal_resposta
        """
        import json
        prompt = f"Ficha de triagem do Atendente:\n{json.dumps(attendant_analysis, ensure_ascii=False, indent=2)}"
        result = self.invoke(prompt, expect_json=True)

        # Garantir campos minimos com fallback inteligente
        if isinstance(result, dict) and "setor" not in result:
            # Tentar inferir setor pelo assunto
            assunto = attendant_analysis.get("assunto", "").lower()
            intencao = attendant_analysis.get("intencao", "").lower()

            if any(w in assunto + intencao for w in ["fatura", "pagamento", "cobran", "nota fiscal", "extrato"]):
                setor = "financeiro"
            elif any(w in assunto + intencao for w in ["contrato", "clausula", "lgpd", "juridic", "legal"]):
                setor = "juridico"
            elif any(w in assunto + intencao for w in ["prazo", "reuniao", "cronograma", "agenda"]):
                setor = "planejador"
            else:
                setor = "comercial"

            result = {
                "setor": setor,
                "justificativa": f"Classificado por palavras-chave do assunto: {assunto}",
                "canal_resposta": attendant_analysis.get("source", "whatsapp"),
            }

        return result
