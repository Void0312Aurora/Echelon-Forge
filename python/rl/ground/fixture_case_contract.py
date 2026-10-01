"""Case contract for fixture-derived Ground infantry acceptance cases.

A :class:`FixtureCase` is one start/waypoint route with an expected native
outcome that the fixture derivation predicted independently of the native
probe. The native blocked-reason names are the probe's own vocabulary.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .fixture_geometry import Point, polyline_length


FIXTURE_CASE_CONTRACT_VERSION = "ground_infantry_fixture_cases.v1"

WATER_TRANSITION_BLOCKED = "water_transition_blocked"
OBSTACLE_TRANSITION_BLOCKED = "obstacle_transition_blocked"

# Landcover legend semantics that the training contract requires to fail
# closed ("unknown terrain semantics cannot silently become passable" and
# "river crossing is only possible through an explicitly admitted crossing").
# Keyed by the bundle legend name and mapped to the native blocked reason the
# probe must report. Every other legend class is expected to be traversable.
BLOCKING_LANDCOVER_SEMANTICS: Mapping[str, str] = {
    "permanent_water": WATER_TRANSITION_BLOCKED,
    "unknown_nodata": OBSTACLE_TRANSITION_BLOCKED,
}


class FixtureCaseError(ValueError):
    """Raised when the fixture cannot populate a required case (fail closed)."""


@dataclass(frozen=True)
class FixtureCase:
    """One start/waypoint case with an independent expected native outcome."""

    case_id: str
    category: str
    expected: str
    start_xy_m: Point
    waypoints_xy_m: tuple[Point, ...]
    expected_block_reason: str | None = None
    # Distance from the start to the first predicted blocked sample, and the
    # last predicted passable sample before it. ``None`` for reach cases.
    block_distance_m: float | None = None
    approach_xy_m: Point | None = None
    requires_bridge_admission: bool = False
    derivation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.expected not in ("reach", "block", "held"):
            raise FixtureCaseError(f"{self.case_id}: expected must be reach, block, or held")
        if (self.expected == "block") != (self.expected_block_reason is not None):
            raise FixtureCaseError(f"{self.case_id}: block cases need exactly one reason")

    @property
    def route_distance_m(self) -> float:
        return polyline_length((self.start_xy_m,) + self.waypoints_xy_m)

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "expected": self.expected,
            "expected_block_reason": self.expected_block_reason,
            "start_xy_m": list(self.start_xy_m),
            "waypoints_xy_m": [list(point) for point in self.waypoints_xy_m],
            "route_distance_m": self.route_distance_m,
            "block_distance_m": self.block_distance_m,
            "approach_xy_m": None if self.approach_xy_m is None else list(self.approach_xy_m),
            "requires_bridge_admission": self.requires_bridge_admission,
            "derivation": dict(self.derivation),
        }


def case_parameters_digest(cases: Sequence[FixtureCase | Mapping[str, Any]]) -> str:
    """SHA-256 over the canonical JSON of every case's derived parameters.

    Accepts cases or their :meth:`FixtureCase.as_dict` records (for example
    the ``cases`` list of an acceptance-matrix report), in case order.
    """

    records = [case.as_dict() if isinstance(case, FixtureCase) else dict(case) for case in cases]
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "BLOCKING_LANDCOVER_SEMANTICS",
    "FIXTURE_CASE_CONTRACT_VERSION",
    "FixtureCase",
    "FixtureCaseError",
    "OBSTACLE_TRANSITION_BLOCKED",
    "WATER_TRANSITION_BLOCKED",
    "case_parameters_digest",
]
