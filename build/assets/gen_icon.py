"""Gera o icone do AgentQuest HQ: build/assets/agentquest.ico + frontend/assets/logo.png.

Uso: python build/assets/gen_icon.py
"""

from PIL import Image, ImageDraw

S = 1024  # canvas de trabalho, reduzido depois para cada tamanho do .ico

# Paleta da identidade do painel
ROXO = (168, 85, 247)
ROXO_ESC = (91, 33, 182)
FUNDO_TOPO = (46, 26, 92)
FUNDO_BASE = (13, 12, 38)
CIANO = (56, 189, 248)
CIANO_CLARO = (165, 233, 252)
CORPO = (233, 229, 255)
CORPO_SOMBRA = (183, 175, 230)
VISOR = (15, 13, 43)

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# ── Fundo: quadrado arredondado com gradiente vertical ──
raio = int(S * 0.22)
grad = Image.new("RGBA", (S, S))
gd = ImageDraw.Draw(grad)
for y in range(S):
    t = y / S
    cor = tuple(int(FUNDO_TOPO[i] + (FUNDO_BASE[i] - FUNDO_TOPO[i]) * t) for i in range(3))
    gd.line([(0, y), (S, y)], fill=cor + (255,))

mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=raio, fill=255)
img.paste(grad, (0, 0), mask)

# Borda roxa com leve brilho
d.rounded_rectangle([0, 0, S - 1, S - 1], radius=raio, outline=ROXO + (200,), width=int(S * 0.018))
d.rounded_rectangle(
    [int(S * 0.035), int(S * 0.035), S - 1 - int(S * 0.035), S - 1 - int(S * 0.035)],
    radius=int(raio * 0.82), outline=ROXO_ESC + (110,), width=int(S * 0.008),
)

# ── Antena ──
cx = S // 2
ant_topo = int(S * 0.135)
d.line([(cx, ant_topo + int(S * 0.02)), (cx, int(S * 0.245))], fill=ROXO + (255,), width=int(S * 0.035))
r_bulbo = int(S * 0.052)
# glow do bulbo
for i, alpha in ((int(r_bulbo * 1.9), 45), (int(r_bulbo * 1.45), 90)):
    d.ellipse([cx - i, ant_topo - i, cx + i, ant_topo + i], fill=CIANO + (alpha,))
d.ellipse([cx - r_bulbo, ant_topo - r_bulbo, cx + r_bulbo, ant_topo + r_bulbo], fill=CIANO + (255,))
d.ellipse(
    [cx - int(r_bulbo * 0.42) - int(r_bulbo * 0.28), ant_topo - int(r_bulbo * 0.42) - int(r_bulbo * 0.1),
     cx - int(r_bulbo * 0.42) + int(r_bulbo * 0.28), ant_topo - int(r_bulbo * 0.42) + int(r_bulbo * 0.3)],
    fill=CIANO_CLARO + (255,),
)

# ── Orelhas laterais ──
orelha_w, orelha_h = int(S * 0.058), int(S * 0.17)
orelha_y = int(S * 0.46)
for lado in (-1, 1):
    x = cx + lado * int(S * 0.335) - orelha_w // 2
    d.rounded_rectangle([x, orelha_y, x + orelha_w, orelha_y + orelha_h],
                        radius=int(orelha_w * 0.45), fill=CORPO_SOMBRA + (255,))

# ── Cabeca (mais quadrada, leitura de robo) ──
cab_w, cab_h = int(S * 0.62), int(S * 0.46)
cab_x, cab_y = cx - cab_w // 2, int(S * 0.255)
d.rounded_rectangle([cab_x, cab_y, cab_x + cab_w, cab_y + cab_h],
                    radius=int(S * 0.085), fill=CORPO + (255,))
d.rounded_rectangle([cab_x, cab_y, cab_x + cab_w, cab_y + cab_h],
                    radius=int(S * 0.085), outline=ROXO_ESC + (110,), width=int(S * 0.010))

# ── Visor escuro ocupando a maior parte do rosto ──
vis_w, vis_h = int(cab_w * 0.80), int(cab_h * 0.56)
vis_x, vis_y = cx - vis_w // 2, cab_y + int(cab_h * 0.19)
d.rounded_rectangle([vis_x, vis_y, vis_x + vis_w, vis_y + vis_h],
                    radius=int(vis_h * 0.30), fill=VISOR + (255,))

# ── Olhos: glow contido para nao apagar o visor ──
olho_r = int(vis_h * 0.21)
olho_y = vis_y + int(vis_h * 0.44)
for lado in (-1, 1):
    ox = cx + lado * int(vis_w * 0.26)
    d.ellipse([ox - int(olho_r * 1.45), olho_y - int(olho_r * 1.45),
               ox + int(olho_r * 1.45), olho_y + int(olho_r * 1.45)], fill=CIANO + (70,))
    d.ellipse([ox - olho_r, olho_y - olho_r, ox + olho_r, olho_y + olho_r], fill=CIANO + (255,))
    hl = int(olho_r * 0.36)
    hx, hy = ox - int(olho_r * 0.26), olho_y - int(olho_r * 0.26)
    d.ellipse([hx - hl, hy - hl, hx + hl, hy + hl], fill=CIANO_CLARO + (255,))

# ── Boca: barra de status em pixels, reforca a leitura de robo ──
bw, bh = int(vis_w * 0.30), int(vis_h * 0.10)
by = vis_y + int(vis_h * 0.76)
seg = bw // 3
for i in range(3):
    sx = cx - bw // 2 + i * seg
    alpha = (255, 150, 90)[i]
    d.rounded_rectangle([sx, by, sx + int(seg * 0.66), by + bh],
                        radius=int(bh * 0.4), fill=CIANO + (alpha,))

# ── Base / tronco sugerido ──
tr_w, tr_h = int(S * 0.40), int(S * 0.085)
tr_x, tr_y = cx - tr_w // 2, cab_y + cab_h + int(S * 0.028)
d.rounded_rectangle([tr_x, tr_y, tr_x + tr_w, tr_y + tr_h],
                    radius=int(tr_h * 0.45), fill=CORPO_SOMBRA + (255,))

import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out_dir = os.path.join(REPO, "build", "assets")
os.makedirs(out_dir, exist_ok=True)

# .ico multi-resolucao
tamanhos = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
img.save(os.path.join(out_dir, "agentquest.ico"), format="ICO", sizes=tamanhos)

# PNG para o favicon e o logo do cabecalho do painel
img.resize((256, 256), Image.LANCZOS).save(
    os.path.join(REPO, "frontend", "assets", "logo.png")
)

print("Icone gerado:", os.path.join(out_dir, "agentquest.ico"))
print("Tamanhos embutidos:", tamanhos)
