"""
Memory Miner Agent — AgentQuest HQ
Lê conversas brutas (WhatsApp, Telegram, E-mail, Documentos) e:
1. Extrai fatos estruturados (quem disse o quê, onde estão objetos, decisões tomadas).
2. Categoriza os assuntos (Futebol, Pessoal, Comercial, Financeiro, etc.).
3. Identifica termos desconhecidos ou lacunas de conhecimento (Active Learning).
4. Persiste fatos no SQLite e nas notas do Obsidian.
"""

import os
import json
import re
from openai import OpenAI
from backend.database import SessionLocal, MemoryFact, KnowledgeGap
from backend.tools.obsidian_bridge import obsidian_bridge
from backend.tools.settings_manager import settings_manager
from backend.utils.paths import base_path

class MemoryMinerAgent:
    def __init__(self):
        self.client = None
        self.model = "gemini-3.6-flash"
        self._init_client()

    def _init_client(self):
        cfg = settings_manager.get_settings().get("ai_providers", {})

        # 1. Tenta OpenRouter
        api_key = cfg.get("nous_api_key") or os.getenv("NOUS_API_KEY")
        base_url = cfg.get("nous_base_url") or os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1")
        model = cfg.get("nous_model_name") or os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b")

        if not api_key:
            # 2. Tenta Gemini
            api_key = cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model = cfg.get("gemini_model") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        if api_key:
            try:
                self.client = OpenAI(base_url=base_url, api_key=api_key)
                self.model = model
            except Exception as e:
                print(f"[MEMORY MINER] Erro ao inicializar cliente IA: {e}")

    def mine_conversation(self, raw_text: str, source_person: str = "Desconhecido", source_channel: str = "whatsapp") -> dict:
        """
        Analisa uma conversa e extrai fatos e termos desconhecidos.
        """
        self._init_client()
        
        prompt = f"""Você é o Especialista em Mineração de Memória e Base de Conhecimento do AgentQuest.
Sua missão é ler o texto/conversa abaixo e extrair:
1. **FATOS e ACONTECIMENTOS:** Quem falou o que, posse de objetos, locais, decisões, pendências, acordos ou informações importantes.
2. **CATEGORIA DO ASSUNTO:** Ex: Futebol, Pessoal, Negócios, Financeiro, Tarefas, Contratos, etc.
3. **TERMOS DESCONHECIDOS / LACUNAS:** Se houver gírias locais, siglas não explicadas, jargões específicos do negócio ou nomes de projetos obscuros que uma IA deveria perguntar ao humano para entender melhor.

TEXTO DA CONVERSA:
---
{raw_text}
---

Responda ESTRITAMENTE em formato JSON com esta estrutura:
{{
  "facts": [
    {{
      "subject": "Entidade ou pessoa ou objeto principal (ex: Cartões de Futebol, João, Proposta #452)",
      "relation": "Relação ou verbo (ex: está_com, deixou_em, reclamou_de, prometeu_para)",
      "object_value": "Valor ou complemento (ex: casa do Carlos, 15 dias úteis)",
      "category": "Categoria (ex: Futebol, Comercial, Financeiro, Pessoal)",
      "context_summary": "Resumo fiel do fato dito nesta conversa"
    }}
  ],
  "unknown_terms": [
    {{
      "term": "Termo ou gíria ou sigla desconhecida",
      "question": "Pergunta amigável e direta para fazer ao humano para esclarecer o significado"
    }}
  ]
}}
"""

        result_data = {"facts": [], "unknown_terms": []}

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um extrator de fatos e entidades analítico e preciso. Responda apenas JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500
                )
                raw_response = response.choices[0].message.content
                # Limpa blocos de código markdown se houver
                clean_json = re.sub(r"^```json\s*", "", raw_response.strip())
                clean_json = re.sub(r"```$", "", clean_json.strip())
                result_data = json.loads(clean_json)
            except Exception as e:
                print(f"[MEMORY MINER ERROR] {e}. Usando extração local de fallback.")
                result_data = self._fallback_extraction(raw_text, source_person)
        else:
            result_data = self._fallback_extraction(raw_text, source_person)

        # Salva os fatos no banco e no Obsidian
        saved_facts = self._save_mined_data(result_data, source_person, source_channel, raw_text)
        return saved_facts

    def _fallback_extraction(self, raw_text: str, source_person: str) -> dict:
        """Extração heurística caso a IA esteja offline."""
        facts = []
        unknown_terms = []
        
        # Categorização simples por palavra-chave
        category = "Geral"
        lower = raw_text.lower()
        if any(w in lower for w in ["futebol", "jogo", "cartão", "time", "campo", "gol"]):
            category = "Futebol / Esportes"
        elif any(w in lower for w in ["pagamento", "fatura", "nota", "valor", "r$", "dinheiro", "pix"]):
            category = "Financeiro"
        elif any(w in lower for w in ["proposta", "contrato", "cliente", "venda", "orçamento"]):
            category = "Comercial"

        facts.append({
            "subject": source_person,
            "relation": "mencionou_informação",
            "object_value": raw_text[:80] + "...",
            "category": category,
            "context_summary": raw_text[:200]
        })

        return {"facts": facts, "unknown_terms": unknown_terms}

    def _save_mined_data(self, data: dict, source_person: str, source_channel: str, raw_text: str) -> dict:
        """Grava fatos e dúvidas no banco SQLite e no Obsidian."""
        db = SessionLocal()
        saved_facts_count = 0
        saved_gaps_count = 0

        try:
            # 1. Salva Fatos
            for f in data.get("facts", []):
                fact = MemoryFact(
                    subject=f.get("subject", source_person),
                    relation=f.get("relation", "relacionado_a"),
                    object_value=f.get("object_value", "não informado"),
                    category=f.get("category", "Geral"),
                    context_summary=f.get("context_summary", raw_text[:200]),
                    source_person=source_person,
                    source_channel=source_channel
                )
                db.add(fact)
                saved_facts_count += 1

            # 2. Salva Dúvidas / Termos Desconhecidos
            for ut in data.get("unknown_terms", []):
                term = ut.get("term", "").strip()
                if term:
                    # Verifica se já existe essa dúvida pendente
                    existing = db.query(KnowledgeGap).filter(KnowledgeGap.term_or_topic == term).first()
                    if not existing:
                        gap = KnowledgeGap(
                            term_or_topic=term,
                            category="Vocabulário / Jargão",
                            detected_in_sources=f"Conversa com {source_person} ({source_channel})",
                            question_to_human=ut.get("question", f"O que significa exatamente o termo '{term}'?"),
                            status="pending"
                        )
                        db.add(gap)
                        saved_gaps_count += 1

            db.commit()

            # 3. Salva no Obsidian / Base de Conhecimento
            self._sync_obsidian_facts(data.get("facts", []), source_person)

        except Exception as e:
            db.rollback()
            print(f"[MEMORY MINER] Erro ao salvar dados no banco: {e}")
        finally:
            db.close()

        return {
            "status": "success",
            "facts_extracted": saved_facts_count,
            "gaps_found": saved_gaps_count
        }

    def _sync_obsidian_facts(self, facts: list, source_person: str):
        """Registra os fatos minerados na base de conhecimento do Obsidian."""
        try:
            vault_dir = base_path("vault", "01_Base_Conhecimento")
            os.makedirs(vault_dir, exist_ok=True)
            fact_file = os.path.join(vault_dir, "Memoria_Fatos_Conversas.md")

            lines = []
            if not os.path.exists(fact_file):
                lines.append("# 🧠 Memória Viva — Fatos & Associações das Conversas\n\n")

            for f in facts:
                lines.append(f"- **[{f.get('category', 'Geral')}]** `{f.get('subject')}` — {f.get('relation')} — `{f.get('object_value')}` (Fonte: *{source_person}*)\n  > Resumo: {f.get('context_summary')}\n")

            with open(fact_file, "a", encoding="utf-8") as file:
                file.writelines(lines)
        except Exception as e:
            print(f"[OBSIDIAN SYNC] Erro ao salvar fatos no vault: {e}")


memory_miner = MemoryMinerAgent()
