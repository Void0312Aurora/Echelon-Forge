// 3D presentation: three.js scene, unit meshes and trails, GLTF asset
// loading via the asset registry, map/nav setup geometry, and camera logic.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

import {
    GRID_COLOR,
    GRID_COLOR_MINOR,
    GRID_MAX_SIZE,
    GRID_MIN_SIZE,
    GRID_STEP,
    MAP_MODE_3D_FRAME_INTERVAL,
    MAX_TRAIL_POINTS_PER_UNIT,
    MAX_UNIT_VISUAL_SAMPLES,
    SCENE_BG,
    VISUAL_EXTRAPOLATION_LIMIT_MS,
    VISUAL_INTERPOLATION_DELAY_MULT,
    VISUAL_INTERPOLATION_MAX_DELAY_MS,
    VISUAL_INTERPOLATION_MIN_DELAY_MS,
} from './config.js';
import { vizState } from './store.js';
import { lerpAngleDeg } from './utils.js';
import { normalizeRegistryEntry, resolveAssetEntry } from './asset-registry.js';
import { requestTacticalDraw } from './tactical-map.js';
import { renderUnitList } from './ui-shell.js';

// --- Scene / camera / renderer ---
export const scene = new THREE.Scene();
scene.background = new THREE.Color(SCENE_BG);
scene.fog = new THREE.FogExp2(SCENE_BG, 0.00005);

export const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1000000);
camera.position.set(0, 15000, 15000);

export const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.domElement.style.position = 'fixed';
renderer.domElement.style.inset = '0';
renderer.domElement.style.zIndex = '0';
document.body.appendChild(renderer.domElement);

export const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enabled = true;
controls.enablePan = false;
controls.rotateSpeed = 0.9;
controls.zoomSpeed = 1.2;
controls.target.set(0, 0, 0);
controls.maxDistance = 700000;
controls.minDistance = 25;

// --- Ground grid ---
let grid = null;
let gridSize = 0;

function rebuildGrid(size) {
    const clamped = Math.max(GRID_MIN_SIZE, Math.min(GRID_MAX_SIZE, size));
    const snapped = Math.ceil(clamped / GRID_STEP) * GRID_STEP;
    if (grid && snapped === gridSize) return;
    if (grid) {
        scene.remove(grid);
        if (grid.geometry) grid.geometry.dispose();
        if (grid.material) grid.material.dispose();
    }
    gridSize = snapped;
    grid = new THREE.GridHelper(gridSize, Math.max(100, Math.floor(gridSize / 100)), GRID_COLOR, GRID_COLOR_MINOR);
    grid.position.y = -5.0;
    scene.add(grid);
}

export function ensureGridContainsPoint(x, z, pad = 5000.0) {
    const extent = Math.max(Math.abs(x), Math.abs(z)) + pad;
    if ((extent * 2.0) > gridSize) rebuildGrid(extent * 2.0);
}

rebuildGrid(GRID_MIN_SIZE);

// --- Lighting driven by the scenario sun truth (vizState.illumination) ---
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 0.75);
dirLight.castShadow = true;
dirLight.shadow.mapSize.set(2048, 2048);
dirLight.shadow.bias = -0.0002;
dirLight.shadow.normalBias = 0.4;
scene.add(dirLight);
scene.add(dirLight.target);

const SUN_DISTANCE_M = 4000.0;

// Fit the orthographic shadow frustum around the area of interest (defaults
// cover a small scene; buildSceneGeometry3D widens it to the bundle extent).
export function fitShadowCameraToRadius(radiusM) {
    const radius = Math.max(500.0, Number(radiusM) || 0);
    const cam = dirLight.shadow.camera;
    cam.left = -radius;
    cam.right = radius;
    cam.top = radius;
    cam.bottom = -radius;
    cam.near = 10.0;
    cam.far = SUN_DISTANCE_M * 2.5;
    cam.updateProjectionMatrix();
}
fitShadowCameraToRadius(2500.0);

// Point the directional light along the operational sun vector. ENU ->
// three.js: x=east, y=up, z=-north. The Lambert geometry term already
// encodes elevation falloff (ground catches sin(el) of a fixed-power sun),
// so the light keeps constant intensity while it is above the horizon; this
// preserves shadow contrast at low sun angles instead of double-dimming.
export function updateSceneIllumination() {
    const ill = vizState.illumination;
    const az = (Number(ill.sunAzimuthDeg) || 0) * (Math.PI / 180.0);
    const el = (Number(ill.sunElevationDeg) || 0) * (Math.PI / 180.0);
    const horizontal = Math.cos(el);
    const east = Math.sin(az) * horizontal;
    const north = Math.cos(az) * horizontal;
    const up = Math.sin(el);
    dirLight.position.set(east * SUN_DISTANCE_M, Math.max(60.0, up * SUN_DISTANCE_M), -north * SUN_DISTANCE_M);
    dirLight.target.position.set(0, 0, 0);
    const aboveHorizon = up > 0.02;
    // High direct-to-ambient ratio keeps cast shadows legible on the dark
    // tactical palette (shadowed ground ~= ambient only).
    dirLight.intensity = aboveHorizon ? 1.4 : 0.0;
    ambientLight.intensity = aboveHorizon ? 0.22 : 0.16;
    dirLight.castShadow = aboveHorizon;
}
updateSceneIllumination();

// --- Human-only NAV markers (mission / cruise points) and map zones ---
const navGroup = new THREE.Group();
scene.add(navGroup);
const mapGroup = new THREE.Group();
scene.add(mapGroup);

export function clearNavGroup() {
    // Dispose geometries/materials to avoid leaks during episode resets.
    while (navGroup.children.length > 0) {
        const obj = navGroup.children[0];
        navGroup.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
    }
}

