// Asset registry entry normalization and unit -> registry entry matching.
// The registry decides which 3D model, 2D symbol, and realism notes apply to
// a unit. 3D model loading itself lives in scene3d.js.

import { vizState } from './store.js';

export function normalizeRegistryEntry(entry) {
    const visual = entry?.visual || {};
    const chase = Array.isArray(visual.chase_offset) ? visual.chase_offset : [0, 30, 80];
    return {
        id: String(entry?.id || '').trim(),
        label: String(entry?.label || '').trim(),
        match: {
            unit_type: String(entry?.match?.unit_type || '').trim(),
            platform_type_patterns: Array.isArray(entry?.match?.platform_type_patterns) ? entry.match.platform_type_patterns : [],
            name_patterns: Array.isArray(entry?.match?.name_patterns) ? entry.match.name_patterns : [],
            service_profiles: Array.isArray(entry?.match?.service_profiles) ? entry.match.service_profiles : [],
        },
        visual: {
            asset_path: String(visual.asset_path || '').trim(),
            scale: Number(visual.scale || 1.0),
            yaw_correction_deg: Number(visual.yaw_correction_deg || 0.0),
            waterline_offset_m: Number(visual.waterline_offset_m || 0.0),
            chase_offset: [
                Number(chase[0] || 0.0),
                Number(chase[1] || 30.0),
                Number(chase[2] || 80.0),
            ],
            fallback_hull_length_m: Number(visual.fallback_hull_length_m || 160.0),
            fallback_hull_beam_m: Number(visual.fallback_hull_beam_m || 24.0),
            fallback_hull_height_m: Number(visual.fallback_hull_height_m || 12.0),
            fallback_super_length_m: Number(visual.fallback_super_length_m || 56.0),
            fallback_super_beam_m: Number(visual.fallback_super_beam_m || 16.0),
            fallback_super_height_m: Number(visual.fallback_super_height_m || 18.0),
            fallback_super_offset_x_m: Number(visual.fallback_super_offset_x_m || -8.0),
            fallback_super_offset_y_m: Number(visual.fallback_super_offset_y_m || 18.0),
        },
        realism: {
            substitute_for: String(entry?.realism?.substitute_for || '').trim(),
            realism_note: String(entry?.realism?.realism_note || '').trim(),
        },
        show_in_2d_as: String(entry?.show_in_2d_as || '').trim(),
        show_sensor_ring: entry?.show_sensor_ring !== false,
        render_priority: Number(entry?.render_priority || 100),
    };
}

export function matchesPattern(pattern, text) {
    const p = String(pattern || '').trim().toUpperCase();
    const t = String(text || '').trim().toUpperCase();
    return !!p && !!t && t.includes(p);
}

export function scoreAssetEntry(entry, uData) {
    const match = entry?.match || {};
    const unitType = String(uData?.type || '').trim();
    const platformType = String(uData?.platform_type || '').trim();
    const name = String(uData?.name || '').trim();
    const serviceProfile = String(uData?.service_profile || '').trim();

    if (match.unit_type && String(match.unit_type).trim() !== unitType) {
        return null;
    }

    let score = Number(entry?.render_priority || 1000);
    let matchedAnything = false;

    const platformPatterns = Array.isArray(match.platform_type_patterns) ? match.platform_type_patterns : [];
    const namePatterns = Array.isArray(match.name_patterns) ? match.name_patterns : [];
    const serviceProfiles = Array.isArray(match.service_profiles) ? match.service_profiles : [];
    const hasIdentityPatterns = platformPatterns.length > 0 || namePatterns.length > 0;

    let identityHit = false;
    if (platformPatterns.length > 0) {
        const hit = platformPatterns.some((pattern) => matchesPattern(pattern, platformType));
        if (hit) {
            identityHit = true;
            matchedAnything = true;
            score -= 100;
        }
    }

    if (namePatterns.length > 0) {
        const hit = namePatterns.some((pattern) => matchesPattern(pattern, name));
        if (hit) {
            identityHit = true;
            matchedAnything = true;
            score -= 25;
        }
    }

    if (hasIdentityPatterns && !identityHit) {
        return null;
    }

    if (serviceProfiles.length > 0) {
        if (serviceProfile) {
            const hit = serviceProfiles.some((pattern) => matchesPattern(pattern, serviceProfile));
            if (!hit) return null;
            matchedAnything = true;
            score -= 10;
        }
    }

    if (!matchedAnything && match.unit_type) {
        score += 500;
    }
    return score;
}

export function resolveAssetEntry(uData) {
    const candidates = Array.isArray(vizState.currentAssetRegistry?.entries)
        ? vizState.currentAssetRegistry.entries
        : [];
    let best = null;
    let bestScore = Infinity;
    candidates.forEach((entry) => {
        const score = scoreAssetEntry(entry, uData);
        if (score === null) return;
        if (score < bestScore) {
            best = entry;
            bestScore = score;
        }
    });
    return best;
}

export function unitSymbolSpec(u) {
    const entry = resolveAssetEntry(u);
    const style = String(entry?.show_in_2d_as || '').trim().toLowerCase();
    if (style === 'ship') {
        return { kind: 'ship', len: 18, wing: 7 };
    }
    if (style === 'aircraft') {
        return { kind: 'aircraft', len: 16, wing: 6 };
    }
    if (style === 'missile') {
        return { kind: 'missile', len: 13, wing: 4 };
    }
    if (style === 'generic') {
        return { kind: 'generic', len: 12, wing: 5 };
    }
    if (u.type === 'Aircraft') {
        return { kind: 'aircraft', len: 16, wing: 6 };
    }
    if (u.type === 'Ship') {
        return { kind: 'ship', len: 18, wing: 7 };
    }
    if (u.type === 'Missile') {
        return { kind: 'missile', len: 13, wing: 4 };
    }
    if (u.type === 'Ground') {
        return { kind: 'generic', len: 10, wing: 5 };
    }
    return { kind: 'generic', len: 12, wing: 5 };
}

export function shouldShowSensorRingForUnit(ring) {
    const pseudoUnit = {
        name: ring?.name || '',
        platform_type: ring?.platform_type || '',
        type: 'Ship',
        side: ring?.side || '',
        service_profile: ring?.service_profile || '',
    };
    const entry = resolveAssetEntry(pseudoUnit);
    if (!entry) return true;
    return entry.show_sensor_ring !== false;
}
