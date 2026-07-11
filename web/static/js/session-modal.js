/**
 * CA Lab — Shared New Session Modal Controller
 * Handles the redesigned split-pane modal with dropdowns and live preview.
 * Loaded on all pages (dashboard, rules, metrics) before the page-specific JS.
 */

// ─── State ─────────────────────────────────────────────────────────────────
let smSelectedRuleId = null;
let smSelectedMetricNames = new Set(['density', 'entropy']);
let smStatesManuallyEdited = false;
let smAllRules = [];
let smAllMetrics = [];
let smRuleDropdownOpen = false;
let smMetricDropdownOpen = false;

// ─── Helpers ───────────────────────────────────────────────────────────────
function smGetRuleStates(rule) {
  if (!rule?.yaml_content) return 2;
  const statesMatch = rule.yaml_content.match(/^states:\s*(\d+)/m);
  if (statesMatch) return parseInt(statesMatch[1], 10);
  const numStatesMatch = rule.yaml_content.match(/^num_states:\s*(\d+)/m);
  if (numStatesMatch) return parseInt(numStatesMatch[1], 10);
  return 2;
}

function smGetRuleHood(rule) {
  return (rule?.yaml_content?.match(/neighbourhood:\s*(\w+)/)?.[1]) || 'moore8';
}

// ─── Modal Open / Close ────────────────────────────────────────────────────
function openNewSessionModal() {
  smStatesManuallyEdited = false;
  smSelectedMetricNames = new Set(['density', 'entropy']);
  smRuleDropdownOpen = false;
  smMetricDropdownOpen = false;

  // Reset form fields
  const nameInput = document.getElementById('session-name-input');
  if (nameInput) nameInput.value = '';

  // Clear dropdown search
  const ruleSearch = document.getElementById('dropdown-rule-search');
  if (ruleSearch) ruleSearch.value = '';
  const metricSearch = document.getElementById('dropdown-metric-search');
  if (metricSearch) metricSearch.value = '';

  // Hide back button
  const backBtn = document.getElementById('session-modal-back');
  if (backBtn) backBtn.classList.add('hidden');

  // Close any open dropdowns visually
  closeRuleDropdown();
  closeMetricDropdown();

  // Fetch data then render
  Promise.all([
    api.get('/api/rules/'),
    api.get('/api/metrics/'),
  ]).then(([rules, metrics]) => {
    smAllRules = rules || [];
    smAllMetrics = metrics || [];
    smSelectedRuleId = null;
    renderRuleDropdown('');
    renderMetricDropdown('');
    clearRulePreview();
    updateMetricTrigger();
    updateRuleTrigger();
    // Default num states
    const numInput = document.getElementById('num-states-input');
    if (numInput) numInput.value = 2;
  }).catch(e => {
    toast('Failed to load modal data: ' + e.message, 'error');
  });

  document.getElementById('newSessionModal')?.classList.remove('hidden');
  document.getElementById('session-name-input')?.focus();
}

function openNewSessionModalWithRule(ruleId) {
  openNewSessionModal();
  // After data loads, select the rule
  Promise.all([
    api.get('/api/rules/'),
    api.get('/api/metrics/'),
  ]).then(([rules, metrics]) => {
    smAllRules = rules || [];
    smAllMetrics = metrics || [];
    selectRuleForSession(ruleId);
    renderMetricDropdown('');
    updateMetricTrigger();
    // Show back button
    const backBtn = document.getElementById('session-modal-back');
    if (backBtn) backBtn.classList.remove('hidden');
  }).catch(() => {});
}

function closeNewSessionModal() {
  document.getElementById('newSessionModal')?.classList.add('hidden');
  closeRuleDropdown();
  closeMetricDropdown();
}

// ─── Rule Dropdown ─────────────────────────────────────────────────────────
function openRuleDropdown() {
  smRuleDropdownOpen = true;
  const panel = document.getElementById('rule-dropdown-panel');
  if (panel) {
    panel.classList.remove('hidden');
    panel.classList.add('animate-fade-in');
  }
  const search = document.getElementById('dropdown-rule-search');
  if (search) setTimeout(() => search.focus(), 50);
}

function closeRuleDropdown() {
  smRuleDropdownOpen = false;
  const panel = document.getElementById('rule-dropdown-panel');
  if (panel) {
    panel.classList.add('hidden');
    panel.classList.remove('animate-fade-in');
  }
}

function toggleRuleDropdown() {
  if (smRuleDropdownOpen) closeRuleDropdown();
  else {
    closeMetricDropdown();
    openRuleDropdown();
  }
}

function filterRuleDropdown(query) {
  renderRuleDropdown(query);
}

