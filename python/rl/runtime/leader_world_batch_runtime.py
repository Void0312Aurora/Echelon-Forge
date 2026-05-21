from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Sequence

import numpy as np
import ef_py
try:
    import gymnasium as gym
except ModuleNotFoundError:  # pragma: no cover
    gym = None

from gym_envs.universal_env import build_pilot_action, build_step_info, normalize_action
from python.rl.runtime.execution_runtime import (
    ExecutionRuntimeAdapter,
    WrappedExecutionRuntimeAdapter,
    copy_info_with_scaled_timing,
    unwrap_nested_env,
)
from python.rl.control.wrappers import MultiTimescaleActionWrapper
from python.rl.runtime.world_batch import WorldBatchVecEnvAccess, copy_obs_batch_item
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv


@dataclass
class _LeaderExecutionWorldView:
    runtime_group: "LeaderWorldBatchExecutionRuntimeGroup"
    env_idx: int

    @property
    def loader(self):
        return self.runtime_group.access.loader(self.env_idx)

    @property
    def sim(self):
        return self.loader.sim

    @property
    def agent_id(self):
        return self.runtime_group.access.agent_id(self.env_idx)

    @property
    def steps(self):
        return self.runtime_group.access.steps(self.env_idx)


class LeaderWorldBatchExecutionRuntimeHandle(ExecutionRuntimeAdapter, gym.Env if gym is not None else object):
    metadata = {"render_modes": []}

    def __init__(self, runtime_group: "LeaderWorldBatchExecutionRuntimeGroup", env_idx: int):
        if gym is not None:
            super().__init__()
        self.runtime_group = runtime_group
        self.env_idx = int(env_idx)
        self._unwrapped = _LeaderExecutionWorldView(runtime_group, int(env_idx))
        self.render_mode = None

    @property
    def action_space(self):
        return self.runtime_group.world_vec.action_space

    @property
    def observation_space(self):
        return self.runtime_group.world_vec.observation_space

    @property
    def policy_env(self):
        return self

    @property
    def unwrapped(self):
        return self._unwrapped

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        _ = options
        return self.runtime_group.reset_index(self.env_idx, seed=seed)

    def step(self, action):
        return self.runtime_group.step_indices([self.env_idx], [action])[0]

    def get_last_state(self):
        return self.runtime_group.access.last_state(self.env_idx)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.runtime_group.set_randomization_overrides(self.env_idx, overrides)

