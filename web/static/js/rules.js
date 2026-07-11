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
  openNewSessionModalWithRule(ruleId);
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

// ─── Init ──────────────────────────────────────────────────────────────────
function initRulesPage() {
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
