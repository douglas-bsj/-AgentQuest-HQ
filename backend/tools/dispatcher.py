"""
Action Dispatcher — AgentQuest HQ
Executa o envio real de mensagens e arquivos quando uma missão é Aprovada:
- 📧 E-mail: Disparo via SMTP (Gmail, Outlook, etc.) ou geração de arquivo .eml
- ✈️ Telegram: Disparo via Telegram Bot API
- 💬 WhatsApp: Geração de link wa.me pronto para clique + arquivo de disparo
- 📋 Ação Interna: Salvamento de minutas e arquivos gerados em outputs/
"""

import os
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")


class ActionDispatcher:
    def __init__(self):
        os.makedirs(OUTPUTS_DIR, exist_ok=True)

    def dispatch(self, source: str, destination: str, subject: str, message_text: str, attachments: list = None) -> dict:
        """
        Roteia o disparo para o canal adequado.
        """
        source = source.lower()
        if source == "email":
            return self._dispatch_email(destination, subject, message_text, attachments)
        elif source == "telegram":
            return self._dispatch_telegram(destination, message_text)
        elif source == "whatsapp":
            return self._dispatch_whatsapp(destination, message_text)
        else:
            return self._dispatch_internal(subject, message_text)

    def _dispatch_email(self, destination: str, subject: str, body: str, attachments: list = None) -> dict:
        """Envia e-mail via SMTP ou salva como minuta em outputs/"""
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_port = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else 587
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        smtp_from = os.getenv("SMTP_FROM", smtp_user)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if smtp_host and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart()
                msg["From"] = smtp_from
                msg["To"] = destination if "@" in destination else smtp_user
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                if attachments:
                    for att_path in attachments:
                        if os.path.isfile(att_path):
                            with open(att_path, "rb") as f:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(att_path)}")
                            msg.attach(part)

                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

                print(f"[DISPATCH EMAIL] E-mail enviado com sucesso via SMTP para: {msg['To']}")
                return {"status": "sent", "channel": "email", "method": "SMTP", "to": msg["To"]}
            except Exception as e:
                print(f"[DISPATCH EMAIL] Erro no SMTP: {e}. Salvando minuta em outputs/...")

        # Fallback / Modo Local Seguro: Salva o e-mail em outputs/
        filename = f"email_{timestamp}.txt"
        file_path = os.path.join(OUTPUTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Para: {destination}\nAssunto: {subject}\nData: {datetime.datetime.now()}\n\n{body}")

        print(f"[DISPATCH EMAIL] Mensagem gravada em outputs/{filename}")
        return {"status": "saved", "channel": "email", "file": f"outputs/{filename}"}

    def _dispatch_telegram(self, chat_id: str, message_text: str) -> dict:
        """Envia mensagem para o Telegram via Bot API ou salva em outputs/"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        target_chat = chat_id if chat_id and chat_id != "Contato Telegram" else os.getenv("TELEGRAM_CHAT_ID", "")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if bot_token and target_chat:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                res = httpx.post(url, json={"chat_id": target_chat, "text": message_text, "parse_mode": "Markdown"}, timeout=10.0)
                if res.status_code == 200:
                    print(f"[DISPATCH TELEGRAM] Mensagem enviada via Bot API para chat {target_chat}")
                    return {"status": "sent", "channel": "telegram", "method": "Bot API"}
            except Exception as e:
                print(f"[DISPATCH TELEGRAM] Erro na API do Telegram: {e}")

        # Fallback / Modo Local: Salva mensagem em outputs/
        filename = f"telegram_{timestamp}.txt"
        file_path = os.path.join(OUTPUTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Telegram Chat: {target_chat}\nData: {datetime.datetime.now()}\n\n{message_text}")

        print(f"[DISPATCH TELEGRAM] Mensagem gravada em outputs/{filename}")
        return {"status": "saved", "channel": "telegram", "file": f"outputs/{filename}"}

    def _dispatch_whatsapp(self, destination: str, message_text: str) -> dict:
        """Envia mensagem real via Evolution API/Z-API ou gera link wa.me como fallback."""
        from backend.tools.settings_manager import settings_manager
        settings = settings_manager.get_settings()
        wa_cfg = settings.get("channels", {}).get("whatsapp", {})

        provider = wa_cfg.get("provider", "evolution")
        api_url = wa_cfg.get("api_url", "").rstrip("/")
        instance = wa_cfg.get("instance_name", "agentquest")
        api_token = wa_cfg.get("api_token", "")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        encoded_text = urllib.parse.quote(message_text)
        clean_phone = "".join(c for c in destination if c.isdigit())
        wa_link = f"https://wa.me/{clean_phone}?text={encoded_text}" if clean_phone else f"https://wa.me/?text={encoded_text}"

        # Tenta envio automático via Evolution API se configurado
        if provider == "evolution" and api_url and api_token and clean_phone:
            try:
                # Endpoint padrão da Evolution API v2: POST /message/sendText/{instance}
                endpoint = f"{api_url}/message/sendText/{instance}"
                headers = {
                    "apikey": api_token,
                    "Content-Type": "application/json"
                }
                payload = {
                    "number": clean_phone,
                    "text": message_text
                }
                res = httpx.post(endpoint, json=payload, headers=headers, timeout=12.0)
                if res.status_code in [200, 201]:
                    print(f"[DISPATCH EVOLUTION API] Mensagem enviada automaticamente para {clean_phone}!")
                    return {
                        "status": "sent",
                        "channel": "whatsapp",
                        "method": "Evolution API",
                        "destination": clean_phone,
                        "wa_link": wa_link
                    }
                else:
                    print(f"[DISPATCH EVOLUTION API] Retorno {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[DISPATCH EVOLUTION API] Falha na requisição: {e}")

        # Fallback padrão seguro: grava em outputs/ e disponibiliza wa.link
        filename = f"whatsapp_{timestamp}.txt"
        file_path = os.path.join(OUTPUTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Destinatário: {destination} ({clean_phone})\nLink WhatsApp Web: {wa_link}\nData: {datetime.datetime.now()}\n\n{message_text}")

        print(f"[DISPATCH WHATSAPP] Resposta gerada. Link direto: {wa_link[:60]}...")
        return {"status": "prepared", "channel": "whatsapp", "wa_link": wa_link, "file": f"outputs/{filename}"}

    def _dispatch_internal(self, title: str, content: str) -> dict:
        """Ação interna: salva arquivo de saída em outputs/"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}.txt"
        file_path = os.path.join(OUTPUTS_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Título: {title}\nData: {datetime.datetime.now()}\n\n{content}")

        print(f"[DISPATCH INTERNO] Arquivo salvo em outputs/{filename}")
        return {"status": "saved", "channel": "internal", "file": f"outputs/{filename}"}


# Instância global
action_dispatcher = ActionDispatcher()
