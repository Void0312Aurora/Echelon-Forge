// UI chrome: workspace tabs, layer buttons, presentation / map-only /
// language toggles, telemetry + mission panels, unit list, and the session
// selector dropdowns. Display-only: nothing here mutates scenario state.

import { dom, getById } from './dom.js';
import { vizState } from './store.js';
import {
    tacticalLayerGroups,
    tacticalLayerKeys,
    tacticalLayerSpec,
    tacticalWorkspaceDefinitions,
} from './symbology.js';
import {
    i18n,
    formatSpeedButton,
    localizeCameraMode,
    localizeMissionLabel,
    localizedLayerText,
    localizedWorkspaceText,
    updateStaticI18nText,
} from './i18n.js';
import {
    applyTacticalLayerSnapshot,
    captureActiveWorkspaceLayers,
    tacticalLayerSnapshot,
    workspaceLayerDefaults,
} from './layers.js';
import { resolveAssetEntry } from './asset-registry.js';
import { refreshAutoLayout } from './layout.js';
import { requestTacticalDraw } from './tactical-map.js';
import { renderer, controls } from './scene3d.js';

// --- Map-only mode ---
export function updateMapOnlyControls() {
    document.documentElement.dataset.mapOnly = vizState.mapOnlyMode ? 'true' : 'false';
    if (dom.mapOnlyButton) {
        dom.mapOnlyButton.innerText = vizState.mapOnlyMode ? i18n('ui.exitMap') : i18n('ui.mapOnly');
        dom.mapOnlyButton.classList.toggle('active', vizState.mapOnlyMode);
        dom.mapOnlyButton.setAttribute('aria-pressed', vizState.mapOnlyMode ? 'true' : 'false');
    }
    if (dom.mapOnlyExitButton) {
        dom.mapOnlyExitButton.innerText = i18n('ui.exitMap');
        dom.mapOnlyExitButton.hidden = !vizState.mapOnlyMode;
        dom.mapOnlyExitButton.setAttribute('aria-hidden', vizState.mapOnlyMode ? 'false' : 'true');
    }
}

window.toggleMapOnlyMode = function (force) {
    const next = typeof force === 'boolean' ? force : !vizState.mapOnlyMode;
    if (next === vizState.mapOnlyMode) return;
    vizState.mapOnlyMode = next;
    if (vizState.mapOnlyMode && vizState.presentationMode !== 'MAP') {
        window.setTacticalWorkspace(vizState.lastMapTacticalWorkspace || 'cop', { skipCapture: true });
        return;
    }
    updatePresentationModeUI();
};

// --- Presentation mode (MAP vs 3D, driven by the workspace tabs) ---
export function updatePresentationModeUI() {
    const mapMode = vizState.presentationMode === 'MAP';
    if (!mapMode && vizState.mapOnlyMode) {
        vizState.mapOnlyMode = false;
    }
    updateMapOnlyControls();
    dom.vizShell?.classList.toggle('viz-shell--3d', !mapMode);
    dom.tacticalPanel.classList.toggle('hidden', !mapMode);
    renderer.domElement.style.opacity = mapMode ? '0.16' : '1.0';
    renderer.domElement.style.pointerEvents = mapMode ? 'none' : 'auto';
    controls.enabled = !mapMode;
    controls.enablePan = (!mapMode && vizState.viewMode !== 'CHASE');
    dom.btnCam.innerText = `${i18n('ui.camera')}: ${localizeCameraMode(vizState.viewMode)}`;
    dom.btnCam.style.display = mapMode ? 'none' : '';
    refreshAutoLayout({ redraw: true });
}

window.toggleCamera = function () {
    vizState.viewMode = vizState.viewMode === 'CHASE' ? 'FREE' : 'CHASE';
    vizState.chaseTargetPrev = null;
    updatePresentationModeUI();
};