class LeaderWorldBatchExecutionRuntimeGroup:
    def __init__(self, world_vec: WorldBatchVecEnv, leader_envs: Sequence[Any] | None = None):
        self.world_vec = world_vec
        self.access = WorldBatchVecEnvAccess(world_vec)
        self._leader_envs = [
            None if env is None else unwrap_nested_env(env)
            for env in (list(leader_envs) if leader_envs is not None else [None] * int(self.world_vec.num_envs))
        ]
        self._handles = [
            LeaderWorldBatchExecutionRuntimeHandle(self, env_idx)
            for env_idx in range(int(self.world_vec.num_envs))
        ]

    @classmethod
    def compatibility_report(cls, envs: Sequence[Any]) -> tuple[bool, str]:
        env_list = list(envs)
        if not env_list:
            return False, "no leader envs provided"

        env0 = unwrap_nested_env(env_list[0])
        scenario_path = str(getattr(env0, "scenario_path", "") or "")
        if not scenario_path:
            return False, "missing scenario_path on leader env"

        if not bool(getattr(env0, "_execution_env_settings", {})) and hasattr(env0, "_resolve_execution_env_spec"):
            env0._resolve_execution_env_spec()
        base_settings = dict(getattr(env0, "_execution_env_settings", {}) or {})
        if not base_settings:
            return False, "execution env settings are unavailable"
        wrapper_class = getattr(env0, "_execution_wrapper_class", None)
        if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
            return False, (
                "execution action wrapper is unsupported by shared WorldBatchRuntime: "
                f"{getattr(wrapper_class, '__name__', str(wrapper_class))}"
            )

        for env_idx, wrapped_env in enumerate(env_list[1:], start=1):
            env = unwrap_nested_env(wrapped_env)
            if str(getattr(env, "scenario_path", "") or "") != scenario_path:
                return False, f"env[{env_idx}] scenario_path differs from env[0]"
            if not bool(getattr(env, "_execution_env_settings", {})) and hasattr(env, "_resolve_execution_env_spec"):
                env._resolve_execution_env_spec()
            env_settings = dict(getattr(env, "_execution_env_settings", {}) or {})
            if env_settings != base_settings:
                return False, f"env[{env_idx}] execution env settings differ from env[0]"
            wrapper_class = getattr(env, "_execution_wrapper_class", None)
            if wrapper_class is not None and wrapper_class is not MultiTimescaleActionWrapper:
                return False, (
                    "execution action wrapper is unsupported by shared WorldBatchRuntime: "
                    f"env[{env_idx}] uses {getattr(wrapper_class, '__name__', str(wrapper_class))}"
                )

        return True, ""

    @classmethod
    def from_leader_envs(
        cls,
        envs: Sequence[Any],
        *,
        world_batch_threads: int | None = None,
    ) -> "LeaderWorldBatchExecutionRuntimeGroup | None":
        env_list = list(envs)
        if not env_list:
            return None

        supported, reason = cls.compatibility_report(env_list)
        if not supported:
            return None
        env0 = unwrap_nested_env(env_list[0])
        scenario_path = str(getattr(env0, "scenario_path", "") or "")

        base_settings = dict(getattr(env0, "_execution_env_settings", {}) or {})

        world_vec = WorldBatchVecEnv(
            scenario_path=scenario_path,
            n_envs=len(env_list),
            worker_threads=world_batch_threads,
            **base_settings,
        )
        group = cls(world_vec, leader_envs=env_list)
        for env_idx, wrapped_env in enumerate(env_list):
            env = unwrap_nested_env(wrapped_env)
            if hasattr(env, "set_deferred_kernel_command_sync"):
                env.set_deferred_kernel_command_sync(True)
            runtime: Any = group.handle(env_idx)
            wrapper_class = getattr(env, "_execution_wrapper_class", None)
            wrapper_kwargs = getattr(env, "_execution_wrapper_kwargs", None)
            if wrapper_class is MultiTimescaleActionWrapper:
                runtime = WrappedExecutionRuntimeAdapter(
                    runtime,
                    wrapper_class,
                    wrapper_kwargs,
                    timing_enabled=lambda world_vec=world_vec: bool(getattr(world_vec, "collect_step_timing", False)),
                )
            env.set_execution_runtime(runtime)
        return group

    def handle(self, env_idx: int) -> LeaderWorldBatchExecutionRuntimeHandle:
        return self._handles[int(env_idx)]

    def leader_env(self, env_idx: int):
        try:
            return self._leader_envs[int(env_idx)]
        except Exception:
            return None

    def leader_window_runtime(self, env_idx: int):
        leader_env = self.leader_env(env_idx)
        if leader_env is None:
            return None
        runtime = getattr(leader_env, "leader_window_runtime", None)
        return runtime if runtime is not None else leader_env

    def leader_env_indices(self):
        return list(range(int(self.world_vec.num_envs)))

    @property
    def batch_runtime(self):
        return self.world_vec.batch_runtime

    @property
    def last_runtime_window_evidence(self):
        return self.access.last_runtime_window_evidence

    def max_decision_interval_steps(self, env_indices: Sequence[int] | None = None) -> int:
        if env_indices is None:
            target_indices = self.leader_env_indices()
        else:
            target_indices = [int(i) for i in env_indices]
        if not target_indices:
            return 0
        return max(
            int(getattr(self.leader_env(env_idx), "decision_interval_steps", 1) or 1)
            for env_idx in target_indices
        )

    def begin_leader_steps(self, actions: Sequence[Any], env_indices: Sequence[int] | None = None) -> None:
        if env_indices is None:
            target_indices = self.leader_env_indices()
        else:
            target_indices = [int(i) for i in env_indices]
        action_items = list(actions)
        if len(target_indices) != len(action_items):
            raise ValueError(f"expected {len(target_indices)} actions, got {len(action_items)}")
        for batch_idx, env_idx in enumerate(target_indices):
            leader_window_runtime = self.leader_window_runtime(env_idx)
            if leader_window_runtime is not None:
                leader_window_runtime.begin(action_items[batch_idx])

    def collect_live_execution_batch(self, env_indices: Sequence[int] | None = None):
        if env_indices is None:
            target_indices = self.leader_env_indices()
        else:
            target_indices = [int(i) for i in env_indices]
        live_indices: list[int] = []
        obs_batch = []
        for env_idx in target_indices:
            leader_window_runtime = self.leader_window_runtime(env_idx)
            if leader_window_runtime is not None and leader_window_runtime.has_pending_execution_step():
                live_indices.append(env_idx)
                obs_batch.append(leader_window_runtime.borrow_execution_observation())
        return live_indices, obs_batch

    def finish_leader_steps(self, env_indices: Sequence[int] | None = None):
        if env_indices is None:
            target_indices = self.leader_env_indices()
        else:
            target_indices = [int(i) for i in env_indices]
        out = {}
        for env_idx in target_indices:
            leader_window_runtime = self.leader_window_runtime(env_idx)
            if leader_window_runtime is not None:
                out[int(env_idx)] = leader_window_runtime.finish()
        return out

    def set_randomization_overrides(self, env_idx: int, overrides: dict | None) -> None:
        self.access.set_randomization_overrides(int(env_idx), overrides)

    def _world_time_step(self, env_idx: int) -> float:
        return self.access.world_time_step(int(env_idx))

    def _get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self.access.get_instrument_states_batch(refs)

    def _get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self.access.get_agent_observations_batch(refs)

    def _set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self.access.set_pilot_actions_batch(assignments)

    def _step_runtime_worlds(self, world_indices: Sequence[int]) -> None:
        self.access.step_worlds(world_indices)

    def reset_index(self, env_idx: int, *, seed: int | None = None):
        return self.access.reset_single_world(int(env_idx), seed=seed)

    @staticmethod
    def _copy_obs_item(obs_batch, env_idx: int):
        return copy_obs_batch_item(obs_batch, env_idx)

    def reset_indices(
        self,
        env_indices: Sequence[int] | None = None,
        *,
        seeds: Sequence[int | None] | None = None,
    ):
        if env_indices is None:
            target_indices = list(range(int(self.world_vec.num_envs)))
        else:
            target_indices = [int(i) for i in env_indices]
        if not target_indices:
            return {}

        seed_items = list(seeds) if seeds is not None else [None] * len(target_indices)
        if len(seed_items) != len(target_indices):
            raise ValueError(f"expected {len(target_indices)} seeds, got {len(seed_items)}")

        if len(target_indices) == int(self.world_vec.num_envs):
            normalized = [self.access.normalize_seed(seed_items[idx]) for idx in range(len(target_indices))]
            self.access.seeds = list(normalized)
            obs_batch = self.access.reset()
            per_env_scale = 1.0 / float(max(1, len(target_indices)))
            return {
                int(env_idx): (
                    self._copy_obs_item(obs_batch, env_idx),
                    copy_info_with_scaled_timing(self.access.reset_infos[int(env_idx)], per_env_scale),
                )
                for env_idx in target_indices
            }

        out = {}
        for idx, env_idx in enumerate(target_indices):
            out[int(env_idx)] = self.access.reset_single_world(int(env_idx), seed=seed_items[idx])
        return out

    def reset_leader_envs(
        self,
        env_indices: Sequence[int] | None = None,
        *,
        seeds: Sequence[int | None] | None = None,
    ):
        if env_indices is None:
            target_indices = list(range(int(self.world_vec.num_envs)))
        else:
            target_indices = [int(i) for i in env_indices]
        reset_results = self.reset_indices(target_indices, seeds=seeds)
        out = {}
        for env_idx in target_indices:
            obs, reset_info = reset_results[int(env_idx)]
            leader_env = self.leader_env(env_idx)
            if leader_env is not None:
                out[int(env_idx)] = leader_env._finish_execution_reset(obs, reset_info)
            else:
                out[int(env_idx)] = (obs, reset_info)
        self.sync_command_chain_indices(target_indices)
        return out

    def step_indices(self, env_indices: Sequence[int], actions: Sequence[Any]):
        target_indices = [int(i) for i in env_indices]
        action_items = list(actions)
        if len(target_indices) != len(action_items):
            raise ValueError(f"expected {len(target_indices)} actions, got {len(action_items)}")
        if not target_indices:
            return []

        collect_timing = bool(getattr(self.world_vec, "collect_step_timing", False))
        total_t0 = time.perf_counter() if collect_timing else 0.0
        command_sync_ms = 0.0
        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.sync_command_chain_indices(target_indices)
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        _, refs = self.access.build_refs(target_indices)
        prepare_t0 = time.perf_counter() if collect_timing else 0.0
        inst_now_list = None
        if self.world_vec.action_mode != "full":
            inst_now_list = self._get_instrument_states_batch(refs)

        assignments = []
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self.access.state(env_idx)
            if handle.agent_id is None:
                raise RuntimeError(f"world {env_idx} is not initialized; call reset() before step().")
            action = normalize_action(
                action_items[batch_idx],
                action_space=self.world_vec.action_space,
                action_mode=self.world_vec.action_mode,
            )
            handle.last_action = action.astype(np.float32, copy=True)
            assign = ef_py.WorldPilotActionAssignment()
            assign.world_index = int(env_idx)
            assign.entity_id = int(handle.agent_id)
            assign.action = build_pilot_action(
                action,
                action_mode=self.world_vec.action_mode,
                inst_now=None if inst_now_list is None else inst_now_list[batch_idx],
            )
            assignments.append(assign)
        action_prepare_ms = (time.perf_counter() - prepare_t0) * 1000.0 if collect_timing else 0.0

        step_t0 = time.perf_counter() if collect_timing else 0.0
        self._set_pilot_actions_batch(assignments)
        self._step_runtime_worlds([int(idx) for idx in target_indices])
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if collect_timing else 0.0

        read_t0 = time.perf_counter() if collect_timing else 0.0
        truth_list = self._get_agent_observations_batch(refs)
        inst_list = self._get_instrument_states_batch(refs)
        state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if collect_timing else 0.0
        behavior_t0 = time.perf_counter() if collect_timing else 0.0
        for batch_idx, env_idx in enumerate(target_indices):
            handle = self.access.state(env_idx)
            handle.steps += 1
            handle.last_truth = truth_list[batch_idx]
            handle.last_inst = inst_list[batch_idx]
            sim_time = float(handle.steps) * self._world_time_step(env_idx)
            handle.loader.update_behaviors(
                sim_time,
                truth=handle.last_truth,
                inst=handle.last_inst,
                sync_to_kernel=False,
            )
        behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if collect_timing else 0.0
        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.access.sync_command_chain(target_indices)
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        out = []
        obs_build_ms = 0.0
        reward_compute_ms = 0.0
        info_build_ms = 0.0
        per_env_timing = {}
        if collect_timing:
            self.access.last_step_timing = {}
        for env_idx in target_indices:
            handle = self.access.state(env_idx)
            obs_t0 = time.perf_counter() if collect_timing else 0.0
            obs = self.access.build_observation_from_cached_state(env_idx)
            if collect_timing:
                obs_build_ms += (time.perf_counter() - obs_t0) * 1000.0
            reward_t0 = time.perf_counter() if collect_timing else 0.0
            reward, terminated, truncated, mission_status = handle.loader.compute_full_step(
                obs,
                handle.loader.sim,
                handle.steps,
                handle.max_steps,
                truth=handle.last_truth,
                inst_state=handle.last_inst,
            )
            if collect_timing:
                reward_compute_ms += (time.perf_counter() - reward_t0) * 1000.0
            info_t0 = time.perf_counter() if collect_timing else 0.0
            info = build_step_info(
                handle.loader,
                handle.loader.sim,
                int(handle.agent_id),
                mission_status=mission_status,
                terminated=bool(terminated),
                truncated=bool(truncated),
                inst_now=handle.last_inst,
                truth_now=handle.last_truth,
            )
            if collect_timing:
                info_build_ms += (time.perf_counter() - info_t0) * 1000.0
            out.append((obs, float(reward), bool(terminated), bool(truncated), info))

        if collect_timing:
            per_env_scale = 1.0 / float(max(1, len(target_indices)))
            batch_timing = {
                "action_prepare_ms": float(action_prepare_ms),
                "batch_step_ms": float(batch_step_ms),
                "state_read_ms": float(state_read_ms),
                "behavior_update_ms": float(behavior_update_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "reward_compute_ms": float(reward_compute_ms),
                "info_build_ms": float(info_build_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
            per_env_timing = {
                key: float(value) * per_env_scale
                for key, value in batch_timing.items()
            }
            self.access.last_step_timing = dict(batch_timing)
        else:
            self.access.last_step_timing = {}

        if per_env_timing:
            out = [
                (
                    obs,
                    reward,
                    terminated,
                    truncated,
                    {**dict(info or {}), "timing": dict(per_env_timing)},
                )
                for obs, reward, terminated, truncated, info in out
            ]
        return out

    def step_leader_envs(self, env_indices: Sequence[int], actions: Sequence[Any]):
        target_indices = [int(i) for i in env_indices]
        action_items = list(actions)
        if len(target_indices) != len(action_items):
            raise ValueError(f"expected {len(target_indices)} actions, got {len(action_items)}")
        if not target_indices:
            return []

        effective_actions = []
        prepared_states = []
        leader_envs = []
        for batch_idx, env_idx in enumerate(target_indices):
            leader_window_runtime = self.leader_window_runtime(env_idx)
            leader_envs.append(leader_window_runtime)
            if leader_window_runtime is not None:
                effective_action, prepared_state = leader_window_runtime.prepare_shared_execution_action(action_items[batch_idx])
            else:
                effective_action = np.asarray(action_items[batch_idx], dtype=np.float32).reshape(-1)
                prepared_state = None
            effective_actions.append(effective_action)
            prepared_states.append(prepared_state)

        step_results = self.step_indices(target_indices, effective_actions)
        for batch_idx, leader_window_runtime in enumerate(leader_envs):
            if leader_window_runtime is None:
                continue
            obs, reward, terminated, truncated, info = step_results[batch_idx]
            leader_window_runtime.apply_execution_step_result(
                obs,
                reward,
                terminated,
                truncated,
                info,
                prepared_action_state=prepared_states[batch_idx],
            )
        return step_results

    def sync_command_chain_indices(self, env_indices: Sequence[int] | None = None) -> None:
        if env_indices is None:
            target_indices = list(range(int(self.world_vec.num_envs)))
        else:
            target_indices = [int(i) for i in env_indices]
        if not target_indices:
            return
        self.world_vec._sync_command_chain_batch(target_indices)
        for env_idx in target_indices:
            leader_env = self.leader_env(env_idx)
            if leader_env is not None:
                if hasattr(leader_env, "_kernel_command_sync_dirty"):
                    leader_env._kernel_command_sync_dirty = False

    def close(self) -> None:
        for leader_env in list(getattr(self, "_leader_envs", []) or []):
            if leader_env is not None and hasattr(leader_env, "set_deferred_kernel_command_sync"):
                try:
                    leader_env.set_deferred_kernel_command_sync(False)
                except Exception:
                    pass
        self.world_vec.close()
