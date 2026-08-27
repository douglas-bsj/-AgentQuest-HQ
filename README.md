# 🤖 AgentQuest HQ

> Sistema MVP de agentes de IA para extração de pendências e follow-up — rodando 100% local no seu PC.

---

## 📋 O que é isso?

O **AgentQuest HQ** é um web app local onde agentes de IA analisam mensagens do **WhatsApp**, **Telegram** e **E-mails**, extraem automaticamente pendências e tarefas, e apresentam tudo num painel para **aprovação humana** antes de qualquer ação.

Nenhuma ação é executada sem sua aprovação. Os agentes só leem, resumem e sugerem.

---

## 🎨 Design

Interface com cenário isométrico pixel art de escritório moderno com painéis de UI limpos sobrepostos.

---

## 🏗️ Stack Técnica

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ + FastAPI |
| Banco de Dados | SQLite |
| IA | Google Gemini API (gratuito) |
| Frontend | HTML + CSS + JavaScript (vanilla) |
| Leitura de arquivos | PyPDF2, python-docx, openpyxl |
| Monitor de pasta | watchdog |
| Comunicação real-time | SSE (Server-Sent Events) |

---

## 🤖 Agentes

| Agente | Função |
|---|---|
| **Orquestrador** | Coordena o fluxo entre os demais agentes |
| **Leitor** | Lê e interpreta documentos e conversas |
| **Extrator** | Extrai pendências, tarefas e responsáveis |
| **Planejador** | Sugere próximos passos e prazos |
| **Revisor** | Valida e melhora os resultados antes de exibir |

---

## 📥 Fontes de Dados Suportadas (v1)

| Fonte | Formato |
|---|---|
| WhatsApp | Exportação de conversa .txt |
| Telegram | Exportação de conversa .json |
| E-mail | Arquivos .eml ou integração IMAP |
| Documentos | .pdf, .docx, .xlsx, .txt, .md |

**Fluxo:** inbox/ → processamento → processed/ + outputs/

---

## 🚀 Como Rodar

### 1. Pré-requisitos
- Python 3.11+
- Chave da API do Google Gemini (gratuita em https://aistudio.google.com)

### 2. Instalar dependências
`
pip install -r requirements.txt
`

### 3. Configurar variáveis de ambiente
`
cp .env.example .env
# Edite o .env e coloque sua GEMINI_API_KEY
`

### 4. Iniciar o sistema
`
python run.py
`

Acesse: http://localhost:8000

---

## 📁 Estrutura do Projeto

`
agentquest-hq/
├── backend/
│   ├── agents/          # Definição dos 5 agentes
│   │   ├── orchestrator.py
│   │   ├── reader.py
│   │   ├── extractor.py
│   │   ├── planner.py
│   │   └── reviewer.py
│   ├── tools/           # Ferramentas dos agentes
│   │   ├── file_reader.py
│   │   ├── whatsapp_parser.py
│   │   ├── telegram_parser.py
│   │   └── email_parser.py
│   ├── database.py      # SQLite — models e queries
│   ├── watcher.py       # Monitor da pasta inbox/
│   └── main.py          # FastAPI app + rotas
├── frontend/
│   ├── index.html       # Página principal
│   ├── style.css        # Estilos
│   └── app.js           # Lógica do frontend
├── docs/mockups/        # Imagens de design
├── inbox/               # Coloque arquivos aqui
├── processed/           # Arquivos já processados
├── outputs/             # Resultados dos agentes
├── .env.example
├── requirements.txt
├── run.py
└── README.md
`

---

## 🔒 Segurança

- Os agentes NÃO enviam mensagens ou alteram dados externos
- Toda sugestão passa pela aprovação manual do usuário
- A API key fica apenas no .env local (nunca sobe para o GitHub)
