"""
Resolução central de caminhos da aplicação.

Distingue dois tipos de caminho, que só divergem no executável empacotado:

- base_path()     → dados mutáveis do usuário (vault/, settings.json, banco,
                    inbox/, outputs/). No .exe, ficam ao lado do executável,
                    para sobreviverem a atualizações e serem acessíveis.
- resource_path() → recursos somente-leitura embutidos no pacote (frontend/,
                    vault_template/, docker-compose.evolution.yml). No .exe
                    do PyInstaller onedir, ficam em _internal/ (sys._MEIPASS).

Rodando via `python start_system.py` os dois apontam para a raiz do projeto.
"""

import os
import sys


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return _project_root()


def get_resource_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return _project_root()


def base_path(*parts) -> str:
    return os.path.join(get_base_dir(), *parts)


def resource_path(*parts) -> str:
    return os.path.join(get_resource_dir(), *parts)
