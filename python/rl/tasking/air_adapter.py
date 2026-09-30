from __future__ import annotations

import ef_py

from .common_core_profile import (
    apply_leader_intent_common_core_defaults,
    apply_leader_intent_common_core_spec,
    apply_pilot_report_common_core_defaults,
    apply_pilot_report_common_core_spec,
    apply_task_order_common_core_defaults,
    apply_task_order_common_core_spec,
)
from .leader_tasking import RuleBasedLeaderPhaseManager
from python.tasking_contracts.air.tasking.c2_manager import ScriptedC2TaskManager
from python.tasking_contracts.air.tasking.c2_observation import C2ReportTypeCodes
from python.simulation.air.tasking import CompiledAirC2TaskOrderProjection
from python.rl.profile.air_profile import (
    build_kernel_mission_command,
    infer_air_task_family,
    infer_air_task_type,
    infer_coordination_mode,
    infer_recovery_approach_type,
    infer_recovery_base_id,
    infer_recovery_runway_id,
    infer_route_ref_id,
    is_patrol_task,
    is_recover_task,
    normalize_task_order_spec,
    task_observation_codes,
)


def _compiled_c2_report_type_codes() -> C2ReportTypeCodes:
    msg = ef_py.CommMsgType
    return C2ReportTypeCodes(
        none=int(getattr(msg, "None")),
        on_station=int(getattr(msg, "REP_ON_STATION")),
        rtb=int(getattr(msg, "REP_RTB")),
        bingo=int(getattr(msg, "WARN_BINGO")),
        unable=int(getattr(msg, "REP_UNABLE")),
        wilco=int(getattr(msg, "REP_WILCO")),
    )


def make_scripted_c2_task_manager(**kwargs: object) -> ScriptedC2TaskManager:
    """Bind the neutral C2 manager to compiled Air runtime ports."""

    options = dict(kwargs)
    options.setdefault("report_type_codes", _compiled_c2_report_type_codes())
    options.setdefault("task_order_projection", CompiledAirC2TaskOrderProjection())
    return ScriptedC2TaskManager(**options)


__all__ = [
    "RuleBasedLeaderPhaseManager",
    "make_scripted_c2_task_manager",
    "apply_leader_intent_common_core_defaults",
    "apply_leader_intent_common_core_spec",
    "apply_pilot_report_common_core_defaults",
    "apply_pilot_report_common_core_spec",
    "apply_task_order_common_core_defaults",
    "apply_task_order_common_core_spec",
    "build_kernel_mission_command",
    "infer_air_task_family",
    "infer_air_task_type",
    "infer_coordination_mode",
    "infer_recovery_approach_type",
    "infer_recovery_base_id",
    "infer_recovery_runway_id",
    "infer_route_ref_id",
    "is_patrol_task",
    "is_recover_task",
    "normalize_task_order_spec",
    "task_observation_codes",
]
