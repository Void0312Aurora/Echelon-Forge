#!/usr/bin/env python3
"""Evaluate the current Stage C component-probability review-readiness gate.

This tool records why the current Stage C candidate package is reviewable on
the author side, yet still blocked from authority release. It deliberately
stays non-authoritative: the output is a blocked gate, not a fragility
validation result, stock runtime authority release, Pk authority, or
deterministic-fuze authority.
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

from tools.maintenance.release_governance import (
    effect_scale_release_readiness as stage_b_gate,
    package_provenance_identity as provenance_identity_gate,
)
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_retained_artifact_pack as stage_c_retained_pack,
)
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_result_pack as stage_c_result_pack,
)
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_snapshot as stage_c_snapshot,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
REVIEW_GATE_SCHEMA_VERSION = "a2.stage_c_component_probability_review_readiness_gate.v1"
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
    "validation_metrics": (
        PACKAGE_DIR
        / "validation_metrics_and_acceptance_criteria_stage_c_component_probability_20260530.zh.md"
    ),
    "validation_snapshot": (
        PACKAGE_DIR / "validation_benchmark_snapshot_stage_c_component_probability_20260530.zh.md"
    ),
    "validation_result_pack": (
        PACKAGE_DIR / "validation_result_pack_stage_c_component_probability_20260530.zh.md"
    ),
    "validation_retained_artifact_pack": (
        PACKAGE_DIR
        / "validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md"
    ),
    "validation_report_draft": PACKAGE_DIR / "validation_report_draft.zh.md",
    "validation_manifest_draft": (
        PACKAGE_DIR / "validation_manifest_draft_blastfrag_20260528.zh.md"
    ),
    "artifact_pin_manifest": (
        PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "surrogate_identity_manifest": (
        PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_stage_c_review_gate": (
        PACKAGE_DIR
        / "validation_review_readiness_gate_stage_c_component_probability_20260530.zh.md"
    ),
    "residual_register": PACKAGE_DIR / "residual_register.zh.md",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_field(text: str, field: str) -> str:
    match = re.search(
        rf"\|\s*`?{re.escape(field)}`?\s*\|\s*`?([^|`]+?)`?\s*\|",
        text,
    )
    return match.group(1).strip() if match else ""


def _scan_placeholder_hits(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    patterns = (
        re.compile(r"<待填>"),
        re.compile(r"<待定义>"),
        re.compile(r"模板"),
    )
    for path in paths:
        for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                hits.append({"path": str(path), "line": line_no, "content": line.strip()})
    return hits


def _open_residual_ids(path: Path) -> set[str]:
    residuals: set[str] = set()
    for line in _read_text(path).splitlines():
        if not line.startswith("| `RES-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        status = cells[-1].strip("`")
        if status == "open" or status.startswith("open_"):
            residuals.add(cells[0].strip("`"))
    return residuals


def _authority_blocked_residual_ids(path: Path) -> set[str]:
    residuals: set[str] = set()
    for line in _read_text(path).splitlines():
        if not line.startswith("| `RES-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        status = cells[-1].strip("`")
        if (
            status == "open"
            or status.startswith("open_")
            or "authority_blocked" in status
            or "authority_fail_closed" in status
            or "authority_boundary_deferred" in status
        ):
            residuals.add(cells[0].strip("`"))
    return residuals


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _artifact_pin_status_counts(text: str) -> dict[str, int]:
    return {
        "acquired_for_candidate": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`acquired_for_candidate`\s*\|", text)
        ),
        "verified_candidate_artifact": len(
            re.findall(
                r"\|\s*`[^`]+`\s*\|.*\|\s*`[^`]*verified_candidate_artifact[^`]*`\s*\|",
                text,
            )
        ),
        "sanity_only": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`sanity_only`\s*\|", text)
        ),
        "pending_acquisition": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`pending_acquisition`\s*\|", text)
        ),
        "rejected": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`rejected`\s*\|", text)
        ),
    }


def _res001_provenance_summary(
    *,
    package_provenance_status: str,
    pin_counts: dict[str, int],
) -> str:
    if pin_counts["pending_acquisition"] > 0:
        return (
            "shared artifact pin surface still contains pending acquisition routes, "
            "so release-grade provenance is not closed"
        )
    if (
        package_provenance_status
        == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
    ):
        return (
            "official public artifacts are externally verified and checksummed, "
            "but shared provenance is still not release-grade closed because "
            "canonical retention, allowed-output policy and "
            "benchmark-consumption closeout remain open"
        )
    return "shared provenance is not yet release-grade closed"


def _satisfied_conditions(
    *,
    placeholder_hits: list[dict[str, Any]],
    criteria_status: str,
    effect_scale_dependency_status: str,
    snapshot_artifact: dict[str, Any],
    result_pack_artifact: dict[str, Any],
    retained_pack_artifact: dict[str, Any],
) -> list[dict[str, str]]:
    conditions: list[dict[str, str]] = []
    if not placeholder_hits:
        conditions.append(
            {
                "condition_id": "READY-CP-001",
                "summary": "Stage C candidate review documentation has no placeholder hits",
            }
        )
    if criteria_status == "frozen_pre_run_stage_c_component_probability_candidate_only":
        conditions.append(
            {
                "condition_id": "READY-CP-002",
                "summary": "Stage C component-probability acceptance criteria are frozen pre-run",
            }
        )
    if (
        effect_scale_dependency_status
        == "stage_b_review_track_retained_separately"
    ):
        conditions.append(
            {
                "condition_id": "READY-CP-003",
                "summary": "Stage C keeps the Stage B effect-scale dependency explicit rather than silently folding tracks",
            }
        )
    if snapshot_artifact["summary"]["all_hard_gates_pass_in_current_snapshot"]:
        conditions.append(
            {
                "condition_id": "READY-CP-004",
                "summary": "current Stage C snapshot passes all frozen component-specific hard gates",
            }
        )
    if result_pack_artifact["result_table_summary"]["all_hard_gates_pass_in_current_snapshot"]:
        conditions.append(
            {
                "condition_id": "READY-CP-005",
                "summary": "current Stage C result pack preserves a passing hard-gate snapshot under stable artifact hashes",
            }
        )
    scope_audit = result_pack_artifact["scope_audit_summary"]
    if (
        scope_audit["gate_band_contains_primary_blast_scaled_distance"]
        and scope_audit["gate_band_contains_primary_fragment_density"]
        and scope_audit["gate_band_contains_primary_fragment_energy"]
        and scope_audit["gate_band_contains_primary_penetration_margin"]
        and scope_audit["gate_band_contains_primary_blast_impulse"]
        and scope_audit["gate_band_contains_primary_surface_incidence"]
    ):
        conditions.append(
            {
                "condition_id": "READY-CP-006",
                "summary": "the current component-specific row still covers the projected primary component load-gate band",
            }
        )
    if (
        retained_pack_artifact["manifest_exists"]
        and retained_pack_artifact["all_artifacts_exist"]
        and retained_pack_artifact["retained_artifact_count"] == 4
    ):
        conditions.append(
            {
                "condition_id": "READY-CP-007",
                "summary": "canonical retained Stage C author-side artifacts are present for the current component-probability candidate surface",
            }
        )
    return conditions


def _blocking_conditions(
    *,
    authority_blocked_residual_ids: set[str],
    validation_manifest_status: str,
    baseline_probability_source: str,
    package_provenance_status: str,
    pin_counts: dict[str, int],
    worktree_state: str,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if "RES-012" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-001",
                "residual_id": "RES-012",
                "summary": "independent fragility review and result-level independence audit are still missing",
            }
        )
    if validation_manifest_status != "validated":
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-002",
                "residual_id": "RES-010",
                "summary": "validation manifest still stays at not_run rather than validated/passed",
            }
        )
    if "RES-009" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-003",
                "residual_id": "RES-009",
                "summary": (
                    "component fragility truth is still unclosed: the baseline remains "
                    f"{baseline_probability_source!r} and the candidate row is still a "
                    "test-local, component-specific positive path"
                ),
            }
        )
    if "RES-011" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-004",
                "residual_id": "RES-011",
                "summary": "probability uncertainty coverage and closeout are still missing",
            }
        )
    if "RES-003" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-005",
                "residual_id": "RES-003",
                "summary": "projected component identity and target-geometry truth remain candidate-only and not independently audited",
            }
        )
    if (
        "RES-001" in authority_blocked_residual_ids
        and package_provenance_status != "release_grade_closed"
    ):
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-006",
                "residual_id": "RES-001",
                "summary": _res001_provenance_summary(
                    package_provenance_status=package_provenance_status,
                    pin_counts=pin_counts,
                ),
            }
        )
    if (
        "RES-002" in authority_blocked_residual_ids
        and worktree_state != "clean_release_candidate"
    ):
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-007",
                "residual_id": "RES-002",
                "summary": "surrogate identity remains author-side because the repo is not in a clean release-grade identity state",
            }
        )
    if "RES-005" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-008",
                "residual_id": "RES-005",
                "summary": "fragment mechanism residual is still authority-blocked for component-probability release",
            }
        )
    if "RES-006" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-009",
                "residual_id": "RES-006",
                "summary": "blast mechanism residual is still authority-blocked for component-probability release",
            }
        )
    if "RES-008" in authority_blocked_residual_ids:
        blockers.append(
            {
                "blocker_id": "BLOCK-CP-010",
                "residual_id": "RES-008",
                "summary": (
                    "upstream candidate closure-sensitive response is present, but RES-008 "
                    "remains non-authoritative and retained as a future authority boundary, so "
                    "Stage C cannot outrun the Stage B scope boundary"
                ),
            }
        )
    blockers.append(
        {
            "blocker_id": "BLOCK-CP-011",
            "residual_id": "RES-013/014-boundary",
            "summary": "stock runtime authority, pk authority and deterministic fuze authority remain explicitly closed by package boundary",
        }
    )
    return blockers


def generate_stage_c_component_probability_review_readiness_gate(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    snapshot_artifact = stage_c_snapshot.generate_stage_c_component_probability_snapshot(
        repo_root=repo_root
    )
    result_pack_artifact = (
        stage_c_result_pack.generate_stage_c_component_probability_result_pack(
            repo_root=repo_root
        )
    )
    retained_pack_artifact = stage_c_retained_pack.load_retained_artifact_pack_manifest(
        repo_root=repo_root
    )
    provenance_identity_artifact = (
        provenance_identity_gate.generate_package_provenance_identity_gate(
            repo_root=repo_root
        )
    )
    stage_b_gate_artifact = stage_b_gate.generate_stage_b_release_readiness_gate(
        repo_root=repo_root
    )
    criteria_text = _read_text(DOC_REFS["validation_metrics"])
    report_text = _read_text(DOC_REFS["validation_report_draft"])
    manifest_text = _read_text(DOC_REFS["validation_manifest_draft"])
    pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
    identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
    placeholder_hits = _scan_placeholder_hits(
        [
            DOC_REFS["validation_metrics"],
            DOC_REFS["validation_snapshot"],
            DOC_REFS["validation_result_pack"],
            DOC_REFS["validation_retained_artifact_pack"],
            DOC_REFS["validation_report_draft"],
            DOC_REFS["validation_manifest_draft"],
            DOC_REFS["artifact_pin_manifest"],
            DOC_REFS["surrogate_identity_manifest"],
            DOC_REFS["validation_stage_c_review_gate"],
        ]
    )
    criteria_status = _extract_field(criteria_text, "criteria_status")
    effect_scale_dependency_status = _extract_field(
        criteria_text, "effect_scale_dependency_status"
    )
    validation_manifest_status = (
        _extract_field(report_text, "validation_status")
        or _extract_field(manifest_text, "validation_status")
    )
    pin_counts = _artifact_pin_status_counts(pin_text)
    package_provenance_status = _extract_field(pin_text, "package_provenance_status")
    worktree_state = _extract_field(identity_text, "worktree_state")
    open_residual_ids = _open_residual_ids(DOC_REFS["residual_register"])
    authority_blocked_residual_ids = _authority_blocked_residual_ids(
        DOC_REFS["residual_register"]
    )
    blockers = _blocking_conditions(
        authority_blocked_residual_ids=authority_blocked_residual_ids,
        validation_manifest_status=validation_manifest_status,
        baseline_probability_source=result_pack_artifact[
            "component_probability_result_summary"
        ]["baseline_component_probability_source"],
        package_provenance_status=package_provenance_status,
        pin_counts=pin_counts,
        worktree_state=worktree_state,
    )
    satisfied = _satisfied_conditions(
        placeholder_hits=placeholder_hits,
        criteria_status=criteria_status,
        effect_scale_dependency_status=effect_scale_dependency_status,
        snapshot_artifact=snapshot_artifact,
        result_pack_artifact=result_pack_artifact,
        retained_pack_artifact=retained_pack_artifact,
    )
    scope = snapshot_artifact["scope"]
    component_row = snapshot_artifact["component_probability_snapshot"]["row"]
    return {
        "package_id": PACKAGE_ID,
        "schema_version": REVIEW_GATE_SCHEMA_VERSION,
        "status": "blocked_non_authoritative_stage_c_review_candidate",
        "scope": {
            "target_type": scope["target_type"],
            "weapon_class": scope["weapon_class"],
            "weapon_family": scope["weapon_family"],
            "aspect_bucket": scope["aspect_bucket"],
            "closure_bucket": scope["closure_bucket"],
            "miss_distance_bucket": scope["runtime_miss_distance_bucket"],
            "candidate_scope_label": scope["candidate_scope_label"],
            "component_name": scope["component_name"],
            "component_system": scope["component_system"],
            "component_redundancy_group_id": scope["component_redundancy_group_id"],
        },
        "review_target": "component_failure_probability_authority_only",
        "readiness_level": (
            "author_side_component_candidate_ready_but_not_fragility_review_closed"
        ),
        "upstream_stage_b_dependency_summary": {
            "dependency_role": "separate_upstream_effect_scale_authority_track",
            "status": stage_b_gate_artifact["status"],
            "release_target": stage_b_gate_artifact["release_target"],
            "readiness_level": stage_b_gate_artifact["readiness_level"],
            "blocking_residual_ids": _dedupe_preserve_order(
                list(stage_b_gate_artifact["blocking_residual_ids"])
            ),
            "dependency_preserved_as_blocked": (
                stage_b_gate_artifact["status"]
                == "blocked_non_authoritative_stage_b_release_candidate"
                and stage_b_gate_artifact["release_target"]
                == "effect_scale_authority_only"
            ),
        },
        "retained_artifact_pack_summary": {
            "status": retained_pack_artifact["status"],
            "manifest_exists": retained_pack_artifact["manifest_exists"],
            "manifest_relative_path": retained_pack_artifact["manifest_relative_path"],
            "retained_artifact_count": retained_pack_artifact["retained_artifact_count"],
            "all_artifacts_exist": retained_pack_artifact["all_artifacts_exist"],
            "retention_scope": retained_pack_artifact.get("retention_scope", ""),
        },
        "shared_provenance_identity_gate_summary": {
            "status": provenance_identity_artifact["status"],
            "readiness_level": provenance_identity_artifact["readiness_level"],
            "satisfied_condition_count": len(
                provenance_identity_artifact["satisfied_conditions"]
            ),
            "blocking_condition_count": len(
                provenance_identity_artifact["blocking_conditions"]
            ),
            "blocking_residual_ids": _dedupe_preserve_order(
                list(provenance_identity_artifact["blocking_residual_ids"])
            ),
        },
        "candidate_row_summary": {
            "component_name": component_row["component_name"],
            "component_system": component_row["component_system"],
            "component_redundancy_group_id": component_row[
                "component_redundancy_group_id"
            ],
            "component_failure_probability": component_row[
                "component_failure_probability"
            ],
            "baseline_component_probability_source": snapshot_artifact[
                "baseline_event_summary"
            ]["component_failure_probability_source"],
        },
        "satisfied_conditions": satisfied,
        "blocking_conditions": blockers,
        "blocking_residual_ids": [row["residual_id"] for row in blockers],
        "open_residual_ids": sorted(open_residual_ids),
        "authority_blocked_residual_ids": sorted(authority_blocked_residual_ids),
        "explicit_boundaries": [
            "do not treat this gate as independent fragility review",
            "do not treat this gate as stock component-probability authority",
            "do not elevate one component-specific candidate row into aircraft-wide fragility truth",
            "do not release pk or deterministic fuze from this Stage C gate",
        ],
        "current_findings": [
            (
                "Stage C now has frozen candidate criteria, a component-specific "
                "snapshot, a unified result pack, a canonical retained pack and "
                "load-gate coverage for one projected component row"
            ),
            (
                "the gate remains blocked because fragility calibration, "
                "uncertainty, provenance/identity, geometry/mechanism residuals "
                "and independent review remain authority-blocked"
            ),
            (
                "Stage B effect-scale remains on a separate blocked upstream track, "
                "so Stage C cannot be promoted above author-side review closure"
            ),
        ],
        "non_authoritative_guards": {
            "stock_descriptor_created": False,
            "stock_database_authority_granted": False,
            "effect_scale_authority_in_stock": False,
            "component_failure_probability_authority_in_stock": False,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
            "candidate_bundle_role": "review_and_packaging_only",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the current Stage C component-probability review-readiness "
            "gate for the A2 blast-fragmentation package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_stage_c_component_probability_review_readiness_gate()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
