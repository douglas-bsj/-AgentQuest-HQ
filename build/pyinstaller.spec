# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para o AgentQuest HQ (modo onedir).

Rodado a partir da pasta de staging sanitizada criada por
scripts/build_release.py — nunca direto no repositório de desenvolvimento,
para que dados reais (vault/, settings.json, .env, banco) jamais entrem
no pacote distribuído.
"""

from PyInstaller.utils.hooks import collect_all

datas = [
    ("frontend", "frontend"),
    ("vault_template", "vault_template"),
    ("docker-compose.evolution.yml", "."),
    (".env.example", "."),
]

# O ícone é copiado para o staging pelo build_release.py.
ICON_FILE = "agentquest.ico"
binaries = []
hiddenimports = [
    "sqlalchemy.sql.default_comparator",
    "aiosqlite",
    "uvicorn.logging",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan.on",
]

# SDKs do Google/gRPC carregam muitos submódulos dinamicamente —
# collect_all é mais confiável que listar hidden-imports manualmente.
for pkg in ("google.genai", "grpc", "google.api_core"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden


a = Analysis(
    ["start_system.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AgentQuestHQ",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_FILE,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AgentQuestHQ",
)
