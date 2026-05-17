"""Control subdomain package for command semantics and scripted controllers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .mission_defs import (
    COMMAND_CODE_IDLE,
    COMMAND_CODE_LANDING,
    COMMAND_CODE_ROUTE,
    COMMAND_CODE_TAKEOFF,
    COMMAND_CODE_VECTOR,
    COMMAND_NAME_TO_CODE,
    CRUISE_PHASE_NAMES,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    command_code_for_phase_name,
    is_cruise_phase_name,
    is_landing_command_code,
    is_landing_phase_name,
    is_route_command_code,
    is_takeoff_phase_name,
    normalize_command_code,
    normalize_phase_name,
    scripted_mode_for_command_code,
    scripted_mode_for_phase_name,
)
from .scripted_landing import ScriptedLandingController
from .scripted_stable_flight import ScriptedStableFlightController, scripted_stable_flight_action
from .scripted_takeoff import ScriptedTakeoffController

if TYPE_CHECKING:
    from .wrappers import (
        MultiTimescaleActionController,
        MultiTimescaleActionWrapper,
        PreparedMultiTimescaleAction,
        get_action_wrapper_spec,
    )


_LAZY_WRAPPER_EXPORTS = {
    "MultiTimescaleActionController",
    "MultiTimescaleActionWrapper",
    "PreparedMultiTimescaleAction",
    "get_action_wrapper_spec",
}


def __getattr__(name: str):
    if name not in _LAZY_WRAPPER_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        wrappers = import_module(".wrappers", __name__)
    except ModuleNotFoundError as exc:
        if exc.name == "gymnasium":
            raise ModuleNotFoundError(
                "python.rl.control wrappers require the optional dependency 'gymnasium'."
            ) from exc
        raise
    value = getattr(wrappers, name)
    globals()[name] = value
    return value

__all__ = [
    "COMMAND_CODE_IDLE",
    "COMMAND_CODE_LANDING",
    "COMMAND_CODE_ROUTE",
    "COMMAND_CODE_TAKEOFF",
    "COMMAND_CODE_VECTOR",
    "COMMAND_NAME_TO_CODE",
    "CRUISE_PHASE_NAMES",
    "LANDING_PHASE_NAMES",
    "TAKEOFF_PHASE_NAMES",
    "MultiTimescaleActionController",
    "MultiTimescaleActionWrapper",
    "PreparedMultiTimescaleAction",
    "ScriptedLandingController",
    "ScriptedStableFlightController",
    "ScriptedTakeoffController",
    "command_code_for_phase_name",
    "get_action_wrapper_spec",
    "is_cruise_phase_name",
    "is_landing_command_code",
    "is_landing_phase_name",
    "is_route_command_code",
    "is_takeoff_phase_name",
    "normalize_command_code",
    "normalize_phase_name",
    "scripted_mode_for_command_code",
    "scripted_mode_for_phase_name",
    "scripted_stable_flight_action",
]
