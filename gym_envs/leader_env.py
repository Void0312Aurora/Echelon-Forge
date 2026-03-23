from __future__ import annotations

import glob
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BUILD_DIR = os.path.join(_REPO_ROOT, "build")
if os.path.isdir(_BUILD_DIR) and glob.glob(os.path.join(_BUILD_DIR, "ef_py*.so")):
    sys.path.insert(0, _BUILD_DIR)

import ef_py

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # pragma: no cover
    gym = None
    spaces = None

from gym_envs.universal_env import UniversalEnv
from python.env_config import VALID_EXECUTION_STEP_RUNTIME_MODES, resolve_env_settings
from python.artifact_paths import resolve_artifact_path
from python.rl.common_core_profile import is_patrol_task, is_recover_task, task_observation_codes
from python.rl.leader_tasking import (
    RuleBasedLeaderPhaseManager,
    ScriptedC2TaskManager,
    infer_recovery_approach_type,
    infer_recovery_base_id,
    infer_recovery_runway_id,
    infer_route_ref_id,
)
from python.rl.mission_defs import (
    COMMAND_CODE_LANDING,
    COMMAND_CODE_ROUTE,
    COMMAND_CODE_TAKEOFF,
    COMMAND_CODE_VECTOR,
    normalize_phase_name,
    scripted_mode_for_phase_name,
)
from python.rl.execution_runtime import SingleExecutionRuntime, coerce_timing_dict
from python.rl.leader_window_runtime import (
    LeaderDecisionState,
    LocalLeaderWindowRuntime,
    WorldBatchLeaderWindowRuntime,
)
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.scripted_landing import ScriptedLandingController
from python.rl.scripted_stable_flight import ScriptedStableFlightController
from python.rl.scripted_takeoff import ScriptedTakeoffController
from python.rl.single_world_batch_runtime import build_single_world_batch_execution_runtime
from python.rl.wrappers import get_action_wrapper_spec
from stable_baselines3 import PPO


def _wrap_deg(angle_deg: float) -> float:
    return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


_TASK_ORDER_FIELDS = (
    "task_id",
    "task_type",
    "service_profile",
    "task_family",
    "tactical_unit_type",
    "priority",
    "issuer_id",
    "assignee_id",
    "command_relationship",
    "authority_scope",
    "parent_node_id",
    "task_group_id",
    "supported_node_id",
    "supporting_node_id",
    "role_code",
    "coordination_mode",
    "relative_slot_code",
    "assignee_kind",
    "recovery_site_id",
    "element_id",
    "package_id",
    "lead_aircraft_id",
    "active",
    "issue_time_s",
    "anchor_x_m",
    "anchor_y_m",
    "anchor_z_m",
    "station_type",
    "station_radius_m",
    "station_leg_length_m",
    "station_heading_deg",
    "altitude_block_min_m",
    "altitude_block_max_m",
    "target_altitude_m",
    "speed_min_mps",
    "speed_max_mps",
    "target_speed_mps",
    "entry_condition_code",
    "exit_condition_code",
    "on_station_time_s",
    "fuel_bingo_override_kg",
    "recovery_base_id",
    "recovery_runway_id",
    "recovery_approach_type",
    "formation_template_id",
    "formation_contract_id",
    "formation_role_id",
    "wingman_slot_id",
    "join_policy_id",
    "rejoin_policy_id",
    "mutual_support_mode",
    "support_sector_id",
)

_LEADER_INTENT_FIELDS = (
    "phase_id",
    "element_phase_id",
    "service_profile",
    "task_family",
    "tactical_unit_type",
    "tactical_unit_id",
    "task_group_id",
    "role_code",
    "coordination_mode",
    "relative_slot_code",
    "recovery_site_id",
    "command_code",
    "route_ref_id",
    "recovery_base_id",
    "recovery_runway_id",
    "recovery_approach_type",
    "cmd_heading_deg",
    "cmd_altitude_m",
    "cmd_speed_mps",
    "formation_id",
    "form_offset_x",
    "form_offset_y",
    "form_offset_z",
    "assigned_target_id",
    "authorization_to_fire",
    "formation_mode_id",
    "join_required_flag",
    "rejoin_required_flag",
    "split_flag",
    "support_anchor_x_m",
    "support_anchor_y_m",
    "support_slot_offset_x_m",
    "support_slot_offset_y_m",
    "wingman_command_mode",
    "approach_armed",
    "commit_to_land",
    "abort_flag",
    "active",
)

_PILOT_REPORT_FIELDS = (
    "report_type",
    "sender_id",
    "task_id",
    "service_profile",
    "task_family",
    "tactical_unit_type",
    "tactical_unit_id",
    "task_group_id",
    "role_code",
    "coordination_mode",
    "element_id",
    "phase_id",
    "formation_role_id",
    "timestamp_s",
    "status_value",
    "entity_ref",
    "location_x_m",
    "location_y_m",
    "location_z_m",
    "formation_error_m",
    "bearing_error_deg",
    "closure_mps",
    "separation_m",
    "active",
)


def _clone_task_order(order: Any) -> ef_py.TaskOrder:
    out = ef_py.TaskOrder()
    if order is None:
        return out
    for name in _TASK_ORDER_FIELDS:
        try:
            setattr(out, name, getattr(order, name))
        except Exception:
            pass
    return out


def _clone_leader_intent(intent: Any) -> ef_py.LeaderIntent:
    out = ef_py.LeaderIntent()
    if intent is None:
        return out
    for name in _LEADER_INTENT_FIELDS:
        try:
            setattr(out, name, getattr(intent, name))
        except Exception:
            pass
    return out


def _clone_pilot_report(report: Any) -> ef_py.PilotReport:
    out = ef_py.PilotReport()
    if report is None:
        return out
    for name in _PILOT_REPORT_FIELDS:
        try:
            setattr(out, name, getattr(report, name))
        except Exception:
            pass
    return out


def _load_json_dict(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _make_args_stub() -> Any:
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None
        execution_step_runtime_mode = None

    return _Args()


def _load_policy(model_path: str, algo_name: str = "auto", device: str = "cpu"):
    resolved_path = resolve_artifact_path(model_path) or str(model_path)
    load_path = resolved_path[:-4] if str(resolved_path).endswith(".zip") else str(resolved_path)
    algo_norm = str(algo_name or "auto").strip()
    if algo_norm in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device=device)
        except Exception:
            if algo_norm != "auto":
                raise
    return PPO.load(load_path, device=device)


