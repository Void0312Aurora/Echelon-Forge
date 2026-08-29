"""P4-B shadow-only mirror for native episode receipts (not packaged)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

RUNTIME_EPISODE_HANDSHAKE_GENERATION = 1
MAX_RETAINED_RECEIPTS = 4096
_KIND = {"action": 0, "reset": 1}
_PHASE = {"running": 0, "terminal": 1, "replacement-barrier": 2, "transfer-committed": 3, "fail-stopped": 4}

class EpisodeMirrorError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail); self.code, self.detail = code, detail

@dataclass(frozen=True)
class EpisodeMirrorState:
    episode: Mapping[str, Any]; phase: str; step_sequence: int; barrier_sequence: int
    snapshot_id: Mapping[str, int]; snapshot_sha256: str

@dataclass(frozen=True)
class EpisodeMirrorApplyResult:
    state: EpisodeMirrorState; replayed: bool

def _u64(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**64 - 1:
        raise EpisodeMirrorError("receipt.invalid", f"{path} must be an unsigned 64-bit integer")
    return value

def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise EpisodeMirrorError("receipt.invalid", f"{path} must be lowercase SHA-256")
    return value

def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping): raise EpisodeMirrorError("receipt.invalid", f"{path} must be an object")
    return value

def _identity(value: Any, path: str) -> dict[str, int]:
    value = _mapping(value, path)
    if set(value) != {"high", "low"}: raise EpisodeMirrorError("receipt.invalid", f"{path} has unknown or missing fields")
    result = {"high": _u64(value["high"], f"{path}.high"), "low": _u64(value["low"], f"{path}.low")}
    if result == {"high": 0, "low": 0}: raise EpisodeMirrorError("receipt.invalid", f"{path} must be non-zero")
    return result

def _episode(value: Any, path: str) -> dict[str, Any]:
    value = _mapping(value, path)
    if set(value) != {"world", "episode_id", "episode_generation"}: raise EpisodeMirrorError("receipt.invalid", f"{path} has unknown or missing fields")
    world = _mapping(value["world"], f"{path}.world"); inc = _mapping(world["incarnation"], f"{path}.world.incarnation"); host = _mapping(inc["host"], f"{path}.world.incarnation.host")
    if set(world) != {"incarnation", "world_slot", "world_generation"} or set(inc) != {"host", "incarnation_epoch"} or set(host) != {"host_id", "boot_id"}:
        raise EpisodeMirrorError("receipt.invalid", f"{path}.world has unknown or missing fields")
    result = {"world": {"incarnation": {"host": {"host_id": _identity(host["host_id"], path), "boot_id": _identity(host["boot_id"], path)}, "incarnation_epoch": _u64(inc["incarnation_epoch"], path)}, "world_slot": _u64(world["world_slot"], path), "world_generation": _u64(world["world_generation"], path)}, "episode_id": _identity(value["episode_id"], path), "episode_generation": _u64(value["episode_generation"], path)}
    if result["world"]["incarnation"]["incarnation_epoch"] == 0 or result["world"]["world_generation"] == 0 or result["episode_generation"] == 0: raise EpisodeMirrorError("receipt.invalid", f"{path} generations must be non-zero")
    return result

def _append_number(output: list[bytes], name: str, value: int) -> None: output.append(f"{name}={value}\n".encode())
def _append_text(output: list[bytes], name: str, value: str) -> None:
    encoded = value.encode(); output.append(f"{name}={len(encoded)}:".encode() + encoded + b"\n")
def _append_identity(output: list[bytes], prefix: str, identity: Mapping[str, int]) -> None:
    _append_number(output, f"{prefix}_high", identity["high"]); _append_number(output, f"{prefix}_low", identity["low"])
def _append_episode(output: list[bytes], prefix: str, episode: Mapping[str, Any]) -> None:
    inc = episode["world"]["incarnation"]; _append_identity(output, f"{prefix}_host_id", inc["host"]["host_id"]); _append_identity(output, f"{prefix}_boot_id", inc["host"]["boot_id"]); _append_number(output, f"{prefix}_incarnation_epoch", inc["incarnation_epoch"]); _append_number(output, f"{prefix}_world_slot", episode["world"]["world_slot"]); _append_number(output, f"{prefix}_world_generation", episode["world"]["world_generation"]); _append_identity(output, f"{prefix}_episode_id", episode["episode_id"]); _append_number(output, f"{prefix}_episode_generation", episode["episode_generation"])

def canonical_episode_transition_intent_bytes(intent: Mapping[str, Any]) -> bytes:
    required = {"protocol_generation", "kind", "expected_episode", "expected_step_sequence", "idempotency_key", "payload_sha256", "production_authorized"}
    if set(intent) != required: raise EpisodeMirrorError("intent.invalid", "intent has unknown or missing fields")
    generation = _u64(intent["protocol_generation"], "protocol_generation")
    if generation != 1 or intent["kind"] not in _KIND: raise EpisodeMirrorError("intent.version", "unsupported episode handshake generation")
    if not isinstance(intent["production_authorized"], bool): raise EpisodeMirrorError("intent.invalid", "production_authorized must be a boolean")
    output = [b"echelon_forge.runtime_episode_transition_intent.v1\n"]; _append_number(output, "protocol_generation", generation); _append_number(output, "kind", _KIND[intent["kind"]]); _append_episode(output, "expected", _episode(intent["expected_episode"], "expected_episode")); _append_number(output, "expected_step_sequence", _u64(intent["expected_step_sequence"], "expected_step_sequence")); _append_identity(output, "idempotency_key", _identity(intent["idempotency_key"], "idempotency_key")); _append_text(output, "payload_sha256", _sha(intent["payload_sha256"], "payload_sha256")); _append_number(output, "production_authorized", int(intent["production_authorized"])); return b"".join(output)

def episode_transition_intent_sha256(intent: Mapping[str, Any]) -> str: return sha256(canonical_episode_transition_intent_bytes(intent)).hexdigest()

def canonical_episode_transition_receipt_bytes(receipt: Mapping[str, Any]) -> bytes:
    required = {"protocol_generation", "kind", "idempotency_key", "episode_before", "episode_after", "previous_step_sequence", "resulting_step_sequence", "resulting_phase", "terminal", "reset_applied", "snapshot_id", "snapshot_sha256", "barrier_sequence", "receipt_sha256"}
    if set(receipt) != required: raise EpisodeMirrorError("receipt.invalid", "receipt has unknown or missing fields")
    generation = _u64(receipt["protocol_generation"], "protocol_generation")
    if generation != 1 or receipt["kind"] not in _KIND or receipt["resulting_phase"] not in _PHASE: raise EpisodeMirrorError("receipt.version", "unsupported episode handshake generation")
    if not isinstance(receipt["terminal"], bool) or not isinstance(receipt["reset_applied"], bool): raise EpisodeMirrorError("receipt.invalid", "terminal/reset_applied must be booleans")
    output = [b"echelon_forge.runtime_episode_transition_receipt.v1\n"]; _append_number(output, "protocol_generation", generation); _append_number(output, "kind", _KIND[receipt["kind"]]); _append_identity(output, "idempotency_key", _identity(receipt["idempotency_key"], "idempotency_key")); _append_episode(output, "episode_before", _episode(receipt["episode_before"], "episode_before")); _append_episode(output, "episode_after", _episode(receipt["episode_after"], "episode_after")); _append_number(output, "previous_step_sequence", _u64(receipt["previous_step_sequence"], "previous_step_sequence")); _append_number(output, "resulting_step_sequence", _u64(receipt["resulting_step_sequence"], "resulting_step_sequence")); _append_number(output, "resulting_phase", _PHASE[receipt["resulting_phase"]]); _append_number(output, "terminal", int(receipt["terminal"])); _append_number(output, "reset_applied", int(receipt["reset_applied"])); _append_identity(output, "snapshot_id", _identity(receipt["snapshot_id"], "snapshot_id")); _append_text(output, "snapshot_sha256", _sha(receipt["snapshot_sha256"], "snapshot_sha256")); _append_number(output, "barrier_sequence", _u64(receipt["barrier_sequence"], "barrier_sequence")); return b"".join(output)

def episode_transition_receipt_sha256(receipt: Mapping[str, Any]) -> str: return sha256(canonical_episode_transition_receipt_bytes(receipt)).hexdigest()
def _same_world_identity(lhs: Mapping[str, Any], rhs: Mapping[str, Any]) -> bool: return lhs["world"]["incarnation"] == rhs["world"]["incarnation"] and lhs["world"]["world_slot"] == rhs["world"]["world_slot"]

class NativeEpisodeMirror:
    def __init__(self, state: EpisodeMirrorState) -> None:
        self._state = EpisodeMirrorState(_episode(state.episode, "initial.episode"), state.phase, _u64(state.step_sequence, "initial.step_sequence"), _u64(state.barrier_sequence, "initial.barrier_sequence"), _identity(state.snapshot_id, "initial.snapshot_id"), _sha(state.snapshot_sha256, "initial.snapshot_sha256")); self._applied: dict[str, bytes] = {}
    @property
    def state(self) -> EpisodeMirrorState: return self._state
    def acknowledge_receipt(self, receipt: Mapping[str, Any]) -> None:
        canonical = canonical_episode_transition_receipt_bytes(receipt)
        digest = _sha(receipt["receipt_sha256"], "receipt_sha256")
        if sha256(canonical).hexdigest() != digest:
            raise EpisodeMirrorError("receipt.digest", "native receipt digest mismatch")
        if digest not in self._applied:
            raise EpisodeMirrorError("receipt.ack_invalid", "receipt is not retained by this mirror")
        del self._applied[digest]
    def apply_receipt(self, receipt: Mapping[str, Any]) -> EpisodeMirrorApplyResult:
        canonical = canonical_episode_transition_receipt_bytes(receipt); digest = _sha(receipt["receipt_sha256"], "receipt_sha256")
        if sha256(canonical).hexdigest() != digest: raise EpisodeMirrorError("receipt.digest", "native receipt digest mismatch")
        if digest in self._applied:
            if self._applied[digest] != canonical: raise EpisodeMirrorError("receipt.conflict", "receipt digest was reused for other bytes")
            return EpisodeMirrorApplyResult(self._state, True)
        if len(self._applied) >= MAX_RETAINED_RECEIPTS: raise EpisodeMirrorError("mirror.receipt_budget", "mirror receipt budget is exhausted")
        before, after = _episode(receipt["episode_before"], "episode_before"), _episode(receipt["episode_after"], "episode_after"); previous, resulting = _u64(receipt["previous_step_sequence"], "previous_step_sequence"), _u64(receipt["resulting_step_sequence"], "resulting_step_sequence"); barrier, kind, phase = _u64(receipt["barrier_sequence"], "barrier_sequence"), receipt["kind"], receipt["resulting_phase"]
        if before != self._state.episode or previous != self._state.step_sequence: raise EpisodeMirrorError("mirror.resync_required", "native receipt has an identity/sequence gap; local guessing is forbidden")
        if phase in {"replacement-barrier", "transfer-committed", "fail-stopped"}: raise EpisodeMirrorError("mirror.resync_required", "control-only phase requires a native snapshot")
        if kind == "action":
            if self._state.phase != "running" or after != before or resulting != previous + 1 or receipt["reset_applied"] or barrier != self._state.barrier_sequence or receipt["terminal"] != (phase == "terminal"): raise EpisodeMirrorError("receipt.semantic", "action receipt violates native sequencing")
        elif kind == "reset":
            if self._state.phase != "terminal" or not receipt["reset_applied"] or receipt["terminal"] or phase != "running" or resulting != 0 or not _same_world_identity(before, after) or after["world"]["world_generation"] != before["world"]["world_generation"] + 1 or after["episode_generation"] != before["episode_generation"] + 1 or after["episode_id"] == before["episode_id"] or barrier != self._state.barrier_sequence + 1: raise EpisodeMirrorError("receipt.semantic", "reset receipt violates native authority")
        else: raise EpisodeMirrorError("receipt.invalid", "unsupported receipt kind")
        self._state = EpisodeMirrorState(after, phase, resulting, barrier, _identity(receipt["snapshot_id"], "snapshot_id"), _sha(receipt["snapshot_sha256"], "snapshot_sha256")); self._applied[digest] = canonical; return EpisodeMirrorApplyResult(self._state, False)
