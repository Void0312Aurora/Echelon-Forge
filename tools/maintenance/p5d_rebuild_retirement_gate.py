"""Evaluate the P5-D gate for retiring production rebuild authority.

The reachability inventory is intentionally pre-cutover and therefore cannot
declare the native rebuild retired by itself.  This module is the separate,
fail-closed post-window gate: it combines a durable ``stable`` rollout
snapshot, the storage-side retention check, the fresh pre-cutover inventory,
and an explicit cutover/adoption attestation.  It only returns a proof
document; it does not delete the native test capability or mutate a rollout
slot.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from tools.maintenance import runtime_rebuild_unreachability as rebuild_inventory
from tools.maintenance.runtime_authority_contracts import canonical_json_bytes


SCHEMA_VERSION = "echelon_forge.p5d_rebuild_retirement.v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_RETENTION_CLASSES = {
    "release_manifest": "active-release",
    "rollout_decision": "rollback-window",
    "run_receipt": "run-retained",
    "rollout_evidence": "rollback-window",
}


class RetirementGateError(ValueError):
    """Raised when the post-cutover rebuild-retirement gate is not met."""


def _require_digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise RetirementGateError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _require_nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise RetirementGateError(f"{name} must be a non-empty string")
    return value


def _stable_admission_fields(
    admission: Mapping[str, Any],
) -> tuple[str, str, str, int, Mapping[str, Any]]:
    try:
        decision = admission["decision"]
        payload = decision["payload"]
        release_id = payload["release_id"]
        decision_id = payload["decision_id"]
        decision_digest = decision["payload_sha256"]
        state = payload["state"]
        version = admission["version"]
    except (KeyError, TypeError) as error:
        raise RetirementGateError("durable rollout admission shape is invalid") from error
    if state != "stable":
        raise RetirementGateError("rebuild retirement requires a stable rollout admission")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise RetirementGateError("durable rollout admission version is invalid")
    if admission.get("admissions_open") is not True or admission.get("writer_advancement_frozen") is not False:
        raise RetirementGateError("stable rollout admission is not open and unfrozen")
    evidence_version = admission.get("evidence_version")
    if isinstance(evidence_version, bool) or not isinstance(evidence_version, int) or evidence_version != version:
        raise RetirementGateError("durable rollout evidence version differs from admission")
    if not isinstance(admission.get("evidence"), Mapping):
        raise RetirementGateError("durable rollout evidence projection is absent")
    evidence = admission["evidence"]
    if evidence.get("release_id") != release_id:
        raise RetirementGateError("durable rollout evidence release identity differs")
    if evidence.get("decision_id") != decision_id:
        raise RetirementGateError("durable rollout evidence decision identity differs")
    if evidence.get("decision_payload_sha256") != decision_digest:
        raise RetirementGateError("durable rollout evidence decision digest differs")
    if evidence.get("admissions_open") is not True or evidence.get("writer_advancement_frozen") is not False:
        raise RetirementGateError("stable rollout evidence is not open and unfrozen")
    for field in (
        "release_manifest_blob_sha256",
        "run_receipt_blob_sha256",
    ):
        _require_digest(evidence.get(field), f"rollout evidence {field}")
    return (
        _require_nonempty(release_id, "release_id"),
        _require_nonempty(decision_id, "decision_id"),
        _require_digest(decision_digest, "decision payload digest"),
        version,
        evidence,
    )


def _validate_retention(
    retention: Mapping[str, Any],
    *,
    release_id: str,
    slot_version: int,
    decision_digest: str,
    decision_envelope_digest: str,
    evidence: Mapping[str, Any],
) -> dict[str, str]:
    if retention.get("release_id") != release_id:
        raise RetirementGateError("rollback retention release identity differs")
    if retention.get("state") != "stable":
        raise RetirementGateError("rollback retention check is not for stable state")
    retention_slot_version = retention.get("slot_version")
    retention_evidence_version = retention.get("evidence_version")
    if (
        isinstance(retention_slot_version, bool)
        or not isinstance(retention_slot_version, int)
        or isinstance(retention_evidence_version, bool)
        or not isinstance(retention_evidence_version, int)
        or retention_slot_version != slot_version
        or retention_evidence_version != slot_version
    ):
        raise RetirementGateError("rollback retention version differs from durable admission")
    blobs = retention.get("blobs")
    if not isinstance(blobs, Mapping) or set(blobs) != set(_RETENTION_CLASSES):
        raise RetirementGateError("rollback retention blob projection is incomplete")
    try:
        expected_digests = {
            "release_manifest": str(evidence["release_manifest_blob_sha256"]),
            "rollout_decision": decision_envelope_digest,
            "run_receipt": str(evidence["run_receipt_blob_sha256"]),
            "rollout_evidence": hashlib.sha256(canonical_json_bytes(evidence)).hexdigest(),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise RetirementGateError("durable rollout evidence projection is not canonical") from error
    digests: dict[str, str] = {}
    for name, expected_class in _RETENTION_CLASSES.items():
        row = blobs[name]
        if not isinstance(row, Mapping):
            raise RetirementGateError(f"rollback retention row is invalid for {name}")
        if row.get("retention_class") != expected_class:
            raise RetirementGateError(f"rollback retention class differs for {name}")
        digest = _require_digest(
            row.get("digest"),
            f"rollback retention digest for {name}",
        )
        if digest != expected_digests[name]:
            raise RetirementGateError(f"rollback retention digest differs for {name}")
        digests[name] = digest
    return digests


def _validate_attestation(
    attestation: Mapping[str, Any] | None,
    *,
    release_id: str,
    decision_id: str,
    decision_digest: str,
    inventory_digest: str,
    retained_digests: Mapping[str, str],
) -> dict[str, Any]:
    if not isinstance(attestation, Mapping):
        raise RetirementGateError("explicit production cutover attestation is required")
    required = {
        "attestation_id",
        "release_id",
        "decision_id",
        "decision_payload_sha256",
        "inventory_sha256",
        "production_caller_cutover",
        "rollback_window_verified",
        "adoption_evidence_sha256",
        "rollback_window_evidence_sha256",
    }
    if set(attestation) != required:
        raise RetirementGateError("production cutover attestation fields are not exact")
    if attestation["release_id"] != release_id or attestation["decision_id"] != decision_id:
        raise RetirementGateError("production cutover attestation identity differs")
    if attestation["decision_payload_sha256"] != decision_digest:
        raise RetirementGateError("production cutover attestation decision digest differs")
    if attestation["inventory_sha256"] != inventory_digest:
        raise RetirementGateError("production cutover attestation inventory digest differs")
    if attestation["production_caller_cutover"] is not True:
        raise RetirementGateError("production caller cutover is not attested")
    if attestation["rollback_window_verified"] is not True:
        raise RetirementGateError("rollback window is not attested")
    _require_nonempty(attestation["attestation_id"], "attestation_id")
    adoption_digest = _require_digest(
        attestation["adoption_evidence_sha256"],
        "adoption evidence digest",
    )
    rollback_digest = _require_digest(
        attestation["rollback_window_evidence_sha256"],
        "rollback-window evidence digest",
    )
    rollout_evidence_digest = retained_digests["rollout_evidence"]
    if adoption_digest != rollout_evidence_digest:
        raise RetirementGateError("adoption evidence digest is not the retained rollout evidence")
    if rollback_digest != rollout_evidence_digest:
        raise RetirementGateError("rollback-window evidence digest is not the retained rollout evidence")
    return dict(attestation)


def build_retirement_proof(
    *,
    admission: Mapping[str, Any],
    retention: Mapping[str, Any],
    inventory: Mapping[str, Any],
    cutover_attestation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a production-authority retirement proof after every gate passes."""

    try:
        rebuild_inventory.validate_inventory(dict(inventory))
    except (rebuild_inventory.InventoryError, TypeError, ValueError) as error:
        raise RetirementGateError("fresh pre-cutover rebuild inventory is not valid") from error
    if inventory.get("production_callable_references") or inventory.get("python_binding_references"):
        raise RetirementGateError("rebuild production or Python callers remain")
    release_id, decision_id, decision_digest, slot_version, evidence = _stable_admission_fields(admission)
    try:
        decision_envelope_digest = hashlib.sha256(
            canonical_json_bytes(admission["decision"])
        ).hexdigest()
    except (KeyError, TypeError, ValueError) as error:
        raise RetirementGateError("durable rollout decision projection is not canonical") from error
    retained_digests = _validate_retention(
        retention,
        release_id=release_id,
        slot_version=slot_version,
        decision_digest=decision_digest,
        decision_envelope_digest=decision_envelope_digest,
        evidence=evidence,
    )
    attestation = _validate_attestation(
        cutover_attestation,
        release_id=release_id,
        decision_id=decision_id,
        decision_digest=decision_digest,
        inventory_digest=str(inventory["inventory_sha256"]),
        retained_digests=retained_digests,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": release_id,
        "decision_id": decision_id,
        "decision_payload_sha256": decision_digest,
        "rollout_state": "stable",
        "slot_version": slot_version,
        "inventory_sha256": inventory["inventory_sha256"],
        "retirement_scope": "production_rebuild_authority_only",
        "reachability_state": "retired_after_rollback_window",
        "retired": True,
        "native_test_capability_retained": True,
        "cutover_attestation": attestation,
    }
