#!/usr/bin/env python3
"""Build the A2 source payload pack for RES-001/RES-002 evidence.

This pack is deliberately fail-closed. It can retain already-present public
payload files and record their checksums, but it does not download sources,
grant rights review, admit comparison outputs, or release any authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_provenance_identity_review_gate as review_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_release_provenance_closeout_gate as closeout_gate,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
SOURCE_PAYLOAD_PACK_SCHEMA_VERSION = "a2.source_payload_pack.v1"
SOURCE_ARTIFACT_PACK_SCHEMA_VERSION = (
    "a2.provenance_identity_retained_source_artifact_pack.v1"
)
RETAINED_MANIFEST_SCHEMA_VERSION = "a2.source_payload_pack_retained_manifest.v1"

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
DEFAULT_OUTPUT_DIR = (
    PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
)

SOURCE_PAYLOAD_PACK_FILENAME = "source_payload_pack.json"
SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME = "source_artifact_pack_manifest.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

DOC_REFS = {
    "artifact_pin_manifest": (
        PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_manifest": PACKAGE_DIR / "validation_manifest_draft_blastfrag_20260528.zh.md",
    "validation_report": PACKAGE_DIR / "validation_report_draft.zh.md",
    "release_provenance_closeout_doc": (
        PACKAGE_DIR / "validation_release_provenance_closeout_gate_20260531.zh.md"
    ),
    "provenance_identity_review_doc": (
        PACKAGE_DIR / "validation_provenance_identity_review_gate_20260531.zh.md"
    ),
    "vps_source_ledger": (
        PACKAGE_DIR
        / "../../data_collection/vps_blast_fragmentation_methods/source_ledger.zh.md"
    ).resolve(),
    "vps_validation_gap_update": (
        PACKAGE_DIR
        / "../../data_collection/vps_blast_fragmentation_methods/validation_gap_update_20260528.zh.md"
    ).resolve(),
}
SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "source_rights_output_policy_20260531"
    / "source_rights_output_policy_gate.json"
)
MECHANISM_COMPARISON_HASHES_PATH = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "mechanism_comparison_hashes_20260531"
    / "mechanism_comparison_hashes.json"
)

PIN_TABLE_COLUMNS = [
    "artifact_id",
    "source_id",
    "source_tier",
    "source_ref",
    "access_status",
    "artifact_status",
    "sha256",
    "retention_ref",
    "consumption_status",
    "candidate_use",
    "authority_boundary",
    "residuals",
]

PAYLOAD_METADATA = {
    "TP-20 PDF": {
        "canonical_filename": "TP-20.pdf",
        "content_type": "application/pdf",
        "search_hints": (
            "tp-20",
            "tp20",
            "202c",
            "blast-effects-computer-open",
            "ddesb-blast-effects-computer",
        ),
        "source_payload_role": "blast_effects_computer_documentation",
    },
    "BEC-O-V1.xlsx": {
        "canonical_filename": "BEC-O-V1.xlsx",
        "content_type": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        "search_hints": ("bec-o-v1.xlsx", "bec-o", "bec_o"),
        "source_payload_role": "blast_effects_computer_spreadsheet_tool",
    },
    "TP-21 PDF": {
        "canonical_filename": "TP-21.pdf",
        "content_type": "application/pdf",
        "search_hints": ("tp-21", "tp21", "171130", "revision-22c"),
        "source_payload_role": "explosion_produced_debris_documentation",
    },
}

EXCLUDED_DISCOVERY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv.pre_rebuild_20260512",
    "__pycache__",
    "build",
    "dist",
    "game",
}

RELEASE_ALLOWED_OUTPUT_POLICY_STATUSES = {
    "release_grade_frozen",
    "reviewer_frozen_release_grade",
    "independently_reviewed_release_grade",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_text_if_exists(path: Path) -> str:
    return _read_text(path) if path.exists() else ""


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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


def _strip_cell(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _split_markdown_row(line: str) -> list[str]:
    return [_strip_cell(cell) for cell in line.strip().strip("|").split("|")]


def _extract_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _split_markdown_row(line)
        if len(cells) >= 2 and cells[0] == field:
            return cells[1].strip()
    return ""


def _parse_artifact_pin_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        cells = _split_markdown_row(line) if line.startswith("|") else []
        if len(cells) < len(PIN_TABLE_COLUMNS):
            continue
        if not cells[0].startswith("PIN-"):
            continue
        rows.append(dict(zip(PIN_TABLE_COLUMNS, cells[: len(PIN_TABLE_COLUMNS)])))
    return rows


def _verified_denix_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["artifact_id"] in {"PIN-BFM-001", "PIN-BFM-002"}
        and "verified_candidate_artifact" in row["artifact_status"]
    ]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "artifact"


def _payload_label_for_row(row: dict[str, str]) -> str:
    if row["artifact_id"] == "PIN-BFM-002":
        return "TP-21 PDF"
    return row["source_ref"]


def _normal_payload_label(label: str) -> str:
    normalized = label.strip()
    if normalized.lower() in {"tp-20 pdf", "tp20 pdf"}:
        return "TP-20 PDF"
    if normalized.lower() in {"bec-o-v1.xlsx", "bec-o v1 xlsx"}:
        return "BEC-O-V1.xlsx"
    if "TP-21" in normalized or "tp-21" in normalized.lower():
        return "TP-21 PDF"
    return normalized


def _source_artifact_requirements(
    verified_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    requirements: list[dict[str, str]] = []
    for row in verified_rows:
        named_hashes = re.findall(
            r"([^:;|]+):\s*([a-f0-9]{64})",
            row["sha256"],
        )
        if named_hashes:
            for label, sha256 in named_hashes:
                normalized_label = _normal_payload_label(label)
                requirements.append(
                    {
                        "requirement_id": (
                            f"{row['artifact_id']}:{_slug(normalized_label)}"
                        ),
                        "artifact_id": row["artifact_id"],
                        "source_id": row["source_id"],
                        "source_artifact_label": normalized_label,
                        "expected_sha256": sha256,
                        "source_ref": row["source_ref"],
                        "source_tier": row["source_tier"],
                        "pin_artifact_status": row["artifact_status"],
                        "pin_consumption_status": row["consumption_status"],
                        "candidate_use": row["candidate_use"],
                        "authority_boundary": row["authority_boundary"],
                    }
                )
            continue

        hashes = re.findall(r"\b[a-f0-9]{64}\b", row["sha256"])
        if hashes:
            label = _payload_label_for_row(row)
            normalized_label = _normal_payload_label(label)
            requirements.append(
                {
                    "requirement_id": f"{row['artifact_id']}:{_slug(normalized_label)}",
                    "artifact_id": row["artifact_id"],
                    "source_id": row["source_id"],
                    "source_artifact_label": normalized_label,
                    "expected_sha256": hashes[0],
                    "source_ref": row["source_ref"],
                    "source_tier": row["source_tier"],
                    "pin_artifact_status": row["artifact_status"],
                    "pin_consumption_status": row["consumption_status"],
                    "candidate_use": row["candidate_use"],
                    "authority_boundary": row["authority_boundary"],
                }
            )
    return requirements


def _metadata_for_requirement(requirement: dict[str, str]) -> dict[str, Any]:
    return PAYLOAD_METADATA.get(
        requirement["source_artifact_label"],
        {
            "canonical_filename": f"{_slug(requirement['source_artifact_label'])}.bin",
            "content_type": "application/octet-stream",
            "search_hints": (_slug(requirement["source_artifact_label"]),),
            "source_payload_role": "source_payload",
        },
    )


def _target_payload_path(
    *,
    requirement: dict[str, str],
    output_dir: Path,
) -> Path:
    metadata = _metadata_for_requirement(requirement)
    return output_dir / "payloads" / str(metadata["canonical_filename"])


def _matches_search_hints(filename: str, hints: tuple[str, ...]) -> bool:
    lower = filename.lower()
    return any(hint.lower() in lower for hint in hints)


def _matches_expected_suffix(path: Path, metadata: dict[str, Any]) -> bool:
    expected_suffix = Path(str(metadata["canonical_filename"])).suffix.lower()
    return not expected_suffix or path.suffix.lower() == expected_suffix


def _iter_discovery_files(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for root, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in EXCLUDED_DISCOVERY_DIRS
        ]
        current = Path(root)
        for filename in filenames:
            paths.append(current / filename)
    return paths


def _discover_payload_candidates(
    *,
    requirement: dict[str, str],
    repo_root: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    metadata = _metadata_for_requirement(requirement)
    hints = tuple(str(value) for value in metadata["search_hints"])
    expected_sha256 = requirement["expected_sha256"]
    candidates: dict[str, dict[str, Any]] = {}

    target_path = _target_payload_path(requirement=requirement, output_dir=output_dir)
    explicit_candidates = [target_path, repo_root / ".playwright-mcp" / target_path.name]
    for path in explicit_candidates:
        if not path.exists() or not path.is_file():
            continue
        actual_sha256 = _sha256_file(path)
        candidates[_display_path(path, repo_root)] = {
            "relative_path": _display_path(path, repo_root),
            "sha256": actual_sha256,
            "hash_matches_expected": actual_sha256 == expected_sha256,
            "candidate_origin": (
                "canonical_retained_payload"
                if path == target_path
                else "workspace_existing_payload"
            ),
        }

    for path in _iter_discovery_files(repo_root):
        if not _matches_search_hints(path.name, hints):
            continue
        if not _matches_expected_suffix(path, metadata):
            continue
        if not path.is_file():
            continue
        actual_sha256 = _sha256_file(path)
        candidates.setdefault(
            _display_path(path, repo_root),
            {
                "relative_path": _display_path(path, repo_root),
                "sha256": actual_sha256,
                "hash_matches_expected": actual_sha256 == expected_sha256,
                "candidate_origin": "workspace_search_match",
            },
        )

    return sorted(
        candidates.values(),
        key=lambda row: (
            not bool(row["hash_matches_expected"]),
            str(row["relative_path"]),
        ),
    )


def _copy_payload_if_available(
    *,
    requirement: dict[str, str],
    repo_root: Path,
    output_dir: Path,
) -> None:
    target_path = _target_payload_path(requirement=requirement, output_dir=output_dir)
    if target_path.exists() and _sha256_file(target_path) == requirement["expected_sha256"]:
        return

    candidates = _discover_payload_candidates(
        requirement=requirement,
        repo_root=repo_root,
        output_dir=output_dir,
    )
    matching_candidates = [
        row for row in candidates if row["hash_matches_expected"] is True
    ]
    if not matching_candidates:
        return

    source_path = repo_root / matching_candidates[0]["relative_path"]
    if source_path.resolve() == target_path.resolve():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _payload_inventory_row(
    *,
    requirement: dict[str, str],
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    metadata = _metadata_for_requirement(requirement)
    target_path = _target_payload_path(requirement=requirement, output_dir=output_dir)
    candidates = _discover_payload_candidates(
        requirement=requirement,
        repo_root=repo_root,
        output_dir=output_dir,
    )
    target_exists = target_path.exists()
    actual_sha256 = _sha256_file(target_path) if target_exists else ""
    hash_matches = bool(actual_sha256 and actual_sha256 == requirement["expected_sha256"])
    retained = target_exists and hash_matches
    retention_status = (
        "candidate_retained_not_release_reviewed"
        if retained
        else "missing_required_payload"
    )
    rights_status = (
        "official_public_candidate_only_rights_not_release_reviewed"
        if retained
        else "missing_payload_rights_not_reviewed"
    )
    return {
        "requirement_id": requirement["requirement_id"],
        "artifact_id": requirement["artifact_id"],
        "source_id": requirement["source_id"],
        "source_artifact_label": requirement["source_artifact_label"],
        "source_payload_role": metadata["source_payload_role"],
        "content_type": metadata["content_type"],
        "expected_sha256": requirement["expected_sha256"],
        "retained_relative_path": _display_path(target_path, repo_root),
        "payload_exists": target_exists,
        "actual_sha256": actual_sha256,
        "hash_matches_expected": hash_matches,
        "retained_for_pack": retained,
        "retention_status": retention_status,
        "rights_status": rights_status,
        "allowed_use": "candidate_provenance_and_benchmark_design_reference_only",
        "forbidden_use": (
            "source truth, runtime authority, stock descriptor authority, "
            "effect-scale authority, component-probability authority, Pk authority, "
            "or deterministic-fuze authority"
        ),
        "pin_artifact_status": requirement["pin_artifact_status"],
        "pin_consumption_status": requirement["pin_consumption_status"],
        "benchmark_consumed_for_release": False,
        "benchmark_consumption_status": requirement["pin_consumption_status"],
        "available_candidates": candidates,
    }


def _missing_payloads(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in inventory:
        if row["retained_for_pack"]:
            continue
        reason = (
            "payload_file_missing"
            if not row["payload_exists"]
            else "payload_sha256_mismatch"
        )
        missing.append(
            {
                "requirement_id": row["requirement_id"],
                "artifact_id": row["artifact_id"],
                "source_id": row["source_id"],
                "source_artifact_label": row["source_artifact_label"],
                "expected_relative_path": row["retained_relative_path"],
                "expected_sha256": row["expected_sha256"],
                "actual_sha256": row["actual_sha256"],
                "missing_reason": reason,
                "required_fields_before_release": [
                    "relative_path",
                    "sha256",
                    "rights_status",
                    "retention_status",
                    "allowed_use",
                    "benchmark_consumption_status",
                ],
            }
        )
    return missing


def _comparison_hash_hits(texts: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    pattern = re.compile(
        r"\bcomparison[-_ ]output[-_ ]sha256\b[^a-f0-9]{0,80}([a-f0-9]{64})",
        re.IGNORECASE,
    )
    for index, text in enumerate(texts):
        for match in pattern.finditer(text):
            hits.append(
                {
                    "source_index": str(index),
                    "comparison_output_sha256": match.group(1),
                }
            )
    return hits


def _rights_allowed_output_policy_status(
    *,
    pin_text: str,
    inventory: list[dict[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    policy_status = _extract_field(pin_text, "allowed_output_policy_status") or "missing"
    retained_payload_count = sum(1 for row in inventory if row["retained_for_pack"])
    all_payloads_retained = retained_payload_count == len(inventory) and bool(inventory)
    rights_policy_gate = (
        _read_json_if_exists(SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH)
        if all_payloads_retained
        else None
    )
    if rights_policy_gate is not None:
        gate_result = rights_policy_gate["res_001_gate_result"]
        policy = rights_policy_gate["allowed_output_policy"]
        rights_summary = rights_policy_gate["rights_review_summary"]
        return {
            "rights_review_status": rights_summary["rights_review_status"],
            "rights_release_grade_satisfied": rights_summary[
                "release_grade_rights_review_satisfied"
            ],
            "allowed_output_policy_status": policy["policy_status"],
            "allowed_output_policy_gate_ref": _display_path(
                SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH,
                repo_root,
            ),
            "allowed_output_policy_gate_sha256": _sha256_file(
                SOURCE_RIGHTS_OUTPUT_POLICY_GATE_PATH
            ),
            "allowed_output_policy_frozen": gate_result[
                "allowed_output_policy_frozen"
            ],
            "allowed_output_release_grade_satisfied": gate_result[
                "allowed_output_policy_release_grade_satisfied"
            ],
            "candidate_public_distribution_supported": gate_result[
                "rights_supported_by_public_distribution_statement"
            ],
            "allowed_output_boundary": (
                "source rights/output policy gate freezes hash-only allowed "
                "outputs and forbids copying source bodies, spreadsheet cells, "
                "comparison values or runtime authority fields"
            ),
            "retained_payloads_with_candidate_rights": [
                row["requirement_id"] for row in inventory if row["retained_for_pack"]
            ],
            "payloads_without_release_rights_review": [
                row["requirement_id"] for row in inventory
            ],
            "release_grade_blockers": list(gate_result["blocking_conditions"]),
        }
    rights_review_status = (
        "candidate_only_not_release_reviewed"
        if retained_payload_count
        else "missing_payload_rights_review"
    )
    return {
        "rights_review_status": rights_review_status,
        "rights_release_grade_satisfied": False,
        "allowed_output_policy_status": policy_status,
        "allowed_output_release_grade_satisfied": (
            policy_status in RELEASE_ALLOWED_OUTPUT_POLICY_STATUSES
            and all_payloads_retained
        ),
        "allowed_output_boundary": (
            "spreadsheet/tool outputs and comparison outputs are not retained, "
            "not source truth, not benchmark outputs, and not runtime authority "
            "unless a later reviewer-frozen policy explicitly admits them"
        ),
        "retained_payloads_with_candidate_rights": [
            row["requirement_id"] for row in inventory if row["retained_for_pack"]
        ],
        "payloads_without_release_rights_review": [
            row["requirement_id"] for row in inventory
        ],
    }


def _benchmark_consumption_trace(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    explicit_non_consumed_artifact_ids = sorted(
        {
            row["artifact_id"]
            for row in inventory
            if row["pin_consumption_status"] == "not_consumed_for_stage_b_release"
        }
    )
    release_consumed_artifact_ids = sorted(
        {
            row["artifact_id"]
            for row in inventory
            if row["benchmark_consumed_for_release"] is True
        }
    )
    return {
        "benchmark_consumption_chain_status": (
            "explicit_non_consumption_only_release_chain_missing"
        ),
        "explicit_non_consumed_artifact_ids": explicit_non_consumed_artifact_ids,
        "release_consumed_artifact_ids": release_consumed_artifact_ids,
        "retained_payloads_consumed_for_release": [],
        "benchmark_consumption_release_grade_satisfied": False,
        "trace_note": (
            "Retained payloads remain candidate provenance/design references only; "
            "the Stage B release path still records DENIX rows as not consumed."
        ),
    }


def _comparison_output_hash_status(
    *,
    enable_retained_artifact_integration: bool,
    repo_root: Path,
) -> dict[str, Any]:
    comparison_hash_artifact = (
        _read_json_if_exists(MECHANISM_COMPARISON_HASHES_PATH)
        if enable_retained_artifact_integration
        else None
    )
    if comparison_hash_artifact is not None:
        beco = comparison_hash_artifact["beco_workbook"]
        selected_hashes = [
            {
                "comparison_id": row["comparison_id"],
                "source_id": row["source_id"],
                "source_artifact_label": row["source_artifact_label"],
                "residual_id": row["residual_id"],
                "comparison_output_sha256": row["comparison_output_sha256"],
                "calculation_source": row["calculation_source"],
                "comparison_hash_is_calibration": row[
                    "comparison_hash_is_calibration"
                ],
                "benchmark_consumed_for_release": row[
                    "benchmark_consumed_for_release"
                ],
                "hash_preimage_disclosure": row["hash_preimage_disclosure"],
            }
            for row in beco.get("selected_comparison_hashes", [])
        ]
        return {
            "comparison_output_hash_status": (
                "partial_hash_manifest_present_release_review_blocked"
            ),
            "mechanism_comparison_hashes_ref": _display_path(
                MECHANISM_COMPARISON_HASHES_PATH,
                repo_root,
            ),
            "mechanism_comparison_hashes_sha256": _sha256_file(
                MECHANISM_COMPARISON_HASHES_PATH
            ),
            "current_gate_results": comparison_hash_artifact["current_gate_results"],
            "selected_comparison_output_hashes": selected_hashes,
            "selected_beco_cached_output_hash_count": len(selected_hashes),
            "tp21_selected_debris_output_hashes_present": comparison_hash_artifact[
                "comparison_hash_decision"
            ]["tp21_selected_debris_output_hashes_present"],
            "comparison_outputs_retained": bool(selected_hashes),
            "comparison_output_release_grade_satisfied": comparison_hash_artifact[
                "comparison_hash_decision"
            ]["release_grade_validated"],
            "benchmark_consumed_for_release": comparison_hash_artifact[
                "comparison_hash_decision"
            ]["benchmark_consumed_for_release"],
            "candidate_result_hashes_are_not_comparison_output_hashes": True,
            "release_grade_blockers": [
                "reviewed spreadsheet execution/recalculation missing",
                "tolerance and allowed-output policy signoff missing",
                "TP-21 selected debris comparison outputs missing",
                "benchmark-consumption chain still fail-closed",
            ],
        }
    texts = [
        _read_text_if_exists(path)
        for path in (
            DOC_REFS["validation_manifest"],
            DOC_REFS["validation_report"],
            DOC_REFS["release_provenance_closeout_doc"],
            DOC_REFS["provenance_identity_review_doc"],
        )
    ]
    hits = _comparison_hash_hits(texts)
    return {
        "comparison_output_hash_status": (
            "selected_comparison_output_hashes_present"
            if hits
            else "missing_selected_comparison_output_hashes"
        ),
        "selected_comparison_output_hashes": hits,
        "comparison_outputs_retained": False,
        "candidate_result_hashes_are_not_comparison_output_hashes": True,
        "comparison_output_release_grade_satisfied": False,
    }


def _review_gate_summary(repo_root: Path) -> dict[str, Any]:
    artifact = review_gate.generate_provenance_identity_review_gate(
        repo_root=repo_root
    )
    closeout_artifact = closeout_gate.generate_release_provenance_closeout_gate(
        repo_root=repo_root
    )
    return {
        "provenance_identity_review_status": artifact["status"],
        "provenance_identity_residual_gate_results": artifact[
            "residual_gate_results"
        ],
        "release_provenance_closeout_status": closeout_artifact["status"],
        "release_closeout_ready": closeout_artifact["release_closeout_decision"][
            "release_closeout_ready"
        ],
        "release_closeout_blocked": closeout_artifact["release_closeout_decision"][
            "release_closeout_blocked"
        ],
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


def _status_for_inventory(inventory: list[dict[str, Any]]) -> str:
    retained_count = sum(1 for row in inventory if row["retained_for_pack"])
    if retained_count == 0:
        return "blocked_missing_required_source_payloads"
    if retained_count < len(inventory):
        return "partial_non_authoritative_source_payload_pack"
    return "partial_payloads_retained_release_review_blocked"


def generate_source_payload_pack(
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    copy_available_payloads: bool = False,
) -> dict[str, Any]:
    pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
    rows = _parse_artifact_pin_rows(pin_text)
    verified_rows = _verified_denix_rows(rows)
    requirements = _source_artifact_requirements(verified_rows)

    if copy_available_payloads:
        for requirement in requirements:
            _copy_payload_if_available(
                requirement=requirement,
                repo_root=repo_root,
                output_dir=output_dir,
            )

    inventory = [
        _payload_inventory_row(
            requirement=requirement,
            repo_root=repo_root,
            output_dir=output_dir,
        )
        for requirement in requirements
    ]
    retained_inventory = [row for row in inventory if row["retained_for_pack"]]
    missing_payloads = _missing_payloads(inventory)
    all_payload_hashes_match = all(
        row["hash_matches_expected"] for row in retained_inventory
    )
    retained_count = len(retained_inventory)
    status = _status_for_inventory(inventory)
    guards = _non_authoritative_guards()

    rights_policy_status = _rights_allowed_output_policy_status(
        pin_text=pin_text,
        inventory=inventory,
        repo_root=repo_root,
    )
    benchmark_trace = _benchmark_consumption_trace(inventory)
    comparison_status = _comparison_output_hash_status(
        enable_retained_artifact_integration=(
            bool(inventory)
            and retained_count == len(inventory)
            and all_payload_hashes_match
        ),
        repo_root=repo_root,
    )

    res_001_blockers = []
    if missing_payloads:
        res_001_blockers.append("required_source_payloads_missing_or_mismatched")
    if not rights_policy_status["rights_release_grade_satisfied"]:
        res_001_blockers.append("release_rights_review_missing")
    if not rights_policy_status["allowed_output_release_grade_satisfied"]:
        res_001_blockers.append("allowed_output_policy_not_release_frozen")
    if not benchmark_trace["benchmark_consumption_release_grade_satisfied"]:
        res_001_blockers.append("benchmark_consumption_release_chain_missing")
    if not comparison_status["comparison_output_release_grade_satisfied"]:
        if comparison_status["selected_comparison_output_hashes"]:
            res_001_blockers.append("selected_comparison_output_hashes_not_release_grade")
        else:
            res_001_blockers.append("selected_comparison_output_hash_missing")

    return {
        "package_id": PACKAGE_ID,
        "schema_version": SOURCE_PAYLOAD_PACK_SCHEMA_VERSION,
        "status": status,
        "review_target": "res_001_source_payload_pack_for_res_002_release_identity",
        "readiness_level": "source_payload_inventory_partial_release_grade_blocked",
        "artifact_dir": _display_path(output_dir, repo_root),
        "source_payload_pack_decision": {
            "source_payload_pack_closed": False,
            "source_payload_pack_partial": retained_count > 0,
            "source_payload_pack_blocked": retained_count == 0,
            "required_payload_count": len(inventory),
            "retained_payload_count": retained_count,
            "missing_payload_count": len(missing_payloads),
            "all_required_payloads_retained": (
                bool(inventory) and retained_count == len(inventory)
            ),
            "all_retained_payload_hashes_match": all_payload_hashes_match,
            "release_grade_rights_reviewed": False,
            "authority_release_included": False,
        },
        "residual_gate_results": {
            "RES-001": "blocked",
            "RES-002": "blocked",
        },
        "res_001_gate_result": {
            "gate_result": "blocked",
            "source_payload_pack_status": status,
            "release_grade_satisfied": False,
            "blocking_conditions": res_001_blockers,
        },
        "res_002_consumption_note": {
            "release_identity_consumable_evidence": retained_count > 0,
            "release_identity_closed_by_this_pack": False,
            "reason": (
                "source payload evidence can be consumed by a later RES-002 "
                "identity lane, but clean release identity and reviewer signoff "
                "are outside this pack"
            ),
        },
        "source_requirements": requirements,
        "retained_payload_inventory": retained_inventory,
        "missing_payloads": missing_payloads,
        "all_payload_inventory": inventory,
        "rights_allowed_output_policy_status": rights_policy_status,
        "benchmark_consumption_trace": benchmark_trace,
        "comparison_output_hash_status": comparison_status,
        "review_gate_summary": _review_gate_summary(repo_root),
        "source_artifact_pack_manifest_ref": _display_path(
            output_dir / SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME,
            repo_root,
        ),
        "explicit_boundaries": [
            "do not use this pack as a stock descriptor",
            "do not treat retained payloads as benchmark outputs",
            "do not treat spreadsheet/tool outputs as source truth",
            "do not release effect-scale, component-probability, Pk, or deterministic-fuze authority",
        ],
        "non_authoritative_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
    }


def _source_artifact_pack_manifest(
    *,
    artifact: dict[str, Any],
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for row in artifact["all_payload_inventory"]:
        artifacts.append(
            {
                "requirement_id": row["requirement_id"],
                "artifact_id": row["artifact_id"],
                "source_id": row["source_id"],
                "source_artifact_label": row["source_artifact_label"],
                "relative_path": row["retained_relative_path"],
                "sha256": row["expected_sha256"],
                "actual_sha256": row["actual_sha256"],
                "payload_exists": row["payload_exists"],
                "hash_matches_expected": row["hash_matches_expected"],
                "retention_status": row["retention_status"],
                "rights_status": row["rights_status"],
                "allowed_use": row["allowed_use"],
                "benchmark_consumption_status": row["benchmark_consumption_status"],
                "benchmark_consumed_for_release": row["benchmark_consumed_for_release"],
                "forbidden_use": row["forbidden_use"],
            }
        )

    manifest = {
        "package_id": PACKAGE_ID,
        "schema_version": SOURCE_ARTIFACT_PACK_SCHEMA_VERSION,
        "status": artifact["status"],
        "artifact_dir": _display_path(output_dir, repo_root),
        "manifest_exists": True,
        "source_payloads_retained": bool(artifact["retained_payload_inventory"]),
        "required_payload_count": artifact["source_payload_pack_decision"][
            "required_payload_count"
        ],
        "retained_payload_count": artifact["source_payload_pack_decision"][
            "retained_payload_count"
        ],
        "all_payloads_exist": artifact["source_payload_pack_decision"][
            "all_required_payloads_retained"
        ],
        "all_payload_hashes_match": (
            not artifact["missing_payloads"]
            and artifact["source_payload_pack_decision"][
                "all_retained_payload_hashes_match"
            ]
        ),
        "rights_review_status": (
            artifact["rights_allowed_output_policy_status"]["rights_review_status"]
        ),
        "allowed_output_policy_status": (
            artifact["rights_allowed_output_policy_status"][
                "allowed_output_policy_status"
            ]
        ),
        "benchmark_consumption_chain_status": (
            artifact["benchmark_consumption_trace"][
                "benchmark_consumption_chain_status"
            ]
        ),
        "comparison_output_hash_status": (
            artifact["comparison_output_hash_status"]["comparison_output_hash_status"]
        ),
        "selected_beco_cached_output_hash_count": artifact[
            "comparison_output_hash_status"
        ].get("selected_beco_cached_output_hash_count", 0),
        "comparison_output_release_grade_satisfied": artifact[
            "comparison_output_hash_status"
        ]["comparison_output_release_grade_satisfied"],
        "artifacts": artifacts,
        "non_authoritative_guards": artifact["non_authoritative_guards"],
    }
    return manifest


def write_source_payload_pack(
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    copy_available_payloads: bool = True,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = generate_source_payload_pack(
        repo_root=repo_root,
        output_dir=output_dir,
        copy_available_payloads=copy_available_payloads,
    )

    artifact_path = output_dir / SOURCE_PAYLOAD_PACK_FILENAME
    artifact_text = _canonical_json(artifact) + "\n"
    artifact_path.write_text(artifact_text, encoding="utf-8")

    source_manifest = _source_artifact_pack_manifest(
        artifact=artifact,
        repo_root=repo_root,
        output_dir=output_dir,
    )
    source_manifest_path = output_dir / SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
    source_manifest_text = _canonical_json(source_manifest) + "\n"
    source_manifest_path.write_text(source_manifest_text, encoding="utf-8")

    retained_manifest = {
        "package_id": PACKAGE_ID,
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "status": artifact["status"],
        "artifact_dir": _display_path(output_dir, repo_root),
        "retention_scope": "res_001_source_payload_candidate_pack_non_authoritative",
        "source_payload_pack_artifact": {
            "filename": SOURCE_PAYLOAD_PACK_FILENAME,
            "relative_path": _display_path(artifact_path, repo_root),
            "sha256": _sha256_file(artifact_path),
            "content_sha256": _sha256_text(artifact_text.rstrip("\n")),
            "schema_version": SOURCE_PAYLOAD_PACK_SCHEMA_VERSION,
        },
        "source_artifact_pack_manifest": {
            "filename": SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME,
            "relative_path": _display_path(source_manifest_path, repo_root),
            "sha256": _sha256_file(source_manifest_path),
            "content_sha256": _sha256_text(source_manifest_text.rstrip("\n")),
            "schema_version": SOURCE_ARTIFACT_PACK_SCHEMA_VERSION,
        },
        "retained_payload_inventory": [
            {
                "requirement_id": row["requirement_id"],
                "relative_path": row["retained_relative_path"],
                "sha256": row["actual_sha256"],
                "source_id": row["source_id"],
                "rights_status": row["rights_status"],
                "benchmark_consumption_status": row["benchmark_consumption_status"],
            }
            for row in artifact["retained_payload_inventory"]
        ],
        "missing_payloads": artifact["missing_payloads"],
        "non_authoritative_guards": artifact["non_authoritative_guards"],
    }
    retained_manifest_path = output_dir / RETAINED_MANIFEST_FILENAME
    retained_manifest_path.write_text(
        _canonical_json(retained_manifest) + "\n",
        encoding="utf-8",
    )
    artifact["retained_manifest_ref"] = _display_path(retained_manifest_path, repo_root)
    artifact["retained_manifest_sha256"] = _sha256_file(retained_manifest_path)
    artifact["source_payload_pack_sha256"] = _sha256_file(artifact_path)
    artifact["source_artifact_pack_manifest_sha256"] = _sha256_file(
        source_manifest_path
    )
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the A2 RES-001 source payload pack without granting authority."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where retained source payload pack files will be written.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--write-retained-artifacts",
        action="store_true",
        help=(
            "Write source_payload_pack.json, source_artifact_pack_manifest.json, "
            "manifest.json, and copy any already-present matching payloads."
        ),
    )
    parser.add_argument(
        "--no-copy-available-payloads",
        action="store_true",
        help="When writing, do not copy matching workspace payloads into the pack.",
    )
    args = parser.parse_args(argv)

    if args.write_retained_artifacts:
        artifact = write_source_payload_pack(
            output_dir=args.output_dir,
            copy_available_payloads=not args.no_copy_available_payloads,
        )
    else:
        artifact = generate_source_payload_pack(output_dir=args.output_dir)

    text = _canonical_json(artifact)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
