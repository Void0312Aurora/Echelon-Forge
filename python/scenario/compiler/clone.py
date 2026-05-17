from __future__ import annotations

import copy
from typing import Any

from .common import _SCALAR_TYPES


def _clone_scenario_value(value: Any) -> Any:
    value_type = type(value)
    if value_type in _SCALAR_TYPES:
        return value
    if value_type is dict:
        return {key: _clone_scenario_value(item) for key, item in value.items()}
    if value_type is list:
        return [_clone_scenario_value(item) for item in value]
    if value_type is tuple:
        return tuple(_clone_scenario_value(item) for item in value)

    if isinstance(value, dict):
        return {key: _clone_scenario_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_scenario_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_scenario_value(item) for item in value)
    return copy.deepcopy(value)


def _clone_runtime_environment(env_cfg: Any) -> Any:
    if not isinstance(env_cfg, dict):
        return _clone_scenario_value(env_cfg)
    cloned = dict(env_cfg)
    if "zones" in env_cfg:
        cloned["zones"] = _clone_scenario_value(env_cfg.get("zones", []))
    return cloned


def _clone_runtime_entity(entity_cfg: Any) -> Any:
    if not isinstance(entity_cfg, dict):
        return _clone_scenario_value(entity_cfg)
    cloned = dict(entity_cfg)
    if "pos" in entity_cfg:
        pos = entity_cfg.get("pos")
        if isinstance(pos, list):
            cloned["pos"] = list(pos)
        elif isinstance(pos, tuple):
            cloned["pos"] = list(pos)
        else:
            cloned["pos"] = _clone_scenario_value(pos)
    if "vel" in entity_cfg:
        vel = entity_cfg.get("vel")
        if isinstance(vel, list):
            cloned["vel"] = list(vel)
        elif isinstance(vel, tuple):
            cloned["vel"] = list(vel)
        else:
            cloned["vel"] = _clone_scenario_value(vel)
    return cloned


def _clone_runtime_entities(entities_cfg: Any) -> Any:
    if not isinstance(entities_cfg, list):
        return _clone_scenario_value(entities_cfg)
    return [_clone_runtime_entity(entity_cfg) for entity_cfg in entities_cfg]


def _clone_runtime_mission_command(cmd_cfg: Any) -> Any:
    if not isinstance(cmd_cfg, dict):
        return _clone_scenario_value(cmd_cfg)
    cloned = dict(cmd_cfg)
    if "waypoints" in cmd_cfg:
        cloned["waypoints"] = _clone_scenario_value(cmd_cfg.get("waypoints", []))
    if "_normalized_waypoints" in cmd_cfg:
        cloned["_normalized_waypoints"] = _clone_scenario_value(cmd_cfg.get("_normalized_waypoints", []))
    if isinstance(cmd_cfg.get("post_waypoint_transition"), dict):
        cloned["post_waypoint_transition"] = _clone_runtime_mission_command(cmd_cfg["post_waypoint_transition"])
    return cloned


def _clone_runtime_task_order(task_cfg: Any) -> Any:
    if not isinstance(task_cfg, dict):
        return _clone_scenario_value(task_cfg)
    return dict(task_cfg)


def _clone_runtime_cooperative_roster(roster_cfg: Any) -> Any:
    if not isinstance(roster_cfg, dict):
        return _clone_scenario_value(roster_cfg)
    cloned = dict(roster_cfg)
    if "members" in roster_cfg:
        cloned["members"] = _clone_scenario_value(roster_cfg.get("members", []))
    return cloned


def _clone_runtime_environment_context(env_cfg: Any) -> Any:
    if not isinstance(env_cfg, dict):
        return _clone_scenario_value(env_cfg)
    cloned: dict[str, Any] = {}
    if "max_steps" in env_cfg:
        cloned["max_steps"] = _clone_scenario_value(env_cfg.get("max_steps"))
    if "time_step" in env_cfg:
        cloned["time_step"] = _clone_scenario_value(env_cfg.get("time_step"))
    return cloned


def _extract_runtime_agent_spawn_context(entities_cfg: Any) -> dict[str, Any] | None:
    if not isinstance(entities_cfg, list) or not entities_cfg:
        return None

    spawn = None
    for ent_cfg in entities_cfg:
        if isinstance(ent_cfg, dict) and bool(ent_cfg.get("is_agent", False)):
            spawn = ent_cfg
            break
    if spawn is None:
        spawn = entities_cfg[0] if isinstance(entities_cfg[0], dict) else None
    if not isinstance(spawn, dict):
        return None

    context: dict[str, Any] = {
        "name": str(spawn.get("name", "")),
        "is_agent": bool(spawn.get("is_agent", False)),
    }
    if "heading" in spawn:
        try:
            context["heading"] = float(spawn.get("heading", 0.0))
        except Exception:
            pass
    if "pos" in spawn:
        pos = spawn.get("pos")
        if isinstance(pos, list):
            context["pos"] = list(pos)
        elif isinstance(pos, tuple):
            context["pos"] = list(pos)
        else:
            context["pos"] = _clone_scenario_value(pos)
    return context


