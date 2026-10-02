"""Simulation-side composition of the neutral scripted Air engagement model."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

import numpy as np

from python.tasking_contracts.air.engagement.model import (
    AIR_COMBAT_C2_ROE_V2,
    AirScriptedEngagementModel,
)

from .action import build_pilot_action
from .observation import build_air_scripted_observation


@dataclass(frozen=True)
class AirEngagementFacts:
    """Declared Air C2/track facts admitted to one tactical decision."""

    authorization_to_fire: bool
    target_contact_present: bool
    fire_mask_open: bool
    launch_window_open: bool
    quality_window_ready: bool
    shot_budget_remaining: float
    pending_assessment: bool = False
    own_missiles_in_flight_count: float = 0.0
    target_range_m: float = 0.0
    target_track_age_s: float = 0.0
    assigned_target_id: int = 0
    assigned_target_track_id: int = 0
    assigned_target_source_id: int = 0
    engagement_authority_holder_id: int = 0
    engagement_authority_grantor_id: int = 0
    roe_state: int = 0

    def __post_init__(self) -> None:
        for name in (
            "shot_budget_remaining",
            "own_missiles_in_flight_count",
            "target_range_m",
            "target_track_age_s",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"Air engagement fact {name} must be finite and non-negative")
        for name in (
            "assigned_target_id",
            "assigned_target_track_id",
            "assigned_target_source_id",
            "engagement_authority_holder_id",
            "engagement_authority_grantor_id",
            "roe_state",
        ):
            value = getattr(self, name)
            try:
                numeric = int(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Air engagement fact {name} must be a non-negative integer") from exc
            if numeric != value or numeric < 0:
                raise ValueError(f"Air engagement fact {name} must be a non-negative integer")
        if self.target_contact_present and self.assigned_target_id <= 0:
            raise ValueError("Air engagement fact assigned_target_id is required when a target contact is present")
        if self.target_contact_present and self.assigned_target_track_id <= 0:
            raise ValueError(
                "Air engagement fact assigned_target_track_id is required when a target contact is present"
            )
        if self.authorization_to_fire and self.engagement_authority_holder_id <= 0:
            raise ValueError(
                "Air engagement fact engagement_authority_holder_id is required when fire is authorized"
            )

    def as_mapping(self) -> dict[str, float | int]:
        return {
            "authorization_to_fire": float(self.authorization_to_fire),
            "target_contact_present": float(self.target_contact_present),
            "fire_mask_open": float(self.fire_mask_open),
            "launch_window_open": float(self.launch_window_open),
            "quality_window_ready": float(self.quality_window_ready),
            "shot_budget_remaining": float(self.shot_budget_remaining),
            "pending_assessment": float(self.pending_assessment),
            "own_missiles_in_flight_count": float(self.own_missiles_in_flight_count),
            "target_range_m": float(self.target_range_m),
            "target_track_age_s": float(self.target_track_age_s),
            "assigned_target_id": int(self.assigned_target_id),
            "assigned_target_track_id": int(self.assigned_target_track_id),
            "assigned_target_source_id": int(self.assigned_target_source_id),
            "engagement_authority_holder_id": int(self.engagement_authority_holder_id),
            "engagement_authority_grantor_id": int(self.engagement_authority_grantor_id),
            "roe_state": int(self.roe_state),
        }


@dataclass(frozen=True)
class AirEngagementDecision:
    """Neutral action plus its native simulation transport projection."""

    action: np.ndarray
    pilot_action: Any
    runtime_info: Mapping[str, Any]


class AirScriptedEngagementController:
    """Adapt native Air state to the replaceable scripted tactical model."""

    def __init__(
        self,
        *,
        model: AirScriptedEngagementModel | None = None,
        dt: float = 0.05,
        mission_obs_mode: str = AIR_COMBAT_C2_ROE_V2,
        weapon_station_id: int | None = None,
    ) -> None:
        self.mission_obs_mode = str(mission_obs_mode).strip().lower() or AIR_COMBAT_C2_ROE_V2
        self.model = model or AirScriptedEngagementModel(
            action_dim=17,
            dt=dt,
            mission_obs_mode=self.mission_obs_mode,
            weapon_station_id=weapon_station_id,
        )
        self._closed = False

    def reset(
        self,
        *,
        observation: Any,
        instruments: Any,
        command: Any,
        facts: AirEngagementFacts,
        phase_name: str = "stable_flight",
    ) -> None:
        scripted_observation = self._observation(
            observation=observation,
            instruments=instruments,
            command=command,
            facts=facts,
        )
        self.model.reset(
            context={
                "observation": scripted_observation,
                "phase_name": phase_name,
                "mission_obs_mode": self.mission_obs_mode,
            }
        )
        self._closed = False

    def decide(
        self,
        *,
        observation: Any,
        instruments: Any,
        command: Any,
        facts: AirEngagementFacts,
        phase_name: str = "stable_flight",
        dt: float | None = None,
        last_event_info: Mapping[str, Any] | None = None,
    ) -> AirEngagementDecision:
        if self._closed:
            raise RuntimeError("Air scripted engagement controller is closed")
        scripted_observation = self._observation(
            observation=observation,
            instruments=instruments,
            command=command,
            facts=facts,
        )
        action = np.asarray(
            self.model.decide(
                observation=scripted_observation,
                context={
                    "phase_name": phase_name,
                    "mission_obs_mode": self.mission_obs_mode,
                    "last_event_info": dict(last_event_info or {}),
                },
                dt=float(dt if dt is not None else self.model.dt),
            ),
            dtype=np.float32,
        ).reshape(-1)
        return AirEngagementDecision(
            action=action,
            pilot_action=build_pilot_action(
                action,
                action_mode="full",
                instrument_state=instruments,
            ),
            runtime_info=dict(self.model.last_decision_info),
        )

    def close(self) -> None:
        self.model.close()
        self._closed = True

    def _observation(self, *, observation: Any, instruments: Any, command: Any, facts: AirEngagementFacts) -> dict[str, np.ndarray]:
        if not isinstance(facts, AirEngagementFacts):
            raise TypeError("Air scripted engagement facts must be AirEngagementFacts")
        return build_air_scripted_observation(
            observation,
            instruments,
            command,
            mode=self.mission_obs_mode,
            mission_facts=facts.as_mapping(),
        )


__all__ = [
    "AIR_COMBAT_C2_ROE_V2",
    "AirEngagementDecision",
    "AirEngagementFacts",
    "AirScriptedEngagementController",
]
