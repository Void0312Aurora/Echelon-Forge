from __future__ import annotations

from functools import lru_cache
from typing import Any

import ef_py


def public_bound_fields(proto: Any) -> tuple[str, ...]:
    return tuple(name for name in dir(proto) if not name.startswith("_"))


_FIELD_BINDINGS = {
    "MISSION_COMMAND_FIELDS": "MissionCommand",
    "TASK_ORDER_FIELDS": "TaskOrder",
    "LEADER_INTENT_FIELDS": "LeaderIntent",
    "PILOT_REPORT_FIELDS": "PilotReport",
}


def _missing_binding_error(binding_name: str, exc: Exception) -> RuntimeError:
    return RuntimeError(
        "world_batch command-chain cache requires ef_py."
        f"{binding_name}() to snapshot command contracts, but that binding is unavailable. "
        "Import succeeds because binding resolution is lazy; rebuild or install the matching "
        "runtime bindings before using command-chain synchronization."
    ).with_traceback(exc.__traceback__)


def _bound_instance(binding_name: str) -> Any:
    try:
        bound_type = getattr(ef_py, binding_name)
    except AttributeError as exc:
        raise _missing_binding_error(binding_name, exc) from exc
    try:
        return bound_type()
    except Exception as exc:
        raise _missing_binding_error(binding_name, exc) from exc


@lru_cache(maxsize=None)
def _bound_fields(binding_name: str) -> tuple[str, ...]:
    return public_bound_fields(_bound_instance(binding_name))


@lru_cache(maxsize=None)
def _projection_helper(binding_name: str, helper_name: str) -> Any:
    try:
        return getattr(ef_py, helper_name)
    except AttributeError as exc:
        raise _missing_binding_error(binding_name, exc) from exc


@lru_cache(maxsize=None)
def _helper_projection_fields(binding_name: str, helper_name: str) -> tuple[str, ...]:
    helper = _projection_helper(binding_name, helper_name)
    try:
        return public_bound_fields(helper(_bound_instance(binding_name)))
    except Exception as exc:
        raise _missing_binding_error(binding_name, exc) from exc


def __getattr__(name: str) -> Any:
    binding_name = _FIELD_BINDINGS.get(name)
    if binding_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _bound_fields(binding_name)


def command_contract_snapshot(value: Any, field_names: tuple[str, ...]) -> tuple[Any, ...] | None:
    if value is None:
        return None
    out: list[Any] = []
    for name in field_names:
        try:
            out.append(getattr(value, name))
        except Exception:
            out.append(None)
    return tuple(out)


def mission_command_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return command_contract_snapshot(value, _bound_fields("MissionCommand"))


def task_order_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return (
        _named_projection_snapshot_from_helper(
            value,
            binding_name="TaskOrder",
            projection_name="task_order_shared_core",
            helper_name="task_order_shared_core",
        ),
        _named_projection_snapshot_from_helper(
            value,
            binding_name="TaskOrder",
            projection_name="task_order_air_owner_slice",
            helper_name="task_order_air_owner_slice",
        ),
        _named_projection_snapshot_from_helper(
            value,
            binding_name="TaskOrder",
            projection_name="task_order_naval_owner_slice",
            helper_name="task_order_naval_owner_slice",
        ),
    )


def _projection_snapshot(
    value: Any,
    field_names: tuple[str, ...],
) -> tuple[tuple[str, Any], ...] | None:
    if value is None:
        return None
    return tuple((name, getattr(value, name, None)) for name in field_names)


def _named_projection_snapshot(
    value: Any,
    *,
    projection_name: str,
    field_names: tuple[str, ...],
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    if value is None:
        return None
    snapshot = _projection_snapshot(value, field_names)
    if snapshot is None:
        return None
    return (projection_name, snapshot)


def _named_projection_snapshot_from_helper(
    value: Any,
    *,
    binding_name: str,
    projection_name: str,
    helper_name: str,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    if value is None:
        return None
    helper = _projection_helper(binding_name, helper_name)
    try:
        projection = helper(value)
    except Exception as exc:
        raise _missing_binding_error(binding_name, exc) from exc
    return _named_projection_snapshot(
        projection,
        projection_name=projection_name,
        field_names=_helper_projection_fields(binding_name, helper_name),
    )


def leader_intent_shared_core_projection_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="LeaderIntent",
        projection_name="leader_intent_shared_core",
        helper_name="leader_intent_shared_core",
    )


def leader_intent_air_owner_slice_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="LeaderIntent",
        projection_name="leader_intent_air_owner_slice",
        helper_name="leader_intent_air_owner_slice",
    )


