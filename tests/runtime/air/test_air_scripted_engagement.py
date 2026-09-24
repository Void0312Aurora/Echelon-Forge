from __future__ import annotations

import numpy as np
import pytest

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.tasking_contracts.air_scripted_engagement import (
    AIR_COMBAT_C2_ROE_V2,
    AIR_SCRIPTED_ENGAGEMENT_MODEL_ID,
    AirScriptedEngagementModel,
)
from python.tasking_contracts.air_scripted_execution import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.scripted_registry import ScriptedDecisionModel


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
        "shot_budget_remaining": budget,
        "pending_assessment": 1.0 if pending else 0.0,
    }
    for name, value in values.items():
        mission[mission_observation_field_index(AIR_COMBAT_C2_ROE_V2, name)] = value
    return {"instruments": instruments, "mission": mission}


def test_engagement_model_uses_neutral_lifecycle_and_declared_observation_only() -> None:
    model = AirScriptedEngagementModel()
    assert isinstance(model, ScriptedDecisionModel)
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
    model = AirScriptedEngagementModel()
    hold = _observation(contact=True, fire_window=False)
    open_window = _observation(contact=True, fire_window=True)
    model.reset(context={"observation": hold, "phase_name": "stable_flight"})
    first = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    second = model.decide(observation=open_window, context={"phase_name": "stable_flight"}, dt=0.05)
    assert first[13] == 1.0
    assert first[14] == 1.0
    assert second[13] == 1.0
    assert second[14] == 0.0

    pending = _observation(contact=True, fire_window=True, budget=1.0, pending=True)
    blocked = model.decide(observation=pending, context={"phase_name": "stable_flight"}, dt=0.05)
    assert blocked[14] == 0.0
    assert model.last_decision_info["pending_assessment"] is True
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


def test_engagement_model_rejects_non_c2_roe_mission_shapes() -> None:
    model = AirScriptedEngagementModel()
    obs = {"instruments": np.zeros((31,), dtype=np.float32), "mission": np.zeros((4,), dtype=np.float32)}
    model.reset(context={"observation": obs})
    with pytest.raises(ValueError, match="missing required fields"):
        model.decide(observation=obs, context={}, dt=0.05)
    model.close()
