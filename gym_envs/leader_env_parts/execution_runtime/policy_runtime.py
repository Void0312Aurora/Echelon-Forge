from __future__ import annotations

import time
from typing import Any

import ef_py
import numpy as np
import torch

from gym_envs.universal_env import UniversalEnv
from python.env_config import resolve_env_settings
from python.rl.runtime.execution_runtime import SingleExecutionRuntime
from python.rl.runtime.single_world_batch_runtime import build_single_world_batch_execution_runtime
from python.rl.control.wrappers import get_action_wrapper_spec

from ..policy import FrozenExecutionPolicyAdapter, load_policy
from ..scripted_exec import ScriptedExecutiveController


def build_execution_env(env: Any):
    env_settings, wrapper_class, wrapper_kwargs = resolve_execution_env_spec(env)
    return build_execution_env_from_spec(env, env_settings, wrapper_class, wrapper_kwargs)


def build_execution_env_from_spec(env: Any, env_settings, wrapper_class, wrapper_kwargs):
    if env.execution_backend == "scripted" and wrapper_kwargs is not None:
        wrapper_kwargs = dict(wrapper_kwargs)
        wrapper_kwargs["scripted_residual_scale"] = 0.0
        wrapper_kwargs["scripted_residual_alt_breakpoints_m"] = []
        wrapper_kwargs["scripted_residual_alt_scales"] = []
        wrapper_kwargs["action_rate_penalty_coef"] = 0.0

    built_env = UniversalEnv(env.scenario_path, **env_settings)
    if wrapper_class is not None:
        built_env = wrapper_class(built_env, **(wrapper_kwargs or {}))
    return built_env


def build_execution_runtime(env: Any):
    env_settings, wrapper_class, wrapper_kwargs = resolve_execution_env_spec(env)
    if env.execution_world_batch_runtime:
        return build_single_world_batch_execution_runtime(
            scenario_path=env.scenario_path,
            env_settings=env_settings,
            wrapper_class=wrapper_class,
            wrapper_kwargs=wrapper_kwargs,
            worker_threads=env.execution_world_batch_threads,
        )
    return SingleExecutionRuntime(
        build_execution_env_from_spec(env, env_settings, wrapper_class, wrapper_kwargs)
    )


def resolve_execution_env_spec(env: Any):
    exec_cfg = env.load_execution_config()
    env_settings = resolve_env_settings(exec_cfg, env.make_execution_args_stub())
    if env.execution_step_runtime_mode is not None:
        env_settings["execution_step_runtime_mode"] = env.execution_step_runtime_mode
    env_settings["collect_step_timing"] = bool(env.collect_step_timing)
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(exec_cfg)
    env._execution_env_settings = dict(env_settings)
    env._execution_wrapper_class = wrapper_class
    env._execution_wrapper_kwargs = None if wrapper_kwargs is None else dict(wrapper_kwargs)
    return env_settings, wrapper_class, wrapper_kwargs


def build_execution_policy(env: Any):
    configure_execution_runtime(env)
    if env.execution_backend == "scripted":
        return ScriptedExecutiveController(
            env._exec_runtime.policy_env,
            transition_alt_agl_m=env.scripted_transition_alt_agl_m,
        )
    if env.execution_backend == "frozen_model":
        if not env.execution_model_path:
            raise ValueError("LeaderTrainingEnv execution_backend='frozen_model' requires execution_model_path")
        model = load_policy(
            env.execution_model_path,
            algo_name=env.execution_algo,
            device=env.execution_device,
        )
        return FrozenExecutionPolicyAdapter(
            model,
            device=env.execution_device,
            use_autocast=env.execution_use_autocast,
        )
    raise ValueError(f"Unknown execution_backend: {env.execution_backend!r}")


def close_execution_runtime(runtime: Any, *, active_runtime: Any | None = None) -> None:
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


def configure_execution_runtime(env: Any) -> None:
    if env.execution_torch_threads is not None:
        torch.set_num_threads(int(env.execution_torch_threads))
    if env.execution_torch_interop_threads is not None:
        try:
            torch.set_num_interop_threads(int(env.execution_torch_interop_threads))
        except RuntimeError:
            pass


def exec_policy_reset(env: Any, obs: dict) -> None:
    if hasattr(env._exec_policy, "reset"):
        try:
            env._exec_policy.reset(obs)
        except Exception:
            pass


def current_leader_window_state(env: Any):
    runtime = getattr(env, "_leader_window_runtime", None)
    if runtime is not None and hasattr(runtime, "decision_state"):
        try:
            state = runtime.decision_state()
        except Exception:
            state = None
        if state is not None:
            return state
    return getattr(env, "_pending_leader_state", None)


