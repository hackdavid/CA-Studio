/**
 * Breed Mode - Right Panel
 * Population stats and history strip.
 */

PanelRegistry.register('breed-right', {
  slot: 'right',
  modes: ['breed'],
  title: 'Population Stats',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-5">
        <div class="bg-white rounded-xl border border-slate-200 p-3 text-center">
          <p class="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Generation</p>
          <p id="breed-gen-counter" class="text-2xl font-bold text-primary-700">0</p>
        </div>

        <div class="bg-white rounded-xl border border-slate-200 p-3">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Diversity</h3>
          <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div id="breed-diversity-bar" class="h-full bg-accent-500 rounded-full transition-all duration-500" style="width:0%"></div>
          </div>
          <p id="breed-diversity-val" class="text-xs text-slate-500 mt-1 text-right">0%</p>
        </div>

        <div class="bg-white rounded-xl border border-slate-200 p-3">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">History</h3>
          <div id="breed-history-strip" class="flex gap-2 overflow-x-auto pb-1">
            <p class="text-xs text-slate-400 italic">No history yet</p>
          </div>
        </div>
      </div>
    `;
  },

  onMount(container) {
    console.log('[breed-right] mounted');
  },
  onModeEnter() {
    console.log('[breed-right] mode entered');
  },
  onModeExit() {
    console.log('[breed-right] mode exited');
  }
});
