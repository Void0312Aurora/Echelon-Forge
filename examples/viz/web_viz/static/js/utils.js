// @ts-check
// Small shared numeric helpers.

/**
 * @param {*} value
 * @param {number|null} [fallback]
 * @returns {number|null}
 */
export function finiteNumber(value, fallback = null) {
    const coerced = Number(value);
    return Number.isFinite(coerced) ? coerced : fallback;
}

/**
 * @param {number} fromDeg
 * @param {number} toDeg
 * @returns {number}
 */
export function shortestAngleDeltaDeg(fromDeg, toDeg) {
    let delta = (Number(toDeg || 0) - Number(fromDeg || 0)) % 360.0;
    if (delta > 180.0) delta -= 360.0;
    if (delta < -180.0) delta += 360.0;
    return delta;
}

/**
 * @param {number} fromDeg
 * @param {number} toDeg
 * @param {number} alpha
 * @returns {number}
 */
export function lerpAngleDeg(fromDeg, toDeg, alpha) {
    const value = Number(fromDeg || 0) + shortestAngleDeltaDeg(fromDeg, toDeg) * alpha;
    return ((value % 360.0) + 360.0) % 360.0;
}

// Unit vector toward the sun in ENU (east, north, up). NAV azimuth: 0=north,
// clockwise positive. Mirrors DefaultEnvironmentModel::get_sun_direction so
// the display lighting matches the engine's operational sun.
/**
 * @param {number} azimuthDeg
 * @param {number} elevationDeg
 * @returns {import('./types.js').SunVector}
 */
export function sunVectorFromAngles(azimuthDeg, elevationDeg) {
    const az = (Number(azimuthDeg) || 0) * (Math.PI / 180.0);
    const el = (Number(elevationDeg) || 0) * (Math.PI / 180.0);
    const horizontal = Math.cos(el);
    return {
        east: Math.sin(az) * horizontal,
        north: Math.cos(az) * horizontal,
        up: Math.sin(el),
    };
}
