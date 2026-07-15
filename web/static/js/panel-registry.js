/**
 * CA Lab — Panel Registry
 *
 * Context-aware panel system for the simulation page.
 * Panels register themselves for specific slots (left, right, center) and modes.
 * When the mode changes, the registry unmounts old panels and mounts new ones.
 *
 * Usage:
 *   PanelRegistry.register('playback', {
 *     slot: 'left',
 *     modes: ['simulate'],
 *     title: 'Controls',
 *     render: () => '<div>...</div>',
 *     onMount: (container) => { ... },
 *     onUnmount: () => { ... },
 *     onModeEnter: () => { ... },
 *     onModeExit: () => { ... },
 *   });
 *
 *   PanelRegistry.setMode('evolve');
 */

const PanelRegistry = (function () {
  const panels = new Map();     // id -> panel definition
  const mounted = new Map();    // slot -> { id, container }
  let currentMode = 'simulate';

  function register(id, definition) {
    if (!id || !definition) return;
    if (!definition.slot || !Array.isArray(definition.modes)) {
      console.warn(`Panel ${id}: missing slot or modes`);
      return;
    }
    panels.set(id, { id, ...definition });
  }

  function getPanelsForMode(mode, slot) {
    const results = [];
    for (const def of panels.values()) {
      if (def.modes.includes(mode) && def.slot === slot) {
        results.push(def);
      }
    }
    // Sort by optional order field, default 0
    results.sort((a, b) => (a.order || 0) - (b.order || 0));
    return results;
  }

  function _getSlotContainer(slot) {
    if (slot === 'left') return document.getElementById('left-slot');
    if (slot === 'right') return document.getElementById('right-slot');
    if (slot === 'center') return document.getElementById('center-slot');
    return null;
  }

  function _unmountSlot(slot) {
    const existing = mounted.get(slot);
    if (!existing) return;
    const def = panels.get(existing.id);
    if (def && typeof def.onUnmount === 'function') {
      try { def.onUnmount(); } catch (e) { console.error(e); }
    }
    if (existing.container) {
      existing.container.innerHTML = '';
    }
    mounted.delete(slot);
  }

  function _mountPanel(def) {
    const container = _getSlotContainer(def.slot);
    if (!container) {
      console.warn(`No container for slot ${def.slot}`);
      return;
    }
    // Unmount any existing panel in this slot
    _unmountSlot(def.slot);

    // Render content
    if (typeof def.render === 'function') {
      const html = def.render();
      if (typeof html === 'string') {
        container.innerHTML = html;
      } else if (html instanceof HTMLElement) {
        container.innerHTML = '';
        container.appendChild(html);
      }
    }

    const mountInfo = { id: def.id, container };
    mounted.set(def.slot, mountInfo);

    // Lifecycle
    if (typeof def.onMount === 'function') {
      try { def.onMount(container); } catch (e) { console.error(e); }
    }
    if (typeof def.onModeEnter === 'function') {
      try { def.onModeEnter(); } catch (e) { console.error(e); }
    }
  }

  function setMode(mode) {
    if (!mode || mode === currentMode) return;
    const oldMode = currentMode;
    currentMode = mode;

    // Unmount all current panels
    for (const slot of ['left', 'right', 'center']) {
      _unmountSlot(slot);
    }

    // Notify old mode panels
    for (const def of panels.values()) {
      if (def.modes.includes(oldMode) && typeof def.onModeExit === 'function') {
        try { def.onModeExit(); } catch (e) { console.error(e); }
      }
    }

    // Mount new panels
    for (const slot of ['left', 'right', 'center']) {
      const slotPanels = getPanelsForMode(mode, slot);
      for (const def of slotPanels) {
        _mountPanel(def);
      }
    }

    // Update body attribute for CSS targeting
    document.body.setAttribute('data-mode', mode);

    // Dispatch global event
    window.dispatchEvent(new CustomEvent('ca-mode-changed', {
      detail: { mode, previous: oldMode },
    }));
  }

  function getMode() {
    return currentMode;
  }

  function getMountedIds() {
    return Array.from(mounted.values()).map(m => m.id);
  }

  return {
    register,
    setMode,
    getMode,
    getPanelsForMode,
    getMountedIds,
  };
})();
