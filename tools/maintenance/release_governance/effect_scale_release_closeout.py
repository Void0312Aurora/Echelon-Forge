#!/usr/bin/env python3
"""Generate the Stage B effect-scale release closeout artifact for A2.

This tool closes the current author-side execution record for the focused
Stage B residual slice without granting authority. It deliberately preserves
the independent-review and release-grade provenance/identity blockers even when
the author-side hard gates pass.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import scope_boundary_probe as scope_probe
from tools.maintenance.candidate_artifacts import effect_scale_snapshot as snapshot
from tools.maintenance.release_governance import effect_scale_release_readiness as readiness
from tools.maintenance.candidate_artifacts import effect_scale_result_pack as result_pack


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
CLOSEOUT_SCHEMA_VERSION = "a2.stage_b_release_closeout.v1"
FOCUSED_RESIDUAL_IDS = ("RES-007", "RES-008", "RES-010", "RES-011", "RES-012")
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


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _criterion_counts(snapshot_artifact: dict[str, Any]) -> dict[str, Any]:
    rows = snapshot_artifact["criteria_evaluation"]
    failed_ids = [row["criteria_id"] for row in rows if not row["pass"]]
    return {
        "criteria_count": len(rows),
        "passed_criteria_count": len(rows) - len(failed_ids),
        "failed_criteria_count": len(failed_ids),
        "failed_criteria_ids": failed_ids,
        "all_hard_gates_pass": not failed_ids,
    }


def _blockers_for_residual(
    readiness_artifact: dict[str, Any], residual_id: str
) -> list[dict[str, str]]:
    return [
        row
        for row in readiness_artifact["blocking_conditions"]
        if row["residual_id"] == residual_id
    ]


def _benchmark_execution_rows(
    snapshot_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "criteria_id": row["criteria_id"],
            "benchmark_id": row["benchmark_id"],
            "field": row["field"],
            "expected": row["expected"],
            "actual": row["actual"],
            "pass": bool(row["pass"]),
        }
        for row in snapshot_artifact["criteria_evaluation"]
    ]


def _near_miss_closeout(scope_artifact: dict[str, Any]) -> dict[str, Any]:
    probe = scope_artifact["miss_distance_probe"]
    metrics = probe["metrics"]
    return {
        "residual_id": "RES-007",
        "closeout_status": "author_side_bucket_probe_complete_release_blocked",
        "gate_result": "author_scope_closeout_passed_pending_independent_review",
        "probe_id": probe["probe_id"],
        "probe_status": probe["status"],
        "rows": probe["rows"],
        "metrics": metrics,
        "author_side_closeout_complete": bool(
            metrics["blast_scaled_distance_monotonic_increasing_pass"]
            and metrics["fragment_areal_density_monotonic_decreasing_pass"]
            and metrics["runtime_bucket_consistent_pass"]
            and metrics["anchor_present"]
        ),
        "release_blocked": True,
        "remaining_dependency": (
            "bucket sensitivity and independent reviewer audit remain required "
            "before any release interpretation"
        ),
    }


def _beam_high_closeout(scope_artifact: dict[str, Any]) -> dict[str, Any]:
    closure_probe = scope_artifact["closure_probe"]
    aspect_guard = scope_artifact["aspect_guard_probe"]
    metrics = closure_probe["metrics"]
    return {
        "residual_id": "RES-008",
        "closeout_status": "author_side_beam_high_scope_complete_release_blocked",
        "gate_result": "author_scope_closeout_passed_pending_independent_review",
        "closure_probe": {
            "probe_id": closure_probe["probe_id"],
            "probe_status": closure_probe["status"],
            "rows": closure_probe["rows"],
            "metrics": metrics,
            "limitation_note": closure_probe["limitation_note"],
        },
        "aspect_guard": {
            "probe_id": aspect_guard["probe_id"],
            "probe_status": aspect_guard["status"],
            "accepted_scope_labels": aspect_guard["accepted_scope_labels"],
            "rejected_scope_labels": aspect_guard["rejected_scope_labels"],
            "metrics": aspect_guard["metrics"],
        },
        "author_side_closeout_complete": bool(
            metrics["closure_label_probe_executed"]
            and metrics["mechanism_response_active"]
            and metrics["runtime_bucket_consistent_pass"]
            and metrics["anchor_present"]
            and aspect_guard["metrics"]["beam_only_guard_documented"]
        ),
        "release_blocked": True,
        "remaining_dependency": (
            "candidate closure-sensitive response is recorded, but closure physics "
            "and scope leakage must still be independently reviewed"
        ),
    }


def _validation_closeout(
    *,
    snapshot_artifact: dict[str, Any],
    result_pack_artifact: dict[str, Any],
    readiness_artifact: dict[str, Any],
) -> dict[str, Any]:
    counts = _criterion_counts(snapshot_artifact)
    return {
        "residual_id": "RES-010",
        "closeout_status": "author_side_run_record_complete_release_blocked",
        "gate_result": "author_execution_record_passed_pending_independent_review",
        "criteria_counts": counts,
        "reviewed_benchmarks": list(
            result_pack_artifact["result_table_summary"]["reviewed_benchmarks"]
        ),
        "artifact_hashes": list(result_pack_artifact["artifact_hashes"]),
        "validation_manifest_status": "not_promoted_to_validated",
        "author_side_closeout_complete": bool(counts["all_hard_gates_pass"]),
        "hard_gate_pass_is_release": False,
        "release_blocked": True,
        "readiness_blockers": _blockers_for_residual(readiness_artifact, "RES-010"),
        "remaining_dependency": (
            "independent reviewer signoff and formal validation-result promotion "
            "remain required"
        ),
    }


def _uncertainty_closeout(result_pack_artifact: dict[str, Any]) -> dict[str, Any]:
    summary = result_pack_artifact["uncertainty_result_summary"]
    cv_rows = [
        {
            "metric": "fragment_areal_density_per_m2.cv",
            "actual": summary["fragment_areal_density_cv"],
            "threshold": "<=0.05",
            "pass": summary["fragment_areal_density_cv"] <= 0.05,
        },
        {
            "metric": "blast_impulse_kpa_ms_proxy.cv",
            "actual": summary["blast_impulse_cv"],
            "threshold": "<=0.05",
            "pass": summary["blast_impulse_cv"] <= 0.05,
        },
        {
            "metric": "fragment_energy_j_proxy.cv",
            "actual": summary["fragment_energy_cv"],
            "threshold": "<=0.05",
            "pass": summary["fragment_energy_cv"] <= 0.05,
        },
        {
            "metric": "penetration_margin_proxy.cv",
            "actual": summary["penetration_margin_cv"],
            "threshold": "<=0.05",
            "pass": summary["penetration_margin_cv"] <= 0.05,
        },
    ]
    return {
        "residual_id": "RES-011",
        "closeout_status": "author_side_uncertainty_snapshot_complete_release_blocked",
        "gate_result": "author_uncertainty_closeout_passed_pending_independent_review",
        "cv_rows": cv_rows,
        "seed_window_cv_pass": bool(summary["seed_window_cv_pass"]),
        "author_side_closeout_complete": all(row["pass"] for row in cv_rows)
        and bool(summary["seed_window_cv_pass"]),
        "release_blocked": True,
        "remaining_dependency": (
            "coverage interpretation and independent uncertainty review remain "
            "required before release"
        ),
    }


def _independence_closeout(
    *,
    result_pack_artifact: dict[str, Any],
    readiness_artifact: dict[str, Any],
) -> dict[str, Any]:
    return {
        "residual_id": "RES-012",
        "closeout_status": "author_side_dependency_trace_complete_release_blocked",
        "gate_result": "author_independence_trace_complete_pending_independent_review",
        "benchmark_independence_rows": list(result_pack_artifact["independence_audit"]),
        "review_dependency_trace": [
            {
                "dependency_id": "REV-DEP-001",
                "owner": "independent_reviewer",
                "status": "missing",
                "required_for": "RES-010/RES-012 release closeout",
            },
            {
                "dependency_id": "REV-DEP-002",
                "owner": "release_integrator",
                "status": "blocked_until_review",
                "required_for": "formal validation manifest promotion",
            },
            {
                "dependency_id": "REV-DEP-003",
                "owner": "provenance_identity_lane",
                "status": "blocked",
                "required_for": "release-grade provenance and surrogate identity",
            },
        ],
        "author_side_closeout_complete": True,
        "release_blocked": True,
        "readiness_blockers": _blockers_for_residual(readiness_artifact, "RES-012"),
        "remaining_dependency": (
            "author-side dependency trace is complete, but the benchmark/input "
            "separation audit still needs an independent reviewer"
        ),
    }


def _residual_gate_results(
    *,
    near_miss: dict[str, Any],
    beam_high: dict[str, Any],
    validation: dict[str, Any],
    uncertainty: dict[str, Any],
    independence: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [near_miss, beam_high, validation, uncertainty, independence]
    return [
        {
            "residual_id": row["residual_id"],
            "gate_result": row["gate_result"],
            "author_side_closeout_complete": bool(row["author_side_closeout_complete"]),
            "release_blocked": bool(row["release_blocked"]),
            "remaining_dependency": row["remaining_dependency"],
        }
        for row in rows
    ]


def generate_stage_b_release_closeout(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    snapshot_artifact = snapshot.generate_stage_b_effect_scale_snapshot(repo_root=repo_root)
    scope_artifact = scope_probe.generate_scope_boundary_probe(repo_root=repo_root)
    result_pack_artifact = result_pack.generate_stage_b_validation_result_pack(
        repo_root=repo_root
    )
    readiness_artifact = readiness.generate_stage_b_release_readiness_gate(
        repo_root=repo_root
    )
    counts = _criterion_counts(snapshot_artifact)
    near_miss = _near_miss_closeout(scope_artifact)
    beam_high = _beam_high_closeout(scope_artifact)
    validation = _validation_closeout(
        snapshot_artifact=snapshot_artifact,
        result_pack_artifact=result_pack_artifact,
        readiness_artifact=readiness_artifact,
    )
    uncertainty = _uncertainty_closeout(result_pack_artifact)
    independence = _independence_closeout(
        result_pack_artifact=result_pack_artifact,
        readiness_artifact=readiness_artifact,
    )
    residual_results = _residual_gate_results(
        near_miss=near_miss,
        beam_high=beam_high,
        validation=validation,
        uncertainty=uncertainty,
        independence=independence,
    )

    return {
        "package_id": PACKAGE_ID,
        "schema_version": CLOSEOUT_SCHEMA_VERSION,
        "status": "author_side_stage_b_release_closeout_complete_release_blocked",
        "generated_on": "2026-05-31",
        "release_target": "effect_scale_authority_only",
        "scope": dict(readiness_artifact["scope"]),
        "focused_residual_ids": list(FOCUSED_RESIDUAL_IDS),
        "release_decision": {
            "release_ready": False,
            "release_blocked": True,
            "current_hard_gate_snapshot_pass": bool(counts["all_hard_gates_pass"]),
            "hard_gate_pass_is_release": False,
            "blocked_even_when_hard_gates_pass": bool(counts["all_hard_gates_pass"]),
            "stage_c_component_probability_release_included": False,
            "stock_runtime_authority_granted": False,
        },
        "validation_run_manifest": {
            "run_id": "STAGE-B-ES-RUN-20260531-001",
            "run_status": "author_side_executed_non_authoritative",
            "execution_mode": "deterministic_fixed_seed_candidate_scaffold",
            "seed": int(snapshot_artifact["artifact_provenance"]["seed"]),
            "sample_count": int(snapshot_artifact["artifact_provenance"]["sample_count"]),
            "standoff_m": 0.35,
            "closure_mps": 900.0,
            "scope_probe_standoffs_m": [0.25, 0.35, 0.45],
            "scope_probe_closures_mps": [700.0, 900.0, 1100.0],
            "frozen_criteria_ref": _display_path(
                PACKAGE_DIR
                / "validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md",
                repo_root,
            ),
            "frozen_scope_ref": _display_path(
                PACKAGE_DIR
                / "validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md",
                repo_root,
            ),
            "result_pack_tool_ref": (
                "tools/maintenance/damage_model_candidate_artifacts.py "
                "effect-scale-result-pack"
            ),
            "release_readiness_gate_tool_ref": (
                "tools/maintenance/damage_model_release_governance.py effect-scale-readiness"
            ),
        },
        "benchmark_result_execution_record": {
            "execution_status": "author_side_hard_gates_passed_non_release",
            "criteria_counts": counts,
            "criteria_results": _benchmark_execution_rows(snapshot_artifact),
            "artifact_hashes": list(result_pack_artifact["artifact_hashes"]),
            "hard_gate_pass_is_release": False,
        },
        "near_miss_bucket_closeout": near_miss,
        "beam_high_scope_closeout": beam_high,
        "validation_result_closeout": validation,
        "uncertainty_closeout": uncertainty,
        "independence_review_dependency_trace": independence,
        "residual_gate_results": residual_results,
        "remaining_release_dependencies": [
            {
                "dependency": "independent_review",
                "status": "blocked",
                "residual_ids": ["RES-007", "RES-008", "RES-010", "RES-011", "RES-012"],
            },
            {
                "dependency": "release_grade_provenance_identity",
                "status": "blocked",
                "residual_ids": ["RES-001", "RES-002"],
            },
            {
                "dependency": "stock_runtime_descriptor",
                "status": "forbidden",
                "residual_ids": ["RES-013/014-boundary"],
            },
        ],
        "readiness_gate_blocking_residual_ids": list(
            readiness_artifact["blocking_residual_ids"]
        ),
        "non_authoritative_guards": {
            "stock_descriptor_created": False,
            "stock_runtime_authority_granted": False,
            "effect_scale_authority_granted": False,
            "component_failure_probability_authority_granted": False,
            "pk_authority_granted": False,
            "deterministic_fuze_authority_granted": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the Stage B effect-scale release closeout artifact for "
            "the current A2 blast-fragmentation candidate package."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args(argv)

    artifact = generate_stage_b_release_closeout()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