def predict_execution_action(env: Any, obs: dict) -> np.ndarray:
    state = current_leader_window_state(env)
    collect_step_timing = bool(getattr(env, "collect_step_timing", False))
    predict_t0 = time.perf_counter() if collect_step_timing and state is not None else 0.0
    if env._last_exec_action is not None and env._exec_action_repeat_remaining > 0:
        env._exec_action_repeat_remaining -= 1
        action_out = np.asarray(env._last_exec_action, dtype=np.float32).reshape(-1)
    else:
        resolved_repeat = max(1, int(env.execution_action_repeat))
        if env.execution_backend == "scripted":
            action = np.asarray(env._exec_policy.predict(obs), dtype=np.float32).reshape(-1)
        else:
            action, _ = env._exec_policy.predict(obs, deterministic=True)
            action = np.asarray(action, dtype=np.float32).reshape(-1)
        env._last_exec_action = np.asarray(action, dtype=np.float32).reshape(-1)
        env._last_effective_execution_action_repeat = int(resolved_repeat)
        env._exec_action_repeat_remaining = max(0, int(resolved_repeat) - 1)
        action_out = np.asarray(env._last_exec_action, dtype=np.float32).reshape(-1)
    if collect_step_timing and state is not None:
        state.timing["execution_action_select_ms"] = float(
            state.timing.get("execution_action_select_ms", 0.0)
            + (time.perf_counter() - predict_t0) * 1000.0
        )
    return action_out


def current_runtime_last_state(env: Any):
    runtime = getattr(env, "_exec_runtime", None)
    if runtime is not None and hasattr(runtime, "get_last_state"):
        try:
            return runtime.get_last_state()
        except Exception:
            return None, None
    return None, None


def capture_execution_runtime_state(env: Any):
    inst_now, truth_now = current_runtime_last_state(env)
    if inst_now is None:
        try:
            inst_now = env.unwrapped.sim.get_instrument_state(env.unwrapped.agent_id)
        except Exception:
            inst_now = None
    if truth_now is None:
        try:
            truth_now = env.unwrapped.sim.get_agent_observation(env.unwrapped.agent_id)
        except Exception:
            truth_now = None
    return inst_now, truth_now


def cache_execution_runtime_state(env: Any, *, inst_now=None, truth_now=None):
    if inst_now is None or truth_now is None:
        runtime_inst, runtime_truth = current_runtime_last_state(env)
        if inst_now is None:
            inst_now = runtime_inst
        if truth_now is None:
            truth_now = runtime_truth
    if inst_now is None or truth_now is None:
        captured_inst, captured_truth = capture_execution_runtime_state(env)
        if inst_now is None:
            inst_now = captured_inst
        if truth_now is None:
            truth_now = captured_truth
    env._last_exec_inst = inst_now
    env._last_exec_truth = truth_now
    return inst_now, truth_now


def current_execution_runtime_state(env: Any):
    inst_now = env._last_exec_inst
    truth_now = env._last_exec_truth
    if inst_now is None or truth_now is None:
        inst_now, truth_now = cache_execution_runtime_state(env)
    return inst_now, truth_now


def snapshot_leader_state(env: Any) -> dict[str, Any]:
    loader = env.unwrapped.loader
    intent = getattr(loader, "leader_intent", None)
    report = getattr(loader, "pilot_report", None)
    return {
        "phase_id": int(getattr(intent, "phase_id", int(getattr(ef_py.LeaderPhase, "Idle", 0))))
        if intent is not None
        else 0,
        "command_code": int(getattr(intent, "command_code", loader.mission_cmd.get("command_code", 0)))
        if intent is not None
        else int(loader.mission_cmd.get("command_code", 0)),
        "heading_deg": float(
            getattr(intent, "cmd_heading_deg", loader.mission_cmd.get("target_heading", 0.0))
        )
        if intent is not None
        else float(loader.mission_cmd.get("target_heading", 0.0)),
        "altitude_m": float(
            getattr(intent, "cmd_altitude_m", loader.mission_cmd.get("target_altitude", 0.0))
        )
        if intent is not None
        else float(loader.mission_cmd.get("target_altitude", 0.0)),
        "speed_mps": float(
            getattr(intent, "cmd_speed_mps", loader.mission_cmd.get("target_speed", 0.0))
        )
        if intent is not None
        else float(loader.mission_cmd.get("target_speed", 0.0)),
        "report_type": int(getattr(report, "report_type", getattr(ef_py.CommMsgType, "None")))
        if report is not None
        else 0,
    }


def sync_bridge_from_loader(env: Any) -> None:
    loader = env.unwrapped.loader
    env._bridge.set_state(
        task_order=getattr(loader, "task_order", None),
        leader_intent=getattr(loader, "leader_intent", None),
        pilot_report=getattr(loader, "pilot_report", None),
    )
    if bool(getattr(env, "_defer_kernel_command_sync", False)):
        env._kernel_command_sync_dirty = True
        return
    try:
        env._bridge.sync_to_kernel(loader)
    except Exception:
        pass
    env._kernel_command_sync_dirty = False
