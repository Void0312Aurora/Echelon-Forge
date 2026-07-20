// Applies the scenario sun truth (from the backend map_setup payload) to
// every lighting consumer: the 2D hillshade and the 3D sun light + shadows.
// One truth source keeps what the operator sees consistent with the sun the
// engine uses for sensor glare adjudication.

import { vizState } from './store.js';
import { refreshIlluminationShading } from './scene-geometry.js';
import { updateSceneIllumination } from './scene3d.js';

export function applyIllumination(raw) {
    if (!raw || typeof raw !== 'object') return;
    const ill = vizState.illumination;
    const azimuth = Number(raw.sun_azimuth_deg);
    const elevation = Number(raw.sun_elevation_deg);
    const nextAzimuth = Number.isFinite(azimuth) ? ((azimuth % 360) + 360) % 360 : ill.sunAzimuthDeg;
    const nextElevation = Number.isFinite(elevation) ? Math.max(-90, Math.min(90, elevation)) : ill.sunElevationDeg;
    const changed = nextAzimuth !== ill.sunAzimuthDeg || nextElevation !== ill.sunElevationDeg;
    ill.sunAzimuthDeg = nextAzimuth;
    ill.sunElevationDeg = nextElevation;
    ill.configured = !!raw.configured;
    ill.engineConfirmed = !!raw.engine_confirmed;
    if (changed) {
        updateSceneIllumination();
        refreshIlluminationShading();
        console.log(
            `Illumination applied: sun az ${nextAzimuth.toFixed(1)} deg, el ${nextElevation.toFixed(1)} deg`
            + (ill.engineConfirmed ? ' (engine-confirmed)' : ''),
        );
    }
}
