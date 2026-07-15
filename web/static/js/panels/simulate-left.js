/**
 * Simulate Mode — Left Panel
 * Playback controls, speed, brush, view options, zoom.
 */

PanelRegistry.register('simulate-left', {
  slot: 'left',
  modes: ['simulate'],
  title: 'Controls',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-5">
        <!-- Playback Controls -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            Controls
          </h3>
          <div class="space-y-2">
            <button id="btn-start" onclick="startSim()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-600 to-blue-600 text-white font-bold rounded-xl hover:from-primary-700 hover:to-blue-700 transition-all shadow-md shadow-primary-500/20">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Start
            </button>
            <button id="btn-pause" onclick="pauseSim()" class="control-btn w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-slate-700 font-semibold rounded-lg border-2 border-slate-300 hover:border-primary-400 hover:text-primary-700 transition-all">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              Pause
            </button>
            <div class="grid grid-cols-2 gap-2">
              <button id="btn-step" onclick="stepOnce()" class="control-btn flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-100 text-slate-700 font-medium text-sm rounded-lg border border-slate-300 hover:bg-slate-200 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
                Step
              </button>
              <button id="btn-reset" onclick="resetSim()" class="control-btn flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-100 text-slate-700 font-medium text-sm rounded-lg border border-slate-300 hover:bg-red-50 hover:border-red-300 hover:text-red-700 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                Reset
              </button>
            </div>
          </div>
        </div>

        <!-- Speed Control -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            Speed
          </h3>
          <div class="space-y-3">
            <input type="range" min="10" max="500" value="100" step="10" id="speed-slider" class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer" oninput="updateSpeed(this.value)">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="text-slate-500">Fast</span>
              <span id="speed-display" class="font-bold text-primary-700">100ms</span>
              <span class="text-slate-500">Slow</span>
            </div>
          </div>
        </div>

        <!-- State brush picker -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path></svg>
            Brush (K states)
          </h3>
          <p id="draw-hint" class="text-xs text-slate-500 mb-2">Select a color, then paint on the grid.</p>
          <div id="brush-container" class="brush-grid"></div>
        </div>

        <!-- View Options -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
            View
          </h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-700 font-medium">Grid Lines</span>
              <div class="toggle-switch active" onclick="toggleGrid(this)"></div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-700 font-medium">Cell Numbers</span>
              <div class="toggle-switch" onclick="toggleCellNumbers(this)"></div>
            </div>
          </div>
        </div>

        <!-- Zoom Controls -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"></path></svg>
            Zoom
          </h3>
          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-2">
              <button id="btn-zoom-in" onclick="zoomIn()" class="control-btn flex items-center justify-center gap-1 px-3 py-2 bg-slate-100 text-slate-700 font-medium text-sm rounded-lg border border-slate-300 hover:bg-slate-200 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                In
              </button>
              <button id="btn-zoom-out" onclick="zoomOut()" class="control-btn flex items-center justify-center gap-1 px-3 py-2 bg-slate-100 text-slate-700 font-medium text-sm rounded-lg border border-slate-300 hover:bg-slate-200 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                Out
              </button>
            </div>
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="text-slate-500">Zoom</span>
              <span id="zoom-display" class="font-bold text-primary-700">100%</span>
            </div>
            <button id="btn-zoom-reset" onclick="resetZoom()" class="control-btn w-full flex items-center justify-center gap-1 px-3 py-2 bg-white text-slate-700 font-medium text-sm rounded-lg border border-slate-300 hover:bg-slate-100 transition-colors">
              Reset View
            </button>
            <p class="text-xs text-slate-500">Wheel to zoom. Right-drag or middle-drag to pan.</p>
          </div>
        </div>
      </div>
    `;
  },

  onMount(container) {
    // If brush rendering depends on numStates, trigger it
    if (typeof renderBrushPicker === 'function') {
      renderBrushPicker();
    }
  },

  onModeEnter() {
    // Ensure simulation controls reflect current state
    if (typeof updateSpeed === 'function') {
      const slider = document.getElementById('speed-slider');
      if (slider) updateSpeed(slider.value);
    }
  },

  onModeExit() {
    // Clean up any timers if needed
  },
});
