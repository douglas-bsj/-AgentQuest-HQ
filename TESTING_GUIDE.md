# 🧪 Guia Rápido de Instalação e Teste (Via Pen Drive) — AgentQuest HQ

> **Versão:** Beta 1.0 Local — Agosto 2026

---

## 💾 Passo a Passo para Instalar pelo Pen Drive

### 1. Copiar os arquivos
1. Conecte o Pen Drive no computador do testador.
2. Copie a pasta inteira `agentquest-hq` para a área de trabalho ou pasta de preferência (ex: `C:\agentquest-hq`).

---

### 2. Pré-requisitos & Instaladores Inclusos
Nesta pasta você já tem tudo que precisa sem precisar baixar nada da internet:
- **`python-installer.exe`**: Instalador do Python (caso o PC do testador não tenha).
- **`obsidian-installer.exe`**: Instalador do Obsidian *(Opcional)* — para visualizar a Base de Conhecimento e os Relatórios em formato de gráficos/Markdown.

> 💡 **Nota sobre o Obsidian:** O sistema funciona **100% perfeitamente mesmo sem o Obsidian instalado** (os agentes gravam e leem os arquivos `.md` da pasta `vault/` de forma nativa). O Obsidian serve apenas se o usuário quiser abrir a pasta `vault/` e ver as notas com interface visual rica.

---

### 3. Como Usar (Os 2 Atalhos)

Na pasta você tem 2 arquivos práticos:

1. **`INSTALAR_E_RODAR.bat`** (Primeiro uso):
   - Use apenas na **primeira vez** que for usar no computador.
   - Ele instala o Python (se não tiver), cria o ambiente e baixa tudo.

2. 👉 **`INICIAR_SISTEMA.bat`** (Uso diário):
   - Depois de já instalado, use sempre este arquivo!
   - Ele **inicia na hora em 1 segundo** e já abre a página no navegador (`http://127.0.0.1:8000`).

---

### 4. Como abrir o Obsidian (Opcional)
Se instalou o Obsidian no computador do testador:
1. Abra o aplicativo Obsidian.
2. Clique em **"Abrir pasta como cofre" (Open folder as vault)**.
3. Selecione a pasta **`vault`** que está dentro de `agentquest-hq`.
4. Todas as memórias dos agentes, regras aprendidas e relatórios de BI aparecerão organizados visualmente.

---

## 🔑 Configurar a IA no Primeiro Acesso
1. No painel aberto no navegador, clique no ícone **⚙️ (Configurações)** no topo.
2. Na aba **🔑 Contas & Provedores IA**, escolha o provedor e insira sua chave (ex: Gemini ou OpenRouter).
3. Clique em **"🔌 Testar Conexão"** e depois em **"💾 Salvar Configurações"**.

---

## 📋 Cenários Rápidos para Testar

- [ ] **Aprovar:** Clique em "✅ Aprovar & Executar" em um card.
- [ ] **Editar:** Clique em "✏️ Editar" para alterar a resposta antes de aprovar.
- [ ] **Rejeitar:** Clique em "❌ Rejeitar" e teste o botão "❌ Rejeitar Direto" ou escreva um motivo em "🎓 Ensinar & Rejeitar".
- [ ] **Recuperar:** Clique no número de "Rejeitadas ↩️" no topo e teste "🔄 Restaurar para a Fila".
- [ ] **Relatórios:** Clique em "📊 Relatório" no topo e explore as métricas de BI.

---

## 🛑 Como Fechar o Sistema
Para encerrar, basta fechar a janela preta do terminal que foi aberta pelo arquivo `.bat` e fechar a aba do navegador.

