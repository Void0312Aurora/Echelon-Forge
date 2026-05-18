from __future__ import annotations

from typing import Any

import ef_py


def public_bound_fields(proto: Any) -> tuple[str, ...]:
    return tuple(name for name in dir(proto) if not name.startswith("_"))


MISSION_COMMAND_FIELDS = public_bound_fields(ef_py.MissionCommand())
TASK_ORDER_FIELDS = public_bound_fields(ef_py.TaskOrder())
LEADER_INTENT_FIELDS = public_bound_fields(ef_py.LeaderIntent())
PILOT_REPORT_FIELDS = public_bound_fields(ef_py.PilotReport())


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
    return command_contract_snapshot(value, MISSION_COMMAND_FIELDS)


def task_order_snapshot(value: Any) -> tuple[Any, ...] | None:
    return command_contract_snapshot(value, TASK_ORDER_FIELDS)


def leader_intent_snapshot(value: Any) -> tuple[Any, ...] | None:
    return command_contract_snapshot(value, LEADER_INTENT_FIELDS)


def pilot_report_snapshot(value: Any) -> tuple[Any, ...] | None:
    return command_contract_snapshot(value, PILOT_REPORT_FIELDS)


def snapshot_changed(previous: Any, current: Any) -> bool:
    return previous != current


__all__ = [
    "leader_intent_snapshot",
    "mission_command_snapshot",
    "pilot_report_snapshot",
    "snapshot_changed",
    "task_order_snapshot",
]
