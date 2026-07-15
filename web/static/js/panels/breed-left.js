/**
 * Breed Mode - Left Panel
 * Population breeding controls.
 */

PanelRegistry.register('breed-left', {
  slot: 'left',
  modes: ['breed'],
  title: 'Breed Controls',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-5">
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-12 0v1z"></path></svg>
            Curation
          </h3>
          <p class="text-xs text-slate-500 mb-3">Click candidates in the grid to select parents, then breed the next generation.</p>
          <div class="space-y-2">
            <button onclick="breedNextGeneration()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-bold rounded-xl hover:from-primary-700 hover:to-purple-700 transition-all shadow-md shadow-primary-500/20">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Breed Next Gen
            </button>
            <button onclick="resetPopulation()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-300 hover:border-red-300 hover:text-red-600 transition-all">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
              New Population
            </button>
          </div>
        </div>

        <hr class="border-slate-200">

        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Mutation</h3>
          <div class="flex items-center gap-2 mt-1">
            <input type="range" id="breed-mutation-rate" min="0" max="50" value="10" class="w-full accent-primary-600" oninput="document.getElementById('breed-mutation-rate-val').textContent=(this.value/100).toFixed(2)">
            <span id="breed-mutation-rate-val" class="text-sm font-mono w-10 text-right">0.10</span>
          </div>
        </div>

        <hr class="border-slate-200">

        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Selected Parents</h3>
          <div id="breed-parents-list" class="space-y-2">
            <p class="text-xs text-slate-400 italic">No parents selected</p>
          </div>
        </div>
      </div>
    `;
  },

  onMount(container) {
    console.log('[breed-left] mounted');
  },
  onModeEnter() {
    console.log('[breed-left] mode entered');
  },
  onModeExit() {
    console.log('[breed-left] mode exited');
  }
});
