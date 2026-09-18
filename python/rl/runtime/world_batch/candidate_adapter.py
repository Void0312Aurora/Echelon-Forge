"""P4-C shadow-only epoch reference adapter.

This module is intentionally not imported by the maintained facade adapter.
It mirrors the native candidate receipt contract so Python probes cannot
silently turn a bare world/entity id or a caller-authored DTO into authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping


RUNTIME_EPISODE_HANDSHAKE_GENERATION = 1
_KIND = {"action": 0, "reset": 1}
_PHASE = {"running": 0, "terminal": 1}
MAX_RETAINED_RECEIPTS = 4096


def _valid_u64(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2**64 - 1


def _valid_identity_tuple(value: Any) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and all(_valid_u64(item) for item in value)
        and value != (0, 0)
    )


@dataclass(frozen=True, slots=True)
class EpochWorldRef:
    host_id: tuple[int, int]
    boot_id: tuple[int, int]
    incarnation_epoch: int
    world_slot: int
    world_generation: int

    def well_formed(self) -> bool:
        return (
            _valid_identity_tuple(self.host_id)
            and _valid_identity_tuple(self.boot_id)
            and _valid_u64(self.incarnation_epoch)
            and self.incarnation_epoch > 0
            and _valid_u64(self.world_slot)
            and _valid_u64(self.world_generation)
            and self.world_generation > 0
        )


@dataclass(frozen=True, slots=True)
class EpochEntityRef:
    world: EpochWorldRef
    entity_id: int
    entity_generation: int

    def well_formed(self) -> bool:
        return (
            self.world.well_formed()
            and _valid_u64(self.entity_id)
            and self.entity_id > 0
            and _valid_u64(self.entity_generation)
            and self.entity_generation > 0
        )


def _u64(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**64 - 1:
        raise ValueError(f"{path} must be an unsigned 64-bit integer")
    return value


def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{path} must be lowercase SHA-256")
    return value


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    return value


def _identity(value: Any, path: str) -> dict[str, int]:
    value = _mapping(value, path)
    if set(value) != {"high", "low"}:
        raise ValueError(f"{path} has unknown or missing fields")
    result = {
        "high": _u64(value["high"], f"{path}.high"),
        "low": _u64(value["low"], f"{path}.low"),
    }
    if result == {"high": 0, "low": 0}:
        raise ValueError(f"{path} must be non-zero")
    return result


def _episode(value: Any, path: str) -> dict[str, Any]:
    value = _mapping(value, path)
    if set(value) != {"world", "episode_id", "episode_generation"}:
        raise ValueError(f"{path} has unknown or missing fields")
    world = _mapping(value["world"], f"{path}.world")
    inc = _mapping(world.get("incarnation"), f"{path}.world.incarnation")
    host = _mapping(inc.get("host"), f"{path}.world.incarnation.host")
    if set(world) != {"incarnation", "world_slot", "world_generation"} or set(inc) != {
        "host",
        "incarnation_epoch",
    } or set(host) != {"host_id", "boot_id"}:
        raise ValueError(f"{path}.world has unknown or missing fields")
    result = {
        "world": {
            "incarnation": {
                "host": {
                    "host_id": _identity(host["host_id"], f"{path}.world.incarnation.host.host_id"),
                    "boot_id": _identity(host["boot_id"], f"{path}.world.incarnation.host.boot_id"),
                },
                "incarnation_epoch": _u64(inc["incarnation_epoch"], f"{path}.world.incarnation_epoch"),
            },
            "world_slot": _u64(world["world_slot"], f"{path}.world.world_slot"),
            "world_generation": _u64(world["world_generation"], f"{path}.world.world_generation"),
        },
        "episode_id": _identity(value["episode_id"], f"{path}.episode_id"),
        "episode_generation": _u64(value["episode_generation"], f"{path}.episode_generation"),
    }
    if (
        result["world"]["incarnation"]["incarnation_epoch"] == 0
        or result["world"]["world_generation"] == 0
        or result["episode_generation"] == 0
    ):
        raise ValueError(f"{path} generations must be non-zero")
    return result


def _append_number(output: list[bytes], name: str, value: int) -> None:
    output.append(f"{name}={value}\n".encode())


def _append_text(output: list[bytes], name: str, value: str) -> None:
    encoded = value.encode()
    output.append(f"{name}={len(encoded)}:".encode() + encoded + b"\n")


def _append_identity(output: list[bytes], prefix: str, identity: Mapping[str, int]) -> None:
    _append_number(output, f"{prefix}_high", identity["high"])
    _append_number(output, f"{prefix}_low", identity["low"])


def _append_episode(output: list[bytes], prefix: str, episode: Mapping[str, Any]) -> None:
    inc = episode["world"]["incarnation"]
    _append_identity(output, f"{prefix}_host_id", inc["host"]["host_id"])
    _append_identity(output, f"{prefix}_boot_id", inc["host"]["boot_id"])
    _append_number(output, f"{prefix}_incarnation_epoch", inc["incarnation_epoch"])
    _append_number(output, f"{prefix}_world_slot", episode["world"]["world_slot"])
    _append_number(output, f"{prefix}_world_generation", episode["world"]["world_generation"])
    _append_identity(output, f"{prefix}_episode_id", episode["episode_id"])
    _append_number(output, f"{prefix}_episode_generation", episode["episode_generation"])


def _receipt_bytes(receipt: Mapping[str, Any]) -> bytes:
    required = {
        "protocol_generation",
        "kind",
        "idempotency_key",
        "episode_before",
        "episode_after",
        "previous_step_sequence",
        "resulting_step_sequence",
        "resulting_phase",
        "terminal",
        "reset_applied",
        "snapshot_id",
        "snapshot_sha256",
        "barrier_sequence",
        "receipt_sha256",
    }
    if set(receipt) != required:
        raise ValueError("receipt has unknown or missing fields")
    generation = _u64(receipt["protocol_generation"], "protocol_generation")
    if generation != RUNTIME_EPISODE_HANDSHAKE_GENERATION or receipt["kind"] not in _KIND:
        raise ValueError("unsupported episode handshake generation or kind")
    if receipt["resulting_phase"] not in _PHASE:
        raise ValueError("unsupported episode phase")
    if not isinstance(receipt["terminal"], bool) or not isinstance(receipt["reset_applied"], bool):
        raise ValueError("terminal/reset_applied must be booleans")
    output = [b"echelon_forge.runtime_episode_transition_receipt.v1\n"]
    _append_number(output, "protocol_generation", generation)
    _append_number(output, "kind", _KIND[receipt["kind"]])
    _append_identity(output, "idempotency_key", _identity(receipt["idempotency_key"], "idempotency_key"))
    _append_episode(output, "episode_before", _episode(receipt["episode_before"], "episode_before"))
    _append_episode(output, "episode_after", _episode(receipt["episode_after"], "episode_after"))
    _append_number(output, "previous_step_sequence", _u64(receipt["previous_step_sequence"], "previous_step_sequence"))
    _append_number(output, "resulting_step_sequence", _u64(receipt["resulting_step_sequence"], "resulting_step_sequence"))
    _append_number(output, "resulting_phase", _PHASE[receipt["resulting_phase"]])
    _append_number(output, "terminal", int(receipt["terminal"]))
    _append_number(output, "reset_applied", int(receipt["reset_applied"]))
    _append_identity(output, "snapshot_id", _identity(receipt["snapshot_id"], "snapshot_id"))
    _append_text(output, "snapshot_sha256", _sha(receipt["snapshot_sha256"], "snapshot_sha256"))
    _append_number(output, "barrier_sequence", _u64(receipt["barrier_sequence"], "barrier_sequence"))
    return b"".join(output)


def episode_receipt_sha256(receipt: Mapping[str, Any]) -> str:
    """Return the native canonical digest for a complete receipt mapping."""

    return sha256(_receipt_bytes(receipt)).hexdigest()


def _episode_world(episode: Mapping[str, Any]) -> EpochWorldRef:
    world = episode["world"]
    inc = world["incarnation"]
    return EpochWorldRef(
        tuple(inc["host"]["host_id"][key] for key in ("high", "low")),
        tuple(inc["host"]["boot_id"][key] for key in ("high", "low")),
        inc["incarnation_epoch"],
        world["world_slot"],
        world["world_generation"],
    )


class EpochReferenceFence:
    """Shadow adapter that rejects stale or cross-host references and receipts."""

    __slots__ = (
        "_world",
        "_entity_generation",
        "_episode_generation",
        "_phase",
        "_step",
        "_barrier",
        "_applied_receipts",
        "_applied_idempotency_keys",
    )

    def __init__(self, world: EpochWorldRef) -> None:
        if not world.well_formed():
            raise ValueError("candidate world reference is not well formed")
        self._world = world
        self._entity_generation = 1
        self._episode_generation = 1
        self._phase = "running"
        self._step = 0
        self._barrier = 0
        self._applied_receipts: dict[str, bytes] = {}
        self._applied_idempotency_keys: dict[tuple[int, int], bytes] = {}

    @property
    def world(self) -> EpochWorldRef:
        return self._world

    def entity(self, entity_id: int) -> EpochEntityRef:
        if isinstance(entity_id, bool) or not isinstance(entity_id, int):
            raise ValueError("candidate entity id must be an integer")
        ref = EpochEntityRef(self._world, entity_id, self._entity_generation)
        if not ref.well_formed():
            raise ValueError("candidate entity reference is not well formed")
        return ref

    def accepts_world(self, ref: EpochWorldRef) -> bool:
        return isinstance(ref, EpochWorldRef) and ref.well_formed() and ref == self._world

    def accepts_entity(self, ref: EpochEntityRef) -> bool:
        return (
            isinstance(ref, EpochEntityRef)
            and ref.well_formed()
            and ref.world == self._world
            and ref.entity_generation == self._entity_generation
        )

    def apply_episode_receipt(self, receipt: Mapping[str, Any]) -> EpochWorldRef:
        if not isinstance(receipt, Mapping):
            raise ValueError("candidate receipt must be a complete native mapping")
        canonical = _receipt_bytes(receipt)
        digest = receipt["receipt_sha256"]
        if sha256(canonical).hexdigest() != digest:
            raise ValueError("native receipt digest mismatch")
        replay = self._applied_receipts.get(digest)
        if replay is not None:
            if replay != canonical:
                raise ValueError("receipt digest was reused for different bytes")
            return self._world
        idempotency = _identity(receipt["idempotency_key"], "idempotency_key")
        idempotency_key = (idempotency["high"], idempotency["low"])
        key_replay = self._applied_idempotency_keys.get(idempotency_key)
        if key_replay is not None and key_replay != canonical:
            raise ValueError("idempotency key was reused for different receipt bytes")
        if len(self._applied_receipts) >= MAX_RETAINED_RECEIPTS:
            raise ValueError("candidate receipt budget is exhausted")
        before = _episode(receipt["episode_before"], "episode_before")
        after = _episode(receipt["episode_after"], "episode_after")
        before_world = _episode_world(before)
        after_world = _episode_world(after)
        if before_world != self._world:
            raise ValueError("receipt source world is stale or belongs to another host")
        if before["episode_generation"] != self._episode_generation:
            raise ValueError("receipt episode generation is stale or gapped")
        previous = _u64(receipt["previous_step_sequence"], "previous_step_sequence")
        resulting = _u64(receipt["resulting_step_sequence"], "resulting_step_sequence")
        barrier = _u64(receipt["barrier_sequence"], "barrier_sequence")
        kind = receipt["kind"]
        phase = receipt["resulting_phase"]
        if kind == "action":
            if (
                self._phase != "running"
                or after != before
                or previous != self._step
                or resulting != previous + 1
                or receipt["reset_applied"]
                or barrier != self._barrier
                or receipt["terminal"] != (phase == "terminal")
            ):
                raise ValueError("action receipt violates native sequencing")
        elif kind == "reset":
            if (
                self._phase != "terminal"
                or not receipt["reset_applied"]
                or receipt["terminal"]
                or phase != "running"
                or previous != self._step
                or resulting != 0
                or before_world.host_id != after_world.host_id
                or before_world.boot_id != after_world.boot_id
                or before_world.incarnation_epoch != after_world.incarnation_epoch
                or before_world.world_slot != after_world.world_slot
                or after_world.world_generation != before_world.world_generation + 1
                or after["episode_generation"] != before["episode_generation"] + 1
                or after["episode_id"] == before["episode_id"]
                or barrier != self._barrier + 1
            ):
                raise ValueError("reset receipt violates native authority")
        else:
            raise ValueError("unsupported receipt kind")
        self._world = after_world
        self._episode_generation = after["episode_generation"]
        self._phase = phase
        self._step = resulting
        self._barrier = barrier
        if receipt["reset_applied"]:
            self._entity_generation += 1
        self._applied_receipts[digest] = canonical
        self._applied_idempotency_keys[idempotency_key] = canonical
        return self._world

    def acknowledge_receipt(self, receipt: Mapping[str, Any]) -> None:
        """Release a retained receipt after the caller has durably consumed it."""

        if not isinstance(receipt, Mapping):
            raise ValueError("candidate receipt must be a complete native mapping")
        canonical = _receipt_bytes(receipt)
        digest = receipt["receipt_sha256"]
        if sha256(canonical).hexdigest() != digest:
            raise ValueError("native receipt digest mismatch")
        retained = self._applied_receipts.get(digest)
        if retained is None:
            raise ValueError("receipt is not retained by this fence")
        if retained != canonical:
            raise ValueError("receipt digest was reused for different bytes")
        identity = _identity(receipt["idempotency_key"], "idempotency_key")
        key = (identity["high"], identity["low"])
        if self._applied_idempotency_keys.get(key) != canonical:
            raise ValueError("receipt idempotency index is inconsistent")
        del self._applied_receipts[digest]
        del self._applied_idempotency_keys[key]
