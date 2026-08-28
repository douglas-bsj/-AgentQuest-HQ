# 📋 Plano de Implementação — AgentQuest HQ (com Obsidian & Hermes BI)

## 1. Visão Geral do Sistema
O **AgentQuest HQ** é um sistema local de orquestração multi-agente que conecta mensagens de entrada (WhatsApp, Telegram, E-mail, documentos), base de conhecimento local em **Obsidian**, geração reflexiva de respostas prontas e relatórios executivos sob demanda.

---

## 2. Squad Oficial de 8 Agentes

```
[1. Atendente] ➔ [2. Administrativo] ➔ [3. Especialista: Financeiro/Comercial/Jurídico/Planejador] ➔ [4. Revisor] ➔ [5. Hermes / Painel]
```

1. **👑 Hermes:** Orquestrador Geral e Gerador de Relatórios BI.
2. **📖 Atendente:** Recepção e leitura de mensagens brutas (WhatsApp, Telegram, E-mail, documentos).
3. **🔍 Administrativo:** Triagem e roteamento por setor técnico.
4. **💰 Financeiro:** Contas a pagar, faturas, extratos e cobranças.
5. **📈 Comercial:** Leads, propostas comerciais e follow-ups.
6. **⚖️ Jurídico LGPD:** Contratos, cláusulas de risco e compliance LGPD.
7. **🗺️ Planejador:** Estratégia, prazos e cronogramas.
8. **✅ Revisor:** Controle de qualidade reflexivo antes da exibição ao usuário.

---

## 3. Estrutura do Cofre Obsidian (`vault/`)

```
vault/
├── 00_Dashboard/          # Painéis de navegação e indicadores
├── 01_Base_Conhecimento/  # Regras que os agentes consultam antes de redigir
├── 02_Clientes_CRM/       # Prontuários dos clientes com histórico contínuo
├── 03_Relatorios_BI/      # Relatórios analíticos salvos pelo Hermes
└── 04_Historico_Acoes/    # Auditoria de ações e aprovações executadas
```

---

## 4. Fluxo de Dados e Execução

1. **Ingestão (`inbox/`):** Arquivo recebido é detectado pelo `watcher.py`.
2. **Leitura & Triagem:** `Atendente` e `Administrativo` extraem intenções e roteiam.
3. **Consulta ao Obsidian (`vault/`):** O agente da área lê as notas da base de conhecimento (preços, políticas, regras).
4. **Geração Reflexiva:** O agente gera a resposta/ação sugerida e o `Revisor` valida a qualidade.
5. **Painel Web:** A missão aparece no card com botão `✍️ Ver Ação & Resposta Preparada`.
6. **Aprovação Humana:** O usuário clica em `✅ Aprovar & Executar`.
7. **Disparo & Registro:** O backend executa o envio (WhatsApp/Telegram/E-mail) e atualiza o histórico no `vault/`.
8. **Relatórios Sob Demanda:** O usuário clica em `📊 Relatórios com Hermes` para gerar dashboards estilo Power BI e exportar em PDF/Excel.
