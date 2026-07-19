// 2D tactical map: canvas sizing, pan/zoom interaction, trail history,
// frame smoothing, and the full layer-ordered draw pass.

import { TACTICAL_RENDER_INTERVAL_MS, MAX_TACTICAL_TRAIL_POINTS_PER_UNIT } from './config.js';
import { dom } from './dom.js';
import { vizState } from './store.js';
import { tacticalSymbology, tacticalAffiliationStyle } from './symbology.js';
import { i18n, formatTacticalScaleText } from './i18n.js';
import { setFocus } from './ui-shell.js';
import { isTacticalDrawPhaseEnabled } from './layers.js';
import { unitSymbolSpec, shouldShowSensorRingForUnit } from './asset-registry.js';
import {
    drawEnvironmentOverlays,
    environmentOverlayBounds,
    getEnvironmentOverlayEntries,
} from './environment-overlays.js';
import {
    drawSceneTerrain,
    drawSceneVectors,
    sceneGeometryAvailable,
    sceneGeometryBounds,
} from './scene-geometry.js';
import { refreshAutoLayout } from './layout.js';

const tacticalCanvas = dom.tacticalCanvas;
const tacticalCtx = tacticalCanvas.getContext('2d');

export function requestTacticalDraw() {
    vizState.tacticalNeedsDraw = true;
}

export function resizeTacticalCanvas() {
    refreshAutoLayout();
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const width = window.innerWidth;
    const height = window.innerHeight;
    tacticalCanvas.style.width = `${width}px`;
    tacticalCanvas.style.height = `${height}px`;
    tacticalCanvas.width = Math.round(width * dpr);
    tacticalCanvas.height = Math.round(height * dpr);
    tacticalCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    requestTacticalDraw();
}

function viewportToWorld(vp, px, py) {
    const centerX = vp.plotLeft + vp.plotWidth * 0.5;
    const centerY = vp.plotTop + vp.plotHeight * 0.5;
    return {
        x: vp.cx + (px - centerX) / vp.scale,
        y: vp.cy - (py - centerY) / vp.scale,
    };
}

function worldToViewport(vp, wx, wy) {
    const centerX = vp.plotLeft + vp.plotWidth * 0.5;
    const centerY = vp.plotTop + vp.plotHeight * 0.5;
    return {
        x: centerX + (wx - vp.cx) * vp.scale,
        y: centerY - (wy - vp.cy) * vp.scale,
    };
}

function updateRecenterButton() {
    const button = dom.btnMapRecenter;
    if (!button) return;
    button.classList.toggle('active', vizState.tacticalInteraction.mode === 'manual');
}

window.recenterTacticalMap = function () {
    const interaction = vizState.tacticalInteraction;
    interaction.mode = 'auto';
    interaction.zoom = 1.0;
    updateRecenterButton();
    requestTacticalDraw();
};

function pickUnitAt(px, py) {
    const vp = vizState.tacticalViewport;
    const state = vizState.lastTacticalState;
    if (!vp || !(vp.scale > 0) || !state) return;
    const unitsList = Array.isArray(state.units) ? state.units : [];
    let bestId = null;
    let bestDist = 18.0; // px hit radius
    for (const u of unitsList) {
        const p = worldToViewport(vp, Number(u.x || 0), Number(u.y || 0));
        const dist = Math.hypot(p.x - px, p.y - py);
        if (dist < bestDist) {
            bestDist = dist;
            bestId = u.id;
        }
    }
    if (bestId !== null) {
        setFocus(bestId);
        requestTacticalDraw();
    }
}