class _FrozenExecutionPolicyAdapter:
    """
    Thin inference wrapper around a frozen SB3 policy.

    LeaderTrainingEnv was previously calling ``model.predict()`` for every low-level step,
    which repeats observation conversion and policy dispatch in Python. This adapter keeps the
    existing output semantics while using the thinner ``policy.obs_to_tensor()`` +
    ``policy._predict()`` path directly.
    """

    def __init__(self, model: Any, *, device: str = "cpu", use_autocast: bool = False) -> None:
        self.model = model
        self.policy = model.policy
        self.device = str(device or "cpu")
        self.use_autocast = bool(use_autocast)
        self.policy.set_training_mode(False)

    def predict(self, obs: Any, deterministic: bool = True):
        obs_tensor, _ = self.policy.obs_to_tensor(obs)
        if isinstance(obs_tensor, dict):
            obs_tensor = {
                key: value.to(self.device, non_blocking=self.device.startswith("cuda"))
                for key, value in obs_tensor.items()
            }
        else:
            obs_tensor = obs_tensor.to(self.device, non_blocking=self.device.startswith("cuda"))
        autocast_enabled = self.use_autocast and self.device.startswith("cuda")
        with torch.inference_mode(), torch.autocast("cuda", enabled=autocast_enabled):
            actions = self.policy._predict(obs_tensor, deterministic=deterministic)
        actions_np = actions.detach().cpu().numpy()
        if bool(getattr(self.policy, "squash_output", False)):
            actions_np = self.policy.unscale_action(actions_np)
        return np.asarray(actions_np, dtype=np.float32).reshape(-1), None

    def reset(self, obs: Any) -> None:
        if hasattr(self.model, "reset"):
            self.model.reset(obs)
class _LeaderCommandBridge:
    """
    Small bridge object installed into ScenarioLoader to replace the rule-only phase manager.

    The leader training env updates this object with the currently selected task/intention state.
    ScenarioLoader will call `update()/sync_to_kernel()` on every low-level sim step, keeping the
    kernel-side command chain aligned with the externally selected leader command.
    """

    def __init__(self) -> None:
        self.task_order = ef_py.TaskOrder()
        self.leader_intent = ef_py.LeaderIntent()
        self.pilot_report = ef_py.PilotReport()

    def set_state(
        self,
        *,
        task_order: Any,
        leader_intent: Any,
        pilot_report: Any,
    ) -> None:
        self.task_order = _clone_task_order(task_order)
        self.leader_intent = _clone_leader_intent(leader_intent)
        self.pilot_report = _clone_pilot_report(pilot_report)

    def reset(self, loader: Any, sim_time_s: float = 0.0, **kwargs) -> None:
        self.update(loader, sim_time_s=sim_time_s, **kwargs)

    def update(self, loader: Any, sim_time_s: float = 0.0, **kwargs) -> None:
        _ = (sim_time_s, kwargs)
        loader.task_order = _clone_task_order(self.task_order)
        loader.leader_intent = _clone_leader_intent(self.leader_intent)
        loader.pilot_report = _clone_pilot_report(self.pilot_report)

    def sync_to_kernel(self, loader: Any) -> None:
        if getattr(loader, "agent_id", None) is None:
            return
        try:
            if hasattr(loader.sim, "set_task_order"):
                loader.sim.set_task_order(loader.agent_id, _clone_task_order(self.task_order))
        except Exception:
            pass
        try:
            if hasattr(loader.sim, "set_leader_intent"):
                loader.sim.set_leader_intent(loader.agent_id, _clone_leader_intent(self.leader_intent))
        except Exception:
            pass
        try:
            if hasattr(loader.sim, "set_pilot_report"):
                loader.sim.set_pilot_report(loader.agent_id, _clone_pilot_report(self.pilot_report))
        except Exception:
            pass

class _ScriptedExecutiveController:
    def __init__(self, env: Any, *, transition_alt_agl_m: float = 140.0):
        self.env = env
        self.transition_alt_agl_m = float(transition_alt_agl_m)
        self.takeoff_ctrl: ScriptedTakeoffController | None = None
        self.stable_ctrl: ScriptedStableFlightController | None = None
        self.landing_ctrl: ScriptedLandingController | None = None
        self.active_mode = "takeoff"

    @property
    def action_dim(self) -> int:
        return int(self.env.action_space.shape[0])

    def reset(self, obs: dict) -> None:
        dt = 0.05
        try:
            dt = float(getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)())
        except Exception:
            dt = 0.05
        self.takeoff_ctrl = ScriptedTakeoffController(action_dim=self.action_dim, dt=dt)
        self.stable_ctrl = ScriptedStableFlightController(action_dim=self.action_dim, dt=dt)
        self.landing_ctrl = ScriptedLandingController(action_dim=self.action_dim, dt=dt)
        self.active_mode = "takeoff"
        self.takeoff_ctrl.reset(obs)
        self.stable_ctrl.reset(obs)
        self.landing_ctrl.reset(obs)

    def _infer_mode(self, obs: dict) -> str:
        loader = getattr(self.env.unwrapped, "loader", None)
        phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
        if phase_name == "departure":
            try:
                inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
                if inst.size >= 4 and float(inst[3]) >= self.transition_alt_agl_m:
                    return "stable_flight"
            except Exception:
                pass
            return "takeoff"
        mode = scripted_mode_for_phase_name(phase_name)
        if mode:
            return mode

        try:
            mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
            if mission.size >= 1 and int(round(float(mission[0]))) >= COMMAND_CODE_LANDING:
                return "landing_ils"
        except Exception:
            pass
        try:
            inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
            if inst.size >= 4 and float(inst[3]) < self.transition_alt_agl_m:
                return "takeoff"
        except Exception:
            pass
        return "stable_flight"

    def predict(self, obs: dict) -> np.ndarray:
        mode = self._infer_mode(obs)
        if mode != self.active_mode:
            ctrl = self._controller_for_mode(mode)
            if ctrl is not None:
                ctrl.reset(obs)
            self.active_mode = mode
        ctrl = self._controller_for_mode(mode)
        if ctrl is None:
            return np.zeros((self.action_dim,), dtype=np.float32)
        return np.asarray(ctrl.step(obs), dtype=np.float32).reshape(-1)

    def _controller_for_mode(self, mode: str):
        if mode == "landing_ils":
            return self.landing_ctrl
        if mode == "stable_flight":
            return self.stable_ctrl
        return self.takeoff_ctrl


@dataclass(frozen=True)
class _LeaderActionMapping:
    phase_bucket: str
    heading_bias_deg: float
    altitude_bias_m: float
    speed_bias_mps: float
    report_bucket: str
    report_status_value: float


if gym is None:
    class LeaderTrainingEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError(
                "LeaderTrainingEnv requires the optional dependency 'gymnasium'. "
                "Install it (e.g. `pip install gymnasium`) to run leader-layer training."
            )
