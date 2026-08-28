"""
AgentQuest HQ — Database Layer
Modelos SQLAlchemy + SQLite local para persistência de missões, logs e histórico.
"""

import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Caminho do banco SQLite ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.sqlite3")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ══════════════════════════════════════════════════════════════════
# ── MODELOS ──────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

class Mission(Base):
    """Missão pendente ou processada — cada card visível no painel."""
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)           # whatsapp | telegram | email
    title = Column(String(300), nullable=False)            # Descrição da missão
    agent = Column(String(50), nullable=False)             # Nome do agente responsável
    deadline = Column(String(20), nullable=False)          # Prazo em texto (ex: "28/08")
    urgent = Column(Boolean, default=False)                # Flag de urgência
    channel = Column(String(200), nullable=False)          # Canal de despacho
    response = Column(Text, nullable=False)                # Resposta rascunhada pelo agente
    status = Column(String(20), default="pending")         # pending | approved | rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class AgentLog(Base):
    """Log de atividade em tempo real dos agentes (feed live)."""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False)
    color = Column(String(10), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ActionHistory(Base):
    """Registro de auditoria de cada aprovação ou rejeição."""
    __tablename__ = "action_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)            # approved | rejected
    edited_response = Column(Text, nullable=True)          # Texto editado (se alterado)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)


# ══════════════════════════════════════════════════════════════════
# ── INICIALIZAÇÃO & SEED ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

# Dados iniciais — mesmas 5 missões que já aparecem no frontend demo
SEED_MISSIONS = [
    {
        "source": "whatsapp",
        "title": "Responder proposta do cliente João Silva — confirmação de prazo",
        "agent": "Comercial",
        "deadline": "28/08",
        "urgent": True,
        "channel": "💬 Disparo automático via WhatsApp",
        "response": (
            "Olá, João! Tudo bem?\n\n"
            "Agradecemos pelo feedback em nossa proposta! "
            "Confirmamos que o prazo de entrega será de 15 dias úteis "
            "a contar da data de assinatura do contrato.\n\n"
            "Caso deseje, podemos formalizar o pedido agora mesmo.\n\n"
            "Fico à total disposição!"
        ),
    },
    {
        "source": "telegram",
        "title": "Follow-up de alinhamento com equipe de TI — migração de servidores",
        "agent": "Planejador",
        "deadline": "29/08",
        "urgent": False,
        "channel": "✈️ Disparo automático via Telegram",
        "response": (
            "Olá, time de TI! Conforme combinado na reunião de ontem:\n\n"
            "1. Documentação da API atualizada até sexta-feira\n"
            "2. Teste no ambiente de homologação na próxima terça\n"
            "3. Janela de migração confirmada para o próximo sábado\n\n"
            "Por favor, confirmem o cronograma."
        ),
    },
    {
        "source": "email",
        "title": "Enviar relatório financeiro compilado de julho para Diretoria",
        "agent": "Financeiro",
        "deadline": "28/08",
        "urgent": True,
        "channel": "📧 Envio automático por E-mail (com anexo .xlsx)",
        "response": (
            "Prezados Diretores,\n\n"
            "Segue o relatório executivo financeiro referente ao mês de Julho:\n\n"
            "• Faturamento Bruto: R$ 92.450,00\n"
            "• Despesas Operacionais: R$ 58.300,00\n"
            "• Margem Líquida: 36,9% (↑ 4.2% vs mês anterior)\n\n"
            "O arquivo analítico segue em anexo para apreciação."
        ),
    },
    {
        "source": "whatsapp",
        "title": "Revisão da Cláusula 4.2 no contrato de prestação de serviços",
        "agent": "Jurídico LGPD",
        "deadline": "30/08",
        "urgent": False,
        "channel": "📋 Ação interna: Minuta atualizada salva em outputs/",
        "response": (
            'Identificamos necessidade de adequação da Cláusula 4.2 ao Artigo 46 da LGPD.\n\n'
            'Texto revisado inserido na minuta:\n'
            '"O CONTRATADO obriga-se a manter medidas de segurança, técnicas e '
            'administrativas aptas a proteger os dados pessoais de acessos não autorizados."\n\n'
            'Documento pronto para envio à assessoria.'
        ),
    },
    {
        "source": "email",
        "title": "Confirmação de horário e pauta da Reunião Semanal de Alinhamento",
        "agent": "Atendente",
        "deadline": "28/08",
        "urgent": False,
        "channel": "📧 Disparo de convite Google Calendar & E-mail",
        "response": (
            "Bom dia a todos!\n\n"
            "Confirmamos a nossa Reunião Semanal de Alinhamento para Quinta-feira, às 10:00h.\n\n"
            "• Sala: Reuniões 02\n"
            "• Link do Meet: meet.google.com/xyz-qwer-tyu\n"
            "• Pauta: Revisão de entregas e metas do próximo ciclo."
        ),
    },
]

SEED_LOGS = [
    {"color": "#a855f7", "agent_name": "Hermes",        "text": "Orquestrando pipeline: 1 nova mensagem recebida do <strong>WhatsApp</strong>"},
    {"color": "#3b82f6", "agent_name": "Atendente",     "text": "Lendo e extraindo intenção do cliente <strong>João Silva</strong>"},
    {"color": "#f97316", "agent_name": "Administrativo", "text": "Pendência classificada para o setor <strong>Comercial</strong>"},
    {"color": "#ef4444", "agent_name": "Comercial",     "text": "Rascunho de resposta de vendas gerado com base no histórico"},
    {"color": "#22c55e", "agent_name": "Revisor",       "text": "Fase Reflexiva concluída: texto validado e liberado para aprovação"},
    {"color": "#eab308", "agent_name": "Financeiro",    "text": "Conciliando extrato de recebimentos com faturas pendentes"},
    {"color": "#14b8a6", "agent_name": "Planejador",    "text": "Ajustando cronograma de entregas no quadro estratégico"},
    {"color": "#6b7280", "agent_name": "Jurídico LGPD", "text": "Varredura de dados sensíveis em documento: 100% em conformidade"},
]


def init_db(force_reset=False):
    """
    Cria as tabelas e popula com dados iniciais.
    Se force_reset=True, apaga o banco e recria do zero.
    Se o banco já existir e tiver dados, não faz nada.
    """
    if force_reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Só popula se o banco estiver vazio
        if db.query(Mission).count() == 0:
            for m in SEED_MISSIONS:
                db.add(Mission(**m))
            db.commit()

        if db.query(AgentLog).count() == 0:
            for log in SEED_LOGS:
                db.add(AgentLog(**log))
            db.commit()
    finally:
        db.close()


def get_db():
    """Dependency injection para FastAPI — fornece sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
