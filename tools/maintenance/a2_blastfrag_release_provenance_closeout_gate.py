#!/usr/bin/env python3
"""Evaluate the A2 release provenance closeout gate.

This gate decomposes the remaining RES-001 / RES-002 blockers after the shared
package provenance/identity gate. It is intentionally non-authoritative: it
records author-side evidence and release-grade gaps, but never releases runtime
authority, effect-scale authority, component-probability authority, Pk authority,
or deterministic-fuze authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_package_provenance_identity_gate as shared_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_b_retained_artifact_pack as stage_b_retained,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_retained_artifact_pack as stage_c_retained,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
RELEASE_PROVENANCE_CLOSEOUT_SCHEMA_VERSION = (
    "a2.release_provenance_closeout_gate.v1"
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

DOC_REFS = {
    "artifact_pin_manifest": (
        PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "surrogate_identity_manifest": (
        PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_manifest": PACKAGE_DIR / "validation_manifest_draft_blastfrag_20260528.zh.md",
    "validation_provenance_identity_gate": (
        PACKAGE_DIR / "validation_provenance_and_identity_gate_20260530.zh.md"
    ),
    "residual_register": PACKAGE_DIR / "residual_register.zh.md",
}

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

REQUIRED_FORBIDDEN_OUTPUTS = [
    "effect_scale_authority",
    "component_failure_probability_authority",
    "pk_authority",
    "deterministic_fuze_authority",
]

RELEASE_GRADE_ALLOWED_OUTPUT_POLICY_STATUSES = {
    "release_grade_frozen",
    "reviewer_frozen_release_grade",
    "independently_reviewed_release_grade",
}
RELEASE_GRADE_BENCHMARK_CONSUMPTION_STATUSES = {
    "release_retained_benchmark_input",
    "release_grade_benchmark_input",
    "consumed_for_release_benchmark",
}
RELEASE_GRADE_VALIDATION_STATUSES = {
    "validated",
    "release_validated",
    "independently_validated",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def _has_sha256(value: str) -> bool:
    return bool(re.search(r"\b[a-f0-9]{64}\b", value))


def _forbidden_outputs(identity_text: str) -> list[str]:
    value = _extract_field(identity_text, "forbidden_outputs")
    normalized = value.replace("`", "")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def _verified_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if "verified_candidate_artifact" in row["artifact_status"]
    ]


def _check_status(author_side_satisfied: bool, release_grade_satisfied: bool) -> str:
    if release_grade_satisfied:
        return "release_grade_satisfied_by_this_check"
    if author_side_satisfied:
        return "blocked_release_grade_evidence_missing"
    return "blocked_author_side_evidence_missing"


def _retained_source_artifact_check(rows: list[dict[str, str]]) -> dict[str, Any]:
    verified_rows = _verified_source_rows(rows)
    verified_ids = [row["artifact_id"] for row in verified_rows]
    sha256_pinned_ids = [
        row["artifact_id"] for row in verified_rows if _has_sha256(row["sha256"])
    ]
    retention_pending_ids = [
        row["artifact_id"]
        for row in verified_rows
        if "retention_pending" in row["artifact_status"]
    ]
    release_retained_ids = [
        row["artifact_id"]
        for row in verified_rows
        if (
            "release_retained" in row["artifact_status"]
            or "release_retained" in row["retention_ref"]
            or row["consumption_status"]
            in RELEASE_GRADE_BENCHMARK_CONSUMPTION_STATUSES
        )
    ]

    author_side_satisfied = bool(verified_rows) and len(sha256_pinned_ids) == len(
        verified_rows
    )
    release_grade_satisfied = (
        bool(verified_rows)
        and not retention_pending_ids
        and len(release_retained_ids) == len(verified_rows)
    )
    return {
        "check_id": "CLOSEOUT-RES001-001",
        "residual_id": "RES-001",
        "closeout_surface": "retained_source_artifact",
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _check_status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": {
            "verified_source_artifact_ids": verified_ids,
            "sha256_pinned_artifact_ids": sha256_pinned_ids,
            "external_verification_and_checksum_present": author_side_satisfied,
        },
        "remaining_release_grade_requirements": [
            "canonical retained source artifact pack for verified DENIX artifacts",
            "release retention refs distinct from source-ledger or validation-gap prose",
            "independent review of retained source artifact rights and checksums",
        ],
        "blocking_summary": (
            "DENIX public artifacts are externally verified and checksummed on "
            "the author side, but their artifact_status still contains "
            "retention_pending and no release-retained source artifact pack is pinned"
        ),
        "blocking_artifact_ids": retention_pending_ids or verified_ids,
    }


def _allowed_output_policy_check(
    *,
    pin_text: str,
    identity_text: str,
) -> dict[str, Any]:
    third_party_policy = _extract_field(pin_text, "third_party_policy")
    forbidden_release_action = _extract_field(pin_text, "forbidden_release_action")
    policy_status = _extract_field(pin_text, "allowed_output_policy_status") or "missing"
    forbidden_outputs = _forbidden_outputs(identity_text)
    missing_forbidden_outputs = [
        output for output in REQUIRED_FORBIDDEN_OUTPUTS if output not in forbidden_outputs
    ]
    author_side_satisfied = (
        "never auto-authoritative" in third_party_policy
        and "do not treat" in forbidden_release_action
        and not missing_forbidden_outputs
    )
    release_grade_satisfied = (
        policy_status in RELEASE_GRADE_ALLOWED_OUTPUT_POLICY_STATUSES
        and author_side_satisfied
    )
    return {
        "check_id": "CLOSEOUT-RES001-002",
        "residual_id": "RES-001",
        "closeout_surface": "allowed_output_policy",
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _check_status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": {
            "third_party_policy": third_party_policy,
            "forbidden_release_action": forbidden_release_action,
            "forbidden_outputs": forbidden_outputs,
            "missing_forbidden_outputs": missing_forbidden_outputs,
        },
        "remaining_release_grade_requirements": [
            "explicit release-grade allowed-output policy status",
            "reviewer-frozen rule for spreadsheet/tool outputs and comparison outputs",
            "machine-readable statement that allowed outputs cannot become source truth",
        ],
        "blocking_summary": (
            "candidate-side forbidden outputs are explicit, but no release-grade "
            "allowed-output policy status is frozen"
        ),
        "policy_status": policy_status,
    }


def _benchmark_consumption_trace_check(
    *,
    rows: list[dict[str, str]],
    validation_manifest_text: str,
) -> dict[str, Any]:
    verified_rows = _verified_source_rows(rows)
    explicit_non_consumed_ids = [
        row["artifact_id"]
        for row in verified_rows
        if row["consumption_status"] == "not_consumed_for_stage_b_release"
    ]
    release_consumed_ids = [
        row["artifact_id"]
        for row in verified_rows
        if row["consumption_status"] in RELEASE_GRADE_BENCHMARK_CONSUMPTION_STATUSES
    ]
    manifest_records_non_consumption = (
        "not as acquired benchmark artifact" in validation_manifest_text
        or "not_consumed_for_stage_b_release" in validation_manifest_text
        or "不作为 acquired benchmark artifact" in validation_manifest_text
    )
    comparison_output_hash_refs = re.findall(
        r"\bcomparison[-_ ]output[-_ ]sha256\b", validation_manifest_text
    )
    author_side_satisfied = bool(verified_rows) and (
        (
            len(explicit_non_consumed_ids) == len(verified_rows)
            and manifest_records_non_consumption
        )
        or len(release_consumed_ids) == len(verified_rows)
    )
    release_grade_satisfied = (
        bool(verified_rows)
        and len(release_consumed_ids) == len(verified_rows)
        and bool(comparison_output_hash_refs)
    )
    return {
        "check_id": "CLOSEOUT-RES001-003",
        "residual_id": "RES-001",
        "closeout_surface": "benchmark_consumption_trace",
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _check_status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": {
            "explicit_non_consumed_artifact_ids": explicit_non_consumed_ids,
            "release_consumed_artifact_ids": release_consumed_ids,
            "manifest_records_non_consumption": manifest_records_non_consumption,
        },
        "remaining_release_grade_requirements": [
            "retained benchmark input manifest",
            "comparison-output hashes",
            "reviewer signoff that benchmark outputs were consumed only under allowed policy",
        ],
        "blocking_summary": (
            "the current package has an explicit non-consumption trace, but no "
            "release-grade benchmark-consumption chain or comparison-output hashes"
        ),
    }


def _release_identity_cleanliness_check(identity_text: str) -> dict[str, Any]:
    model_ref = _extract_field(identity_text, "model_ref")
    model_version = _extract_field(identity_text, "model_version")
    repo_commit = _extract_field(identity_text, "repo_commit")
    worktree_state = _extract_field(identity_text, "worktree_state")
    validation_status = _extract_field(identity_text, "current_validation_status")
    output_anchor_count = len(re.findall(r"/tmp/a2_[^|`]+\.json", identity_text))
    author_side_satisfied = (
        bool(model_ref)
        and bool(model_version)
        and bool(re.fullmatch(r"[a-f0-9]{40}", repo_commit))
    )
    release_grade_satisfied = (
        worktree_state == "clean_release_candidate"
        and validation_status in RELEASE_GRADE_VALIDATION_STATUSES
        and output_anchor_count == 0
    )
    blockers = []
    if worktree_state != "clean_release_candidate":
        blockers.append("worktree_state is not clean_release_candidate")
    if validation_status not in RELEASE_GRADE_VALIDATION_STATUSES:
        blockers.append("current_validation_status is not release validated")
    if output_anchor_count > 0:
        blockers.append("/tmp author-side output anchors remain in the identity manifest")
    return {
        "check_id": "CLOSEOUT-RES002-001",
        "residual_id": "RES-002",
        "closeout_surface": "release_identity_cleanliness",
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _check_status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": {
            "model_ref": model_ref,
            "model_version": model_version,
            "repo_commit": repo_commit,
            "worktree_state": worktree_state,
            "current_validation_status": validation_status,
            "output_anchor_count": output_anchor_count,
        },
        "remaining_release_grade_requirements": [
            "clean release candidate identity state",
            "release validation status rather than not_validated",
            "canonical retained outputs instead of /tmp author-side output anchors",
        ],
        "blocking_summary": "; ".join(blockers)
        or "release-grade surrogate identity cleanliness is not proven",
    }


def _pack_release_grade_identity(pack: dict[str, Any]) -> bool:
    origin = pack.get("retained_origin_summary", {})
    return (
        bool(pack.get("manifest_exists"))
        and bool(pack.get("all_artifacts_exist"))
        and origin.get("independent_release_artifact_present") is True
        and origin.get("stock_runtime_authority_present") is True
        and "author" not in str(pack.get("status", ""))
        and "candidate" not in str(pack.get("status", ""))
    )


def _author_pack_release_identity_gap_check(
    *,
    stage_b_pack: dict[str, Any],
    stage_c_pack: dict[str, Any],
) -> dict[str, Any]:
    stage_b_complete = (
        stage_b_pack.get("manifest_exists") is True
        and stage_b_pack.get("all_artifacts_exist") is True
        and stage_b_pack.get("retained_artifact_count") == 4
    )
    stage_c_complete = (
        stage_c_pack.get("manifest_exists") is True
        and stage_c_pack.get("all_artifacts_exist") is True
        and stage_c_pack.get("retained_artifact_count") == 4
    )
    author_side_satisfied = stage_b_complete and stage_c_complete
    release_grade_satisfied = _pack_release_grade_identity(
        stage_b_pack
    ) and _pack_release_grade_identity(stage_c_pack)
    return {
        "check_id": "CLOSEOUT-RES002-002",
        "residual_id": "RES-002",
        "closeout_surface": "author_retained_pack_vs_release_identity",
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _check_status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": {
            "stage_b_status": stage_b_pack.get("status", ""),
            "stage_b_manifest_exists": stage_b_pack.get("manifest_exists", False),
            "stage_b_all_artifacts_exist": stage_b_pack.get("all_artifacts_exist", False),
            "stage_b_retained_artifact_count": stage_b_pack.get(
                "retained_artifact_count", 0
            ),
            "stage_b_retained_origin_summary": stage_b_pack.get(
                "retained_origin_summary", {}
            ),
            "stage_c_status": stage_c_pack.get("status", ""),
            "stage_c_manifest_exists": stage_c_pack.get("manifest_exists", False),
            "stage_c_all_artifacts_exist": stage_c_pack.get("all_artifacts_exist", False),
            "stage_c_retained_artifact_count": stage_c_pack.get(
                "retained_artifact_count", 0
            ),
            "stage_c_retained_origin_summary": stage_c_pack.get(
                "retained_origin_summary", {}
            ),
        },
        "remaining_release_grade_requirements": [
            "independent release artifact present for the retained identity surface",
            "release identity manifest distinct from author-side retained packs",
            "stock/runtime authority review must remain separate from retained evidence",
        ],
        "blocking_summary": (
            "Stage B and Stage C author-side retained packs are present, but "
            "their retained_origin_summary keeps independent_release_artifact_present "
            "and stock_runtime_authority_present false"
        ),
    }


def _residual_condition_trace(closeout_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for residual_id in ("RES-001", "RES-002"):
        checks = [row for row in closeout_checks if row["residual_id"] == residual_id]
        trace.append(
            {
                "residual_id": residual_id,
                "author_side_satisfied_check_ids": [
                    row["check_id"] for row in checks if row["author_side_satisfied"]
                ],
                "release_grade_blocking_check_ids": [
                    row["check_id"] for row in checks if not row["release_grade_satisfied"]
                ],
                "gate_result": (
                    "blocked"
                    if any(not row["release_grade_satisfied"] for row in checks)
                    else "release_closeout_ready_by_this_gate"
                ),
            }
        )
    return trace


def _shared_gate_summary(shared_artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": shared_artifact["status"],
        "schema_version": shared_artifact["schema_version"],
        "readiness_level": shared_artifact["readiness_level"],
        "satisfied_condition_count": len(shared_artifact["satisfied_conditions"]),
        "blocking_condition_count": len(shared_artifact["blocking_conditions"]),
        "blocking_residual_ids": list(
            dict.fromkeys(shared_artifact["blocking_residual_ids"])
        ),
    }


def generate_release_provenance_closeout_gate(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
    identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
    validation_manifest_text = _read_text(DOC_REFS["validation_manifest"])
    rows = _parse_artifact_pin_rows(pin_text)
    stage_b_pack = stage_b_retained.load_retained_artifact_pack_manifest(
        repo_root=repo_root
    )
    stage_c_pack = stage_c_retained.load_retained_artifact_pack_manifest(
        repo_root=repo_root
    )
    shared_artifact = shared_gate.generate_package_provenance_identity_gate(
        repo_root=repo_root
    )

    closeout_checks = [
        _retained_source_artifact_check(rows),
        _allowed_output_policy_check(
            pin_text=pin_text,
            identity_text=identity_text,
        ),
        _benchmark_consumption_trace_check(
            rows=rows,
            validation_manifest_text=validation_manifest_text,
        ),
        _release_identity_cleanliness_check(identity_text),
        _author_pack_release_identity_gap_check(
            stage_b_pack=stage_b_pack,
            stage_c_pack=stage_c_pack,
        ),
    ]
    release_closeout_ready = all(
        row["release_grade_satisfied"] for row in closeout_checks
    )
    blocking_residual_ids = [
        row["residual_id"]
        for row in closeout_checks
        if not row["release_grade_satisfied"]
    ]
    blocking_residual_ids.append("RES-013/014-boundary")

    return {
        "package_id": PACKAGE_ID,
        "schema_version": RELEASE_PROVENANCE_CLOSEOUT_SCHEMA_VERSION,
        "status": (
            "release_provenance_closeout_review_ready_non_authoritative"
            if release_closeout_ready
            else "blocked_non_authoritative_release_provenance_closeout_candidate"
        ),
        "review_target": "res_001_002_release_provenance_closeout_lane",
        "readiness_level": (
            "author_side_subitems_present_but_release_grade_closeout_blocked"
        ),
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss_0_35m",
        },
        "release_closeout_decision": {
            "release_closeout_ready": release_closeout_ready,
            "release_closeout_blocked": not release_closeout_ready,
            "author_side_subitems_recorded": all(
                row["author_side_satisfied"] for row in closeout_checks
            ),
            "authority_release_included": False,
        },
        "shared_provenance_identity_gate_summary": _shared_gate_summary(shared_artifact),
        "closeout_checks": closeout_checks,
        "residual_condition_trace": _residual_condition_trace(closeout_checks),
        "blocking_residual_ids": blocking_residual_ids,
        "author_side_satisfied_summary": {
            "RES-001": [
                "DENIX official public artifact URLs, content types and sha256 values are recorded",
                "candidate-side forbidden release action and forbidden outputs are explicit",
                "verified DENIX rows are explicitly marked not consumed for Stage B release",
            ],
            "RES-002": [
                "model ref, model version and repo commit are recorded",
                "Stage B and Stage C canonical author-side retained packs are present",
            ],
        },
        "remaining_release_grade_paths": {
            "RES-001": [
                "canonical retained source artifact pack",
                "release-grade allowed-output policy freeze",
                "benchmark-consumption trace with comparison-output hashes and reviewer signoff",
            ],
            "RES-002": [
                "clean release candidate identity state",
                "release validation status",
                "release identity manifest that distinguishes retained author packs from authority",
                "independent release artifact/review state external to the author-side retained packs",
            ],
        },
        "explicit_boundaries": [
            "do not use this gate to close Stage B release readiness",
            "do not use this gate to close Stage C fragility review",
            "do not treat source retention or surrogate identity as stock descriptor release",
            "do not release pk or deterministic fuze authority from this gate",
        ],
        "non_authoritative_guards": {
            "stock_descriptor_created": False,
            "stock_database_authority_granted": False,
            "effect_scale_authority_released": False,
            "effect_scale_authority_in_stock": False,
            "component_failure_probability_authority_released": False,
            "component_failure_probability_authority_in_stock": False,
            "pk_authority_released": False,
            "pk_authority": False,
            "deterministic_fuze_authority_released": False,
            "deterministic_fuze_authority": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the release provenance closeout gate for the current A2 "
            "blast-fragmentation candidate package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_release_provenance_closeout_gate()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
