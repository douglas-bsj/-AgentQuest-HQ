"""
AgentQuest HQ — FastAPI Server
Servidor REST local que alimenta o painel web com dados reais do SQLite.
"""

import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import init_db, get_db, Mission, AgentLog, ActionHistory


# ── Lifespan: inicializa o banco ao subir o servidor ─────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[OK] Banco de dados inicializado com sucesso!")
    yield


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
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DraftUpdate(BaseModel):
    response: str


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
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Missão já foi processada")

    mission.status = "approved"
    mission.resolved_at = datetime.datetime.utcnow()

    # Registrar no histórico de auditoria
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


@app.put("/api/missions/{mission_id}/draft", response_model=MissionOut)
def update_draft(mission_id: int, body: DraftUpdate, db: Session = Depends(get_db)):
    """Edita o texto da resposta rascunhada pelo agente."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    if mission.status != "pending":
        raise HTTPException(status_code=400, detail="Só é possível editar missões pendentes")

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
