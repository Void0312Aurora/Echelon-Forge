// Central mutable state shared by the viz frontend modules.
//
// Modules read and write fields on `vizState` directly; there is no reactive
// machinery. Rendering is pulled by the animation loop and by explicit
// `requestTacticalDraw()` calls, so plain mutation is sufficient.

export const vizState = {
    // --- Entities (id -> { mesh, trail, data, renderData, assetEntry, ... }) ---
    units: new Map(),
    focusedId: null,

    // --- View / presentation ---
    viewMode: 'CHASE', // 3D camera mode: CHASE | FREE
    presentationMode: 'MAP', // MAP | 3D
    mapOnlyMode: false,
    uiLanguage: 'en',

    // --- Simulation ---
    simTime: 0,
    simSpeed: 1,

    // --- Tactical map ---
    lastTacticalState: null,
    environmentOverlays: null,
    tacticalViewport: null,
    lastStateFrameAt: null,
    smoothedStateFrameIntervalMs: 1000.0 / 30.0,
    lastTacticalRenderAt: 0.0,
    tacticalNeedsDraw: true,
    tacticalTrailHistory: new Map(),
    tacticalInteraction: {
        zoom: 1.0,
        panX: 0.0,
        panY: 0.0,
        dragging: false,
        pointerId: null,
        dragStartX: 0.0,
        dragStartY: 0.0,
        panStartX: 0.0,
        panStartY: 0.0,
    },

    // --- Tactical workspaces / layers ---
    // Live toggle state; seeded from the symbology catalog by layers.js.
    tacticalLayers: {},
    activeTacticalWorkspace: 'cop',
    lastMapTacticalWorkspace: 'cop',
    tacticalWorkspaceLayerState: new Map(),

    // --- Session / app status ---
    socketConnected: false,
    vizScenarioList: [],
    vizProfileList: [],
    vizAssetRegistryList: [],
    currentScenario: '',
    currentProfile: '',
    sessionReady: false,
    currentProfileUiDefaults: null,
    appliedProfileUiDefaultsKey: '',
    currentAssetRegistry: { name: 'default', entries: [] },
    sessionControlState: { loaded: false, ready: false, running: false, paused: false, error: '' },

    // --- Layout ---
    layoutState: {
        mode: 'wide',
        topInset: 76,
        leftInset: 24,
        rightInset: 24,
        bottomInset: 72,
        tacticalPadding: { left: 24, right: 24, top: 88, bottom: 72 },
        measurements: {},
        applying: false,
    },
    dockState: {
        left: window.innerWidth >= 960,
        right: window.innerWidth >= 1180,
    },
    dockUserTouched: false,

    // --- 3D chase camera ---
    chaseTargetPrev: null,

    // --- Keyboard input for the 3D free camera ---
    keys: { w: false, a: false, s: false, d: false, q: false, e: false, Shift: false },
};
