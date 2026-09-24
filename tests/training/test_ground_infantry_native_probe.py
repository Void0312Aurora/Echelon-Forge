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
    assert float(env.action_space.high[3]) == pytest.approx(0.0)
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


def test_native_ground_gym_adapter_passes_gymnasium_checker() -> None:
    from gymnasium.utils.env_checker import check_env

    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(max_steps=2)
    )
    check_env(env, skip_render_check=True)


def test_native_ground_gym_adapter_reaches_fixed_waypoint() -> None:
    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(
            start_xy_m=(400.0, 100.0),
            goal_xy_m=(410.0, 100.0),
            max_speed_mps=10.0,
            time_step_s=1.0,
            max_steps=4,
        )
    )
    env.reset(seed=7)
    observation, _reward, terminated, truncated, info = env.step([90.0, 1.0, 0.0, 0.0])

    assert terminated is True
    assert truncated is False
    assert info["blocked"] is False
    assert float(observation["mission_state"][2]) <= 5.0
    assert info["termination_reason"] == "waypoint_reached"


def test_native_ground_gym_adapter_advances_fixed_direct_waypoint_sequence() -> None:
    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(
            start_xy_m=(400.0, 100.0),
            waypoints_xy_m=((406.0, 100.0), (412.0, 100.0)),
            max_speed_mps=10.0,
            time_step_s=1.0,
            max_steps=4,
        )
    )
    observation, info = env.reset(seed=7)

    assert info["waypoint_index"] == 0
    assert info["waypoint_count"] == 2
    assert tuple(observation["waypoint_state"]) == pytest.approx((0.0, 2.0))

    observation, _reward, terminated, truncated, info = env.step(
        [90.0, 1.0, 0.0, 0.0]
    )
    assert terminated is False
    assert truncated is False
    assert info["trace"]["waypoint_advanced"] is True
    assert info["trace"]["waypoint_index_before"] == 0
    assert info["trace"]["waypoint_index_after"] == 1
    assert float(observation["waypoint_state"][0]) == pytest.approx(1.0)

    observation, _reward, terminated, truncated, info = env.step(
        [90.0, 1.0, 0.0, 0.0]
    )
    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "waypoint_reached"
    assert info["trace"]["waypoint_advanced"] is False
    assert float(observation["waypoint_state"][0]) == pytest.approx(1.0)


def test_native_ground_gym_adapter_accepts_sb3_cpu_smoke_rollout() -> None:
    pytest.importorskip("stable_baselines3")
    from stable_baselines3 import PPO

    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(max_steps=4)
    )
    model = PPO(
        "MultiInputPolicy",
        env,
        n_steps=4,
        batch_size=4,
        learning_rate=1.0e-3,
        seed=42,
        device="cpu",
        verbose=0,
    )
    model.learn(total_timesteps=4)

    assert int(model.num_timesteps) == 4


def test_native_ground_gym_adapter_replay_is_seed_stable() -> None:
    actions = ([90.0, 0.5, 0.0, 0.0], [-90.0, 0.75, 2.0, 0.0])

    def run() -> str:
        env = GroundInfantryNativeEnv(
            GroundInfantryNativeProbe.from_fixture(max_steps=4)
        )
        observation, info = env.reset(seed=11)
        records: list[dict[str, object]] = [
            {
                "observation": {key: value.tolist() for key, value in observation.items()},
                "trace": info["trace"],
            }
        ]
        for action in actions:
            observation, reward, terminated, truncated, info = env.step(action)
            records.append(
                {
                    "observation": {
                        key: value.tolist() for key, value in observation.items()
                    },
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "trace": info["trace"],
                }
            )
        return json.dumps(records, sort_keys=True)

    assert run() == run()


def test_native_ground_gym_adapter_reports_max_step_truncation() -> None:
    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(max_steps=1)
    )
    env.reset(seed=13)
    _observation, _reward, terminated, truncated, info = env.step(
        [90.0, 0.0, 0.0, 0.0]
    )

    assert terminated is False
    assert truncated is True
    assert info["termination_reason"] is None
    assert info["truncation_reason"] == "max_steps"
    assert info["trace"]["truncation_reason"] == "max_steps"


def test_native_ground_gym_adapter_reports_blocked_step_truncation() -> None:
    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(
            start_xy_m=(0.0, 100.0),
            goal_xy_m=(100.0, 100.0),
            blocked_step_limit=1,
            max_steps=8,
        )
    )
    env.reset(seed=17)
    _observation, _reward, terminated, truncated, info = env.step(
        [90.0, 1.0, 0.0, 0.0]
    )

    assert terminated is False
    assert truncated is True
    assert info["blocked_reason"] == "water_transition_blocked"
    assert info["truncation_reason"] == "blocked_step_limit"


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
        "health_state",
        "command_state",
        "mission_state",
        "waypoint_state",
        "state",
    }
    assert len(observation["terrain"]) == 5
    assert len(observation["terrain_effects"]) == 1
    assert math.isfinite(observation["terrain_effects"][0])
    assert observation["terrain_effects"][0] >= 0.0
    assert len(observation["field_semantics"]) == 7
    assert len(observation["weapon_state"]) == 8
    assert tuple(observation["health_state"]) == (100.0, 100.0)
    assert len(observation["command_state"]) == 7
    assert observation["command_state"][0] == pytest.approx(0.0)
    assert len(observation["mission_state"]) == 3
    assert observation["mission_state"][2] > 0.0
    assert len(observation["waypoint_state"]) == 2
    assert tuple(observation["waypoint_state"]) == pytest.approx((0.0, 1.0))

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
