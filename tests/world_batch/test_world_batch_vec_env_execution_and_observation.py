from __future__ import annotations

import json
from typing import Any

import numpy as np
import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import torch  # noqa: E402

import python.rl.runtime.world_batch._observation_mixin as observation_mixin_module  # noqa: E402
import python.rl.runtime.world_batch.vec_env as vec_env_module  # noqa: E402
from python.rl.policy_algo.device_dict_rollout_buffer import DeviceDictRolloutBuffer  # noqa: E402
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv  # noqa: E402
from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
from tests.support._leader_env_runtime_test_support import CounterDictEnv  # noqa: E402
from tests.support._world_batch_vec_env_test_support import (  # noqa: E402
    _inline_vec_env_route_transition_scenario,
    _inline_vec_env_scenario,
)


def _write_scenario(tmp_path, scenario: dict, filename: str = "inline_scenario.json") -> str:
    scenario_path = tmp_path / filename
    scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
    return str(scenario_path)


def test_world_batch_vec_env_disables_execution_device_export_for_naval_profile(
    tmp_path,
    monkeypatch,
) -> None:
    scenario = _inline_vec_env_route_transition_scenario()
    scenario["tasking_profile"] = "naval"
    scenario["mission_command"]["tasking_profile"] = "naval"
    scenario["task_order"] = {
        "tasking_profile": "naval",
        "service_profile": "Navy",
        "task_name": "TASK_SCREEN",
    }
    scenario_path = _write_scenario(
        tmp_path,
        scenario,
        "inline_naval_route_transition_scenario.json",
    )

    observed_allow_device_export: list[bool] = []
    original_compute_batch = observation_mixin_module.compute_execution_observation_batch

    def _wrapped_compute_execution_observation_batch(**kwargs):
        observed_allow_device_export.append(bool(kwargs.get("allow_device_export")))
        return original_compute_batch(**kwargs)

    monkeypatch.setattr(
        observation_mixin_module,
        "compute_execution_observation_batch",
        _wrapped_compute_execution_observation_batch,
    )
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        action_mode="naval_station3",
        batch_observation_backend="compiled",
        policy_observation_torch_bridge=True,
    )
    try:
        vec_env.seed(123)
        vec_env.reset()
        assert observed_allow_device_export
        assert all(not value for value in observed_allow_device_export)
        assert vec_env._policy_execution_device_view is None
    finally:
        vec_env.close()


def test_world_batch_vec_env_reuses_cached_step_evaluation_for_reward_tail(tmp_path) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = _write_scenario(tmp_path, scenario)

    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
        execution_step_batch_prepare=True,
    )
    try:
        vec_env.seed(123)
        vec_env.reset()
        original_compute_full_step = vec_env.envs[0].loader.compute_full_step
        captured: dict[str, object] = {}

        def _wrapped_compute_full_step(*args, **kwargs):
            captured["step_evaluation"] = kwargs.get("step_evaluation")
            return original_compute_full_step(*args, **kwargs)

        vec_env.envs[0].loader.compute_full_step = _wrapped_compute_full_step
        vec_env.step(np.zeros((1, 17), dtype=np.float32))

        assert isinstance(captured.get("step_evaluation"), dict)
        assert captured["step_evaluation"] is vec_env.envs[0].loader._runtime_eval_cache.get(
            "step_evaluation"
        )
    finally:
        vec_env.close()


def test_world_batch_vec_env_routes_reward_and_info_through_named_helpers(
    tmp_path,
    monkeypatch,
) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = _write_scenario(tmp_path, scenario)
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=False,
        execution_step_runtime_mode="compiled",
    )
    try:
        vec_env.seed(123)
        vec_env.reset()
        original_compute = vec_env_module._compute_loader_step_outcome
        original_build = vec_env_module._build_loader_step_info
        observed: dict[str, Any] = {}

        def _wrapped_compute(loader, **kwargs):
            observed["compute_loader"] = loader
            return original_compute(loader, **kwargs)

        def _wrapped_build(loader, **kwargs):
            observed["build_loader"] = loader
            observed["build_entity_id"] = kwargs.get("entity_id")
            return original_build(loader, **kwargs)

        monkeypatch.setattr(vec_env_module, "_compute_loader_step_outcome", _wrapped_compute)
        monkeypatch.setattr(vec_env_module, "_build_loader_step_info", _wrapped_build)
        _obs, rewards, dones, infos = vec_env.step(np.zeros((1, 17), dtype=np.float32))

        assert observed.get("compute_loader") is vec_env.envs[0].loader
        assert observed.get("build_loader") is vec_env.envs[0].loader
        assert int(observed.get("build_entity_id", -1)) == int(vec_env.envs[0].agent_id)
        assert np.isfinite(float(rewards[0]))
        assert isinstance(infos[0], dict)
        assert bool(dones[0]) == bool(infos[0]["terminated"] or infos[0]["truncated"])
    finally:
        vec_env.close()


