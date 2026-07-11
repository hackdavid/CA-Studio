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

function useRule(ruleId) {
  openNewSessionModalWithRule(ruleId);
}

// ─── Init ──────────────────────────────────────────────────────────────────
function initMetricsPage() {
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
