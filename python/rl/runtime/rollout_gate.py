"""Fail-closed local production rollout admission for the maintained runtime.

This module is deliberately smaller than the ArtifactLedger implementation:
it owns only the local, in-process RolloutDecision slot used at the P5-D
caller boundary.  It never manufactures plan/package digests and it does not
provide a remote or multi-process election mechanism.  The slot is durable,
single-writer, and append-by-replacement so a process can refuse to construct
the maintained runtime unless an explicitly admitted decision is present.
"""

from __future__ import annotations

import contextlib
import hmac
import hashlib
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA_VERSION = "echelon_forge.production_rollout_slot.v1"
ENVELOPE_VERSION = "echelon_forge.authority_envelope.v1"
CANONICALIZATION = "echelon_forge.canonical_json.v2"
ROLLOUT_DOMAIN = "release.rollout-decision"
ROLLOUT_MEDIA_TYPE = "application/vnd.echelon-forge.rollout-decision.v1+json"
STATES = frozenset(
    {
        "prepared",
        "shadow",
        "canary-ready",
        "production-canary",
        "adoption-expanding",
        "rollback-window",
        "stable",
        "backed-out",
    }
)
PRODUCTION_STATES = frozenset(
    {"production-canary", "adoption-expanding", "rollback-window", "stable"}
)
TRANSITIONS: dict[str, frozenset[str]] = {
    "prepared": frozenset({"shadow", "backed-out"}),
    "shadow": frozenset({"canary-ready", "backed-out"}),
    "canary-ready": frozenset({"production-canary", "backed-out"}),
    "production-canary": frozenset({"adoption-expanding", "backed-out"}),
    "adoption-expanding": frozenset(
        {"adoption-expanding", "rollback-window", "backed-out"}
    ),
    "rollback-window": frozenset({"stable", "backed-out"}),
    "stable": frozenset({"prepared"}),
    "backed-out": frozenset({"prepared"}),
}
PAYLOAD_FIELDS = frozenset(
    {
        "authority_kind",
        "schema_version",
        "contract_version",
        "writer_role",
        "decision_id",
        "release_id",
        "manifest_sha256",
        "plan_sha256",
        "plan_reader_generation_min",
        "plan_reader_generation_max",
        "predecessor_decision_id",
        "state",
        "writer_generation",
        "decision_sequence",
        "cohort",
        "rollback_deadline",
        "checkpoint_id",
        "irreversible_write_boundary",
    }
)
SLOT_FIELDS = frozenset(
    {
        "schema_version",
        "decision",
        "decision_sha256",
        "admissions_open",
        "writer_advancement_frozen",
        "kill_switch_reasons",
    }
)


class RolloutAdmissionError(RuntimeError):
    """Raised when a rollout slot is missing, corrupt, or not admissible."""


