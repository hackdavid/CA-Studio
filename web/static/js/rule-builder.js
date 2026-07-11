/**
 * Visual rule builder for CA Lab dashboard.
 */

const RuleBuilder = (function () {
  let step = 1;
  let editId = null;
  let selectAfterSave = null;
  let advancedYaml = false;

  const RULE_TEMPLATES = {
    conway: {
      label: 'Conway Life (B3/S23)',
      states: 2,
      neighbourhood: 'moore8',
      transitions: [
        { from: [1], neighbors: [2, 3], to: 1 },
        { from: [0], neighbors: [3], to: 1 },
        { from: [1], neighbors: [0, 1, 4, 5, 6, 7, 8, 9], to: 0 },
        { from: [0], neighbors: [0, 1, 2, 4, 5, 6, 7, 8, 9], to: 0 },
      ],
    },
    birth3: {
      label: 'Birth on 3 neighbors only',
      states: 2,
      neighbourhood: 'moore8',
      transitions: [
        { from: [0], neighbors: [3], to: 1 },
        { from: [1], neighbors: [0, 1, 2, 4, 5, 6, 7, 8, 9], to: 0 },
      ],
    },
    always_die: {
      label: 'All cells die',
      states: 2,
      neighbourhood: 'moore8',
      transitions: [
        { from: [0, 1], neighbors: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], to: 0 },
      ],
    },
  };

  const state = {
    name: '',
    description: '',
    category: 'custom',
    states: 2,
    neighbourhood: 'moore8',
    transitions: [{ from: [0], neighbors: [3], to: 1 }],
  };

  function el(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }

  function reset(editRule = null, onSelect = null) {
    step = 1;
    editId = editRule?.id || null;
    selectAfterSave = onSelect;
    advancedYaml = false;
    if (editRule) {
      state.name = editRule.name;
      state.description = editRule.description || '';
      state.category = editRule.category || 'custom';
      try {
        const parsed = parseYamlTransitions(editRule.yaml_content);
        Object.assign(state, parsed);
      } catch {
        state.states = 2;
        state.neighbourhood = 'moore8';
        state.transitions = [{ from: [0], neighbors: [3], to: 1 }];
      }
    } else {
      state.name = '';
      state.description = '';
      state.category = 'custom';
      state.states = 2;
      state.neighbourhood = 'moore8';
      state.transitions = [{ from: [0], neighbors: [3], to: 1 }];
    }
    render();
  }

  function parseYamlTransitions(yaml) {
    const lines = yaml.split('\n');
    let states = 2;
    let neighbourhood = 'moore8';
    for (const line of lines) {
      const sm = line.match(/^states:\s*(\d+)/);
      if (sm) states = parseInt(sm[1], 10);
      const nm = line.match(/^neighbourhood:\s*(\S+)/);
      if (nm) neighbourhood = nm[1];
    }
    const transitions = [];
    const blocks = yaml.split(/- from:/).slice(1);
    for (const block of blocks) {
      const fromMatch = block.match(/\[([^\]]*)\]|^:\s*\n\s*-\s*(\d+)/);
      const fromLine = block.match(/from:\s*\n((?:\s*-\s*\d+\s*\n?)+)/);
      let from = [];
      if (fromLine) {
        from = [...fromLine[1].matchAll(/-\s*(\d+)/g)].map(m => parseInt(m[1], 10));
      } else {
        const inline = block.match(/from:\s*\[([^\]]+)\]/);
        if (inline) from = inline[1].split(',').map(s => parseInt(s.trim(), 10));
      }
      const neighMatch = block.match(/neighbors:\s*\n((?:\s*-\s*\d+\s*\n?)+)|neighbors:\s*\[([^\]]+)\]/);
      let neighbors = [];
      if (neighMatch) {
        if (neighMatch[1]) {
          neighbors = [...neighMatch[1].matchAll(/-\s*(\d+)/g)].map(m => parseInt(m[1], 10));
        } else if (neighMatch[2]) {
          neighbors = neighMatch[2].split(',').map(s => parseInt(s.trim(), 10));
        }
      }
      const toMatch = block.match(/to:\s*(\d+|same)/);
      const to = toMatch ? (toMatch[1] === 'same' ? 'same' : parseInt(toMatch[1], 10)) : 0;
      if (from.length && neighbors.length) transitions.push({ from, neighbors, to });
    }
    return { states, neighbourhood, transitions: transitions.length ? transitions : [{ from: [0], neighbors: [3], to: 1 }] };
  }

  async function open(editRule = null, onSelect = null) {
    reset(editRule, onSelect);
    el('ruleBuilderModal')?.classList.remove('hidden');
  }

  function close() {
    el('ruleBuilderModal')?.classList.add('hidden');
  }

  function setStep(n) {
    step = Math.max(1, Math.min(4, n));
    render();
  }

  function buildYaml() {
    const header = `name: ${state.name}\nversion: "1.0"\nstates: ${state.states}\nneighbourhood: ${state.neighbourhood}\ndescription: ${JSON.stringify(state.description)}\ncategory: ${state.category}\ntransitions:\n`;
    const body = state.transitions.map(t => {
      const toVal = t.to === 'same' ? 'same' : t.to;
      return `- from: [${t.from.join(', ')}]\n  neighbors: [${t.neighbors.join(', ')}]\n  to: ${toVal}`;
    }).join('\n');
    return header + body + '\n';
  }

  function applyTemplate(key) {
    const tpl = RULE_TEMPLATES[key];
    if (!tpl) return;
    state.states = tpl.states;
    state.neighbourhood = tpl.neighbourhood;
    state.transitions = JSON.parse(JSON.stringify(tpl.transitions));
    render();
  }

  function addTransition() {
    state.transitions.push({ from: [0], neighbors: [3], to: 1 });
    render();
  }

  function removeTransition(idx) {
    state.transitions.splice(idx, 1);
    if (!state.transitions.length) state.transitions.push({ from: [0], neighbors: [3], to: 1 });
    render();
  }

  function toggleFrom(ti, s) {
    const t = state.transitions[ti];
    const set = new Set(t.from);
    if (set.has(s)) set.delete(s); else set.add(s);
    t.from = [...set].sort((a, b) => a - b);
    render();
  }

  function toggleNeighbor(ti, n) {
    const t = state.transitions[ti];
    const set = new Set(t.neighbors);
    if (set.has(n)) set.delete(n); else set.add(n);
    t.neighbors = [...set].sort((a, b) => a - b);
    render();
  }

  function setTransitionTo(ti, val) {
    state.transitions[ti].to = val === 'same' ? 'same' : parseInt(val, 10);
  }

  function humanSummary() {
    return state.transitions.map((t, i) => {
      const from = t.from.join(', ') || '?';
      const neigh = t.neighbors.join(', ') || '?';
      const to = t.to === 'same' ? 'stay the same' : `state ${t.to}`;
      return `Rule ${i + 1}: If cell is in state(s) ${from} and has ${neigh} active neighbors → becomes ${to}.`;
    }).join(' ');
  }

  function renderBasics() {
    return `
      <p class="text-sm text-slate-600 mb-4">A rule tells each cell how to change based on its neighbors.</p>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Rule name</label>
          <input type="text" value="${escapeHtml(state.name)}" oninput="RuleBuilder.setName(this.value)"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm" placeholder="MyLifeRule">
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Description</label>
          <input type="text" value="${escapeHtml(state.description)}" oninput="RuleBuilder.setDescription(this.value)"
            class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm">
        </div>
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1">Category</label>
          <select onchange="RuleBuilder.setCategory(this.value)" class="w-full px-4 py-2.5 border border-slate-300 rounded-lg input-focus text-sm bg-white">
            ${['life-like', 'expansion', 'experimental', 'custom'].map(c =>
              `<option value="${c}" ${state.category === c ? 'selected' : ''}>${c}</option>`
            ).join('')}
          </select>
        </div>
      </div>
    `;
  }

  function renderGridSettings() {
    const hoods = [
      { id: 'moore8', label: 'Moore 8', desc: '8 neighbors (no center)' },
      { id: 'moore9', label: 'Moore 9', desc: '8 neighbors + center' },
      { id: 'neumann', label: 'Von Neumann', desc: '4 orthogonal neighbors' },
    ];
    return `
      <div class="mb-4">
        <label class="block text-sm font-semibold text-slate-700 mb-2">Number of states (K): <span id="rule-states-val">${state.states}</span></label>
        <input type="range" min="2" max="10" value="${state.states}" class="w-full"
          oninput="RuleBuilder.setStates(parseInt(this.value,10)); document.getElementById('rule-states-val').textContent=this.value">
        <p class="text-xs text-slate-500 mt-1">State 0 is usually empty; state 1+ are active colors.</p>
      </div>
      <label class="block text-sm font-semibold text-slate-700 mb-2">Neighborhood</label>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
        ${hoods.map(h => `
          <button type="button" onclick="RuleBuilder.setNeighbourhood('${h.id}')"
            class="p-3 rounded-xl border-2 text-left ${state.neighbourhood === h.id ? 'border-primary-500 bg-primary-50' : 'border-slate-200'}">
            <div class="font-semibold text-sm">${h.label}</div>
            <div class="text-xs text-slate-500">${h.desc}</div>
          </button>
        `).join('')}
      </div>
    `;
  }

  function renderTransitions() {
    const maxNeigh = state.neighbourhood === 'neumann' ? 4 : 8;
    const tplOpts = Object.entries(RULE_TEMPLATES).map(([k, v]) =>
      `<option value="${k}">${v.label}</option>`
    ).join('');
    const cards = state.transitions.map((t, ti) => {
      const stateChips = Array.from({ length: state.states }, (_, s) => {
        const on = t.from.includes(s);
        return `<button type="button" onclick="RuleBuilder.toggleFrom(${ti},${s})"
          class="px-2 py-1 text-xs rounded-lg border ${on ? 'bg-primary-100 border-primary-400' : 'bg-white border-slate-200'}">${s}</button>`;
      }).join('');
      const neighChips = Array.from({ length: maxNeigh + 1 }, (_, n) => {
        const on = t.neighbors.includes(n);
        return `<button type="button" onclick="RuleBuilder.toggleNeighbor(${ti},${n})"
          class="px-2 py-1 text-xs rounded-lg border ${on ? 'bg-accent-100 border-accent-400' : 'bg-white border-slate-200'}">${n}</button>`;
      }).join('');
      const toOpts = Array.from({ length: state.states }, (_, s) =>
        `<option value="${s}" ${t.to === s ? 'selected' : ''}>State ${s}</option>`
      ).join('') + `<option value="same" ${t.to === 'same' ? 'selected' : ''}>Stay the same</option>`;
      return `
        <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-sm font-semibold text-slate-800">Transition ${ti + 1}</span>
            ${state.transitions.length > 1 ? `<button type="button" onclick="RuleBuilder.removeTransition(${ti})" class="text-xs text-red-600">Remove</button>` : ''}
          </div>
          <div>
            <div class="text-xs font-medium text-slate-600 mb-1">When cell is in state:</div>
            <div class="flex flex-wrap gap-1">${stateChips}</div>
          </div>
          <div>
            <div class="text-xs font-medium text-slate-600 mb-1">And active neighbor count is:</div>
            <div class="flex flex-wrap gap-1">${neighChips}</div>
          </div>
          <div>
            <div class="text-xs font-medium text-slate-600 mb-1">Then cell becomes:</div>
            <select onchange="RuleBuilder.setTransitionTo(${ti}, this.value)" class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">${toOpts}</select>
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="mb-3 flex flex-wrap gap-2 items-center">
        <label class="text-sm font-medium text-slate-700">Start from template:</label>
        <select onchange="RuleBuilder.applyTemplate(this.value); this.value=''" class="text-sm border border-slate-300 rounded-lg px-2 py-1 bg-white">
          <option value="">Choose…</option>${tplOpts}
        </select>
      </div>
      <div class="space-y-3 mb-3">${cards}</div>
      <button type="button" onclick="RuleBuilder.addTransition()" class="text-sm font-semibold text-primary-700">+ Add another transition</button>
      <p class="text-xs text-slate-500 mt-3 p-3 bg-white rounded-lg border">${escapeHtml(humanSummary())}</p>
    `;
  }

  function renderReview() {
    const yaml = advancedYaml ? (el('rule-yaml-advanced')?.value || buildYaml()) : buildYaml();
    return `
      <div id="rule-validation-result" class="mb-4"></div>
      <div class="flex gap-2 mb-3">
        <button type="button" onclick="RuleBuilder.setAdvanced(false)" class="text-sm px-3 py-1 rounded-lg ${!advancedYaml ? 'bg-primary-100 text-primary-800' : 'bg-slate-100'}">Summary</button>
        <button type="button" onclick="RuleBuilder.setAdvanced(true)" class="text-sm px-3 py-1 rounded-lg ${advancedYaml ? 'bg-primary-100 text-primary-800' : 'bg-slate-100'}">Advanced YAML</button>
      </div>
      ${advancedYaml ? `
        <textarea id="rule-yaml-advanced" rows="14" class="w-full font-mono text-xs border border-slate-300 rounded-lg p-3">${escapeHtml(yaml)}</textarea>
      ` : `
        <pre class="text-xs bg-slate-50 border border-slate-200 rounded-xl p-4 overflow-x-auto whitespace-pre-wrap">${escapeHtml(yaml)}</pre>
      `}
    `;
  }

  function render() {
    const body = el('rule-builder-body');
    const steps = el('rule-builder-steps');
    const title = el('rule-builder-title');
    if (!body) return;
    if (title) title.textContent = editId ? 'Edit Rule' : 'Create Rule';
    const labels = ['Basics', 'Grid', 'Transitions', 'Review'];
    if (steps) {
      steps.innerHTML = labels.map((l, i) => {
        const n = i + 1;
        return `<span class="text-xs font-semibold px-2 py-1 rounded-full ${n === step ? 'bg-primary-100 text-primary-800' : n < step ? 'text-accent-700' : 'text-slate-400'}">${n}. ${l}</span>`;
      }).join('');
    }
    if (step === 1) body.innerHTML = renderBasics();
    else if (step === 2) body.innerHTML = renderGridSettings();
    else if (step === 3) body.innerHTML = renderTransitions();
    else body.innerHTML = renderReview();

    el('rule-builder-back')?.classList.toggle('hidden', step === 1);
    el('rule-builder-next')?.classList.toggle('hidden', step === 4);
    el('rule-builder-save')?.classList.toggle('hidden', step !== 4);
  }

  function setName(v) { state.name = v.trim(); }
  function setDescription(v) { state.description = v.trim(); }
  function setCategory(v) { state.category = v; }
  function setStates(n) { state.states = Math.max(2, Math.min(10, n)); }
  function setNeighbourhood(v) { state.neighbourhood = v; render(); }
  function setAdvanced(v) { advancedYaml = v; render(); }

  function builderPayload() {
    if (advancedYaml && step === 4) {
      const yaml = el('rule-yaml-advanced')?.value || buildYaml();
      return { yaml_content: yaml, name: state.name, description: state.description, category: state.category };
    }
    return {
      name: state.name,
      description: state.description,
      category: state.category,
      states: state.states,
      neighbourhood: state.neighbourhood,
      transitions: state.transitions,
    };
  }

  async function validate() {
    const resultEl = el('rule-validation-result');
    let yamlContent;
    if (advancedYaml && step === 4) {
      yamlContent = el('rule-yaml-advanced')?.value || buildYaml();
    } else {
      yamlContent = buildYaml();
    }
    try {
      const result = await api.post('/api/rules/validate', {
        name: state.name,
        yaml_content: yamlContent,
        description: state.description,
        category: state.category,
      });
      if (result.is_valid) {
        const warns = (result.warnings || []).map(w => `<p class="text-amber-700 text-sm">⚠ ${w.message}</p>`).join('');
        resultEl.innerHTML = `<div class="text-accent-700 text-sm font-medium">✓ Rule is valid</div>${warns}`;
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
      const payload = builderPayload();
      if (editId) {
        if (payload.transitions) {
          saved = await api.put(`/api/rules/${editId}`, {
            name: payload.name,
            description: payload.description,
            category: payload.category,
            yaml_content: buildYaml(),
          });
        } else {
          saved = await api.put(`/api/rules/${editId}`, payload);
        }
      } else if (payload.transitions) {
        saved = await api.post('/api/rules/from-builder', payload);
      } else {
        saved = await api.post('/api/rules/', payload);
      }
      toast(editId ? 'Rule updated' : 'Rule created', 'success');
      close();
      if (typeof loadDashboard === 'function') await loadDashboard();
      if (selectAfterSave && saved?.id) {
        selectedRuleId = saved.id;
        if (typeof renderModalRules === 'function') renderModalRules();
      }
    } catch (e) {
      toast('Save failed: ' + e.message, 'error');
    }
  }

  async function next() {
    if (step < 4) {
      setStep(step + 1);
      if (step === 4) await validate();
    }
  }

  function back() {
    if (step > 1) setStep(step - 1);
  }

  return {
    open, close, setStep, setName, setDescription, setCategory, setStates, setNeighbourhood,
    applyTemplate, addTransition, removeTransition, toggleFrom, toggleNeighbor, setTransitionTo,
    setAdvanced, next, back, save, validate,
  };
})();

function openNewRuleModal(fromSession = false) {
  RuleBuilder.open(null, fromSession ? true : null);
}

function editRule(ruleId) {
  const r = allRules.find(x => x.id === ruleId);
  if (r && r.is_editable) RuleBuilder.open(r);
  else toast('Built-in rules cannot be edited', 'warning');
}

async function deleteRule(ruleId) {
  if (!confirm('Delete this custom rule?')) return;
  try {
    await api.delete(`/api/rules/${ruleId}`);
    toast('Rule deleted', 'success');
    await loadDashboard();
  } catch (e) {
    toast('Delete failed: ' + e.message, 'error');
  }
}