export function clearMapGroup() {
    while (mapGroup.children.length > 0) {
        const obj = mapGroup.children[0];
        mapGroup.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
        if (Array.isArray(obj.children)) {
            obj.children.forEach((child) => {
                if (child.geometry) child.geometry.dispose();
                if (child.material) child.material.dispose();
            });
        }
    }
}

function makeHorizontalRing(radius, color, y = 0.0) {
    const segs = 96;
    const pts = [];
    for (let i = 0; i < segs; i++) {
        const t = (i / segs) * Math.PI * 2.0;
        pts.push(new THREE.Vector3(Math.cos(t) * radius, y, Math.sin(t) * radius));
    }
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    return new THREE.LineLoop(
        geo,
        new THREE.LineBasicMaterial({ color: color, opacity: 0.85, transparent: true })
    );
}

export function applyMapSetup(zones) {
    clearMapGroup();
    if (!Array.isArray(zones)) return;
    zones.forEach(zone => {
        ensureGridContainsPoint(zone.x + zone.width * 0.5, -zone.y + zone.length * 0.5, 15000.0);
        ensureGridContainsPoint(zone.x - zone.width * 0.5, -zone.y - zone.length * 0.5, 15000.0);

        // Color based on surface - brighter for visibility.
        let color = 0x666666; // Concrete
        if (zone.surface === 'Asphalt') color = 0x444444;
        if (zone.surface === 'SoftDirt') color = 0x8B5a2B;

        // Use BasicMaterial to ignore lighting issues (flat, always visible).
        const mat = new THREE.MeshBasicMaterial({ color: color, side: THREE.DoubleSide });
        const geo = new THREE.PlaneGeometry(zone.width, zone.length);
        geo.rotateX(-Math.PI / 2);
        const mesh = new THREE.Mesh(geo, mat);

        // Layering to prevent Z-fighting: apron (Asphalt) at 0.01, runway
        // (Concrete) at 0.02.
        let heightOffset = 0.01;
        if (zone.surface === 'Concrete') heightOffset = 0.02;

        mesh.position.set(zone.x, heightOffset, -zone.y);
        mesh.rotation.y = -zone.heading * (Math.PI / 180);
        mapGroup.add(mesh);

        // Yellow outline as a child so it inherits the mesh transform.
        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffff00 }));
        mesh.add(line);
    });
}

export function applyNavSetup(markers) {
    clearNavGroup();
    if (!Array.isArray(markers) || markers.length === 0) return;

    // Draw markers in the same coordinate mapping as units:
    // Sim (ENU) -> Three (X=East, Y=Up, Z=-North).
    markers.forEach(m => {
        const arrivalRadius = Number.isFinite(m.arrival_radius_m) ? Math.max(1.0, m.arrival_radius_m) : 1000.0;
        const sequenceGate = Number.isFinite(m.sequence_gate_m) ? Math.max(arrivalRadius, m.sequence_gate_m) : null;
        const isActive = !!m.is_active;
        const mode = String(m.waypoint_mode || 'flyby').toLowerCase();

        const markerColor = isActive ? 0x00ff00 : 0xffff00;
        const sphereRadius = Math.max(18.0, Math.min(55.0, arrivalRadius * 0.018));
        const geo = new THREE.SphereGeometry(sphereRadius, 16, 12);
        const mat = new THREE.MeshBasicMaterial({ color: markerColor });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(m.x, m.z, -m.y);
        navGroup.add(mesh);

        const arrivalRingColor = (mode === 'flyover') ? 0xff8844 : markerColor;
        const arrivalRing = makeHorizontalRing(arrivalRadius, arrivalRingColor, 0.0);
        arrivalRing.position.set(m.x, m.z, -m.y);
        navGroup.add(arrivalRing);

        if (isActive && sequenceGate !== null && sequenceGate > arrivalRadius + 1.0) {
            const gateRing = makeHorizontalRing(sequenceGate, 0x00ffff, 0.0);
            gateRing.position.set(m.x, m.z + 8.0, -m.y);
            navGroup.add(gateRing);
        }

        ensureGridContainsPoint(m.x, -m.y, 15000.0);
    });

    // Connect markers with a thin line for readability.
    if (markers.length >= 2) {
        const pts = markers.map(m => new THREE.Vector3(m.x, m.z, -m.y));
        const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
        const lineMat = new THREE.LineBasicMaterial({ color: 0xffff00, opacity: 0.5, transparent: true });
        navGroup.add(new THREE.Line(lineGeo, lineMat));
    }
}

// --- Unified scene geometry (terrain + static vectors, display-only) ---
const sceneGeometryGroup = new THREE.Group();
scene.add(sceneGeometryGroup);

export function clearSceneGeometry3D() {
    while (sceneGeometryGroup.children.length > 0) {
        const child = sceneGeometryGroup.children[0];
        sceneGeometryGroup.remove(child);
        disposeObjectTree(child);
    }
}