def _canonical(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not (value == value and abs(value) != float("inf")):
            raise RolloutAdmissionError("non-finite rollout value")
        return value
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise RolloutAdmissionError("rollout value contains a lone UTF-16 surrogate")
        return value
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, Mapping):
        keys = [key for key in value if isinstance(key, str)]
        if len(keys) != len(value) or len(set(keys)) != len(keys):
            raise RolloutAdmissionError("rollout object keys are invalid")
        return {key: _canonical(value[key]) for key in sorted(keys, key=lambda item: item.encode("utf-16-be"))}
    raise RolloutAdmissionError(f"unsupported rollout value: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Encode the same restricted UTF-8/canonical shape used by authority records."""

    return json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _authority_digest(payload: Mapping[str, Any]) -> str:
    return sha256_bytes(
        b"echelon-forge-authority-v1\x00"
        + ROLLOUT_DOMAIN.encode("utf-8")
        + b"\x00"
        + ROLLOUT_MEDIA_TYPE.encode("utf-8")
        + b"\x00"
        + canonical_json_bytes(payload)
    )


def _require_digest(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise RolloutAdmissionError(f"{field} must be lowercase SHA-256 hex")


def _require_identifier(value: Any, field: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not value and not allow_empty) or len(value) > 128:
        raise RolloutAdmissionError(f"{field} must be a bounded identifier")
    if value and not value[0].isalpha():
        raise RolloutAdmissionError(f"{field} must start with a letter")
    if value and any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-" for char in value[1:]):
        raise RolloutAdmissionError(f"{field} contains an invalid identifier character")


def _require_nonempty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise RolloutAdmissionError(f"{field} must be a non-empty string")


def _signature_material(payload_sha256: str, signer_context: str) -> bytes:
    return f"echelon-forge-local-rollout-v1\0{payload_sha256}\0{signer_context}".encode("utf-8")


def _durable_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}-{threading.get_ident()}")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_rollout_decision_envelope(
    payload: Mapping[str, Any],
    *,
    key_id: str,
    signing_key: bytes,
) -> dict[str, Any]:
    """Build one authority envelope; callers still must persist it through the store."""

    normalized = dict(payload)
    validate_rollout_payload(normalized)
    if not isinstance(key_id, str) or not key_id:
        raise RolloutAdmissionError("key_id is required")
    if not isinstance(signing_key, bytes) or len(signing_key) < 32:
        raise RolloutAdmissionError("local rollout signing key must contain at least 32 bytes")
    payload_sha256 = _authority_digest(normalized)
    signer_context = "in-process-single-writer"
    return {
        "canonicalization": CANONICALIZATION,
        "domain": ROLLOUT_DOMAIN,
        "envelope_version": ENVELOPE_VERSION,
        "media_type": ROLLOUT_MEDIA_TYPE,
        "payload": normalized,
        "payload_sha256": payload_sha256,
        "signatures": [
            {
                "algorithm": "hmac-sha256-local.v1",
                "key_id": key_id,
                "signature": hmac.new(
                    signing_key,
                    _signature_material(payload_sha256, signer_context),
                    hashlib.sha256,
                ).hexdigest(),
                "signer_context": signer_context,
            }
        ],
    }


def validate_rollout_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) != PAYLOAD_FIELDS:
        raise RolloutAdmissionError("rollout payload fields are not exact")
    normalized = dict(payload)
    if normalized["authority_kind"] != "rollout_decision" or normalized["schema_version"] != "echelon_forge.rollout_decision.v1" or normalized["contract_version"] != "echelon_forge.rollout_decision_contract.v1" or normalized["writer_role"] != "release_controller":
        raise RolloutAdmissionError("rollout payload authority identity is invalid")
    for field in ("decision_id", "release_id"):
        _require_identifier(normalized[field], field)
    for field in ("cohort", "rollback_deadline", "irreversible_write_boundary"):
        _require_nonempty_string(normalized[field], field)
    _require_identifier(normalized["predecessor_decision_id"], "predecessor_decision_id", allow_empty=True)
    _require_identifier(normalized["checkpoint_id"], "checkpoint_id", allow_empty=True)
    for field in ("manifest_sha256", "plan_sha256"):
        _require_digest(normalized[field], field)
    for field in ("plan_reader_generation_min", "plan_reader_generation_max", "writer_generation", "decision_sequence"):
        value = normalized[field]
        if not isinstance(value, str) or not value.isdecimal() or (len(value) > 1 and value.startswith("0")):
            raise RolloutAdmissionError(f"{field} must be a canonical decimal string")
    if int(normalized["plan_reader_generation_min"]) > int(normalized["plan_reader_generation_max"]):
        raise RolloutAdmissionError("rollout plan reader window is inverted")
    if normalized["state"] not in STATES:
        raise RolloutAdmissionError("rollout state is not admitted")
    return normalized


