"""Injection port for Air C2 task-order projection.

Task-order DTOs are runtime-owned artifacts. The C2 decision layer only needs
to request that the active order be projected for a new task state; the
implementation may bind compiled enums, scenario schemas, or another
simulation provider. This protocol keeps those concerns out of the Air
decision algorithms.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class C2TaskOrderProjection(Protocol):
    """Project one C2 task state into the runtime's task-order DTO."""

    def retask_order(self, loader: Any, *, task_name: str, sim_time_s: float) -> None: ...


__all__ = ["C2TaskOrderProjection"]
