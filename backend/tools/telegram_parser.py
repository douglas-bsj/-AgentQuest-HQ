"""
Telegram Parser — AgentQuest HQ
Lê e processa arquivos de exportação de chat do Telegram (.json).
"""

import json


def parse_telegram_json(file_path: str) -> dict:
    """
    Lê um arquivo .json exportado pelo Telegram Desktop e extrai:
    - full_text: Mensagens em texto
    - last_sender: Nome do último remetente
    - chat_name: Nome do chat
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    chat_name = data.get("name", "Chat Telegram")
    raw_messages = data.get("messages", [])

    parsed_lines = []
    last_sender = "Contato Telegram"

    for msg in raw_messages:
        # Filtra apenas mensagens regulares de texto
        if msg.get("type") == "message":
            sender = msg.get("from", "Usuário")
            last_sender = sender
            text_content = msg.get("text", "")

            # No Telegram, text pode ser string ou lista de partes
            if isinstance(text_content, list):
                parts = []
                for p in text_content:
                    if isinstance(p, str):
                        parts.append(p)
                    elif isinstance(p, dict) and "text" in p:
                        parts.append(p["text"])
                text_content = "".join(parts)

            if text_content.strip():
                parsed_lines.append(f"{sender}: {text_content.strip()}")

    recent = parsed_lines[-15:] if len(parsed_lines) > 15 else parsed_lines
    consolidated_text = f"Chat: {chat_name}\n" + "\n".join(recent)

    return {
        "source": "telegram",
        "sender": last_sender,
        "content": consolidated_text,
        "message_count": len(parsed_lines)
    }