def validate_rollout_envelope(
    envelope: Mapping[str, Any],
    *,
    verification_key: bytes,
    expected_key_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(envelope, Mapping) or set(envelope) != {
        "canonicalization", "domain", "envelope_version", "media_type", "payload", "payload_sha256", "signatures"
    }:
        raise RolloutAdmissionError("rollout envelope fields are not exact")
    if envelope["canonicalization"] != CANONICALIZATION or envelope["domain"] != ROLLOUT_DOMAIN or envelope["envelope_version"] != ENVELOPE_VERSION or envelope["media_type"] != ROLLOUT_MEDIA_TYPE:
        raise RolloutAdmissionError("rollout envelope identity is invalid")
    payload = validate_rollout_payload(envelope["payload"])
    _require_digest(envelope["payload_sha256"], "payload_sha256")
    if envelope["payload_sha256"] != _authority_digest(payload):
        raise RolloutAdmissionError("rollout payload digest mismatch")
    signatures = envelope["signatures"]
    if not isinstance(verification_key, bytes) or len(verification_key) < 32:
        raise RolloutAdmissionError("local rollout verification key must contain at least 32 bytes")
    if not isinstance(signatures, list) or len(signatures) != 1:
        raise RolloutAdmissionError("rollout envelope requires an attestation")
    for signature in signatures:
        if not isinstance(signature, Mapping) or set(signature) != {"algorithm", "key_id", "signature", "signer_context"}:
            raise RolloutAdmissionError("rollout attestation fields are invalid")
        if any(not isinstance(signature[field], str) or not signature[field] for field in signature):
            raise RolloutAdmissionError("rollout attestation fields are empty")
        if signature["algorithm"] != "hmac-sha256-local.v1" or signature["signer_context"] != "in-process-single-writer":
            raise RolloutAdmissionError("rollout attestation algorithm/context is not admitted")
        if expected_key_id is not None and signature["key_id"] != expected_key_id:
            raise RolloutAdmissionError("rollout attestation key identity differs")
        _require_digest(signature["signature"], "signature")
        expected = hmac.new(
            verification_key,
            _signature_material(envelope["payload_sha256"], signature["signer_context"]),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature["signature"], expected):
            raise RolloutAdmissionError("rollout attestation verification failed")
    return dict(envelope)


@contextlib.contextmanager
def _exclusive_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        handle.seek(0)
        if not handle.read(1):
            handle.seek(0)
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True, slots=True)
class RolloutAdmission:
    path: Path
    envelope: dict[str, Any]
    decision_sha256: str
    admissions_open: bool
    writer_advancement_frozen: bool
    kill_switch_reasons: tuple[str, ...]

    @property
    def state(self) -> str:
        return str(self.envelope["payload"]["state"])

    @property
    def production_authorized(self) -> bool:
        return self.admissions_open and not self.writer_advancement_frozen and self.state in PRODUCTION_STATES

    def assert_production_authorized(self) -> None:
        if not self.production_authorized:
            raise RolloutAdmissionError(
                f"rollout decision is not production-authorized: state={self.state!r}, "
                f"admissions_open={self.admissions_open}, writer_advancement_frozen={self.writer_advancement_frozen}"
            )

    @classmethod
    def from_slot(
        cls,
        path: str | os.PathLike[str],
        *,
        expected_release_id: str | None = None,
        expected_manifest_sha256: str | None = None,
        expected_plan_sha256: str | None = None,
        topology: str = "in-process",
        verification_key: bytes,
        expected_key_id: str | None = None,
    ) -> "RolloutAdmission":
        slot_path = Path(path)
        try:
            raw_bytes = slot_path.read_bytes()
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RolloutAdmissionError(f"cannot read rollout slot: {slot_path}") from error
        if not isinstance(raw, Mapping):
            raise RolloutAdmissionError("rollout slot schema is invalid")
        return cls.from_document(
            raw,
            source_path=slot_path,
            expected_release_id=expected_release_id,
            expected_manifest_sha256=expected_manifest_sha256,
            expected_plan_sha256=expected_plan_sha256,
            topology=topology,
            verification_key=verification_key,
            expected_key_id=expected_key_id,
            require_canonical_bytes=raw_bytes,
        )

    @classmethod
    def from_document(
        cls,
        raw: Mapping[str, Any],
        *,
        source_path: str | os.PathLike[str] = "<rollout-reader>",
        expected_release_id: str | None = None,
        expected_manifest_sha256: str | None = None,
        expected_plan_sha256: str | None = None,
        topology: str = "in-process",
        verification_key: bytes,
        expected_key_id: str | None = None,
        require_canonical_bytes: bytes | None = None,
    ) -> "RolloutAdmission":
        slot_path = Path(source_path)
        if not isinstance(raw, Mapping):
            raise RolloutAdmissionError("rollout slot schema is invalid")
        if set(raw) != SLOT_FIELDS or raw.get("schema_version") != SCHEMA_VERSION:
            raise RolloutAdmissionError("rollout slot schema is invalid")
        if require_canonical_bytes is not None and canonical_json_bytes(raw) != require_canonical_bytes:
            raise RolloutAdmissionError("rollout slot is not canonical JSON")
        envelope = validate_rollout_envelope(
            raw["decision"],
            verification_key=verification_key,
            expected_key_id=expected_key_id,
        )
        decision_sha256 = sha256_bytes(canonical_json_bytes(envelope))
        if raw["decision_sha256"] != decision_sha256:
            raise RolloutAdmissionError("rollout slot decision digest mismatch")
        if not isinstance(raw["admissions_open"], bool) or not isinstance(raw["writer_advancement_frozen"], bool):
            raise RolloutAdmissionError("rollout slot admission flags are invalid")
        if (raw["admissions_open"], raw["writer_advancement_frozen"]) not in {
            (True, False),
            (False, True),
        }:
            raise RolloutAdmissionError("rollout slot admission flags are invalid")
        reasons = raw["kill_switch_reasons"]
        if not isinstance(reasons, list) or any(not isinstance(reason, str) or not reason for reason in reasons) or reasons != sorted(set(reasons)):
            raise RolloutAdmissionError("rollout kill-switch reasons are invalid")
        if bool(reasons) != (not raw["admissions_open"] and raw["writer_advancement_frozen"]):
            raise RolloutAdmissionError("rollout kill-switch reasons differ from admission state")
        payload = envelope["payload"]
        if expected_release_id is not None and payload["release_id"] != expected_release_id:
            raise RolloutAdmissionError("rollout release identity differs from caller")
        if expected_manifest_sha256 is not None and payload["manifest_sha256"] != expected_manifest_sha256:
            raise RolloutAdmissionError("rollout manifest differs from caller")
        if expected_plan_sha256 is not None and payload["plan_sha256"] != expected_plan_sha256:
            raise RolloutAdmissionError("rollout plan differs from caller")
        if topology != "in-process":
            raise RolloutAdmissionError("only the admitted local in-process topology is supported")
        return cls(
            slot_path,
            envelope,
            decision_sha256,
            bool(raw["admissions_open"]),
            bool(raw["writer_advancement_frozen"]),
            tuple(reasons),
        )


