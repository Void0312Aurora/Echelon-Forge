"""Typed strategy contracts for the independent scripted Air line.

These DTOs are deliberately narrower than the Air observation and action
arrays. They are the boundary between adapters and replaceable decision
strategies; they do not import RL, native runtime, or world-truth surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from .weapons import AirWeaponEnvelope


def _finite(value: Any, *, name: str, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _nonnegative(value: Any, *, name: str) -> float:
    number = _finite(value, name=name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return number


@dataclass(frozen=True)
class AirPlanningContext:
    """Normalized, declared input for one tactical planning cycle."""

    target_contact_present: bool
    authorization_to_fire: bool
    fire_mask_open: bool
    launch_window_open: bool
    quality_window_ready: bool
    pending_assessment: bool
    shot_budget_remaining: float
    target_range_m: float = 0.0
    target_track_age_s: float = 0.0
    contact_bearing_deg: float = 0.0
    contact_elevation_deg: float = 0.0
    closing_speed_mps: float = 0.0
    weapon_envelope: AirWeaponEnvelope | None = None
    observation_version: str = ""

    def __post_init__(self) -> None:
        for name in (
            "shot_budget_remaining",
            "target_range_m",
            "target_track_age_s",
        ):
            _nonnegative(getattr(self, name), name=name)
        for name in (
            "contact_bearing_deg",
            "contact_elevation_deg",
            "closing_speed_mps",
        ):
            _finite(getattr(self, name), name=name)
        object.__setattr__(self, "observation_version", str(self.observation_version).strip())


@dataclass(frozen=True)
class AirTacticalDecision:
    """Stable tactical result consumed by the action adapter and fire gate."""

    mode: str
    selected_candidate: str
    fire_recommended: bool
    guidance_roll: float = 0.0
    guidance_pitch: float = 0.0
    guidance_throttle: float = 0.0
    reason_codes: tuple[str, ...] = ()
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        mode = str(self.mode).strip()
        candidate = str(self.selected_candidate).strip()
        if not mode or not candidate:
            raise ValueError("mode and selected_candidate must be non-empty")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "selected_candidate", candidate)
        guidance = {}
        for name in ("guidance_roll", "guidance_pitch", "guidance_throttle"):
            value = _finite(getattr(self, name), name=name)
            if abs(value) > 1.0:
                raise ValueError(f"{name} must be within [-1, 1]")
            guidance[name] = value
            object.__setattr__(self, name, value)
        object.__setattr__(self, "reason_codes", tuple(str(code) for code in self.reason_codes))
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "selected_candidate": self.selected_candidate,
            "fire_recommended": bool(self.fire_recommended),
            "guidance_roll": self.guidance_roll,
            "guidance_pitch": self.guidance_pitch,
            "guidance_throttle": self.guidance_throttle,
            "reason_codes": list(self.reason_codes),
            "diagnostics": dict(self.diagnostics),
        }


@dataclass(frozen=True)
class AirAssessmentInput:
    """Typed evidence and declared state for one post-launch assessment."""

    release_executed: bool
    pending_assessment: bool
    target_contact_present: bool
    own_missiles_in_flight_count: float = 0.0
    shot_budget_remaining: float = 0.0
    target_track_age_s: float = 0.0
    target_effect_observed: bool = False
    target_mission_killed: bool = False
    target_destroyed: bool = False
    dt_s: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "own_missiles_in_flight_count",
            "shot_budget_remaining",
            "target_track_age_s",
            "dt_s",
        ):
            _nonnegative(getattr(self, name), name=name)


@dataclass(frozen=True)
class AirTacticalObservation:
    """Normalized Air observation packet consumed by the tactical planner."""

    mission_values: Mapping[str, float]
    mission_obs_mode: str
    contact_bearing_deg: float = 0.0
    contact_elevation_deg: float = 0.0
    closing_speed_mps: float = 0.0

    def __post_init__(self) -> None:
        values = {
            str(name): _finite(value, name=str(name))
            for name, value in dict(self.mission_values).items()
        }
        object.__setattr__(self, "mission_values", MappingProxyType(values))
        object.__setattr__(self, "mission_obs_mode", str(self.mission_obs_mode).strip())
        for name in ("contact_bearing_deg", "contact_elevation_deg", "closing_speed_mps"):
            object.__setattr__(self, name, _finite(getattr(self, name), name=name))


@dataclass(frozen=True)
class AirTacticalActionIntent:
    """Declared tactical intent presented to the maintained action layout."""

    target_contact_present: bool
    authorization_to_fire: bool
    shot_budget_available: bool
    fire_window_open: bool
    assessment_blocked: bool
    request_fire: bool
    station_id: int | None = 1
    guidance_roll: float = 0.0
    guidance_pitch: float = 0.0
    guidance_throttle: float = 0.0

    def __post_init__(self) -> None:
        if self.station_id is not None:
            station_id = int(self.station_id)
            if station_id < 0 or station_id > 7:
                raise ValueError("station_id must be within the maintained range [0, 7]")
            object.__setattr__(self, "station_id", station_id)
        for name in ("guidance_roll", "guidance_pitch", "guidance_throttle"):
            value = _finite(getattr(self, name), name=name)
            if abs(value) > 1.0:
                raise ValueError(f"{name} must be within [-1, 1]")
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class AirActionApplication:
    """Action adapter result with transport facts used in the runtime report."""

    action: Any
    tms_pulse: float
    master_arm: float
    fire_pulse: float

    def __post_init__(self) -> None:
        for name in ("tms_pulse", "master_arm", "fire_pulse"):
            value = _finite(getattr(self, name), name=name)
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be within [0, 1]")
            object.__setattr__(self, name, value)


@runtime_checkable
class AirTacticalPlanner(Protocol):
    """Protocol for a replaceable tactical planner implementation."""

    def reset(self) -> None:
        ...

    def decide(self, *, context: AirPlanningContext) -> AirTacticalDecision:
        ...


@runtime_checkable
class AirPostLaunchAssessor(Protocol):
    """Protocol for a replaceable post-launch assessment implementation."""

    def reset(self) -> None:
        ...

    def assess(self, *, inputs: AirAssessmentInput) -> Any:
        ...


@runtime_checkable
class AirObservationAdapter(Protocol):
    """Protocol for mission/contact decoding owned by the Air boundary."""

    def decode(self, *, observation: Mapping[str, Any], mission_obs_mode: str) -> AirTacticalObservation:
        ...


@runtime_checkable
class AirActionAdapter(Protocol):
    """Protocol for versioned Air action-layout and pulse transport."""

    def reset(self) -> None:
        ...

    def apply(
        self,
        action: Any,
        *,
        intent: AirTacticalActionIntent,
    ) -> AirActionApplication:
        ...


__all__ = [
    "AirAssessmentInput",
    "AirActionApplication",
    "AirActionAdapter",
    "AirPlanningContext",
    "AirObservationAdapter",
    "AirPostLaunchAssessor",
    "AirTacticalActionIntent",
    "AirTacticalDecision",
    "AirTacticalObservation",
    "AirTacticalPlanner",
]