function buildTerrainMesh(terrain, helpers) {
    const rows = Number(terrain.rows);
    const cols = Number(terrain.cols);
    if (!(rows > 1) || !(cols > 1)) return null;
    const originX = Number(terrain.origin_x);
    const originY = Number(terrain.origin_y);
    const stepX = Number(terrain.step_x);
    const stepY = Number(terrain.step_y);

    const positions = new Float32Array(rows * cols * 3);
    const colors = new Float32Array(rows * cols * 3);
    for (let r = 0; r < rows; r += 1) {
        for (let c = 0; c < cols; c += 1) {
            const worldX = originX + stepX * c;
            const worldY = originY + stepY * r;
            const height = Number(terrain.heights[r][c]) || 0;
            const offset = (r * cols + c) * 3;
            // ENU -> three.js: x=east, y=up, z=-north.
            positions[offset] = worldX;
            positions[offset + 1] = height;
            positions[offset + 2] = -worldY;
            // Plain material color only: slope shading and shadows come from
            // the sun-driven directional light, so relief and occlusion read
            // from one physically consistent source (no baked hillshade).
            const base = helpers.terrainCellColor(terrain, r, c);
            const gain = 1.5 / 255;
            colors[offset] = Math.min(1, base[0] * gain);
            colors[offset + 1] = Math.min(1, base[1] * gain);
            colors[offset + 2] = Math.min(1, base[2] * gain);
        }
    }
    const indices = [];
    for (let r = 0; r < rows - 1; r += 1) {
        for (let c = 0; c < cols - 1; c += 1) {
            const a = r * cols + c;
            const b = a + 1;
            const d = a + cols;
            const e = d + 1;
            indices.push(a, d, b, b, d, e);
        }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const material = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.receiveShadow = true;
    return mesh;
}

function shapeFromRings(rings) {
    let shape = null;
    for (const ring of rings) {
        const points = (ring.points || []).map((p) => new THREE.Vector2(Number(p[0]), Number(p[1])));
        if (points.length < 3) continue;
        if (ring.role !== 'hole') {
            if (shape === null) {
                shape = new THREE.Shape(points);
            }
            // Additional outer rings become separate shapes handled by caller.
        } else if (shape !== null) {
            shape.holes.push(new THREE.Path(points));
        }
    }
    return shape;
}

function buildBuildingsMesh(buildings) {
    const group = new THREE.Group();
    const material = new THREE.MeshLambertMaterial({ color: 0x8d8878, transparent: true, opacity: 0.92 });
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0xcfc5a0, transparent: true, opacity: 0.35 });
    for (const building of buildings || []) {
        const shape = shapeFromRings(building.rings || []);
        if (!shape) continue;
        const height = Math.max(1.0, Number(building.height_m) || 1.0);
        const geometry = new THREE.ExtrudeGeometry(shape, { depth: height, bevelEnabled: false });
        // Shape lies in the XY plane extruded along +Z; rotate so the prism
        // rises along +Y with ENU north mapped to -Z.
        geometry.rotateX(-Math.PI / 2);
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.position.y = Number(building.base_m) || 0;
        mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 30), edgeMaterial));
        group.add(mesh);
    }
    return group;
}

function pushCorridorTriangles(target, polygon, lift) {
    // Fan triangulation of a convex corridor quad; ENU -> three.js axes.
    for (let i = 1; i + 1 < polygon.length; i += 1) {
        for (const p of [polygon[0], polygon[i], polygon[i + 1]]) {
            target.push(Number(p[0]), (Number(p[2]) || 0) + lift, -Number(p[1]));
        }
    }
}

function corridorMesh(positions, material) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.receiveShadow = true;
    return mesh;
}

// Per-class lift keeps overlapping carriageways, service roads, and paths
// from z-fighting where OSM stacks parallel ways on the same ground.
function roadLiftM(highwayType) {
    const key = String(highwayType || '').toLowerCase();
    if (/^(motorway|trunk|primary|secondary|tertiary)/.test(key)) return 0.45;
    if (/^(footway|path|steps|pedestrian|cycleway)/.test(key)) return 0.28;
    return 0.36;
}

// Continuous ribbon along the centerline: averaged-direction normals join
// segments without wedge gaps, and the deck height comes from the rendered
// terrain sampler so roads follow the exact surface the 3D mesh shows.
function pushRoadRibbon(target, part, halfWidth, lift, sampleHeight) {
    const count = part.length;
    if (count < 2) return;
    const left = new Array(count);
    const right = new Array(count);
    for (let i = 0; i < count; i += 1) {
        const prev = part[Math.max(0, i - 1)];
        const next = part[Math.min(count - 1, i + 1)];
        let dirX = Number(next[0]) - Number(prev[0]);
        let dirY = Number(next[1]) - Number(prev[1]);
        const len = Math.hypot(dirX, dirY) || 1.0;
        dirX /= len;
        dirY /= len;
        const x = Number(part[i][0]);
        const y = Number(part[i][1]);
        // Cross-section stays level at the centerline height, like a graded
        // roadbed; the sampler pins it to the rendered terrain basis.
        const sampled = sampleHeight ? sampleHeight(x, y) : null;
        const z = (Number.isFinite(sampled) ? sampled : Number(part[i][2]) || 0) + lift;
        left[i] = [x - dirY * halfWidth, y + dirX * halfWidth, z];
        right[i] = [x + dirY * halfWidth, y - dirX * halfWidth, z];
    }
    for (let i = 0; i + 1 < count; i += 1) {
        for (const p of [left[i], right[i], right[i + 1]]) {
            target.push(p[0], p[2], -p[1]);
        }
        for (const p of [left[i], right[i + 1], left[i + 1]]) {
            target.push(p[0], p[2], -p[1]);
        }
    }
}

function buildRoadsGroup(roads, sampleHeight) {
    const group = new THREE.Group();
    const roadPositions = [];
    const bridgePositions = [];
    for (const road of roads || []) {
        if (road.kind === 'bridge_deck') {
            // Bridge decks keep the backend abutment-interpolated elevations;
            // they must not be re-draped onto the terrain below.
            const corridor = Array.isArray(road.corridor) ? road.corridor : [];
            for (const polygon of corridor) {
                if (Array.isArray(polygon) && polygon.length >= 3) {
                    pushCorridorTriangles(bridgePositions, polygon, 0.6);
                }
            }
            continue;
        }
        const halfWidth = Math.max(0.5, Number(road.width_m || 2) * 0.5);
        const lift = roadLiftM(road.highway_type);
        for (const part of road.parts || []) {
            if (Array.isArray(part) && part.length >= 2) {
                pushRoadRibbon(roadPositions, part, halfWidth, lift, sampleHeight);
            }
        }
    }
    if (roadPositions.length > 0) {
        group.add(corridorMesh(roadPositions, new THREE.MeshLambertMaterial({
            color: 0x716c59,
            side: THREE.DoubleSide,
        })));
    }
    if (bridgePositions.length > 0) {
        group.add(corridorMesh(bridgePositions, new THREE.MeshLambertMaterial({
            color: 0x9fb8b8,
            side: THREE.DoubleSide,
        })));
    }
    return group;
}

