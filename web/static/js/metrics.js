/**
 * CA Lab Metrics Library Controller
 */

// ─── State ─────────────────────────────────────────────────────────────────
let allMetrics = [];
let searchQuery = '';
let selectedType = 'all';

// ─── Compatibility with builder scripts ──────────────────────────────────────
function loadDashboard() {
  loadMetricsPage();
}

function renderModalRules() {}
function renderModalMetrics() {}
function renderModalSessions() {}

// ─── Sidebar helpers (shared with dashboard) ───────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('dashboard-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;
  sidebar.classList.toggle('-translate-x-full');
  if (overlay) overlay.classList.toggle('hidden');
}
function closeSidebar() {
  const sidebar = document.getElementById('dashboard-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.add('-translate-x-full');
  if (overlay) overlay.classList.add('hidden');
}

// ─── Data Loading ───────────────────────────────────────────────────────────
async function loadMetricsPage() {
  try {
    allMetrics = await api.get('/api/metrics/');
    renderTypePills();
    renderMetricList();
    renderSidebarNav();
  } catch (e) {
    toast('Failed to load metrics: ' + e.message, 'error');
  }
}

// ─── Type Pills ────────────────────────────────────────────────────────────
function renderTypePills() {
  const container = document.getElementById('type-pills');
  if (!container) return;

  const builtInCount = allMetrics.filter(m => m.is_builtin).length;
  const customCount = allMetrics.filter(m => !m.is_builtin).length;

  const pills = [
    { key: 'all', label: 'All Metrics', count: allMetrics.length },
    { key: 'builtin', label: 'Built-in', count: builtInCount },
    { key: 'custom', label: 'Custom', count: customCount },
  ];

  container.innerHTML = pills.map(p => {
    const active = selectedType === p.key;
    return `
      <button onclick="selectType('${p.key}')" class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${active ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-slate-600 border-slate-200 hover:border-primary-300 hover:text-primary-700'}">
        ${p.label} <span class="${active ? 'text-primary-200' : 'text-slate-400'}">${p.count}</span>
      </button>
    `;
  }).join('');
}

function selectType(type) {
  selectedType = type;
  renderTypePills();
  renderMetricList();
}

// ─── Search ─────────────────────────────────────────────────────────────────
function onSearchInput(value) {
  searchQuery = value.trim().toLowerCase();
  renderMetricList();
}

// ─── Metric List Rendering ──────────────────────────────────────────────────
function renderMetricList() {
  const container = document.getElementById('metrics-list');
  if (!container) return;

  let filtered = allMetrics.filter(m => {
    const matchesSearch = !searchQuery || m.name.toLowerCase().includes(searchQuery) || (m.description || '').toLowerCase().includes(searchQuery);
    const matchesType = selectedType === 'all' || (selectedType === 'builtin' && m.is_builtin) || (selectedType === 'custom' && !m.is_builtin);
    return matchesSearch && matchesType;
  });

  if (!filtered.length) {
    container.innerHTML = `
      <div class="text-center py-12">
        <div class="text-4xl mb-3">📊</div>
        <p class="text-sm font-semibold text-slate-600">No metrics found</p>
        <p class="text-xs text-slate-400 mt-1">Try a different search or type filter</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(metric => {
    const builtIn = metric.is_builtin;
    const typeLabel = metric.metric_type || (metric.formula ? 'formula' : 'custom');
    const formulaSnippet = metric.formula || metric.metric_type || '—';
    const barColor = builtIn ? 'bg-primary-500' : 'bg-accent-500';

    return `
      <div class="featured-card bg-white rounded-2xl p-4 lg:p-5 border border-slate-200 flex flex-col sm:flex-row sm:items-center gap-4">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <h3 class="font-bold text-sm text-slate-900">${metric.name}</h3>
            <span class="px-2 py-0.5 text-[10px] rounded-full font-bold ${builtIn ? 'bg-primary-100 text-primary-700' : 'bg-accent-100 text-accent-700'}">
              ${builtIn ? 'Built-in' : 'Custom'}
            </span>
            <span class="px-2 py-0.5 text-[10px] rounded-md bg-slate-100 text-slate-600 font-medium uppercase">${typeLabel}</span>
          </div>
          <p class="text-xs text-slate-500 mb-2">${metric.description || 'CA metric'}</p>
          <div class="inline-flex items-center gap-2 px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Formula</span>
            <code class="text-xs font-mono text-slate-700">${formulaSnippet}</code>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          ${!builtIn ? `
            <button onclick="editMetric(${metric.id})" class="px-3 py-2 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-50 transition-colors">
              Edit
            </button>
            <button onclick="deleteMetricPage(${metric.id})" class="px-3 py-2 bg-white border border-red-200 text-red-600 text-xs font-bold rounded-lg hover:bg-red-50 transition-colors">
              Delete
            </button>
          ` : `
            <span class="text-xs text-slate-400 italic">Built-in</span>
          `}
        </div>
      </div>
    `;
  }).join('');
}

// ─── Actions ───────────────────────────────────────────────────────────────
async function deleteMetricPage(metricId) {
  if (!confirm('Delete this metric?')) return;
  try {
    await api.delete(`/api/metrics/${metricId}`);
    toast('Metric deleted', 'success');
    await loadMetricsPage();
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}

// ─── Sidebar Nav ───────────────────────────────────────────────────────────
function renderSidebarNav() {
  const customCount = allMetrics.filter(m => !m.is_builtin).length;
  const badge = document.getElementById('nav-metrics-count');
  if (badge) {
    if (customCount > 0) {
      badge.textContent = String(customCount);
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }
}

// ─── New Session Modal Helpers ─────────────────────────────────────────────
let selectedRuleId = null;
let selectedMetricNames = new Set(['density', 'entropy']);
let statesManuallyEdited = false;

function openNewSessionModal() {
  const search = document.getElementById('modal-rule-search');
  if (search) search.value = '';
  const metricSearch = document.getElementById('modal-metric-search');
  if (metricSearch) metricSearch.value = '';
  statesManuallyEdited = false;
  renderModalRulesData();
  renderModalMetricsData();
  document.getElementById('newSessionModal')?.classList.remove('hidden');
  document.getElementById('session-name-input')?.focus();
}

function closeNewSessionModal() {
  document.getElementById('newSessionModal')?.classList.add('hidden');
}

function selectRule(ruleId) {
  selectedRuleId = ruleId;
  document.querySelectorAll('#modal-rule-list .rule-option').forEach(el => {
    const active = parseInt(el.dataset.ruleId, 10) === ruleId;
    el.className = active
      ? 'rule-option px-3 py-2 bg-primary-50 border border-primary-400 ring-1 ring-primary-300 rounded-lg cursor-pointer transition-colors'
      : 'rule-option px-3 py-2 bg-white border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors';
  });
  updateNumStatesFromRule();
}

function getRuleStates(rule) {
  if (!rule?.yaml_content) return 2;
  const statesMatch = rule.yaml_content.match(/^states:\s*(\d+)/m);
  if (statesMatch) return parseInt(statesMatch[1], 10);
  const numStatesMatch = rule.yaml_content.match(/^num_states:\s*(\d+)/m);
  if (numStatesMatch) return parseInt(numStatesMatch[1], 10);
  return 2;
}

function updateNumStatesFromRule() {
  if (statesManuallyEdited) return;
  const rule = allRules.find(r => r.id === selectedRuleId);
  if (!rule) return;
  const states = getRuleStates(rule);
  const input = document.getElementById('num-states-input');
  if (input) input.value = states;
}

function renderModalRulesData(query = '') {
  const container = document.getElementById('modal-rule-list');
  if (!container) return;
  container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">Loading rules...</p>';
  api.get('/api/rules/').then(rules => {
    allRules = rules;
    const q = query.trim().toLowerCase();
    const filtered = rules.filter(r => r.name.toLowerCase().includes(q));
    if (!filtered.length) {
      container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">No matching rules</p>';
      return;
    }
    if (!selectedRuleId || !filtered.some(r => r.id === selectedRuleId)) {
      selectedRuleId = filtered[0].id;
    }
    container.innerHTML = filtered.map(rule => `
      <div class="rule-option px-3 py-2 border rounded-lg cursor-pointer transition-colors ${rule.id === selectedRuleId ? 'bg-primary-50 border-primary-400 ring-1 ring-primary-300' : 'bg-white border-slate-200 hover:bg-slate-50'}"
           data-rule-id="${rule.id}" onclick="selectRule(${rule.id})">
        <div class="font-semibold text-sm text-slate-900 leading-tight">${rule.name}</div>
        <div class="text-xs text-slate-500 mt-0.5">${rule.is_builtin ? 'Built-in' : 'Custom'} · ${rule.category || 'experimental'}</div>
      </div>
    `).join('');
    updateNumStatesFromRule();
  });
}

function toggleMetric(name, checked) {
  if (checked) selectedMetricNames.add(name);
  else selectedMetricNames.delete(name);
}

function renderModalMetricsData(query = '') {
  const container = document.getElementById('modal-metrics-list');
  if (!container) return;
  const q = query.trim().toLowerCase();
  const filtered = allMetrics.filter(m => m.name.toLowerCase().includes(q) || (m.description || '').toLowerCase().includes(q));

  if (!allMetrics.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">No metrics available</p>';
    return;
  }
  if (!filtered.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">No matching metrics</p>';
    return;
  }

  container.innerHTML = filtered.map(metric => {
    const checked = selectedMetricNames.has(metric.name);
    const badge = metric.is_builtin
      ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-primary-100 text-primary-700 font-medium">Built-in</span>'
      : '<span class="text-[10px] px-1.5 py-0.5 rounded bg-accent-100 text-accent-700 font-medium">Custom</span>';
    return `
      <label class="metric-option flex items-start gap-2.5 px-3 py-2 bg-white border border-slate-200 rounded-lg cursor-pointer hover:border-primary-300 transition-colors">
        <input type="checkbox" class="mt-0.5 w-4 h-4 rounded border-slate-300 text-primary-600"
          data-metric-name="${metric.name}" ${checked ? 'checked' : ''}
          onchange="toggleMetric('${metric.name}', this.checked)">
        <span class="min-w-0 flex-1">
          <span class="flex items-center gap-2">
            <span class="text-sm font-semibold text-slate-900 leading-tight">${metric.name}</span>
            ${badge}
          </span>
          <span class="block text-xs text-slate-500 mt-0.5">${metric.description || 'CA metric'}</span>
        </span>
      </label>
    `;
  }).join('');
}

async function createSession() {
  const name = document.getElementById('session-name-input').value.trim() || 'Untitled Session';
  const width = parseInt(document.getElementById('board-width-input').value, 10) || 64;
  const height = parseInt(document.getElementById('board-height-input').value, 10) || 64;
  const numStates = parseInt(document.getElementById('num-states-input').value, 10) || 2;
  const seedKey = document.getElementById('seed-select').value;
  const seedMap = {
    random_30: { type: 'random', density: 0.3, states: Array.from({ length: numStates - 1 }, (_, i) => i + 1) },
    random_50: { type: 'random', density: 0.5, states: Array.from({ length: numStates - 1 }, (_, i) => i + 1) },
    center: { type: 'single', state: 1, position: 'center' },
    empty: { type: 'empty' },
  };
  const metrics = Array.from(selectedMetricNames);

  if (!selectedRuleId) {
    toast('Please select a rule', 'error');
    return;
  }
  if (numStates < 2 || numStates > 101) {
    toast('Number of states must be between 2 and 101', 'error');
    return;
  }

  try {
    const session = await api.post('/api/sessions/', {
      name,
      rule_id: selectedRuleId,
      board_width: width,
      board_height: height,
      neighbourhood: 'moore8',
      num_states: numStates,
      seed_config: seedMap[seedKey] || { type: 'random', density: 0.3, states: [1] },
      metrics_enabled: metrics.length ? metrics : ['density', 'entropy'],
    });
    closeNewSessionModal();
    window.location.href = `/simulation/${session.id}`;
  } catch (e) {
    toast('Failed to create session: ' + e.message, 'error');
  }
}

// ─── Init ──────────────────────────────────────────────────────────────────
function initMetricsPage() {
  document.getElementById('num-states-input')?.addEventListener('input', () => {
    statesManuallyEdited = true;
  });
  document.getElementById('sidebar-overlay')?.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSidebar();
      closeNewSessionModal();
    }
  });
  loadMetricsPage();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMetricsPage);
} else {
  initMetricsPage();
}
