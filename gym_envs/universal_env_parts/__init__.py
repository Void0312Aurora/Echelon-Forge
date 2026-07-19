"""Universal env parts — public names resolve lazily (PEP 562).

I27: package init must not eagerly import residual profile-dispatch modules
(``info`` / ``naval_actions`` / ``observations``) that previously pulled
``python.rl`` via module-level bridge imports.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "AIR_COMBAT_HYBRID_V1_ACTION_DIM",
    "AIR_COMBAT_HYBRID_V1_ACTION_MODE",
    "add_air_combat_event_action_info",
    "air_combat_event_action_contract_present",
    "air_combat_hybrid_effective_action",
    "apply_air_combat_event_action_gate",
    "build_pilot_action",
    "build_step_info",
    "build_step_info_minimal",
    "build_universal_observation",
    "downsample_visual_mean",
    "expected_action_dim",
    "finalize_air_combat_event_action_info",
    "append_temporal_history",
    "apply_naval_station_action",
    "attach_temporal_history",
    "bind_naval_station_eval_reference",
    "build_naval_station_action_transport",
    "build_neutral_ship_pilot_action",
    "half_to_unit",
    "is_air_combat_hybrid_action_mode",
    "is_naval_station_action_mode",
    "make_action_space",
    "make_observation_space",
    "make_temporal_history_buffer",
    "mission_observation_dim",
    "NAVAL_STATION3_ACTION_FAMILY",
    "NAVAL_STATION3_ACTION_MODE",
    "NAVAL_STATION3_CARRIER_INTERFACE_KIND",
    "NAVAL_STATION3_COMMAND_SURFACE_KIND",
    "NAVAL_STATION3_TRANSPORT_ADAPTER_KIND",
    "NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE",
    "NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE",
    "NavalStationActionTransport",
    "build_naval_station_command_surface",
    "naval_action_family_for_mode",
    "naval_policy_instruments",
    "naval_station_action_command",
    "normalize_action",
    "reset_air_combat_event_action_state",
    "reset_naval_station_action_state",
    "reset_temporal_history",
    "temporal_history_enabled",
    "validate_naval_action_mode_for_loader",
]

# name -> (relative module, attribute)
_EXPORTS: dict[str, tuple[str, str]] = {
    "AIR_COMBAT_HYBRID_V1_ACTION_DIM": (".spaces", "AIR_COMBAT_HYBRID_V1_ACTION_DIM"),
    "AIR_COMBAT_HYBRID_V1_ACTION_MODE": (".spaces", "AIR_COMBAT_HYBRID_V1_ACTION_MODE"),
    "add_air_combat_event_action_info": (".air_combat_event_action", "add_air_combat_event_action_info"),
    "air_combat_event_action_contract_present": (
        ".air_combat_event_action",
        "air_combat_event_action_contract_present",
    ),
    "air_combat_hybrid_effective_action": (".actions", "air_combat_hybrid_effective_action"),
    "apply_air_combat_event_action_gate": (".air_combat_event_action", "apply_air_combat_event_action_gate"),
    "build_pilot_action": (".actions", "build_pilot_action"),
    "build_step_info": (".info", "build_step_info"),
    "build_step_info_minimal": (".info", "build_step_info_minimal"),
    "build_universal_observation": (".observations", "build_universal_observation"),
    "downsample_visual_mean": (".observations", "downsample_visual_mean"),
    "expected_action_dim": (".spaces", "expected_action_dim"),
    "finalize_air_combat_event_action_info": (
        ".air_combat_event_action",
        "finalize_air_combat_event_action_info",
    ),
    "append_temporal_history": (".history", "append_temporal_history"),
    "apply_naval_station_action": (".naval_actions", "apply_naval_station_action"),
    "attach_temporal_history": (".history", "attach_temporal_history"),
    "bind_naval_station_eval_reference": (".naval_actions", "bind_naval_station_eval_reference"),
    "build_naval_station_action_transport": (".naval_actions", "build_naval_station_action_transport"),
    "build_neutral_ship_pilot_action": (".naval_actions", "build_neutral_ship_pilot_action"),
    "half_to_unit": (".actions", "half_to_unit"),
    "is_air_combat_hybrid_action_mode": (".actions", "is_air_combat_hybrid_action_mode"),
    "is_naval_station_action_mode": (".naval_actions", "is_naval_station_action_mode"),
    "make_action_space": (".spaces", "make_action_space"),
    "make_observation_space": (".spaces", "make_observation_space"),
    "make_temporal_history_buffer": (".history", "make_temporal_history_buffer"),
    "mission_observation_dim": (".spaces", "mission_observation_dim"),
    "NAVAL_STATION3_ACTION_FAMILY": (".naval_actions", "NAVAL_STATION3_ACTION_FAMILY"),
    "NAVAL_STATION3_ACTION_MODE": (".naval_actions", "NAVAL_STATION3_ACTION_MODE"),
    "NAVAL_STATION3_CARRIER_INTERFACE_KIND": (".naval_actions", "NAVAL_STATION3_CARRIER_INTERFACE_KIND"),
    "NAVAL_STATION3_COMMAND_SURFACE_KIND": (".naval_actions", "NAVAL_STATION3_COMMAND_SURFACE_KIND"),
    "NAVAL_STATION3_TRANSPORT_ADAPTER_KIND": (".naval_actions", "NAVAL_STATION3_TRANSPORT_ADAPTER_KIND"),
    "NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE": (
        ".naval_actions",
        "NAVAL_STATION3_TRANSPORT_DIAGNOSTICS_NOTE",
    ),
    "NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE": (".naval_actions", "NAVAL_STATION3_TRANSPORT_PAYLOAD_TYPE"),
    "NavalStationActionTransport": (".naval_actions", "NavalStationActionTransport"),
    "build_naval_station_command_surface": (".naval_actions", "build_naval_station_command_surface"),
    "naval_action_family_for_mode": (".naval_actions", "naval_action_family_for_mode"),
    "naval_policy_instruments": (".observations", "naval_policy_instruments"),
    "naval_station_action_command": (".naval_actions", "naval_station_action_command"),
    "normalize_action": (".actions", "normalize_action"),
    "reset_air_combat_event_action_state": (
        ".air_combat_event_action",
        "reset_air_combat_event_action_state",
    ),
    "reset_naval_station_action_state": (".naval_actions", "reset_naval_station_action_state"),
    "reset_temporal_history": (".history", "reset_temporal_history"),
    "temporal_history_enabled": (".history", "temporal_history_enabled"),
    "validate_naval_action_mode_for_loader": (".naval_actions", "validate_naval_action_mode_for_loader"),
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