function buildWaterGroup(water) {
    const group = new THREE.Group();
    const material = new THREE.MeshLambertMaterial({
        color: 0x1e5f8a,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide,
    });
    const ribbonPositions = [];
    for (const entry of water || []) {
        const outers = (entry.paths || []).filter((path) => {
            const role = String(path.role || '');
            return role !== 'line' && !role.includes('hole');
        });
        const holes = (entry.paths || []).filter((path) => String(path.role || '').includes('hole'));
        const lines = (entry.paths || []).filter((path) => String(path.role || '') === 'line');
        // Linear watercourses become width ribbons along the DEM-draped
        // centerline; treating them as polygons fabricated area (and dropped
        // two-point segments entirely).
        const halfWidth = Math.max(0.75, Number(entry.width_m || 3) * 0.5);
        for (const line of lines) {
            const points = line.points || [];
            if (points.length >= 2) {
                pushRoadRibbon(ribbonPositions, points, halfWidth, 0.15, null);
            }
        }
        for (const outer of outers) {
            const points = outer.points || [];
            if (points.length < 3) continue;
            const shape = new THREE.Shape(points.map((p) => new THREE.Vector2(Number(p[0]), Number(p[1]))));
            for (const hole of holes) {
                const holePoints = (hole.points || []).map((p) => new THREE.Vector2(Number(p[0]), Number(p[1])));
                if (holePoints.length >= 3) shape.holes.push(new THREE.Path(holePoints));
            }
            const zValues = points.map((p) => Number(p[2]) || 0);
            const surfaceZ = zValues.reduce((a, b) => a + b, 0) / Math.max(1, zValues.length);
            const geometry = new THREE.ShapeGeometry(shape);
            geometry.rotateX(-Math.PI / 2);
            const mesh = new THREE.Mesh(geometry, material);
            mesh.receiveShadow = true;
            mesh.position.y = surfaceZ + 0.2;
            group.add(mesh);
        }
    }
    if (ribbonPositions.length > 0) {
        group.add(corridorMesh(ribbonPositions, material));
    }
    return group;
}

export function buildSceneGeometry3D(payload, helpers) {
    clearSceneGeometry3D();
    if (!payload || typeof payload !== 'object') return;
    const terrain = payload.terrain;
    if (terrain) {
        const mesh = buildTerrainMesh(terrain, helpers);
        if (mesh) sceneGeometryGroup.add(mesh);
    }
    sceneGeometryGroup.add(buildWaterGroup(payload.water));
    sceneGeometryGroup.add(buildRoadsGroup(payload.roads, helpers.sampleTerrainHeightM));
    sceneGeometryGroup.add(buildBuildingsMesh(payload.buildings));
    const extent = payload.region_extent || {};
    const spanX = Math.abs(Number(extent.max_x) - Number(extent.min_x)) || 0;
    const spanY = Math.abs(Number(extent.max_y) - Number(extent.min_y)) || 0;
    ensureGridContainsPoint(spanX * 0.5, spanY * 0.5, 500.0);
    fitShadowCameraToRadius(Math.hypot(spanX, spanY) * 0.5 + 300.0);
    console.log('Unified scene geometry loaded into 3D view');
}

// --- Registry asset loading ---
const loader = new GLTFLoader();
const assetModelCache = new Map();

export function disposeObjectTree(root) {
    if (!root) return;
    root.traverse?.((node) => {
        if (node.geometry) node.geometry.dispose();
        if (node.material) {
            if (Array.isArray(node.material)) node.material.forEach((mat) => mat?.dispose?.());
            else node.material.dispose?.();
        }
    });
}

function ensureRegistryAssetLoaded(entry) {
    const assetPath = String(entry?.visual?.asset_path || '').trim();
    if (!assetPath) return;
    if (assetModelCache.has(assetPath)) return;
    assetModelCache.set(assetPath, { status: 'loading', model: null });
    loader.load(assetPath, (gltf) => {
        let root = gltf.scene;
        if (assetPath.endsWith('usns_patuxent_tao_201.glb')) {
            const sourceHull = root.getObjectByName('OceanSupplyShip') || root;
            const visibleHull = sourceHull.clone(true);
            const hullWrapper = new THREE.Group();
            hullWrapper.add(visibleHull);
            const scale = Number(entry?.visual?.scale || 1.0);
            hullWrapper.scale.set(scale, scale, scale);
            const bbox = new THREE.Box3().setFromObject(hullWrapper);
            hullWrapper.position.y -= bbox.min.y;
            root = hullWrapper;
        }
        const yawDeg = Number(entry?.visual?.yaw_correction_deg || 0.0);
        root.rotation.y = yawDeg * (Math.PI / 180.0);
        const wrapper = new THREE.Group();
        wrapper.add(root);
        // Many third-party GLTF assets carry an arbitrary origin. Re-center
        // air/missile models on their bounding-box center so the visual sits
        // exactly on the unit's logical position (trail end, chase target).
        // Ships keep their authored origin: their waterline alignment is
        // handled via waterline_offset_m instead.
        if (String(entry?.match?.unit_type || '').trim() !== 'Ship') {
            const bounds = new THREE.Box3().setFromObject(wrapper);
            if (!bounds.isEmpty()) {
                const center = bounds.getCenter(new THREE.Vector3());
                root.position.sub(center);
            }
        }
        assetModelCache.set(assetPath, { status: 'ready', model: wrapper });
        console.log(`Asset Loaded: ${assetPath}`);
    }, undefined, (error) => {
        console.warn(`Asset Load Failed: ${assetPath}`, error);
        assetModelCache.set(assetPath, { status: 'error', model: null });
    });
}

