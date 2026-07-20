// Unified scene geometry (display-only): fetches the arnis-derived terrain,
// road, water, and building payload from the backend and renders it beneath
// the common tactical picture. The same payload feeds the 3D scene, so air,
// naval, and ground sessions share one world substrate.
//
// Governance: the payload is metadata/display-only (see its evidence flags);
// held objects arrive as counts and are never rendered as geometry.

import { vizState } from './store.js';
import { sunVectorFromAngles } from './utils.js';
import { isTacticalDrawPhaseEnabled } from './layers.js';
import { requestTacticalDraw } from './tactical-map.js';
import { buildSceneGeometry3D, clearSceneGeometry3D } from './scene3d.js';

let payload = null;
let terrainBitmap = null;
let terrainRect = null;

// Hillshade light vector (ENU) derived from the scenario sun truth, so the
// 2D map shading and the engine's glare adjudication share one sun.
let shadeLight = sunVectorFromAngles(
    vizState.illumination.sunAzimuthDeg,
    vizState.illumination.sunElevationDeg,
);

// Dark-theme land-cover base colors (ESA WorldCover class codes).
const LANDCOVER_COLORS = {
    0: [38, 48, 58],
    10: [23, 64, 42],
    20: [44, 69, 38],
    30: [46, 74, 36],
    40: [61, 74, 34],
    50: [58, 63, 70],
    60: [74, 66, 52],
    70: [91, 109, 117],
    80: [18, 60, 85],
    90: [29, 70, 67],
    95: [22, 64, 54],
    100: [51, 80, 46],
};

const ROAD_STYLES = [
    { match: /^(motorway|trunk|primary)/, stroke: 'rgba(212, 196, 140, 0.85)', casing: 'rgba(10, 16, 22, 0.9)' },
    { match: /^(secondary|tertiary)/, stroke: 'rgba(178, 170, 132, 0.75)', casing: 'rgba(10, 16, 22, 0.85)' },
    { match: /^(footway|path|steps|pedestrian|cycleway)/, stroke: 'rgba(120, 138, 128, 0.55)', casing: null },
    { match: /./, stroke: 'rgba(150, 150, 128, 0.65)', casing: 'rgba(10, 16, 22, 0.8)' },
];

const BRIDGE_STYLE = { stroke: 'rgba(176, 214, 214, 0.95)', casing: 'rgba(6, 10, 14, 0.95)' };

const WATER_FILL = 'rgba(38, 110, 160, 0.42)';
const WATER_STROKE = 'rgba(110, 200, 240, 0.55)';
const BUILDING_FILL = 'rgba(196, 186, 156, 0.20)';
const BUILDING_STROKE = 'rgba(222, 206, 160, 0.6)';

export function sceneGeometryAvailable() {
    return payload !== null;
}

export function sceneGeometryPayload() {
    return payload;
}

// Geodetic anchor of the local ENU frame (lat/lon of the local origin plus
// the source WGS84 bbox), or null. Strategic-scale views will use this to
// place local scenes on a globe; nothing in the tactical views consumes it
// yet beyond surfacing it for inspection.
export function sceneGeodeticAnchor() {
    const anchor = payload?.geodetic_anchor;
    return (anchor && typeof anchor === 'object') ? anchor : null;
}

export function sceneGeometryBounds() {
    if (!payload) return null;
    const extent = payload.region_extent || {};
    const bounds = {
        minX: Number(extent.min_x),
        maxX: Number(extent.max_x),
        minY: Number(extent.min_y),
        maxY: Number(extent.max_y),
    };
    if (![bounds.minX, bounds.maxX, bounds.minY, bounds.maxY].every(Number.isFinite)) return null;
    if (bounds.maxX <= bounds.minX || bounds.maxY <= bounds.minY) return null;
    return bounds;
}

