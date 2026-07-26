// @ts-check
// Central JSDoc type definitions for the viz frontend.
//
// These mirror the versioned wire contracts emitted by the backend
// (examples/viz/runtime/viz_session.py and scene_geometry.py). They are
// enforced by the editor / `tsc --noEmit` via jsconfig.json, not by a build
// step: the app stays buildless. Modules opt in with `// @ts-check`.
//
// Extra fields are allowed everywhere (additive contract evolution), which
// is why payload shapes carry an index signature.

/**
 * One unit entry in a state frame (`examples.viz.state_frame.v1`).
 * @typedef {Object} UnitData
 * @property {number} id
 * @property {string} name
 * @property {'Blue'|'Red'|'Neutral'|'Unknown'|string} side
 * @property {'Aircraft'|'Ship'|'Ground'|'Missile'|'Facility'|string} type
 * @property {string} platform_type
 * @property {string} echelon  MIL-STD echelon token ('' when unknown/none).
 * @property {number} x  East, meters (local ENU frame).
 * @property {number} y  North, meters.
 * @property {number} z  Up, meters.
 * @property {number} heading  Degrees, NAV convention (0=north, CW).
 * @property {number} pitch
 * @property {number} roll
 * @property {number} speed
 * @property {number} hp
 * @property {number} max_hp
 * @property {number} [ias]
 * @property {string} [service_profile]
 * @property {number} [attacker_id]
 * @property {number} [target_id]
 */

/**
 * Socket `state_update` payload.
 * @typedef {Object} StateFrame
 * @property {string} [contract_version]  `examples.viz.state_frame.v1`.
 * @property {number} tick  Simulation time, seconds.
 * @property {UnitData[]} units
 * @property {Object<string, *>} [mission_status]
 * @property {{sensor_rings: *[], datalinks: *[], tracks: *[]}} [tactical]
 */

/**
 * Scenario sun truth inside `map_setup` (drives 2D hillshade, 3D light and
 * shadows, and matches the engine's glare adjudication sun).
 * @typedef {Object} IlluminationPayload
 * @property {number} sun_azimuth_deg  NAV azimuth: 0=north, CW positive.
 * @property {number} sun_elevation_deg  Above horizon; negative = night.
 * @property {boolean} configured  True when the scenario set it explicitly.
 * @property {boolean} engine_confirmed  True when cross-checked with the kernel.
 */

/**
 * Socket `map_setup` payload (`examples.viz.map_setup.v1`).
 * @typedef {Object} MapSetupPayload
 * @property {string} [contract_version]
 * @property {Array<Object<string, *>>} zones
 * @property {Object<string, *>|null} [environment_overlays]
 * @property {IlluminationPayload} [illumination]
 */

/**
 * Geodetic anchor binding the local ENU frame to WGS84 so local scenes can
 * be placed on a globe at operational/strategic scale.
 * @typedef {Object} GeodeticAnchor
 * @property {'local_enu_m'|string} frame
 * @property {number} anchor_lat_deg
 * @property {number} anchor_lon_deg
 * @property {{min_lat: number, max_lat: number, min_lon: number, max_lon: number}} bbox_wgs84
 * @property {string} projection  Source projection that produced the frame.
 * @property {string} source
 */

/**
 * Downsampled terrain grid inside the scene-geometry payload. Row 0 is the
 * northernmost sample (step_y < 0).
 * @typedef {Object} TerrainGrid
 * @property {number} rows
 * @property {number} cols
 * @property {number} origin_x
 * @property {number} origin_y
 * @property {number} step_x
 * @property {number} step_y
 * @property {number} min_m
 * @property {number} max_m
 * @property {number[][]} heights
 * @property {{legend: Object<string, string>, values: number[][]}} [landcover]
 */

/**
 * REST `/api/viz/scene_geometry` payload
 * (`examples.viz.scene_geometry.arnis_static_scene.v1`, display-only).
 * @typedef {Object} SceneGeometryPayload
 * @property {string} contract_version
 * @property {'local_enu_m'} coordinate_frame
 * @property {{min_x: number, max_x: number, min_y: number, max_y: number}} region_extent
 * @property {GeodeticAnchor|null} [geodetic_anchor]
 * @property {TerrainGrid} terrain
 * @property {Array<Object<string, *>>} buildings
 * @property {Array<Object<string, *>>} roads
 * @property {Array<Object<string, *>>} water
 * @property {{total: number, by_reason: Object<string, number>, rendered: false}} held
 */

/**
 * Frontend illumination state (camelCase mirror of IlluminationPayload,
 * normalized; single source for every lighting consumer).
 * @typedef {Object} IlluminationState
 * @property {number} sunAzimuthDeg
 * @property {number} sunElevationDeg
 * @property {boolean} configured
 * @property {boolean} engineConfirmed
 */

/**
 * Sun direction as a unit vector in ENU axes.
 * @typedef {Object} SunVector
 * @property {number} east
 * @property {number} north
 * @property {number} up
 */

export {};