function getRegistryModelClone(entry) {
    if (!entry) return null;
    ensureRegistryAssetLoaded(entry);
    const assetPath = String(entry?.visual?.asset_path || '').trim();
    const cached = assetModelCache.get(assetPath);
    if (!cached || cached.status !== 'ready' || !cached.model) return null;
    return cached.model.clone(true);
}

function buildFallbackVisual(uData, assetEntry) {
    const group = new THREE.Group();
    if (uData.type === 'Ship') {
        const hullLength = Number(assetEntry?.visual?.fallback_hull_length_m || 160);
        const hullBeam = Number(assetEntry?.visual?.fallback_hull_beam_m || 24);
        const hullHeight = Number(assetEntry?.visual?.fallback_hull_height_m || 12);
        const hullGeo = new THREE.BoxGeometry(hullLength, hullHeight, hullBeam);
        hullGeo.translate(0, hullHeight * 0.5, 0);
        const hullMat = new THREE.MeshLambertMaterial({
            color: uData.side === 'Red' ? 0x8b3a3a : 0x6f7f8f,
        });
        group.add(new THREE.Mesh(hullGeo, hullMat));

        const superGeo = new THREE.BoxGeometry(
            Number(assetEntry?.visual?.fallback_super_length_m || 56),
            Number(assetEntry?.visual?.fallback_super_height_m || 18),
            Number(assetEntry?.visual?.fallback_super_beam_m || 16)
        );
        superGeo.translate(
            Number(assetEntry?.visual?.fallback_super_offset_x_m || -8),
            Number(assetEntry?.visual?.fallback_super_offset_y_m || 18),
            0
        );
        const superMat = new THREE.MeshLambertMaterial({
            color: uData.side === 'Red' ? 0xb85c5c : 0x9ca8b5,
        });
        group.add(new THREE.Mesh(superGeo, superMat));
    } else if (uData.type === 'Aircraft') {
        const geo = new THREE.ConeGeometry(5, 18, 10);
        geo.rotateZ(Math.PI / 2);
        const mat = new THREE.MeshLambertMaterial({ color: uData.side === 'Red' ? 0xff6666 : 0x7fc8ff });
        group.add(new THREE.Mesh(geo, mat));
    } else if (uData.type === 'Missile') {
        const geo = new THREE.ConeGeometry(1.6, 10, 8);
        geo.rotateZ(Math.PI / 2);
        const mat = new THREE.MeshLambertMaterial({ color: uData.side === 'Red' ? 0xff4f4f : 0xffdd55 });
        group.add(new THREE.Mesh(geo, mat));
    } else if (uData.type === 'Ground') {
        // Compact vehicle-scale marker: hull box plus a small turret cap.
        const hullGeo = new THREE.BoxGeometry(7, 2.6, 4);
        hullGeo.translate(0, 1.3, 0);
        const hullMat = new THREE.MeshLambertMaterial({ color: uData.side === 'Red' ? 0x9c4a3c : 0x4a6d4f });
        group.add(new THREE.Mesh(hullGeo, hullMat));
        const capGeo = new THREE.BoxGeometry(3.2, 1.4, 2.4);
        capGeo.translate(-0.6, 3.3, 0);
        const capMat = new THREE.MeshLambertMaterial({ color: uData.side === 'Red' ? 0xb86a58 : 0x5f8763 });
        group.add(new THREE.Mesh(capGeo, capMat));
    } else {
        const geo = new THREE.BoxGeometry(30, 60, 30);
        geo.translate(0, 30, 0);
        const mat = new THREE.MeshLambertMaterial({ color: uData.side === 'Red' ? 0xff0000 : 0xffaa00 });
        group.add(new THREE.Mesh(geo, mat));
    }
    return group;
}

function markUnitVisualShadows(root) {
    root.traverse?.((node) => {
        if (node.isMesh) node.castShadow = true;
    });
    return root;
}

function buildVisualGroupForUnit(uData, assetEntry) {
    const registryModel = getRegistryModelClone(assetEntry);
    if (registryModel) {
        registryModel.position.y = Number(assetEntry?.visual?.waterline_offset_m || 0.0);
        if (!String(assetEntry?.visual?.asset_path || '').includes('usns_patuxent_tao_201.glb')) {
            const configuredScale = Number(assetEntry?.visual?.scale || 1.0);
            registryModel.scale.set(configuredScale, configuredScale, configuredScale);
        }

        const exFlame = registryModel.getObjectByName("ExternalFlame");
        const inFlame = registryModel.getObjectByName("InternalFlame");
        if (exFlame) exFlame.visible = false;
        if (inFlame) inFlame.visible = false;
        return { group: markUnitVisualShadows(registryModel), usingRegistryAsset: true };
    }
    return { group: markUnitVisualShadows(buildFallbackVisual(uData, assetEntry)), usingRegistryAsset: false };
}

function maybeUpgradeUnitVisual(uObj) {
    if (!uObj || uObj.usingRegistryAsset) return;
    const assetEntry = uObj.assetEntry;
    const assetPath = String(assetEntry?.visual?.asset_path || '').trim();
    if (!assetPath) return;
    const upgraded = buildVisualGroupForUnit(uObj.data, assetEntry);
    if (!upgraded.usingRegistryAsset || !upgraded.group) return;

    const prevChildren = [...uObj.mesh.children];
    prevChildren.forEach((child) => uObj.mesh.remove(child));
    prevChildren.forEach((child) => disposeObjectTree(child));
    uObj.mesh.add(upgraded.group);
    uObj.usingRegistryAsset = true;
    renderUnitList();
}

