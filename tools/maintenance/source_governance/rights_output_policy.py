#!/usr/bin/env python3
"""Evaluate the A2 RES-001 source rights and allowed-output policy gate.

This gate starts from the already-retained source payload pack. It verifies the
payload hashes, records whether public distribution statements can support a
rights review, freezes a fail-closed release-candidate output policy, and keeps
all authority guards false. It does not copy source payload bodies, admit tool
outputs, consume benchmark outputs, or release any stock/runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
SOURCE_RIGHTS_OUTPUT_POLICY_SCHEMA_VERSION = (
    "a2.source_rights_output_policy_gate.v1"
)
SOURCE_RIGHTS_OUTPUT_POLICY_MANIFEST_SCHEMA_VERSION = (
    "a2.source_rights_output_policy_retained_manifest.v1"
)
SOURCE_ARTIFACT_PACK_SCHEMA_VERSION = (
    "a2.provenance_identity_retained_source_artifact_pack.v1"
)

PACKAGE_DIR = (
    REPO_ROOT
    / "docs"
    / "task"
    / "air_combat"
    / "archive"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
SOURCE_PAYLOAD_PACK_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
)
DEFAULT_SOURCE_MANIFEST = (
    SOURCE_PAYLOAD_PACK_DIR / "source_artifact_pack_manifest.json"
)
DEFAULT_OUTPUT_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "source_rights_output_policy_20260531"
)

RIGHTS_POLICY_ARTIFACT_FILENAME = "source_rights_output_policy_gate.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"
POLICY_ID = "A2-RES001-SOURCE-RIGHTS-OUTPUT-POLICY-20260531"
POLICY_STATUS = "release_candidate_fail_closed_policy_frozen"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _resolve_repo_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else repo_root / path


def _content_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def _normalize_statement_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().upper()


def _public_distribution_statement(text: str) -> dict[str, Any]:
    normalized = _normalize_statement_text(text)
    has_public_release = "APPROVED FOR PUBLIC RELEASE" in normalized
    has_unlimited_distribution = "DISTRIBUTION IS UNLIMITED" in normalized
    has_statement_a = "DISTRIBUTION STATEMENT A" in normalized
    supported = has_public_release and has_unlimited_distribution
    if supported and has_statement_a:
        phrase_id = "distribution_statement_a_public_release_unlimited"
    elif supported:
        phrase_id = "public_release_distribution_unlimited"
    else:
        phrase_id = ""
    return {
        "statement_detected": supported,
        "statement_id": phrase_id,
        "has_distribution_statement_a_label": has_statement_a,
        "has_public_release_phrase": has_public_release,
        "has_unlimited_distribution_phrase": has_unlimited_distribution,
    }


def _pdf_text_probe(path: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "8", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return {
            "extraction_status": "pdftotext_missing_fail_closed",
            "statement_locator": "pdf_first_8_pages",
            "statement_detected": False,
            "statement_id": "",
            "has_distribution_statement_a_label": False,
            "has_public_release_phrase": False,
            "has_unlimited_distribution_phrase": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "extraction_status": "pdftotext_timeout_fail_closed",
            "statement_locator": "pdf_first_8_pages",
            "statement_detected": False,
            "statement_id": "",
            "has_distribution_statement_a_label": False,
            "has_public_release_phrase": False,
            "has_unlimited_distribution_phrase": False,
        }

    evidence = _public_distribution_statement(result.stdout)
    evidence.update(
        {
            "extraction_status": (
                "pdf_text_probe_ok" if result.returncode == 0 else "pdf_text_probe_failed"
            ),
            "statement_locator": "pdf_first_8_pages",
        }
    )
    return evidence


def _xlsx_text_probe(path: Path) -> dict[str, Any]:
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as workbook:
            for name in (
                "xl/sharedStrings.xml",
                "docProps/core.xml",
                "docProps/app.xml",
            ):
                if name not in workbook.namelist():
                    continue
                raw = workbook.read(name)
                try:
                    root = ElementTree.fromstring(raw)
                    chunks.append(" ".join(root.itertext()))
                except ElementTree.ParseError:
                    chunks.append(raw.decode("utf-8", errors="ignore"))
    except (OSError, zipfile.BadZipFile):
        return {
            "extraction_status": "xlsx_text_probe_failed",
            "statement_locator": "xlsx_shared_strings_and_docprops",
            "statement_detected": False,
            "statement_id": "",
            "has_distribution_statement_a_label": False,
            "has_public_release_phrase": False,
            "has_unlimited_distribution_phrase": False,
        }

    evidence = _public_distribution_statement("\n".join(chunks))
    evidence.update(
        {
            "extraction_status": "xlsx_text_probe_ok",
            "statement_locator": "xlsx_shared_strings_and_docprops",
        }
    )
    return evidence


def _extract_rights_evidence(path: Path, content_type: str) -> dict[str, Any]:
    if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
        return _pdf_text_probe(path)
    if path.suffix.lower() == ".xlsx":
        return _xlsx_text_probe(path)
    return {
        "extraction_status": "unsupported_payload_type_fail_closed",
        "statement_locator": "",
        "statement_detected": False,
        "statement_id": "",
        "has_distribution_statement_a_label": False,
        "has_public_release_phrase": False,
        "has_unlimited_distribution_phrase": False,
    }


def _non_authoritative_guards() -> dict[str, bool]:
    return {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "runtime_authority_granted": False,
        "effect_scale_authority_released": False,
        "effect_scale_authority_in_stock": False,
        "component_failure_probability_authority_released": False,
        "component_failure_probability_authority_in_stock": False,
        "pk_authority_released": False,
        "pk_authority": False,
        "deterministic_fuze_authority_released": False,
        "deterministic_fuze_authority": False,
    }


def _allowed_use_for_payload(label: str) -> str:
    if label == "BEC-O-V1.xlsx":
        return (
            "candidate_provenance_hash_rights_evidence_and_future_tool_output_"
            "hash_planning_only"
        )
    if label == "TP-21 PDF":
        return (
            "candidate_provenance_hash_rights_evidence_and_debris_vocabulary_"
            "reference_only"
        )
    return (
        "candidate_provenance_hash_rights_evidence_and_blast_method_design_"
        "reference_only"
    )


def _forbidden_use_for_payload(label: str) -> str:
    if label == "BEC-O-V1.xlsx":
        return (
            "copying spreadsheet body, formula or output tables; consuming "
            "spreadsheet/tool outputs as benchmark results; source truth; runtime "
            "authority; stock descriptor authority; effect-scale authority; "
            "component-probability authority; Pk authority; deterministic-fuze authority"
        )
    return (
        "copying document body, tables or figures into release artifacts; consuming "
        "document examples as benchmark results; source truth; runtime authority; "
        "stock descriptor authority; effect-scale authority; component-probability "
        "authority; Pk authority; deterministic-fuze authority"
    )


def _output_policy_for_payload(label: str) -> dict[str, Any]:
    copy_forbidden = [
        "payload_body_or_bulk_content",
        "numeric_tables_or_figures",
        "derived_calibration_values",
        "runtime_or_stock_descriptor_fields",
    ]
    if label == "BEC-O-V1.xlsx":
        copy_forbidden.extend(
            [
                "spreadsheet_formulas",
                "spreadsheet_cell_ranges",
                "spreadsheet_or_tool_output_tables",
            ]
        )

    return {
        "policy_status": POLICY_STATUS,
        "hash_allowed_outputs": [
            "retained_payload_file_sha256",
            "source_manifest_sha256",
            "rights_policy_gate_sha256",
            "future_selected_comparison_output_sha256_only_after_reviewer_admission",
        ],
        "copy_allowed_outputs": [
            "payload_filename",
            "payload_sha256",
            "content_type",
            "public_distribution_statement_locator_and_phrase_id",
            "rights_status",
            "allowed_use",
            "forbidden_use",
        ],
        "copy_forbidden_outputs": copy_forbidden,
        "consume_forbidden_outputs": [
            "source_payload_body_as_benchmark_input",
            "spreadsheet_or_tool_outputs_as_release_benchmark",
            "document_examples_as_release_benchmark",
            "comparison_outputs_without_selected_sha256_and_signoff",
            "effect_scale_authority",
            "component_failure_probability_authority",
            "pk_authority",
            "deterministic_fuze_authority",
            "stock_descriptor_authority",
            "runtime_authority",
        ],
        "current_comparison_outputs_admitted": False,
        "benchmark_consumption_allowed": False,
        "release_authority_allowed": False,
    }


def _payload_rights_row(
    *,
    manifest_row: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    path = _resolve_repo_path(str(manifest_row.get("relative_path", "")), repo_root)
    payload_exists = path.exists() and path.is_file()
    expected_sha256 = str(manifest_row.get("sha256", ""))
    actual_sha256 = _sha256_file(path) if payload_exists else ""
    hash_matches = bool(expected_sha256 and actual_sha256 == expected_sha256)
    content_type = str(manifest_row.get("content_type", "")) or _content_type_for_path(
        path
    )
    evidence = (
        _extract_rights_evidence(path, content_type)
        if payload_exists and hash_matches
        else {
            "extraction_status": "payload_missing_or_hash_mismatch_fail_closed",
            "statement_locator": "",
            "statement_detected": False,
            "statement_id": "",
            "has_distribution_statement_a_label": False,
            "has_public_release_phrase": False,
            "has_unlimited_distribution_phrase": False,
        }
    )
    statement_supported = bool(hash_matches and evidence["statement_detected"])
    label = str(manifest_row.get("source_artifact_label", ""))
    rights_status = (
        "public_distribution_statement_supported_rights_review_candidate"
        if statement_supported
        else "rights_review_public_distribution_statement_not_supported_fail_closed"
    )

    return {
        "requirement_id": manifest_row.get("requirement_id", ""),
        "artifact_id": manifest_row.get("artifact_id", ""),
        "source_id": manifest_row.get("source_id", ""),
        "source_artifact_label": label,
        "content_type": content_type,
        "relative_path": manifest_row.get("relative_path", ""),
        "payload_exists": payload_exists,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "hash_matches_expected": hash_matches,
        "payload_retention_status": (
            "retained_hash_matched" if hash_matches else "missing_or_hash_mismatch"
        ),
        "rights_statement_evidence": evidence,
        "rights_supported_by_public_distribution_statement": statement_supported,
        "rights_status": rights_status,
        "rights_release_grade_satisfied": False,
        "allowed_use": _allowed_use_for_payload(label),
        "forbidden_use": _forbidden_use_for_payload(label),
        "output_policy": _output_policy_for_payload(label),
        "release_consumption_allowed": False,
        "benchmark_consumed_for_release": False,
        "benchmark_consumption_status": manifest_row.get(
            "benchmark_consumption_status",
            "not_consumed_for_stage_b_release",
        ),
    }


def _release_signoff_fields() -> list[dict[str, str]]:
    return [
        {
            "field": "rights_reviewer_identity",
            "current_value": "missing",
            "required_value": "named independent rights reviewer or release owner",
        },
        {
            "field": "rights_review_decision",
            "current_value": "missing",
            "required_value": "release_reviewed or reviewer_approved_public_retention",
        },
        {
            "field": "allowed_output_policy_reviewer_identity",
            "current_value": "missing",
            "required_value": "named reviewer who freezes copy/hash/consume policy",
        },
        {
            "field": "allowed_output_policy_release_grade_status",
            "current_value": POLICY_STATUS,
            "required_value": "reviewer_frozen_release_grade or independently_reviewed_release_grade",
        },
        {
            "field": "selected_comparison_output_hash_manifest_sha256",
            "current_value": "missing",
            "required_value": "sha256 manifest for each admitted comparison/tool output",
        },
        {
            "field": "benchmark_consumption_signoff",
            "current_value": "missing",
            "required_value": "explicit consume-or-do-not-consume release decision",
        },
        {
            "field": "authority_boundary_signoff",
            "current_value": "missing",
            "required_value": "reviewer confirmation that no stock/runtime/Pk/fuze authority is released",
        },
    ]


def _blocking_conditions(
    *,
    all_payloads_retained: bool,
    all_rights_supported: bool,
) -> list[str]:
    blockers: list[str] = []
    if not all_payloads_retained:
        blockers.append("payload_retention_missing_or_hash_mismatch")
    if not all_rights_supported:
        blockers.append("public_distribution_statement_evidence_missing")
    blockers.extend(
        [
            "independent_rights_reviewer_signoff_missing",
            "allowed_output_policy_release_grade_signoff_missing",
            "selected_comparison_output_hash_manifest_missing",
            "benchmark_consumption_release_signoff_missing",
            "authority_boundary_signoff_missing",
        ]
    )
    return blockers


def _status_for_gate(
    *,
    all_payloads_retained: bool,
    all_rights_supported: bool,
) -> str:
    if not all_payloads_retained:
        return "blocked_payload_retention_incomplete_fail_closed"
    if not all_rights_supported:
        return "blocked_public_distribution_statement_support_incomplete_fail_closed"
    return "blocked_release_candidate_rights_supported_policy_fail_closed"


def generate_source_rights_output_policy_gate(
    *,
    repo_root: Path = REPO_ROOT,
    source_manifest_path: Path = DEFAULT_SOURCE_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    source_manifest = _read_json(source_manifest_path)
    payload_rows = [
        _payload_rights_row(manifest_row=row, repo_root=repo_root)
        for row in source_manifest.get("artifacts", [])
    ]
    all_payloads_retained = bool(payload_rows) and all(
        row["payload_exists"] and row["hash_matches_expected"] for row in payload_rows
    )
    all_rights_supported = bool(payload_rows) and all(
        row["rights_supported_by_public_distribution_statement"]
        for row in payload_rows
    )
    blockers = _blocking_conditions(
        all_payloads_retained=all_payloads_retained,
        all_rights_supported=all_rights_supported,
    )
    guards = _non_authoritative_guards()

    return {
        "package_id": PACKAGE_ID,
        "schema_version": SOURCE_RIGHTS_OUTPUT_POLICY_SCHEMA_VERSION,
        "status": _status_for_gate(
            all_payloads_retained=all_payloads_retained,
            all_rights_supported=all_rights_supported,
        ),
        "review_target": "res_001_source_rights_review_allowed_output_policy",
        "readiness_level": (
            "payload_retention_complete_public_distribution_supported_policy_"
            "candidate_frozen_release_grade_blocked"
            if all_payloads_retained and all_rights_supported
            else "source_rights_output_policy_fail_closed"
        ),
        "artifact_dir": _display_path(output_dir, repo_root),
        "source_payload_pack_manifest": {
            "relative_path": _display_path(source_manifest_path, repo_root),
            "schema_version": source_manifest.get("schema_version", ""),
            "status": source_manifest.get("status", ""),
            "sha256": _sha256_file(source_manifest_path)
            if source_manifest_path.exists()
            else "",
            "all_payloads_exist": source_manifest.get("all_payloads_exist", False),
            "all_payload_hashes_match": source_manifest.get(
                "all_payload_hashes_match",
                False,
            ),
            "rights_review_status": source_manifest.get(
                "rights_review_status",
                "missing",
            ),
            "allowed_output_policy_status": source_manifest.get(
                "allowed_output_policy_status",
                "missing",
            ),
        },
        "res_001_gate_result": {
            "gate_result": "blocked",
            "release_grade_satisfied": False,
            "payload_retention_complete": all_payloads_retained,
            "payload_hashes_match": all_payloads_retained,
            "rights_supported_by_public_distribution_statement": all_rights_supported,
            "release_grade_rights_reviewed": False,
            "allowed_output_policy_frozen": True,
            "allowed_output_policy_release_grade_satisfied": False,
            "comparison_outputs_admitted": False,
            "benchmark_consumption_release_grade_satisfied": False,
            "blocking_conditions": blockers,
        },
        "rights_review_summary": {
            "rights_review_status": (
                "public_distribution_statement_supported_candidate_not_signed_off"
                if all_rights_supported
                else "public_distribution_statement_support_incomplete"
            ),
            "public_distribution_statement_supported_payload_count": sum(
                1
                for row in payload_rows
                if row["rights_supported_by_public_distribution_statement"]
            ),
            "required_payload_count": len(payload_rows),
            "release_grade_rights_review_satisfied": False,
            "release_grade_blocker": "independent_rights_reviewer_signoff_missing",
        },
        "allowed_output_policy": {
            "policy_id": POLICY_ID,
            "policy_status": POLICY_STATUS,
            "policy_frozen_by_this_gate": True,
            "release_grade_satisfied": False,
            "current_selected_comparison_output_hashes": [],
            "allowed_hash_outputs": [
                "retained_payload_file_sha256",
                "source_manifest_sha256",
                "rights_policy_gate_sha256",
                "future_selected_comparison_output_sha256_only_after_reviewer_admission",
            ],
            "forbidden_copy_outputs": [
                "source_payload_body_or_bulk_content",
                "document_numeric_tables_or_figures",
                "spreadsheet_formulas_or_cell_ranges",
                "spreadsheet_tool_output_tables",
                "comparison_output_values_without_review_admission",
                "stock_descriptor_fields",
                "runtime_authority_fields",
            ],
            "forbidden_consume_outputs": [
                "source_payloads_as_release_benchmark_inputs",
                "spreadsheet_or_tool_outputs_as_release_benchmark_without_signoff",
                "document_examples_as_release_benchmark",
                "comparison_outputs_without_selected_sha256_and_signoff",
                "effect_scale_authority",
                "component_failure_probability_authority",
                "pk_authority",
                "deterministic_fuze_authority",
            ],
        },
        "payload_rights_inventory": payload_rows,
        "required_release_signoff_fields": _release_signoff_fields(),
        "remaining_release_grade_paths": {
            "RES-001": [
                "record independent rights reviewer identity and decision for the retained DENIX payloads",
                "upgrade allowed-output policy from release-candidate fail-closed to reviewer-frozen release-grade",
                "pin selected comparison-output hashes before any comparison output is admitted",
                "record benchmark-consumption signoff, including explicit do-not-consume decisions if outputs stay excluded",
                "record authority-boundary signoff with all stock/effect/component/Pk/fuze guards false",
            ]
        },
        "explicit_boundaries": [
            "payload retention is complete only because retained files exist and sha256 values match",
            "public distribution statements can support rights review but are not reviewer signoff",
            "allowed-output policy is frozen fail-closed and not release-grade",
            "hashes may be recorded for retained payloads and future admitted comparison outputs",
            "payload bodies, spreadsheet outputs and comparison values cannot be copied or consumed by this gate",
            "no stock, runtime, effect-scale, component-probability, Pk or deterministic-fuze authority is released",
        ],
        "non_authoritative_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
    }


def _retained_manifest(
    *,
    artifact: dict[str, Any],
    artifact_path: Path,
    artifact_text: str,
    source_manifest_path: Path,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "package_id": PACKAGE_ID,
        "schema_version": SOURCE_RIGHTS_OUTPUT_POLICY_MANIFEST_SCHEMA_VERSION,
        "status": artifact["status"],
        "artifact_dir": _display_path(output_dir, repo_root),
        "source_rights_output_policy_gate": {
            "filename": RIGHTS_POLICY_ARTIFACT_FILENAME,
            "relative_path": _display_path(artifact_path, repo_root),
            "sha256": _sha256_file(artifact_path),
            "content_sha256": _sha256_text(artifact_text.rstrip("\n")),
            "schema_version": SOURCE_RIGHTS_OUTPUT_POLICY_SCHEMA_VERSION,
        },
        "source_payload_pack_manifest": artifact["source_payload_pack_manifest"],
        "payload_rights_inventory": [
            {
                "requirement_id": row["requirement_id"],
                "source_artifact_label": row["source_artifact_label"],
                "relative_path": row["relative_path"],
                "sha256": row["actual_sha256"],
                "hash_matches_expected": row["hash_matches_expected"],
                "rights_status": row["rights_status"],
                "allowed_use": row["allowed_use"],
                "forbidden_use": row["forbidden_use"],
                "policy_status": row["output_policy"]["policy_status"],
                "benchmark_consumed_for_release": row[
                    "benchmark_consumed_for_release"
                ],
            }
            for row in artifact["payload_rights_inventory"]
        ],
        "res_001_gate_result": artifact["res_001_gate_result"],
        "required_release_signoff_fields": artifact["required_release_signoff_fields"],
        "source_manifest_ref": _display_path(source_manifest_path, repo_root),
        "non_authoritative_guards": artifact["non_authoritative_guards"],
    }


def write_retained_source_rights_output_policy_gate(
    *,
    repo_root: Path = REPO_ROOT,
    source_manifest_path: Path = DEFAULT_SOURCE_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = generate_source_rights_output_policy_gate(
        repo_root=repo_root,
        source_manifest_path=source_manifest_path,
        output_dir=output_dir,
    )
    artifact_path = output_dir / RIGHTS_POLICY_ARTIFACT_FILENAME
    artifact_text = _canonical_json(artifact) + "\n"
    artifact_path.write_text(artifact_text, encoding="utf-8")

    manifest = _retained_manifest(
        artifact=artifact,
        artifact_path=artifact_path,
        artifact_text=artifact_text,
        source_manifest_path=source_manifest_path,
        repo_root=repo_root,
        output_dir=output_dir,
    )
    manifest_path = output_dir / RETAINED_MANIFEST_FILENAME
    manifest_text = _canonical_json(manifest) + "\n"
    manifest_path.write_text(manifest_text, encoding="utf-8")

    artifact["source_rights_output_policy_gate_sha256"] = _sha256_file(artifact_path)
    artifact["retained_manifest_ref"] = _display_path(manifest_path, repo_root)
    artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the A2 RES-001 source rights and allowed-output policy gate."
        )
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=DEFAULT_SOURCE_MANIFEST,
        help="Path to source_artifact_pack_manifest.json from the retained payload pack.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for retained source rights/output policy artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--write-retained-artifacts",
        action="store_true",
        help="Write source_rights_output_policy_gate.json and manifest.json.",
    )
    args = parser.parse_args(argv)

    if args.write_retained_artifacts:
        payload = write_retained_source_rights_output_policy_gate(
            source_manifest_path=args.source_manifest,
            output_dir=args.output_dir,
        )
    else:
        payload = generate_source_rights_output_policy_gate(
            source_manifest_path=args.source_manifest,
            output_dir=args.output_dir,
        )

    text = _canonical_json(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
