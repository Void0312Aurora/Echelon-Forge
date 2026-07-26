"""Resolve the scenario sun-illumination truth for the viz frontend.

The engine owns the operational sun direction (``IEnvironmentModel``); the
scenario's ``environment.illumination`` block is the configuration that both
the kernel apply path and this viz payload read, so display and sensor-glare
adjudication share one source. When the sim handle exposes the kernel getter
we cross-check that the engine actually holds the same direction.
"""

from __future__ import annotations

import math
from typing import Any

DEFAULT_SUN_AZIMUTH_DEG = 0.0
DEFAULT_SUN_ELEVATION_DEG = 45.0


def sun_vector_from_angles(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    """Unit vector toward the sun in ENU (east, north, up).

    NAV azimuth: 0 = North (+Y), clockwise positive toward East (+X).
    Mirrors DefaultEnvironmentModel::get_sun_direction.
    """
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    horizontal = math.cos(el)
    return (math.sin(az) * horizontal, math.cos(az) * horizontal, math.sin(el))


def resolve_scenario_illumination(
    scenario_data: dict[str, Any] | None,
    *,
    sim: Any = None,
) -> dict[str, Any]:
    """Build the ``illumination`` block for the viz ``map_setup`` payload."""
    env_cfg = (scenario_data or {}).get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    raw_cfg = env_cfg.get("illumination", None)
    configured = isinstance(raw_cfg, dict)
    cfg = raw_cfg if configured else {}

    try:
        azimuth = float(cfg.get("sun_azimuth_deg", DEFAULT_SUN_AZIMUTH_DEG))
    except (TypeError, ValueError):
        azimuth = DEFAULT_SUN_AZIMUTH_DEG
    try:
        elevation = float(cfg.get("sun_elevation_deg", DEFAULT_SUN_ELEVATION_DEG))
    except (TypeError, ValueError):
        elevation = DEFAULT_SUN_ELEVATION_DEG

    # Same normalization the engine applies.
    azimuth = azimuth % 360.0
    elevation = max(-90.0, min(90.0, elevation))

    payload: dict[str, Any] = {
        "sun_azimuth_deg": azimuth,
        "sun_elevation_deg": elevation,
        "configured": configured,
        "engine_confirmed": False,
    }

    if sim is not None and hasattr(sim, "get_sun_direction"):
        try:
            engine_vec = tuple(float(v) for v in sim.get_sun_direction())
            expected_vec = sun_vector_from_angles(azimuth, elevation)
            dot = sum(a * b for a, b in zip(engine_vec, expected_vec))
            payload["engine_confirmed"] = bool(dot > 0.99999)
        except Exception:
            pass

    return payload
