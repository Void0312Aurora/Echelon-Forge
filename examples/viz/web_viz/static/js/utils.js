// Small shared numeric helpers.

export function finiteNumber(value, fallback = null) {
    const coerced = Number(value);
    return Number.isFinite(coerced) ? coerced : fallback;
}

export function shortestAngleDeltaDeg(fromDeg, toDeg) {
    let delta = (Number(toDeg || 0) - Number(fromDeg || 0)) % 360.0;
    if (delta > 180.0) delta -= 360.0;
    if (delta < -180.0) delta += 360.0;
    return delta;
}

export function lerpAngleDeg(fromDeg, toDeg, alpha) {
    const value = Number(fromDeg || 0) + shortestAngleDeltaDeg(fromDeg, toDeg) * alpha;
    return ((value % 360.0) + 360.0) % 360.0;
}
