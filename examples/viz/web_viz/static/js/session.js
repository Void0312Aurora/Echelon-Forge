// Socket.IO wiring and session control: state stream handlers, run/pause/
// speed controls, scenario / profile / asset-set loading, and profile UI
// defaults. All loading goes through the backend session manager via
// socket events; the frontend never mutates scenario content itself.

import { SPEED_STEPS } from './config.js';
import { dom } from './dom.js';
import { vizState } from './store.js';
import { formatSpeedButton } from './i18n.js';
import {
    applyTacticalLayerSnapshot,
    captureActiveWorkspaceLayers,
    mergeTacticalLayerSnapshot,
    workspaceLayerDefaults,
} from './layers.js';
import { tacticalWorkspaceDefinitions } from './symbology.js';
import { refreshAutoLayout } from './layout.js';
import {
    requestTacticalDraw,
    resetTacticalMapState,
    updateTacticalTrailHistory,
} from './tactical-map.js';
import {
    applyAssetRegistry,
    applyMapSetup,
    applyNavSetup,
    clearMapGroup,
    clearNavGroup,
    clearUnitVisuals,
    getOrSpawnUnit,
    removeUnitVisual,
    updateUnit,
} from './scene3d.js';
import { ensureSceneGeometry } from './scene-geometry.js';
import { applyIllumination } from './illumination.js';
import {
    clearErrorBanner,
    renderAssetRegistryOptions,
    renderMissionStatus,
    renderProfileOptions,
    renderScenarioOptions,
    renderUnitList,
    resetTelemetryDisplay,
    showErrorBanner,
    syncRunControl,
    updateFocusedTelemetry,
    updatePresentationModeUI,
    updateSessionLabelText,
    updateSimTimeDisplay,
    updateTacticalLayerButtons,
    updateTacticalWorkspaceUI,
} from './ui-shell.js';

let socket = null;

// Contract-version tolerance: unknown versions render best-effort but are
// reported once per channel+version so protocol drift is visible instead of
// silent. Additive changes keep the same version string.
const warnedContractVersions = new Set();
function checkContractVersion(channel, received, expected) {
    if (received === undefined || received === expected) return;
    const key = `${channel}:${received}`;
    if (warnedContractVersions.has(key)) return;
    warnedContractVersions.add(key);
    console.warn(
        `viz ${channel} contract version mismatch: got ${JSON.stringify(received)}, `
        + `frontend expects ${expected}; rendering best-effort`,
    );
}

export function resetVizScene() {
    clearUnitVisuals();
    clearNavGroup();
    clearMapGroup();
    vizState.simTime = 0;
    resetTelemetryDisplay();
    renderMissionStatus(null);
    resetTacticalMapState();
}

// --- Run controls ---
window.startSim = function () {
    socket.emit('start_sim');
    vizState.sessionControlState.running = true;
    vizState.sessionControlState.paused = false;
    syncRunControl();
};

window.pauseSim = function () {
    socket.emit('pause_sim');
    vizState.sessionControlState.running = true;
    vizState.sessionControlState.paused = true;
    syncRunControl();
};

window.resumeSim = function () {
    socket.emit('resume_sim');
    vizState.sessionControlState.running = true;
    vizState.sessionControlState.paused = false;
    syncRunControl();
};

window.runSessionAction = function () {
    const control = vizState.sessionControlState;
    if (!control.loaded || !control.ready) return;
    if (control.paused) {
        window.resumeSim();
        return;
    }
    if (control.running) {
        window.pauseSim();
        return;
    }
    window.startSim();
};

// --- Speed controls ---
function setSpeed(value) {
    vizState.simSpeed = Number(value);
    socket.emit('set_speed', { value });
    dom.btnSpeed.innerText = formatSpeedButton(value);
}

window.adjustSpeed = function (dir) {
    const idx = Math.max(0, SPEED_STEPS.indexOf(vizState.simSpeed));
    const nextIdx = Math.max(0, Math.min(SPEED_STEPS.length - 1, idx + dir));
    setSpeed(SPEED_STEPS[nextIdx]);
};

window.resetSpeed = function () {
    setSpeed(1);
};

// --- Session loading ---
window.loadSelectedProfile = function () {
    const profile = String(dom.profileSelect.value || '').trim();
    if (!profile) return;
    socket.emit('viz_load_profile', { profile });
};

window.loadSelectedScenario = function () {
    const scenario = String(dom.scenarioSelect.value || '').trim();
    if (!scenario) return;
    socket.emit('viz_load_session', { scenario });
};

window.loadSelectedAssetRegistry = function () {
    const assetRegistry = String(dom.assetRegistrySelect.value || '').trim();
    if (!assetRegistry) return;
    socket.emit('viz_load_asset_registry', { asset_registry: assetRegistry });
};

