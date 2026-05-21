from __future__ import annotations

from typing import Any

import ef_py

from . import air_adapter as _air
from . import ground_adapter as _ground
from . import naval_adapter as _naval


def _normalized_profile_name(profile_name: Any | None) -> str | None:
    if profile_name is None:
        return None

    service_profile = getattr(ef_py, "ServiceProfile", None)
    if service_profile is not None:
        if profile_name == getattr(service_profile, "Navy", object()):
            return "naval"
        if profile_name == getattr(service_profile, "Army", object()):
            return "ground"
        if profile_name == getattr(service_profile, "AirForce", object()):
            return "air"

    text = str(getattr(profile_name, "name", profile_name)).strip().lower()
    if text.startswith("serviceprofile."):
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


def _resolve_profile_from_candidates(*candidates: Any) -> Any:
    for candidate in candidates:
        normalized = _normalized_profile_name(candidate)
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
    mission_cmd = getattr(loader, "mission_cmd", None)
    explicit_profile_candidates = [
        scenario_data.get("tasking_profile", None) if isinstance(scenario_data, dict) else None,
        mission_cfg.get("tasking_profile", None) if isinstance(mission_cfg, dict) else None,
        getattr(task_order, "tasking_profile", None),
        mission_cmd.get("tasking_profile", None) if isinstance(mission_cmd, dict) else None,
    ]
    profile = _resolve_profile_from_candidates(*explicit_profile_candidates)
    if profile is not _air or any(_normalized_profile_name(candidate) == "air" for candidate in explicit_profile_candidates):
        return profile

    inferred_profile_candidates = [
        getattr(task_order, "service_profile", None),
        mission_cmd.get("service_profile", None) if isinstance(mission_cmd, dict) else None,
        mission_cfg.get("service_profile", None) if isinstance(mission_cfg, dict) else None,
        scenario_data.get("service_profile", None) if isinstance(scenario_data, dict) else None,
    ]
    return _resolve_profile_from_candidates(*inferred_profile_candidates)


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
