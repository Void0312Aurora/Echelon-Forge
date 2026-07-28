from __future__ import annotations

import time
from typing import Any

import ef_py
import numpy as np

from python.tasking_contracts.timing_utils import coerce_timing_dict

from .bridges import LeaderCommandBridge
from .common import load_json_dict, make_args_stub
from .decision_runtime import (
    apply_leader_command,
    bucket_allows_command_bias,
    build_observation,
    clip_altitude,
    clip_speed,
    current_command_tuple,
    decode_action,
    fuel_margin_state,
    has_active_waypoints,
    landing_reference_command,
    mapping_has_bias,
    phase_enum_for_id,
    phase_name_for_id,
    resolve_report_type,
    sanitize_action_mapping,
    station_metrics,
    terminal_context,
    terminal_feasible,
    zero_mapping_biases,
)
from .execution_runtime import (
    build_execution_env,
    build_execution_env_from_spec,
    build_execution_policy,
    build_execution_runtime,
    cache_execution_runtime_state,
    capture_execution_runtime_state,
    close_execution_runtime,
    configure_execution_runtime,
    current_execution_runtime_state,
    current_leader_window_state,
    current_runtime_last_state,
    exec_policy_reset,
    predict_execution_action,
    resolve_execution_env_spec,
    snapshot_leader_state,
    sync_bridge_from_loader,
)