export function applyAssetRegistry(registry) {
    const current = vizState.currentAssetRegistry;
    const nextPath = String(registry?.path || '').trim();
    const nextName = String(registry?.name || 'default').trim() || 'default';
    const nextEntries = Array.isArray(registry?.entries) ? registry.entries : [];
    const currentPath = String(current?.path || '').trim();
    const currentName = String(current?.name || '').trim();
    const currentEntryCount = Array.isArray(current?.entries) ? current.entries.length : 0;
    if (
        currentPath === nextPath
        && currentName === nextName
        && currentEntryCount === nextEntries.length
        && assetModelCache.size > 0
    ) {
        return;
    }
    const entries = Array.isArray(registry?.entries) ? registry.entries.map(normalizeRegistryEntry) : [];
    vizState.currentAssetRegistry = {
        name: nextName,
        description: String(registry?.description || '').trim(),
        path: nextPath,
        entries,
    };
    assetModelCache.clear();
    vizState.units.forEach((uObj) => {
        uObj.assetEntry = resolveAssetEntry(uObj.data);
        uObj.usingRegistryAsset = false;
        maybeUpgradeUnitVisual(uObj);
    });
    renderUnitList();
    requestTacticalDraw();
}

export function getAssetChaseOffset(entry, fallbackType) {
    const chase = entry?.visual?.chase_offset;
    if (Array.isArray(chase) && chase.length === 3) {
        return new THREE.Vector3(Number(chase[0] || 0), Number(chase[1] || 30), Number(chase[2] || 80));
    }
    if (fallbackType === 'Ship') return new THREE.Vector3(0, 75, 240);
    if (fallbackType === 'Ground') return new THREE.Vector3(0, 18, 42);
    return new THREE.Vector3(0, 30, 80);
}

// --- Unit lifecycle ---
export function clearUnitVisuals() {
    vizState.units.forEach((uObj) => {
        if (uObj.mesh) {
            scene.remove(uObj.mesh);
            disposeObjectTree(uObj.mesh);
        }
        if (uObj.trail) {
            scene.remove(uObj.trail);
            if (uObj.trail.geometry) uObj.trail.geometry.dispose();
            if (uObj.trail.material) uObj.trail.material.dispose();
        }
    });
    vizState.units = new Map();
    vizState.tacticalTrailHistory.clear();
    vizState.focusedId = null;
    vizState.chaseTargetPrev = null;
    renderUnitList();
}

export function removeUnitVisual(id) {
    const uObj = vizState.units.get(id);
    if (!uObj) return;
    if (uObj.mesh) {
        scene.remove(uObj.mesh);
        disposeObjectTree(uObj.mesh);
    }
    if (uObj.trail) {
        scene.remove(uObj.trail);
        if (uObj.trail.geometry) uObj.trail.geometry.dispose();
        if (uObj.trail.material) uObj.trail.material.dispose();
    }
    vizState.units.delete(id);
    vizState.tacticalTrailHistory.delete(id);
    if (vizState.focusedId === id) {
        vizState.focusedId = null;
        vizState.chaseTargetPrev = null;
    }
}

export function getOrSpawnUnit(uData) {
    if (vizState.units.has(uData.id)) return vizState.units.get(uData.id);

    console.log("Spawning Unit:", uData);

    const group = new THREE.Group();
    const assetEntry = resolveAssetEntry(uData);
    const visualBuild = buildVisualGroupForUnit(uData, assetEntry);
    group.add(visualBuild.group);

    scene.add(group);

    // Trail
    const trailGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(MAX_TRAIL_POINTS_PER_UNIT * 3);
    trailGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    trailGeo.setDrawRange(0, 0);
    const trailMat = new THREE.LineBasicMaterial({ color: 0x00ffff, opacity: 0.5, transparent: true });
    const trail = new THREE.Line(trailGeo, trailMat);
    trail.frustumCulled = false;
    scene.add(trail);

    const unitObj = {
        id: uData.id,
        mesh: group,
        trail: trail,
        trailCount: 0,
        trailPos: positions,
        data: uData,
        assetEntry: assetEntry,
        usingRegistryAsset: !!visualBuild.usingRegistryAsset,
        isNew: true,
        targetPosition: new THREE.Vector3(),
        targetQuaternion: new THREE.Quaternion(),
        visualSamples: [],
        renderData: { ...uData },
    };

    vizState.units.set(uData.id, unitObj);

    // Auto focus logic: first unit.
    if (vizState.focusedId === null) vizState.focusedId = uData.id;

    renderUnitList();
    return unitObj;
}

// --- Frame interpolation ---
function blendUnitData(aData, bData, alpha) {
    const t = Math.max(0.0, Math.min(1.0, Number(alpha) || 0.0));
    const out = { ...bData };
    const numericFields = ['x', 'y', 'z', 'pitch', 'roll', 'speed', 'ias', 'throttle', 'hp', 'max_hp'];
    for (const key of numericFields) {
        const av = Number(aData?.[key]);
        const bv = Number(bData?.[key]);
        if (Number.isFinite(av) && Number.isFinite(bv)) {
            out[key] = av + (bv - av) * t;
        }
    }
    const ah = Number(aData?.heading);
    const bh = Number(bData?.heading);
    if (Number.isFinite(ah) && Number.isFinite(bh)) {
        out.heading = lerpAngleDeg(ah, bh, t);
    }
    return out;
}

