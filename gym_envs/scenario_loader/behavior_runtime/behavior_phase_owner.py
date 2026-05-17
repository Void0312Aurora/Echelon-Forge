from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BEHAVIOR_PHASE_OWNER_ATTRS = frozenset(
    {
        "_approach_prev_dme_m",
        "_approach_prev_loc_abs",
        "_approach_prev_gs_abs",
        "post_waypoint_transition",
        "mission_phase_name",
    }
)


@dataclass(slots=True)
class BehaviorPhaseOwner:
    _approach_prev_dme_m: float | None = None
    _approach_prev_loc_abs: float | None = None
    _approach_prev_gs_abs: float | None = None
    post_waypoint_transition: dict[str, Any] | None = None
    mission_phase_name: str = "idle"

    def reset(self) -> None:
        self._approach_prev_dme_m = None
        self._approach_prev_loc_abs = None
        self._approach_prev_gs_abs = None
        self.post_waypoint_transition = None
        self.mission_phase_name = "idle"


def make_behavior_phase_owner() -> BehaviorPhaseOwner:
    owner = BehaviorPhaseOwner()
    owner.reset()
    return owner


def ensure_behavior_phase_owner(loader: Any) -> BehaviorPhaseOwner:
    owner = getattr(loader, "_behavior_phase_owner", None)
    if owner is None:
        owner = make_behavior_phase_owner()
        loader._behavior_phase_owner = owner
    return owner


def reset_behavior_phase_owner(loader: Any) -> BehaviorPhaseOwner:
    owner = make_behavior_phase_owner()
    loader._behavior_phase_owner = owner
    return owner
