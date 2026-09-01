"""
Agente Hermes — Orquestrador Geral do Squad
Gerencia o fluxo ponta a ponta: Recepção -> Triagem -> Especialista -> Revisor -> Painel SQLite.
"""

from backend.agents.attendant import AttendantAgent
from backend.agents.administrative import AdministrativeAgent
from backend.agents.financial import FinancialAgent
from backend.agents.commercial import CommercialAgent
from backend.agents.legal_lgpd import LegalLGPDAgent
from backend.agents.planner import PlannerAgent
from backend.agents.reviewer import ReviewerAgent
from backend.tools.obsidian_bridge import obsidian_bridge
from backend.database import SessionLocal, Mission, AgentLog


class HermesOrchestrator:
    def __init__(self):
        self.attendant = AttendantAgent()
        self.admin = AdministrativeAgent()
        self.financial = FinancialAgent()
        self.commercial = CommercialAgent()
        self.legal = LegalLGPDAgent()
        self.planner = PlannerAgent()
        self.reviewer = ReviewerAgent()

    def process_incoming_event(self, raw_text: str, source: str = "whatsapp", db=None, sender_override: str = None):
        """
        Executa o pipeline completo de 5 etapas:
        1. Atendente: Extração estruturada de intenção
        2. Administrativo: Triagem e roteamento por setor
        3. Especialista: Elaboração da resposta/ação técnica
        4. Revisor: Fase reflexiva e validação de qualidade
        5. Persistência: Registro no SQLite e emissão de logs no feed
        """
        close_db_at_end = False
        if db is None:
            db = SessionLocal()
            close_db_at_end = True

        try:
            # ── ETAPA 1: Hermes anuncia início da triagem ──
            db.add(AgentLog(
                agent_name="Hermes",
                color="#a855f7",
                text=f"Novo evento detectado via <strong>{source.capitalize()}</strong>. Iniciando pipeline multi-agente."
            ))
            db.commit()

            # ── ETAPA 2: Atendente lê a mensagem ──
            attendant_data = self.attendant.read_message(raw_text, source)
            sender = sender_override or attendant_data.get("remetente", "Remetente")
            subject = attendant_data.get("assunto", "Demanda recebida")
            urgency = attendant_data.get("urgencia", "media")
            is_urgent = (urgency == "alta")

            db.add(AgentLog(
                agent_name="Atendente",
                color="#3b82f6",
                text=f"Mensagem lida de <strong>{sender}</strong>: \"{subject}\""
            ))
            db.commit()

            # ── MINERAÇÃO DE MEMÓRIA & FATOS CRUZADOS (Oráculo) ──
            try:
                from backend.agents.memory_miner import memory_miner
                memory_miner.mine_conversation(raw_text=raw_text, source_person=sender, source_channel=source)
            except Exception as e:
                print(f"[MEMORY MINER HOOK ERRO] {e}")

            # ── ETAPA 3: Administrativo classifica o setor ──
            routing_data = self.admin.classify(attendant_data)
            sector = routing_data.get("setor", "comercial").lower()

            db.add(AgentLog(
                agent_name="Administrativo",
                color="#f97316",
                text=f"Demanda roteada para o setor <strong>{sector.capitalize()}</strong>."
            ))
            db.commit()

            # ── ETAPA 4: Especialista gera a resposta com base no Obsidian ──
            knowledge_rules = obsidian_bridge.get_knowledge_context()
            context = {
                "source": source,
                "attendant_analysis": attendant_data,
                "routing": routing_data,
                "knowledge_base": knowledge_rules,
                "raw_text": raw_text
            }

            specialist_name = "Comercial"
            specialist_color = "#ef4444"
            draft_response = ""

            if sector == "financeiro":
                specialist_name = "Financeiro"
                specialist_color = "#eab308"
                draft_response = self.financial.generate_response(context)
            elif sector == "juridico":
                specialist_name = "Jurídico LGPD"
                specialist_color = "#6b7280"
                draft_response = self.legal.generate_response(context)
            elif sector == "planejador":
                specialist_name = "Planejador"
                specialist_color = "#14b8a6"
                draft_response = self.planner.generate_response(context)
            else:
                specialist_name = "Comercial"
                specialist_color = "#ef4444"
                draft_response = self.commercial.generate_response(context)

            db.add(AgentLog(
                agent_name=specialist_name,
                color=specialist_color,
                text=f"Rascunho técnico e plano de ação elaborados."
            ))
            db.commit()

            # ── ETAPA 5: Revisor executa Fase Reflexiva ──
            final_reviewed_response = self.reviewer.review_response(
                original_message=raw_text,
                specialist_draft=draft_response,
                channel=source
            )

            db.add(AgentLog(
                agent_name="Revisor",
                color="#22c55e",
                text=f"Fase Reflexiva concluída: texto validado e liberado para aprovação humana."
            ))
            db.commit()

            # ── ETAPA 6: Grava a Missão no Banco de Dados ──
            channel_label = (
                "💬 Disparo automático via WhatsApp" if source == "whatsapp"
                else "✈️ Disparo automático via Telegram" if source == "telegram"
                else "📧 Envio automático por E-mail"
            )

            new_mission = Mission(
                source=source,
                title=f"{subject} — {sender}",
                agent=specialist_name,
                deadline="Hoje" if is_urgent else "Em 48h",
                urgent=is_urgent,
                channel=channel_label,
                response=final_reviewed_response,
                received_message=raw_text,
                status="pending"
            )
            db.add(new_mission)
            db.commit()
            db.refresh(new_mission)

            return new_mission

        finally:
            if close_db_at_end:
                db.close()


# Instância global compartilhada
hermes_orchestrator = HermesOrchestrator()
hermes_bridge = hermes_orchestrator
