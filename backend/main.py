"""
AgentQuest HQ — FastAPI Server
Servidor REST local que alimenta o painel web com dados reais do SQLite.
"""

import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, Mission, AgentLog, ActionHistory, MemoryFact, KnowledgeGap, OracleChatMessage
from backend.agents.hermes_bridge import hermes_orchestrator, hermes_bridge
from backend.agents.memory_miner import memory_miner
from backend.agents.oracle_agent import oracle_agent
from backend.watcher import start_watcher_thread
from backend.tools.obsidian_bridge import obsidian_bridge
from backend.tools.dispatcher import action_dispatcher
from backend.tools.report_generator import generate_bi_report, export_pdf_file, export_xlsx_file
from backend.agents.feedback_learner import process_feedback_rule
from backend.tools.settings_manager import settings_manager


# ── Lifespan: inicializa o banco e o watcher ao subir o servidor ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[OK] Banco de dados inicializado com sucesso!")
    observer = start_watcher_thread()
    yield
    if observer:
        observer.stop()
        observer.join()


# ── App FastAPI ──────────────────────────────────────────────────
app = FastAPI(
    title="AgentQuest HQ API",
    description="API REST para o painel de missões e BI executivo do AgentQuest HQ",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS: permitir acesso do frontend local (file:// e localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════
# ── SCHEMAS (Pydantic) ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

class MissionOut(BaseModel):
    id: int
    source: str
    title: str
    agent: str
    deadline: str
    urgent: bool
    channel: str
    response: str
    received_message: str | None = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DraftUpdate(BaseModel):
    response: str

class RejectFeedback(BaseModel):
    feedback: str

class AgentInfo(BaseModel):
    id: str
    name: str
    role: str
    icon: str
    color: str
    status: str


class FeedItem(BaseModel):
    id: int
    agent_name: str
    color: str
    text: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    pending: int
    processing: int
    approved: int
    rejected: int


# ── Definição estática dos 8 agentes (status gerenciado em memória)
AGENTS_STATE = [
    {"id": "hermes",     "name": "Hermes",         "role": "Orquestrador Geral",    "icon": "👑", "color": "#a855f7", "status": "ativo"},
    {"id": "atendente",  "name": "Atendente",      "role": "Recepção & Leitura",    "icon": "📖", "color": "#3b82f6", "status": "ativo"},
    {"id": "admin",      "name": "Administrativo", "role": "Triagem & Roteamento",  "icon": "🔍", "color": "#f97316", "status": "ativo"},
    {"id": "financeiro", "name": "Financeiro",     "role": "Cobranças & Notas",     "icon": "💰", "color": "#eab308", "status": "ocioso"},
    {"id": "comercial",  "name": "Comercial",      "role": "Leads & Follow-ups",    "icon": "📈", "color": "#ef4444", "status": "ocioso"},
    {"id": "juridico",   "name": "Jurídico LGPD",  "role": "Contratos & LGPD",      "icon": "⚖️", "color": "#6b7280", "status": "ativo"},
    {"id": "planejador", "name": "Planejador",     "role": "Estratégia & Prazos",   "icon": "🗺️", "color": "#14b8a6", "status": "ocioso"},
    {"id": "revisor",    "name": "Revisor",        "role": "Controle de Qualidade", "icon": "✅", "color": "#22c55e", "status": "ativo"},
]


# ══════════════════════════════════════════════════════════════════
# ── ENDPOINTS ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

class ProcessInput(BaseModel):
    text: str
    source: str = "whatsapp"


@app.post("/api/process", response_model=MissionOut)
def process_message(body: ProcessInput, db: Session = Depends(get_db)):
    """
    Aciona o pipeline completo do Hermes com os 8 agentes:
    Atendente -> Administrativo -> Especialista -> Revisor -> SQLite
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Texto não pode ser vazio")
    
    mission = hermes_orchestrator.process_incoming_event(
        raw_text=body.text,
        source=body.source.lower(),
        db=db
    )
    return mission


@app.get("/api/agents", response_model=list[AgentInfo])
def list_agents():
    """Retorna os 8 agentes com status atual."""
    return AGENTS_STATE


@app.get("/api/missions", response_model=list[MissionOut])
def list_missions(status: str = "pending", db: Session = Depends(get_db)):
    """Lista missões filtradas por status (default: pending)."""
    return db.query(Mission).filter(Mission.status == status).order_by(Mission.created_at.desc()).all()


@app.post("/api/missions/{mission_id}/approve", response_model=MissionOut)
def approve_mission(mission_id: int, db: Session = Depends(get_db)):
    """Aprova uma missão: muda status para 'approved' e registra no histórico."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status not in ["pending", "rejected"]:
        raise HTTPException(status_code=400, detail="Missão já foi processada")

    mission.status = "approved"
    mission.resolved_at = datetime.datetime.utcnow()

    # Registrar no histórico de auditoria SQLite
    history = ActionHistory(
        mission_id=mission.id,
        action="approved",
        edited_response=mission.response,
    )
    db.add(history)

    # Log de atividade
    log = AgentLog(
        agent_name="Você (Humano)",
        color="#22c55e",
        text=f"Aprovou e executou ação da missão <strong>#{mission.id}</strong> — Resposta enviada!",
    )
    db.add(log)

    db.commit()
    db.refresh(mission)

    # ── Atualização do Cofre Obsidian (CRM + Auditoria) ──
    try:
        # Extrai nome do cliente a partir do título (ex: "Assunto — Nome")
        client_name = mission.title.split("—")[-1].strip() if "—" in mission.title else "Cliente_Geral"
        obsidian_bridge.update_client_crm(
            client_name=client_name,
            channel=mission.source,
            mission_title=mission.title,
            response_text=mission.response
        )
        obsidian_bridge.log_approved_action(
            mission_id=mission.id,
            agent_name=mission.agent,
            client_name=client_name,
            response_text=mission.response,
            channel=mission.channel
        )
    except Exception as e:
        print(f"[OBSIDIAN] Erro ao sincronizar cofre: {e}")

    # ── Execução Real do Disparo (E-mail, Telegram, WhatsApp, outputs/) ──
    try:
        # Se for WhatsApp, garante que o número limpo é passado como destino
        dest = client_name
        if mission.source == "whatsapp":
            import re
            phone_match = re.search(r'\((\d+)\)', mission.title)
            if phone_match:
                dest = phone_match.group(1)
            else:
                digits = re.sub(r'\D', '', mission.title)
                if len(digits) >= 10:
                    dest = digits

        dispatch_result = action_dispatcher.dispatch(
            source=mission.source,
            destination=dest,
            subject=mission.title,
            message_text=mission.response
        )
        print(f"[DISPATCH] Resultado da missão #{mission.id}: {dispatch_result}")
    except Exception as e:
        print(f"[DISPATCH] Erro no disparo da ação: {e}")

    return mission


@app.post("/api/missions/{mission_id}/restore", response_model=MissionOut)
def restore_mission(mission_id: int, db: Session = Depends(get_db)):
    """Restaura uma missão rejeitada de volta para a fila pendente."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status != "rejected":
        raise HTTPException(status_code=400, detail="Apenas missões rejeitadas podem ser restauradas")

    mission.status = "pending"
    mission.resolved_at = None

    history = ActionHistory(
        mission_id=mission.id,
        action="restored",
    )
    db.add(history)

    log = AgentLog(
        agent_name="Você (Humano)",
        color="#38bdf8",
        text=f"Restaurou a missão <strong>#{mission.id}</strong> de volta para a fila de aprovação.",
    )
    db.add(log)
    db.commit()
    db.refresh(mission)
    return mission


@app.post("/api/missions/{mission_id}/reject", response_model=MissionOut)
def reject_mission(mission_id: int, db: Session = Depends(get_db)):
    """Rejeita uma missão: muda status para 'rejected' e registra no histórico."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Missão já foi processada")

    mission.status = "rejected"
    mission.resolved_at = datetime.datetime.utcnow()

    history = ActionHistory(
        mission_id=mission.id,
        action="rejected",
    )
    db.add(history)

    log = AgentLog(
        agent_name="Você (Humano)",
        color="#ef4444",
        text=f"Rejeitou a sugestão da missão <strong>#{mission.id}</strong> — Nenhuma ação externa realizada.",
    )
    db.add(log)

    db.commit()
    db.refresh(mission)
    return mission


@app.post("/api/missions/{mission_id}/reject_with_feedback")
def reject_mission_with_feedback(mission_id: int, body: RejectFeedback, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Rejeita missão e usa background task para extrair regra de aprendizado via LLM."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Missão já foi processada")

    mission.status = "rejected"
    mission.resolved_at = datetime.datetime.utcnow()

    history = ActionHistory(
        mission_id=mission.id,
        action="rejected",
    )
    db.add(history)

    log = AgentLog(
        agent_name="Você (Humano)",
        color="#ef4444",
        text=f"Rejeitou a missão <strong>#{mission.id}</strong> ensinando uma nova regra: <em>{body.feedback}</em>",
    )
    db.add(log)
    db.commit()

    # Passa a extração da regra para background (Hermes API call)
    background_tasks.add_task(process_feedback_rule, mission.title, mission.response, body.feedback)

    return {"status": "ok", "message": "Feedback recebido! Agente está analisando e criando a regra."}


@app.put("/api/missions/{mission_id}/draft", response_model=MissionOut)
def update_draft(mission_id: int, body: DraftUpdate, db: Session = Depends(get_db)):
    """Edita o texto da resposta rascunhada pelo agente."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status not in ["pending", "rejected"]:
        raise HTTPException(status_code=400, detail="Só é possível editar missões pendentes ou rejeitadas")

    mission.response = body.response

    log = AgentLog(
        agent_name="Hermes",
        color="#a855f7",
        text=f"Humano editou o rascunho da missão <strong>#{mission.id}</strong>",
    )
    db.add(log)

    db.commit()
    db.refresh(mission)
    return mission


@app.post("/api/webhook/whatsapp")
async def receive_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe mensagens em tempo real da Evolution API e dispara a orquestração dos agentes."""
    try:
        data = await request.json()
        print(f"\n[WHATSAPP WEBHOOK CHEGOU] Evento: {data.get('event')}")
        
        # Estrutura padrão Evolution API v2: data['data']['message']
        event = data.get("event")
        message_data = data.get("data", {})
        
        # Ignora mensagens enviadas por você mesmo (fromMe = True)
        key_info = message_data.get("key", {})
        if key_info.get("fromMe", False):
            print("[WHATSAPP WEBHOOK] Ignorando: mensagem enviada pelo próprio usuário (fromMe=True)")
            return {"status": "ignored", "reason": "outgoing_message"}

        # Verifica filtro de grupos
        remote_jid = key_info.get("remoteJid", "")
        is_group = "@g.us" in remote_jid or "-" in remote_jid.split("@")[0]
        
        cfg = settings_manager.get_settings().get("channels", {}).get("whatsapp", {})
        ignore_groups = cfg.get("ignore_groups", True)
        if is_group and ignore_groups:
            print(f"[WHATSAPP WEBHOOK] Ignorando mensagem de GRUPO ({remote_jid}) conforme configurado.")
            return {"status": "ignored", "reason": "group_message_ignored"}

        # Extrai texto ou legenda de mídia (vídeo, foto, áudio, documento)
        msg = message_data.get("message", {})
        text = (
            msg.get("conversation")
            or msg.get("extendedTextMessage", {}).get("text")
            or msg.get("videoMessage", {}).get("caption")
            or msg.get("imageMessage", {}).get("caption")
            or msg.get("documentMessage", {}).get("caption")
            or msg.get("documentWithCaptionMessage", {}).get("message", {}).get("documentMessage", {}).get("caption")
        )
        
        # Se for mídia sem legenda (vídeo/áudio/imagem direto)
        if not text:
            if "videoMessage" in msg:
                text = "[Vídeo recebido via WhatsApp]"
            elif "imageMessage" in msg:
                text = "[Imagem/Foto recebida via WhatsApp]"
            elif "audioMessage" in msg:
                text = "[Áudio/Mensagem de voz recebida via WhatsApp]"
            elif "documentMessage" in msg:
                filename = msg.get("documentMessage", {}).get("fileName", "documento")
                text = f"[Documento recebido: {filename}]"
            elif "stickerMessage" in msg:
                return {"status": "ignored", "reason": "sticker"}
            else:
                print(f"[WHATSAPP WEBHOOK] Conteúdo não identificado na mensagem: {list(msg.keys())}")
                return {"status": "ignored", "reason": "no_supported_content"}

        # Extrai número e nome do remetente (suporte a formato tradicional @s.whatsapp.net e formato moderno @lid)
        sender_phone = (
            key_info.get("participantAlt", "").split("@")[0]
            or message_data.get("participantAlt", "").split("@")[0]
            or key_info.get("remoteJid", "").split("@")[0]
        )
        # Se vier com sufixo ou caracteres não numéricos
        import re
        digits_phone = re.sub(r"\D", "", sender_phone)
        if len(digits_phone) >= 10:
            sender_phone = digits_phone

        sender_name = message_data.get("pushName") or sender_phone or "Contato WhatsApp"

        print(f"[WHATSAPP WEBHOOK] Mensagem válida de {sender_name} ({sender_phone}): {text[:60]}")
        raw_event = f"Mensagem de {sender_name} ({sender_phone}):\n{text}"
        
        # Processa através da ponte de agentes Hermes
        mission = hermes_bridge.process_incoming_event(
            raw_text=raw_event, 
            source="whatsapp", 
            db=db,
            sender_override=f"{sender_name} ({sender_phone})"
        )
        print(f"[WHATSAPP WEBHOOK] Missão #{mission.id if mission else '?'} gerada com sucesso!")
        
        return {
            "status": "success",
            "message": "Mensagem processada pelo Squad de Agentes!",
            "mission_id": mission.id if mission else None
        }
    except Exception as e:
        print(f"[WEBHOOK WHATSAPP ERRO] {e}")
        return {"status": "error", "detail": str(e)}


@app.get("/api/settings")
def get_settings():
    """Retorna configurações completas do sistema."""
    return settings_manager.get_all()


@app.post("/api/settings")
def update_settings(body: dict):
    """Atualiza e persiste configurações do sistema."""
    saved = settings_manager.save(body)
    return {"status": "success", "message": "Configurações salvas e aplicadas com sucesso!", "settings": saved}


class TestAIInput(BaseModel):
    provider: str
    api_key: str
    base_url: str = ""
    model: str = ""


@app.post("/api/settings/test-ai")
def test_ai_connection(body: TestAIInput):
    """Testa a conexão e resposta de uma chave/modelo de IA."""
    if not body.api_key.strip() and body.provider != "local":
        return {"success": False, "message": "Chave de API não informada."}
        
    try:
        if body.provider in ["nous_openrouter", "openai", "local"]:
            from openai import OpenAI
            base_url = body.base_url or ("https://openrouter.ai/api/v1" if body.provider == "nous_openrouter" else "http://127.0.0.1:8642/v1")
            client = OpenAI(base_url=base_url, api_key=body.api_key)
            model = body.model or ("nousresearch/hermes-3-llama-3.1-405b" if body.provider == "nous_openrouter" else "gpt-4o-mini")
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Responda apenas 'Conectado com sucesso!' em 3 palavras."}],
                max_tokens=30
            )
            reply = res.choices[0].message.content.strip()
            return {"success": True, "message": f"Conexão com IA OK! Resposta: {reply}"}
        elif body.provider == "gemini":
            from google import genai
            client = genai.Client(api_key=body.api_key)
            model = body.model or "gemini-2.5-flash"
            res = client.models.generate_content(model=model, contents="Responda apenas 'Conectado com sucesso!' em 3 palavras.")
            return {"success": True, "message": f"Conexão Gemini OK! Resposta: {res.text.strip()}"}
        else:
            return {"success": False, "message": f"Provedor '{body.provider}' não suportado."}
    except Exception as e:
        return {"success": False, "message": f"Falha no teste de conexão: {str(e)}"}


