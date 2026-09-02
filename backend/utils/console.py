"""
Configuracao de codificacao do console.

No Windows o stdout costuma usar cp1252, que nao representa emojis. Como as
mensagens de WhatsApp quase sempre trazem emoji, qualquer print do texto
recebido lancava UnicodeEncodeError — e, dentro do webhook, esse erro era
capturado pelo tratamento generico e a mensagem acabava descartada em vez de
gerar missao.

Forcar UTF-8 com errors="replace" garante que o log nunca derrube o
processamento: no pior caso um caractere aparece como "?" no console.
"""

import sys


def configurar_console_utf8():
    for stream in (sys.stdout, sys.stderr):
        # Em builds sem console (windowed) os streams podem ser None
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Streams redirecionados podem nao suportar reconfigure —
            # nesse caso seguimos com o comportamento padrao.
            pass