else:
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
            self._teacher_manager = RuleBasedLeaderPhaseManager()
            self._c2_manager = ScriptedC2TaskManager()
            self._bridge = _LeaderCommandBridge()
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
            env_settings, wrapper_class, wrapper_kwargs = self._resolve_execution_env_spec()
            return self._build_execution_env_from_spec(env_settings, wrapper_class, wrapper_kwargs)

        def _build_execution_env_from_spec(self, env_settings, wrapper_class, wrapper_kwargs):
            if self.execution_backend == "scripted" and wrapper_kwargs is not None:
                wrapper_kwargs = dict(wrapper_kwargs)
                wrapper_kwargs["scripted_residual_scale"] = 0.0
                wrapper_kwargs["scripted_residual_alt_breakpoints_m"] = []
                wrapper_kwargs["scripted_residual_alt_scales"] = []
                wrapper_kwargs["action_rate_penalty_coef"] = 0.0

            env = UniversalEnv(self.scenario_path, **env_settings)
            if wrapper_class is not None:
                env = wrapper_class(env, **(wrapper_kwargs or {}))
            return env

        def _build_execution_runtime(self):
            env_settings, wrapper_class, wrapper_kwargs = self._resolve_execution_env_spec()
            if self.execution_world_batch_runtime:
                return build_single_world_batch_execution_runtime(
                    scenario_path=self.scenario_path,
                    env_settings=env_settings,
                    wrapper_class=wrapper_class,
                    wrapper_kwargs=wrapper_kwargs,
                    worker_threads=self.execution_world_batch_threads,
                )
            return SingleExecutionRuntime(
                self._build_execution_env_from_spec(env_settings, wrapper_class, wrapper_kwargs)
            )

        def _resolve_execution_env_spec(self):
            exec_cfg = _load_json_dict(self.execution_train_config)
            env_settings = resolve_env_settings(exec_cfg, _make_args_stub())
            if self.execution_step_runtime_mode is not None:
                env_settings["execution_step_runtime_mode"] = self.execution_step_runtime_mode
            env_settings["collect_step_timing"] = bool(self.collect_step_timing)
            wrapper_class, wrapper_kwargs = get_action_wrapper_spec(exec_cfg)
            self._execution_env_settings = dict(env_settings)
            self._execution_wrapper_class = wrapper_class
            self._execution_wrapper_kwargs = None if wrapper_kwargs is None else dict(wrapper_kwargs)
            return env_settings, wrapper_class, wrapper_kwargs

        def _build_execution_policy(self):
            self._configure_execution_runtime()
            if self.execution_backend == "scripted":
                return _ScriptedExecutiveController(
                    self._exec_runtime.policy_env,
                    transition_alt_agl_m=self.scripted_transition_alt_agl_m,
                )
            if self.execution_backend == "frozen_model":
                if not self.execution_model_path:
                    raise ValueError("LeaderTrainingEnv execution_backend='frozen_model' requires execution_model_path")
                model = _load_policy(
                    self.execution_model_path,
                    algo_name=self.execution_algo,
                    device=self.execution_device,
                )
                return _FrozenExecutionPolicyAdapter(
                    model,
                    device=self.execution_device,
                    use_autocast=self.execution_use_autocast,
                )
            raise ValueError(f"Unknown execution_backend: {self.execution_backend!r}")

        def close(self):
            runtime = getattr(self, "_exec_runtime", None)
            self._exec_runtime = None
            self._close_execution_runtime(runtime)
            try:
                super().close()
            except Exception:
                pass

        def _configure_execution_runtime(self) -> None:
            if self.execution_torch_threads is not None:
                torch.set_num_threads(int(self.execution_torch_threads))
            if self.execution_torch_interop_threads is not None:
                try:
                    torch.set_num_interop_threads(int(self.execution_torch_interop_threads))
                except RuntimeError:
                    pass

        def _exec_policy_reset(self, obs: dict) -> None:
            if hasattr(self._exec_policy, "reset"):
                try:
                    self._exec_policy.reset(obs)
                except Exception:
                    pass

        def _current_leader_window_state(self):
            runtime = getattr(self, "_leader_window_runtime", None)
            if runtime is not None and hasattr(runtime, "decision_state"):
                try:
                    state = runtime.decision_state()
                except Exception:
                    state = None
                if state is not None:
                    return state
            return getattr(self, "_pending_leader_state", None)

        def _predict_execution_action(self, obs: dict) -> np.ndarray:
            state = self._current_leader_window_state()
            collect_step_timing = bool(getattr(self, "collect_step_timing", False))
            predict_t0 = time.perf_counter() if collect_step_timing and state is not None else 0.0
            if self._last_exec_action is not None and self._exec_action_repeat_remaining > 0:
                self._exec_action_repeat_remaining -= 1
                action_out = np.asarray(self._last_exec_action, dtype=np.float32).reshape(-1)
            else:
                resolved_repeat = max(1, int(self.execution_action_repeat))
                if self.execution_backend == "scripted":
                    action = np.asarray(self._exec_policy.predict(obs), dtype=np.float32).reshape(-1)
                else:
                    action, _ = self._exec_policy.predict(obs, deterministic=True)
                    action = np.asarray(action, dtype=np.float32).reshape(-1)
                self._last_exec_action = np.asarray(action, dtype=np.float32).reshape(-1)
                self._last_effective_execution_action_repeat = int(resolved_repeat)
                self._exec_action_repeat_remaining = max(0, int(resolved_repeat) - 1)
                action_out = np.asarray(self._last_exec_action, dtype=np.float32).reshape(-1)
            if collect_step_timing and state is not None:
                state.timing["execution_action_select_ms"] = float(
                    state.timing.get("execution_action_select_ms", 0.0) + (time.perf_counter() - predict_t0) * 1000.0
                )
            return action_out

        def _runtime_last_state(self):
            runtime = getattr(self, "_exec_runtime", None)
            if runtime is not None and hasattr(runtime, "get_last_state"):
                try:
                    return runtime.get_last_state()
                except Exception:
                    return None, None
            return None, None

        def _capture_execution_runtime_state(self):
            inst_now, truth_now = self._runtime_last_state()
            if inst_now is None:
                try:
                    inst_now = self.unwrapped.sim.get_instrument_state(self.unwrapped.agent_id)
                except Exception:
                    inst_now = None
            if truth_now is None:
                try:
                    truth_now = self.unwrapped.sim.get_agent_observation(self.unwrapped.agent_id)
                except Exception:
                    truth_now = None
            return inst_now, truth_now

        def _cache_execution_runtime_state(self, *, inst_now=None, truth_now=None):
            if inst_now is None or truth_now is None:
                runtime_inst, runtime_truth = self._runtime_last_state()
                if inst_now is None:
                    inst_now = runtime_inst
                if truth_now is None:
                    truth_now = runtime_truth
            if inst_now is None or truth_now is None:
                captured_inst, captured_truth = self._capture_execution_runtime_state()
                if inst_now is None:
                    inst_now = captured_inst
                if truth_now is None:
                    truth_now = captured_truth
            self._last_exec_inst = inst_now
            self._last_exec_truth = truth_now
            return inst_now, truth_now

        def _current_execution_runtime_state(self):
            inst_now = self._last_exec_inst
            truth_now = self._last_exec_truth
            if inst_now is None or truth_now is None:
                inst_now, truth_now = self._cache_execution_runtime_state()
            return inst_now, truth_now

        def _snapshot_leader_state(self) -> dict[str, Any]:
            loader = self.unwrapped.loader
            intent = getattr(loader, "leader_intent", None)
            report = getattr(loader, "pilot_report", None)
            return {
                "phase_id": int(getattr(intent, "phase_id", int(getattr(ef_py.LeaderPhase, "Idle", 0)))) if intent is not None else 0,
                "command_code": int(getattr(intent, "command_code", loader.mission_cmd.get("command_code", 0))) if intent is not None else int(loader.mission_cmd.get("command_code", 0)),
                "heading_deg": float(getattr(intent, "cmd_heading_deg", loader.mission_cmd.get("target_heading", 0.0))) if intent is not None else float(loader.mission_cmd.get("target_heading", 0.0)),
                "altitude_m": float(getattr(intent, "cmd_altitude_m", loader.mission_cmd.get("target_altitude", 0.0))) if intent is not None else float(loader.mission_cmd.get("target_altitude", 0.0)),
                "speed_mps": float(getattr(intent, "cmd_speed_mps", loader.mission_cmd.get("target_speed", 0.0))) if intent is not None else float(loader.mission_cmd.get("target_speed", 0.0)),
                "report_type": int(getattr(report, "report_type", getattr(ef_py.CommMsgType, "None"))) if report is not None else 0,
            }

        def _sync_bridge_from_loader(self) -> None:
            loader = self.unwrapped.loader
            self._bridge.set_state(
                task_order=getattr(loader, "task_order", None),
                leader_intent=getattr(loader, "leader_intent", None),
                pilot_report=getattr(loader, "pilot_report", None),
            )
            if bool(getattr(self, "_defer_kernel_command_sync", False)):
                self._kernel_command_sync_dirty = True
                return
            try:
                self._bridge.sync_to_kernel(loader)
            except Exception:
                pass
            self._kernel_command_sync_dirty = False

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

        def _decode_action(self, action: np.ndarray) -> _LeaderActionMapping:
            phase_val = float(np.clip(float(action[0]), -1.0, 1.0))
            if abs(phase_val) <= self.teacher_keep_deadband:
                bucket = "teacher"
            elif phase_val <= -0.60:
                bucket = "takeoff"
            elif phase_val <= -0.20:
                bucket = "route"
            elif phase_val <= 0.20:
                bucket = "teacher"
            elif phase_val <= 0.60:
                bucket = "rtb"
            elif phase_val <= 0.85:
                bucket = "approach"
            else:
                bucket = "abort"
            report_val = float(np.clip(float(action[4]), -1.0, 1.0))
            if abs(report_val) <= 0.20:
                report_bucket = "auto"
            elif report_val <= -0.60:
                report_bucket = "wilco"
            elif report_val <= -0.20:
                report_bucket = "on_station"
            elif report_val <= 0.20:
                report_bucket = "auto"
            elif report_val <= 0.60:
                report_bucket = "rtb"
            elif report_val <= 0.85:
                report_bucket = "bingo"
            else:
                report_bucket = "unable"
            return _LeaderActionMapping(
                phase_bucket=str(bucket),
                heading_bias_deg=float(np.clip(float(action[1]), -1.0, 1.0)) * self.heading_bias_limit_deg,
                altitude_bias_m=float(np.clip(float(action[2]), -1.0, 1.0)) * self.altitude_bias_limit_m,
                speed_bias_mps=float(np.clip(float(action[3]), -1.0, 1.0)) * self.speed_bias_limit_mps,
                report_bucket=str(report_bucket),
                report_status_value=float(0.5 * (float(np.clip(float(action[5]), -1.0, 1.0)) + 1.0)),
            )

        @staticmethod
        def _mapping_has_bias(mapping: _LeaderActionMapping) -> bool:
            return (
                abs(float(mapping.heading_bias_deg)) > 1e-6
                or abs(float(mapping.altitude_bias_m)) > 1e-6
                or abs(float(mapping.speed_bias_mps)) > 1e-6
            )

        @staticmethod
        def _zero_mapping_biases(mapping: _LeaderActionMapping) -> _LeaderActionMapping:
            return _LeaderActionMapping(
                phase_bucket=str(mapping.phase_bucket),
                heading_bias_deg=0.0,
                altitude_bias_m=0.0,
                speed_bias_mps=0.0,
                report_bucket=str(mapping.report_bucket),
                report_status_value=float(mapping.report_status_value),
            )

        @staticmethod
        def _bucket_allows_command_bias(phase_bucket: str) -> bool:
            """
            Leader actions should primarily choose mission mode / phase timing.

            Keep continuous heading/altitude/speed trims only on route-like buckets,
            where the command semantics are still "track / stage reference". Teacher,
            takeoff, approach, and abort should not act like a generic vector editor.
            """
            return str(phase_bucket).strip().lower() in {"route", "rtb"}

        def _resolve_report_type(self, mapping: _LeaderActionMapping, *, phase_bucket: str):
            report_bucket = str(mapping.report_bucket)
            if report_bucket == "wilco":
                return getattr(ef_py.CommMsgType, "REP_WILCO")
            if report_bucket == "on_station":
                return getattr(ef_py.CommMsgType, "REP_ON_STATION")
            if report_bucket == "rtb":
                return getattr(ef_py.CommMsgType, "REP_RTB")
            if report_bucket == "bingo":
                return getattr(ef_py.CommMsgType, "WARN_BINGO")
            if report_bucket == "unable":
                return getattr(ef_py.CommMsgType, "REP_UNABLE")

            loader = self.unwrapped.loader
            c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
            task = getattr(loader, "task_order", None)
            if is_patrol_task(task, task_name=c2_task_name):
                try:
                    station_metrics = self._station_metrics(loader)
                except Exception:
                    station_metrics = {"near_station": False}
                if bool(station_metrics.get("near_station", False)):
                    return getattr(ef_py.CommMsgType, "REP_ON_STATION")
            if is_recover_task(task, task_name=c2_task_name):
                return getattr(ef_py.CommMsgType, "REP_RTB")
            if phase_bucket in {"rtb", "approach"}:
                return getattr(ef_py.CommMsgType, "REP_RTB")
            if phase_bucket == "abort":
                return getattr(ef_py.CommMsgType, "REP_UNABLE")
            if phase_bucket == "teacher":
                report = getattr(loader, "pilot_report", None)
                if report is not None and bool(getattr(report, "active", False)):
                    baseline_type = getattr(report, "report_type", getattr(ef_py.CommMsgType, "None"))
                    if int(baseline_type) != int(getattr(ef_py.CommMsgType, "None")):
                        return baseline_type
            return getattr(ef_py.CommMsgType, "REP_WILCO")

        def _fuel_margin_state(self, task: Any, inst: Any) -> tuple[float, float]:
            fuel_total_kg = float(max(0.0, getattr(inst, "fuel_internal", 0.0) + getattr(inst, "fuel_external", 0.0)))
            bingo_kg = float(max(0.0, getattr(task, "fuel_bingo_override_kg", 0.0) if task is not None else 0.0))
            if bingo_kg <= 1.0:
                return fuel_total_kg, 1.0
            margin_frac = float(np.clip((fuel_total_kg - bingo_kg) / max(bingo_kg, 1.0), -1.0, 2.0))
            return fuel_total_kg, margin_frac

        def _terminal_context(self) -> dict[str, float | bool | str]:
            loader = self.unwrapped.loader
            inst, truth = self._current_execution_runtime_state()
            if inst is None or truth is None:
                inst, truth = self._capture_execution_runtime_state()
            phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
            ils = np.asarray(
                loader.get_ils_observation(
                    float(getattr(truth, "x", 0.0)),
                    float(getattr(truth, "y", 0.0)),
                    float(getattr(inst, "alt_baro", 0.0)),
                ),
                dtype=np.float32,
            ).reshape(-1)
            valid_rf, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
            )
            runway_heading_err = 0.0
            try:
                beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
                if beacon is not None:
                    runway_heading_err = _wrap_deg(float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)))
            except Exception:
                runway_heading_err = 0.0
            return {
                "phase_name": str(phase_name),
                "alt_agl_m": float(getattr(inst, "alt_radar", 0.0)),
                "dme_m": float(ils[3]) if ils.size >= 4 else 0.0,
                "loc_dev": float(ils[1]) if ils.size >= 2 else 0.0,
                "gs_dev": float(ils[2]) if ils.size >= 3 else 0.0,
                "valid_runway_frame": bool(valid_rf),
                "along_m": float(along_m if valid_rf else 0.0),
                "cross_m": float(cross_m if valid_rf else 0.0),
                "runway_heading_err_deg": float(runway_heading_err),
            }

        def _terminal_feasible(self, baseline: dict[str, Any], terminal_ctx: dict[str, Any]) -> bool:
            phase_name = str(terminal_ctx.get("phase_name", ""))
            if phase_name in {"approach_armed", "landing_final", "rollout", "abort"}:
                return True
            if int(baseline.get("command_code", 0)) == COMMAND_CODE_LANDING:
                return True
            loader = self.unwrapped.loader
            task = getattr(loader, "task_order", None)
            if (
                is_recover_task(task, task_name=str(getattr(loader, "c2_task_name", "")).strip().upper(), phase_name=phase_name)
                and not self._has_active_waypoints()
            ):
                return True
            if not bool(terminal_ctx.get("valid_runway_frame", False)):
                return False
            dme_m = abs(float(terminal_ctx.get("dme_m", 0.0)))
            cross_m = abs(float(terminal_ctx.get("cross_m", 0.0)))
            heading_err = abs(float(terminal_ctx.get("runway_heading_err_deg", 180.0)))
            along_m = float(terminal_ctx.get("along_m", 0.0))
            return bool(
                along_m >= -1000.0
                and dme_m <= self.approach_gate_distance_m
                and cross_m <= self.approach_gate_cross_m
                and heading_err <= self.approach_gate_heading_error_deg
            )

        def _landing_reference_command(self) -> tuple[float, float, float] | None:
            loader = self.unwrapped.loader
            post = None
            try:
                scenario_data = getattr(loader, "scenario_data", {}) or {}
                mission_cfg = scenario_data.get("mission_command", {}) if isinstance(scenario_data, dict) else {}
                if isinstance(mission_cfg, dict):
                    post = mission_cfg.get("post_waypoint_transition", None)
            except Exception:
                post = None
            if not isinstance(post, dict) or not post:
                post = getattr(loader, "post_waypoint_transition", None)
            if not isinstance(post, dict) or not post:
                return None

            target_heading = float(post.get("target_heading", loader.mission_cmd.get("target_heading", 0.0)))
            if bool(getattr(loader, "rotate_mission_heading_with_world", False)) and abs(float(getattr(loader, "world_yaw_deg", 0.0))) > 1.0e-6:
                target_heading = (target_heading + float(getattr(loader, "world_yaw_deg", 0.0))) % 360.0
            target_altitude = float(post.get("target_altitude", loader.mission_cmd.get("target_altitude", 0.0)))
            target_speed = float(post.get("target_speed", loader.mission_cmd.get("target_speed", 0.0)))
            return float(target_heading), float(target_altitude), float(target_speed)

        def _has_active_waypoints(self) -> bool:
            loader = self.unwrapped.loader
            waypoints = list(getattr(loader, "waypoints", []) or [])
            if not waypoints:
                return False
            waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
            return 0 <= waypoint_idx < len(waypoints)

        def _sanitize_action_mapping(
            self,
            *,
            mapping: _LeaderActionMapping,
            baseline: dict[str, Any],
        ) -> tuple[_LeaderActionMapping, dict[str, Any]]:
            terminal_ctx = self._terminal_context()
            phase_name = str(terminal_ctx.get("phase_name", ""))
            alt_agl_m = float(terminal_ctx.get("alt_agl_m", 0.0))
            requested_bucket = str(mapping.phase_bucket)
            applied_bucket = requested_bucket
            reason = ""
            terminal_feasible = self._terminal_feasible(baseline, terminal_ctx)
            bias_guarded = False
            bias_guard_reason = ""
            loader = self.unwrapped.loader
            c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
            task = getattr(loader, "task_order", None)
            recovery_vector_state = (
                is_recover_task(task, task_name=c2_task_name, phase_name=phase_name)
                and not self._has_active_waypoints()
                and not terminal_feasible
            )

            critical_takeoff = (
                phase_name in {"scramble", "takeoff", "departure"}
                and alt_agl_m < self.scripted_transition_alt_agl_m
            )

            if (
                requested_bucket in {"route", "rtb", "approach", "abort"}
                and critical_takeoff
            ):
                applied_bucket = "teacher"
                reason = "departure_low_altitude"
            elif requested_bucket == "approach" and self._has_active_waypoints():
                applied_bucket = "teacher"
                reason = "approach_before_route_complete"
            elif requested_bucket == "approach" and not terminal_feasible:
                applied_bucket = "teacher"
                reason = "approach_not_feasible"
            elif requested_bucket in {"route", "rtb"} and recovery_vector_state:
                applied_bucket = "teacher"
                reason = "recovery_vector_teacher"
            elif (
                requested_bucket == "abort"
                and phase_name not in {"approach_armed", "landing_final", "rollout", "abort"}
                and not terminal_feasible
            ):
                applied_bucket = "teacher"
                reason = "abort_not_terminal"

            sanitized_mapping = mapping
            if critical_takeoff and self._mapping_has_bias(mapping):
                sanitized_mapping = self._zero_mapping_biases(
                    _LeaderActionMapping(
                        phase_bucket=str(applied_bucket),
                        heading_bias_deg=float(mapping.heading_bias_deg),
                        altitude_bias_m=float(mapping.altitude_bias_m),
                        speed_bias_mps=float(mapping.speed_bias_mps),
                        report_bucket=str(mapping.report_bucket),
                        report_status_value=float(mapping.report_status_value),
                    )
                )
                bias_guarded = True
                bias_guard_reason = "departure_low_altitude"
            elif applied_bucket != requested_bucket:
                sanitized_mapping = _LeaderActionMapping(
                    phase_bucket=str(applied_bucket),
                    heading_bias_deg=float(mapping.heading_bias_deg),
                    altitude_bias_m=float(mapping.altitude_bias_m),
                    speed_bias_mps=float(mapping.speed_bias_mps),
                    report_bucket=str(mapping.report_bucket),
                    report_status_value=float(mapping.report_status_value),
                )

            if self._mapping_has_bias(sanitized_mapping) and not self._bucket_allows_command_bias(applied_bucket):
                sanitized_mapping = self._zero_mapping_biases(sanitized_mapping)
                bias_guarded = True
                if not bias_guard_reason:
                    bias_guard_reason = f"{str(applied_bucket)}_disallows_bias"

            if applied_bucket == requested_bucket:
                return sanitized_mapping, {
                    "requested_bucket": requested_bucket,
                    "guarded": False,
                    "reason": "",
                    "bias_guarded": bias_guarded,
                    "bias_guard_reason": bias_guard_reason,
                    "terminal_feasible": terminal_feasible,
                }
            return (
                sanitized_mapping,
                {
                    "requested_bucket": requested_bucket,
                    "guarded": True,
                    "reason": reason,
                    "bias_guarded": bias_guarded,
                    "bias_guard_reason": bias_guard_reason,
                    "terminal_feasible": terminal_feasible,
                },
            )

        def _apply_leader_command(self, *, mapping: _LeaderActionMapping, baseline: dict[str, Any]) -> None:
            loader = self.unwrapped.loader
            task = _clone_task_order(getattr(loader, "task_order", None))
            intent = _clone_leader_intent(getattr(loader, "leader_intent", None))
            report = _clone_pilot_report(getattr(loader, "pilot_report", None))
            cmd_code = int(baseline.get("command_code", loader.mission_cmd.get("command_code", 0)))
            phase_id = int(baseline.get("phase_id", getattr(ef_py.LeaderPhase, "Idle")))
            heading_deg = float(baseline.get("heading_deg", loader.mission_cmd.get("target_heading", 0.0)))
            altitude_m = float(baseline.get("altitude_m", loader.mission_cmd.get("target_altitude", 0.0)))
            speed_mps = float(baseline.get("speed_mps", loader.mission_cmd.get("target_speed", 0.0)))
            baseline_is_landing = int(cmd_code) == COMMAND_CODE_LANDING
            has_active_waypoints = self._has_active_waypoints()
            route_ref_id = int(getattr(intent, "route_ref_id", 0) or infer_route_ref_id(loader))
            recovery_base_id = int(getattr(intent, "recovery_base_id", 0) or infer_recovery_base_id(loader, task=task))
            recovery_runway_id = int(
                getattr(intent, "recovery_runway_id", 0) or infer_recovery_runway_id(loader, task=task)
            )
            recovery_approach_type = getattr(
                intent,
                "recovery_approach_type",
                infer_recovery_approach_type(loader, task=task),
            )

            if mapping.phase_bucket == "takeoff":
                cmd_code = COMMAND_CODE_TAKEOFF
                phase_id = int(getattr(ef_py.LeaderPhase, "Takeoff"))
            elif mapping.phase_bucket == "route":
                if not baseline_is_landing:
                    cmd_code = COMMAND_CODE_ROUTE
                    phase_id = int(getattr(ef_py.LeaderPhase, "TransitToStation"))
                    route_ref_id = int(infer_route_ref_id(loader)) if int(cmd_code) == COMMAND_CODE_ROUTE else 0
            elif mapping.phase_bucket == "rtb":
                if not baseline_is_landing:
                    cmd_code = COMMAND_CODE_ROUTE
                    phase_id = int(getattr(ef_py.LeaderPhase, "RTB"))
                    route_ref_id = int(infer_route_ref_id(loader)) if int(cmd_code) == COMMAND_CODE_ROUTE else 0
            elif mapping.phase_bucket == "approach":
                cmd_code = COMMAND_CODE_LANDING
                phase_id = int(getattr(ef_py.LeaderPhase, "ApproachArmed"))
                recovery_base_id = int(infer_recovery_base_id(loader, task=task))
                recovery_runway_id = int(infer_recovery_runway_id(loader, task=task))
                recovery_approach_type = infer_recovery_approach_type(loader, task=task)
            elif mapping.phase_bucket == "abort":
                cmd_code = COMMAND_CODE_VECTOR
                phase_id = int(getattr(ef_py.LeaderPhase, "Abort"))
                altitude_m = max(altitude_m, float(getattr(loader.mission_cmd, "target_altitude", altitude_m) if not isinstance(loader.mission_cmd, dict) else loader.mission_cmd.get("target_altitude", altitude_m)))
            report_type = self._resolve_report_type(mapping, phase_bucket=str(mapping.phase_bucket))

            if cmd_code == COMMAND_CODE_LANDING:
                # The leader layer decides *when* to recover, but the frozen execution
                # policy must keep the terminal geometry from the scenario-defined
                # landing transition. Re-applying leader biases here causes heading
                # drift to accumulate across decisions and can pull touchdown off runway.
                landing_ref = self._landing_reference_command()
                if landing_ref is not None:
                    heading_deg, altitude_m, speed_mps = landing_ref
                speed_mps = min(speed_mps, max(70.0, float(loader.mission_cmd.get("target_speed", speed_mps))))
                altitude_m = min(altitude_m, max(0.0, float(loader.mission_cmd.get("target_altitude", altitude_m))))
            elif self._bucket_allows_command_bias(mapping.phase_bucket):
                heading_deg = float((heading_deg + mapping.heading_bias_deg + 360.0) % 360.0)
                altitude_m = self._clip_altitude(task, altitude_m + mapping.altitude_bias_m)
                speed_mps = self._clip_speed(task, speed_mps + mapping.speed_bias_mps)

            if (
                int(cmd_code) == COMMAND_CODE_ROUTE
                and not has_active_waypoints
                and is_recover_task(
                    task,
                    task_name=str(getattr(loader, "c2_task_name", "")).strip().upper(),
                    phase_name=str(getattr(loader, "mission_phase_name", "") or ""),
                )
            ):
                landing_ref = self._landing_reference_command()
                if landing_ref is not None:
                    heading_deg = float(landing_ref[0])

            if int(cmd_code) == COMMAND_CODE_ROUTE and not has_active_waypoints:
                route_ref_id = 0

            intent.phase_id = self._phase_enum_for_id(int(phase_id))
            intent.command_code = int(cmd_code)
            intent.route_ref_id = int(route_ref_id if int(cmd_code) == COMMAND_CODE_ROUTE else 0)
            intent.recovery_base_id = int(recovery_base_id)
            intent.recovery_runway_id = int(recovery_runway_id)
            intent.recovery_approach_type = recovery_approach_type
            intent.cmd_heading_deg = float(heading_deg)
            intent.cmd_altitude_m = float(altitude_m)
            intent.cmd_speed_mps = float(speed_mps)
            intent.approach_armed = bool(cmd_code == COMMAND_CODE_LANDING)
            intent.commit_to_land = bool(cmd_code == COMMAND_CODE_LANDING and mapping.phase_bucket == "approach")
            intent.abort_flag = bool(mapping.phase_bucket == "abort")
            intent.active = True

            try:
                sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
            except Exception:
                sim_time_s = 0.0
            report.report_type = report_type
            report.task_id = int(getattr(task, "task_id", 0))
            report.phase_id = int(self._phase_enum_for_id(int(phase_id)))
            report.sender_id = int(getattr(loader, "agent_id", 0) or 0)
            report.timestamp_s = float(sim_time_s)
            inst_now, truth_now = self._current_execution_runtime_state()
            if int(report_type) == int(getattr(ef_py.CommMsgType, "WARN_BINGO")):
                _fuel_total_kg, fuel_margin_frac = self._fuel_margin_state(task, inst_now)
                report.status_value = float(fuel_margin_frac)
            else:
                report.status_value = float(mapping.report_status_value)
            report.active = True
            if truth_now is not None:
                report.location_x_m = float(getattr(truth_now, "x", 0.0))
                report.location_y_m = float(getattr(truth_now, "y", 0.0))
                report.location_z_m = float(getattr(truth_now, "z", 0.0))

            loader.mission_cmd["command_code"] = int(cmd_code)
            loader.mission_cmd["route_ref_id"] = int(route_ref_id)
            loader.mission_cmd["recovery_base_id"] = int(recovery_base_id)
            loader.mission_cmd["recovery_runway_id"] = int(recovery_runway_id)
            loader.mission_cmd["recovery_approach_type"] = int(recovery_approach_type)
            loader.mission_cmd["target_heading"] = float(heading_deg)
            loader.mission_cmd["target_altitude"] = float(altitude_m)
            loader.mission_cmd["target_speed"] = float(speed_mps)
            loader.mission_phase_name = self._phase_name_for_id(int(phase_id), fallback=mapping.phase_bucket)

            self._bridge.set_state(task_order=task, leader_intent=intent, pilot_report=report)
            self._bridge.update(loader, sim_time_s=sim_time_s)
            if bool(getattr(self, "_defer_kernel_command_sync", False)):
                self._kernel_command_sync_dirty = True
            else:
                try:
                    loader._sync_kernel_mission_command()
                except Exception:
                    pass
            self._sync_bridge_from_loader()
            self._last_leader_mode = str(mapping.phase_bucket)

        def _clip_altitude(self, task: ef_py.TaskOrder, altitude_m: float) -> float:
            lo = float(getattr(task, "altitude_block_min_m", 0.0))
            hi = float(getattr(task, "altitude_block_max_m", 0.0))
            if hi > lo + 1.0:
                return float(np.clip(altitude_m, lo, hi))
            return float(np.clip(altitude_m, 0.0, 12000.0))

        def _clip_speed(self, task: ef_py.TaskOrder, speed_mps: float) -> float:
            lo = float(getattr(task, "speed_min_mps", 0.0))
            hi = float(getattr(task, "speed_max_mps", 0.0))
            if hi > lo + 1.0:
                return float(np.clip(speed_mps, max(40.0, lo), hi))
            return float(np.clip(speed_mps, 60.0, 320.0))

        def _phase_name_for_id(self, phase_id: int, *, fallback: str) -> str:
            mapping = {
                int(getattr(ef_py.LeaderPhase, "Idle")): "idle",
                int(getattr(ef_py.LeaderPhase, "Scramble")): "scramble",
                int(getattr(ef_py.LeaderPhase, "Takeoff")): "takeoff",
                int(getattr(ef_py.LeaderPhase, "Departure")): "departure",
                int(getattr(ef_py.LeaderPhase, "TransitToStation")): "transit_to_station",
                int(getattr(ef_py.LeaderPhase, "EstablishCAP")): "establish_cap",
                int(getattr(ef_py.LeaderPhase, "OnStation")): "on_station",
                int(getattr(ef_py.LeaderPhase, "Reposition")): "reposition",
                int(getattr(ef_py.LeaderPhase, "RTB")): "rtb",
                int(getattr(ef_py.LeaderPhase, "ApproachArmed")): "approach_armed",
                int(getattr(ef_py.LeaderPhase, "LandingFinal")): "landing_final",
                int(getattr(ef_py.LeaderPhase, "Rollout")): "rollout",
                int(getattr(ef_py.LeaderPhase, "Abort")): "abort",
            }
            return str(mapping.get(int(phase_id), str(fallback or "idle")))

        def _phase_enum_for_id(self, phase_id: int):
            phase_name = self._phase_name_for_id(phase_id, fallback="idle")
            attr_map = {
                "idle": "Idle",
                "scramble": "Scramble",
                "takeoff": "Takeoff",
                "departure": "Departure",
                "transit_to_station": "TransitToStation",
                "establish_cap": "EstablishCAP",
                "on_station": "OnStation",
                "reposition": "Reposition",
                "rtb": "RTB",
                "approach_armed": "ApproachArmed",
                "landing_final": "LandingFinal",
                "rollout": "Rollout",
                "abort": "Abort",
            }
            return getattr(ef_py.LeaderPhase, attr_map.get(phase_name, "Idle"))

        def _current_command_tuple(self) -> tuple[int, float, float, float]:
            loader = self.unwrapped.loader
            return (
                int(loader.mission_cmd.get("command_code", 0)),
                float(loader.mission_cmd.get("target_heading", 0.0)),
                float(loader.mission_cmd.get("target_altitude", 0.0)),
                float(loader.mission_cmd.get("target_speed", 0.0)),
            )

        def _build_observation(self) -> dict[str, np.ndarray]:
            loader = self.unwrapped.loader
            inst, truth = self._current_execution_runtime_state()
            if inst is None or truth is None:
                inst, truth = self._capture_execution_runtime_state()
            mission_nav = np.asarray(
                loader.get_mission_observation("nav_v2", truth=truth, inst=inst),
                dtype=np.float32,
            ).reshape(-1)
            ils = np.asarray(
                loader.get_ils_observation(
                    float(getattr(truth, "x", 0.0)),
                    float(getattr(truth, "y", 0.0)),
                    float(getattr(inst, "alt_baro", 0.0)),
                ),
                dtype=np.float32,
            ).reshape(-1)

            report = getattr(loader, "pilot_report", None)
            task = getattr(loader, "task_order", None)
            phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
            phase_id = float(getattr(getattr(loader, "leader_intent", None), "phase_id", 0))
            c2_task_id = float(getattr(loader, "c2_task_id", 0))

            valid_rf, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
            runway_heading_err = 0.0
            try:
                beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
                if beacon is not None:
                    runway_heading_err = _wrap_deg(float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)))
            except Exception:
                runway_heading_err = 0.0

            ownship = np.asarray(
                [
                    float(getattr(inst, "ias", 0.0)),
                    float(getattr(inst, "ground_speed", 0.0)),
                    float(getattr(inst, "alt_radar", 0.0)),
                    float(getattr(inst, "alt_baro", 0.0)),
                    float(getattr(inst, "vvi", 0.0)),
                    float(getattr(inst, "heading", 0.0)),
                    float(getattr(inst, "ground_track", 0.0)),
                    float(getattr(inst, "roll", 0.0)),
                    float(getattr(inst, "pitch", 0.0)),
                    float(getattr(inst, "beta", 0.0)),
                    float(getattr(inst, "r", 0.0)),
                    float(getattr(inst, "gear_pos", 0.0)),
                ],
                dtype=np.float32,
            )
            anchor_dx = float(getattr(task, "anchor_x_m", 0.0) if task is not None else 0.0) - float(getattr(truth, "x", 0.0))
            anchor_dy = float(getattr(task, "anchor_y_m", 0.0) if task is not None else 0.0) - float(getattr(truth, "y", 0.0))
            anchor_dist_m = float(math.hypot(anchor_dx, anchor_dy))
            anchor_bearing_deg = float((math.degrees(math.atan2(anchor_dx, anchor_dy)) + 360.0) % 360.0) if anchor_dist_m > 1.0e-6 else 0.0
            anchor_bearing_rel_deg = float(_wrap_deg(anchor_bearing_deg - float(getattr(inst, "heading", 0.0))))
            fuel_total_kg, fuel_margin_frac = self._fuel_margin_state(task, inst)
            task_primary_code, task_coordination_code, task_unit_code = task_observation_codes(
                task,
                fallback_phase_id=int(phase_id),
            )
            task_vec = np.asarray(
                [
                    float(c2_task_id),
                    float(task_primary_code),
                    float(task_coordination_code),
                    float(task_unit_code),
                    float(loader.mission_cmd.get("target_altitude", 0.0)),
                    float(loader.mission_cmd.get("target_speed", 0.0)),
                    float(anchor_dist_m),
                    float(anchor_bearing_rel_deg),
                    float(max(0.0, float(getattr(task, "on_station_time_s", 0.0) if task is not None else 0.0) - float(getattr(loader, "c2_on_station_elapsed_s", 0.0)))),
                    float(fuel_margin_frac),
                ],
                dtype=np.float32,
            )
            navigation = np.asarray(mission_nav[4:14] if mission_nav.size >= 14 else np.pad(mission_nav[4:], (0, max(0, 10 - max(0, mission_nav.size - 4)))), dtype=np.float32)
            if navigation.size != 10:
                navigation = np.resize(navigation, (10,)).astype(np.float32)

            terminal = np.asarray(
                [
                    float(ils[3]) if ils.size >= 4 else 0.0,
                    float(ils[1]) if ils.size >= 2 else 0.0,
                    float(ils[2]) if ils.size >= 3 else 0.0,
                    float(along_m if valid_rf else 0.0),
                    float(cross_m if valid_rf else 0.0),
                    float(runway_heading_err),
                    1.0 if phase_name in {"approach_armed", "landing_final", "rollout"} else 0.0,
                    1.0 if float(loader.mission_cmd.get("command_code", 0)) >= COMMAND_CODE_LANDING else 0.0,
                ],
                dtype=np.float32,
            )
            link = np.asarray(
                [
                    float(getattr(report, "report_type", 0) if report is not None else 0.0),
                    float(getattr(report, "status_value", 0.0) if report is not None else 0.0),
                    float(max(0.0, getattr(self.unwrapped, "steps", 0) * float(self.unwrapped.sim.get_time_step()) - float(getattr(report, "timestamp_s", 0.0))) if report is not None else 0.0),
                    float(self._fuel_margin_state(task, inst)[1]),
                    float(getattr(inst, "missiles_remaining", 0.0)),
                    float(1.0 if getattr(inst, "rwr_active", False) else 0.0),
                ],
                dtype=np.float32,
            )

            return {
                "ownship": np.nan_to_num(ownship, nan=0.0, posinf=0.0, neginf=0.0),
                "task": np.nan_to_num(task_vec, nan=0.0, posinf=0.0, neginf=0.0),
                "navigation": np.nan_to_num(navigation, nan=0.0, posinf=0.0, neginf=0.0),
                "terminal": np.nan_to_num(terminal, nan=0.0, posinf=0.0, neginf=0.0),
                "link": np.nan_to_num(link, nan=0.0, posinf=0.0, neginf=0.0),
            }
        def _close_execution_runtime(self, runtime: Any, *, active_runtime: Any | None = None) -> None:
            if runtime is None or runtime is active_runtime:
                return
            if hasattr(runtime, "close"):
                try:
                    runtime.close()
                    return
                except Exception:
                    pass
            if isinstance(runtime, SingleExecutionRuntime):
                try:
                    if hasattr(runtime.env, "close"):
                        runtime.env.close()
                except Exception:
                    pass
