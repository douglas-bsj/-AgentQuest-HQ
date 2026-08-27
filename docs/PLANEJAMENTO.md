# 📋 Planejamento do Projeto — AgentQuest HQ
## Versão 2.0 — Time Completo de Agentes

## Visão Geral

Sistema local de agentes de IA para extração de pendências de conversas (WhatsApp, Telegram, E-mail) e documentos, com painel de aprovação humana antes de qualquer ação. Orquestrado pelo **Hermes Agent** (Nous Research).

---

## 🏗️ Arquitetura de Agentes

### Orquestrador
| Agente | Tecnologia | Função |
|---|---|---|
| **Hermes Agent** | Nous Research (open-source, MIT) | Orquestrador principal: recebe mensagens, distribui tarefas, mantém memória persistente, spawna sub-agentes em paralelo |

### Pipeline Base (todos os documentos passam por aqui)
| Agente | Função |
|---|---|
| **Leitor** | Lê e transcreve o conteúdo dos arquivos e conversas |
| **Administrativo** | Identifica pendências, responsáveis, prazos e classifica o tipo |
| **Planejador** | Sugere próximos passos e ações para cada pendência |
| **Revisor** | Valida e melhora os resultados (usa Fase Reflexiva do Hermes) |

### Agentes Especializados (roteados pelo Administrativo)
| Agente | Área | Responsabilidades |
|---|---|---|
| **Agente Financeiro** | Finanças | Analisa cobranças, pagamentos, notas fiscais, orçamentos, fluxo de caixa, inadimplência |
| **Agente Comercial** | Vendas / CRM | Analisa oportunidades, follow-ups de clientes, propostas enviadas, leads em aberto |
| **Agente Jurídico (LGPD)** | Jurídico / Compliance | Verifica conformidade com LGPD, analisa contratos, identifica riscos legais e prazos processuais |
| **Agente RH** | Recursos Humanos | Analisa férias, contratos, seleção, benefícios, ocorrências de funcionários |
| **Agente Atendente** | Secretaria / Triagem | Agenda reuniões, prioriza mensagens, filtra spam, redireciona para o agente correto quando necessário |

---

## 🔄 Fluxo de Processamento

`
[WhatsApp / Telegram / E-mail / Arquivo]
                ↓
        [Hermes Agent]  ← Orquestrador
                ↓
          [Leitor]       ← Lê e transcreve
                ↓
          [Administrativo]     ← Identifica tipo da pendência
                ↓
    ┌───────────┴────────────┐
    │ Classifica e roteia    │
    └───────────┬────────────┘
                ↓
  ┌─────────────────────────────┐
  │  Agente Especializado       │
  │  (Financeiro / Comercial /  │
  │   Jurídico / RH / Atendente)│
  └─────────────┬───────────────┘
                ↓
          [Planejador]   ← Sugere próximos passos
                ↓
          [Revisor]      ← Valida e melhora
                ↓
   [Painel de Aprovação] ← Humano aprova ou rejeita
                ↓
    [processed/] + [outputs/]
`

---

## 🤖 Detalhamento dos Agentes Especializados

### 💰 Agente Financeiro
- Detecta: cobranças vencidas, notas fiscais recebidas, pagamentos pendentes, orçamentos para aprovação
- Extrai: valor, vencimento, fornecedor/cliente, conta bancária mencionada
- Sugere: aprovar pagamento, enviar cobrança, contestar nota fiscal, agendar transferência

### 📈 Agente Comercial
- Detecta: novos leads, follow-ups atrasados, propostas sem resposta, oportunidades de upsell
- Extrai: nome do cliente, produto/serviço, valor da oportunidade, etapa no funil
- Sugere: retomar contato, enviar proposta revisada, marcar reunião de fechamento

### ⚖️ Agente Jurídico (LGPD)
- Detecta: contratos para assinar, cláusulas problemáticas, dados pessoais expostos, prazos judiciais
- Extrai: partes envolvidas, prazo, tipo de documento, risco identificado
- Sugere: revisar cláusula X, solicitar DPA, anonimizar dado, acionar advogado
- Alerta automático para violações de LGPD em documentos

### 👥 Agente RH
- Detecta: solicitações de férias, admissões, demissões, avaliações de desempenho, benefícios
- Extrai: nome do colaborador, tipo de solicitação, data, departamento
- Sugere: aprovar férias, enviar contrato, agendar entrevista, processar desligamento

### 📅 Agente Atendente (Secretaria)
- Detecta: agendamentos, confirmações de reunião, mensagens urgentes, spam
- Extrai: data/hora, participantes, pauta, local/link
- Sugere: confirmar reunião, bloquear agenda, enviar convite, redirecionar mensagem
- **Atua como triagem**: redireciona mensagens ambíguas para o agente mais adequado

---

## 🔧 Stack Técnica

| Camada | Tecnologia |
|---|---|
| Orquestrador | Hermes Agent (Nous Research, MIT) |
| Backend | Python 3.11+ + FastAPI |
| Banco de Dados | SQLite |
| IA | Google Gemini API (gratuito via aistudio.google.com) |
| Frontend | HTML + CSS + JavaScript (vanilla) |
| Leitura de arquivos | PyPDF2, python-docx, openpyxl |
| Monitor de pasta | watchdog (ou gateway nativo do Hermes) |
| Comunicação real-time | SSE (Server-Sent Events) |

---

## 📥 Fontes de Dados (v1)

| Fonte | Formato |
|---|---|
| WhatsApp | Exportação .txt (Menu > Exportar conversa) |
| Telegram | Exportação .json (Configurações > Exportar) |
| E-mail | Arquivos .eml ou integração IMAP |
| Documentos | .pdf, .docx, .xlsx, .txt, .md |

---

## 📁 Estrutura do Projeto

`
agentquest-hq/
├── backend/
│   ├── agents/
│   │   ├── hermes_bridge.py      # Interface com o Hermes Agent
│   │   ├── reader.py             # Agente Leitor
│   │   ├── administrative.py          # Agente Administrativo + roteador
│   │   ├── planner.py            # Agente Planejador
│   │   ├── reviewer.py           # Agente Revisor
│   │   ├── financial.py          # Agente Financeiro
│   │   ├── commercial.py         # Agente Comercial
│   │   ├── legal_lgpd.py         # Agente Jurídico (LGPD)
│   │   ├── hr.py                 # Agente RH
│   │   └── attendant.py          # Agente Atendente / Secretaria
│   ├── tools/
│   │   ├── file_reader.py
│   │   ├── whatsapp_parser.py
│   │   ├── telegram_parser.py
│   │   └── email_parser.py
│   ├── database.py
│   ├── watcher.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   ├── mockups/
│   └── PLANEJAMENTO.md
├── inbox/
├── processed/
├── outputs/
├── .env.example
├── requirements.txt
├── run.py
└── README.md
`

---

## 🔒 Segurança

- Os agentes NÃO realizam ações externas no v1
- Toda sugestão passa pela aprovação manual do usuário
- Dados pessoais processados localmente (sem envio para nuvem além da API de IA)
- Agente Jurídico monitora ativamente violações de LGPD

---

## 📚 Referências

- Hermes Agent: https://github.com/nousresearch/hermes-agent
- Google Gemini Docs: https://ai.google.dev/docs
- FastAPI: https://fastapi.tiangolo.com
- Inspiração multi-agente: https://github.com/douglas-bsj/multiagentes-em-debate


