from __future__ import annotations

import copy
import json
import math
import os
from typing import Any

from python.testing.runtime import ensure_repo_imports

from .common import (
    ContractSkipped,
    _load_spec,
    _materialize_scenario_path,
    _wrap_deg,
    _write_inline_scenario,
)


def _vector_from_source(obs: dict[str, Any], source: str, np: Any) -> Any:
    if source == "obs.mission":
        return np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
    if source == "obs.instruments":
        return np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
    raise ValueError(f"Unknown observation vector source: {source}")


def _check_numeric_rule(actual: float, rule: dict[str, Any], vector: Any, label: str) -> str | None:
    rel_tol = float(rule.get("rel_tol", 1.0e-5))
    abs_tol = float(rule.get("abs_tol", 1.0e-5))
    if "equals" in rule and not math.isclose(actual, float(rule["equals"]), rel_tol=rel_tol, abs_tol=abs_tol):
        return f"expected {label}={float(rule['equals']):.6g}, got {actual:.6g}"
    if "int_equals" in rule and int(actual) != int(rule["int_equals"]):
        return f"expected {label}={int(rule['int_equals'])}, got {actual:.6g}"
    if "abs_max" in rule and abs(actual) > float(rule["abs_max"]):
        return f"expected abs({label}) <= {float(rule['abs_max']):.6g}, got {actual:.6g}"
    if "abs_min_exclusive" in rule and abs(actual) <= float(rule["abs_min_exclusive"]):
        return f"expected abs({label}) > {float(rule['abs_min_exclusive']):.6g}, got {actual:.6g}"
    if "gt" in rule and not (actual > float(rule["gt"])):
        return f"expected {label} > {float(rule['gt']):.6g}, got {actual:.6g}"
    if "lt" in rule and not (actual < float(rule["lt"])):
        return f"expected {label} < {float(rule['lt']):.6g}, got {actual:.6g}"
    if "lt_index" in rule:
        other = float(vector[int(rule["lt_index"])])
        if not actual < other:
            return f"expected {label} < vector[{int(rule['lt_index'])}] ({other:.6g}), got {actual:.6g}"
    return None


def _run_observation_vector_assertions(spec: dict[str, Any], obs: dict[str, Any], np: Any) -> tuple[bool, str]:
    source = str(spec.get("vector_source", "")).strip()
    vector = _vector_from_source(obs, source, np)
    expected_shape = spec.get("expected_shape")
    if expected_shape is not None:
        shape = tuple(int(x) for x in list(expected_shape))
        if tuple(vector.shape) != shape:
            return False, f"{source} expected shape {shape}, got {tuple(vector.shape)}"

    assertions = list(spec.get("assertions", []) or [])
    if not assertions:
        raise ValueError("observation_vector_assertions requires non-empty 'assertions'")
    for idx, raw_rule in enumerate(assertions):
        if not isinstance(raw_rule, dict):
            raise ValueError("observation vector assertions must be JSON objects")
        vector_index = int(raw_rule["index"])
        label = str(raw_rule.get("label", f"{source}[{vector_index}]"))
        actual = float(vector[vector_index])
        mismatch = _check_numeric_rule(actual, raw_rule, vector, label)
        if mismatch is not None:
            return False, mismatch
    return True, str(spec.get("success_message", "observation vector assertions passed"))


def _run_step_info_assertions(spec: dict[str, Any], info: dict[str, Any]) -> tuple[bool, str]:
    reward_terms = dict((info or {}).get("reward_terms", {}) or {})
    for term in [str(item) for item in list(spec.get("required_reward_terms", []) or [])]:
        if term not in reward_terms:
            return False, f"{term} reward term missing"
    return True, str(spec.get("success_message", "step info assertions passed"))


def _clear_loader_runtime_cache(loader: Any) -> None:
    cache = getattr(loader, "_runtime_eval_cache", None)
    if isinstance(cache, dict):
        cache.clear()


