// ── SQUAD DE 8 AGENTES ──────────────────────────────────────────
const SQUAD_AGENTS = [
  { id: 'hermes',      name: 'Hermes',         role: 'Orquestrador Geral',   icon: '👑', color: '#a855f7', status: 'ativo' },
  { id: 'atendente',   name: 'Atendente',      role: 'Recepção & Leitura',   icon: '📖', color: '#3b82f6', status: 'processando' },
  { id: 'admin',       name: 'Administrativo', role: 'Triagem & Roteamento', icon: '🔍', color: '#f97316', status: 'ativo' },
  { id: 'financeiro',  name: 'Financeiro',     role: 'Cobranças & Notas',    icon: '💰', color: '#eab308', status: 'ocioso' },
  { id: 'comercial',   name: 'Comercial',      role: 'Leads & Follow-ups',   icon: '📈', color: '#ef4444', status: 'processando' },
  { id: 'juridico',    name: 'Jurídico LGPD',  role: 'Contratos & LGPD',     icon: '⚖️', color: '#6b7280', status: 'ativo' },
  { id: 'planejador',  name: 'Planejador',     role: 'Estratégia & Prazos',  icon: '🗺️', color: '#14b8a6', status: 'ocioso' },
  { id: 'revisor',     name: 'Revisor',        role: 'Controle de Qualidade',icon: '✅', color: '#22c55e', status: 'ativo' }
];

// ── MISSÕES INICIAIS COM RESPOSTAS PRONTAS ──────────────────────
const INITIAL_MISSIONS = [
  {
    source: 'whatsapp',
    title: 'Responder proposta do cliente João Silva — confirmação de prazo',
    agent: 'Comercial',
    deadline: '28/08',
    urgent: true,
    channel: '💬 Disparo automático via WhatsApp',
    response: 'Olá, João! Tudo bem?\n\nAgradecemos pelo feedback em nossa proposta! Confirmamos que o prazo de entrega será de 15 dias úteis a contar da data de assinatura do contrato.\n\nCaso deseje, podemos formalizar o pedido agora mesmo.\n\nFico à total disposição!'
  },
  {
    source: 'telegram',
    title: 'Follow-up de alinhamento com equipe de TI — migração de servidores',
    agent: 'Planejador',
    deadline: '29/08',
    urgent: false,
    channel: '✈️ Disparo automático via Telegram',
    response: 'Olá, time de TI! Conforme combinado na reunião de ontem:\n\n1. Documentação da API atualizada até sexta-feira\n2. Teste no ambiente de homologação na próxima terça\n3. Janela de migração confirmada para o próximo sábado\n\nPor favor, confirmem o cronograma.'
  },
  {
    source: 'email',
    title: 'Enviar relatório financeiro compilado de julho para Diretoria',
    agent: 'Financeiro',
    deadline: '28/08',
    urgent: true,
    channel: '📧 Envio automático por E-mail (com anexo .xlsx)',
    response: 'Prezados Diretores,\n\nSegue o relatório executivo financeiro referente ao mês de Julho:\n\n• Faturamento Bruto: R$ 92.450,00\n• Despesas Operacionais: R$ 58.300,00\n• Margem Líquida: 36,9% (↑ 4.2% vs mês anterior)\n\nO arquivo analítico segue em anexo para apreciação.'
  },
  {
    source: 'whatsapp',
    title: 'Revisão da Cláusula 4.2 no contrato de prestação de serviços',
    agent: 'Jurídico LGPD',
    deadline: '30/08',
    urgent: false,
    channel: '📋 Ação interna: Minuta atualizada salva em outputs/',
    response: 'Identificamos necessidade de adequação da Cláusula 4.2 ao Artigo 46 da LGPD.\n\nTexto revisado inserido na minuta:\n"O CONTRATADO obriga-se a manter medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados."\n\nDocumento pronto para envio à assessoria.'
  },
  {
    source: 'email',
    title: 'Confirmação de horário e pauta da Reunião Semanal de Alinhamento',
    agent: 'Atendente',
    deadline: '28/08',
    urgent: false,
    channel: '📧 Disparo de convite Google Calendar & E-mail',
    response: 'Bom dia a todos!\n\nConfirmamos a nossa Reunião Semanal de Alinhamento para Quinta-feira, às 10:00h.\n\n• Sala: Reuniões 02\n• Link do Meet: meet.google.com/xyz-qwer-tyu\n• Pauta: Revisão de entregas e metas do próximo ciclo.'
  }
];

