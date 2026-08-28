"""
Obsidian Bridge — AgentQuest HQ
Ponte de integração bidirecional entre os Agentes de IA e o Cofre Obsidian (vault/).
- Leitura: Base de Conhecimento (preços, regras contratuais, diretrizes)
- Escrita: Prontuário de Clientes (CRM), Histórico de Ações Aprovadas e Relatórios BI
"""

import os
import re
import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DIR = os.path.join(BASE_DIR, "vault")
KNOWLEDGE_DIR = os.path.join(VAULT_DIR, "01_Base_Conhecimento")
CRM_DIR = os.path.join(VAULT_DIR, "02_Clientes_CRM")
REPORTS_DIR = os.path.join(VAULT_DIR, "03_Relatorios_BI")
HISTORY_DIR = os.path.join(VAULT_DIR, "04_Historico_Acoes")


class ObsidianBridge:
    def __init__(self):
        self._ensure_folders()

    def _ensure_folders(self):
        """Garante que todas as pastas do cofre existam."""
        for folder in [VAULT_DIR, KNOWLEDGE_DIR, CRM_DIR, REPORTS_DIR, HISTORY_DIR]:
            os.makedirs(folder, exist_ok=True)

    def get_knowledge_context(self) -> str:
        """
        Lê todos os arquivos Markdown de vault/01_Base_Conhecimento/
        e retorna uma string consolidada para injetar no prompt dos agentes.
        """
        self._ensure_folders()
        knowledge_texts = []

        if not os.path.exists(KNOWLEDGE_DIR):
            return ""

        for file in sorted(os.listdir(KNOWLEDGE_DIR)):
            if file.endswith(".md") and not file.startswith("."):
                file_path = os.path.join(KNOWLEDGE_DIR, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().strip()
                        if content:
                            title = os.path.splitext(file)[0].replace("_", " ")
                            knowledge_texts.append(f"### [Regra da Empresa: {title}]\n{content}")
                except Exception as e:
                    print(f"[OBSIDIAN] Erro ao ler nota {file}: {e}")

        if not knowledge_texts:
            return ""

        return "\n\n=== BASE DE CONHECIMENTO DA EMPRESA (OBSIDIAN) ===\n" + "\n\n".join(knowledge_texts) + "\n===================================================\n"

    def update_client_crm(self, client_name: str, channel: str, mission_title: str, response_text: str):
        """
        Cria ou atualiza a nota do cliente em vault/02_Clientes_CRM/{Nome_Cliente}.md
        Mantém tabela cronológica de interações e metadados.
        """
        self._ensure_folders()
        clean_name = re.sub(r'[\\/*?:"<>|]', "", client_name).strip()
        if not clean_name or clean_name.lower() in ["desconhecido", "remetente"]:
            clean_name = "Contato_Geral"

        filename = f"{clean_name.replace(' ', '_')}.md"
        file_path = os.path.join(CRM_DIR, filename)

        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        today_date = datetime.datetime.now().strftime("%d/%m/%Y")

        log_entry = (
            f"\n### 💬 Interação em {now_str} via {channel.capitalize()}\n"
            f"- **Assunto:** {mission_title}\n"
            f"- **Canal:** {channel}\n"
            f"- **Status:** ✅ Aprovado & Executado\n\n"
            f"**Resposta Enviada:**\n"
            f"> {response_text.replace(chr(10), chr(10) + '> ')}\n"
        )

        if not os.path.exists(file_path):
            # Cria novo prontuário do cliente
            initial_content = (
                f"# 👤 Prontuário do Cliente: {clean_name.replace('_', ' ')}\n\n"
                f"- **Data de Cadastro:** {today_date}\n"
                f"- **Canal Principal:** {channel.capitalize()}\n"
                f"- **Status:** Ativo\n"
                f"- **Links:** [[00_Dashboard/Visao_Geral|Painel Geral]]\n\n"
                f"---\n\n"
                f"## 📜 Histórico de Atendimentos & Propostas\n"
                f"{log_entry}"
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(initial_content)
            print(f"[OBSIDIAN CRM] Criado novo prontuário: {filename}")
        else:
            # Anexa nova interação ao prontuário existente
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"\n---\n{log_entry}")
            print(f"[OBSIDIAN CRM] Atualizado prontuário: {filename}")

    def log_approved_action(self, mission_id: int, agent_name: str, client_name: str, response_text: str, channel: str):
        """
        Registra a auditoria de ação aprovada em vault/04_Historico_Acoes/{YYYY-MM-DD}_Acoes_Aprovadas.md
        """
        self._ensure_folders()
        today_slug = datetime.datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.datetime.now().strftime("%H:%M:%S")

        filename = f"{today_slug}_Acoes_Aprovadas.md"
        file_path = os.path.join(HISTORY_DIR, filename)

        entry = (
            f"## [{now_time}] Missão #{mission_id} — Agente {agent_name}\n"
            f"- **Destinatário:** [[02_Clientes_CRM/{client_name.replace(' ', '_')}|{client_name}]]\n"
            f"- **Canal:** {channel}\n"
            f"- **Decisão Humana:** ✅ Aprovado & Executado\n\n"
            f"```text\n{response_text}\n```\n\n---\n\n"
        )

        if not os.path.exists(file_path):
            header = f"# 📝 Registro de Ações Aprovadas — {datetime.datetime.now().strftime('%d/%m/%Y')}\n\n---\n\n"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(header + entry)
        else:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(entry)

        print(f"[OBSIDIAN HISTÓRICO] Registrada aprovação da missão #{mission_id} em {filename}")

    def save_bi_report(self, title: str, subtitle: str, kpis: list, synthesis: str) -> str:
        """
        Salva um relatório executivo do Hermes em vault/03_Relatorios_BI/
        """
        self._ensure_folders()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        # Remove emojis e caracteres especiais do nome do arquivo
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")[:35] or "Relatorio_BI"
        filename = f"{timestamp}_{clean_title}.md"
        file_path = os.path.join(REPORTS_DIR, filename)

        kpis_md = "\n".join([f"- **{k.get('label', 'Métrica')}:** `{k.get('value', '-')}` ({k.get('trend', '')})" for k in kpis])

        content = (
            f"# {title}\n"
            f"> *{subtitle}*\n"
            f"- **Data de Emissão:** {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n"
            f"- **Orquestrador:** 👑 Hermes Agent\n\n"
            f"---\n\n"
            f"## 📊 Indicadores Chave (KPIs)\n"
            f"{kpis_md}\n\n"
            f"---\n\n"
            f"## 👑 Síntese Executiva & Recomendações\n"
            f"{synthesis}\n"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[OBSIDIAN BI] Relatório salvo em: {filename}")
        return filename


# Instância global
obsidian_bridge = ObsidianBridge()