export function initTacticalMapInteractions() {
    const interaction = vizState.tacticalInteraction;

    tacticalCanvas.addEventListener('contextmenu', (event) => event.preventDefault());

    tacticalCanvas.addEventListener('wheel', (event) => {
        if (vizState.presentationMode !== 'MAP') return;
        event.preventDefault();
        const vp = vizState.tacticalViewport;
        if (!vp || !(vp.scale > 0)) return;
        // The rendered viewport lags behind rapid gestures (draw throttling),
        // so prefer the live manual-mode anchor over the last-drawn one.
        const view = interaction.mode === 'manual' && interaction.scale > 0
            ? { ...vp, cx: interaction.anchorX, cy: interaction.anchorY, scale: interaction.scale }
            : vp;
        const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
        // Anchor the zoom on the cursor: the world point under the pointer
        // stays fixed on screen.
        const cursorWorld = viewportToWorld(view, event.clientX, event.clientY);
        const minScale = vp.baseScale * 0.35;
        const maxScale = vp.baseScale * 12.0;
        const newScale = Math.max(minScale, Math.min(maxScale, view.scale * factor));
        const centerX = view.plotLeft + view.plotWidth * 0.5;
        const centerY = view.plotTop + view.plotHeight * 0.5;
        interaction.mode = 'manual';
        interaction.scale = newScale;
        interaction.anchorX = cursorWorld.x - (event.clientX - centerX) / newScale;
        interaction.anchorY = cursorWorld.y + (event.clientY - centerY) / newScale;
        updateRecenterButton();
        requestTacticalDraw();
    }, { passive: false });

    tacticalCanvas.addEventListener('pointerdown', (event) => {
        if (vizState.presentationMode !== 'MAP') return;
        const vp = vizState.tacticalViewport;
        if (event.button === 2) {
            // Right-drag: range/bearing ruler. A right click without drag
            // clears the previous measurement.
            if (!vp || !(vp.scale > 0)) return;
            const w = viewportToWorld(vp, event.clientX, event.clientY);
            interaction.measuring = true;
            interaction.measureMoved = false;
            interaction.pointerId = event.pointerId;
            interaction.dragStartX = event.clientX;
            interaction.dragStartY = event.clientY;
            vizState.mapMeasure = { x0: w.x, y0: w.y, x1: w.x, y1: w.y };
            try {
                tacticalCanvas.setPointerCapture(event.pointerId);
            } catch (err) {
                // Synthetic pointers cannot be captured; drag still works.
            }
            requestTacticalDraw();
            return;
        }
        if (event.button !== 0) return;
        const manualView = interaction.mode === 'manual' && interaction.scale > 0;
        interaction.dragging = true;
        interaction.dragMoved = false;
        interaction.pointerId = event.pointerId;
        interaction.dragStartX = event.clientX;
        interaction.dragStartY = event.clientY;
        interaction.anchorStartX = manualView ? interaction.anchorX : (vp ? vp.cx : interaction.anchorX);
        interaction.anchorStartY = manualView ? interaction.anchorY : (vp ? vp.cy : interaction.anchorY);
        interaction.scaleAtDragStart = manualView ? interaction.scale : (vp && vp.scale > 0 ? vp.scale : interaction.scale);
        try {
            tacticalCanvas.setPointerCapture(event.pointerId);
        } catch (err) {
            // Synthetic pointers cannot be captured; drag still works.
        }
    });

    tacticalCanvas.addEventListener('pointermove', (event) => {
        if (vizState.presentationMode !== 'MAP') return;
        if (interaction.pointerId !== event.pointerId) return;
        if (interaction.measuring) {
            const vp = vizState.tacticalViewport;
            if (!vp || !(vp.scale > 0) || !vizState.mapMeasure) return;
            if (Math.hypot(event.clientX - interaction.dragStartX, event.clientY - interaction.dragStartY) >= 4) {
                interaction.measureMoved = true;
            }
            const w = viewportToWorld(vp, event.clientX, event.clientY);
            vizState.mapMeasure.x1 = w.x;
            vizState.mapMeasure.y1 = w.y;
            requestTacticalDraw();
            return;
        }
        if (!interaction.dragging) return;
        const dx = event.clientX - interaction.dragStartX;
        const dy = event.clientY - interaction.dragStartY;
        if (!interaction.dragMoved && Math.hypot(dx, dy) < 4) return;
        const scale = interaction.scaleAtDragStart;
        if (!(scale > 0)) return;
        interaction.dragMoved = true;
        interaction.mode = 'manual';
        interaction.scale = scale;
        interaction.anchorX = interaction.anchorStartX - dx / scale;
        interaction.anchorY = interaction.anchorStartY + dy / scale;
        updateRecenterButton();
        requestTacticalDraw();
    });

    function endTacticalPointer(event) {
        if (interaction.pointerId !== null && event && interaction.pointerId === event.pointerId) {
            try {
                tacticalCanvas.releasePointerCapture(event.pointerId);
            } catch (err) {
                // Ignore pointer release races when capture was already cleared.
            }
        }
        interaction.dragging = false;
        interaction.measuring = false;
        interaction.pointerId = null;
    }

    tacticalCanvas.addEventListener('pointerup', (event) => {
        if (interaction.pointerId !== event.pointerId) return;
        if (interaction.measuring) {
            const clearMeasure = !interaction.measureMoved;
            endTacticalPointer(event);
            if (clearMeasure) {
                vizState.mapMeasure = null;
            }
            requestTacticalDraw();
            return;
        }
        const wasClick = interaction.dragging && !interaction.dragMoved && event.button === 0;
        endTacticalPointer(event);
        if (wasClick) pickUnitAt(event.clientX, event.clientY);
    });
    tacticalCanvas.addEventListener('pointercancel', endTacticalPointer);
    tacticalCanvas.addEventListener('pointerleave', (event) => {
        if ((interaction.dragging || interaction.measuring) && interaction.pointerId === event.pointerId) {
            endTacticalPointer(event);
        }
    });
}

export function updateTacticalTrailHistory(unitsData) {
    const tacticalTrailHistory = vizState.tacticalTrailHistory;
    const activeIds = new Set();
    const items = Array.isArray(unitsData) ? unitsData : [];
    for (const uData of items) {
        const id = Number(uData?.id);
        if (!Number.isFinite(id)) continue;
        activeIds.add(id);
        const x = Number(uData?.x);
        const y = Number(uData?.y);
        if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
        const type = String(uData?.type || '');
        const minSpacingSq = type === 'Missile' ? 16.0 : 400.0;
        let points = tacticalTrailHistory.get(id);
        if (!points) {
            points = [];
            tacticalTrailHistory.set(id, points);
        }
        const prev = points.length > 0 ? points[points.length - 1] : null;
        const dx = prev ? x - prev.x : Infinity;
        const dy = prev ? y - prev.y : Infinity;
        if (!prev || (dx * dx + dy * dy) >= minSpacingSq) {
            points.push({
                x,
                y,
                side: String(uData?.side || 'Unknown'),
                type,
                name: String(uData?.name || id),
            });
            if (points.length > MAX_TACTICAL_TRAIL_POINTS_PER_UNIT) {
                points.splice(0, points.length - MAX_TACTICAL_TRAIL_POINTS_PER_UNIT);
            }
        }
    }
    Array.from(tacticalTrailHistory.keys()).forEach((id) => {
        if (!activeIds.has(id) && !vizState.units.has(id)) {
            tacticalTrailHistory.delete(id);
        }
    });
}