const EVENT_POOL = [
  {
    source: 'whatsapp',
    title: 'Cliente Camila solicitou 2ª via da fatura de serviços #1092',
    agent: 'Financeiro',
    deadline: 'Hoje',
    urgent: true,
    channel: '💬 Envio de PDF e chave Pix via WhatsApp',
    response: 'Olá, Camila! Tudo bem?\n\nSegue a 2ª via da sua fatura #1092 com vencimento atualizado para hoje, sem encargos adicionais.\n\nChave Pix Copia e Cola: 00020126580014br.gov.bcb.pix...\n\nQualquer dúvida, estamos à disposição!'
  },
  {
    source: 'telegram',
    title: 'Fornecedor CloudHost propõe desconto de 15% para plano anual',
    agent: 'Comercial',
    deadline: '30/08',
    urgent: false,
    channel: '✈️ Resposta via Telegram com contraproposta',
    response: 'Olá, equipe CloudHost! Analisamos a proposta de renovação anual com 15% de desconto.\n\nGostaríamos de aceitar caso seja mantido o suporte 24/7 sem taxa adicional de adesão.\n\nPodem formalizar a proposta com esses termos?'
  }
];

const AGENT_ACTIVITY_LOGS = [
  { color: '#a855f7', agent: 'Hermes',        text: 'Orquestrando pipeline: 1 nova mensagem recebida do <strong>WhatsApp</strong>' },
  { color: '#3b82f6', agent: 'Atendente',     text: 'Lendo e extraindo intenção do cliente <strong>João Silva</strong>' },
  { color: '#f97316', agent: 'Administrativo',text: 'Pendência classificada para o setor <strong>Comercial</strong>' },
  { color: '#ef4444', agent: 'Comercial',     text: 'Rascunho de resposta de vendas gerado com base no histórico' },
  { color: '#22c55e', agent: 'Revisor',       text: 'Fase Reflexiva concluída: texto validado e liberado para aprovação' },
  { color: '#eab308', agent: 'Financeiro',    text: 'Conciliando extrato de recebimentos com faturas pendentes' },
  { color: '#14b8a6', agent: 'Planejador',    text: 'Ajustando cronograma de entregas no quadro estratégico' },
  { color: '#6b7280', agent: 'Jurídico LGPD', text: 'Varredura de dados sensíveis em documento: 100% em conformidade' }
];

let countApproved = 0;
let countRejected = 0;
let nextMissionId = 0;
let logCursor = 0;

function initApp() {
  renderSquadAgents();
  renderBottomDock();
  
  INITIAL_MISSIONS.forEach((m, idx) => {
    setTimeout(() => addMissionCard(m), idx * 200);
  });

  startFeedLoop();
  startAgentStatusCycle();
  startClockTick();
}

function renderSquadAgents() {
  const container = document.getElementById('agents-container');
  container.innerHTML = SQUAD_AGENTS.map(agent => 
    '<div class="agent-item" id="agent-row-' + agent.id + '">' +
      '<div class="agent-icon-box" style="background: ' + agent.color + '20; border: 1px solid ' + agent.color + '40;">' +
        agent.icon +
      '</div>' +
      '<div class="agent-meta">' +
        '<div class="agent-meta-name">' + agent.name + '</div>' +
        '<div class="agent-meta-role">' + agent.role + '</div>' +
      '</div>' +
      '<span class="status-pill ' + agent.status + '" id="badge-status-' + agent.id + '">' +
        agent.status +
      '</span>' +
    '</div>'
  ).join('');
}

function renderBottomDock() {
  const dock = document.getElementById('squad-dock');
  dock.innerHTML = SQUAD_AGENTS.map(agent => 
    '<div class="squad-avatar-dock" title="' + agent.name + ' (' + agent.role + ')" style="border-color: ' + agent.color + '33;">' +
      agent.icon +
      '<div class="squad-dot-badge" style="background: ' + (agent.status === 'ativo' ? '#22c55e' : agent.status === 'processando' ? '#f59e0b' : '#3b82f6') + ';"></div>' +
    '</div>'
  ).join('');
}

function updateAgentState(agentId, newStatus) {
  const badge = document.getElementById('badge-status-' + agentId);
  if (badge) {
    badge.className = 'status-pill ' + newStatus;
    badge.textContent = newStatus;
  }
}

function startAgentStatusCycle() {
  const schedule = [
    [2500, 'atendente', 'ativo'],
    [4500, 'comercial', 'ativo'],
    [7000, 'financeiro', 'processando'],
    [9500, 'planejador', 'processando'],
    [13000, 'financeiro', 'ativo'],
    [16000, 'planejador', 'ativo'],
    [19000, 'atendente', 'processando']
  ];
  schedule.forEach(([delay, id, status]) => {
    setTimeout(() => updateAgentState(id, status), delay);
  });
}

