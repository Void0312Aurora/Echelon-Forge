from __future__ import annotations

import json
import os

from python.testing.runtime import ensure_repo_imports

from .common import (
    _check_optional_range,
    _leg_lengths,
    _load_spec,
    _materialize_scenario_path,
    _turn_budget_cost_m,
    _turn_geometry,
)

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
