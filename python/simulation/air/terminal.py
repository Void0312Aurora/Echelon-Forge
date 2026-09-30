"""Event-owned Air combat terminal evaluation for the scripted line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AirCombatTerminalState:
    """Terminal state derived only from maintained engagement reports."""

    status: str
    reason: str
    destroyed_target_ids: tuple[int, ...]
    destroyed_own_ids: tuple[int, ...]
    damage_report_ids: tuple[int, ...]


class AirCombatTerminalEvaluator:
    """Evaluate win/loss without reading kernel truth or reward state."""

    def evaluate(
        self,
        packet: Any,
        *,
        own_entity_ids: Iterable[int],
        target_entity_ids: Iterable[int],
    ) -> AirCombatTerminalState:
        own_ids = {int(value) for value in own_entity_ids if int(value) > 0}
        target_ids = {int(value) for value in target_entity_ids if int(value) > 0}
        if not own_ids or not target_ids:
            raise ValueError("Air combat terminal evaluation requires own and target entity IDs")
        destroyed_targets: set[int] = set()
        destroyed_own: set[int] = set()
        report_ids: list[int] = []
        for report in list(getattr(packet, "damage_reports", ()) or ()):
            target_id = _entity_id(getattr(report, "target", None))
            if target_id <= 0:
                continue
            report_ids.append(int(getattr(report, "report_id", 0)))
            if not bool(getattr(report, "destroyed", False)):
                continue
            if target_id in target_ids:
                destroyed_targets.add(target_id)
            if target_id in own_ids:
                destroyed_own.add(target_id)

        if own_ids.intersection(destroyed_own):
            status, reason = "combat_loss", "own_entity_destroyed"
        elif target_ids.issubset(destroyed_targets):
            status, reason = "combat_win", "all_targets_destroyed"
        else:
            status, reason = "running", "no_terminal_damage_report"
        return AirCombatTerminalState(
            status=status,
            reason=reason,
            destroyed_target_ids=tuple(sorted(destroyed_targets)),
            destroyed_own_ids=tuple(sorted(destroyed_own)),
            damage_report_ids=tuple(report_ids),
        )


def _entity_id(ref: Any) -> int:
    try:
        return int(getattr(ref, "entity_id"))
    except (AttributeError, TypeError, ValueError):
        return 0


__all__ = ["AirCombatTerminalEvaluator", "AirCombatTerminalState"]