function roadStyle(highwayType) {
    const key = String(highwayType || '').toLowerCase();
    for (const style of ROAD_STYLES) {
        if (style.match.test(key)) return style;
    }
    return ROAD_STYLES[ROAD_STYLES.length - 1];
}

function landcoverColor(code) {
    return LANDCOVER_COLORS[Number(code)] || LANDCOVER_COLORS[0];
}

function heightColor(t) {
    // Subtle dark elevation ramp used when land cover is unavailable.
    const low = [30, 44, 38];
    const high = [88, 92, 74];
    return [
        low[0] + (high[0] - low[0]) * t,
        low[1] + (high[1] - low[1]) * t,
        low[2] + (high[2] - low[2]) * t,
    ];
}

export function terrainCellColor(terrain, row, col) {
    const landcover = terrain.landcover;
    if (landcover && Array.isArray(landcover.values)) {
        const rowValues = landcover.values[row];
        if (rowValues) return landcoverColor(rowValues[col]);
    }
    const span = Math.max(1e-6, Number(terrain.max_m) - Number(terrain.min_m));
    const t = (terrain.heights[row][col] - Number(terrain.min_m)) / span;
    return heightColor(Math.max(0, Math.min(1, t)));
}

// Bilinear height sample against the transported terrain grid, in world
// meters. Returns null outside the grid. Used to pin draped geometry to the
// rendered 3D terrain so both use the same interpolation basis.
export function sampleTerrainHeightM(x, y) {
    const terrain = payload?.terrain;
    if (!terrain || !Array.isArray(terrain.heights)) return null;
    const fx = (x - Number(terrain.origin_x)) / Number(terrain.step_x);
    const fy = (y - Number(terrain.origin_y)) / Number(terrain.step_y);
    const cols = Number(terrain.cols);
    const rows = Number(terrain.rows);
    if (!(fx >= 0) || !(fy >= 0) || fx > cols - 1 || fy > rows - 1) return null;
    const c0 = Math.min(cols - 1, Math.floor(fx));
    const r0 = Math.min(rows - 1, Math.floor(fy));
    const c1 = Math.min(cols - 1, c0 + 1);
    const r1 = Math.min(rows - 1, r0 + 1);
    const tx = fx - c0;
    const ty = fy - r0;
    const h = terrain.heights;
    return (
        h[r0][c0] * (1 - tx) * (1 - ty)
        + h[r0][c1] * tx * (1 - ty)
        + h[r1][c0] * (1 - tx) * ty
        + h[r1][c1] * tx * ty
    );
}

export function terrainShade(terrain, row, col) {
    const heights = terrain.heights;
    const rows = terrain.rows;
    const cols = terrain.cols;
    const stepX = Math.abs(Number(terrain.step_x)) || 1;
    const stepY = Math.abs(Number(terrain.step_y)) || 1;
    const r0 = Math.max(0, row - 1);
    const r1 = Math.min(rows - 1, row + 1);
    const c0 = Math.max(0, col - 1);
    const c1 = Math.min(cols - 1, col + 1);
    const dzdx = (heights[row][c1] - heights[row][c0]) / ((c1 - c0 || 1) * stepX);
    // Row index grows southward (step_y is negative), so north is r0.
    const dzdy = (heights[r0][col] - heights[r1][col]) / ((r1 - r0 || 1) * stepY);
    // Lambertian shade lit by the operational sun (see vizState.illumination).
    const len = Math.sqrt(dzdx * dzdx + dzdy * dzdy + 1);
    const dot = (-dzdx * shadeLight.east + -dzdy * shadeLight.north + shadeLight.up) / len;
    return Math.max(0, Math.min(1, dot));
}

// Re-derive the hillshade light from the current illumination truth and
// rebuild the 2D terrain bitmap. The 3D scene needs no geometry rebuild: its
// relief shading comes live from the sun-driven directional light.
export function refreshIlluminationShading() {
    shadeLight = sunVectorFromAngles(
        vizState.illumination.sunAzimuthDeg,
        vizState.illumination.sunElevationDeg,
    );
    if (!payload) return;
    (async () => {
        await buildTerrainBitmap();
        requestTacticalDraw();
    })();
}

