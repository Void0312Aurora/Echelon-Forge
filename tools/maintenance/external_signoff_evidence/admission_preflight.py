#!/usr/bin/env python3
"""Generate the damage-model signoff admission preflight packet.

This packet is deliberately not an admission gate. It reads the retained
signoff intake contract, optionally shape-checks an external signoff packet
through the intake contract generator, and reports whether the next RES-005/
RES-006 admission gate can be entered. It never consumes signoff decisions,
never closes residuals, and never grants authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.external_signoff_evidence import (  # noqa: E402
    intake_contract,
)


PACKAGE_ID = intake_contract.PACKAGE_ID
SCHEMA_VERSION = "a2.blastfrag_signoff_admission_preflight.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.blastfrag_signoff_admission_preflight_retained_manifest.v1"
)

DEFAULT_SIGNOFF_INTAKE_CONTRACT_PATH = (
    intake_contract.DEFAULT_RETAINED_DIR / intake_contract.CONTRACT_FILENAME
)
DEFAULT_RETAINED_DIR = (
    intake_contract.RETAINED_ROOT / "signoff_admission_preflight_20260601"
)

PREFLIGHT_FILENAME = "signoff_admission_preflight_packet.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"


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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def _input_ref(
    *,
    artifact_key: str,
    path: Path,
    repo_root: Path,
    role: str,
    required: bool,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "artifact_key": artifact_key,
        "relative_path": _rel(path, repo_root),
        "role": role,
        "required_for_preflight": required,
        "present": path.is_file(),
    }
    if not path.is_file():
        ref["status"] = (
            "missing_required_fail_closed" if required else "missing_optional_fail_closed"
        )
        return ref

    ref["sha256"] = _sha256_file(path)
    payload = _load_json_optional(path)
    if payload is None:
        ref["status"] = "json_parse_failed_fail_closed"
        return ref

    ref["schema_version"] = payload.get("schema_version", "")
    ref["package_id"] = payload.get("package_id", "")
    ref["status"] = payload.get("status", "")
    return ref


def _candidate_packet_ref(
    *,
    candidate_signoff_packet_path: Path | None,
    repo_root: Path,
) -> dict[str, Any]:
    if candidate_signoff_packet_path is None:
        return {
            "present": False,
            "status": "external_signoff_packet_not_supplied_fail_closed",
        }

    ref = _input_ref(
        artifact_key="candidate_signoff_packet",
        path=candidate_signoff_packet_path,
        repo_root=repo_root,
        role="optional_external_signoff_packet_shape_check_only",
        required=False,
    )
    if ref["present"] and ref.get("schema_version"):
        ref["status"] = "external_signoff_packet_loaded_for_shape_check_only"
    return ref


def _contract_required_signoff_ids(contract_payload: dict[str, Any] | None) -> list[str]:
    shape = (contract_payload or {}).get("intake_contract_shape", {})
    required_ids = shape.get("required_signoff_ids", [])
    if not isinstance(required_ids, list):
        return []
    return [signoff_id for signoff_id in required_ids if isinstance(signoff_id, str)]


def _contract_state(
    *,
    contract_payload: dict[str, Any] | None,
    contract_ref: dict[str, Any],
    generated_contract: dict[str, Any],
) -> dict[str, Any]:
    generated_required_ids = generated_contract.get("intake_contract_shape", {}).get(
        "required_signoff_ids", []
    )
    retained_required_ids = _contract_required_signoff_ids(contract_payload)
    schema_valid = contract_ref.get("schema_version") == intake_contract.SCHEMA_VERSION
    package_valid = contract_ref.get("package_id") == PACKAGE_ID
    retained_guards = (contract_payload or {}).get("authority_guards", {})
    authority_guards_all_false = (
        isinstance(retained_guards, dict) and not any(retained_guards.values())
    )
    contract_does_not_grant = all(
        (contract_payload or {}).get(field) is False
        for field in ("approval_granted", "admission_granted")
    )
    required_shape_matches = retained_required_ids == generated_required_ids
    usable = all(
        [
            contract_ref["present"],
            contract_payload is not None,
            schema_valid,
            package_valid,
            authority_guards_all_false,
            contract_does_not_grant,
            required_shape_matches,
        ]
    )

    blockers: list[dict[str, str]] = []
    if not contract_ref["present"]:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_missing",
                "detail": "retained signoff intake contract artifact is missing",
            }
        )
    elif contract_payload is None:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_json_invalid",
                "detail": "retained signoff intake contract artifact is not valid JSON",
            }
        )
    if contract_payload is not None and not schema_valid:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_schema_mismatch",
                "detail": f"expected {intake_contract.SCHEMA_VERSION}",
            }
        )
    if contract_payload is not None and not package_valid:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_package_mismatch",
                "detail": "retained contract package_id does not match this package",
            }
        )
    if contract_payload is not None and not authority_guards_all_false:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_authority_guard_true",
                "detail": "retained contract authority guards must all remain false",
            }
        )
    if contract_payload is not None and not contract_does_not_grant:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_grants_authority",
                "detail": "retained contract must not grant approval or admission",
            }
        )
    if contract_payload is not None and not required_shape_matches:
        blockers.append(
            {
                "blocker_id": "signoff_intake_contract_required_ids_stale",
                "detail": "retained contract required signoff ids differ from current shape",
            }
        )

    return {
        "present": bool(contract_ref["present"]),
        "schema_version": contract_ref.get("schema_version", ""),
        "status": contract_ref.get("status", ""),
        "sha256": contract_ref.get("sha256", ""),
        "schema_valid": schema_valid,
        "package_valid": package_valid,
        "authority_guards_all_false": authority_guards_all_false,
        "contract_does_not_grant_approval_or_admission": contract_does_not_grant,
        "required_signoff_ids": retained_required_ids,
        "required_signoff_ids_match_current_shape": required_shape_matches,
        "usable_for_preflight": usable,
        "blockers": blockers,
    }


def _shape_blockers(shape_result: dict[str, Any]) -> list[dict[str, str]]:
    if not shape_result.get("candidate_packet_supplied"):
        return [
            {
                "blocker_id": "external_signoff_packet_not_supplied",
                "detail": "no external signoff packet was supplied for shape check",
            }
        ]
    if shape_result.get("intake_shape_valid") is True:
        return []

    blockers: list[dict[str, str]] = []
    for finding in shape_result.get("findings", []):
        if not isinstance(finding, dict):
            continue
        blockers.append(
            {
                "blocker_id": "external_signoff_packet_shape_invalid",
                "source_finding_id": str(finding.get("finding_id", "")),
                "detail": str(finding.get("detail", "")),
            }
        )
    return blockers


def _admission_paths(ready_for_admission_gate: bool) -> list[dict[str, Any]]:
    return [
        {
            "path_id": "RES-005",
            "gate_family": "tp21_selected_case_admission",
            "ready_for_admission_gate": ready_for_admission_gate,
            "approval_granted_by_this_preflight": False,
            "admission_granted_by_this_preflight": False,
            "residual_closed_by_this_preflight": False,
        },
        {
            "path_id": "RES-006",
            "gate_family": "beco_replacement_tolerance_admission",
            "ready_for_admission_gate": ready_for_admission_gate,
            "approval_granted_by_this_preflight": False,
            "admission_granted_by_this_preflight": False,
            "residual_closed_by_this_preflight": False,
        },
    ]


def generate_signoff_admission_preflight(
    *,
    repo_root: Path = REPO_ROOT,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    signoff_intake_contract_path: Path = DEFAULT_SIGNOFF_INTAKE_CONTRACT_PATH,
    candidate_signoff_packet_path: Path | None = None,
) -> dict[str, Any]:
    contract_payload = _load_json_optional(signoff_intake_contract_path)
    generated_contract = intake_contract.generate_signoff_intake_contract(
        repo_root=repo_root,
        retained_dir=signoff_intake_contract_path.parent,
        candidate_signoff_packet_path=candidate_signoff_packet_path,
    )
    shape_result = generated_contract["current_check_result"]
    contract_ref = _input_ref(
        artifact_key="signoff_intake_contract",
        path=signoff_intake_contract_path,
        repo_root=repo_root,
        role="current_retained_signoff_intake_contract_input",
        required=True,
    )
    candidate_ref = _candidate_packet_ref(
        candidate_signoff_packet_path=candidate_signoff_packet_path,
        repo_root=repo_root,
    )
    input_refs = [contract_ref]
    if candidate_signoff_packet_path is not None:
        input_refs.append(candidate_ref)

    contract_state = _contract_state(
        contract_payload=contract_payload,
        contract_ref=contract_ref,
        generated_contract=generated_contract,
    )
    shape_valid = bool(shape_result.get("intake_shape_valid") is True)
    ready_for_admission_gate = bool(
        contract_state["usable_for_preflight"] and shape_valid
    )
    blockers = [
        *contract_state["blockers"],
        *_shape_blockers(shape_result),
    ]

    if ready_for_admission_gate:
        status = "preflight_ready_for_res005_res006_admission_gate_shape_only_not_approval"
    elif not contract_state["usable_for_preflight"]:
        status = "blocked_fail_closed_signoff_admission_preflight_contract_not_usable"
    elif not shape_result.get("candidate_packet_supplied"):
        status = "retained_fail_closed_signoff_admission_preflight_no_external_packet"
    else:
        status = "blocked_fail_closed_signoff_admission_preflight_shape_invalid"

    guards = intake_contract._authority_guards()
    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "status": status,
        "packet_type": "signoff_admission_preflight_packet_not_admission_gate",
        "artifact_dir": _rel(retained_dir, repo_root),
        "preflight_id": "TC-A2-BF-003-SIGNOFF-INTAKE-NEXT-C-ADMISSION-PREFLIGHT-20260601",
        "approval_granted": False,
        "release_grade_satisfied": False,
        "admission_granted": False,
        "ready_for_admission_gate": ready_for_admission_gate,
        "ready_for_res005_admission_gate": ready_for_admission_gate,
        "ready_for_res006_admission_gate": ready_for_admission_gate,
        "signoff_decisions_consumed": False,
        "residuals_closed_by_this_preflight": [],
        "benchmark_consumed_for_release": False,
        "fail_closed": True,
        "not_admission_gate": True,
        "input_refs": input_refs,
        "signoff_intake_contract_state": contract_state,
        "candidate_signoff_packet_ref": candidate_ref,
        "shape_check_source": (
            "external_signoff_evidence.intake_contract."
            "generate_signoff_intake_contract"
        ),
        "shape_check_result": {
            "candidate_packet_supplied": shape_result["candidate_packet_supplied"],
            "intake_shape_valid": shape_result["intake_shape_valid"],
            "ready_for_separate_reviewer_admission_gate": shape_result[
                "ready_for_separate_reviewer_admission_gate"
            ],
            "signoff_decisions_consumed": False,
            "reviewer_decision_summaries": shape_result["reviewer_decision_summaries"],
            "missing_signoff_ids": shape_result["missing_signoff_ids"],
            "unexpected_signoff_ids": shape_result["unexpected_signoff_ids"],
            "duplicate_signoff_ids": shape_result.get("duplicate_signoff_ids", []),
            "forbidden_key_hits": shape_result["forbidden_key_hits"],
            "finding_count": shape_result["finding_count"],
            "findings": shape_result["findings"],
        },
        "preflight_blockers": blockers,
        "preflight_blocker_count": len(blockers),
        "admission_paths": _admission_paths(ready_for_admission_gate),
        "authority_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
        "forbidden_output_policy": {
            "raw_source_text_tables_values_formulas_retained": False,
            "raw_outputs_retained": False,
            "selected_output_preimages_retained": False,
            "temporary_workbook_copy_stdout_or_stderr_retained": False,
            "source_payloads_consumed_as_release_benchmarks": False,
        },
        "integration_notes": [
            "This preflight only reports whether RES-005/RES-006 admission gate inputs can be attempted.",
            "A shape-valid signoff packet is not approval and is not consumed by this preflight.",
            "Later admission gates must explicitly consume retained hash refs and reviewer decisions.",
            "No TP-21/BEC-O raw source text, tables, values, formulas, raw outputs, workbook copies, stdout, or stderr are retained here.",
        ],
        "behavior_risks": [
            "ready_for_admission_gate can be mistaken for admission; it is only a next-step preflight result",
            "shape-valid reviewer decisions can be mistaken for consumed approval; this packet keeps signoff_decisions_consumed false",
            "hash-only refs can be mistaken for permission to disclose raw TP-21/BEC-O content",
        ],
        "preflight_sha256": _sha256_text(
            _canonical_json(
                {
                    "input_refs": input_refs,
                    "contract_state": contract_state,
                    "candidate_signoff_packet_ref": candidate_ref,
                    "shape_check_result": shape_result,
                    "ready_for_admission_gate": ready_for_admission_gate,
                    "authority_guards": guards,
                }
            )
        ),
    }


def write_retained_artifacts(
    *,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    signoff_intake_contract_path: Path = DEFAULT_SIGNOFF_INTAKE_CONTRACT_PATH,
    candidate_signoff_packet_path: Path | None = None,
) -> dict[str, Any]:
    artifact = generate_signoff_admission_preflight(
        repo_root=repo_root,
        retained_dir=retained_dir,
        signoff_intake_contract_path=signoff_intake_contract_path,
        candidate_signoff_packet_path=candidate_signoff_packet_path,
    )
    retained_dir.mkdir(parents=True, exist_ok=True)

    preflight_path = retained_dir / PREFLIGHT_FILENAME
    _write_json(preflight_path, artifact)
    preflight_sha256 = _sha256_file(preflight_path)
    preflight_artifact = {
        "artifact_key": "signoff_admission_preflight_packet",
        "filename": PREFLIGHT_FILENAME,
        "relative_path": _rel(preflight_path, repo_root),
        "schema_version": artifact["schema_version"],
        "sha256": preflight_sha256,
    }

    manifest = {
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "status": artifact["status"],
        "artifact_dir": _rel(retained_dir, repo_root),
        "artifacts": [preflight_artifact],
        "input_refs": artifact["input_refs"],
        "approval_granted": False,
        "release_grade_satisfied": False,
        "admission_granted": False,
        "ready_for_admission_gate": artifact["ready_for_admission_gate"],
        "ready_for_res005_admission_gate": artifact["ready_for_res005_admission_gate"],
        "ready_for_res006_admission_gate": artifact["ready_for_res006_admission_gate"],
        "signoff_decisions_consumed": False,
        "residuals_closed_by_this_preflight": [],
        "fail_closed": True,
        "not_admission_gate": True,
        "candidate_packet_supplied": artifact["shape_check_result"][
            "candidate_packet_supplied"
        ],
        "intake_shape_valid": artifact["shape_check_result"]["intake_shape_valid"],
        "preflight_blocker_count": artifact["preflight_blocker_count"],
        "raw_source_text_tables_values_formulas_retained": False,
        "raw_outputs_retained": False,
        "selected_output_preimages_retained": False,
        "benchmark_consumed_for_release": False,
        "authority_guards": artifact["authority_guards"],
        "authority_guards_all_false": artifact["authority_guards_all_false"],
    }
    manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
    _write_json(manifest_path, manifest)

    artifact["retained_artifact_ref"] = _rel(preflight_path, repo_root)
    artifact["retained_artifact_sha256"] = preflight_sha256
    artifact["retained_manifest_ref"] = _rel(manifest_path, repo_root)
    artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the fail-closed damage-model signoff admission preflight packet. "
            "This is not an admission gate."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated preflight packet JSON.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained signoff admission preflight artifacts.",
    )
    parser.add_argument(
        "--signoff-intake-contract",
        type=Path,
        default=DEFAULT_SIGNOFF_INTAKE_CONTRACT_PATH,
        help="Current retained signoff intake contract JSON.",
    )
    parser.add_argument(
        "--candidate-signoff-packet",
        type=Path,
        help="Optional external signoff packet to shape-check without consuming.",
    )
    args = parser.parse_args(argv)

    artifact = write_retained_artifacts(
        retained_dir=args.retained_dir,
        signoff_intake_contract_path=args.signoff_intake_contract,
        candidate_signoff_packet_path=args.candidate_signoff_packet,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
