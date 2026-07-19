// Environment overlay geometry, styling, LOD label logic, and 2D drawing.
// Overlays are display-only products delivered by the backend
// (examples/viz/runtime/environment_overlays.py); nothing here feeds back
// into the simulation.

import { dom } from './dom.js';
import { vizState } from './store.js';
import { tacticalSymbology } from './symbology.js';
import { i18n, localizeEnvironmentToken } from './i18n.js';
import { isTacticalDrawPhaseEnabled } from './layers.js';
import { finiteNumber } from './utils.js';

export function getEnvironmentOverlayEntries() {
    if (!isTacticalDrawPhaseEnabled('environment') || !vizState.environmentOverlays) return [];
    const layers = Array.isArray(vizState.environmentOverlays.layers) ? vizState.environmentOverlays.layers : [];
    const entries = [];
    for (const layer of layers) {
        const layerEntries = Array.isArray(layer.entries) ? layer.entries : [];
        for (const entry of layerEntries) {
            if (!entry || typeof entry !== 'object') continue;
            entries.push({
                ...entry,
                layer_id: layer.layer_id || '',
                layer_source: layer.source || '',
            });
        }
    }
    return entries;
}

export function rotatedRectCorners(geometry) {
    const x = finiteNumber(geometry?.x);
    const y = finiteNumber(geometry?.y);
    const width = finiteNumber(geometry?.width);
    const length = finiteNumber(geometry?.length);
    const heading = finiteNumber(geometry?.heading, 0.0);
    if (x === null || y === null || width === null || length === null || width <= 0 || length <= 0) {
        return [];
    }
    const rad = heading * Math.PI / 180.0;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    return [
        [-width * 0.5, -length * 0.5],
        [width * 0.5, -length * 0.5],
        [width * 0.5, length * 0.5],
        [-width * 0.5, length * 0.5],
    ].map(([dx, dy]) => ({
        x: x + dx * cos - dy * sin,
        y: y + dx * sin + dy * cos,
    }));
}

export function environmentOverlayBounds(entry) {
    const geometry = entry?.geometry || {};
    const geometryType = String(geometry.geometry_type || '').toLowerCase();
    if (geometryType === 'rect') {
        const corners = rotatedRectCorners(geometry);
        if (corners.length === 0) return null;
        return corners.reduce((acc, point) => ({
            minX: Math.min(acc.minX, point.x),
            maxX: Math.max(acc.maxX, point.x),
            minY: Math.min(acc.minY, point.y),
            maxY: Math.max(acc.maxY, point.y),
        }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });
    }
    if (geometryType === 'aabb') {
        const minX = finiteNumber(geometry.min_x);
        const maxX = finiteNumber(geometry.max_x);
        const minY = finiteNumber(geometry.min_y);
        const maxY = finiteNumber(geometry.max_y);
        if (minX === null || maxX === null || minY === null || maxY === null || maxX <= minX || maxY <= minY) {
            return null;
        }
        return { minX, maxX, minY, maxY };
    }
    return null;
}

export function environmentOverlayStyle(entry) {
    const kind = String(entry?.overlay_kind || '').toLowerCase();
    const attrs = entry?.attributes || {};
    if (kind === 'occlusion_candidate') {
        const family = String(attrs.component_family || '').toLowerCase();
        if (family === 'vegetation') {
            return tacticalSymbology.environment.occlusionCandidate.vegetation;
        }
        return tacticalSymbology.environment.occlusionCandidate.structure;
    }

    const surface = String(attrs.surface || '').toLowerCase();
    return tacticalSymbology.environment.surfaces[surface]
        || tacticalSymbology.environment.surfaces.default;
}

export function formatEnvironmentMeters(value) {
    const meters = Number(value);
    if (!Number.isFinite(meters)) return '';
    if (vizState.uiLanguage === 'zh') {
        if (Math.abs(meters) >= 1000) return `${(meters / 1000.0).toFixed(1)}公里`;
        if (Math.abs(meters) >= 100) return `${Math.round(meters)}米`;
        return `${meters.toFixed(1).replace(/\.0$/, '')}米`;
    }
    if (Math.abs(meters) >= 1000) return `${(meters / 1000.0).toFixed(1)}${i18n('ui.kilometers')}`;
    if (Math.abs(meters) >= 100) return `${Math.round(meters)}${i18n('ui.meters')}`;
    return `${meters.toFixed(1).replace(/\.0$/, '')}${i18n('ui.meters')}`;
}

export function compactEnvironmentLabel(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const localized = localizeEnvironmentToken(raw);
    if (localized) return localized.length > 14 ? `${localized.slice(0, 12)}...` : localized;
    const tail = raw.split(':').filter(Boolean).pop() || raw;
    const cleaned = tail
        .replace(/^deterministic[-_]/i, '')
        .replace(/^test[-_]/i, '')
        .replace(/[-_]+/g, ' ')
        .trim();
    const text = (cleaned || raw).toUpperCase();
    return text.length > 28 ? `${text.slice(0, 25)}...` : text;
}

