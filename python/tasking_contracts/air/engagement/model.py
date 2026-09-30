"""RL-independent scripted Air tactical engagement model.

The model composes the maintained phase-flight controller and adds only the
declared Air combat C2/ROE event fields.  A deterministic bounded tactical
planner evaluates the declared track geometry before the event policy emits a
release request.  It never reads a kernel, world truth, or a privileged target
geometry.  The action payload remains the existing 17-element full Air action
so the environment adapter owns transport and the existing fire gate owns
final release authority.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from python.mission_obs_taxonomy import mission_observation_dim

from ..execution.model import AirScriptedExecutionModel
from ..strategy.assessment import AirPostLaunchAssessment
from ..strategy.planning import AirEngagementPlanner, AirEngagementPlannerConfig
from ..strategy.contracts import (
    AirActionAdapter,
    AirTacticalActionIntent,
    AirAssessmentInput,
    AirPlanningContext,
    AirObservationAdapter,
    AirPostLaunchAssessor,
    AirTacticalPlanner,
)
from ..strategy.action import (
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AIR_FULL_ACTION_DIM,
    AirActionLayoutAdapter,
)
from ..strategy.observation import AirMissionContactObservationAdapter
from ..strategy.weapons import AirWeaponEnvelope, load_air_weapon_envelope


AIR_SCRIPTED_ENGAGEMENT_MODEL_ID = "air.engagement.c2_roe_scripted"
AIR_COMBAT_C2_ROE_V2 = "air_combat_c2_roe_v2"
_SUPPORTED_ACTION_DIMS = frozenset({AIR_FULL_ACTION_DIM, AIR_COMBAT_HYBRID_ACTION_DIM})


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
        planner_config: AirEngagementPlannerConfig | None = None,
        weapon_envelope: AirWeaponEnvelope | None = None,
        weapon_profile_path: str | Path | None = None,
        planner: AirTacticalPlanner | None = None,
        assessor: AirPostLaunchAssessor | None = None,
        observation_adapter: AirObservationAdapter | None = None,
        action_adapter: AirActionAdapter | None = None,
        weapon_station_id: int | None = 1,
    ) -> None:
        if int(action_dim) not in _SUPPORTED_ACTION_DIMS:
            raise ValueError(
                "Air scripted engagement requires a maintained Air combat action "
                f"dimension ({AIR_FULL_ACTION_DIM} full or {AIR_COMBAT_HYBRID_ACTION_DIM} hybrid)"
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
        self.weapon_station_id = weapon_station_id
        if weapon_envelope is not None and weapon_profile_path is not None:
            raise ValueError("provide weapon_envelope or weapon_profile_path, not both")
        if weapon_profile_path is not None:
            weapon_envelope = load_air_weapon_envelope(weapon_profile_path)
        if weapon_envelope is not None:
            if planner_config is not None and planner_config.weapon_envelope is not None:
                raise ValueError("planner_config already declares a weapon_envelope")
            planner_config = replace(
                planner_config or AirEngagementPlannerConfig(),
                weapon_envelope=weapon_envelope,
            )
        if planner is not None:
            if planner_config is not None or weapon_envelope is not None or weapon_profile_path is not None:
                raise ValueError("planner injection cannot be combined with planner or weapon configuration")
            if not isinstance(planner, AirTacticalPlanner):
                raise TypeError("planner must implement AirTacticalPlanner")
            self.planner = planner
        else:
            self.planner = AirEngagementPlanner(planner_config)
        if assessor is not None:
            if not isinstance(assessor, AirPostLaunchAssessor):
                raise TypeError("assessor must implement AirPostLaunchAssessor")
            self.assessment = assessor
        else:
            max_track_age_s = getattr(getattr(self.planner, "config", None), "max_track_age_s", 5.0)
            self.assessment = AirPostLaunchAssessment(max_track_age_s=max_track_age_s)
        if observation_adapter is not None:
            if not isinstance(observation_adapter, AirObservationAdapter):
                raise TypeError("observation_adapter must implement AirObservationAdapter")
            self.observation_adapter = observation_adapter
        else:
            self.observation_adapter = AirMissionContactObservationAdapter()
        if action_adapter is not None:
            if not isinstance(action_adapter, AirActionAdapter):
                raise TypeError("action_adapter must implement AirActionAdapter")
            self.action_adapter = action_adapter
        else:
            self.action_adapter = AirActionLayoutAdapter(action_dim=self.action_dim)
        self._closed = False
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
        self.planner.reset()
        self.assessment.reset()
        self.action_adapter.reset()
        self._closed = False
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

        tactical_observation = self.observation_adapter.decode(
            observation=observation,
            mission_obs_mode=self.mission_obs_mode,
        )
        values = tactical_observation.mission_values
        target_contact = bool(values["target_contact_present"] > 0.5)
        fire_window = bool(values["fire_mask_open"] > 0.5 and values["launch_window_open"] > 0.5)
        authorized = bool(values["authorization_to_fire"] > 0.5)
        pending_assessment = bool(values["pending_assessment"] > 0.5)
        budget_available = bool(values["shot_budget_remaining"] > 0.5)
        station_id = self._resolve_weapon_station_id(context)
        event_info = context.get("last_event_info") if isinstance(context, dict) else None
        assessment_input = self._assessment_input(
            event_info=event_info,
            pending_assessment=pending_assessment,
            target_contact_present=target_contact,
            own_missiles_in_flight_count=values["own_missiles_in_flight_count"],
            shot_budget_remaining=values["shot_budget_remaining"],
            target_track_age_s=values["target_track_age_s"],
            dt_s=dt,
        )
        assessment_report = self.assessment.assess(inputs=assessment_input)
        assessment_gate = bool(pending_assessment or assessment_report.blocks_fire)
        planning_context = AirPlanningContext(
            target_contact_present=target_contact,
            authorization_to_fire=authorized,
            fire_mask_open=bool(values["fire_mask_open"] > 0.5),
            launch_window_open=bool(values["launch_window_open"] > 0.5),
            quality_window_ready=bool(values["quality_window_ready"] > 0.5),
            pending_assessment=assessment_gate,
            shot_budget_remaining=values["shot_budget_remaining"],
            target_range_m=values["target_range_m"],
            target_track_age_s=values["target_track_age_s"],
            contact_bearing_deg=tactical_observation.contact_bearing_deg,
            contact_elevation_deg=tactical_observation.contact_elevation_deg,
            closing_speed_mps=tactical_observation.closing_speed_mps,
            observation_version=(
                str(context.get("observation_version", ""))
                if isinstance(context, Mapping)
                else ""
            ),
        )
        decision = self.planner.decide(context=planning_context)

        request_fire = bool(decision.fire_recommended)
        action_application = self.action_adapter.apply(
            action,
            intent=AirTacticalActionIntent(
                target_contact_present=target_contact,
                authorization_to_fire=authorized,
                shot_budget_available=budget_available,
                fire_window_open=fire_window,
                assessment_blocked=assessment_gate,
                request_fire=request_fire,
                station_id=station_id,
                guidance_roll=decision.guidance_roll,
                guidance_pitch=decision.guidance_pitch,
                guidance_throttle=decision.guidance_throttle,
            ),
        )
        action = np.asarray(action_application.action, dtype=np.float32).reshape(-1)
        if action.size != self.action_dim:
            raise RuntimeError(
                f"Air action adapter returned {action.size} values, expected {self.action_dim}"
            )
        tactical_plan = dict(decision.diagnostics)
        if not tactical_plan:
            tactical_plan = decision.as_dict()
        tactical_plan["decision_contract"] = decision.as_dict()
        self.last_decision_info = {
            "role": "air_tactical_engagement_controller",
            "mission_obs_mode": self.mission_obs_mode,
            "target_contact_present": target_contact,
            "fire_mask_open": bool(values["fire_mask_open"] > 0.5),
            "launch_window_open": bool(values["launch_window_open"] > 0.5),
            "authorization_to_fire": authorized,
            "pending_assessment": pending_assessment,
            "post_launch_assessment": assessment_report.as_dict(),
            "shot_budget_remaining": float(values["shot_budget_remaining"]),
            "weapon_station_id": station_id,
            "weapon_station_valid": station_id is not None,
            "fire_requested": bool(action_application.fire_pulse > 0.5),
            "tactical_plan": tactical_plan,
            "tactical_decision": decision.as_dict(),
        }
        return action

    def _resolve_weapon_station_id(self, context: Any) -> int | None:
        raw = self.weapon_station_id
        if isinstance(context, Mapping) and "weapon_station_id" in context:
            raw = context.get("weapon_station_id")
        if raw is None or isinstance(raw, bool):
            return None
        try:
            numeric = float(raw)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(numeric) or numeric != float(int(numeric)):
            return None
        station_id = int(numeric)
        return station_id if 0 <= station_id <= 7 else None

    def close(self) -> None:
        self.flight_model.close()
        self._closed = True

    @staticmethod
    def _assessment_input(
        *,
        event_info: Any,
        pending_assessment: bool,
        target_contact_present: bool,
        own_missiles_in_flight_count: float,
        shot_budget_remaining: float,
        target_track_age_s: float,
        dt_s: float,
    ) -> AirAssessmentInput:
        info = event_info if isinstance(event_info, Mapping) else {}
        return AirAssessmentInput(
            release_executed=bool(info.get("release_executed", False)),
            pending_assessment=pending_assessment,
            target_contact_present=target_contact_present,
            own_missiles_in_flight_count=own_missiles_in_flight_count,
            shot_budget_remaining=shot_budget_remaining,
            target_track_age_s=target_track_age_s,
            target_effect_observed=bool(info.get("target_effect_observed", False)),
            target_mission_killed=bool(info.get("target_mission_killed", False)),
            target_destroyed=bool(info.get("target_destroyed", False)),
            dt_s=dt_s,
        )


def make_air_scripted_engagement_model(**kwargs: Any) -> AirScriptedEngagementModel:
    return AirScriptedEngagementModel(**kwargs)


__all__ = [
    "AIR_COMBAT_C2_ROE_V2",
    "AIR_COMBAT_HYBRID_ACTION_DIM",
    "AIR_FULL_ACTION_DIM",
    "AIR_SCRIPTED_ENGAGEMENT_MODEL_ID",
    "AirScriptedEngagementModel",
    "make_air_scripted_engagement_model",
]
