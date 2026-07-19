from __future__ import annotations

from importlib import import_module
from typing import Any

import ef_py

from python.tasking_contracts.bridge_views import (
    TASKING_INSTRUMENT_READ_BLOCKER,
    TASKING_TRUTH_READ_BLOCKER,
    LoaderOwnedRuntimeView,
    LoaderOwnedScriptedOpponentKernelView,
    MissionCommandView,
    apply_loader_owned_world_layout_to_kernel,
    get_policy_agent_observation,
    get_policy_instrument_state,
    has_mission_command_dict,
    loader_owned_runtime_view,
    loader_owned_scripted_opponent_kernel_view,
    mission_command_dict,
    mission_command_view,
    resolve_loader_time_step,
    sync_loader_command_chain,
    sync_loader_command_chain_reentrant,
    sync_loader_mission_command,
)

# I24 (W2 critical period) moved the loader-owned runtime views and the
# profile-independent command-chain/mission-command helpers above into the
# neutral `python.tasking_contracts.bridge_views` module so `gym_envs` no
# longer has to import `python.rl` for them. Every re-exported name is the
# exact same object as its neutral-layer counterpart (see the compat-shim
# assertIs test in `tests/architecture/tasking_contracts/`).
#
# Everything below this line is the genuine entanglement point that stays
# `python.rl`-internal: it dispatches to the air/ground/naval profile
# implementations (`python.rl.tasking.{air,ground,naval}_adapter`, in turn
# backed by `python.rl.profile.*`), which are themselves `python.rl`-internal
# and out of scope for the neutral contracts layer.


class _ProfileModuleProxy:
    def __init__(self, module_name: str):
        self._module_name = str(module_name)

    def _module(self):
        return import_module(f"{__package__}.{self._module_name}")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._module(), name)

    def __repr__(self) -> str:
        return f"<tasking-profile-proxy {self._module_name}>"


_air = _ProfileModuleProxy("air_adapter")
_ground = _ProfileModuleProxy("ground_adapter")
_naval = _ProfileModuleProxy("naval_adapter")


def _normalized_profile_name(profile_name: Any | None) -> str | None:
    if profile_name is None:
        return None

    service_profile = getattr(ef_py, "ServiceProfile", None)
    if service_profile is not None:
        if profile_name == getattr(service_profile, "Unspecified", object()):
            return None
        if profile_name == getattr(service_profile, "Navy", object()):
            return "naval"
        if profile_name == getattr(service_profile, "Army", object()):
            return "ground"
        if profile_name == getattr(service_profile, "AirForce", object()):
            return "air"

    text = str(getattr(profile_name, "name", profile_name)).strip().lower()
    if "serviceprofile." in text:
        text = text.rsplit(".", 1)[-1]

    if text in {"", "unspecified"}:
        return None
    if text in {"air", "airforce", "joint"}:
        return "air"
    if text in {"army", "ground", "land"}:
        return "ground"
    if text in {"naval", "navy"}:
        return "naval"
    return None


def _profile_candidate_has_value(candidate: Any) -> bool:
    if candidate is None:
        return False
    text = str(getattr(candidate, "name", candidate)).strip().lower()
    if "serviceprofile." in text:
        text = text.rsplit(".", 1)[-1]
    return text not in {"", "unspecified"}


def _strict_profile_name(profile_name: Any | None) -> str | None:
    normalized = _normalized_profile_name(profile_name)
    if normalized is not None:
        return normalized
    if not _profile_candidate_has_value(profile_name):
        return None
    raise ValueError(f"Unknown tasking profile: {profile_name!r}")


def _resolve_profile_from_candidates(*candidates: Any, strict: bool = False) -> Any:
    for candidate in candidates:
        normalized = _strict_profile_name(candidate) if strict else _normalized_profile_name(candidate)
        if normalized is not None:
            return resolve_tasking_profile(candidate)
    return resolve_tasking_profile(None)


def resolve_tasking_profile(profile_name: str | None = None):
    normalized = _normalized_profile_name(profile_name)
    if normalized is None:
        if profile_name is None or not str(getattr(profile_name, "name", profile_name)).strip():
            return _air
        raise ValueError(f"Unknown tasking profile: {profile_name!r}")
    if normalized == "air":
        return _air
    if normalized == "ground":
        return _ground
    if normalized == "naval":
        return _naval
    raise ValueError(f"Unknown tasking profile: {profile_name!r}")


