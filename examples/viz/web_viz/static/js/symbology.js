// Static tactical-map registries: layer catalog, layer groups, draw phases,
// symbology palette, and workspace definitions. Pure data plus lookups; the
// live toggle state lives in the store and is managed by layers.js.

export const tacticalLayerCatalog = Object.freeze({
    environment: {
        label: 'Environment overlays',
        shortLabel: 'ENV',
        summaryLabel: 'ENV',
        group: 'environment',
        drawOrder: 10,
        buttonId: 'btn-layer-environment',
        defaultEnabled: true,
    },
    route: {
        label: 'Routes and waypoints',
        shortLabel: 'ROUTE',
        summaryLabel: 'ROUTE',
        group: 'maneuver',
        drawOrder: 20,
        buttonId: 'btn-layer-route',
        defaultEnabled: true,
    },
    trails: {
        label: 'Movement trails',
        shortLabel: 'TRAIL',
        summaryLabel: 'TRAILS',
        group: 'maneuver',
        drawOrder: 30,
        buttonId: 'btn-layer-trails',
        defaultEnabled: true,
    },
    datalinks: {
        label: 'Datalinks',
        shortLabel: 'LINK',
        summaryLabel: 'LINKS',
        group: 'sensors',
        drawOrder: 40,
        buttonId: 'btn-layer-datalinks',
        defaultEnabled: false,
    },
    sensorRings: {
        label: 'Sensor rings',
        shortLabel: 'RING',
        summaryLabel: 'RINGS',
        group: 'sensors',
        drawOrder: 50,
        buttonId: 'btn-layer-sensor-rings',
        defaultEnabled: false,
    },
    tracks: {
        label: 'Sensor tracks',
        shortLabel: 'TRACK',
        summaryLabel: 'TRACKS',
        group: 'sensors',
        drawOrder: 60,
        buttonId: 'btn-layer-tracks',
        defaultEnabled: false,
    },
    weapons: {
        label: 'Weapons and effects',
        shortLabel: 'WEPN',
        summaryLabel: 'WEAPONS',
        group: 'effects',
        drawOrder: 70,
        buttonId: 'btn-layer-weapons',
        defaultEnabled: true,
    },
});

export const tacticalLayerKeys = Object.keys(tacticalLayerCatalog);

export const tacticalLayerGroups = Object.freeze([
    { id: 'environment', label: 'ENVIRONMENT', role: 'terrain / areas', layerKeys: ['environment'] },
    { id: 'maneuver', label: 'MANEUVER', role: 'routes / trails', layerKeys: ['route', 'trails'] },
    { id: 'sensors', label: 'SENSORS', role: 'tracks / rings / links', layerKeys: ['tracks', 'sensorRings', 'datalinks'] },
    { id: 'effects', label: 'EFFECTS', role: 'weapons / fires', layerKeys: ['weapons'] },
]);

export const tacticalDrawPhases = Object.freeze([
    { id: 'grid', layer: null, order: 0 },
    { id: 'environment', layer: 'environment', order: tacticalLayerCatalog.environment.drawOrder },
    { id: 'route', layer: 'route', order: tacticalLayerCatalog.route.drawOrder },
    { id: 'trails', layer: 'trails', order: tacticalLayerCatalog.trails.drawOrder },
    { id: 'datalinks', layer: 'datalinks', order: tacticalLayerCatalog.datalinks.drawOrder },
    { id: 'sensorRings', layer: 'sensorRings', order: tacticalLayerCatalog.sensorRings.drawOrder },
    { id: 'tracks', layer: 'tracks', order: tacticalLayerCatalog.tracks.drawOrder },
    { id: 'weapons', layer: 'weapons', order: tacticalLayerCatalog.weapons.drawOrder },
    { id: 'units', layer: null, order: 80 },
    { id: 'missileUnits', layer: 'weapons', order: 90 },
    { id: 'labels', layer: null, order: 100 },
]);

export const tacticalDrawPhaseById = Object.freeze(Object.fromEntries(
    tacticalDrawPhases.map((phase) => [phase.id, phase])
));