// --- Tactical layer controls ---
export function renderTacticalLayerControls() {
    const container = dom.tacticalLayerControls;
    if (!container) return;
    container.innerHTML = '';
    for (const group of tacticalLayerGroups) {
        const groupEl = document.createElement('div');
        groupEl.className = 'tactical-layer-group';
        groupEl.dataset.layerGroup = group.id;

        const header = document.createElement('div');
        header.className = 'tactical-layer-group-header';
        const title = document.createElement('span');
        title.className = 'tactical-layer-group-title';
        title.innerText = i18n(`layerGroup.${group.id}.label`, group.label);
        const role = document.createElement('span');
        role.className = 'tactical-layer-group-role';
        role.innerText = i18n(`layerGroup.${group.id}.role`, group.role);
        header.append(title, role);

        const buttons = document.createElement('div');
        buttons.className = 'tactical-layer-group-buttons';
        for (const key of group.layerKeys) {
            const spec = tacticalLayerSpec(key);
            const button = document.createElement('button');
            button.id = spec.buttonId;
            button.type = 'button';
            button.className = 'tactical-layer-button';
            button.dataset.layerKey = key;
            button.innerText = localizedLayerText(key, 'short');
            button.setAttribute('aria-label', `${localizedLayerText(key, 'label')} ${i18n('ui.layerSuffix')}`);
            button.onclick = () => window.toggleTacticalLayer(key);
            buttons.appendChild(button);
        }

        groupEl.append(header, buttons);
        container.appendChild(groupEl);
    }
}

export function updateTacticalLayerButtons() {
    for (const key of tacticalLayerKeys) {
        const button = getById(tacticalLayerSpec(key).buttonId);
        if (!button) continue;
        button.classList.toggle('active', !!vizState.tacticalLayers[key]);
        button.setAttribute('aria-pressed', vizState.tacticalLayers[key] ? 'true' : 'false');
    }
}

window.toggleTacticalLayer = function (layerName) {
    if (!Object.prototype.hasOwnProperty.call(vizState.tacticalLayers, layerName)) return;
    vizState.tacticalLayers[layerName] = !vizState.tacticalLayers[layerName];
    captureActiveWorkspaceLayers();
    updateTacticalLayerButtons();
    updateTacticalWorkspaceUI();
    requestTacticalDraw();
};

// --- Workspaces ---
export function updateWorkspaceTabLabels() {
    for (const workspaceId of Object.keys(tacticalWorkspaceDefinitions)) {
        const tab = getById(`workspace-tab-${workspaceId}`);
        if (tab) tab.innerText = localizedWorkspaceText(workspaceId, 'label');
    }
}

export function updateTacticalWorkspaceUI() {
    document.documentElement.dataset.tacticalWorkspace = vizState.activeTacticalWorkspace;
    for (const workspaceId of Object.keys(tacticalWorkspaceDefinitions)) {
        const tab = getById(`workspace-tab-${workspaceId}`);
        if (!tab) continue;
        const active = workspaceId === vizState.activeTacticalWorkspace;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-pressed', active ? 'true' : 'false');
    }

    if (dom.workspaceName) dom.workspaceName.innerText = localizedWorkspaceText(vizState.activeTacticalWorkspace, 'label');
    if (dom.workspaceRole) dom.workspaceRole.innerText = localizedWorkspaceText(vizState.activeTacticalWorkspace, 'role');
    if (!dom.workspaceLayerSummary) return;

    // Summarize only the layers that are actually enabled; the full on/off
    // matrix already lives in the layer buttons right below.
    dom.workspaceLayerSummary.innerHTML = '';
    const activeKeys = tacticalLayerKeys.filter((key) => !!vizState.tacticalLayers[key]);
    if (activeKeys.length === 0) {
        const chip = document.createElement('span');
        chip.className = 'workspace-chip';
        chip.innerText = '--';
        dom.workspaceLayerSummary.appendChild(chip);
        return;
    }
    for (const key of activeKeys) {
        const chip = document.createElement('span');
        chip.className = 'workspace-chip active';
        chip.innerText = localizedLayerText(key, 'summary');
        dom.workspaceLayerSummary.appendChild(chip);
    }
}

window.setTacticalWorkspace = function (workspaceId, options = {}) {
    const nextId = String(workspaceId || '').trim();
    const nextWorkspace = tacticalWorkspaceDefinitions[nextId];
    if (!nextWorkspace) return;
    if (!options.skipCapture) captureActiveWorkspaceLayers();

    vizState.activeTacticalWorkspace = nextId;
    if (nextWorkspace.viewMode === 'MAP') {
        vizState.lastMapTacticalWorkspace = nextId;
    }

    const requestedLayers = options.layers
        ? tacticalLayerSnapshot(options.layers)
        : null;
    if (requestedLayers) {
        vizState.tacticalWorkspaceLayerState.set(nextId, requestedLayers);
    }
    const storedLayers = requestedLayers || vizState.tacticalWorkspaceLayerState.get(nextId);
    applyTacticalLayerSnapshot(storedLayers || workspaceLayerDefaults(nextId));
    vizState.presentationMode = nextWorkspace.viewMode === '3D' ? '3D' : 'MAP';

    updateTacticalLayerButtons();
    updateTacticalWorkspaceUI();
    updatePresentationModeUI();
    requestTacticalDraw();
};