class LeaderRuntimeFacadeMixin:
    @property
    def unwrapped(self):
        return self._exec_runtime.unwrapped

    def _build_default_leader_window_runtime(self):
        from python.rl.runtime.leader_window_runtime import (
            LocalLeaderWindowRuntime,
            WorldBatchLeaderWindowRuntime,
        )

        execution_runtime = getattr(self, "_exec_runtime", None)
        if bool(getattr(self, "execution_world_batch_runtime", False)) and hasattr(execution_runtime, "rollout_window"):
            return WorldBatchLeaderWindowRuntime(self)
        return LocalLeaderWindowRuntime(self)

    def _ensure_leader_window_runtime(self):
        runtime = getattr(self, "_leader_window_runtime", None)
        if runtime is None:
            runtime = self._build_default_leader_window_runtime()
            self._leader_window_runtime = runtime
        return runtime

    @property
    def leader_window_runtime(self):
        return self._ensure_leader_window_runtime()

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        try:
            self._exec_runtime.set_randomization_overrides(overrides)
        except Exception:
            pass

    def set_execution_runtime(self, execution_runtime: Any) -> None:
        old_runtime = getattr(self, "_exec_runtime", None)
        self._exec_runtime = execution_runtime
        if self.execution_backend == "scripted":
            self._exec_policy = self._build_execution_policy()
        self._last_exec_obs = None
        self._last_exec_inst = None
        self._last_exec_truth = None
        self._last_exec_action = None
        self._exec_action_repeat_remaining = 0
        self._last_effective_execution_action_repeat = 1
        self._kernel_command_sync_dirty = False
        self._close_execution_runtime(old_runtime, active_runtime=execution_runtime)

    def set_leader_window_runtime(self, leader_window_runtime: Any | None) -> None:
        self._leader_window_runtime = leader_window_runtime or self._build_default_leader_window_runtime()

    def set_deferred_kernel_command_sync(self, enabled: bool) -> None:
        self._defer_kernel_command_sync = bool(enabled)
        if not self._defer_kernel_command_sync:
            self.flush_kernel_command_sync()

    def flush_kernel_command_sync(self) -> None:
        loader = self.unwrapped.loader
        try:
            loader._sync_kernel_mission_command()
        except Exception:
            pass
        self._bridge.set_state(
            task_order=getattr(loader, "task_order", None),
            leader_intent=getattr(loader, "leader_intent", None),
            pilot_report=getattr(loader, "pilot_report", None),
        )
        try:
            self._bridge.sync_to_kernel(loader)
        except Exception:
            pass
        self._kernel_command_sync_dirty = False

    def set_leader_overrides(self, overrides: dict | None) -> None:
        if not isinstance(overrides, dict):
            return
        float_fields = {
            "teacher_keep_deadband": (0.0, 0.95),
            "invalid_phase_penalty": (0.0, None),
            "premature_approach_penalty": (0.0, None),
            "baseline_deviation_penalty": (0.0, None),
            "mode_change_penalty": (0.0, None),
            "approach_gate_distance_m": (500.0, None),
            "approach_gate_cross_m": (100.0, None),
            "approach_gate_heading_error_deg": (5.0, None),
            "heading_bias_limit_deg": (0.0, None),
            "altitude_bias_limit_m": (0.0, None),
            "speed_bias_limit_mps": (0.0, None),
        }
        for key, bounds in float_fields.items():
            if key not in overrides:
                continue
            try:
                value = float(overrides[key])
            except Exception:
                continue
            lo, hi = bounds
            if lo is not None:
                value = max(float(lo), value)
            if hi is not None:
                value = min(float(hi), value)
            setattr(self, key, float(value))

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        _ = options
        collect_step_timing = bool(getattr(self, "collect_step_timing", False))
        reset_t0 = time.perf_counter() if collect_step_timing else 0.0
        obs, info = self._exec_runtime.reset(seed=seed)
        base_timing = None
        if collect_step_timing:
            base_timing = {
                "execution_reset_ms": float((time.perf_counter() - reset_t0) * 1000.0),
            }
        return self._finish_execution_reset(obs, info, base_timing=base_timing)

    def _finish_execution_reset(self, obs, info, *, base_timing: dict[str, float] | None = None):
        collect_step_timing = bool(getattr(self, "collect_step_timing", False))
        total_t0 = time.perf_counter() if collect_step_timing else 0.0
        self._last_exec_obs = obs
        policy_t0 = time.perf_counter() if collect_step_timing else 0.0
        try:
            self._exec_runtime.reset_policy_state(obs)
        except Exception:
            pass
        policy_reset_ms = (time.perf_counter() - policy_t0) * 1000.0 if collect_step_timing else 0.0
        cache_t0 = time.perf_counter() if collect_step_timing else 0.0
        self._cache_execution_runtime_state()
        cache_state_ms = (time.perf_counter() - cache_t0) * 1000.0 if collect_step_timing else 0.0
        self._last_exec_action = None
        self._exec_action_repeat_remaining = 0
        self._last_effective_execution_action_repeat = 1
        self._pending_leader_state = None
        self._exec_policy_reset(obs)
        loader = self.unwrapped.loader
        self._bridge.set_state(
            task_order=getattr(loader, "task_order", None),
            leader_intent=getattr(loader, "leader_intent", None),
            pilot_report=getattr(loader, "pilot_report", None),
        )
        loader._leader_phase_manager = self._bridge
        try:
            sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
        except Exception:
            sim_time_s = 0.0
        inst_now, truth_now = self._current_execution_runtime_state()
        c2_t0 = time.perf_counter() if collect_step_timing else 0.0
        try:
            self._last_c2_info = self._c2_manager.reset(
                loader,
                sim_time_s=sim_time_s,
                truth=truth_now,
                inst=inst_now,
                sync_to_kernel=not bool(getattr(self, "_defer_kernel_command_sync", False)),
            )
        except TypeError:
            self._last_c2_info = self._c2_manager.reset(loader, sim_time_s=sim_time_s)
        c2_reset_ms = (time.perf_counter() - c2_t0) * 1000.0 if collect_step_timing else 0.0
        self._last_leader_command = None
        self._last_leader_mode = "teacher"
        self._last_requested_bucket = "teacher"
        self._last_baseline_snapshot = self._snapshot_leader_state()
        self._sync_bridge_from_loader()
        obs_t0 = time.perf_counter() if collect_step_timing else 0.0
        leader_obs = self._build_observation()
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if collect_step_timing else 0.0

        execution_reset_info = dict(info or {}) if isinstance(info, dict) else {"value": info}
        execution_reset_timing = coerce_timing_dict(execution_reset_info.get("timing"))
        info_out = {"execution_reset_info": execution_reset_info}
        if execution_reset_timing:
            info_out["execution_reset_timing"] = execution_reset_timing
        if collect_step_timing:
            timing = dict(base_timing or {})
            timing["policy_reset_ms"] = float(timing.get("policy_reset_ms", 0.0) + policy_reset_ms)
            timing["cache_state_ms"] = float(timing.get("cache_state_ms", 0.0) + cache_state_ms)
            timing["c2_reset_ms"] = float(timing.get("c2_reset_ms", 0.0) + c2_reset_ms)
            timing["obs_build_ms"] = float(timing.get("obs_build_ms", 0.0) + obs_build_ms)
            timing["total_ms"] = float((time.perf_counter() - total_t0) * 1000.0)
            self.last_reset_timing = timing
            info_out["timing"] = dict(timing)
        else:
            self.last_reset_timing = {}
        return leader_obs, info_out

    def step(self, action):
        return self.leader_window_runtime.run_step(action)

    def _normalize_leader_action(self, action: Any) -> np.ndarray:
        action = np.asarray(action, dtype=np.float32).reshape(-1)
        if action.size == 4:
            # Backward compatibility for previously trained leader models that only emitted
            # mission-command decisions without an explicit report head.
            action = np.concatenate([action, np.zeros((2,), dtype=np.float32)], axis=0)
        if action.size != 6:
            raise ValueError(f"LeaderTrainingEnv expected action shape (4,) or (6,), got {tuple(action.shape)}")
        return action

    def _begin_local_leader_window(self, action: Any) -> None:
        self._ensure_leader_window_runtime().begin(action)

    def begin_batched_leader_step(self, action: Any) -> None:
        self.leader_window_runtime.begin(action)

    def _has_pending_local_execution_step(self) -> bool:
        return bool(self._ensure_leader_window_runtime().has_pending_execution_step())

    def has_pending_execution_step(self) -> bool:
        return bool(self.leader_window_runtime.has_pending_execution_step())

    def _borrow_local_execution_observation(self) -> dict[str, Any]:
        return self._ensure_leader_window_runtime().borrow_execution_observation()

    def borrow_execution_observation(self) -> dict[str, Any]:
        return self.leader_window_runtime.borrow_execution_observation()

    def current_execution_observation(self) -> dict[str, Any]:
        return self.leader_window_runtime.current_execution_observation()

    def _prepare_shared_execution_action_impl(self, exec_action: Any):
        return self._ensure_leader_window_runtime().prepare_shared_execution_action(exec_action)

    def prepare_shared_execution_action(self, exec_action: Any):
        return self.leader_window_runtime.prepare_shared_execution_action(exec_action)

    def _execute_local_execution_step(self, exec_action: Any) -> None:
        self._ensure_leader_window_runtime().step_execution_once(exec_action)

    def step_execution_once(self, exec_action: Any) -> None:
        self.leader_window_runtime.step_execution_once(exec_action)

    def _rollout_pending_execution_window_impl(self, *, max_steps: int | None = None) -> int:
        return int(self._ensure_leader_window_runtime().rollout(max_steps=max_steps))

    def rollout_pending_execution_window(self, *, max_steps: int | None = None) -> int:
        return int(self.leader_window_runtime.rollout(max_steps=max_steps))

    def _apply_execution_step_result_impl(
        self,
        obs,
        reward,
        terminated,
        truncated,
        info,
        prepared_action_state: Any = None,
    ) -> None:
        self._ensure_leader_window_runtime().apply_execution_step_result(
            obs,
            reward,
            terminated,
            truncated,
            info,
            prepared_action_state=prepared_action_state,
        )

    def apply_execution_step_result(self, obs, reward, terminated, truncated, info, prepared_action_state: Any = None) -> None:
        self.leader_window_runtime.apply_execution_step_result(
            obs,
            reward,
            terminated,
            truncated,
            info,
            prepared_action_state=prepared_action_state,
        )

    def _finish_local_leader_window(self):
        return self._ensure_leader_window_runtime().finish()

    def finish_batched_leader_step(self):
        return self.leader_window_runtime.finish()

    def _build_execution_env(self):
        return build_execution_env(self)

    def _build_execution_env_from_spec(self, env_settings, wrapper_class, wrapper_kwargs):
        return build_execution_env_from_spec(self, env_settings, wrapper_class, wrapper_kwargs)

    def _build_execution_runtime(self):
        return build_execution_runtime(self)

    def _resolve_execution_env_spec(self):
        return resolve_execution_env_spec(self)

    def load_execution_config(self) -> dict[str, Any]:
        return load_json_dict(self.execution_train_config)

    @staticmethod
    def make_execution_args_stub() -> Any:
        return make_args_stub()

    def _build_execution_policy(self):
        return build_execution_policy(self)

    def close(self):
        runtime = getattr(self, "_exec_runtime", None)
        self._exec_runtime = None
        close_execution_runtime(runtime)
        try:
            super().close()
        except Exception:
            pass

    def _configure_execution_runtime(self) -> None:
        configure_execution_runtime(self)

    def _exec_policy_reset(self, obs: dict) -> None:
        exec_policy_reset(self, obs)

    def _current_leader_window_state(self):
        return current_leader_window_state(self)

    def _predict_execution_action(self, obs: dict) -> np.ndarray:
        return predict_execution_action(self, obs)

    def _runtime_last_state(self):
        return current_runtime_last_state(self)

    def _capture_execution_runtime_state(self):
        return capture_execution_runtime_state(self)

    def _cache_execution_runtime_state(self, *, inst_now=None, truth_now=None):
        return cache_execution_runtime_state(self, inst_now=inst_now, truth_now=truth_now)

    def _current_execution_runtime_state(self):
        return current_execution_runtime_state(self)

    def _snapshot_leader_state(self) -> dict[str, Any]:
        return snapshot_leader_state(self)

    def _sync_bridge_from_loader(self) -> None:
        sync_bridge_from_loader(self)

    def _compute_teacher_baseline(self) -> dict[str, Any]:
        loader = self.unwrapped.loader
        try:
            sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
        except Exception:
            sim_time_s = 0.0
        inst_now, truth_now = self._current_execution_runtime_state()
        self._teacher_manager.update(
            loader,
            sim_time_s=sim_time_s,
            truth=truth_now,
            inst=inst_now,
            sync_to_kernel=not bool(getattr(self, "_defer_kernel_command_sync", False)),
        )
        baseline = self._snapshot_leader_state()
        self._sync_bridge_from_loader()
        return baseline

    def _update_scripted_c2(self) -> dict[str, Any]:
        loader = self.unwrapped.loader
        try:
            sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
        except Exception:
            sim_time_s = 0.0
        inst_now, truth_now = self._current_execution_runtime_state()
        try:
            c2_info = self._c2_manager.update(
                loader,
                sim_time_s=sim_time_s,
                truth=truth_now,
                inst=inst_now,
                sync_to_kernel=not bool(getattr(self, "_defer_kernel_command_sync", False)),
            )
        except TypeError:
            c2_info = self._c2_manager.update(loader, sim_time_s=sim_time_s)
        self._last_c2_info = dict(c2_info or {})
        self._sync_bridge_from_loader()
        return self._last_c2_info

    def _decode_action(self, action: np.ndarray):
        return decode_action(self, action)

    @staticmethod
    def _mapping_has_bias(mapping) -> bool:
        return mapping_has_bias(mapping)

    @staticmethod
    def _zero_mapping_biases(mapping):
        return zero_mapping_biases(mapping)

    @staticmethod
    def _bucket_allows_command_bias(phase_bucket: str) -> bool:
        return bucket_allows_command_bias(phase_bucket)

    def _resolve_report_type(self, mapping, *, phase_bucket: str):
        return resolve_report_type(self, mapping, phase_bucket=phase_bucket)

    def _station_metrics(self, loader: Any, *, truth: Any = None, inst: Any = None) -> dict[str, float | bool]:
        return station_metrics(self, loader, truth=truth, inst=inst)

    def _fuel_margin_state(self, task: Any, inst: Any) -> tuple[float, float]:
        return fuel_margin_state(self, task, inst)

    def _terminal_context(self) -> dict[str, float | bool | str]:
        return terminal_context(self)

    def _terminal_feasible(self, baseline: dict[str, Any], terminal_ctx: dict[str, Any]) -> bool:
        return terminal_feasible(self, baseline, terminal_ctx)

    def _landing_reference_command(self) -> tuple[float, float, float] | None:
        return landing_reference_command(self)

    def _has_active_waypoints(self) -> bool:
        return has_active_waypoints(self)

    def _sanitize_action_mapping(
        self,
        *,
        mapping,
        baseline: dict[str, Any],
    ):
        return sanitize_action_mapping(self, mapping=mapping, baseline=baseline)

    def _apply_leader_command(self, *, mapping, baseline: dict[str, Any]) -> None:
        apply_leader_command(self, mapping=mapping, baseline=baseline)

    def _clip_altitude(self, task: ef_py.TaskOrder, altitude_m: float) -> float:
        return clip_altitude(self, task, altitude_m)

    def _clip_speed(self, task: ef_py.TaskOrder, speed_mps: float) -> float:
        return clip_speed(self, task, speed_mps)

    def _phase_name_for_id(self, phase_id: int, *, fallback: str) -> str:
        return phase_name_for_id(self, phase_id, fallback=fallback)

    def _phase_enum_for_id(self, phase_id: int):
        return phase_enum_for_id(self, phase_id)

    def _current_command_tuple(self) -> tuple[int, float, float, float]:
        return current_command_tuple(self)

    def _build_observation(self) -> dict[str, np.ndarray]:
        return build_observation(self)

    def _close_execution_runtime(self, runtime: Any, *, active_runtime: Any | None = None) -> None:
        close_execution_runtime(runtime, active_runtime=active_runtime)


__all__ = ["LeaderRuntimeFacadeMixin"]
