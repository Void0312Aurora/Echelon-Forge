"""Pure decision-window state record shared with gym_envs.

``LeaderDecisionState`` has no dependency on ``python.rl`` or ``gym_envs``;
runtime adapters import this canonical dataclass directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LeaderDecisionState:
    mapping: Any
    guard_info: dict[str, Any]
    prev_mode: str
    exec_reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    last_info: dict[str, Any] = field(default_factory=dict)
    decision_c2_transitioned: bool = False
    decision_c2_transition_reason: str = ""
    timing: dict[str, float] = field(default_factory=dict)
    execution_step_count: int = 0
    decision_started_at: float = 0.0


__all__ = ["LeaderDecisionState"]
