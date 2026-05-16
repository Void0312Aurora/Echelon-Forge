"""Tasking subdomain package.

This package hosts the concrete tasking/profile implementation while the
root-level `python.rl.*` modules remain temporary compatibility shims.
"""

from .bridge import (
    build_kernel_mission_command,
    infer_recovery_approach_type,
    infer_recovery_base_id,
    infer_recovery_runway_id,
    infer_route_ref_id,
    is_patrol_task,
    is_recover_task,
    make_rule_based_leader_phase_manager,
    make_scripted_c2_task_manager,
    normalize_task_order_spec,
    resolve_tasking_profile,
    scripted_c2_task_manager_class,
    task_observation_codes,
    tasking_profile_for_loader,
)

__all__ = [
    "build_kernel_mission_command",
    "infer_recovery_approach_type",
    "infer_recovery_base_id",
    "infer_recovery_runway_id",
    "infer_route_ref_id",
    "is_patrol_task",
    "is_recover_task",
    "make_rule_based_leader_phase_manager",
    "make_scripted_c2_task_manager",
    "normalize_task_order_spec",
    "resolve_tasking_profile",
    "scripted_c2_task_manager_class",
    "task_observation_codes",
    "tasking_profile_for_loader",
]
