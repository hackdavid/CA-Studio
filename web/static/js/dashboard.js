/**
 * CA Lab Dashboard Controller
 * Handles data loading, rendering, modals, and responsive interactions.
 */

// ─── Global State ───────────────────────────────────────────────────────────
let allRules = [];
let allSessions = [];
let allMetrics = [];
let sidebarOpen = false;
let activeSessionPollInterval = null;

// ─── Status Helpers ──────────────────────────────────────────────────────────
const statusStyles = {
  running:  { cls: 'bg-green-100 text-green-700 border-green-200', dot: 'bg-green-600 animate-pulse', label: 'Running' },
  paused:   { cls: 'bg-yellow-100 text-yellow-700 border-yellow-200', dot: 'bg-yellow-600', label: 'Paused' },
  stopped:  { cls: 'bg-slate-100 text-slate-600 border-slate-200', dot: 'bg-slate-400', label: 'Stopped' },
  completed:{ cls: 'bg-blue-100 text-blue-700 border-blue-200', dot: 'bg-blue-600', label: 'Completed' },
  created:  { cls: 'bg-slate-100 text-slate-600 border-slate-200', dot: 'bg-slate-400', label: 'Created' },
};

function formatStatus(status) {
  const key = (status || 'paused').toLowerCase();
  const s = statusStyles[key] || statusStyles.paused;
  return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${s.cls}"><span class="w-1.5 h-1.5 rounded-full ${s.dot}"></span>${s.label}</span>`;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function getRuleStates(rule) {
  if (!rule?.yaml_content) return 2;
  const statesMatch = rule.yaml_content.match(/^states:\s*(\d+)/m);
  if (statesMatch) return parseInt(statesMatch[1], 10);
  const numStatesMatch = rule.yaml_content.match(/^num_states:\s*(\d+)/m);
  if (numStatesMatch) return parseInt(numStatesMatch[1], 10);
  return 2;
}

// ─── Sidebar / Responsive ──────────────────────────────────────────────────
function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
  const sb = document.getElementById('dashboard-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebarOpen) {
    sb?.classList.remove('-translate-x-full');
    overlay?.classList.remove('hidden');
  } else {
    sb?.classList.add('-translate-x-full');
    overlay?.classList.add('hidden');
  }
}

function closeSidebar() {
  sidebarOpen = false;
  document.getElementById('dashboard-sidebar')?.classList.add('-translate-x-full');
  document.getElementById('sidebar-overlay')?.classList.add('hidden');
}

// ─── Stats Computation ─────────────────────────────────────────────────────
function computeStats() {
  const total = allSessions.length;
  const active = allSessions.filter(s => s.status === 'running').length;
  const completed = allSessions.filter(s => s.status === 'completed').length;
  const customRules = allRules.filter(r => !r.is_builtin).length;
  const stepsToday = allSessions.reduce((sum, s) => sum + (s.current_step || 0), 0);
  return { total, active, completed, stepsToday, customRules };
}

// ─── KPI Cards ───────────────────────────────────────────────────────────────
function renderKpiCards(stats) {
  const container = document.getElementById('kpi-row');
  if (!container) return;
  const cards = [
    { label: 'Total Experiments', value: stats.total, icon: '🧪', color: 'from-primary-100 to-blue-100', text: 'text-primary-700' },
    { label: 'Active', value: stats.active, icon: '▶', color: 'from-green-100 to-emerald-100', text: 'text-green-700' },
    { label: 'Completed', value: stats.completed, icon: '✓', color: 'from-blue-100 to-indigo-100', text: 'text-blue-700' },
    { label: 'Steps Today', value: stats.stepsToday.toLocaleString(), icon: '⚡', color: 'from-amber-100 to-orange-100', text: 'text-amber-700' },
    { label: 'Custom Rules', value: stats.customRules, icon: '📐', color: 'from-purple-100 to-pink-100', text: 'text-purple-700' },
  ];
  container.innerHTML = cards.map(c => `
    <div class="hover-lift bg-white rounded-2xl p-5 border border-slate-200 cursor-default">
      <div class="flex items-center justify-between mb-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br ${c.color} flex items-center justify-center text-lg">${c.icon}</div>
      </div>
      <div class="text-2xl font-bold text-slate-900 mb-0.5">${c.value}</div>
      <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">${c.label}</div>
    </div>
  `).join('');
}

