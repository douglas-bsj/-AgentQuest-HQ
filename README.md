# 🤖 AgentQuest HQ

> Sistema MVP de agentes de IA para extração de pendências e follow-up — rodando 100% local no seu PC.

---

## 📋 O que é isso?

O **AgentQuest HQ** é um web app local onde um time de **10 agentes de IA especializados** analisam mensagens do **WhatsApp**, **Telegram** e **E-mails**, extraem automaticamente pendências por área (Financeiro, Comercial, Jurídico, RH, Atendimento) e apresentam tudo num painel para **aprovação humana** antes de qualquer ação.

---

## 🤖 Time de Agentes

### Orquestrador
| Agente | Tecnologia | Função |
|---|---|---|
| **Hermes Agent** | Nous Research (MIT) | Coordena todo o fluxo, memória persistente, spawna sub-agentes |

### Pipeline Base
| Agente | Função |
|---|---|
| **Leitor** | Lê e transcreve conversas e documentos |
| **Administrativo** | Identifica pendências e classifica por área |
| **Planejador** | Sugere próximos passos |
| **Revisor** | Valida e melhora os resultados |

### Agentes Especializados
| Agente | Área | O que detecta |
|---|---|---|
| **💰 Financeiro** | Finanças | Cobranças, pagamentos, notas fiscais, orçamentos |
| **📈 Comercial** | Vendas | Leads, follow-ups, propostas, oportunidades |
| **⚖️ Jurídico (LGPD)** | Jurídico | Contratos, riscos legais, violações de LGPD |
| **📅 Atendente** | Secretaria | Agendamentos, triagem, redirecionamento |

---

## 🔄 Fluxo

`
[WhatsApp / Telegram / E-mail / Arquivo]
              ↓
       [Hermes Agent]       ← Orquestrador
              ↓
   [Leitor] → [Administrativo]    ← Pipeline base
              ↓
  [Agente Especializado]    ← Financeiro / Comercial /
                               Jurídico / RH / Atendente
              ↓
   [Planejador] → [Revisor] ← Valida e melhora
              ↓
  [Painel de Aprovação]     ← Você aprova ou rejeita
`

---

## 🏗️ Stack Técnica

| Camada | Tecnologia |
|---|---|
| Orquestrador | Hermes Agent (Nous Research, MIT) |
| Backend | Python 3.11+ + FastAPI |
| Banco de Dados | SQLite |
| IA | Google Gemini API (gratuito) |
| Frontend | HTML + CSS + JavaScript |
| Real-time | SSE (Server-Sent Events) |

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

## 📥 Fontes Suportadas (v1)

| Fonte | Formato |
|---|---|
| WhatsApp | .txt (exportação de conversa) |
| Telegram | .json (exportação de conversa) |
| E-mail | .eml ou IMAP |
| Documentos | .pdf, .docx, .xlsx, .txt, .md |

---

## 🔒 Segurança

- Agentes NÃO realizam ações externas sem aprovação
- Dados processados localmente
- Agente Jurídico monitora violações de LGPD automaticamente
- API Key salva apenas no .env local (nunca vai ao GitHub)

---

## 📄 Documentação completa

Veja [docs/PLANEJAMENTO.md](docs/PLANEJAMENTO.md) para detalhes de cada agente e arquitetura completa.


