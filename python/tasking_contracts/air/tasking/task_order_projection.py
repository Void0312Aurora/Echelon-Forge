"""Injection port for Air C2 task-order projection.

Task-order DTOs are runtime-owned artifacts. The C2 decision layer only needs
to request that the active order be projected for the current task state on
each update; the implementation may also refresh time-dependent fields on
non-transition ticks. This protocol keeps those concerns out of the Air
decision algorithms.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class C2TaskOrderProjection(Protocol):
    """Refresh one C2 task state into the runtime's task-order DTO.

    Implementations are called on every manager update, including ticks without
    a task transition. The operation must therefore be idempotent for the
    current task state and may refresh time-dependent fields on each update.
    """

    def retask_order(self, loader: Any, *, task_name: str, sim_time_s: float) -> None: ...


__all__ = ["C2TaskOrderProjection"]
