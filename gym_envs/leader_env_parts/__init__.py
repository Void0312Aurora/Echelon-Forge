"""Leader env parts — public names resolve lazily (PEP 562).

I27: package init must not eagerly import residual modules
(``decision_runtime`` / ``policy`` / ``execution_runtime`` / ``runtime_facade``)
that previously pulled ``python.rl`` via module-level imports.

No registration side effects were found in the re-export surface; every public
name is safe to resolve on first attribute access. No ``from ... import *``
consumers exist for this package (``__all__`` retained for API completeness).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "apply_leader_command",
    "bucket_allows_command_bias",
    "build_observation",
    "build_execution_env",
    "build_execution_env_from_spec",
    "build_execution_policy",
    "build_execution_runtime",
    "cache_execution_runtime_state",
    "capture_execution_runtime_state",
    "clip_altitude",
    "clip_speed",
    "close_execution_runtime",
    "configure_execution_runtime",
    "current_command_tuple",
    "current_execution_runtime_state",
    "current_leader_window_state",
    "current_runtime_last_state",
    "decode_action",
    "exec_policy_reset",
    "FrozenExecutionPolicyAdapter",
    "fuel_margin_state",
    "has_active_waypoints",
    "LEADER_INTENT_FIELDS",
    "landing_reference_command",
    "LeaderActionMapping",
    "LeaderCommandBridge",
    "LeaderRuntimeFacadeMixin",
    "LeaderRuntimeServices",
    "mapping_has_bias",
    "phase_enum_for_id",
    "phase_name_for_id",
    "predict_execution_action",
    "PILOT_REPORT_FIELDS",
    "resolve_execution_env_spec",
    "resolve_report_type",
    "sanitize_action_mapping",
    "snapshot_leader_state",
    "ScriptedExecutiveController",
    "station_metrics",
    "sync_bridge_from_loader",
    "TASK_ORDER_FIELDS",
    "terminal_context",
    "terminal_feasible",
    "clone_leader_intent",
    "clone_pilot_report",
    "clone_task_order",
    "load_json_dict",
    "load_policy",
    "leader_runtime_services",
    "make_args_stub",
    "wrap_deg",
    "zero_mapping_biases",
]

# name -> (relative module, attribute)
_EXPORTS: dict[str, tuple[str, str]] = {
    "apply_leader_command": (".decision_runtime", "apply_leader_command"),
    "bucket_allows_command_bias": (".decision_runtime", "bucket_allows_command_bias"),
    "build_observation": (".decision_runtime", "build_observation"),
    "build_execution_env": (".execution_runtime", "build_execution_env"),
    "build_execution_env_from_spec": (".execution_runtime", "build_execution_env_from_spec"),
    "build_execution_policy": (".execution_runtime", "build_execution_policy"),
    "build_execution_runtime": (".execution_runtime", "build_execution_runtime"),
    "cache_execution_runtime_state": (".execution_runtime", "cache_execution_runtime_state"),
    "capture_execution_runtime_state": (".execution_runtime", "capture_execution_runtime_state"),
    "clip_altitude": (".decision_runtime", "clip_altitude"),
    "clip_speed": (".decision_runtime", "clip_speed"),
    "close_execution_runtime": (".execution_runtime", "close_execution_runtime"),
    "configure_execution_runtime": (".execution_runtime", "configure_execution_runtime"),
    "current_command_tuple": (".decision_runtime", "current_command_tuple"),
    "current_execution_runtime_state": (".execution_runtime", "current_execution_runtime_state"),
    "current_leader_window_state": (".execution_runtime", "current_leader_window_state"),
    "current_runtime_last_state": (".execution_runtime", "current_runtime_last_state"),
    "decode_action": (".decision_runtime", "decode_action"),
    "exec_policy_reset": (".execution_runtime", "exec_policy_reset"),
    "FrozenExecutionPolicyAdapter": (".policy", "FrozenExecutionPolicyAdapter"),
    "fuel_margin_state": (".decision_runtime", "fuel_margin_state"),
    "has_active_waypoints": (".decision_runtime", "has_active_waypoints"),
    "LEADER_INTENT_FIELDS": (".contracts", "LEADER_INTENT_FIELDS"),
    "landing_reference_command": (".decision_runtime", "landing_reference_command"),
    "LeaderActionMapping": (".common", "LeaderActionMapping"),
    "LeaderCommandBridge": (".bridges", "LeaderCommandBridge"),
    "LeaderRuntimeFacadeMixin": (".runtime_facade", "LeaderRuntimeFacadeMixin"),
    "LeaderRuntimeServices": (".runtime_services", "LeaderRuntimeServices"),
    "mapping_has_bias": (".decision_runtime", "mapping_has_bias"),
    "phase_enum_for_id": (".decision_runtime", "phase_enum_for_id"),
    "phase_name_for_id": (".decision_runtime", "phase_name_for_id"),
    "predict_execution_action": (".execution_runtime", "predict_execution_action"),
    "PILOT_REPORT_FIELDS": (".contracts", "PILOT_REPORT_FIELDS"),
    "resolve_execution_env_spec": (".execution_runtime", "resolve_execution_env_spec"),
    "resolve_report_type": (".decision_runtime", "resolve_report_type"),
    "sanitize_action_mapping": (".decision_runtime", "sanitize_action_mapping"),
    "snapshot_leader_state": (".execution_runtime", "snapshot_leader_state"),
    "ScriptedExecutiveController": (".scripted_exec", "ScriptedExecutiveController"),
    "station_metrics": (".decision_runtime", "station_metrics"),
    "sync_bridge_from_loader": (".execution_runtime", "sync_bridge_from_loader"),
    "TASK_ORDER_FIELDS": (".contracts", "TASK_ORDER_FIELDS"),
    "terminal_context": (".decision_runtime", "terminal_context"),
    "terminal_feasible": (".decision_runtime", "terminal_feasible"),
    "clone_leader_intent": (".contracts", "clone_leader_intent"),
    "clone_pilot_report": (".contracts", "clone_pilot_report"),
    "clone_task_order": (".contracts", "clone_task_order"),
    "load_json_dict": (".common", "load_json_dict"),
    "load_policy": (".policy", "load_policy"),
    "leader_runtime_services": (".runtime_services", "leader_runtime_services"),
    "make_args_stub": (".common", "make_args_stub"),
    "wrap_deg": (".common", "wrap_deg"),
    "zero_mapping_biases": (".decision_runtime", "zero_mapping_biases"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attr = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name, __name__), attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
