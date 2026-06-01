#!/usr/bin/env python3
"""Generate a template-only A2 external signoff packet.

This generator emits a reviewer-fillable packet template for the existing
signoff intake contract. It is deliberately not approval, not signoff, and not
admission: reviewer decisions are placeholders until a real reviewer replaces
them with hash-only decision refs accepted by the intake contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import a2_blastfrag_signoff_intake_contract as contract  # noqa: E402


TEMPLATE_SCHEMA_VERSION = "a2.external_signoff_packet_template.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.external_signoff_packet_template_retained_manifest.v1"
)
DEFAULT_RETAINED_DIR = (
    contract.RETAINED_ROOT / "external_signoff_packet_template_20260601"
)

TEMPLATE_FILENAME = "external_signoff_packet_template.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"
PLACEHOLDER_DECISION = "REVIEWER_TO_FILL_ALLOWED_DECISION"
PLACEHOLDER_SHA256 = "REVIEWER_TO_FILL_64_HEX_SHA256"


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_json_optional(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _source_request_ref(path: Path, repo_root: Path) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "artifact_key": "source_rights_signoff_request_packet",
        "relative_path": _rel(path, repo_root),
        "role": "current_source_rights_request_hash_pin_for_template_only_packet",
        "required_for_template": True,
        "present": path.is_file(),
    }
    if not path.is_file():
        ref["status"] = "missing_required_fail_closed"
        return ref

    ref["sha256"] = _sha256_file(path)
    payload = _load_json_optional(path)
    if payload is None:
        ref["status"] = "json_parse_failed_fail_closed"
        return ref

    ref["schema_version"] = payload.get("schema_version", "")
    ref["status"] = payload.get("status", "")
    return ref


def _current_required_signoff_ids(source_request_packet_path: Path) -> list[str]:
    intake_artifact = contract.generate_signoff_intake_contract(
        source_rights_signoff_request_packet_path=source_request_packet_path,
    )
    return list(intake_artifact["intake_contract_shape"]["required_signoff_ids"])


def _reviewer_decision_placeholders(
    required_signoff_ids: list[str],
    *,
    source_request_sha256: str,
) -> list[dict[str, Any]]:
    return [
        {
            "signoff_id": signoff_id,
            "decision": PLACEHOLDER_DECISION,
            "reviewer_ref_sha256": PLACEHOLDER_SHA256,
            "decision_ref_sha256": PLACEHOLDER_SHA256,
            "reviewed_input_ref_sha256": source_request_sha256,
            "placeholder_ref_only": True,
            "template_only": True,
            "approval_granted": False,
            "admission_granted": False,
            "signoff_decisions_consumed": False,
        }
        for signoff_id in required_signoff_ids
    ]


def _external_packet_json_schema(
    *,
    source_request_sha256: str,
    required_signoff_ids: list[str],
) -> dict[str, Any]:
    guard_fields = sorted(contract._authority_guards())
    top_level_required = [
        "schema_version",
        "package_id",
        "signoff_packet_id",
        "source_rights_signoff_request_packet_sha256",
        "reviewer_decisions",
        "raw_content_absence",
        "authority_guard_confirmation",
        "benchmark_consumption_decision",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "A2 external signoff intake packet template shape",
        "type": "object",
        "required": top_level_required,
        "additionalProperties": True,
        "properties": {
            "schema_version": {"const": contract.EXPECTED_EXTERNAL_SCHEMA_VERSION},
            "package_id": {"const": contract.PACKAGE_ID},
            "signoff_packet_id": {"type": "string", "minLength": 1},
            "source_rights_signoff_request_packet_sha256": {
                "const": source_request_sha256,
            },
            "reviewer_decisions": {
                "type": "array",
                "minItems": len(required_signoff_ids),
                "maxItems": len(required_signoff_ids),
            },
            "raw_content_absence": {
                "type": "object",
                "required": contract.RAW_ABSENCE_FIELDS,
                "properties": {
                    field: {"const": False} for field in contract.RAW_ABSENCE_FIELDS
                },
                "additionalProperties": False,
            },
            "authority_guard_confirmation": {
                "type": "object",
                "required": guard_fields,
                "properties": {
                    guard_id: {"const": False} for guard_id in guard_fields
                },
                "additionalProperties": False,
            },
            "benchmark_consumption_decision": {
                "enum": contract.BENCHMARK_DECISION_VALUES,
            },
        },
    }


def generate_external_signoff_packet_template(
    *,
    repo_root: Path = REPO_ROOT,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    source_rights_signoff_request_packet_path: Path = (
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    ),
) -> dict[str, Any]:
    source_ref = _source_request_ref(
        source_rights_signoff_request_packet_path,
        repo_root,
    )
    source_request_sha256 = source_ref.get("sha256", "")
    required_signoff_ids = _current_required_signoff_ids(
        source_rights_signoff_request_packet_path
    )
    raw_absence = {field: False for field in contract.RAW_ABSENCE_FIELDS}
    authority_guards = contract._authority_guards()

    return {
        "schema_version": contract.EXPECTED_EXTERNAL_SCHEMA_VERSION,
        "template_schema_version": TEMPLATE_SCHEMA_VERSION,
        "package_id": contract.PACKAGE_ID,
        "status": "retained_external_signoff_packet_template_only_not_approval_not_signoff",
        "packet_type": "external_signoff_packet_template_for_reviewer_completion",
        "artifact_dir": _rel(retained_dir, repo_root),
        "signoff_packet_id": "REVIEWER_TO_FILL_UNIQUE_PACKET_ID",
        "source_rights_signoff_request_packet_sha256": source_request_sha256,
        "source_rights_signoff_request_packet_ref": source_ref,
        "reviewer_decisions": _reviewer_decision_placeholders(
            required_signoff_ids,
            source_request_sha256=source_request_sha256,
        ),
        "raw_content_absence": raw_absence,
        "authority_guard_confirmation": authority_guards,
        "benchmark_consumption_decision": (
            "not_consumed_for_release_by_this_packet"
        ),
        "approval_granted": False,
        "release_grade_satisfied": False,
        "template_only": True,
        "admission_granted": False,
        "signoff_decisions_consumed": False,
        "benchmark_consumed_for_release": False,
        "required_signoff_ids_ref": required_signoff_ids,
        "allowed_review_decisions_ref": contract.ALLOWED_REVIEW_DECISIONS,
        "reviewer_fill_in_contract": {
            "replace_placeholder_decision_before_intake": True,
            "replace_placeholder_hash_refs_before_intake": True,
            "retain_hash_refs_only": True,
            "do_not_attach_source_payloads_or_workbook_copies": True,
        },
        "json_schema": _external_packet_json_schema(
            source_request_sha256=source_request_sha256,
            required_signoff_ids=required_signoff_ids,
        ),
        "integration_notes": [
            "This file is a template for external reviewer completion only.",
            "Template placeholder decisions are intentionally not intake-valid decisions.",
            "A filled packet must be checked by the existing signoff intake contract before any later admission gate may consider it.",
            "No source payload bodies, selected-output bodies, workbook copies, or command streams are retained by this template.",
        ],
    }


def write_retained_artifacts(
    *,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    source_rights_signoff_request_packet_path: Path = (
        contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH
    ),
) -> dict[str, Any]:
    template = generate_external_signoff_packet_template(
        repo_root=repo_root,
        retained_dir=retained_dir,
        source_rights_signoff_request_packet_path=source_rights_signoff_request_packet_path,
    )
    retained_dir.mkdir(parents=True, exist_ok=True)

    template_path = retained_dir / TEMPLATE_FILENAME
    _write_json(template_path, template)
    template_sha256 = _sha256_file(template_path)
    template_artifact = {
        "artifact_key": "external_signoff_packet_template",
        "filename": TEMPLATE_FILENAME,
        "relative_path": _rel(template_path, repo_root),
        "schema_version": TEMPLATE_SCHEMA_VERSION,
        "external_schema_version": template["schema_version"],
        "sha256": template_sha256,
    }

    authority_guards = contract._authority_guards()
    manifest = {
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "package_id": contract.PACKAGE_ID,
        "status": template["status"],
        "artifact_dir": _rel(retained_dir, repo_root),
        "artifacts": [template_artifact],
        "input_refs": [template["source_rights_signoff_request_packet_ref"]],
        "approval_granted": False,
        "release_grade_satisfied": False,
        "template_only": True,
        "admission_granted": False,
        "signoff_decisions_consumed": False,
        "benchmark_consumed_for_release": False,
        "authority_guards": authority_guards,
        "authority_guards_all_false": not any(authority_guards.values()),
        "raw_content_absence": template["raw_content_absence"],
        "required_signoff_ids": template["required_signoff_ids_ref"],
        "retained_manifest_integrity_expected": "clean_for_single_manifest",
    }
    manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
    _write_json(manifest_path, manifest)

    template["retained_artifact_ref"] = _rel(template_path, repo_root)
    template["retained_artifact_sha256"] = template_sha256
    template["retained_manifest_ref"] = _rel(manifest_path, repo_root)
    template["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a template-only external signoff packet for the A2 "
            "blast-fragmentation signoff intake contract."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated template JSON.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained external signoff packet template artifacts.",
    )
    parser.add_argument(
        "--source-rights-signoff-request-packet",
        type=Path,
        default=contract.SOURCE_RIGHTS_SIGNOFF_REQUEST_PACKET_PATH,
        help="Current source-rights signoff request packet JSON.",
    )
    args = parser.parse_args(argv)

    template = write_retained_artifacts(
        retained_dir=args.retained_dir,
        source_rights_signoff_request_packet_path=args.source_rights_signoff_request_packet,
    )
    if args.output:
        _write_json(args.output, template)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