function addMissionCard(data) {
  const list = document.getElementById('missions-list');
  const currentCards = list.querySelectorAll('.card-mission');
  
  if (currentCards.length >= 6) {
    showToast('⚠️ Limite de 6 missões simultâneas atingido. Aprove ou rejeite itens.', 'info');
    return;
  }

  const id = ++nextMissionId;
  const card = document.createElement('article');
  card.className = 'card-mission';
  card.id = 'mission-card-' + id;

  const sourceLabel = data.source === 'whatsapp' ? '💬 WhatsApp' : data.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';

  card.innerHTML = 
    '<div class="mission-header-bar ' + data.source + '">' +
      '<span>' + sourceLabel + '</span>' +
      (data.urgent ? '<span class="tag-urgente">URGENTE</span>' : '') +
    '</div>' +
    '<div class="mission-content-box">' +
      '<div class="mission-description">' + data.title + '</div>' +
      '<div class="mission-info-tags">' +
        '<span class="info-tag">🤖 Agente: <strong>' + data.agent + '</strong></span>' +
        '<span class="info-tag">📅 Prazo: ' + data.deadline + '</span>' +
      '</div>' +
      '<button class="draft-toggle-btn" onclick="toggleDraftAccordion(this)" title="Expandir resposta preparada pelo agente">' +
        '<span>✍️ Ver Ação & Resposta Preparada</span>' +
        '<span class="draft-arrow">▼</span>' +
      '</button>' +
      '<div class="draft-collapse">' +
        '<div class="draft-card-inner">' +
          '<div class="draft-header-label"><span>⚡</span> Resposta pronta para execução pós-aprovação:</div>' +
          '<div class="draft-body-text" id="draft-text-' + id + '">' + data.response + '</div>' +
          '<div class="draft-dispatch-channel"><span>🚀</span> ' + data.channel + '</div>' +
          '<button class="draft-edit-action" onclick="openEditDraftModal(' + id + ')">✏️ Editar texto da resposta antes de aprovar</button>' +
        '</div>' +
      '</div>' +
      '<div class="mission-buttons-row">' +
        '<button class="btn-action btn-approve-exec" onclick="handleApproveMission(' + id + ')" title="Aprova e executa a resposta imediatamente"><span>✅</span> Aprovar & Executar</button>' +
        '<button class="btn-action btn-reject-task" onclick="handleRejectMission(' + id + ')" title="Descarta a ação sugerida"><span>❌</span> Rejeitar</button>' +
      '</div>' +
    '</div>';

  list.appendChild(card);
  refreshCounters();
}

function toggleDraftAccordion(btn) {
  btn.classList.toggle('open');
  const collapse = btn.nextElementSibling;
  collapse.classList.toggle('open');
}

function openEditDraftModal(id) {
  const textEl = document.getElementById('draft-text-' + id);
  if (!textEl) return;
  const currentText = textEl.innerText;
  const newText = prompt('Editar a resposta rascunhada pelo agente antes do envio:', currentText);
  if (newText !== null && newText.trim() !== '') {
    textEl.innerText = newText;
    showToast('✍️ Resposta atualizada com sucesso!', 'info');
    appendFeedItem({
      color: '#a855f7',
      agent: 'Hermes',
      text: 'Humano editou o rascunho da missão <strong>#' + id + '</strong>'
    });
  }
}

function handleApproveMission(id) {
  const card = document.getElementById('mission-card-' + id);
  if (!card) return;

  card.classList.add('approving');
  countApproved++;
  document.getElementById('metric-approved').textContent = countApproved;

  showToast('🚀 Aprovado! Resposta despachada com sucesso.', 'success');
  appendFeedItem({
    color: '#22c55e',
    agent: 'Você (Humano)',
    text: 'Aprovou e executou ação da missão <strong>#' + id + '</strong> — Resposta enviada!'
  });

  setTimeout(() => {
    card.remove();
    refreshCounters();
  }, 480);
}

function handleRejectMission(id) {
  const card = document.getElementById('mission-card-' + id);
  if (!card) return;

  card.classList.add('rejecting');
  countRejected++;
  document.getElementById('metric-rejected').textContent = countRejected;

  showToast('❌ Missão rejeitada e arquivada.', 'error');
  appendFeedItem({
    color: '#ef4444',
    agent: 'Você (Humano)',
    text: 'Rejeitou a sugestão da missão <strong>#' + id + '</strong> — Nenhuma ação externa realizada.'
  });

  setTimeout(() => {
    card.remove();
    refreshCounters();
  }, 480);
}