def _clone_runtime_scenario_data(merged_scenario_data: dict[str, Any]) -> dict[str, Any]:
    runtime_data = dict(merged_scenario_data)
    if "environment" in merged_scenario_data:
        runtime_data["environment"] = _clone_runtime_environment(merged_scenario_data.get("environment"))
    if "entities" in merged_scenario_data:
        runtime_data["entities"] = _clone_runtime_entities(merged_scenario_data.get("entities"))
    if "mission_command" in merged_scenario_data:
        runtime_data["mission_command"] = _clone_runtime_mission_command(merged_scenario_data.get("mission_command"))
    if "task_order" in merged_scenario_data:
        runtime_data["task_order"] = _clone_runtime_task_order(merged_scenario_data.get("task_order"))
    if "cooperative_roster" in merged_scenario_data:
        runtime_data["cooperative_roster"] = _clone_runtime_cooperative_roster(
            merged_scenario_data.get("cooperative_roster")
        )
    if "active_controllable_roster" in merged_scenario_data:
        runtime_data["active_controllable_roster"] = _clone_runtime_cooperative_roster(
            merged_scenario_data.get("active_controllable_roster")
        )
    return runtime_data


def _clone_runtime_context_scenario_data(merged_scenario_data: dict[str, Any]) -> dict[str, Any]:
    runtime_data: dict[str, Any] = {}
    if "environment" in merged_scenario_data:
        runtime_data["environment"] = _clone_runtime_environment_context(merged_scenario_data.get("environment"))
    if "mission_command" in merged_scenario_data:
        runtime_data["mission_command"] = _clone_runtime_mission_command(merged_scenario_data.get("mission_command"))
    if "task_order" in merged_scenario_data:
        runtime_data["task_order"] = _clone_runtime_task_order(merged_scenario_data.get("task_order"))
    if "cooperative_roster" in merged_scenario_data:
        runtime_data["cooperative_roster"] = _clone_runtime_cooperative_roster(
            merged_scenario_data.get("cooperative_roster")
        )
    if "active_controllable_roster" in merged_scenario_data:
        runtime_data["active_controllable_roster"] = _clone_runtime_cooperative_roster(
            merged_scenario_data.get("active_controllable_roster")
        )
    if "meta" in merged_scenario_data:
        runtime_data["meta"] = _clone_scenario_value(merged_scenario_data.get("meta"))
    if "rewards" in merged_scenario_data:
        runtime_data["rewards"] = _clone_scenario_value(merged_scenario_data.get("rewards"))
    if "objectives" in merged_scenario_data:
        runtime_data["objectives"] = _clone_scenario_value(merged_scenario_data.get("objectives"))
    entities_cfg = merged_scenario_data.get("entities", [])
    if isinstance(entities_cfg, list):
        runtime_entities: list[dict[str, Any]] = []
        for ent_cfg in entities_cfg:
            if not isinstance(ent_cfg, dict):
                continue
            scripted_cfg = ent_cfg.get("scripted_agent", None)
            if not isinstance(scripted_cfg, dict):
                continue
            runtime_ent = {
                "name": str(ent_cfg.get("name", "")),
                "is_agent": bool(ent_cfg.get("is_agent", False)),
                "scripted_agent": _clone_scenario_value(scripted_cfg),
            }
            runtime_entities.append(runtime_ent)
        if runtime_entities:
            runtime_data["entities"] = runtime_entities

    agent_spawn = _extract_runtime_agent_spawn_context(merged_scenario_data.get("entities"))
    if agent_spawn is not None:
        runtime_data["_runtime_agent_spawn"] = agent_spawn
    return runtime_data


__all__ = [
    "_clone_scenario_value",
    "_clone_runtime_environment",
    "_clone_runtime_entity",
    "_clone_runtime_entities",
    "_clone_runtime_mission_command",
    "_clone_runtime_task_order",
    "_clone_runtime_cooperative_roster",
    "_clone_runtime_environment_context",
    "_extract_runtime_agent_spawn_context",
    "_clone_runtime_scenario_data",
    "_clone_runtime_context_scenario_data",
]