export function environmentOverlayTypeCode(entry) {
    const kind = String(entry?.overlay_kind || '').toLowerCase();
    const attrs = entry?.attributes || {};
    if (kind === 'occlusion_candidate') {
        const family = String(attrs.component_family || '').toLowerCase();
        if (family === 'vegetation') return i18n('env.vegetationCode');
        if (family === 'structure') return i18n('env.structureCode');
        return i18n('env.occlusionCode');
    }
    const source = String(attrs.source || entry?.layer_source || '').toLowerCase();
    if (source.includes('surface_zone_index')) return i18n('env.surfaceIndexCode');
    return i18n('env.surfaceCode');
}

export function environmentOverlayDetailText(entry, bounds) {
    const kind = String(entry?.overlay_kind || '').toLowerCase();
    const attrs = entry?.attributes || {};
    if (kind === 'occlusion_candidate') {
        const height = finiteNumber(attrs.height_m);
        const family = compactEnvironmentLabel(attrs.component_family || 'candidate');
        return height === null ? family : `${family} ${i18n('env.height')} ${formatEnvironmentMeters(height)}`;
    }
    const geometry = entry?.geometry || {};
    const width = finiteNumber(geometry.width, bounds.maxX - bounds.minX);
    const length = finiteNumber(geometry.length, bounds.maxY - bounds.minY);
    const surface = compactEnvironmentLabel(attrs.surface || 'surface');
    if (width === null || length === null) return surface;
    return `${surface} ${formatEnvironmentMeters(width)} x ${formatEnvironmentMeters(length)}`;
}

export function environmentOverlayLabelPriority(entry) {
    const kind = String(entry?.overlay_kind || '').toLowerCase();
    const attrs = entry?.attributes || {};
    if (kind === 'occlusion_candidate') {
        const family = String(attrs.component_family || '').toLowerCase();
        if (family === 'vegetation') return 0.75;
        if (family === 'structure') return 1.0;
        return 0.9;
    }
    const surface = String(attrs.surface || '').toLowerCase();
    if (surface === 'water') return 1.8;
    if (surface === 'asphalt' || surface === 'concrete') return 1.15;
    return 0.95;
}

export function environmentOverlayLabelLod(entry, bounds, scale) {
    const widthPx = Math.max(0, (bounds.maxX - bounds.minX) * scale);
    const heightPx = Math.max(0, (bounds.maxY - bounds.minY) * scale);
    const maxDimPx = Math.max(widthPx, heightPx);
    const minDimPx = Math.min(widthPx, heightPx);
    const footprintPx = Math.sqrt(Math.max(0, widthPx * heightPx));
    const zoom = Math.max(0.35, finiteNumber(vizState.tacticalInteraction.zoom, 1.0) || 1.0);
    const zoomWeight = Math.sqrt(zoom);
    const priority = environmentOverlayLabelPriority(entry);
    const labelScore = Math.max(
        footprintPx * 1.1,
        maxDimPx * 0.42,
        minDimPx * 3.8
    ) * priority * zoomWeight;
    const detailScore = (
        Math.min(maxDimPx, 260.0) * 0.32
        + minDimPx * 4.2
        + footprintPx * 0.6
    ) * priority * zoomWeight;

    if (labelScore < 82.0) return { level: 'hidden', alpha: 0.0 };
    const alpha = Math.max(0.35, Math.min(1.0, (labelScore - 82.0) / 28.0));
    if (zoom >= 1.25 && detailScore >= 150.0) {
        return { level: 'detail', alpha };
    }
    return { level: 'summary', alpha };
}

export function environmentLabelBoxesOverlap(a, b) {
    return !(
        a.right < b.left
        || a.left > b.right
        || a.bottom < b.top
        || a.top > b.bottom
    );
}

export function drawEnvironmentOverlayAnchor(ctx, center, style, bounds, scale) {
    const widthPx = Math.max(0, (bounds.maxX - bounds.minX) * scale);
    const heightPx = Math.max(0, (bounds.maxY - bounds.minY) * scale);
    const radius = Math.max(3.5, Math.min(7.0, Math.max(widthPx, heightPx) * 0.16 + 3.0));
    ctx.save();
    ctx.lineWidth = 4;
    ctx.strokeStyle = tacticalSymbology.environment.marker.halo;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = tacticalSymbology.environment.marker.anchorFill;
    ctx.fill();
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = style.stroke;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(center.x - radius - 2, center.y);
    ctx.lineTo(center.x + radius + 2, center.y);
    ctx.moveTo(center.x, center.y - radius - 2);
    ctx.lineTo(center.x, center.y + radius + 2);
    ctx.stroke();
    ctx.restore();
}

