"""Ground infantry command projections onto the maintained batch boundary.

The existing command contract can transport heading/speed and the Ground
static-task slice.  It cannot yet represent stance or route intent, so this
module rejects those values instead of silently dropping them.  Transport
success is not movement execution; the native Ground consumer remains held.
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


def _positive(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise GroundInfantryProxyError(f"{label} must be numeric") from exc
    if result <= 0.0:
        raise GroundInfantryProxyError(f"{label} must be positive")
    return result


def build_ground_infantry_mission_command(
    action: GroundInfantryAction | dict[str, Any] | list[Any] | tuple[Any, ...],
    *,
    max_speed_mps: float = 1.5,
    objective_area_id: int = 0,
    objective_node_id: int = 0,
    ground_commander_id: int = 0,
    tactical_cadence_hz: float = 1.0,
) -> ef_py.MissionCommand:
    """Build the representable movement subset of a native MissionCommand.

    Route intent is still checked here because the current maintained C++
    command shape has no route field. Stance is now admitted as a bounded
    native movement posture; it changes movement cost only and does not claim
    cover, concealment, or weapon semantics.
    """

    normalized = normalize_ground_infantry_action(action)
    if normalized.route_intent != "direct":
        raise GroundInfantryProxyError(
            "native MissionCommand projection cannot represent route_intent; keep non-direct "
            "actions on the proxy contract"
        )
    speed_limit = _positive(max_speed_mps, "max_speed_mps")
    cadence = _positive(tactical_cadence_hz, "tactical_cadence_hz")

    command = ef_py.MissionCommand()
    command.active = True
    command.cmd_heading_deg = float(normalized.desired_heading_deg)
    command.cmd_speed_mps = float(normalized.desired_speed_fraction) * speed_limit
    command.cmd_altitude_m = 0.0
    command.ground_task_mode = ef_py.GroundTaskMode.MoveStatic
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
) -> Any:
    """Project a representable action into a maintained world assignment."""

    command = build_ground_infantry_mission_command(
        action,
        max_speed_mps=max_speed_mps,
        objective_area_id=objective_area_id,
        objective_node_id=objective_node_id,
        ground_commander_id=ground_commander_id,
        tactical_cadence_hz=tactical_cadence_hz,
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
