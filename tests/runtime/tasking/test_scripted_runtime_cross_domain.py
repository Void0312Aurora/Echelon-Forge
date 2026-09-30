from __future__ import annotations

import numpy as np

from python.tasking_contracts.air_scripted_execution import (
    AIR_SCRIPTED_EXECUTION_MODEL_ID,
    AIR_SCRIPTED_MODEL_REGISTRY,
)
from python.tasking_contracts.naval_scripted_execution import (
    NAVAL_SCRIPTED_MODEL_REGISTRY,
    NAVAL_STATION_HOLD_MODEL_ID,
)
from python.tasking_contracts.scripted_runtime import (
    SCRIPTED_RUNTIME_ACTION_DECIDED,
    SCRIPTED_RUNTIME_ACTION_HELD,
    ScriptedRuntimeAgent,
    ScriptedRuntimeAgentSpec,
    ScriptedRuntimeRoster,
)


def _air_observation() -> dict[str, np.ndarray]:
    instruments = np.zeros((31,), dtype=np.float32)
    instruments[0] = 120.0
    instruments[2] = 50.0
    instruments[3] = 50.0
    instruments[9] = 90.0
    instruments[30] = 90.0
    return {
        "instruments": instruments,
        "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
    }


def test_scripted_runtime_spec_constructor_covers_all_maintained_domains() -> None:
    specs = (
        ScriptedRuntimeAgentSpec(
            agent_id="air:lead",
            model_id=AIR_SCRIPTED_EXECUTION_MODEL_ID,
            domain="air",
            role_id="autopilot_controller",
        ),
        ScriptedRuntimeAgentSpec(
            agent_id="naval:screen",
            model_id=NAVAL_STATION_HOLD_MODEL_ID,
            domain="naval",
            role_id="naval_warfare_commander",
        ),
        ScriptedRuntimeAgentSpec(
            agent_id="joint:director",
            model_id="joint.scripted_coordination.v1",
            domain="joint",
            role_id="joint_coordination_director",
        ),
    )

    assert tuple(spec.domain for spec in specs) == ("air", "naval", "joint")


def test_air_and_naval_models_share_one_runtime_roster_envelope() -> None:
    air_agent_id = "air:lead"
    naval_agent_id = "naval:screen"
    air_model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="air",
        role_id="autopilot_controller",
        model_id=AIR_SCRIPTED_EXECUTION_MODEL_ID,
        action_dim=17,
        dt=0.05,
    )
    naval_model = NAVAL_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="naval",
        role_id="naval_warfare_commander",
        model_id=NAVAL_STATION_HOLD_MODEL_ID,
        action_dim=3,
    )
    roster = ScriptedRuntimeRoster(
        (
            ScriptedRuntimeAgent(
                ScriptedRuntimeAgentSpec(
                    agent_id=air_agent_id,
                    model_id=AIR_SCRIPTED_EXECUTION_MODEL_ID,
                    domain="air",
                    role_id="autopilot_controller",
                    decision_period_s=1.0,
                    authority_scope="platform_control",
                ),
                air_model,
            ),
            ScriptedRuntimeAgent(
                ScriptedRuntimeAgentSpec(
                    agent_id=naval_agent_id,
                    model_id=NAVAL_STATION_HOLD_MODEL_ID,
                    domain="naval",
                    role_id="naval_warfare_commander",
                    decision_period_s=1.0,
                    authority_scope="naval_station_command",
                ),
                naval_model,
            ),
        )
    )
    try:
        roster.reset(
            context_by_agent={
                air_agent_id: {"observation": _air_observation(), "phase_name": "scramble"},
                naval_agent_id: {"scenario": "n4"},
            },
            episode_seed=7,
        )
        first = roster.step(
            observations={air_agent_id: _air_observation(), naval_agent_id: None},
            clock_s=0.0,
            observation_versions={air_agent_id: "air:0", naval_agent_id: "naval:0"},
        )
        second = roster.step(
            observations={air_agent_id: _air_observation(), naval_agent_id: None},
            clock_s=0.1,
            observation_versions={air_agent_id: "air:1", naval_agent_id: "naval:1"},
        )
        assert list(first) == [air_agent_id, naval_agent_id]
        assert first[air_agent_id].report.domain == "air"
        assert first[naval_agent_id].report.domain == "naval"
        assert first[air_agent_id].report.action_source == SCRIPTED_RUNTIME_ACTION_DECIDED
        assert first[naval_agent_id].report.action_source == SCRIPTED_RUNTIME_ACTION_DECIDED
        assert second[air_agent_id].report.action_source == SCRIPTED_RUNTIME_ACTION_HELD
        assert second[naval_agent_id].report.action_source == SCRIPTED_RUNTIME_ACTION_HELD
        assert first[air_agent_id].action.shape == (17,)
        assert first[naval_agent_id].action.shape == (3,)
        assert roster.agent(air_agent_id).replay_identity.endswith("seed=7:reset=1")
        assert roster.agent(naval_agent_id).replay_identity.endswith("seed=7:reset=1")
    finally:
        roster.close()
