from __future__ import annotations

from typing import Any

from . import air_adapter as _air
from . import naval_adapter as _naval


def resolve_tasking_profile(profile_name: str | None = None):
    normalized = str(profile_name or "air").strip().lower()
    if normalized in {"", "air", "airforce", "joint"}:
        return _air
    if normalized in {"naval", "navy"}:
        return _naval
    raise ValueError(f"Unknown tasking profile: {profile_name!r}")


def tasking_profile_for_loader(loader: Any):
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    profile_name = None
    if isinstance(scenario_data, dict):
        profile_name = scenario_data.get("tasking_profile", None)
        if profile_name is None:
            mission_cmd = scenario_data.get("mission_command", None)
            if isinstance(mission_cmd, dict):
                profile_name = mission_cmd.get("tasking_profile", None)
    return resolve_tasking_profile(profile_name)


def normalize_task_order_spec(order_spec: dict[str, Any] | None, *, loader: Any | None = None) -> dict[str, Any]:
    if loader is not None:
        profile = tasking_profile_for_loader(loader)
    else:
        profile_name = None
        if isinstance(order_spec, dict):
            profile_name = order_spec.get("tasking_profile", None)
            if profile_name is None:
                profile_name = order_spec.get("service_profile", None)
        profile = resolve_tasking_profile(profile_name)
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
