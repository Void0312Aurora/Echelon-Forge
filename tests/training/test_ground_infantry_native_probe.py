from __future__ import annotations

import json
import math

import pytest

from python.rl.ground import (
    GroundInfantryNativeEnv,
    GroundInfantryNativeProbe,
    GroundInfantryNativeProbeError,
)


def test_native_ground_gym_adapter_preserves_probe_authority_and_observation() -> None:
    env = GroundInfantryNativeEnv(GroundInfantryNativeProbe.from_fixture(max_steps=2))
    observation, info = env.reset(seed=42)

    assert info["authority"] == "native_probe_only"
    assert info["production_boundary"] == "not_world_batch"
    assert env.observation_space.contains(observation)

    next_observation, reward, terminated, truncated, step_info = env.step(
        [90.0, 0.5, 1.0, 0.0]
    )
    assert env.observation_space.contains(next_observation)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert step_info["authority"] == "native_probe_only"
    assert len(env.trace) == 2


def test_native_ground_probe_reset_and_step_use_compiled_observation_surfaces() -> None:
    probe = GroundInfantryNativeProbe.from_fixture(max_steps=4)
    observation, info = probe.reset(seed=42)

    assert info["authority"] == "native_probe_only"
    assert info["production_boundary"] == "not_world_batch"
    assert set(observation) == {
        "position_local_enu_m",
        "velocity_local_enu_mps",
        "terrain",
        "terrain_effects",
        "field_semantics",
        "weapon_state",
        "state",
    }
    assert len(observation["terrain"]) == 5
    assert len(observation["terrain_effects"]) == 1
    assert math.isfinite(observation["terrain_effects"][0])
    assert observation["terrain_effects"][0] >= 0.0
    assert len(observation["field_semantics"]) == 7
    assert len(observation["weapon_state"]) == 8

    transition = probe.step([90.0, 0.5, 1.0, 0.0])
    assert transition.trace["authority"] == "native_probe_only"
    assert len(transition.trace["transition_observation"]) == 7
    assert transition.trace["transition_observation"][0] == pytest.approx(1.0)
    assert transition.observation["state"][1] == pytest.approx(1.0)
    assert transition.observation["position_local_enu_m"] != observation[
        "position_local_enu_m"
    ]


def test_native_ground_probe_replay_is_seed_stable() -> None:
    actions = ([90.0, 0.5, 0.0, 0.0], [-90.0, 0.75, 2.0, 0.0])

    def run() -> list[dict]:
        probe = GroundInfantryNativeProbe.from_fixture(max_steps=4)
        probe.reset(seed=7)
        return [probe.step(action).trace for action in actions]

    assert json.dumps(run(), sort_keys=True) == json.dumps(run(), sort_keys=True)


def test_native_ground_probe_rejects_held_route_intent() -> None:
    probe = GroundInfantryNativeProbe.from_fixture()
    probe.reset(seed=1)
    with pytest.raises(GroundInfantryNativeProbeError, match="cannot represent route_intent"):
        probe.step([90.0, 1.0, 0.0, 3.0])


def test_native_ground_probe_reports_water_block_from_native_transition() -> None:
    probe = GroundInfantryNativeProbe.from_fixture(
        start_xy_m=(0.0, 100.0),
        goal_xy_m=(100.0, 100.0),
        max_steps=2,
    )
    probe.reset(seed=3)
    transition = probe.step([90.0, 1.0, 0.0, 0.0])

    assert transition.blocked is True
    assert transition.blocked_reason == "water_transition_blocked"
    assert transition.trace["transition_observation"][3] == pytest.approx(1.0)
