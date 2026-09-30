"""Deterministic opaque command-link delivery for a scripted joint roster."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Any

from .coordination import ScriptedJointTaskGraph


def _clock(value: Any, *, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"joint command-link {name} must be finite and non-negative") from exc
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"joint command-link {name} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class JointCommandLinkEnvelope:
    """One opaque command delivery record; domain payloads are not decoded."""

    sequence: int
    source_node_id: str
    target_node_id: str
    issued_clock_s: float
    deliver_at_s: float
    payload: Any


class ScriptedJointCommandLink:
    """Queue and deliver graph-scoped commands with deterministic ordering."""

    def __init__(self, graph: ScriptedJointTaskGraph) -> None:
        if not isinstance(graph, ScriptedJointTaskGraph):
            raise TypeError("joint command link requires ScriptedJointTaskGraph")
        active = graph.active_node_ids()
        if not active:
            raise ValueError("joint command link requires active graph nodes")
        self.graph = graph
        self._active_node_ids = frozenset(active)
        self._pending: list[JointCommandLinkEnvelope] = []
        self._sequence = 0
        self._last_clock_s = 0.0
        self._closed = False

    @property
    def pending(self) -> tuple[JointCommandLinkEnvelope, ...]:
        return tuple(self._pending)

    def send(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        payload: Any,
        clock_s: float,
        delay_s: float = 0.0,
    ) -> JointCommandLinkEnvelope:
        self._require_open()
        now = _clock(clock_s, name="clock_s")
        delay = _clock(delay_s, name="delay_s")
        if now < self._last_clock_s:
            raise ValueError("joint command-link clock moved backwards")
        source = str(source_node_id).strip()
        target = str(target_node_id).strip()
        if source not in self._active_node_ids or target not in self._active_node_ids:
            raise KeyError("joint command-link source and target must be active graph nodes")
        if not self.graph.allows_command(source, target):
            raise ValueError(
                f"joint command-link rejects undeclared command edge: {source!r} -> {target!r}"
            )
        self._last_clock_s = now
        self._sequence += 1
        envelope = JointCommandLinkEnvelope(
            sequence=self._sequence,
            source_node_id=source,
            target_node_id=target,
            issued_clock_s=now,
            deliver_at_s=now + delay,
            payload=payload,
        )
        self._pending.append(envelope)
        return envelope

    def reset(self) -> None:
        self._require_open()
        self._pending.clear()
        self._sequence = 0
        self._last_clock_s = 0.0

    def deliver(self, *, clock_s: float) -> tuple[JointCommandLinkEnvelope, ...]:
        self._require_open()
        now = _clock(clock_s, name="clock_s")
        if now < self._last_clock_s:
            raise ValueError("joint command-link clock moved backwards")
        self._last_clock_s = now
        due = tuple(
            sorted(
                (
                    item
                    for item in self._pending
                    if item.deliver_at_s <= now
                    or isclose(item.deliver_at_s, now, rel_tol=0.0, abs_tol=1.0e-12)
                ),
                key=lambda item: (item.deliver_at_s, item.sequence),
            )
        )
        if due:
            delivered = {item.sequence for item in due}
            self._pending = [item for item in self._pending if item.sequence not in delivered]
        return due

    def close(self) -> None:
        self._pending.clear()
        self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("joint command link is closed")


__all__ = ["JointCommandLinkEnvelope", "ScriptedJointCommandLink"]