@app.get("/api/feed", response_model=list[FeedItem])
def list_feed(limit: int = 15, db: Session = Depends(get_db)):
    """Retorna os últimos N logs de atividade dos agentes."""
    return db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()


@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    """Retorna contadores resumidos para o painel de métricas."""
    pending = db.query(Mission).filter(Mission.status == "pending").count()
    approved = db.query(Mission).filter(Mission.status == "approved").count()
    rejected = db.query(Mission).filter(Mission.status == "rejected").count()
    # "processando" = agentes que estão com status processando (contagem estática)
    processing = sum(1 for a in AGENTS_STATE if a["status"] == "processando")
    return StatsOut(pending=pending, processing=processing, approved=approved, rejected=rejected)


class SaveReportInput(BaseModel):
    title: str
    subtitle: str = ""
    kpis: list = []
    synthesis: str = ""


# ── ROTAS DO MÓDULO ORÁCULO & MEMÓRIA VIVA ──────────────────────────
class OracleAskInput(BaseModel):
    question: str

class GapAnswerInput(BaseModel):
    answer: str

class MineTextInput(BaseModel):
    text: str
    person: str = "Desconhecido"
    channel: str = "manual"

@app.get("/api/oracle/chat")
def get_oracle_chat_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retorna o histórico de conversas do usuário com o Oráculo."""
    messages = db.query(OracleChatMessage).order_by(OracleChatMessage.id.asc()).limit(limit).all()
    return [{
        "id": m.id,
        "sender": m.sender,
        "message": m.message,
        "created_at": m.created_at.strftime("%H:%M") if m.created_at else ""
    } for m in messages]

@app.post("/api/oracle/chat")
def ask_oracle(body: OracleAskInput):
    """Envia pergunta para o Oráculo com cruzamento de memórias."""
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode ser vazia.")
    result = oracle_agent.ask(body.question)
    return result

@app.get("/api/oracle/facts")
def get_oracle_facts(limit: int = 50, db: Session = Depends(get_db)):
    """Retorna a lista de fatos e acontecimentos minerados nas conversas."""
    facts = db.query(MemoryFact).order_by(MemoryFact.id.desc()).limit(limit).all()
    return [{
        "id": f.id,
        "subject": f.subject,
        "relation": f.relation,
        "object_value": f.object_value,
        "category": f.category,
        "context_summary": f.context_summary,
        "source_person": f.source_person,
        "source_channel": f.source_channel,
        "created_at": f.created_at.strftime("%d/%m %H:%M") if f.created_at else ""
    } for f in facts]

@app.get("/api/oracle/gaps")
def get_knowledge_gaps(db: Session = Depends(get_db)):
    """Retorna dúvidas/termos desconhecidos que a IA quer esclarecer com o humano."""
    gaps = db.query(KnowledgeGap).order_by(KnowledgeGap.status.desc(), KnowledgeGap.id.desc()).all()
    return [{
        "id": g.id,
        "term": g.term_or_topic,
        "category": g.category,
        "detected_in": g.detected_in_sources,
        "question": g.question_to_human,
        "status": g.status,
        "learned_definition": g.learned_definition
    } for g in gaps]

@app.post("/api/oracle/gaps/{gap_id}/answer")
def answer_gap(gap_id: int, body: GapAnswerInput):
    """Humano ensina a IA sobre uma dúvida/termo específico."""
    if not body.answer.strip():
        raise HTTPException(status_code=400, detail="A resposta não pode ser vazia.")
    res = oracle_agent.answer_knowledge_gap(gap_id, body.answer)
    return res

@app.post("/api/oracle/mine-text")
def mine_custom_text(body: MineTextInput):
    """Minera um texto ou conversa enviada manualmente para a memória."""
    res = memory_miner.mine_conversation(raw_text=body.text, source_person=body.person, source_channel=body.channel)
    return res


@app.get("/api/reports/generate")
def api_generate_report(type: str = "executivo", query: str = "", db: Session = Depends(get_db)):
    """Gera dados reais do relatório estilo Power BI via Hermes + Gemini + SQLite + Obsidian."""
    return generate_bi_report(report_type=type, custom_query=query, db=db)


@app.get("/api/reports/export/pdf")
def api_export_pdf(type: str = "executivo", query: str = "", db: Session = Depends(get_db)):
    """Gera e retorna download de arquivo PDF."""
    report_data = generate_bi_report(report_type=type, custom_query=query, db=db)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"relatorio_{type}_{timestamp}.pdf"
    pdf_path = os.path.join(FRONTEND_DIR, "..", "outputs", pdf_filename)
    export_pdf_file(report_data, pdf_path)
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_filename)


@app.get("/api/reports/export/xlsx")
def api_export_xlsx(type: str = "executivo", query: str = "", db: Session = Depends(get_db)):
    """Gera e retorna download de planilha Excel (.xlsx)."""
    report_data = generate_bi_report(report_type=type, custom_query=query, db=db)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_filename = f"metricas_{type}_{timestamp}.xlsx"
    xlsx_path = os.path.join(FRONTEND_DIR, "..", "outputs", xlsx_filename)
    export_xlsx_file(report_data, db, xlsx_path)
    return FileResponse(xlsx_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=xlsx_filename)


@app.post("/api/reports/save")
def save_report_vault(body: SaveReportInput):
    """Salva um relatório do Hermes BI diretamente no cofre Obsidian."""
    filename = obsidian_bridge.save_bi_report(
        title=body.title,
        subtitle=body.subtitle,
        kpis=body.kpis,
        synthesis=body.synthesis
    )
    return {"status": "success", "filename": filename, "folder": "vault/03_Relatorios_BI/"}


# ── Servir frontend como arquivos estáticos ──────────────────────
import os
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    """Serve o index.html do frontend."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/style.css")
def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"), media_type="text/css")


@app.get("/app.js")
def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"), media_type="application/javascript")
