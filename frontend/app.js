// ══════════════════════════════════════════════════════════════════
// ── API CONNECTION MODULE ────────────────────────────────────────
// ══════════════════════════════════════════════════════════════════
// Quando o painel é servido pelo próprio backend, usa a origem da página —
// o servidor escolhe uma porta livre no boot, então fixar 8000 quebraria o
// painel em qualquer máquina onde essa porta já esteja ocupada.
const API_BASE = window.location.protocol.startsWith('http')
  ? window.location.origin
  : 'http://127.0.0.1:8000';
let isOnline = false;  // true = API mode, false = demo mode

const API = {
  async check() {
    try {
      const r = await fetch(API_BASE + '/api/stats', { signal: AbortSignal.timeout(2000) });
      return r.ok;
    } catch (e) { return false; }
  },
  async getAgents() {
    const r = await fetch(API_BASE + '/api/agents');
    return r.json();
  },
  async getMissions() {
    const r = await fetch(API_BASE + '/api/missions?status=pending');
    return r.json();
  },
  async getStats() {
    const r = await fetch(API_BASE + '/api/stats');
    return r.json();
  },
  async getFeed() {
    const r = await fetch(API_BASE + '/api/feed?limit=15');
    return r.json();
  },
  async approveMission(id) {
    const r = await fetch(API_BASE + '/api/missions/' + id + '/approve', { method: 'POST' });
    return r.json();
  },
  async rejectMission(id) {
    const r = await fetch(API_BASE + '/api/missions/' + id + '/reject', { method: 'POST' });
    return r.json();
  },
  async updateDraft(id, text) {
    const r = await fetch(API_BASE + '/api/missions/' + id + '/draft', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response: text })
    });
    return r.json();
  },
  async processEvent(text, source) {
    const r = await fetch(API_BASE + '/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, source: source })
    });
    return r.json();
  },
  async getRejectedMissions() {
    const r = await fetch(API_BASE + '/api/missions?status=rejected');
    return r.json();
  },
  async getApprovedMissions() {
    const r = await fetch(API_BASE + '/api/missions?status=approved');
    return r.json();
  },
  async restoreMission(id) {
    const r = await fetch(API_BASE + '/api/missions/' + id + '/restore', { method: 'POST' });
    return r.json();
  },
  async getSettings() {
    const r = await fetch(API_BASE + '/api/settings');
    return r.json();
  },
  async saveSettings(settings) {
    const r = await fetch(API_BASE + '/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    return r.json();
  },
  async testAI(data) {
    const r = await fetch(API_BASE + '/api/settings/test-ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return r.json();
  },
  async generateReport(type, query) {
    const q = query ? '&query=' + encodeURIComponent(query) : '';
    const r = await fetch(API_BASE + '/api/reports/generate?type=' + type + q);
    return r.json();
  },
  async getOnboardingStatus() {
    const r = await fetch(API_BASE + '/api/settings/onboarding-status');
    return r.json();
  },
  async saveOnboarding(geminiApiKey) {
    const r = await fetch(API_BASE + '/api/settings/onboarding', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gemini_api_key: geminiApiKey })
    });
    return r.json();
  },
  async getWhatsAppStatus() {
    const r = await fetch(API_BASE + '/api/channels/whatsapp/status');
    return r.json();
  },
  async connectWhatsApp() {
    const r = await fetch(API_BASE + '/api/channels/whatsapp/connect', { method: 'POST' });
    return r.json();
  },
  async peekWhatsAppQR() {
    const r = await fetch(API_BASE + '/api/channels/whatsapp/qr');
    return r.json();
  },
  async restartWhatsAppStack() {
    const r = await fetch(API_BASE + '/api/channels/whatsapp/restart-stack', { method: 'POST' });
    return r.json();
  }
};

// ── SQUAD DE 8 AGENTES ──────────────────────────────────────────
const SQUAD_AGENTS = [
  { id: 'hermes',      name: 'Hermes',         role: 'Orquestrador Geral',   icon: '👑', color: '#a855f7', status: 'ativo' },
  { id: 'atendente',   name: 'Atendente',      role: 'Recepção & Leitura',   icon: '📖', color: '#3b82f6', status: 'ativo' },
  { id: 'admin',       name: 'Administrativo', role: 'Triagem & Roteamento', icon: '🔍', color: '#f97316', status: 'ativo' },
  { id: 'financeiro',  name: 'Financeiro',     role: 'Cobranças & Notas',    icon: '💰', color: '#eab308', status: 'ativo' },
  { id: 'comercial',   name: 'Comercial',      role: 'Leads & Follow-ups',   icon: '📈', color: '#ef4444', status: 'ativo' },
  { id: 'juridico',    name: 'Jurídico LGPD',  role: 'Contratos & LGPD',     icon: '⚖️', color: '#6b7280', status: 'ativo' },
  { id: 'planejador',  name: 'Planejador',     role: 'Estratégia & Prazos',  icon: '🗺️', color: '#14b8a6', status: 'ativo' },
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

async function initApp() {
  // ── Detectar se o backend está rodando ──
  isOnline = await API.check();
  updateConnectionBadge();

  if (isOnline) {
    await checkOnboardingStatus();
  }

  if (isOnline) {
    // ── MODO API: carregar dados reais do servidor ──
    try {
      // Carregar agentes do servidor
      const agents = await API.getAgents();
      if (agents && agents.length) {
        SQUAD_AGENTS.length = 0;
        agents.forEach(function(a) { SQUAD_AGENTS.push(a); });
      }
      renderSquadAgents();
      renderBottomDock();

      // Carregar missões pendentes
      const missions = await API.getMissions();
      missions.forEach(function(m, idx) {
        setTimeout(function() { addMissionCardFromAPI(m); }, idx * 200);
      });

      // Carregar stats
      const stats = await API.getStats();
      countApproved = stats.approved || 0;
      countRejected = stats.rejected || 0;
      var mAppr = document.getElementById('metric-approved');
      var mRej = document.getElementById('metric-rejected');
      if (mAppr) mAppr.textContent = countApproved;
      if (mRej) mRej.textContent = countRejected;

      // Carregar feed
      const feed = await API.getFeed();
      feed.reverse().forEach(function(item) {
        appendFeedItem({
          color: item.color,
          agent: item.agent_name,
          text: item.text
        });
      });

      console.log('🟢 AgentQuest HQ conectado à API em ' + API_BASE);
    } catch (err) {
      console.error('Erro ao carregar dados da API:', err);
      isOnline = false;
      updateConnectionBadge();
      loadDemoMode();
    }
  } else {
    // ── MODO DEMO: dados hardcoded ──
    loadDemoMode();
    console.log('🔴 AgentQuest HQ em modo DEMO (backend offline)');
  }

  startFeedLoop();
  startAgentStatusCycle();
  startClockTick();
}

function loadDemoMode() {
  renderSquadAgents();
  renderBottomDock();
  // Não injeta mais missões fictícias
}

function updateConnectionBadge() {
  var badge = document.getElementById('badge-counter');
  if (!badge) return;
  var dot = isOnline ? '🟢' : '🔴';
  var label = isOnline ? 'API ONLINE' : 'MODO DEMO';
  badge.title = label;
  // Adicionar indicador de conexão ao topbar
  var existing = document.getElementById('connection-indicator');
  if (!existing) {
    existing = document.createElement('span');
    existing.id = 'connection-indicator';
    existing.style.cssText = 'font-size: 10px; margin-left: 8px; padding: 2px 8px; border-radius: 8px; font-weight: 600;';
    badge.parentElement.insertBefore(existing, badge.nextSibling);
  }
  existing.textContent = dot + ' ' + label;
  existing.style.background = isOnline ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)';
  existing.style.color = isOnline ? '#4ade80' : '#f87171';
  existing.style.border = isOnline ? '1px solid rgba(34,197,94,0.3)' : '1px solid rgba(239,68,68,0.3)';
}

function addMissionCardFromAPI(data) {
  // Converte formato da API para formato do card
  addMissionCardWithId(data.id, {
    source: data.source,
    title: data.title,
    agent: data.agent,
    deadline: data.deadline,
    urgent: data.urgent,
    channel: data.channel,
    response: data.response,
    received_message: data.received_message
  });
}

