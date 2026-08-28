"""
E-mail Parser — AgentQuest HQ
Lê arquivos .eml e extrai remetente, assunto, corpo do e-mail e nomes de anexos.
"""

import email
from email import policy
from email.parser import BytesParser


def parse_email_eml(file_path: str) -> dict:
    """
    Lê um arquivo .eml e extrai:
    - sender: Remetente do e-mail
    - subject: Assunto
    - body: Corpo do e-mail em texto puro
    - attachments: Lista de nomes de arquivos em anexo
    """
    with open(file_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    sender = msg.get("from", "Remetente E-mail")
    subject = msg.get("subject", "Sem Assunto")
    body = ""
    attachments = []

    # Extrai o corpo do e-mail
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part:
        body = body_part.get_content()

    # Extrai anexos
    for part in msg.iter_attachments():
        fn = part.get_filename()
        if fn:
            attachments.append(fn)

    att_str = f"\n[Anexos identificados: {', '.join(attachments)}]" if attachments else ""
    full_text = f"De: {sender}\nAssunto: {subject}\n\n{body}{att_str}"

    return {
        "source": "email",
        "sender": sender,
        "subject": subject,
        "content": full_text.strip(),
        "attachments": attachments
    }
