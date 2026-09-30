from __future__ import annotations

import numpy as np
import pytest

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.tasking_contracts.air.engagement.model import (
    AIR_COMBAT_C2_ROE_V2,
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
    AirScriptedEngagementModel,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.common.decision_registry import DecisionModel
from python.tasking_contracts.air.strategy.action import AirActionLayoutAdapter
from python.tasking_contracts.air.strategy.contracts import (
    AirActionApplication,
    AirActionAdapter,
    AirObservationAdapter,
    AirTacticalActionIntent,
    AirTacticalObservation,
)
from python.tasking_contracts.air.strategy.observation import AirMissionContactObservationAdapter


def _observation(*, contact: bool, fire_window: bool, budget: float = 1.0, pending: bool = False) -> dict:
    instruments = np.zeros((31,), dtype=np.float32)
    instruments[0] = 120.0
    instruments[2] = 7000.0
    instruments[3] = 7000.0
    instruments[9] = 0.0
    mission = np.zeros((mission_observation_dim(AIR_COMBAT_C2_ROE_V2),), dtype=np.float32)
    values = {
        "authorization_to_fire": 1.0,
        "target_contact_present": 1.0 if contact else 0.0,
        "fire_mask_open": 1.0 if fire_window else 0.0,
        "launch_window_open": 1.0 if fire_window else 0.0,
        "quality_window_ready": 1.0 if fire_window else 0.0,
        "shot_budget_remaining": budget,
        "pending_assessment": 1.0 if pending else 0.0,
    }
    for name, value in values.items():
        mission[mission_observation_field_index(AIR_COMBAT_C2_ROE_V2, name)] = value
    return {"instruments": instruments, "mission": mission}


def test_engagement_model_uses_neutral_lifecycle_and_declared_observation_only() -> None:
    model = AirScriptedEngagementModel()
    assert isinstance(model, DecisionModel)
    obs = _observation(contact=False, fire_window=False)
    model.reset(context={"observation": obs, "phase_name": "stable_flight"})
    action = model.decide(
        observation=obs,
        context={"phase_name": "stable_flight", "mission_obs_mode": AIR_COMBAT_C2_ROE_V2},
        dt=0.05,
    )
    assert action.shape == (17,)
    assert np.isfinite(action).all()
    assert action[9] == 1.0
    assert action[13] == 0.0
    assert action[14] == 0.0
    model.close()


def test_engagement_model_emits_one_fire_pulse_and_respects_assessment() -> None:
    model = AirScriptedEngagementModel(weapon_station_id=1)
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    first = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    second = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    assert first[13] == 1.0
    assert first[14] == 1.0
    assert first[16] == pytest.approx(1.0 / 7.0)
    assert second[13] == 1.0
    assert second[14] == 0.0

    pending = _observation(contact=True, fire_window=True, budget=1.0, pending=True)
    blocked = model.decide(observation=pending, context={"phase_name": "stable_flight"}, dt=0.05)
    assert blocked[14] == 0.0
    assert model.last_decision_info["pending_assessment"] is True
    model.close()


def test_engagement_model_reports_conservative_post_launch_assessment() -> None:
    model = AirScriptedEngagementModel()
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    model.decide(
        observation=open_window,
        context={
            "phase_name": "stable_flight",
            "last_event_info": {"release_executed": True},
        },
        dt=0.05,
    )

    report = model.last_decision_info["post_launch_assessment"]
    assert report["state"] == "reattack_ready"
    assert report["outcome"] == "inconclusive"
    assert report["confidence"] == 0.0
    model.close()


def test_engagement_model_blocks_fire_after_terminal_effect_evidence() -> None:
    model = AirScriptedEngagementModel(weapon_station_id=1)
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    terminal = model.decide(
        observation=open_window,
        context={
            "phase_name": "stable_flight",
            "last_event_info": {
                "release_executed": True,
                "target_effect_observed": True,
            },
        },
        dt=0.05,
    )

    assert terminal[14] == 0.0
    assert model.last_decision_info["post_launch_assessment"]["state"] == "terminal_observed"
    assert model.last_decision_info["post_launch_assessment"]["blocks_fire"] is True
    model.close()


def test_engagement_model_maps_the_maintained_hybrid_action_layout() -> None:
    model = AirScriptedEngagementModel(action_dim=AIR_COMBAT_HYBRID_ACTION_DIM, weapon_station_id=1)
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    first = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    second = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    assert first.shape == (AIR_COMBAT_HYBRID_ACTION_DIM,)
    assert np.isfinite(first).all()
    assert first[6] == 1.0
    assert first[7] == 1.0
    assert first[8] == 1.0
    assert first[9] == 1.0
    assert first[11] == 1.0
    assert second[9] == 0.0
    model.close()


def test_engagement_model_fails_closed_for_invalid_weapon_station() -> None:
    model = AirScriptedEngagementModel(weapon_station_id=99)
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    action = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    assert action[13] == 0.0
    assert action[14] == 0.0
    assert action[16] == 0.0
    assert model.last_decision_info["weapon_station_valid"] is False
    assert model.last_decision_info["fire_rejected_reason"] == "invalid_weapon_station"
    model.close()


def test_engagement_model_accepts_context_station_override_and_fails_closed_when_missing() -> None:
    model = AirScriptedEngagementModel(weapon_station_id=1)
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    action = model.decide(
        observation=open_window,
        context={"phase_name": "stable_flight", "weapon_station_id": None},
        dt=0.05,
    )

    assert action[13] == 0.0
    assert action[14] == 0.0
    assert model.last_decision_info["weapon_station_valid"] is False
    model.close()


def test_engagement_model_is_registered_as_an_adapter_until_runtime_gate_closes() -> None:
    entries = AIR_SCRIPTED_MODEL_REGISTRY.resolve(
        domain="air",
        role_id="air_tactical_engagement_controller",
    )
    assert [entry.model_id for entry in entries] == [AIR_SCRIPTED_ENGAGEMENT_MODEL_ID]
    assert entries[0].status == "adapter"
    model = AIR_SCRIPTED_MODEL_REGISTRY.create(AIR_SCRIPTED_ENGAGEMENT_MODEL_ID)
    assert isinstance(model, AirScriptedEngagementModel)
    model.close()


def test_engagement_model_can_consume_a_maintained_weapon_profile() -> None:
    model = AirScriptedEngagementModel(
        weapon_profile_path="examples/config/database/weapons/air_to_air/aim_120c.json"
    )

    assert model.planner.config.weapon_envelope is not None
    assert model.planner.config.weapon_envelope.weapon_id == "AIM-120C-7"
    assert model.planner.config.weapon_envelope.pk_authority is False
    model.close()


def test_engagement_model_fails_closed_without_declared_weapon_station() -> None:
    model = AirScriptedEngagementModel()
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    action = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    assert action[13] == 0.0
    assert action[14] == 0.0
    assert action[16] == 0.0
    assert model.last_decision_info["weapon_station_valid"] is False
    assert model.last_decision_info["fire_rejected_reason"] == "invalid_weapon_station"
    model.close()


def test_engagement_model_rejects_non_c2_roe_mission_shapes() -> None:
    model = AirScriptedEngagementModel(weapon_station_id=1)
    obs = {"instruments": np.zeros((31,), dtype=np.float32), "mission": np.zeros((4,), dtype=np.float32)}
    model.reset(context={"observation": obs})
    with pytest.raises(ValueError, match="missing required fields"):
        model.decide(observation=obs, context={}, dt=0.05)
    model.close()


class _RecordingObservationAdapter:
    def __init__(self) -> None:
        self.delegate = AirMissionContactObservationAdapter()
        self.last: AirTacticalObservation | None = None

    def decode(self, *, observation: dict, mission_obs_mode: str) -> AirTacticalObservation:
        self.last = self.delegate.decode(
            observation=observation,
            mission_obs_mode=mission_obs_mode,
        )
        return self.last


class _RecordingActionAdapter:
    def __init__(self) -> None:
        self.delegate = AirActionLayoutAdapter(action_dim=17)
        self.last_intent: AirTacticalActionIntent | None = None

    def reset(self) -> None:
        self.delegate.reset()

    def apply(self, action: np.ndarray, *, intent: AirTacticalActionIntent) -> AirActionApplication:
        self.last_intent = intent
        return self.delegate.apply(action, intent=intent)


def test_engagement_model_injects_observation_and_action_adapters_with_default_parity() -> None:
    observation = _observation(contact=True, fire_window=True)
    observation_adapter = _RecordingObservationAdapter()
    action_adapter = _RecordingActionAdapter()
    model = AirScriptedEngagementModel(
        observation_adapter=observation_adapter,
        action_adapter=action_adapter,
        weapon_station_id=1,
    )
    model.reset(context={"observation": observation, "phase_name": "stable_flight"})
    action = model.decide(observation=observation, context={"phase_name": "stable_flight"}, dt=0.05)

    assert isinstance(observation_adapter, AirObservationAdapter)
    assert isinstance(action_adapter, AirActionAdapter)
    assert observation_adapter.last is not None
    assert action_adapter.last_intent is not None
    assert action_adapter.last_intent.request_fire is True
    assert action[14] == 1.0
    model.close()
