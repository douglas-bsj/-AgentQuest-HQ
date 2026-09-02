"""
AgentQuest HQ — FastAPI Server
Servidor REST local que alimenta o painel web com dados reais do SQLite.
"""

import os
import re
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
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
from backend.tools.first_run import ensure_vault_initialized
from backend.utils.paths import base_path, resource_path
from backend.routers.channels import router as channels_router

FRONTEND_DIR = resource_path("frontend")
OUTPUTS_DIR = base_path("outputs")


# ── Lifespan: inicializa o banco e o watcher ao subir o servidor ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[OK] Banco de dados inicializado com sucesso!")
    settings_manager.hydrate_environment()
    ensure_vault_initialized()
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

app.include_router(channels_router)


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


# ── Definição dos 8 agentes (status sincronizado com eventos reais)
AGENTS_STATE = [
    {"id": "hermes",     "name": "Hermes",         "role": "Orquestrador Geral",    "icon": "👑", "color": "#a855f7", "status": "ativo"},
    {"id": "atendente",  "name": "Atendente",      "role": "Recepção & Leitura",    "icon": "📖", "color": "#3b82f6", "status": "ativo"},
    {"id": "admin",      "name": "Administrativo", "role": "Triagem & Roteamento",  "icon": "🔍", "color": "#f97316", "status": "ativo"},
    {"id": "financeiro", "name": "Financeiro",     "role": "Cobranças & Notas",     "icon": "💰", "color": "#eab308", "status": "ativo"},
    {"id": "comercial",  "name": "Comercial",      "role": "Leads & Follow-ups",    "icon": "📈", "color": "#ef4444", "status": "ativo"},
    {"id": "juridico",   "name": "Jurídico LGPD",  "role": "Contratos & LGPD",      "icon": "⚖️", "color": "#6b7280", "status": "ativo"},
    {"id": "planejador", "name": "Planejador",     "role": "Estratégia & Prazos",   "icon": "🗺️", "color": "#14b8a6", "status": "ativo"},
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


def classificar_remetente(jid: str) -> str:
    """Classifica o remetente de uma mensagem de WhatsApp pelo JID.

    Checar apenas "@g.us" nao era suficiente: grupos e canais no formato novo
    chegam com IDs de 18 digitos e outros sufixos (@newsletter, @lid), e
    passavam pelo filtro como se fossem conversa individual. A regra aqui e
    invertida — so vale como pessoa o que comprovadamente e pessoa.
    """
    if not jid:
        return "desconhecido"
    if jid.endswith("@g.us"):
        return "grupo"
    if jid.endswith("@newsletter"):
        return "canal"
    if jid == "status@broadcast" or jid.endswith("@broadcast"):
        return "transmissao"
    if jid.endswith("@s.whatsapp.net") or jid.endswith("@lid"):
        numero = re.sub(r"\D", "", jid.split("@")[0])
        # Telefones tem no maximo 15 digitos (padrao E.164); acima disso e
        # identificador de grupo/canal
        return "grupo" if len(numero) > 15 else "individual"
    return "desconhecido"


@app.get("/api/webhook/whatsapp")
def verify_whatsapp_webhook(request: Request):
    """Verificação do webhook exigida pela Meta ao registrar a Cloud API.

    A Meta chama esta URL com hub.verify_token e espera receber de volta o
    hub.challenge em texto puro quando o token confere.
    """
    params = request.query_params
    modo = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    esperado = (
        settings_manager.get_settings()
        .get("channels", {})
        .get("whatsapp", {})
        .get("meta_verify_token", "")
    )

    if modo == "subscribe" and token and token == esperado:
        print("[WEBHOOK META] Verificação aceita.")
        return PlainTextResponse(challenge or "")

    print("[WEBHOOK META] Verificação recusada: token não confere.")
    raise HTTPException(status_code=403, detail="Verify token inválido.")


@app.post("/api/webhook/whatsapp")
async def receive_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Recebe mensagens em tempo real do provedor de WhatsApp e dispara a
    orquestração dos agentes.

    Aceita dois formatos: o da Evolution API (também usado pela ponte Baileys,
    que o imita de propósito) e o da Cloud API oficial da Meta.
    """
    try:
        data = await request.json()

        # ── Formato da Meta: entry[].changes[].value.messages[] ──
        if data.get("object") == "whatsapp_business_account":
            from backend.tools.meta_cloud_manager import parse_incoming

            recebidas = parse_incoming(data)
            if not recebidas:
                return {"status": "ignored", "reason": "sem mensagens de texto no payload"}

            def processar_meta(raw, remetente):
                from backend.database import SessionLocal
                bg_db = SessionLocal()
                try:
                    hermes_bridge.process_incoming_event(
                        raw_text=raw, source="whatsapp", db=bg_db, sender_override=remetente
                    )
                finally:
                    bg_db.close()

            for m in recebidas:
                print(f"[WEBHOOK META] Mensagem de {m['nome']} ({m['numero']}): {m['texto'][:60]}")
                raw_event = f"Mensagem de {m['nome']} ({m['numero']}):\n{m['texto']}"
                background_tasks.add_task(
                    processar_meta, raw_event, f"{m['nome']} ({m['numero']})"
                )

            return {"status": "success", "processadas": len(recebidas)}

        print(f"\n[WHATSAPP WEBHOOK CHEGOU] Evento: {data.get('event')}")

        # Estrutura padrão Evolution API v2: data['data']['message']
        event = data.get("event")
        message_data = data.get("data", {})
        
        # Ignora mensagens enviadas por você mesmo (fromMe = True), mas usa isso para auto-aprovar missões!
        key_info = message_data.get("key", {})
        if key_info.get("fromMe", False):
            print("[WHATSAPP WEBHOOK] Mensagem enviada pelo próprio usuário (fromMe=True). Auto-aprovando missões...")
            remote_jid = key_info.get("remoteJid", "")
            if remote_jid:
                contact_number = remote_jid.split("@")[0]
                import re
                contact_number = re.sub(r"\D", "", contact_number)
                
                # Procura missão pendente no banco para este contato
                pending_missions = db.query(Mission).filter(Mission.status == "pending").all()
                for m in pending_missions:
                    if contact_number in m.title or contact_number in (m.received_message or ""):
                        m.status = "executed"
                        import datetime
                        m.resolved_at = datetime.datetime.utcnow()
                        db.commit()
                        print(f"[AUTO-APROVAÇÃO] Missão #{m.id} fechada pois o humano respondeu via celular.")
            return {"status": "success", "reason": "auto_approved_on_human_reply"}

        # Filtro de grupos, canais e transmissões
        remote_jid = key_info.get("remoteJid", "")
        tipo_remetente = classificar_remetente(remote_jid)

        if tipo_remetente == "transmissao":
            return {"status": "ignored", "reason": "status_broadcast"}

        cfg = settings_manager.get_settings().get("channels", {}).get("whatsapp", {})
        ignore_groups = cfg.get("ignore_groups", True)
        if ignore_groups and tipo_remetente != "individual":
            print(f"[WHATSAPP WEBHOOK] Ignorando mensagem de {tipo_remetente.upper()} ({remote_jid}) conforme configurado.")
            return {"status": "ignored", "reason": f"{tipo_remetente}_ignorado"}

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
            elif "documentWithCaptionMessage" in msg:
                doc = msg.get("documentWithCaptionMessage", {}).get("message", {}).get("documentMessage", {})
                filename = doc.get("fileName", "documento")
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
        
        # Processa através da ponte de agentes Hermes em background para não dar timeout no Evolution API
        def process_background(raw, source, s_override):
            # Usar uma nova sessao de banco para a thread em background
            from backend.database import SessionLocal
            bg_db = SessionLocal()
            try:
                hermes_bridge.process_incoming_event(
                    raw_text=raw, 
                    source=source, 
                    db=bg_db,
                    sender_override=s_override
                )
            finally:
                bg_db.close()

        background_tasks.add_task(process_background, raw_event, "whatsapp", f"{sender_name} ({sender_phone})")
        
        return {
            "status": "success",
            "message": "Mensagem enfileirada para processamento!"
        }
    except Exception as e:
        print(f"[WEBHOOK WHATSAPP ERRO] {e}")
        return {"status": "error", "detail": str(e)}


@app.post("/api/missions/{mission_id}/generate", response_model=MissionOut)
def generate_ai_response(mission_id: int, db: Session = Depends(get_db)):
    """Gera a resposta da IA para uma missão pendente (sob demanda)."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Missão não está pendente")
    
    try:
        updated_mission = hermes_bridge.generate_ai_response_for_mission(mission_id, db)
        return updated_mission
    except Exception as e:
        print(f"[GERAR RESPOSTA ERRO] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
def get_settings():
    """Retorna configurações completas do sistema."""
    return settings_manager.get_all()


@app.post("/api/settings")
def update_settings(body: dict):
    """Atualiza e persiste configurações do sistema."""
    saved = settings_manager.save(body)
    return {"status": "success", "message": "Configurações salvas e aplicadas com sucesso!", "settings": saved}


@app.get("/api/settings/onboarding-status")
def onboarding_status():
    """Indica se a instalação atual ainda precisa do assistente de primeira execução."""
    cfg = settings_manager.get_settings().get("ai_providers", {})
    has_key = any(cfg.get(k) for k in ("gemini_api_key", "nous_api_key", "openai_api_key"))
    provider_is_local = cfg.get("active_provider") == "local"
    return {"needs_onboarding": not has_key and not provider_is_local}


class OnboardingInput(BaseModel):
    gemini_api_key: str


@app.post("/api/settings/onboarding")
def save_onboarding(body: OnboardingInput):
    """Grava só a chave Gemini (gravação parcial, sem apagar o resto das configurações)
    e valida a chave na hora, para o assistente de primeira execução."""
    settings_manager.update_partial({
        "ai_providers": {"gemini_api_key": body.gemini_api_key, "active_provider": "gemini"},
    })
    return check_ai_provider_status(provider="gemini", api_key=body.gemini_api_key)


class TestAIInput(BaseModel):
    provider: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""


def check_ai_provider_status(provider: str, api_key: str = "", model: str = "", base_url: str = ""):
    """Diagnóstico em tempo real da conta, cota, créditos, latência e status do provedor de IA."""
    import time
    import datetime
    import json
    import urllib.request
    import re

    provider = (provider or "gemini").lower().strip()
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Se não passou chave e não for local, tenta carregar das configurações
    if not api_key.strip() and provider != "local":
        cfg = settings_manager.get_settings().get("ai_providers", {})
        if provider == "gemini":
            api_key = cfg.get("gemini_api_key", "")
            model = model or cfg.get("gemini_model", "gemini-3.6-flash")
        elif provider == "nous_openrouter":
            api_key = cfg.get("nous_api_key", "")
            model = model or cfg.get("nous_model_name", "nousresearch/hermes-3-llama-3.1-405b")
            base_url = base_url or cfg.get("nous_base_url", "https://openrouter.ai/api/v1")
        elif provider == "openai":
            api_key = cfg.get("openai_api_key", "")
            model = model or cfg.get("openai_model", "gpt-4o-mini")

    if not api_key.strip() and provider != "local":
        return {
            "success": False,
            "status": "not_configured",
            "status_badge": "⚪ Não Configurado",
            "provider": provider,
            "provider_label": "Google Gemini" if provider == "gemini" else ("OpenRouter" if provider == "nous_openrouter" else ("OpenAI" if provider == "openai" else "Local")),
            "model": model or "Padrão",
            "latency_ms": 0,
            "checked_at": now_str,
            "credits_info": "Chave de API não informada",
            "message": "Nenhuma chave de API configurada para este provedor.",
            "recommendation": "Insira uma chave no formulário e clique em Salvar ou Testar."
        }

    t0 = time.perf_counter()

    # ── NOUS / OPENROUTER ──
    if provider == "nous_openrouter":
        base_url = base_url or "https://openrouter.ai/api/v1"
        model = model or "nousresearch/hermes-3-llama-3.1-405b"
        credits_info = "Consultando OpenRouter..."

        # 1. Consulta metadados da chave na API do OpenRouter
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}", "User-Agent": "AgentQuestHQ/2.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                key_data = json.loads(resp.read().decode()).get("data", {})
                usage = key_data.get("usage", 0)
                limit = key_data.get("limit")
                is_free = key_data.get("is_free_tier", False)
                if limit is not None:
                    remaining = max(0, limit - usage)
                    credits_info = f"Saldo: ${remaining:.4f} (Usado: ${usage:.4f})"
                elif is_free:
                    credits_info = f"Plano Free Tier (Uso: ${usage:.4f})"
                else:
                    credits_info = f"Conta Ativa (Uso total: ${usage:.4f})"
        except Exception:
            credits_info = "Chave Ativa (Verificada via Chamada)"

        # 2. Chamada de teste
        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url, api_key=api_key)
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Responda apenas 'OK'."}],
                max_tokens=10,
                timeout=12
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": True,
                "status": "online",
                "status_badge": "🟢 Operacional & Online",
                "provider": provider,
                "provider_label": "OpenRouter / Nous Research",
                "model": model,
                "latency_ms": latency_ms,
                "checked_at": now_str,
                "credits_info": credits_info,
                "message": f"Conexão OK! Modelo respondeu em {latency_ms}ms.",
                "recommendation": ""
            }
        except Exception as e:
            err_str = str(e)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if "402" in err_str or "insufficient" in err_str.lower() or "credits" in err_str.lower():
                return {
                    "success": False,
                    "status": "quota_exhausted",
                    "status_badge": "🟡 Saldo Esgotado (402)",
                    "provider": provider,
                    "provider_label": "OpenRouter / Nous Research",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Sem saldo disponível na conta OpenRouter",
                    "message": "Seus créditos no OpenRouter acabaram. Recarregue em openrouter.ai/credits.",
                    "recommendation": "Adicione créditos ou use modelos gratuitos como hermes-3."
                }
            elif "401" in err_str or "auth" in err_str.lower():
                return {
                    "success": False,
                    "status": "invalid_key",
                    "status_badge": "🔴 Chave Inválida (401)",
                    "provider": provider,
                    "provider_label": "OpenRouter / Nous Research",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Não autenticado",
                    "message": "Chave OpenRouter inválida ou revogada.",
                    "recommendation": "Gere uma nova chave em openrouter.ai/keys."
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "status_badge": "🔴 Fora do Ar / Erro",
                    "provider": provider,
                    "provider_label": "OpenRouter / Nous Research",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": credits_info,
                    "message": f"Erro de comunicação: {err_str[:120]}",
                    "recommendation": "Verifique sua conexão ou se o modelo está acessível."
                }

    # ── GOOGLE GEMINI ──
    elif provider == "gemini":
        model = model or "gemini-3.6-flash"
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            res = client.models.generate_content(
                model=model,
                contents="Diga OK."
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": True,
                "status": "online",
                "status_badge": "🟢 Operacional & Online",
                "provider": provider,
                "provider_label": "Google Gemini",
                "model": model,
                "latency_ms": latency_ms,
                "checked_at": now_str,
                "credits_info": "Plano Free Tier (Google AI Studio) • Cota Ativa",
                "message": f"Conexão Gemini OK! Modelo '{model}' respondeu em {latency_ms}ms.",
                "recommendation": ""
            }
        except Exception as e:
            err_str = str(e)
            latency_ms = int((time.perf_counter() - t0) * 1000)

            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Tenta extrair tempo de espera
                retry_match = re.search(r"retry in (\d+[\.\d]*)s", err_str, re.IGNORECASE) or re.search(r"retryDelay': '(\d+s)'", err_str)
                retry_info = f" (Liberando em ~{retry_match.group(1)})" if retry_match else ""
                return {
                    "success": False,
                    "status": "rate_limited",
                    "status_badge": "🟡 Limite de Requisições Atingido (429)",
                    "provider": provider,
                    "provider_label": "Google Gemini",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": f"Quota de Requisições por Minuto/Dia Atingida{retry_info}",
                    "message": f"O plano gratuito do Gemini atingiu o limite de cota temporária.{retry_info}",
                    "recommendation": "Aguarde cerca de 30-60 segundos para restabelecer ou crie uma chave alternativa no aistudio.google.com."
                }
            elif "404" in err_str or "NOT_FOUND" in err_str:
                return {
                    "success": False,
                    "status": "model_not_found",
                    "status_badge": "🟡 Modelo Não Encontrado (404)",
                    "provider": provider,
                    "provider_label": "Google Gemini",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Modelo indisponível",
                    "message": f"O modelo '{model}' não foi localizado na API do Google Gemini.",
                    "recommendation": "Selecione o modelo 'gemini-3.6-flash' que é o recomendado e ultra rápido."
                }
            elif "400" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str or "unauthenticated" in err_str.lower():
                return {
                    "success": False,
                    "status": "invalid_key",
                    "status_badge": "🔴 Chave Gemini Inválida (403)",
                    "provider": provider,
                    "provider_label": "Google Gemini",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Chave não autorizada",
                    "message": "Chave do Google Gemini não reconhecida ou sem permissão de acesso.",
                    "recommendation": "Obtenha uma nova chave gratuita em aistudio.google.com/app/apikey."
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "status_badge": "🔴 Falha de Conexão Gemini",
                    "provider": provider,
                    "provider_label": "Google Gemini",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Erro no provedor",
                    "message": f"Falha no Gemini: {err_str[:120]}",
                    "recommendation": "Verifique sua conexão de rede ou tente novamente."
                }

    # ── OPENAI ──
    elif provider == "openai":
        model = model or "gpt-4o-mini"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Responda apenas 'OK'."}],
                max_tokens=10,
                timeout=12
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": True,
                "status": "online",
                "status_badge": "🟢 Operacional & Online",
                "provider": provider,
                "provider_label": "OpenAI Oficial",
                "model": model,
                "latency_ms": latency_ms,
                "checked_at": now_str,
                "credits_info": "Conta Ativa • Saldo Disponível",
                "message": f"Conexão OpenAI OK! Modelo '{model}' respondeu em {latency_ms}ms.",
                "recommendation": ""
            }
        except Exception as e:
            err_str = str(e)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if "insufficient_quota" in err_str.lower() or "quota" in err_str.lower():
                return {
                    "success": False,
                    "status": "quota_exhausted",
                    "status_badge": "🔴 Saldo Esgotado na OpenAI (Quota)",
                    "provider": provider,
                    "provider_label": "OpenAI Oficial",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Saldo $0.00 / Limite Excedido",
                    "message": "Sua conta da OpenAI está sem saldo disponível.",
                    "recommendation": "Recarregue seus créditos em platform.openai.com/account/billing."
                }
            elif "invalid_api_key" in err_str.lower() or "401" in err_str:
                return {
                    "success": False,
                    "status": "invalid_key",
                    "status_badge": "🔴 Chave OpenAI Inválida (401)",
                    "provider": provider,
                    "provider_label": "OpenAI Oficial",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Não autenticado",
                    "message": "Chave sk-... da OpenAI inválida ou revogada.",
                    "recommendation": "Verifique sua chave em platform.openai.com/api-keys."
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "status_badge": "🔴 Erro OpenAI",
                    "provider": provider,
                    "provider_label": "OpenAI Oficial",
                    "model": model,
                    "latency_ms": latency_ms,
                    "checked_at": now_str,
                    "credits_info": "Erro no provedor",
                    "message": f"Falha na OpenAI: {err_str[:120]}",
                    "recommendation": ""
                }

    # ── LOCAL GATEWAY ──
    elif provider == "local":
        base_url = base_url or "http://127.0.0.1:8642/v1"
        try:
            from openai import OpenAI
            client = OpenAI(base_url=base_url, api_key=api_key or "agentquest-local-key")
            res = client.models.list()
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": True,
                "status": "online",
                "status_badge": "🟢 Gateway Local Online",
                "provider": provider,
                "provider_label": "Hermes Local Gateway",
                "model": "Local Host",
                "latency_ms": latency_ms,
                "checked_at": now_str,
                "credits_info": "Execução Local (Gratuito / Ilimitado)",
                "message": f"Servidor local ativo em {base_url} (Respondendo em {latency_ms}ms).",
                "recommendation": ""
            }
        except Exception as e:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "success": False,
                "status": "offline",
                "status_badge": "🔴 Gateway Local Desconectado",
                "provider": provider,
                "provider_label": "Hermes Local Gateway",
                "model": "Local Host",
                "latency_ms": latency_ms,
                "checked_at": now_str,
                "credits_info": "Servidor offline",
                "message": f"Não foi possível conectar ao endpoint local {base_url}.",
                "recommendation": "Inicie o servidor local (Ollama / vLLM / LM Studio / Hermes Gateway)."
            }

    return {
        "success": False,
        "status": "error",
        "status_badge": "🔴 Provedor Não Suportado",
        "provider": provider,
        "provider_label": provider,
        "model": model,
        "latency_ms": 0,
        "checked_at": now_str,
        "credits_info": "N/A",
        "message": f"Provedor '{provider}' não suportado.",
        "recommendation": ""
    }