function renderRuleDropdown(query) {
  const container = document.getElementById('rule-dropdown-list');
  if (!container) return;
  const q = (query || '').trim().toLowerCase();
  const filtered = smAllRules.filter(r => r.name.toLowerCase().includes(q));

  if (!smAllRules.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-4">No rules available</p>';
    return;
  }
  if (!filtered.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-4">No matching rules</p>';
    return;
  }

  container.innerHTML = filtered.map(rule => {
    const active = rule.id === smSelectedRuleId;
    const states = smGetRuleStates(rule);
    const dot = active
      ? '<span class="w-4 h-4 rounded-full border-4 border-primary-600 flex-shrink-0 mt-0.5"></span>'
      : '<span class="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0 mt-0.5"></span>';
    return `
      <div class="dropdown-item flex items-start gap-2.5 px-3 py-2.5 cursor-pointer transition-colors ${active ? 'bg-primary-50' : 'hover:bg-slate-50'}"
           onclick="selectRuleForSession(${rule.id})" role="option" aria-selected="${active}">
        ${dot}
        <span class="min-w-0 flex-1">
          <span class="flex items-center gap-2">
            <span class="text-sm font-semibold text-slate-900 leading-tight">${rule.name}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-medium ${rule.is_builtin ? 'bg-primary-100 text-primary-700' : 'bg-accent-100 text-accent-700'}">${rule.is_builtin ? 'Built-in' : 'Custom'}</span>
          </span>
          <span class="block text-xs text-slate-500 mt-0.5">${states} states · ${rule.category || 'experimental'}</span>
        </span>
      </div>
    `;
  }).join('');
}

function selectRuleForSession(ruleId) {
  smSelectedRuleId = ruleId;
  closeRuleDropdown();
  updateRuleTrigger();
  renderRulePreview(ruleId);
  updateNumStatesFromRule();
}

function updateRuleTrigger() {
  const trigger = document.getElementById('rule-dropdown-trigger');
  if (!trigger) return;
  const rule = smAllRules.find(r => r.id === smSelectedRuleId);
  if (rule) {
    trigger.innerHTML = `
      <span class="flex items-center gap-2 min-w-0">
        <span class="w-2 h-2 rounded-full bg-primary-600 flex-shrink-0"></span>
        <span class="text-sm font-semibold text-slate-900 truncate">${rule.name}</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded font-medium ${rule.is_builtin ? 'bg-primary-100 text-primary-700' : 'bg-accent-100 text-accent-700'}">${rule.is_builtin ? 'Built-in' : 'Custom'}</span>
      </span>
      <svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
    `;
  } else {
    trigger.innerHTML = `
      <span class="text-sm text-slate-400">Select a rule...</span>
      <svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
    `;
  }
}

function updateNumStatesFromRule() {
  if (smStatesManuallyEdited) return;
  const rule = smAllRules.find(r => r.id === smSelectedRuleId);
  if (!rule) return;
  const states = smGetRuleStates(rule);
  const input = document.getElementById('num-states-input');
  if (input) input.value = states;
}

// ─── Metric Dropdown ───────────────────────────────────────────────────────
function openMetricDropdown() {
  smMetricDropdownOpen = true;
  const panel = document.getElementById('metric-dropdown-panel');
  if (panel) {
    panel.classList.remove('hidden');
    panel.classList.add('animate-fade-in');
  }
  const search = document.getElementById('dropdown-metric-search');
  if (search) setTimeout(() => search.focus(), 50);
}

function closeMetricDropdown() {
  smMetricDropdownOpen = false;
  const panel = document.getElementById('metric-dropdown-panel');
  if (panel) {
    panel.classList.add('hidden');
    panel.classList.remove('animate-fade-in');
  }
}

function toggleMetricDropdown() {
  if (smMetricDropdownOpen) closeMetricDropdown();
  else {
    closeRuleDropdown();
    openMetricDropdown();
  }
}

function filterMetricDropdown(query) {
  renderMetricDropdown(query);
}

