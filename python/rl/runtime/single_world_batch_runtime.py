from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import time

import ef_py
import numpy as np

try:
    import gymnasium as gym
except ModuleNotFoundError:  # pragma: no cover
    gym = None

from python.rl.runtime.execution_runtime import ExecutionRuntimeAdapter, WrappedExecutionRuntimeAdapter
from python.rl.control.wrappers import MultiTimescaleActionWrapper
from gym_envs.universal_env import build_pilot_action, build_step_info, normalize_action
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv


@dataclass
class _SingleWorldView:
    runtime: "SingleWorldBatchExecutionRuntimeHandle"

    @property
    def loader(self):
        return self.runtime.world_vec._handles[0].loader

    @property
    def sim(self):
        return self.runtime.world_vec.batch_runtime.world(0)

    @property
    def agent_id(self):
        return self.runtime.world_vec._handles[0].agent_id

    @property
    def steps(self):
        return self.runtime.world_vec._handles[0].steps


class SingleWorldBatchExecutionRuntimeHandle(ExecutionRuntimeAdapter, gym.Env if gym is not None else object):
    metadata = {"render_modes": []}

    def __init__(self, world_vec: WorldBatchVecEnv):
        if gym is not None:
            super().__init__()
        self.world_vec = world_vec
        self._unwrapped = _SingleWorldView(self)
        self.render_mode = None

    @property
    def action_space(self):
        return self.world_vec.action_space

    @property
    def observation_space(self):
        return self.world_vec.observation_space

    @property
    def policy_env(self):
        return self

    @property
    def unwrapped(self):
        return self._unwrapped

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        _ = options
        return self.world_vec._reset_single_world(0, seed=seed)

    def step(self, action):
        env_idx = 0
        collect_timing = bool(getattr(self.world_vec, "collect_step_timing", False))
        total_t0 = time.perf_counter() if collect_timing else 0.0
        handle = self.world_vec._handles[env_idx]
        if handle.agent_id is None:
            raise RuntimeError("world 0 is not initialized; call reset() before step().")

        command_sync_ms = 0.0
        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.world_vec._sync_command_chain_batch([env_idx])
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        _, refs = self.world_vec._build_refs([env_idx])
        prepare_t0 = time.perf_counter() if collect_timing else 0.0
        inst_now = None
        if self.world_vec.action_mode != "full":
            inst_now = self.world_vec.batch_runtime.get_instrument_states_batch(refs)[0]
        normalized_action = normalize_action(
            action,
            action_space=self.world_vec.action_space,
            action_mode=self.world_vec.action_mode,
        )
        handle.last_action = normalized_action.astype(np.float32, copy=True)
        assignment = ef_py.WorldPilotActionAssignment()
        assignment.world_index = int(env_idx)
        assignment.entity_id = int(handle.agent_id)
        assignment.action = build_pilot_action(
            normalized_action,
            action_mode=self.world_vec.action_mode,
            inst_now=inst_now,
        )
        action_prepare_ms = (time.perf_counter() - prepare_t0) * 1000.0 if collect_timing else 0.0

        step_t0 = time.perf_counter() if collect_timing else 0.0
        self.world_vec.batch_runtime.set_pilot_actions_batch([assignment])
        self.world_vec.batch_runtime.step_worlds([env_idx])
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if collect_timing else 0.0

        read_t0 = time.perf_counter() if collect_timing else 0.0
        truth = self.world_vec.batch_runtime.get_agent_observations_batch(refs)[0]
        inst = self.world_vec.batch_runtime.get_instrument_states_batch(refs)[0]
        state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if collect_timing else 0.0

        behavior_t0 = time.perf_counter() if collect_timing else 0.0
        handle.steps += 1
        handle.last_truth = truth
        handle.last_inst = inst
        sim_time = float(handle.steps) * float(self.world_vec.batch_runtime.world(env_idx).get_time_step())
        handle.loader.update_behaviors(
            sim_time,
            truth=truth,
            inst=inst,
            sync_to_kernel=False,
        )
        behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if collect_timing else 0.0

        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.world_vec._sync_command_chain_batch([env_idx])
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        obs_t0 = time.perf_counter() if collect_timing else 0.0
        obs = self.world_vec._build_observation_from_cached_state(env_idx)
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if collect_timing else 0.0

        reward_t0 = time.perf_counter() if collect_timing else 0.0
        reward, terminated, truncated, mission_status = handle.loader.compute_full_step(
            obs,
            self.world_vec.batch_runtime.world(env_idx),
            handle.steps,
            handle.max_steps,
            truth=truth,
            inst_state=inst,
        )
        reward_compute_ms = (time.perf_counter() - reward_t0) * 1000.0 if collect_timing else 0.0

        info_t0 = time.perf_counter() if collect_timing else 0.0
        info = build_step_info(
            handle.loader,
            self.world_vec.batch_runtime.world(env_idx),
            int(handle.agent_id),
            mission_status=mission_status,
            terminated=bool(terminated),
            truncated=bool(truncated),
            inst_now=inst,
            truth_now=truth,
        )
        if collect_timing:
            info["timing"] = {
                "action_prepare_ms": float(action_prepare_ms),
                "batch_step_ms": float(batch_step_ms),
                "state_read_ms": float(state_read_ms),
                "behavior_update_ms": float(behavior_update_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "reward_compute_ms": float(reward_compute_ms),
                "info_build_ms": float((time.perf_counter() - info_t0) * 1000.0),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
        return obs, float(reward), bool(terminated), bool(truncated), info

    def rollout_window(self, *, initial_obs: Any, predict_action, max_steps: int, on_step_result):
        collect_timing = bool(getattr(self.world_vec, "collect_step_timing", False))
        timing = {
            "execution_runtime_step_ms": 0.0,
        }
        obs = initial_obs if isinstance(initial_obs, dict) else {}
        steps = 0
        limit = max(0, int(max_steps))
        while steps < limit:
            action = predict_action(obs)
            step_t0 = time.perf_counter() if collect_timing else 0.0
            obs, reward, terminated, truncated, info = self.step(action)
            if collect_timing:
                timing["execution_runtime_step_ms"] = float(
                    timing.get("execution_runtime_step_ms", 0.0) + (time.perf_counter() - step_t0) * 1000.0
                )
            on_step_result(obs, reward, terminated, truncated, info)
            steps += 1
            if bool(terminated or truncated):
                break
        return int(steps), timing

    def get_last_state(self):
        handle = self.world_vec._handles[0]
        return handle.last_inst, handle.last_truth

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.world_vec._handles[0].set_randomization_overrides(overrides)

    def close(self) -> None:
        self.world_vec.close()


def build_single_world_batch_execution_runtime(
    *,
    scenario_path: str,
    env_settings: dict[str, Any],
    wrapper_class: type | None = None,
    wrapper_kwargs: dict[str, Any] | None = None,
    worker_threads: int | None = None,
):
    if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
        raise ValueError(
            "single-world WorldBatchRuntime only supports an unwrapped execution env or "
            f"MultiTimescaleActionWrapper; got {getattr(wrapper_class, '__name__', str(wrapper_class))}"
        )

    resolved_threads = 1 if worker_threads is None else max(0, int(worker_threads))
    world_vec = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=1,
        worker_threads=resolved_threads,
        **dict(env_settings or {}),
    )
    handle = SingleWorldBatchExecutionRuntimeHandle(world_vec)
    runtime: Any = handle
    if wrapper_class is MultiTimescaleActionWrapper:
        runtime = WrappedExecutionRuntimeAdapter(
            handle,
            wrapper_class,
            wrapper_kwargs,
            timing_enabled=lambda: bool(getattr(world_vec, "collect_step_timing", False)),
        )
    return runtime