@app.post("/api/settings/test-ai")
def test_ai_connection(body: TestAIInput):
    """Testa a conexão e retorna diagnóstico completo de conta, latência e status."""
    return check_ai_provider_status(
        provider=body.provider,
        api_key=body.api_key,
        model=body.model,
        base_url=body.base_url
    )


@app.get("/api/settings/ai-status")
def get_ai_status(provider: str = None, api_key: str = None, model: str = None, base_url: str = None):
    """Retorna o status em tempo real do provedor configurado no sistema."""
    cfg = settings_manager.get_settings().get("ai_providers", {})
    p = provider or cfg.get("active_provider", "gemini")
    k = api_key or (cfg.get("gemini_api_key") if p == "gemini" else (cfg.get("nous_api_key") if p == "nous_openrouter" else cfg.get("openai_api_key", "")))
    m = model or (cfg.get("gemini_model") if p == "gemini" else (cfg.get("nous_model_name") if p == "nous_openrouter" else cfg.get("openai_model", "")))
    u = base_url or (cfg.get("nous_base_url") if p == "nous_openrouter" else cfg.get("local_base_url", ""))
    
    return check_ai_provider_status(provider=p, api_key=k, model=m, base_url=u)



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
    pdf_path = os.path.join(OUTPUTS_DIR, pdf_filename)
    export_pdf_file(report_data, pdf_path)
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_filename)


@app.get("/api/reports/export/xlsx")
def api_export_xlsx(type: str = "executivo", query: str = "", db: Session = Depends(get_db)):
    """Gera e retorna download de planilha Excel (.xlsx)."""
    report_data = generate_bi_report(report_type=type, custom_query=query, db=db)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_filename = f"metricas_{type}_{timestamp}.xlsx"
    xlsx_path = os.path.join(OUTPUTS_DIR, xlsx_filename)
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
