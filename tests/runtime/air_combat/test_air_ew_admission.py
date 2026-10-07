"""Canonical EW config -> training factory -> native action/state acceptance."""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest
from stable_baselines3 import PPO

from gym_envs.universal_env_parts import EW_STATE_FIELDS, make_action_space
from python.env_config import resolve_env_settings
from python.rl.policy_algo.policies import _normalize_hybrid_action_layout
from python.runtime_bootstrap import resolve_repo_path
from python.training import build_train_arg_parser
from python.training.vec_env_factory import (
    build_cooperative_world_batch_vec_env,
    build_execution_world_batch_vec_env,
)
from tests.runtime.multi_agent.test_cooperative_vec_env_tasking import (
    _cooperative_cruise_scenario,
)


_FIELD = {name: idx for idx, name in enumerate(EW_STATE_FIELDS)}
_SCENARIO = resolve_repo_path(
    "scenarios", "air_combat", "air_combat_1v1_headon_sensor_smoke_v1.json",
)


def _bootstrap(mode: str, scenario: str, *, include_ew_state: bool = True):
    config = {
        "env": {
            "action_mode": mode,
            "include_ew_state": include_ew_state,
            "include_proprio": True,
            "mission_obs_mode": "basic",
            "execution_step_runtime_mode": "compiled",
            "flight_shaping_backend": "compiled",
        },
        "runtime": {
            "world_batch_vec_env": True,
            "world_batch_threads": 1,
            "batch_observation_backend": "compiled",
            "policy_observation_torch_bridge": False,
        },
    }
    args = build_train_arg_parser().parse_args(["--scenario", scenario, "--action_mode", mode])
    return SimpleNamespace(
        train_config=config,
        runtime_cfg=config["runtime"],
        env_settings=resolve_env_settings(config, args),
        scenario_path=scenario,
        n_envs=1,
        training_seed=20261007,
    )


def _actions(rows: int, dim: int) -> np.ndarray:
    action = np.zeros((rows, dim), dtype=np.float32)
    action[:, 3] = 0.7
    return action


@pytest.mark.parametrize(("mode", "dim"), [("air_ew_hybrid_v1", 14), ("air_ew_hybrid_v2", 16)])
def test_canonical_ew_training_factory_reaches_native_resources_and_jammer(mode, dim):
    env = build_execution_world_batch_vec_env(_bootstrap(mode, _SCENARIO))
    assert env is not None
    try:
        assert env.action_space.shape == (dim,)
        base = make_action_space("air_combat_hybrid_v1")
        np.testing.assert_array_equal(env.action_space.low[:12], base.low)
        np.testing.assert_array_equal(env.action_space.high[:12], base.high)
        env.reset()
        neutral = _actions(1, dim)
        obs, _, _, _ = env.step(neutral)
        assert obs["proprio"].shape == (1, dim)
        before = obs["ew_state"].copy()
        assert before[0, _FIELD["chaff_remaining"]] > 0
        assert before[0, _FIELD["flare_remaining"]] > 0
        requested = neutral.copy()
        requested[:, 12:14] = 1.0
        if dim == 16:
            requested[:, 14:16] = (1.0, 1.6)
        for _ in range(20):
            obs, rewards, dones, _ = env.step(requested)
            assert np.isfinite(rewards).all()
            assert not dones.any()
            ew = obs["ew_state"]
            if np.all(ew[:, :2] < before[:, :2]):
                break
        np.testing.assert_array_equal(ew[:, :2], before[:, :2] - 1)
        inst = env.envs[0].last_inst
        assert ew[0, _FIELD["chaff_remaining"]] == inst.countermeasure_chaff_remaining
        assert ew[0, _FIELD["flare_remaining"]] == inst.countermeasure_flare_remaining
        assert bool(inst.jammer_transmitting) == (dim == 16)
        if dim == 16:
            assert inst.jammer_mode == 1
            assert ew[0, _FIELD["jammer_transmitting"]] == 1.0
        env.step(neutral)
        assert not env.envs[0].last_inst.jammer_transmitting
    finally:
        env.close()


@pytest.mark.parametrize(("mode", "dim"), [("air_ew_hybrid_v1", 14), ("air_ew_hybrid_v2", 16)])
def test_canonical_cooperative_factory_preserves_member_resource_isolation(tmp_path, mode, dim):
    scenario = tmp_path / "ew_cooperative_admission.json"
    scenario.write_text(json.dumps(_cooperative_cruise_scenario()), encoding="utf-8")
    env = build_cooperative_world_batch_vec_env(_bootstrap(mode, str(scenario)))
    try:
        assert env.action_space.shape == (dim,)
        env.reset()
        neutral = _actions(2, dim)
        obs, _, _, _ = env.step(neutral)
        before = obs["ew_state"][:, :2].copy()
        requested = neutral.copy()
        requested[0, 12] = 1.0
        requested[1, 13] = 1.0
        if dim == 16:
            requested[0, 14:16] = (1.0, 2.0)
        for _ in range(20):
            obs, _, dones, _ = env.step(requested)
            assert not dones.any()
            if obs["ew_state"][0, 0] < before[0, 0] and obs["ew_state"][1, 1] < before[1, 1]:
                break
        np.testing.assert_array_equal(obs["ew_state"][:, :2], before - np.eye(2))
        for index, slot in enumerate(env._slots):
            assert bool(slot.last_inst.jammer_transmitting) == (dim == 16 and index == 0)
        assert obs["proprio"].shape == (2, dim)
    finally:
        env.close()


@pytest.mark.parametrize(("mode", "dim"), [("air_ew_hybrid_v1", 14), ("air_ew_hybrid_v2", 16)])
def test_factory_built_ew_mode_runs_standard_ppo_and_rejects_12d_hybrid_consumer(mode, dim):
    env = build_execution_world_batch_vec_env(_bootstrap(mode, _SCENARIO))
    assert env is not None
    try:
        # This consumer supports a Box transport. The existing specialized
        # Bernoulli/categorical layout remains a separate 12D contract.
        with pytest.raises(ValueError, match=f"requires a 12D transport action space, got {dim}D"):
            _normalize_hybrid_action_layout("air_combat_hybrid_v1", env.action_space)
        with pytest.raises(ValueError, match="Unknown hybrid_action_spec"):
            _normalize_hybrid_action_layout(mode, env.action_space)
        model = PPO(
            "MultiInputPolicy", env, n_steps=2, batch_size=2, n_epochs=1,
            device="cpu", seed=31, policy_kwargs={"net_arch": {"pi": [16], "vf": [16]}},
        )
        model.learn(total_timesteps=2)
        actions, _ = model.predict(env.reset(), deterministic=True)
        assert actions.shape == (1, dim)
        assert np.isfinite(actions).all()
    finally:
        env.close()


@pytest.mark.parametrize("mode", ["air_ew_hybrid_v1", "air_ew_hybrid_v2"])
def test_ew_cli_override_wins_and_state_remains_opt_in(mode):
    bootstrap = _bootstrap(mode, _SCENARIO, include_ew_state=False)
    bootstrap.train_config["env"]["action_mode"] = "air_combat_hybrid_v1"
    args = build_train_arg_parser().parse_args(["--scenario", _SCENARIO, "--action_mode", mode])
    bootstrap.env_settings = resolve_env_settings(bootstrap.train_config, args)
    env = build_execution_world_batch_vec_env(bootstrap)
    assert env is not None
    try:
        assert env.action_mode == mode
        assert "ew_state" not in env.observation_space.spaces
    finally:
        env.close()
