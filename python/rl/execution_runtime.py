from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


def _normalize_runtime_action(action: Any) -> np.ndarray:
    return np.asarray(action, dtype=np.float32).reshape(-1)


def unwrap_nested_env(env: Any) -> Any:
    current = env
    seen: set[int] = set()
    while hasattr(current, "env") and id(current) not in seen:
        seen.add(id(current))
        next_env = getattr(current, "env", None)
        if next_env is None:
            break
        current = next_env
    return current


def coerce_timing_dict(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except Exception:
            pass
    return out


def scale_timing_dict(raw: Any, scale: float) -> dict[str, float]:
    base = coerce_timing_dict(raw)
    if not base:
        return {}
    factor = float(scale)
    return {key: float(value) * factor for key, value in base.items()}


def copy_info_with_scaled_timing(info: Any, scale: float) -> dict[str, Any]:
    out = dict(info or {})
    timing = scale_timing_dict(out.get("timing"), scale)
    if timing:
        out["timing"] = timing
    return out


class ExecutionRuntimeAdapter:
    """
    Thin compatibility layer between LeaderTrainingEnv and concrete execution runtimes.

    Leader code should talk to this interface instead of reaching into wrapper-specific
    `policy_env` helpers directly.
    """

    @property
    def policy_env(self) -> Any:
        raise NotImplementedError

    @property
    def unwrapped(self) -> Any:
        raise NotImplementedError

    def reset_policy_state(self, obs: Any) -> None:
        policy_env = getattr(self, "policy_env", None)
        if policy_env is None or policy_env is self or not hasattr(policy_env, "reset_state"):
            return
        try:
            policy_env.reset_state(obs)
        except Exception:
            pass

    def prepare_action(self, action: Any) -> tuple[np.ndarray, Any]:
        normalized = _normalize_runtime_action(action)
        policy_env = getattr(self, "policy_env", None)
        if policy_env is None or policy_env is self or not hasattr(policy_env, "prepare_action"):
            return normalized, None
        prepared = policy_env.prepare_action(normalized)
        effective = getattr(prepared, "action", normalized)
        return _normalize_runtime_action(effective), prepared

    def finalize_step_result(self, obs: Any, reward: float, info: Any, prepared_action_state: Any = None):
        if prepared_action_state is not None:
            policy_env = getattr(self, "policy_env", None)
            if policy_env is not None and policy_env is not self and hasattr(policy_env, "finalize_step_result"):
                try:
                    return policy_env.finalize_step_result(obs, reward, info, prepared_action_state)
                except Exception:
                    pass
        return obs, float(reward), dict(info or {})

    def get_last_state(self):
        return None, None


class WrappedExecutionRuntimeAdapter(ExecutionRuntimeAdapter):
    def __init__(
        self,
        handle: Any,
        wrapper_class: type,
        wrapper_kwargs: dict[str, Any] | None = None,
        *,
        timing_enabled: Callable[[], bool] | None = None,
    ) -> None:
        self._handle = handle
        self._policy_env = wrapper_class(handle, **(dict(wrapper_kwargs or {}) or {}))
        self._timing_enabled = timing_enabled or (lambda: False)

    def reset(self, *, seed: int | None = None):
        return self._policy_env.reset(seed=seed)

    def step(self, action: Any):
        return self._policy_env.step(action)

    def rollout_window(self, *, initial_obs: Any, predict_action, max_steps: int, on_step_result):
        collect_timing = bool(self._timing_enabled())
        timing = {
            "execution_prepare_action_ms": 0.0,
            "execution_runtime_step_ms": 0.0,
            "execution_finalize_ms": 0.0,
        }
        obs = initial_obs if isinstance(initial_obs, dict) else {}
        steps = 0
        limit = max(0, int(max_steps))
        while steps < limit:
            raw_action = predict_action(obs)
            prepare_t0 = time.perf_counter() if collect_timing else 0.0
            effective_action, prepared_state = self.prepare_action(raw_action)
            if collect_timing:
                timing["execution_prepare_action_ms"] = float(
                    timing.get("execution_prepare_action_ms", 0.0) + (time.perf_counter() - prepare_t0) * 1000.0
                )
            step_t0 = time.perf_counter() if collect_timing else 0.0
            obs_raw, reward_raw, terminated, truncated, info_raw = self._handle.step(effective_action)
            if collect_timing:
                timing["execution_runtime_step_ms"] = float(
                    timing.get("execution_runtime_step_ms", 0.0) + (time.perf_counter() - step_t0) * 1000.0
                )
            finalize_t0 = time.perf_counter() if collect_timing else 0.0
            obs, reward, info = self.finalize_step_result(
                obs_raw,
                reward_raw,
                info_raw,
                prepared_action_state=prepared_state,
            )
            if collect_timing:
                timing["execution_finalize_ms"] = float(
                    timing.get("execution_finalize_ms", 0.0) + (time.perf_counter() - finalize_t0) * 1000.0
                )
            on_step_result(obs, reward, terminated, truncated, info)
            steps += 1
            if bool(terminated or truncated):
                break
        return int(steps), timing

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        if hasattr(self._handle, "set_randomization_overrides"):
            self._handle.set_randomization_overrides(overrides)

    def get_last_state(self):
        if hasattr(self._handle, "get_last_state"):
            return self._handle.get_last_state()
        return super().get_last_state()

    @property
    def policy_env(self) -> Any:
        return self._policy_env

    @property
    def unwrapped(self):
        return self._handle.unwrapped

    def close(self) -> None:
        closer = getattr(self._handle, "close", None)
        if callable(closer):
            closer()


@dataclass
class SingleExecutionRuntime(ExecutionRuntimeAdapter):
    env: Any

    def reset(self, *, seed: int | None = None):
        return self.env.reset(seed=seed)

    def step(self, action: Any):
        return self.env.step(action)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        if hasattr(self.env, "set_randomization_overrides"):
            self.env.set_randomization_overrides(overrides)
            return
        try:
            self.env.env_method("set_randomization_overrides", overrides)
        except Exception:
            pass

    @property
    def policy_env(self) -> Any:
        return self.env

    @property
    def unwrapped(self) -> Any:
        return self.env.unwrapped
