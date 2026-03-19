from __future__ import annotations

import glob
import json
import math
import os
import sys
from dataclasses import dataclass, field
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
from python.env_config import resolve_env_settings
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
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.scripted_landing import ScriptedLandingController
from python.rl.scripted_stable_flight import ScriptedStableFlightController
from python.rl.scripted_takeoff import ScriptedTakeoffController
from python.rl.wrappers import get_action_wrapper_spec
from stable_baselines3 import PPO


def _wrap_deg(angle_deg: float) -> float:
    return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


def _clone_task_order(order: Any) -> ef_py.TaskOrder:
    out = ef_py.TaskOrder()
    if order is None:
        return out
    for name in (
        "task_id",
        "task_type",
        "priority",
        "issuer_id",
        "assignee_id",
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
    ):
        try:
            setattr(out, name, getattr(order, name))
        except Exception:
            pass
    return out


def _clone_leader_intent(intent: Any) -> ef_py.LeaderIntent:
    out = ef_py.LeaderIntent()
    if intent is None:
        return out
    for name in (
        "phase_id",
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
        "approach_armed",
        "commit_to_land",
        "abort_flag",
        "active",
    ):
        try:
            setattr(out, name, getattr(intent, name))
        except Exception:
            pass
    return out


def _clone_pilot_report(report: Any) -> ef_py.PilotReport:
    out = ef_py.PilotReport()
    if report is None:
        return out
    for name in (
        "report_type",
        "sender_id",
        "task_id",
        "phase_id",
        "timestamp_s",
        "status_value",
        "entity_ref",
        "location_x_m",
        "location_y_m",
        "location_z_m",
        "active",
    ):
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

    return _Args()


def _load_policy(model_path: str, algo_name: str = "auto", device: str = "cpu"):
    load_path = model_path[:-4] if str(model_path).endswith(".zip") else str(model_path)
    algo_norm = str(algo_name or "auto").strip()
    if algo_norm in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device=device)
        except Exception:
            if algo_norm != "auto":
                raise
    return PPO.load(load_path, device=device)


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

    def reset(self, loader: Any, sim_time_s: float = 0.0) -> None:
        self.update(loader, sim_time_s=sim_time_s)

    def update(self, loader: Any, sim_time_s: float = 0.0) -> None:
        _ = sim_time_s
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


