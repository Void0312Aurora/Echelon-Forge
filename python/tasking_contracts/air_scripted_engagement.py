"""RL-independent scripted Air tactical engagement model.

The model composes the maintained phase-flight controller and adds only the
declared Air combat C2/ROE event fields.  It never reads a kernel, world truth,
or a privileged target geometry.  The action payload remains the existing
17-element full Air action so the environment adapter owns transport and the
existing fire gate owns final release authority.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from python.mission_obs_taxonomy import (
    mission_observation_field_index,
    mission_observation_dim,
)

from .air_scripted_execution import AirScriptedExecutionModel


AIR_SCRIPTED_ENGAGEMENT_MODEL_ID = "air.engagement.c2_roe_scripted"
AIR_COMBAT_C2_ROE_V2 = "air_combat_c2_roe_v2"
AIR_FULL_ACTION_DIM = 17


class AirScriptedEngagementModel:
    """Compose flight control with a legal, single-shot tactical event policy.

    ``observation`` must contain the existing ``instruments`` and ``mission``
    arrays.  The mission array is interpreted only through the named
    ``air_combat_c2_roe_v2`` taxonomy.  The model emits a full Air action and
    lets the existing environment fire gate decide whether a requested release
    is accepted by the runtime.
    """

    def __init__(
        self,
        *,
        action_dim: int = AIR_FULL_ACTION_DIM,
        dt: float = 0.05,
        mission_obs_mode: str = AIR_COMBAT_C2_ROE_V2,
        transition_alt_agl_m: float = 140.0,
        runway_length_m: float = 0.0,
    ) -> None:
        if int(action_dim) != AIR_FULL_ACTION_DIM:
            raise ValueError(
                "Air scripted engagement currently requires the maintained "
                f"full action dimension ({AIR_FULL_ACTION_DIM})"
            )
        self.action_dim = int(action_dim)
        self.dt = float(dt) if float(dt) > 1.0e-6 else 0.05
        self.mission_obs_mode = str(mission_obs_mode).strip().lower() or AIR_COMBAT_C2_ROE_V2
        if mission_observation_dim(self.mission_obs_mode) <= 0:
            raise ValueError(f"unsupported Air tactical mission observation mode: {self.mission_obs_mode!r}")
        self.flight_model = AirScriptedExecutionModel(
            action_dim=self.action_dim,
            dt=self.dt,
            transition_alt_agl_m=transition_alt_agl_m,
            runway_length_m=runway_length_m,
        )
        self._closed = False
        self._fire_latched = False
        self._last_target_contact = False
        self.last_decision_info: dict[str, Any] = {}

    def reset(self, *, context: Any) -> None:
        observation = context.get("observation") if isinstance(context, dict) else None
        if not isinstance(observation, dict):
            raise TypeError("Air scripted engagement reset requires context['observation'] dict")
        requested_mode = context.get("mission_obs_mode") if isinstance(context, dict) else None
        if requested_mode:
            mode = str(requested_mode).strip().lower()
            if mission_observation_dim(mode) <= 0:
                raise ValueError(f"unsupported Air tactical mission observation mode: {mode!r}")
            self.mission_obs_mode = mode
        self.flight_model.reset(context={"observation": observation, "phase_name": context.get("phase_name", "")})
        self._closed = False
        self._fire_latched = False
        self._last_target_contact = False
        self.last_decision_info = {}

    def decide(self, *, observation: Any, context: Any, dt: float) -> np.ndarray:
        if self._closed:
            raise RuntimeError("Air scripted engagement model is closed")
        if not isinstance(observation, dict):
            raise TypeError("Air scripted engagement observation must be a dict")
        phase_name = str(context.get("phase_name", "")) if isinstance(context, dict) else ""
        mission_mode = str(context.get("mission_obs_mode", self.mission_obs_mode)) if isinstance(context, dict) else self.mission_obs_mode
        mission_mode = mission_mode.strip().lower() or self.mission_obs_mode
        if mission_mode != self.mission_obs_mode:
            if mission_observation_dim(mission_mode) <= 0:
                raise ValueError(f"unsupported Air tactical mission observation mode: {mission_mode!r}")
            self.mission_obs_mode = mission_mode

        action = np.asarray(
            self.flight_model.decide(observation=observation, context={"phase_name": phase_name}, dt=dt),
            dtype=np.float32,
        ).reshape(-1)
        if action.size != self.action_dim:
            raise RuntimeError(f"Air scripted flight model returned {action.size} values, expected {self.action_dim}")

        mission = np.asarray(observation.get("mission", []), dtype=np.float32).reshape(-1)
        values = self._mission_values(mission)
        target_contact = bool(values["target_contact_present"] > 0.5)
        fire_window = bool(values["fire_mask_open"] > 0.5 and values["launch_window_open"] > 0.5)
        authorized = bool(values["authorization_to_fire"] > 0.5)
        pending_assessment = bool(values["pending_assessment"] > 0.5)
        budget_available = bool(values["shot_budget_remaining"] > 0.5)

        # Existing full-action transport owns the field positions.  Tactical
        # bits are derived only from the declared mission packet.
        action[9] = 1.0  # radar active
        action[10] = 0.0  # centered scan azimuth
        action[11] = 0.0  # centered scan elevation
        action[12] = 1.0 if target_contact and not self._last_target_contact else 0.0  # TMS-up pulse
        action[13] = 1.0 if authorized and target_contact and budget_available else 0.0
        request_fire = bool(fire_window and authorized and target_contact and budget_available and not pending_assessment)
        action[14] = 1.0 if request_fire and not self._fire_latched else 0.0
        action[15] = 0.0
        action[16] = 0.0  # maintained first weapon slot; database/adapter owns mapping

        if not fire_window or pending_assessment or not budget_available:
            self._fire_latched = False
        elif request_fire:
            self._fire_latched = True

        self._last_target_contact = target_contact
        self.last_decision_info = {
            "role": "air_tactical_engagement_controller",
            "mission_obs_mode": self.mission_obs_mode,
            "target_contact_present": target_contact,
            "fire_mask_open": bool(values["fire_mask_open"] > 0.5),
            "launch_window_open": bool(values["launch_window_open"] > 0.5),
            "authorization_to_fire": authorized,
            "pending_assessment": pending_assessment,
            "shot_budget_remaining": float(values["shot_budget_remaining"]),
            "fire_requested": bool(action[14] > 0.5),
        }
        return action

    def close(self) -> None:
        self.flight_model.close()
        self._closed = True

    def _mission_values(self, mission: np.ndarray) -> dict[str, float]:
        required = {
            name: mission_observation_field_index(self.mission_obs_mode, name)
            for name in (
                "authorization_to_fire",
                "target_contact_present",
                "fire_mask_open",
                "launch_window_open",
                "shot_budget_remaining",
                "pending_assessment",
            )
        }
        missing = [name for name, idx in required.items() if idx >= mission.size]
        if missing:
            raise ValueError(
                f"Air tactical mission observation is missing required fields {missing!r} "
                f"for mode {self.mission_obs_mode!r}"
            )
        return {name: float(mission[idx]) for name, idx in required.items()}


def make_air_scripted_engagement_model(**kwargs: Any) -> AirScriptedEngagementModel:
    return AirScriptedEngagementModel(**kwargs)


__all__ = [
    "AIR_COMBAT_C2_ROE_V2",
    "AIR_FULL_ACTION_DIM",
    "AIR_SCRIPTED_ENGAGEMENT_MODEL_ID",
    "AirScriptedEngagementModel",
    "make_air_scripted_engagement_model",
]