export function resetTacticalMapState() {
    vizState.lastTacticalState = null;
    vizState.tacticalViewport = null;
    vizState.lastStateFrameAt = null;
    vizState.smoothedStateFrameIntervalMs = 1000.0 / 30.0;
    vizState.lastTacticalRenderAt = 0.0;
    vizState.tacticalNeedsDraw = true;
    vizState.mapMeasure = null;
    vizState.tacticalInteraction.mode = 'auto';
    vizState.tacticalInteraction.zoom = 1.0;
    updateRecenterButton();
    tacticalCtx.clearRect(0, 0, tacticalCanvas.clientWidth || window.innerWidth, tacticalCanvas.clientHeight || window.innerHeight);
    tacticalCtx.fillStyle = tacticalSymbology.canvas.background;
    tacticalCtx.fillRect(0, 0, tacticalCanvas.clientWidth || window.innerWidth, tacticalCanvas.clientHeight || window.innerHeight);
    dom.tacticalScale.innerText = i18n('ui.scaleEmpty');
}

function getSmoothedUnitsForTacticalState(state) {
    const unitsList = Array.isArray(state?.units) ? state.units : [];
    return unitsList.map((uData) => {
        const id = Number(uData?.id);
        const uObj = vizState.units.get(id);
        if (!uObj?.renderData) return uData;
        return { ...uData, ...uObj.renderData };
    });
}

export function buildSmoothedTacticalState(state) {
    if (!state) return state;
    const smoothedUnits = getSmoothedUnitsForTacticalState(state);
    const smoothedById = new Map(smoothedUnits.map((u) => [Number(u.id), u]));
    const tactical = state.tactical || {};
    const sensorRings = Array.isArray(tactical.sensor_rings)
        ? tactical.sensor_rings.map((ring) => {
            const u = smoothedById.get(Number(ring?.entity_id));
            return u ? { ...ring, x: u.x, y: u.y } : ring;
        })
        : tactical.sensor_rings;
    const datalinks = Array.isArray(tactical.datalinks)
        ? tactical.datalinks.map((link) => {
            const from = smoothedById.get(Number(link?.from_id));
            const to = smoothedById.get(Number(link?.to_id));
            return {
                ...link,
                from_x: from ? from.x : link.from_x,
                from_y: from ? from.y : link.from_y,
                to_x: to ? to.x : link.to_x,
                to_y: to ? to.y : link.to_y,
            };
        })
        : tactical.datalinks;
    const tracks = Array.isArray(tactical.tracks)
        ? tactical.tracks.map((track) => {
            const observer = smoothedById.get(Number(track?.observer_id));
            if (!observer) return track;
            const dx = Number(track.x1 || 0) - Number(track.x0 || 0);
            const dy = Number(track.y1 || 0) - Number(track.y0 || 0);
            return {
                ...track,
                x0: observer.x,
                y0: observer.y,
                x1: Number(observer.x || 0) + dx,
                y1: Number(observer.y || 0) + dy,
            };
        })
        : tactical.tracks;
    const weapons = Array.isArray(tactical.weapons)
        ? tactical.weapons.map((weapon) => {
            const id = Number(weapon?.entity_id);
            const u = smoothedById.get(id);
            if (!u) return weapon;
            return {
                ...weapon,
                x: u.x,
                y: u.y,
                z: u.z,
                heading: u.heading,
                speed_mps: Number.isFinite(Number(u.speed)) ? u.speed : weapon.speed_mps,
            };
        })
        : tactical.weapons;
    return {
        ...state,
        units: smoothedUnits,
        tactical: {
            ...tactical,
            sensor_rings: sensorRings,
            datalinks,
            tracks,
            weapons,
        },
    };
}

const EMPTY_TACTICAL_STATE = Object.freeze({ units: [], tactical: {} });