def leader_intent_naval_owner_slice_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="LeaderIntent",
        projection_name="leader_intent_naval_owner_slice",
        helper_name="leader_intent_naval_owner_slice",
    )


def leader_intent_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return (
        leader_intent_shared_core_projection_snapshot(value),
        leader_intent_air_owner_slice_snapshot(value),
        leader_intent_naval_owner_slice_snapshot(value),
    )


def pilot_report_shared_core_projection_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="PilotReport",
        projection_name="pilot_report_shared_core",
        helper_name="pilot_report_shared_core",
    )


def pilot_report_air_owner_slice_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="PilotReport",
        projection_name="pilot_report_air_owner_slice",
        helper_name="pilot_report_air_owner_slice",
    )


def pilot_report_naval_owner_slice_snapshot(
    value: Any,
) -> tuple[str, tuple[tuple[str, Any], ...]] | None:
    return _named_projection_snapshot_from_helper(
        value,
        binding_name="PilotReport",
        projection_name="pilot_report_naval_owner_slice",
        helper_name="pilot_report_naval_owner_slice",
    )


def pilot_report_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return (
        pilot_report_shared_core_projection_snapshot(value),
        pilot_report_air_owner_slice_snapshot(value),
        pilot_report_naval_owner_slice_snapshot(value),
    )


def project_world_leader_intent_assignment_transport(
    assignment: Any,
    *,
    world_index: int,
    entity_id: int,
    compatibility_intent_shell: Any,
) -> Any:
    assignment.world_index = int(world_index)
    assignment.entity_id = int(entity_id)
    assignment.intent = compatibility_intent_shell
    return assignment


def task_order_maintained_batch_contract(
    compatibility_task_order_shell: Any,
) -> Any:
    contract = ef_py.TaskOrderMaintainedBatchContract()
    contract.shared_core = ef_py.task_order_shared_core_directive(
        compatibility_task_order_shell
    )
    contract.air_tasking_identity = ef_py.task_order_air_tasking_identity_directive(
        compatibility_task_order_shell
    )
    contract.air_stationing = ef_py.task_order_air_stationing_directive(
        compatibility_task_order_shell
    )
    contract.air_recovery = ef_py.task_order_air_recovery_directive(
        compatibility_task_order_shell
    )
    contract.air_takeoff = ef_py.task_order_air_takeoff_directive(
        compatibility_task_order_shell
    )
    contract.air_formation = ef_py.task_order_air_formation_directive(
        compatibility_task_order_shell
    )
    contract.naval_command_authority = ef_py.task_order_naval_command_authority(
        compatibility_task_order_shell
    )
    contract.naval_stationing = ef_py.task_order_naval_stationing_directive(
        compatibility_task_order_shell
    )
    return contract


def project_world_task_order_maintained_assignment(
    assignment: Any,
    *,
    world_index: int,
    entity_id: int,
    compatibility_task_order_shell: Any,
) -> Any:
    assignment.world_index = int(world_index)
    assignment.entity_id = int(entity_id)
    assignment.task_order = task_order_maintained_batch_contract(
        compatibility_task_order_shell
    )
    return assignment


def project_world_pilot_report_assignment_transport(
    assignment: Any,
    *,
    world_index: int,
    entity_id: int,
    compatibility_report_shell: Any,
) -> Any:
    assignment.world_index = int(world_index)
    assignment.entity_id = int(entity_id)
    assignment.report = compatibility_report_shell
    return assignment


def snapshot_changed(previous: Any, current: Any) -> bool:
    return previous != current


__all__ = [
    "leader_intent_air_owner_slice_snapshot",
    "leader_intent_naval_owner_slice_snapshot",
    "leader_intent_shared_core_projection_snapshot",
    "leader_intent_snapshot",
    "mission_command_snapshot",
    "pilot_report_air_owner_slice_snapshot",
    "pilot_report_naval_owner_slice_snapshot",
    "pilot_report_shared_core_projection_snapshot",
    "pilot_report_snapshot",
    "project_world_leader_intent_assignment_transport",
    "project_world_pilot_report_assignment_transport",
    "project_world_task_order_maintained_assignment",
    "snapshot_changed",
    "task_order_maintained_batch_contract",
    "task_order_snapshot",
]
