"""
WhatsApp Parser — AgentQuest HQ
Lê e processa arquivos de exportação de conversas do WhatsApp (.txt).
"""

import re


def parse_whatsapp_txt(file_path: str) -> dict:
    """
    Lê um arquivo .txt de conversa exportada do WhatsApp e retorna:
    - full_text: Texto consolidado das mensagens recentes
    - last_sender: Nome do último remetente
    - message_count: Total de mensagens encontradas
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    messages = []
    last_sender = "Cliente WhatsApp"

    # Padrão comum: [DD/MM/AAAA, HH:MM:SS] Nome: Mensagem OU DD/MM/AAAA HH:MM - Nome: Mensagem
    pattern = re.compile(r"^\[?(\d{1,2}/\d{1,2}/\d{2,4}[,\s]+\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(?:-\s*)?([^:]+):\s*(.*)$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            date_time, sender, content = match.groups()
            sender = sender.strip()
            content = content.strip()
            # Ignora mensagens de sistema do WhatsApp
            if not any(sys in content.lower() for sys in ["mensagens e chamadas são protegidas", "criptografia", "criou o grupo"]):
                messages.append(f"{sender}: {content}")
                last_sender = sender
        else:
            # Continuação da mensagem anterior
            if messages:
                messages[-1] += f" {line}"
            else:
                messages.append(line)

    # Pega as últimas 15 mensagens mais relevantes
    recent_messages = messages[-15:] if len(messages) > 15 else messages
    consolidated_text = "\n".join(recent_messages) if recent_messages else "\n".join(lines[-10:])

    return {
        "source": "whatsapp",
        "sender": last_sender,
        "content": consolidated_text,
        "message_count": len(messages)
    }
