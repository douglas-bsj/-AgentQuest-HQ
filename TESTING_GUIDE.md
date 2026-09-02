# 🧪 Guia de Instalação e Teste — AgentQuest HQ

> **Versão:** 1.0.0 — Instalador Windows

---

## 💾 Instalação (para quem vai usar)

1. Receba o arquivo **`AgentQuestHQ-Setup-1.0.0.exe`** (~98 MB).
2. Dê duplo clique e siga o assistente (Avançar → Instalar).
3. Marque, se quiser, as opções de **atalho na Área de Trabalho** e **iniciar junto com o Windows**.
4. Ao final, o painel abre sozinho no navegador.

**Não é preciso instalar Python nem nada além do instalador** — o runtime já vem embutido.

O programa é instalado em `%LOCALAPPDATA%\Programs\AgentQuest HQ` (não exige senha de
administrador) e aparece normalmente em **Configurações → Aplicativos instalados** do Windows.

---

## 🔑 Primeiro Acesso: Configurar a IA

Na primeira execução o painel mostra o assistente **"Configure sua Chave de IA"**:

1. Gere uma chave gratuita em [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
2. Cole no campo e clique em **"Salvar e Começar"** — a chave é validada na hora.
3. Pronto: o painel libera e os 8 agentes passam a funcionar.

Quer trocar de provedor depois (OpenRouter, OpenAI ou IA local via Ollama)?
Vá em **⚙️ Configurações → Contas & Provedores IA**.

---

## 💬 Conectar o WhatsApp (requer Docker Desktop)

O WhatsApp usa a Evolution API, que roda em containers Docker.

1. Instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/) e deixe-o aberto.
   *(Ele não é instalado junto com o AgentQuest — é um pré-requisito à parte.)*
2. No painel, vá em **⚙️ Configurações → Canais de Mensageria**.
3. O card de status no topo mostra a situação da conexão:
   - 🔴 **Docker Desktop não encontrado** — instale pelo link exibido ali.
   - 🟡 **Docker Desktop parado** — abra o Docker Desktop e clique em Conectar.
   - 🟢 **Evolution API online** — clique em **"📡 Conectar WhatsApp"**.
4. O **QR Code aparece na própria tela**: escaneie com o celular
   (WhatsApp → Aparelhos conectados → Conectar um aparelho).
5. O status muda para **🟢 WhatsApp conectado** automaticamente.

---

## 📚 Obsidian (opcional)

O sistema funciona **100% sem o Obsidian** — os agentes leem e gravam os arquivos `.md`
da pasta `vault/` de forma nativa. O Obsidian serve apenas para visualizar essas notas
com interface rica:

1. Instale o [Obsidian](https://obsidian.md).
2. Clique em **"Abrir pasta como cofre"**.
3. Selecione a pasta `vault` dentro do diretório de instalação.

---

## 📋 Cenários Rápidos para Testar

- [ ] **Aprovar:** clique em "✅ Aprovar & Executar" em um card.
- [ ] **Editar:** clique em "✏️ Editar" para ajustar a resposta antes de aprovar.
- [ ] **Rejeitar:** teste "❌ Rejeitar Direto" e também "🎓 Ensinar & Rejeitar" com um motivo.
- [ ] **Recuperar:** clique no contador "Rejeitadas" e use "🔄 Restaurar para a Fila".
- [ ] **Relatórios:** abra "📊 Relatórios com Hermes" e explore as métricas de BI.
- [ ] **Oráculo:** abra "Oráculo & Memórias" e faça uma pergunta em linguagem natural.

---

## 🛑 Como Fechar

Feche a janela preta do terminal e a aba do navegador. Se marcou a opção de iniciar
com o Windows, o programa volta a subir sozinho no próximo login.

---

## 🗑️ Desinstalar

Use **Configurações → Aplicativos instalados → AgentQuest HQ → Desinstalar**.

O desinstalador pergunta se você quer **apagar também seus dados** (cofre Obsidian,
configurações, banco e arquivos processados). O padrão é **manter** — escolha "Não"
se pretende reinstalar depois sem perder nada.

---

## 🛠️ Para desenvolvedores: rodar a partir do código

```bash
pip install -r requirements.txt
python start_system.py
```

Para gerar um novo instalador (requer [Inno Setup 6](https://jrsoftware.org/isdl.php)):

```bash
python scripts/build_release.py
```

O pipeline monta um staging sanitizado (nunca empacota `settings.json`, `.env`,
o banco ou o `vault/` real), roda o PyInstaller e compila o instalador em
`build/output/`.