window.reloadCurrentScenario = function () {
    if (vizState.currentProfile) {
        socket.emit('viz_reload_session', { profile: vizState.currentProfile });
        return;
    }
    const scenario = vizState.currentScenario || String(dom.scenarioSelect.value || '').trim();
    if (!scenario) return;
    socket.emit('viz_reload_session', { scenario });
};

window.stopCurrentSession = function () {
    socket.emit('viz_stop_session');
};

// --- App status ---
export function updateSessionButtonState(appStatus) {
    const session = appStatus?.session || null;
    const loaded = !!appStatus?.loaded && !!session;
    const sessionError = String(session?.error || '').trim();
    vizState.sessionReady = !!session?.ready;
    vizState.sessionControlState = {
        loaded,
        ready: !!session?.ready,
        running: !!session?.running,
        paused: !!session?.paused,
        error: sessionError,
    };
    if (sessionError) {
        showErrorBanner(sessionError);
    } else if (vizState.sessionControlState.ready) {
        clearErrorBanner();
    }
    vizState.currentScenario = loaded ? String(session.scenario || '') : '';
    if (appStatus && Object.prototype.hasOwnProperty.call(appStatus, 'profile')) {
        vizState.currentProfile = String(appStatus?.profile?.path || '').trim();
        vizState.currentProfileUiDefaults = appStatus?.profile?.ui_defaults || null;
        if (!vizState.currentProfile) vizState.appliedProfileUiDefaultsKey = '';
    }
    if (appStatus && Object.prototype.hasOwnProperty.call(appStatus, 'asset_registry')) {
        applyAssetRegistry(appStatus.asset_registry);
    }
    if (appStatus && Object.prototype.hasOwnProperty.call(appStatus, 'scene_geometry')) {
        const sceneGeo = appStatus.scene_geometry;
        // Key by the backend-computed cache key (load generation + digest),
        // never by the bundle's self-declared id, which is unvalidated and
        // could be empty or collide across bundles.
        ensureSceneGeometry(sceneGeo?.available ? (sceneGeo.cache_key || `fallback:${sceneGeo.bundle_id || ''}`) : null);
    }

    if (Array.isArray(appStatus?.profiles)) {
        renderProfileOptions(appStatus.profiles);
    }
    if (Array.isArray(appStatus?.asset_registries)) {
        renderAssetRegistryOptions(appStatus.asset_registries);
    }

    if (Array.isArray(appStatus?.scenarios)) {
        renderScenarioOptions(appStatus.scenarios);
    }
    if (vizState.currentProfile) {
        dom.profileSelect.value = vizState.currentProfile;
    }
    if (vizState.currentAssetRegistry?.path) {
        dom.assetRegistrySelect.value = vizState.currentAssetRegistry.path;
    }
    if (vizState.currentScenario && vizState.vizScenarioList.includes(vizState.currentScenario)) {
        dom.scenarioSelect.value = vizState.currentScenario;
    }

    if (!loaded) {
        resetVizScene();
        updateSessionLabelText();
        dom.btnReload.disabled = true;
        dom.btnStop.disabled = true;
        dom.btnLoad.disabled = vizState.vizScenarioList.length === 0;
        dom.btnLoadProfile.disabled = vizState.vizProfileList.length === 0;
        dom.btnLoadAssetRegistry.disabled = vizState.vizAssetRegistryList.length === 0;
        syncRunControl();
        refreshAutoLayout({ redraw: true });
        return;
    }

    updateSessionLabelText();
    dom.btnLoad.disabled = false;
    dom.btnReload.disabled = false;
    dom.btnStop.disabled = false;
    dom.btnLoadProfile.disabled = vizState.vizProfileList.length === 0;
    dom.btnLoadAssetRegistry.disabled = vizState.vizAssetRegistryList.length === 0;
    syncRunControl();
    refreshAutoLayout({ redraw: true });
}

