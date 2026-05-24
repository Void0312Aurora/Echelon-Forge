from __future__ import annotations

from typing import Any

from gym_envs.universal_env import build_step_info


_RUNTIME_COMPAT_TRUE = {"1", "true", "on", "yes", "compat", "compatibility", "diagnostics", "debug"}
_RUNTIME_COMPAT_FALSE = {"", "0", "false", "off", "no", "none", "mainline", "compiled"}


def normalize_runtime_compatibility_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return bool(value)
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in _RUNTIME_COMPAT_TRUE:
        return True
    if normalized in _RUNTIME_COMPAT_FALSE:
        return False
    return bool(value)


def runtime_compatibility_required_message(surface: str) -> str:
    return (
        f"{surface} is a quarantined compatibility/diagnostics escape hatch; "
        "pass runtime_compatibility_enabled=True to opt in explicitly."
    )


def resolve_loader_runtime_sim(loader: Any) -> Any:
    """Name the loader-owned runtime seam used by maintained reward/info helpers."""
    return getattr(loader, "sim")


def compute_loader_step_outcome(
    loader: Any,
    *,
    obs: Any,
    steps: int,
    max_steps: int,
    truth: Any,
    inst_state: Any,
    step_evaluation: dict[str, Any] | None = None,
) -> tuple[Any, Any, Any, Any]:
    return loader.compute_full_step(
        obs,
        resolve_loader_runtime_sim(loader),
        steps,
        max_steps,
        truth=truth,
        inst_state=inst_state,
        step_evaluation=step_evaluation,
    )


def build_loader_step_info(
    loader: Any,
    *,
    entity_id: int,
    mission_status: Any,
    terminated: bool,
    truncated: bool,
    inst_now: Any,
    truth_now: Any,
) -> dict[str, Any]:
    return build_step_info(
        loader,
        resolve_loader_runtime_sim(loader),
        int(entity_id),
        mission_status=mission_status,
        terminated=bool(terminated),
        truncated=bool(truncated),
        inst_now=inst_now,
        truth_now=truth_now,
    )


__all__ = [
    "build_loader_step_info",
    "compute_loader_step_outcome",
    "normalize_runtime_compatibility_enabled",
    "resolve_loader_runtime_sim",
    "runtime_compatibility_required_message",
]