async function buildTerrainBitmap() {
    terrainBitmap = null;
    terrainRect = null;
    const terrain = payload?.terrain;
    if (!terrain || !Array.isArray(terrain.heights)) return;
    const rows = Number(terrain.rows);
    const cols = Number(terrain.cols);
    if (!(rows > 1) || !(cols > 1)) return;

    const canvas = document.createElement('canvas');
    canvas.width = cols;
    canvas.height = rows;
    const ctx = canvas.getContext('2d');
    const image = ctx.createImageData(cols, rows);
    for (let r = 0; r < rows; r += 1) {
        for (let c = 0; c < cols; c += 1) {
            const base = terrainCellColor(terrain, r, c);
            const shade = 0.55 + 0.45 * terrainShade(terrain, r, c);
            const offset = (r * cols + c) * 4;
            image.data[offset] = Math.round(base[0] * shade);
            image.data[offset + 1] = Math.round(base[1] * shade);
            image.data[offset + 2] = Math.round(base[2] * shade);
            image.data[offset + 3] = 235;
        }
    }
    ctx.putImageData(image, 0, 0);
    terrainBitmap = await createImageBitmap(canvas);

    // Row 0 is the northernmost sample (step_y < 0), matching canvas top.
    const stepX = Number(terrain.step_x);
    const stepY = Number(terrain.step_y);
    const originX = Number(terrain.origin_x);
    const originY = Number(terrain.origin_y);
    const xs = [originX, originX + stepX * (cols - 1)];
    const ys = [originY, originY + stepY * (rows - 1)];
    terrainRect = {
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
        northFirst: stepY < 0,
    };
}

export function clearSceneGeometry() {
    // Invalidate any in-flight fetch so a stale response cannot install
    // geometry after the clear.
    fetchGeneration += 1;
    loadedBundleKey = null;
    const hadPayload = payload !== null;
    payload = null;
    if (terrainBitmap && typeof terrainBitmap.close === 'function') terrainBitmap.close();
    terrainBitmap = null;
    terrainRect = null;
    if (hadPayload) {
        clearSceneGeometry3D();
        requestTacticalDraw();
    }
}

// Cache/in-flight state is keyed by the backend bundle identity so switching
// profiles (bundle A -> B) refetches instead of keeping A's terrain forever.
let loadedBundleKey = null;
let fetchGeneration = 0;

export function ensureSceneGeometry(bundleKey) {
    const key = bundleKey ? String(bundleKey) : null;
    if (key === null) {
        clearSceneGeometry();
        return;
    }
    if (key === loadedBundleKey) return; // already loaded or loading this bundle
    loadedBundleKey = key;
    const generation = ++fetchGeneration;
    (async () => {
        try {
            const response = await fetch('/api/viz/scene_geometry');
            if (generation !== fetchGeneration) return; // superseded
            if (!response.ok) {
                loadedBundleKey = null;
                return;
            }
            const body = await response.json();
            if (generation !== fetchGeneration) return;
            if (!body || typeof body !== 'object' || !body.terrain) {
                loadedBundleKey = null;
                return;
            }
            payload = body;
            const anchor = sceneGeodeticAnchor();
            if (anchor) {
                console.log(
                    `Scene geometry anchored at lat ${Number(anchor.anchor_lat_deg).toFixed(4)}, `
                    + `lon ${Number(anchor.anchor_lon_deg).toFixed(4)} (${anchor.frame})`,
                );
            }
            await buildTerrainBitmap();
            if (generation !== fetchGeneration) return; // cleared/superseded during build
            buildSceneGeometry3D(payload, {
                terrainCellColor,
                terrainShade,
                sampleTerrainHeightM,
            });
            requestTacticalDraw();
        } catch (err) {
            console.warn('scene geometry fetch failed', err);
            if (generation === fetchGeneration) loadedBundleKey = null;
        }
    })();
}