export function drawTacticalView(state) {
    if (vizState.presentationMode !== 'MAP' || !tacticalCtx) return;
    if (!state) {
        // Scene geometry (terrain/vectors) can render before the first
        // simulation state frame arrives.
        if (!sceneGeometryAvailable()) return;
        state = EMPTY_TACTICAL_STATE;
    }
    const tacticalTrailHistory = vizState.tacticalTrailHistory;
    const tacticalInteraction = vizState.tacticalInteraction;
    const renderState = buildSmoothedTacticalState(state);
    const unitsList = Array.isArray(renderState.units) ? renderState.units : [];
    const tactical = renderState.tactical || {};
    const rings = Array.isArray(tactical.sensor_rings) ? tactical.sensor_rings : [];
    const tracks = Array.isArray(tactical.tracks) ? tactical.tracks : [];
    const links = Array.isArray(tactical.datalinks) ? tactical.datalinks : [];
    const navMarkers = Array.isArray(tactical.nav?.markers) ? tactical.nav.markers : [];
    const weapons = Array.isArray(tactical.weapons) ? tactical.weapons : [];
    const plottedUnits = isTacticalDrawPhaseEnabled('weapons')
        ? unitsList
        : unitsList.filter((u) => String(u.type || '') !== 'Missile');
    const environmentEntries = getEnvironmentOverlayEntries();

    const width = tacticalCanvas.clientWidth || window.innerWidth;
    const height = tacticalCanvas.clientHeight || window.innerHeight;
    tacticalCtx.clearRect(0, 0, width, height);
    tacticalCtx.fillStyle = tacticalSymbology.canvas.background;
    tacticalCtx.fillRect(0, 0, width, height);

    if (
        plottedUnits.length === 0
        && navMarkers.length === 0
        && environmentEntries.length === 0
        && !sceneGeometryAvailable()
    ) {
        tacticalCtx.fillStyle = tacticalSymbology.canvas.emptyText;
        tacticalCtx.font = '12px monospace';
        tacticalCtx.fillText(i18n('ui.noUnits'), 24, 40);
        return;
    }

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const u of plottedUnits) {
        minX = Math.min(minX, Number(u.x || 0));
        maxX = Math.max(maxX, Number(u.x || 0));
        minY = Math.min(minY, Number(u.y || 0));
        maxY = Math.max(maxY, Number(u.y || 0));
    }
    if (isTacticalDrawPhaseEnabled('route')) {
        for (const marker of navMarkers) {
            minX = Math.min(minX, Number(marker.x || 0));
            maxX = Math.max(maxX, Number(marker.x || 0));
            minY = Math.min(minY, Number(marker.y || 0));
            maxY = Math.max(maxY, Number(marker.y || 0));
        }
    }
    if (isTacticalDrawPhaseEnabled('trails')) {
        tacticalTrailHistory.forEach((points) => {
            const isMissileTrail = String(points?.[0]?.type || '') === 'Missile';
            if (isMissileTrail) return;
            const step = Math.max(1, Math.floor(Math.max(1, points.length) / 180));
            for (let i = 0; i < points.length; i += step) {
                minX = Math.min(minX, Number(points[i].x || 0));
                maxX = Math.max(maxX, Number(points[i].x || 0));
                minY = Math.min(minY, Number(points[i].y || 0));
                maxY = Math.max(maxY, Number(points[i].y || 0));
            }
        });
    }
    if (isTacticalDrawPhaseEnabled('weapons')) {
        for (const weapon of weapons) {
            minX = Math.min(minX, Number(weapon.x || 0));
            maxX = Math.max(maxX, Number(weapon.x || 0));
            minY = Math.min(minY, Number(weapon.y || 0));
            maxY = Math.max(maxY, Number(weapon.y || 0));
        }
        tacticalTrailHistory.forEach((points) => {
            const isMissileTrail = String(points?.[0]?.type || '') === 'Missile';
            if (!isMissileTrail) return;
            const step = Math.max(1, Math.floor(Math.max(1, points.length) / 180));
            for (let i = 0; i < points.length; i += step) {
                minX = Math.min(minX, Number(points[i].x || 0));
                maxX = Math.max(maxX, Number(points[i].x || 0));
                minY = Math.min(minY, Number(points[i].y || 0));
                maxY = Math.max(maxY, Number(points[i].y || 0));
            }
        });
    }
    if (isTacticalDrawPhaseEnabled('sensorRings')) {
        for (const r of rings) {
            if (!shouldShowSensorRingForUnit(r)) continue;
            const range = Number(r.range_m || 0);
            minX = Math.min(minX, Number(r.x || 0) - range);
            maxX = Math.max(maxX, Number(r.x || 0) + range);
            minY = Math.min(minY, Number(r.y || 0) - range);
            maxY = Math.max(maxY, Number(r.y || 0) + range);
        }
    }
    if (isTacticalDrawPhaseEnabled('datalinks')) {
        for (const link of links) {
            minX = Math.min(minX, Number(link.from_x || 0), Number(link.to_x || 0));
            maxX = Math.max(maxX, Number(link.from_x || 0), Number(link.to_x || 0));
            minY = Math.min(minY, Number(link.from_y || 0), Number(link.to_y || 0));
            maxY = Math.max(maxY, Number(link.from_y || 0), Number(link.to_y || 0));
        }
    }
    if (isTacticalDrawPhaseEnabled('tracks')) {
        for (const track of tracks) {
            minX = Math.min(minX, Number(track.x0 || 0), Number(track.x1 || 0));
            maxX = Math.max(maxX, Number(track.x0 || 0), Number(track.x1 || 0));
            minY = Math.min(minY, Number(track.y0 || 0), Number(track.y1 || 0));
            maxY = Math.max(maxY, Number(track.y0 || 0), Number(track.y1 || 0));
        }
    }
    if (environmentEntries.length > 0) {
        for (const entry of environmentEntries) {
            const bounds = environmentOverlayBounds(entry);
            if (!bounds) continue;
            minX = Math.min(minX, bounds.minX);
            maxX = Math.max(maxX, bounds.maxX);
            minY = Math.min(minY, bounds.minY);
            maxY = Math.max(maxY, bounds.maxY);
        }
    }
    if (sceneGeometryAvailable() && isTacticalDrawPhaseEnabled('terrain')) {
        const sceneBounds = sceneGeometryBounds();
        if (sceneBounds) {
            minX = Math.min(minX, sceneBounds.minX);
            maxX = Math.max(maxX, sceneBounds.maxX);
            minY = Math.min(minY, sceneBounds.minY);
            maxY = Math.max(maxY, sceneBounds.maxY);
        }
    }
    if (!Number.isFinite(minX) || !Number.isFinite(maxX) || !Number.isFinite(minY) || !Number.isFinite(maxY)) {
        minX = -500.0;
        maxX = 500.0;
        minY = -500.0;
        maxY = 500.0;
    }

    const viewportPadding = vizState.layoutState.tacticalPadding || {
        left: Math.min(420, Math.max(220, width * 0.26)),
        right: Math.min(260, Math.max(180, width * 0.18)),
        top: 72,
        bottom: 110,
    };
    const plotWidth = Math.max(320, width - viewportPadding.left - viewportPadding.right);
    const plotHeight = Math.max(240, height - viewportPadding.top - viewportPadding.bottom);
    const plotLeft = viewportPadding.left;
    const plotTop = viewportPadding.top;
    const spanX = Math.max(1000, maxX - minX);
    const spanY = Math.max(1000, maxY - minY);
    const span = Math.max(spanX, spanY) * 1.12;
    const baseScale = Math.min(plotWidth / span, plotHeight / span);
    let cx;
    let cy;
    let scale;
    if (tacticalInteraction.mode === 'manual') {
        // Manual mode holds the user's world anchor and absolute scale; the
        // zoom field becomes a readout relative to the current fit scale.
        cx = tacticalInteraction.anchorX;
        cy = tacticalInteraction.anchorY;
        scale = tacticalInteraction.scale;
        tacticalInteraction.zoom = baseScale > 0 ? scale / baseScale : 1.0;
    } else {
        cx = (minX + maxX) * 0.5;
        cy = (minY + maxY) * 0.5;
        scale = baseScale * tacticalInteraction.zoom;
        tacticalInteraction.anchorX = cx;
        tacticalInteraction.anchorY = cy;
        tacticalInteraction.scale = scale;
    }
    const screenCenterX = plotLeft + plotWidth * 0.5;
    const screenCenterY = plotTop + plotHeight * 0.5;
    const toCanvas = (x, y) => ({
        x: screenCenterX + (x - cx) * scale,
        y: screenCenterY - (y - cy) * scale,
    });
    const toWorld = (sx, sy) => ({
        x: cx + (sx - screenCenterX) / scale,
        y: cy - (sy - screenCenterY) / scale,
    });
    const niceGridStepM = (targetMeters) => {
        const bounded = Math.max(100.0, targetMeters);
        const exp = 10 ** Math.floor(Math.log10(bounded));
        for (const multiplier of [1, 2, 5, 10]) {
            const step = multiplier * exp;
            if (step >= bounded) return step;
        }
        return 10 * exp;
    };

    const plotRight = plotLeft + plotWidth;
    const plotBottom = plotTop + plotHeight;
    tacticalCtx.strokeStyle = tacticalSymbology.canvas.plotStroke;
    tacticalCtx.lineWidth = 1;
    tacticalCtx.strokeRect(plotLeft, plotTop, plotWidth, plotHeight);

    tacticalCtx.save();
    tacticalCtx.beginPath();
    tacticalCtx.rect(plotLeft, plotTop, plotWidth, plotHeight);
    tacticalCtx.clip();

    drawSceneTerrain(tacticalCtx, toCanvas);

    const worldA = toWorld(plotLeft, plotBottom);
    const worldB = toWorld(plotRight, plotTop);
    const worldMinX = Math.min(worldA.x, worldB.x);
    const worldMaxX = Math.max(worldA.x, worldB.x);
    const worldMinY = Math.min(worldA.y, worldB.y);
    const worldMaxY = Math.max(worldA.y, worldB.y);
    const gridStepM = niceGridStepM(110.0 / scale);

    tacticalCtx.strokeStyle = tacticalSymbology.canvas.gridStroke;
    tacticalCtx.lineWidth = 1;
    for (
        let gx = Math.floor(worldMinX / gridStepM) * gridStepM;
        gx <= worldMaxX + gridStepM * 0.5;
        gx += gridStepM
    ) {
        const p0 = toCanvas(gx, worldMinY);
        const p1 = toCanvas(gx, worldMaxY);
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(p0.x, p0.y);
        tacticalCtx.lineTo(p1.x, p1.y);
        tacticalCtx.stroke();
    }
    for (
        let gy = Math.floor(worldMinY / gridStepM) * gridStepM;
        gy <= worldMaxY + gridStepM * 0.5;
        gy += gridStepM
    ) {
        const p0 = toCanvas(worldMinX, gy);
        const p1 = toCanvas(worldMaxX, gy);
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(p0.x, p0.y);
        tacticalCtx.lineTo(p1.x, p1.y);
        tacticalCtx.stroke();
    }

    drawSceneVectors(tacticalCtx, toCanvas, scale);

    if (isTacticalDrawPhaseEnabled('environment') && environmentEntries.length > 0) {
        drawEnvironmentOverlays(tacticalCtx, environmentEntries, toCanvas, scale);
    }

    if (isTacticalDrawPhaseEnabled('route') && navMarkers.length > 0) {
        if (navMarkers.length >= 2) {
            tacticalCtx.strokeStyle = tacticalSymbology.route.path;
            tacticalCtx.lineWidth = 1.2;
            tacticalCtx.setLineDash([7, 6]);
            tacticalCtx.beginPath();
            for (const [idx, marker] of navMarkers.entries()) {
                const p = toCanvas(Number(marker.x || 0), Number(marker.y || 0));
                if (idx === 0) tacticalCtx.moveTo(p.x, p.y);
                else tacticalCtx.lineTo(p.x, p.y);
            }
            tacticalCtx.stroke();
            tacticalCtx.setLineDash([]);
        }
        for (const [idx, marker] of navMarkers.entries()) {
            const p = toCanvas(Number(marker.x || 0), Number(marker.y || 0));
            const radiusM = Number(marker.arrival_radius_m || marker.radius_m || 0);
            const rr = Math.max(5, Math.min(28, radiusM * scale));
            const active = !!marker.is_active;
            const mode = String(marker.waypoint_mode || 'flyby').toLowerCase();
            tacticalCtx.strokeStyle = active
                ? tacticalSymbology.route.activeStroke
                : mode === 'flyover'
                    ? tacticalSymbology.route.flyoverStroke
                    : tacticalSymbology.route.defaultStroke;
            tacticalCtx.fillStyle = active
                ? tacticalSymbology.route.activeFill
                : tacticalSymbology.route.defaultFill;
            tacticalCtx.lineWidth = active ? 1.8 : 1.1;
            tacticalCtx.beginPath();
            tacticalCtx.arc(p.x, p.y, rr, 0, Math.PI * 2);
            tacticalCtx.fill();
            tacticalCtx.stroke();
            tacticalCtx.fillStyle = active ? tacticalSymbology.route.activeLabel : tacticalSymbology.route.defaultStroke;
            tacticalCtx.font = '10px monospace';
            tacticalCtx.fillText(String(marker.name || `WP_${idx + 1}`), p.x + rr + 5, p.y - rr - 3);
            const sequenceGate = Number(marker.sequence_gate_m || 0);
            if (active && sequenceGate > radiusM + 1.0) {
                tacticalCtx.strokeStyle = tacticalSymbology.route.sequenceGate;
                tacticalCtx.lineWidth = 1;
                tacticalCtx.beginPath();
                tacticalCtx.arc(p.x, p.y, Math.max(rr + 3, sequenceGate * scale), 0, Math.PI * 2);
                tacticalCtx.stroke();
            }
        }
    }

    if (isTacticalDrawPhaseEnabled('trails')) {
        tacticalTrailHistory.forEach((points) => {
            if (!Array.isArray(points) || points.length < 2 || String(points[0]?.type || '') === 'Missile') return;
            const step = Math.max(1, Math.floor(points.length / 260));
            tacticalCtx.strokeStyle = tacticalAffiliationStyle(points[0]?.side).trailStroke;
            tacticalCtx.lineWidth = 1.2;
            tacticalCtx.beginPath();
            let first = true;
            for (let i = 0; i < points.length; i += step) {
                const p = toCanvas(Number(points[i].x || 0), Number(points[i].y || 0));
                if (first) {
                    tacticalCtx.moveTo(p.x, p.y);
                    first = false;
                } else {
                    tacticalCtx.lineTo(p.x, p.y);
                }
            }
            tacticalCtx.stroke();
        });
    }

    if (isTacticalDrawPhaseEnabled('datalinks')) {
        for (const link of links) {
            const a = toCanvas(Number(link.from_x || 0), Number(link.from_y || 0));
            const b = toCanvas(Number(link.to_x || 0), Number(link.to_y || 0));
            tacticalCtx.strokeStyle = tacticalSymbology.datalink.stroke;
            tacticalCtx.lineWidth = 1;
            tacticalCtx.beginPath();
            tacticalCtx.moveTo(a.x, a.y);
            tacticalCtx.lineTo(b.x, b.y);
            tacticalCtx.stroke();
        }
    }

    if (isTacticalDrawPhaseEnabled('sensorRings')) {
        for (const ring of rings) {
            if (!shouldShowSensorRingForUnit(ring)) continue;
            const p = toCanvas(Number(ring.x || 0), Number(ring.y || 0));
            const rr = Math.max(2, Number(ring.range_m || 0) * scale);
            tacticalCtx.strokeStyle = tacticalAffiliationStyle(ring.side).sensorStroke;
            tacticalCtx.lineWidth = 1;
            tacticalCtx.beginPath();
            tacticalCtx.arc(p.x, p.y, rr, 0, Math.PI * 2);
            tacticalCtx.stroke();
        }
    }

    if (isTacticalDrawPhaseEnabled('tracks')) {
        for (const track of tracks) {
            const a = toCanvas(Number(track.x0 || 0), Number(track.y0 || 0));
            const b = toCanvas(Number(track.x1 || 0), Number(track.y1 || 0));
            tacticalCtx.strokeStyle = Number(track.source) === 3
                ? tacticalSymbology.track.fusedStroke
                : tacticalSymbology.track.rawStroke;
            tacticalCtx.lineWidth = 1.4;
            tacticalCtx.beginPath();
            tacticalCtx.moveTo(a.x, a.y);
            tacticalCtx.lineTo(b.x, b.y);
            tacticalCtx.stroke();
            tacticalCtx.fillStyle = Number(track.source) === 3
                ? tacticalSymbology.track.fusedDot
                : tacticalSymbology.track.rawDot;
            tacticalCtx.beginPath();
            tacticalCtx.arc(b.x, b.y, 2.5, 0, Math.PI * 2);
            tacticalCtx.fill();
        }
    }

    if (isTacticalDrawPhaseEnabled('weapons')) {
        const unitById = new Map(unitsList.map((u) => [Number(u.id), u]));
        tacticalTrailHistory.forEach((points) => {
            if (!Array.isArray(points) || points.length < 2 || String(points[0]?.type || '') !== 'Missile') return;
            const step = Math.max(1, Math.floor(points.length / 240));
            tacticalCtx.strokeStyle = tacticalAffiliationStyle(points[0]?.side).weaponTrail;
            tacticalCtx.lineWidth = 2.2;
            tacticalCtx.beginPath();
            let first = true;
            for (let i = 0; i < points.length; i += step) {
                const p = toCanvas(Number(points[i].x || 0), Number(points[i].y || 0));
                if (first) {
                    tacticalCtx.moveTo(p.x, p.y);
                    first = false;
                } else {
                    tacticalCtx.lineTo(p.x, p.y);
                }
            }
            tacticalCtx.stroke();
        });

        for (const weapon of weapons) {
            const p = toCanvas(Number(weapon.x || 0), Number(weapon.y || 0));
            const hdg = Number(weapon.heading || 0);
            const rad = (90.0 - hdg) * Math.PI / 180.0;
            const dirX = Math.cos(rad);
            const dirY = -Math.sin(rad);
            const sideStyle = tacticalAffiliationStyle(weapon.side);
            const color = sideStyle.weaponColor;
            const target = unitById.get(Number(weapon.target_id || 0));

            if (target) {
                const t = toCanvas(Number(target.x || 0), Number(target.y || 0));
                tacticalCtx.save();
                tacticalCtx.setLineDash([4, 5]);
                tacticalCtx.strokeStyle = sideStyle.weaponTarget;
                tacticalCtx.lineWidth = 1;
                tacticalCtx.beginPath();
                tacticalCtx.moveTo(p.x, p.y);
                tacticalCtx.lineTo(t.x, t.y);
                tacticalCtx.stroke();
                tacticalCtx.restore();
            }

            tacticalCtx.save();
            tacticalCtx.shadowBlur = 14;
            tacticalCtx.shadowColor = color;
            tacticalCtx.strokeStyle = color;
            tacticalCtx.fillStyle = color;
            tacticalCtx.lineWidth = 2.4;
            tacticalCtx.beginPath();
            tacticalCtx.moveTo(p.x - dirX * 30, p.y - dirY * 30);
            tacticalCtx.lineTo(p.x - dirX * 8, p.y - dirY * 8);
            tacticalCtx.stroke();
            tacticalCtx.beginPath();
            tacticalCtx.moveTo(p.x + dirX * 17, p.y + dirY * 17);
            tacticalCtx.lineTo(p.x - dirX * 11 + dirY * 6, p.y - dirY * 11 - dirX * 6);
            tacticalCtx.lineTo(p.x - dirX * 5, p.y - dirY * 5);
            tacticalCtx.lineTo(p.x - dirX * 11 - dirY * 6, p.y - dirY * 11 + dirX * 6);
            tacticalCtx.closePath();
            tacticalCtx.fill();
            tacticalCtx.beginPath();
            tacticalCtx.arc(p.x, p.y, 10, 0, Math.PI * 2);
            tacticalCtx.stroke();
            tacticalCtx.shadowBlur = 0;
            tacticalCtx.font = '10px monospace';
            tacticalCtx.fillText(`MSL ${Number(weapon.entity_id || 0)}`, p.x + 12, p.y - 12);
            tacticalCtx.restore();
        }
    }

    for (const u of plottedUnits) {
        const p = toCanvas(Number(u.x || 0), Number(u.y || 0));
        const hdg = Number(u.heading || 0);
        const rad = (90.0 - hdg) * Math.PI / 180.0;
        const dirX = Math.cos(rad);
        const dirY = -Math.sin(rad);
        const symbol = unitSymbolSpec(u);
        const len = symbol.len;
        const wing = symbol.wing;
        if (Number(u.id) === Number(vizState.focusedId)) {
            drawFocusBrackets(p, Math.max(len, wing) + 8, tacticalAffiliationStyle(u.side).unitFill);
        }
        tacticalCtx.fillStyle = tacticalAffiliationStyle(u.side).unitFill;
        tacticalCtx.beginPath();
        if (symbol.kind === 'ship') {
            tacticalCtx.moveTo(p.x + dirX * len, p.y + dirY * len);
            tacticalCtx.lineTo(p.x - dirX * len * 0.75 + dirY * wing, p.y - dirY * len * 0.75 - dirX * wing);
            tacticalCtx.lineTo(p.x - dirX * len * 0.48, p.y - dirY * len * 0.48);
            tacticalCtx.lineTo(p.x - dirX * len * 0.75 - dirY * wing, p.y - dirY * len * 0.75 + dirX * wing);
        } else if (symbol.kind === 'aircraft') {
            tacticalCtx.moveTo(p.x + dirX * len, p.y + dirY * len);
            tacticalCtx.lineTo(p.x - dirX * len * 0.65 + dirY * wing, p.y - dirY * len * 0.65 - dirX * wing);
            tacticalCtx.lineTo(p.x - dirX * len * 0.45, p.y - dirY * len * 0.45);
            tacticalCtx.lineTo(p.x - dirX * len * 0.65 - dirY * wing, p.y - dirY * len * 0.65 + dirX * wing);
        } else if (symbol.kind === 'missile') {
            tacticalCtx.moveTo(p.x + dirX * len, p.y + dirY * len);
            tacticalCtx.lineTo(p.x - dirX * len * 0.6 + dirY * wing, p.y - dirY * len * 0.6 - dirX * wing);
            tacticalCtx.lineTo(p.x - dirX * len * 0.35, p.y - dirY * len * 0.35);
            tacticalCtx.lineTo(p.x - dirX * len * 0.6 - dirY * wing, p.y - dirY * len * 0.6 + dirX * wing);
        } else {
            tacticalCtx.arc(p.x, p.y, 5, 0, Math.PI * 2);
        }
        tacticalCtx.closePath();
        tacticalCtx.fill();
    }

    if (isTacticalDrawPhaseEnabled('missileUnits')) {
        const missileUnits = plottedUnits.filter((u) => String(u.type || '') === 'Missile');
        for (const u of missileUnits) {
            const p = toCanvas(Number(u.x || 0), Number(u.y || 0));
            const hdg = Number(u.heading || 0);
            const rad = (90.0 - hdg) * Math.PI / 180.0;
            const dirX = Math.cos(rad);
            const dirY = -Math.sin(rad);
            const color = tacticalAffiliationStyle(u.side).weaponColor;
            tacticalCtx.save();
            tacticalCtx.shadowBlur = 12;
            tacticalCtx.shadowColor = color;
            tacticalCtx.strokeStyle = color;
            tacticalCtx.fillStyle = color;
            tacticalCtx.lineWidth = 2;
            tacticalCtx.beginPath();
            tacticalCtx.moveTo(p.x + dirX * 15, p.y + dirY * 15);
            tacticalCtx.lineTo(p.x - dirX * 10 + dirY * 5, p.y - dirY * 10 - dirX * 5);
            tacticalCtx.lineTo(p.x - dirX * 5, p.y - dirY * 5);
            tacticalCtx.lineTo(p.x - dirX * 10 - dirY * 5, p.y - dirY * 10 + dirX * 5);
            tacticalCtx.closePath();
            tacticalCtx.fill();
            tacticalCtx.beginPath();
            tacticalCtx.arc(p.x, p.y, 8, 0, Math.PI * 2);
            tacticalCtx.stroke();
            tacticalCtx.restore();
        }
    }
    tacticalCtx.restore();

    const placedLabels = [];
    tacticalCtx.font = '11px monospace';
    for (const [idx, u] of plottedUnits.entries()) {
        if (String(u.type || '') === 'Missile') continue;
        const p = toCanvas(Number(u.x || 0), Number(u.y || 0));
        const label = String(u.name || u.id);
        const textWidth = tacticalCtx.measureText(label).width;
        const textHeight = 11;
        let anchorX = p.x + 10;
        let anchorY = p.y - 10;
        let attempts = 0;
        while (attempts < 8) {
            const box = {
                left: anchorX - 3,
                top: anchorY - textHeight,
                right: anchorX + textWidth + 3,
                bottom: anchorY + 4,
            };
            const overlaps = placedLabels.some((other) => !(
                box.right < other.left
                || box.left > other.right
                || box.bottom < other.top
                || box.top > other.bottom
            ));
            if (!overlaps) {
                placedLabels.push(box);
                break;
            }
            const lane = attempts + 1;
            const dir = ((idx + lane) % 2 === 0) ? -1 : 1;
            anchorY = p.y + dir * (14 + lane * 12);
            anchorX = p.x + 10 + lane * 4;
            attempts += 1;
        }

        tacticalCtx.strokeStyle = tacticalSymbology.label.leader;
        tacticalCtx.lineWidth = 1;
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(p.x + 3, p.y - 3);
        tacticalCtx.lineTo(anchorX - 4, anchorY - 4);
        tacticalCtx.stroke();

        tacticalCtx.fillStyle = tacticalSymbology.label.background;
        tacticalCtx.fillRect(anchorX - 4, anchorY - textHeight - 2, textWidth + 8, textHeight + 6);
        tacticalCtx.strokeStyle = tacticalAffiliationStyle(u.side).labelStroke;
        tacticalCtx.strokeRect(anchorX - 4, anchorY - textHeight - 2, textWidth + 8, textHeight + 6);
        tacticalCtx.fillStyle = tacticalSymbology.label.text;
        tacticalCtx.fillText(label, anchorX, anchorY);
    }

    if (vizState.mapMeasure) {
        drawMeasurement(vizState.mapMeasure, toCanvas);
    }

    vizState.tacticalViewport = {
        cx,
        cy,
        scale,
        baseScale,
        gridStepM,
        plotLeft,
        plotTop,
        plotWidth,
        plotHeight,
    };
    const kmPer100px = (100.0 / scale) / 1000.0;
    const zoomPct = Math.round(tacticalInteraction.zoom * 100);
    dom.tacticalScale.innerText = formatTacticalScaleText(kmPer100px, gridStepM, zoomPct);
}