def _run_rudder_sign_contract(
    spec: dict[str, Any],
    env: Any,
    *,
    scenario_path: str,
    seed: int,
    np: Any,
    universal_env_cls: Any,
) -> tuple[bool, str]:
    def _shortest_angle_deg(target: float, current: float) -> float:
        d = float(target) - float(current)
        while d > 180.0:
            d -= 360.0
        while d < -180.0:
            d += 360.0
        return d

    def _run_episode(case_env: Any, *, rudder_pulse: float) -> float:
        current_obs, _ = case_env.reset(seed=seed)
        pulse_started = False
        pulse_steps_left = 0
        hdg_before = None
        hdg_after = None
        for _step in range(int(case_env.max_steps)):
            inst = np.asarray(current_obs["instruments"], dtype=np.float32).reshape(-1)
            ias = float(inst[int(spec.get("ias_index", 0))])
            alt = float(inst[int(spec.get("alt_index", 2))])
            pitch_deg = float(inst[int(spec.get("pitch_index", 7))])
            hdg = float(inst[int(spec.get("heading_index", 9))])
            if ias < float(spec.get("rotation_speed_mps", 100.0)):
                pitch_cmd = 0.0
            else:
                pitch_cmd = float(
                    np.clip(
                        (float(spec.get("target_pitch_deg", 15.0)) - pitch_deg)
                        * float(spec.get("pitch_gain", 0.05)),
                        -1.0,
                        1.0,
                    )
                )
            rud = 0.0
            if alt > float(spec.get("airborne_alt_m", 80.0)):
                if not pulse_started:
                    pulse_started = True
                    hdg_before = hdg
                    pulse_steps_left = int(spec.get("pulse_steps", 40))
                if pulse_steps_left > 0:
                    rud = float(rudder_pulse)
                    pulse_steps_left -= 1
                elif hdg_after is None:
                    hdg_after = hdg
            act = np.array([pitch_cmd, 0.0, rud, 1.0], dtype=np.float32)
            current_obs, _r, terminated_case, truncated_case, _i = case_env.step(act)
            if terminated_case or truncated_case:
                break
            if pulse_started and hdg_after is not None:
                break
        if hdg_before is None or hdg_after is None:
            raise RuntimeError("rudder pulse window was not reached (did not get airborne fast enough)")
        return _shortest_angle_deg(hdg_after, hdg_before)

    d_pos = _run_episode(env, rudder_pulse=float(spec.get("positive_pulse", 0.25)))
    env_neg = universal_env_cls(
        scenario_path,
        include_visual=bool(spec.get("include_visual", False)),
        include_proprio=bool(spec.get("include_proprio", False)),
        action_mode=str(spec.get("action_mode", "takeoff4")),
        mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
        visual_downsample=int(spec.get("visual_downsample", 1)),
        visual_update_interval=int(spec.get("visual_update_interval", 1)),
        runtime_compatibility_enabled=True,
    )
    env_neg.set_randomization_overrides(dict(spec.get("randomization_overrides", {}) or {}))
    d_neg = _run_episode(env_neg, rudder_pulse=float(spec.get("negative_pulse", -0.25)))
    if not (d_pos > float(spec.get("positive_delta_min_deg", 0.5))):
        return False, "positive rudder pulse did not increase heading"
    if not (d_neg < float(spec.get("negative_delta_max_deg", -0.5))):
        return False, "negative rudder pulse did not decrease heading"
    return True, "rudder sign contract passed"