// --- Language ---
export function updateLanguageUi() {
    updateStaticI18nText();
    updateWorkspaceTabLabels();
    if (dom.languageButton) dom.languageButton.innerText = i18n('ui.languageButton');
    if (dom.btnToggleLeft) dom.btnToggleLeft.innerText = i18n('ui.setup');
    if (dom.btnToggleRight) dom.btnToggleRight.innerText = i18n('ui.data');
    if (dom.btnReload) dom.btnReload.innerText = i18n('ui.reload');
    if (dom.btnStop) dom.btnStop.innerText = i18n('ui.stop');
    if (dom.btnSpeedDown) dom.btnSpeedDown.innerText = i18n('ui.slow');
    if (dom.btnSpeedUp) dom.btnSpeedUp.innerText = i18n('ui.fast');
    dom.btnSpeed.innerText = formatSpeedButton(vizState.simSpeed);
    dom.btnSpeed.title = i18n('ui.speedResetTitle');
    updateSessionLabelText();
    renderTacticalLayerControls();
    updateTacticalLayerButtons();
    updateTacticalWorkspaceUI();
    updatePresentationModeUI();
    syncRunControl();
    renderProfileOptions(vizState.vizProfileList);
    renderScenarioOptions(vizState.vizScenarioList);
    renderAssetRegistryOptions(vizState.vizAssetRegistryList);
    if (vizState.currentScenario && vizState.vizScenarioList.includes(vizState.currentScenario)) {
        dom.scenarioSelect.value = vizState.currentScenario;
    }
    if (vizState.currentProfile) dom.profileSelect.value = vizState.currentProfile;
    if (vizState.currentAssetRegistry?.path) {
        dom.assetRegistrySelect.value = vizState.currentAssetRegistry.path;
    }
    if (!vizState.lastTacticalState) {
        dom.tacticalScale.innerText = i18n('ui.scaleEmpty');
    }
    requestTacticalDraw();
}

window.toggleUiLanguage = function () {
    vizState.uiLanguage = vizState.uiLanguage === 'zh' ? 'en' : 'zh';
    updateLanguageUi();
};

// --- Session label and run control ---
function sessionLedState(control) {
    if (!control.loaded) return 'unloaded';
    if (control.paused) return 'paused';
    if (control.running) return 'running';
    return control.ready ? 'ready' : 'loading';
}

export function updateSessionLabelText() {
    const label = dom.sessionLabel;
    if (!label) return;
    const control = vizState.sessionControlState;
    if (dom.sessionLed) dom.sessionLed.dataset.state = sessionLedState(control);
    if (!control.loaded) {
        label.innerText = vizState.currentProfile
            ? `${i18n('ui.unloaded')} | ${i18n('ui.profileSuffix')} ${vizState.currentProfile}`
            : i18n('ui.unloaded');
        return;
    }
    const stateKey = control.paused
        ? 'ui.paused'
        : control.running
            ? 'ui.running'
            : control.ready
                ? 'ui.ready'
                : 'ui.loading';
    const profileSuffix = vizState.currentProfile ? ` | ${i18n('ui.profileSuffix')} ${vizState.currentProfile}` : '';
    label.innerText = `${i18n(stateKey)} | ${vizState.currentScenario || '--'}${profileSuffix}`;
}

export function syncRunControl() {
    const btnStart = dom.btnStart;
    const control = vizState.sessionControlState;
    if (!control.loaded) {
        btnStart.disabled = true;
        btnStart.innerText = i18n('ui.start');
        return;
    }
    if (!control.ready) {
        btnStart.disabled = true;
        btnStart.innerText = i18n('ui.loading');
        return;
    }
    btnStart.disabled = false;
    if (control.paused) {
        btnStart.innerText = i18n('ui.resume');
        return;
    }
    btnStart.innerText = control.running ? i18n('ui.pause') : i18n('ui.start');
}

