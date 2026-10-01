"""Ground infantry command projections onto the maintained batch boundary.

The maintained command contract transports heading/speed, bounded stance, and
the Ground static-task slice. ``OccupyStatic`` and ``SupportStatic`` are
bounded position-hold directives; they do not imply cover, concealment, sensing,
or fire-control semantics. It still cannot represent route intent, so this
module rejects non-direct values instead of silently dropping them. Transport
success is not movement execution, and all native behavior remains outside
production ``WorldBatch``.
"""

from __future__ import annotations

from typing import Any

import ef_py

from python.rl.runtime.world_batch.command_chain_cache import (
    project_world_mission_command_maintained_assignment,
)

from .infantry_proxy import (
    GroundInfantryProxyError,
    GroundInfantryAction,
    normalize_ground_infantry_action,
)


_GROUND_TASK_MODE_NAMES = {
    "move_static": "MoveStatic",
    "occupy_static": "OccupyStatic",
    "support_static": "SupportStatic",
}


def _positive(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise GroundInfantryProxyError(f"{label} must be numeric") from exc
    if result <= 0.0:
        raise GroundInfantryProxyError(f"{label} must be positive")
    return result


def _ground_task_mode(value: Any) -> tuple[Any, str]:
    """Resolve the admitted static task modes without accepting Unspecified."""

    namespace = ef_py.GroundTaskMode
    if isinstance(value, str):
        key = value.strip().lower()
        if key not in _GROUND_TASK_MODE_NAMES:
            raise GroundInfantryProxyError(
                f"ground_task_mode must be one of {tuple(_GROUND_TASK_MODE_NAMES)}"
            )
        return getattr(namespace, _GROUND_TASK_MODE_NAMES[key]), key
    for key, enum_name in _GROUND_TASK_MODE_NAMES.items():
        enum_value = getattr(namespace, enum_name)
        if value == enum_value:
            return enum_value, key
    raise GroundInfantryProxyError(
        f"ground_task_mode must be one of {tuple(_GROUND_TASK_MODE_NAMES)}"
    )


def build_ground_infantry_mission_command(
    action: GroundInfantryAction | dict[str, Any] | list[Any] | tuple[Any, ...],
    *,
    max_speed_mps: float = 1.5,
    objective_area_id: int = 0,
    objective_node_id: int = 0,
    ground_commander_id: int = 0,
    tactical_cadence_hz: float = 1.0,
    ground_task_mode: Any = "move_static",
) -> ef_py.MissionCommand:
    """Build the representable movement/task subset of a native MissionCommand.

    Route intent is still checked here because the current maintained C++
    command shape has no route field. Stance is now admitted as a bounded
    native movement posture; static hold modes force zero speed and do not
    claim cover, concealment, sensing, or weapon semantics.
    """

    normalized = normalize_ground_infantry_action(action)
    if normalized.route_intent != "direct":
        raise GroundInfantryProxyError(
            "native MissionCommand projection cannot represent route_intent; keep non-direct "
            "actions on the proxy contract"
        )
    speed_limit = _positive(max_speed_mps, "max_speed_mps")
    cadence = _positive(tactical_cadence_hz, "tactical_cadence_hz")
    task_mode, task_mode_name = _ground_task_mode(ground_task_mode)

    command = ef_py.MissionCommand()
    command.active = True
    command.cmd_heading_deg = float(normalized.desired_heading_deg)
    command.cmd_speed_mps = (
        float(normalized.desired_speed_fraction) * speed_limit
        if task_mode_name == "move_static"
        else 0.0
    )
    command.cmd_altitude_m = 0.0
    command.ground_task_mode = task_mode
    command.ground_stance = {
        "stand": ef_py.GroundStance.Stand,
        "crouch": ef_py.GroundStance.Crouch,
        "prone": ef_py.GroundStance.Prone,
    }[normalized.stance]
    command.objective_area_id = int(objective_area_id)
    command.objective_node_id = int(objective_node_id)
    command.ground_commander_id = int(ground_commander_id)
    command.tactical_cadence_hz = cadence
    return command


def build_ground_infantry_maintained_assignment(
    action: GroundInfantryAction | dict[str, Any] | list[Any] | tuple[Any, ...],
    *,
    world_index: int,
    entity_id: int,
    max_speed_mps: float = 1.5,
    objective_area_id: int = 0,
    objective_node_id: int = 0,
    ground_commander_id: int = 0,
    tactical_cadence_hz: float = 1.0,
    ground_task_mode: Any = "move_static",
) -> Any:
    """Project a representable action into a maintained world assignment."""

    command = build_ground_infantry_mission_command(
        action,
        max_speed_mps=max_speed_mps,
        objective_area_id=objective_area_id,
        objective_node_id=objective_node_id,
        ground_commander_id=ground_commander_id,
        tactical_cadence_hz=tactical_cadence_hz,
        ground_task_mode=ground_task_mode,
    )
    try:
        assignment = ef_py.WorldMissionCommandMaintainedAssignment()
        project_world_mission_command_maintained_assignment(
            assignment,
            world_index=int(world_index),
            entity_id=int(entity_id),
            compatibility_mission_command_shell=command,
        )
    except (AttributeError, RuntimeError) as exc:
        raise GroundInfantryProxyError(
            "maintained MissionCommand batch projection is unavailable; fail closed"
        ) from exc
    if not hasattr(assignment.mission_command, "ground_static_task"):
        raise GroundInfantryProxyError(
            "maintained MissionCommand batch binding lacks ground_static_task; fail closed"
        )
    return assignment


__all__ = [
    "build_ground_infantry_maintained_assignment",
    "build_ground_infantry_mission_command",
]