def test_world_batch_vec_env_applies_multi_timescale_action_controller(tmp_path) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 3
    scenario_path = _write_scenario(tmp_path, scenario)
    wrapper_kwargs = {
        "hold_steps": 4,
        "low_freq_indices": [4, 5, 6, 9, 12, 13, 14, 15, 16],
        "snap_binary_indices": [4, 9, 12, 13, 14, 15],
        "binary_hysteresis_indices": [4, 9, 12, 13, 14, 15],
        "binary_on_threshold": 0.75,
        "binary_off_threshold": 0.25,
        "binary_initial_values": {
            "4": 1.0,
            "9": 0.0,
            "12": 0.0,
            "13": 0.0,
            "14": 0.0,
            "15": 0.0,
        },
        "center_deadband_indices": [5, 6, 7, 8],
        "center_deadband_center": 0.5,
        "center_deadband_half_width": 0.18,
        "scripted_baseline_mode": "stable_flight",
        "scripted_residual_scale": 0.0,
        "action_rate_penalty_coef": 0.0002,
    }
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        include_visual=False,
        include_proprio=True,
        action_wrapper_kwargs=wrapper_kwargs,
    )
    try:
        vec_env.seed(123)
        vec_obs = vec_env.reset()
        for key in ("contacts", "rwr", "mission", "proprio"):
            assert np.asarray(vec_obs[key][0]).shape == tuple(vec_env.observation_space[key].shape)

        first_action = np.full((17,), 0.9, dtype=np.float32)
        vec_obs, rewards, dones, infos = vec_env.step(first_action.reshape(1, -1))
        assert not bool(dones[0])
        assert np.isfinite(float(rewards[0]))
        for key in ("contacts", "rwr", "mission", "proprio"):
            assert np.asarray(vec_obs[key][0]).shape == tuple(vec_env.observation_space[key].shape)
        first_effective = np.asarray(infos[0]["effective_action"], dtype=np.float32)
        assert first_effective.shape == (17,)
        assert float(first_effective[4]) == 1.0
        assert float(first_effective[9]) == 1.0

        second_action = np.full((17,), 0.1, dtype=np.float32)
        _obs, rewards, _dones, infos = vec_env.step(second_action.reshape(1, -1))
        second_effective = np.asarray(infos[0]["effective_action"], dtype=np.float32)
        assert np.isfinite(float(rewards[0]))
        held_indices = np.asarray(wrapper_kwargs["low_freq_indices"], dtype=np.int64)
        free_indices = np.asarray([0, 1, 2, 3, 7, 8, 10, 11], dtype=np.int64)
        assert np.allclose(second_effective[held_indices], first_effective[held_indices], atol=1.0e-6)
        assert np.allclose(second_effective[free_indices], second_action[free_indices], atol=1.0e-6)
    finally:
        vec_env.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is not available")
def test_world_batch_vec_env_cuda_bridge_uses_device_rollout_buffer(tmp_path) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = _write_scenario(tmp_path, scenario)
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        batch_observation_backend="gpu_host",
        policy_observation_torch_bridge=True,
    )
    try:
        model = AdaptiveKLPPO(
            "MultiInputPolicy",
            vec_env,
            n_steps=2,
            batch_size=4,
            n_epochs=1,
            learning_rate=3.0e-4,
            gamma=0.99,
            gae_lambda=0.95,
            ent_coef=0.0,
            vf_coef=0.5,
            max_grad_norm=0.5,
            device="cuda",
            verbose=0,
        )
        assert isinstance(model.rollout_buffer, DeviceDictRolloutBuffer)
        model.learn(total_timesteps=4)
        assert torch.is_tensor(model.rollout_buffer.observations["instruments"])
        assert model.rollout_buffer.observations["instruments"].device.type == "cuda"
    finally:
        vec_env.close()