function refreshCounters() {
  const total = document.querySelectorAll('.card-mission').length;
  document.getElementById('metric-pending').textContent = total;
  
  const badge = document.getElementById('badge-counter');
  const badgeText = document.getElementById('badge-text');
  
  if (total === 0) {
    badgeText.textContent = 'Tudo revisado! Nenhuma pendência';
    badge.style.background = 'rgba(34, 197, 94, 0.2)';
    badge.style.border = '1px solid rgba(34, 197, 94, 0.4)';
    document.getElementById('empty-state').style.display = 'block';
  } else {
    badgeText.textContent = total + (total === 1 ? ' missão aguarda aprovação' : ' missões com respostas prontas');
    badge.style.background = 'linear-gradient(135deg, #f59e0b, #ef4444)';
    badge.style.border = 'none';
    document.getElementById('empty-state').style.display = 'none';
  }
}

function addRandomMission() {
  const poolItem = EVENT_POOL[Math.floor(Math.random() * EVENT_POOL.length)];
  addMissionCard(poolItem);
  appendFeedItem({
    color: '#a855f7',
    agent: 'Hermes',
    text: 'Novo arquivo recebido via <strong>' + poolItem.source + '</strong> — Triagem iniciada!'
  });
  showToast('📥 Novo evento detectado no inbox!', 'info');
}

function startFeedLoop() {
  appendFeedItem(AGENT_ACTIVITY_LOGS[logCursor % AGENT_ACTIVITY_LOGS.length]);
  logCursor++;
  
  setInterval(() => {
    appendFeedItem(AGENT_ACTIVITY_LOGS[logCursor % AGENT_ACTIVITY_LOGS.length]);
    logCursor++;
  }, 3800);
}

function appendFeedItem(item) {
  const feed = document.getElementById('feed-list');
  const timeStr = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  
  const el = document.createElement('div');
  el.className = 'feed-item';
  el.style.borderLeftColor = item.color;
  el.innerHTML = 
    '<div class="feed-dot" style="background: ' + item.color + ';"></div>' +
    '<div class="feed-content">' +
      '<strong style="color: ' + item.color + ';">' + item.agent + '</strong> — ' + item.text +
    '</div>' +
    '<div class="feed-time">' + timeStr + '</div>';
  
  feed.insertBefore(el, feed.firstChild);
  if (feed.children.length > 15) {
    feed.lastChild.remove();
  }
}

