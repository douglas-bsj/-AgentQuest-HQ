"""
Oracle Agent — AgentQuest HQ
Agente conversacional de Inteligência Artificial que:
1. Responde perguntas do humano cruzando informações e memórias de múltiplas conversas.
2. Explica contradições (ex: "Fulano disse que deixou com Ciclano, mas Ciclano disse que não está com ele").
3. Apresenta termos que a IA precisa aprender e aprende novas definições ensinadas pelo humano em tempo real.
4. Registra novos conhecimentos no cofre do Obsidian.
"""

import os
import json
import datetime
from openai import OpenAI
from backend.database import SessionLocal, MemoryFact, KnowledgeGap, OracleChatMessage
from backend.tools.settings_manager import settings_manager
from backend.utils.paths import base_path

class OracleAgent:
    def __init__(self):
        self.client = None
        self.model = "gemini-3.6-flash"
        self._init_client()

    def _init_client(self):
        cfg = settings_manager.get_settings().get("ai_providers", {})

        api_key = cfg.get("nous_api_key") or os.getenv("NOUS_API_KEY")
        base_url = cfg.get("nous_base_url") or os.getenv("NOUS_BASE_URL", "https://openrouter.ai/api/v1")
        model = cfg.get("nous_model_name") or os.getenv("NOUS_MODEL_NAME", "nousresearch/hermes-3-llama-3.1-405b")

        if not api_key:
            api_key = cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model = cfg.get("gemini_model") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        if api_key:
            try:
                self.client = OpenAI(base_url=base_url, api_key=api_key)
                self.model = model
            except Exception as e:
                print(f"[ORACLE AGENT] Erro ao inicializar cliente IA: {e}")

    def ask(self, question: str) -> dict:
        """
        Recebe a pergunta do usuário, busca fatos no banco e responde com contexto cruzado.
        """
        self._init_client()
        db = SessionLocal()

        try:
            # 1. Recupera todos os fatos relevantes da memória
            facts = db.query(MemoryFact).order_by(MemoryFact.id.desc()).limit(40).all()
            
            # 2. Recupera conhecimentos e termos já aprendidos
            resolved_gaps = db.query(KnowledgeGap).filter(KnowledgeGap.status == "resolved").all()

            # 3. Formata a base de fatos para o Prompt
            facts_context = []
            for f in facts:
                facts_context.append(
                    f"- [{f.category}] Sujeito: '{f.subject}', Relação: '{f.relation}', Objeto: '{f.object_value}', "
                    f"Fonte: '{f.source_person}' ({f.source_channel}). Resumo: \"{f.context_summary}\""
                )
            
            gaps_context = []
            for g in resolved_gaps:
                gaps_context.append(f"- Termo/Assunto '{g.term_or_topic}': {g.learned_definition}")

            facts_text = "\n".join(facts_context) if facts_context else "Nenhum fato minerado ainda."
            gaps_text = "\n".join(gaps_context) if gaps_context else "Nenhum termo personalizado aprendido ainda."

            prompt = f"""Você é o ORÁCULO do AgentQuest HQ, uma inteligência central com memória contínua que lê todas as conversas do usuário.
Sua missão é responder à pergunta do usuário utilizando os fatos e informações aprendidas nas conversas.

DIRETRIZES CRÍTICAS:
1. **CRUZAMENTO DE CONTEXTOS:** Se houver declarações de pessoas diferentes sobre o mesmo assunto (por exemplo: uma pessoa disse que deixou o cartão com fulano, mas fulano disse que não está com ele), mencione explicitamente as duas fontes e a contradição de forma clara.
2. **TERMOS APRENDIDOS:** Utilize o dicionário de termos personalizados sempre que o termo for mencionado.
3. **TRANSPARÊNCIA:** Se você não tiver informações suficientes nas conversas para responder com certeza, diga educadamente o que sabe e o que ainda falta esclarecer.
4. **TOM:** Cordial, assertivo, executivo e objetivo.

BASE DE FATOS EXTRAÍDOS DAS CONVERSAS:
{facts_text}

DICIONÁRIO DE TERMOS APRENDIDOS COM O HUMANO:
{gaps_text}

PERGUNTA DO USUÁRIO:
"{question}"
"""

            answer = ""
            cited_sources = []

            # Passa pelo cliente compartilhado: se o provedor de nuvem estiver
            # fora do ar ou sem cota, a IA Local (Ollama) assume automaticamente
            # em vez de o Oráculo devolver erro.
            from backend.agents.ai_client import chat

            texto, erro = chat(
                "Você é o Oráculo do AgentQuest HQ. Responda em português com base nos fatos fornecidos.",
                prompt,
            )
            if texto and not erro:
                answer = texto
            else:
                print(f"[ORACLE] IA indisponível ({str(erro)[:120]}). Usando resposta heurística local.")
                answer = self._fallback_answer(question, facts)

            # 4. Salva a interação no histórico do chat
            user_msg = OracleChatMessage(sender="user", message=question)
            db.add(user_msg)
            
            oracle_msg = OracleChatMessage(
                sender="oracle", 
                message=answer,
                sources_cited=json.dumps([f.subject for f in facts[:5]])
            )
            db.add(oracle_msg)
            db.commit()

            return {
                "answer": answer,
                "facts_count": len(facts),
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            }

        except Exception as e:
            print(f"[ORACLE ERROR] {e}")
            return {"answer": f"Ocorreu um erro ao consultar a memória: {str(e)}", "facts_count": 0}
        finally:
            db.close()

    def answer_knowledge_gap(self, gap_id: int, human_answer: str) -> dict:
        """
        Humano ensina a definição de um termo que a IA tinha dúvida.
        Salva no banco e persiste no Obsidian.
        """
        db = SessionLocal()
        try:
            gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
            if not gap:
                return {"status": "error", "message": "Dúvida não encontrada."}

            gap.learned_definition = human_answer.strip()
            gap.status = "resolved"
            gap.resolved_at = datetime.datetime.utcnow()

            # Também cria um fato de memória sobre esse aprendizado
            fact = MemoryFact(
                subject=gap.term_or_topic,
                relation="significa / definido_como",
                object_value=human_answer.strip()[:200],
                category="Aprendizado Ativo",
                context_summary=f"Definido diretamente pelo humano: {human_answer.strip()}",
                source_person="Você (Humano)",
                source_channel="chat_oraculo"
            )
            db.add(fact)
            db.commit()

            # Salva no Obsidian / Dicionário
            self._save_term_to_obsidian(gap.term_or_topic, human_answer.strip())

            return {
                "status": "success",
                "message": f"Conhecimento sobre '{gap.term_or_topic}' assimilado com sucesso!",
                "gap": {
                    "id": gap.id,
                    "term": gap.term_or_topic,
                    "definition": gap.learned_definition
                }
            }
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    def _save_term_to_obsidian(self, term: str, definition: str):
        """Grava a definição no cofre Obsidian."""
        try:
            vault_dir = base_path("vault", "01_Base_Conhecimento")
            os.makedirs(vault_dir, exist_ok=True)
            dict_file = os.path.join(vault_dir, "Dicionario_Termos_Aprendidos.md")

            lines = []
            if not os.path.exists(dict_file):
                lines.append("# 📖 Dicionário de Termos & Aprendizados Ativos\n\n")

            lines.append(f"### 📌 {term}\n- **Definição:** {definition}\n- **Data de Aprendizado:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")

            with open(dict_file, "a", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"[ORACLE OBSIDIAN] Erro ao salvar termo no vault: {e}")

    def _fallback_answer(self, question: str, facts: list) -> str:
        """Resposta local heurística caso IA esteja indisponível."""
        q_lower = question.lower()
        matching = []
        for f in facts:
            if any(word in f.context_summary.lower() or word in f.subject.lower() or word in f.object_value.lower() for word in q_lower.split() if len(word) > 3):
                matching.append(f"- **{f.subject}** ({f.source_person}): {f.context_summary}")

        if matching:
            return "Encontrei as seguintes informações nas conversas registradas:\n\n" + "\n".join(matching[:4])
        return "Consultei o histórico das conversas mas não encontrei informações específicas sobre esse tema ainda."


oracle_agent = OracleAgent()
