from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from gym_envs.scenario_loader import ScenarioLoader

from python.rl.control.wrappers import MultiTimescaleActionController
from python.rl.runtime.multi_agent_runtime import MultiAgentControlSlot, MultiAgentWorldRuntimeView


@dataclass
class BatchWorldHandle:
    env_idx: int
    loader: ScenarioLoader
    scenario_path: str
    render_mode: str | None
    include_visual: bool
    include_proprio: bool
    action_mode: str
    mission_obs_mode: str
    agent_id: int | None = None
    max_steps: int = 1000
    steps: int = 0
    last_action: np.ndarray | None = None
    last_inst: Any = None
    last_truth: Any = None
    randomization_overrides: dict[str, Any] = field(default_factory=dict)
    episode_return: float = 0.0
    episode_length: int = 0
    visual_cache: np.ndarray | None = None
    visual_cache_step: int = -1
    action_controller: MultiTimescaleActionController | None = None
    execution_episode_controller_config: Any = None
    last_mission_command_snapshot: Any = None
    last_task_order_snapshot: Any = None
    last_leader_intent_snapshot: Any = None
    last_pilot_report_snapshot: Any = None

    @property
    def world_index(self) -> int:
        return int(self.env_idx)

    @property
    def entity_id(self) -> int:
        if self.agent_id is None:
            raise RuntimeError(f"world {self.env_idx} has no active agent_id")
        return int(self.agent_id)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.loader.set_randomization_overrides(overrides)
        self.randomization_overrides = dict(getattr(self.loader, "randomization_overrides", {}) or {})


@dataclass
class CooperativeWorldState:
    world_index: int
    randomization_overrides: dict[str, Any] = field(default_factory=dict)
    leader_overrides: dict[str, Any] = field(default_factory=dict)
    director: Any = None
    routing_loader: ScenarioLoader | None = None
    view: MultiAgentWorldRuntimeView | None = None
    slot_indices: list[int] = field(default_factory=list)
    director_dirty: bool = True
    command_chain_dirty: bool = True
    last_mission_command_snapshots: dict[int, Any] = field(default_factory=dict)
    last_task_order_snapshots: dict[int, Any] = field(default_factory=dict)
    last_leader_intent_snapshots: dict[int, Any] = field(default_factory=dict)
    last_pilot_report_snapshots: dict[int, Any] = field(default_factory=dict)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        if overrides is None:
            self.randomization_overrides = {}
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"randomization overrides must be a dict or None, got {type(overrides)}")
        self.randomization_overrides = dict(overrides)

    def set_leader_overrides(self, overrides: dict | None) -> None:
        if overrides is None:
            self.leader_overrides = {}
            self.director_dirty = True
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"leader overrides must be a dict or None, got {type(overrides)}")
        self.leader_overrides = dict(overrides)
        self.director_dirty = True


@dataclass
class CooperativeSlotState:
    slot_index: int
    local_slot_index: int
    world: CooperativeWorldState
    control_slot: MultiAgentControlSlot
    loader: ScenarioLoader
    max_steps: int
    steps: int = 0
    last_action: np.ndarray | None = None
    last_inst: Any = None
    last_truth: Any = None
    last_obs: dict[str, np.ndarray] | None = None
    episode_return: float = 0.0
    episode_length: int = 0
    visual_cache: np.ndarray | None = None
    visual_cache_step: int = -1
    action_controller: MultiTimescaleActionController | None = None
    coop_success_latched: bool = False
    coop_completion_reason: str = ""
    coop_completion_mission_status: np.ndarray | None = None
    coop_completion_info: dict[str, Any] | None = None
    coop_completion_terminal_observation: dict[str, np.ndarray] | None = None

    @property
    def world_index(self) -> int:
        return int(self.world.world_index)

    @property
    def entity_id(self) -> int:
        return int(self.control_slot.entity_id)

    @property
    def entity_name(self) -> str:
        return str(self.control_slot.entity_name)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.world.set_randomization_overrides(overrides)


__all__ = [
    "BatchWorldHandle",
    "CooperativeSlotState",
    "CooperativeWorldState",
]
