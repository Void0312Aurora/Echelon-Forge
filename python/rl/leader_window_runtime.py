from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from python.rl.execution_runtime import coerce_timing_dict


def _wrap_deg(angle_deg: float) -> float:
    return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


@dataclass
class LeaderDecisionState:
    mapping: Any
    guard_info: dict[str, Any]
    prev_mode: str
    exec_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    last_info: dict[str, Any] = field(default_factory=dict)
    decision_c2_transitioned: bool = False
    decision_c2_transition_reason: str = ""
    timing: dict[str, float] = field(default_factory=dict)
    execution_step_count: int = 0
    decision_started_at: float = 0.0


class LeaderWindowRuntimeAdapter:
    """
    Compatibility boundary for one leader decision window.

    The current implementation is still Python-based, but the env and vec backends now talk
    to this interface instead of reaching directly into the env's window orchestration methods.
    That keeps the next compiled runtime step scoped to a single replaceable boundary.
    """

    def begin(self, action: Any) -> None:
        raise NotImplementedError

    def has_pending_execution_step(self) -> bool:
        raise NotImplementedError

    def decision_state(self) -> Any | None:
        return None

    def borrow_execution_observation(self) -> dict[str, Any]:
        raise NotImplementedError

    def current_execution_observation(self) -> dict[str, Any]:
        return dict(self.borrow_execution_observation())

    def predict_execution_action(self, obs: dict[str, Any]):
        raise NotImplementedError

    def prepare_shared_execution_action(self, exec_action: Any):
        raise NotImplementedError

    def step_execution_once(self, exec_action: Any) -> None:
        raise NotImplementedError

    def rollout(self, *, max_steps: int | None = None) -> int:
        raise NotImplementedError

    def apply_execution_step_result(
        self,
        obs: Any,
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Any,
        *,
        prepared_action_state: Any = None,
    ) -> None:
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError

    def run_step(self, action: Any):
        self.begin(action)
        self.rollout()
        return self.finish()