function extrapolateUnitData(prevData, latestData, dtSeconds) {
    const dt = Math.max(0.0, Number(dtSeconds) || 0.0);
    const out = { ...latestData };
    const speed = Number(latestData?.speed);
    const heading = Number(latestData?.heading);
    if (Number.isFinite(speed) && Number.isFinite(heading) && speed > 0.0) {
        const rad = (90.0 - heading) * Math.PI / 180.0;
        out.x = Number(latestData.x || 0) + Math.cos(rad) * speed * dt;
        out.y = Number(latestData.y || 0) + Math.sin(rad) * speed * dt;
    } else if (prevData && Number.isFinite(Number(prevData.x)) && Number.isFinite(Number(prevData.y))) {
        const latestAt = Number(latestData?.sampleAt);
        const prevAt = Number(prevData?.sampleAt);
        const sampleDt = latestAt - prevAt;
        if (Number.isFinite(sampleDt) && sampleDt > 1.0) {
            const gain = (dt * 1000.0) / sampleDt;
            out.x = Number(latestData.x || 0) + (Number(latestData.x || 0) - Number(prevData.x || 0)) * gain;
            out.y = Number(latestData.y || 0) + (Number(latestData.y || 0) - Number(prevData.y || 0)) * gain;
            out.z = Number(latestData.z || 0) + (Number(latestData.z || 0) - Number(prevData.z || 0)) * gain;
        }
    }
    return out;
}

function sampleUnitForRender(uObj, nowMs) {
    const samples = Array.isArray(uObj?.visualSamples) ? uObj.visualSamples : [];
    if (samples.length === 0) return uObj?.data || null;
    const control = vizState.sessionControlState;
    if (!control.running || control.paused || samples.length === 1) {
        return { ...samples[samples.length - 1] };
    }

    const delayMs = Math.max(
        VISUAL_INTERPOLATION_MIN_DELAY_MS,
        Math.min(VISUAL_INTERPOLATION_MAX_DELAY_MS, vizState.smoothedStateFrameIntervalMs * VISUAL_INTERPOLATION_DELAY_MULT)
    );
    const renderAt = Number(nowMs || performance.now()) - delayMs;
    let before = samples[0];
    let after = samples[samples.length - 1];
    for (let i = 1; i < samples.length; i++) {
        if (samples[i].sampleAt >= renderAt) {
            before = samples[i - 1];
            after = samples[i];
            break;
        }
    }

    if (renderAt <= samples[0].sampleAt) return { ...samples[0] };
    if (renderAt <= after.sampleAt && after.sampleAt > before.sampleAt) {
        return blendUnitData(before, after, (renderAt - before.sampleAt) / (after.sampleAt - before.sampleAt));
    }

    const latest = samples[samples.length - 1];
    const prev = samples.length >= 2 ? samples[samples.length - 2] : null;
    const extraMs = Math.min(VISUAL_EXTRAPOLATION_LIMIT_MS, Math.max(0.0, renderAt - latest.sampleAt));
    return extrapolateUnitData(prev, latest, extraMs / 1000.0);
}

function updateUnitFromRenderData(uObj, renderData, snap = false) {
    if (!uObj || !renderData) return;

    // Update Transform
    // Sim (ENU: X=East, Y=North, Z=Up) -> Three (Y-Up: X=East, Y=Up, Z=-North)
    const tx = Number(renderData.x || 0);
    const ty = Number(renderData.z || 0) + (renderData.type === 'Aircraft' ? 2.5 : 0); // Z is Up. Add 2.5m for gear.
    const tz = -Number(renderData.y || 0); // Y is North -> -Z

    const nextPosition = new THREE.Vector3(tx, ty, tz);

    if (snap || uObj.isNew) {
        uObj.mesh.position.copy(nextPosition);
        uObj.targetPosition.copy(nextPosition);
        uObj.isNew = false;
    } else {
        uObj.targetPosition.copy(nextPosition);
    }

    // Afterburner FX: flame meshes are toggled by throttle setting.
    const exFlame = uObj.mesh.getObjectByName("ExternalFlame");
    const inFlame = uObj.mesh.getObjectByName("InternalFlame");
    const abActive = (renderData.throttle || 0) > 1.0;
    if (exFlame) exFlame.visible = abActive;
    if (inFlame) inFlame.visible = abActive;

    // Rotation Logic (Unified)
    // ==========================================
    // Principle: all assets are standardized to face North (-Z).
    // Sim: Heading 0 = North. Heading 90 = East (CW).
    // Three: Rot 0 = North (-Z). Rot -90 = East (CCW around Y).
    // Formula: RotY = -Heading
    const rad = Math.PI / 180;
    const yawRad = -Number(renderData.heading || 0) * rad;

    const qYaw = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yawRad);
    // Pitch: Sim +Pitch is Nose Up. RotX + is nose up.
    const qPitch = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), Number(renderData.pitch || 0) * rad);
    // Roll: Sim +Roll is right wing down.
    const qRoll = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), -Number(renderData.roll || 0) * rad);

    const targetQuat = qYaw.multiply(qPitch).multiply(qRoll);
    if (uObj.mesh.quaternion.lengthSq() < 1e-8) {
        uObj.mesh.quaternion.copy(targetQuat);
    }
    uObj.targetQuaternion.copy(targetQuat);
}

export function updateUnit(uObj, uData, sampleAtMs) {
    const sample = {
        ...uData,
        sampleAt: Number(sampleAtMs || performance.now()),
    };
    uObj.data = uData;
    uObj.assetEntry = resolveAssetEntry(uData);
    maybeUpgradeUnitVisual(uObj);
    uObj.renderData = { ...uData };
    if (!Array.isArray(uObj.visualSamples)) uObj.visualSamples = [];
    const samples = uObj.visualSamples;
    const last = samples.length > 0 ? samples[samples.length - 1] : null;
    if (!last || sample.sampleAt >= last.sampleAt) {
        samples.push(sample);
    } else {
        samples.splice(0, samples.length, sample);
    }
    if (samples.length > MAX_UNIT_VISUAL_SAMPLES) {
        samples.splice(0, samples.length - MAX_UNIT_VISUAL_SAMPLES);
    }
    const control = vizState.sessionControlState;
    if (uObj.isNew || !control.running || control.paused) {
        updateUnitFromRenderData(uObj, sample, true);
        uObj.renderData = { ...sample };
    }
}