@dataclass
class _LeaderDecisionState:
    mapping: _LeaderActionMapping
    guard_info: dict[str, Any]
    prev_mode: str
    exec_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    last_info: dict[str, Any] = field(default_factory=dict)
    decision_c2_transitioned: bool = False
    decision_c2_transition_reason: str = ""


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

            self._exec_env = self._build_execution_env()
            self._exec_policy = self._build_execution_policy()
            self._teacher_manager = RuleBasedLeaderPhaseManager()
            self._c2_manager = ScriptedC2TaskManager()
            self._bridge = _LeaderCommandBridge()
            self._last_exec_obs = None
            self._last_leader_command: tuple[int, float, float, float] | None = None
            self._last_leader_mode = "teacher"
            self._last_requested_bucket = "teacher"
            self._last_baseline_snapshot: dict[str, Any] = {}
            self._last_c2_info: dict[str, Any] = {}
            self._pending_leader_state: _LeaderDecisionState | None = None

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
            return self._exec_env.unwrapped

        def set_randomization_overrides(self, overrides: dict | None) -> None:
            if hasattr(self._exec_env, "set_randomization_overrides"):
                self._exec_env.set_randomization_overrides(overrides)
                return
            try:
                self._exec_env.env_method("set_randomization_overrides", overrides)
            except Exception:
                pass

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
            obs, info = self._exec_env.reset(seed=seed)
            self._last_exec_obs = obs
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
            self._last_c2_info = self._c2_manager.reset(loader, sim_time_s=sim_time_s)
            self._last_leader_command = None
            self._last_leader_mode = "teacher"
            self._last_requested_bucket = "teacher"
            self._last_baseline_snapshot = self._snapshot_leader_state()
            self._sync_bridge_from_loader()
            leader_obs = self._build_observation()
            return leader_obs, {"execution_reset_info": info}

        def step(self, action):
            self.begin_batched_leader_step(action)
            for _ in range(self.decision_interval_steps):
                if not self.has_pending_execution_step():
                    break
                exec_action = self._predict_execution_action(self._last_exec_obs)
                self.step_execution_once(exec_action)
            return self.finish_batched_leader_step()

        def _normalize_leader_action(self, action: Any) -> np.ndarray:
            action = np.asarray(action, dtype=np.float32).reshape(-1)
            if action.size == 4:
                # Backward compatibility for previously trained leader models that only emitted
                # mission-command decisions without an explicit report head.
                action = np.concatenate([action, np.zeros((2,), dtype=np.float32)], axis=0)
            if action.size != 6:
                raise ValueError(f"LeaderTrainingEnv expected action shape (4,) or (6,), got {tuple(action.shape)}")
            return action

        def begin_batched_leader_step(self, action: Any) -> None:
            if self._pending_leader_state is not None:
                raise RuntimeError("LeaderTrainingEnv already has a pending batched leader step")
            action = self._normalize_leader_action(action)
            mapping = self._decode_action(action)

            self._update_scripted_c2()
            decision_c2_transitioned = bool(self._last_c2_info.get("transitioned", False))
            decision_c2_transition_reason = (
                str(self._last_c2_info.get("transition_reason", "")) if decision_c2_transitioned else ""
            )
            baseline = self._compute_teacher_baseline()
            self._last_baseline_snapshot = baseline
            mapping, guard_info = self._sanitize_action_mapping(mapping=mapping, baseline=baseline)
            prev_mode = str(self._last_leader_mode)
            self._apply_leader_command(mapping=mapping, baseline=baseline)
            self._update_scripted_c2()
            if bool(self._last_c2_info.get("transitioned", False)):
                decision_c2_transitioned = True
                decision_c2_transition_reason = str(self._last_c2_info.get("transition_reason", ""))

            self._pending_leader_state = _LeaderDecisionState(
                mapping=mapping,
                guard_info=dict(guard_info or {}),
                prev_mode=prev_mode,
                decision_c2_transitioned=decision_c2_transitioned,
                decision_c2_transition_reason=decision_c2_transition_reason,
            )

        def has_pending_execution_step(self) -> bool:
            state = self._pending_leader_state
            return state is not None and not bool(state.terminated or state.truncated)

        def current_execution_observation(self) -> dict[str, Any]:
            if self._pending_leader_state is None:
                raise RuntimeError("LeaderTrainingEnv has no pending leader step")
            return dict(self._last_exec_obs or {})

        def step_execution_once(self, exec_action: Any) -> None:
            state = self._pending_leader_state
            if state is None:
                raise RuntimeError("LeaderTrainingEnv has no pending leader step")
            if state.terminated or state.truncated:
                return
            obs, reward, terminated, truncated, info = self._exec_env.step(np.asarray(exec_action, dtype=np.float32).reshape(-1))
            self._last_exec_obs = obs
            state.exec_reward += float(reward)
            state.terminated = bool(terminated)
            state.truncated = bool(truncated)
            state.last_info = dict(info or {})
            self._update_scripted_c2()
            if bool(self._last_c2_info.get("transitioned", False)):
                state.decision_c2_transitioned = True
                state.decision_c2_transition_reason = str(self._last_c2_info.get("transition_reason", ""))

        def finish_batched_leader_step(self):
            state = self._pending_leader_state
            if state is None:
                raise RuntimeError("LeaderTrainingEnv has no pending leader step to finish")
            loader = self.unwrapped.loader

            reward_terms = {
                "execution_reward": float(state.exec_reward),
                "command_change_penalty": 0.0,
                "invalid_phase_penalty": 0.0,
                "premature_approach_penalty": 0.0,
                "baseline_deviation_penalty": 0.0,
                "mode_change_penalty": 0.0,
                "c2_transition_bonus": 0.0,
                "report_validity_bonus": 0.0,
            }
            total_reward = float(state.exec_reward)
            if self.command_change_penalty != 0.0 and self._last_leader_command is not None:
                current_cmd = self._current_command_tuple()
                change_mag = (
                    abs(float(current_cmd[0]) - float(self._last_leader_command[0]))
                    + abs(_wrap_deg(float(current_cmd[1]) - float(self._last_leader_command[1]))) / 180.0
                    + abs(float(current_cmd[2]) - float(self._last_leader_command[2])) / max(1.0, self.altitude_bias_limit_m)
                    + abs(float(current_cmd[3]) - float(self._last_leader_command[3])) / max(1.0, self.speed_bias_limit_mps)
                )
                penalty = float(self.command_change_penalty) * float(change_mag)
                total_reward -= penalty
                reward_terms["command_change_penalty"] = -float(penalty)

            if bool(state.guard_info.get("guarded", False)) and self.invalid_phase_penalty != 0.0:
                total_reward -= float(self.invalid_phase_penalty)
                reward_terms["invalid_phase_penalty"] = -float(self.invalid_phase_penalty)

            if (
                str(state.guard_info.get("reason", "")) == "approach_not_feasible"
                and self.premature_approach_penalty != 0.0
            ):
                total_reward -= float(self.premature_approach_penalty)
                reward_terms["premature_approach_penalty"] = -float(self.premature_approach_penalty)

            if self.baseline_deviation_penalty != 0.0:
                current_cmd = self._current_command_tuple()
                baseline_cmd = (
                    int(self._last_baseline_snapshot.get("command_code", 0)),
                    float(self._last_baseline_snapshot.get("heading_deg", 0.0)),
                    float(self._last_baseline_snapshot.get("altitude_m", 0.0)),
                    float(self._last_baseline_snapshot.get("speed_mps", 0.0)),
                )
                deviation_mag = (
                    abs(float(current_cmd[0]) - float(baseline_cmd[0]))
                    + abs(_wrap_deg(float(current_cmd[1]) - float(baseline_cmd[1]))) / 180.0
                    + abs(float(current_cmd[2]) - float(baseline_cmd[2])) / max(1.0, self.altitude_bias_limit_m)
                    + abs(float(current_cmd[3]) - float(baseline_cmd[3])) / max(1.0, self.speed_bias_limit_mps)
                )
                penalty = float(self.baseline_deviation_penalty) * float(deviation_mag)
                total_reward -= penalty
                reward_terms["baseline_deviation_penalty"] = -float(penalty)

            if self.mode_change_penalty != 0.0 and str(self._last_leader_mode) != state.prev_mode:
                total_reward -= float(self.mode_change_penalty)
                reward_terms["mode_change_penalty"] = -float(self.mode_change_penalty)

            c2_info = dict(self._last_c2_info or {})
            if state.decision_c2_transitioned:
                c2_info["transitioned"] = True
                c2_info["transition_reason"] = str(state.decision_c2_transition_reason)
            if bool(c2_info.get("report_valid", False)):
                total_reward += 0.02
                reward_terms["report_validity_bonus"] = 0.02
            else:
                report = getattr(loader, "pilot_report", None)
                if report is not None and int(getattr(report, "report_type", 0)) != 0:
                    total_reward -= 0.05
                    reward_terms["report_validity_bonus"] = -0.05

            if bool(c2_info.get("transitioned", False)):
                total_reward += 0.10
                reward_terms["c2_transition_bonus"] = 0.10

            self._last_leader_command = self._current_command_tuple()
            self._last_requested_bucket = str(state.guard_info.get("requested_bucket", state.mapping.phase_bucket))
            leader_obs = self._build_observation()
            info_out = dict(state.last_info)
            info_out["leader_phase_bucket"] = str(state.mapping.phase_bucket)
            info_out["leader_requested_phase_bucket"] = str(state.guard_info.get("requested_bucket", state.mapping.phase_bucket))
            info_out["leader_phase_guarded"] = bool(state.guard_info.get("guarded", False))
            info_out["leader_phase_guard_reason"] = str(state.guard_info.get("reason", ""))
            info_out["leader_bias_guarded"] = bool(state.guard_info.get("bias_guarded", False))
            info_out["leader_bias_guard_reason"] = str(state.guard_info.get("bias_guard_reason", ""))
            info_out["leader_terminal_feasible"] = bool(state.guard_info.get("terminal_feasible", False))
            info_out["leader_backend"] = str(self.execution_backend)
            info_out["leader_mode"] = str(self._last_leader_mode)
            info_out["leader_decision_interval_steps"] = int(self.decision_interval_steps)
            info_out["leader_effective_command"] = np.asarray(self._last_leader_command, dtype=np.float32)
            report = getattr(loader, "pilot_report", None)
            info_out["leader_effective_report"] = np.asarray(
                [
                    float(int(getattr(report, "report_type", 0)) if report is not None else 0.0),
                    float(getattr(report, "status_value", 0.0) if report is not None else 0.0),
                ],
                dtype=np.float32,
            )
            info_out["leader_c2_task_name"] = str(c2_info.get("task_name", getattr(loader, "c2_task_name", "")))
            info_out["leader_c2_task_id"] = int(c2_info.get("task_id", getattr(loader, "c2_task_id", 0)))
            info_out["leader_c2_transitioned"] = bool(c2_info.get("transitioned", False))
            info_out["leader_c2_transition_reason"] = str(c2_info.get("transition_reason", ""))
            info_out["leader_report_valid"] = bool(c2_info.get("report_valid", False))
            info_out["leader_report_reason"] = str(c2_info.get("report_reason", ""))
            info_out["leader_baseline_command"] = np.asarray(
                [
                    float(self._last_baseline_snapshot.get("command_code", 0)),
                    float(self._last_baseline_snapshot.get("heading_deg", 0.0)),
                    float(self._last_baseline_snapshot.get("altitude_m", 0.0)),
                    float(self._last_baseline_snapshot.get("speed_mps", 0.0)),
                ],
                dtype=np.float32,
            )
            info_out["leader_reward_terms"] = reward_terms
            terminated = bool(state.terminated)
            truncated = bool(state.truncated)
            self._pending_leader_state = None
            return leader_obs, float(total_reward), terminated, truncated, info_out

        def _build_execution_env(self):
            exec_cfg = _load_json_dict(self.execution_train_config)
            env_settings = resolve_env_settings(exec_cfg, _make_args_stub())
            wrapper_class, wrapper_kwargs = get_action_wrapper_spec(exec_cfg)
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

        def _build_execution_policy(self):
            self._configure_execution_runtime()
            if self.execution_backend == "scripted":
                return _ScriptedExecutiveController(
                    self._exec_env,
                    transition_alt_agl_m=self.scripted_transition_alt_agl_m,
                )
            if self.execution_backend == "frozen_model":
                if not self.execution_model_path:
                    raise ValueError("LeaderTrainingEnv execution_backend='frozen_model' requires execution_model_path")
                return _load_policy(self.execution_model_path, algo_name=self.execution_algo)
            raise ValueError(f"Unknown execution_backend: {self.execution_backend!r}")

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

        def _predict_execution_action(self, obs: dict) -> np.ndarray:
            if self.execution_backend == "scripted":
                return np.asarray(self._exec_policy.predict(obs), dtype=np.float32).reshape(-1)
            action, _ = self._exec_policy.predict(obs, deterministic=True)
            return np.asarray(action, dtype=np.float32).reshape(-1)

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
            try:
                self._bridge.sync_to_kernel(loader)
            except Exception:
                pass

        def _compute_teacher_baseline(self) -> dict[str, Any]:
            loader = self.unwrapped.loader
            try:
                sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
            except Exception:
                sim_time_s = 0.0
            self._teacher_manager.update(loader, sim_time_s=sim_time_s)
            baseline = self._snapshot_leader_state()
            self._sync_bridge_from_loader()
            return baseline

        def _update_scripted_c2(self) -> dict[str, Any]:
            loader = self.unwrapped.loader
            try:
                sim_time_s = float(self.unwrapped.steps) * float(self.unwrapped.sim.get_time_step())
            except Exception:
                sim_time_s = 0.0
            self._last_c2_info = dict(self._c2_manager.update(loader, sim_time_s=sim_time_s) or {})
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
            if c2_task_name == ScriptedC2TaskManager.TASK_CAP:
                try:
                    station_metrics = self._station_metrics(loader)
                except Exception:
                    station_metrics = {"near_station": False}
                if bool(station_metrics.get("near_station", False)):
                    return getattr(ef_py.CommMsgType, "REP_ON_STATION")
            if c2_task_name in (
                ScriptedC2TaskManager.TASK_RTB,
                ScriptedC2TaskManager.TASK_RECOVER_LAND,
            ):
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
            inst = self.unwrapped.sim.get_instrument_state(self.unwrapped.agent_id)
            truth = self.unwrapped.sim.get_agent_observation(self.unwrapped.agent_id)
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
            elif requested_bucket == "approach" and not terminal_feasible:
                applied_bucket = "teacher"
                reason = "approach_not_feasible"
            elif (
                requested_bucket == "abort"
                and phase_name not in {"approach_armed", "landing_final", "rollout", "abort"}
                and not terminal_feasible
            ):
                applied_bucket = "teacher"
                reason = "abort_not_terminal"

            sanitized_mapping = mapping
            if critical_takeoff and (
                abs(float(mapping.heading_bias_deg)) > 1e-6
                or abs(float(mapping.altitude_bias_m)) > 1e-6
                or abs(float(mapping.speed_bias_mps)) > 1e-6
            ):
                sanitized_mapping = _LeaderActionMapping(
                    phase_bucket=str(applied_bucket),
                    heading_bias_deg=0.0,
                    altitude_bias_m=0.0,
                    speed_bias_mps=0.0,
                    report_bucket=str(mapping.report_bucket),
                    report_status_value=float(mapping.report_status_value),
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
                    cmd_code = COMMAND_CODE_ROUTE if bool(getattr(loader, "waypoints", [])) else COMMAND_CODE_VECTOR
                    phase_id = int(getattr(ef_py.LeaderPhase, "TransitToStation"))
                    route_ref_id = int(infer_route_ref_id(loader))
            elif mapping.phase_bucket == "rtb":
                if not baseline_is_landing:
                    cmd_code = COMMAND_CODE_ROUTE if bool(getattr(loader, "waypoints", [])) else COMMAND_CODE_VECTOR
                    phase_id = int(getattr(ef_py.LeaderPhase, "RTB"))
                    route_ref_id = int(infer_route_ref_id(loader))
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
            else:
                heading_deg = float((heading_deg + mapping.heading_bias_deg + 360.0) % 360.0)
                altitude_m = self._clip_altitude(task, altitude_m + mapping.altitude_bias_m)
                speed_mps = self._clip_speed(task, speed_mps + mapping.speed_bias_mps)

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
            if int(report_type) == int(getattr(ef_py.CommMsgType, "WARN_BINGO")):
                _fuel_total_kg, fuel_margin_frac = self._fuel_margin_state(task, self.unwrapped.sim.get_instrument_state(loader.agent_id))
                report.status_value = float(fuel_margin_frac)
            else:
                report.status_value = float(mapping.report_status_value)
            report.active = True
            try:
                truth = self.unwrapped.sim.get_agent_observation(loader.agent_id)
                report.location_x_m = float(getattr(truth, "x", 0.0))
                report.location_y_m = float(getattr(truth, "y", 0.0))
                report.location_z_m = float(getattr(truth, "z", 0.0))
            except Exception:
                pass

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
            inst = self.unwrapped.sim.get_instrument_state(self.unwrapped.agent_id)
            truth = self.unwrapped.sim.get_agent_observation(self.unwrapped.agent_id)
            mission_nav = np.asarray(loader.get_mission_observation("nav_v2"), dtype=np.float32).reshape(-1)
            ils = np.asarray(
                loader.get_ils_observation(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)), float(getattr(inst, "alt_baro", 0.0))),
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
            task_vec = np.asarray(
                [
                    float(c2_task_id),
                    float(getattr(task, "task_type", 0) if task is not None else 0.0),
                    float(getattr(task, "station_type", 0) if task is not None else 0.0),
                    float(phase_id),
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
