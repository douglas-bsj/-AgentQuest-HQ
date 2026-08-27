# 📋 Planejamento do Projeto — AgentQuest HQ

## Visão Geral

Sistema local de agentes de IA para extração de pendências de conversas (WhatsApp, Telegram, E-mail) e documentos, com painel de aprovação humana antes de qualquer ação.

## Decisões de Design

### Interface
- **Estilo:** Isométrico pixel art — escritório moderno tipo startup tech
- **Layout:** Cenário de fundo + painéis de UI sobrepostos
- **Painel esquerdo:** Status dos agentes em tempo real
- **Painel direito:** Missões pendentes com Aprovar/Rejeitar
- **Sem gamificação:** Não há XP, moedas ou conquistas

### API de IA
- **Google Gemini** (gratuito)
- Obter em: https://aistudio.google.com → "Get API Key"

## Agentes

1. **Orquestrador** — coordena o pipeline completo
2. **Leitor** — lê e transcreve o conteúdo dos arquivos
3. **Extrator** — identifica pendências, responsáveis e prazos
4. **Planejador** — sugere próximos passos e ações
5. **Revisor** — valida e melhora os resultados (inspirado no padrão de debate do repo multiagentes-em-debate)

## Fontes de Dados (v1)

- WhatsApp: exportação .txt (Menu > Exportar conversa)
- Telegram: exportação .json (Configurações > Exportar)
- E-mail: arquivos .eml ou IMAP
- Documentos: .pdf, .docx, .xlsx, .txt, .md

## Fluxo de Processamento

`
[Arquivo em inbox/]
        ↓
[Agente Leitor] — lê e extrai texto
        ↓
[Agente Extrator] — identifica pendências
        ↓
[Agente Planejador] — sugere próximos passos
        ↓
[Agente Revisor] — valida e melhora
        ↓
[Painel de Aprovação] — humano aprova ou rejeita
        ↓
[Arquivo movido para processed/]
[Resultado salvo em outputs/]
`

## Segurança

- Agentes NÃO realizam ações externas no v1
- Tudo passa por aprovação humana
- API Key salva apenas em .env local

## Referências

- Repo de inspiração para padrão multi-agente: https://github.com/douglas-bsj/multiagentes-em-debate
- Google Gemini Docs: https://ai.google.dev/docs
- FastAPI Docs: https://fastapi.tiangolo.com