export function drawEnvironmentOverlayCallout(ctx, entry, center, style, scale, bounds, labelLod, placedLabelBoxes = []) {
    const lod = labelLod || environmentOverlayLabelLod(entry, bounds, scale);
    if (!lod || lod.level === 'hidden') return;
    const typeCode = environmentOverlayTypeCode(entry);
    const label = compactEnvironmentLabel(entry?.label || entry?.attributes?.source_object_id || entry?.overlay_id);
    const detail = environmentOverlayDetailText(entry, bounds);
    if (!label && !detail) return;

    const widthPx = Math.max(0, (bounds.maxX - bounds.minX) * scale);
    const heightPx = Math.max(0, (bounds.maxY - bounds.minY) * scale);
    const maxDimPx = Math.max(widthPx, heightPx);
    const offsetX = Math.max(14, Math.min(42, maxDimPx * 0.35 + 12));
    const offsetY = Math.max(12, Math.min(28, maxDimPx * 0.22 + 10));
    const primary = [typeCode, label].filter(Boolean).join(' ');
    const lines = lod.level === 'detail'
        ? [primary, detail].filter(Boolean)
        : [primary || detail].filter(Boolean);
    if (lines.length === 0) return;

    ctx.save();
    ctx.globalAlpha *= Math.max(0.35, Math.min(1.0, Number(lod.alpha || 1.0)));
    ctx.font = '10px monospace';
    const textWidth = Math.max(...lines.map((line) => ctx.measureText(line).width));
    const boxWidth = textWidth + 10;
    const boxHeight = lines.length * 12 + 6;
    const canvasWidth = dom.tacticalCanvas.clientWidth || window.innerWidth;
    const canvasHeight = dom.tacticalCanvas.clientHeight || window.innerHeight;
    let boxX = center.x + offsetX;
    if (boxX + boxWidth > canvasWidth - 8) boxX = center.x - offsetX - boxWidth;
    boxX = Math.max(8, Math.min(canvasWidth - boxWidth - 8, boxX));
    let boxY = center.y - offsetY - boxHeight;
    if (boxY < 8) boxY = center.y + offsetY;
    boxY = Math.max(8, Math.min(canvasHeight - boxHeight - 8, boxY));
    const leaderEndX = Math.max(4, Math.min(canvasWidth - 4, boxX));
    const leaderEndY = boxY + boxHeight;

    ctx.strokeStyle = tacticalSymbology.environment.marker.leader;
    ctx.lineWidth = 1;
    const labelBox = {
        left: boxX - 5,
        top: boxY - 4,
        right: boxX + boxWidth + 5,
        bottom: boxY + boxHeight + 4,
    };
    if (placedLabelBoxes.some((other) => environmentLabelBoxesOverlap(labelBox, other))) {
        ctx.restore();
        return;
    }
    placedLabelBoxes.push(labelBox);

    ctx.setLineDash([3, 4]);
    ctx.beginPath();
    ctx.moveTo(center.x, center.y);
    ctx.lineTo(leaderEndX, leaderEndY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = tacticalSymbology.environment.marker.textBackground;
    ctx.strokeStyle = style.stroke;
    ctx.lineWidth = 1;
    ctx.fillRect(boxX, boxY, boxWidth, boxHeight);
    ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);
    ctx.fillStyle = tacticalSymbology.environment.marker.sourceText;
    ctx.fillText(lines[0], boxX + 5, boxY + 12);
    if (lines.length > 1) {
        ctx.fillStyle = style.label;
        ctx.fillText(lines[1], boxX + 5, boxY + 24);
    }
    ctx.restore();
}

export function drawEnvironmentOverlays(ctx, entries, toCanvas, scale) {
    const placedLabelBoxes = [];
    for (const entry of entries) {
        const geometry = entry?.geometry || {};
        const geometryType = String(geometry.geometry_type || '').toLowerCase();
        const bounds = environmentOverlayBounds(entry);
        if (!bounds) continue;
        const style = environmentOverlayStyle(entry);
        ctx.save();
        ctx.fillStyle = style.fill;
        ctx.strokeStyle = style.stroke;
        ctx.lineWidth = String(entry?.overlay_kind || '') === 'occlusion_candidate' ? 1.2 : 1.0;
        ctx.setLineDash(style.dash || []);
        if (geometryType === 'rect') {
            const corners = rotatedRectCorners(geometry).map((point) => toCanvas(point.x, point.y));
            if (corners.length === 4) {
                ctx.beginPath();
                ctx.moveTo(corners[0].x, corners[0].y);
                for (let idx = 1; idx < corners.length; idx += 1) {
                    ctx.lineTo(corners[idx].x, corners[idx].y);
                }
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }
        } else if (geometryType === 'aabb') {
            const a = toCanvas(bounds.minX, bounds.maxY);
            const b = toCanvas(bounds.maxX, bounds.minY);
            ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
            ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);
        }
        ctx.setLineDash([]);
        const center = toCanvas((bounds.minX + bounds.maxX) * 0.5, (bounds.minY + bounds.maxY) * 0.5);
        drawEnvironmentOverlayAnchor(ctx, center, style, bounds, scale);
        const labelLod = environmentOverlayLabelLod(entry, bounds, scale);
        drawEnvironmentOverlayCallout(ctx, entry, center, style, scale, bounds, labelLod, placedLabelBoxes);
        ctx.restore();
    }
}
