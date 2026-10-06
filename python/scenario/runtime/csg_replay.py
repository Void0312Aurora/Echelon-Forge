"""Native, agent-free CSG state frames shared by spectator views and replay checks."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

from python.runtime_bootstrap import resolve_repo_path
from python.simulation import create_scenario_runtime_adapter


CSG_REPLAY_SCHEMA = "csg.s0.replay.v1"
def _csg_replay_platform_type(platform_type: str) -> str:
    """Project the catalog type into the stable visualization category."""
    lowered = platform_type.lower()
    if any(token in lowered for token in ("submarine", "ssn", "type093")):
        return "Submarine"
    if any(
        token in lowered
        for token in (
            "aircraft",
            "fa-",
            "f-35",
            "j-15",
            "j-35",
            "e-2",
            "ea-18",
            "mh-",
            "c-2",
            "cmv-",
            "kj-600",
            "gj-21",
            "z-20",
        )
    ):
        return "Aircraft"
    return "Ship"


def _csg_replay_unit_frame(sim, loader) -> list[dict[str, Any]]:
    """Build the stable, frontend-compatible unit slice for one native tick."""
    scenario_data = getattr(loader, "scenario_data", {})
    raw_entities = scenario_data.get("entities", []) if isinstance(scenario_data, dict) else []
    config_by_name = {
        str(item.get("name")): item
        for item in raw_entities
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }
    try:
        groups = loader._compiled_runtime_metadata.meta_config.get("csg", {}).get("groups", [])
    except Exception:
        groups = []

    out: list[dict[str, Any]] = []
    physical_names_by_member: dict[tuple[str, str], list[str]] = {}
    for name in loader.entities:
        config = config_by_name.get(str(name), {})
        csg_member = config.get("csg_member", {})
        if isinstance(csg_member, dict):
            key = (str(csg_member.get("group_id", "")), str(csg_member.get("member_id", "")))
            physical_names_by_member.setdefault(key, []).append(str(name))

    def append_unit(entity_id: int, name: str, config: dict[str, Any], observation: Any) -> None:
        platform_type = str(config.get("type", ""))
        unit_type = _csg_replay_platform_type(platform_type)
        side = str(config.get("side", "Unknown"))
        velocity = tuple(float(getattr(observation, axis, 0.0)) for axis in ("vx", "vy", "vz"))
        speed = float(getattr(observation, "speed", 0.0))
        if not math.isfinite(speed):
            speed = math.sqrt(sum(value * value for value in velocity))
        health = float(getattr(observation, "health", 100.0))
        out.append(
            {
                "id": entity_id,
                "name": str(name),
                "side": side,
                "type": unit_type,
                "platform_type": platform_type or unit_type,
                "echelon": "platform",
                "service_profile": "BlueAir" if side == "Blue" and unit_type == "Aircraft" else "RedAir" if side == "Red" and unit_type == "Aircraft" else "",
                "x": float(getattr(observation, "x", 0.0)),
                "y": float(getattr(observation, "y", 0.0)),
                "z": float(getattr(observation, "z", 0.0)),
                "heading": float(getattr(observation, "heading", 0.0)),
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

    # Runtime entity IDs are allocator state and can differ across platforms.
    # Replay evidence uses a scenario-order projection ID so the same artifact
    # validates on Windows and Linux while facade lookups retain the live IDs.
    for stable_id, (name, runtime_id) in enumerate(loader.entities.items(), start=1):
        name = str(name)
        entity_id = int(runtime_id)
        config = config_by_name.get(name, {})
        observation = sim.get_agent_observation(entity_id)
        append_unit(stable_id, name, config, observation)

    # The facade setup path keeps embarked inventories as metadata at S0. Keep
    # their stable spectator presence by projecting one stowed aircraft per
    # active host, colocated with the host until a future deck-cycle phase.
    virtual_id = -1
    virtual_hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, dict):
            continue
        group_id = str(group.get("group_id", ""))
        side = str(group.get("side", "Unknown"))
        for inventory in group.get("embarked_inventory", []):
            if not isinstance(inventory, dict) or int(inventory.get("count", 0)) <= 0:
                continue
            member_id = str(inventory.get("embarked_on", ""))
            for host_name in physical_names_by_member.get((group_id, member_id), []):
                virtual_hosts.setdefault(
                    host_name,
                    (side, {"type": str(inventory.get("type", "Aircraft"))}),
                )
    for host_name, (side, config) in virtual_hosts.items():
        host_id = int(loader.entities[host_name])
        host_observation = sim.get_agent_observation(host_id)
        virtual_name = f"{host_name}__stowed_aircraft"
        config = {**config, "name": virtual_name, "side": side}
        append_unit(virtual_id, virtual_name, config, host_observation)
        virtual_id -= 1
    return out


def capture_csg_replay(scenario_path: str, *, seed: int, max_steps: int | None = None) -> dict[str, Any]:
    """Run an agent-free CSG scenario and capture deterministic state frames."""
    scenario_abs = resolve_repo_path(scenario_path)
    with open(scenario_abs, "rb") as handle:
        scenario_sha256 = hashlib.sha256(handle.read()).hexdigest()
    with open(scenario_abs, "r", encoding="utf-8") as handle:
        raw_scenario = json.load(handle)

    database = resolve_repo_path("examples", "config", "database")
    adapter = create_scenario_runtime_adapter(1)
    if not adapter.load_database(database):
        raise RuntimeError(f"database load failed for {scenario_abs}")
    loader = adapter.make_scenario_loader(0)
    sim = loader.sim
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
    anchor_config = environment.get("geodetic_anchor", {})
    if not isinstance(anchor_config, dict):
        anchor_config = {}
    anchor = [
        float(anchor_config.get("latitude_deg", 0.0)),
        float(anchor_config.get("longitude_deg", 0.0)),
        float(anchor_config.get("height_m", 0.0)),
    ]
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

    adapter = create_scenario_runtime_adapter(1)
    if not adapter.load_database(resolve_repo_path("examples", "config", "database")):
        raise RuntimeError(f"database load failed for {scenario_abs}")
    loader = adapter.make_scenario_loader(0)
    sim = loader.sim
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
