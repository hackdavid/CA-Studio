/**
 * Evolve Mode - Left Panel
 * Evolution controls, mask brush, and target image upload.
 */

PanelRegistry.register('evolve-left', {
  slot: 'left',
  modes: ['evolve'],
  title: 'Evolution Controls',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-5">
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
            Controls
          </h3>
          <div class="space-y-2">
            <button id="evo-btn-start" onclick="startEvolution()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-accent-600 to-green-600 text-white font-bold rounded-xl hover:from-accent-700 hover:to-green-700 transition-all shadow-md shadow-accent-500/20">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
              Start Evolution
            </button>
            <button id="evo-btn-pause" onclick="pauseEvolution()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-300 hover:border-primary-400 hover:text-primary-700 transition-all">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Pause
            </button>
            <button id="evo-btn-step" onclick="stepEvolution()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-300 hover:border-primary-400 hover:text-primary-700 transition-all">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
              Next Generation
            </button>
            <button id="evo-btn-reset" onclick="resetEvolution()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-300 hover:border-red-300 hover:text-red-600 transition-all">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
              Reset Population
            </button>
          </div>
        </div>

        <hr class="border-slate-200">

        <!-- Brush Panel (shared with simulate) -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Mask Brush</h3>
          <p class="text-xs text-slate-500 mb-3">Paint on the board to mark regions to ignore during fitness evaluation.</p>
          <div class="flex items-center justify-between">
            <label class="text-sm text-slate-700">Enable Mask</label>
            <input type="checkbox" id="evo-mask-enable" class="w-4 h-4 rounded border-slate-300 text-primary-600" onchange="toggleMaskMode(this.checked)">
          </div>
        </div>

        <hr class="border-slate-200">

        <!-- Population Settings -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Population</h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-slate-500">Size</label>
              <div class="flex items-center gap-2 mt-1">
                <input type="range" id="evo-pop-size" min="10" max="100" value="30" class="w-full accent-primary-600" oninput="document.getElementById('evo-pop-size-val').textContent=this.value">
                <span id="evo-pop-size-val" class="text-sm font-mono w-8 text-right">30</span>
              </div>
            </div>
            <div>
              <label class="text-xs text-slate-500">Mutation Rate</label>
              <div class="flex items-center gap-2 mt-1">
                <input type="range" id="evo-mutation-rate" min="0" max="50" value="5" class="w-full accent-primary-600" oninput="document.getElementById('evo-mutation-rate-val').textContent=(this.value/100).toFixed(2)">
                <span id="evo-mutation-rate-val" class="text-sm font-mono w-10 text-right">0.05</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  onMount(container) {
    console.log('[evolve-left] mounted');
  },
  onModeEnter() {
    console.log('[evolve-left] mode entered');
  },
  onModeExit() {
    console.log('[evolve-left] mode exited');
  }
});
