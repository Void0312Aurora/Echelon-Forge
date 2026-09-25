"""Build and validate provider-neutral evidence manifests for P7-B."""

from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Any, Mapping


SCHEMA_VERSION = "echelon_forge.evidence_manifest.v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_FIELDS = frozenset({
    "artifact_id",
    "claim",
    "sha256",
    "producer",
    "created_at",
    "retention_until",
    "restore_owner",
    "access_policy",
    "backup_policy",
    "provider",
    "provider_migration_policy",
})


class EvidenceManifestError(ValueError):
    """Raised when a retained evidence manifest is incomplete or invalid."""


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceManifestError(f"{field} must be a non-empty string")
    return value.strip()


def _parse_timestamp(value: Any, field: str) -> tuple[str, datetime]:
    text = _require_text(value, field)
    try:
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise EvidenceManifestError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceManifestError(f"{field} must include a timezone offset")
    return text, parsed


def _require_timestamp(value: Any, field: str) -> str:
    return _parse_timestamp(value, field)[0]


def _require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise EvidenceManifestError(f"{field} must be a lowercase SHA-256 digest")
    return value


def build_evidence_manifest(
    *,
    artifact_id: str,
    claim: str,
    payload: bytes,
    producer: str,
    created_at: str,
    retention_until: str,
    restore_owner: str,
    access_policy: str,
    backup_policy: str,
    provider: str,
    provider_migration_policy: str,
) -> dict[str, Any]:
    """Return a manifest whose digest is bound to the retained payload bytes."""

    if not isinstance(payload, bytes):
        raise EvidenceManifestError("payload must be bytes")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _require_text(artifact_id, "artifact_id"),
        "claim": _require_text(claim, "claim"),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "producer": _require_text(producer, "producer"),
        "created_at": _require_timestamp(created_at, "created_at"),
        "retention_until": _require_timestamp(retention_until, "retention_until"),
        "restore_owner": _require_text(restore_owner, "restore_owner"),
        "access_policy": _require_text(access_policy, "access_policy"),
        "backup_policy": _require_text(backup_policy, "backup_policy"),
        "provider": _require_text(provider, "provider"),
        "provider_migration_policy": _require_text(
            provider_migration_policy,
            "provider_migration_policy",
        ),
    }
    validate_evidence_manifest(manifest, payload=payload)
    return manifest


def validate_evidence_manifest(
    manifest: Mapping[str, Any],
    *,
    payload: bytes | None = None,
) -> dict[str, Any]:
    """Validate the exact manifest shape required by the retention authority."""

    if not isinstance(manifest, Mapping):
        raise EvidenceManifestError("evidence manifest must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceManifestError("evidence manifest schema version is invalid")
    if set(manifest) != _REQUIRED_FIELDS | {"schema_version"}:
        raise EvidenceManifestError("evidence manifest fields are not exact")
    for field in _REQUIRED_FIELDS - {"sha256", "created_at", "retention_until"}:
        _require_text(manifest[field], field)
    _require_digest(manifest["sha256"], "sha256")
    _, created_at = _parse_timestamp(manifest["created_at"], "created_at")
    _, retention_until = _parse_timestamp(manifest["retention_until"], "retention_until")
    if retention_until < created_at:
        raise EvidenceManifestError("retention_until must not precede created_at")
    if payload is not None:
        if not isinstance(payload, bytes):
            raise EvidenceManifestError("payload must be bytes")
        if manifest["sha256"] != hashlib.sha256(payload).hexdigest():
            raise EvidenceManifestError("evidence payload digest differs")
    return dict(manifest)
