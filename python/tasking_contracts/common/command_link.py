"""Seeded opaque command delivery; domain payloads are never interpreted."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from math import isclose, isfinite
from random import Random
from typing import Any, Iterable


def _clock(value: Any, *, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"command-link {name} must be finite and non-negative") from exc
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"command-link {name} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class CommandLinkEnvelope:
    sequence: int
    source_node_id: str
    target_node_id: str
    issued_clock_s: float
    deliver_at_s: float
    payload: Any
    expires_at_s: float | None = None


@dataclass(frozen=True)
class CommandLinkReceipt:
    sequence: int
    source_node_id: str
    target_node_id: str
    clock_s: float
    outcome: str


class ScriptedCommandLink:
    """Deliver only authorized edges, with optional loss and finite lifetimes.

    Defaults preserve the lossless delayed-delivery behavior. Receipts retain
    the latest 256 events; counters retain totals until reset. Payload ownership
    stays with the caller, which must supply immutable snapshots.
    """

    def __init__(
        self,
        *,
        active_node_ids: Iterable[str],
        command_edges: Iterable[tuple[str, str]],
        seed: int = 0,
    ) -> None:
        nodes = tuple(str(value).strip() for value in active_node_ids)
        if not nodes or any(not node for node in nodes) or len(set(nodes)) != len(nodes):
            raise ValueError("command link requires unique non-empty active graph nodes")
        self._node_ids = frozenset(nodes)
        self._active_node_ids = set(nodes)
        self._command_edges = frozenset(command_edges)
        if any(
            source not in self._node_ids or target not in self._node_ids
            for source, target in self._command_edges
        ):
            raise ValueError("command-link edge references unknown graph nodes")
        self._seed = int(seed)
        self._rng = Random(self._seed)
        self._pending: list[CommandLinkEnvelope] = []
        self._receipts: deque[CommandLinkReceipt] = deque(maxlen=256)
        self._counts: Counter[str] = Counter()
        self._sequence = 0
        self._last_clock_s = 0.0
        self._closed = False

    @property
    def pending(self) -> tuple[CommandLinkEnvelope, ...]:
        return tuple(self._pending)

    @property
    def receipts(self) -> tuple[CommandLinkReceipt, ...]:
        return tuple(self._receipts)

    @property
    def counts(self) -> dict[str, int]:
        return dict(self._counts)

    def _record(self, envelope: CommandLinkEnvelope, *, clock_s: float, outcome: str) -> None:
        self._receipts.append(
            CommandLinkReceipt(
                envelope.sequence,
                envelope.source_node_id,
                envelope.target_node_id,
                clock_s,
                outcome,
            )
        )
        self._counts[outcome] += 1

    def _advance_clock(self, clock_s: float) -> float:
        self._require_open()
        now = _clock(clock_s, name="clock_s")
        if now < self._last_clock_s:
            raise ValueError("command-link clock moved backwards")
        self._last_clock_s = now
        return now

    def send(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        payload: Any,
        clock_s: float,
        delay_s: float = 0.0,
        ttl_s: float | None = None,
        drop_prob: float = 0.0,
    ) -> CommandLinkEnvelope:
        self._require_open()
        now = _clock(clock_s, name="clock_s")
        delay = _clock(delay_s, name="delay_s")
        probability = _clock(drop_prob, name="drop_prob")
        if probability > 1.0:
            raise ValueError("command-link drop_prob must be in [0, 1]")
        lifetime = None if ttl_s is None else _clock(ttl_s, name="ttl_s")
        if lifetime is not None and lifetime <= 0.0:
            raise ValueError("command-link ttl_s must be positive")
        deliver_at = _clock(now + delay, name="deliver_at_s")
        expires_at = None if lifetime is None else _clock(now + lifetime, name="expires_at_s")
        source, target = str(source_node_id).strip(), str(target_node_id).strip()
        if source not in self._active_node_ids or target not in self._active_node_ids:
            raise KeyError("command-link source and target must be active graph nodes")
        if (source, target) not in self._command_edges:
            raise ValueError(
                f"command-link rejects undeclared command edge: {source!r} -> {target!r}"
            )
        self._advance_clock(now)
        self._sequence += 1
        envelope = CommandLinkEnvelope(
            self._sequence, source, target, now, deliver_at, payload, expires_at
        )
        if probability > 0.0 and self._rng.random() < probability:
            self._record(envelope, clock_s=now, outcome="dropped")
        else:
            self._pending.append(envelope)
            self._record(envelope, clock_s=now, outcome="queued")
        return envelope

    def deliver(self, *, clock_s: float) -> tuple[CommandLinkEnvelope, ...]:
        now = self._advance_clock(clock_s)
        due: list[CommandLinkEnvelope] = []
        remaining: list[CommandLinkEnvelope] = []
        for item in self._pending:
            # Expiration wins at the exact boundary, including before a delay
            # has elapsed. No expired command reaches the domain consumer.
            if item.expires_at_s is not None and now >= item.expires_at_s:
                self._record(item, clock_s=now, outcome="expired")
            elif item.deliver_at_s <= now or isclose(
                item.deliver_at_s, now, rel_tol=0.0, abs_tol=1e-12
            ):
                due.append(item)
            else:
                remaining.append(item)
        self._pending = remaining
        due.sort(key=lambda item: (item.deliver_at_s, item.sequence))
        for item in due:
            self._record(item, clock_s=now, outcome="delivered")
        return tuple(due)

    def set_node_available(self, node_id: str, *, available: bool, clock_s: float) -> None:
        node = str(node_id).strip()
        if node not in self._node_ids:
            raise KeyError(f"command-link unknown graph node: {node!r}")
        now = self._advance_clock(clock_s)
        if available:
            self._active_node_ids.add(node)
            return
        self._active_node_ids.discard(node)
        remaining = []
        for item in self._pending:
            if node in (item.source_node_id, item.target_node_id):
                self._record(item, clock_s=now, outcome="cancelled")
            else:
                remaining.append(item)
        self._pending = remaining

    def reset(self, *, seed: int | None = None) -> None:
        self._require_open()
        if seed is not None:
            self._seed = int(seed)
        self._rng.seed(self._seed)
        self._active_node_ids = set(self._node_ids)
        self._pending.clear()
        self._receipts.clear()
        self._counts.clear()
        self._sequence = 0
        self._last_clock_s = 0.0

    def close(self) -> None:
        self._pending.clear()
        self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("command link is closed")


__all__ = ["CommandLinkEnvelope", "CommandLinkReceipt", "ScriptedCommandLink"]
