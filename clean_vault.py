import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "vault")
DB_FILE = os.path.join(BASE_DIR, "backend", "database.sqlite3")
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

def clean_all():
    print("[LIMPEZA] Limpando cofre, banco SQLite e outputs...")

    # 1. Limpa o banco de dados
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print("[OK] Banco SQLite database.sqlite3 apagado.")
        except Exception as e:
            print(f"[AVISO] Erro ao remover banco: {e}")

    # 2. Limpa o cofre Obsidian mantendo as pastas
    folders = [
        "00_Dashboard",
        "01_Base_Conhecimento",
        "02_Clientes_CRM",
        "03_Relatorios_BI",
        "04_Historico_Acoes"
    ]
    for folder in folders:
        dir_path = os.path.join(VAULT_DIR, folder)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"[OK] Pasta vault/{folder}/ limpa.")
        else:
            os.makedirs(dir_path, exist_ok=True)

    # 3. Limpa arquivos gerados
    for work_dir in [INBOX_DIR, PROCESSED_DIR, OUTPUTS_DIR]:
        if os.path.exists(work_dir):
            for f in os.listdir(work_dir):
                fp = os.path.join(work_dir, f)
                if os.path.isfile(fp) and not f.startswith(".git"):
                    os.remove(fp)
            print(f"[OK] Pasta {os.path.basename(work_dir)}/ limpa.")

    # 4. Inicializa o banco de dados limpo
    from backend.database import init_db
    init_db(force_reset=True)
    print("[SUCESSO] Sistema completamente limpo e pronto para uso real!")

if __name__ == "__main__":
    clean_all()