def tasking_profile_for_loader(loader: Any):
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    mission_cfg = None
    if isinstance(scenario_data, dict):
        mission_cfg = scenario_data.get("mission_command", None)

    task_order = getattr(loader, "task_order", None)
    mission_cmd = mission_command_dict(loader)
    explicit_profile_candidates = [
        scenario_data.get("tasking_profile", None) if isinstance(scenario_data, dict) else None,
        mission_cfg.get("tasking_profile", None) if isinstance(mission_cfg, dict) else None,
        getattr(task_order, "tasking_profile", None),
        mission_cmd.get("tasking_profile", None),
    ]
    profile = _resolve_profile_from_candidates(*explicit_profile_candidates, strict=True)
    if profile is not _air or any(_normalized_profile_name(candidate) == "air" for candidate in explicit_profile_candidates):
        return profile

    inferred_profile_candidates = [
        getattr(task_order, "service_profile", None),
        mission_cmd.get("service_profile", None),
        mission_cfg.get("service_profile", None) if isinstance(mission_cfg, dict) else None,
        scenario_data.get("service_profile", None) if isinstance(scenario_data, dict) else None,
    ]
    return _resolve_profile_from_candidates(*inferred_profile_candidates, strict=True)


def normalize_task_order_spec(order_spec: dict[str, Any] | None, *, loader: Any | None = None) -> dict[str, Any]:
    if loader is not None:
        profile = tasking_profile_for_loader(loader)
    else:
        if isinstance(order_spec, dict):
            profile = _resolve_profile_from_candidates(
                order_spec.get("tasking_profile", None),
                order_spec.get("service_profile", None),
            )
        else:
            profile = resolve_tasking_profile(None)
    return profile.normalize_task_order_spec(order_spec)


def build_kernel_mission_command(loader: Any):
    return tasking_profile_for_loader(loader).build_kernel_mission_command(loader)


def make_rule_based_leader_phase_manager(loader: Any | None = None, **kwargs: Any):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.RuleBasedLeaderPhaseManager(**kwargs)


def make_scripted_c2_task_manager(loader: Any | None = None, **kwargs: Any):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.ScriptedC2TaskManager(**kwargs)


def scripted_c2_task_manager_class(loader: Any | None = None):
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.ScriptedC2TaskManager


def is_patrol_task(
    task: Any | None = None,
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    loader: Any | None = None,
) -> bool:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.is_patrol_task(task, task_name=task_name, phase_name=phase_name)


def is_recover_task(
    task: Any | None = None,
    *,
    task_name: str | None = None,
    phase_name: str | None = None,
    loader: Any | None = None,
) -> bool:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.is_recover_task(task, task_name=task_name, phase_name=phase_name)


def task_observation_codes(
    task: Any | None,
    *,
    fallback_phase_id: int = 0,
    loader: Any | None = None,
) -> tuple[float, float, float]:
    profile = tasking_profile_for_loader(loader) if loader is not None else resolve_tasking_profile(None)
    return profile.task_observation_codes(task, fallback_phase_id=fallback_phase_id)


def infer_route_ref_id(loader: Any) -> int:
    return tasking_profile_for_loader(loader).infer_route_ref_id(loader)


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    return tasking_profile_for_loader(loader).infer_recovery_base_id(loader, task=task)


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    return tasking_profile_for_loader(loader).infer_recovery_runway_id(loader, task=task)


def infer_recovery_approach_type(loader: Any, task: Any | None = None):
    return tasking_profile_for_loader(loader).infer_recovery_approach_type(loader, task=task)


def has_active_waypoint_leg(loader: Any) -> bool:
    profile = tasking_profile_for_loader(loader)
    probe = getattr(profile, "has_active_waypoint_leg", None)
    if callable(probe):
        return bool(probe(loader))
    return False


def landing_reference_heading_deg(loader: Any, default_heading_deg: float) -> float:
    profile = tasking_profile_for_loader(loader)
    probe = getattr(profile, "_landing_reference_heading_deg", None)
    if callable(probe):
        return float(probe(loader, default_heading_deg))
    return float(default_heading_deg)


__all__ = [
    "TASKING_INSTRUMENT_READ_BLOCKER",
    "TASKING_TRUTH_READ_BLOCKER",
    "LoaderOwnedRuntimeView",
    "LoaderOwnedScriptedOpponentKernelView",
    "MissionCommandView",
    "apply_loader_owned_world_layout_to_kernel",
    "build_kernel_mission_command",
    "get_policy_agent_observation",
    "get_policy_instrument_state",
    "has_active_waypoint_leg",
    "has_mission_command_dict",
    "infer_recovery_approach_type",
    "infer_recovery_base_id",
    "infer_recovery_runway_id",
    "infer_route_ref_id",
    "is_patrol_task",
    "is_recover_task",
    "landing_reference_heading_deg",
    "loader_owned_runtime_view",
    "loader_owned_scripted_opponent_kernel_view",
    "make_rule_based_leader_phase_manager",
    "make_scripted_c2_task_manager",
    "mission_command_dict",
    "mission_command_view",
    "normalize_task_order_spec",
    "resolve_loader_time_step",
    "resolve_tasking_profile",
    "scripted_c2_task_manager_class",
    "sync_loader_command_chain",
    "sync_loader_command_chain_reentrant",
    "sync_loader_mission_command",
    "task_observation_codes",
    "tasking_profile_for_loader",
]
