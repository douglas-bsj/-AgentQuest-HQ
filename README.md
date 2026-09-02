# 🤖 AgentQuest HQ

> **Sistema Local de Orquestração com Multi-Agentes de IA e Centro de Inteligência Executiva.**
> 100% Gratuito, Local e Seguro — Nenhuma ação externa é executada sem sua aprovação explícita.

---

## 🏛️ Visão Geral da Arquitetura

O **AgentQuest HQ** é uma central autônoma de operações executivas que processa mensagens e documentos (WhatsApp, Telegram, E-mails, PDFs e planilhas), classifica as demandas por área especializada, gera respostas prontas com ações sugeridas e compila relatórios analíticos estilo Power BI sob demanda.

```
                  ┌──────────────────┐
                  │ 📥 Pasta inbox/  │ (WhatsApp, Telegram, E-mail, Documentos)
                  └────────┬─────────┘
                           │ (Watcher local)
                           ▼
                  ┌──────────────────┐
                  │ 👑 Hermes Agent  │ (Orquestrador Geral)
                  └────────┬─────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 📖 Atendente │    │ 🔍 Admin     │    │ 📚 Obsidian  │
│ (Leitura)    │    │ (Triagem)    │    │ (Vault Base) │
└──────┬───────┘    └──────┬───────┘    └──────────────┘
       └───────────────────┼───────────────────┘
                           ▼
        ┌──────────────────────────────────────┐
        │       Agentes Especialistas          │
        │ 💰 Financeiro  •  📈 Comercial       │
        │ ⚖️ Jurídico    •  🗺️ Planejador       │
        └──────────────────┬───────────────────┘
                           ▼
                  ┌──────────────────┐
                  │   ✅ Revisor     │ (Fase Reflexiva de Qualidade)
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │  🖥️ Painel Web   │ ➔ ✍️ Resposta Pronta
                  │  (Aprovação)     │ ➔ 📊 Relatórios BI
                  └────────┬─────────┘
                           │ [Clique em Aprovar & Executar]
                           ▼
                  ┌──────────────────┐
                  │ 🚀 Execução Real │ (Disparo WhatsApp/Email + Atualiza Obsidian)
                  └──────────────────┘
```

---

## 🤖 Squad Oficial de Agentes (8 Agentes Especialistas)

| | Agente | Função | O que faz no sistema |
|:---:|---|---|---|
| 👑 | **Hermes** | Orquestrador Geral | Gerencia o pipeline, consulta a base de conhecimento e gera relatórios de BI sob demanda. |
| 📖 | **Atendente** | Recepção & Leitura | Lê e decodifica mensagens do WhatsApp, Telegram, E-mails e documentos recebidos. |
| 🔍 | **Administrativo** | Triagem & Roteamento | Classifica a demanda e direciona para a área técnica correta. |
| 💰 | **Financeiro** | Cobranças & Caixa | Analisa faturas, extratos bancários, pagamentos e elabora comprovantes/alertas. |
| 📈 | **Comercial** | Vendas & Propostas | Qualifica leads, rascunha propostas comerciais e programa follow-ups. |
| ⚖️ | **Jurídico LGPD** | Contratos & Compliance | Revisa minutas contratuais, cláusulas de risco e conformidade com a LGPD (Art. 46). |
| 🗺️ | **Planejador** | Estratégia & Prazos | Define cronogramas, próximos passos e marcos de entregas. |
| ✅ | **Revisor** | Controle de Qualidade | Valida coerência numérica, tom de voz e clareza antes de exibir no painel. |

---

## 🧠 Integração Nativa com Obsidian (`vault/`)

A pasta `vault/` funciona como um **Cofre Nativo do Obsidian** (*Segundo Cérebro* local):

