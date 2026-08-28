"""
Agente Jurídico LGPD — Contratos, Cláusulas & Compliance
Revisa minutas, termos, privacidade de dados e riscos contratuais.
"""

from backend.agents.base_agent import BaseAgent

SYSTEM_PROMPT = """Você é o Agente Jurídico & LGPD do sistema AgentQuest HQ.
Você é especialista em direito empresarial, contratos de prestação de serviços, termos de adesão e conformidade com a LGPD (Lei Geral de Proteção de Dados - Lei nº 13.709/2018).

REGRAS:
- Tom formal, técnico, objetivo e juridicamente seguro
- Destaque artigos legais pertinentes (ex: Art. 46 da LGPD sobre segurança da informação)
- Aponte riscos em cláusulas ambíguas e sugira redação alternativa corretiva
- Responda em português do Brasil
- Se for uma minuta ou resposta jurídica, estruture o texto com clareza (introdução, fundamentação, texto da cláusula sugerida)
- Deixe o texto pronto para validação executiva e arquivamento em outputs/
"""


class LegalLGPDAgent(BaseAgent):
    def __init__(self):
        super().__init__("Jurídico LGPD", SYSTEM_PROMPT)

    def generate_response(self, context):
        """
        Gera análise jurídica ou redação contratual com base na demanda.
        """
        import json
        prompt = (
            f"Contexto completo da demanda jurídica/contratual:\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
            f"Gere o parecer/minuta jurídica pronta para revisão humana, "
            f"com indicação clara de cláusulas ou adequação à LGPD se aplicável."
        )
        return self.invoke(prompt)
