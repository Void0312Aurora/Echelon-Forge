#!/usr/bin/env python3
"""Generate a Stage B effect-scale candidate validation result pack for A2.

This tool packages the current non-authoritative Stage B effect-scale review
artifacts into a single machine-readable bundle with stable content hashes and
explicit independence semantics. It remains below runtime authority: the output
is a candidate review artifact and must not be treated as validated effect
scale, stock runtime authority, Pk, or deterministic-fuze authority.
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

from tools.maintenance import a2_blastfrag_scope_boundary_probe as scope_probe
from tools.maintenance import a2_blastfrag_stage_b_effect_scale_snapshot as stage_b_snapshot
from tools.maintenance import a2_blastfrag_validation_scaffold as scaffold


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
RESULT_PACK_SCHEMA_VERSION = "a2.stage_b_validation_result_pack.v1"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _artifact_hash_rows(
    *,
    scaffold_artifact: dict[str, Any],
    scope_probe_artifact: dict[str, Any],
    stage_b_snapshot_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        {
            "artifact_id": "ART-SCAFFOLD-001",
            "artifact_kind": "validation_scaffold_snapshot",
            "tool_ref": "tools/maintenance/a2_blastfrag_validation_scaffold.py",
            "status": scaffold_artifact["validation_status"],
            "sha256": _payload_sha256(scaffold_artifact),
        },
        {
            "artifact_id": "ART-SCOPE-PROBE-001",
            "artifact_kind": "scope_boundary_probe_snapshot",
            "tool_ref": "tools/maintenance/a2_blastfrag_scope_boundary_probe.py",
            "status": scope_probe_artifact["status"],
            "sha256": _payload_sha256(scope_probe_artifact),
        },
        {
            "artifact_id": "ART-STAGE-B-SNAPSHOT-001",
            "artifact_kind": "stage_b_hard_gate_snapshot",
            "tool_ref": "tools/maintenance/a2_blastfrag_stage_b_effect_scale_snapshot.py",
            "status": stage_b_snapshot_artifact["status"],
            "sha256": _payload_sha256(stage_b_snapshot_artifact),
        },
    ]
    return rows


def _independence_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "benchmark_id": "BFM-BM-001",
            "independence_class": "partial_independent_method_only",
            "current_release_role": "unit_domain_lock",
            "allowed_claim": "candidate blast unit/domain lock only",
            "forbidden_claim": "external blast truth or missile-specific validation truth",
            "audit_outcome": "candidate_method_independence_only",
        },
        {
            "benchmark_id": "BFM-BM-002",
            "independence_class": "synthetic_only",
            "current_release_role": "deferred_fragment_sanity",
            "allowed_claim": "toy fragment mass-energy sanity only",
            "forbidden_claim": "AIM-120C fragment truth or release gating",
            "audit_outcome": "deferred_not_release_gating",
        },
        {
            "benchmark_id": "BFM-BM-003",
            "independence_class": "independent_for_sampler_replay_not_for_target_truth",
            "current_release_role": "sampler_reproducibility_and_convergence",
            "allowed_claim": "sampling replay and convergence inside witness-geometry bookkeeping",
            "forbidden_claim": "true F-16 exposure geometry or direction-pattern truth",
            "audit_outcome": "candidate_sampling_hygiene_only",
        },
        {
            "benchmark_id": "BFM-BM-004",
            "independence_class": "partial_independent_method_only",
            "current_release_role": "deferred_penetration_domain_hygiene",
            "allowed_claim": "formula-shape and domain-rejection hygiene only",
            "forbidden_claim": "aircraft component penetration truth or release gating",
            "audit_outcome": "deferred_not_release_gating",
        },
        {
            "benchmark_id": "BFM-BM-005",
            "independence_class": "not_independent_real_validation",
            "current_release_role": "integrated_mechanism_load_hygiene_only",
            "allowed_claim": "integrated mechanism-load bookkeeping hygiene only",
            "forbidden_claim": "independent surrogate validation or authority release by itself",
            "audit_outcome": "candidate_hygiene_only_not_independent_validation",
        },
        {
            "benchmark_id": "BFM-BM-006",
            "independence_class": "administratively_independent",
            "current_release_role": "source_trace_and_rights_gate",
            "allowed_claim": "administrative trace and rights gate only",
            "forbidden_claim": "physics validation by itself",
            "audit_outcome": "administrative_gate_only",
        },
    ]


def generate_stage_b_validation_result_pack(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    scaffold_artifact = scaffold.generate_validation_scaffold(repo_root=repo_root)
    scope_probe_artifact = scope_probe.generate_scope_boundary_probe(repo_root=repo_root)
    stage_b_snapshot_artifact = stage_b_snapshot.generate_stage_b_effect_scale_snapshot(
        repo_root=repo_root
    )
    artifact_hashes = _artifact_hash_rows(
        scaffold_artifact=scaffold_artifact,
        scope_probe_artifact=scope_probe_artifact,
        stage_b_snapshot_artifact=stage_b_snapshot_artifact,
    )
    artifact_hash_map = {row["artifact_id"]: row["sha256"] for row in artifact_hashes}
    miss_distance_probe = scope_probe_artifact["miss_distance_probe"]
    closure_probe = scope_probe_artifact["closure_probe"]
    stage_b_summary = stage_b_snapshot_artifact["summary"]
    bm005 = stage_b_snapshot_artifact["benchmark_snapshot"]["BFM-BM-005"]

    return {
        "package_id": PACKAGE_ID,
        "schema_version": RESULT_PACK_SCHEMA_VERSION,
        "status": "candidate_non_authoritative_stage_b_result_pack",
        "scope": dict(stage_b_snapshot_artifact["scope"]),
        "artifact_hashes": artifact_hashes,
        "result_table_summary": {
            "all_hard_gates_pass_in_current_snapshot": stage_b_summary[
                "all_hard_gates_pass_in_current_snapshot"
            ],
            "hard_gate_pass_is_release": False,
            "failed_criteria_ids": list(stage_b_summary["failed_criteria_ids"]),
            "reviewed_benchmarks": list(stage_b_summary["reviewed_benchmarks"]),
            "primary_release_scope": stage_b_summary["primary_release_scope"],
            "review_status": "author_result_pack_only_pending_independent_review",
            "evidence_artifact_hashes": {
                "validation_scaffold": artifact_hash_map["ART-SCAFFOLD-001"],
                "scope_boundary_probe": artifact_hash_map["ART-SCOPE-PROBE-001"],
                "stage_b_snapshot": artifact_hash_map["ART-STAGE-B-SNAPSHOT-001"],
            },
        },
        "release_readiness_interpretation": {
            "current_hard_gate_snapshot_pass": bool(
                stage_b_summary["all_hard_gates_pass_in_current_snapshot"]
            ),
            "hard_gate_pass_is_release": False,
            "release_ready": False,
            "release_target": "effect_scale_authority_only",
            "current_release_decision": (
                "blocked_pending_independent_review_release_grade_identity_"
                "provenance_uncertainty_and_scope_closeout"
            ),
            "stage_c_component_probability_release_included": False,
            "stock_runtime_authority_granted": False,
        },
        "uncertainty_result_summary": {
            "fragment_areal_density_cv": float(
                bm005["uncertainty_summary"]["fragment_areal_density_per_m2"]["cv"]
            ),
            "blast_impulse_cv": float(
                bm005["uncertainty_summary"]["blast_impulse_kpa_ms_proxy"]["cv"]
            ),
            "fragment_energy_cv": float(
                bm005["uncertainty_summary"]["fragment_energy_j_proxy"]["cv"]
            ),
            "penetration_margin_cv": float(
                bm005["uncertainty_summary"]["penetration_margin_proxy"]["cv"]
            ),
            "seed_window_cv_pass": bool(bm005["metrics"]["seed_window_cv_pass"]),
            "result_interpretation": (
                "candidate uncertainty snapshot only; not an independently reviewed "
                "uncertainty boundary"
            ),
        },
        "scope_audit_summary": {
            "miss_distance_row_count": len(miss_distance_probe["rows"]),
            "miss_distance_monotonic_pass": bool(
                miss_distance_probe["metrics"][
                    "blast_scaled_distance_monotonic_increasing_pass"
                ]
            )
            and bool(
                miss_distance_probe["metrics"][
                    "fragment_areal_density_monotonic_decreasing_pass"
                ]
            ),
            "closure_mechanism_response_active": bool(
                closure_probe["metrics"]["mechanism_response_active"]
            ),
            "closure_limitation_note": str(closure_probe["limitation_note"]),
            "scope_guard_interpretation": (
                "candidate closure-sensitive response is observed in Stage B scope probe; "
                "RES-008 remains non-authoritative and retained as a future authority boundary"
            ),
        },
        "independence_audit": _independence_audit_rows(),
        "current_findings": [
            (
                "the current result pack consolidates fixed-seed scaffold, scope "
                "probe and stage-b snapshot outputs under stable content hashes"
            ),
            (
                "all current Stage B hard gates pass inside the candidate snapshot, "
                "but the result pack is still author-side and non-authoritative"
            ),
            (
                "BFM-BM-005 remains integrated hygiene only and must not be narrated "
                "as independent surrogate validation"
            ),
        ],
        "non_authoritative_guards": {
            "stock_runtime_authority_granted": False,
            "effect_scale_authority_granted": False,
            "component_failure_probability_authority_granted": False,
            "pk_authority_granted": False,
            "deterministic_fuze_authority_granted": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the Stage B effect-scale candidate validation result pack "
            "for the current A2 blast-fragmentation package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_stage_b_validation_result_pack()
    payload = _canonical_json(artifact)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
