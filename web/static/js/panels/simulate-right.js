/**
 * Simulate Mode — Right Panel
 * Metrics display and session info.
 */

PanelRegistry.register('simulate-right', {
  slot: 'right',
  modes: ['simulate'],
  title: 'Metrics',
  order: 0,

  render() {
    return `
      <div class="p-4 space-y-4">
        <!-- Metrics Header -->
        <div>
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            Metrics
          </h3>
          <p class="text-xs text-slate-500">Real-time analysis</p>
        </div>

        <!-- Metric Cards (populated from session metrics_enabled) -->
        <div id="metrics-panel" class="space-y-3">
          <p class="text-xs text-slate-500 text-center py-2">Loading metrics…</p>
        </div>

        <!-- Info Section -->
        <div class="pt-4 border-t border-slate-200">
          <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Session Info</h3>
          <div class="space-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-slate-600">Board Size</span>
              <span class="font-mono font-bold text-slate-900" id="info-board-size">64×64</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Cell Size</span>
              <span class="font-mono font-bold text-slate-900" id="info-cell-size">12px</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">States (K)</span>
              <span class="font-mono font-bold text-slate-900" id="info-states">2</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-600">Rule</span>
              <span class="font-mono font-bold text-primary-700" id="info-rule">—</span>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  onMount(container) {
    // If session metrics are already known, rebuild the panel
    if (typeof buildMetricsPanel === 'function') {
      buildMetricsPanel(window.enabledMetricNames);
    }
  },

  onModeEnter() {
    // Refresh metrics display when entering simulate mode
    if (typeof buildMetricsPanel === 'function') {
      buildMetricsPanel(window.enabledMetricNames);
    }
  },

  onModeExit() {
    // Nothing to clean up
  },
});
