"""Canonical scalar angle/geometry helpers.

Single owner for the small degree-domain helpers that were previously
re-implemented across runtime, tooling, contracts, and example agents.
The two wrap conventions are distinct functions on purpose:

- ``wrap_signed_deg``: [-180.0, 180.0) signed error/delta convention.
- ``wrap_heading_deg``: [0.0, 360.0) compass-heading convention.

Float caveats (inherited verbatim from the replaced implementations):
``wrap_heading_deg`` uses plain ``% 360.0`` and can return exactly 360.0 for
inputs a few ULP below zero; ``bearing_deg`` uses the historical
``(degrees(atan2(dx, dy)) + 360.0) % 360.0`` form, which is NOT bit-identical
to ``wrap_heading_deg(degrees(atan2(dx, dy)))`` (the +360.0 round-trip
perturbs positive angles by ~1e-14 deg). Call sites that historically used
the plain ``% 360.0`` bearing form keep it locally instead of aliasing.

This module must stay dependency-free (stdlib ``math`` only) so that every
layer (gym_envs, python.scenario, tools, examples) can import it without
cycles.
"""

from __future__ import annotations

import math


def wrap_signed_deg(angle_deg: float) -> float:
    """Wrap an angle in degrees to the signed interval [-180.0, 180.0)."""
    return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


def wrap_heading_deg(angle_deg: float) -> float:
    """Wrap an angle in degrees to the compass interval [0.0, 360.0)."""
    return float(float(angle_deg) % 360.0)


def heading_error_deg(target_deg: float, current_deg: float) -> float:
    """Signed shortest heading delta (target - current) in [-180.0, 180.0].

    Unlike ``wrap_signed_deg``, an exact half-turn keeps its sign
    (``heading_error_deg(270.0, 90.0) == 180.0``), matching the behavior of
    the migrated naval-screen runtime helper.
    """
    delta = wrap_heading_deg(target_deg) - wrap_heading_deg(current_deg)
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return float(delta)


def bearing_deg(dx: float, dy: float) -> float:
    """Compass bearing of a displacement (dx east, dy north) in [0.0, 360.0).

    The zero displacement maps to 0.0; callers that need a fallback heading
    for degenerate geometry keep that branch at the call site.
    """
    return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)


def bearing_between_deg(x0_m: float, y0_m: float, x1_m: float, y1_m: float) -> float:
    """Compass bearing from point (x0, y0) to point (x1, y1) in [0.0, 360.0)."""
    return bearing_deg(float(x1_m) - float(x0_m), float(y1_m) - float(y0_m))


def distance_m(x0_m: float, y0_m: float, x1_m: float, y1_m: float) -> float:
    """Planar euclidean distance between two points in meters."""
    return math.hypot(float(x1_m) - float(x0_m), float(y1_m) - float(y0_m))


__all__ = [
    "bearing_between_deg",
    "bearing_deg",
    "distance_m",
    "heading_error_deg",
    "wrap_heading_deg",
    "wrap_signed_deg",
]