function drawFocusBrackets(p, radius, color) {
    const arm = Math.max(5, radius * 0.45);
    tacticalCtx.save();
    tacticalCtx.strokeStyle = color;
    tacticalCtx.lineWidth = 1.6;
    tacticalCtx.globalAlpha = 0.9;
    for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        const cornerX = p.x + sx * radius;
        const cornerY = p.y + sy * radius;
        tacticalCtx.beginPath();
        tacticalCtx.moveTo(cornerX - sx * arm, cornerY);
        tacticalCtx.lineTo(cornerX, cornerY);
        tacticalCtx.lineTo(cornerX, cornerY - sy * arm);
        tacticalCtx.stroke();
    }
    tacticalCtx.restore();
}

function formatMeasureDistance(meters) {
    if (meters >= 10000) return `${(meters / 1000).toFixed(1)} km`;
    if (meters >= 1000) return `${(meters / 1000).toFixed(2)} km`;
    return `${Math.round(meters)} m`;
}

function drawMeasurement(measure, toCanvas) {
    const a = toCanvas(measure.x0, measure.y0);
    const b = toCanvas(measure.x1, measure.y1);
    const dx = measure.x1 - measure.x0;
    const dy = measure.y1 - measure.y0;
    const distM = Math.hypot(dx, dy);
    // Bearing measured from north, clockwise (sim: +y north, +x east).
    const bearing = (Math.atan2(dx, dy) * 180.0 / Math.PI + 360.0) % 360.0;

    tacticalCtx.save();
    tacticalCtx.strokeStyle = 'rgba(255, 180, 84, 0.9)';
    tacticalCtx.fillStyle = 'rgba(255, 180, 84, 0.9)';
    tacticalCtx.lineWidth = 1.4;
    tacticalCtx.setLineDash([7, 5]);
    tacticalCtx.beginPath();
    tacticalCtx.moveTo(a.x, a.y);
    tacticalCtx.lineTo(b.x, b.y);
    tacticalCtx.stroke();
    tacticalCtx.setLineDash([]);
    for (const point of [a, b]) {
        tacticalCtx.beginPath();
        tacticalCtx.arc(point.x, point.y, 3, 0, Math.PI * 2);
        tacticalCtx.fill();
    }

    const label = `${formatMeasureDistance(distM)} | ${String(Math.round(bearing)).padStart(3, '0')}°`;
    tacticalCtx.font = '11px monospace';
    const textWidth = tacticalCtx.measureText(label).width;
    const midX = (a.x + b.x) * 0.5;
    const midY = (a.y + b.y) * 0.5;
    tacticalCtx.fillStyle = 'rgba(5, 11, 17, 0.9)';
    tacticalCtx.fillRect(midX + 8, midY - 18, textWidth + 10, 17);
    tacticalCtx.strokeStyle = 'rgba(255, 180, 84, 0.55)';
    tacticalCtx.lineWidth = 1;
    tacticalCtx.strokeRect(midX + 8, midY - 18, textWidth + 10, 17);
    tacticalCtx.fillStyle = '#ffd9a1';
    tacticalCtx.fillText(label, midX + 13, midY - 5);
    tacticalCtx.restore();
}

export function maybeDrawTacticalView(nowMs) {
    if (vizState.presentationMode !== 'MAP' || !vizState.tacticalNeedsDraw) return;
    if (!vizState.lastTacticalState && !sceneGeometryAvailable()) return;
    if ((nowMs - vizState.lastTacticalRenderAt) < TACTICAL_RENDER_INTERVAL_MS) return;
    drawTacticalView(vizState.lastTacticalState);
    vizState.lastTacticalRenderAt = nowMs;
    vizState.tacticalNeedsDraw = false;
}