function renderMetricDropdown(query) {
  const container = document.getElementById('metric-dropdown-list');
  if (!container) return;
  const q = (query || '').trim().toLowerCase();
  const filtered = smAllMetrics.filter(m =>
    m.name.toLowerCase().includes(q) || (m.description || '').toLowerCase().includes(q)
  );

  if (!smAllMetrics.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-4">No metrics available</p>';
    return;
  }
  if (!filtered.length) {
    container.innerHTML = '<p class="text-sm text-slate-500 text-center py-4">No matching metrics</p>';
    return;
  }

  container.innerHTML = filtered.map(metric => {
    const checked = smSelectedMetricNames.has(metric.name);
    const badge = metric.is_builtin
      ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-primary-100 text-primary-700 font-medium">Built-in</span>'
      : '<span class="text-[10px] px-1.5 py-0.5 rounded bg-accent-100 text-accent-700 font-medium">Custom</span>';
    return `
      <label class="dropdown-item flex items-start gap-2.5 px-3 py-2.5 cursor-pointer transition-colors hover:bg-slate-50"
             role="option" aria-selected="${checked}">
        <input type="checkbox" class="mt-0.5 w-4 h-4 rounded border-slate-300 text-primary-600 flex-shrink-0"
          ${checked ? 'checked' : ''}
          onchange="toggleMetricForSession('${metric.name}', this.checked)">
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

function toggleMetricForSession(name, checked) {
  if (checked) smSelectedMetricNames.add(name);
  else smSelectedMetricNames.delete(name);
  updateMetricTrigger();
}

function updateMetricTrigger() {
  const trigger = document.getElementById('metric-dropdown-trigger');
  if (!trigger) return;
  const count = smSelectedMetricNames.size;
  if (count === 0) {
    trigger.innerHTML = `
      <span class="text-sm text-slate-400">Select metrics...</span>
      <svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
    `;
  } else {
    const names = Array.from(smSelectedMetricNames).slice(0, 2).join(', ');
    const more = count > 2 ? ` +${count - 2} more` : '';
    trigger.innerHTML = `
      <span class="flex items-center gap-2 min-w-0">
        <span class="w-5 h-5 rounded-full bg-accent-100 text-accent-700 flex items-center justify-center text-[10px] font-bold flex-shrink-0">${count}</span>
        <span class="text-sm font-semibold text-slate-900 truncate">${names}${more}</span>
      </span>
      <svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
    `;
  }
}

// ─── Preview Panel ───────────────────────────────────────────────────────────
function renderRulePreview(ruleId) {
  const panel = document.getElementById('preview-panel');
  const empty = document.getElementById('preview-empty');
  if (!panel || !empty) return;

  const rule = smAllRules.find(r => r.id === ruleId);
  if (!rule) {
    clearRulePreview();
    return;
  }

  empty.classList.add('hidden');
  const states = smGetRuleStates(rule);
  const hood = smGetRuleHood(rule);
  const builtIn = rule.is_builtin;
  const thumbColor = builtIn ? 'from-primary-200 to-blue-200' : 'from-accent-200 to-green-200';
  const thumbIcon = builtIn ? '🔒' : '✎';

  panel.innerHTML = `
    <div class="preview-thumbnail w-full h-32 rounded-xl bg-gradient-to-br ${thumbColor} mb-4 flex items-center justify-center text-3xl">${thumbIcon}</div>
    <div class="flex items-start justify-between gap-2 mb-2">
      <h3 class="font-bold text-sm text-slate-900 leading-tight">${rule.name}</h3>
      <span class="flex-shrink-0 px-2 py-0.5 text-[10px] rounded-full font-bold ${builtIn ? 'bg-primary-100 text-primary-700' : 'bg-accent-100 text-accent-700'}">
        ${builtIn ? 'Built-in' : 'Custom'}
      </span>
    </div>
    <div class="flex flex-wrap gap-1.5 mb-3">
      <span class="px-2 py-0.5 text-[10px] rounded-md bg-slate-100 text-slate-600 font-medium">${rule.category || 'experimental'}</span>
    </div>
    <div class="flex flex-wrap gap-3 text-xs text-slate-500 mb-3">
      <span class="flex items-center gap-1">📋 ${states} states</span>
      <span class="flex items-center gap-1">🌐 ${hood}</span>
    </div>
    <p class="text-xs text-slate-400 mb-4 leading-relaxed">${rule.description || 'Cellular automaton rule'}</p>
    <button type="button" onclick="window.location.href='/rules'" class="text-xs font-semibold text-primary-700 hover:text-primary-900 flex items-center gap-1">
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      View Rule Details
    </button>
  `;
  panel.classList.remove('hidden');
}

function clearRulePreview() {
  const panel = document.getElementById('preview-panel');
  const empty = document.getElementById('preview-empty');
  if (panel) {
    panel.innerHTML = '';
    panel.classList.add('hidden');
  }
  if (empty) empty.classList.remove('hidden');
}

// ─── Create Session ────────────────────────────────────────────────────────
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
  const metrics = Array.from(smSelectedMetricNames);

  if (!smSelectedRuleId) {
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
      rule_id: smSelectedRuleId,
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

// ─── Click-Outside Handling ────────────────────────────────────────────────
document.addEventListener('click', (e) => {
  const ruleTrigger = document.getElementById('rule-dropdown-trigger');
  const rulePanel = document.getElementById('rule-dropdown-panel');
  const metricTrigger = document.getElementById('metric-dropdown-trigger');
  const metricPanel = document.getElementById('metric-dropdown-panel');

  if (smRuleDropdownOpen && rulePanel && ruleTrigger) {
    if (!rulePanel.contains(e.target) && !ruleTrigger.contains(e.target)) {
      closeRuleDropdown();
    }
  }
  if (smMetricDropdownOpen && metricPanel && metricTrigger) {
    if (!metricPanel.contains(e.target) && !metricTrigger.contains(e.target)) {
      closeMetricDropdown();
    }
  }
});

// ─── Keyboard Handling ───────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (smRuleDropdownOpen) {
      e.stopImmediatePropagation();
      closeRuleDropdown();
      return;
    }
    if (smMetricDropdownOpen) {
      e.stopImmediatePropagation();
      closeMetricDropdown();
      return;
    }
  }
});

// ─── Num-states manual-edit tracking ─────────────────────────────────────────
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('num-states-input')?.addEventListener('input', () => {
      smStatesManuallyEdited = true;
    });
  });
} else {
  document.getElementById('num-states-input')?.addEventListener('input', () => {
    smStatesManuallyEdited = true;
  });
}