function addMissionCardWithId(serverId, data) {
  var list = document.getElementById('missions-list');
  if (!list) return;
  var currentCards = list.querySelectorAll('.card-mission');

  var id = serverId || (++nextMissionId);
  var card = document.createElement('article');
  card.className = 'card-mission';
  card.id = 'mission-card-' + id;
  card.dataset.serverId = serverId || '';
  card.dataset.agent = data.agent || 'Agente';
  card.dataset.channel = data.channel || 'Canal';
  card.dataset.title = data.title || 'Missão';

  var sourceLabel = data.source === 'whatsapp' ? '💬 WhatsApp' : (data.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail');

    var incomingText = data.received_message || data.title || '';
    if (incomingText.indexOf('Mensagem de') !== -1) {
      incomingText = incomingText.split(':\n').slice(1).join(':\n').trim() || incomingText;
    } else if (incomingText.indexOf('—') !== -1) {
      incomingText = incomingText.split('—')[0].trim();
    }

    var draftHtml = '';
    var buttonsHtml = '';
    
    if (!data.response || data.response.trim() === '') {
      buttonsHtml = '<div style="display: flex; gap: 8px; width: 100%;">' +
          '<button class="btn-action generate-ai-btn" onclick="generateAI(' + id + ', this)" style="flex: 1; background: linear-gradient(135deg, #a855f7 0%, #7e22ce 100%); color: white; border: none; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">🪄 Gerar Resposta IA</button>' +
          '<button class="btn-action btn-reject-task" onclick="openRejectModal(' + id + ')" title="Arquivar a missão sem gerar IA" style="flex: 0 0 110px;"><span>❌</span> Rejeitar</button>' +
        '</div>';
    } else {
      draftHtml = '<button class="draft-toggle-btn" onclick="toggleDraftAccordion(this)" title="Expandir resposta preparada pelo agente">' +
        '<span>✍️ Ver Resposta Preparada pelo Agente</span>' +
        '<span class="draft-arrow">▼</span>' +
      '</button>' +
      '<div class="draft-collapse">' +
        '<div class="draft-card-inner">' +
          '<div class="draft-header-label"><span>⚡</span> Resposta pronta para execução pós-aprovação:</div>' +
          '<div class="draft-body-text" id="draft-text-' + id + '">' + data.response + '</div>' +
          '<div class="draft-dispatch-channel"><span>🚀</span> ' + data.channel + '</div>' +
        '</div>' +
      '</div>';
      
      buttonsHtml = '<button class="btn-action btn-approve-exec" onclick="handleApproveMission(' + id + ')" title="Aprova e executa a resposta imediatamente"><span>✅</span> Aprovar</button>' +
        '<button class="btn-action btn-edit-inline" onclick="openEditDraftModal(' + id + ')" title="Editar o texto da resposta antes do envio"><span>✏️</span> Editar</button>' +
        '<button class="btn-action btn-reject-task" onclick="openRejectModal(' + id + ')" title="Rejeita a ação e dá feedback de aprendizado"><span>❌</span> Rejeitar</button>';
    }

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
      '<div class="mission-preview-snippet" style="font-size: 11.5px; color: #38bdf8; background: rgba(56, 189, 248, 0.08); padding: 8px 12px; border-radius: 8px; margin: 8px 0; border: 1px solid rgba(56, 189, 248, 0.2);">' +
        '<strong>📩 Mensagem Recebida:</strong> "' + (incomingText ? incomingText.substring(0, 450) + (incomingText.length > 450 ? '...' : '') : 'Mensagem direta do contato') + '"' +
      '</div>' +
      draftHtml +
      '<div class="mission-buttons-row">' +
        buttonsHtml +
      '</div>' +
    '</div>';

  list.appendChild(card);
  refreshCounters();
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
  card.dataset.agent = data.agent || 'Agente';
  card.dataset.channel = data.channel || 'Canal';
  card.dataset.title = data.title || 'Missão';

  const sourceLabel = data.source === 'whatsapp' ? '💬 WhatsApp' : data.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';

  var incomingText = data.received_message || data.title || '';
  if (incomingText.indexOf('Mensagem de') !== -1) {
    incomingText = incomingText.split(':\n').slice(1).join(':\n').trim() || incomingText;
  } else if (incomingText.indexOf('—') !== -1) {
    incomingText = incomingText.split('—')[0].trim();
  }

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
      '<div class="mission-preview-snippet" style="font-size: 11.5px; color: #38bdf8; background: rgba(56, 189, 248, 0.08); padding: 8px 12px; border-radius: 8px; margin: 8px 0; border: 1px solid rgba(56, 189, 248, 0.2);">' +
        '<strong>📩 Mensagem Recebida:</strong> "' + (incomingText ? incomingText.substring(0, 140) : 'Mensagem direta do contato') + '"' +
      '</div>' +
      '<button class="draft-toggle-btn" onclick="toggleDraftAccordion(this)" title="Expandir resposta preparada pelo agente">' +
        '<span>✍️ Ver Resposta Preparada pelo Agente</span>' +
        '<span class="draft-arrow">▼</span>' +
      '</button>' +
      '<div class="draft-collapse">' +
        '<div class="draft-card-inner">' +
          '<div class="draft-header-label"><span>⚡</span> Resposta pronta para execução pós-aprovação:</div>' +
          '<div class="draft-body-text" id="draft-text-' + id + '">' + data.response + '</div>' +
          '<div class="draft-dispatch-channel"><span>🚀</span> ' + data.channel + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="mission-buttons-row">' +
        '<button class="btn-action btn-approve-exec" onclick="handleApproveMission(' + id + ')" title="Aprova e executa a resposta imediatamente"><span>✅</span> Aprovar</button>' +
        '<button class="btn-action btn-edit-inline" onclick="openEditDraftModal(' + id + ')" title="Editar o texto da resposta antes do envio"><span>✏️</span> Editar</button>' +
        '<button class="btn-action btn-reject-task" onclick="openRejectModal(' + id + ')" title="Rejeita a ação e dá feedback de aprendizado"><span>❌</span> Rejeitar</button>' +
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

// ── EDIT DRAFT MODAL STATE & HANDLERS ──
let currentEditingMissionId = null;

function openGlobalEditor() {
  const firstMission = document.querySelector('#missions-list .card-mission');
  if (firstMission) {
    const id = firstMission.id.replace('mission-card-', '');
    openEditDraftModal(id);
  } else {
    showToast('🎉 Nenhuma missão pendente para edição no momento!', 'success');
  }
}

function openEditDraftModal(id) {
  const textEl = document.getElementById('draft-text-' + id);
  if (!textEl) {
    showToast('⚠️ Erro ao localizar texto da missão #' + id, 'error');
    return;
  }

  currentEditingMissionId = id;
  const currentText = textEl.innerText.trim();

  // Preenche dados da missão no modal
  const card = document.getElementById('mission-card-' + id);
  const agentName = card ? (card.dataset.agent || 'Especialista') : 'Especialista';
  const channelName = card ? (card.dataset.channel || 'Canal') : 'Canal';
  const titleText = card ? (card.dataset.title || 'Missão #' + id) : 'Missão #' + id;

  document.getElementById('edit-modal-title').textContent = 'Editar Resposta — Missão #' + id;
  document.getElementById('edit-modal-subtitle').textContent = titleText;
  document.getElementById('edit-modal-agent').innerHTML = '🤖 Agente: <strong>' + agentName + '</strong>';
  document.getElementById('edit-modal-channel').innerHTML = '🚀 ' + channelName;

  const textarea = document.getElementById('edit-modal-textarea');
  textarea.value = currentText;
  updateEditCharCounter();

  textarea.oninput = updateEditCharCounter;

  // Abre o modal
  const overlay = document.getElementById('edit-modal-overlay');
  if (overlay) {
    overlay.classList.add('active');
    setTimeout(() => textarea.focus(), 150);
  }
}

function updateEditCharCounter() {
  const textarea = document.getElementById('edit-modal-textarea');
  const counter = document.getElementById('edit-modal-chars');
  if (textarea && counter) {
    const chars = textarea.value.length;
    const words = textarea.value.trim() ? textarea.value.trim().split(/\s+/).length : 0;
    counter.textContent = chars + ' caracteres • ' + words + ' palavras';
  }
}

function closeEditDraftModal() {
  const overlay = document.getElementById('edit-modal-overlay');
  if (overlay) overlay.classList.remove('active');
  currentEditingMissionId = null;
}

function saveEditedDraft() {
  if (!currentEditingMissionId) return;
  const id = currentEditingMissionId;
  const textarea = document.getElementById('edit-modal-textarea');
  const newText = textarea ? textarea.value.trim() : '';

  if (!newText) {
    showToast('O texto da resposta não pode ficar vazio.', 'info');
    return;
  }

  const textEl = document.getElementById('draft-text-' + id);
  if (textEl) {
    textEl.innerText = newText;
  }

  showToast('✍️ Resposta da missão #' + id + ' atualizada com sucesso!', 'success');
  appendFeedItem({
    color: '#a855f7',
    agent: 'Hermes',
    text: 'Humano editou o rascunho da missão <strong>#' + id + '</strong>'
  });

  // Persistir no banco via API
  if (isOnline) {
    API.updateDraft(id, newText).catch(function(e) { console.error('Erro ao salvar rascunho:', e); });
  }

  closeEditDraftModal();
}

function saveAndApproveDraft() {
  if (!currentEditingMissionId) return;
  const id = currentEditingMissionId;
  saveEditedDraft();
  setTimeout(() => {
    handleApproveMission(id);
  }, 200);
}

function handleApproveMission(id) {
  var card = document.getElementById('mission-card-' + id);
  if (!card) return;

  card.classList.add('approving');
  countApproved++;
  var mAppr = document.getElementById('metric-approved');
  if (mAppr) mAppr.textContent = countApproved;

  showToast('🚀 Aprovado! Resposta despachada com sucesso.', 'success');
  appendFeedItem({
    color: '#22c55e',
    agent: 'Você (Humano)',
    text: 'Aprovou e executou ação da missão <strong>#' + id + '</strong> — Resposta enviada!'
  });

  // Persistir no banco via API
  if (isOnline) {
    API.approveMission(id).catch(function(e) { console.error('Erro ao aprovar:', e); });
  }

  setTimeout(function() {
    card.remove();
    refreshCounters();
  }, 480);
}

function handleRejectMission(id) {
  var card = document.getElementById('mission-card-' + id);
  if (!card) return;

  card.classList.add('rejecting');
  countRejected++;
  var mRej = document.getElementById('metric-rejected');
  if (mRej) mRej.textContent = countRejected;

  showToast('❌ Missão rejeitada e arquivada.', 'error');
  appendFeedItem({
    color: '#ef4444',
    agent: 'Você (Humano)',
    text: 'Rejeitou a sugestão da missão <strong>#' + id + '</strong> — Nenhuma ação externa realizada.'
  });

  // Persistir no banco via API
  if (isOnline) {
    API.rejectMission(id).catch(function(e) { console.error('Erro ao rejeitar:', e); });
  }

  setTimeout(function() {
    card.remove();
    refreshCounters();
  }, 480);
}

// ── REJECT MODAL STATE & HANDLERS ──
let currentRejectingMissionId = null;

function openRejectModal(id) {
  currentRejectingMissionId = id;
  const overlay = document.getElementById('reject-modal-overlay');
  if (overlay) {
    overlay.classList.add('active');
    const txt = document.getElementById('reject-modal-textarea');
    if (txt) {
      txt.value = '';
      setTimeout(() => txt.focus(), 100);
    }
  }
}

function closeRejectModal() {
  currentRejectingMissionId = null;
  const overlay = document.getElementById('reject-modal-overlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
}

function directRejectCurrentMission() {
  if (!currentRejectingMissionId) return;
  const id = currentRejectingMissionId;
  closeRejectModal();
  handleRejectMission(id);
}

function submitRejectFeedback() {
  if (!currentRejectingMissionId) return;
  const id = currentRejectingMissionId;
  const feedback = document.getElementById('reject-modal-textarea').value.trim();
  
  if (!feedback) {
    directRejectCurrentMission();
    return;
  }
  
  closeRejectModal();
  
  var card = document.getElementById('mission-card-' + id);
  if (card) {
    card.classList.add('rejecting');
  }
  
  countRejected++;
  var mRej = document.getElementById('metric-rejected');
  if (mRej) mRej.textContent = countRejected;
  
  showToast('🧠 Feedback enviado! O Agente está processando a nova regra...', 'info');
  
  if (isOnline) {
    fetch(API_BASE + '/api/missions/' + id + '/reject_with_feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback: feedback })
    })
    .then(r => r.json())
    .then(data => {
      showToast('✅ ' + (data.message || 'Missão rejeitada com aprendizado.'), 'success');
      appendFeedItem({
        color: '#ef4444',
        agent: 'Sistema',
        text: 'Nova regra de aprendizado criada com sucesso após rejeição da missão <strong>#' + id + '</strong>.'
      });
      if (card) {
        card.remove();
        refreshCounters();
      }
    })
    .catch(e => {
      console.error(e);
      showToast('⚠️ Missão arquivada (erro ao gerar regra de feedback).', 'info');
      if (card) {
        card.remove();
        refreshCounters();
      }
    });
  } else {
    setTimeout(() => {
      showToast('❌ Missão rejeitada e arquivada.', 'error');
      if (card) {
        card.remove();
        refreshCounters();
      }
    }, 480);
  }
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

async function addRandomMission() {
  const sampleMessages = [
    { text: "Olá! Gostaria de saber qual o prazo para entrega do módulo de integração da proposta #884.", source: "whatsapp" },
    { text: "Prezados, favor enviar a 2ª via da fatura #1092 com vencimento atualizado e chave Pix.", source: "whatsapp" },
    { text: "Revisamos o contrato de prestação de serviços e solicitamos adequação da cláusula 5 à LGPD.", source: "email" },
    { text: "Alinhamento com equipe de infraestrutura sobre a janela de manutenção no próximo sábado.", source: "telegram" }
  ];

  const randomItem = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];

  if (isOnline) {
    showToast('⚡ Hermes & Squad processando novo evento...', 'info');
    try {
      const newMission = await API.processEvent(randomItem.text, randomItem.source);
      if (newMission && newMission.id) {
        addMissionCardFromAPI(newMission);
        showToast('✅ Nova missão criada pelo squad de IA!', 'success');
        // Atualiza feed
        const feed = await API.getFeed();
        if (feed && feed.length) {
          const latest = feed[0];
          appendFeedItem({
            color: latest.color,
            agent: latest.agent_name,
            text: latest.text
          });
        }
      }
    } catch (e) {
      console.error('Erro ao processar evento via IA:', e);
      showToast('⚠️ Erro ao chamar API, usando modo local.', 'error');
      addMissionCard(EVENT_POOL[Math.floor(Math.random() * EVENT_POOL.length)]);
    }
  } else {
    const poolItem = EVENT_POOL[Math.floor(Math.random() * EVENT_POOL.length)];
    addMissionCard(poolItem);
    appendFeedItem({
      color: '#a855f7',
      agent: 'Hermes',
      text: 'Novo arquivo recebido via <strong>' + poolItem.source + '</strong> — Triagem iniciada!'
    });
    showToast('📥 Novo evento simulado no inbox!', 'info');
  }
}

let lastFeedId = 0;

function startFeedLoop() {
  // Quando estiver conectado à API, consulta os logs reais do servidor a cada 3 segundos
  setInterval(async () => {
    if (!isOnline) return;
    try {
      // 1. Atualiza Feed em tempo real
      const feed = await API.getFeed();
      if (feed && feed.length > 0) {
        const feedList = document.getElementById('feed-list');
        const existingIds = new Set(Array.from(feedList.querySelectorAll('.feed-item')).map(el => el.dataset.logId));
        
        feed.slice(0, 10).reverse().forEach(item => {
          if (!existingIds.has(String(item.id))) {
            appendFeedItem({
              id: item.id,
              color: item.color,
              agent: item.agent_name,
              text: item.text
            });
          }
        });
      }

      // 2. Atualiza Missões em tempo real
      const missions = await API.getMissions();
      const currentCards = document.querySelectorAll('#missions-list .card-mission');
      const currentIds = new Set(Array.from(currentCards).map(c => parseInt(c.id.replace('mission-card-', ''))));
      const incomingIds = new Set(missions.map(m => m.id));
      
      missions.forEach(m => {
        if (!currentIds.has(m.id)) {
          addMissionCardFromAPI(m);
        }
      });
      
      // Remove missões que foram fechadas/resolvidas por fora (ex: auto-aprovação via celular)
      currentIds.forEach(id => {
        if (!incomingIds.has(id)) {
          const card = document.getElementById('mission-card-' + id);
          if (card) {
            card.classList.add('approving');
            setTimeout(() => card.remove(), 480);
          }
        }
      });

      // 3. Atualiza Stats
      const stats = await API.getStats();
      countApproved = stats.approved || 0;
      countRejected = stats.rejected || 0;
      const mAppr = document.getElementById('metric-approved');
      const mRej = document.getElementById('metric-rejected');
      if (mAppr) mAppr.textContent = countApproved;
      if (mRej) mRej.textContent = countRejected;
      refreshCounters();

    } catch (e) {
      console.warn('Erro na sincronização em tempo real:', e);
    }
  }, 1000);
}

function appendFeedItem(item) {
  const feed = document.getElementById('feed-list');
  const timeStr = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  
  const el = document.createElement('div');
  el.className = 'feed-item';
  if (item.id) el.dataset.logId = item.id;
  el.style.borderLeftColor = item.color;
  el.innerHTML = 
    '<div class="feed-dot" style="background: ' + item.color + ';"></div>' +
    '<div class="feed-content">' +
      '<strong style="color: ' + item.color + ';">' + (item.agent || item.agent_name || 'Agente') + '</strong> — ' + item.text +
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

let currentActiveReportType = 'executivo';
let currentActiveReportQuery = '';

async function generateReportPreset(presetKey) {
  currentActiveReportType = presetKey;
  currentActiveReportQuery = '';
  
  if (isOnline) {
    runReportLoading();
    try {
      const realData = await API.generateReport(presetKey, '');
      renderReportView(realData);
    } catch (e) {
      console.error('Erro ao gerar relatório via API:', e);
      const fallbackData = REPORT_TEMPLATES[presetKey] || REPORT_TEMPLATES.executivo;
      renderReportView(fallbackData);
    }
  } else {
    const data = REPORT_TEMPLATES[presetKey] || REPORT_TEMPLATES.executivo;
    runReportGenerationOffline(data);
  }
}

async function generateReportCustom() {
  const query = document.getElementById('custom-query-text').value.trim();
  if (!query) {
    showToast('Por favor, digite sua pergunta para o Hermes.', 'info');
    return;
  }
  
  currentActiveReportType = 'custom';
  currentActiveReportQuery = query;

  if (isOnline) {
    runReportLoading();
    try {
      const realData = await API.generateReport('custom', query);
      renderReportView(realData);
    } catch (e) {
      console.error('Erro ao gerar relatório via API:', e);
      const customData = getOfflineCustomData(query);
      renderReportView(customData);
    }
  } else {
    const customData = getOfflineCustomData(query);
    runReportGenerationOffline(customData);
  }
}

function runReportLoading() {
  document.getElementById('report-view-select').style.display = 'none';
  document.getElementById('report-view-loading').style.display = 'block';
  document.getElementById('report-view-content').style.display = 'none';

  const steps = [
    'Hermes consultando o banco de dados e o cofre Obsidian...',
    'Compilando métricas reais de faturamento e vendas...',
    'Revisor validando coerência dos números...',
    'Formatando painel executivo estilo Power BI...'
  ];

  let sIdx = 0;
  const stepInterval = setInterval(() => {
    sIdx++;
    if (sIdx < steps.length) {
      const el = document.getElementById('loading-agent-step');
      if (el) el.textContent = steps[sIdx];
    }
  }, 400);

  setTimeout(() => clearInterval(stepInterval), 3000);
}

function runReportGenerationOffline(reportData) {
  runReportLoading();
  setTimeout(() => {
    renderReportView(reportData);
  }, 1400);
}

function getOfflineCustomData(query) {
  return {
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
}

function exportCurrentReport(format) {
  if (isOnline) {
    const q = currentActiveReportQuery ? '&query=' + encodeURIComponent(currentActiveReportQuery) : '';
    const url = API_BASE + '/api/reports/export/' + format + '?type=' + currentActiveReportType + q;
    window.open(url, '_blank');
    showToast('📥 Download do ' + format.toUpperCase() + ' iniciado e salvo em outputs/', 'success');
  } else {
    showToast('📥 [DEMO] Relatório salvo na pasta outputs/', 'info');
  }
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

// ── REJECTED MISSIONS MODAL HANDLERS ──
let rejectedMissionsCache = [];

async function openRejectedMissionsModal() {
  const overlay = document.getElementById('rejected-modal-overlay');
  if (overlay) overlay.classList.add('active');
  const listEl = document.getElementById('rejected-missions-list');
  const emptyEl = document.getElementById('rejected-empty-state');
  listEl.innerHTML = '<div style="color: #94a3b8; padding: 20px; text-align: center;">Carregando histórico de rejeitadas...</div>';
  emptyEl.style.display = 'none';

  if (isOnline) {
    try {
      const missions = await API.getRejectedMissions();
      rejectedMissionsCache = missions;
      renderRejectedMissions(missions);
    } catch (e) {
      console.error(e);
      listEl.innerHTML = '<div style="color: #f87171; padding: 20px; text-align: center;">Erro ao carregar missões rejeitadas.</div>';
    }
  } else {
    // Offline simulated
    renderRejectedMissions(rejectedMissionsCache);
  }
}

function closeRejectedMissionsModal() {
  const overlay = document.getElementById('rejected-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function renderRejectedMissions(missions) {
  const listEl = document.getElementById('rejected-missions-list');
  const emptyEl = document.getElementById('rejected-empty-state');

  if (!missions || missions.length === 0) {
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }

  emptyEl.style.display = 'none';
  listEl.innerHTML = missions.map(m => {
    const sourceLabel = m.source === 'whatsapp' ? '💬 WhatsApp' : m.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';
    return `
      <div class="rejected-mission-card" id="rejected-card-${m.id}">
        <div class="rejected-card-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="info-tag" style="background: rgba(239, 68, 68, 0.15); color: #fca5a5;">Missão #${m.id}</span>
            <span class="info-tag">${sourceLabel}</span>
            <span class="info-tag">🤖 ${m.agent}</span>
          </div>
          <span style="font-size: 10px; color: #64748b;">${m.deadline || 'Sem prazo'}</span>
        </div>
        <div class="rejected-card-title">${m.title}</div>
        <div class="rejected-card-body" id="rejected-text-${m.id}">${m.response}</div>
        <div class="rejected-card-actions">
          <button class="btn-restore-mission" onclick="handleRestoreMission(${m.id})" title="Devolve esta missão para a fila ativa de aprovação">
            <span>🔄</span> Restaurar para a Fila
          </button>
          <button class="btn-edit-approve-rejected" onclick="handleEditAndApproveRejected(${m.id})" title="Edita o texto e aprova imediatamente">
            <span>✏️</span> Editar & Aprovar
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function handleRestoreMission(id) {
  if (isOnline) {
    try {
      const restored = await API.restoreMission(id);
      showToast('🔄 Missão #' + id + ' restaurada com sucesso para a fila!', 'success');
      appendFeedItem({
        color: '#38bdf8',
        agent: 'Você (Humano)',
        text: 'Restaurou a missão <strong>#' + id + '</strong> de volta para a fila de aprovação.'
      });
      // Remove from rejected modal UI
      const card = document.getElementById('rejected-card-' + id);
      if (card) card.remove();
      
      // Update rejected counter
      countRejected = Math.max(0, countRejected - 1);
      const mRej = document.getElementById('metric-rejected');
      if (mRej) mRej.textContent = countRejected;
      
      // Re-add to main pending list
      addMissionCard(restored);
      refreshCounters();
      
      // Check if rejected list empty
      const remaining = document.querySelectorAll('.rejected-mission-card').length;
      if (remaining === 0) {
        document.getElementById('rejected-empty-state').style.display = 'block';
      }
    } catch (e) {
      console.error(e);
      showToast('⚠️ Erro ao restaurar missão.', 'error');
    }
  } else {
    showToast('🔄 [DEMO] Missão restaurada para a fila', 'success');
  }
}

function handleEditAndApproveRejected(id) {
  closeRejectedMissionsModal();
  // Open edit modal directly for this mission
  openEditDraftModal(id);
}

// ── APPROVED / EXECUTED MISSIONS MODAL STATE & HANDLERS ──
let approvedMissionsCache = [];

async function openApprovedMissionsModal() {
  const overlay = document.getElementById('approved-modal-overlay');
  if (overlay) overlay.classList.add('active');

  const listEl = document.getElementById('approved-missions-list');
  const emptyEl = document.getElementById('approved-empty-state');
  listEl.innerHTML = '<div style="color: #4ade80; padding: 25px; text-align: center;">⏳ Carregando histórico de missões executadas...</div>';
  emptyEl.style.display = 'none';

  if (isOnline) {
    try {
      const missions = await API.getApprovedMissions();
      approvedMissionsCache = missions;
      renderApprovedMissions(missions);
    } catch (e) {
      console.error(e);
      listEl.innerHTML = '<div style="color: #f87171; padding: 20px; text-align: center;">Erro ao carregar histórico de missões aprovadas.</div>';
    }
  } else {
    renderApprovedMissions(approvedMissionsCache);
  }
}

function closeApprovedMissionsModal() {
  const overlay = document.getElementById('approved-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function renderApprovedMissions(missions) {
  const listEl = document.getElementById('approved-missions-list');
  const emptyEl = document.getElementById('approved-empty-state');

  if (!missions || missions.length === 0) {
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }

  emptyEl.style.display = 'none';
  listEl.innerHTML = missions.map(m => {
    const sourceLabel = m.source === 'whatsapp' ? '💬 WhatsApp' : m.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';
    const incoming = m.received_message || '';
    const dateStr = m.created_at ? new Date(m.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';
    return `
      <div class="rejected-mission-card" id="approved-card-${m.id}" style="border-left: 3px solid #22c55e; background: rgba(15, 23, 42, 0.75);">
        <div class="rejected-card-header">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span class="info-tag" style="background: rgba(34, 197, 94, 0.2); color: #86efac; font-weight: 700;">✅ Executada #${m.id}</span>
            <span class="info-tag">${sourceLabel}</span>
            <span class="info-tag">🤖 ${m.agent}</span>
            <span class="info-tag" style="background: rgba(56, 189, 248, 0.12); color: #7dd3fc;">🚀 ${m.channel || 'Despachado'}</span>
          </div>
          <span style="font-size: 10.5px; color: #94a3b8;">${dateStr || m.deadline || ''}</span>
        </div>
        <div class="rejected-card-title" style="color: #f8fafc; font-weight: 700; margin: 8px 0 4px 0; font-size: 13px;">${m.title}</div>
        ${incoming ? `<div style="font-size: 11px; color: #94a3b8; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 7px 10px; border-radius: 6px; margin: 6px 0;"><strong>📩 Mensagem Recebida:</strong> "${incoming.length > 250 ? incoming.substring(0, 250) + '...' : incoming}"</div>` : ''}
        <div class="rejected-card-body" style="background: rgba(34, 197, 94, 0.05); border: 1px solid rgba(34, 197, 94, 0.25); color: #e2e8f0; white-space: pre-wrap; font-size: 12px; line-height: 1.5; margin-top: 6px; padding: 10px 12px; border-radius: 8px;">${m.response || 'Nenhuma resposta gravada.'}</div>
      </div>
    `;
  }).join('');
}

// ── PENDING / AWAITING ACTION MISSIONS MODAL HANDLERS ──
async function openPendingMissionsModal() {
  const overlay = document.getElementById('pending-modal-overlay');
  if (overlay) overlay.classList.add('active');

  const listEl = document.getElementById('pending-modal-list');
  const emptyEl = document.getElementById('pending-modal-empty-state');
  listEl.innerHTML = '<div style="color: #f59e0b; padding: 25px; text-align: center;">⏳ Carregando demandas pendentes...</div>';
  emptyEl.style.display = 'none';

  if (isOnline) {
    try {
      const missions = await API.getMissions();
      renderPendingModalMissions(missions);
    } catch (e) {
      console.error(e);
      listEl.innerHTML = '<div style="color: #f87171; padding: 20px; text-align: center;">Erro ao carregar demandas pendentes.</div>';
    }
  } else {
    const mainCards = document.querySelectorAll('#missions-list .card-mission');
    if (mainCards.length === 0) {
      listEl.innerHTML = '';
      emptyEl.style.display = 'block';
    } else {
      listEl.innerHTML = '<div style="color: #cbd5e1; padding: 20px; text-align: center;">As demandas ativas estão visíveis no painel central.</div>';
    }
  }
}

function closePendingMissionsModal() {
  const overlay = document.getElementById('pending-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function renderPendingModalMissions(missions) {
  const listEl = document.getElementById('pending-modal-list');
  const emptyEl = document.getElementById('pending-modal-empty-state');

  if (!missions || missions.length === 0) {
    listEl.innerHTML = '';
    emptyEl.style.display = 'block';
    return;
  }

  emptyEl.style.display = 'none';
  listEl.innerHTML = missions.map(m => {
    const sourceLabel = m.source === 'whatsapp' ? '💬 WhatsApp' : m.source === 'telegram' ? '✈️ Telegram' : '📧 E-mail';
    const incoming = m.received_message || '';
    const hasResponse = m.response && m.response.trim().length > 0;
    return `
      <div class="rejected-mission-card" id="pending-modal-card-${m.id}" style="border-left: 3px solid #f59e0b; background: rgba(15, 23, 42, 0.75);">
        <div class="rejected-card-header">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span class="info-tag" style="background: rgba(245, 158, 11, 0.2); color: #fde68a; font-weight: 700;">⏳ Demanda #${m.id}</span>
            <span class="info-tag">${sourceLabel}</span>
            <span class="info-tag">🤖 ${m.agent}</span>
            ${m.urgent ? '<span class="tag-urgente">URGENTE</span>' : ''}
          </div>
          <span style="font-size: 10.5px; color: #94a3b8;">📅 Prazo: ${m.deadline || 'Pendente'}</span>
        </div>
        <div class="rejected-card-title" style="color: #f8fafc; font-weight: 700; margin: 8px 0 4px 0; font-size: 13px;">${m.title}</div>
        ${incoming ? `<div style="font-size: 11px; color: #38bdf8; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.2); padding: 7px 10px; border-radius: 6px; margin: 6px 0;"><strong>📩 Mensagem Recebida:</strong> "${incoming.length > 250 ? incoming.substring(0, 250) + '...' : incoming}"</div>` : ''}
        ${hasResponse ? `
          <div class="rejected-card-body" style="background: rgba(245, 158, 11, 0.04); border: 1px solid rgba(245, 158, 11, 0.25); color: #e2e8f0; white-space: pre-wrap; font-size: 12px; line-height: 1.5; margin-top: 6px; padding: 10px 12px; border-radius: 8px;"><strong>✍️ Resposta Proposta:</strong>\n${m.response}</div>
        ` : `
          <div style="font-size: 11px; color: #94a3b8; font-style: italic; margin-top: 6px;">Aguardando acionamento da IA ou resposta manual pelo celular.</div>
        `}
      </div>
    `;
  }).join('');
}

// ── PROCESSING SQUAD AGENTS MODAL HANDLERS ──
function openProcessingAgentsModal() {
  const overlay = document.getElementById('processing-modal-overlay');
  if (overlay) overlay.classList.add('active');
  renderProcessingAgents();
}

function closeProcessingAgentsModal() {
  const overlay = document.getElementById('processing-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function renderProcessingAgents() {
  const container = document.getElementById('processing-agents-list');
  if (!container) return;

  container.innerHTML = SQUAD_AGENTS.map(agent => {
    const isProcessing = agent.status === 'processando';
    const statusClass = isProcessing ? 'processing' : (agent.status === 'ativo' ? 'active' : 'idle');
    const statusBadge = isProcessing ? '⚙️ Processando' : (agent.status === 'ativo' ? '🟢 Ativo & Monitorando' : '🔵 Ocioso / Standby');
    const statusBg = isProcessing ? 'rgba(56, 189, 248, 0.15)' : 'rgba(34, 197, 94, 0.1)';
    const statusColor = isProcessing ? '#7dd3fc' : '#86efac';

    return `
      <div class="cfg-agent-card" style="border-left: 3px solid ${agent.color}; background: rgba(15, 23, 42, 0.85);">
        <div class="cfg-agent-header">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">${agent.icon}</span>
            <div>
              <div class="cfg-agent-title" style="color: #f8fafc; font-weight: 700;">${agent.name}</div>
              <div class="cfg-agent-role" style="color: #94a3b8; font-size: 11px;">${agent.role}</div>
            </div>
          </div>
          <span style="font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 12px; background: ${statusBg}; color: ${statusColor}; border: 1px solid ${statusColor}40;">
            ${statusBadge}
          </span>
        </div>
        <div style="font-size: 11px; color: #cbd5e1; margin-top: 6px; line-height: 1.45;">
          ${isProcessing ? '⚡ Executando varredura de pendências e sintetizando plano de ação.' : '👀 Em prontidão para receber novos eventos do WhatsApp, Telegram e E-mail.'}
        </div>
      </div>
    `;
  }).join('');
}


// ── GLOBAL SETTINGS STATE & HANDLERS ──
let globalSettings = null;

function openSettingsModal() {
  const overlay = document.getElementById('settings-modal-overlay');
  if (overlay) overlay.classList.add('active');
  loadSettings();
}

function closeSettingsModal() {
  const overlay = document.getElementById('settings-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function switchSettingsTab(tabName) {
  document.querySelectorAll('.settings-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.settings-tab-pane').forEach(pane => pane.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.settings-tab-btn')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabName));
  if (activeBtn) activeBtn.classList.add('active');

  const pane = document.getElementById('settings-tab-' + tabName);
  if (pane) pane.classList.add('active');

  if (tabName === 'ai') {
    setTimeout(() => checkActiveAIStatus(false), 80);
  }
  if (tabName === 'channels') {
    setTimeout(() => checkWhatsAppStatus(), 80);
  }
}

function toggleAIProviderFields() {
  const provider = document.getElementById('cfg-ai-active-provider').value;
  document.getElementById('cfg-field-nous').style.display = (provider === 'nous_openrouter') ? 'block' : 'none';
  document.getElementById('cfg-field-gemini').style.display = (provider === 'gemini') ? 'block' : 'none';
  document.getElementById('cfg-field-openai').style.display = (provider === 'openai') ? 'block' : 'none';
  document.getElementById('cfg-field-local').style.display = (provider === 'local') ? 'block' : 'none';
}

async function loadSettings() {
  let settings = null;
  if (isOnline) {
    try {
      settings = await API.getSettings();
    } catch (e) {
      console.warn('Falha ao carregar settings do backend, usando localStorage:', e);
    }
  }
  
  if (!settings) {
    const cached = localStorage.getItem('agentquest_settings');
    if (cached) {
      try { settings = JSON.parse(cached); } catch(e){}
    }
  }

  if (settings) {
    globalSettings = settings;
    populateSettingsForm(settings);
  }
}

function populateSettingsForm(s) {
  // Tab 1: AI
  if (s.ai_providers) {
    const ai = s.ai_providers;
    if (ai.active_provider) document.getElementById('cfg-ai-active-provider').value = ai.active_provider;
    if (ai.nous_api_key) document.getElementById('cfg-nous-key').value = ai.nous_api_key;
    if (ai.nous_model_name) document.getElementById('cfg-nous-model').value = ai.nous_model_name;
    if (ai.nous_base_url) document.getElementById('cfg-nous-base-url').value = ai.nous_base_url;
    if (ai.gemini_api_key) document.getElementById('cfg-gemini-key').value = ai.gemini_api_key;
    if (ai.gemini_model) document.getElementById('cfg-gemini-model').value = ai.gemini_model;
    if (ai.openai_api_key) document.getElementById('cfg-openai-key').value = ai.openai_api_key;
    if (ai.openai_model) document.getElementById('cfg-openai-model').value = ai.openai_model;
    if (ai.local_base_url) document.getElementById('cfg-local-url').value = ai.local_base_url;
    if (ai.local_model && document.getElementById('cfg-local-model')) document.getElementById('cfg-local-model').value = ai.local_model;
    if (ai.local_api_key) document.getElementById('cfg-local-key').value = ai.local_api_key;
    if (ai.auto_fallback_local !== undefined && document.getElementById('cfg-auto-fallback-local')) {
      document.getElementById('cfg-auto-fallback-local').checked = Boolean(ai.auto_fallback_local);
    }
    toggleAIProviderFields();
    setTimeout(() => checkActiveAIStatus(false), 100);
  }

  // Tab 2: Agents
  const agentsContainer = document.getElementById('cfg-agents-list');
  const squad = s.agents || SQUAD_AGENTS;
  agentsContainer.innerHTML = squad.map(a => `
    <div class="cfg-agent-card" id="cfg-agent-${a.id}">
      <div class="cfg-agent-header">
        <span style="font-size: 20px;">${a.icon || '🤖'}</span>
        <div>
          <div class="cfg-agent-title">${a.name}</div>
          <div class="cfg-agent-role">${a.role}</div>
        </div>
      </div>
      <div class="cfg-agent-row">
        <div class="settings-form-group">
          <label>Status Operacional:</label>
          <select class="settings-select cfg-agent-status" data-agent="${a.id}">
            <option value="ativo" ${a.status === 'ativo' ? 'selected' : ''}>🟢 Ativo</option>
            <option value="ocioso" ${a.status === 'ocioso' ? 'selected' : ''}>🔵 Ocioso</option>
            <option value="pausado" ${a.status === 'pausado' ? 'selected' : ''}>⏸️ Pausado</option>
          </select>
        </div>
        <div class="settings-form-group">
          <label>Nível de Autonomia:</label>
          <select class="settings-select cfg-agent-autonomy" data-agent="${a.id}">
            <option value="manual" ${(a.autonomy || 'manual') === 'manual' ? 'selected' : ''}>🛡️ Exigir Aprovação</option>
            <option value="auto" ${a.autonomy === 'auto' ? 'selected' : ''}>⚡ Auto-Executar</option>
          </select>
        </div>
      </div>
      <div class="settings-form-group">
        <label>Tom de Voz:</label>
        <input type="text" class="settings-input cfg-agent-tone" data-agent="${a.id}" value="${a.tone || 'Padrão Profissional'}">
      </div>
    </div>
  `).join('');

  // Tab 3: Channels
  if (s.channels) {
    if (s.channels.whatsapp) {
      const wa = s.channels.whatsapp;
      if (wa.provider) document.getElementById('cfg-wa-provider').value = wa.provider;
      if (wa.api_url) document.getElementById('cfg-wa-url').value = wa.api_url;
      if (wa.instance_name) document.getElementById('cfg-wa-instance').value = wa.instance_name;
      if (wa.api_token) document.getElementById('cfg-wa-token').value = wa.api_token;
      if (wa.webhook_url) document.getElementById('cfg-wa-webhook').value = wa.webhook_url;
      if (wa.ignore_groups !== undefined) document.getElementById('cfg-wa-ignore-groups').value = String(wa.ignore_groups);
      if (wa.meta_phone_number_id) document.getElementById('cfg-wa-meta-phone-id').value = wa.meta_phone_number_id;
      if (wa.meta_access_token) document.getElementById('cfg-wa-meta-token').value = wa.meta_access_token;
      if (wa.meta_verify_token) document.getElementById('cfg-wa-meta-verify').value = wa.meta_verify_token;
      if (wa.meta_api_version) document.getElementById('cfg-wa-meta-version').value = wa.meta_api_version;
      toggleWhatsAppProviderFields();
    }
    if (s.channels.telegram) {
      const tg = s.channels.telegram;
      if (tg.bot_token) document.getElementById('cfg-tg-token').value = tg.bot_token;
      if (tg.default_chat_id) document.getElementById('cfg-tg-chat').value = tg.default_chat_id;
    }
    if (s.channels.email) {
      const em = s.channels.email;
      if (em.email_user) document.getElementById('cfg-email-user').value = em.email_user;
      if (em.email_password) document.getElementById('cfg-email-pass').value = em.email_password;
      if (em.imap_host) document.getElementById('cfg-email-imap').value = em.imap_host + (em.imap_port ? ':' + em.imap_port : '');
      if (em.smtp_host) document.getElementById('cfg-email-smtp').value = em.smtp_host + (em.smtp_port ? ':' + em.smtp_port : '');
    }
  }

  // Tab 4: Storage
  if (s.storage) {
    if (s.storage.inbox_folder) document.getElementById('cfg-dir-inbox').value = s.storage.inbox_folder;
    if (s.storage.processed_folder) document.getElementById('cfg-dir-processed').value = s.storage.processed_folder;
    if (s.storage.outputs_folder) document.getElementById('cfg-dir-outputs').value = s.storage.outputs_folder;
    if (s.storage.vault_folder) document.getElementById('cfg-dir-vault').value = s.storage.vault_folder;
  }
}

async function saveAllSettings() {
  const agentsData = [];
  document.querySelectorAll('.cfg-agent-card').forEach(card => {
    const id = card.id.replace('cfg-agent-', '');
    const status = card.querySelector('.cfg-agent-status').value;
    const autonomy = card.querySelector('.cfg-agent-autonomy').value;
    const tone = card.querySelector('.cfg-agent-tone').value;
    const baseAgent = SQUAD_AGENTS.find(a => a.id === id) || {};
    agentsData.push({
      id: id,
      name: baseAgent.name || id,
      role: baseAgent.role || '',
      icon: baseAgent.icon || '🤖',
      color: baseAgent.color || '#38bdf8',
      status: status,
      autonomy: autonomy,
      tone: tone
    });
  });

  const emailSmtpVal = document.getElementById('cfg-email-smtp').value;
  const emailImapVal = document.getElementById('cfg-email-imap').value;

  const payload = {
    ai_providers: {
      active_provider: document.getElementById('cfg-ai-active-provider').value,
      nous_api_key: document.getElementById('cfg-nous-key').value,
      nous_model_name: document.getElementById('cfg-nous-model').value,
      nous_base_url: document.getElementById('cfg-nous-base-url').value,
      gemini_api_key: document.getElementById('cfg-gemini-key').value,
      gemini_model: document.getElementById('cfg-gemini-model').value,
      openai_api_key: document.getElementById('cfg-openai-key').value,
      openai_model: document.getElementById('cfg-openai-model').value,
      local_base_url: document.getElementById('cfg-local-url').value,
      local_model: document.getElementById('cfg-local-model') ? document.getElementById('cfg-local-model').value : 'qwen2.5:7b',
      local_api_key: document.getElementById('cfg-local-key').value,
      auto_fallback_local: document.getElementById('cfg-auto-fallback-local') ? document.getElementById('cfg-auto-fallback-local').checked : true
    },
    agents: agentsData,
    channels: {
      whatsapp: {
        enabled: true,
        provider: document.getElementById('cfg-wa-provider').value,
        api_url: document.getElementById('cfg-wa-url').value,
        instance_name: document.getElementById('cfg-wa-instance').value,
        api_token: document.getElementById('cfg-wa-token').value,
        webhook_url: document.getElementById('cfg-wa-webhook').value,
        ignore_groups: document.getElementById('cfg-wa-ignore-groups').value === 'true',
        meta_phone_number_id: document.getElementById('cfg-wa-meta-phone-id').value,
        meta_access_token: document.getElementById('cfg-wa-meta-token').value,
        meta_verify_token: document.getElementById('cfg-wa-meta-verify').value,
        meta_api_version: document.getElementById('cfg-wa-meta-version').value || 'v21.0'
      },
      telegram: {
        enabled: true,
        bot_token: document.getElementById('cfg-tg-token').value,
        default_chat_id: document.getElementById('cfg-tg-chat').value
      },
      email: {
        enabled: true,
        email_user: document.getElementById('cfg-email-user').value,
        email_password: document.getElementById('cfg-email-pass').value,
        imap_host: emailImapVal.split(':')[0] || 'imap.gmail.com',
        imap_port: parseInt(emailImapVal.split(':')[1] || '993'),
        smtp_host: emailSmtpVal.split(':')[0] || 'smtp.gmail.com',
        smtp_port: parseInt(emailSmtpVal.split(':')[1] || '587')
      }
    },
    storage: {
      inbox_folder: document.getElementById('cfg-dir-inbox').value,
      processed_folder: document.getElementById('cfg-dir-processed').value,
      outputs_folder: document.getElementById('cfg-dir-outputs').value,
      vault_folder: document.getElementById('cfg-dir-vault').value
    }
  };

  localStorage.setItem('agentquest_settings', JSON.stringify(payload));
  globalSettings = payload;

  if (isOnline) {
    try {
      const res = await API.saveSettings(payload);
      showToast('💾 ' + res.message, 'success');
    } catch (e) {
      console.error(e);
      showToast('⚠️ Salvo no navegador, mas erro ao sincronizar com servidor.', 'info');
    }
  } else {
    showToast('💾 Configurações salvas localmente com sucesso!', 'success');
  }

  closeSettingsModal();
}

async function checkActiveAIStatus(forceRefresh = false) {
  const card = document.getElementById('ai-status-card');
  if (!card) return;

  const providerSelect = document.getElementById('cfg-ai-active-provider');
  const provider = providerSelect ? providerSelect.value : 'gemini';

  let apiKey = '';
  let model = '';
  let baseUrl = '';

  if (provider === 'nous_openrouter') {
    apiKey = document.getElementById('cfg-nous-key') ? document.getElementById('cfg-nous-key').value : '';
    model = document.getElementById('cfg-nous-model') ? document.getElementById('cfg-nous-model').value : '';
    baseUrl = document.getElementById('cfg-nous-base-url') ? document.getElementById('cfg-nous-base-url').value : '';
  } else if (provider === 'gemini') {
    apiKey = document.getElementById('cfg-gemini-key') ? document.getElementById('cfg-gemini-key').value : '';
    model = document.getElementById('cfg-gemini-model') ? document.getElementById('cfg-gemini-model').value : '';
  } else if (provider === 'openai') {
    apiKey = document.getElementById('cfg-openai-key') ? document.getElementById('cfg-openai-key').value : '';
    model = document.getElementById('cfg-openai-model') ? document.getElementById('cfg-openai-model').value : '';
  } else if (provider === 'local') {
    apiKey = document.getElementById('cfg-local-key') ? document.getElementById('cfg-local-key').value : '';
    baseUrl = document.getElementById('cfg-local-url') ? document.getElementById('cfg-local-url').value : '';
  }

  const dotEl = document.getElementById('ai-status-dot');
  const providerEl = document.getElementById('ai-stat-provider');
  const statusEl = document.getElementById('ai-stat-status');
  const latencyEl = document.getElementById('ai-stat-latency');
  const creditsEl = document.getElementById('ai-stat-credits');
  const updatedEl = document.getElementById('ai-stat-updated');
  const msgBox = document.getElementById('ai-status-msg-box');
  const msgText = document.getElementById('ai-status-msg-text');
  const msgRecom = document.getElementById('ai-status-msg-recom');
  const msgIcon = document.getElementById('ai-status-msg-icon');
  const btnRefresh = document.getElementById('btn-refresh-ai-status');

  if (dotEl) dotEl.className = 'status-pulse-dot loading';
  if (statusEl) statusEl.innerHTML = '<span class="badge-status-pill loading">⏳ Diagnosticando...</span>';
  if (btnRefresh) btnRefresh.disabled = true;

  try {
    const res = await API.testAI({
      provider: provider,
      api_key: apiKey,
      model: model,
      base_url: baseUrl
    });

    const isOnline = res.success && res.status === 'online';
    const isWarning = res.status === 'rate_limited' || res.status === 'quota_exhausted' || res.status === 'model_not_found';

    if (dotEl) {
      dotEl.className = 'status-pulse-dot ' + (isOnline ? 'online' : (isWarning ? 'warning' : 'error'));
    }

    if (providerEl) {
      providerEl.textContent = (res.provider_label || provider) + (res.model ? ' (' + res.model + ')' : '');
    }

    if (statusEl) {
      const badgeClass = isOnline ? 'online' : (isWarning ? 'warning' : 'error');
      statusEl.innerHTML = `<span class="badge-status-pill ${badgeClass}">${res.status_badge || (res.success ? '🟢 Online' : '🔴 Erro')}</span>`;
    }

    if (latencyEl) {
      latencyEl.textContent = res.latency_ms > 0 ? `${res.latency_ms} ms` : '-- ms';
      latencyEl.style.color = res.latency_ms > 0 ? (res.latency_ms < 1500 ? '#4ade80' : '#fbbf24') : '#f1f5f9';
    }

    if (creditsEl) {
      creditsEl.textContent = res.credits_info || 'N/A';
      creditsEl.style.color = isOnline ? '#38bdf8' : (isWarning ? '#fde68a' : '#fca5a5');
    }

    if (updatedEl) {
      updatedEl.textContent = 'Última checagem: ' + (res.checked_at || new Date().toLocaleTimeString('pt-BR'));
    }

    if (msgBox && msgText) {
      msgBox.style.display = 'flex';
      msgBox.className = 'ai-status-message-box ' + (isOnline ? 'success' : (isWarning ? 'warning' : 'error'));
      if (msgIcon) msgIcon.textContent = isOnline ? '✨' : (isWarning ? '⚠️' : '❌');
      msgText.textContent = res.message || '';
      if (msgRecom) {
        msgRecom.textContent = res.recommendation ? '💡 Dica: ' + res.recommendation : '';
        msgRecom.style.display = res.recommendation ? 'block' : 'none';
      }
    }

    if (forceRefresh) {
      showToast(isOnline ? '✅ Provedor e Conta 100% Operacionais!' : (isWarning ? '⚠️ Alerta de Cota/Créditos no Provedor' : '❌ Provedor Inacessível'), isOnline ? 'success' : (isWarning ? 'info' : 'error'));
    }

  } catch (err) {
    if (dotEl) dotEl.className = 'status-pulse-dot error';
    if (statusEl) statusEl.innerHTML = '<span class="badge-status-pill error">🔴 Erro Local</span>';
    if (msgBox && msgText) {
      msgBox.style.display = 'flex';
      msgBox.className = 'ai-status-message-box error';
      if (msgIcon) msgIcon.textContent = '❌';
      msgText.textContent = 'Não foi possível contatar o servidor local para diagnóstico.';
      if (msgRecom) msgRecom.style.display = 'none';
    }
  } finally {
    if (btnRefresh) btnRefresh.disabled = false;
  }
}

async function testCurrentAIConnection() {
  const statusEl = document.getElementById('cfg-test-status');
  if (statusEl) {
    statusEl.className = 'test-status-msg loading';
    statusEl.textContent = '⏳ Diagnosticando conta e modelo...';
  }
  await checkActiveAIStatus(true);
  if (statusEl) {
    const dot = document.getElementById('ai-status-dot');
    const isOnline = dot && dot.classList.contains('online');
    const isWarning = dot && dot.classList.contains('warning');
    statusEl.className = 'test-status-msg ' + (isOnline ? 'success' : (isWarning ? 'loading' : 'error'));
    statusEl.textContent = isOnline ? '✅ Conexão e Conta Operacionais!' : (isWarning ? '⚠️ Limite de Cota/Créditos Atingido' : '❌ Falha na Conexão');
  }
}

window.addEventListener('click', (e) => {
  const reportOverlay = document.getElementById('report-modal-overlay');
  if (e.target === reportOverlay) {
    closeReportModal();
  }
  const editOverlay = document.getElementById('edit-modal-overlay');
  if (e.target === editOverlay) {
    closeEditDraftModal();
  }
  const rejectOverlay = document.getElementById('reject-modal-overlay');
  if (e.target === rejectOverlay) {
    closeRejectModal();
  }
  const rejectedOverlay = document.getElementById('rejected-modal-overlay');
  if (e.target === rejectedOverlay) {
    closeRejectedMissionsModal();
  }
  const approvedOverlay = document.getElementById('approved-modal-overlay');
  if (e.target === approvedOverlay) {
    closeApprovedMissionsModal();
  }
  const pendingOverlay = document.getElementById('pending-modal-overlay');
  if (e.target === pendingOverlay) {
    closePendingMissionsModal();
  }
  const processingOverlay = document.getElementById('processing-modal-overlay');
  if (e.target === processingOverlay) {
    closeProcessingAgentsModal();
  }
  const settingsOverlay = document.getElementById('settings-modal-overlay');
  if (e.target === settingsOverlay) {
    closeSettingsModal();
  }
  const oracleOverlay = document.getElementById('oracle-modal-overlay');
  if (e.target === oracleOverlay) {
    closeOracleModal();
  }
});

// ══════════════════════════════════════════════════════════════════
// ── ORÁCULO & MEMÓRIA VIVA HANDLERS ───────────────────────────────
// ══════════════════════════════════════════════════════════════════

function openOracleModal() {
  const overlay = document.getElementById('oracle-modal-overlay');
  if (overlay) overlay.classList.add('active');
  loadOracleChatHistory();
  loadKnowledgeGaps();
  loadOracleFacts();
}

function closeOracleModal() {
  const overlay = document.getElementById('oracle-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function switchOracleTab(tabName) {
  document.querySelectorAll('.oracle-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.oracle-tab-pane').forEach(pane => pane.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.oracle-tab-btn')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabName));
  if (activeBtn) activeBtn.classList.add('active');

  const pane = document.getElementById('oracle-tab-' + tabName);
  if (pane) pane.classList.add('active');

  if (tabName === 'gaps') loadKnowledgeGaps();
  if (tabName === 'facts') loadOracleFacts();
}

function handleOracleKeyPress(e) {
  if (e.key === 'Enter') {
    sendOracleMessage();
  }
}

async function loadOracleChatHistory() {
  if (!isOnline) return;
  try {
    const res = await fetch(API_BASE + '/api/oracle/chat');
    const messages = await res.json();
    const box = document.getElementById('oracle-messages-list');
    if (!box) return;

    if (messages && messages.length > 0) {
      box.innerHTML = messages.map(m => `
        <div class="oracle-msg-bubble ${m.sender}">
          <div class="oracle-msg-header">${m.sender === 'user' ? '👤 Você' : '🤖 Oráculo'} ${m.created_at ? '• ' + m.created_at : ''}</div>
          <div class="oracle-msg-text">${m.message.replace(/\n/g, '<br>')}</div>
        </div>
      `).join('');
      box.scrollTop = box.scrollHeight;
    }
  } catch (e) {
    console.error('Erro ao carregar chat do oráculo:', e);
  }
}

async function sendOracleMessage() {
  const input = document.getElementById('oracle-input-text');
  if (!input) return;
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  const box = document.getElementById('oracle-messages-list');

  // Adiciona bolha do usuário imediatamente
  const userBubble = document.createElement('div');
  userBubble.className = 'oracle-msg-bubble user';
  userBubble.innerHTML = `
    <div class="oracle-msg-header">👤 Você</div>
    <div class="oracle-msg-text">${question}</div>
  `;
  box.appendChild(userBubble);

  // Adiciona bolha de pensando
  const loadingBubble = document.createElement('div');
  loadingBubble.className = 'oracle-msg-bubble oracle';
  loadingBubble.id = 'oracle-loading-msg';
  loadingBubble.innerHTML = `
    <div class="oracle-msg-header">🤖 Oráculo</div>
    <div class="oracle-msg-text"><em>Consultando memórias e cruzando conversas... 🧠</em></div>
  `;
  box.appendChild(loadingBubble);
  box.scrollTop = box.scrollHeight;

  if (isOnline) {
    try {
      const res = await fetch(API_BASE + '/api/oracle/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      });
      const data = await res.json();
      
      const loadEl = document.getElementById('oracle-loading-msg');
      if (loadEl) loadEl.remove();

      const answerBubble = document.createElement('div');
      answerBubble.className = 'oracle-msg-bubble oracle';
      answerBubble.innerHTML = `
        <div class="oracle-msg-header">🤖 Oráculo ${data.timestamp ? '• ' + data.timestamp : ''}</div>
        <div class="oracle-msg-text">${(data.answer || '').replace(/\n/g, '<br>')}</div>
      `;
      box.appendChild(answerBubble);
      box.scrollTop = box.scrollHeight;
    } catch (e) {
      console.error(e);
      const loadEl = document.getElementById('oracle-loading-msg');
      if (loadEl) {
        loadEl.innerHTML = `
          <div class="oracle-msg-header">🤖 Oráculo</div>
          <div class="oracle-msg-text" style="color: #f87171;">Erro ao processar resposta com o servidor.</div>
        `;
      }
    }
  } else {
    setTimeout(() => {
      const loadEl = document.getElementById('oracle-loading-msg');
      if (loadEl) {
        loadEl.innerHTML = `
          <div class="oracle-msg-header">🤖 Oráculo</div>
          <div class="oracle-msg-text">[DEMO] Resposta simulada baseada nas conversas registradas.</div>
        `;
      }
    }, 600);
  }
}

async function loadKnowledgeGaps() {
  if (!isOnline) return;
  try {
    const res = await fetch(API_BASE + '/api/oracle/gaps');
    const gaps = await res.json();
    const listEl = document.getElementById('oracle-gaps-list');
    const badgeEl = document.getElementById('oracle-gaps-badge');
    if (!listEl) return;

    const pendingCount = gaps.filter(g => g.status === 'pending').length;
    if (badgeEl) badgeEl.textContent = pendingCount;

    if (!gaps || gaps.length === 0) {
      listEl.innerHTML = '<div style="color: #94a3b8; padding: 20px; text-align: center;">🎉 Nenhuma dúvida pendente! A IA compreendeu todos os termos das conversas.</div>';
      return;
    }

    listEl.innerHTML = gaps.map(g => {
      const isPending = (g.status === 'pending');
      return `
        <div class="gap-card ${isPending ? '' : 'resolved'}" id="gap-card-${g.id}">
          <div class="gap-card-header">
            <span class="gap-term-badge">❓ ${g.term}</span>
            <span style="font-size: 11px; color: ${isPending ? '#f87171' : '#4ade80'}; font-weight: 700;">
              ${isPending ? '● Aguardando sua explicação' : '✅ Aprendido'}
            </span>
          </div>
          <div style="font-size: 12px; color: #cbd5e1;">${g.question}</div>
          <div style="font-size: 10px; color: #64748b;">Detectado em: ${g.detected_in || 'Conversas recentes'}</div>
          
          ${isPending ? `
            <div class="gap-input-row">
              <input type="text" id="gap-answer-input-${g.id}" placeholder="Explique o que é este termo...">
              <button class="btn-teach-gap" onclick="submitGapAnswer(${g.id})">
                <span>🎓 Ensinar</span>
              </button>
            </div>
          ` : `
            <div style="font-size: 11.5px; color: #86efac; background: rgba(34,197,94,0.1); padding: 8px 12px; border-radius: 8px; margin-top: 4px;">
              <strong>Você ensinou:</strong> ${g.learned_definition}
            </div>
          `}
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Erro ao carregar dúvidas:', e);
  }
}

async function submitGapAnswer(gapId) {
  const input = document.getElementById('gap-answer-input-' + gapId);
  if (!input) return;
  const answer = input.value.trim();
  if (!answer) {
    showToast('⚠️ Digite a definição do termo para ensinar a IA.', 'error');
    return;
  }

  showToast('🧠 Ensinando a IA e salvando na Base de Conhecimento...', 'info');

  try {
    const res = await fetch(API_BASE + '/api/oracle/gaps/' + gapId + '/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: answer })
    });
    const data = await res.json();
    showToast('✅ ' + data.message, 'success');
    appendFeedItem({
      color: '#10b981',
      agent: 'Você (Humano)',
      text: 'Ensinou o Oráculo sobre o termo <strong>' + (data.gap ? data.gap.term : '') + '</strong> com sucesso.'
    });
    loadKnowledgeGaps();
  } catch (e) {
    console.error(e);
    showToast('❌ Erro ao enviar resposta.', 'error');
  }
}

async function loadOracleFacts() {
  if (!isOnline) return;
  try {
    const res = await fetch(API_BASE + '/api/oracle/facts');
    const facts = await res.json();
    const listEl = document.getElementById('oracle-facts-list');
    if (!listEl) return;

    if (!facts || facts.length === 0) {
      listEl.innerHTML = '<div style="color: #94a3b8; padding: 20px; text-align: center;">Nenhum fato minerado ainda. Cole uma conversa na aba "Minerar Texto" para começar!</div>';
      return;
    }

    listEl.innerHTML = facts.map(f => `
      <div class="fact-item-card">
        <div class="fact-badge-row">
          <span class="fact-category-tag">${f.category}</span>
          <span style="font-size: 11px; font-weight: 700; color: #f8fafc;">${f.subject}</span>
          <span style="font-size: 11px; color: #94a3b8;">${f.relation}</span>
          <span style="font-size: 11px; color: #38bdf8; font-weight: 600;">${f.object_value}</span>
        </div>
        <div style="font-size: 11.5px; color: #cbd5e1; margin-top: 4px;">${f.context_summary}</div>
        <div style="font-size: 10px; color: #64748b; margin-top: 2px;">
          Fonte: <strong>${f.source_person}</strong> (${f.source_channel}) • ${f.created_at}
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Erro ao carregar fatos:', e);
  }
}

async function submitCustomMining() {
  const person = document.getElementById('mine-input-person').value.trim() || 'Contato';
  const channel = document.getElementById('mine-input-channel').value;
  const text = document.getElementById('mine-input-text').value.trim();

  if (!text) {
    showToast('⚠️ Cole o texto da conversa para minerar.', 'error');
    return;
  }

  showToast('🔍 Agente Minerador analisando texto e extraindo fatos...', 'info');

  try {
    const res = await fetch(API_BASE + '/api/oracle/mine-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, person: person, channel: channel })
    });
    const data = await res.json();
    showToast(`✅ Mineração concluída! ${data.facts_extracted || 0} fatos salvos e ${data.gaps_found || 0} dúvidas geradas.`, 'success');
    document.getElementById('mine-input-text').value = '';
    switchOracleTab('facts');
  } catch (e) {
    console.error(e);
    showToast('❌ Erro ao minerar texto.', 'error');
  }
}

// ══════════════════════════════════════════════════════════════════
// ── ONBOARDING DE PRIMEIRA EXECUÇÃO ──────────────────────────────
// ══════════════════════════════════════════════════════════════════

async function checkOnboardingStatus() {
  if (localStorage.getItem('agentquest_onboarding_dismissed') === 'true') return;

  try {
    const res = await API.getOnboardingStatus();
    if (res.needs_onboarding) {
      showOnboardingModal();
    }
  } catch (e) {
    console.warn('Falha ao checar status de onboarding:', e);
  }
}

function showOnboardingModal() {
  const overlay = document.getElementById('onboarding-modal-overlay');
  if (overlay) overlay.classList.add('active');
}

function dismissOnboarding() {
  localStorage.setItem('agentquest_onboarding_dismissed', 'true');
  const overlay = document.getElementById('onboarding-modal-overlay');
  if (overlay) overlay.classList.remove('active');
  showToast('⚠️ Configure sua chave de IA depois em Configurações → Provedores de IA.', 'info');
}

async function submitOnboarding() {
  const input = document.getElementById('onboarding-gemini-key');
  const key = input ? input.value.trim() : '';
  const msgBox = document.getElementById('onboarding-msg-box');
  const btn = document.getElementById('btn-onboarding-submit');

  if (!key) {
    showToast('⚠️ Cole sua chave da API Gemini para continuar.', 'error');
    return;
  }

  if (btn) btn.disabled = true;
  if (msgBox) {
    msgBox.style.display = 'block';
    msgBox.className = 'ai-status-message-box';
    msgBox.textContent = '⏳ Validando chave...';
  }

  try {
    const res = await API.saveOnboarding(key);
    // Cota esgotada (429) indica chave válida com limite temporário atingido —
    // a chave serve, então o onboarding não deve prender o usuário aqui.
    const isQuotaOnly = res.status === 'rate_limited' || res.status === 'quota_exhausted';
    const keyAccepted = (res.success && res.status === 'online') || isQuotaOnly;

    if (msgBox) {
      msgBox.className = 'ai-status-message-box ' + (keyAccepted ? (isQuotaOnly ? 'warning' : 'success') : 'error');
      msgBox.textContent = (keyAccepted ? (isQuotaOnly ? '⚠️ ' : '✅ ') : '❌ ')
        + (res.message || (keyAccepted ? 'Chave validada com sucesso!' : 'Não foi possível validar a chave.'));
    }

    if (keyAccepted) {
      localStorage.removeItem('agentquest_onboarding_dismissed');
      showToast(isQuotaOnly
        ? '⚠️ Chave salva! A cota do plano gratuito está no limite no momento.'
        : '🎉 Configuração concluída! Bem-vindo ao AgentQuest HQ.',
        isQuotaOnly ? 'info' : 'success');
      setTimeout(() => {
        const overlay = document.getElementById('onboarding-modal-overlay');
        if (overlay) overlay.classList.remove('active');
        loadSettings();
      }, isQuotaOnly ? 2200 : 1200);
    }
  } catch (e) {
    console.error(e);
    if (msgBox) {
      msgBox.className = 'ai-status-message-box error';
      msgBox.textContent = '❌ Erro ao salvar. Verifique sua conexão e tente novamente.';
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ══════════════════════════════════════════════════════════════════
// ── ABA CHANNELS: STATUS & QR CODE DO WHATSAPP ───────────────────
// ══════════════════════════════════════════════════════════════════

let whatsappStatusPollTimer = null;

function toggleWhatsAppProviderFields(trocaDoUsuario = false) {
  const select = document.getElementById('cfg-wa-provider');
  if (!select) return;
  const provider = select.value;

  const blocos = {
    baileys: 'cfg-wa-fields-baileys',
    meta_official: 'cfg-wa-fields-meta',
    evolution: 'cfg-wa-fields-evolution',
    mock: 'cfg-wa-fields-mock'
  };

  Object.entries(blocos).forEach(([nome, id]) => {
    const el = document.getElementById(id);
    if (el) el.style.display = (nome === provider) ? 'block' : 'none';
  });

  // O botão de conectar só faz sentido em provedores que mantêm sessão
  const btn = document.getElementById('btn-wa-connect');
  if (btn) {
    btn.style.display = (provider === 'mock') ? 'none' : 'inline-flex';
    btn.innerHTML = (provider === 'meta_official')
      ? '<span class="refresh-icon">🔍</span> Validar Credenciais'
      : '<span class="refresh-icon">📡</span> Conectar WhatsApp';
  }

  // Só Baileys e Evolution pareiam por QR — ao trocar de provedor, o QR
  // exibido antes deixa de fazer sentido e some junto com o polling.
  if (provider !== 'baileys' && provider !== 'evolution') {
    const qrBox = document.getElementById('wa-qr-box');
    if (qrBox) qrBox.style.display = 'none';
    if (whatsappStatusPollTimer) {
      clearInterval(whatsappStatusPollTimer);
      whatsappStatusPollTimer = null;
    }
  }

  // O endpoint de status responde pelo provedor SALVO. Se o usuário acabou de
  // trocar o select e ainda não salvou, mostrar o status antigo enganaria —
  // então pedimos para salvar em vez de exibir dado de outro provedor.
  const salvo = (globalSettings?.channels?.whatsapp?.provider) || null;
  const dotEl = document.getElementById('wa-status-dot');
  const labelEl = document.getElementById('wa-status-label');

  if (trocaDoUsuario && salvo && salvo !== provider) {
    if (dotEl) dotEl.className = 'status-pulse-dot warning';
    if (labelEl) labelEl.textContent = '⚠️ Salve as configurações para aplicar este provedor';
  } else if (dotEl) {
    setTimeout(() => checkWhatsAppStatus(), 50);
  }
}

async function checkWhatsAppStatus() {
  const dotEl = document.getElementById('wa-status-dot');
  const labelEl = document.getElementById('wa-status-label');
  const qrBox = document.getElementById('wa-qr-box');
  const qrImg = document.getElementById('wa-qr-image');
  const dockerWarning = document.getElementById('wa-docker-warning');
  const connectBtn = document.getElementById('btn-wa-connect');

  if (!dotEl) return;

  dotEl.className = 'status-pulse-dot loading';
  if (labelEl) labelEl.textContent = 'Verificando...';

  try {
    const res = await API.getWhatsAppStatus();
    const provider = res.provider || 'baileys';

    // O aviso de Docker só se aplica ao provedor Evolution
    const faltaDocker = provider === 'evolution' && (!res.docker_installed || !res.docker_running);
    if (dockerWarning) dockerWarning.style.display = faltaDocker ? 'block' : 'none';
    if (connectBtn) connectBtn.disabled = faltaDocker;

    let statusClass = 'warning';
    let label = '🟡 Verificando...';

    if (provider === 'mock') {
      statusClass = 'online';
      label = '🟢 Modo link wa.me — envio manual em 1 clique';
      if (qrBox) qrBox.style.display = 'none';
    } else if (provider === 'meta_official') {
      if (res.instance_state === 'open') {
        statusClass = 'online';
        const num = res.connected_number ? ` (${res.connected_number})` : '';
        label = `🟢 Conectado via Meta Cloud API${num}`;
      } else {
        statusClass = 'error';
        label = '🔴 Credenciais da Meta não validadas';
      }
      if (qrBox) qrBox.style.display = 'none';
    } else if (provider === 'baileys') {
      if (!res.node_installed) {
        statusClass = 'error';
        label = '🔴 Node.js não encontrado — ponte indisponível';
      } else if (!res.bridge_running) {
        statusClass = 'warning';
        label = '🟡 Ponte de WhatsApp parada — clique em Conectar';
      } else if (res.instance_state === 'open') {
        statusClass = 'online';
        const num = res.connected_number ? ` (${res.connected_number})` : '';
        label = `🟢 WhatsApp conectado${num}`;
        if (qrBox) qrBox.style.display = 'none';
      } else if (res.instance_state === 'connecting') {
        statusClass = 'warning';
        label = '🟠 Aguardando pareamento — escaneie o QR Code';
      } else {
        statusClass = 'warning';
        label = '🟡 Ponte ativa, sem conta pareada — clique em Conectar';
      }
    } else {
      // Evolution
      if (!res.docker_installed) {
        statusClass = 'error';
        label = '🔴 Docker Desktop não encontrado';
      } else if (!res.docker_running) {
        statusClass = 'warning';
        label = '🟡 Docker Desktop parado';
      } else if (!res.evolution_reachable) {
        statusClass = 'warning';
        label = '🟡 Evolution API iniciando...';
      } else if (res.instance_state === 'open') {
        statusClass = 'online';
        label = '🟢 WhatsApp conectado';
        if (qrBox) qrBox.style.display = 'none';
      } else if (res.instance_state === 'connecting') {
        statusClass = 'warning';
        label = '🟠 Aguardando pareamento (escaneie o QR Code)';
      } else {
        statusClass = 'online';
        label = '🟢 Evolution API online — clique em Conectar';
      }
    }

    dotEl.className = 'status-pulse-dot ' + statusClass;
    if (labelEl) labelEl.textContent = label;

    if (res.instance_state === 'open') {
      // Conectou: para o polling e esconde o QR
      if (whatsappStatusPollTimer) {
        clearInterval(whatsappStatusPollTimer);
        whatsappStatusPollTimer = null;
      }
      if (qrBox) qrBox.style.display = 'none';
    } else if (res.instance_state === 'connecting' && qrBox && qrBox.style.display !== 'none') {
      // O QR do WhatsApp expira em poucos segundos e o provedor emite um novo.
      // Sem rebuscar a cada ciclo, a tela mostraria um QR morto e o pareamento
      // nunca completaria.
      try {
        const novo = await API.peekWhatsAppQR();
        if (novo.status === 'qr_ready' && novo.qr_base64 && qrImg) {
          qrImg.src = novo.qr_base64;
        } else if (novo.status === 'already_connected') {
          if (qrBox) qrBox.style.display = 'none';
        }
      } catch (e) {
        console.warn('Falha ao renovar o QR Code:', e);
      }
    }
  } catch (e) {
    console.warn('Falha ao checar status do WhatsApp:', e);
    dotEl.className = 'status-pulse-dot error';
    if (labelEl) labelEl.textContent = '🔴 Erro ao consultar status';
  }
}

async function connectWhatsApp() {
  const qrBox = document.getElementById('wa-qr-box');
  const qrImg = document.getElementById('wa-qr-image');
  const connectBtn = document.getElementById('btn-wa-connect');

  if (connectBtn) connectBtn.disabled = true;
  showToast('📡 Conectando ao WhatsApp...', 'info');

  try {
    const res = await API.connectWhatsApp();

    if (res.status === 'qr_ready' && res.qr_base64) {
      if (qrBox) qrBox.style.display = 'block';
      if (qrImg) qrImg.src = res.qr_base64;
      showToast('📱 Escaneie o QR Code com o WhatsApp do celular.', 'info');

      if (whatsappStatusPollTimer) clearInterval(whatsappStatusPollTimer);
      whatsappStatusPollTimer = setInterval(checkWhatsAppStatus, 3000);
    } else if (res.status === 'already_connected') {
      showToast('✅ WhatsApp já está conectado!', 'success');
      checkWhatsAppStatus();
    } else {
      showToast('❌ ' + (res.message || 'Não foi possível conectar.'), 'error');
    }
  } catch (e) {
    console.error(e);
    showToast('❌ Erro ao conectar ao WhatsApp.', 'error');
  } finally {
    if (connectBtn) connectBtn.disabled = false;
  }
}

window.addEventListener('DOMContentLoaded', initApp);



function generateAI(id, btnElement) {
  if (!isOnline) {
    showToast('❌ Backend offline. Não é possível gerar IA no modo demo.', 'error');
    return;
  }
  
  btnElement.disabled = true;
  btnElement.innerHTML = '⏳ Gerando...';
  btnElement.style.opacity = '0.7';
  
  fetch(API_BASE + '/api/missions/' + id + '/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(res => {
    if (!res.ok) throw new Error('Erro na geração da IA');
    return res.json();
  })
  .then(data => {
    showToast('✨ Resposta gerada pela IA com sucesso!', 'success');
    forceFeedUpdate();
  })
  .catch(err => {
    console.error(err);
    showToast('❌ Erro ao gerar resposta IA.', 'error');
    btnElement.disabled = false;
    btnElement.innerHTML = '🪄 Gerar Resposta IA';
    btnElement.style.opacity = '1';
  });
}

function forceFeedUpdate() {
  if (isOnline) {
    API.getMissions().then(missions => {
      const list = document.getElementById('missions-list');
      if (list) list.innerHTML = '';
      missions.forEach(m => addMissionCardWithId(m.id, m));
    });
  }
}