// --- 2D drawing (called from the tactical map draw pass) ---

export function drawSceneTerrain(ctx, toCanvas) {
    if (!isTacticalDrawPhaseEnabled('terrain')) return;
    if (!terrainBitmap || !terrainRect) return;
    const topLeft = toCanvas(terrainRect.minX, terrainRect.maxY);
    const bottomRight = toCanvas(terrainRect.maxX, terrainRect.minY);
    const width = bottomRight.x - topLeft.x;
    const height = bottomRight.y - topLeft.y;
    if (!(width > 0) || !(height > 0)) return;
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(terrainBitmap, topLeft.x, topLeft.y, width, height);
    ctx.restore();
}

function tracePath(ctx, toCanvas, points, close) {
    ctx.beginPath();
    for (let i = 0; i < points.length; i += 1) {
        const p = toCanvas(Number(points[i][0]), Number(points[i][1]));
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
    }
    if (close) ctx.closePath();
}

export function drawSceneVectors(ctx, toCanvas, scale) {
    if (!payload) return;

    if (isTacticalDrawPhaseEnabled('water')) {
        ctx.save();
        for (const entry of payload.water || []) {
            for (const path of entry.paths || []) {
                const points = path.points || [];
                const role = String(path.role || '');
                if (role === 'line') {
                    // Linear watercourse: stroke along the centerline at the
                    // authored width; closing/filling would fabricate area.
                    if (points.length < 2) continue;
                    tracePath(ctx, toCanvas, points, false);
                    ctx.strokeStyle = WATER_STROKE;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.lineWidth = Math.max(1.2, Number(entry.width_m || 2) * scale);
                    ctx.stroke();
                    continue;
                }
                if (points.length < 3) continue;
                tracePath(ctx, toCanvas, points, true);
                const isHole = role.includes('hole');
                ctx.fillStyle = isHole ? 'rgba(5, 11, 18, 0.85)' : WATER_FILL;
                ctx.fill();
                ctx.strokeStyle = WATER_STROKE;
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }
        ctx.restore();
    }

    if (isTacticalDrawPhaseEnabled('roads')) {
        ctx.save();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        for (const road of payload.roads || []) {
            const isBridge = road.kind === 'bridge_deck';
            const width = Math.max(isBridge ? 1.4 : 0.8, Number(road.width_m || 2) * scale);
            const style = isBridge ? BRIDGE_STYLE : roadStyle(road.highway_type);
            for (const part of road.parts || []) {
                if (!Array.isArray(part) || part.length < 2) continue;
                if (style.casing && (isBridge || width >= 2.5)) {
                    tracePath(ctx, toCanvas, part, false);
                    ctx.strokeStyle = style.casing;
                    ctx.lineWidth = width + (isBridge ? 2.4 : 1.6);
                    ctx.stroke();
                }
                tracePath(ctx, toCanvas, part, false);
                ctx.strokeStyle = style.stroke;
                ctx.lineWidth = width;
                ctx.stroke();
            }
        }
        ctx.restore();
    }

    if (isTacticalDrawPhaseEnabled('buildings')) {
        ctx.save();
        for (const building of payload.buildings || []) {
            for (const ring of building.rings || []) {
                const points = ring.points || [];
                if (points.length < 3) continue;
                tracePath(ctx, toCanvas, points, true);
                if (ring.role === 'hole') {
                    ctx.fillStyle = 'rgba(5, 11, 18, 0.9)';
                    ctx.fill();
                    continue;
                }
                ctx.fillStyle = BUILDING_FILL;
                ctx.fill();
                ctx.strokeStyle = BUILDING_STROKE;
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }
        ctx.restore();
    }
}