// --- Selector dropdowns ---
export function renderProfileOptions(profiles) {
    const select = dom.profileSelect;
    select.innerHTML = '';
    const items = Array.isArray(profiles) ? profiles : [];
    vizState.vizProfileList = items.slice();
    if (items.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.innerText = i18n('ui.noProfiles');
        select.appendChild(option);
        return;
    }
    const scenarioOnlySession = !!vizState.sessionControlState.loaded && !!vizState.currentScenario && !vizState.currentProfile;
    if (scenarioOnlySession) {
        const option = document.createElement('option');
        option.value = '';
        option.innerText = i18n('ui.scenarioOnly');
        option.title = i18n('ui.scenarioOnlyTitle');
        select.appendChild(option);
    }
    items.forEach((profile) => {
        const path = String(profile?.path || '').trim();
        const name = String(profile?.name || path || '--');
        const option = document.createElement('option');
        option.value = path;
        option.innerText = name;
        option.title = String(profile?.description || path || '');
        select.appendChild(option);
    });
    const knownPaths = items.map((item) => String(item?.path || '').trim()).filter(Boolean);
    const desired = vizState.currentProfile && knownPaths.includes(vizState.currentProfile)
        ? vizState.currentProfile
        : scenarioOnlySession ? '' : (knownPaths[0] || '');
    select.value = desired;
}

export function renderScenarioOptions(scenarios) {
    const select = dom.scenarioSelect;
    select.innerHTML = '';
    const items = Array.isArray(scenarios) ? scenarios : [];
    vizState.vizScenarioList = items.slice();
    if (items.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.innerText = i18n('ui.noScenarios');
        select.appendChild(option);
        return;
    }
    items.forEach((scenario) => {
        const option = document.createElement('option');
        option.value = scenario;
        option.innerText = scenario;
        select.appendChild(option);
    });
    const desired = vizState.currentScenario && items.includes(vizState.currentScenario) ? vizState.currentScenario : items[0];
    select.value = desired;
}

export function renderAssetRegistryOptions(registries) {
    const select = dom.assetRegistrySelect;
    select.innerHTML = '';
    const items = Array.isArray(registries) ? registries : [];
    vizState.vizAssetRegistryList = items.slice();
    if (items.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.innerText = i18n('ui.noAssetSets');
        select.appendChild(option);
        return;
    }
    items.forEach((registry) => {
        const path = String(registry?.path || '').trim();
        const name = String(registry?.name || path || '--');
        const option = document.createElement('option');
        option.value = path;
        option.innerText = name;
        option.title = String(registry?.description || path || '');
        select.appendChild(option);
    });
    const currentPath = String(vizState.currentAssetRegistry?.path || '').trim();
    const knownPaths = items.map((item) => String(item?.path || '').trim()).filter(Boolean);
    const desired = currentPath && knownPaths.includes(currentPath) ? currentPath : (knownPaths[0] || '');
    select.value = desired;
}

// --- Unit list ---
// The unit list only rebuilds when its content signature changes; the
// state_update stream calls this every frame, and rebuilding DOM plus
// re-measuring the layout each time is wasted work.
let lastUnitListSignature = null;

function unitListSignature() {
    const parts = [
        String(vizState.focusedId),
        vizState.uiLanguage,
        String(vizState.currentAssetRegistry?.path || ''),
        String(Array.isArray(vizState.currentAssetRegistry?.entries) ? vizState.currentAssetRegistry.entries.length : 0),
    ];
    vizState.units.forEach((u) => {
        parts.push(`${u.data.id}\u0001${u.data.name || ''}\u0001${u.usingRegistryAsset ? 1 : 0}`);
    });
    return parts.join('\u0002');
}

export function renderUnitList() {
    const signature = unitListSignature();
    if (signature === lastUnitListSignature) return;
    lastUnitListSignature = signature;

    const list = dom.unitListContent;
    list.innerHTML = '';
    vizState.units.forEach(u => {
        const div = document.createElement('div');
        div.className = 'unit-item' + (u.id === vizState.focusedId ? ' active' : '');
        div.dataset.side = String(u.data.side || 'Unknown');
        const assetEntry = resolveAssetEntry(u.data);
        const title = document.createElement('div');
        title.innerText = `[${u.data.id}] ${u.data.name || i18n('ui.unitFallback', 'Unit')}`;
        div.appendChild(title);
        if (assetEntry?.realism?.substitute_for || assetEntry?.realism?.realism_note) {
            const meta = document.createElement('div');
            meta.className = 'unit-meta';
            const noteParts = [];
            if (assetEntry.realism.substitute_for) {
                noteParts.push(`<em>SUBSTITUTE</em> for ${assetEntry.realism.substitute_for}`);
            }
            if (assetEntry.realism.realism_note) {
                noteParts.push(assetEntry.realism.realism_note);
            }
            meta.innerHTML = noteParts.join('<br>');
            div.appendChild(meta);
        }
        div.onclick = () => setFocus(u.id);
        list.appendChild(div);
    });
    refreshAutoLayout();
}

