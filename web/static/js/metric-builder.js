/**
 * Metric creator wizard for CA Lab dashboard.
 */

const MetricBuilder = (function () {
  let step = 1;
  let editId = null;
  let selectAfterSave = null;
  let templates = [];

  const state = {
    metric_type: 'state_count',
    name: '',
    description: '',
    formula: '',
    config: { state: 1 },
  };

  function el(id) {
    return document.getElementById(id);
  }

  function reset(editMetric = null, onSelect = null) {
    step = 1;
    editId = editMetric?.id || null;
    selectAfterSave = onSelect;
    state.metric_type = editMetric?.metric_type || 'state_count';
    state.name = editMetric?.name || '';
    state.description = editMetric?.description || '';
    state.formula = editMetric?.formula || '';
    state.config = { ...(editMetric?.config || { state: 1 }) };
    render();
  }

  async function open(editMetric = null, onSelect = null) {
    try {
      templates = await api.get('/api/metrics/templates');
    } catch {
      templates = [];
    }
    reset(editMetric, onSelect);
    el('metricBuilderModal')?.classList.remove('hidden');
  }

  function close() {
    el('metricBuilderModal')?.classList.add('hidden');
  }

  function setStep(n) {
    step = Math.max(1, Math.min(4, n));
    render();
  }

  function suggestName() {
    if (state.name) return;
    if (state.metric_type === 'state_count') {
      state.name = `cells_in_state_${state.config.state ?? 1}`;
    } else if (state.metric_type === 'state_ratio') {
      state.name = `ratio_state_${state.config.state ?? 1}`;
    } else if (state.metric_type === 'alive_ratio') {
      state.name = 'alive_fraction';
    } else if (state.formula) {
      state.name = state.formula.replace(/[^a-z0-9]+/gi, '_').toLowerCase().slice(0, 24);
    }
  }

  function insertFormulaToken(token) {
    const input = el('metric-formula-input');
    if (!input) return;
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? input.value.length;
    const before = input.value.slice(0, start);
    const after = input.value.slice(end);
    const spacer = before && !before.endsWith(' ') && !'([*/+-'.includes(before.slice(-1)) ? ' ' : '';
    const spacerAfter = after && !after.startsWith(' ') && !')'.includes(after[0]) ? ' ' : '';
    input.value = `${before}${spacer}${token}${spacerAfter}${after}`;
    state.formula = input.value;
    input.focus();
  }

  function renderTypeStep() {
    const cards = [
      { type: 'state_count', title: 'Count cells in a state', desc: 'How many cells are in a chosen state?' },
      { type: 'state_ratio', title: 'Fraction in a state', desc: 'Share of the board in one state (0–1).' },
      { type: 'alive_ratio', title: 'Alive fraction', desc: 'Fraction of non-empty cells.' },
      { type: 'formula', title: 'Combine measurements', desc: 'Use density, entropy, and math.' },
    ];
    return `
      <p class="text-sm text-slate-600 mb-4">Choose what you want to measure. No coding required.</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        ${cards.map(c => `
          <label class="cursor-pointer block p-4 rounded-xl border-2 transition-colors ${state.metric_type === c.type ? 'border-primary-500 bg-primary-50' : 'border-slate-200 hover:border-primary-300'}">
            <input type="radio" name="metric-type" value="${c.type}" class="sr-only" ${state.metric_type === c.type ? 'checked' : ''}
              onchange="MetricBuilder.setType('${c.type}')">
            <div class="font-semibold text-sm text-slate-900">${c.title}</div>
            <div class="text-xs text-slate-500 mt-1">${c.desc}</div>
          </label>
        `).join('')}
      </div>
    `;
  }

  function renderConfigStep() {
    if (state.metric_type === 'formula') {
      const chips = ['density', 'entropy', 'entropy_nonzero', '+', '-', '*', '/', '(', ')', '100', '2'];
      return `
        <p class="text-sm text-slate-600 mb-3">Build a formula from built-in measurements.</p>
        <div class="flex flex-wrap gap-2 mb-3">
          ${chips.map(t => `
            <button type="button" onclick="MetricBuilder.insertToken('${t}')"
              class="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-primary-100 text-slate-700">${t}</button>
          `).join('')}
        </div>
        <label class="block text-sm font-semibold text-slate-700 mb-1">Formula</label>
        <input type="text" id="metric-formula-input" value="${escapeHtml(state.formula)}"
          placeholder="density * 100"
          oninput="MetricBuilder.setFormula(this.value)"
          class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm font-mono">
        <p class="text-xs text-slate-500 mt-2">Examples: <code>density * 100</code>, <code>(entropy + density) / 2</code></p>
      `;
    }
    if (state.metric_type === 'alive_ratio') {
      return `<p class="text-sm text-slate-600">This metric counts cells that are not in state 0 (empty/dead), divided by board size.</p>`;
    }
    const st = state.config.state ?? 1;
    return `
      <p class="text-sm text-slate-600 mb-3">State 0 is usually empty or dead. Pick which state to measure.</p>
      <label class="block text-sm font-semibold text-slate-700 mb-1">State number</label>
      <input type="number" min="0" max="100" value="${st}"
        onchange="MetricBuilder.setConfigState(parseInt(this.value, 10))"
        class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm">
    `;
  }

  function renderNameStep() {
    return `
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Metric name</label>
          <input type="text" value="${escapeHtml(state.name)}" placeholder="cells_in_state_1"
            oninput="MetricBuilder.setName(this.value)"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm">
          <p class="text-xs text-slate-500 mt-1">Lowercase letters, numbers, underscores (3–32 chars).</p>
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Description</label>
          <input type="text" value="${escapeHtml(state.description)}" placeholder="What this measures"
            oninput="MetricBuilder.setDescription(this.value)"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm">
        </div>
      </div>
    `;
  }

  function renderReviewStep() {
    return `
      <div id="metric-validation-result" class="mb-4"></div>
      <dl class="text-sm space-y-2 bg-slate-50 rounded-xl p-4 border border-slate-200">
        <div class="flex justify-between gap-4"><dt class="text-slate-500">Type</dt><dd class="font-medium">${state.metric_type}</dd></div>
        <div class="flex justify-between gap-4"><dt class="text-slate-500">Name</dt><dd class="font-medium">${escapeHtml(state.name) || '—'}</dd></div>
        ${state.metric_type === 'formula' ? `<div><dt class="text-slate-500 mb-1">Formula</dt><dd class="font-mono text-xs bg-white p-2 rounded border">${escapeHtml(state.formula)}</dd></div>` : ''}
        ${state.metric_type !== 'formula' && state.metric_type !== 'alive_ratio' ? `<div class="flex justify-between"><dt class="text-slate-500">State</dt><dd>${state.config.state ?? 0}</dd></div>` : ''}
      </dl>
    `;
  }

  function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }

  function render() {
    const title = el('metric-builder-title');
    const body = el('metric-builder-body');
    const steps = el('metric-builder-steps');
    if (!body) return;

    if (title) title.textContent = editId ? 'Edit Metric' : 'Create Metric';

    const stepLabels = ['Type', 'Configure', 'Name', 'Review'];
    if (steps) {
      steps.innerHTML = stepLabels.map((label, i) => {
        const n = i + 1;
        const active = n === step;
        const done = n < step;
        return `<span class="text-xs font-semibold px-2 py-1 rounded-full ${active ? 'bg-primary-100 text-primary-800' : done ? 'text-accent-700' : 'text-slate-400'}">${n}. ${label}</span>`;
      }).join('');
    }

    if (step === 1) body.innerHTML = renderTypeStep();
    else if (step === 2) body.innerHTML = renderConfigStep();
    else if (step === 3) {
      suggestName();
      body.innerHTML = renderNameStep();
    } else body.innerHTML = renderReviewStep();

    const backBtn = el('metric-builder-back');
    const nextBtn = el('metric-builder-next');
    const saveBtn = el('metric-builder-save');
    if (backBtn) backBtn.classList.toggle('hidden', step === 1);
    if (nextBtn) nextBtn.classList.toggle('hidden', step === 4);
    if (saveBtn) saveBtn.classList.toggle('hidden', step !== 4);
  }

  function setType(t) {
    state.metric_type = t;
    render();
  }

  function setConfigState(n) {
    state.config.state = isNaN(n) ? 0 : n;
    suggestName();
  }

  function setName(v) { state.name = v.trim(); }
  function setDescription(v) { state.description = v.trim(); }
  function setFormula(v) { state.formula = v.trim(); }

  function payload() {
    return {
      name: state.name,
      metric_type: state.metric_type,
      formula: state.metric_type === 'formula' ? state.formula : '',
      config: state.metric_type === 'alive_ratio' ? {} : { ...state.config },
      description: state.description,
    };
  }

  async function validate() {
    const resultEl = el('metric-validation-result');
    try {
      const result = await api.post('/api/metrics/validate', payload());
      if (result.is_valid) {
        const warns = (result.warnings || []).map(w => `<p class="text-amber-700 text-sm">⚠ ${w.message}</p>`).join('');
        resultEl.innerHTML = `<div class="text-accent-700 text-sm font-medium mb-2">✓ Metric looks good</div>${warns}`;
        return true;
      }
      resultEl.innerHTML = (result.errors || []).map(e => `<p class="text-red-600 text-sm">✗ ${e.message}</p>`).join('');
      return false;
    } catch (e) {
      resultEl.innerHTML = `<p class="text-red-600 text-sm">✗ ${e.message}</p>`;
      return false;
    }
  }

  async function save() {
    if (!(await validate())) return;
    try {
      let saved;
      if (editId) {
        saved = await api.put(`/api/metrics/${editId}`, payload());
      } else {
        saved = await api.post('/api/metrics/', payload());
      }
      toast(editId ? 'Metric updated' : 'Metric created', 'success');
      close();
      if (typeof loadDashboard === 'function') await loadDashboard();
      if (selectAfterSave && saved?.name) {
        selectedMetricNames.add(saved.name);
        if (typeof renderModalMetrics === 'function') renderModalMetrics();
      }
    } catch (e) {
      toast('Save failed: ' + e.message, 'error');
    }
  }

  async function next() {
    if (step === 3) suggestName();
    if (step < 4) {
      setStep(step + 1);
      if (step === 4) await validate();
    }
  }

  function back() {
    if (step > 1) setStep(step - 1);
  }

  return {
    open, close, setStep, setType, setConfigState, setName, setDescription, setFormula,
    insertToken: insertFormulaToken, next, back, save, validate,
  };
})();

function openNewMetricModal(fromSession = false) {
  MetricBuilder.open(null, fromSession ? true : null);
}

function editMetric(metricId) {
  const m = allMetrics.find(x => x.id === metricId);
  if (m) MetricBuilder.open(m);
}

async function deleteMetric(metricId) {
  if (!confirm('Delete this custom metric?')) return;
  try {
    await api.delete(`/api/metrics/${metricId}`);
    toast('Metric deleted', 'success');
    await loadDashboard();
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}
