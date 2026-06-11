#!/usr/bin/env python3
"""Evaluate the shared package-level provenance and identity gate for A2.

This tool consolidates the current package-wide RES-001 / RES-002 blocker
surface into one machine-readable artifact. It records what is already present
on the author side, while keeping the package explicitly non-authoritative: it
does not grant runtime authority, release-grade provenance, release-grade
surrogate identity, Pk authority, or deterministic-fuze authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import effect_scale_retained_pack as stage_b_retained
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_retained_artifact_pack as stage_c_retained,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
PROVENANCE_IDENTITY_GATE_SCHEMA_VERSION = "a2.package_provenance_identity_gate.v1"
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
    "validation_retained_artifact_pack_stage_b": (
        PACKAGE_DIR / "validation_retained_artifact_pack_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_retained_artifact_pack_stage_c": (
        PACKAGE_DIR
        / "validation_retained_artifact_pack_stage_c_component_probability_20260530.zh.md"
    ),
    "validation_provenance_identity_gate": (
        PACKAGE_DIR / "validation_provenance_and_identity_gate_20260530.zh.md"
    ),
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
        return "pending acquisition artifact routes still exist in the package pin surface"
    if (
        package_provenance_status
        == "official_public_artifacts_partially_verified_release_grade_closeout_pending"
    ):
        return (
            "official public artifacts are externally verified and checksummed, "
            "but package provenance is still not release-grade closed because "
            "canonical retention, allowed-output policy and "
            "benchmark-consumption closeout remain open"
        )
    return "package provenance is not yet release-grade closed"


def _identity_summary(text: str) -> dict[str, Any]:
    output_anchor_count = len(re.findall(r"/tmp/a2_[^|`]+\.json", text))
    return {
        "model_ref": _extract_field(text, "model_ref"),
        "model_version": _extract_field(text, "model_version"),
        "repo_commit": _extract_field(text, "repo_commit"),
        "worktree_state": _extract_field(text, "worktree_state"),
        "retained_artifact_pack_status": _extract_field(
            text, "retained_artifact_pack_status"
        ),
        "retained_artifact_count": int(
            _extract_field(text, "retained_artifact_count") or 0
        ),
        "current_validation_status": _extract_field(text, "current_validation_status"),
        "primary_release_scope": _extract_field(text, "primary_release_scope"),
        "output_anchor_count": output_anchor_count,
    }


def _satisfied_conditions(
    *,
    placeholder_hits: list[dict[str, Any]],
    manifest_status: str,
    identity_summary: dict[str, Any],
    stage_b_retained_artifact: dict[str, Any],
    stage_c_retained_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    if not placeholder_hits:
        conditions.append(
            {
                "condition_id": "READY-PI-001",
                "residual_ids": ["RES-001", "RES-002"],
                "summary": "package provenance and identity documentation has no placeholder hits",
            }
        )
    if manifest_status == "author_frozen_pending_independent_review":
        conditions.append(
            {
                "condition_id": "READY-PI-002",
                "residual_ids": ["RES-001"],
                "summary": "artifact pin manifest is frozen for author-side candidate review",
            }
        )
    if (
        identity_summary["model_ref"]
        and identity_summary["model_version"]
        and identity_summary["repo_commit"]
    ):
        conditions.append(
            {
                "condition_id": "READY-PI-003",
                "residual_ids": ["RES-002"],
                "summary": (
                    "surrogate identity manifest records the current "
                    "model/version/repo anchor surface"
                ),
            }
        )
    if (
        stage_b_retained_artifact["manifest_exists"]
        and stage_b_retained_artifact["all_artifacts_exist"]
        and stage_b_retained_artifact["retained_artifact_count"] == 4
    ):
        conditions.append(
            {
                "condition_id": "READY-PI-004",
                "residual_ids": ["RES-002"],
                "summary": "canonical retained Stage B author-side artifacts are present",
            }
        )
    if (
        stage_c_retained_artifact["manifest_exists"]
        and stage_c_retained_artifact["all_artifacts_exist"]
        and stage_c_retained_artifact["retained_artifact_count"] == 4
    ):
        conditions.append(
            {
                "condition_id": "READY-PI-005",
                "residual_ids": ["RES-002"],
                "summary": "canonical retained Stage C author-side artifacts are present",
            }
        )
    return conditions


def _release_grade_provenance_candidate_surface_present(pin_counts: dict[str, int]) -> bool:
    return (
        pin_counts["pending_acquisition"] > 0
        or pin_counts["verified_candidate_artifact"] > 0
        or pin_counts["sanity_only"] > 0
    )


def _blocking_conditions(
    *,
    placeholder_hits: list[dict[str, Any]],
    manifest_status: str,
    package_provenance_status: str,
    pin_counts: dict[str, int],
    identity_summary: dict[str, Any],
    stage_b_retained_artifact: dict[str, Any],
    stage_c_retained_artifact: dict[str, Any],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if placeholder_hits:
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-000",
                "residual_id": "RES-001/002",
                "summary": (
                    "placeholder text remains in package provenance or "
                    "surrogate-identity documentation"
                ),
            }
        )
    if manifest_status != "author_frozen_pending_independent_review":
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-001",
                "residual_id": "RES-001",
                "summary": (
                    "artifact pin manifest is not yet frozen to the current "
                    "candidate review surface"
                ),
            }
        )
    elif package_provenance_status != "release_grade_closed":
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-001",
                "residual_id": "RES-001",
                "summary": _res001_provenance_summary(
                    package_provenance_status=package_provenance_status,
                    pin_counts=pin_counts,
                ),
            }
        )
    elif _release_grade_provenance_candidate_surface_present(pin_counts):
        if package_provenance_status == "release_grade_closed":
            blockers.append(
                {
                    "blocker_id": "BLOCK-PI-001",
                    "residual_id": "RES-001",
                    "summary": (
                        "release-grade provenance cannot be accepted while "
                        "candidate-only, sanity-only or pending artifact entries "
                        "remain in the package pin surface"
                    ),
                }
            )
    if identity_summary["worktree_state"] != "clean_release_candidate":
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-002",
                "residual_id": "RES-002",
                "summary": (
                    "surrogate identity remains author-side because the repo is "
                    "not in a clean release-grade identity state"
                ),
            }
        )
    if (
        identity_summary["retained_artifact_pack_status"]
        != "present_author_side_non_authoritative"
    ):
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-003",
                "residual_id": "RES-002",
                "summary": (
                    "Stage B retained artifact status is not pinned to the "
                    "expected author-side non-authoritative identity surface"
                ),
            }
        )
    else:
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-003",
                "residual_id": "RES-002",
                "summary": (
                    "author-side retained artifact packs are present, but they "
                    "do not close release-grade surrogate identity"
                ),
            }
        )
    if (
        identity_summary["retained_artifact_pack_status"]
        == "present_author_side_non_authoritative"
        and not (
            stage_b_retained_artifact["manifest_exists"]
            and stage_b_retained_artifact["all_artifacts_exist"]
            and stage_c_retained_artifact["manifest_exists"]
            and stage_c_retained_artifact["all_artifacts_exist"]
        )
    ):
        blockers.append(
            {
                "blocker_id": "BLOCK-PI-005",
                "residual_id": "RES-002",
                "summary": (
                    "canonical retained artifact packs are not yet complete "
                    "across the shared Stage B / Stage C candidate surface"
                ),
            }
        )
    blockers.append(
        {
            "blocker_id": "BLOCK-PI-004",
            "residual_id": "RES-013/014-boundary",
            "summary": (
                "this shared provenance/identity surface does not grant stock "
                "authority, pk authority or deterministic fuze authority"
            ),
        }
    )
    return blockers


def _mentions_residual(row_residual_id: str, residual_id: str) -> bool:
    residual_ids = set(re.findall(r"RES-\d{3}", row_residual_id))
    shorthand_match = re.match(r"RES-\d{3}/(\d{3})", row_residual_id)
    if shorthand_match:
        residual_ids.add(f"RES-{shorthand_match.group(1)}")
    return residual_id in residual_ids


def _residual_condition_trace(
    *,
    satisfied: list[dict[str, Any]],
    blockers: list[dict[str, str]],
) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for residual_id in ("RES-001", "RES-002"):
        satisfied_ids = [
            row["condition_id"]
            for row in satisfied
            if residual_id in row.get("residual_ids", [])
        ]
        blocking_ids = [
            row["blocker_id"]
            for row in blockers
            if _mentions_residual(row["residual_id"], residual_id)
        ]
        trace.append(
            {
                "residual_id": residual_id,
                "satisfied_condition_ids": satisfied_ids,
                "blocking_condition_ids": blocking_ids,
                "gate_result": "blocked" if blocking_ids else "not_blocked_by_this_gate",
            }
        )
    return trace


def generate_package_provenance_identity_gate(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
    identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
    manifest_status = _extract_field(pin_text, "manifest_status")
    package_provenance_status = _extract_field(pin_text, "package_provenance_status")
    pin_counts = _artifact_pin_status_counts(pin_text)
    identity_summary = _identity_summary(identity_text)
    stage_b_retained_artifact = stage_b_retained.load_retained_artifact_pack_manifest(
        repo_root=repo_root
    )
    stage_c_retained_artifact = stage_c_retained.load_retained_artifact_pack_manifest(
        repo_root=repo_root
    )
    placeholder_hits = _scan_placeholder_hits(
        [
            DOC_REFS["artifact_pin_manifest"],
            DOC_REFS["surrogate_identity_manifest"],
            DOC_REFS["validation_retained_artifact_pack_stage_b"],
            DOC_REFS["validation_retained_artifact_pack_stage_c"],
            DOC_REFS["validation_provenance_identity_gate"],
        ]
    )
    satisfied = _satisfied_conditions(
        placeholder_hits=placeholder_hits,
        manifest_status=manifest_status,
        identity_summary=identity_summary,
        stage_b_retained_artifact=stage_b_retained_artifact,
        stage_c_retained_artifact=stage_c_retained_artifact,
    )
    blockers = _blocking_conditions(
        placeholder_hits=placeholder_hits,
        manifest_status=manifest_status,
        package_provenance_status=package_provenance_status,
        pin_counts=pin_counts,
        identity_summary=identity_summary,
        stage_b_retained_artifact=stage_b_retained_artifact,
        stage_c_retained_artifact=stage_c_retained_artifact,
    )
    return {
        "package_id": PACKAGE_ID,
        "schema_version": PROVENANCE_IDENTITY_GATE_SCHEMA_VERSION,
        "status": "blocked_non_authoritative_package_provenance_identity_candidate",
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss_0_35m",
        },
        "review_target": "shared_provenance_and_surrogate_identity_surface",
        "readiness_level": (
            "author_side_pin_and_identity_surface_present_but_not_release_grade"
        ),
        "artifact_pin_manifest_summary": {
            "manifest_status": manifest_status,
            "package_provenance_status": package_provenance_status,
            "status_counts": pin_counts,
            "third_party_policy": _extract_field(pin_text, "third_party_policy"),
            "forbidden_release_action": _extract_field(
                pin_text, "forbidden_release_action"
            ),
        },
        "surrogate_identity_summary": identity_summary,
        "retained_artifact_pack_summary": {
            "stage_b": {
                "status": stage_b_retained_artifact["status"],
                "manifest_exists": stage_b_retained_artifact["manifest_exists"],
                "retained_artifact_count": stage_b_retained_artifact[
                    "retained_artifact_count"
                ],
                "all_artifacts_exist": stage_b_retained_artifact[
                    "all_artifacts_exist"
                ],
            },
            "stage_c": {
                "status": stage_c_retained_artifact["status"],
                "manifest_exists": stage_c_retained_artifact["manifest_exists"],
                "retained_artifact_count": stage_c_retained_artifact[
                    "retained_artifact_count"
                ],
                "all_artifacts_exist": stage_c_retained_artifact[
                    "all_artifacts_exist"
                ],
            },
        },
        "satisfied_conditions": satisfied,
        "blocking_conditions": blockers,
        "residual_condition_trace": _residual_condition_trace(
            satisfied=satisfied,
            blockers=blockers,
        ),
        "blocking_residual_ids": [row["residual_id"] for row in blockers],
        "explicit_boundaries": [
            "do not treat author-side retained packs as release-grade identity closure",
            "do not treat candidate or sanity-only pins as acquired authority inputs",
            (
                "do not grant stock runtime authority, pk authority or "
                "deterministic fuze authority from this gate"
            ),
        ],
        "current_findings": [
            (
                "the package now has explicit artifact-pin, surrogate-identity, "
                "Stage B retained and Stage C retained surfaces"
            ),
            (
                "release-grade provenance and surrogate identity remain blocked by "
                "retention/consumption closeout and the current dirty release-state"
            ),
        ],
        "non_authoritative_guards": {
            "stock_descriptor_created": False,
            "stock_database_authority_granted": False,
            "effect_scale_authority_in_stock": False,
            "component_failure_probability_authority_in_stock": False,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the shared package-level provenance and surrogate-identity "
            "gate for the A2 blast-fragmentation candidate package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args(argv)

    artifact = generate_package_provenance_identity_gate()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
