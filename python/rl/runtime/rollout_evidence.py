"""Release and RunReceipt binding for the local P5-D admission gate.

This module validates only the cross-record identity projection needed before
constructing a maintained production caller. Full release/receipt schema
qualification remains owned by the release and native evidence lanes; this
projection prevents a locally valid rollout slot from being paired with a
different release, plan, decision, or package.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .rollout_gate import RolloutAdmission
from .rollout_gate import canonical_json_bytes


class RolloutEvidenceError(RuntimeError):
    """Raised when release or receipt binding evidence is invalid."""


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$")
_ENVELOPE_FIELDS = frozenset(
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
_CANONICALIZATION = "echelon_forge.canonical_json.v2"
_ENVELOPE_VERSION = "echelon_forge.authority_envelope.v1"
_RELEASE_DOMAIN = "release.manifest"
_RELEASE_MEDIA_TYPE = "application/vnd.echelon-forge.release-manifest.v1+json"
_RECEIPT_DOMAIN = "runtime.run-receipt"
_RECEIPT_MEDIA_TYPE = "application/vnd.echelon-forge.run-receipt.v1+json"
_RELEASE_PAYLOAD_FIELDS = frozenset(
    {
        "authority_kind",
        "schema_version",
        "contract_version",
        "writer_role",
        "release_id",
        "writer_generation",
        "reader_generation_min",
        "reader_generation_max",
        "package_set",
        "supported_rows",
        "provenance_sha256",
        "sbom_sha256",
        "toolchain_identity",
        "source_revision",
        "compatibility_generation",
        "minimum_reader_generation",
        "state_schema_generation",
        "rollback_policy",
        "stored_artifact_inventory_sha256",
        "rollback_deadline",
        "last_reader_deadline",
        "irreversible_write_boundary",
    }
)


def _require_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise RolloutEvidenceError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _require_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise RolloutEvidenceError(f"{field} must be a bounded identifier")
    return value


def _authority_digest(domain: str, media_type: str, payload: Mapping[str, Any]) -> str:
    material = (
        b"echelon-forge-authority-v1\x00"
        + domain.encode("utf-8")
        + b"\x00"
        + media_type.encode("utf-8")
        + b"\x00"
        + canonical_json_bytes(payload)
    )
    return hashlib.sha256(material).hexdigest()


def _validate_envelope_document(
    value: Mapping[str, Any],
    *,
    source_label: str,
    domain: str,
    media_type: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ENVELOPE_FIELDS:
        raise RolloutEvidenceError(f"{source_label} has an invalid authority envelope shape")
    if (
        value["canonicalization"] != _CANONICALIZATION
        or value["envelope_version"] != _ENVELOPE_VERSION
        or value["domain"] != domain
        or value["media_type"] != media_type
    ):
        raise RolloutEvidenceError(f"{source_label} authority identity differs")
    payload = value["payload"]
    if not isinstance(payload, Mapping):
        raise RolloutEvidenceError(f"{source_label} payload is not an object")
    payload_digest = _require_sha(value["payload_sha256"], f"{source_label}.payload_sha256")
    if payload_digest != _authority_digest(domain, media_type, payload):
        raise RolloutEvidenceError(f"{source_label} payload digest does not match its bytes")
    if not isinstance(value["signatures"], list):
        raise RolloutEvidenceError(f"{source_label}.signatures is not an array")
    return dict(value)


def _read_envelope(path: str | Path, *, domain: str, media_type: str) -> dict[str, Any]:
    source = Path(path)
    try:
        raw_bytes = source.read_bytes()
        value = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RolloutEvidenceError(f"{source} is not readable canonical JSON") from error
    if canonical_json_bytes(value) != raw_bytes:
        raise RolloutEvidenceError(f"{source} is not canonical JSON")
    return _validate_envelope_document(
        value,
        source_label=str(source),
        domain=domain,
        media_type=media_type,
    )


def _validate_release_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if set(payload) != _RELEASE_PAYLOAD_FIELDS:
        raise RolloutEvidenceError("release manifest payload fields are not exact")
    if payload["authority_kind"] != "release_manifest":
        raise RolloutEvidenceError("release manifest authority kind is invalid")
    _require_id(payload["release_id"], "release_id")
    for field in (
        "provenance_sha256",
        "sbom_sha256",
        "stored_artifact_inventory_sha256",
    ):
        _require_sha(payload[field], field)
    package_set = payload["package_set"]
    if not isinstance(package_set, list) or not package_set:
        raise RolloutEvidenceError("release manifest package_set is empty")
    names: list[str] = []
    for package in package_set:
        if not isinstance(package, Mapping) or set(package) != {"name", "sha256"}:
            raise RolloutEvidenceError("release manifest package_set row is invalid")
        names.append(_require_id(package["name"], "package_set.name"))
        _require_sha(package["sha256"], "package_set.sha256")
    if names != sorted(names) or len(names) != len(set(names)):
        raise RolloutEvidenceError("release manifest package_set is not sorted and unique")
    return dict(payload)


@dataclass(frozen=True, slots=True)
class RolloutEvidenceBinding:
    release_id: str
    manifest_sha256: str
    plan_sha256: str
    decision_id: str
    decision_sha256: str
    receipt_id: str
    package_digest: str
    wheel_digest: str


def load_rollout_evidence(
    release_manifest_path: str | Path,
    run_receipt_path: str | Path,
) -> RolloutEvidenceBinding:
    """Load and validate the release/receipt identity projection."""

    release_envelope = _read_envelope(
        release_manifest_path,
        domain=_RELEASE_DOMAIN,
        media_type=_RELEASE_MEDIA_TYPE,
    )
    receipt_envelope = _read_envelope(
        run_receipt_path,
        domain=_RECEIPT_DOMAIN,
        media_type=_RECEIPT_MEDIA_TYPE,
    )
    return project_rollout_evidence(release_envelope, receipt_envelope)


def project_rollout_evidence(
    release_envelope: Mapping[str, Any],
    receipt_envelope: Mapping[str, Any],
) -> RolloutEvidenceBinding:
    """Project already-loaded canonical documents into the binding record.

    Release-controller backends use this mapping form while they hold their
    durable transaction; file callers should use :func:`load_rollout_evidence`
    so canonical bytes are checked at the filesystem boundary first.
    """

    release_document = _validate_envelope_document(
        release_envelope,
        source_label="release manifest",
        domain=_RELEASE_DOMAIN,
        media_type=_RELEASE_MEDIA_TYPE,
    )
    receipt_document = _validate_envelope_document(
        receipt_envelope,
        source_label="RunReceipt",
        domain=_RECEIPT_DOMAIN,
        media_type=_RECEIPT_MEDIA_TYPE,
    )
    release = _validate_release_payload(release_document["payload"])
    receipt = receipt_document["payload"]
    if not isinstance(receipt, Mapping):
        raise RolloutEvidenceError("RunReceipt payload is not an object")
    release_binding = receipt.get("release_binding")
    plan_binding = receipt.get("plan_binding")
    package = receipt.get("package")
    completion = receipt.get("completion")
    if not all(isinstance(value, Mapping) for value in (release_binding, plan_binding, package, completion)):
        raise RolloutEvidenceError("RunReceipt is missing binding sections")
    release_id = _require_id(release_binding.get("release_id"), "receipt.release_binding.release_id")
    manifest_sha256 = _require_sha(
        release_binding.get("release_manifest_sha256"),
        "receipt.release_binding.release_manifest_sha256",
    )
    decision_id = _require_id(
        release_binding.get("rollout_decision_id"),
        "receipt.release_binding.rollout_decision_id",
    )
    decision_sha256 = _require_sha(
        release_binding.get("rollout_decision_sha256"),
        "receipt.release_binding.rollout_decision_sha256",
    )
    plan_sha256 = _require_sha(plan_binding.get("plan_sha256"), "receipt.plan_binding.plan_sha256")
    receipt_id = _require_id(receipt.get("receipt_id"), "receipt.receipt_id")
    package_digest = _require_sha(package.get("digest"), "receipt.package.digest")
    wheel_digest = _require_sha(package.get("wheel_digest"), "receipt.package.wheel_digest")
    release_package_digests = {
        str(package_row["sha256"])
        for package_row in release["package_set"]
    }
    if package_digest not in release_package_digests:
        raise RolloutEvidenceError("RunReceipt package digest is absent from the release manifest")
    if completion.get("durable_ack") is not True:
        raise RolloutEvidenceError("RunReceipt completion is not durably acknowledged")
    if receipt.get("terminal_state") not in {
        "completed",
        "failed",
        "cancelled",
        "rejected",
        "crashed",
        "incomplete",
    }:
        raise RolloutEvidenceError("RunReceipt terminal state is not admitted")
    if release_id != release["release_id"] or manifest_sha256 != release_document["payload_sha256"]:
        raise RolloutEvidenceError("RunReceipt release binding differs from release manifest")
    return RolloutEvidenceBinding(
        release_id=release_id,
        manifest_sha256=manifest_sha256,
        plan_sha256=plan_sha256,
        decision_id=decision_id,
        decision_sha256=decision_sha256,
        receipt_id=receipt_id,
        package_digest=package_digest,
        wheel_digest=wheel_digest,
    )


def assert_rollout_evidence_binding(
    admission: RolloutAdmission,
    binding: RolloutEvidenceBinding,
    *,
    expected_package_digest: str | None = None,
    expected_wheel_digest: str | None = None,
) -> None:
    """Fail closed unless evidence names the exact admitted rollout identity."""

    assert_rollout_evidence_decision_binding(
        admission.envelope,
        binding,
        expected_package_digest=expected_package_digest,
        expected_wheel_digest=expected_wheel_digest,
    )


def assert_rollout_evidence_decision_binding(
    decision_envelope: Mapping[str, Any],
    binding: RolloutEvidenceBinding,
    *,
    expected_package_digest: str | None = None,
    expected_wheel_digest: str | None = None,
) -> None:
    """Validate evidence against a not-yet-persisted rollout envelope.

    The release-controller CLI uses this pre-commit form so a production
    decision cannot be written first and checked only after the slot has
    already become authoritative.  ``RuntimeFacadeAdapter`` continues to use
    :func:`assert_rollout_evidence_binding` for the persisted-slot path.
    """

    if not isinstance(decision_envelope, Mapping):
        raise RolloutEvidenceError("rollout decision envelope is not an object")
    payload = decision_envelope.get("payload")
    if not isinstance(payload, Mapping):
        raise RolloutEvidenceError("rollout decision payload is not an object")
    decision_sha256 = _require_sha(
        decision_envelope.get("payload_sha256"),
        "rollout decision payload_sha256",
    )
    if (
        binding.release_id != payload["release_id"]
        or binding.manifest_sha256 != payload["manifest_sha256"]
        or binding.plan_sha256 != payload["plan_sha256"]
        or binding.decision_id != payload["decision_id"]
        or binding.decision_sha256 != decision_sha256
    ):
        raise RolloutEvidenceError("release/plan/decision evidence differs from rollout admission")
    if expected_package_digest is not None and binding.package_digest != _require_sha(
        expected_package_digest,
        "expected_package_digest",
    ):
        raise RolloutEvidenceError("RunReceipt package digest differs from the admitted package")
    if expected_wheel_digest is not None and binding.wheel_digest != _require_sha(
        expected_wheel_digest,
        "expected_wheel_digest",
    ):
        raise RolloutEvidenceError("RunReceipt wheel digest differs from the admitted wheel")


__all__ = [
    "RolloutEvidenceBinding",
    "RolloutEvidenceError",
    "assert_rollout_evidence_binding",
    "assert_rollout_evidence_decision_binding",
    "load_rollout_evidence",
    "project_rollout_evidence",
]
