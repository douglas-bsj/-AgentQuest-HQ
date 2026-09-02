"""
Inicialização de primeiro uso — AgentQuest HQ

Semeia o cofre Obsidian (vault/) a partir do vault_template/ versionado,
que não contém dados pessoais.

A cópia é feita arquivo a arquivo, apenas para o que ainda não existe: o
ObsidianBridge cria as pastas do cofre já no import do módulo, então checar
apenas a existência de vault/ deixaria o cofre sem os arquivos do template.
Copiar só o que falta também garante que atualizações futuras nunca
sobrescrevam notas do usuário.
"""

import os
import shutil

from backend.utils.paths import base_path, resource_path


def ensure_vault_initialized():
    vault_dir = base_path("vault")
    template_dir = resource_path("vault_template")

    if not os.path.isdir(template_dir):
        os.makedirs(vault_dir, exist_ok=True)
        print("[FIRST RUN] vault_template/ não encontrado — vault/ mantido como está.")
        return

    copied = 0
    for root, _, files in os.walk(template_dir):
        rel_dir = os.path.relpath(root, template_dir)
        target_dir = vault_dir if rel_dir == "." else os.path.join(vault_dir, rel_dir)
        os.makedirs(target_dir, exist_ok=True)

        for name in files:
            target_file = os.path.join(target_dir, name)
            if not os.path.exists(target_file):
                shutil.copy2(os.path.join(root, name), target_file)
                copied += 1

    if copied:
        print(f"[FIRST RUN] Cofre Obsidian semeado com {copied} arquivo(s) do template limpo.")
