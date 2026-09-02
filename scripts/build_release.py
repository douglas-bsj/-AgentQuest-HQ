"""
Build de release do AgentQuest HQ.

Pipeline: staging sanitizado -> PyInstaller (onedir) -> Inno Setup (.exe).

O staging é a trava de segurança central: só entra no pacote o que está na
allow-list explícita, e o build aborta se qualquer arquivo com dado real
(settings.json, .env, banco, vault do usuário) escapar para lá.

Uso:
    python scripts/build_release.py [--skip-installer]
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_node import fetch_node

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
STAGING_DIR = os.path.join(BUILD_DIR, "staging")
WORK_DIR = os.path.join(BUILD_DIR, "work")
DIST_DIR = os.path.join(BUILD_DIR, "dist")
OUTPUT_DIR = os.path.join(BUILD_DIR, "output")

APP_VERSION = "1.0.0"
ICON_NAME = "agentquest.ico"

# Só isto entra no pacote distribuído.
ALLOWED_DIRS = ["backend", "frontend", "vault_template", "whatsapp-bridge"]
ALLOWED_FILES = [
    "run.py",
    "start_system.py",
    "requirements.txt",
    "docker-compose.evolution.yml",
    ".env.example",
]

# Nada disto pode chegar ao staging — contém dados/segredos reais.
FORBIDDEN_IN_STAGING = [
    "settings.json",
    ".env",
    "vault",
    ".git",
    "whatsapp_session",
    os.path.join("backend", "database.sqlite3"),
    os.path.join("whatsapp-bridge", "auth_state"),
]

# Únicos executáveis permitidos no pacote (Node portátil da ponte de WhatsApp).
ALLOWED_EXECUTABLES = {os.path.join("node", "node.exe")}

PHONE_PATTERN = re.compile(r"\(\d{10,}\)")
EXPECTED_VAULT_FOLDERS = {
    "00_Dashboard",
    "01_Base_Conhecimento",
    "02_Clientes_CRM",
    "03_Relatorios_BI",
    "04_Historico_Acoes",
}


def fail(message):
    print(f"\n[BUILD ABORTADO] {message}")
    sys.exit(1)


def validate_vault_template():
    """Garante que o template distribuído não carrega dado pessoal."""
    template_dir = os.path.join(PROJECT_ROOT, "vault_template")
    if not os.path.isdir(template_dir):
        fail("vault_template/ não encontrado — necessário para instalações limpas.")

    found_folders = {e for e in os.listdir(template_dir) if os.path.isdir(os.path.join(template_dir, e))}
    unexpected = found_folders - EXPECTED_VAULT_FOLDERS
    if unexpected:
        fail(f"vault_template/ tem pastas inesperadas: {sorted(unexpected)}")

    for root, _, files in os.walk(template_dir):
        for name in files:
            if PHONE_PATTERN.search(name):
                fail(f"vault_template/ contém arquivo com padrão de telefone (dado real?): {name}")
            if not (name.endswith(".md") or name == ".gitkeep"):
                fail(f"vault_template/ só deve conter .md/.gitkeep — encontrado: {name}")

    print("[OK] vault_template/ validado (sem dados pessoais).")


def build_staging():
    """Recria o staging copiando apenas a allow-list."""
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR)
    os.makedirs(STAGING_DIR)

    # auth_state: sessão de WhatsApp de quem desenvolveu — nunca pode ser distribuída
    ignore = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.pyo", "*.sqlite3", "auth_state", "whatsapp_session"
    )

    for dirname in ALLOWED_DIRS:
        src = os.path.join(PROJECT_ROOT, dirname)
        if not os.path.isdir(src):
            fail(f"Pasta obrigatória ausente: {dirname}/")
        shutil.copytree(src, os.path.join(STAGING_DIR, dirname), ignore=ignore)

    if not os.path.isdir(os.path.join(STAGING_DIR, "whatsapp-bridge", "node_modules")):
        fail(
            "whatsapp-bridge/node_modules ausente. Rode:\n"
            "  cd whatsapp-bridge && npm install"
        )

    # Node portátil, para a ponte de WhatsApp rodar sem Node instalado na máquina
    node_exe = fetch_node()
    node_destino = os.path.join(STAGING_DIR, "node")
    os.makedirs(node_destino, exist_ok=True)
    shutil.copy2(node_exe, os.path.join(node_destino, "node.exe"))

    for filename in ALLOWED_FILES:
        src = os.path.join(PROJECT_ROOT, filename)
        if not os.path.isfile(src):
            fail(f"Arquivo obrigatório ausente: {filename}")
        shutil.copy2(src, os.path.join(STAGING_DIR, filename))

    # O ícone é referenciado pelo spec como caminho relativo ao staging.
    icon_src = os.path.join(BUILD_DIR, "assets", ICON_NAME)
    if not os.path.isfile(icon_src):
        fail(f"Ícone não encontrado: {icon_src}")
    shutil.copy2(icon_src, os.path.join(STAGING_DIR, ICON_NAME))

    print(f"[OK] Staging montado em {STAGING_DIR}")


def assert_staging_is_clean():
    """Trava final: nenhum dado real pode ter escapado para o staging."""
    for forbidden in FORBIDDEN_IN_STAGING:
        path = os.path.join(STAGING_DIR, forbidden)
        if os.path.exists(path):
            fail(f"Arquivo/pasta proibido presente no staging: {forbidden}")

    for root, _, files in os.walk(STAGING_DIR):
        for name in files:
            if name.endswith((".sqlite3", ".db", ".exe")):
                rel = os.path.relpath(os.path.join(root, name), STAGING_DIR)
                if rel in ALLOWED_EXECUTABLES:
                    continue
                fail(f"Arquivo não permitido no staging: {rel}")

    # A sessão do WhatsApp de quem desenvolveu jamais pode ser distribuída:
    # quem instalasse o pacote entraria na conta de outra pessoa.
    for root, dirs, files in os.walk(STAGING_DIR):
        for nome in list(dirs) + list(files):
            if nome in ("auth_state", "whatsapp_session") or nome.startswith("creds.json"):
                rel = os.path.relpath(os.path.join(root, nome), STAGING_DIR)
                fail(f"Sessão de WhatsApp encontrada no staging: {rel}")

    print("[OK] Staging validado — nenhum dado real ou binário indevido.")


def run_pyinstaller():
    source_spec = os.path.join(BUILD_DIR, "pyinstaller.spec")
    if not os.path.isfile(source_spec):
        fail("build/pyinstaller.spec não encontrado.")

    # O PyInstaller resolve os caminhos relativos do spec a partir da pasta do
    # próprio spec — por isso ele é copiado para dentro do staging.
    spec_path = os.path.join(STAGING_DIR, "pyinstaller.spec")
    shutil.copy2(source_spec, spec_path)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        spec_path,
        "--noconfirm",
        "--distpath", DIST_DIR,
        "--workpath", WORK_DIR,
    ]
    print(f"\n[PyInstaller] Empacotando a partir do staging...\n")
    result = subprocess.run(cmd, cwd=STAGING_DIR)
    if result.returncode != 0:
        fail("PyInstaller falhou. Veja a saída acima.")

    warn_file = os.path.join(WORK_DIR, "AgentQuestHQ", "warn-AgentQuestHQ.txt")
    if os.path.isfile(warn_file):
        print(f"\n[ATENÇÃO] Revise os avisos de import em:\n  {warn_file}")

    print(f"[OK] Build onedir gerado em {os.path.join(DIST_DIR, 'AgentQuestHQ')}")


def run_inno_setup():
    iss_path = os.path.join(BUILD_DIR, "installer.iss")
    if not os.path.isfile(iss_path):
        fail("build/installer.iss não encontrado.")

    iscc = shutil.which("ISCC") or shutil.which("ISCC.exe")
    if not iscc:
        # O Inno Setup pode ser instalado por máquina (Program Files) ou apenas
        # para o usuário atual (%LOCALAPPDATA%, caso do instalador via winget).
        candidates = []
        for env_var in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
            root = os.environ.get(env_var)
            if not root:
                continue
            prefix = os.path.join(root, "Programs") if env_var == "LOCALAPPDATA" else root
            for version in ("Inno Setup 6", "Inno Setup 7"):
                candidates.append(os.path.join(prefix, version, "ISCC.exe"))

        for candidate in candidates:
            if os.path.isfile(candidate):
                iscc = candidate
                break

    if not iscc:
        print("\n[AVISO] Inno Setup (ISCC.exe) não encontrado no PATH.")
        print("        Instale em https://jrsoftware.org/isdl.php e rode novamente,")
        print("        ou use --skip-installer para gerar apenas a pasta onedir.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n[Inno Setup] Gerando instalador...\n")
    result = subprocess.run([iscc, iss_path], cwd=BUILD_DIR)
    if result.returncode != 0:
        fail("Inno Setup falhou. Veja a saída acima.")

    installer = os.path.join(OUTPUT_DIR, f"AgentQuestHQ-Setup-{APP_VERSION}.exe")
    if os.path.isfile(installer):
        size_mb = os.path.getsize(installer) / (1024 * 1024)
        print(f"\n[OK] Instalador gerado: {installer} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Build de release do AgentQuest HQ")
    parser.add_argument("--skip-installer", action="store_true", help="Gera só a pasta onedir, sem rodar o Inno Setup")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  AGENTQUEST HQ — BUILD DE RELEASE v{APP_VERSION}")
    print("=" * 60)

    validate_vault_template()
    build_staging()
    assert_staging_is_clean()
    run_pyinstaller()

    if not args.skip_installer:
        run_inno_setup()

    print("\n[CONCLUÍDO] Build finalizado.")


if __name__ == "__main__":
    main()
