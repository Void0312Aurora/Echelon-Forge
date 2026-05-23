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


@lru_cache(maxsize=None)
def _bound_fields(binding_name: str) -> tuple[str, ...]:
    try:
        bound_type = getattr(ef_py, binding_name)
    except AttributeError as exc:
        raise _missing_binding_error(binding_name, exc) from exc
    try:
        return public_bound_fields(bound_type())
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
    return command_contract_snapshot(value, _bound_fields("TaskOrder"))


def leader_intent_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return command_contract_snapshot(value, _bound_fields("LeaderIntent"))


def pilot_report_snapshot(value: Any) -> tuple[Any, ...] | None:
    if value is None:
        return None
    return command_contract_snapshot(value, _bound_fields("PilotReport"))


def snapshot_changed(previous: Any, current: Any) -> bool:
    return previous != current


__all__ = [
    "leader_intent_snapshot",
    "mission_command_snapshot",
    "pilot_report_snapshot",
    "snapshot_changed",
    "task_order_snapshot",
]
