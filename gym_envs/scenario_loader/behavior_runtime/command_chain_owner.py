from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from python.rl.tasking.bridge import make_rule_based_leader_phase_manager


COMMAND_CHAIN_OWNER_ATTRS = frozenset(
    {
        "_leader_phase_manager",
        "_naval_screen_last_reference_id",
        "_naval_screen_last_heading_deg",
        "_naval_screen_last_speed_mps",
        "_naval_screen_use_direct_command",
    }
)


@dataclass(slots=True)
class CommandChainOwner:
    _leader_phase_manager: Any = None
    _naval_screen_last_reference_id: int = 0
    _naval_screen_last_heading_deg: float | None = None
    _naval_screen_last_speed_mps: float | None = None
    _naval_screen_use_direct_command: bool = False

    def reset_naval_screen_state(self) -> None:
        self._naval_screen_last_reference_id = 0
        self._naval_screen_last_heading_deg = None
        self._naval_screen_last_speed_mps = None
        self._naval_screen_use_direct_command = False

    def reset(self, loader: Any | None = None) -> None:
        self._leader_phase_manager = make_rule_based_leader_phase_manager(loader)
        self.reset_naval_screen_state()


def make_command_chain_owner(loader: Any | None = None) -> CommandChainOwner:
    owner = CommandChainOwner()
    owner.reset(loader)
    return owner


def ensure_command_chain_owner(loader: Any) -> CommandChainOwner:
    owner = getattr(loader, "_command_chain_owner", None)
    if owner is None:
        owner = make_command_chain_owner(loader)
        loader._command_chain_owner = owner
    return owner


def reset_command_chain_owner(loader: Any) -> CommandChainOwner:
    owner = make_command_chain_owner(loader)
    loader._command_chain_owner = owner
    return owner