def run_env_regression_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    try:
        import gymnasium  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ContractSkipped("gymnasium not installed") from exc

    import numpy as np

    from gym_envs.universal_env import UniversalEnv

    spec = _load_spec(spec_path)
    scenario_path, should_cleanup = _materialize_scenario_path(spec)
    if "scenario_inline" in spec and isinstance(spec.get("scenario_inline"), dict):
        base_scenario = dict(spec["scenario_inline"])
    else:
        with open(scenario_path, "r", encoding="utf-8") as f:
            base_scenario = json.load(f)

    env = UniversalEnv(
        scenario_path,
        include_visual=bool(spec.get("include_visual", False)),
        include_proprio=bool(spec.get("include_proprio", False)),
        action_mode=str(spec.get("action_mode", "full")),
        mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
        visual_downsample=int(spec.get("visual_downsample", 1)),
        visual_update_interval=int(spec.get("visual_update_interval", 1)),
        runtime_compatibility_enabled=True,
    )

    seed = int(spec.get("seed", 0))
    check_kind = str(spec.get("check_kind", "")).strip().lower()
    action = np.asarray(spec.get("action", np.zeros((17,), dtype=np.float32)), dtype=np.float32).reshape(-1)
    extra_cleanup_paths: list[str] = []

    try:
        obs, _ = env.reset(seed=seed)
        loader_updates = dict(spec.get("loader_updates", {}) or {})
        for attr_name, value in loader_updates.items():
            setattr(env.loader, str(attr_name), value)
        if loader_updates:
            _clear_loader_runtime_cache(env.loader)

        if check_kind == "observation_vector_assertions":
            return _run_observation_vector_assertions(spec, obs, np)

        if check_kind == "departure_soft_shaping":
            reward_center, terminated_center, truncated_center, _status_center = env.loader.compute_full_step(obs, env.sim, 0, env.max_steps)
            breakdown_center = dict(getattr(env.loader, "last_reward_breakdown", {}) or {})
            if terminated_center or truncated_center:
                return False, "center departure case terminated before reward regression could be measured"

            comparison_inline = spec.get("comparison_scenario_inline", None)
            if not isinstance(comparison_inline, dict):
                return False, "departure_soft_shaping requires comparison_scenario_inline"
            comparison_path = _write_inline_scenario(comparison_inline)
            extra_cleanup_paths.append(comparison_path)
            env_drift = UniversalEnv(
                comparison_path,
                include_visual=bool(spec.get("include_visual", False)),
                include_proprio=bool(spec.get("include_proprio", False)),
                action_mode=str(spec.get("action_mode", "full")),
                mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
                visual_downsample=int(spec.get("visual_downsample", 1)),
                visual_update_interval=int(spec.get("visual_update_interval", 1)),
                runtime_compatibility_enabled=True,
            )
            obs_drift, _ = env_drift.reset(seed=seed)
            reward_drift, terminated_drift, truncated_drift, _status_drift = env_drift.loader.compute_full_step(
                obs_drift, env_drift.sim, 0, env_drift.max_steps
            )
            breakdown_drift = dict(getattr(env_drift.loader, "last_reward_breakdown", {}) or {})
            if terminated_drift or truncated_drift:
                return False, "drift departure case terminated before reward regression could be measured"
            if float(reward_center) <= float(reward_drift):
                return False, "centered/aligned case should score higher than drifted case"
            if float(breakdown_center.get("departure_centerline_reward", 0.0)) <= 0.0:
                return False, "centered case should receive departure centerline reward"
            if float(breakdown_drift.get("departure_centerline_m_penalty", 0.0)) >= 0.0:
                return False, "drifted case should receive departure centerline penalty"
            if float(breakdown_drift.get("departure_track_error_penalty", 0.0)) >= 0.0:
                return False, "drifted case should receive departure track penalty"
            return True, "departure soft shaping contract passed"

        if check_kind == "post_waypoint_transition":
            reward, terminated, truncated, _info = env.loader.compute_full_step(obs, env.sim, 0, env.max_steps)
            phase = dict(env.loader.mission_cmd)
            if terminated or truncated:
                return False, "waypoint transition should not terminate the episode immediately"
            if int(phase.get("command_code", 0)) != 4:
                return False, "mission command did not switch to landing phase"
            if str(phase.get("landing_mode", "")).strip().lower() != "ils_final":
                return False, "landing phase metadata missing after transition"
            if len(getattr(env.loader, "waypoints", [])) != 0:
                return False, "waypoint state should be cleared after phase transition"
            return True, f"post-waypoint transition contract passed with reward {reward:.3f}"

        if check_kind == "visual_update_interval":
            if "visual" not in obs:
                return False, "initial observation missing visual channel"
            if getattr(env, "_visual_cache", None) is None or int(getattr(env, "_visual_cache_step", -1)) != 0:
                return False, "initial visual cache state invalid"
            action_vec = np.zeros((int(env.action_space.shape[0]),), dtype=np.float32)
            hold_steps = list(spec.get("cache_hold_steps", [1, 2]))
            refresh_step = int(spec.get("refresh_step", 3))
            for expected_step in hold_steps:
                _next_obs, _reward, terminated, truncated, _info = env.step(action_vec)
                if "visual" not in _next_obs:
                    return False, f"step {expected_step}: missing visual channel"
                if int(getattr(env, "_visual_cache_step", -1)) != 0:
                    return False, f"step {expected_step}: visual cache refreshed too early"
                if terminated or truncated:
                    return False, f"step {expected_step}: environment terminated unexpectedly"
                if int(getattr(env, "steps", -1)) != expected_step:
                    return False, f"step {expected_step}: env.steps mismatch"
            _next_obs, _reward, _terminated, _truncated, _info = env.step(action_vec)
            if "visual" not in _next_obs:
                return False, "refresh step missing visual channel"
            if int(getattr(env, "steps", -1)) != refresh_step:
                return False, "refresh step env.steps mismatch"
            if int(getattr(env, "_visual_cache_step", -1)) != refresh_step:
                return False, "visual cache did not refresh at configured interval"
            return True, "visual update interval contract passed"

        if check_kind == "rudder_sign":
            return _run_rudder_sign_contract(
                spec,
                env,
                scenario_path=scenario_path,
                seed=seed,
                np=np,
                universal_env_cls=UniversalEnv,
            )

        _obs, _reward, terminated, truncated, info = env.step(action)

        if check_kind == "step_info_assertions":
            return _run_step_info_assertions(spec, info)

        if check_kind == "waypoint_mode_reward_overrides":
            if terminated or truncated:
                return False, "environment terminated before mode-aware reward regression could be measured"
            reward_terms = dict((info or {}).get("reward_terms", {}) or {})
            mission_status = list((info or {}).get("mission_status", [math.nan, math.nan, math.nan, math.nan]))
            if "waypoint_distance" not in reward_terms:
                return False, "waypoint_distance term missing"
            if "waypoint_proximity" not in reward_terms:
                return False, "waypoint_proximity term missing"
            rewards_cfg = base_scenario.get("rewards", {})
            dist_to_wp_m = float(mission_status[0])
            actual_dist = float(reward_terms["waypoint_distance"])
            actual_prox = float(reward_terms["waypoint_proximity"])
            expected_dist = dist_to_wp_m * float(rewards_cfg["waypoint_distance_weight_flyover"])
            wp_idx = int(getattr(env.loader, "waypoint_idx", 0))
            wp = env.loader.waypoints[wp_idx] if 0 <= wp_idx < len(env.loader.waypoints) else {}
            waypoint_radius_m = max(
                1.0,
                float(wp.get("radius_m", env.loader.mission_cmd.get("waypoint_radius_m", 500.0))),
            )
            prox_ref = max(
                float(rewards_cfg["waypoint_proximity_ref_m_flyover"]),
                max(2.5 * waypoint_radius_m, waypoint_radius_m + 1500.0),
            )
            prox_weight = float(rewards_cfg["waypoint_proximity_weight_flyover"])
            expected_prox = prox_weight * (1.0 - min(dist_to_wp_m, prox_ref) / prox_ref)
            if not math.isclose(actual_dist, expected_dist, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"fly-over waypoint_distance override mismatch: {actual_dist:.6f} != {expected_dist:.6f}"
            if not math.isclose(actual_prox, expected_prox, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"fly-over waypoint_proximity override mismatch: {actual_prox:.6f} != {expected_prox:.6f}"
            return True, "waypoint mode reward override contract passed"

        if check_kind == "waypoint_progress_negative_scale":
            if terminated or truncated:
                return False, "environment terminated before progress-scaling regression could be measured"
            reward_terms = dict((info or {}).get("reward_terms", {}) or {})
            mission_status = list((info or {}).get("mission_status", [math.nan, math.nan, math.nan, math.nan]))
            if "waypoint_progress" not in reward_terms:
                return False, "waypoint_progress term missing"
            prev_dist = float(spec.get("loader_updates", {}).get("_waypoint_prev_dist_m", 1000.0))
            dist_to_wp_m = float(mission_status[0])
            raw_delta = prev_dist - dist_to_wp_m
            if raw_delta >= 0.0:
                return False, f"expected negative progress case, got raw_delta={raw_delta:.6f}"
            expected = raw_delta * float(base_scenario.get("rewards", {}).get("waypoint_progress_negative_scale_flyover", 0.2))
            actual = float(reward_terms["waypoint_progress"])
            if not math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"negative waypoint progress mismatch: {actual:.6f} != {expected:.6f}"
            return True, "waypoint negative progress scaling contract passed"

        if check_kind == "waypoint_route_scaling":
            if terminated or truncated:
                return False, "environment terminated before route-scaling regression could be measured"
            reward_terms = dict((info or {}).get("reward_terms", {}) or {})
            actual = float(reward_terms.get("waypoint_distance", 0.0))
            rewards_cfg = base_scenario.get("rewards", {})
            expected = (
                float(rewards_cfg["waypoint_distance_clip_m"])
                * float(rewards_cfg["waypoint_distance_weight"])
                * 0.5
            )
            if not math.isclose(actual, expected, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"route-scaled waypoint_distance mismatch: {actual:.6f} != {expected:.6f}"
            return True, "waypoint route scaling contract passed"

        if check_kind == "waypoint_reward_balance":
            if terminated or truncated:
                return False, "environment terminated before reward regression could be measured"
            reward_terms = dict((info or {}).get("reward_terms", {}) or {})
            if "waypoint_distance" not in reward_terms:
                return False, "waypoint_distance term missing"
            if "waypoint_cross_track" not in reward_terms:
                return False, "waypoint_cross_track term missing"
            rewards_cfg = base_scenario.get("rewards", {})
            actual_dist = float(reward_terms["waypoint_distance"])
            actual_xtk = float(reward_terms["waypoint_cross_track"])
            expected_dist = float(rewards_cfg["waypoint_distance_clip_m"]) * float(rewards_cfg["waypoint_distance_weight"])
            xtk_err_m = max(0.0, 10000.0 - float(rewards_cfg["waypoint_cross_track_deadband_m"]))
            x = xtk_err_m / float(rewards_cfg["waypoint_cross_track_norm_m"])
            x = min(x, float(rewards_cfg["waypoint_cross_track_clip"]))
            expected_xtk = float(rewards_cfg["waypoint_cross_track_weight"]) * (x ** float(rewards_cfg["waypoint_cross_track_power"]))
            if not math.isclose(actual_dist, expected_dist, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"clipped waypoint_distance mismatch: {actual_dist:.6f} != {expected_dist:.6f}"
            if not math.isclose(actual_xtk, expected_xtk, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"waypoint_cross_track mismatch: {actual_xtk:.6f} != {expected_xtk:.6f}"
            return True, "waypoint reward balance contract passed"

        if check_kind == "waypoint_track_reward":
            reward_terms = None
            heading = 0.0
            ground_track = 0.0
            target = 0.0
            current_obs = obs
            current_info: dict[str, Any] = {}
            current_terminated = False
            current_truncated = False
            for _ in range(int(spec.get("max_rollout_steps", 10))):
                current_obs, _step_reward, current_terminated, current_truncated, current_info = env.step(action)
                inst = np.asarray(current_obs["instruments"], dtype=np.float32).reshape(-1)
                mission = np.asarray(current_obs["mission"], dtype=np.float32).reshape(-1)
                heading = float(inst[9])
                ground_track = float(inst[30])
                target = float(mission[1])
                reward_terms = dict((current_info or {}).get("reward_terms", {}) or {})
                if abs(_wrap_deg(ground_track - heading)) > 0.5:
                    break
                if current_terminated or current_truncated:
                    break
            if reward_terms is None or "heading_error_penalty" not in reward_terms:
                return False, "heading_error_penalty missing from reward_terms"
            track_err = abs(_wrap_deg(target - ground_track))
            heading_err = abs(_wrap_deg(target - heading))
            actual = float(reward_terms["heading_error_penalty"])
            weight = float(base_scenario.get("rewards", {}).get("heading_error_weight", -0.01))
            expected_track = track_err * weight
            legacy_heading = heading_err * weight
            if abs(_wrap_deg(ground_track - heading)) <= 0.5:
                return False, "test did not generate enough wind-induced drift to validate the regression"
            if not math.isclose(actual, expected_track, rel_tol=1e-5, abs_tol=1e-5):
                return False, f"expected ground-track penalty {expected_track:.6f}, got {actual:.6f}"
            if math.isclose(actual, legacy_heading, rel_tol=1e-5, abs_tol=1e-5):
                return False, "reward still matches heading-based penalty"
            return True, "waypoint track reward contract passed"

        if check_kind == "waypoint_turn_relief":
            def _run_case(turn_relief_enabled: bool) -> float:
                rewards_cfg = dict(base_scenario.get("rewards", {}) or {})
                if turn_relief_enabled:
                    rewards_cfg.update(
                        {
                            "waypoint_turn_relief_max": 0.7,
                            "waypoint_turn_relief_window_m": 3500.0,
                            "waypoint_turn_relief_min_turn_deg": 20.0,
                            "waypoint_turn_relief_angle_ref_deg": 85.0,
                            "waypoint_turn_relief_power": 1.25,
                        }
                    )
                else:
                    for key in (
                        "waypoint_turn_relief_max",
                        "waypoint_turn_relief_window_m",
                        "waypoint_turn_relief_min_turn_deg",
                        "waypoint_turn_relief_angle_ref_deg",
                        "waypoint_turn_relief_power",
                    ):
                        rewards_cfg.pop(key, None)

                scenario = dict(base_scenario)
                scenario["rewards"] = rewards_cfg
                case_path = _write_inline_scenario(scenario)
                try:
                    case_env = UniversalEnv(
                        case_path,
                        include_visual=bool(spec.get("include_visual", False)),
                        include_proprio=bool(spec.get("include_proprio", False)),
                        action_mode=str(spec.get("action_mode", "full")),
                        mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
                        visual_downsample=int(spec.get("visual_downsample", 1)),
                        visual_update_interval=int(spec.get("visual_update_interval", 1)),
                        runtime_compatibility_enabled=True,
                    )
                    case_env.reset(seed=seed)
                    case_env.loader.waypoint_idx = 1
                    _clear_loader_runtime_cache(case_env.loader)
                    case_env.loader._waypoint_prev_dist_m = None
                    _next_obs, _case_reward, case_terminated, case_truncated, case_info = case_env.step(action)
                    if case_terminated or case_truncated:
                        raise RuntimeError("environment terminated before turn-relief reward regression could be measured")
                    reward_terms = dict((case_info or {}).get("reward_terms", {}) or {})
                    if "waypoint_cross_track" not in reward_terms:
                        raise RuntimeError("waypoint_cross_track term missing")
                    return float(reward_terms["waypoint_cross_track"])
                finally:
                    try:
                        os.unlink(case_path)
                    except OSError:
                        pass

            no_relief = _run_case(False)
            with_relief = _run_case(True)
            if not (with_relief > no_relief):
                return False, "turn relief did not reduce the magnitude of the cross-track penalty"
            if not (abs(with_relief) < abs(no_relief) * 0.8):
                return False, "turn relief effect was too small to matter"
            return True, "waypoint turn relief contract passed"

        if check_kind == "flyby_sequence_past_fix_guard":
            env.loader.waypoint_idx = int(spec.get("waypoint_idx", 1))
            _clear_loader_runtime_cache(env.loader)
            gstate = env.loader._compute_waypoint_guidance_state()
            if not isinstance(gstate, dict):
                return False, "guidance state missing"
            wp = env.loader.waypoints[int(env.loader.waypoint_idx)]
            truth = env.sim.get_agent_observation(env.agent_id)
            _dist_m = float(math.hypot(float(wp["x"]) - float(truth.x), float(wp["y"]) - float(truth.y)))
            along_m = float(gstate["along_m"])
            leg_len_m = float(gstate["leg_len_m"])
            xtk_m = float(gstate["reward_xtk_m"])
            next_wp = env.loader.waypoints[int(env.loader.waypoint_idx) + 1]
            nx = float(next_wp["x"]) - float(wp["x"])
            ny = float(next_wp["y"]) - float(wp["y"])
            cur_trk = float(env.loader._bearing_to_deg(float(gstate["lx"]), float(gstate["ly"])))
            next_trk = float(env.loader._bearing_to_deg(nx, ny))
            delta = abs(float((next_trk - cur_trk + 180.0) % 360.0 - 180.0))
            turn_lead_m = float(
                env.loader._turn_lead_distance_m(
                    delta,
                    float(spec.get("turn_speed_mps", 210.0)),
                    float(spec.get("bank_limit_deg", 30.0)),
                )
            )
            seq_gate_m = max(
                float(spec.get("seq_gate_min_m", 1200.0)),
                min(
                    float(spec.get("seq_gate_max_m", 3000.0)),
                    float(spec.get("seq_gate_base_m", 1200.0))
                    + float(spec.get("seq_gate_turn_lead_scale", 0.35)) * max(0.0, turn_lead_m),
                ),
            )
            if along_m <= leg_len_m or abs(xtk_m) > seq_gate_m:
                return False, "scenario geometry did not enter the past-fix false-sequencing regime"
            _reward_guard, _terminated_guard, _truncated_guard, _mission_status_guard = env.loader.compute_full_step(
                obs, env.sim, 0, env.max_steps
            )
            _ = _reward_guard, _terminated_guard, _truncated_guard, _mission_status_guard
            if int(env.loader.waypoint_idx) != int(spec.get("waypoint_idx", 1)):
                return False, "fly-by waypoint sequenced after the aircraft had already passed far beyond the fix"
            return True, "fly-by past-fix sequence guard contract passed"

        if check_kind == "flyover_guidance_capture":
            env.loader.waypoint_idx = int(spec.get("waypoint_idx", 1))
            _clear_loader_runtime_cache(env.loader)
            env.loader.update_behaviors(0.0)
            cmd_track = float(env.loader.mission_cmd["target_heading"])
            own_x = float(spec.get("own_x_m", 20800.0))
            own_y = float(spec.get("own_y_m", 400.0))
            wp_x = float(spec.get("wp_x_m", 20000.0))
            wp_y = float(spec.get("wp_y_m", 0.0))
            direct_to_deg = float((math.degrees(math.atan2(wp_x - own_x, wp_y - own_y)) + 360.0) % 360.0)
            if abs(((cmd_track - direct_to_deg + 180.0) % 360.0) - 180.0) > float(spec.get("heading_tolerance_deg", 5.0)):
                return False, "fly-over guidance did not switch to direct-to capture after passing the fix"
            return True, "fly-over guidance capture contract passed"

        if check_kind == "flyover_nav_reward_geometry":
            env.loader.waypoint_idx = int(spec.get("waypoint_idx", 1))
            _clear_loader_runtime_cache(env.loader)
            env.loader.update_behaviors(0.0)
            nav = env.loader._get_waypoint_nav_products()
            if nav is None:
                return False, "nav products missing"
            if abs(float(nav["xtk_m"])) > float(spec.get("nav_xtk_abs_max", 1.0e-6)):
                return False, "fly-over direct-to nav products still expose stale leg cross-track"
            if not math.isclose(float(nav["dtg_m"]), float(nav["dist_m"]), rel_tol=1e-6, abs_tol=1e-6):
                return False, "fly-over direct-to nav products did not use range-to-fix as DTG"
            step_action = np.asarray(spec.get("action", action), dtype=np.float32).reshape(-1)
            _obs2, _reward2, terminated2, truncated2, info2 = env.step(step_action)
            if terminated2 or truncated2:
                return False, "environment terminated before reward geometry regression could be measured"
            reward_terms = dict((info2 or {}).get("reward_terms", {}) or {})
            xtk_term = float(reward_terms.get("waypoint_cross_track", 0.0))
            if abs(xtk_term) > float(spec.get("reward_xtk_abs_max", 1.0e-6)):
                return False, "fly-over direct-to reward still penalized stale leg cross-track"
            return True, "fly-over nav/reward geometry contract passed"

        if check_kind == "landing_objective_properties":
            reward, terminated, truncated, mission_status = env.loader.compute_full_step(obs, env.sim, 0, env.max_steps)
            reason = getattr(env.loader, "last_termination_reason", None)
            if not terminated or truncated or reason != "success_objective":
                return False, (
                    "landing objective properties did not produce success termination "
                    f"(reward={reward:.3f}, reason={reason!r}, mission_status={mission_status})"
                )
            return True, "landing objective properties contract passed"

        if check_kind == "landing_short_final_not_offrunway":
            _next_obs, _step_reward, terminated, truncated, info = env.step(action)
            reason = (info or {}).get("termination_reason")
            if terminated and reason == "off_runway_terminate":
                return False, "short-final landing approach was misclassified as off-runway ground phase"
            return True, "landing short-final off-runway guard contract passed"

        if check_kind == "landing_dme_progress_quality_gate":
            ils_dme = float(np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)[-1])
            env.loader._approach_prev_dme_m = ils_dme + 100.0
            reward, terminated, truncated, _mission_status = env.loader.compute_full_step(obs, env.sim, 0, env.max_steps)
            reward_terms = dict(getattr(env.loader, "last_reward_breakdown", {}) or {})
            dme_reward = float(reward_terms.get("approach_dme_progress", 0.0))
            if abs(dme_reward) > 1.0e-6:
                return False, (
                    "expected DME progress reward to be gated off for poor ILS alignment "
                    f"(reward={reward:.3f}, terminated={terminated}, truncated={truncated}, dme_reward={dme_reward:.6f})"
                )
            return True, "landing DME progress quality gate contract passed"

        if check_kind == "landing_approach_improvement_reward":
            inst = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
            curr_loc_abs = abs(float(inst[-3]))
            curr_gs_abs = abs(float(inst[-2]))
            env.loader._approach_prev_loc_abs = curr_loc_abs + 0.2
            env.loader._approach_prev_gs_abs = curr_gs_abs + 0.2
            reward, terminated, truncated, _mission_status = env.loader.compute_full_step(obs, env.sim, 0, env.max_steps)
            reward_terms = dict(getattr(env.loader, "last_reward_breakdown", {}) or {})
            if float(reward_terms.get("approach_localizer_improve", 0.0)) <= 0.0:
                return False, (
                    "expected positive localizer improvement reward "
                    f"(reward={reward:.3f}, terminated={terminated}, truncated={truncated})"
                )
            if float(reward_terms.get("approach_glideslope_improve", 0.0)) <= 0.0:
                return False, (
                    "expected positive glideslope improvement reward "
                    f"(reward={reward:.3f}, terminated={terminated}, truncated={truncated})"
                )
            return True, "landing approach improvement reward contract passed"

        if check_kind == "flat_terrain_respected":
            _next_obs, _step_reward, terminated, truncated, _info = env.step(action)
            inst = np.asarray(_next_obs["instruments"], dtype=np.float32).reshape(-1)
            alt_radar = float(inst[3])
            if terminated or truncated:
                return False, "flat airborne scenario terminated immediately"
            if alt_radar < float(spec.get("min_alt_radar_m", 1000.0)):
                return False, "flat terrain was not respected; radar altitude collapsed near the legacy hill"
            return True, "flat terrain contract passed"

        if check_kind == "takeoff_departure_constraints":
            base = dict(base_scenario)
            cases = list(spec.get("cases", []) or [])
            if not cases:
                raise ValueError("takeoff_departure_constraints requires non-empty 'cases'")
            for case in cases:
                case_name = str(case.get("name", "case"))
                scenario = copy.deepcopy(base)
                spawn = scenario["entities"][0]
                spawn["pos"][1] = float(case.get("spawn_y_m", 0.0))
                spawn["heading"] = float(case.get("heading_deg", 90.0))
                case_path = _write_inline_scenario(scenario)
                try:
                    case_env = UniversalEnv(
                        case_path,
                        include_visual=bool(spec.get("include_visual", False)),
                        include_proprio=bool(spec.get("include_proprio", False)),
                        action_mode=str(spec.get("action_mode", "full")),
                        mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
                        visual_downsample=int(spec.get("visual_downsample", 1)),
                        visual_update_interval=int(spec.get("visual_update_interval", 1)),
                        runtime_compatibility_enabled=True,
                    )
                    case_obs, _ = case_env.reset(seed=seed)
                    _reward, case_terminated, _case_truncated, _status = case_env.loader.compute_full_step(
                        case_obs, case_env.sim, 0, case_env.max_steps
                    )
                    reason = getattr(case_env.loader, "last_termination_reason", None)
                    expect_terminated = bool(case.get("expect_terminated", False))
                    expect_reason = case.get("expect_reason", None)
                    if bool(case_terminated) != expect_terminated:
                        return False, f"{case_name}: expected terminated={expect_terminated}, got {case_terminated}"
                    if expect_reason is not None and reason != expect_reason:
                        return False, f"{case_name}: expected reason {expect_reason!r}, got {reason!r}"
                finally:
                    try:
                        os.unlink(case_path)
                    except OSError:
                        pass
            return True, "takeoff departure constraints contract passed"

        if check_kind == "scripted_waypoint_coordination":
            from python.rl.control.scripted_stable_flight import ScriptedStableFlightController

            ctrl = ScriptedStableFlightController(action_dim=int(env.action_space.shape[0]), dt=float(env.sim.get_time_step()))
            ctrl.reset(obs)
            abs_beta: list[float] = []
            abs_yaw_rate: list[float] = []
            rollout_steps = int(spec.get("rollout_steps", 1800))
            for _ in range(rollout_steps):
                ctrl_action = ctrl.step(obs)
                obs, _rew, terminated_case, truncated_case, _info_case = env.step(ctrl_action)
                inst = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
                abs_beta.append(abs(float(inst[int(spec.get("beta_index", 6))])))
                abs_yaw_rate.append(abs(float(inst[int(spec.get("yaw_rate_index", 14))])))
                if terminated_case or truncated_case:
                    break
            if not abs_beta or not abs_yaw_rate:
                return False, "scripted waypoint coordination rollout produced no samples"
            if float(np.percentile(np.asarray(abs_beta, dtype=np.float64), 95.0)) >= float(spec.get("beta_p95_max", 10.0)):
                return False, "scripted waypoint controller beta coordination exceeded limit"
            if float(np.percentile(np.asarray(abs_yaw_rate, dtype=np.float64), 95.0)) >= float(spec.get("yaw_rate_p95_max", 20.0)):
                return False, "scripted waypoint controller yaw-rate coordination exceeded limit"
            return True, "scripted waypoint coordination contract passed"

        raise ValueError(f"Unknown env_regression check_kind: {check_kind}")
    finally:
        if should_cleanup:
            try:
                os.unlink(scenario_path)
            except OSError:
                pass
