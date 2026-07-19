from __future__ import annotations

import copy
import math
import os
from typing import Any

from python.angles import bearing_between_deg
from python.artifact_paths import resolve_artifact_path
from python.runtime_bootstrap import resolve_repo_path

from ..common import (
    ContractSkipped,
    _deep_merge,
    _load_json_file,
    _materialize_scenario_path,
    _write_inline_scenario,
    _wrap_deg,
)


def run_leader_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    if check_kind == "leader_training_env":
        try:
            import gymnasium  # noqa: F401
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import numpy as np
        from gym_envs.leader_env import LeaderTrainingEnv

        scenario_path = resolve_repo_path(str(spec["scenario"]))
        leader_cfg = dict(spec.get("leader_env", {}) or {})
        env = LeaderTrainingEnv(
            scenario_path=scenario_path,
            decision_interval_steps=int(leader_cfg.get("decision_interval_steps", 5)),
            execution_backend=str(leader_cfg.get("execution_backend", "scripted")),
            execution_train_config=(
                resolve_repo_path(str(leader_cfg["execution_train_config"]))
                if leader_cfg.get("execution_train_config")
                else None
            ),
            execution_model_path=(
                resolve_repo_path(str(leader_cfg["execution_model_path"]))
                if leader_cfg.get("execution_model_path")
                else None
            ),
            execution_algo=str(leader_cfg.get("execution_algo", "auto")),
            scripted_transition_alt_agl_m=float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
            heading_bias_limit_deg=float(leader_cfg.get("heading_bias_limit_deg", 35.0)),
            altitude_bias_limit_m=float(leader_cfg.get("altitude_bias_limit_m", 600.0)),
            speed_bias_limit_mps=float(leader_cfg.get("speed_bias_limit_mps", 30.0)),
            command_change_penalty=float(leader_cfg.get("command_change_penalty", 0.0)),
            teacher_keep_deadband=float(leader_cfg.get("teacher_keep_deadband", 0.2)),
            invalid_phase_penalty=float(leader_cfg.get("invalid_phase_penalty", 0.0)),
            premature_approach_penalty=float(leader_cfg.get("premature_approach_penalty", 0.0)),
            baseline_deviation_penalty=float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
            mode_change_penalty=float(leader_cfg.get("mode_change_penalty", 0.0)),
            approach_gate_distance_m=float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
            approach_gate_cross_m=float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
            approach_gate_heading_error_deg=float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
        )
        obs, info = env.reset(seed=int(spec.get("seed", 7)))
        expected_obs_shapes = dict(spec.get("expected_obs_shapes", {}) or {})
        for key, shape in expected_obs_shapes.items():
            arr = np.asarray(obs.get(key))
            if tuple(arr.shape) != tuple(shape):
                return False, f"leader obs {key!r} shape mismatch: {tuple(arr.shape)} != {tuple(shape)}"

        action = np.asarray(spec.get("action", [0.0, 0.0, 0.0, 0.0]), dtype=np.float32).reshape(-1)
        obs2, reward, terminated, truncated, info2 = env.step(action)
        if not isinstance(info, dict):
            return False, "leader env reset info should be a dict"
        if not isinstance(info2, dict):
            return False, "leader env step info should be a dict"
        if "leader_effective_command" not in info2:
            return False, "leader_effective_command missing from info"
        eff_cmd = np.asarray(info2["leader_effective_command"], dtype=np.float32).reshape(-1)
        if tuple(eff_cmd.shape) != (4,):
            return False, f"leader_effective_command shape mismatch: {tuple(eff_cmd.shape)}"
        allowed_codes = set(int(x) for x in spec.get("allowed_command_codes", [1, 2, 3, 4]))
        if int(round(float(eff_cmd[0]))) not in allowed_codes:
            return False, f"unexpected effective command code {eff_cmd[0]}"
        if "leader_backend" not in info2:
            return False, "leader_backend missing from info"
        expected_info = dict(spec.get("expected_info", {}) or {})
        for key, expected in expected_info.items():
            if key not in info2:
                return False, f"expected info key missing: {key}"
            actual = info2.get(key)
            if isinstance(expected, bool):
                if bool(actual) != bool(expected):
                    return False, f"info[{key!r}] mismatch: {actual!r} != {expected!r}"
            elif isinstance(expected, (int, float)):
                if not math.isclose(float(actual), float(expected), rel_tol=1e-6, abs_tol=1e-6):
                    return False, f"info[{key!r}] mismatch: {actual!r} != {expected!r}"
            else:
                if str(actual) != str(expected):
                    return False, f"info[{key!r}] mismatch: {actual!r} != {expected!r}"
        reward_term_keys = list(spec.get("expected_reward_term_keys", []) or [])
        if reward_term_keys:
            reward_terms = info2.get("leader_reward_terms", {})
            if not isinstance(reward_terms, dict):
                return False, "leader_reward_terms missing or not a dict"
            for key in reward_term_keys:
                if key not in reward_terms:
                    return False, f"leader_reward_terms missing key: {key}"
        if not isinstance(reward, (float, int)):
            return False, f"leader reward has unexpected type: {type(reward)}"
        if not isinstance(bool(terminated), bool) or not isinstance(bool(truncated), bool):
            return False, "terminated/truncated flags could not be coerced to bool"
        for key, shape in expected_obs_shapes.items():
            arr = np.asarray(obs2.get(key))
            if tuple(arr.shape) != tuple(shape):
                return False, f"post-step leader obs {key!r} shape mismatch: {tuple(arr.shape)} != {tuple(shape)}"
        return True, "leader training env contract passed"

    if check_kind == "leader_policy_generalization":
        try:
            import gymnasium  # noqa: F401
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import concurrent.futures
        import numpy as np
        from stable_baselines3 import PPO
        from gym_envs.leader_env import LeaderTrainingEnv
        from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO

        def _load_leader_policy(model_path: str, algo_name: str):
            resolved_path = resolve_artifact_path(model_path) or str(model_path)
            load_path = resolved_path[:-4] if str(resolved_path).endswith(".zip") else str(resolved_path)
            algo_norm = str(algo_name or "auto").strip()
            if algo_norm in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
                try:
                    return AdaptiveKLPPO.load(load_path, device="cpu")
                except Exception:
                    if algo_norm != "auto":
                        raise
            return PPO.load(load_path, device="cpu")

        def _task_block_ok(value: float, lo: float, hi: float) -> bool:
            if float(hi) > float(lo) + 1.0:
                return bool(float(lo) - 1.0e-6 <= float(value) <= float(hi) + 1.0e-6)
            return True

        def _active_nav_target(loader: Any, task: Any) -> tuple[str | None, float | None, float | None]:
            waypoints = list(getattr(loader, "waypoints", []) or [])
            waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
            if 0 <= waypoint_idx < len(waypoints):
                wp = waypoints[waypoint_idx]
                return "waypoint", float(wp.get("x", 0.0)), float(wp.get("y", 0.0))
            if task is not None and bool(getattr(task, "active", False)):
                return "anchor", float(getattr(task, "anchor_x_m", 0.0)), float(getattr(task, "anchor_y_m", 0.0))
            return None, None, None

        def _scheduled_fallback_action(decision_idx: int) -> np.ndarray:
            action_np = np.asarray(fallback_action, dtype=np.float32).reshape(-1)
            for from_decision, scheduled_action in fallback_schedule:
                if int(decision_idx) >= int(from_decision):
                    action_np = np.asarray(scheduled_action, dtype=np.float32).reshape(-1)
                else:
                    break
            return action_np

        def _collect_leader_snapshot(env: LeaderTrainingEnv, info: dict[str, Any], decision_idx: int) -> dict[str, Any]:
            loader = env.unwrapped.loader
            task = getattr(loader, "task_order", None)
            truth = env.unwrapped.sim.get_agent_observation(env.unwrapped.agent_id)

            command_code = int(loader.mission_cmd.get("command_code", 0))
            heading_deg = float(loader.mission_cmd.get("target_heading", 0.0))
            altitude_m = float(loader.mission_cmd.get("target_altitude", 0.0))
            speed_mps = float(loader.mission_cmd.get("target_speed", 0.0))
            phase_name = str(getattr(loader, "mission_phase_name", "")).strip().lower()
            target_kind, target_x, target_y = _active_nav_target(loader, task)
            heading_err_deg = None
            if target_x is not None and target_y is not None:
                desired_bearing = bearing_between_deg(
                    float(getattr(truth, "x", 0.0)),
                    float(getattr(truth, "y", 0.0)),
                    float(target_x),
                    float(target_y),
                )
                heading_err_deg = abs(_wrap_deg(heading_deg - desired_bearing))

            return {
                "decision_idx": int(decision_idx),
                "phase_name": phase_name,
                "command_code": int(command_code),
                "heading_deg": float(heading_deg),
                "altitude_m": float(altitude_m),
                "speed_mps": float(speed_mps),
                "waypoint_idx": int(getattr(loader, "waypoint_idx", 0) or 0),
                "waypoint_total": int(len(list(getattr(loader, "waypoints", []) or []))),
                "target_kind": target_kind,
                "heading_error_deg": heading_err_deg,
                "terminal_feasible": bool(info.get("leader_terminal_feasible", False)),
                "c2_task_name": str(info.get("leader_c2_task_name", "")),
                "c2_transitioned": bool(info.get("leader_c2_transitioned", False)),
                "c2_transition_reason": str(info.get("leader_c2_transition_reason", "")),
                "report_valid": bool(info.get("leader_report_valid", False)),
                "report_reason": str(info.get("leader_report_reason", "")),
                "altitude_ok": _task_block_ok(
                    altitude_m,
                    float(getattr(task, "altitude_block_min_m", 0.0) if task is not None else 0.0),
                    float(getattr(task, "altitude_block_max_m", 0.0) if task is not None else 0.0),
                ),
                "speed_ok": _task_block_ok(
                    speed_mps,
                    float(getattr(task, "speed_min_mps", 0.0) if task is not None else 0.0),
                    float(getattr(task, "speed_max_mps", 0.0) if task is not None else 0.0),
                ),
            }

        def _validate_leader_case_rollout(
            *,
            case_name: str,
            snapshots: list[dict[str, Any]],
            checks: dict[str, Any],
            final_info: dict[str, Any],
            expected_reason: Any,
        ) -> tuple[bool, str]:
            if not snapshots:
                return False, f"{case_name}: no leader rollout snapshots were collected"

            allowed_codes = set(int(x) for x in checks.get("allowed_command_codes", [1, 2, 3, 4]))
            for snap in snapshots:
                if int(snap["command_code"]) not in allowed_codes:
                    return False, f"{case_name}: unexpected command code {snap['command_code']} at decision {snap['decision_idx']}"

            required_codes = set(int(x) for x in checks.get("required_command_codes", []) or [])
            seen_codes = {int(snap["command_code"]) for snap in snapshots}
            missing = sorted(required_codes - seen_codes)
            if missing:
                return False, f"{case_name}: missing required command codes {missing}, saw {sorted(seen_codes)}"

            phase_expect = {
                str(k).strip().lower(): {int(x) for x in v}
                for k, v in dict(checks.get("phase_command_expectations", {}) or {}).items()
                if isinstance(v, (list, tuple))
            }
            for snap in snapshots:
                allowed = phase_expect.get(str(snap["phase_name"]).strip().lower(), None)
                if allowed is not None and int(snap["command_code"]) not in allowed:
                    return False, (
                        f"{case_name}: phase {snap['phase_name']!r} emitted command code "
                        f"{snap['command_code']} outside allowed set {sorted(allowed)}"
                    )

            if bool(checks.get("require_altitude_within_task_block", False)):
                bad = next((snap for snap in snapshots if not bool(snap["altitude_ok"])), None)
                if bad is not None:
                    return False, f"{case_name}: altitude left task block at decision {bad['decision_idx']}"

            if bool(checks.get("require_speed_within_task_block", False)):
                bad = next((snap for snap in snapshots if not bool(snap["speed_ok"])), None)
                if bad is not None:
                    return False, f"{case_name}: speed left task block at decision {bad['decision_idx']}"

            if bool(checks.get("disallow_landing_before_terminal_feasible", True)):
                bad = next(
                    (
                        snap for snap in snapshots
                        if int(snap["command_code"]) == 4 and not bool(snap["terminal_feasible"])
                    ),
                    None,
                )
                if bad is not None:
                    return False, f"{case_name}: landing command issued before terminal feasibility at decision {bad['decision_idx']}"

            heading_abs_max = checks.get("active_target_heading_abs_max_deg", None)
            if heading_abs_max is not None:
                filter_phases = {str(x).strip().lower() for x in checks.get("heading_alignment_phases", []) or []}
                samples = [
                    float(snap["heading_error_deg"])
                    for snap in snapshots
                    if snap.get("heading_error_deg") is not None
                    and (not filter_phases or str(snap["phase_name"]).strip().lower() in filter_phases)
                ]
                min_samples = int(checks.get("min_heading_alignment_samples", 1))
                if len(samples) < min_samples:
                    return False, f"{case_name}: insufficient heading-alignment samples ({len(samples)} < {min_samples})"
                if max(samples) > float(heading_abs_max):
                    return False, f"{case_name}: heading-to-target error exceeded limit ({max(samples):.1f} > {float(heading_abs_max):.1f})"

            if bool(checks.get("require_waypoint_progress", False)):
                initial_idx = int(snapshots[0]["waypoint_idx"])
                max_idx = max(int(snap["waypoint_idx"]) for snap in snapshots)
                if max_idx <= initial_idx:
                    return False, f"{case_name}: no waypoint progress observed"

            required_c2_tasks = {
                str(x).strip().upper()
                for x in checks.get("required_c2_tasks", []) or []
                if str(x).strip()
            }
            if required_c2_tasks:
                seen_c2_tasks = {
                    str(snap.get("c2_task_name", "")).strip().upper()
                    for snap in snapshots
                    if str(snap.get("c2_task_name", "")).strip()
                }
                missing = sorted(required_c2_tasks - seen_c2_tasks)
                if missing:
                    return False, f"{case_name}: missing required C2 tasks {missing}, saw {sorted(seen_c2_tasks)}"

            min_report_valid_frac = checks.get("min_report_valid_fraction", None)
            if min_report_valid_frac is not None:
                report_valid_frac = float(
                    sum(1 for snap in snapshots if bool(snap.get("report_valid", False))) / max(1, len(snapshots))
                )
                if report_valid_frac < float(min_report_valid_frac):
                    return False, (
                        f"{case_name}: report-valid fraction too low "
                        f"({report_valid_frac:.3f} < {float(min_report_valid_frac):.3f})"
                    )

            min_c2_transitions = checks.get("min_c2_transition_count", None)
            if min_c2_transitions is not None:
                transition_count = sum(1 for snap in snapshots if bool(snap.get("c2_transitioned", False)))
                if transition_count < int(min_c2_transitions):
                    return False, (
                        f"{case_name}: insufficient C2 transitions "
                        f"({transition_count} < {int(min_c2_transitions)})"
                    )

            if expected_reason is not None:
                final_reason = str(final_info.get("termination_reason", ""))
                if final_reason != str(expected_reason):
                    return False, (
                        f"{case_name}: termination reason mismatch "
                        f"({final_reason!r} != {str(expected_reason)!r})"
                    )

            return True, (
                f"{case_name}[steps={len(snapshots)}, cmds={sorted(seen_codes)}, "
                f"c2={sorted({str(s.get('c2_task_name', '')).strip().upper() for s in snapshots if str(s.get('c2_task_name', '')).strip()})}, "
                f"wp={snapshots[0]['waypoint_idx']}->{max(int(s['waypoint_idx']) for s in snapshots)}]"
            )

        def _build_case_scenario(case_spec: dict[str, Any]) -> tuple[str, bool]:
            if "scenario" in case_spec or "scenario_inline" in case_spec or "scenario_base" in case_spec:
                return _materialize_scenario_path(case_spec)
            if base_scenario is None:
                raise ValueError("leader_policy_generalization requires top-level scenario_base/scenario or per-case scenario")
            scenario_obj = copy.deepcopy(base_scenario)
            if isinstance(top_level_patch, dict) and top_level_patch:
                scenario_obj = _deep_merge(scenario_obj, top_level_patch)
            case_patch = case_spec.get("scenario_patch", None)
            if case_patch is not None:
                if not isinstance(case_patch, dict):
                    raise ValueError("leader_policy_generalization case scenario_patch must be a dict")
                scenario_obj = _deep_merge(scenario_obj, case_patch)
            return _write_inline_scenario(scenario_obj), True

        policy_cfg = dict(spec.get("leader_policy", {}) or {})
        leader_cfg = dict(spec.get("leader_env", {}) or {})
        cases = list(spec.get("cases", []) or [])
        if not cases:
            return False, "leader_policy_generalization requires non-empty cases list"

        deterministic = bool(policy_cfg.get("deterministic", True))
        fallback_action = np.asarray(policy_cfg.get("fallback_action", []), dtype=np.float32).reshape(-1)
        fallback_schedule_raw = list(policy_cfg.get("fallback_schedule", []) or [])
        fallback_schedule: list[tuple[int, np.ndarray]] = []
        for item in fallback_schedule_raw:
            if not isinstance(item, dict):
                continue
            arr = np.asarray(item.get("action", []), dtype=np.float32).reshape(-1)
            if arr.size != 4:
                continue
            fallback_schedule.append((int(item.get("from_decision", 0)), arr))
        fallback_schedule.sort(key=lambda x: x[0])
        model_path_raw = policy_cfg.get("model_path", None)
        leader_model = None
        using_model = False
        if model_path_raw:
            leader_model = _load_leader_policy(resolve_repo_path(str(model_path_raw)), str(policy_cfg.get("algo", "auto")))
            using_model = True
        elif fallback_action.size != 4:
            raise ContractSkipped("leader model not provided and fallback_action is missing")

        base_scenario = None
        top_level_patch = spec.get("scenario_patch", None)
        if "scenario_base" in spec:
            base_scenario = _load_json_file(resolve_repo_path(str(spec["scenario_base"])))
        elif "scenario" in spec:
            base_scenario = _load_json_file(resolve_repo_path(str(spec["scenario"])))
        elif "scenario_inline" in spec and isinstance(spec.get("scenario_inline"), dict):
            base_scenario = copy.deepcopy(spec["scenario_inline"])

        default_seed = int(spec.get("seed", 7))
        default_max_decisions = int(spec.get("max_decisions", 24))
        default_checks = dict(spec.get("checks", {}) or {})
        def _make_leader_env(scenario_path: str) -> LeaderTrainingEnv:
            return LeaderTrainingEnv(
                scenario_path=scenario_path,
                decision_interval_steps=int(leader_cfg.get("decision_interval_steps", 20)),
                execution_backend=str(leader_cfg.get("execution_backend", "scripted")),
                execution_train_config=(
                    resolve_repo_path(str(leader_cfg["execution_train_config"]))
                    if leader_cfg.get("execution_train_config")
                    else None
                ),
                execution_model_path=(
                    resolve_repo_path(str(leader_cfg["execution_model_path"]))
                    if leader_cfg.get("execution_model_path")
                    else None
                ),
                execution_algo=str(leader_cfg.get("execution_algo", "auto")),
                scripted_transition_alt_agl_m=float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
                heading_bias_limit_deg=float(leader_cfg.get("heading_bias_limit_deg", 35.0)),
                altitude_bias_limit_m=float(leader_cfg.get("altitude_bias_limit_m", 600.0)),
                speed_bias_limit_mps=float(leader_cfg.get("speed_bias_limit_mps", 30.0)),
                command_change_penalty=float(leader_cfg.get("command_change_penalty", 0.0)),
                teacher_keep_deadband=float(leader_cfg.get("teacher_keep_deadband", 0.2)),
                invalid_phase_penalty=float(leader_cfg.get("invalid_phase_penalty", 0.0)),
                premature_approach_penalty=float(leader_cfg.get("premature_approach_penalty", 0.0)),
                baseline_deviation_penalty=float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
                mode_change_penalty=float(leader_cfg.get("mode_change_penalty", 0.0)),
                approach_gate_distance_m=float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
                approach_gate_cross_m=float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
                approach_gate_heading_error_deg=float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
            )

        case_contexts: list[dict[str, Any]] = []
        for idx, raw_case in enumerate(cases):
            case = dict(raw_case or {})
            scenario_path, should_cleanup = _build_case_scenario(case)
            checks = dict(default_checks)
            checks.update(dict(case.get("checks", {}) or {}))
            case_contexts.append(
                {
                    "case_name": str(case.get("name", f"case_{idx+1}")),
                    "case": case,
                    "scenario_path": scenario_path,
                    "should_cleanup": should_cleanup,
                    "seed": int(case.get("seed", default_seed)),
                    "max_decisions": int(case.get("max_decisions", default_max_decisions)),
                    "checks": checks,
                    "randomization_overrides": case.get("randomization_overrides", spec.get("randomization_overrides", None)),
                    "expected_reason": case.get("expected_termination_reason", spec.get("expected_termination_reason", None)),
                }
            )

        use_batched_rollout = (
            len(case_contexts) > 1
            and bool(spec.get("parallel_case_rollouts", True))
        )

        def _run_leader_case_rollout(ctx: dict[str, Any], *, model_override: Any = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
            env = None
            local_model = model_override
            try:
                env = _make_leader_env(str(ctx["scenario_path"]))
                randomization_overrides = ctx.get("randomization_overrides", None)
                if randomization_overrides is not None:
                    env.set_randomization_overrides(dict(randomization_overrides))
                obs, _info0 = env.reset(seed=int(ctx["seed"]))
                if using_model and local_model is None:
                    local_model = _load_leader_policy(
                        resolve_repo_path(str(model_path_raw)),
                        str(policy_cfg.get("algo", "auto")),
                    )
                snapshots: list[dict[str, Any]] = []
                final_info: dict[str, Any] = {}
                for decision_idx in range(int(ctx["max_decisions"])):
                    if using_model:
                        action, _ = local_model.predict(obs, deterministic=deterministic)
                        action_np = np.asarray(action, dtype=np.float32).reshape(-1)
                    else:
                        action_np = _scheduled_fallback_action(decision_idx)
                    obs, _reward, terminated, truncated, info = env.step(action_np)
                    final_info = dict(info or {})
                    snapshots.append(_collect_leader_snapshot(env, final_info, decision_idx))
                    if bool(terminated) or bool(truncated):
                        break
                return snapshots, final_info
            finally:
                if env is not None:
                    try:
                        env.close()
                    except Exception:
                        pass

        try:
            if use_batched_rollout:
                max_workers = int(spec.get("parallel_case_workers", len(case_contexts)))
                max_workers = max(1, min(max_workers, len(case_contexts)))
                rollout_results: list[tuple[list[dict[str, Any]], dict[str, Any]] | None] = [None] * len(case_contexts)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_idx = {
                        executor.submit(_run_leader_case_rollout, ctx, model_override=None): idx
                        for idx, ctx in enumerate(case_contexts)
                    }
                    for future in concurrent.futures.as_completed(future_to_idx):
                        idx = int(future_to_idx[future])
                        rollout_results[idx] = future.result()
            else:
                rollout_results = [
                    _run_leader_case_rollout(ctx, model_override=leader_model if using_model else None)
                    for ctx in case_contexts
                ]

            case_summaries: list[str] = []
            for idx, ctx in enumerate(case_contexts):
                result = rollout_results[idx]
                if result is None:
                    return False, f"{ctx['case_name']}: rollout result missing"
                snapshots, final_info = result
                ok, detail = _validate_leader_case_rollout(
                    case_name=str(ctx["case_name"]),
                    snapshots=list(snapshots),
                    checks=dict(ctx["checks"]),
                    final_info=dict(final_info),
                    expected_reason=ctx.get("expected_reason", None),
                )
                if not ok:
                    return False, detail
                case_summaries.append(detail)
        finally:
            for ctx in case_contexts:
                if bool(ctx.get("should_cleanup", False)) and os.path.exists(str(ctx["scenario_path"])):
                    try:
                        os.remove(str(ctx["scenario_path"]))
                    except OSError:
                        pass
        policy_desc = "model" if using_model else "fallback_action"
        return True, f"leader policy generalization contract passed ({policy_desc}): " + "; ".join(case_summaries)

    if check_kind == "leader_phase_manager_approach_arm":
        import ef_py
        from python.rl.tasking.bridge import build_kernel_mission_command, make_rule_based_leader_phase_manager

        truth_spec = dict(spec.get("truth", {}) or {})
        inst_spec = dict(spec.get("instruments", {}) or {})
        loader_spec = dict(spec.get("loader", {}) or {})

        class FakeTruth:
            x = float(truth_spec.get("x", -9000.0))
            y = float(truth_spec.get("y", 0.0))
            z = float(truth_spec.get("z", 520.0))
            heading = float(truth_spec.get("heading", 90.0))

        class FakeInst:
            alt_radar = float(inst_spec.get("alt_radar", 520.0))
            alt_baro = float(inst_spec.get("alt_baro", 520.0))
            ground_speed = float(inst_spec.get("ground_speed", 115.0))

        class FakeSim:
            def __init__(self):
                self.last_mission = None
                self.last_intent = None
                self.last_order = None
                self.last_report = None

            def get_agent_observation(self, entity_id):
                _ = entity_id
                return FakeTruth()

            def get_instrument_state(self, entity_id):
                _ = entity_id
                return FakeInst()

            def set_mission_command(self, entity_id, cmd):
                _ = entity_id
                self.last_mission = cmd

            def set_task_order(self, entity_id, order):
                _ = entity_id
                self.last_order = order

            def set_leader_intent(self, entity_id, intent):
                _ = entity_id
                self.last_intent = intent

            def set_pilot_report(self, entity_id, report):
                _ = entity_id
                self.last_report = report

        class FakeLoader:
            def __init__(self):
                self.sim = FakeSim()
                self.agent_id = int(loader_spec.get("agent_id", 42))
                self.waypoints = copy.deepcopy(loader_spec.get("waypoints", [{"x": -12000.0, "y": 0.0}, {"x": -8200.0, "y": 0.0}]))
                self.waypoint_idx = int(loader_spec.get("waypoint_idx", 0))
                self.mission_cmd = copy.deepcopy(
                    loader_spec.get(
                        "mission_cmd",
                        {
                            "command_code": 3,
                            "target_heading": 90.0,
                            "target_altitude": 560.0,
                            "target_speed": 96.0,
                        },
                    )
                )
                self.post_waypoint_transition = copy.deepcopy(
                    loader_spec.get(
                        "post_waypoint_transition",
                        {
                            "phase_name": "landing_ils",
                            "command_code": 4,
                            "target_heading": 90.0,
                            "target_altitude": 0.0,
                            "target_speed": 82.0,
                            "landing_mode": "ils_final",
                        },
                    )
                )
                self.mission_phase_name = str(loader_spec.get("mission_phase_name", "rtb"))
                self.task_order = None
                self.leader_intent = None
                self.pilot_report = None
                self.transition_calls = 0

            def get_ils_observation(self, x_m, y_m, alt_m):
                _ = x_m, y_m, alt_m
                return list(loader_spec.get("ils_observation", [1.0, 0.05, 0.15, 8000.0]))

            def _nearest_ils_beacon(self, x_m, y_m):
                _ = x_m, y_m
                return dict(loader_spec.get("nearest_ils_beacon", {"heading": 90.0}))

            def _activate_post_waypoint_transition(self):
                self.transition_calls += 1
                self.mission_cmd["command_code"] = 4
                self.mission_cmd["target_heading"] = 90.0
                self.mission_cmd["target_altitude"] = 0.0
                self.mission_cmd["target_speed"] = 82.0
                self.post_waypoint_transition = None
                self.waypoints = []
                self.waypoint_idx = 0
                return {"command_code": 4}

        loader = FakeLoader()
        mgr = make_rule_based_leader_phase_manager(
            None,
            terminal_waypoint_count=int(spec.get("terminal_waypoint_count", 2)),
        )
        mgr.reset(loader, sim_time_s=float(spec.get("sim_time_s", 10.0)))
        mgr.sync_to_kernel(loader)
        mission = build_kernel_mission_command(loader)

        if int(loader.transition_calls) != int(spec.get("expected_transition_calls", 1)):
            return False, f"expected approach-arm transition count mismatch: {loader.transition_calls}"
        expected_phase_name = str(spec.get("expected_phase_name", "approach_armed")).strip().lower()
        if str(loader.mission_phase_name).strip().lower() != expected_phase_name:
            return False, f"expected mission_phase_name {expected_phase_name!r}, got {loader.mission_phase_name!r}"
        if loader.leader_intent is None or int(loader.leader_intent.command_code) != int(spec.get("expected_command_code", 4)):
            return False, "leader intent did not switch to landing command"
        if not bool(getattr(loader.leader_intent, "approach_armed", False)):
            return False, "leader intent did not arm approach"
        if int(mission.command_code) != int(spec.get("expected_command_code", 4)):
            return False, f"kernel mission mapping did not reflect landing command: {mission.command_code}"
        if loader.sim.last_intent is None or int(loader.sim.last_intent.command_code) != int(spec.get("expected_command_code", 4)):
            return False, "synced leader intent did not reach simulated kernel"
        return True, "leader phase manager approach-arm contract passed"
    return None