class FileRolloutDecisionStore:
    """Durable single-writer RolloutDecision slot for the local support row."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        writer_id: str,
        signing_key: bytes,
        key_id: str,
    ) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_name(self.path.name + ".lock")
        if not writer_id:
            raise RolloutAdmissionError("rollout writer identity is required")
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise RolloutAdmissionError("rollout signing key must contain at least 32 bytes")
        if not key_id:
            raise RolloutAdmissionError("rollout signing key identity is required")
        self.writer_id = writer_id
        self.signing_key = signing_key
        self.key_id = key_id
        self._mutex = threading.RLock()

    def _read_unlocked(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            raw_bytes = self.path.read_bytes()
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RolloutAdmissionError("rollout slot is unreadable") from error
        RolloutAdmission.from_document(
            raw,
            source_path=self.path,
            verification_key=self.signing_key,
            expected_key_id=self.key_id,
            require_canonical_bytes=raw_bytes,
        )
        return dict(raw)

    def read(self, **kwargs: Any) -> RolloutAdmission | None:
        with self._mutex, _exclusive_lock(self.lock_path):
            if not self.path.exists():
                return None
            return RolloutAdmission.from_slot(
                self.path,
                verification_key=self.signing_key,
                expected_key_id=self.key_id,
                **kwargs,
            )

    def commit(
        self,
        envelope: Mapping[str, Any],
        *,
        admissions_open: bool = True,
        writer_advancement_frozen: bool = False,
        expected_decision_sha256: str | None = None,
    ) -> RolloutAdmission:
        normalized = validate_rollout_envelope(
            envelope,
            verification_key=self.signing_key,
            expected_key_id=self.key_id,
        )
        payload = normalized["payload"]
        if (admissions_open, writer_advancement_frozen) not in {(True, False), (False, True)}:
            raise RolloutAdmissionError("admission flags must be open/unfrozen or closed/frozen")
        with self._mutex, _exclusive_lock(self.lock_path):
            previous = self._read_unlocked()
            previous_envelope = None if previous is None else previous["decision"]
            previous_sha = None if previous is None else previous["decision_sha256"]
            if expected_decision_sha256 is not None and previous_sha != expected_decision_sha256:
                raise RolloutAdmissionError("rollout slot compare-and-swap predecessor mismatch")
            if previous_envelope is None:
                if payload["state"] != "prepared" or payload["decision_sequence"] != "0" or payload["predecessor_decision_id"]:
                    raise RolloutAdmissionError("rollout slot must begin with prepared sequence zero")
            else:
                prior_payload = previous_envelope["payload"]
                if payload["predecessor_decision_id"] != prior_payload["decision_id"]:
                    raise RolloutAdmissionError("rollout predecessor identity mismatch")
                if int(payload["decision_sequence"]) != int(prior_payload["decision_sequence"]) + 1:
                    raise RolloutAdmissionError("rollout decision sequence is not monotonic")
                if payload["state"] not in TRANSITIONS[prior_payload["state"]]:
                    raise RolloutAdmissionError("rollout state transition is not admitted")
                if (
                    previous["admissions_open"] is False
                    and not (
                        payload["state"] == "backed-out"
                        or (
                            prior_payload["state"] == "backed-out"
                            and payload["state"] == "prepared"
                        )
                    )
                ):
                    raise RolloutAdmissionError("closed rollout admission requires typed backout repair")
                if payload["manifest_sha256"] != prior_payload["manifest_sha256"]:
                    raise RolloutAdmissionError("rollout manifest binding changed")
                writer_changed = payload["writer_generation"] != prior_payload["writer_generation"]
                plan_changed = payload["plan_sha256"] != prior_payload["plan_sha256"]
                if writer_changed != plan_changed:
                    raise RolloutAdmissionError("rollout writer and plan changed independently")
                if plan_changed and payload["state"] not in {"adoption-expanding", "backed-out"}:
                    raise RolloutAdmissionError("rollout plan changed outside advancement/backout")
                if writer_changed:
                    expected = int(prior_payload["writer_generation"]) - 1 if payload["state"] == "backed-out" else int(prior_payload["writer_generation"]) + 1
                    if int(payload["writer_generation"]) != expected:
                        raise RolloutAdmissionError("rollout writer generation is not adjacent")
            if payload["state"] == "backed-out":
                if payload["irreversible_write_boundary"] != "none":
                    raise RolloutAdmissionError("backout is forbidden after the irreversible write boundary")
                admissions_open = False
                writer_advancement_frozen = True
            record = {
                "schema_version": SCHEMA_VERSION,
                "decision": normalized,
                "decision_sha256": sha256_bytes(canonical_json_bytes(normalized)),
                "admissions_open": admissions_open,
                "writer_advancement_frozen": writer_advancement_frozen,
                "kill_switch_reasons": (
                    [] if admissions_open else ["typed-backout"]
                ),
            }
            _durable_replace(self.path, canonical_json_bytes(record))
        loaded = RolloutAdmission.from_slot(
            self.path,
            verification_key=self.signing_key,
            expected_key_id=self.key_id,
        )
        return loaded

    def trip_kill_switch(self, reasons: list[str]) -> RolloutAdmission:
        if not reasons or any(not isinstance(reason, str) or not reason for reason in reasons):
            raise RolloutAdmissionError("kill switch requires typed reasons")
        with self._mutex, _exclusive_lock(self.lock_path):
            current = self._read_unlocked()
            if current is None:
                raise RolloutAdmissionError("cannot kill an absent rollout slot")
            current["admissions_open"] = False
            current["writer_advancement_frozen"] = True
            current["kill_switch_reasons"] = sorted(set(reasons))
            _durable_replace(self.path, canonical_json_bytes(current))
        return RolloutAdmission.from_slot(
            self.path,
            verification_key=self.signing_key,
            expected_key_id=self.key_id,
        )


__all__ = [
    "FileRolloutDecisionStore",
    "RolloutAdmission",
    "RolloutAdmissionError",
    "build_rollout_decision_envelope",
    "canonical_json_bytes",
    "validate_rollout_envelope",
]
