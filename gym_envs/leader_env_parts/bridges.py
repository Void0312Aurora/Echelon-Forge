from __future__ import annotations

from typing import Any

import ef_py

from .contracts import clone_leader_intent, clone_pilot_report, clone_task_order


class LeaderCommandBridge:
    """
    Small bridge object installed into ScenarioLoader to replace the rule-only phase manager.

    The leader training env updates this object with the currently selected task/intention state.
    ScenarioLoader will call `update()/sync_to_kernel()` on every low-level sim step, keeping the
    kernel-side command chain aligned with the externally selected leader command.
    """

    def __init__(self) -> None:
        self.task_order = ef_py.TaskOrder()
        self.leader_intent = ef_py.LeaderIntent()
        self.pilot_report = ef_py.PilotReport()

    def set_state(
        self,
        *,
        task_order: Any,
        leader_intent: Any,
        pilot_report: Any,
    ) -> None:
        self.task_order = clone_task_order(task_order)
        self.leader_intent = clone_leader_intent(leader_intent)
        self.pilot_report = clone_pilot_report(pilot_report)

    def reset(self, loader: Any, sim_time_s: float = 0.0, **kwargs) -> None:
        self.update(loader, sim_time_s=sim_time_s, **kwargs)

    def update(self, loader: Any, sim_time_s: float = 0.0, **kwargs) -> None:
        _ = (sim_time_s, kwargs)
        loader.task_order = clone_task_order(self.task_order)
        loader.leader_intent = clone_leader_intent(self.leader_intent)
        loader.pilot_report = clone_pilot_report(self.pilot_report)

    def sync_to_kernel(self, loader: Any) -> None:
        if getattr(loader, "agent_id", None) is None:
            return
        try:
            if hasattr(loader.sim, "set_task_order"):
                loader.sim.set_task_order(loader.agent_id, clone_task_order(self.task_order))
        except Exception:
            pass
        try:
            if hasattr(loader.sim, "set_leader_intent"):
                loader.sim.set_leader_intent(loader.agent_id, clone_leader_intent(self.leader_intent))
        except Exception:
            pass
        try:
            if hasattr(loader.sim, "set_pilot_report"):
                loader.sim.set_pilot_report(loader.agent_id, clone_pilot_report(self.pilot_report))
        except Exception:
            pass
