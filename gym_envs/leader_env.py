from __future__ import annotations

import os
import sys
import time
from typing import Any

import numpy as np
import torch

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BUILD_DIRS = []
_ENV_BUILD_DIR = os.environ.get("CMO_BUILD_DIR", "").strip()
if _ENV_BUILD_DIR:
    _BUILD_DIRS.append(_ENV_BUILD_DIR if os.path.isabs(_ENV_BUILD_DIR) else os.path.join(_REPO_ROOT, _ENV_BUILD_DIR))
_BUILD_DIRS.extend(
    [
        os.path.join(_REPO_ROOT, "build-workshop"),
        os.path.join(_REPO_ROOT, "build-gpu"),
        os.path.join(_REPO_ROOT, "build"),
    ]
)
for _build_dir in reversed(_BUILD_DIRS):
    _build_dir = os.path.abspath(_build_dir)
    if os.path.isdir(_build_dir) and any(
        fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_build_dir)
    ):
        if _build_dir in sys.path:
            sys.path.remove(_build_dir)
        sys.path.insert(0, _build_dir)

import ef_py

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # pragma: no cover
    gym = None
    spaces = None

from gym_envs.leader_env_parts import (
    LeaderActionMapping,
    LeaderCommandBridge,
    apply_leader_command,
    bucket_allows_command_bias,
    build_observation,
    clip_altitude,
    clip_speed,
    current_command_tuple,
    current_execution_runtime_state,
    current_leader_window_state,
    current_runtime_last_state,
    decode_action,
    exec_policy_reset,
    fuel_margin_state,
    has_active_waypoints,
    landing_reference_command,
    load_json_dict,
    mapping_has_bias,
    make_args_stub,
    phase_enum_for_id,
    phase_name_for_id,
    predict_execution_action,
    resolve_execution_env_spec,
    resolve_report_type,
    sanitize_action_mapping,
    station_metrics,
    snapshot_leader_state,
    sync_bridge_from_loader,
    terminal_context,
    terminal_feasible,
    zero_mapping_biases,
    build_execution_env,
    build_execution_env_from_spec,
    build_execution_policy,
    build_execution_runtime,
    cache_execution_runtime_state,
    capture_execution_runtime_state,
    close_execution_runtime,
    configure_execution_runtime,
)
from python.env_config import VALID_EXECUTION_STEP_RUNTIME_MODES
from python.rl.tasking.bridge import (
    make_rule_based_leader_phase_manager,
    make_scripted_c2_task_manager,
    scripted_c2_task_manager_class,
)
from python.rl.runtime.execution_runtime import coerce_timing_dict
from python.rl.runtime.leader_window_runtime import (
    LeaderDecisionState,
    LocalLeaderWindowRuntime,
    WorldBatchLeaderWindowRuntime,
)

if gym is None:
    class LeaderTrainingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "LeaderTrainingEnv requires the optional dependency 'gymnasium'. "
                "Install it (e.g. `pip install gymnasium`) to run leader-layer training."
            )
