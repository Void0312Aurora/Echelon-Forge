"""Native, agent-free CSG state frames shared by spectator views and replay checks."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from python.runtime_bootstrap import resolve_repo_path


CSG_REPLAY_SCHEMA = "csg.s0.replay.v1"
_CSG_REPLAY_TYPE_NAMES = {
    1: "Aircraft",
    2: "Ship",
    3: "Missile",
    4: "Facility",
    5: "C2Node",
    6: "Sensor",
    7: "Engine",
    8: "EWSuite",
    9: "RCSProfile",
    10: "Submarine",
    11: "Ground",
}
_CSG_REPLAY_SIDE_NAMES = {1: "Blue", 2: "Red", 0: "Neutral"}


def _csg_replay_unit_frame(sim, loader) -> list[dict[str, Any]]:
    """Build the stable, frontend-compatible unit slice for one native tick."""
    scenario_data = getattr(loader, "scenario_data", {})
    raw_entities = scenario_data.get("entities", []) if isinstance(scenario_data, dict) else []
    config_by_name = {
        str(item.get("name")): item
        for item in raw_entities
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }
    explicit_by_id = {int(entity_id): str(name) for name, entity_id in loader.entities.items()}
    csg_groups = {}
    try:
        groups = loader._compiled_runtime_metadata.meta_config.get("csg", {}).get("groups", [])
    except Exception:
        groups = []
    for group in groups if isinstance(groups, list) else []:
        if isinstance(group, dict):
            csg_groups[str(group.get("side", "Unknown"))] = str(group.get("group_id", "CSG"))

    runtime_units = sorted(list(sim.get_all_units()), key=lambda unit: int(unit.id))
    aircraft_ordinals: dict[str, int] = {}
    out: list[dict[str, Any]] = []
    for unit in runtime_units:
        entity_id = int(unit.id)
        side_code = int(unit.side)
        type_code = int(unit.type)
        side = _CSG_REPLAY_SIDE_NAMES.get(side_code, f"Side{side_code}")
        unit_type = _CSG_REPLAY_TYPE_NAMES.get(type_code, f"UnitType{type_code}")
        name = explicit_by_id.get(entity_id)
        config = config_by_name.get(name or "", {})
        if not name:
            if unit_type == "Aircraft":
                ordinal = aircraft_ordinals.get(side, 0) + 1
                aircraft_ordinals[side] = ordinal
                group_id = csg_groups.get(side, f"{side.upper()}_CSG")
                name = f"{group_id}__stowed_aircraft_{ordinal:02d}"
            else:
                name = f"{side.lower()}__runtime_{entity_id}"
        try:
            velocity = tuple(float(value) for value in sim.get_unit_velocity(entity_id))
            speed = math.sqrt(sum(value * value for value in velocity))
        except Exception:
            speed = float(getattr(unit, "speed", 0.0))
        try:
            health = float(sim.get_unit_health(entity_id))
        except Exception:
            health = float(getattr(unit, "health", 100.0))
        out.append(
            {
                "id": entity_id,
                "name": str(name),
                "side": side,
                "type": unit_type,
                "platform_type": str(config.get("type", unit_type)),
                "echelon": "platform",
                "service_profile": "BlueAir" if side == "Blue" and unit_type == "Aircraft" else "RedAir" if side == "Red" and unit_type == "Aircraft" else "",
                "x": float(unit.x),
                "y": float(unit.y),
                "z": float(unit.z),
                "heading": float(getattr(unit, "heading", 0.0)),
                "pitch": 0.0,
                "roll": 0.0,
                "speed": speed,
                "ias": speed,
                "hp": health,
                "max_hp": 100.0,
                "active": True,
                "is_active": True,
            }
        )
    return out


def capture_csg_replay(scenario_path: str, *, seed: int, max_steps: int | None = None) -> dict[str, Any]:
    """Run an agent-free CSG scenario and capture deterministic state frames."""
    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    scenario_abs = resolve_repo_path(scenario_path)
    with open(scenario_abs, "rb") as handle:
        scenario_sha256 = hashlib.sha256(handle.read()).hexdigest()
    with open(scenario_abs, "r", encoding="utf-8") as handle:
        raw_scenario = json.load(handle)

    database = resolve_repo_path("examples", "config", "database")
    sim = ef_py.SimulationKernel()
    sim.reset(1)
    if not sim.load_database(database):
        raise RuntimeError(f"database load failed for {scenario_abs}")
    loader = ScenarioLoader(sim)
    if loader.load_scenario(scenario_abs, seed=int(seed)) is not None:
        raise RuntimeError(f"CSG replay scenario must remain agent-free: {scenario_abs}")

    environment = raw_scenario.get("environment", {}) if isinstance(raw_scenario, dict) else {}
    if not isinstance(environment, dict):
        environment = {}
    steps = int(environment.get("max_steps", 0) if max_steps is None else max_steps)
    if steps < 0:
        raise ValueError("CSG replay max_steps must be non-negative")
    time_step_s = float(environment.get("time_step", 0.5))
    frames = [{"tick": 0, "sim_time_s": 0.0, "units": _csg_replay_unit_frame(sim, loader)}]
    for step in range(1, steps + 1):
        sim.step()
        frames.append(
            {
                "tick": step,
                "sim_time_s": float(step * time_step_s),
                "units": _csg_replay_unit_frame(sim, loader),
            }
        )
    anchor = [float(value) for value in sim.get_geodetic_anchor()]
    return {
        "schema": CSG_REPLAY_SCHEMA,
        "scenario": os.path.relpath(scenario_abs, os.getcwd()).replace("\\", "/"),
        "scenario_sha256": scenario_sha256,
        "seed": int(seed),
        "time_step_s": time_step_s,
        "max_steps": steps,
        "duration_s": float(steps * time_step_s),
        "geodetic_anchor": anchor,
        "entity_roster": frames[0]["units"],
        "frames": frames,
        "verification": {
            "mode": "native_deterministic_step",
            "agent_free": True,
            "frame_count": len(frames),
        },
    }


def iter_csg_spectator_frames(
    scenario_path: str,
    *,
    seed: int = 20260930,
    max_steps: int | None = None,
):
    """Yield native CSG state frames for a no-agent spectator session."""
    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    scenario_abs = resolve_repo_path(scenario_path)
    with open(scenario_abs, "r", encoding="utf-8") as handle:
        raw_scenario = json.load(handle)
    environment = raw_scenario.get("environment", {}) if isinstance(raw_scenario, dict) else {}
    if not isinstance(environment, dict):
        environment = {}
    steps = int(environment.get("max_steps", 0) if max_steps is None else max_steps)
    if steps < 0:
        raise ValueError("CSG spectator max_steps must be non-negative")
    time_step_s = float(environment.get("time_step", 0.5))

    sim = ef_py.SimulationKernel()
    sim.reset(1)
    if not sim.load_database(resolve_repo_path("examples", "config", "database")):
        raise RuntimeError(f"database load failed for {scenario_abs}")
    loader = ScenarioLoader(sim)
    if loader.load_scenario(scenario_abs, seed=int(seed)) is not None:
        raise RuntimeError(f"CSG spectator scenario must remain agent-free: {scenario_abs}")

    yield {"tick": 0, "sim_time_s": 0.0, "units": _csg_replay_unit_frame(sim, loader)}
    for step in range(1, steps + 1):
        sim.step()
        yield {
            "tick": step,
            "sim_time_s": float(step * time_step_s),
            "units": _csg_replay_unit_frame(sim, loader),
        }


def write_csg_replay_artifact(
    scenario_path: str,
    output_path: str,
    *,
    seed: int = 20260930,
    max_steps: int | None = None,
) -> dict[str, Any]:
    artifact = capture_csg_replay(scenario_path, seed=int(seed), max_steps=max_steps)
    output_abs = Path(output_path)
    if not output_abs.is_absolute():
        output_abs = Path(os.getcwd()) / output_abs
    output_abs.parent.mkdir(parents=True, exist_ok=True)
    output_abs.write_text(json.dumps(artifact, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return artifact

