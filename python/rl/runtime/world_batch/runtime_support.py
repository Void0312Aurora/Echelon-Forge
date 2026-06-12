from __future__ import annotations

from typing import Any

from gym_envs.universal_env import build_step_info


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
    "resolve_loader_runtime_sim",
]
