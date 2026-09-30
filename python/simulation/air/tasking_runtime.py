"""Simulation-owned lifecycle adapter for the neutral scripted Air C2 manager."""

from __future__ import annotations

from typing import Any

from .tasking import make_scripted_c2_task_manager


class AirScriptedTaskingRuntime:
    """Update task state between navigation and leader command projection."""

    def __init__(self, *, manager: Any | None = None) -> None:
        self.manager = manager or make_scripted_c2_task_manager()
        self.transition_history: list[dict[str, Any]] = []
        self.task_sequence: list[str] = []
        self._closed = False

    def reset(
        self,
        loader: Any,
        *,
        sim_time_s: float = 0.0,
        truth: Any = None,
        inst: Any = None,
        sync_to_kernel: bool = False,
    ) -> dict[str, Any]:
        if self._closed:
            raise RuntimeError("Air scripted tasking runtime is closed")
        self.transition_history.clear()
        self.task_sequence.clear()
        info = dict(
            self.manager.reset(
                loader,
                sim_time_s=float(sim_time_s),
                truth=truth,
                inst=inst,
                sync_to_kernel=bool(sync_to_kernel),
            )
            or {}
        )
        task_name = str(info.get("task_name", "")).strip()
        if task_name:
            self.task_sequence.append(task_name)
        return info

    def update(
        self,
        loader: Any,
        *,
        sim_time_s: float,
        truth: Any = None,
        inst: Any = None,
        sync_to_kernel: bool = False,
    ) -> dict[str, Any]:
        if self._closed:
            raise RuntimeError("Air scripted tasking runtime is closed")
        info = dict(
            self.manager.update(
                loader,
                sim_time_s=float(sim_time_s),
                truth=truth,
                inst=inst,
                sync_to_kernel=bool(sync_to_kernel),
            )
            or {}
        )
        if bool(info.get("transitioned", False)):
            task_name = str(info.get("task_name", ""))
            self.transition_history.append(
                {
                    "task_name": task_name,
                    "reason": str(info.get("transition_reason", "")),
                    "sim_time_s": float(sim_time_s),
                }
            )
            if task_name:
                self.task_sequence.append(task_name)
        return info

    def close(self) -> None:
        self._closed = True


__all__ = ["AirScriptedTaskingRuntime"]
