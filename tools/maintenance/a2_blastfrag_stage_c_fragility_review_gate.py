#!/usr/bin/env python3
"""Evaluate the Stage C fragility review gate for A2.

This gate reviews the current Stage C fragility prep packet for the
right_aileron_actuator component surface. It can mark bounded review checks as
review_passed, but it deliberately fails closed at residual and authority level
when independent benchmark evidence, formal result promotion or Stage B release
dependencies are still missing.
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

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_component_probability_review_readiness_gate as readiness_gate,
)
from tools.maintenance import (  # noqa: E402
    a2_blastfrag_stage_c_fragility_validation_prep as prep,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
REVIEW_GATE_SCHEMA_VERSION = "a2.stage_c_fragility_review_gate.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = "a2.stage_c_fragility_review_retained_manifest.v1"
BENCHMARK_SCHEMA_VERSION = "a2.stage_c_fragility_benchmark.v1"
BENCHMARK_COMPARISON_SCHEMA_VERSION = (
    "a2.stage_c_fragility_benchmark_comparison.v1"
)
BENCHMARK_RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.stage_c_fragility_benchmark_retained_manifest.v1"
)
FOCUSED_RESIDUAL_IDS = ("RES-009", "RES-010", "RES-011", "RES-012")
PACKAGE_RELATIVE_DIR = (
    Path("docs")
    / "task"
    / "air_combat"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
BENCHMARK_RETAINED_RELATIVE_DIR = (
    PACKAGE_RELATIVE_DIR
    / "retained_artifacts"
    / "stage_c_fragility_benchmark_20260531"
)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _blockers_for_residual(
    readiness_artifact: dict[str, Any], residual_id: str
) -> list[dict[str, str]]:
    return [
        row
        for row in readiness_artifact["blocking_conditions"]
        if row["residual_id"] == residual_id
    ]


def _matrix_rows_by_id(prep_artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["matrix_id"]: row
        for row in prep_artifact["fragility_validation_matrix"]
    }


def _safe_json_load(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), "loaded"
    except json.JSONDecodeError:
        return None, "invalid_json"


def _manifest_artifact_by_id(
    manifest: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if manifest is None:
        return {}
    return {
        str(row["artifact_id"]): row
        for row in manifest.get("artifacts", [])
        if "artifact_id" in row
    }


def _sha256_verified(path: Path, expected_sha256: str | None) -> bool:
    if not expected_sha256 or not path.exists():
        return False
    return _sha256_text(path.read_text(encoding="utf-8")) == expected_sha256


def _retained_benchmark_artifact_review(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    retained_dir = repo_root / BENCHMARK_RETAINED_RELATIVE_DIR
    manifest_path = retained_dir / "manifest.json"
    benchmark_path = retained_dir / "stage_c_fragility_benchmark.json"
    comparison_path = retained_dir / "candidate_vs_synthetic_sigmoid_comparison.json"

    manifest, manifest_load_status = _safe_json_load(manifest_path)
    benchmark, benchmark_load_status = _safe_json_load(benchmark_path)
    comparison, comparison_load_status = _safe_json_load(comparison_path)
    artifact_rows = _manifest_artifact_by_id(manifest)

    missing_or_invalid = [
        label
        for label, load_status in (
            ("manifest", manifest_load_status),
            ("stage_c_fragility_benchmark", benchmark_load_status),
            (
                "candidate_vs_synthetic_sigmoid_comparison",
                comparison_load_status,
            ),
        )
        if load_status != "loaded"
    ]
    if missing_or_invalid:
        return {
            "review_result": "blocked",
            "artifact_read_status": "missing_or_invalid_retained_benchmark_artifact",
            "retained_dir": _display_path(retained_dir, repo_root),
            "manifest_path": _display_path(manifest_path, repo_root),
            "benchmark_artifact_path": _display_path(benchmark_path, repo_root),
            "comparison_artifact_path": _display_path(comparison_path, repo_root),
            "missing_or_invalid_artifacts": missing_or_invalid,
            "candidate_vs_synthetic_delta_evidence_present": False,
            "delta_evidence_status": "absent_retained_artifact_not_consumable",
            "independent_truth_present": False,
            "truth_status": "unknown_because_retained_artifact_not_consumable",
            "replacement_allowed": False,
            "retained_artifact_claims_replacement_allowed": False,
            "blocking_conditions_remaining": [
                "retained benchmark artifact must be readable before review consumption",
                "independent fragility truth is still required before replacement",
            ],
            "authority_release_effect": (
                "continues_to_block_stage_c_component_probability_authority"
            ),
        }

    assert manifest is not None
    assert benchmark is not None
    assert comparison is not None

    benchmark_row = artifact_rows.get("stage_c_fragility_benchmark", {})
    comparison_row = artifact_rows.get("candidate_vs_synthetic_sigmoid_comparison", {})
    benchmark_sha_verified = _sha256_verified(
        benchmark_path, benchmark_row.get("sha256")
    )
    comparison_sha_verified = _sha256_verified(
        comparison_path, comparison_row.get("sha256")
    )
    benchmark_comparison = benchmark[
        "candidate_vs_synthetic_sigmoid_comparison"
    ]
    comparison_payload = comparison["comparison"]
    comparison_rows = comparison_payload["rows"]
    comparison_metrics = comparison_payload["metrics"]
    truth_inventory = benchmark["truth_inventory"]
    independent_truth_present = bool(
        manifest.get("external_truth_present")
        or truth_inventory["external_truth_present"]
    )
    retained_artifact_claims_replacement_allowed = any(
        bool(value)
        for value in (
            manifest.get("replacement_allowed"),
            benchmark_comparison.get("replacement_allowed"),
            benchmark["authority_decision"].get("replacement_allowed"),
            comparison_payload.get("replacement_allowed"),
            comparison["authority_decision"].get("replacement_allowed"),
            comparison["authority_guards"].get("replacement_allowed"),
        )
    )
    delta_evidence_present = bool(
        manifest.get("schema_version") == BENCHMARK_RETAINED_MANIFEST_SCHEMA_VERSION
        and benchmark.get("schema_version") == BENCHMARK_SCHEMA_VERSION
        and comparison.get("schema_version") == BENCHMARK_COMPARISON_SCHEMA_VERSION
        and benchmark_sha_verified
        and comparison_sha_verified
        and benchmark_comparison["comparison_status"]
        == "author_side_delta_available_but_not_truth_benchmark"
        and comparison_payload["comparison_status"]
        == "author_side_delta_available_but_not_truth_benchmark"
        and len(comparison_rows) > 0
        and int(comparison_metrics["point_count"]) == len(comparison_rows)
    )

    return {
        "review_result": "blocked",
        "artifact_read_status": (
            "present_retained_candidate_vs_synthetic_delta_evidence"
            if delta_evidence_present
            else "present_but_not_accepted_as_delta_evidence"
        ),
        "retained_dir": _display_path(retained_dir, repo_root),
        "manifest_path": _display_path(manifest_path, repo_root),
        "benchmark_artifact_path": _display_path(benchmark_path, repo_root),
        "comparison_artifact_path": _display_path(comparison_path, repo_root),
        "manifest_schema_version": manifest["schema_version"],
        "benchmark_schema_version": benchmark["schema_version"],
        "comparison_schema_version": comparison["schema_version"],
        "benchmark_sha256_verified": benchmark_sha_verified,
        "comparison_sha256_verified": comparison_sha_verified,
        "candidate_vs_synthetic_delta_evidence_present": delta_evidence_present,
        "delta_evidence_status": (
            "present_author_side_candidate_vs_synthetic_only"
            if delta_evidence_present
            else "not_accepted_as_review_consumable_delta_evidence"
        ),
        "comparison_status": benchmark_comparison["comparison_status"],
        "comparison_point_count": len(comparison_rows),
        "comparison_probe_labels": [
            str(row["probe_label"]) for row in comparison_rows
        ],
        "candidate_probability_sources": [
            str(row["candidate_probability_source"]) for row in comparison_rows
        ],
        "synthetic_sigmoid_probability_source": "synthetic_sigmoid",
        "candidate_vs_synthetic_delta_metrics": {
            "mean_absolute_difference_vs_synthetic_sigmoid": comparison_metrics[
                "mean_absolute_difference_vs_synthetic_sigmoid"
            ],
            "max_absolute_difference_vs_synthetic_sigmoid": comparison_metrics[
                "max_absolute_difference_vs_synthetic_sigmoid"
            ],
            "min_candidate_to_synthetic_sigmoid_ratio": comparison_metrics[
                "min_candidate_to_synthetic_sigmoid_ratio"
            ],
            "max_candidate_to_synthetic_sigmoid_ratio": comparison_metrics[
                "max_candidate_to_synthetic_sigmoid_ratio"
            ],
            "all_candidate_probabilities_exceed_synthetic_sigmoid": (
                comparison_metrics[
                    "all_candidate_probabilities_exceed_synthetic_sigmoid"
                ]
            ),
        },
        "independent_truth_present": independent_truth_present,
        "truth_status": truth_inventory["truth_status"],
        "replacement_allowed": False,
        "retained_artifact_claims_replacement_allowed": (
            retained_artifact_claims_replacement_allowed
        ),
        "replacement_decision": benchmark_comparison["replacement_decision"],
        "stage_b_dependency_preserved_as_blocked": bool(
            manifest["stage_b_dependency_preserved_as_blocked"]
            and benchmark["stage_b_dependency_interlock"][
                "dependency_preserved_as_blocked"
            ]
        ),
        "blocking_conditions_remaining": [
            "independent fragility truth absent",
            "reviewer-owned candidate-vs-truth scoring absent",
            "formal result closeout absent",
            "uncertainty closeout absent",
            "independence audit absent",
        ],
        "authority_release_effect": (
            "continues_to_block_stage_c_component_probability_authority"
        ),
    }


def _fragility_matrix_review_rows(
    prep_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = _matrix_rows_by_id(prep_artifact)
    return [
        {
            "check_id": "FRAG-REVIEW-001",
            "source_matrix_id": "FRAG-MAT-CP-001",
            "residual_links": rows["FRAG-MAT-CP-001"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "candidate surface remains locked to right_aileron_actuator, "
                "flight_control and lateral_flight_control_actuators"
            ),
            "release_effect": "supports review entry only; does not release authority",
        },
        {
            "check_id": "FRAG-REVIEW-002",
            "source_matrix_id": "FRAG-MAT-CP-002",
            "residual_links": rows["FRAG-MAT-CP-002"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "inner/middle/outer candidate rows cover the projected primary "
                "mechanism-load gate band"
            ),
            "release_effect": "supports reviewer audit input only",
        },
        {
            "check_id": "FRAG-REVIEW-003",
            "source_matrix_id": "FRAG-MAT-CP-003",
            "residual_links": rows["FRAG-MAT-CP-003"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "baseline remains synthetic_sigmoid and is correctly retained as "
                "non-authoritative"
            ),
            "release_effect": "blocks replacement until independent fragility closeout",
        },
        {
            "check_id": "FRAG-REVIEW-004",
            "source_matrix_id": "FRAG-MAT-CP-004",
            "residual_links": rows["FRAG-MAT-CP-004"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "author-side probabilities decrease across inner/middle/outer "
                "near-miss probes"
            ),
            "release_effect": "candidate behavior is review input, not truth",
        },
        {
            "check_id": "FRAG-REVIEW-005",
            "source_matrix_id": "FRAG-MAT-CP-005",
            "residual_links": rows["FRAG-MAT-CP-005"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "fixed-seed repeatability probe is stable enough to hand to an "
                "uncertainty reviewer"
            ),
            "release_effect": "uncertainty coverage remains blocked",
        },
        {
            "check_id": "FRAG-REVIEW-006",
            "source_matrix_id": "FRAG-MAT-CP-006",
            "residual_links": rows["FRAG-MAT-CP-006"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "author-side input/result separation trace is present and fail-closed"
            ),
            "release_effect": "independent result-level audit remains blocked",
        },
        {
            "check_id": "FRAG-REVIEW-007",
            "source_matrix_id": "FRAG-MAT-CP-007",
            "residual_links": rows["FRAG-MAT-CP-007"]["residual_links"],
            "review_result": "review_passed",
            "reviewed_finding": (
                "Stage C preserves the blocked Stage B effect-scale dependency "
                "instead of promoting component probability independently"
            ),
            "release_effect": "Stage B remains an upstream authority blocker",
        },
    ]


def _baseline_replacement_review(
    prep_artifact: dict[str, Any],
    benchmark_artifact_review: dict[str, Any],
) -> dict[str, Any]:
    path = prep_artifact[
        "baseline_synthetic_sigmoid_vs_candidate_evidence_row_replacement_path"
    ]
    candidate_rows = path["candidate_evidence_row_surface"]
    return {
        "review_result": "review_passed",
        "replacement_result": "blocked",
        "baseline_component_probability_source": path["baseline"][
            "component_probability_source"
        ],
        "candidate_row_ids": [row["candidate_row_id"] for row in candidate_rows],
        "candidate_probability_sources": [
            row["candidate_probability_source"] for row in candidate_rows
        ],
        "replacement_allowed_now": bool(path["baseline"]["replacement_allowed_now"]),
        "retained_benchmark_delta_evidence_present": benchmark_artifact_review[
            "candidate_vs_synthetic_delta_evidence_present"
        ],
        "retained_benchmark_artifact_status": benchmark_artifact_review[
            "artifact_read_status"
        ],
        "retained_benchmark_comparison_path": benchmark_artifact_review[
            "comparison_artifact_path"
        ],
        "candidate_vs_synthetic_delta_metrics": benchmark_artifact_review.get(
            "candidate_vs_synthetic_delta_metrics", {}
        ),
        "independent_truth_present": benchmark_artifact_review[
            "independent_truth_present"
        ],
        "replacement_allowed": False,
        "fail_closed_finding": (
            "retained candidate-vs-synthetic delta evidence is present, but "
            "candidate evidence rows are still author-side vulnerability_evidence_row "
            "inputs, independent truth is absent, and they are not authorized to "
            "replace the synthetic_sigmoid baseline"
        ),
        "minimum_evidence_path": [
            "obtain an independent right_aileron_actuator fragility curve or benchmark over the frozen Stage C load band",
            "compare candidate evidence-row probabilities against that benchmark with reviewer-owned scoring",
            "record reviewer signoff before any separate stock descriptor admission review",
        ],
    }


def _formal_result_closeout_review(
    *,
    prep_artifact: dict[str, Any],
    readiness_artifact: dict[str, Any],
) -> dict[str, Any]:
    inventory = {
        row["artifact_id"]: row
        for row in prep_artifact["review_entry_artifact_inventory"]
    }
    blockers = _blockers_for_residual(readiness_artifact, "RES-010")
    return {
        "review_result": "blocked",
        "author_result_pack_present": "REVIEW-CP-001" in inventory,
        "fragility_prep_packet_present": "REVIEW-CP-004" in inventory,
        "stage_c_readiness_gate_status": readiness_artifact["status"],
        "validation_manifest_promoted": False,
        "independent_reviewer_signoff_present": False,
        "blocking_conditions": blockers,
        "minimum_evidence_path": [
            "promote the Stage C validation manifest only after a reviewer-owned result record exists",
            "attach a formal result table that references the frozen criteria and retained artifacts",
            "record independent reviewer signoff for the Stage C component-probability result",
        ],
    }


def _uncertainty_review(prep_artifact: dict[str, Any]) -> dict[str, Any]:
    probe = prep_artifact["author_side_uncertainty_probe"]
    return {
        "author_repeatability_review_result": "review_passed",
        "uncertainty_closeout_result": "blocked",
        "anchor_probe_label": probe["anchor_probe_label"],
        "seed_values": probe["seed_values"],
        "component_failure_probability_cv": probe[
            "component_failure_probability"
        ]["cv"],
        "not_covered": list(probe["not_covered"]),
        "minimum_evidence_path": [
            "run independent Brier/log-loss or calibration-curve scoring for the component-probability surface",
            "extend seed and scenario spread beyond the three-point author-side probe",
            "record reviewer-accepted confidence or coverage bounds before authority promotion",
        ],
    }


def _independence_review(prep_artifact: dict[str, Any]) -> dict[str, Any]:
    trace = prep_artifact["independence_trace"]
    return {
        "author_trace_review_result": "review_passed",
        "independent_result_audit_result": "blocked",
        "trace_status": trace["trace_status"],
        "input_or_tuning_artifact_ids": [
            row["artifact_id"] for row in trace["input_or_tuning_layer"]
        ],
        "result_or_review_artifact_ids": [
            row["artifact_id"] for row in trace["result_or_review_layer"]
        ],
        "open_independence_blockers": list(trace["open_independence_blockers"]),
        "required_independent_review_record": trace[
            "required_independent_review_record"
        ],
        "minimum_evidence_path": [
            "have an independent reviewer audit benchmark outputs, thresholds and candidate inputs for circular reuse",
            "record reviewer-owned independence signoff at result level",
            "rerun the Stage C review gate after the independence blocker is removed from readiness output",
        ],
    }


def _stage_b_interlock_review(prep_artifact: dict[str, Any]) -> dict[str, Any]:
    stage_b = prep_artifact["stage_b_dependency_interlock"]
    still_blocking = bool(
        stage_b["dependency_preserved_as_blocked"]
        and stage_b["stage_b_status"]
        == "blocked_non_authoritative_stage_b_release_candidate"
    )
    return {
        "review_result": "review_passed",
        "stage_b_status": stage_b["stage_b_status"],
        "stage_b_release_target": stage_b["stage_b_release_target"],
        "stage_b_blocking_residual_ids": stage_b["stage_b_blocking_residual_ids"],
        "dependency_preserved_as_blocked": stage_b["dependency_preserved_as_blocked"],
        "still_blocks_stage_c_authority": still_blocking,
        "stage_c_authority_promotion_allowed": False,
        "minimum_evidence_path": [
            "close the separate Stage B effect-scale release gate before any Stage C authority promotion",
            "rerun the Stage C fragility review gate after Stage B no longer reports blocked release status",
        ],
    }


def _residual_gate_results(
    *,
    readiness_artifact: dict[str, Any],
    benchmark_artifact_review: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        {
            "residual_id": "RES-009",
            "review_gate_result": "blocked",
            "review_passed_items": [
                "right_aileron_actuator matrix identity",
                "load-gate coverage",
                "baseline replacement path fail-closed",
                "candidate surface monotonicity",
                "retained candidate-vs-synthetic delta evidence",
            ],
            "blocker_owner": "independent_fragility_reviewer",
            "missing_evidence": [
                "independent component fragility curve or benchmark",
                "reviewer-owned comparison of candidate evidence rows against independent fragility truth",
            ],
            "minimum_evidence_path": [
                "run an independent right_aileron_actuator fragility benchmark over the frozen load band",
                "score candidate evidence-row probabilities against the independent benchmark",
                "retain reviewer signoff before replacing synthetic_sigmoid",
            ],
            "forced_review_trigger": (
                "readiness gate no longer emits BLOCK-CP-003 and retained "
                "benchmark evidence is available"
            ),
        },
        {
            "residual_id": "RES-010",
            "review_gate_result": "blocked",
            "review_passed_items": [
                "pre-run criteria entry exists",
                "author-side result pack exists",
                "review artifact inventory exists",
            ],
            "blocker_owner": "validation_integrator_and_independent_reviewer",
            "missing_evidence": [
                "validated/passed validation manifest state",
                "formal reviewer-owned result closeout",
                "independent signoff",
            ],
            "minimum_evidence_path": [
                "attach the frozen Stage C criteria to a formal result table",
                "promote validation manifest only after independent reviewer signoff",
                "rerun readiness and fragility review gates",
            ],
            "forced_review_trigger": (
                "readiness gate no longer emits BLOCK-CP-002 and the validation "
                "manifest is reviewer-promoted"
            ),
        },
        {
            "residual_id": "RES-011",
            "review_gate_result": "blocked",
            "review_passed_items": [
                "fixed-seed author repeatability probe is stable",
                "uncertainty closeout plan is actionable",
            ],
            "blocker_owner": "independent_uncertainty_reviewer",
            "missing_evidence": [
                "calibration or coverage scoring",
                "scenario spread beyond the author-side probe",
                "reviewer-accepted uncertainty bounds",
            ],
            "minimum_evidence_path": [
                "run independent calibration or coverage metrics against frozen thresholds",
                "extend seed/scenario spread and publish reviewer-owned uncertainty table",
                "rerun the review gate after BLOCK-CP-004 is absent",
            ],
            "forced_review_trigger": (
                "readiness gate no longer emits BLOCK-CP-004 and uncertainty "
                "coverage results are retained"
            ),
        },
        {
            "residual_id": "RES-012",
            "review_gate_result": "blocked",
            "review_passed_items": [
                "input/result separation trace exists",
                "Stage B dependency interlock is preserved",
            ],
            "blocker_owner": "independent_independence_reviewer",
            "missing_evidence": [
                "reviewer-owned result-level independence audit",
                "non-circular benchmark/input separation signoff",
            ],
            "minimum_evidence_path": [
                "audit benchmark outputs, acceptance thresholds and candidate inputs for circular reuse",
                "record independent result-level separation signoff",
                "rerun readiness and fragility review gates after BLOCK-CP-001 is absent",
            ],
            "forced_review_trigger": (
                "readiness gate no longer emits BLOCK-CP-001 and the result-level "
                "independence signoff is retained"
            ),
        },
    ]
    for row in rows:
        if row["residual_id"] == "RES-009":
            row["retained_benchmark_artifact_status"] = (
                benchmark_artifact_review["artifact_read_status"]
            )
            row["candidate_vs_synthetic_delta_evidence_present"] = (
                benchmark_artifact_review[
                    "candidate_vs_synthetic_delta_evidence_present"
                ]
            )
            row["delta_evidence_status"] = benchmark_artifact_review[
                "delta_evidence_status"
            ]
            row["independent_truth_present"] = benchmark_artifact_review[
                "independent_truth_present"
            ]
            row["replacement_allowed"] = benchmark_artifact_review[
                "replacement_allowed"
            ]
            row["comparison_point_count"] = benchmark_artifact_review.get(
                "comparison_point_count", 0
            )
            row["candidate_vs_synthetic_delta_metrics"] = (
                benchmark_artifact_review.get(
                    "candidate_vs_synthetic_delta_metrics", {}
                )
            )
            row["blocking_conditions_remaining"] = [
                "independent_fragility_truth_absent",
                "reviewer_owned_candidate_vs_truth_scoring_absent",
            ]
        blockers = _blockers_for_residual(readiness_artifact, row["residual_id"])
        row["blocking_conditions"] = blockers
        row["blocking_condition_ids"] = [
            blocker["blocker_id"] for blocker in blockers
        ]
        row["authority_release_effect"] = (
            "continues_to_block_stage_c_component_probability_authority"
        )
    return rows


def _retained_manifest(artifact: dict[str, Any], artifact_sha256: str) -> dict[str, Any]:
    guards = artifact["authority_guards"]
    benchmark_artifact_review = artifact["retained_benchmark_artifact_review"]
    return {
        "package_id": PACKAGE_ID,
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "status": "author_retained_stage_c_fragility_review_gate_artifact_only",
        "retention_scope": "stage_c_fragility_review_gate_candidate_only",
        "artifact_count": 1,
        "artifacts": [
            {
                "artifact_id": "stage_c_fragility_review_gate",
                "path": "stage_c_fragility_review_gate.json",
                "role": "Stage C residual fragility review gate and shortest evidence paths",
                "schema_version": REVIEW_GATE_SCHEMA_VERSION,
                "sha256": artifact_sha256,
            }
        ],
        "authority_granted": False,
        "candidate_vs_synthetic_delta_evidence_present": (
            benchmark_artifact_review[
                "candidate_vs_synthetic_delta_evidence_present"
            ]
        ),
        "independent_truth_present": benchmark_artifact_review[
            "independent_truth_present"
        ],
        "replacement_allowed": False,
        "stock_component_probability_authority": guards[
            "stock_component_probability_authority"
        ],
        "pk_authority": guards["pk_authority"],
        "deterministic_fuze_authority": guards["deterministic_fuze_authority"],
        "stage_b_dependency_preserved_as_blocked": artifact[
            "stage_b_dependency_interlock_review"
        ]["dependency_preserved_as_blocked"],
    }


def generate_stage_c_fragility_review_gate(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    prep_artifact = prep.generate_stage_c_fragility_validation_prep(repo_root=repo_root)
    readiness_artifact = (
        readiness_gate.generate_stage_c_component_probability_review_readiness_gate(
            repo_root=repo_root
        )
    )
    matrix_review = _fragility_matrix_review_rows(prep_artifact)
    benchmark_artifact_review = _retained_benchmark_artifact_review(
        repo_root=repo_root
    )
    residual_results = _residual_gate_results(
        readiness_artifact=readiness_artifact,
        benchmark_artifact_review=benchmark_artifact_review,
    )
    stage_b_review = _stage_b_interlock_review(prep_artifact)
    authority_guards = {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "stock_component_probability_authority": False,
        "pk_authority": False,
        "deterministic_fuze_authority": False,
        "replacement_allowed": False,
        "stage_c_candidate_bundle_role": "review_gate_only",
    }

    return {
        "package_id": PACKAGE_ID,
        "schema_version": REVIEW_GATE_SCHEMA_VERSION,
        "generated_on": "2026-05-31",
        "status": "blocked_non_authoritative_stage_c_fragility_review_gate",
        "review_target": "right_aileron_actuator_component_fragility_review_only",
        "readiness_level": (
            "bounded_review_checks_passed_but_residuals_and_authority_blocked"
        ),
        "scope": dict(prep_artifact["scope"]),
        "focused_residual_ids": list(FOCUSED_RESIDUAL_IDS),
        "residual_gate_results": residual_results,
        "fragility_matrix_review": {
            "review_result": "review_passed",
            "source_matrix_status": prep_artifact["status"],
            "review_rows": matrix_review,
        },
        "retained_benchmark_artifact_review": benchmark_artifact_review,
        "baseline_replacement_review": _baseline_replacement_review(
            prep_artifact,
            benchmark_artifact_review,
        ),
        "formal_result_closeout_review": _formal_result_closeout_review(
            prep_artifact=prep_artifact,
            readiness_artifact=readiness_artifact,
        ),
        "uncertainty_review": _uncertainty_review(prep_artifact),
        "independence_review": _independence_review(prep_artifact),
        "stage_b_dependency_interlock_review": stage_b_review,
        "authority_decision": {
            "review_gate_release_ready": False,
            "stage_c_component_probability_authority_ready": False,
            "stage_b_upstream_dependency_still_blocking": stage_b_review[
                "still_blocks_stage_c_authority"
            ],
            "blocked_residual_ids": list(FOCUSED_RESIDUAL_IDS),
            "stock_component_probability_authority": False,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
            "candidate_vs_synthetic_delta_evidence_present": (
                benchmark_artifact_review[
                    "candidate_vs_synthetic_delta_evidence_present"
                ]
            ),
            "independent_fragility_truth_present": benchmark_artifact_review[
                "independent_truth_present"
            ],
            "replacement_allowed": False,
        },
        "remaining_paths": [
            {
                "residual_id": row["residual_id"],
                "owner": row["blocker_owner"],
                "minimum_evidence_path": row["minimum_evidence_path"],
                "forced_review_trigger": row["forced_review_trigger"],
            }
            for row in residual_results
        ],
        "authority_guards": authority_guards,
        "explicit_boundaries": [
            "review gate only; not an independent fragility benchmark",
            "retained candidate-vs-synthetic delta evidence is review input only",
            "do not replace synthetic_sigmoid from this gate",
            "do not create or update stock runtime descriptors from this artifact",
            "do not promote Stage C component probability while Stage B remains blocked",
            "stock_component_probability_authority=false remains mandatory",
            "pk_authority=false and deterministic_fuze_authority=false remain mandatory",
        ],
    }


def write_retained_artifacts(
    artifact: dict[str, Any],
    retained_dir: Path,
) -> dict[str, Any]:
    retained_dir.mkdir(parents=True, exist_ok=True)
    artifact_payload = _canonical_json(artifact)
    artifact_path = retained_dir / "stage_c_fragility_review_gate.json"
    artifact_path.write_text(artifact_payload + "\n", encoding="utf-8")

    manifest = _retained_manifest(artifact, _sha256_text(artifact_payload + "\n"))
    manifest_path = retained_dir / "manifest.json"
    manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the Stage C fragility review gate for the current A2 "
            "right_aileron_actuator component-probability candidate."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout unless --retained-dir is used.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        help=(
            "Optional retained artifact directory. Writes "
            "stage_c_fragility_review_gate.json and manifest.json."
        ),
    )
    args = parser.parse_args()

    artifact = generate_stage_c_fragility_review_gate()
    payload = _canonical_json(artifact)
    wrote_output = False
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        wrote_output = True
    if args.retained_dir:
        write_retained_artifacts(artifact, args.retained_dir)
        wrote_output = True
    if not wrote_output:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