export const tacticalSymbology = Object.freeze({
    canvas: {
        background: '#050b12',
        emptyText: '#5f7887',
        plotStroke: 'rgba(95, 216, 255, 0.22)',
        gridStroke: 'rgba(46, 98, 132, 0.5)',
    },
    affiliation: {
        Blue: {
            unitFill: '#73cfff',
            trailStroke: 'rgba(100, 210, 255, 0.34)',
            sensorStroke: 'rgba(90, 210, 255, 0.24)',
            weaponColor: '#ffe65a',
            weaponTrail: 'rgba(255, 230, 90, 0.9)',
            weaponTarget: 'rgba(255, 230, 90, 0.4)',
            labelStroke: 'rgba(115, 207, 255, 0.45)',
        },
        Red: {
            unitFill: '#ff6d6d',
            trailStroke: 'rgba(255, 120, 120, 0.34)',
            sensorStroke: 'rgba(255, 120, 120, 0.24)',
            weaponColor: '#ff5252',
            weaponTrail: 'rgba(255, 92, 92, 0.86)',
            weaponTarget: 'rgba(255, 82, 82, 0.38)',
            labelStroke: 'rgba(255, 109, 109, 0.45)',
        },
        Unknown: {
            unitFill: '#d7e7ee',
            trailStroke: 'rgba(190, 208, 216, 0.26)',
            sensorStroke: 'rgba(190, 208, 216, 0.2)',
            weaponColor: '#e5d27a',
            weaponTrail: 'rgba(229, 210, 122, 0.72)',
            weaponTarget: 'rgba(229, 210, 122, 0.35)',
            labelStroke: 'rgba(185, 210, 224, 0.35)',
        },
    },
    route: {
        path: 'rgba(235, 218, 106, 0.62)',
        defaultStroke: '#e8db7d',
        flyoverStroke: '#ffb16a',
        activeStroke: '#89ff8b',
        defaultFill: 'rgba(232, 219, 125, 0.12)',
        activeFill: 'rgba(137, 255, 139, 0.18)',
        activeLabel: '#c8ffd0',
        sequenceGate: 'rgba(80, 220, 255, 0.45)',
    },
    datalink: {
        stroke: 'rgba(80, 170, 255, 0.28)',
    },
    track: {
        fusedStroke: 'rgba(0, 255, 200, 0.75)',
        rawStroke: 'rgba(255, 200, 0, 0.78)',
        fusedDot: '#00ffd0',
        rawDot: '#ffd04d',
    },
    label: {
        leader: 'rgba(185, 210, 224, 0.35)',
        background: 'rgba(5, 11, 17, 0.88)',
        text: '#d7e7ee',
    },
    environment: {
        occlusionCandidate: {
            vegetation: {
                fill: 'rgba(61, 126, 80, 0.16)',
                stroke: 'rgba(128, 216, 154, 0.72)',
                label: '#a7e7b8',
                dash: [5, 5],
            },
            structure: {
                fill: 'rgba(158, 143, 104, 0.15)',
                stroke: 'rgba(232, 210, 143, 0.74)',
                label: '#ead599',
                dash: [7, 4],
            },
        },
        surfaces: {
            asphalt: {
                fill: 'rgba(101, 117, 124, 0.22)',
                stroke: 'rgba(168, 187, 194, 0.64)',
                label: '#c2d1d8',
                dash: [],
            },
            concrete: {
                fill: 'rgba(126, 133, 138, 0.22)',
                stroke: 'rgba(204, 214, 218, 0.66)',
                label: '#d5e0e4',
                dash: [],
            },
            softdirt: {
                fill: 'rgba(137, 106, 65, 0.23)',
                stroke: 'rgba(211, 173, 112, 0.68)',
                label: '#e1c18b',
                dash: [],
            },
            water: {
                fill: 'rgba(54, 119, 146, 0.22)',
                stroke: 'rgba(118, 204, 226, 0.64)',
                label: '#9ed9e9',
                dash: [],
            },
            default: {
                fill: 'rgba(105, 126, 116, 0.21)',
                stroke: 'rgba(173, 207, 183, 0.62)',
                label: '#bdddc5',
                dash: [],
            },
        },
        marker: {
            halo: 'rgba(3, 8, 12, 0.88)',
            textBackground: 'rgba(4, 10, 14, 0.82)',
            sourceText: '#92dcff',
            leader: 'rgba(154, 205, 214, 0.58)',
            anchorFill: '#071116',
        },
    },
});

export const tacticalWorkspaceDefinitions = {
    cop: {
        label: 'COP',
        role: 'COMMON PICTURE',
        viewMode: 'MAP',
        layerDefaults: {
            environment: true,
            route: true,
            trails: true,
            weapons: true,
            tracks: false,
            sensorRings: false,
            datalinks: false,
        },
    },
    environment: {
        label: 'ENVIRONMENT',
        role: 'ENV / AREAS',
        viewMode: 'MAP',
        layerDefaults: {
            environment: true,
            route: false,
            trails: false,
            weapons: false,
            tracks: false,
            sensorRings: false,
            datalinks: false,
        },
    },
    tracks: {
        label: 'TRACKS',
        role: 'SENSORS / LINKS',
        viewMode: 'MAP',
        layerDefaults: {
            environment: false,
            route: false,
            trails: true,
            weapons: false,
            tracks: true,
            sensorRings: true,
            datalinks: true,
        },
    },
    inspect3d: {
        label: '3D INSPECT',
        role: 'MODEL INSPECT',
        viewMode: '3D',
        layerDefaults: {
            environment: true,
            route: true,
            trails: true,
            weapons: true,
            tracks: false,
            sensorRings: false,
            datalinks: false,
        },
    },
};

export function tacticalLayerSpec(layerName) {
    return tacticalLayerCatalog[layerName] || {
        label: String(layerName || 'Layer'),
        shortLabel: String(layerName || 'LAYER').toUpperCase(),
        summaryLabel: String(layerName || 'LAYER').toUpperCase(),
        buttonId: '',
    };
}

export function tacticalAffiliationStyle(side) {
    return tacticalSymbology.affiliation[String(side || 'Unknown')]
        || tacticalSymbology.affiliation.Unknown;
}
