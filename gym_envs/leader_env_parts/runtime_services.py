from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class LeaderRuntimeServices:
    env: Any

    def normalize_leader_action(self, action: Any) -> np.ndarray:
        return self.env._normalize_leader_action(action)

    def decode_action(self, action: np.ndarray):
        return self.env._decode_action(action)

    def sanitize_action_mapping(self, *, mapping: Any, baseline: dict[str, Any]):
        return self.env._sanitize_action_mapping(mapping=mapping, baseline=baseline)

    def apply_leader_command(self, *, mapping: Any, baseline: dict[str, Any]) -> None:
        self.env._apply_leader_command(mapping=mapping, baseline=baseline)

    def predict_execution_action(self, obs: dict[str, Any]) -> np.ndarray:
        return self.env._predict_execution_action(obs)

    def current_command_tuple(self) -> tuple[int, float, float, float]:
        return self.env._current_command_tuple()

    def build_observation(self) -> dict[str, np.ndarray]:
        return self.env._build_observation()

    def compute_teacher_baseline(self) -> dict[str, Any]:
        return self.env._compute_teacher_baseline()

    def update_scripted_c2(self) -> dict[str, Any]:
        return self.env._update_scripted_c2()

    def prepare_execution_action(self, exec_action: Any):
        return self.env._exec_runtime.prepare_action(exec_action)

    def finalize_execution_step_result(
        self,
        obs: Any,
        reward: float,
        info: Any,
        prepared_action_state: Any = None,
    ):
        return self.env._exec_runtime.finalize_step_result(
            obs,
            reward,
            info,
            prepared_action_state,
        )

    def execution_step(self, exec_action: Any):
        return self.env._exec_runtime.step(np.asarray(exec_action, dtype=np.float32).reshape(-1))

    def cache_execution_runtime_state(self) -> None:
        self.env._cache_execution_runtime_state()

    def last_execution_observation(self) -> dict[str, Any]:
        obs = self.env._last_exec_obs
        return obs if isinstance(obs, dict) else {}

    def set_last_execution_observation(self, obs: Any) -> None:
        self.env._last_exec_obs = obs

    def last_c2_info(self) -> dict[str, Any]:
        return dict(self.env._last_c2_info or {})

    def last_baseline_snapshot(self) -> dict[str, Any]:
        return dict(self.env._last_baseline_snapshot or {})

    def set_last_baseline_snapshot(self, baseline: dict[str, Any]) -> None:
        self.env._last_baseline_snapshot = dict(baseline or {})

    def last_leader_mode(self) -> str:
        return str(self.env._last_leader_mode)

    def set_last_leader_command(self, command: tuple[int, float, float, float]) -> None:
        self.env._last_leader_command = command

    def last_leader_command(self):
        return self.env._last_leader_command

    def set_last_requested_bucket(self, bucket: str) -> None:
        self.env._last_requested_bucket = str(bucket)

    def effective_execution_action_repeat(self) -> int:
        return int(self.env._last_effective_execution_action_repeat)

    def reset_execution_action_repeat(self) -> None:
        self.env._last_exec_action = None
        self.env._exec_action_repeat_remaining = 0
        self.env._last_effective_execution_action_repeat = 1

    def collect_step_timing_enabled(self) -> bool:
        return bool(getattr(self.env, "collect_step_timing", False))

    def decision_interval_steps(self) -> int:
        return int(self.env.decision_interval_steps)

    def execution_backend(self) -> str:
        return str(self.env.execution_backend)

    def altitude_bias_limit_m(self) -> float:
        return float(self.env.altitude_bias_limit_m)

    def speed_bias_limit_mps(self) -> float:
        return float(self.env.speed_bias_limit_mps)

    def command_change_penalty(self) -> float:
        return float(self.env.command_change_penalty)

    def invalid_phase_penalty(self) -> float:
        return float(self.env.invalid_phase_penalty)

    def premature_approach_penalty(self) -> float:
        return float(self.env.premature_approach_penalty)

    def baseline_deviation_penalty(self) -> float:
        return float(self.env.baseline_deviation_penalty)

    def mode_change_penalty(self) -> float:
        return float(self.env.mode_change_penalty)

    def unwrapped(self):
        return self.env.unwrapped

    def last_step_timing_set(self, timing: dict[str, float]) -> None:
        self.env.last_step_timing = dict(timing)

    def clear_last_step_timing(self) -> None:
        self.env.last_step_timing = {}


def leader_runtime_services(env: Any) -> LeaderRuntimeServices:
    services = getattr(env, "_leader_runtime_services", None)
    if services is None:
        services = LeaderRuntimeServices(env)
        env._leader_runtime_services = services
    return services
