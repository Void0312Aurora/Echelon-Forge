// Entry point: bootstraps layer state, canvas sizing, socket wiring, and
// the shared animation loop, then installs global input handlers.

import { vizState } from './store.js';
import { initTacticalLayers } from './layers.js';
import {
    initTacticalMapInteractions,
    maybeDrawTacticalView,
    resizeTacticalCanvas,
} from './tactical-map.js';
import { animateUnits, render3D, resize3D, updateCameraForFrame } from './scene3d.js';
import { renderTacticalLayerControls, updateLanguageUi } from './ui-shell.js';
import { initSession } from './session.js';

// --- Bootstrap ---
initTacticalLayers();
resizeTacticalCanvas();
initTacticalMapInteractions();
initSession();

renderTacticalLayerControls();
window.setTacticalWorkspace('cop', { skipCapture: true });
updateLanguageUi();

// --- Animation loop ---
let lastFrameTs = performance.now();

function animate() {
    requestAnimationFrame(animate);
    const now = performance.now();
    const dt = Math.min(0.05, Math.max(0.001, (now - lastFrameTs) / 1000.0));
    lastFrameTs = now;
    animateUnits(dt);
    maybeDrawTacticalView(now);
    updateCameraForFrame(dt);
    render3D();
}
animate();

// --- Global input handlers ---
window.addEventListener('resize', () => {
    resize3D();
    resizeTacticalCanvas();
});

window.addEventListener('keydown', (e) => {
    const tagName = String(e.target?.tagName || '').toUpperCase();
    const k = e.key.toLowerCase();
    if (e.key === 'Escape' && vizState.mapOnlyMode) {
        e.preventDefault();
        window.toggleMapOnlyMode(false);
        return;
    }
    if (Object.prototype.hasOwnProperty.call(vizState.keys, k)) vizState.keys[k] = true;
    if (e.key === 'Shift') vizState.keys.Shift = true;
    if (e.code === 'Space' && !e.repeat && !['SELECT', 'INPUT', 'TEXTAREA', 'BUTTON'].includes(tagName)) {
        e.preventDefault();
        window.runSessionAction();
    }
});

window.addEventListener('keyup', (e) => {
    const k = e.key.toLowerCase();
    if (Object.prototype.hasOwnProperty.call(vizState.keys, k)) vizState.keys[k] = false;
    if (e.key === 'Shift') vizState.keys.Shift = false;
});
