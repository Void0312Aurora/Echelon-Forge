"""Deterministic behavior snapshots for the maintained execution mainline."""

from __future__ import annotations

import json

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from gym_envs.universal_env_parts.common import gym as _gym  # noqa: E402
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
from tests.support._world_batch_vec_env_test_support import (  # noqa: E402
    _inline_vec_env_scenario,
)


_OBS_KEYS = ("instruments", "contacts", "rwr", "mission")
_OPTION_CELLS = (
    ("auto", "full", 17),
    ("compiled", "full", 17),
    ("compiled", "takeoff2", 2),
    ("compiled", "takeoff4", 4),
)
_EXPECTED_SHAPES = {
    "instruments": (1, 42),
    "contacts": (1, 10, 5),
    "rwr": (1, 4, 4),
    "mission": (1, 4),
}
_EXPECTED_RESET_DIGEST = {
    "instruments": (3882.3386, 2093.5623),
    "contacts": (0.0, 0.0),
    "rwr": (0.0, 0.0),
    "mission": (1472.0, 1216.7596),
}
_EXPECTED_STEPS = (
    {
        "done": False,
        "reward": 0.01,
        "reason": "running",
        "status": (0.0, 0.0, 0.0, 0.0),
        "terms": {
            "speed_reward": 0.0,
            "survival": 0.01,
            "total": 0.01,
            "tracked_total": 0.01,
            "untracked": 0.0,
        },
        "instruments": (5902.3701, 2444.0850),
    },
    {
        "done": True,
        "reward": 0.01,
        "reason": "timeout",
        "status": (0.0, 0.0, 0.0, 0.0),
        "terms": {
            "speed_reward": 0.0,
            "survival": 0.01,
            "total": 0.01,
            "tracked_total": 0.01,
            "untracked": 0.0,
        },
        "instruments": (3882.3386, 2093.5623),
    },
    {
        "done": False,
        "reward": 0.01,
        "reason": "running",
        "status": (0.0, 0.0, 0.0, 0.0),
        "terms": {
            "speed_reward": 0.0,
            "survival": 0.01,
            "total": 0.01,
            "tracked_total": 0.01,
            "untracked": 0.0,
        },
        "instruments": (5876.0557, 2444.4524),
    },
    {
        "done": True,
        "reward": -92.859558,
        "reason": "failfast_deep_stall",
        "status": (0.0, 0.0, 0.0, -1.0),
        "terms": {
            "failfast_penalty": -50.0,
            "speed_reward": 0.0,
            "stall_penalty": -42.86956,
            "survival": 0.01,
            "total": -92.85956,
            "tracked_total": -92.85956,
            "untracked": 0.0,
        },
        "instruments": (3882.3386, 2093.5623),
    },
)


requires_gym = pytest.mark.skipif(_gym is None, reason="WorldBatchVecEnv requires gymnasium")


def _observation_digest(observation) -> dict[str, tuple[float, float]]:
    return {
        key: (
            float(np.asarray(observation[key]).sum()),
            float(np.linalg.norm(np.asarray(observation[key]))),
        )
        for key in _OBS_KEYS
    }


def _assert_digest(
    observation,
    expected: dict[str, tuple[float, float]],
) -> None:
    for key in _OBS_KEYS:
        array = np.asarray(observation[key])
        assert array.shape == _EXPECTED_SHAPES[key]
        assert array.dtype == np.float32
    actual = _observation_digest(observation)
    for key, expected_values in expected.items():
        assert actual[key] == pytest.approx(expected_values, abs=2.0e-3)


@requires_gym
@pytest.mark.parametrize(
    ("backend", "action_mode", "action_dim"),
    _OPTION_CELLS,
    ids=lambda value: str(value).lower(),
)
def test_execution_mainline_behavior_snapshot(
    tmp_path,
    backend: str,
    action_mode: str,
    action_dim: int,
) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = tmp_path / f"execution_mainline_{backend}_{action_mode}.json"
    scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")

    env = WorldBatchVecEnv(
        scenario_path=str(scenario_path),
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode=action_mode,
        execution_step_runtime_mode="compiled",
        flight_shaping_backend=backend,
    )
    try:
        env.seed(123)
        _assert_digest(env.reset(), _EXPECTED_RESET_DIGEST)
        assert env.envs[0].loader._flight_shaping_backend_mode() == "compiled"

        action = np.zeros((1, action_dim), dtype=np.float32)
        for expected in _EXPECTED_STEPS:
            observation, rewards, dones, infos = env.step(action)
            info = infos[0]
            assert bool(dones[0]) is expected["done"]
            assert float(rewards[0]) == pytest.approx(expected["reward"], abs=1.0e-5)
            assert info.get("termination_reason") == expected["reason"]
            assert tuple(info["mission_status"]) == pytest.approx(expected["status"], abs=1.0e-6)

            reward_terms = dict(info.get("reward_terms", {}))
            assert set(reward_terms) == set(expected["terms"])
            for term, expected_value in expected["terms"].items():
                assert float(reward_terms[term]) == pytest.approx(expected_value, abs=1.0e-5)

            _assert_digest(
                observation,
                {
                    "instruments": expected["instruments"],
                    "contacts": (0.0, 0.0),
                    "rwr": (0.0, 0.0),
                    "mission": (1472.0, 1216.7596),
                },
            )
    finally:
        env.close()