class LocalLeaderWindowRuntime(LeaderWindowRuntimeAdapter):
    def __init__(self, env: Any) -> None:
        self.env = env
        self._pending_state: LeaderDecisionState | Any | None = None

    def _set_state(self, state: LeaderDecisionState | Any | None) -> None:
        self._pending_state = state
        try:
            self.env._pending_leader_state = state
        except Exception:
            pass

    def _state(self) -> LeaderDecisionState | Any | None:
        if self._pending_state is not None:
            return self._pending_state
        return getattr(self.env, "_pending_leader_state", None)

    def decision_state(self) -> LeaderDecisionState | Any | None:
        return self._state()

    def begin(self, action: Any) -> None:
        env = self.env
        if self._state() is not None:
            raise RuntimeError("LeaderTrainingEnv already has a pending batched leader step")
        collect_step_timing = bool(getattr(env, "collect_step_timing", False))
        decision_t0 = time.perf_counter() if collect_step_timing else 0.0
        decode_t0 = time.perf_counter() if collect_step_timing else 0.0
        action = env._normalize_leader_action(action)
        mapping = env._decode_action(action)
        action_decode_ms = (time.perf_counter() - decode_t0) * 1000.0 if collect_step_timing else 0.0
        env._last_exec_action = None
        env._exec_action_repeat_remaining = 0
        env._last_effective_execution_action_repeat = 1

        c2_pre_t0 = time.perf_counter() if collect_step_timing else 0.0
        env._update_scripted_c2()
        c2_pre_ms = (time.perf_counter() - c2_pre_t0) * 1000.0 if collect_step_timing else 0.0
        decision_c2_transitioned = bool(env._last_c2_info.get("transitioned", False))
        decision_c2_transition_reason = (
            str(env._last_c2_info.get("transition_reason", "")) if decision_c2_transitioned else ""
        )
        baseline_t0 = time.perf_counter() if collect_step_timing else 0.0
        baseline = env._compute_teacher_baseline()
        teacher_baseline_ms = (time.perf_counter() - baseline_t0) * 1000.0 if collect_step_timing else 0.0
        env._last_baseline_snapshot = baseline
        sanitize_t0 = time.perf_counter() if collect_step_timing else 0.0
        mapping, guard_info = env._sanitize_action_mapping(mapping=mapping, baseline=baseline)
        sanitize_action_ms = (time.perf_counter() - sanitize_t0) * 1000.0 if collect_step_timing else 0.0
        prev_mode = str(env._last_leader_mode)
        apply_t0 = time.perf_counter() if collect_step_timing else 0.0
        env._apply_leader_command(mapping=mapping, baseline=baseline)
        command_apply_ms = (time.perf_counter() - apply_t0) * 1000.0 if collect_step_timing else 0.0
        c2_post_t0 = time.perf_counter() if collect_step_timing else 0.0
        env._update_scripted_c2()
        c2_post_ms = (time.perf_counter() - c2_post_t0) * 1000.0 if collect_step_timing else 0.0
        if bool(env._last_c2_info.get("transitioned", False)):
            decision_c2_transitioned = True
            decision_c2_transition_reason = str(env._last_c2_info.get("transition_reason", ""))

        timing = {}
        if collect_step_timing:
            timing = {
                "action_decode_ms": float(action_decode_ms),
                "c2_pre_ms": float(c2_pre_ms),
                "teacher_baseline_ms": float(teacher_baseline_ms),
                "sanitize_action_ms": float(sanitize_action_ms),
                "command_apply_ms": float(command_apply_ms),
                "c2_post_ms": float(c2_post_ms),
                "decision_setup_ms": float((time.perf_counter() - decision_t0) * 1000.0),
                "execution_action_select_ms": 0.0,
                "execution_prepare_action_ms": 0.0,
                "execution_runtime_step_ms": 0.0,
                "execution_finalize_ms": 0.0,
                "execution_c2_update_ms": 0.0,
            }
        self._set_state(LeaderDecisionState(
            mapping=mapping,
            guard_info=dict(guard_info or {}),
            prev_mode=prev_mode,
            decision_c2_transitioned=decision_c2_transitioned,
            decision_c2_transition_reason=decision_c2_transition_reason,
            timing=timing,
            decision_started_at=decision_t0,
        ))

    def has_pending_execution_step(self) -> bool:
        state = self._state()
        return state is not None and not bool(state.terminated or state.truncated)

    def borrow_execution_observation(self) -> dict[str, Any]:
        if self._state() is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        obs = self.env._last_exec_obs
        return obs if isinstance(obs, dict) else {}

    def predict_execution_action(self, obs: dict[str, Any]):
        return self.env._predict_execution_action(obs)

    def prepare_shared_execution_action(self, exec_action: Any):
        state = self._state()
        collect_step_timing = bool(getattr(self.env, "collect_step_timing", False))
        timing_t0 = time.perf_counter() if collect_step_timing and state is not None else 0.0
        out = self.env._exec_runtime.prepare_action(exec_action)
        if collect_step_timing and state is not None:
            state.timing["execution_prepare_action_ms"] = float(
                state.timing.get("execution_prepare_action_ms", 0.0) + (time.perf_counter() - timing_t0) * 1000.0
            )
        return out

    def _record_finalized_execution_result(
        self,
        obs: Any,
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Any,
    ) -> None:
        env = self.env
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        if state.terminated or state.truncated:
            return
        collect_step_timing = bool(getattr(env, "collect_step_timing", False))
        env._last_exec_obs = obs
        env._cache_execution_runtime_state()
        state.exec_reward += float(reward)
        state.terminated = bool(terminated)
        state.truncated = bool(truncated)
        state.last_info = dict(info or {})
        state.execution_step_count = int(getattr(state, "execution_step_count", 0)) + 1
        c2_t0 = time.perf_counter() if collect_step_timing else 0.0
        env._update_scripted_c2()
        c2_update_ms = (time.perf_counter() - c2_t0) * 1000.0 if collect_step_timing else 0.0
        if bool(env._last_c2_info.get("transitioned", False)):
            state.decision_c2_transitioned = True
            state.decision_c2_transition_reason = str(env._last_c2_info.get("transition_reason", ""))
        if collect_step_timing:
            state.timing["execution_c2_update_ms"] = float(
                state.timing.get("execution_c2_update_ms", 0.0) + c2_update_ms
            )

    def _apply_execution_result(
        self,
        obs: Any,
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Any,
        *,
        prepared_action_state: Any = None,
    ) -> None:
        env = self.env
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        if state.terminated or state.truncated:
            return
        collect_step_timing = bool(getattr(env, "collect_step_timing", False))
        finalize_t0 = time.perf_counter() if collect_step_timing else 0.0
        obs, reward, info = env._exec_runtime.finalize_step_result(
            obs,
            reward,
            info,
            prepared_action_state,
        )
        finalize_ms = (time.perf_counter() - finalize_t0) * 1000.0 if collect_step_timing else 0.0
        self._record_finalized_execution_result(
            obs,
            reward,
            terminated,
            truncated,
            info,
        )
        if collect_step_timing:
            state.timing["execution_finalize_ms"] = float(
                state.timing.get("execution_finalize_ms", 0.0) + finalize_ms
            )

    def step_execution_once(self, exec_action: Any) -> None:
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        if state.terminated or state.truncated:
            return
        collect_step_timing = bool(getattr(self.env, "collect_step_timing", False))
        step_t0 = time.perf_counter() if collect_step_timing else 0.0
        obs, reward, terminated, truncated, info = self.env._exec_runtime.step(
            np.asarray(exec_action, dtype=np.float32).reshape(-1)
        )
        if collect_step_timing:
            state.timing["execution_runtime_step_ms"] = float(
                state.timing.get("execution_runtime_step_ms", 0.0) + (time.perf_counter() - step_t0) * 1000.0
            )
        self._apply_execution_result(
            obs,
            reward,
            terminated,
            truncated,
            info,
            prepared_action_state=None,
        )

    def rollout(self, *, max_steps: int | None = None) -> int:
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        limit = self.env.decision_interval_steps if max_steps is None else max(0, int(max_steps))
        if limit <= 0:
            return 0
        steps = 0
        while steps < limit and self.has_pending_execution_step():
            self.step_execution_once(self.predict_execution_action(self.borrow_execution_observation()))
            steps += 1
        return steps

    def apply_execution_step_result(
        self,
        obs: Any,
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Any,
        *,
        prepared_action_state: Any = None,
    ) -> None:
        self._apply_execution_result(
            obs,
            reward,
            terminated,
            truncated,
            info,
            prepared_action_state=prepared_action_state,
        )

    def finish(self):
        env = self.env
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step to finish")
        loader = env.unwrapped.loader
        collect_step_timing = bool(getattr(env, "collect_step_timing", False))
        reward_t0 = time.perf_counter() if collect_step_timing else 0.0

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
        if env.command_change_penalty != 0.0 and env._last_leader_command is not None:
            current_cmd = env._current_command_tuple()
            change_mag = (
                abs(float(current_cmd[0]) - float(env._last_leader_command[0]))
                + abs(_wrap_deg(float(current_cmd[1]) - float(env._last_leader_command[1]))) / 180.0
                + abs(float(current_cmd[2]) - float(env._last_leader_command[2])) / max(1.0, env.altitude_bias_limit_m)
                + abs(float(current_cmd[3]) - float(env._last_leader_command[3])) / max(1.0, env.speed_bias_limit_mps)
            )
            penalty = float(env.command_change_penalty) * float(change_mag)
            total_reward -= penalty
            reward_terms["command_change_penalty"] = -float(penalty)

        if bool(state.guard_info.get("guarded", False)) and env.invalid_phase_penalty != 0.0:
            total_reward -= float(env.invalid_phase_penalty)
            reward_terms["invalid_phase_penalty"] = -float(env.invalid_phase_penalty)

        if (
            str(state.guard_info.get("reason", "")) == "approach_not_feasible"
            and env.premature_approach_penalty != 0.0
        ):
            total_reward -= float(env.premature_approach_penalty)
            reward_terms["premature_approach_penalty"] = -float(env.premature_approach_penalty)

        if env.baseline_deviation_penalty != 0.0:
            current_cmd = env._current_command_tuple()
            baseline_cmd = (
                int(env._last_baseline_snapshot.get("command_code", 0)),
                float(env._last_baseline_snapshot.get("heading_deg", 0.0)),
                float(env._last_baseline_snapshot.get("altitude_m", 0.0)),
                float(env._last_baseline_snapshot.get("speed_mps", 0.0)),
            )
            deviation_mag = (
                abs(float(current_cmd[0]) - float(baseline_cmd[0]))
                + abs(_wrap_deg(float(current_cmd[1]) - float(baseline_cmd[1]))) / 180.0
                + abs(float(current_cmd[2]) - float(baseline_cmd[2])) / max(1.0, env.altitude_bias_limit_m)
                + abs(float(current_cmd[3]) - float(baseline_cmd[3])) / max(1.0, env.speed_bias_limit_mps)
            )
            penalty = float(env.baseline_deviation_penalty) * float(deviation_mag)
            total_reward -= penalty
            reward_terms["baseline_deviation_penalty"] = -float(penalty)

        if env.mode_change_penalty != 0.0 and str(env._last_leader_mode) != state.prev_mode:
            total_reward -= float(env.mode_change_penalty)
            reward_terms["mode_change_penalty"] = -float(env.mode_change_penalty)

        c2_info = dict(env._last_c2_info or {})
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

        env._last_leader_command = env._current_command_tuple()
        env._last_requested_bucket = str(state.guard_info.get("requested_bucket", state.mapping.phase_bucket))
        reward_finalize_ms = (time.perf_counter() - reward_t0) * 1000.0 if collect_step_timing else 0.0
        obs_t0 = time.perf_counter() if collect_step_timing else 0.0
        leader_obs = env._build_observation()
        obs_build_ms = (time.perf_counter() - obs_t0) * 1000.0 if collect_step_timing else 0.0
        info_t0 = time.perf_counter() if collect_step_timing else 0.0
        info_out = dict(state.last_info)
        execution_timing = coerce_timing_dict(info_out.get("timing"))
        if execution_timing:
            info_out["execution_timing"] = execution_timing
        info_out["leader_phase_bucket"] = str(state.mapping.phase_bucket)
        info_out["leader_requested_phase_bucket"] = str(state.guard_info.get("requested_bucket", state.mapping.phase_bucket))
        info_out["leader_phase_guarded"] = bool(state.guard_info.get("guarded", False))
        info_out["leader_phase_guard_reason"] = str(state.guard_info.get("reason", ""))
        info_out["leader_bias_guarded"] = bool(state.guard_info.get("bias_guarded", False))
        info_out["leader_bias_guard_reason"] = str(state.guard_info.get("bias_guard_reason", ""))
        info_out["leader_terminal_feasible"] = bool(state.guard_info.get("terminal_feasible", False))
        info_out["leader_backend"] = str(env.execution_backend)
        info_out["leader_mode"] = str(env._last_leader_mode)
        info_out["leader_decision_interval_steps"] = int(env.decision_interval_steps)
        info_out["leader_execution_action_repeat"] = int(env._last_effective_execution_action_repeat)
        info_out["leader_effective_command"] = np.asarray(env._last_leader_command, dtype=np.float32)
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
        info_out["leader_low_level_steps"] = int(getattr(state, "execution_step_count", 0))
        info_out["leader_baseline_command"] = np.asarray(
            [
                float(env._last_baseline_snapshot.get("command_code", 0)),
                float(env._last_baseline_snapshot.get("heading_deg", 0.0)),
                float(env._last_baseline_snapshot.get("altitude_m", 0.0)),
                float(env._last_baseline_snapshot.get("speed_mps", 0.0)),
            ],
            dtype=np.float32,
        )
        info_out["leader_reward_terms"] = reward_terms
        if collect_step_timing:
            info_build_ms = (time.perf_counter() - info_t0) * 1000.0
            state.timing["reward_finalize_ms"] = float(
                state.timing.get("reward_finalize_ms", 0.0) + reward_finalize_ms
            )
            state.timing["obs_build_ms"] = float(state.timing.get("obs_build_ms", 0.0) + obs_build_ms)
            state.timing["info_build_ms"] = float(state.timing.get("info_build_ms", 0.0) + info_build_ms)
            state.timing["total_ms"] = float((time.perf_counter() - state.decision_started_at) * 1000.0)
            env.last_step_timing = dict(state.timing)
            info_out["timing"] = dict(env.last_step_timing)
        else:
            env.last_step_timing = {}
        terminated = bool(state.terminated)
        truncated = bool(state.truncated)
        self._set_state(None)
        return leader_obs, float(total_reward), terminated, truncated, info_out


