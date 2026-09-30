"""Event-owned Air combat terminal evaluation for the scripted line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

EntityKey = tuple[int, int]


@dataclass(frozen=True)
class AirCombatTerminalState:
    """Terminal state derived only from maintained engagement reports."""

    status: str
    reason: str
    destroyed_target_ids: tuple[int, ...]
    destroyed_own_ids: tuple[int, ...]
    destroyed_target_keys: tuple[EntityKey, ...]
    destroyed_own_keys: tuple[EntityKey, ...]
    damage_report_ids: tuple[int, ...]


class AirCombatTerminalEvaluator:
    """Evaluate win/loss without reading kernel truth or reward state."""

    def evaluate(
        self,
        packet: Any,
        *,
        own_entity_ids: Iterable[int | EntityKey],
        target_entity_ids: Iterable[int | EntityKey],
    ) -> AirCombatTerminalState:
        own_keys = _entity_keys(own_entity_ids)
        target_keys = _entity_keys(target_entity_ids)
        if not own_keys or not target_keys:
            raise ValueError("Air combat terminal evaluation requires own and target entity IDs")
        destroyed_targets: set[EntityKey] = set()
        destroyed_own: set[EntityKey] = set()
        report_ids: list[int] = []
        for report in list(getattr(packet, "damage_reports", ()) or ()):
            target_key = _entity_key(getattr(report, "target", None))
            if target_key[1] <= 0:
                continue
            report_ids.append(int(getattr(report, "report_id", 0)))
            if not bool(getattr(report, "destroyed", False)):
                continue
            if target_key in target_keys:
                destroyed_targets.add(target_key)
            if target_key in own_keys:
                destroyed_own.add(target_key)

        if own_keys.intersection(destroyed_own):
            status, reason = "combat_loss", "own_entity_destroyed"
        elif target_keys.issubset(destroyed_targets):
            status, reason = "combat_win", "all_targets_destroyed"
        else:
            status, reason = "running", "no_terminal_damage_report"
        return AirCombatTerminalState(
            status=status,
            reason=reason,
            destroyed_target_ids=tuple(sorted({key[1] for key in destroyed_targets})),
            destroyed_own_ids=tuple(sorted({key[1] for key in destroyed_own})),
            destroyed_target_keys=tuple(sorted(destroyed_targets)),
            destroyed_own_keys=tuple(sorted(destroyed_own)),
            damage_report_ids=tuple(report_ids),
        )


def _entity_key(ref: Any) -> EntityKey:
    try:
        return (int(getattr(ref, "world_index", 0)), int(getattr(ref, "entity_id")))
    except (AttributeError, TypeError, ValueError):
        return (0, 0)


def _entity_keys(values: Iterable[int | EntityKey]) -> set[EntityKey]:
    keys: set[EntityKey] = set()
    for value in values:
        if isinstance(value, (tuple, list)) and len(value) == 2:
            key = (int(value[0]), int(value[1]))
        else:
            key = (0, int(value))
        if key[0] < 0 or key[1] <= 0:
            continue
        keys.add(key)
    return keys


__all__ = ["AirCombatTerminalEvaluator", "AirCombatTerminalState", "EntityKey"]
