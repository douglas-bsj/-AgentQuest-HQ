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

// ── MISSÕES COM RESPOSTAS PRONTAS DOS AGENTES ──────────────────
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
  },
  {
    source: 'email',
    title: 'Alerta de termo de consentimento LGPD expirando em 15 dias',
    agent: 'Jurídico LGPD',
    deadline: '02/09',
    urgent: false,
    channel: '📧 Notificação automática de renovação de consentimento',
    response: 'Prezado cliente,\n\nPara garantir a conformidade contínua com a Lei Geral de Proteção de Dados (LGPD), solicitamos a confirmação da renovação do seu termo de consentimento de tratamento de dados cadastrais.\n\nClique no link seguro para confirmar em 1 clique.'
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
  container.innerHTML = SQUAD_AGENTS.map(agent => `
    <div class="agent-item" id="agent-row-${agent.id}">
      <div class="agent-icon-box" style="background: ${agent.color}20; border: 1px solid ${agent.color}40;">
        ${agent.icon}
      </div>
      <div class="agent-meta">
        <div class="agent-meta-name">${agent.name}</div>
        <div class="agent-meta-role">${agent.role}</div>
      </div>
      <span class="status-pill ${agent.status}" id="badge-status-${agent.id}">
        ${agent.status}
      </span>
    </div>
  `).join('');
}

function renderBottomDock() {
  const dock = document.getElementById('squad-dock');
  dock.innerHTML = SQUAD_AGENTS.map(agent => `
    <div class="squad-avatar-dock" title="${agent.name} (${agent.role})" style="border-color: ${agent.color}33;">
      ${agent.icon}
      <div class="squad-dot-badge" style="background: ${agent.status === 'ativo' ? '#22c55e' : agent.status === 'processando' ? '#f59e0b' : '#3b82f6'};"></div>
    </div>
  `).join('');
}

function updateAgentState(agentId, newStatus) {
  const badge = document.getElementById(`badge-status-${agentId}`);
  if (badge) {
    badge.className = `status-pill ${newStatus}`;
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
  card.id = `mission-card-${id}`;

  const sourceLabel = data.source === 'whatsapp' ? '💬 WhatsApp' : data.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';

  card.innerHTML = `
    <div class="mission-header-bar ${data.source}">
      <span>${sourceLabel}</span>
      ${data.urgent ? '<span class="tag-urgente">URGENTE</span>' : ''}
    </div>
    <div class="mission-content-box">
      <div class="mission-description">${data.title}</div>
      
      <div class="mission-info-tags">
        <span class="info-tag">🤖 Agente: <strong>${data.agent}</strong></span>
        <span class="info-tag">📅 Prazo: ${data.deadline}</span>
      </div>

      <button class="draft-toggle-btn" onclick="toggleDraftAccordion(this)" title="Expandir resposta preparada pelo agente">
        <span>✍️ Ver Ação & Resposta Preparada</span>
        <span class="draft-arrow">▼</span>
      </button>

      <div class="draft-collapse">
        <div class="draft-card-inner">
          <div class="draft-header-label">
            <span>⚡</span> Resposta pronta para execução pós-aprovação:
          </div>
          <div class="draft-body-text" id="draft-text-${id}">${data.response}</div>
          <div class="draft-dispatch-channel">
            <span>🚀</span> ${data.channel}
          </div>
          <button class="draft-edit-action" onclick="openEditDraftModal(${id})">
            ✏️ Editar texto da resposta antes de aprovar
          </button>
        </div>
      </div>

      <div class="mission-buttons-row">
        <button class="btn-action btn-approve-exec" onclick="handleApproveMission(${id})" title="Aprova e executa a resposta imediatamente">
          <span>✅</span> Aprovar & Executar
        </button>
        <button class="btn-action btn-reject-task" onclick="handleRejectMission(${id})" title="Descarta a ação sugerida">
          <span>❌</span> Rejeitar
        </button>
      </div>
    </div>
  `;

  list.appendChild(card);
  refreshCounters();
}

function toggleDraftAccordion(btn) {
  btn.classList.toggle('open');
  const collapse = btn.nextElementSibling;
  collapse.classList.toggle('open');
}

function openEditDraftModal(id) {
  const textEl = document.getElementById(`draft-text-${id}`);
  if (!textEl) return;
  const currentText = textEl.innerText;
  const newText = prompt('Editar a resposta rascunhada pelo agente antes do envio:', currentText);
  if (newText !== null && newText.trim() !== '') {
    textEl.innerText = newText;
    showToast('✍️ Resposta atualizada com sucesso!', 'info');
    appendFeedItem({
      color: '#a855f7',
      agent: 'Hermes',
      text: `Humano editou o rascunho da missão <strong>#${id}</strong>`
    });
  }
}

function handleApproveMission(id) {
  const card = document.getElementById(`mission-card-${id}`);
  if (!card) return;

  card.classList.add('approving');
  countApproved++;
  document.getElementById('metric-approved').textContent = countApproved;

  showToast('🚀 Aprovado! Resposta despachada com sucesso.', 'success');
  appendFeedItem({
    color: '#22c55e',
    agent: 'Você (Humano)',
    text: `Aprovou e executou ação da missão <strong>#${id}</strong> — Resposta enviada!`
  });

  setTimeout(() => {
    card.remove();
    refreshCounters();
  }, 480);
}

function handleRejectMission(id) {
  const card = document.getElementById(`mission-card-${id}`);
  if (!card) return;

  card.classList.add('rejecting');
  countRejected++;
  document.getElementById('metric-rejected').textContent = countRejected;

  showToast('❌ Missão rejeitada e arquivada.', 'error');
  appendFeedItem({
    color: '#ef4444',
    agent: 'Você (Humano)',
    text: `Rejeitou a sugestão da missão <strong>#${id}</strong> — Nenhuma ação externa realizada.`
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
    badgeText.textContent = `${total} ${total === 1 ? 'missão aguarda aprovação' : 'missões com respostas prontas'}`;
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
    text: `Novo arquivo recebido via <strong>${poolItem.source}</strong> — Triagem iniciada!`
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
  el.innerHTML = `
    <div class="feed-dot" style="background: ${item.color};"></div>
    <div class="feed-content">
      <strong style="color: ${item.color};">${item.agent}</strong> — ${item.text}
    </div>
    <div class="feed-time">${timeStr}</div>
  `;
  
  feed.insertBefore(el, feed.firstChild);
  if (feed.children.length > 15) {
    feed.lastChild.remove();
  }
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toasts');
  const toast = document.createElement('div');
  toast.className = `toast-msg ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span> ${msg}`;
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

window.addEventListener('DOMContentLoaded', initApp);
