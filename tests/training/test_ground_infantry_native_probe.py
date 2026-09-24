from __future__ import annotations

import json

import pytest

from python.rl.ground import (
    GroundInfantryNativeProbe,
    GroundInfantryNativeProbeError,
)


def test_native_ground_probe_reset_and_step_use_compiled_observation_surfaces() -> None:
    probe = GroundInfantryNativeProbe.from_fixture(max_steps=4)
    observation, info = probe.reset(seed=42)

    assert info["authority"] == "native_probe_only"
    assert info["production_boundary"] == "not_world_batch"
    assert set(observation) == {
        "position_local_enu_m",
        "velocity_local_enu_mps",
        "terrain",
        "field_semantics",
        "weapon_state",
        "state",
    }
    assert len(observation["terrain"]) == 5
    assert len(observation["field_semantics"]) == 7
    assert len(observation["weapon_state"]) == 8

    transition = probe.step([90.0, 0.5, 1.0, 0.0])
    assert transition.trace["authority"] == "native_probe_only"
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