// ─── Active Sessions ───────────────────────────────────────────────────────
function renderActiveSessions() {
  const container = document.getElementById('active-sessions-grid');
  const sidebarList = document.getElementById('sidebar-active-list');
  if (!container) return;

  const active = allSessions.filter(s => s.status === 'running' || s.status === 'paused');

  // Sidebar mini-list
  if (sidebarList) {
    if (!active.length) {
      sidebarList.innerHTML = '<p class="text-xs text-slate-400 px-2 py-1">No active sessions</p>';
    } else {
      sidebarList.innerHTML = active.slice(0, 5).map(s => {
        const st = statusStyles[s.status] || statusStyles.paused;
        return `
          <div class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors" onclick="loadSession(${s.id})">
            <span class="w-2 h-2 rounded-full ${st.dot} flex-shrink-0"></span>
            <div class="min-w-0">
              <div class="text-xs font-semibold text-slate-800 truncate">${s.name}</div>
              <div class="text-[10px] text-slate-500">${s.board_width}×${s.board_height} · ${s.current_step} stp</div>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // Main grid cards
  if (!active.length) {
    container.innerHTML = `
      <div class="col-span-full text-center py-8">
        <div class="text-4xl mb-2">🔬</div>
        <p class="text-sm text-slate-500 font-medium">No active simulations</p>
        <p class="text-xs text-slate-400 mt-1">Start a new session to see it here</p>
      </div>
    `;
    return;
  }

  container.innerHTML = active.map(s => {
    const st = statusStyles[s.status] || statusStyles.paused;
    const isRun = s.status === 'running';
    return `
      <div class="card bg-white rounded-2xl p-5 border border-slate-200 hover:border-primary-300 transition-all">
        <div class="flex items-start justify-between mb-3">
          <div class="w-16 h-16 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-2xl">🧬</div>
          <span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-bold border ${st.cls}">
            <span class="w-1.5 h-1.5 rounded-full ${st.dot}"></span>${st.label}
          </span>
        </div>
        <h3 class="font-bold text-sm text-slate-900 mb-1 truncate">${s.name}</h3>
        <p class="text-xs text-slate-500 mb-3">${s.rule_name} · ${s.board_width}×${s.board_height}</p>
        <div class="flex items-center justify-between text-xs text-slate-600 mb-3">
          <span>${s.current_step.toLocaleString()} steps</span>
          <span class="text-slate-400">${s.neighbourhood}</span>
        </div>
        <div class="flex gap-2">
          <button onclick="${isRun ? `pauseSession(${s.id})` : `resumeSession(${s.id})`}" class="flex-1 px-3 py-2 ${isRun ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' : 'bg-green-50 text-green-700 border border-green-200'} text-xs font-bold rounded-lg hover:brightness-95 transition-all">
            ${isRun ? '⏸ Pause' : '▶ Resume'}
          </button>
          <button onclick="viewSession(${s.id})" class="px-3 py-2 bg-primary-600 text-white text-xs font-bold rounded-lg hover:bg-primary-700 transition-colors">
            View
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Metrics Overview ────────────────────────────────────────────────────────
function renderMetricsOverview() {
  const container = document.getElementById('metrics-overview');
  if (!container) return;

  const builtIn = allMetrics.filter(m => m.is_builtin);
  const display = builtIn.length ? builtIn.slice(0, 5) : allMetrics.slice(0, 5);

  if (!display.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-4">No metrics configured</p>';
    return;
  }

  // Demo progress values (in real app these come from latest snapshot)
  const demoValues = { density: 72, entropy: 38, activity: 45, births: 60, deaths: 30 };

  const rows = display.map(m => {
    const val = demoValues[m.name] || Math.floor(Math.random() * 80 + 10);
    const barColor = val > 70 ? 'bg-green-500' : val > 40 ? 'bg-primary-500' : 'bg-amber-500';
    return `
      <div class="group">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-semibold text-slate-700 capitalize">${m.name}</span>
          <span class="text-xs font-bold text-slate-900">${val}%</span>
        </div>
        <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div class="h-full ${barColor} rounded-full transition-all duration-700" style="width: ${val}%"></div>
        </div>
      </div>
    `;
  }).join('');

  // Tiny sparkline using CSS bars
  const sparkBars = [35, 42, 38, 55, 48, 62, 58, 71, 65, 72].map(h =>
    `<div class="flex-1 bg-primary-300 rounded-t-sm" style="height: ${h}%"></div>`
  ).join('');

  container.innerHTML = `
    <div class="space-y-3 mb-4">${rows}</div>
    <div class="pt-3 border-t border-slate-100">
      <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Density trend (last 50 steps)</div>
      <div class="flex items-end gap-1 h-12 w-full">${sparkBars}</div>
    </div>
  `;
}

// ─── Featured Rules ────────────────────────────────────────────────────────
function renderFeaturedRules() {
  const container = document.getElementById('featured-rules-grid');
  if (!container) return;

  const featuredNames = ['Conway', '413', 'DormancyA', 'C6', 'TGA'];
  const featured = featuredNames.map(name => allRules.find(r => r.name === name)).filter(Boolean);

  if (!featured.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 col-span-full text-center py-4">Loading featured rules...</p>';
    return;
  }

  container.innerHTML = featured.map(rule => {
    const states = getRuleStates(rule);
    const hood = (rule.yaml_content?.match(/neighbourhood:\s*(\w+)/)?.[1]) || 'moore8';
    return `
      <div class="card bg-white rounded-2xl p-5 border border-slate-200 hover:border-primary-300 transition-all flex flex-col">
        <div class="w-full h-24 rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 mb-4 flex items-center justify-center text-3xl">🧬</div>
        <h3 class="font-bold text-sm text-slate-900 mb-1">${rule.name}</h3>
        <p class="text-xs text-slate-500 mb-1">${states} states · ${hood}</p>
        <p class="text-xs text-slate-400 mb-4 flex-1">${rule.description || 'Cellular automaton rule'}</p>
        <button onclick="useRule(${rule.id})" class="w-full px-3 py-2 bg-white border-2 border-primary-600 text-primary-700 text-xs font-bold rounded-lg hover:bg-primary-600 hover:text-white transition-all">
          Use This Rule
        </button>
      </div>
    `;
  }).join('');
}

function useRule(ruleId) {
  openNewSessionModalWithRule(ruleId);
}

// ─── Recent Experiments Table ────────────────────────────────────────────────
let tableSort = { key: 'created_at', dir: 'desc' };

function sortTable(key) {
  if (tableSort.key === key) {
    tableSort.dir = tableSort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    tableSort.key = key;
    tableSort.dir = 'desc';
  }
  renderRecentExperiments();
}

function renderRecentExperiments() {
  const tbody = document.getElementById('recent-experiments-body');
  if (!tbody) return;

  let rows = [...allSessions];
  rows.sort((a, b) => {
    const av = a[tableSort.key] || '';
    const bv = b[tableSort.key] || '';
    if (typeof av === 'number' && typeof bv === 'number') {
      return tableSort.dir === 'asc' ? av - bv : bv - av;
    }
    return tableSort.dir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
  });

  if (!rows.length) {
    tbody.innerHTML = `
      <tr><td colspan="6" class="px-4 py-8 text-center text-sm text-slate-500">
        <div class="text-2xl mb-2">🧪</div>
        <p class="font-medium">No experiments yet</p>
        <p class="text-xs text-slate-400 mt-1">Click "New Session" to begin your research</p>
      </td></tr>
    `;
    return;
  }

  tbody.innerHTML = rows.map(s => `
    <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer" onclick="viewSession(${s.id})">
      <td class="px-4 py-3">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-sm">🧬</div>
      </td>
      <td class="px-4 py-3">
        <div class="font-semibold text-sm text-slate-900">${s.name}</div>
        <div class="text-xs text-slate-500">${s.rule_name}</div>
      </td>
      <td class="px-4 py-3">
        ${formatStatus(s.status)}
        ${s.mode && s.mode !== 'simulate' ? `<span class="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${s.mode === 'evolve' ? 'bg-accent-100 text-accent-700' : 'bg-purple-100 text-purple-700'}">${s.mode === 'evolve' ? 'EVO' : 'Breed'}</span>` : ''}
      </td>
      <td class="px-4 py-3 text-sm text-slate-600">${s.board_width}×${s.board_height}</td>
      <td class="px-4 py-3 text-sm text-slate-600">${s.current_step.toLocaleString()}</td>
      <td class="px-4 py-3 text-xs text-slate-500">${formatDate(s.created_at)}</td>
      <td class="px-4 py-3 text-right">
        <button onclick="event.stopPropagation(); viewSession(${s.id})" class="text-xs font-semibold text-primary-700 hover:text-primary-900 px-2 py-1 rounded hover:bg-primary-50 transition-colors">Open</button>
      </td>
    </tr>
  `).join('');
}

// ─── Sidebar Navigation Rendering ───────────────────────────────────────────
function renderSidebarNav() {
  // Update active session count badge (running + paused)
  const activeCount = allSessions.filter(s => s.status === 'running' || s.status === 'paused').length;
  const badge = document.getElementById('nav-active-count');
  if (badge) {
    if (activeCount > 0) {
      badge.textContent = String(activeCount);
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }
}

// ─── Data Loading ────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    [allRules, allSessions, allMetrics] = await Promise.all([
      api.get('/api/rules/'),
      api.get('/api/sessions/'),
      api.get('/api/metrics/'),
    ]);

    const stats = computeStats();
    renderKpiCards(stats);
    renderActiveSessions();
    renderMetricsOverview();
    renderFeaturedRules();
    renderRecentExperiments();
    renderSidebarNav();

    // Update header summary and date
    const summaryEl = document.getElementById('dashboard-summary');
    if (summaryEl) {
      summaryEl.textContent = `${stats.total} experiments · ${stats.active} active · ${stats.completed} completed · ${stats.customRules} custom rules`;
    }
    const dateEl = document.getElementById('current-date');
    if (dateEl) {
      dateEl.textContent = new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
  } catch (e) {
    toast('Failed to load dashboard: ' + e.message, 'error');
  }
}

function viewSession(id) {
  window.location.href = `/simulation/${id}`;
}

function loadSession(id) {
  viewSession(id);
}

async function deleteSession(id) {
  if (!confirm('Delete this session?')) return;
  try {
    await api.delete(`/api/sessions/${id}`);
    toast('Session deleted', 'success');
    await loadDashboard();
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}

async function pauseSession(id) {
  try {
    await api.put(`/api/sessions/${id}`, { status: 'paused' });
    toast('Session paused', 'success');
    await loadDashboard();
  } catch (e) {
    toast('Pause failed: ' + e.message, 'error');
  }
}

async function resumeSession(id) {
  try {
    await api.put(`/api/sessions/${id}`, { status: 'running' });
    toast('Session resumed', 'success');
    await loadDashboard();
  } catch (e) {
    toast('Resume failed: ' + e.message, 'error');
  }
}

// ─── Initialization ──────────────────────────────────────────────────────────
function initDashboard() {
  // Close sidebar when clicking overlay
  document.getElementById('sidebar-overlay')?.addEventListener('click', closeSidebar);

  // Keyboard: Escape closes sidebar
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSidebar();
      closeNewSessionModal();
    }
  });

  loadDashboard();

  // Poll for active session updates every 5 seconds
  activeSessionPollInterval = setInterval(async () => {
    try {
      const sessions = await api.get('/api/sessions/');
      allSessions = sessions;
      renderActiveSessions();
      renderSidebarNav();
      renderRecentExperiments();
      const stats = computeStats();
      renderKpiCards(stats);
    } catch {
      // silent fail on poll
    }
  }, 5000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}