```
vault/
├── 00_Dashboard/          ➔ Painel de navegação e indicadores
├── 01_Base_Conhecimento/  ➔ Regras de negócio que os agentes LEEM antes de responder
├── 02_Clientes_CRM/       ➔ Prontuário dos clientes atualizado automaticamente
├── 03_Relatorios_BI/      ➔ Relatórios e balanços exportados pelo Hermes
└── 04_Historico_Acoes/    ➔ Registro de auditoria de tudo o que foi aprovado
```

### 🔄 Fluxo Bidirecional:
1. **Você escreve no Obsidian:** Define tabelas de preços, regras de desconto e tom de voz em `01_Base_Conhecimento/`. Os agentes leem essas notas e seguem suas diretrizes.
2. **Você aprova no Painel Web:** O sistema dispara a mensagem e atualiza a ficha do cliente em `02_Clientes_CRM/` com histórico completo e links bidirecionais.

---

## 📊 Hermes BI & Relatórios Inteligentes

No topo do painel web, o botão **`📊 Relatórios com Hermes`** abre uma central analítica estilo Power BI com:
* **Relatórios Rápidos:** Balanço Financeiro, Funil Comercial, Visão Executiva 360°, Auditoria Jurídica e Dossiê de Clientes.
* **Consulta Livre:** Digite qualquer pergunta em linguagem natural para o Hermes cruzar os dados locais.
* **Exportação:** Download em PDF, Excel (.xlsx) e Markdown.

---

## 📁 Estrutura do Repositório

```
agentquest-hq/
├── vault/                  # Cofre nativo do Obsidian (Base de conhecimento e CRM)
├── inbox/                  # Pasta de entrada para novos arquivos (.txt, .pdf, .eml)
├── processed/              # Arquivos brutos já processados
├── outputs/                # Arquivos finais gerados para download
├── backend/                # Motor em Python (FastAPI, SQLite, Hermes & Agentes)
│   ├── agents/             # 8 Agentes especialistas em Python
│   ├── tools/              # Leitores de arquivos e ponte do Obsidian
│   ├── watcher.py          # Monitor de pasta inbox/
│   └── main.py             # API local
├── frontend/               # Painel Web em Pixel Art Isométrico
│   ├── assets/             # Cenário do escritório moderno e ícones
│   ├── index.html          # Interface do usuário e modal de BI
│   ├── style.css           # Estilos e gráficos
│   └── app.js              # Lógica dos agentes e relatórios
├── whatsapp-bridge/        # Ponte Node/Baileys — WhatsApp por QR Code, sem Docker
├── vault_template/         # Cofre limpo copiado para vault/ na primeira execução
├── build/                  # Spec do PyInstaller e script do Inno Setup
├── scripts/                # build_release.py — gera o instalador distribuível
├── docs/                   # Documentação detalhada e mockups aprovados
└── requirements.txt        # Dependências Python
```

---

## 🚀 Instalação

### Para usuários finais (instalador Windows)
Execute o **`AgentQuestHQ-Setup-1.0.0.exe`** e siga o assistente. O runtime Python vem
embutido — não é preciso instalar mais nada. Na primeira execução, um assistente pede a
chave gratuita da API Gemini e o painel abre sozinho no navegador.

Instala em `%LOCALAPPDATA%\Programs\AgentQuest HQ` (sem exigir administrador), cria atalhos
e aparece em "Aplicativos instalados" do Windows. Detalhes e passo a passo do WhatsApp em
[`TESTING_GUIDE.md`](TESTING_GUIDE.md).

> 💬 **WhatsApp:** o pareamento é feito dentro do próprio painel, em
> **⚙️ Configurações → Canais de Mensageria**, escaneando um QR Code — sem Docker
> e sem virtualização (o Node.js necessário vem embutido). Também é possível usar
> a **Cloud API oficial da Meta**, a **Evolution API** (essa sim requer Docker) ou
> o modo **link wa.me** para envio manual.

### Para desenvolvedores (a partir do código)
```bash
pip install -r requirements.txt
python start_system.py
```

Gerar um novo instalador (requer [Inno Setup 6](https://jrsoftware.org/isdl.php)):
```bash
python scripts/build_release.py
```
