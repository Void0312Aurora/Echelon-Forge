// Live tactical layer toggle state on top of the static symbology catalog:
// snapshots, workspace defaults, and draw-phase gating.

import { vizState } from './store.js';
import {
    tacticalDrawPhaseById,
    tacticalLayerCatalog,
    tacticalLayerKeys,
    tacticalWorkspaceDefinitions,
} from './symbology.js';

export function initTacticalLayers() {
    for (const [key, spec] of Object.entries(tacticalLayerCatalog)) {
        vizState.tacticalLayers[key] = !!spec.defaultEnabled;
    }
}

export function isTacticalDrawPhaseEnabled(phaseId) {
    const phase = tacticalDrawPhaseById[phaseId];
    if (!phase || !phase.layer) return true;
    return !!vizState.tacticalLayers[phase.layer];
}

export function tacticalLayerSnapshot(source = vizState.tacticalLayers) {
    const snapshot = {};
    for (const key of tacticalLayerKeys) {
        snapshot[key] = !!source[key];
    }
    return snapshot;
}

export function mergeTacticalLayerSnapshot(base, overrides) {
    const snapshot = tacticalLayerSnapshot(base || vizState.tacticalLayers);
    if (!overrides || typeof overrides !== 'object') return snapshot;
    for (const key of tacticalLayerKeys) {
        if (Object.prototype.hasOwnProperty.call(overrides, key)) {
            snapshot[key] = !!overrides[key];
        }
    }
    return snapshot;
}

export function applyTacticalLayerSnapshot(snapshot) {
    const source = snapshot || {};
    for (const key of tacticalLayerKeys) {
        vizState.tacticalLayers[key] = !!source[key];
    }
}

export function captureActiveWorkspaceLayers() {
    if (!tacticalWorkspaceDefinitions[vizState.activeTacticalWorkspace]) return;
    vizState.tacticalWorkspaceLayerState.set(
        vizState.activeTacticalWorkspace,
        tacticalLayerSnapshot()
    );
}

export function workspaceLayerDefaults(workspaceId) {
    const defaults = tacticalWorkspaceDefinitions[workspaceId]?.layerDefaults;
    return tacticalLayerSnapshot(defaults || tacticalWorkspaceDefinitions.cop.layerDefaults);
}
