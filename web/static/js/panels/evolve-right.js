/**
 * Evolve Mode - Right Panel
 * Evolution dashboard: generation counter, fitness plot, fitness breakdown, constraints.
 */

PanelRegistry.register('evolve-right', {
  slot: 'right',
  modes: ['evolve'],
  title: 'Evolution Dashboard',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-5">
        <!-- Target Image -->
        <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div class="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider">Target Image</h3>
            <span id="evo-target-label" class="text-[10px] text-slate-500">none</span>
          </div>
          <div id="evo-target-preview" class="h-32 bg-slate-100 flex items-center justify-center">
            <p class="text-xs text-slate-400">Upload an image from the session modal</p>
          </div>
        </div>

        <!-- Generation Counter -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-white rounded-xl border border-slate-200 p-3 text-center">
            <p class="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Generation</p>
            <p id="evo-gen-counter" class="text-2xl font-bold text-primary-700">0</p>
          </div>
          <div class="bg-white rounded-xl border border-slate-200 p-3 text-center">
            <p class="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Best Fitness</p>
            <p id="evo-best-fitness" class="text-2xl font-bold text-green-600">—</p>
          </div>
        </div>

        <!-- Fitness Sparkline -->
        <div class="bg-white rounded-xl border border-slate-200 p-3">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
            Fitness Over Time
          </h3>
          <canvas id="evo-fitness-chart" width="260" height="100" class="w-full h-24"></canvas>
        </div>

        <!-- Fitness Breakdown -->
        <div class="bg-white rounded-xl border border-slate-200 p-3">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Fitness Breakdown</h3>
          <div class="space-y-2">
            <div>
              <div class="flex justify-between text-xs mb-1"><span>Similarity</span><span id="evo-score-similarity">—</span></div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden"><div id="evo-bar-similarity" class="h-full bg-accent-500 rounded-full transition-all duration-500" style="width:0%"></div></div>
            </div>
            <div>
              <div class="flex justify-between text-xs mb-1"><span>Metrics</span><span id="evo-score-metrics">—</span></div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden"><div id="evo-bar-metrics" class="h-full bg-blue-500 rounded-full transition-all duration-500" style="width:0%"></div></div>
            </div>
            <div>
              <div class="flex justify-between text-xs mb-1"><span>Simplicity</span><span id="evo-score-simplicity">—</span></div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden"><div id="evo-bar-simplicity" class="h-full bg-teal-500 rounded-full transition-all duration-500" style="width:0%"></div></div>
            </div>
          </div>
        </div>

        <!-- Constraints -->
        <div class="bg-white rounded-xl border border-slate-200 p-3">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Constraints</h3>
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
              <input type="checkbox" id="evo-constrain-lock-rule" class="w-4 h-4 rounded border-slate-300 text-primary-600">
              Lock rule (evolve seed only)
            </label>
            <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
              <input type="checkbox" id="evo-constrain-lock-seed" class="w-4 h-4 rounded border-slate-300 text-primary-600">
              Lock seed (evolve rule only)
            </label>
            <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
              <input type="checkbox" id="evo-constrain-symmetry" class="w-4 h-4 rounded border-slate-300 text-primary-600">
              Force symmetry
            </label>
          </div>
        </div>

        <!-- Save Best -->
        <button onclick="saveBestRule()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-bold rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all shadow-md shadow-primary-500/20">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
          Save Best Rule
        </button>
      </div>
    `;
  },

  onMount(container) {
    this._onUpdate = (e) => this._updateDashboard(e.detail);
    this._onDone = (e) => this._markDone(e.detail);
    window.addEventListener('ca-evolution-update', this._onUpdate);
    window.addEventListener('ca-evolution-done', this._onDone);

    this.fitnessHistory = [];
    this.canvas = container.querySelector('#evo-fitness-chart');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }
  },

  onUnmount() {
    window.removeEventListener('ca-evolution-update', this._onUpdate);
    window.removeEventListener('ca-evolution-done', this._onDone);
  },

  onModeEnter() {
    console.log('[evolve-right] mode entered');
  },
  onModeExit() {
    console.log('[evolve-right] mode exited');
  },

  _updateDashboard(msg) {
    const container = document.getElementById('right-slot');
    if (!container) return;

    const genEl = container.querySelector('#evo-gen-counter');
    const fitEl = container.querySelector('#evo-best-fitness');
    if (genEl) genEl.textContent = msg.generation ?? '—';
    if (fitEl) fitEl.textContent = msg.best_fitness_ever != null ? msg.best_fitness_ever.toFixed(4) : '—';

    // Update fitness breakdown (server doesn't send breakdown yet, so use placeholder)
    const simEl = container.querySelector('#evo-score-similarity');
    const simBar = container.querySelector('#evo-bar-similarity');
    if (simEl && simBar) {
      const sim = msg.best_fitness != null ? (msg.best_fitness * 0.5).toFixed(2) : '—';
      simEl.textContent = sim;
      simBar.style.width = (msg.best_fitness != null ? msg.best_fitness * 50 : 0) + '%';
    }

    // Sparkline
    if (msg.best_fitness_ever != null) {
      this.fitnessHistory.push(msg.best_fitness_ever);
      if (this.fitnessHistory.length > 50) this.fitnessHistory.shift();
      this._drawSparkline();
    }
  },

  _markDone(msg) {
    const container = document.getElementById('right-slot');
    if (container) {
      const fitEl = container.querySelector('#evo-best-fitness');
      if (fitEl) fitEl.textContent = msg.best_fitness?.toFixed(4) || '—';
    }
  },

  _drawSparkline() {
    if (!this.ctx || this.fitnessHistory.length < 2) return;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, w, h);

    const data = this.fitnessHistory;
    const min = Math.min(...data, 0);
    const max = Math.max(...data, 1);
    const range = max - min || 1;

    ctx.strokeStyle = '#0ea5e9';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < data.length; i++) {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((data[i] - min) / range) * (h - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Fill area
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = 'rgba(14,165,233,0.1)';
    ctx.fill();
  }
});