@pytest.mark.parametrize(
    ("return_mode", "shares_memory"),
    (("view", True), ("copy", False)),
)
def test_world_batch_vec_env_observation_return_memory_mode(
    tmp_path,
    return_mode: str,
    shares_memory: bool,
) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = _write_scenario(tmp_path, scenario)
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=True,
        observation_return_mode=return_mode,
    )
    try:
        obs = vec_env.reset()
        for key in ("instruments", "proprio"):
            assert np.shares_memory(obs[key], vec_env.buf_obs[key]) is shares_memory

        obs, _rewards, _dones, _infos = vec_env.step(np.zeros((2, 17), dtype=np.float32))
        for key in ("instruments", "proprio"):
            assert np.shares_memory(obs[key], vec_env.buf_obs[key]) is shares_memory

        if return_mode == "view":
            _obs, _rewards, dones, infos = vec_env.step(
                np.zeros((2, 17), dtype=np.float32)
            )
            assert np.all(dones == np.asarray([True, True]))
            for key in ("instruments", "proprio"):
                assert not np.shares_memory(
                    infos[0]["terminal_observation"][key],
                    vec_env.buf_obs[key][0],
                )
    finally:
        vec_env.close()


def test_shared_memory_vec_env_rejects_action_batch_size_mismatch() -> None:
    vec_env = SharedMemorySubprocVecEnv(
        [lambda env_id=i: CounterDictEnv(env_id) for i in range(2)],
        start_method="forkserver",
    )
    try:
        vec_env.reset()
        for action_count in (1, 3):
            with pytest.raises(ValueError, match="action batch size mismatch"):
                vec_env.step_async(np.zeros((action_count, 1), dtype=np.float32))
            assert not vec_env.waiting
    finally:
        vec_env.close()


def test_shared_memory_vec_env_returns_shared_observation_views() -> None:
    vec_env = SharedMemorySubprocVecEnv(
        [lambda env_id=i: CounterDictEnv(env_id) for i in range(2)],
        start_method="forkserver",
    )
    try:
        obs = vec_env.reset()
        assert obs["vec"].shape == (2, 3)
        assert obs["mat"].shape == (2, 2, 2)
        assert np.shares_memory(obs["vec"], vec_env.buf_obs["vec"])
        assert np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32))

        obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
        assert np.allclose(rewards, np.asarray([1.0, 1.0], dtype=np.float32))
        assert np.all(dones == np.asarray([False, False]))
        assert np.allclose(obs["vec"][:, 1], np.asarray([1.0, 1.0], dtype=np.float32))
        assert infos[0]["count"] == 1

        obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
        assert np.all(dones == np.asarray([True, True]))
        assert np.allclose(rewards, np.asarray([2.0, 2.0], dtype=np.float32))
        assert np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32))
        assert infos[0]["terminal_observation"]["vec"][1] == 2.0
        assert infos[1]["terminal_observation"]["vec"][1] == 2.0
    finally:
        vec_env.close()


def test_world_batch_vec_env_reports_timing_breakdown(tmp_path) -> None:
    scenario = _inline_vec_env_scenario()
    scenario["meta"]["max_steps"] = 2
    scenario_path = _write_scenario(tmp_path, scenario)
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=2,
        include_visual=False,
        include_proprio=False,
        collect_step_timing=True,
    )
    try:
        vec_env.reset()
        reset_timing = vec_env.reset_infos[0]["timing"]
        assert "layout_build_ms" in reset_timing or "batch_setup_ms" in reset_timing
        assert "total_ms" in reset_timing

        _obs, _rewards, _dones, infos = vec_env.step(
            np.zeros((2, 17), dtype=np.float32)
        )
        assert "batch_step_ms" in infos[0]["timing"]
        assert "command_sync_ms" in infos[0]["timing"]
        assert "total_ms" in infos[0]["timing"]
    finally:
        vec_env.close()
