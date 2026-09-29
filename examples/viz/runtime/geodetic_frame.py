"""Geodetic anchor of the viz scene (Geodetic Frame P3-B).

The ``map_setup`` payload carries the scenario's geodetic anchor so a viewer can
place the local ENU frame on the globe. The anchor comes from the scenario's
``environment.geodetic_anchor`` (or the documented default) and, when the kernel
is available, is cross-checked against the engine's own anchor.
"""

from __future__ import annotations

from typing import Any

from python.scenario.compiler import resolve_environment_geodetic_anchor


def resolve_scenario_geodetic_frame(
    scenario_data: dict[str, Any] | None,
    *,
    sim: Any = None,
) -> dict[str, Any]:
    """Build the ``geodetic_frame`` block for the viz ``map_setup`` payload."""
    env_cfg = (scenario_data or {}).get("environment", {})
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    (latitude_deg, longitude_deg, height_m), source = resolve_environment_geodetic_anchor(env_cfg)
    payload: dict[str, Any] = {
        "frame": "local_enu_m",
        "projection": "azimuthal_equidistant_sphere",
        "anchor_lat_deg": latitude_deg,
        "anchor_lon_deg": longitude_deg,
        "anchor_height_m": height_m,
        "source": source,
        "engine_confirmed": False,
    }
    if sim is not None and hasattr(sim, "get_geodetic_anchor"):
        try:
            engine = tuple(float(v) for v in sim.get_geodetic_anchor())
            payload["engine_confirmed"] = bool(
                abs(engine[0] - latitude_deg) < 1e-9
                and abs(engine[1] - longitude_deg) < 1e-9
                and abs(engine[2] - height_m) < 1e-6
            )
        except Exception:
            pass
    return payload


__all__ = ["resolve_scenario_geodetic_frame"]
