from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from gym_envs.universal_env import build_step_info

if TYPE_CHECKING:
    from .adapter import RuntimeFacadeAdapter


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


class RuntimeCompatibilityView:
    """Compatibility-only view for callers that still expect `vec_env.batch_runtime`."""

    def __init__(self, adapter: RuntimeFacadeAdapter):
        self._adapter = adapter

    def __getattr__(self, name: str) -> Any:
        return getattr(self._adapter, name)

    def world_count(self) -> int:
        return self._adapter.world_count()

    def worker_threads(self) -> int:
        return self._adapter.worker_threads()

    def effective_worker_threads(self) -> int:
        return self._adapter.effective_worker_threads()

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.get_agent_observations_batch(refs)

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.get_instrument_states_batch(refs)

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._adapter.set_pilot_actions_batch(assignments)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._adapter.step_worlds(world_indices)

    def export_execution_episode_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.export_execution_episode_states_batch(refs)

    def execution_episode_controller_ready(self, world_index: int) -> bool:
        return self._adapter.execution_episode_controller_ready(world_index)


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
    "RuntimeCompatibilityView",
    "normalize_runtime_compatibility_enabled",
    "resolve_loader_runtime_sim",
    "runtime_compatibility_required_message",
]
