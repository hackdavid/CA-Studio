/**
 * Simulate Mode — Center Panel
 * Configures the main canvas for single-grid simulation rendering.
 */

PanelRegistry.register('simulate-center', {
  slot: 'center',
  modes: ['simulate'],
  title: 'Grid',
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
    // Nothing to clean up
  },
});