else:
    ScriptedC2TaskManager = scripted_c2_task_manager_class()

    class LeaderTrainingEnv(gym.Env):
        """
        Leader-only training environment.

        The leader policy does not emit pilot actions. Instead, it emits high-level command adjustments,
        while a scripted or frozen execution backend flies the aircraft using the existing low-level stack.
        """

        metadata = {"render_modes": ["human"], "render_fps": 20}

        def __init__(
            self,
            scenario_path: str,
            *,
            decision_interval_steps: int = 20,
            execution_backend: str = "scripted",
            execution_train_config: str | None = None,
            execution_model_path: str | None = None,
            execution_algo: str = "auto",
            execution_action_repeat: int = 1,
            scripted_transition_alt_agl_m: float = 140.0,
            heading_bias_limit_deg: float = 45.0,
            altitude_bias_limit_m: float = 800.0,
            speed_bias_limit_mps: float = 40.0,
            command_change_penalty: float = 0.0,
            teacher_keep_deadband: float = 0.20,
            invalid_phase_penalty: float = 0.0,
            premature_approach_penalty: float = 0.0,
            baseline_deviation_penalty: float = 0.0,
            mode_change_penalty: float = 0.0,
            approach_gate_distance_m: float = 18000.0,
            approach_gate_cross_m: float = 3500.0,
            approach_gate_heading_error_deg: float = 85.0,
            execution_torch_threads: int | None = None,
            execution_torch_interop_threads: int | None = None,
            execution_device: str = "cpu",
            execution_use_autocast: bool = False,
            execution_step_runtime_mode: str | None = None,
            execution_world_batch_runtime: bool = False,
            execution_world_batch_threads: int | None = None,
            execution_runtime: Any | None = None,
            collect_step_timing: bool = False,
        ):
            super().__init__()
            self.scenario_path = os.path.abspath(str(scenario_path))
            self.decision_interval_steps = max(1, int(decision_interval_steps))
            self.execution_backend = str(execution_backend).strip().lower() or "scripted"
            self.execution_train_config = (
                None if not execution_train_config else os.path.abspath(str(execution_train_config))
            )
            self.execution_model_path = None if not execution_model_path else os.path.abspath(str(execution_model_path))
            self.execution_algo = str(execution_algo or "auto")
            self.execution_action_repeat = max(1, int(execution_action_repeat))
            self.scripted_transition_alt_agl_m = max(10.0, float(scripted_transition_alt_agl_m))
            self.heading_bias_limit_deg = max(0.0, float(heading_bias_limit_deg))
            self.altitude_bias_limit_m = max(0.0, float(altitude_bias_limit_m))
            self.speed_bias_limit_mps = max(0.0, float(speed_bias_limit_mps))
            self.command_change_penalty = float(command_change_penalty)
            self.teacher_keep_deadband = float(np.clip(float(teacher_keep_deadband), 0.0, 0.95))
            self.invalid_phase_penalty = float(invalid_phase_penalty)
            self.premature_approach_penalty = float(premature_approach_penalty)
            self.baseline_deviation_penalty = float(baseline_deviation_penalty)
            self.mode_change_penalty = float(mode_change_penalty)
            self.approach_gate_distance_m = max(500.0, float(approach_gate_distance_m))
            self.approach_gate_cross_m = max(100.0, float(approach_gate_cross_m))
            self.approach_gate_heading_error_deg = max(5.0, float(approach_gate_heading_error_deg))
            self.execution_torch_threads = (
                None if execution_torch_threads is None else max(1, int(execution_torch_threads))
            )
            self.execution_torch_interop_threads = (
                None
                if execution_torch_interop_threads is None
                else max(1, int(execution_torch_interop_threads))
            )
            self.execution_device = str(execution_device or "cpu")
            self.execution_use_autocast = bool(execution_use_autocast)
            self.execution_step_runtime_mode = (
                None if execution_step_runtime_mode is None else str(execution_step_runtime_mode).strip().lower()
            )
            self.execution_world_batch_runtime = bool(execution_world_batch_runtime)
            self.execution_world_batch_threads = (
                None if execution_world_batch_threads is None else max(0, int(execution_world_batch_threads))
            )
            if (
                self.execution_step_runtime_mode is not None
                and self.execution_step_runtime_mode not in VALID_EXECUTION_STEP_RUNTIME_MODES
            ):
                raise ValueError(
                    f"Unknown execution_step_runtime_mode: {execution_step_runtime_mode!r}"
                )
            self.collect_step_timing = bool(collect_step_timing)
            self._execution_env_settings: dict[str, Any] = {}
            self._execution_wrapper_class = None
            self._execution_wrapper_kwargs: dict[str, Any] | None = None
            self.last_reset_timing: dict[str, float] = {}
            self.last_step_timing: dict[str, float] = {}

            self._exec_runtime = (
                execution_runtime
                if execution_runtime is not None
                else self._build_execution_runtime()
            )
            self._exec_policy = self._build_execution_policy()
            tasking_loader = getattr(self.unwrapped, "loader", None)
            self._teacher_manager = make_rule_based_leader_phase_manager(tasking_loader)
            self._c2_manager = make_scripted_c2_task_manager(tasking_loader)
            self._bridge = LeaderCommandBridge()
            self._last_exec_obs = None
            self._last_exec_inst = None
            self._last_exec_truth = None
            self._last_exec_action: np.ndarray | None = None
            self._exec_action_repeat_remaining = 0
            self._last_effective_execution_action_repeat = 1
            self._defer_kernel_command_sync = False
            self._kernel_command_sync_dirty = False
            self._last_leader_command: tuple[int, float, float, float] | None = None
            self._last_leader_mode = "teacher"
            self._last_requested_bucket = "teacher"
            self._last_baseline_snapshot: dict[str, Any] = {}
            self._last_c2_info: dict[str, Any] = {}
            self._pending_leader_state: LeaderDecisionState | None = None
            self._leader_window_runtime = self._build_default_leader_window_runtime()

            self.action_space = spaces.Box(
                low=np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0], dtype=np.float32),
                high=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                dtype=np.float32,
            )
            self.observation_space = spaces.Dict(
                {
                    "ownship": spaces.Box(low=-np.inf, high=np.inf, shape=(12,), dtype=np.float32),
                    "task": spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),
                    "navigation": spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32),
                    "terminal": spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32),
                    "link": spaces.Box(low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32),
                }
            )

        @property
        def unwrapped(self):
            return self._exec_runtime.unwrapped

        def _build_default_leader_window_runtime(self):
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

        def _decode_action(self, action: np.ndarray) -> LeaderActionMapping:
            return decode_action(self, action)

        @staticmethod
        def _mapping_has_bias(mapping: LeaderActionMapping) -> bool:
            return mapping_has_bias(mapping)

        @staticmethod
        def _zero_mapping_biases(mapping: LeaderActionMapping) -> LeaderActionMapping:
            return zero_mapping_biases(mapping)

        @staticmethod
        def _bucket_allows_command_bias(phase_bucket: str) -> bool:
            return bucket_allows_command_bias(phase_bucket)

        def _resolve_report_type(self, mapping: LeaderActionMapping, *, phase_bucket: str):
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
            mapping: LeaderActionMapping,
            baseline: dict[str, Any],
        ) -> tuple[LeaderActionMapping, dict[str, Any]]:
            return sanitize_action_mapping(self, mapping=mapping, baseline=baseline)

        def _apply_leader_command(self, *, mapping: LeaderActionMapping, baseline: dict[str, Any]) -> None:
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
