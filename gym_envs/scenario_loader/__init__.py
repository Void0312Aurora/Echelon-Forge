"""Scenario loader package — public names resolve lazily (PEP 562).

I27: avoid eager re-exports that pulled residual profile-dispatch modules
(and thereby ``python.rl``) into ``sys.modules`` during package init.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "OBJECTIVE_DYNAMIC_TARGET_MAP",
    "OBJECTIVE_OP_MAP",
    "OBJECTIVE_PROPERTY_MAP",
    "ScenarioLoader",
    "coerce_nonnegative_int",
    "execution_step_runtime_mode_enabled",
    "formation_role_code_from_member",
    "normalize_execution_step_runtime_mode",
    "normalize_flight_shaping_backend",
    "safe_json_dict_loads",
    "stable_json_dumps",
]

# name -> (relative module, attribute)
_EXPORTS: dict[str, tuple[str, str]] = {
    "OBJECTIVE_DYNAMIC_TARGET_MAP": (".common", "OBJECTIVE_DYNAMIC_TARGET_MAP"),
    "OBJECTIVE_OP_MAP": (".common", "OBJECTIVE_OP_MAP"),
    "OBJECTIVE_PROPERTY_MAP": (".common", "OBJECTIVE_PROPERTY_MAP"),
    "ScenarioLoader": (".core", "ScenarioLoader"),
    "coerce_nonnegative_int": (".common", "coerce_nonnegative_int"),
    "execution_step_runtime_mode_enabled": (".common", "execution_step_runtime_mode_enabled"),
    "formation_role_code_from_member": (".common", "formation_role_code_from_member"),
    "normalize_execution_step_runtime_mode": (".common", "normalize_execution_step_runtime_mode"),
    "normalize_flight_shaping_backend": (".common", "normalize_flight_shaping_backend"),
    "safe_json_dict_loads": (".common", "safe_json_dict_loads"),
    "stable_json_dumps": (".common", "stable_json_dumps"),
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