export function setFocus(id) {
    vizState.focusedId = id;
    vizState.chaseTargetPrev = null;
    renderUnitList();
}
window.setFocus = setFocus;

// --- Telemetry and mission panels ---
export function updateSimTimeDisplay(simTime) {
    dom.telemetryTime.innerText = simTime.toFixed(2) + " s";
}

export function updateFocusedTelemetry(uData) {
    dom.telemetryName.innerText = uData.name || uData.id;
    dom.telemetryAlt.innerText = uData.z.toFixed(0) + " m";
    const ias = Number.isFinite(uData.ias) ? uData.ias : (uData.speed || 0);
    const gs = Number.isFinite(uData.speed) ? uData.speed : 0;
    dom.telemetrySpd.innerText = `${ias.toFixed(1)} / ${gs.toFixed(1)} m/s`;
    dom.telemetryHdg.innerText = uData.heading.toFixed(0);
    dom.telemetryPitch.innerText = (uData.pitch || 0).toFixed(1);
    dom.telemetryRoll.innerText = (uData.roll || 0).toFixed(1);
}

export function resetTelemetryDisplay() {
    dom.telemetryTime.innerText = '0.00 s';
    dom.telemetryName.innerText = '--';
    dom.telemetryAlt.innerText = '0.0 m';
    dom.telemetrySpd.innerText = '0.0 / 0.0 m/s';
    dom.telemetryHdg.innerText = '000';
    dom.telemetryPitch.innerText = '0.0';
    dom.telemetryRoll.innerText = '0.0';
}

export function renderMissionStatus(status) {
    const taskEl = dom.missionTask;
    const phaseEl = dom.missionPhase;
    const cmdEl = dom.missionCommand;
    const wpEl = dom.missionWaypoint;
    const seqEl = dom.missionSequence;
    const histEl = dom.missionHistory;

    if (!status) {
        taskEl.innerText = '--';
        phaseEl.innerText = '--';
        cmdEl.innerText = '--';
        wpEl.innerText = '--';
        seqEl.innerHTML = '';
        histEl.innerHTML = '';
        return;
    }

    taskEl.innerText = localizeMissionLabel(status.c2_task_label || status.c2_task || '--');
    phaseEl.innerText = localizeMissionLabel(status.phase_label || status.phase_name || '--');
    const cmdCode = Number.isFinite(status.command_code) ? status.command_code : '--';
    cmdEl.innerText = `${localizeMissionLabel(status.command_name || '--')} (${cmdCode})`;

    if (Number(status.waypoint_total || 0) > 0) {
        const activeWp = Number(status.active_waypoint || 0);
        const totalWp = Number(status.waypoint_total || 0);
        wpEl.innerText = `${activeWp}/${totalWp}`;
    } else {
        wpEl.innerText = '--';
    }

    const sequence = Array.isArray(status.task_sequence) ? status.task_sequence : [];
    const activeIdx = Number.isFinite(status.task_sequence_index) ? status.task_sequence_index : -1;
    seqEl.innerHTML = '';
    sequence.forEach((taskName, idx) => {
        const chip = document.createElement('span');
        chip.className = 'task-chip';
        if (idx < activeIdx) chip.classList.add('done');
        else if (idx === activeIdx) chip.classList.add('active');
        else chip.classList.add('pending');
        chip.innerText = localizeMissionLabel(taskName);
        seqEl.appendChild(chip);
    });

    const history = Array.isArray(status.history) ? status.history : [];
    histEl.innerHTML = '';
    history.slice().reverse().forEach((entry) => {
        const row = document.createElement('div');
        row.className = 'history-item';

        const time = document.createElement('span');
        time.className = 'history-time';
        const t = Number(entry.time_s || 0);
        time.innerText = `${t.toFixed(1)}s`;

        const text = document.createElement('span');
        text.className = 'history-text';
        const taskLabel = localizeMissionLabel(entry.c2_task_label || entry.c2_task || '--');
        const phaseLabel = localizeMissionLabel(entry.phase_label || entry.phase_name || '--');
        const waypointText = entry.waypoint_text && entry.waypoint_text !== '--'
            ? ` | ${i18n('ui.waypointShort')} ${entry.waypoint_text}`
            : '';
        text.innerText = `${taskLabel} / ${phaseLabel}${waypointText}`;

        row.appendChild(time);
        row.appendChild(text);
        histEl.appendChild(row);
    });
}
