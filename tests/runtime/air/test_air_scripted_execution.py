from __future__ import annotations

import numpy as np

from python.tasking_contracts.air_scripted_execution import (
    AIR_SCRIPTED_EXECUTION_MODEL_ID,
    AIR_SCRIPTED_MODEL_REGISTRY,
    AirScriptedExecutionModel,
)
from python.tasking_contracts.scripted_registry import ScriptedDecisionModel


def _observation(*, altitude_agl_m: float = 50.0, command_code: int = 1) -> dict:
    instruments = np.zeros((31,), dtype=np.float32)
    instruments[0] = 120.0
    instruments[2] = altitude_agl_m
    instruments[3] = altitude_agl_m
    instruments[9] = 90.0
    instruments[30] = 90.0
    return {
        "instruments": instruments,
        "mission": np.asarray([command_code, 90.0, 1000.0, 120.0], dtype=np.float32),
    }


def test_air_model_is_a_neutral_scripted_lifecycle_consumer() -> None:
    model = AirScriptedExecutionModel(action_dim=17, dt=0.05)
    assert isinstance(model, ScriptedDecisionModel)

    obs = _observation()
    model.reset(context={"observation": obs, "phase_name": "scramble"})
    action = model.decide(observation=obs, context={"phase_name": "scramble"}, dt=0.05)
    assert action.shape == (17,)
    assert np.isfinite(action).all()
    assert model.active_mode == "takeoff"


def test_air_model_switches_phase_controllers_without_kernel_or_rl_access() -> None:
    model = AirScriptedExecutionModel(action_dim=17, dt=0.05, transition_alt_agl_m=140.0)
    takeoff = _observation(altitude_agl_m=80.0, command_code=1)
    departure = _observation(altitude_agl_m=180.0, command_code=1)
    landing = _observation(altitude_agl_m=40.0, command_code=4)

    model.reset(context={"observation": takeoff, "phase_name": "scramble"})
    model.step(takeoff, phase_name="scramble")
    assert model.active_mode == "takeoff"
    model.step(departure, phase_name="departure")
    assert model.active_mode == "stable_flight"
    model.step(landing, phase_name="landing_final")
    assert model.active_mode == "landing_ils"


def test_air_model_is_registered_as_a_maintained_autopilot_model() -> None:
    entries = AIR_SCRIPTED_MODEL_REGISTRY.resolve(domain="air", role_id="autopilot_controller")
    assert [entry.model_id for entry in entries] == [AIR_SCRIPTED_EXECUTION_MODEL_ID]
    model = AIR_SCRIPTED_MODEL_REGISTRY.create(AIR_SCRIPTED_EXECUTION_MODEL_ID, action_dim=2, dt=0.05)
    assert isinstance(model, AirScriptedExecutionModel)
