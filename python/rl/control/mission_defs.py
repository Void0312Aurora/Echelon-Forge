"""Compatibility shell: canonical implementation moved to ``python.tasking_contracts.mission_defs``.

I24 (W2 critical period) extracted this module's constants/helpers into the
neutral ``python.tasking_contracts`` layer so ``gym_envs`` no longer needs to
import ``python.rl`` for the task-dispatch vocabulary. Every name below is the
exact same object as its neutral-layer counterpart (see the compat-shim
assertIs test in ``tests/architecture/tasking_contracts/``).
"""

from __future__ import annotations

from python.tasking_contracts.mission_defs import (
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
    "command_code_for_phase_name",
    "is_cruise_phase_name",
    "is_landing_command_code",
    "is_landing_phase_name",
    "is_route_command_code",
    "is_takeoff_phase_name",
    "normalize_command_code",
    "normalize_phase_name",
    "scripted_mode_for_command_code",
    "scripted_mode_for_phase_name",
]
