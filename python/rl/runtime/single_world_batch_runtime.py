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
from gym_envs.universal_env import (
    add_air_combat_event_action_info,
    air_combat_hybrid_effective_action,
    apply_air_combat_event_action_gate,
    apply_naval_station_action,
    build_pilot_action,
    finalize_air_combat_event_action_info,
    is_air_combat_hybrid_action_mode,
    is_naval_station_action_mode,
    naval_action_family_for_mode,
    naval_station_action_command,
    normalize_action,
)
from python.rl.runtime.world_batch import (
    WorldBatchVecEnvAccess,
    build_loader_step_info,
    compute_loader_step_outcome,
)
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv


@dataclass
class _SingleWorldView:
    runtime: "SingleWorldBatchExecutionRuntimeHandle"

    @property
    def loader(self):
        return self.runtime.access.loader(0)

    @property
    def sim(self):
        return self.runtime.access.sim(0)

    @property
    def agent_id(self):
        return self.runtime.access.agent_id(0)

    @property
    def steps(self):
        return self.runtime.access.steps(0)


class SingleWorldBatchExecutionRuntimeHandle(ExecutionRuntimeAdapter, gym.Env if gym is not None else object):
    metadata = {"render_modes": []}

    def __init__(self, world_vec: WorldBatchVecEnv):
        if gym is not None:
            super().__init__()
        self.world_vec = world_vec
        self.access = WorldBatchVecEnvAccess(world_vec)
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
    def loader(self):
        return self.access.loader(0)

    @property
    def sim(self):
        return self.access.sim(0)

    @property
    def agent_id(self):
        return self.access.agent_id(0)

    @property
    def steps(self):
        return self.access.steps(0)

    @property
    def max_steps(self):
        return self.access.max_steps(0)

    def get_time_step(self) -> float:
        return float(self.access.world_time_step(0))

    @property
    def unwrapped(self):
        return self._unwrapped

    @property
    def last_runtime_window_evidence(self):
        return self.access.last_runtime_window_evidence

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        _ = options
        return self.access.reset_single_world(0, seed=seed)

    def step(self, action):
        env_idx = 0
        collect_timing = bool(getattr(self.world_vec, "collect_step_timing", False))
        total_t0 = time.perf_counter() if collect_timing else 0.0
        handle = self.access.state(env_idx)
        if handle.agent_id is None:
            raise RuntimeError("world 0 is not initialized; call reset() before step().")

        command_sync_ms = 0.0
        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.access.sync_command_chain([env_idx])
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        _, refs = self.access.build_refs([env_idx])
        prepare_t0 = time.perf_counter() if collect_timing else 0.0
        inst_now = None
        if self.world_vec.action_mode != "full":
            inst_now = self.access.get_instrument_states_batch(refs)[0]
        normalized_action = normalize_action(
            action,
            action_space=self.world_vec.action_space,
            action_mode=self.world_vec.action_mode,
        )
        air_combat_truth_before = None
        if is_naval_station_action_mode(self.world_vec.action_mode):
            normalized_action = naval_station_action_command(normalized_action)
            handle.last_action = normalized_action.astype(np.float32, copy=True)
            if apply_naval_station_action(handle.loader, normalized_action):
                sync_t0 = time.perf_counter() if collect_timing else 0.0
                self.access.sync_command_chain([env_idx])
                if collect_timing:
                    command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0
        elif is_air_combat_hybrid_action_mode(self.world_vec.action_mode):
            policy_intent = normalized_action.astype(np.float32, copy=True)
            normalized_action = air_combat_hybrid_effective_action(
                normalized_action,
                previous_intent=handle.last_policy_action_intent,
            )
            handle.last_policy_action_intent = policy_intent
            air_combat_truth_before = handle.last_truth
            normalized_action, _ = apply_air_combat_event_action_gate(
                handle.loader,
                normalized_action,
                agent_id=int(handle.agent_id),
                truth_before=handle.last_truth,
            )
            handle.last_action = normalized_action.astype(np.float32, copy=True)
        else:
            handle.last_action = normalized_action.astype(np.float32, copy=True)
        handle.loader._last_action_mode = str(self.world_vec.action_mode)
        handle.loader._last_effective_action = handle.last_action.astype(np.float32, copy=True)
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
        source_time_s = float(getattr(handle.last_truth, "sim_time", 0.0) or 0.0)
        window_evidence = None
        if self.access.supports_runtime_window_api():
            window_evidence = self.access.run_maintained_window(
                world_index=int(env_idx),
                entity_id=int(handle.agent_id),
                pilot_action=assignment.action,
                source_time_s=source_time_s,
                window_id=f"single_world:{int(env_idx)}:{int(handle.steps)}",
                input_snapshot_version=f"obs:{int(env_idx)}:{int(handle.steps)}",
                source_layer="training_policy",
                information_state_label="facade_observation_packet",
                action_family=naval_action_family_for_mode(self.world_vec.action_mode),
                include_engagement=True,
                include_diagnostics=True,
            )
        if window_evidence is None:
            raise RuntimeError(
                "RuntimeFacade.run_window() is required by single-world training consumers"
            )
        else:
            batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if collect_timing else 0.0
            read_t0 = time.perf_counter() if collect_timing else 0.0
            observation_packet = window_evidence.observation_packet
            truth_list = list(getattr(observation_packet, "agent_observations", []) or [])
            inst_list = list(getattr(observation_packet, "instrument_states", []) or [])
            if not truth_list or not inst_list:
                raise RuntimeError(
                    "RuntimeFacade.run_window() did not return the maintained observation packet payload "
                    "required by single-world training consumers"
                )
            truth = truth_list[0]
            inst = inst_list[0]
            state_read_ms = (time.perf_counter() - read_t0) * 1000.0 if collect_timing else 0.0

        if is_air_combat_hybrid_action_mode(self.world_vec.action_mode):
            finalize_air_combat_event_action_info(
                handle.loader,
                truth_before=air_combat_truth_before,
                truth_after=truth,
            )

        behavior_t0 = time.perf_counter() if collect_timing else 0.0
        handle.steps += 1
        handle.last_truth = truth
        handle.last_inst = inst
        sim_time = float(handle.steps) * float(self.access.world_time_step(env_idx))
        handle.loader.update_behaviors(
            sim_time,
            truth=truth,
            inst=inst,
            sync_to_kernel=False,
        )
        behavior_update_ms = (time.perf_counter() - behavior_t0) * 1000.0 if collect_timing else 0.0

        sync_t0 = time.perf_counter() if collect_timing else 0.0
        self.access.sync_command_chain([env_idx])
        if collect_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        obs_t0 = time.perf_counter() if collect_timing else 0.0
        obs = self.access.build_observation_from_cached_state(env_idx)
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if collect_timing else 0.0

        reward_t0 = time.perf_counter() if collect_timing else 0.0
        reward, terminated, truncated, mission_status = compute_loader_step_outcome(
            handle.loader,
            obs=obs,
            steps=handle.steps,
            max_steps=handle.max_steps,
            truth=truth,
            inst_state=inst,
        )
        reward_compute_ms = (time.perf_counter() - reward_t0) * 1000.0 if collect_timing else 0.0

        info_t0 = time.perf_counter() if collect_timing else 0.0
        info = build_loader_step_info(
            handle.loader,
            entity_id=int(handle.agent_id),
            mission_status=mission_status,
            terminated=bool(terminated),
            truncated=bool(truncated),
            inst_now=inst,
            truth_now=truth,
        )
        if is_air_combat_hybrid_action_mode(self.world_vec.action_mode):
            add_air_combat_event_action_info(info, handle.loader)
        if window_evidence is not None:
            engagement_barrier_id = ""
            if window_evidence.engagement_packet is not None:
                engagement_barrier_id = str(
                    getattr(window_evidence.engagement_packet, "barrier_id", "") or ""
                )
            info["runtime_window_evidence"] = {
                "barrier_ids": [
                    str(getattr(record, "barrier_id", "") or "")
                    for record in list(window_evidence.barrier_trace)
                ],
                "event_barrier_id": engagement_barrier_id,
                "observation_barrier_id": str(
                    getattr(window_evidence.observation_packet, "barrier_id", "") or ""
                ),
                "observation_provenance": str(
                    getattr(
                        getattr(window_evidence.observation_packet, "provenance", None),
                        "source_label",
                        "",
                    )
                    or ""
                ),
                "engagement_provenance": str(
                    getattr(
                        getattr(window_evidence.engagement_packet, "packet_provenance", None),
                        "source_label",
                        "",
                    )
                    or ""
                ),
                "diagnostics_provenance": str(
                    getattr(
                        getattr(window_evidence.engagement_packet, "diagnostics_provenance", None),
                        "source_label",
                        "",
                    )
                    or ""
                ),
                "cadence_reason": str(window_evidence.cadence_reason),
                "uses_compat_fallback": bool(window_evidence.uses_compat_fallback),
            }
        else:
            raise RuntimeError("RuntimeFacade.run_window() is required by single-world info builders")
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
        return self.access.last_state(0)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.access.set_randomization_overrides(0, overrides)

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
