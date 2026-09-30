from __future__ import annotations

import numpy as np
from types import SimpleNamespace

from python.tasking_contracts.air.execution.model import (
    AIR_SCRIPTED_EXECUTION_MODEL_ID,
    AirScriptedExecutionModel,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.common.decision_registry import DecisionModel
from python.tasking_contracts.air.execution.landing import ScriptedLandingController
from gym_envs.leader_env_parts.scripted_exec import ScriptedExecutiveController


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
    assert isinstance(model, DecisionModel)

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


def test_landing_controller_aligns_localizer_range_with_runway_geometry() -> None:
    controller = ScriptedLandingController(action_dim=17, runway_length_m=3000.0)
    cross = controller._estimate_cross_track_m(0.334, 274.0)
    assert 45.0 < cross < 52.0


def test_leader_scripted_entry_uses_neutral_runtime_envelope() -> None:
    observation = _observation(altitude_agl_m=80.0, command_code=1)
    env = SimpleNamespace(
        action_space=SimpleNamespace(shape=(17,)),
        unwrapped=SimpleNamespace(
            agent_id="Blue_F16",
            steps=0,
            sim=SimpleNamespace(get_time_step=lambda: 0.05),
            loader=SimpleNamespace(mission_phase_name="scramble", ils_beacons=[]),
        ),
    )
    controller = ScriptedExecutiveController(env)
    controller.reset(observation, episode_seed=7)
    first = controller.predict(observation)
    env.unwrapped.steps = 1
    second = controller.predict(observation)

    assert first.shape == (17,)
    assert second.shape == (17,)
    assert controller.runtime_report is not None
    assert controller.runtime_report.domain == "air"
    assert controller.runtime_report.action_source == "decided"
    assert controller.runtime_report.decision_index == 2
    assert controller.runtime_report.observation_version == "reset:1:step:1"
    first_runtime_agent = controller._runtime_agent
    controller.reset(observation, episode_seed=8)
    assert controller._runtime_agent is first_runtime_agent
    assert controller.replay_identity == "Blue_F16:air.execution.phase_scripted:seed=8:reset=2"
    controller.close()
    assert first_runtime_agent.status == "closed"
