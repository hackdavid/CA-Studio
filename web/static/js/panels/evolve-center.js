/**
 * Evolve Mode - Center Panel
 * Configures center canvas for single-grid rendering of best candidate.
 */

PanelRegistry.register('evolve-center', {
  slot: 'center',
  modes: ['evolve'],
  title: 'Evolution Canvas',
  order: 0,

  render() {
    return '<div class="canvas-container h-full w-full" id="canvas-container"><canvas id="main-canvas"></canvas></div>';
  },

  onMount(container) {
    window.caGridMode = 'single';
    if (typeof drawGrid === 'function' && currentGrid) {
      drawGrid();
    }
  },
  onModeEnter() {
    window.caGridMode = 'single';
    if (typeof drawGrid === 'function' && currentGrid) {
      drawGrid();
    }
  },
  onModeExit() {
    // nothing
  }
});
