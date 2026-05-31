#!/usr/bin/env python3
"""Close out RES-011/012 independent review evidence for bounded Stage B only.

This gate consumes retained Stage B independent review, Stage B release
closeout, uncertainty review, Stage C fragility, and provenance gates. It can
close RES-011 uncertainty and RES-012 benchmark/input separation only for the
Stage B effect-scale review surface. Stage C component probability remains
blocked unless probability uncertainty, independent fragility truth, and
result-level independence are all present.
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


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
GATE_SCHEMA_VERSION = "a2.res011012_independent_review_closeout_gate.v1"
MANIFEST_SCHEMA_VERSION = (
    "a2.res011012_independent_review_closeout_retained_manifest.v1"
)
GENERATED_ON = "2026-05-31"
PACKAGE_DIR = (
    REPO_ROOT
    / "docs"
    / "task"
    / "air_combat"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
DEFAULT_RETAINED_DIR = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "res011012_independent_review_closeout_20260531"
)


EVIDENCE_REFS = {
    "stage_b_independent_review_gate": (
        "stage_b_independent_review_20260531/stage_b_independent_review_gate.json"
    ),
    "stage_b_independent_review_manifest": (
        "stage_b_independent_review_20260531/manifest.json"
    ),
    "stage_b_release_closeout": (
        "stage_b_effect_scale_20260531/stage_b_release_closeout.json"
    ),
    "uncertainty_review_gate": "uncertainty_review_20260531/uncertainty_review_gate.json",
    "uncertainty_review_manifest": "uncertainty_review_20260531/manifest.json",
    "stage_c_fragility_review_gate": (
        "stage_c_fragility_review_20260531/stage_c_fragility_review_gate.json"
    ),
    "stage_c_fragility_review_manifest": (
        "stage_c_fragility_review_20260531/manifest.json"
    ),
    "stage_c_fragility_validation_prep": (
        "stage_c_fragility_validation_prep_20260531/"
        "stage_c_fragility_validation_prep.json"
    ),
    "stage_c_fragility_validation_prep_manifest": (
        "stage_c_fragility_validation_prep_20260531/manifest.json"
    ),
    "stage_c_fragility_benchmark": (
        "stage_c_fragility_benchmark_20260531/stage_c_fragility_benchmark.json"
    ),
    "provenance_identity_review_gate": (
        "provenance_identity_review_20260531/provenance_identity_review_gate.json"
    ),
    "geometry_warhead_row_provenance_gate": (
        "geometry_warhead_row_provenance_20260531/"
        "geometry_warhead_row_provenance_gate.json"
    ),
    "mechanism_source_closeout_gate": (
        "mechanism_source_closeout_20260531/mechanism_source_closeout_gate.json"
    ),
    "source_rights_output_policy_gate": (
        "source_rights_output_policy_20260531/source_rights_output_policy_gate.json"
    ),
}


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _retained_path(package_dir: Path, rel: str) -> Path:
    return package_dir / "retained_artifacts" / rel


def _authority_guards() -> dict[str, bool]:
    return {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "stock_runtime_authority_granted": False,
        "runtime_authority_granted": False,
        "effect_scale_authority_granted": False,
        "effect_scale_authority_in_stock": False,
        "effect_scale_authority_released": False,
        "component_failure_probability_authority_granted": False,
        "component_failure_probability_authority_in_stock": False,
        "component_failure_probability_authority_released": False,
        "stock_component_probability_authority": False,
        "pk_authority_granted": False,
        "pk_authority_released": False,
        "deterministic_fuze_authority_granted": False,
        "deterministic_fuze_authority_released": False,
        "formal_validation_manifest_promoted": False,
        "hard_gate_pass_is_release": False,
        "replacement_allowed": False,
    }


def _guard_has_no_true_values(guards: dict[str, Any] | None) -> bool:
    if not guards:
        return False
    return not any(value is True for value in guards.values())


def _evidence_record(
    *,
    evidence_id: str,
    path: Path,
    repo_root: Path,
    required_for: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "evidence_id": evidence_id,
        "path": _display_path(path, repo_root),
        "present": path.is_file(),
        "required_for": required_for,
    }
    if path.is_file():
        record["content_sha256"] = _file_sha256(path)
    if payload is None:
        record["status"] = "missing"
    else:
        record["schema_version"] = payload.get("schema_version", "")
        record["status"] = payload.get("status", "")
    return record


def _check(check_id: str, summary: str, passed: bool) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "summary": summary,
        "pass": bool(passed),
    }


def _missing_evidence(consumed_evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "evidence_id": row["evidence_id"],
            "path": row["path"],
            "blocker": f"{row['required_for']} evidence is missing",
        }
        for row in consumed_evidence
        if not row["present"]
    ]


def _artifact_map(
    *,
    repo_root: Path,
    package_dir: Path,
) -> tuple[dict[str, dict[str, Any] | None], list[dict[str, Any]]]:
    payloads: dict[str, dict[str, Any] | None] = {}
    consumed: list[dict[str, Any]] = []
    required_for = {
        "stage_b_independent_review_gate": "Stage B RES-011/012 independent review pass",
        "stage_b_independent_review_manifest": "retained Stage B review provenance",
        "stage_b_release_closeout": "Stage B author-side release closeout evidence",
        "uncertainty_review_gate": "RES-011 split Stage B/Stage C uncertainty decision",
        "uncertainty_review_manifest": "retained RES-011 uncertainty review provenance",
        "stage_c_fragility_review_gate": "Stage C RES-011/012 blocking decision",
        "stage_c_fragility_review_manifest": "retained Stage C fragility review provenance",
        "stage_c_fragility_validation_prep": "Stage C review-prep uncertainty and independence trace",
        "stage_c_fragility_validation_prep_manifest": "retained Stage C prep provenance",
        "stage_c_fragility_benchmark": "Stage C independent truth inventory",
        "provenance_identity_review_gate": "RES-001/002 provenance and identity interlock",
        "geometry_warhead_row_provenance_gate": "RES-003/004 provenance interlock",
        "mechanism_source_closeout_gate": "RES-003/004/005/006 mechanism-source interlock",
        "source_rights_output_policy_gate": "RES-001 rights and output-policy interlock",
    }
    for evidence_id, rel in EVIDENCE_REFS.items():
        path = _retained_path(package_dir, rel)
        payload = _load_json(path)
        payloads[evidence_id] = payload
        consumed.append(
            _evidence_record(
                evidence_id=evidence_id,
                path=path,
                repo_root=repo_root,
                required_for=required_for[evidence_id],
                payload=payload,
            )
        )
    return payloads, consumed


def _stage_b_closeout(payloads: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    independent = payloads["stage_b_independent_review_gate"] or {}
    closeout = payloads["stage_b_release_closeout"] or {}
    uncertainty_gate = payloads["uncertainty_review_gate"] or {}

    review_decision = independent.get("review_decision", {})
    release_decision = independent.get("release_decision", {})
    res011 = independent.get("uncertainty_review", {})
    res012 = independent.get("benchmark_input_independence_review", {})
    closeout_uncertainty = closeout.get("uncertainty_closeout", {})
    closeout_independence = closeout.get("independence_review_dependency_trace", {})
    uncertainty_decision = uncertainty_gate.get("review_decision", {})
    uncertainty_residual = uncertainty_gate.get("residual_status", {})
    passed_ids = set(review_decision.get("review_passed_residual_ids", []))
    blocked_ids = set(review_decision.get("review_blocked_residual_ids", []))

    checks = [
        _check(
            "RES011012-B-001",
            "retained Stage B independent review completed with no focused blocked residuals",
            independent.get("status") == "independent_review_passed_release_blocked"
            and review_decision.get("independent_review_complete") is True
            and review_decision.get("focused_review_passed") is True
            and not blocked_ids,
        ),
        _check(
            "RES011012-B-002",
            "RES-011 and RES-012 are included in the Stage B review-passed residual set",
            {"RES-011", "RES-012"}.issubset(passed_ids),
        ),
        _check(
            "RES011012-B-003",
            "Stage B RES-011 seed-window CV evidence passes retained thresholds",
            res011.get("review_gate_result") == "review_passed"
            and res011.get("seed_window_cv_pass") is True
            and all(row.get("pass") is True for row in res011.get("cv_rows", []))
            and closeout_uncertainty.get("author_side_closeout_complete") is True,
        ),
        _check(
            "RES011012-B-004",
            "Stage B RES-012 benchmark/input separation review passes while preserving forbidden claims",
            res012.get("review_gate_result") == "review_passed"
            and closeout_independence.get("author_side_closeout_complete") is True
            and res012.get("release_gate_result")
            == "blocked_by_provenance_identity_and_source_residuals",
        ),
        _check(
            "RES011012-B-005",
            "uncertainty gate agrees that Stage B author-side closeout is complete but not release-grade uncertainty authority",
            uncertainty_gate.get("status")
            == "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
            and uncertainty_decision.get(
                "stage_b_author_side_uncertainty_closeout_complete"
            )
            is True
            and uncertainty_decision.get("stage_b_release_grade_uncertainty_complete")
            is False
            and uncertainty_residual.get("stage_b_decision")
            == "narrow_author_side_pass_release_blocked",
        ),
        _check(
            "RES011012-B-006",
            "Stage B release closeout remains effect-scale-only and release-blocked",
            closeout.get("status")
            == "author_side_stage_b_release_closeout_complete_release_blocked"
            and closeout.get("release_target") == "effect_scale_authority_only"
            and release_decision.get("stage_c_component_probability_release_included")
            is False
            and release_decision.get("release_blocked") is True,
        ),
        _check(
            "RES011012-B-007",
            "retained Stage B guards do not grant stock/runtime/component/Pk/fuze authority",
            _guard_has_no_true_values(independent.get("non_authoritative_guards"))
            and _guard_has_no_true_values(closeout.get("non_authoritative_guards")),
        ),
    ]
    closeable = all(row["pass"] for row in checks)
    return {
        "stage": "stage_b_effect_scale",
        "decision": (
            "closeable_for_stage_b_effect_scale_independent_review_only"
            if closeable
            else "fail_closed_stage_b_res011012_evidence_incomplete"
        ),
        "closeout_allowed": closeable,
        "closed_scope": (
            "RES-011 uncertainty and RES-012 benchmark/input separation are "
            "closed only for the retained Stage B effect-scale review surface"
        ),
        "res011_stage_b_effect_scale_closeout": closeable,
        "res012_stage_b_effect_scale_closeout": closeable,
        "res011_basis": {
            "source": "retained Stage B independent review plus RES-011 uncertainty review gate",
            "seed_window_cv_pass": res011.get("seed_window_cv_pass", False),
            "release_grade_uncertainty_complete": False,
        },
        "res012_basis": {
            "source": "retained Stage B independent review benchmark/input separation audit",
            "review_gate_result": res012.get("review_gate_result", ""),
            "external_validation_claimed": False,
        },
        "release_authority_effect": "none_review_closeout_record_only",
        "stage_c_component_probability_included": False,
        "checks": checks,
        "forbidden_promotions": [
            "stock descriptor admission",
            "component probability authority",
            "Pk authority",
            "deterministic fuze authority",
            "external validation claim",
            "formal validation manifest promotion",
        ],
    }


def _stage_c_closeout(payloads: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    fragility_review = payloads["stage_c_fragility_review_gate"] or {}
    fragility_prep = payloads["stage_c_fragility_validation_prep"] or {}
    fragility_benchmark = payloads["stage_c_fragility_benchmark"] or {}
    uncertainty_gate = payloads["uncertainty_review_gate"] or {}

    authority = fragility_review.get("authority_decision", {})
    benchmark_authority = fragility_benchmark.get("authority_decision", {})
    truth = fragility_benchmark.get("truth_inventory", {})
    residual_rows = {
        row.get("residual_id"): row
        for row in fragility_review.get("residual_gate_results", [])
    }
    prep_rows = {
        row.get("residual_id"): row
        for row in fragility_prep.get("residual_gate_results", [])
    }
    uncertainty = fragility_review.get("uncertainty_review", {})
    independence = fragility_review.get("independence_review", {})
    uncertainty_decision = uncertainty_gate.get("review_decision", {})

    checks = [
        _check(
            "RES011012-C-001",
            "Stage C fragility review remains blocked for RES-011 and RES-012",
            fragility_review.get("status")
            == "blocked_non_authoritative_stage_c_fragility_review_gate"
            and residual_rows.get("RES-011", {}).get("review_gate_result") == "blocked"
            and residual_rows.get("RES-012", {}).get("review_gate_result") == "blocked",
        ),
        _check(
            "RES011012-C-002",
            "Stage C prep records RES-011/012 as blocked non-authoritative review inputs",
            fragility_prep.get("status")
            == "prepared_non_authoritative_stage_c_fragility_validation_review_inputs"
            and prep_rows.get("RES-011", {}).get("current_gate_result")
            == "blocked_non_authoritative"
            and prep_rows.get("RES-012", {}).get("current_gate_result")
            == "blocked_non_authoritative",
        ),
        _check(
            "RES011012-C-003",
            "probability uncertainty is repeatable author-side only and lacks release-grade coverage",
            uncertainty.get("author_repeatability_review_result") == "review_passed"
            and uncertainty.get("uncertainty_closeout_result") == "blocked"
            and uncertainty_decision.get("stage_c_release_grade_uncertainty_complete")
            is False,
        ),
        _check(
            "RES011012-C-004",
            "independent fragility truth is absent and replacement is not allowed",
            authority.get("independent_fragility_truth_present") is False
            and authority.get("replacement_allowed") is False
            and truth.get("external_truth_present") is False
            and benchmark_authority.get("replacement_allowed") is False,
        ),
        _check(
            "RES011012-C-005",
            "result-level benchmark/input independence remains blocked",
            independence.get("author_trace_review_result") == "review_passed"
            and independence.get("independent_result_audit_result") == "blocked",
        ),
        _check(
            "RES011012-C-006",
            "Stage C grants no stock/component/Pk/fuze authority",
            _guard_has_no_true_values(fragility_review.get("authority_guards"))
            and _guard_has_no_true_values(fragility_prep.get("authority_guards"))
            and _guard_has_no_true_values(fragility_benchmark.get("authority_guards")),
        ),
    ]
    blocked = all(row["pass"] for row in checks)
    return {
        "stage": "stage_c_component_probability",
        "decision": (
            "blocked_probability_uncertainty_fragility_truth_and_independence_missing"
            if blocked
            else "fail_closed_stage_c_evidence_state_unexpected"
        ),
        "closeout_allowed": False,
        "res011_stage_c_closeout": False,
        "res012_stage_c_closeout": False,
        "blocked_residual_ids": sorted(
            set(authority.get("blocked_residual_ids", []))
            | {"RES-009", "RES-010", "RES-011", "RES-012"}
        ),
        "blocking_evidence": {
            "probability_uncertainty_release_grade_complete": False,
            "author_repeatability_present": uncertainty.get(
                "author_repeatability_review_result"
            )
            == "review_passed",
            "component_failure_probability_cv": uncertainty.get(
                "component_failure_probability_cv"
            ),
            "independent_fragility_truth_present": False,
            "replacement_allowed": False,
            "result_level_independence_audit_complete": False,
        },
        "minimum_evidence_to_unblock": [
            "independent component fragility curve or benchmark over the frozen Stage C load band",
            "probability uncertainty coverage with reviewer-accepted bounds",
            "result-level benchmark/input separation signoff proving non-circularity",
            "formal Stage C validation result promotion after independent review",
        ],
        "checks": checks,
    }


def _provenance_interlock(payloads: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    provenance = payloads["provenance_identity_review_gate"] or {}
    geometry = payloads["geometry_warhead_row_provenance_gate"] or {}
    mechanism = payloads["mechanism_source_closeout_gate"] or {}
    rights = payloads["source_rights_output_policy_gate"] or {}
    geometry_status = geometry.get("residual_status", {})

    checks = [
        _check(
            "RES011012-PROV-001",
            "RES-001/002 provenance and identity review remains release-grade blocked",
            provenance.get("status")
            == "blocked_non_authoritative_provenance_identity_review_gate"
            and provenance.get("review_decision", {}).get("release_grade_review_blocked")
            is True,
        ),
        _check(
            "RES011012-PROV-002",
            "source rights and allowed-output policy remains fail-closed for release",
            rights.get("status")
            == "blocked_release_candidate_rights_supported_policy_fail_closed",
        ),
        _check(
            "RES011012-PROV-003",
            "geometry and warhead row provenance keeps RES-003/004 open",
            geometry.get("status")
            == "blocked_non_authoritative_geometry_warhead_row_provenance_candidate"
            and geometry_status.get("RES-003", {}).get("closed_by_this_gate") is False
            and geometry_status.get("RES-004", {}).get("closed_by_this_gate") is False,
        ),
        _check(
            "RES011012-PROV-004",
            "mechanism-source closeout remains non-authoritative",
            mechanism.get("status")
            == "blocked_non_authoritative_mechanism_source_closeout_candidate",
        ),
        _check(
            "RES011012-PROV-005",
            "provenance gates grant no stock/component/Pk/fuze authority",
            _guard_has_no_true_values(provenance.get("non_authoritative_guards"))
            and _guard_has_no_true_values(rights.get("non_authoritative_guards"))
            and _guard_has_no_true_values(mechanism.get("non_authoritative_guards")),
        ),
    ]
    return {
        "decision": (
            "provenance_interlocks_preserved_release_blocked"
            if all(row["pass"] for row in checks)
            else "fail_closed_provenance_interlock_unexpected"
        ),
        "release_ready": False,
        "release_blocked": True,
        "blocking_residual_ids": [
            "RES-001",
            "RES-002",
            "RES-003",
            "RES-004",
            "RES-005",
            "RES-006",
        ],
        "checks": checks,
    }


def generate_res011012_independent_review_closeout_gate(
    *,
    repo_root: Path = REPO_ROOT,
    package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
    payloads, consumed_evidence = _artifact_map(
        repo_root=repo_root,
        package_dir=package_dir,
    )
    missing = _missing_evidence(consumed_evidence)
    stage_b = _stage_b_closeout(payloads)
    stage_c = _stage_c_closeout(payloads)
    provenance = _provenance_interlock(payloads)

    stage_b_pass = stage_b["closeout_allowed"] is True
    stage_c_blocked = stage_c["decision"] == (
        "blocked_probability_uncertainty_fragility_truth_and_independence_missing"
    )
    provenance_blocked = (
        provenance["decision"] == "provenance_interlocks_preserved_release_blocked"
    )
    pass_gate = not missing and stage_b_pass and stage_c_blocked and provenance_blocked

    return {
        "package_id": PACKAGE_ID,
        "schema_version": GATE_SCHEMA_VERSION,
        "generated_on": GENERATED_ON,
        "status": (
            "res011012_stage_b_effect_scale_closeout_pass_stage_c_blocked_release_blocked"
            if pass_gate
            else "res011012_independent_review_closeout_fail_closed"
        ),
        "review_target": "RES-011_RES-012_independent_review_closeout_gate",
        "release_target": "stage_b_effect_scale_review_closeout_only",
        "reviewer_identity": {
            "worker_id": "A2-RES011012-INDEPENDENT-REVIEW-CLOSEOUT",
            "nickname": "res011012-closeout-reviewer",
            "independence_class": "project_internal_independent_review_worker",
            "external_validation_claimed": False,
            "note": (
                "Reviewer identity is project-internal; this gate does not claim "
                "external validation or third-party certification."
            ),
        },
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "candidate_scope_label": "near_miss_0_35m",
            "stage_b_scope": "effect_scale_only",
            "stage_c_scope": "right_aileron_actuator_component_probability",
        },
        "consumed_evidence": consumed_evidence,
        "missing_evidence": missing,
        "stage_b_effect_scale_closeout": stage_b,
        "stage_c_component_probability_closeout": stage_c,
        "provenance_interlock": provenance,
        "residual_closeout_decisions": {
            "RES-011": {
                "stage_b_effect_scale": (
                    "closed_for_bounded_independent_review_closeout"
                    if stage_b_pass
                    else "fail_closed"
                ),
                "stage_c_component_probability": "blocked",
                "package_release_grade": "remains_open_release_blocked",
                "residual_register_edit_required_by_this_gate": False,
            },
            "RES-012": {
                "stage_b_effect_scale": (
                    "closed_for_bounded_independent_review_closeout"
                    if stage_b_pass
                    else "fail_closed"
                ),
                "stage_c_component_probability": "blocked",
                "package_release_grade": "remains_open_release_blocked",
                "residual_register_edit_required_by_this_gate": False,
            },
        },
        "closeout_decision": {
            "stage_b_effect_scale_res011012_closeout_complete": stage_b_pass,
            "stage_b_effect_scale_closeout_is_release_authority": False,
            "stage_c_res011012_closeout_complete": False,
            "stage_c_blocked_until_evidence_present": True,
            "res011012_package_release_grade_complete": False,
            "release_ready": False,
            "release_blocked": True,
        },
        "authority_guards": _authority_guards(),
        "explicit_boundaries": [
            "Stage B closeout is limited to retained effect-scale independent review evidence",
            "Stage B closeout does not grant stock/runtime authority or external validation",
            "Stage C remains blocked without probability uncertainty coverage and independent fragility truth",
            "Benchmark/input separation closure for Stage B does not close Stage C result-level independence",
            "No stock, component-probability, Pk, deterministic-fuze, or formal validation authority is released",
        ],
        "integration_notes": [
            "Do not edit residual_register.zh.md from this gate; use the retained JSON as closeout evidence.",
            "Downstream release integration may cite the Stage B RES-011/012 bounded closeout only for effect-scale review.",
            "Any Stage C promotion must rerun after independent fragility truth, probability uncertainty bounds, and result-level independence signoff exist.",
        ],
    }


def write_retained_artifacts(
    *,
    output_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
    gate = generate_res011012_independent_review_closeout_gate(
        repo_root=repo_root,
        package_dir=package_dir,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_path = output_dir / "res011012_independent_review_closeout_gate.json"
    gate_path.write_text(_canonical_json(gate) + "\n", encoding="utf-8")

    manifest = {
        "package_id": PACKAGE_ID,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "status": "res011012_independent_review_closeout_retained_release_blocked",
        "generated_on": GENERATED_ON,
        "artifact_dir": _display_path(output_dir, repo_root),
        "retention_scope": "RES-011_RES-012_stage_b_effect_scale_review_closeout_only",
        "artifacts": [
            {
                "artifact_key": "res011012_independent_review_closeout_gate",
                "filename": gate_path.name,
                "relative_path": _display_path(gate_path, repo_root),
                "schema_version": GATE_SCHEMA_VERSION,
                "status": gate["status"],
                "content_sha256": _file_sha256(gate_path),
                "payload_sha256": _payload_sha256(gate),
                "size_bytes": gate_path.stat().st_size,
                "origin_class": "project_internal_independent_review_closeout_gate",
                "allowed_claim": (
                    "RES-011/012 are closed only for bounded Stage B "
                    "effect-scale independent review closeout"
                ),
                "forbidden_claim": (
                    "external validation, Stage C component-probability release, "
                    "stock runtime authority, Pk authority, deterministic-fuze "
                    "authority, or formal validation manifest promotion"
                ),
            }
        ],
        "reviewer_identity": dict(gate["reviewer_identity"]),
        "closeout_decision": dict(gate["closeout_decision"]),
        "authority_guards": _authority_guards(),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
    return {
        "gate": gate,
        "manifest": manifest,
        "paths": {"gate": gate_path, "manifest": manifest_path},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate retained RES-011/012 independent review closeout gate artifacts."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained JSON artifacts.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also print the gate JSON after writing retained artifacts.",
    )
    args = parser.parse_args()

    result = write_retained_artifacts(output_dir=args.output_dir)
    gate = result["gate"]
    if args.stdout:
        print(_canonical_json(gate))
    else:
        print(
            json.dumps(
                {
                    "status": gate["status"],
                    "gate": _display_path(result["paths"]["gate"], REPO_ROOT),
                    "manifest": _display_path(result["paths"]["manifest"], REPO_ROOT),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
