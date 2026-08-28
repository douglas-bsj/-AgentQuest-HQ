"""
Inbox Watcher — AgentQuest HQ
Monitora continuamente a pasta inbox/ usando watchdog.
Ao detectar um novo arquivo:
1. Identifica a extensão e roda o parser correspondente
2. Aciona o HermesOrchestrator para processar com o squad de IA
3. Move o arquivo original para processed/ com timestamp
"""

import os
import time
import shutil
import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.tools.whatsapp_parser import parse_whatsapp_txt
from backend.tools.telegram_parser import parse_telegram_json
from backend.tools.email_parser import parse_email_eml
from backend.tools.doc_parser import parse_document
from backend.agents.hermes_bridge import hermes_orchestrator
from backend.database import SessionLocal, AgentLog

# Caminhos das pastas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")


def process_inbox_file(file_path: str):
    """
    Processa um arquivo que caiu na pasta inbox/.
    """
    if not os.path.isfile(file_path):
        return

    filename = os.path.basename(file_path)
    # Ignora arquivos ocultos, temporários ou .gitkeep
    if filename.startswith(".") or filename.endswith(".tmp"):
        return

    print(f"\n[INBOX] Novo arquivo detectado: {filename}")
    time.sleep(0.5)  # Espera escrita do arquivo terminar

    ext = os.path.splitext(filename)[1].lower()
    parsed_data = None

    try:
        if ext == ".txt":
            # Pode ser export de WhatsApp ou texto simples
            parsed_data = parse_whatsapp_txt(file_path)
        elif ext == ".json":
            # Export de chat do Telegram
            parsed_data = parse_telegram_json(file_path)
        elif ext in [".eml", ".msg"]:
            # Mensagem de e-mail
            parsed_data = parse_email_eml(file_path)
        elif ext in [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv"]:
            # Documentos e planilhas
            parsed_data = parse_document(file_path)
        else:
            print(f"[INBOX] Extensão não suportada: {ext}")
            return

        if parsed_data and parsed_data.get("content"):
            print(f"[HERMES] Iniciando orquestração para {filename} (Canal: {parsed_data['source']})...")
            
            db = SessionLocal()
            try:
                mission = hermes_orchestrator.process_incoming_event(
                    raw_text=parsed_data["content"],
                    source=parsed_data.get("source", "whatsapp"),
                    db=db
                )
                print(f"[SUCESSO] Missão #{mission.id} criada: {mission.title}")
            finally:
                db.close()

            # Mover arquivo para processed/
            os.makedirs(PROCESSED_DIR, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_filename = f"{timestamp}_{filename}"
            dest_path = os.path.join(PROCESSED_DIR, dest_filename)
            shutil.move(file_path, dest_path)
            print(f"[ARQUIVADO] Arquivo movido para: processed/{dest_filename}")

    except Exception as e:
        print(f"[ERRO] Falha ao processar arquivo {filename}: {e}")
        db = SessionLocal()
        try:
            db.add(AgentLog(
                agent_name="Hermes",
                color="#ef4444",
                text=f"Erro ao processar arquivo <strong>{filename}</strong>: {str(e)[:100]}"
            ))
            db.commit()
        finally:
            db.close()


class InboxHandler(FileSystemEventHandler):
    """Handler de eventos do Watchdog para a pasta inbox/"""

    def on_created(self, event):
        if not event.is_directory:
            process_inbox_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            process_inbox_file(event.dest_path)


def start_watcher_thread():
    """
    Inicia o monitoramento da pasta inbox/ em uma thread separada.
    """
    import threading

    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, path=INBOX_DIR, recursive=False)
    observer.start()
    print(f"[WATCHER] Monitorando pasta inbox/ ({INBOX_DIR})")

    # Varre arquivos que já estavam na pasta inbox/ ao iniciar
    for f in os.listdir(INBOX_DIR):
        full_p = os.path.join(INBOX_DIR, f)
        if os.path.isfile(full_p) and not f.startswith("."):
            threading.Thread(target=process_inbox_file, args=(full_p,), daemon=True).start()

    return observer
