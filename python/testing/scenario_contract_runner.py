from __future__ import annotations

import json
import os
import tempfile
import math
import copy
from typing import Any

from python.testing.runtime import ensure_repo_imports, resolve_repo_path
from python.artifact_paths import resolve_artifact_path


class ContractSkipped(RuntimeError):
    pass


def _load_spec(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Contract spec must be a JSON object: {path}")
    return data


def _write_inline_scenario(scenario: dict[str, Any]) -> str:
    fd, path = tempfile.mkstemp(suffix=".json", prefix="scenario_contract_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(scenario, f)
    return path


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = {k: copy.deepcopy(v) for k, v in base.items()}
        for key, value in patch.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(patch, list):
        return copy.deepcopy(patch)
    return copy.deepcopy(patch)


def _load_json_file(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Scenario JSON must be an object: {path}")
    return data


def _materialize_scenario_path(spec: dict[str, Any]) -> tuple[str, bool]:
    scenario_base = spec.get("scenario_base", None)
    scenario_patch = spec.get("scenario_patch", None)
    if scenario_base is not None:
        base_path = resolve_repo_path(str(scenario_base))
        base_scenario = _load_json_file(base_path)
        if scenario_patch is not None:
            if not isinstance(scenario_patch, dict):
                raise ValueError("'scenario_patch' must be a JSON object")
            base_scenario = _deep_merge(base_scenario, scenario_patch)
        return _write_inline_scenario(base_scenario), True
    if "scenario" in spec:
        return resolve_repo_path(str(spec["scenario"])), False
    inline_scenario = spec.get("scenario_inline", None)
    if isinstance(inline_scenario, dict):
        return _write_inline_scenario(inline_scenario), True
    raise ValueError("Contract must provide either 'scenario' or 'scenario_inline'")


def _leg_lengths(route: list[dict[str, Any]]) -> list[float]:
    prev_x = 0.0
    prev_y = 0.0
    out: list[float] = []
    for wp in route:
        x = float(wp["x"])
        y = float(wp["y"])
        out.append(float(math.hypot(x - prev_x, y - prev_y)))
        prev_x = x
        prev_y = y
    return out


def _turn_geometry(route: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    points = [(0.0, 0.0)] + [(float(wp["x"]), float(wp["y"])) for wp in route]
    tracks: list[float] = []
    legs: list[float] = []
    for idx in range(1, len(points)):
        dx = points[idx][0] - points[idx - 1][0]
        dy = points[idx][1] - points[idx - 1][1]
        legs.append(float(math.hypot(dx, dy)))
        tracks.append(float(math.degrees(math.atan2(dx, dy)) % 360.0))
    turns: list[float] = []
    for idx in range(1, len(tracks)):
        delta = (tracks[idx] - tracks[idx - 1] + 180.0) % 360.0 - 180.0
        turns.append(abs(float(delta)))
    return legs, turns


def _turn_radius_m(speed_mps: float, bank_limit_deg: float) -> float:
    bank_rad = math.radians(max(1.0, min(80.0, float(bank_limit_deg))))
    tanb = math.tan(bank_rad)
    if abs(tanb) <= 1.0e-6:
        return float("inf")
    speed = max(30.0, float(speed_mps))
    return (speed * speed) / (9.80665 * abs(tanb))


def _turn_budget_cost_m(turn_abs_deg: float, *, speed_mps: float, bank_limit_deg: float, cost_scale: float) -> float:
    turn_abs_deg = abs(float(turn_abs_deg))
    if turn_abs_deg <= 1.0e-6 or float(cost_scale) <= 1.0e-6:
        return 0.0
    radius_m = _turn_radius_m(float(speed_mps), float(bank_limit_deg))
    if not math.isfinite(radius_m) or radius_m <= 0.0:
        return 0.0
    return float(radius_m) * math.radians(turn_abs_deg) * float(cost_scale)


def _wrap_deg(angle_deg: float) -> float:
    return float((float(angle_deg) + 180.0) % 360.0 - 180.0)


def _check_optional_range(value: float, bounds: dict[str, Any], *, label: str) -> str | None:
    if "min" in bounds and value < float(bounds["min"]):
        return f"{label} below minimum: {value:.1f} < {float(bounds['min']):.1f}"
    if "max" in bounds and value > float(bounds["max"]):
        return f"{label} above maximum: {value:.1f} > {float(bounds['max']):.1f}"
    if "abs_min" in bounds and abs(value) < float(bounds["abs_min"]):
        return f"{label} abs below minimum: {abs(value):.1f} < {float(bounds['abs_min']):.1f}"
    if "abs_max" in bounds and abs(value) > float(bounds["abs_max"]):
        return f"{label} abs exceeds maximum: {abs(value):.1f} > {float(bounds['abs_max']):.1f}"
    return None


def run_loader_command_chain_contract(spec_path: str) -> tuple[bool, str]:
    repo_root = ensure_repo_imports()

    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    spec = _load_spec(spec_path)
    scenario_path = resolve_repo_path(str(spec["scenario"]))
    seed = int(spec.get("seed", 7))
    expected_phase_names = {str(x).strip().lower() for x in spec.get("expected_phase_names", [])}
    expected_intent_command_code = int(spec.get("expected_intent_command_code", 1))
    expected_kernel_command_code = int(spec.get("expected_kernel_command_code", expected_intent_command_code))

    sim = ef_py.SimulationKernel()
    sim.load_database("examples/config/database")

    loader = ScenarioLoader(sim)
    agent_id = loader.load_scenario(scenario_path, seed=seed)
    if agent_id is None:
        return False, "expected agent in scenario"

    if loader.task_order is None or not bool(loader.task_order.active):
        return False, "task order was not initialized"
    if loader.leader_intent is None or not bool(loader.leader_intent.active):
        return False, "leader intent was not initialized"
    if loader.pilot_report is None or not bool(loader.pilot_report.active):
        return False, "pilot report was not initialized"

    phase_name = str(loader.mission_phase_name).strip().lower()
    if expected_phase_names and phase_name not in expected_phase_names:
        return False, f"unexpected initial mission phase {loader.mission_phase_name!r}"

    kernel_order = sim.get_task_order(agent_id)
    kernel_intent = sim.get_leader_intent(agent_id)
    kernel_report = sim.get_pilot_report(agent_id)
    kernel_mission = sim.get_mission_command(agent_id)

    if not bool(kernel_order.active):
        return False, "task order did not reach kernel"
    if not bool(kernel_intent.active):
        return False, "leader intent did not reach kernel"
    if not bool(kernel_report.active):
        return False, "pilot report did not reach kernel"
    if int(kernel_intent.command_code) != expected_intent_command_code:
        return False, (
            "unexpected leader intent command_code "
            f"{kernel_intent.command_code} != {expected_intent_command_code}"
        )
    if not bool(kernel_mission.active):
        return False, "kernel mission command was not initialized"
    if int(kernel_mission.command_code) != expected_kernel_command_code:
        return False, (
            "unexpected kernel mission command "
            f"{kernel_mission.command_code} != {expected_kernel_command_code}"
        )
    if int(kernel_mission.command_code) != int(kernel_intent.command_code):
        return False, (
            "kernel mission command is not aligned with leader intent "
            f"({kernel_mission.command_code} vs {kernel_intent.command_code})"
    )
    return True, "loader command chain contract passed"


def run_route_generator_contract(spec_path: str) -> tuple[bool, str]:
    repo_root = ensure_repo_imports()

    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    spec = _load_spec(spec_path)
    scenario_path, should_cleanup = _materialize_scenario_path(spec)
    extra_cleanup_paths: list[str] = []
    if "scenario_inline" in spec and isinstance(spec.get("scenario_inline"), dict):
        base_scenario = dict(spec["scenario_inline"])
    else:
        with open(scenario_path, "r", encoding="utf-8") as f:
            base_scenario = json.load(f)
    seeds = [int(x) for x in spec.get("seeds", [0])]
    checks = dict(spec.get("checks", {}) or {})

    sim = ef_py.SimulationKernel()
    sim.load_database(os.path.join(repo_root, "examples/config/database"))
    loader = ScenarioLoader(sim)

    route_signatures: list[tuple[tuple[float, float, float, float], ...]] = []

    try:
        for seed in seeds:
            loader.load_scenario(scenario_path, seed=seed)
            route = list(loader.waypoints)
            legs = _leg_lengths(route)

            count_range = checks.get("waypoint_count_range", None)
            if isinstance(count_range, (list, tuple)) and len(count_range) >= 2:
                lo = int(count_range[0])
                hi = int(count_range[1])
                if not (lo <= len(route) <= hi):
                    return False, f"seed {seed}: waypoint count out of range: {len(route)} not in [{lo}, {hi}]"

            if bool(checks.get("distinct_routes", False)):
                signature = tuple(
                    (
                        round(float(wp.get("x", 0.0)), 1),
                        round(float(wp.get("y", 0.0)), 1),
                        round(float(wp.get("altitude_m", 0.0)), 1),
                        round(float(wp.get("speed_mps", 0.0)), 1),
                    )
                    for wp in route
                )
                route_signatures.append(signature)

            first_leg_range = checks.get("first_leg_range", None)
            if isinstance(first_leg_range, (list, tuple)) and len(first_leg_range) >= 2:
                if not legs:
                    return False, f"seed {seed}: no legs generated"
                lo = float(first_leg_range[0])
                hi = float(first_leg_range[1])
                if not (lo <= legs[0] <= hi):
                    return False, f"seed {seed}: first leg out of range: {legs[0]:.1f} not in [{lo:.1f}, {hi:.1f}]"

            subsequent_leg_range = checks.get("subsequent_leg_range", None)
            if isinstance(subsequent_leg_range, (list, tuple)) and len(subsequent_leg_range) >= 2:
                lo = float(subsequent_leg_range[0])
                hi = float(subsequent_leg_range[1])
                for leg in legs[1:]:
                    if not (lo <= leg <= hi):
                        return False, f"seed {seed}: subsequent leg out of range: {leg:.1f} not in [{lo:.1f}, {hi:.1f}]"

            attr_ranges = dict(checks.get("waypoint_attr_ranges", {}) or {})
            for attr_name, bounds in attr_ranges.items():
                if not isinstance(bounds, (list, tuple)) or len(bounds) < 2:
                    continue
                lo = float(bounds[0])
                hi = float(bounds[1])
                for wp in route:
                    value = float(wp.get(attr_name, 0.0))
                    if not (lo <= value <= hi):
                        return False, f"seed {seed}: {attr_name} out of range: {value:.1f} not in [{lo:.1f}, {hi:.1f}]"

            if bool(checks.get("reachability_budget_from_scenario", False)):
                route_cfg = (
                    base_scenario.get("mission_command", {})
                    .get("randomization", {})
                    .get("route_generator", {})
                )
                env_cfg = base_scenario.get("environment", {})
                mission_cfg = base_scenario.get("mission_command", {})
                budget = (
                    float(mission_cfg.get("target_speed", 0.0))
                    * float(env_cfg.get("time_step", 0.05))
                    * float(env_cfg.get("max_steps", loader.get_max_steps()))
                    * float(route_cfg.get("route_budget_fraction", 0.80))
                    * (1.0 - float(route_cfg.get("route_budget_margin_fraction", 0.0)))
                )
                total_route = float(sum(legs))
                tolerance_m = float(checks.get("reachability_budget_tolerance_m", 1.0))
                if total_route > budget + tolerance_m:
                    return False, f"seed {seed}: route exceeds reachable budget: {total_route:.1f} > {budget:.1f}"

            if bool(checks.get("turn_budget_from_scenario", False)):
                route_cfg = (
                    base_scenario.get("mission_command", {})
                    .get("randomization", {})
                    .get("route_generator", {})
                )
                mission_cfg = base_scenario.get("mission_command", {})
                env_cfg = base_scenario.get("environment", {})
                legs_geom, turns = _turn_geometry(route)
                route_total = float(sum(legs_geom))
                time_budget_s = float(env_cfg.get("time_step", 0.05)) * float(env_cfg.get("max_steps", loader.get_max_steps()))
                base_speed_mps = float(mission_cfg.get("target_speed", 0.0))
                speed_lo = float(route_cfg.get("speed_mps_range", [base_speed_mps, base_speed_mps])[0])
                turn_speed_mps = max(base_speed_mps, speed_lo)
                bank_limit_deg = float(mission_cfg.get("lnav_bank_limit_deg", 30.0))
                cost_scale = float(route_cfg.get("turn_budget_cost_scale", 0.0))
                if cost_scale <= 0.0 and bool(route_cfg.get("turn_feasibility_enabled", False)):
                    cost_scale = 0.75
                cost_scale = float(max(0.0, cost_scale))
                turn_cost_total = float(
                    sum(
                        _turn_budget_cost_m(
                            turn_abs_deg,
                            speed_mps=turn_speed_mps,
                            bank_limit_deg=bank_limit_deg,
                            cost_scale=cost_scale,
                        )
                        for turn_abs_deg in turns
                    )
                )
                budget = float(base_speed_mps) * float(time_budget_s) * float(route_cfg.get("route_budget_fraction", 0.80))
                budget *= 1.0 - float(route_cfg.get("route_budget_margin_fraction", 0.0))
                tolerance_m = float(checks.get("turn_budget_tolerance_m", checks.get("reachability_budget_tolerance_m", 1.0)))
                if route_total + turn_cost_total > budget + tolerance_m:
                    return False, (
                        f"seed {seed}: route+turn budget exceeded: "
                        f"{route_total + turn_cost_total:.1f} > {budget:.1f} "
                        f"(route={route_total:.1f}, turn_cost={turn_cost_total:.1f})"
                    )

            if bool(checks.get("waypoint_modes_from_scenario", False)):
                route_cfg = (
                    base_scenario.get("mission_command", {})
                    .get("randomization", {})
                    .get("route_generator", {})
                )
                cycle = [str(x).strip().lower() for x in route_cfg.get("waypoint_mode_cycle", [])]
                final_mode = str(route_cfg.get("final_waypoint_mode", "")).strip().lower()
                modes = [str(wp.get("waypoint_mode", "")).strip().lower() for wp in route]
                if len(modes) < 2:
                    return False, f"seed {seed}: expected at least 2 waypoints, got {len(modes)}"
                if cycle:
                    for idx, mode in enumerate(modes[:-1]):
                        expected = cycle[idx % len(cycle)]
                        if mode != expected:
                            return False, f"seed {seed}: waypoint {idx + 1} expected mode {expected!r}, got {mode!r}"
                if final_mode and modes[-1] != final_mode:
                    return False, f"seed {seed}: final waypoint expected mode {final_mode!r}, got {modes[-1]!r}"

            first_wp_bounds = dict(checks.get("first_waypoint_bounds", {}) or {})
            if first_wp_bounds:
                if not route:
                    return False, f"seed {seed}: route generator produced no waypoints"
                wp0 = route[0]
                for axis in ("x", "y"):
                    if axis in first_wp_bounds and isinstance(first_wp_bounds[axis], dict):
                        msg = _check_optional_range(float(wp0.get(axis, 0.0)), dict(first_wp_bounds[axis]), label=f"seed {seed}: first waypoint {axis}")
                        if msg is not None:
                            return False, msg

            heading_range = checks.get("mission_heading_range", None)
            if isinstance(heading_range, (list, tuple)) and len(heading_range) >= 2:
                heading = float(loader.mission_cmd.get("target_heading", 0.0))
                lo = float(heading_range[0])
                hi = float(heading_range[1])
                if not (lo <= heading <= hi):
                    return False, f"seed {seed}: mission heading out of range: {heading:.1f} not in [{lo:.1f}, {hi:.1f}]"

            if bool(checks.get("turn_feasibility_from_scenario", False)):
                route_cfg = (
                    base_scenario.get("mission_command", {})
                    .get("randomization", {})
                    .get("route_generator", {})
                )
                if bool(route_cfg.get("turn_feasibility_enabled", False)):
                    mission_cfg = base_scenario.get("mission_command", {})
                    bank_limit_deg = float(mission_cfg.get("lnav_bank_limit_deg", 30.0))
                    legs_geom, turns = _turn_geometry(route)
                    frac_limit = float(route_cfg.get("turn_leg_usage_fraction_limit", 0.30))
                    clearance_m = float(route_cfg.get("turn_clearance_m", 0.0))
                    speed_lo = float(route_cfg.get("speed_mps_range", [mission_cfg.get("target_speed", 0.0), mission_cfg.get("target_speed", 0.0)])[0])
                    turn_speed_mps = max(float(mission_cfg.get("target_speed", 0.0)), speed_lo)
                    tanb = math.tan(math.radians(bank_limit_deg))
                    turn_radius_m = (turn_speed_mps * turn_speed_mps) / max(1.0e-6, 9.80665 * abs(tanb))
                    for idx, turn_abs_deg in enumerate(turns):
                        lead_m = turn_radius_m * math.tan(0.5 * math.radians(turn_abs_deg))
                        waypoint_radius_m = float(route[idx].get("radius_m", 0.0))
                        lead_budget_m = min(float(legs_geom[idx]), float(legs_geom[idx + 1])) * frac_limit - max(clearance_m, waypoint_radius_m)
                        tolerance_m = float(checks.get("turn_feasibility_tolerance_m", 1.0))
                        if lead_m > lead_budget_m + tolerance_m:
                            return False, (
                                f"seed {seed}: turn lead exceeds budget: "
                                f"turn={turn_abs_deg:.1f} lead={lead_m:.1f} budget={lead_budget_m:.1f}"
                            )

        if bool(checks.get("distinct_routes", False)) and len(route_signatures) >= 2:
            if len(set(route_signatures)) != len(route_signatures):
                return False, "different seeds produced identical routes"
        return True, f"route generator contract passed for {len(seeds)} seed(s)"
    finally:
        for cleanup_path in extra_cleanup_paths:
            try:
                os.unlink(cleanup_path)
            except OSError:
                pass
        if should_cleanup:
            try:
                os.unlink(scenario_path)
            except OSError:
                pass


def run_scripted_bridge_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    try:
        import gymnasium  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ContractSkipped("gymnasium not installed") from exc

    import numpy as np

    from gym_envs.universal_env import UniversalEnv
    from python.rl.control.wrappers import get_action_wrapper_spec

    spec = _load_spec(spec_path)
    scenario_path = resolve_repo_path(str(spec["scenario"]))
    wrapper_cfg_path = resolve_repo_path(str(spec["wrapper_config"]))

    with open(wrapper_cfg_path, "r", encoding="utf-8") as f:
        wrapper_cfg = json.load(f)

    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(wrapper_cfg)
    require_wrapper = bool(spec.get("require_wrapper", True))
    if wrapper_class is None:
        if require_wrapper:
            return False, f"expected wrapper spec from {wrapper_cfg_path}"
        return True, "scripted bridge contract passed without wrapper requirement"

    wrapper_kwargs = dict(wrapper_kwargs or {})
    wrapper_kwargs.update(dict(spec.get("wrapper_overrides", {}) or {}))

    env = UniversalEnv(
        scenario_path,
        include_visual=bool(spec.get("include_visual", False)),
        include_proprio=bool(spec.get("include_proprio", True)),
        mission_obs_mode=str(spec.get("mission_obs_mode", "nav_v2")),
        action_mode=str(spec.get("action_mode", "full")),
    )
    randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
    if randomization_overrides:
        env.set_randomization_overrides(randomization_overrides)
    env = wrapper_class(env, **wrapper_kwargs)

    seed = int(spec.get("seed", 7))
    max_steps = int(spec.get("max_steps", getattr(env.unwrapped, "max_steps", 8000)))
    expected_reason = str(spec.get("expected_termination_reason", "success_objective"))

    _obs, _info = env.reset(seed=seed)
    action = np.zeros((int(env.action_space.shape[0]),), dtype=np.float32)

    for step in range(max_steps):
        _obs, _reward, terminated, truncated, info = env.step(action)
        if bool(terminated or truncated):
            reason = str((info or {}).get("termination_reason", ""))
            if reason != expected_reason:
                return False, f"unexpected termination reason {reason!r} at step {step + 1}"
            return True, f"scripted bridge contract passed in {step + 1} steps"

    return False, f"scripted bridge contract did not terminate within {max_steps} steps"


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

        if check_kind == "mission_obs_nav_v1":
            mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
            if mission.shape != (11,):
                return False, f"expected mission shape (11,), got {mission.shape}"
            checks = [
                (int(mission[0]) == 3, f"expected command_code=3, got {mission[0]}"),
                (math.isclose(float(mission[4]), 0.0, abs_tol=1e-6), f"expected active waypoint index 0, got {mission[4]}"),
                (math.isclose(float(mission[5]), 2.0, abs_tol=1e-6), f"expected total waypoints 2, got {mission[5]}"),
                (math.isclose(float(mission[6]), 10000.0, rel_tol=1e-5, abs_tol=1e-5), f"expected distance-to-go 10000m, got {mission[6]}"),
                (abs(float(mission[7])) <= 1e-5, f"expected cross-track near 0, got {mission[7]}"),
                (math.isclose(float(mission[8]), 10000.0, rel_tol=1e-5, abs_tol=1e-5), f"expected along-track remaining 10000m, got {mission[8]}"),
                (math.isclose(float(mission[9]), 90.0, rel_tol=1e-5, abs_tol=1e-5), f"expected direct bearing 90 deg, got {mission[9]}"),
                (math.isclose(float(mission[10]), 90.0, rel_tol=1e-5, abs_tol=1e-5), f"expected desired leg track 90 deg, got {mission[10]}"),
            ]
            for ok, msg in checks:
                if not ok:
                    return False, msg
            return True, "nav_v1 mission observation contract passed"

        if check_kind == "mission_obs_nav_v2":
            mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
            if mission.shape != (14,):
                return False, f"expected mission shape (14,), got {mission.shape}"
            checks = [
                (int(mission[0]) == 3, f"expected command_code=3, got {mission[0]}"),
                (math.isclose(float(mission[4]), 1.0, abs_tol=1e-6), f"expected selected steerpoint 1, got {mission[4]}"),
                (math.isclose(float(mission[5]), 1.0, abs_tol=1e-6), f"expected steerpoint mode code 1.0 for flyover, got {mission[5]}"),
                (math.isclose(float(mission[6]), 10000.0, rel_tol=1e-5, abs_tol=1e-5), f"expected steerpoint range 10000m, got {mission[6]}"),
                (abs(float(mission[7])) <= 1e-5, f"expected steerpoint bearing rel near 0 deg, got {mission[7]}"),
                (abs(float(mission[8])) <= 1e-5, f"expected steerpoint altitude delta near 0, got {mission[8]}"),
                (abs(float(mission[9])) <= 1e-5, f"expected CDI near 0, got {mission[9]}"),
                (abs(float(mission[10])) <= 1e-5, f"expected track angle error near 0, got {mission[10]}"),
                (math.isclose(float(mission[11]), 10000.0, rel_tol=1e-5, abs_tol=1e-5), f"expected leg distance remaining 10000m, got {mission[11]}"),
                (math.isclose(float(mission[12]), -45.0, rel_tol=1e-4, abs_tol=1e-4), f"expected next turn -45 deg, got {mission[12]}"),
                (0.0 < float(mission[13]) < float(mission[11]), f"expected distance_to_turn between 0 and DTG, got {mission[13]}"),
            ]
            for ok, msg in checks:
                if not ok:
                    return False, msg
            return True, "nav_v2 mission observation contract passed"

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

        _obs, _reward, terminated, truncated, info = env.step(action)

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
            prox_ref = float(rewards_cfg["waypoint_proximity_ref_m_flyover"])
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
                    )
                    case_env.reset(seed=seed)
                    case_env.loader.waypoint_idx = 1
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

        if check_kind == "ils_threshold_crossing_height":
            ils = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)[-4:]
            if float(ils[0]) <= 0.5:
                return False, "ILS should be valid on inbound final"
            if abs(float(ils[2])) > 0.08:
                return False, "ideal threshold-crossing-height glidepath should be near zero glideslope deviation"
            return True, "ILS threshold crossing height contract passed"

        if check_kind == "ils_glideslope_inbound_final":
            ils = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)[-4:]
            if float(ils[0]) <= 0.5:
                return False, "ILS should be valid on inbound final"
            if abs(float(ils[2])) <= 1.0e-6:
                return False, "inbound-final glideslope deviation unexpectedly collapsed to zero"
            return True, "ILS inbound-final glideslope contract passed"

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

        if check_kind == "landing_approach_reward_terms":
            _next_obs, _step_reward, _terminated, _truncated, info = env.step(action)
            reward_terms = dict((info or {}).get("reward_terms", {}) or {})
            if "approach_localizer" not in reward_terms:
                return False, "approach_localizer reward term missing"
            if "approach_glideslope" not in reward_terms:
                return False, "approach_glideslope reward term missing"
            return True, "landing approach reward terms contract passed"

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

        if check_kind == "rudder_sign":
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
                                (float(spec.get("target_pitch_deg", 15.0)) - pitch_deg) * float(spec.get("pitch_gain", 0.05)),
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
            env_neg = UniversalEnv(
                scenario_path,
                include_visual=bool(spec.get("include_visual", False)),
                include_proprio=bool(spec.get("include_proprio", False)),
                action_mode=str(spec.get("action_mode", "takeoff4")),
                mission_obs_mode=str(spec.get("mission_obs_mode", "basic")),
            )
            env_neg.set_randomization_overrides(dict(spec.get("randomization_overrides", {}) or {}))
            d_neg = _run_episode(env_neg, rudder_pulse=float(spec.get("negative_pulse", -0.25)))
            if not (d_pos > float(spec.get("positive_delta_min_deg", 0.5))):
                return False, "positive rudder pulse did not increase heading"
            if not (d_neg < float(spec.get("negative_delta_max_deg", -0.5))):
                return False, "negative rudder pulse did not decrease heading"
            return True, "rudder sign contract passed"

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

        raise ValueError(f"Unknown env_regression check_kind: {check_kind}")
    finally:
        if should_cleanup:
            try:
                os.unlink(scenario_path)
            except OSError:
                pass


def run_unit_regression_contract(spec_path: str) -> tuple[bool, str]:
    ensure_repo_imports()

    spec = _load_spec(spec_path)
    check_kind = str(spec.get("check_kind", "")).strip().lower()

    def _int_equal(lhs: Any, rhs: Any) -> bool:
        try:
            return int(lhs) == int(rhs)
        except Exception:
            return lhs == rhs

    def _check_fields(actual: Any, expected: Any, field_names: tuple[str, ...], *, label: str) -> tuple[bool, str]:
        for field_name in field_names:
            actual_value = getattr(actual, field_name)
            expected_value = getattr(expected, field_name)
            if not _int_equal(actual_value, expected_value):
                return False, f"stored {label} {field_name} mismatch: {actual_value} != {expected_value}"
        return True, ""

    def _recovery_approach_enum(raw_value, default_name: str = "None"):
        import ef_py

        namespace = getattr(ef_py, "RecoveryApproachType", None)
        if namespace is None:
            try:
                return int(raw_value)
            except Exception:
                return 0
        default_value = getattr(namespace, default_name, 0)
        if raw_value is None:
            return default_value
        if isinstance(raw_value, str):
            return getattr(namespace, raw_value, default_value)
        try:
            return namespace(int(raw_value))
        except Exception:
            pass
        try:
            return int(raw_value)
        except Exception:
            return default_value

    def _common_core_field_names(kind: str) -> tuple[str, ...]:
        if kind == "task_order":
            return (
                "service_profile",
                "task_family",
                "tactical_unit_type",
                "command_relationship",
                "authority_scope",
                "parent_node_id",
                "task_group_id",
                "supported_node_id",
                "supporting_node_id",
                "role_code",
                "coordination_mode",
                "relative_slot_code",
                "recovery_site_id",
                "warfare_role_code",
                "officer_in_tactical_command",
            )
        if kind == "leader_intent":
            return (
                "service_profile",
                "task_family",
                "tactical_unit_type",
                "tactical_unit_id",
                "task_group_id",
                "role_code",
                "coordination_mode",
                "relative_slot_code",
                "recovery_site_id",
                "warfare_role_code",
                "officer_in_tactical_command",
            )
        if kind == "pilot_report":
            return (
                "service_profile",
                "task_family",
                "tactical_unit_type",
                "tactical_unit_id",
                "task_group_id",
                "role_code",
                "coordination_mode",
                "element_id",
                "warfare_role_code",
                "officer_in_tactical_command",
            )
        raise ValueError(f"Unknown common-core field kind: {kind}")

    def _air_task_order_field_names() -> tuple[str, ...]:
        return (
            "task_type",
            "station_type",
            "recovery_base_id",
            "recovery_runway_id",
            "recovery_approach_type",
        )

    def _air_leader_intent_field_names() -> tuple[str, ...]:
        return (
            "phase_id",
            "command_code",
            "route_ref_id",
            "recovery_base_id",
            "recovery_runway_id",
            "recovery_approach_type",
        )

    def _air_pilot_report_field_names() -> tuple[str, ...]:
        return (
            "report_type",
            "task_id",
            "phase_id",
        )

    def _task_order_enum_fields():
        import ef_py

        return {
            "task_type": ef_py.TaskType,
            "service_profile": ef_py.ServiceProfile,
            "task_family": ef_py.TaskFamily,
            "tactical_unit_type": ef_py.TacticalUnitType,
            "command_relationship": ef_py.CommandRelationship,
            "authority_scope": ef_py.AuthorityScope,
            "coordination_mode": ef_py.CoordinationMode,
            "station_type": ef_py.StationType,
            "naval_station_type": getattr(ef_py, "NavalStationType", None),
            "warfare_role_code": getattr(ef_py, "NavalWarfareRole", None),
        }

    def _enum_value_or_default(namespace: Any, raw_value: Any, default_name: str):
        default_value = getattr(namespace, default_name)
        if raw_value is None:
            return default_value
        if isinstance(raw_value, str):
            return getattr(namespace, raw_value, default_value)
        try:
            return namespace(int(raw_value))
        except Exception:
            pass
        try:
            return int(raw_value)
        except Exception:
            return default_value

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

    def _compare_kernel_summary_values(
        expected_value: Any,
        actual_value: Any,
        *,
        key: str,
        abs_tol: float,
        rel_tol: float,
    ) -> str | None:
        if isinstance(expected_value, bool) or isinstance(actual_value, bool):
            if bool(expected_value) != bool(actual_value):
                return f"{key}: {actual_value!r} != {expected_value!r}"
            return None
        if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
            if not math.isclose(float(actual_value), float(expected_value), rel_tol=rel_tol, abs_tol=abs_tol):
                return f"{key}: {actual_value!r} != {expected_value!r}"
            return None
        if actual_value != expected_value:
            return f"{key}: {actual_value!r} != {expected_value!r}"
        return None

    def _run_kernel_flight_contract(kernel_spec: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        import numpy as np
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader
        from gym_envs.universal_env import half_to_unit

        controller_kind = str(kernel_spec.get("controller_kind", "")).strip().lower()
        scenario_path = resolve_repo_path(str(kernel_spec["scenario"]))
        seed = int(kernel_spec.get("seed", 0))
        checks = dict(kernel_spec.get("checks", {}) or {})

        sim = ef_py.SimulationKernel()
        sim.load_database(resolve_repo_path("examples", "config", "database"))
        loader = ScenarioLoader(sim)
        randomization_overrides = dict(kernel_spec.get("randomization_overrides", {}) or {})
        if randomization_overrides:
            loader.set_randomization_overrides(randomization_overrides)
        agent_id = loader.load_scenario(scenario_path, seed=seed)
        if agent_id is None:
            return False, "scenario did not spawn an agent", {}

        def _finite(x: float) -> bool:
            try:
                return math.isfinite(float(x))
            except Exception:
                return False

        def _base_pilot_action():
            pa = ef_py.PilotAction()
            pa.active = True
            pa.stick_pitch = 0.0
            pa.stick_roll = 0.0
            pa.rudder = 0.0
            pa.throttle = 0.0
            pa.gear_handle = 0.0
            pa.flaps = 0.0
            pa.speedbrake = 0.0
            pa.brake = 0.0
            pa.brake_left = False
            pa.brake_right = False
            pa.radar_active = False
            pa.radar_scan_az = 0.0
            pa.radar_scan_el = 0.0
            pa.tms_up = False
            pa.master_arm = False
            pa.fire_weapon = False
            pa.fire_gun = False
            pa.weapon_select_id = 0
            pa.program_chaff = False
            pa.program_flare = False
            pa.jettison_emergency = False
            return pa

        def _summary(extra: dict[str, Any] | None = None) -> dict[str, Any]:
            inst = sim.get_instrument_state(agent_id)
            truth = sim.get_agent_observation(agent_id)
            pos = sim.get_unit_position(agent_id)
            vel = sim.get_unit_velocity(agent_id)
            out: dict[str, Any] = {
                "controller_kind": controller_kind,
                "seed": seed,
                "alt_baro_m": float(inst.alt_baro),
                "ias_mps": float(inst.ias),
                "vvi_mps": float(inst.vvi),
                "pitch_deg": float(inst.pitch),
                "roll_deg": float(inst.roll),
                "heading_deg": float(inst.heading),
                "aoa_deg": float(inst.aoa),
                "beta_deg": float(inst.beta),
                "q_deg_s": float(inst.q),
                "r_deg_s": float(inst.r),
                "g_load": float(inst.g_load),
                "ground_speed_mps": float(inst.ground_speed),
                "ground_track_deg": float(inst.ground_track),
                "wind_speed_mps": float(inst.wind_speed),
                "wind_dir_deg": float(inst.wind_dir),
                "track_heading_delta_deg": _wrap_deg(float(inst.ground_track) - float(inst.heading)),
                "truth_health": float(truth.health),
                "truth_x_m": float(pos[0]),
                "truth_y_m": float(pos[1]),
                "truth_z_m": float(pos[2]),
                "truth_vx_mps": float(vel[0]),
                "truth_vy_mps": float(vel[1]),
                "truth_vz_mps": float(vel[2]),
            }
            if extra:
                out.update(dict(extra))
            return out

        if controller_kind == "midpoint_env_action":
            action_dim = int(kernel_spec.get("action_dim", 17))
            action = np.zeros((action_dim,), dtype=np.float32)
            for idx in list(kernel_spec.get("midpoint_indices", []) or []):
                if 0 <= int(idx) < action_dim:
                    action[int(idx)] = 0.5
            max_steps = int(kernel_spec.get("max_steps", 200))
            for _ in range(max_steps):
                pa = _base_pilot_action()
                pa.stick_pitch = float(action[0])
                pa.stick_roll = float(action[1])
                pa.rudder = float(action[2])
                pa.throttle = float(action[3])
                pa.gear_handle = float(action[4])
                pa.flaps = float(half_to_unit(float(action[5])))
                pa.speedbrake = float(half_to_unit(float(action[6])))
                pa.brake_left = False
                pa.brake_right = False
                pa.brake = float(half_to_unit(float(max(action[7], action[8]))))
                pa.radar_active = bool(action[9] > 0.5)
                pa.radar_scan_az = float(action[10]) * 60.0
                pa.radar_scan_el = float(action[11]) * 30.0
                pa.tms_up = bool(action[12] > 0.5)
                pa.master_arm = bool(action[13] > 0.5)
                pa.fire_weapon = bool(action[14] > 0.5)
                pa.fire_gun = bool(action[15] > 0.5)
                pa.weapon_select_id = int(action[16] * 7)
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            inst = sim.get_instrument_state(agent_id)
            final_ias = float(inst.ias)
            final_ias_min = float(checks.get("final_ias_min", 5.0))
            if final_ias <= final_ias_min:
                return False, f"expected IAS > {final_ias_min:.1f}, got {final_ias:.3f}", _summary({"steps": max_steps})
            return True, f"kernel midpoint ground-roll contract passed with IAS={final_ias:.2f}", _summary({"steps": max_steps})

        if controller_kind == "manual_takeoff":
            target_pitch = float(kernel_spec.get("target_pitch_deg", 15.0))
            success_alt = float(checks.get("success_alt_min", 300.0))
            success_speed = float(checks.get("success_speed_min", 150.0))
            max_steps = int(kernel_spec.get("max_steps", 2000))
            for step in range(max_steps):
                inst = sim.get_instrument_state(agent_id)
                speed = float(inst.ias)
                alt = float(inst.alt_baro)
                pitch = float(inst.pitch)
                pa = _base_pilot_action()
                pa.stick_roll = 0.0
                pa.rudder = 0.0
                pa.throttle = 1.0
                pa.flaps = 0.0
                pa.speedbrake = 0.0
                pa.brake = 0.0
                pa.brake_left = False
                pa.brake_right = False
                if speed < float(kernel_spec.get("rotation_speed_mps", 100.0)):
                    pa.stick_pitch = 0.0
                else:
                    pa.stick_pitch = float(
                        np.clip(
                            (target_pitch - pitch) * float(kernel_spec.get("pitch_gain", 0.05)),
                            -1.0,
                            1.0,
                        )
                    )
                pa.gear_handle = 0.0 if alt > float(kernel_spec.get("gear_up_alt_m", 30.0)) else 1.0
                sim.set_pilot_action(agent_id, pa)
                sim.step()
                if alt > success_alt and speed > success_speed:
                    return True, f"kernel manual takeoff contract passed in {step + 1} steps", _summary({"steps": step + 1})
            return False, f"manual takeoff did not reach alt>{success_alt:.1f} and speed>{success_speed:.1f}", _summary({"steps": max_steps})

        if controller_kind == "stable_level_hold":
            dt = float(sim.get_time_step())
            if dt <= 0.0:
                return False, f"invalid sim time step {dt}", {}
            inst0 = sim.get_instrument_state(agent_id)
            alt_ref = float(inst0.alt_baro)
            ias_ref = float(inst0.ias)
            pa = _base_pilot_action()
            pa.rudder = 0.0
            pa.gear_handle = 0.0
            pa.flaps = 0.0
            pa.speedbrake = 0.0
            pa.brake = 0.0
            pa.brake_left = False
            pa.brake_right = False
            thr = float(kernel_spec.get("initial_throttle", 0.6))
            alt_int = 0.0
            min_alt = float("inf")
            max_abs_roll = 0.0
            max_abs_pitch = 0.0
            max_abs_g = 0.0
            steps = int(round(float(kernel_spec.get("duration_s", 200.0)) / dt))
            for _ in range(steps):
                inst = sim.get_instrument_state(agent_id)
                truth = sim.get_agent_observation(agent_id)
                if float(truth.health) <= 0.0:
                    return False, "aircraft crashed during level-flight stability test", _summary({"steps": steps})
                alt = float(inst.alt_baro)
                vvi = float(inst.vvi)
                ias = float(inst.ias)
                pitch = float(inst.pitch)
                roll = float(inst.roll)
                p = float(inst.p)
                q = float(inst.q)
                g_load = float(inst.g_load)
                for value in (alt, vvi, ias, pitch, roll, p, q, g_load):
                    if not _finite(value):
                        return False, f"non-finite instrument value during stable flight: {value!r}", _summary({"steps": steps})
                min_alt = min(min_alt, alt)
                max_abs_roll = max(max_abs_roll, abs(roll))
                max_abs_pitch = max(max_abs_pitch, abs(pitch))
                max_abs_g = max(max_abs_g, abs(g_load))
                pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.5, 0.5))
                alt_err = alt_ref - alt
                alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
                pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
                pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))
                thr = float(np.clip(thr + 0.003 * (ias_ref - ias), 0.0, 1.0))
                pa.throttle = thr
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            if min_alt <= float(checks.get("min_alt_min", 800.0)):
                return False, f"altitude dipped too low: min_alt={min_alt:.1f}m", _summary({"steps": steps, "min_alt_m": min_alt})
            if max_abs_roll >= float(checks.get("max_abs_roll_max", 10.0)):
                return False, f"excessive roll during level flight: {max_abs_roll:.1f}deg", _summary({"steps": steps, "max_abs_roll_deg": max_abs_roll})
            if max_abs_pitch >= float(checks.get("max_abs_pitch_max", 15.0)):
                return False, f"excessive pitch during level flight: {max_abs_pitch:.1f}deg", _summary({"steps": steps, "max_abs_pitch_deg": max_abs_pitch})
            if max_abs_g >= float(checks.get("max_abs_g_max", 3.0)):
                return False, f"excessive G-load during level flight: {max_abs_g:.2f}", _summary({"steps": steps, "max_abs_g": max_abs_g})
            return True, (
                "kernel stable level-flight contract passed "
                f"(min_alt={min_alt:.1f}, max_roll={max_abs_roll:.1f}, max_pitch={max_abs_pitch:.1f}, max_g={max_abs_g:.2f})"
            ), _summary(
                {
                    "steps": steps,
                    "min_alt_m": min_alt,
                    "max_abs_roll_deg": max_abs_roll,
                    "max_abs_pitch_deg": max_abs_pitch,
                    "max_abs_g": max_abs_g,
                }
            )

        if controller_kind == "takeoff_then_stable_hold":
            dt = float(sim.get_time_step())
            if dt <= 0.0:
                return False, f"invalid sim time step {dt}", {}
            pa = _base_pilot_action()
            pa.flaps = 0.0
            pa.speedbrake = 0.0
            pa.brake = 0.0
            pa.brake_left = False
            pa.brake_right = False
            stage = "takeoff"
            thr = 1.0
            alt_ref = 0.0
            ias_ref = 0.0
            alt_int = 0.0
            stable_steps = 0
            min_alt_stable = float("inf")
            max_abs_roll = 0.0
            max_abs_pitch = 0.0
            max_steps = int(kernel_spec.get("max_steps", 2000))
            stable_entry_alt_min = float(checks.get("stable_entry_alt_min", 300.0))
            stable_entry_speed_min = float(checks.get("stable_entry_speed_min", 150.0))
            for _ in range(max_steps):
                inst = sim.get_instrument_state(agent_id)
                truth = sim.get_agent_observation(agent_id)
                if float(truth.health) <= 0.0:
                    return False, "aircraft crashed during takeoff/stable-flight test", _summary({"steps": max_steps, "stage": stage})
                for value in (
                    float(inst.alt_baro),
                    float(inst.alt_radar),
                    float(inst.ias),
                    float(inst.vvi),
                    float(inst.pitch),
                    float(inst.roll),
                    float(inst.p),
                    float(inst.q),
                    float(inst.g_load),
                ):
                    if not _finite(value):
                        return False, f"non-finite instrument value: {value!r}", _summary({"steps": max_steps, "stage": stage})
                if stage == "takeoff":
                    pa.throttle = 1.0
                    pa.stick_roll = 0.0
                    pa.rudder = 0.0
                    if float(inst.ias) < float(kernel_spec.get("rotation_speed_mps", 100.0)):
                        pa.stick_pitch = 0.0
                    else:
                        pitch_err = float(kernel_spec.get("target_takeoff_pitch_deg", 13.0)) - float(inst.pitch)
                        pa.stick_pitch = float(
                            np.clip(
                                pitch_err * float(kernel_spec.get("takeoff_pitch_gain", 0.05)),
                                -1.0,
                                1.0,
                            )
                        )
                    pa.gear_handle = 0.0 if float(inst.alt_baro) > float(kernel_spec.get("gear_up_alt_m", 30.0)) else 1.0
                    if float(inst.alt_baro) > stable_entry_alt_min and float(inst.ias) > stable_entry_speed_min:
                        stage = "stable"
                        alt_ref = float(inst.alt_baro)
                        ias_ref = float(inst.ias)
                        thr = float(pa.throttle)
                        alt_int = 0.0
                        stable_steps = 0
                        min_alt_stable = float("inf")
                else:
                    stable_steps += 1
                    alt = float(inst.alt_baro)
                    vvi = float(inst.vvi)
                    pitch = float(inst.pitch)
                    roll = float(inst.roll)
                    p = float(inst.p)
                    q = float(inst.q)
                    ias = float(inst.ias)
                    min_alt_stable = min(min_alt_stable, alt)
                    max_abs_roll = max(max_abs_roll, abs(roll))
                    max_abs_pitch = max(max_abs_pitch, abs(pitch))
                    pa.stick_roll = float(np.clip(-0.03 * roll - 0.01 * p, -0.6, 0.6))
                    alt_err = alt_ref - alt
                    alt_int = float(np.clip(alt_int + alt_err * dt, -2000.0, 2000.0))
                    pitch_tgt = float(np.clip(0.02 * alt_err + 0.0005 * alt_int - 0.06 * vvi, -15.0, 15.0))
                    pa.stick_pitch = float(np.clip(0.08 * (pitch_tgt - pitch) - 0.015 * q, -1.0, 1.0))
                    thr = float(np.clip(thr + 0.003 * (ias_ref - ias), 0.0, 1.0))
                    pa.throttle = thr
                    pa.rudder = 0.0
                    pa.gear_handle = 0.0
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            if stage != "stable":
                return False, "did not reach stable flight phase within max_steps", _summary({"steps": max_steps, "stage": stage})
            stable_steps_min = int(round(float(checks.get("stable_steps_min_s", 40.0)) / dt))
            if stable_steps < stable_steps_min:
                return False, f"stable phase too short: {stable_steps} steps", _summary({"steps": max_steps, "stable_steps": stable_steps})
            if min_alt_stable <= float(checks.get("min_alt_stable_min", 150.0)):
                return False, (
                    f"altitude dipped too low during stable flight: min_alt={min_alt_stable:.1f}m"
                ), _summary({"steps": max_steps, "stable_steps": stable_steps, "min_alt_stable_m": min_alt_stable})
            if max_abs_roll >= float(checks.get("max_abs_roll_max", 20.0)):
                return False, f"excessive roll in stable phase: {max_abs_roll:.1f}deg", _summary({"steps": max_steps, "stable_steps": stable_steps, "max_abs_roll_deg": max_abs_roll})
            if max_abs_pitch >= float(checks.get("max_abs_pitch_max", 20.0)):
                return False, f"excessive pitch in stable phase: {max_abs_pitch:.1f}deg", _summary({"steps": max_steps, "stable_steps": stable_steps, "max_abs_pitch_deg": max_abs_pitch})
            return True, (
                "kernel takeoff-then-stable contract passed "
                f"(stable_steps={stable_steps}, min_alt={min_alt_stable:.1f}, max_roll={max_abs_roll:.1f}, max_pitch={max_abs_pitch:.1f})"
            ), _summary(
                {
                    "steps": max_steps,
                    "stage": stage,
                    "stable_steps": stable_steps,
                    "min_alt_stable_m": min_alt_stable,
                    "max_abs_roll_deg": max_abs_roll,
                    "max_abs_pitch_deg": max_abs_pitch,
                }
            )

        if controller_kind == "pilot_pitch_sign_response":
            response_steps = int(kernel_spec.get("response_steps", 10))
            pa = _base_pilot_action()
            pa.stick_pitch = float(kernel_spec.get("stick_pitch", 0.5))
            pa.throttle = float(kernel_spec.get("throttle", 0.8))
            pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
            for _ in range(response_steps):
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            inst = sim.get_instrument_state(agent_id)
            pitch_min = float(checks.get("pitch_min_deg", 0.0))
            q_min = float(checks.get("q_min_deg_s", 0.0))
            aoa_min = float(checks.get("aoa_min_deg", 0.0))
            if float(inst.pitch) <= pitch_min:
                return False, f"expected pitch > {pitch_min:.3f}, got {float(inst.pitch):.6f}", _summary({"steps": response_steps})
            if float(inst.q) <= q_min:
                return False, f"expected q > {q_min:.3f}, got {float(inst.q):.6f}", _summary({"steps": response_steps})
            if float(inst.aoa) <= aoa_min:
                return False, f"expected AoA > {aoa_min:.3f}, got {float(inst.aoa):.6f}", _summary({"steps": response_steps})
            return True, "kernel pilot pitch-sign contract passed", _summary({"steps": response_steps})

        if controller_kind == "pitch_hold":
            dt = float(sim.get_time_step())
            if dt <= 0.0:
                return False, f"invalid sim time step {dt}", {}
            steps = int(kernel_spec.get("max_steps", max(1, int(round(float(kernel_spec.get("duration_s", 6.0)) / dt)))))
            target_pitch = float(kernel_spec.get("target_pitch_deg", 0.0))
            pitch_kp = float(kernel_spec.get("pitch_kp", 0.12))
            pitch_kd = float(kernel_spec.get("pitch_kd", 0.02))
            pa = _base_pilot_action()
            pa.stick_roll = float(kernel_spec.get("stick_roll", 0.0))
            pa.rudder = float(kernel_spec.get("rudder", 0.0))
            pa.throttle = float(kernel_spec.get("throttle", 0.5))
            pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
            pa.flaps = float(kernel_spec.get("flaps", 0.0))
            pa.speedbrake = float(kernel_spec.get("speedbrake", 0.0))
            pa.brake = float(kernel_spec.get("brake", 0.0))
            pa.brake_left = bool(kernel_spec.get("brake_left", False))
            pa.brake_right = bool(kernel_spec.get("brake_right", False))
            min_alt = float("inf")
            max_abs_roll = 0.0
            max_abs_pitch_error = 0.0
            for _ in range(steps):
                inst = sim.get_instrument_state(agent_id)
                truth = sim.get_agent_observation(agent_id)
                if float(truth.health) <= 0.0:
                    return False, "aircraft crashed during pitch-hold test", _summary({"steps": steps})
                alt = float(inst.alt_baro)
                pitch = float(inst.pitch)
                roll = float(inst.roll)
                q = float(inst.q)
                ias = float(inst.ias)
                vvi = float(inst.vvi)
                aoa = float(inst.aoa)
                for value in (alt, pitch, roll, q, ias, vvi, aoa):
                    if not _finite(value):
                        return False, f"non-finite instrument value during pitch-hold test: {value!r}", _summary({"steps": steps})
                min_alt = min(min_alt, alt)
                max_abs_roll = max(max_abs_roll, abs(roll))
                max_abs_pitch_error = max(max_abs_pitch_error, abs(target_pitch - pitch))
                pa.stick_pitch = float(np.clip(pitch_kp * (target_pitch - pitch) - pitch_kd * q, -1.0, 1.0))
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            final_inst = sim.get_instrument_state(agent_id)
            final_pitch_error = abs(target_pitch - float(final_inst.pitch))
            pitch_error_abs_max = checks.get("pitch_error_abs_max", None)
            if pitch_error_abs_max is not None and final_pitch_error > float(pitch_error_abs_max):
                return False, (
                    f"pitch-hold final error too large: {final_pitch_error:.3f} > {float(pitch_error_abs_max):.3f}"
                ), _summary(
                    {
                        "steps": steps,
                        "target_pitch_deg": target_pitch,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "min_alt_m": min_alt,
                        "max_abs_roll_deg": max_abs_roll,
                    }
                )
            min_alt_min = checks.get("min_alt_min", None)
            if min_alt_min is not None and min_alt < float(min_alt_min):
                return False, f"pitch-hold altitude dipped too low: {min_alt:.3f} < {float(min_alt_min):.3f}", _summary(
                    {
                        "steps": steps,
                        "target_pitch_deg": target_pitch,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "min_alt_m": min_alt,
                        "max_abs_roll_deg": max_abs_roll,
                    }
                )
            max_abs_roll_max = checks.get("max_abs_roll_max", None)
            if max_abs_roll_max is not None and max_abs_roll > float(max_abs_roll_max):
                return False, f"pitch-hold roll excursion too large: {max_abs_roll:.3f} > {float(max_abs_roll_max):.3f}", _summary(
                    {
                        "steps": steps,
                        "target_pitch_deg": target_pitch,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "min_alt_m": min_alt,
                        "max_abs_roll_deg": max_abs_roll,
                    }
                )
            return True, (
                "kernel pitch-hold contract passed "
                f"(pitch={float(final_inst.pitch):.2f}, vvi={float(final_inst.vvi):.2f}, ias={float(final_inst.ias):.2f})"
            ), _summary(
                {
                    "steps": steps,
                    "target_pitch_deg": target_pitch,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "min_alt_m": min_alt,
                    "max_abs_roll_deg": max_abs_roll,
                }
            )

        if controller_kind == "heading_hold_pitch":
            dt = float(sim.get_time_step())
            if dt <= 0.0:
                return False, f"invalid sim time step {dt}", {}
            steps = int(kernel_spec.get("max_steps", max(1, int(round(float(kernel_spec.get("duration_s", 6.0)) / dt)))))
            inst0 = sim.get_instrument_state(agent_id)
            target_heading = float(kernel_spec.get("target_heading_deg", float(inst0.heading)))
            target_pitch = float(kernel_spec.get("target_pitch_deg", 0.0))
            heading_kp = float(kernel_spec.get("heading_kp", 0.12))
            roll_kp = float(kernel_spec.get("roll_kp", 0.05))
            roll_rate_kd = float(kernel_spec.get("roll_rate_kd", 0.01))
            pitch_kp = float(kernel_spec.get("pitch_kp", 0.16))
            pitch_kd = float(kernel_spec.get("pitch_kd", 0.03))
            max_roll_cmd = float(kernel_spec.get("max_roll_cmd", 0.7))
            pa = _base_pilot_action()
            pa.rudder = float(kernel_spec.get("rudder", 0.0))
            pa.throttle = float(kernel_spec.get("throttle", 0.6))
            pa.gear_handle = float(kernel_spec.get("gear_handle", 0.0))
            pa.flaps = float(kernel_spec.get("flaps", 0.0))
            pa.speedbrake = float(kernel_spec.get("speedbrake", 0.0))
            pa.brake = float(kernel_spec.get("brake", 0.0))
            pa.brake_left = bool(kernel_spec.get("brake_left", False))
            pa.brake_right = bool(kernel_spec.get("brake_right", False))
            max_abs_heading_error = 0.0
            max_abs_pitch_error = 0.0
            max_abs_roll = 0.0
            min_alt = float("inf")
            for _ in range(steps):
                inst = sim.get_instrument_state(agent_id)
                truth = sim.get_agent_observation(agent_id)
                if float(truth.health) <= 0.0:
                    return False, "aircraft crashed during heading/pitch-hold test", _summary({"steps": steps})
                alt = float(inst.alt_baro)
                heading = float(inst.heading)
                pitch = float(inst.pitch)
                roll = float(inst.roll)
                p = float(inst.p)
                q = float(inst.q)
                ias = float(inst.ias)
                vvi = float(inst.vvi)
                for value in (alt, heading, pitch, roll, p, q, ias, vvi):
                    if not _finite(value):
                        return False, f"non-finite instrument value during heading/pitch-hold test: {value!r}", _summary({"steps": steps})
                heading_error = _wrap_deg(target_heading - heading)
                max_abs_heading_error = max(max_abs_heading_error, abs(heading_error))
                max_abs_pitch_error = max(max_abs_pitch_error, abs(target_pitch - pitch))
                max_abs_roll = max(max_abs_roll, abs(roll))
                min_alt = min(min_alt, alt)
                pa.stick_roll = float(
                    np.clip(heading_kp * heading_error - roll_kp * roll - roll_rate_kd * p, -max_roll_cmd, max_roll_cmd)
                )
                pa.stick_pitch = float(np.clip(pitch_kp * (target_pitch - pitch) - pitch_kd * q, -1.0, 1.0))
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            final_inst = sim.get_instrument_state(agent_id)
            final_heading_error = abs(_wrap_deg(target_heading - float(final_inst.heading)))
            final_pitch_error = abs(target_pitch - float(final_inst.pitch))
            heading_error_abs_max = checks.get("heading_error_abs_max", None)
            if heading_error_abs_max is not None and final_heading_error > float(heading_error_abs_max):
                return False, (
                    f"heading-hold final error too large: {final_heading_error:.3f} > {float(heading_error_abs_max):.3f}"
                ), _summary(
                    {
                        "steps": steps,
                        "target_heading_deg": target_heading,
                        "target_pitch_deg": target_pitch,
                        "final_heading_error_deg": final_heading_error,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_heading_error_deg": max_abs_heading_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "max_abs_roll_deg": max_abs_roll,
                        "min_alt_m": min_alt,
                    }
                )
            pitch_error_abs_max = checks.get("pitch_error_abs_max", None)
            if pitch_error_abs_max is not None and final_pitch_error > float(pitch_error_abs_max):
                return False, (
                    f"heading-hold pitch error too large: {final_pitch_error:.3f} > {float(pitch_error_abs_max):.3f}"
                ), _summary(
                    {
                        "steps": steps,
                        "target_heading_deg": target_heading,
                        "target_pitch_deg": target_pitch,
                        "final_heading_error_deg": final_heading_error,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_heading_error_deg": max_abs_heading_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "max_abs_roll_deg": max_abs_roll,
                        "min_alt_m": min_alt,
                    }
                )
            max_abs_roll_max = checks.get("max_abs_roll_max", None)
            if max_abs_roll_max is not None and max_abs_roll > float(max_abs_roll_max):
                return False, (
                    f"heading-hold roll excursion too large: {max_abs_roll:.3f} > {float(max_abs_roll_max):.3f}"
                ), _summary(
                    {
                        "steps": steps,
                        "target_heading_deg": target_heading,
                        "target_pitch_deg": target_pitch,
                        "final_heading_error_deg": final_heading_error,
                        "final_pitch_error_deg": final_pitch_error,
                        "max_abs_heading_error_deg": max_abs_heading_error,
                        "max_abs_pitch_error_deg": max_abs_pitch_error,
                        "max_abs_roll_deg": max_abs_roll,
                        "min_alt_m": min_alt,
                    }
                )
            return True, (
                "kernel heading/pitch-hold contract passed "
                f"(heading={float(final_inst.heading):.2f}, track={float(final_inst.ground_track):.2f}, "
                f"track-heading={_wrap_deg(float(final_inst.ground_track) - float(final_inst.heading)):.2f})"
            ), _summary(
                {
                    "steps": steps,
                    "target_heading_deg": target_heading,
                    "target_pitch_deg": target_pitch,
                    "final_heading_error_deg": final_heading_error,
                    "final_pitch_error_deg": final_pitch_error,
                    "max_abs_heading_error_deg": max_abs_heading_error,
                    "max_abs_pitch_error_deg": max_abs_pitch_error,
                    "max_abs_roll_deg": max_abs_roll,
                    "min_alt_m": min_alt,
                }
            )

        if controller_kind == "free_fall_idle":
            dt = float(sim.get_time_step())
            if dt <= 0.0:
                return False, f"invalid sim time step {dt}", {}
            max_steps = int(kernel_spec.get("max_steps", 20))
            initial_pos = sim.get_unit_position(agent_id)
            initial_vel = sim.get_unit_velocity(agent_id)
            pa = _base_pilot_action()
            pa.throttle = float(kernel_spec.get("throttle", 0.0))
            pa.gear_handle = float(kernel_spec.get("gear_handle", 1.0))
            for _ in range(max_steps):
                sim.set_pilot_action(agent_id, pa)
                sim.step()
            final_pos = sim.get_unit_position(agent_id)
            final_vel = sim.get_unit_velocity(agent_id)
            elapsed_s = max(1.0e-9, max_steps * dt)
            mean_vertical_accel = (float(final_vel[2]) - float(initial_vel[2])) / elapsed_s
            accel_range = list(checks.get("mean_vertical_accel_range", [-10.8, -8.8]))
            if len(accel_range) >= 2:
                accel_lo = float(accel_range[0])
                accel_hi = float(accel_range[1])
                if not (accel_lo <= mean_vertical_accel <= accel_hi):
                    return False, (
                        f"mean vertical accel out of range: {mean_vertical_accel:.3f} "
                        f"not in [{accel_lo:.3f}, {accel_hi:.3f}]"
                    ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
            final_alt_max = checks.get("final_alt_max", None)
            if final_alt_max is not None and float(final_pos[2]) > float(final_alt_max):
                return False, (
                    f"expected final altitude <= {float(final_alt_max):.3f}, got {float(final_pos[2]):.6f}"
                ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
            final_vz_max = checks.get("final_vz_max", None)
            if final_vz_max is not None and float(final_vel[2]) > float(final_vz_max):
                return False, (
                    f"expected final vz <= {float(final_vz_max):.3f}, got {float(final_vel[2]):.6f}"
                ), _summary({"steps": max_steps, "mean_vertical_accel_mps2": mean_vertical_accel})
            return True, "kernel free-fall contract passed", _summary(
                {
                    "steps": max_steps,
                    "mean_vertical_accel_mps2": mean_vertical_accel,
                    "initial_alt_m": float(initial_pos[2]),
                    "initial_vz_mps": float(initial_vel[2]),
                }
            )

        raise ValueError(f"Unknown kernel_flight controller_kind: {controller_kind}")

    if check_kind == "kernel_flight_regression":
        ok, message, _summary = _run_kernel_flight_contract(spec)
        return ok, message

    if check_kind == "kernel_flight_repeatability":
        repeat_runs = max(2, int(spec.get("repeat_runs", 2)))
        abs_tol = float(spec.get("float_abs_tol", 1.0e-6))
        rel_tol = float(spec.get("float_rel_tol", 1.0e-6))
        compare_keys = [str(x) for x in list(spec.get("compare_keys", []) or [])]
        baseline_summary: dict[str, Any] | None = None
        for run_idx in range(repeat_runs):
            ok, message, summary = _run_kernel_flight_contract(spec)
            if not ok:
                return False, f"repeat run {run_idx + 1} failed: {message}"
            if baseline_summary is None:
                baseline_summary = dict(summary)
                if not compare_keys:
                    compare_keys = sorted(baseline_summary.keys())
                continue
            for key in compare_keys:
                mismatch = _compare_kernel_summary_values(
                    baseline_summary.get(key),
                    summary.get(key),
                    key=key,
                    abs_tol=abs_tol,
                    rel_tol=rel_tol,
                )
                if mismatch is not None:
                    return False, f"repeatability mismatch on run {run_idx + 1}: {mismatch}"
        return True, f"kernel flight repeatability contract passed for {repeat_runs} run(s)"

    if check_kind == "kernel_flight_parameter_scan":
        cases = list(spec.get("cases", []) or [])
        if not cases:
            raise ValueError("kernel_flight_parameter_scan requires non-empty 'cases'")

        def _resolve_case_spec(case_spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
            resolved = copy.deepcopy(case_spec)
            cleanup_paths: list[str] = []
            if (
                "scenario" not in resolved
                and ("scenario_base" in resolved or "scenario_inline" in resolved)
            ):
                scenario_path, should_cleanup = _materialize_scenario_path(resolved)
                resolved["scenario"] = scenario_path
                resolved.pop("scenario_base", None)
                resolved.pop("scenario_patch", None)
                resolved.pop("scenario_inline", None)
                if should_cleanup:
                    cleanup_paths.append(scenario_path)
            return resolved, cleanup_paths

        base_case_spec = copy.deepcopy(spec)
        for key in ("cases", "ordered_field_checks", "case_field_checks"):
            base_case_spec.pop(key, None)
        base_case_spec["check_kind"] = "kernel_flight_regression"

        case_summaries: dict[str, dict[str, Any]] = {}
        for idx, raw_case in enumerate(cases):
            if not isinstance(raw_case, dict):
                raise ValueError("kernel_flight_parameter_scan cases must be JSON objects")
            case_name = str(raw_case.get("name", f"case_{idx + 1}"))
            case_overrides = raw_case.get("spec", raw_case.get("overrides", None))
            if case_overrides is None:
                case_overrides = {k: copy.deepcopy(v) for k, v in raw_case.items() if k != "name"}
            if not isinstance(case_overrides, dict):
                raise ValueError(f"kernel_flight_parameter_scan case {case_name!r} overrides must be a JSON object")
            merged_case_spec = _deep_merge(base_case_spec, case_overrides)
            merged_case_spec.pop("name", None)
            run_case_spec, cleanup_paths = _resolve_case_spec(merged_case_spec)
            try:
                ok, message, summary = _run_kernel_flight_contract(run_case_spec)
            finally:
                for cleanup_path in cleanup_paths:
                    try:
                        os.unlink(cleanup_path)
                    except OSError:
                        pass
            if not ok:
                return False, f"scan case {case_name} failed: {message}"
            case_summaries[case_name] = dict(summary)

        for raw_check in list(spec.get("case_field_checks", []) or []):
            if not isinstance(raw_check, dict):
                raise ValueError("kernel_flight_parameter_scan case_field_checks entries must be JSON objects")
            case_name = str(raw_check["case"])
            field_name = str(raw_check["field"])
            if case_name not in case_summaries:
                return False, f"unknown scan case in case_field_checks: {case_name!r}"
            if field_name not in case_summaries[case_name]:
                return False, f"scan case {case_name!r} missing summary field {field_name!r}"
            err = _check_optional_range(
                float(case_summaries[case_name][field_name]),
                raw_check,
                label=f"{case_name}.{field_name}",
            )
            if err is not None:
                return False, err

        for raw_check in list(spec.get("ordered_field_checks", []) or []):
            if not isinstance(raw_check, dict):
                raise ValueError("kernel_flight_parameter_scan ordered_field_checks entries must be JSON objects")
            field_name = str(raw_check["field"])
            case_order = [str(x) for x in list(raw_check.get("case_order", raw_check.get("order", [])) or [])]
            if len(case_order) < 2:
                raise ValueError("ordered_field_checks requires at least two case names")
            direction = str(raw_check.get("direction", "increasing")).strip().lower()
            min_delta = float(raw_check.get("min_delta", 0.0))
            for case_name in case_order:
                if case_name not in case_summaries:
                    return False, f"unknown scan case in ordered_field_checks: {case_name!r}"
                if field_name not in case_summaries[case_name]:
                    return False, f"scan case {case_name!r} missing summary field {field_name!r}"
            for prev_name, curr_name in zip(case_order[:-1], case_order[1:]):
                prev_value = float(case_summaries[prev_name][field_name])
                curr_value = float(case_summaries[curr_name][field_name])
                if direction == "increasing":
                    if (curr_value - prev_value) < min_delta:
                        return False, (
                            f"{field_name} was not increasing enough from {prev_name} to {curr_name}: "
                            f"{curr_value:.3f} - {prev_value:.3f} < {min_delta:.3f}"
                        )
                elif direction == "decreasing":
                    if (prev_value - curr_value) < min_delta:
                        return False, (
                            f"{field_name} was not decreasing enough from {prev_name} to {curr_name}: "
                            f"{prev_value:.3f} - {curr_value:.3f} < {min_delta:.3f}"
                        )
                else:
                    raise ValueError(f"unsupported ordered_field_checks direction: {direction!r}")

        return True, f"kernel flight parameter scan passed for {len(case_summaries)} case(s)"

    if check_kind == "task_order_and_mission_link":
        import ef_py
        from python.rl.tasking.common_core_profile import (
            apply_leader_intent_common_core_defaults,
            apply_leader_intent_common_core_spec,
            apply_pilot_report_common_core_defaults,
            apply_pilot_report_common_core_spec,
            apply_task_order_common_core_defaults,
            apply_task_order_common_core_spec,
        )
        from python.rl.tasking.bridge import normalize_task_order_spec

        def _spawn_aircraft(sim):
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            return sim.spawn_unit(
                ef_py.Side.Blue,
                "F-16C_Block50",
                0.0,
                0.0,
                1200.0,
                90.0,
                0.0,
                0.0,
                90.0,
                0.0,
                0.0,
            )

        sim = ef_py.SimulationKernel()
        entity_id = _spawn_aircraft(sim)

        order_spec = normalize_task_order_spec(dict(spec.get("task_order", {}) or {}))
        order = ef_py.TaskOrder()
        order.task_id = int(order_spec.get("task_id", 77))
        order.task_type = _enum_value_or_default(ef_py.TaskType, order_spec.get("task_type", None), "Idle")
        order.priority = int(order_spec.get("priority", 3))
        order.issuer_id = int(order_spec.get("issuer_id", 1001))
        order.assignee_id = int(order_spec.get("assignee_id", entity_id))
        order.anchor_x_m = float(order_spec.get("anchor_x_m", 12000.0))
        order.anchor_y_m = float(order_spec.get("anchor_y_m", -8000.0))
        order.anchor_z_m = float(order_spec.get("anchor_z_m", 6500.0))
        order.station_type = _enum_value_or_default(ef_py.StationType, order_spec.get("station_type", None), "Racetrack")
        order.station_radius_m = float(order_spec.get("station_radius_m", 18000.0))
        order.station_leg_length_m = float(order_spec.get("station_leg_length_m", 30000.0))
        order.station_heading_deg = float(order_spec.get("station_heading_deg", 45.0))
        order.target_altitude_m = float(order_spec.get("target_altitude_m", 7000.0))
        order.target_speed_mps = float(order_spec.get("target_speed_mps", 210.0))
        order.on_station_time_s = float(order_spec.get("on_station_time_s", 900.0))
        order.recovery_base_id = int(order_spec.get("recovery_base_id", 55))
        order.recovery_runway_id = int(order_spec.get("recovery_runway_id", 7))
        if hasattr(order, "recovery_approach_type"):
            order.recovery_approach_type = _recovery_approach_enum(order_spec.get("recovery_approach_type", "None"))
        apply_task_order_common_core_spec(order, order_spec)
        apply_task_order_common_core_defaults(order)
        sim.set_task_order(entity_id, order)

        stored_order = sim.get_task_order(entity_id)
        if not bool(stored_order.active):
            return False, "stored task order is not active"
        if int(stored_order.task_id) != int(order.task_id):
            return False, f"stored task_id mismatch: {stored_order.task_id} != {order.task_id}"
        if int(stored_order.task_type) != int(order.task_type):
            return False, f"stored task_type mismatch: {stored_order.task_type} != {order.task_type}"
        if int(stored_order.station_type) != int(order.station_type):
            return False, f"stored station_type mismatch: {stored_order.station_type} != {order.station_type}"
        if not math.isclose(float(stored_order.target_speed_mps), float(order.target_speed_mps), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored target_speed mismatch: {stored_order.target_speed_mps} != {order.target_speed_mps}"
        ok, detail = _check_fields(
            stored_order,
            order,
            _common_core_field_names("task_order"),
            label="task_order",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_order,
            order,
            _air_task_order_field_names(),
            label="task_order_air",
        )
        if not ok:
            return False, detail

        intent_spec = dict(spec.get("leader_intent", {}) or {})
        intent = ef_py.LeaderIntent()
        intent.phase_id = _enum_value_or_default(ef_py.LeaderPhase, intent_spec.get("phase_id", None), "TransitToStation")
        intent.command_code = int(intent_spec.get("command_code", 3))
        if hasattr(intent, "route_ref_id"):
            intent.route_ref_id = int(intent_spec.get("route_ref_id", 0))
        if hasattr(intent, "recovery_base_id"):
            intent.recovery_base_id = int(intent_spec.get("recovery_base_id", order.recovery_base_id))
        if hasattr(intent, "recovery_runway_id"):
            intent.recovery_runway_id = int(intent_spec.get("recovery_runway_id", order.recovery_runway_id))
        if hasattr(intent, "recovery_approach_type"):
            intent.recovery_approach_type = _recovery_approach_enum(
                intent_spec.get("recovery_approach_type", order_spec.get("recovery_approach_type", "None"))
            )
        intent.cmd_heading_deg = float(intent_spec.get("cmd_heading_deg", 135.0))
        intent.cmd_altitude_m = float(intent_spec.get("cmd_altitude_m", 6800.0))
        intent.cmd_speed_mps = float(intent_spec.get("cmd_speed_mps", 205.0))
        intent.approach_armed = bool(intent_spec.get("approach_armed", False))
        apply_leader_intent_common_core_spec(intent, intent_spec)
        apply_leader_intent_common_core_defaults(intent, order=order, default_tactical_unit_id=int(entity_id))
        sim.set_leader_intent(entity_id, intent)

        stored_intent = sim.get_leader_intent(entity_id)
        if not bool(stored_intent.active):
            return False, "stored leader intent is not active"
        if int(stored_intent.phase_id) != int(intent.phase_id):
            return False, f"stored phase_id mismatch: {stored_intent.phase_id} != {intent.phase_id}"
        if int(stored_intent.command_code) != int(intent.command_code):
            return False, f"stored command_code mismatch: {stored_intent.command_code} != {intent.command_code}"
        if not math.isclose(float(stored_intent.cmd_heading_deg), float(intent.cmd_heading_deg), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored intent heading mismatch: {stored_intent.cmd_heading_deg} != {intent.cmd_heading_deg}"
        ok, detail = _check_fields(
            stored_intent,
            intent,
            _common_core_field_names("leader_intent"),
            label="leader_intent",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_intent,
            intent,
            _air_leader_intent_field_names(),
            label="leader_intent_air",
        )
        if not ok:
            return False, detail

        report_spec = dict(spec.get("pilot_report", {}) or {})
        report = ef_py.PilotReport()
        report.report_type = _enum_value_or_default(ef_py.CommMsgType, report_spec.get("report_type", None), "REP_ON_STATION")
        report.sender_id = int(report_spec.get("sender_id", entity_id))
        report.task_id = int(report_spec.get("task_id", order.task_id))
        report.phase_id = int(_enum_value_or_default(ef_py.LeaderPhase, report_spec.get("phase_id", None), "OnStation"))
        report.timestamp_s = float(report_spec.get("timestamp_s", 12.5))
        report.status_value = float(report_spec.get("status_value", 1.0))
        report.location_x_m = float(report_spec.get("location_x_m", 12010.0))
        report.location_y_m = float(report_spec.get("location_y_m", -7990.0))
        report.location_z_m = float(report_spec.get("location_z_m", 6980.0))
        apply_pilot_report_common_core_spec(report, report_spec)
        apply_pilot_report_common_core_defaults(report, order=order, default_tactical_unit_id=int(entity_id))
        sim.set_pilot_report(entity_id, report)

        stored_report = sim.get_pilot_report(entity_id)
        if not bool(stored_report.active):
            return False, "stored pilot report is not active"
        if int(stored_report.report_type) != int(report.report_type):
            return False, f"stored report_type mismatch: {stored_report.report_type} != {report.report_type}"
        if int(stored_report.task_id) != int(report.task_id):
            return False, f"stored report task_id mismatch: {stored_report.task_id} != {report.task_id}"
        if not math.isclose(float(stored_report.location_z_m), float(report.location_z_m), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored report altitude mismatch: {stored_report.location_z_m} != {report.location_z_m}"
        ok, detail = _check_fields(
            stored_report,
            report,
            _common_core_field_names("pilot_report"),
            label="pilot_report",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_report,
            report,
            _air_pilot_report_field_names(),
            label="pilot_report_air",
        )
        if not ok:
            return False, detail

        latency_sim = ef_py.SimulationKernel()
        latency_entity_id = _spawn_aircraft(latency_sim)
        command_link = dict(spec.get("command_link", {}) or {})
        latency_sim.set_command_link(
            latency_entity_id,
            float(command_link.get("latency_s", 0.2)),
            float(command_link.get("loss_probability", 0.0)),
        )
        mission_spec = dict(spec.get("mission_command", {}) or {})
        command = ef_py.MissionCommand()
        command.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 222.0))
        command.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 5000.0))
        command.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 190.0))
        command.command_code = int(mission_spec.get("command_code", 4))
        if hasattr(command, "route_ref_id"):
            command.route_ref_id = int(mission_spec.get("route_ref_id", 0))
        if hasattr(command, "recovery_base_id"):
            command.recovery_base_id = int(mission_spec.get("recovery_base_id", order.recovery_base_id))
        if hasattr(command, "recovery_runway_id"):
            command.recovery_runway_id = int(mission_spec.get("recovery_runway_id", order.recovery_runway_id))
        if hasattr(command, "recovery_approach_type"):
            command.recovery_approach_type = _recovery_approach_enum(
                mission_spec.get("recovery_approach_type", order_spec.get("recovery_approach_type", "None"))
            )
        latency_sim.set_mission_command(latency_entity_id, command)

        before = latency_sim.get_mission_command(latency_entity_id)
        if bool(before.active):
            return False, "mission command should still be inactive before command-link latency elapses"
        if int(before.command_code) != int(spec.get("pre_link_command_code", 0)):
            return False, f"unexpected pre-link command_code {before.command_code}"
        for _ in range(int(spec.get("link_settle_steps", 20))):
            latency_sim.step()
        after = latency_sim.get_mission_command(latency_entity_id)
        if not bool(after.active):
            return False, "mission command did not activate after command-link latency"
        if int(after.command_code) != int(command.command_code):
            return False, f"post-link command_code mismatch: {after.command_code} != {command.command_code}"
        if not math.isclose(float(after.cmd_heading_deg), float(command.cmd_heading_deg), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"post-link heading mismatch: {after.cmd_heading_deg} != {command.cmd_heading_deg}"
        if not math.isclose(float(after.cmd_altitude_m), float(command.cmd_altitude_m), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"post-link altitude mismatch: {after.cmd_altitude_m} != {command.cmd_altitude_m}"
        if hasattr(command, "recovery_base_id") and int(getattr(after, "recovery_base_id", 0)) != int(getattr(command, "recovery_base_id", 0)):
            return False, f"post-link recovery_base_id mismatch: {after.recovery_base_id} != {command.recovery_base_id}"
        if hasattr(command, "recovery_runway_id") and int(getattr(after, "recovery_runway_id", 0)) != int(getattr(command, "recovery_runway_id", 0)):
            return False, f"post-link recovery_runway_id mismatch: {after.recovery_runway_id} != {command.recovery_runway_id}"
        if hasattr(command, "recovery_approach_type") and int(getattr(after, "recovery_approach_type", 0)) != int(getattr(command, "recovery_approach_type", 0)):
            return False, f"post-link recovery_approach_type mismatch: {after.recovery_approach_type} != {command.recovery_approach_type}"
        return True, "task order / mission link contract passed"

    if check_kind == "task_order_common_core":
        import ef_py
        from python.rl.tasking.common_core_profile import (
            apply_task_order_common_core_defaults,
            apply_task_order_common_core_spec,
        )
        from python.rl.tasking.bridge import normalize_task_order_spec

        order_spec = normalize_task_order_spec(dict(spec.get("task_order", {}) or {}))
        order = ef_py.TaskOrder()
        apply_task_order_common_core_spec(order, order_spec)
        apply_task_order_common_core_defaults(
            order,
            task_name=str(spec.get("task_name", "") or "").strip().upper() or None,
            phase_name=str(spec.get("phase_name", "") or "").strip().lower() or None,
            force_task_family=bool(spec.get("force_task_family", False)),
            force_coordination_mode=bool(spec.get("force_coordination_mode", False)),
        )

        expected_common = dict(spec.get("expected_common_core", spec.get("expected_task_order", {})) or {})
        if not expected_common:
            expected_common = dict(order_spec)

        expected = ef_py.TaskOrder()
        apply_task_order_common_core_spec(expected, expected_common)
        apply_task_order_common_core_defaults(
            expected,
            task_name=str(spec.get("task_name", "") or "").strip().upper() or None,
            phase_name=str(spec.get("phase_name", "") or "").strip().lower() or None,
            force_task_family=bool(spec.get("force_task_family", False)),
            force_coordination_mode=bool(spec.get("force_coordination_mode", False)),
        )
        ok, detail = _check_fields(order, expected, _common_core_field_names("task_order"), label="task_order_common_core")
        if not ok:
            return False, detail
        return True, "task order common-core contract passed"

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

        def _bearing_deg(x0: float, y0: float, x1: float, y1: float) -> float:
            return float((math.degrees(math.atan2(float(x1) - float(x0), float(y1) - float(y0))) + 360.0) % 360.0)

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
                desired_bearing = _bearing_deg(
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

    if check_kind == "takeoff_safe_action_bias":
        try:
            import gymnasium as gym
            from stable_baselines3 import PPO
            from train import apply_safe_action_bias
        except ModuleNotFoundError as exc:
            raise ContractSkipped(f"optional dependency missing: {exc.name}") from exc
        import numpy as np

        class _DummyTakeoff4Env(gym.Env):
            metadata = {}

            def __init__(self):
                super().__init__()
                self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
                self.action_space = gym.spaces.Box(
                    low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
                    high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                    dtype=np.float32,
                )

            def reset(self, *, seed=None, options=None):
                super().reset(seed=seed)
                return np.zeros((4,), dtype=np.float32), {}

            def step(self, action):
                _ = action
                return np.zeros((4,), dtype=np.float32), 0.0, False, False, {}

        env = _DummyTakeoff4Env()
        model = PPO(
            "MlpPolicy",
            env,
            n_steps=int(spec.get("n_steps", 8)),
            batch_size=int(spec.get("batch_size", 8)),
            n_epochs=int(spec.get("n_epochs", 1)),
            learning_rate=float(spec.get("learning_rate", 3.0e-4)),
            gamma=float(spec.get("gamma", 0.99)),
            verbose=0,
        )
        scenario_path = resolve_repo_path(str(spec.get("scenario", "scenarios/takeoff/takeoff_stage1_runway45.json")))
        apply_safe_action_bias(model, str(spec.get("action_mode", "takeoff4")), scenario_path)
        bias = model.policy.action_net.bias.detach().cpu().numpy()
        if bias.shape[0] < int(spec.get("min_action_dim", 4)):
            return False, f"unexpected action bias shape {bias.shape}"
        if abs(float(bias[3]) - float(spec.get("expected_throttle_bias", 1.0))) > 1.0e-6:
            return False, f"takeoff4 throttle bias was not initialized high: {bias}"
        for idx in list(spec.get("neutral_indices", [0, 1, 2])) or []:
            if abs(float(bias[int(idx)])) > 1.0e-6:
                return False, f"takeoff4 lateral controls should start neutral: {bias}"
        return True, "takeoff safe action bias contract passed"

    if check_kind == "scripted_stable_flight_rudder_sign":
        import numpy as np
        from python.rl.control.scripted_stable_flight import ScriptedStableFlightController

        ctrl = ScriptedStableFlightController(
            action_dim=int(spec.get("action_dim", 17)),
            dt=float(spec.get("dt", 0.05)),
        )
        obs = {
            "mission": np.asarray(spec.get("mission", [3.0, 90.0, 1200.0, 210.0]), dtype=np.float32),
            "instruments": np.zeros((int(spec.get("instrument_dim", 42)),), dtype=np.float32),
        }
        obs["instruments"][int(spec.get("beta_index", 6))] = float(spec.get("beta_deg", 5.0))
        obs["instruments"][int(spec.get("yaw_rate_index", 14))] = float(spec.get("yaw_rate_dps", 10.0))
        ctrl.reset(obs)
        act = ctrl.step(obs)
        if float(act[int(spec.get("rudder_index", 2))]) <= float(spec.get("rudder_min", 0.0)):
            return False, f"expected positive rudder command for positive beta/yaw-rate, got {act}"
        return True, "scripted stable-flight rudder sign contract passed"

    if check_kind == "replay_expert_actions":
        import tempfile
        import numpy as np
        from python.world_model.replay import DatasetSpec, Episode, EpisodeDataset, EpisodeStore

        def _make_episode(*, T: int, obs_dim: int, act_dim: int, include_expert: bool) -> Any:
            rng = np.random.default_rng(0)
            obs_vec = rng.standard_normal((T + 1, obs_dim), dtype=np.float32)
            actions = rng.standard_normal((T, act_dim), dtype=np.float32)
            rewards = rng.standard_normal((T,), dtype=np.float32)
            dones = np.zeros((T,), dtype=np.bool_)
            dones[-1] = True
            expert_actions = actions + float(spec.get("expert_offset", 0.123)) if include_expert else None
            return Episode(obs_vec=obs_vec, actions=actions, rewards=rewards, dones=dones, expert_actions=expert_actions)

        with tempfile.TemporaryDirectory() as td:
            roundtrip_spec = dict(spec.get("roundtrip", {}) or {})
            ds_spec = DatasetSpec(
                action_dim=int(roundtrip_spec.get("action_dim", 3)),
                obs_vec_dim=int(roundtrip_spec.get("obs_dim", 4)),
                action_low=-np.ones((int(roundtrip_spec.get("action_dim", 3)),), dtype=np.float32),
                action_high=np.ones((int(roundtrip_spec.get("action_dim", 3)),), dtype=np.float32),
            )
            store = EpisodeStore(td, ds_spec)
            ep = _make_episode(
                T=int(roundtrip_spec.get("T", 8)),
                obs_dim=int(roundtrip_spec.get("obs_dim", 4)),
                act_dim=int(roundtrip_spec.get("action_dim", 3)),
                include_expert=True,
            )
            store.add(ep, seed=int(roundtrip_spec.get("seed", 123)))
            ds = EpisodeDataset(td)
            loaded = ds.get_episode(0)
            if loaded.expert_actions is None:
                return False, "expert_actions missing after roundtrip save/load"
            np.testing.assert_allclose(loaded.expert_actions, ep.expert_actions)
            batch = ds.sample_batch(
                batch_size=int(roundtrip_spec.get("batch_size", 2)),
                seq_len=int(roundtrip_spec.get("seq_len", 5)),
                rng=np.random.default_rng(int(roundtrip_spec.get("batch_rng_seed", 1))),
            )
            if "expert_actions" not in batch:
                return False, "expert_actions missing from sampled batch"
            if tuple(batch["expert_actions"].shape) != tuple(batch["actions"].shape):
                return False, (
                    f"expert_actions batch shape mismatch: {batch['expert_actions'].shape} "
                    f"!= {batch['actions'].shape}"
                )

        with tempfile.TemporaryDirectory() as td2:
            fallback_spec = dict(spec.get("fallback", {}) or {})
            ds_spec2 = DatasetSpec(
                action_dim=int(fallback_spec.get("action_dim", 2)),
                obs_vec_dim=int(fallback_spec.get("obs_dim", 3)),
                action_low=-np.ones((int(fallback_spec.get("action_dim", 2)),), dtype=np.float32),
                action_high=np.ones((int(fallback_spec.get("action_dim", 2)),), dtype=np.float32),
            )
            store2 = EpisodeStore(td2, ds_spec2)
            ep2 = _make_episode(
                T=int(fallback_spec.get("T", 6)),
                obs_dim=int(fallback_spec.get("obs_dim", 3)),
                act_dim=int(fallback_spec.get("action_dim", 2)),
                include_expert=False,
            )
            store2.add(ep2)
            ds2 = EpisodeDataset(td2)
            batch2 = ds2.sample_batch(
                batch_size=int(fallback_spec.get("batch_size", 1)),
                seq_len=int(fallback_spec.get("seq_len", 6)),
                rng=np.random.default_rng(int(fallback_spec.get("batch_rng_seed", 2))),
            )
            np.testing.assert_allclose(batch2["expert_actions"], batch2["actions"])
        return True, "replay expert-actions contract passed"

    if check_kind == "continuous_waypoint_template_geometry":
        def _wrap_deg_local(angle_deg: float) -> float:
            return float((float(angle_deg) + 180.0) % 360.0 - 180.0)

        def _bearing_deg(dx: float, dy: float) -> float:
            return float((math.degrees(math.atan2(float(dx), float(dy))) + 360.0) % 360.0)

        def _turn_radius_m(speed_mps: float, bank_limit_deg: float) -> float:
            bank_rad = math.radians(max(1.0, min(80.0, float(bank_limit_deg))))
            tanb = math.tan(bank_rad)
            if abs(tanb) <= 1.0e-6:
                return float("inf")
            v = max(30.0, float(speed_mps))
            return (v * v) / (9.80665 * abs(tanb))

        scenario_paths = [resolve_repo_path(str(path)) for path in list(spec.get("scenarios", []) or [])]
        if not scenario_paths:
            return False, "continuous_waypoint_template_geometry requires non-empty scenarios list"
        for path in scenario_paths:
            with open(path, "r", encoding="utf-8") as f:
                scenario = json.load(f)
            spawn = next(ent for ent in scenario["entities"] if bool(ent.get("is_agent", False)))
            spawn_x = float(spawn["pos"][0])
            spawn_y = float(spawn["pos"][1])
            bank_limit_deg = float(scenario["mission_command"]["lnav_bank_limit_deg"])
            runway_heading_deg = float(scenario["mission_command"]["post_waypoint_transition"]["target_heading"])
            templates = list(scenario["mission_command"]["randomization"]["waypoint_templates"] or [])
            for ti, route in enumerate(templates):
                points = [(spawn_x, spawn_y)] + [(float(wp["x"]), float(wp["y"])) for wp in route]
                modes = [str(wp.get("waypoint_mode", "")).strip().lower() for wp in route]
                if not modes or modes[-1] != "flyover":
                    return False, f"{os.path.basename(path)} template {ti}: final waypoint must remain flyover"
                if any(mode == "flyover" for mode in modes[-3:-1]):
                    return False, f"{os.path.basename(path)} template {ti}: late arrival bridge should not require stacked flyover fixes"
                legs = []
                for i in range(1, len(points)):
                    dx = points[i][0] - points[i - 1][0]
                    dy = points[i][1] - points[i - 1][1]
                    legs.append((math.hypot(dx, dy), _bearing_deg(dx, dy)))
                final_track = float(legs[-1][1])
                if abs(_wrap_deg_local(final_track - runway_heading_deg)) > float(spec.get("final_leg_alignment_max_deg", 15.0)):
                    return False, f"{os.path.basename(path)} template {ti}: final leg track {final_track:.1f} not aligned with runway"
                for wi in range(1, len(route)):
                    prev_leg_m, prev_track_deg = legs[wi - 1]
                    next_leg_m, next_track_deg = legs[wi]
                    turn_abs_deg = abs(_wrap_deg_local(next_track_deg - prev_track_deg))
                    if turn_abs_deg > float(spec.get("turn_abs_max_deg", 85.0)):
                        return False, f"{os.path.basename(path)} template {ti}: turn {wi} too sharp ({turn_abs_deg:.1f} deg)"
                    speed_mps = float(route[wi - 1].get("speed_mps", scenario["mission_command"]["target_speed"]))
                    radius_m = float(route[wi - 1].get("radius_m", scenario["mission_command"].get("waypoint_radius_m", 1000.0)))
                    lead_m = _turn_radius_m(speed_mps, bank_limit_deg) * math.tan(0.5 * math.radians(turn_abs_deg))
                    lead_budget_m = float(spec.get("lead_budget_leg_fraction", 0.45)) * min(prev_leg_m, next_leg_m) - max(
                        radius_m,
                        float(spec.get("lead_budget_clearance_m", 800.0)),
                    )
                    if lead_m > lead_budget_m + float(spec.get("lead_budget_tolerance_m", 1.0)):
                        return False, (
                            f"{os.path.basename(path)} template {ti}: turn {wi} lead {lead_m:.1f} exceeds budget {lead_budget_m:.1f}"
                        )
        return True, "continuous waypoint-template geometry contract passed"

    if check_kind == "landing_entity_spawn_randomization":
        import numpy as np
        from gym_envs.scenario_loader import ScenarioLoader

        loader = ScenarioLoader(None)
        loader.rng = np.random.RandomState(int(spec.get("seed", 7)))
        ent = copy.deepcopy(dict(spec.get("entity", {}) or {}))
        pos, vel, heading, pitch, roll = loader._sample_entity_spawn(ent)
        _ = pitch, roll
        if pos == ent["pos"] and vel == ent["vel"] and abs(float(heading) - float(ent.get("heading", 0.0))) < 1.0e-9:
            return False, "entity randomization did not change the spawn"
        alt_bounds = list(spec.get("altitude_offset_bounds", [-20.0, 20.0]))
        hdg_bounds = list(spec.get("heading_offset_bounds", [-5.0, 5.0]))
        sink_bounds = list(spec.get("sink_rate_bounds", [-2.0, -1.0]))
        base_alt = float(ent["pos"][2])
        base_hdg = float(ent.get("heading", 0.0))
        if not (float(alt_bounds[0]) <= float(pos[2]) - base_alt <= float(alt_bounds[1])):
            return False, "altitude offset out of configured range"
        if not (float(hdg_bounds[0]) <= float(heading) - base_hdg <= float(hdg_bounds[1])):
            return False, "heading offset out of configured range"
        if not (float(sink_bounds[0]) <= float(vel[2]) <= float(sink_bounds[1])):
            return False, "sink rate out of configured range"
        return True, "landing entity spawn randomization contract passed"

    if check_kind == "scenario_loader_mission_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            expected_initial = dict(spec.get("expected_initial", {}) or {})
            for key, expected in expected_initial.items():
                got = loader.mission_cmd.get(key, None)
                if got != expected:
                    return False, f"initial mission_cmd[{key!r}] mismatch: {got!r} != {expected!r}"

            expected_task_order_common = dict(
                spec.get("expected_task_order_common_core", spec.get("expected_task_order", {})) or {}
            )
            expected_task_order_air = dict(spec.get("expected_task_order_air", {}) or {})
            if expected_task_order_common or expected_task_order_air:
                task_order_spec = loader._task_order_spec()
                enum_fields = _task_order_enum_fields()
                for key, expected in expected_task_order_common.items():
                    got = task_order_spec.get(key, None)
                    namespace = enum_fields.get(key, None)
                    if namespace is not None and isinstance(expected, str):
                        expected = getattr(namespace, expected, expected)
                    try:
                        same = int(got) == int(expected)
                    except Exception:
                        same = got == expected
                    if not same:
                        return False, f"task_order common-core[{key!r}] mismatch: {got!r} != {expected!r}"
                for key, expected in expected_task_order_air.items():
                    got = task_order_spec.get(key, None)
                    namespace = enum_fields.get(key, None)
                    if namespace is not None and isinstance(expected, str):
                        expected = getattr(namespace, expected, expected)
                    try:
                        same = int(got) == int(expected)
                    except Exception:
                        same = got == expected
                    if not same:
                        return False, f"task_order air[{key!r}] mismatch: {got!r} != {expected!r}"

            expected_post = dict(spec.get("expected_post_transition_air", spec.get("expected_post_transition", {})) or {})
            if expected_post:
                post = getattr(loader, "post_waypoint_transition", None)
                if not isinstance(post, dict):
                    return False, "expected normalized post_waypoint_transition, got none"
                for key, expected in expected_post.items():
                    got = post.get(key, None)
                    if got != expected:
                        return False, f"post transition field {key!r} mismatch: {got!r} != {expected!r}"

            if bool(spec.get("activate_post_transition", True)):
                transitioned = loader._activate_post_waypoint_transition()
                if not isinstance(transitioned, dict):
                    return False, "post_waypoint_transition did not activate"
                expected_activated = dict(spec.get("expected_activated", expected_post) or {})
                for key, expected in expected_activated.items():
                    got = loader.mission_cmd.get(key, None)
                    if got != expected:
                        return False, f"activated mission_cmd[{key!r}] mismatch: {got!r} != {expected!r}"
            return True, "scenario loader mission semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "scenario_loader_common_core_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            expected_task_order = dict(spec.get("expected_task_order_common_core", spec.get("expected_task_order", {})) or {})
            if not expected_task_order:
                return False, "scenario_loader_common_core_semantics requires expected_task_order_common_core"
            task_order_spec = loader._task_order_spec()
            enum_fields = _task_order_enum_fields()
            for key, expected in expected_task_order.items():
                got = task_order_spec.get(key, None)
                namespace = enum_fields.get(key, None)
                if namespace is not None and isinstance(expected, str):
                    expected = getattr(namespace, expected, expected)
                try:
                    same = int(got) == int(expected)
                except Exception:
                    same = got == expected
                if not same:
                    return False, f"task_order common-core[{key!r}] mismatch: {got!r} != {expected!r}"
            return True, "scenario loader common-core semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "naval_screen_contact_report":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            scenario_data = _load_json_file(scenario_path)
            entities_cfg = scenario_data.get("entities", [])
            if not isinstance(entities_cfg, list):
                return False, "scenario entities must be a list"

            entities_by_name = {
                str(item.get("name", "")).strip(): item
                for item in entities_cfg
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            }

            screen_name = str(spec.get("screen_entity", "")).strip()
            hvu_name = str(spec.get("hvu_entity", "")).strip()
            contact_name = str(spec.get("contact_entity", "")).strip()
            if not screen_name or not hvu_name or not contact_name:
                return False, "naval_screen_contact_report requires screen_entity, hvu_entity, and contact_entity"

            for required_name in (screen_name, hvu_name, contact_name):
                if required_name not in entities_by_name:
                    return False, f"scenario is missing entity {required_name!r}"

            def _entity_position(name: str) -> tuple[float, float, float]:
                pos = entities_by_name[name].get("pos", None)
                if not isinstance(pos, list) or len(pos) < 3:
                    raise ValueError(f"entity {name!r} is missing 3D pos")
                return (float(pos[0]), float(pos[1]), float(pos[2]))

            screen_pos0 = _entity_position(screen_name)
            hvu_pos0 = _entity_position(hvu_name)
            contact_pos0 = _entity_position(contact_name)

            checks = dict(spec.get("checks", {}) or {})
            initial_screen_hvu_m = float(math.dist(screen_pos0, hvu_pos0))
            initial_screen_contact_m = float(math.dist(screen_pos0, contact_pos0))
            initial_hvu_contact_m = float(math.dist(hvu_pos0, contact_pos0))

            for label, value in (
                ("initial_screen_hvu_separation_m", initial_screen_hvu_m),
                ("initial_screen_contact_range_m", initial_screen_contact_m),
                ("initial_hvu_contact_range_m", initial_hvu_contact_m),
            ):
                bounds = checks.get(label, None)
                if isinstance(bounds, dict):
                    message = _check_optional_range(value, bounds, label=label)
                    if message is not None:
                        return False, message

            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            if int(agent_id) != int(loader.entities.get(screen_name, 0)):
                return False, "screen entity was not selected as the active agent"

            screen_id = int(loader.entities[screen_name])
            hvu_id = int(loader.entities[hvu_name])
            contact_id = int(loader.entities[contact_name])

            max_steps = max(1, int(spec.get("max_steps", 80)))
            continue_after_contact_chain = bool(spec.get("continue_after_contact_chain", False))
            screen_required_first_source = int(spec.get("screen_required_first_source", 1))
            hvu_required_shared_source = int(spec.get("hvu_required_shared_source", 3))
            report_msg_type = int(getattr(ef_py.CommMsgType, str(spec.get("report_message_type", "ReportContact"))))
            forbid_hvu_local_source = bool(spec.get("forbid_hvu_local_source", True))

            first_screen_step = None
            first_hvu_shared_step = None
            first_hvu_report_step = None
            first_screen_source = None
            hvu_local_source_seen = False
            min_screen_hvu_m = float("inf")
            max_screen_hvu_m = 0.0
            min_hvu_contact_m = float("inf")

            for step in range(max_steps):
                sim.step()
                screen_obs = sim.get_agent_observation(screen_id)
                hvu_obs = sim.get_agent_observation(hvu_id)

                screen_tracks = {
                    int(getattr(track, "id", 0)): track
                    for track in getattr(screen_obs, "contacts", [])
                }
                hvu_tracks = {
                    int(getattr(track, "id", 0)): track
                    for track in getattr(hvu_obs, "contacts", [])
                }

                screen_pos = sim.get_unit_position(screen_id)
                hvu_pos = sim.get_unit_position(hvu_id)
                contact_pos = sim.get_unit_position(contact_id)

                screen_hvu_m = float(math.dist(screen_pos, hvu_pos))
                hvu_contact_m = float(math.dist(hvu_pos, contact_pos))
                min_screen_hvu_m = min(min_screen_hvu_m, screen_hvu_m)
                max_screen_hvu_m = max(max_screen_hvu_m, screen_hvu_m)
                min_hvu_contact_m = min(min_hvu_contact_m, hvu_contact_m)

                if contact_id in screen_tracks and first_screen_step is None:
                    first_screen_step = step + 1
                    first_screen_source = int(getattr(screen_tracks[contact_id], "source", 0))

                if contact_id in hvu_tracks:
                    track_source = int(getattr(hvu_tracks[contact_id], "source", 0))
                    if track_source == 1:
                        hvu_local_source_seen = True
                    if track_source == hvu_required_shared_source and first_hvu_shared_step is None:
                        first_hvu_shared_step = step + 1

                if first_hvu_report_step is None:
                    for msg in sim.get_unit_messages(hvu_id):
                        if (
                            int(getattr(msg, "type", 0)) == report_msg_type
                            and int(getattr(msg, "entity_ref", 0)) == contact_id
                        ):
                            first_hvu_report_step = step + 1
                            break

                if (
                    first_screen_step is not None
                    and first_hvu_shared_step is not None
                    and first_hvu_report_step is not None
                    and not continue_after_contact_chain
                ):
                    break

            if first_screen_step is None:
                return False, "screen never acquired the contact track"
            if int(first_screen_source or 0) != screen_required_first_source:
                return False, (
                    f"screen first contact source mismatch: {first_screen_source} != {screen_required_first_source}"
                )
            if first_hvu_shared_step is None:
                return False, "HVU never received the shared contact track"
            if first_hvu_report_step is None:
                return False, "HVU never received the contact report message"
            if first_hvu_shared_step < first_screen_step:
                return False, "HVU shared track appeared before the screen detected the contact"
            if first_hvu_report_step < first_screen_step:
                return False, "HVU report arrived before the screen detected the contact"
            if forbid_hvu_local_source and hvu_local_source_seen:
                return False, "HVU unexpectedly acquired a local radar track inside the blind-zone contract"

            runtime_checks = {
                "screen_first_detection_step": float(first_screen_step),
                "hvu_first_shared_track_step": float(first_hvu_shared_step),
                "hvu_first_report_step": float(first_hvu_report_step),
                "screen_hvu_separation_m_min": float(min_screen_hvu_m),
                "screen_hvu_separation_m_max": float(max_screen_hvu_m),
                "hvu_contact_closest_approach_m": float(min_hvu_contact_m),
            }
            for label, value in runtime_checks.items():
                bounds = checks.get(label, None)
                if isinstance(bounds, dict):
                    message = _check_optional_range(value, bounds, label=label)
                    if message is not None:
                        return False, message

            return True, "naval screen/contact reporting contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "mission_command_landing_gear_hold":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            mission_spec = dict(spec.get("mission_command", {}) or {})
            cmd = ef_py.MissionCommand()
            cmd.active = True
            cmd.command_code = int(mission_spec.get("command_code", 4))
            cmd.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 90.0))
            cmd.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 0.0))
            cmd.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 82.0))
            if hasattr(cmd, "recovery_base_id"):
                cmd.recovery_base_id = int(mission_spec.get("recovery_base_id", 1))
            if hasattr(cmd, "recovery_runway_id"):
                cmd.recovery_runway_id = int(mission_spec.get("recovery_runway_id", 1))
            if hasattr(cmd, "recovery_approach_type") and hasattr(ef_py, "RecoveryApproachType"):
                raw = mission_spec.get("recovery_approach_type", "ILS")
                cmd.recovery_approach_type = (
                    getattr(ef_py.RecoveryApproachType, str(raw), ef_py.RecoveryApproachType.ILS)
                    if isinstance(raw, str)
                    else ef_py.RecoveryApproachType(int(raw))
                )
            sim.set_mission_command(agent_id, cmd)

            min_gear_pos = float("inf")
            step_count = int(spec.get("step_count", 30))
            for _ in range(step_count):
                sim.step()
                truth = sim.get_agent_observation(agent_id)
                if float(getattr(truth, "health", 0.0)) <= 0.0:
                    return False, "aircraft crashed during landing gear hold contract"
                inst = sim.get_instrument_state(agent_id)
                min_gear_pos = min(min_gear_pos, float(getattr(inst, "gear_pos", 0.0)))

            required_min = float(spec.get("min_gear_pos", 0.9))
            if min_gear_pos < required_min:
                return False, f"landing command retracted gear too far: min gear_pos={min_gear_pos:.3f} < {required_min:.3f}"
            return True, f"landing gear hold contract passed with min gear_pos={min_gear_pos:.3f}"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "instrument_command_bug_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            mission_spec = dict(spec.get("mission_command", {}) or {})
            cmd = ef_py.MissionCommand()
            cmd.active = True
            cmd.command_code = int(mission_spec.get("command_code", 3))
            cmd.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 90.0))
            cmd.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 1200.0))
            cmd.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 180.0))
            if hasattr(cmd, "route_ref_id"):
                cmd.route_ref_id = int(mission_spec.get("route_ref_id", 0))
            if hasattr(cmd, "recovery_base_id"):
                cmd.recovery_base_id = int(mission_spec.get("recovery_base_id", 0))
            if hasattr(cmd, "recovery_runway_id"):
                cmd.recovery_runway_id = int(mission_spec.get("recovery_runway_id", 0))
            if hasattr(cmd, "recovery_approach_type") and hasattr(ef_py, "RecoveryApproachType"):
                raw = mission_spec.get("recovery_approach_type", "None")
                default_recovery = getattr(ef_py.RecoveryApproachType, "None")
                cmd.recovery_approach_type = (
                    getattr(ef_py.RecoveryApproachType, str(raw), default_recovery)
                    if isinstance(raw, str)
                    else ef_py.RecoveryApproachType(int(raw))
                )
            sim.set_mission_command(agent_id, cmd)

            inst = None
            step_count = max(1, int(spec.get("step_count", 1)))
            for _ in range(step_count):
                sim.step()
                truth = sim.get_agent_observation(agent_id)
                if float(getattr(truth, "health", 0.0)) <= 0.0:
                    return False, "aircraft crashed during instrument command bug contract"
                inst = sim.get_instrument_state(agent_id)

            if inst is None:
                inst = sim.get_instrument_state(agent_id)
            expected = dict(spec.get("expected", {}) or {})
            heading_tol = float(expected.get("heading_tol_deg", 1.0e-3))
            scalar_tol = float(expected.get("scalar_tol", 1.0e-3))

            if "cmd_heading_deg" in expected:
                actual_heading = float(
                    getattr(inst, "cmd_heading", getattr(inst, "cmd_heading_deg", 0.0))
                )
                if not math.isclose(actual_heading, float(expected["cmd_heading_deg"]), rel_tol=1.0e-6, abs_tol=heading_tol):
                    return False, (
                        f"instrument cmd_heading mismatch: {actual_heading:.6f} != "
                        f"{float(expected['cmd_heading_deg']):.6f}"
                    )
            if "cmd_alt_m" in expected:
                actual_alt = float(getattr(inst, "cmd_alt", getattr(inst, "cmd_alt_m", 0.0)))
                if not math.isclose(actual_alt, float(expected["cmd_alt_m"]), rel_tol=1.0e-6, abs_tol=scalar_tol):
                    return False, f"instrument cmd_alt mismatch: {actual_alt:.6f} != {float(expected['cmd_alt_m']):.6f}"
            if "cmd_speed_mps" in expected:
                actual_speed = float(getattr(inst, "cmd_speed", getattr(inst, "cmd_speed_mps", 0.0)))
                if not math.isclose(actual_speed, float(expected["cmd_speed_mps"]), rel_tol=1.0e-6, abs_tol=scalar_tol):
                    return False, (
                        f"instrument cmd_speed mismatch: {actual_speed:.6f} != "
                        f"{float(expected['cmd_speed_mps']):.6f}"
                    )
            return True, "instrument command bug semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "scripted_takeoff_takeoff2_throttle":
        import numpy as np
        from python.rl.control.scripted_takeoff import ScriptedTakeoffController

        ctrl = ScriptedTakeoffController(action_dim=2, dt=0.05)
        obs = {
            "instruments": np.asarray(spec["obs"]["instruments"], dtype=np.float32),
            "mission": np.asarray(spec["obs"]["mission"], dtype=np.float32),
        }
        ctrl.reset(obs)
        action = ctrl.step(obs)
        if tuple(action.shape) != (2,):
            return False, f"unexpected action shape {action.shape}"
        if abs(float(action[1]) - 1.0) > 1.0e-6:
            return False, f"takeoff2 throttle axis was modified during departure hold: {action}"
        return True, "scripted takeoff takeoff2 throttle contract passed"

    if check_kind == "scripted_takeoff_clearance_hold":
        import numpy as np
        from python.rl.control.scripted_takeoff import ScriptedTakeoffController

        ctrl = ScriptedTakeoffController(action_dim=4, dt=0.05)
        obs = {
            "instruments": np.asarray(spec["obs"]["instruments"], dtype=np.float32),
            "mission": np.asarray(spec["obs"]["mission"], dtype=np.float32),
        }
        ctrl.reset(obs)
        action = ctrl.step(obs)
        if tuple(action.shape) != (4,):
            return False, f"unexpected action shape {action.shape}"
        if abs(float(action[3])) > 1.0e-6:
            return False, f"throttle should remain idle before clearance: {action}"
        return True, "scripted takeoff clearance hold contract passed"

    if check_kind == "scripted_landing_controller":
        import numpy as np
        from python.rl.control.scripted_landing import ScriptedLandingController

        for idx, case in enumerate(list(spec.get("cases", []) or []), start=1):
            obs = {
                "mission": np.asarray(case["mission"], dtype=np.float32),
                "instruments": np.asarray(case["instruments"], dtype=np.float32),
            }
            ctrl = ScriptedLandingController(action_dim=int(spec.get("action_dim", 17)), dt=float(spec.get("dt", 0.05)))
            ctrl.reset(obs)
            action = ctrl.step(obs)
            checks = dict(case.get("checks", {}) or {})
            for action_idx_str, rule in checks.items():
                action_idx = int(action_idx_str)
                value = float(action[action_idx])
                if "gt" in rule and not (value > float(rule["gt"])):
                    return False, f"case {idx}: action[{action_idx}] expected > {rule['gt']}, got {value}"
                if "lt" in rule and not (value < float(rule["lt"])):
                    return False, f"case {idx}: action[{action_idx}] expected < {rule['lt']}, got {value}"
                if "eq" in rule and not math.isclose(value, float(rule["eq"]), rel_tol=1e-6, abs_tol=1e-6):
                    return False, f"case {idx}: action[{action_idx}] expected == {rule['eq']}, got {value}"
                if "min" in rule and not (value >= float(rule["min"])):
                    return False, f"case {idx}: action[{action_idx}] expected >= {rule['min']}, got {value}"
                if "max" in rule and not (value <= float(rule["max"])):
                    return False, f"case {idx}: action[{action_idx}] expected <= {rule['max']}, got {value}"
        return True, "scripted landing controller contract passed"

    if check_kind == "env_config_resolution":
        import argparse
        from python.env_config import resolve_env_settings

        def _make_args(**overrides):
            base = {
                "include_visual": None,
                "include_proprio": None,
                "mission_obs_mode": None,
                "visual_downsample": None,
                "visual_update_interval": None,
                "action_mode": None,
            }
            base.update(overrides)
            return argparse.Namespace(**base)

        train_config = dict(spec.get("train_config", {}) or {})
        resolved = resolve_env_settings(train_config, _make_args())
        for key, value in dict(spec.get("expected_defaults", {}) or {}).items():
            if resolved.get(key) != value:
                return False, f"expected default {key}={value!r}, got {resolved}"
        overridden = resolve_env_settings(train_config, _make_args(**dict(spec.get("overrides", {}) or {})))
        for key, value in dict(spec.get("expected_overrides", {}) or {}).items():
            if overridden.get(key) != value:
                return False, f"expected override {key}={value!r}, got {overridden}"
        return True, "env config resolution contract passed"

    if check_kind == "takeoff_curriculum_auto_gear_agl":
        try:
            import gymnasium as gym
        except ModuleNotFoundError as exc:
            raise ContractSkipped("gymnasium not installed") from exc
        import numpy as np
        from types import SimpleNamespace
        from gym_envs.universal_env import UniversalEnv

        class _StubSim:
            def __init__(self) -> None:
                self._inst = SimpleNamespace(
                    alt_baro=float(spec.get("alt_baro", 500.0)),
                    alt_radar=float(spec.get("alt_radar", 0.0)),
                    on_runway=True,
                    gear_collapsed=False,
                    gear_stress=0.0,
                )
                self.captured_action = None

            def get_instrument_state(self, _agent_id):
                return self._inst

            def set_pilot_action(self, _agent_id, pilot_action):
                self.captured_action = pilot_action

            def step(self):
                return None

            def get_time_step(self):
                return 0.05

        class _StubLoader:
            def update_behaviors(self, _t):
                return None

            def compute_full_step(self, _obs, _sim, _steps, _max_steps):
                return 0.0, False, False, [0.0, 0.0, 0.0, 0.0]

            def get_rewards_config(self):
                return {}

        env = object.__new__(UniversalEnv)
        env.action_mode = "takeoff4"
        env.action_space = gym.spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
        env.sim = _StubSim()
        env.loader = _StubLoader()
        env.agent_id = 1
        env.steps = 0
        env.max_steps = 10
        env._last_action = None
        env._last_inst = None
        env._last_truth = None
        env._get_obs = lambda: {
            "instruments": np.zeros((42,), dtype=np.float32),
            "contacts": np.zeros((10, 5), dtype=np.float32),
            "rwr": np.zeros((4, 4), dtype=np.float32),
            "mission": np.zeros((4,), dtype=np.float32),
        }
        env.step(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32))
        pilot_action = env.sim.captured_action
        if pilot_action is None:
            return False, "pilot action was not sent to the sim"
        if abs(float(pilot_action.gear_handle) - 1.0) > 1.0e-6:
            return False, f"gear retracted on-ground when baro alt was high: gear_handle={pilot_action.gear_handle}"
        return True, "takeoff curriculum auto-gear contract passed"

    raise ValueError(f"Unknown unit_regression check_kind: {check_kind}")


def run_contract(spec_path: str) -> tuple[bool, str]:
    spec = _load_spec(spec_path)
    contract_type = str(spec.get("type", "")).strip().lower()
    if contract_type == "loader_command_chain":
        return run_loader_command_chain_contract(spec_path)
    if contract_type == "route_generator":
        return run_route_generator_contract(spec_path)
    if contract_type == "env_regression":
        return run_env_regression_contract(spec_path)
    if contract_type == "unit_regression":
        return run_unit_regression_contract(spec_path)
    if contract_type == "scripted_bridge":
        return run_scripted_bridge_contract(spec_path)
    raise ValueError(f"Unknown contract type: {contract_type}")
