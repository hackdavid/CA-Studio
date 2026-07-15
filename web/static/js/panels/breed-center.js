/**
 * Breed Mode - Center Panel
 * Configures center canvas for gallery grid rendering.
 */

PanelRegistry.register('breed-center', {
  slot: 'center',
  modes: ['breed'],
  title: 'Breed Gallery',
  order: 0,

  render() {
    return '<div class="canvas-container h-full w-full" id="canvas-container"><canvas id="main-canvas"></canvas></div>';
  },

  onMount(container) {
    window.caGridMode = 'gallery';
    if (typeof drawGallery === 'function' && breedGrids.length) {
      drawGallery();
    }
  },
  onModeEnter() {
    window.caGridMode = 'gallery';
    if (typeof drawGallery === 'function' && breedGrids.length) {
      drawGallery();
    }
  },
  onModeExit() {
    window.caGridMode = 'single';
  }
});
