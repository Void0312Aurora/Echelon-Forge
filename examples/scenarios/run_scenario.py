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

        detections = {name: kernel.get_detections(eid) for name, eid in entity_map.items()}
        metrics.update(step_index * dt, positions, detections, healths)
        if logger:
            logger.log_tick(step_index, step_index * dt, positions, detections)

        if require_detection and not detected:
            for contacts in detections.values():
                if contacts:
                    detected = True
                    break

    summary = metrics.summary()
    summary["require_detection"] = require_detection
    summary["detected"] = detected
    summary["steps"] = steps
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