// --- Profile UI defaults ---
export function applyProfileUiDefaults() {
    if (!vizState.currentProfile || !vizState.currentProfileUiDefaults) return;
    const defaultsKey = `${vizState.currentProfile}|${JSON.stringify(vizState.currentProfileUiDefaults)}`;
    if (vizState.appliedProfileUiDefaultsKey === defaultsKey) return;
    vizState.appliedProfileUiDefaultsKey = defaultsKey;

    const ui = vizState.currentProfileUiDefaults || {};
    const nextPresentationMode = String(ui.presentation_mode || '').toUpperCase();
    const nextCameraMode = String(ui.camera_mode || '').toUpperCase();
    const nextWorkspace = String(ui.tactical_workspace || '').trim();
    const hasProfileLayerDefaults = ui.tactical_layers && typeof ui.tactical_layers === 'object';
    const nextMapOnly = typeof ui.map_only === 'boolean' ? ui.map_only : null;
    const nextZoom = Number(ui.tactical_zoom);

    if (nextPresentationMode === 'MAP' || nextPresentationMode === '3D') {
        vizState.presentationMode = nextPresentationMode;
    }
    if (nextCameraMode === 'CHASE' || nextCameraMode === 'FREE') {
        vizState.viewMode = nextCameraMode;
    }
    if (Number.isFinite(nextZoom) && nextZoom > 0.0) {
        vizState.tacticalInteraction.zoom = Math.max(0.35, Math.min(12.0, nextZoom));
        vizState.tacticalInteraction.mode = 'auto';
    }

    let targetWorkspace = '';
    if (tacticalWorkspaceDefinitions[nextWorkspace]) {
        targetWorkspace = nextWorkspace;
    } else if (vizState.presentationMode === '3D') {
        targetWorkspace = 'inspect3d';
    } else if (vizState.presentationMode === 'MAP' && vizState.activeTacticalWorkspace === 'inspect3d') {
        targetWorkspace = vizState.lastMapTacticalWorkspace || 'cop';
    }

    const baseWorkspace = targetWorkspace || vizState.activeTacticalWorkspace || 'cop';
    const profileLayers = hasProfileLayerDefaults
        ? mergeTacticalLayerSnapshot(workspaceLayerDefaults(baseWorkspace), ui.tactical_layers)
        : null;

    if (targetWorkspace) {
        window.setTacticalWorkspace(targetWorkspace, { skipCapture: true, layers: profileLayers });
        if (nextMapOnly !== null) window.toggleMapOnlyMode(nextMapOnly);
        return;
    }
    if (profileLayers) {
        applyTacticalLayerSnapshot(profileLayers);
        captureActiveWorkspaceLayers();
        updateTacticalLayerButtons();
    }
    updateTacticalWorkspaceUI();
    updatePresentationModeUI();
    if (nextMapOnly !== null) window.toggleMapOnlyMode(nextMapOnly);
    requestTacticalDraw();
}

// --- Socket wiring ---
export function initSession() {
    socket = io({ transports: ['websocket'] });

    socket.on('connect', () => {
        vizState.socketConnected = true;
        updateSessionLabelText();
    });

    socket.on('disconnect', () => {
        vizState.socketConnected = false;
        updateSessionLabelText();
    });

    socket.on('viz_error', (data) => {
        showErrorBanner(String(data?.message || ''));
    });

    socket.on('map_setup', (data) => {
        checkContractVersion('map_setup', data?.contract_version, 'examples.viz.map_setup.v1');
        const zones = Array.isArray(data?.zones) ? data.zones : [];
        console.log(`Map setup received: ${zones.length} zones`);
        vizState.environmentOverlays = data.environment_overlays || null;
        applyIllumination(data?.illumination);
        requestTacticalDraw();
        applyMapSetup(zones);
    });

    socket.on('nav_setup', (data) => {
        applyNavSetup(data?.markers);
    });

    socket.on('state_update', (state) => {
        checkContractVersion('state_update', state?.contract_version, 'examples.viz.state_frame.v1');
        const frameAt = performance.now();
        if (vizState.lastStateFrameAt !== null) {
            const interval = Math.max(1.0, frameAt - vizState.lastStateFrameAt);
            vizState.smoothedStateFrameIntervalMs = vizState.smoothedStateFrameIntervalMs * 0.82 + interval * 0.18;
        }
        vizState.lastStateFrameAt = frameAt;
        vizState.simTime = state.tick;
        updateSimTimeDisplay(vizState.simTime);
        renderMissionStatus(state.mission_status);
        updateTacticalTrailHistory(state.units);

        const activeIds = new Set();

        state.units.forEach(uData => {
            activeIds.add(uData.id);
            const uObj = getOrSpawnUnit(uData);
            updateUnit(uObj, uData, frameAt);

            if (uData.id === vizState.focusedId) {
                updateFocusedTelemetry(uData);
            }
        });

        vizState.lastTacticalState = state;
        requestTacticalDraw();

        Array.from(vizState.units.keys()).forEach((id) => {
            if (!activeIds.has(id)) {
                removeUnitVisual(id);
            }
        });
        if (vizState.focusedId === null && vizState.units.size > 0) {
            vizState.focusedId = Array.from(vizState.units.keys())[0];
        }
        renderUnitList();
    });

    socket.on('speed_update', (data) => {
        const value = Number(data?.value);
        if (!Number.isFinite(value) || value < 0.05) return;
        vizState.simSpeed = value;
        dom.btnSpeed.innerText = formatSpeedButton(vizState.simSpeed);
    });

    socket.on('viz_app_status', (status) => {
        updateSessionButtonState(status);
        applyProfileUiDefaults();
    });

    socket.on('viz_session_status', (status) => {
        updateSessionButtonState({
            loaded: !!status?.scenario,
            session: status,
            scenarios: vizState.vizScenarioList,
        });
    });
}
