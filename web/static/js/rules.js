/**
 * CA Lab Rule Library Controller
 */

// ─── State ─────────────────────────────────────────────────────────────────
let allRules = [];
let allCategories = [];
let searchQuery = '';
let selectedCategory = 'all';

// ─── Compatibility with builder scripts ──────────────────────────────────────
// The rule-builder.js calls loadDashboard() after save/delete.
// We alias it so the builder works on this page without modification.
function loadDashboard() {
  loadRulesPage();
}

// No-op functions for modal rendering that the builder expects
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
async function loadRulesPage() {
  try {
    const [rulesRes, categoriesRes] = await Promise.all([
      api.get('/api/rules/'),
      api.get('/api/rules/categories/list'),
    ]);
    allRules = rulesRes;
    allCategories = categoriesRes || [];
    renderCategoryPills();
    renderRuleGrid();
    renderSidebarNav();
  } catch (e) {
    toast('Failed to load rules: ' + e.message, 'error');
  }
}

// ─── Category Pills ────────────────────────────────────────────────────────
function renderCategoryPills() {
  const container = document.getElementById('category-pills');
  if (!container) return;

  const pills = [
    { key: 'all', label: 'All Rules', count: allRules.length },
    ...allCategories.map(cat => ({
      key: cat,
      label: cat.charAt(0).toUpperCase() + cat.slice(1),
      count: allRules.filter(r => (r.category || 'experimental') === cat).length,
    })),
  ];

  container.innerHTML = pills.map(p => {
    const active = selectedCategory === p.key;
    return `
      <button onclick="selectCategory('${p.key}')" class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${active ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-slate-600 border-slate-200 hover:border-primary-300 hover:text-primary-700'}">
        ${p.label} <span class="${active ? 'text-primary-200' : 'text-slate-400'}">${p.count}</span>
      </button>
    `;
  }).join('');
}

function selectCategory(cat) {
  selectedCategory = cat;
  renderCategoryPills();
  renderRuleGrid();
}

// ─── Search ─────────────────────────────────────────────────────────────────
function onSearchInput(value) {
  searchQuery = value.trim().toLowerCase();
  renderRuleGrid();
}

