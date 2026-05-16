from __future__ import annotations

from typing import Any

import ef_py


def public_bound_fields(proto: Any) -> tuple[str, ...]:
    return tuple(name for name in dir(proto) if not name.startswith("_"))


TASK_ORDER_FIELDS = public_bound_fields(ef_py.TaskOrder())
LEADER_INTENT_FIELDS = public_bound_fields(ef_py.LeaderIntent())
PILOT_REPORT_FIELDS = public_bound_fields(ef_py.PilotReport())


def clone_assign_field(out: Any, name: str, value: Any) -> None:
    try:
        setattr(out, name, value)
        return
    except TypeError:
        pass
    except Exception:
        return

    try:
        field_type = type(getattr(out, name))
    except Exception:
        return

    if getattr(field_type, "__module__", "") != "ef_py":
        return

    try:
        coerced = field_type(int(value))
    except Exception:
        return

    try:
        setattr(out, name, coerced)
    except Exception:
        pass


def clone_bound_contract(source: Any, out: Any, field_names: tuple[str, ...]) -> Any:
    if source is None:
        return out
    for name in field_names:
        try:
            clone_assign_field(out, name, getattr(source, name))
        except Exception:
            pass
    return out


def clone_task_order(order: Any) -> ef_py.TaskOrder:
    return clone_bound_contract(order, ef_py.TaskOrder(), TASK_ORDER_FIELDS)


def clone_leader_intent(intent: Any) -> ef_py.LeaderIntent:
    return clone_bound_contract(intent, ef_py.LeaderIntent(), LEADER_INTENT_FIELDS)


def clone_pilot_report(report: Any) -> ef_py.PilotReport:
    return clone_bound_contract(report, ef_py.PilotReport(), PILOT_REPORT_FIELDS)
