from __future__ import annotations

from .common_core_profile import (
    apply_leader_intent_common_core_defaults,
    apply_leader_intent_common_core_spec,
    apply_pilot_report_common_core_defaults,
    apply_pilot_report_common_core_spec,
    apply_task_order_common_core_defaults,
    apply_task_order_common_core_spec,
)
from .leader_tasking import RuleBasedLeaderPhaseManager
from python.simulation.air.tasking import make_scripted_c2_task_manager as _make_scripted_c2_task_manager
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


def make_scripted_c2_task_manager(**kwargs: object):
    """Forward the RL entry point to the simulation-owned Air adapter."""

    return _make_scripted_c2_task_manager(**kwargs)


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
