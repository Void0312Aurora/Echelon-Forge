// Entry point: bootstraps layer state, canvas sizing, socket wiring, and
// the shared animation loop, then installs global input handlers.

import { vizState } from './store.js';
import { initTacticalLayers, mergeTacticalLayerSnapshot, workspaceLayerDefaults } from './layers.js';
import { tacticalWorkspaceDefinitions } from './symbology.js';
import {
    initTacticalMapInteractions,
    maybeDrawTacticalView,
    resizeTacticalCanvas,
} from './tactical-map.js';
import { animateUnits, camera, controls, render3D, resize3D, scene, updateCameraForFrame } from './scene3d.js';
import { renderTacticalLayerControls, updateLanguageUi } from './ui-shell.js';
import { initSession } from './session.js';
import { loadUiPrefs } from './storage.js';

// Expose shared state for DevTools debugging (read-only usage intended).
window.vizDebug = { vizState, scene, camera, controls };

// --- Bootstrap ---
initTacticalLayers();

// Restore persisted display preferences before the first render. Profile
// ui_defaults still win later because they are applied on top via
// applyProfileUiDefaults once the app status arrives.
const uiPrefs = loadUiPrefs();
if (uiPrefs.uiLanguage === 'zh' || uiPrefs.uiLanguage === 'en') {
    vizState.uiLanguage = uiPrefs.uiLanguage;
}
if (uiPrefs.dockState && typeof uiPrefs.dockState === 'object') {
    vizState.dockState.left = !!uiPrefs.dockState.left;
    vizState.dockState.right = !!uiPrefs.dockState.right;
    vizState.dockUserTouched = true;
}
if (uiPrefs.workspaceLayers && typeof uiPrefs.workspaceLayers === 'object') {
    for (const [workspaceId, snapshot] of Object.entries(uiPrefs.workspaceLayers)) {
        if (!tacticalWorkspaceDefinitions[workspaceId] || typeof snapshot !== 'object') continue;
        // Merge over the workspace defaults so layers introduced after the
        // snapshot was saved keep their default visibility.
        vizState.tacticalWorkspaceLayerState.set(
            workspaceId,
            mergeTacticalLayerSnapshot(workspaceLayerDefaults(workspaceId), snapshot)
        );
    }
}
const startupWorkspace = tacticalWorkspaceDefinitions[uiPrefs.activeWorkspace]
    ? uiPrefs.activeWorkspace
    : 'cop';

resizeTacticalCanvas();
initTacticalMapInteractions();
initSession();

renderTacticalLayerControls();
window.setTacticalWorkspace(startupWorkspace, { skipCapture: true });
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