// ─── Rule Grid Rendering ───────────────────────────────────────────────────
function renderRuleGrid() {
  const container = document.getElementById('rules-grid');
  if (!container) return;

  let filtered = allRules.filter(r => {
    const matchesSearch = !searchQuery || r.name.toLowerCase().includes(searchQuery) || (r.description || '').toLowerCase().includes(searchQuery);
    const matchesCategory = selectedCategory === 'all' || (r.category || 'experimental') === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (!filtered.length) {
    container.innerHTML = `
      <div class="col-span-full text-center py-12">
        <div class="text-4xl mb-3">📐</div>
        <p class="text-sm font-semibold text-slate-600">No rules found</p>
        <p class="text-xs text-slate-400 mt-1">Try a different search or category filter</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(rule => {
    const states = getRuleStates(rule);
    const hood = (rule.yaml_content?.match(/neighbourhood:\s*(\w+)/)?.[1]) || 'moore8';
    const builtIn = rule.is_builtin;
    const editable = rule.is_editable;
    const thumbColor = builtIn ? 'from-primary-200 to-blue-200' : 'from-accent-200 to-green-200';
    const thumbIcon = builtIn ? '🔒' : '✎';

    return `
      <div class="featured-card bg-white rounded-2xl p-5 border border-slate-200 flex flex-col h-full">
        <div class="w-full h-28 rounded-xl bg-gradient-to-br ${thumbColor} mb-4 flex items-center justify-center text-3xl">${thumbIcon}</div>
        <div class="flex items-start justify-between gap-2 mb-1">
          <h3 class="font-bold text-sm text-slate-900 leading-tight">${rule.name}</h3>
          <span class="flex-shrink-0 px-2 py-0.5 text-[10px] rounded-full font-bold ${builtIn ? 'bg-primary-100 text-primary-700' : 'bg-accent-100 text-accent-700'}">
            ${builtIn ? 'Built-in' : 'Custom'}
          </span>
        </div>
        <p class="text-xs text-slate-500 mb-1">${states} states · ${hood}</p>
        <p class="text-xs text-slate-400 mb-4 flex-1 line-clamp-2">${rule.description || 'Cellular automaton rule'}</p>
        <div class="flex items-center gap-1.5 mb-3">
          <span class="px-2 py-0.5 text-[10px] rounded-md bg-slate-100 text-slate-600 font-medium">${rule.category || 'experimental'}</span>
        </div>
        <div class="flex gap-2 mt-auto">
          <button onclick="useRule(${rule.id})" class="flex-1 px-3 py-2 bg-white border-2 border-primary-600 text-primary-700 text-xs font-bold rounded-lg hover:bg-primary-600 hover:text-white transition-all">
            Use
          </button>
          ${editable ? `
            <button onclick="editRule(${rule.id})" class="px-3 py-2 bg-slate-100 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-200 transition-colors">
              Edit
            </button>
            <button onclick="deleteRulePage(${rule.id})" class="px-3 py-2 bg-slate-100 text-red-600 text-xs font-bold rounded-lg hover:bg-red-50 transition-colors">
              Del
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// ─── Helpers ─────────────────────────────────────────────────────────────
function getRuleStates(rule) {
  if (!rule?.yaml_content) return 2;
  const statesMatch = rule.yaml_content.match(/^states:\s*(\d+)/m);
  if (statesMatch) return parseInt(statesMatch[1], 10);
  const numStatesMatch = rule.yaml_content.match(/^num_states:\s*(\d+)/m);
  if (numStatesMatch) return parseInt(numStatesMatch[1], 10);
  return 2;
}

function useRule(ruleId) {
  // Pre-select rule and open New Session modal
  const rule = allRules.find(r => r.id === ruleId);
  if (!rule) return;
  selectedRuleId = ruleId;
  statesManuallyEdited = false;
  openNewSessionModal();
  setTimeout(() => {
    selectRule(ruleId);
    document.getElementById('session-name-input')?.focus();
  }, 50);
}

async function deleteRulePage(ruleId) {
  if (!confirm('Delete this rule? It cannot be used by any session.')) return;
  try {
    await api.delete(`/api/rules/${ruleId}`);
    toast('Rule deleted', 'success');
    await loadRulesPage();
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}

// ─── Sidebar Nav ───────────────────────────────────────────────────────────
function renderSidebarNav() {
  const activeCount = allRules.filter(r => !r.is_builtin).length;
  const badge = document.getElementById('nav-rules-count');
  if (badge) {
    if (activeCount > 0) {
      badge.textContent = String(activeCount);
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }
}

// ─── New Session Modal Helpers (mirrored from dashboard.js) ────────────────
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
  const q = query.trim().toLowerCase();
  const filtered = allRules.filter(r => r.name.toLowerCase().includes(q));

  if (!allRules.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">No rules available</p>';
    return;
  }
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
}

function toggleMetric(name, checked) {
  if (checked) selectedMetricNames.add(name);
  else selectedMetricNames.delete(name);
}

function renderModalMetricsData(query = '') {
  const container = document.getElementById('modal-metrics-list');
  if (!container) return;
  const q = query.trim().toLowerCase();
  // Metrics aren't loaded on this page, fetch minimal set
  container.innerHTML = '<p class="text-sm text-slate-500 text-center py-3">Loading metrics...</p>';
  api.get('/api/metrics/').then(metrics => {
    const filtered = metrics.filter(m => m.name.toLowerCase().includes(q) || (m.description || '').toLowerCase().includes(q));
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
  });
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
function initRulesPage() {
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
  loadRulesPage();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRulesPage);
} else {
  initRulesPage();
}
