import json
import math
import os
import sys
from datetime import datetime

# Ensure we can import the module from build/
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))
sys.path.append(repo_root)

import ef_py
from python.scenario_metrics import ScenarioLogger, ScenarioMetrics


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def nav_heading_to_target(src, dst):
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    math_angle = math.atan2(dy, dx)
    nav_heading = 90.0 - math.degrees(math_angle)
    return nav_heading % 360.0


def resolve_enum(enum_type, name):
    try:
        return getattr(enum_type, name)
    except AttributeError:
        raise ValueError(f"Unknown {enum_type.__name__} value: {name}")

def safe_slug(value):
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_"):
            cleaned.append(ch)
        elif ch.isspace():
            cleaned.append("_")
    slug = "".join(cleaned).strip("_")
    return slug or "scenario"

def resolve_output_path(path, repo_root, run_dir, default_name):
    if not path:
        return None
    if os.path.isabs(path):
        return path
    filename = os.path.basename(path) or default_name
    if run_dir:
        return os.path.join(run_dir, filename)
    return os.path.join(repo_root, path)


def resolve_scenario_path(arg, repo_root):
    if os.path.isfile(arg):
        return arg

    candidate = os.path.join(repo_root, arg)
    if os.path.isfile(candidate):
        return candidate

    index_path = os.path.join(repo_root, "content", "scenarios", "index.json")
    if os.path.isfile(index_path):
        index = load_json(index_path)
        for entry in index.get("scenarios", []):
            if entry.get("id") == arg:
                entry_path = entry.get("path")
                if entry_path:
                    return os.path.join(repo_root, entry_path)

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/scenarios/run_scenario.py <scenario.json|scenario_id>")
        sys.exit(1)

    scenario_path = resolve_scenario_path(sys.argv[1], repo_root)
    if not scenario_path:
        print("Scenario not found. Check path or content/scenarios/index.json.")
        sys.exit(1)
    scenario = load_json(scenario_path)

    kernel = ef_py.SimulationKernel()
    kernel.reset(int(scenario.get("seed", 42)))

    unit_defs_path = scenario.get("unit_definitions")
    if unit_defs_path:
        unit_defs_abs = os.path.join(repo_root, unit_defs_path)
        if not kernel.load_unit_definitions(unit_defs_abs):
            print("FAILURE: failed to load unit definitions.")
            sys.exit(1)

    entity_map = {}
    for entity in scenario.get("entities", []):
        side = resolve_enum(ef_py.Side, entity["side"])
        unit_type = resolve_enum(ef_py.UnitType, entity["type"])
        pos = entity["position"]
        vel = entity["velocity"]
        entity_id = kernel.spawn_unit(side, unit_type,
                                      pos[0], pos[1], pos[2],
                                      vel[0], vel[1], vel[2])
        entity_map[entity["id"]] = entity_id

    behaviors = scenario.get("behaviors", [])
    duration_seconds = float(scenario.get("duration_seconds", 10.0))
    tick_hz = float(scenario.get("tick_hz", 60))
    dt = kernel.get_time_step()
    if tick_hz > 0:
        requested_dt = 1.0 / tick_hz
        if abs(requested_dt - dt) > 1e-6:
            print("Warning: tick_hz requested but kernel time step is fixed.")

    steps = int(duration_seconds / dt)
    require_detection = scenario.get("expectations", {}).get("require_detection", False)
    detected = False
    termination_cfg = scenario.get("termination", {})
    disengage_range_m = termination_cfg.get("disengage_range_m")
    disengage_hold_s = float(termination_cfg.get("disengage_hold_s", 0.0))
    min_specific_energy = termination_cfg.get("min_specific_energy_j_kg")
    energy_hold_s = float(termination_cfg.get("energy_hold_s", 0.0))
    ammo_depletion_ends = bool(termination_cfg.get("ammo_depletion_ends", False))

    output_cfg = scenario.get("output", {})
    log_path = output_cfg.get("log_path")
    metrics_path = output_cfg.get("metrics_path")
    gif_path = output_cfg.get("gif_path")
    gif_fps = output_cfg.get("gif_fps", 20)
    gif_max_frames = output_cfg.get("gif_max_frames", 600)

    run_dir = None
    if output_cfg and (log_path or metrics_path or gif_path):
        run_root = output_cfg.get("run_dir", "logs")
        scenario_name = safe_slug(scenario.get("name", "scenario"))
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(repo_root, run_root, f"{scenario_name}_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)

    log_path = resolve_output_path(log_path, repo_root, run_dir, "log.jsonl")
    metrics_path = resolve_output_path(metrics_path, repo_root, run_dir, "metrics.json")
    gif_path = resolve_output_path(gif_path, repo_root, run_dir, "playback.gif")
    metadata = {
        "schema_version": 1,
        "scenario": scenario.get("name", "unknown"),
        "seed": scenario.get("seed", 42),
        "duration_seconds": duration_seconds,
        "tick_hz": tick_hz,
        "dt": dt,
        "entities": list(entity_map.keys()),
    }
    logger = ScenarioLogger(log_path, metadata) if log_path else None
    metrics = ScenarioMetrics(entity_map.keys())

    engagement_pairs = []
    engaged_entities = set()
    for behavior in behaviors:
        if behavior.get("type") != "pursuit":
            continue
        entity_name = behavior.get("entity")
        target_name = behavior.get("target")
        if entity_name and target_name:
            engagement_pairs.append((entity_name, target_name))
            engaged_entities.add(entity_name)
            engaged_entities.add(target_name)

    disengage_timer = {pair: 0.0 for pair in engagement_pairs}
    energy_timer = {name: 0.0 for name in engaged_entities}

    termination_reason = None
    termination_time = None

    for step_index in range(steps):
        positions = {name: kernel.get_unit_position(eid) for name, eid in entity_map.items()}
        healths = {name: kernel.get_unit_health(eid) for name, eid in entity_map.items()}

        for behavior in behaviors:
            if behavior.get("type") != "pursuit":
                continue

            entity_name = behavior["entity"]
            target_name = behavior["target"]
            speed = float(behavior.get("speed", 300.0))

            entity_id = entity_map[entity_name]
            entity_pos = positions[entity_name]
            target_pos = positions[target_name]
            heading = nav_heading_to_target(entity_pos, target_pos)

            kernel.set_command(entity_id, heading, speed, entity_pos[2])

        kernel.step()

        positions = {name: kernel.get_unit_position(eid) for name, eid in entity_map.items()}
        healths = {name: kernel.get_unit_health(eid) for name, eid in entity_map.items()}
        observations = {name: kernel.get_agent_observation(eid) for name, eid in entity_map.items()}
        detections = {name: kernel.get_detections(eid) for name, eid in entity_map.items()}
        sim_time = (step_index + 1) * dt
        metrics.update(sim_time, positions, detections, healths)
        if logger:
            logger.log_tick(step_index, sim_time, positions, detections)

        if require_detection and not detected:
            for contacts in detections.values():
                if contacts:
                    detected = True
                    break
        if termination_reason:
            break

        if disengage_range_m is not None and engagement_pairs:
            for pair in engagement_pairs:
                entity_name, target_name = pair
                a = positions[entity_name]
                b = positions[target_name]
                dx = a[0] - b[0]
                dy = a[1] - b[1]
                dz = a[2] - b[2]
                dist = (dx * dx + dy * dy + dz * dz) ** 0.5
                if dist > disengage_range_m:
                    disengage_timer[pair] += dt
                else:
                    disengage_timer[pair] = 0.0
                if disengage_hold_s <= 0.0 or disengage_timer[pair] >= disengage_hold_s:
                    termination_reason = f"disengage_range:{entity_name}->{target_name}"
                    termination_time = sim_time
                    break
            if termination_reason:
                break

        if min_specific_energy is not None:
            for name in engaged_entities:
                obs = observations.get(name)
                if not obs:
                    continue
                specific_energy = 0.5 * obs.speed * obs.speed + 9.80665 * obs.z
                if specific_energy < min_specific_energy:
                    energy_timer[name] += dt
                else:
                    energy_timer[name] = 0.0
                if energy_hold_s <= 0.0 or energy_timer[name] >= energy_hold_s:
                    termination_reason = f"energy_low:{name}"
                    termination_time = sim_time
                    break
            if termination_reason:
                break

        if ammo_depletion_ends and engaged_entities:
            ammo_values = []
            for name in engaged_entities:
                obs = observations.get(name)
                if not obs:
                    continue
                if obs.missiles_remaining >= 0:
                    ammo_values.append(obs.missiles_remaining)
            if ammo_values and all(v <= 0 for v in ammo_values):
                missiles_in_flight = [
                    unit for unit in kernel.get_all_units()
                    if unit.type == int(ef_py.UnitType.Missile)
                ]
                if not missiles_in_flight:
                    termination_reason = "ammo_depleted"
                    termination_time = sim_time
                    break

    summary = metrics.summary()
    summary["require_detection"] = require_detection
    summary["detected"] = detected
    summary["steps"] = steps
    summary["termination_reason"] = termination_reason
    summary["termination_time"] = termination_time
    summary["schema_version"] = 1

    if logger:
        logger.close()

    if metrics_path:
        metrics_dir = os.path.dirname(metrics_path)
        if metrics_dir:
            os.makedirs(metrics_dir, exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=True)

    if gif_path and log_path:
        try:
            from python.scenario_visualizer import render_gif
        except Exception as exc:
            print(f"Warning: failed to import visualizer ({exc}).")
        else:
            try:
                render_gif(log_path, gif_path, fps=gif_fps, max_frames=gif_max_frames)
            except Exception as exc:
                print(f"Warning: failed to render GIF ({exc}).")

    if require_detection and not detected:
        print("SCENARIO FAILED: no detections recorded.")
        sys.exit(1)

    print("SCENARIO COMPLETE.")


if __name__ == "__main__":
    main()