function showToast(msg, type) {
  type = type || 'info';
  const container = document.getElementById('toasts');
  const toast = document.createElement('div');
  toast.className = 'toast-msg ' + type;
  toast.innerHTML = '<span>' + (type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️') + '</span> ' + msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function startClockTick() {
  function update() {
    document.getElementById('clock-display').textContent = new Date().toLocaleTimeString('pt-BR');
  }
  update();
  setInterval(update, 1000);
}

// ══════════════════════════════════════════════════════════════════
// ── HERMES REPORT & BI INTELLIGENCE SYSTEM ───────────────────────
// ══════════════════════════════════════════════════════════════════

const REPORT_TEMPLATES = {
  financeiro: {
    title: '💰 Balanço Financeiro & Fluxo de Caixa Executivo',
    subtitle: 'Consolidado via Notas Fiscais, Extratos e Comprovantes em inbox/ (Mês Vigente)',
    kpis: [
      { label: 'Faturamento Total', value: 'R$ 94.200', trend: '↑ 14% vs mês anterior', color: 'green' },
      { label: 'Contas Pagas', value: 'R$ 58.150', trend: 'Margem Líquida: 38,2%', color: 'purple' },
      { label: 'Faturas a Vencer (7d)', value: 'R$ 12.800', trend: '3 faturas prioritárias', color: 'orange' },
      { label: 'Inadimplência', value: '1,8%', trend: '↓ Menor taxa do trimestre', color: 'blue' }
    ],
    chart1Title: '📊 Entradas x Despesas por Categoria (R$ Milhares)',
    chart1Bars: [
      { label: 'Serviços Prestados (Entrada)', value: 'R$ 78.500', pct: 85, color: '#22c55e' },
      { label: 'Contratos Recorrentes (Entrada)', value: 'R$ 15.700', pct: 40, color: '#10b981' },
      { label: 'Infraestrutura & Nuvem (Despesa)', value: 'R$ 18.200', pct: 35, color: '#ef4444' },
      { label: 'Folha & Prestadores (Despesa)', value: 'R$ 32.400', pct: 60, color: '#f87171' }
    ],
    chart2Bars: [
      { label: 'Comprovantes via WhatsApp', value: '38 arquivos', pct: 75, color: '#25d366' },
      { label: 'Notas Fiscais por E-mail', value: '24 arquivos', pct: 55, color: '#ea4335' },
      { label: 'Planilhas em Anexo', value: '11 arquivos', pct: 30, color: '#38bdf8' }
    ],
    synthesis: '<p>O <strong>Agente Financeiro</strong> e o <strong>Revisor</strong> analisaram 73 transações do período:</p>' +
      '<ul>' +
        '<li><strong>Saúde de Caixa Excelente:</strong> Margem líquida fechou em <strong>38,2%</strong>, superando a meta de 32%.</li>' +
        '<li><strong>Ação Recomendada:</strong> Existem 3 faturas somando R$ 12.800 que vencem nos próximos 5 dias. Os rascunhos de pagamento já foram gerados e aguardam sua aprovação no painel.</li>' +
        '<li><strong>Alerta de Economia:</strong> O fornecedor <em>CloudHost</em> ofereceu 15% de desconto para plano anual (economia estimada de R$ 3.200/ano).</li>' +
      '</ul>'
  },
  comercial: {
    title: '📈 Performance Comercial & Funil de Vendas',
    subtitle: 'Conversas de WhatsApp, Propostas e E-mails de Clientes (Últimos 30 dias)',
    kpis: [
      { label: 'Novos Leads Recebidos', value: '42 Leads', trend: '↑ 28% no WhatsApp', color: 'green' },
      { label: 'Propostas Enviadas', value: '19 Propostas', trend: 'R$ 138.000 em pipeline', color: 'purple' },
      { label: 'Taxa de Fechamento', value: '31,5%', trend: '6 contratos fechados', color: 'blue' },
      { label: 'Tempo Médio Resposta', value: '12 min', trend: 'Agente Atendente ativo', color: 'orange' }
    ],
    chart1Title: '📈 Funil de Conversão Comercial',
    chart1Bars: [
      { label: '1. Primeiro Contato / Triagem', value: '42 contatos', pct: 95, color: '#38bdf8' },
      { label: '2. Qualificação & Reunião', value: '28 reuniões', pct: 68, color: '#818cf8' },
      { label: '3. Proposta Comercial Enviada', value: '19 propostas', pct: 48, color: '#a855f7' },
      { label: '4. Negociação & Fechamento', value: '6 clientes', pct: 28, color: '#22c55e' }
    ],
    chart2Bars: [
      { label: 'Leads via WhatsApp', value: '29 contatos', pct: 85, color: '#25d366' },
      { label: 'Leads via E-mail', value: '10 contatos', pct: 35, color: '#ea4335' },
      { label: 'Leads via Telegram', value: '3 contatos', pct: 15, color: '#38bdf8' }
    ],
    synthesis: '<p>O <strong>Agente Comercial</strong> identificou um aumento forte na procura por novos projetos:</p>' +
      '<ul>' +
        '<li><strong>Destaque Positivo:</strong> O WhatsApp é o canal mais rápido, convertendo <strong>68%</strong> dos contatos qualificados em reuniões.</li>' +
        '<li><strong>Follow-up Urgente:</strong> O cliente <em>João Silva</em> e a cliente <em>Camila Santos</em> estão aguardando confirmação de prazo e proposta há mais de 24h. As respostas já estão preparadas no painel.</li>' +
        '<li><strong>Previsão de Receita:</strong> Se 50% das propostas abertas forem aprovadas, o faturamento do próximo mês somará +R$ 69.000.</li>' +
      '</ul>'
  },
  executivo: {
    title: '📊 Visão Executiva 360° — Operação & Negócios',
    subtitle: 'Relatório Consolidado de todos os 8 Agentes Especialistas',
    kpis: [
      { label: 'Pendências Resolvidas', value: '88%', trend: '↑ 12% de eficiência', color: 'green' },
      { label: 'Faturamento Estimado', value: 'R$ 94.200', trend: 'Meta mensal atingida', color: 'purple' },
      { label: 'Contratos em Vigência', value: '14 Ativos', trend: '100% conformes LGPD', color: 'blue' },
      { label: 'Ações Críticas Hoje', value: '3 Ações', trend: 'Aguardando aprovação', color: 'orange' }
    ],
    chart1Title: '📊 Distribuição de Tarefas por Departamento',
    chart1Bars: [
      { label: 'Comercial & Vendas', value: '42% do volume', pct: 85, color: '#ef4444' },
      { label: 'Financeiro & Cobranças', value: '28% do volume', pct: 60, color: '#eab308' },
      { label: 'Atendimento & Triagem', value: '18% do volume', pct: 40, color: '#3b82f6' },
      { label: 'Jurídico & LGPD', value: '12% do volume', pct: 25, color: '#6b7280' }
    ],
    chart2Bars: [
      { label: 'Mensagens WhatsApp', value: '142 mensagens', pct: 90, color: '#25d366' },
      { label: 'E-mails Processados', value: '58 e-mails', pct: 45, color: '#ea4335' },
      { label: 'Documentos PDF / DOCX', value: '23 arquivos', pct: 25, color: '#818cf8' }
    ],
    synthesis: '<p><strong>Síntese do Hermes (Orquestrador Geral):</strong> A operação está fluindo com estabilidade e alto índice de automação com supervisão humana.</p>' +
      '<ul>' +
        '<li><strong>Nenhuma Ação Despachada sem Aval:</strong> 100% dos envios para clientes e parceiros passaram pela sua aprovação manual no painel.</li>' +
        '<li><strong>Jurídico & LGPD:</strong> Todas as minutas contratuais foram revisadas com cláusula de proteção de dados conforme Art. 46 da LGPD.</li>' +
        '<li><strong>Próximo Passo:</strong> Revisar as 3 missões urgentes na lista à direita para fechar os ciclos pendentes do dia.</li>' +
      '</ul>'
  },
  juridico: {
    title: '⚖️ Auditoria Jurídica, Contratos & Conformidade LGPD',
    subtitle: 'Análise de Minutas, Termos e Tratamento de Dados Pessoais',
    kpis: [
      { label: 'Contratos Analisados', value: '18 Minutas', trend: '100% verificadas', color: 'blue' },
      { label: 'Cláusulas Adequadas', value: '94,4%', trend: 'Adequação LGPD Art. 46', color: 'green' },
      { label: 'Termos a Vencer (30d)', value: '2 Termos', trend: 'Aviso prévio gerado', color: 'orange' },
      { label: 'Vazamentos / Riscos', value: 'Zero', trend: 'Varredura local segura', color: 'purple' }
    ],
    chart1Title: '⚖️ Status das Minutas Contratuais',
    chart1Bars: [
      { label: 'Contratos Aprovados e Assinados', value: '12 contratos', pct: 80, color: '#22c55e' },
      { label: 'Minutas em Revisão de Cláusulas', value: '4 minutas', pct: 35, color: '#f59e0b' },
      { label: 'Contratos em Fase de Negociação', value: '2 minutas', pct: 20, color: '#38bdf8' }
    ],
    chart2Bars: [
      { label: 'Contratos de Prestação de Serviços', value: '11 arquivos', pct: 75, color: '#818cf8' },
      { label: 'Termos de Consentimento LGPD', value: '5 arquivos', pct: 40, color: '#c084fc' },
      { label: 'Acordos de Confidencialidade (NDA)', value: '2 arquivos', pct: 20, color: '#3b82f6' }
    ],
    synthesis: '<p>O <strong>Agente Jurídico LGPD</strong> concluiu a varredura preventiva dos documentos:</p>' +
      '<ul>' +
        '<li><strong>Cláusula 4.2 Ajustada:</strong> Foi identificada uma redação ambígua de responsabilidade em contrato de serviços. O texto já foi corrigido para proteger sua empresa contra responsabilidades indevidas.</li>' +
        '<li><strong>Privacidade em Dia:</strong> Nenhum dado sensível de clientes foi exposto em pastas públicas.</li>' +
      '</ul>'
  },
  cliente: {
    title: '👤 Dossiê 360° — Prontuário do Cliente João Silva',
    subtitle: 'Histórico Completo de Conversas, Propostas e Pagamentos (CRM Local)',
    kpis: [
      { label: 'Status da Conta', value: 'Ativo / Quente', trend: 'Negociação em andamento', color: 'green' },
      { label: 'LTV / Valor Histórico', value: 'R$ 34.500', trend: '3 projetos entregues', color: 'purple' },
      { label: 'Pontualidade de Pagamento', value: '100%', trend: 'Zero inadimplência', color: 'blue' },
      { label: 'Canal Principal', value: 'WhatsApp', trend: 'Tempo resp: 8 min', color: 'orange' }
    ],
    chart1Title: '📊 Histórico de Contratações por Trimestre',
    chart1Bars: [
      { label: 'Q1 2026 — Projeto Fase 1', value: 'R$ 12.000 (Concluído)', pct: 60, color: '#22c55e' },
      { label: 'Q2 2026 — Módulo de Integração', value: 'R$ 22.500 (Concluído)', pct: 90, color: '#10b981' },
      { label: 'Q3 2026 — Nova Proposta Atual', value: 'R$ 18.000 (Aguardando)', pct: 75, color: '#a855f7' }
    ],
    chart2Bars: [
      { label: 'Mensagens no WhatsApp', value: '48 mensagens', pct: 85, color: '#25d366' },
      { label: 'E-mails / Faturas', value: '14 e-mails', pct: 35, color: '#ea4335' }
    ],
    synthesis: '<p><strong>Raio-X de Relacionamento:</strong> O cliente <em>João Silva</em> é um dos parceiros mais antigos e pontuais da empresa.</p>' +
      '<ul>' +
        '<li><strong>Pendência Atual:</strong> Ele perguntou sobre o prazo de entrega da proposta #452. O rascunho de confirmação para 15 dias úteis já está pronto no painel à direita.</li>' +
        '<li><strong>Potencial de Expansão:</strong> Cliente com excelente perfil para pacote anual com desconto de fidelidade.</li>' +
      '</ul>'
  },
  operacional: {
    title: '⚡ Produtividade & Desempenho dos Agentes',
    subtitle: 'Métricas de Triagem, Leitura e Eficiência da IA Local',
    kpis: [
      { label: 'Arquivos Processados', value: '148 Itens', trend: 'Média de 1.4s por item', color: 'green' },
      { label: 'Taxa de Acerto na Triagem', value: '98,6%', trend: 'Roteamento Administrativo', color: 'purple' },
      { label: 'Economia de Tempo Humano', value: '18,5 Horas', trend: 'Nesta semana', color: 'blue' },
      { label: 'Fase Reflexiva (Revisor)', value: '100% OK', trend: 'Zero alucinações', color: 'orange' }
    ],
    chart1Title: '⚡ Volume de Trabalho por Agente',
    chart1Bars: [
      { label: 'Atendente (Recepção & Leitura)', value: '148 arquivos lidos', pct: 95, color: '#3b82f6' },
      { label: 'Administrativo (Triagem)', value: '148 rotas criadas', pct: 95, color: '#f97316' },
      { label: 'Comercial (Propostas & Leads)', value: '62 rascunhos', pct: 55, color: '#ef4444' },
      { label: 'Financeiro (Cálculos & Notas)', value: '44 conciliações', pct: 40, color: '#eab308' }
    ],
    chart2Bars: [
      { label: 'Tempo Médio Gemini API', value: '1.2 segundos', pct: 85, color: '#a855f7' },
      { label: 'Uso de CPU Local', value: 'Menos de 2%', pct: 15, color: '#22c55e' }
    ],
    synthesis: '<p><strong>Eficiência Operacional:</strong> Os agentes reduziram o tempo de resposta a clientes de horas para poucos minutos, sem abrir mão da segurança do botão de aprovação.</p>'
  }
};

function openReportModal() {
  document.getElementById('report-modal-overlay').classList.add('active');
  backToReportSelect();
}

function closeReportModal() {
  document.getElementById('report-modal-overlay').classList.remove('active');
}

function backToReportSelect() {
  document.getElementById('report-view-select').style.display = 'block';
  document.getElementById('report-view-loading').style.display = 'none';
  document.getElementById('report-view-content').style.display = 'none';
}

function generateReportPreset(presetKey) {
  const data = REPORT_TEMPLATES[presetKey] || REPORT_TEMPLATES.executivo;
  runReportGeneration(data);
}

function generateReportCustom() {
  const query = document.getElementById('custom-query-text').value.trim();
  if (!query) {
    showToast('Por favor, digite sua pergunta para o Hermes.', 'info');
    return;
  }
  
  const customData = {
    title: '💬 Relatório Personalizado: ' + (query.length > 35 ? query.substring(0, 35) + '...' : query),
    subtitle: 'Consulta livre respondida pelo Hermes & Squad • Base de Dados Local',
    kpis: [
      { label: 'Itens Cruzados', value: '48 Msg/Docs', trend: 'Varredura completa', color: 'purple' },
      { label: 'Nível de Confiança', value: '99,2%', trend: 'Validado pelo Revisor', color: 'green' },
      { label: 'Ações Sugeridas', value: '2 Ações', trend: 'Prontas para aprovação', color: 'orange' },
      { label: 'Tempo de Análise', value: '1.4s', trend: 'Motor Gemini Flash', color: 'blue' }
    ],
    chart1Title: '📊 Distribuição da Análise por Relevância',
    chart1Bars: [
      { label: 'Alta Relevância para sua pergunta', value: '24 evidências', pct: 85, color: '#a855f7' },
      { label: 'Média Relevância / Contexto', value: '16 evidências', pct: 55, color: '#38bdf8' },
      { label: 'Informações Complementares', value: '8 notas', pct: 30, color: '#64748b' }
    ],
    chart2Bars: [
      { label: 'Evidências do WhatsApp', value: '28 mensagens', pct: 75, color: '#25d366' },
      { label: 'Evidências de E-mail', value: '14 mensagens', pct: 45, color: '#ea4335' },
      { label: 'Evidências em Arquivos Locais', value: '6 documentos', pct: 25, color: '#eab308' }
    ],
    synthesis: '<p><strong>Resposta do Hermes para sua solicitação:</strong></p>' +
      '<p><em>"' + query + '"</em></p>' +
      '<ul>' +
        '<li>O time de agentes compilou os dados mais recentes das pastas e mensagens.</li>' +
        '<li>Identificamos que as principais pendências relacionadas a esse assunto estão sob a supervisão do <strong>Financeiro</strong> e <strong>Comercial</strong>.</li>' +
        '<li>Recomendamos manter o plano de ação sugerido nas missões ativas para garantir a resolução até o fim da semana.</li>' +
      '</ul>'
  };

  runReportGeneration(customData);
}

function runReportGeneration(reportData) {
  document.getElementById('report-view-select').style.display = 'none';
  document.getElementById('report-view-loading').style.display = 'block';
  document.getElementById('report-view-content').style.display = 'none';

  const steps = [
    'Hermes consultando os agentes especialistas...',
    'Compilando métricas financeiras e comerciais...',
    'Revisor validando coerência dos números...',
    'Formatando painel executivo estilo Power BI...'
  ];

  let sIdx = 0;
  const stepInterval = setInterval(() => {
    sIdx++;
    if (sIdx < steps.length) {
      document.getElementById('loading-agent-step').textContent = steps[sIdx];
    }
  }, 350);

  setTimeout(() => {
    clearInterval(stepInterval);
    renderReportView(reportData);
  }, 1400);
}

function renderReportView(data) {
  document.getElementById('report-view-loading').style.display = 'none';
  document.getElementById('report-view-content').style.display = 'block';

  document.getElementById('report-active-title').innerHTML = data.title;
  document.getElementById('report-active-subtitle').textContent = data.subtitle;

  // Render KPIs
  const kpiContainer = document.getElementById('bi-kpi-container');
  kpiContainer.innerHTML = data.kpis.map(kpi => 
    '<div class="bi-kpi-card ' + kpi.color + '">' +
      '<div class="bi-kpi-label">' + kpi.label + '</div>' +
      '<div class="bi-kpi-value">' + kpi.value + '</div>' +
      '<div class="bi-kpi-trend ' + (kpi.trend.indexOf('↑') !== -1 ? 'up' : 'neutral') + '">' + kpi.trend + '</div>' +
    '</div>'
  ).join('');

  // Render Chart 1
  document.getElementById('chart1-title').textContent = data.chart1Title;
  const c1Container = document.getElementById('chart1-bars');
  c1Container.innerHTML = data.chart1Bars.map(b => 
    '<div class="bar-item">' +
      '<div class="bar-label-val">' +
        '<span>' + b.label + '</span>' +
        '<strong>' + b.value + '</strong>' +
      '</div>' +
      '<div class="bar-track">' +
        '<div class="bar-fill" style="width: ' + b.pct + '%; background: ' + b.color + ';"></div>' +
      '</div>' +
    '</div>'
  ).join('');

  // Render Chart 2
  const c2Container = document.getElementById('chart2-bars');
  c2Container.innerHTML = data.chart2Bars.map(b => 
    '<div class="bar-item">' +
      '<div class="bar-label-val">' +
        '<span>' + b.label + '</span>' +
        '<strong>' + b.value + '</strong>' +
      '</div>' +
      '<div class="bar-track">' +
        '<div class="bar-fill" style="width: ' + b.pct + '%; background: ' + b.color + ';"></div>' +
      '</div>' +
    '</div>'
  ).join('');

  // Render Synthesis
  document.getElementById('hermes-synthesis-text').innerHTML = data.synthesis;
}

window.addEventListener('click', (e) => {
  const overlay = document.getElementById('report-modal-overlay');
  if (e.target === overlay) {
    closeReportModal();
  }
});

window.addEventListener('DOMContentLoaded', initApp);