class WorldBatchLeaderWindowRuntime(LocalLeaderWindowRuntime):
    """
    Dedicated decision-window runtime for the single-world WorldBatch execution backend.

    This keeps the leader window on the same coarse-grained boundary as the new execution
    backend, instead of driving it through repeated generic `step()` calls from the env.
    """

    def rollout(self, *, max_steps: int | None = None) -> int:
        state = self._state()
        if state is None:
            raise RuntimeError("LeaderTrainingEnv has no pending leader step")
        limit = self.env.decision_interval_steps if max_steps is None else max(0, int(max_steps))
        if limit <= 0:
            return 0
        execution_runtime = getattr(self.env, "_exec_runtime", None)
        if execution_runtime is None or not hasattr(execution_runtime, "rollout_window"):
            return super().rollout(max_steps=max_steps)
        steps, runtime_timing = execution_runtime.rollout_window(
            initial_obs=self.borrow_execution_observation(),
            predict_action=self.predict_execution_action,
            max_steps=limit,
            on_step_result=self._record_finalized_execution_result,
        )
        if bool(getattr(self.env, "collect_step_timing", False)):
            for key, value in coerce_timing_dict(runtime_timing).items():
                state.timing[key] = float(state.timing.get(key, 0.0) + float(value))
        return int(steps)
