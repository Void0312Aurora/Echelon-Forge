"""Runtime-owned projection for binding a resolved input lock to a RunReceipt.

The experiment layer owns construction and comparison of a resolved input lock.
This module only reads the immutable lock projection and checks that an already
validated runtime receipt names its digest.  It deliberately does not create,
validate, or replace the native receipt authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "echelon_forge.resolved_experiment.v1"
_LOCK_STATES = frozenset({"static_candidate", "completed", "failed", "unknown"})
_RECEIPT_ENVELOPE_FIELDS = frozenset(
    {
        "canonicalization",
        "domain",
        "envelope_version",
        "media_type",
        "payload",
        "payload_sha256",
        "signatures",
    }
)


class InputLockBindingError(ValueError):
    """Raised when a runtime input-lock projection cannot be bound safely."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise TypeError("input-lock keys must be non-empty strings")
        return {key: _canonical(child) for key, child in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"input-lock value is not JSON-compatible: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a lock projection using its stable UTF-8 JSON rules."""

    return json.dumps(
        _canonical(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def input_lock_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ResolvedInputLockBinding:
    document: Mapping[str, Any]
    digest: str


def load_resolved_input_lock_path(path: str | Path) -> ResolvedInputLockBinding:
    """Load one canonical lock projection without granting it runtime authority."""

    source = Path(path)
    try:
        raw = source.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputLockBindingError(f"input_lock.document_unreadable:{source}") from exc
    if not isinstance(document, Mapping):
        raise InputLockBindingError("input_lock.document_invalid")
    if canonical_json_bytes(document) != raw:
        raise InputLockBindingError("input_lock.document_not_canonical")
    required = {
        "schema_version",
        "status",
        "experiment_ref",
        "intent",
        "input_lock",
        "native_runtime",
        "provenance",
    }
    if set(document) != required or document["schema_version"] != SCHEMA_VERSION:
        raise InputLockBindingError("input_lock.document_schema_invalid")
    if document["status"] not in _LOCK_STATES:
        raise InputLockBindingError("input_lock.document_status_invalid")
    if not isinstance(document["input_lock"], Mapping):
        raise InputLockBindingError("input_lock.document_payload_invalid")
    return ResolvedInputLockBinding(document, input_lock_digest(document["input_lock"]))


def assert_run_receipt_input_lock_binding(
    candidate: ResolvedInputLockBinding, receipt: Mapping[str, Any]
) -> None:
    """Require an already validated receipt to name the candidate digest."""

    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_ENVELOPE_FIELDS:
        raise InputLockBindingError("input_lock.receipt_invalid")
    payload = receipt.get("payload")
    if not isinstance(payload, Mapping):
        raise InputLockBindingError("input_lock.receipt_invalid")
    inputs = payload.get("inputs")
    artifacts = inputs.get("artifacts") if isinstance(inputs, Mapping) else None
    if not isinstance(artifacts, Mapping):
        raise InputLockBindingError("input_lock.receipt_invalid")
    if artifacts.get("resolved_input_lock") != candidate.digest:
        raise InputLockBindingError("input_lock.receipt_input_binding_mismatch")


def assert_run_receipt_input_lock_path(
    candidate: ResolvedInputLockBinding, receipt_path: str | Path
) -> None:
    """Validate canonical receipt bytes against an already loaded lock."""

    source = Path(receipt_path)
    try:
        raw = source.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputLockBindingError(f"input_lock.receipt_unreadable:{source}") from exc
    if not isinstance(document, Mapping) or canonical_json_bytes(document) != raw:
        raise InputLockBindingError("input_lock.receipt_not_canonical")
    assert_run_receipt_input_lock_binding(candidate, document)


__all__ = [
    "InputLockBindingError",
    "ResolvedInputLockBinding",
    "assert_run_receipt_input_lock_binding",
    "assert_run_receipt_input_lock_path",
    "canonical_json_bytes",
    "input_lock_digest",
    "load_resolved_input_lock_path",
]