let trailFrameCounter = 0;

export function animateUnits(dt) {
    const alpha = 1.0 - Math.exp(-Math.max(0.0, dt) * 10.0);
    trailFrameCounter = (trailFrameCounter + 1) % 3;
    const nowMs = performance.now();
    let moved = false;
    vizState.units.forEach((uObj) => {
        if (!uObj.targetPosition || !uObj.targetQuaternion) return;
        const prevX = uObj.mesh.position.x;
        const prevY = uObj.mesh.position.y;
        const prevZ = uObj.mesh.position.z;
        const renderData = sampleUnitForRender(uObj, nowMs);
        if (renderData) {
            uObj.renderData = renderData;
            updateUnitFromRenderData(uObj, renderData, false);
        }
        uObj.mesh.position.lerp(uObj.targetPosition, alpha);
        uObj.mesh.quaternion.slerp(uObj.targetQuaternion, alpha);
        if (
            Math.abs(uObj.mesh.position.x - prevX) > 0.01
            || Math.abs(uObj.mesh.position.y - prevY) > 0.01
            || Math.abs(uObj.mesh.position.z - prevZ) > 0.01
        ) {
            moved = true;
        }

        if (trailFrameCounter !== 0) return;
        const prevIdx = Math.max(0, uObj.trailCount - 1);
        const px = uObj.trailPos[prevIdx * 3];
        const py = uObj.trailPos[prevIdx * 3 + 1];
        const pz = uObj.trailPos[prevIdx * 3 + 2];
        const dx = uObj.mesh.position.x - px;
        const dy = uObj.mesh.position.y - py;
        const dz = uObj.mesh.position.z - pz;
        if (uObj.trailCount === 0 || (dx * dx + dy * dy + dz * dz) > 25.0) {
            if (uObj.trailCount >= MAX_TRAIL_POINTS_PER_UNIT) {
                uObj.trailPos.copyWithin(0, 3);
            }
            const idx = Math.min(uObj.trailCount, MAX_TRAIL_POINTS_PER_UNIT - 1);
            uObj.trailPos[idx * 3] = uObj.mesh.position.x;
            uObj.trailPos[idx * 3 + 1] = uObj.mesh.position.y;
            uObj.trailPos[idx * 3 + 2] = uObj.mesh.position.z;
            uObj.trailCount = Math.min(MAX_TRAIL_POINTS_PER_UNIT, uObj.trailCount + 1);
            uObj.trail.geometry.setDrawRange(0, uObj.trailCount);
            uObj.trail.geometry.attributes.position.needsUpdate = true;
            ensureGridContainsPoint(uObj.mesh.position.x, uObj.mesh.position.z);
        }
    });
    if (moved) requestTacticalDraw();
}

// --- Camera ---
export function updateCameraForFrame(dt) {
    const keys = vizState.keys;
    if (vizState.viewMode === 'FREE') {
        const baseSpeed = 100.0;
        const speed = keys.Shift ? baseSpeed * 5.0 : baseSpeed;
        const moveDist = speed * dt;

        const fwd = new THREE.Vector3();
        camera.getWorldDirection(fwd);
        fwd.y = 0; // Move on XZ plane by default for WASD
        fwd.normalize();

        const right = new THREE.Vector3();
        right.crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();

        const moveParams = new THREE.Vector3();

        if (keys.w) moveParams.add(fwd);
        if (keys.s) moveParams.add(fwd.clone().negate());
        if (keys.d) moveParams.add(right);
        if (keys.a) moveParams.add(right.clone().negate());

        // Vertical
        if (keys.e) moveParams.y += 1;
        if (keys.q) moveParams.y -= 1;

        if (moveParams.lengthSq() > 0) {
            moveParams.normalize().multiplyScalar(moveDist);
            // Move the camera and the orbit target together so orbiting
            // continues around the new position.
            camera.position.add(moveParams);
            controls.target.add(moveParams);
        }
    } else if (vizState.viewMode === 'CHASE' && vizState.focusedId && vizState.units.has(vizState.focusedId)) {
        const focusedUnit = vizState.units.get(vizState.focusedId);
        const target = focusedUnit.mesh;
        const targetPos = target.position.clone();
        if (vizState.chaseTargetPrev === null) {
            vizState.chaseTargetPrev = targetPos.clone();
            const fallbackOffsetBase = getAssetChaseOffset(focusedUnit?.assetEntry, focusedUnit?.data?.type);
            const fallbackOffset = fallbackOffsetBase.clone().applyQuaternion(target.quaternion);
            camera.position.copy(targetPos.clone().add(fallbackOffset));
            controls.target.copy(targetPos);
        } else {
            const delta = targetPos.clone().sub(vizState.chaseTargetPrev);
            camera.position.add(delta);
            vizState.chaseTargetPrev.copy(targetPos);
            controls.target.copy(targetPos);
        }
    }
}

let render3dFrameCounter = 0;

export function render3D() {
    controls.update();
    // The 3D scene is only a faint underlay while the tactical map is
    // presented, so skip most WebGL frames in MAP mode.
    render3dFrameCounter = (render3dFrameCounter + 1) % MAP_MODE_3D_FRAME_INTERVAL;
    if (vizState.presentationMode === 'MAP' && render3dFrameCounter !== 0) return;
    renderer.render(scene, camera);
}

export function resize3D() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}