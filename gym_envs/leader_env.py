from __future__ import annotations

import os
from typing import Any

import numpy as np

from python.runtime_bootstrap import configure_repo_imports


configure_repo_imports()

import ef_py
import torch

try:
    import gymnasium as gym
    from gymnasium import spaces
except ModuleNotFoundError:  # pragma: no cover
    gym = None
    spaces = None

from gym_envs.leader_env_parts import (
    LeaderCommandBridge,
    LeaderRuntimeFacadeMixin,
)
from python.env_config import VALID_EXECUTION_STEP_RUNTIME_MODES
from python.tasking_contracts.leader_decision_state import LeaderDecisionState
# `make_rule_based_leader_phase_manager`/`make_scripted_c2_task_manager`/
# `scripted_c2_task_manager_class` stay python.rl-resident: they dispatch to
# the air/ground/naval profile modules, a genuine entanglement point (see I24
# report).
from python.rl.tasking.bridge import (
    make_rule_based_leader_phase_manager,
    make_scripted_c2_task_manager,
    scripted_c2_task_manager_class,
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

    class LeaderTrainingEnv(LeaderRuntimeFacadeMixin, gym.Env):
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
            execution_world_batch_runtime: bool = True,
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
