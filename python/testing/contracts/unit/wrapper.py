from __future__ import annotations

import copy
import math
from typing import Any

from ..common import ContractSkipped


def run_wrapper_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    if check_kind == "wrapper_scripted_mode_sequence":
        try:
            import gymnasium as gym
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import numpy as np

        import python.rl.control.wrappers as wrappers

        def _deep_apply_patch(target: Any, patch: Any) -> None:
            if not isinstance(patch, dict):
                return
            if isinstance(target, dict):
                for key, value in patch.items():
                    current = target.get(key)
                    if isinstance(value, dict) and current is not None and (isinstance(current, dict) or hasattr(current, "__dict__")):
                        _deep_apply_patch(current, value)
                    else:
                        target[key] = copy.deepcopy(value)
                return
            for key, value in patch.items():
                current = getattr(target, key, None)
                if isinstance(value, dict) and current is not None and (hasattr(current, "__dict__") or isinstance(current, dict)):
                    _deep_apply_patch(current, value)
                else:
                    setattr(target, key, copy.deepcopy(value))

        def _vector_from_spec(value: Any, size: int, *, default: float = 0.0) -> np.ndarray:
            if value is None:
                return np.full((size,), float(default), dtype=np.float32)
            if isinstance(value, (int, float)):
                return np.full((size,), float(value), dtype=np.float32)
            arr = np.asarray(value, dtype=np.float32).reshape(-1)
            if arr.size != size:
                raise ValueError(f"Expected vector of length {size}, got {arr.size}")
            return arr.astype(np.float32, copy=True)

        env_spec = dict(spec.get("env", {}) or {})
        controllers_spec = dict(spec.get("controllers", {}) or {})
        action_dim = int(env_spec.get("action_dim", 4))
        instrument_dim = int(env_spec.get("instrument_dim", 40))
        mission_dim = int(env_spec.get("mission_dim", 8))
        default_mission_values = dict(env_spec.get("default_mission_values", {}) or {})
        default_instrument_values = dict(env_spec.get("default_instrument_values", {}) or {})

        def _build_obs(obs_spec: dict[str, Any] | None) -> dict[str, Any]:
            obs_spec = dict(obs_spec or {})
            instruments = np.zeros((instrument_dim,), dtype=np.float32)
            mission = np.zeros((mission_dim,), dtype=np.float32)
            for idx_str, value in default_instrument_values.items():
                instruments[int(idx_str)] = float(value)
            for idx_str, value in default_mission_values.items():
                mission[int(idx_str)] = float(value)
            if "instrument_values" in obs_spec:
                for idx_str, value in dict(obs_spec.get("instrument_values", {}) or {}).items():
                    instruments[int(idx_str)] = float(value)
            if "mission_values" in obs_spec:
                for idx_str, value in dict(obs_spec.get("mission_values", {}) or {}).items():
                    mission[int(idx_str)] = float(value)
            if "alt_agl" in obs_spec and instrument_dim >= 4:
                instruments[3] = float(obs_spec["alt_agl"])
            if "cmd_code" in obs_spec and mission_dim >= 1:
                mission[0] = float(obs_spec["cmd_code"])
            return {"instruments": instruments, "mission": mission}

        class _DummyLeaderIntent:
            def __init__(self, phase_id: str = "Idle") -> None:
                self.phase_id = str(phase_id)

        class _DummyLoader:
            def __init__(self, loader_spec: dict[str, Any] | None = None) -> None:
                loader_spec = dict(loader_spec or {})
                waypoint_count = int(loader_spec.get("waypoint_count", 0))
                self.waypoints = copy.deepcopy(loader_spec.get("waypoints", [{"x": 0.0, "y": 0.0} for _ in range(waypoint_count)]))
                self.waypoint_idx = int(loader_spec.get("waypoint_idx", 0))
                self.mission_cmd = copy.deepcopy(dict(loader_spec.get("mission_cmd", {}) or {}))
                self.mission_phase_name = str(loader_spec.get("mission_phase_name", ""))
                leader_phase = str(loader_spec.get("leader_intent_phase_id", loader_spec.get("leader_phase_id", "Idle")))
                self.leader_intent = _DummyLeaderIntent(leader_phase)

        class _DummyEnv(gym.Env):
            metadata = {}

            def __init__(self, env_case_spec: dict[str, Any]) -> None:
                super().__init__()
                self.observation_space = gym.spaces.Dict(
                    {
                        "instruments": gym.spaces.Box(low=-1.0e6, high=1.0e6, shape=(instrument_dim,), dtype=np.float32),
                        "mission": gym.spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=np.float32),
                    }
                )
                self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(action_dim,), dtype=np.float32)
                self._loader_spec = dict(env_case_spec.get("loader", {}) or {})
                self._reset_obs_spec = dict(env_case_spec.get("reset_obs", {}) or {})
                self._steps = list(env_case_spec.get("steps", []) or [])
                self.loader = _DummyLoader(self._loader_spec)
                self.last_action = None
                self._phase = 0

            def reset(self, *, seed=None, options=None):
                super().reset(seed=seed)
                self._phase = 0
                self.last_action = None
                self.loader = _DummyLoader(self._loader_spec)
                return _build_obs(self._reset_obs_spec), {}

            def step(self, action):
                if self._phase >= len(self._steps):
                    raise RuntimeError(f"Dummy wrapper regression exhausted scripted steps at index {self._phase}")
                step_spec = dict(self._steps[self._phase] or {})
                self.last_action = np.asarray(action, dtype=np.float32).copy()
                self._phase += 1
                _deep_apply_patch(self.loader, dict(step_spec.get("loader_updates", {}) or {}))
                next_obs = _build_obs(dict(step_spec.get("next_obs", {}) or {}))
                reward = float(step_spec.get("reward", 0.0))
                terminated = bool(step_spec.get("terminated", False))
                truncated = bool(step_spec.get("truncated", False))
                info = dict(step_spec.get("info", {}) or {})
                return next_obs, reward, terminated, truncated, info

        def _make_ctrl_class(action_spec: Any):
            class _StaticCtrl:
                def __init__(self, *, action_dim: int, dt: float = 0.05):
                    self.action_dim = int(action_dim)
                    self.dt = float(dt)
                    self.reset_calls = 0

                def reset(self, obs: dict) -> None:
                    _ = obs
                    self.reset_calls += 1

                def step(self, obs: dict) -> np.ndarray:
                    _ = obs
                    return _vector_from_spec(action_spec, self.action_dim)

            return _StaticCtrl

        controller_attr_map = {
            "takeoff": "_scripted_takeoff_ctrl",
            "stable_flight": "_scripted_stable_ctrl",
            "landing_ils": "_scripted_landing_ctrl",
        }
        orig_takeoff = wrappers.ScriptedTakeoffController
        orig_stable = wrappers.ScriptedStableFlightController
        orig_landing = wrappers.ScriptedLandingController
        wrappers.ScriptedTakeoffController = _make_ctrl_class(controllers_spec.get("takeoff", 0.25))
        wrappers.ScriptedStableFlightController = _make_ctrl_class(controllers_spec.get("stable_flight", 0.75))
        wrappers.ScriptedLandingController = _make_ctrl_class(controllers_spec.get("landing_ils", 0.50))
        try:
            cases = list(spec.get("cases", []) or [])
            if not cases:
                raise ValueError("wrapper_scripted_mode_sequence requires at least one case")
            for case_idx, case in enumerate(cases, start=1):
                case_name = str(case.get("name", f"case_{case_idx}"))
                case_env_spec = copy.deepcopy(env_spec)
                _deep_apply_patch(case_env_spec, dict(case.get("env_overrides", {}) or {}))
                env = _DummyEnv(case_env_spec)
                wrapper_kwargs = dict(case.get("wrapper", {}) or {})
                wrapped = wrappers.MultiTimescaleActionWrapper(env, **wrapper_kwargs)
                wrapped.reset()
                expected_initial_mode = case.get("expected_initial_mode")
                if expected_initial_mode is not None and str(wrapped._scripted_active_mode) != str(expected_initial_mode):
                    return False, (
                        f"{case_name}: expected initial mode {expected_initial_mode!r}, "
                        f"got {wrapped._scripted_active_mode!r}"
                    )
                expected_initial_resets = dict(case.get("expected_initial_reset_counts", {}) or {})
                for mode_name, expected in expected_initial_resets.items():
                    ctrl = getattr(wrapped, controller_attr_map[str(mode_name)], None)
                    if ctrl is None:
                        return False, f"{case_name}: missing controller {mode_name!r} for initial reset check"
                    min_resets = int(dict(expected or {}).get("min", 0))
                    if int(getattr(ctrl, "reset_calls", 0)) < min_resets:
                        return False, (
                            f"{case_name}: controller {mode_name!r} reset_calls "
                            f"{getattr(ctrl, 'reset_calls', 0)} < {min_resets}"
                        )

                rollout = list(case.get("rollout", []) or [])
                for step_idx, step_expect in enumerate(rollout, start=1):
                    action_input = _vector_from_spec(step_expect.get("action_input"), action_dim, default=0.0)
                    _obs, _reward, _terminated, _truncated, _info = wrapped.step(action_input)
                    expected_mode = step_expect.get("expected_mode")
                    if expected_mode is not None and str(wrapped._scripted_active_mode) != str(expected_mode):
                        return False, (
                            f"{case_name}: step {step_idx} expected mode {expected_mode!r}, "
                            f"got {wrapped._scripted_active_mode!r}"
                        )
                    if "expected_action" in step_expect:
                        expected_action = _vector_from_spec(step_expect.get("expected_action"), action_dim)
                        if env.last_action is None or not np.allclose(env.last_action, expected_action, atol=1.0e-6):
                            return False, (
                                f"{case_name}: step {step_idx} expected action "
                                f"{expected_action.tolist()}, got {None if env.last_action is None else env.last_action.tolist()}"
                            )

                expected_resets = dict(case.get("expected_reset_counts", {}) or {})
                for mode_name, expected in expected_resets.items():
                    ctrl = getattr(wrapped, controller_attr_map[str(mode_name)], None)
                    if ctrl is None:
                        return False, f"{case_name}: missing controller {mode_name!r} for reset check"
                    min_resets = int(dict(expected or {}).get("min", 0))
                    if int(getattr(ctrl, "reset_calls", 0)) < min_resets:
                        return False, (
                            f"{case_name}: controller {mode_name!r} reset_calls "
                            f"{getattr(ctrl, 'reset_calls', 0)} < {min_resets}"
                        )
            return True, f"wrapper scripted mode sequence contract passed for {len(cases)} case(s)"
        finally:
            wrappers.ScriptedTakeoffController = orig_takeoff
            wrappers.ScriptedStableFlightController = orig_stable
            wrappers.ScriptedLandingController = orig_landing

    if check_kind == "wrapper_action_processing_sequence":
        try:
            import gymnasium as gym
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import numpy as np

        import python.rl.control.wrappers as wrappers

        def _action_from_spec(action_spec: Any, action_dim: int, *, default: float = 0.0) -> np.ndarray:
            if action_spec is None:
                return np.full((action_dim,), float(default), dtype=np.float32)
            if isinstance(action_spec, (int, float)):
                return np.full((action_dim,), float(action_spec), dtype=np.float32)
            if isinstance(action_spec, dict):
                if "vector" in action_spec:
                    arr = np.asarray(action_spec["vector"], dtype=np.float32).reshape(-1)
                    if arr.size != action_dim:
                        raise ValueError(f"Expected vector of length {action_dim}, got {arr.size}")
                    return arr.astype(np.float32, copy=True)
                values = dict(action_spec.get("values", {}) or {})
                arr = np.full((action_dim,), float(action_spec.get("default", default)), dtype=np.float32)
                for idx_str, value in values.items():
                    arr[int(idx_str)] = float(value)
                return arr
            arr = np.asarray(action_spec, dtype=np.float32).reshape(-1)
            if arr.size != action_dim:
                raise ValueError(f"Expected vector of length {action_dim}, got {arr.size}")
            return arr.astype(np.float32, copy=True)

        class _SimpleDummyEnv(gym.Env):
            metadata = {}

            def __init__(self, env_spec: dict[str, Any]) -> None:
                super().__init__()
                action_dim = int(env_spec.get("action_dim", 17))
                obs_kind = str(env_spec.get("obs_kind", "box")).strip().lower()
                self.action_space = gym.spaces.Box(
                    low=np.asarray(env_spec.get("action_low", np.zeros((action_dim,), dtype=np.float32)), dtype=np.float32).reshape(-1),
                    high=np.asarray(env_spec.get("action_high", np.ones((action_dim,), dtype=np.float32)), dtype=np.float32).reshape(-1),
                    dtype=np.float32,
                )
                if obs_kind == "dict":
                    instrument_dim = int(env_spec.get("instrument_dim", 42))
                    mission_dim = int(env_spec.get("mission_dim", 4))
                    self.observation_space = gym.spaces.Dict(
                        {
                            "instruments": gym.spaces.Box(low=-1.0e6, high=1.0e6, shape=(instrument_dim,), dtype=np.float32),
                            "mission": gym.spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=np.float32),
                        }
                    )
                    self._obs_kind = "dict"
                    self._instrument_dim = instrument_dim
                    self._mission_dim = mission_dim
                else:
                    obs_dim = int(env_spec.get("obs_dim", 1))
                    self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32)
                    self._obs_kind = "box"
                    self._obs_dim = obs_dim
                self.last_action = None

            def _obs(self):
                if self._obs_kind == "dict":
                    return {
                        "instruments": np.zeros((self._instrument_dim,), dtype=np.float32),
                        "mission": np.zeros((self._mission_dim,), dtype=np.float32),
                    }
                return np.zeros((self._obs_dim,), dtype=np.float32)

            def reset(self, *, seed=None, options=None):
                super().reset(seed=seed)
                self.last_action = None
                return self._obs(), {}

            def step(self, action):
                self.last_action = np.asarray(action, dtype=np.float32).copy()
                return self._obs(), 0.0, False, False, {}

        def _make_static_ctrl(action_spec: Any):
            class _StaticCtrl:
                def __init__(self, *, action_dim: int, dt: float = 0.05):
                    self.action_dim = int(action_dim)
                    self.dt = float(dt)

                def reset(self, obs: dict) -> None:
                    _ = obs
                    return None

                def step(self, obs: dict) -> np.ndarray:
                    _ = obs
                    return _action_from_spec(action_spec, self.action_dim)

            return _StaticCtrl

        orig_takeoff = wrappers.ScriptedTakeoffController
        orig_stable = wrappers.ScriptedStableFlightController
        orig_landing = wrappers.ScriptedLandingController
        controllers_spec = dict(spec.get("controllers", {}) or {})
        wrappers.ScriptedTakeoffController = _make_static_ctrl(controllers_spec.get("takeoff", 0.0))
        wrappers.ScriptedStableFlightController = _make_static_ctrl(controllers_spec.get("stable_flight", 0.0))
        wrappers.ScriptedLandingController = _make_static_ctrl(controllers_spec.get("landing_ils", 0.0))
        try:
            cases = list(spec.get("cases", []) or [])
            if not cases:
                raise ValueError("wrapper_action_processing_sequence requires at least one case")
            for case_idx, case in enumerate(cases, start=1):
                case_name = str(case.get("name", f"case_{case_idx}"))
                env = _SimpleDummyEnv(dict(case.get("env", {}) or {}))
                action_dim = int(env.action_space.shape[0])
                wrapped = wrappers.MultiTimescaleActionWrapper(env, **dict(case.get("wrapper", {}) or {}))
                wrapped.reset()
                expected_initial_mode = case.get("expected_initial_mode")
                if expected_initial_mode is not None and str(wrapped._scripted_active_mode) != str(expected_initial_mode):
                    return False, (
                        f"{case_name}: expected initial mode {expected_initial_mode!r}, "
                        f"got {wrapped._scripted_active_mode!r}"
                    )
                for step_idx, step_spec in enumerate(list(case.get("rollout", []) or []), start=1):
                    action_input = _action_from_spec(step_spec.get("action_input"), action_dim, default=0.0)
                    _obs, _reward, _terminated, _truncated, info = wrapped.step(action_input)
                    expected_mode = step_spec.get("expected_mode")
                    if expected_mode is not None and str(wrapped._scripted_active_mode) != str(expected_mode):
                        return False, (
                            f"{case_name}: step {step_idx} expected mode {expected_mode!r}, "
                            f"got {wrapped._scripted_active_mode!r}"
                        )
                    expected_action_values = dict(step_spec.get("expected_action_values", {}) or {})
                    for idx_str, expected_value in expected_action_values.items():
                        idx = int(idx_str)
                        if env.last_action is None:
                            return False, f"{case_name}: step {step_idx} missing last action"
                        actual_value = float(env.last_action[idx])
                        if not math.isclose(actual_value, float(expected_value), rel_tol=1e-6, abs_tol=1e-6):
                            return False, (
                                f"{case_name}: step {step_idx} expected action[{idx}]={expected_value}, "
                                f"got {actual_value}"
                            )
                    expected_info_keys = [str(x) for x in list(step_spec.get("expected_info_keys", []) or [])]
                    for key in expected_info_keys:
                        if key not in dict(info or {}):
                            return False, f"{case_name}: step {step_idx} missing info[{key!r}]"
            return True, f"wrapper action processing contract passed for {len(cases)} case(s)"
        finally:
            wrappers.ScriptedTakeoffController = orig_takeoff
            wrappers.ScriptedStableFlightController = orig_stable
            wrappers.ScriptedLandingController = orig_landing
    return None
