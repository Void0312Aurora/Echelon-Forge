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

    // --- Environment truth shared by 2D hillshade and 3D lighting ---
    // Mirrors the engine sun defaults (IEnvironmentModel): NAV azimuth 0
    // (north), 45 deg above horizon. Updated from the map_setup payload so
    // the display uses the same sun the sensor glare adjudication does.
    illumination: {
        sunAzimuthDeg: 0.0,
        sunElevationDeg: 45.0,
        configured: false,
        engineConfirmed: false,
    },

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
        // 'auto' keeps the classic fit-to-content follow view; any pan/zoom
        // gesture switches to 'manual', which holds a fixed world anchor.
        mode: 'auto',
        zoom: 1.0, // auto-mode multiplier; derived readout in manual mode
        scale: 0.0, // px per meter (authoritative in manual mode)
        anchorX: 0.0, // world-space view center (authoritative in manual mode)
        anchorY: 0.0,
        dragging: false,
        dragMoved: false,
        pointerId: null,
        dragStartX: 0.0,
        dragStartY: 0.0,
        anchorStartX: 0.0,
        anchorStartY: 0.0,
        scaleAtDragStart: 0.0,
        measuring: false,
        measureMoved: false,
    },
    // Right-drag range/bearing ruler: { x0, y0, x1, y1 } in world meters.
    mapMeasure: null,

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
