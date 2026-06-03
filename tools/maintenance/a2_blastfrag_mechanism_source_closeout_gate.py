#!/usr/bin/env python3
"""Evaluate the A2 blast-fragmentation mechanism/source closeout gate.

This gate consolidates the current RES-003 / RES-004 / RES-005 / RES-006
evidence surface into one auditable artifact. It records author-side evidence
that is already present, while failing closed for calibrated authority: it does
not release target-geometry authority, AIM-120C warhead authority, fragment or
blast mechanism authority, Pk authority, or deterministic-fuze authority.
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

from tools.maintenance import a2_candidate_vps_bundle as candidate_bundle  # noqa: E402


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.mechanism_source_closeout_gate.v1"
RESIDUAL_IDS = ("RES-003", "RES-004", "RES-005", "RES-006")


def _package_dir(repo_root: Path) -> Path:
    return (
        repo_root
        / "docs"
        / "task"
        / "air_combat"
        / "archive"
        / "a2_high_fidelity_damage_model"
        / "calibration"
        / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
    )


def _a2_root(repo_root: Path) -> Path:
    return (
        repo_root
        / "docs"
        / "task"
        / "air_combat"
        / "archive"
        / "a2_high_fidelity_damage_model"
    )


def _doc_refs(repo_root: Path) -> dict[str, Path]:
    package_dir = _package_dir(repo_root)
    a2_root = _a2_root(repo_root)
    data_root = a2_root / "data_collection"
    return {
        "residual_register": package_dir / "residual_register.zh.md",
        "artifact_pin_manifest": (
            package_dir / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
        ),
        "target_geometry_assumptions": (
            package_dir / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md"
        ),
        "warhead_scope_and_sensitivity": (
            package_dir / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md"
        ),
        "stage_b_result_pack": (
            package_dir / "validation_result_pack_stage_b_effect_scale_20260530.zh.md"
        ),
        "stage_c_result_pack": (
            package_dir
            / "validation_result_pack_stage_c_component_probability_20260530.zh.md"
        ),
        "target_geometry_source_ledger": (
            data_root / "f16c_block50_target_geometry" / "source_ledger.zh.md"
        ),
        "warhead_source_ledger": (
            data_root / "aim120c_warhead_fuze" / "source_ledger.zh.md"
        ),
        "vps_blastfrag_source_ledger": (
            data_root / "vps_blast_fragmentation_methods" / "source_ledger.zh.md"
        ),
        "mechanism_model_source_ledger": (
            data_root / "mechanism_model_public_methods" / "source_ledger.zh.md"
        ),
        "source_trace_manifest_gate": (
            a2_root / "validation" / "bfm_bm_006_source_trace_manifest_gate_20260528.zh.md"
        ),
    }


def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


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
            return cells[1]
    return ""


def _scan_placeholder_hits(paths: list[Path], repo_root: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    patterns = (
        re.compile(r"<待填>"),
        re.compile(r"<待定义>"),
        re.compile(r"模板"),
    )
    for path in paths:
        for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                hits.append(
                    {
                        "path": _rel(path, repo_root),
                        "line": line_no,
                        "content": line.strip(),
                    }
                )
    return hits


def _find_source_row(text: str, source_id: str) -> str:
    pattern = re.compile(rf"\|\s*`{re.escape(source_id)}`\s*\|")
    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()
    return ""


def _source_evidence(
    *,
    ledger_ref: Path,
    source_ids: list[str],
    repo_root: Path,
) -> dict[str, Any]:
    text = _read_text(ledger_ref)
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        row = _find_source_row(text, source_id)
        normalized = row.lower()
        rows.append(
            {
                "source_id": source_id,
                "present": bool(row),
                "candidate_boundary_present": bool(
                    row
                    and (
                        "candidate" in normalized
                        or "sanity" in normalized
                        or "pending" in normalized
                        or "non-authoritative" in normalized
                        or "候选" in row
                        or "不是" in row
                        or "不能" in row
                        or "不得" in row
                    )
                ),
                "rejected_or_pending": bool(
                    row
                    and (
                        "pending" in normalized
                        or "rejected" in normalized
                        or "not_admitted" in normalized
                        or "拒绝" in row
                        or "未固定" in row
                    )
                ),
            }
        )
    return {
        "ledger_ref": _rel(ledger_ref, repo_root),
        "selected_source_ids": list(source_ids),
        "present_source_ids": [row["source_id"] for row in rows if row["present"]],
        "missing_source_ids": [row["source_id"] for row in rows if not row["present"]],
        "candidate_boundary_source_ids": [
            row["source_id"] for row in rows if row["candidate_boundary_present"]
        ],
        "rejected_or_pending_source_ids": [
            row["source_id"] for row in rows if row["rejected_or_pending"]
        ],
        "ledger_has_non_authoritative_boundary": "non-authoritative" in text.lower(),
        "rows": rows,
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


def _pin_evidence(rows: list[dict[str, str]], residual_id: str) -> dict[str, Any]:
    selected = [row for row in rows if residual_id in row["residuals"]]
    return {
        "pin_ids": [row["artifact_id"] for row in selected],
        "verified_candidate_artifact_ids": [
            row["artifact_id"]
            for row in selected
            if "verified_candidate_artifact" in row["artifact_status"]
            or row["artifact_status"] == "official_public_pdf"
        ],
        "release_consumed_pin_ids": [
            row["artifact_id"]
            for row in selected
            if row["consumption_status"]
            in {
                "release_retained_benchmark_input",
                "release_grade_benchmark_input",
                "consumed_for_release_benchmark",
            }
        ],
        "retention_pending_pin_ids": [
            row["artifact_id"]
            for row in selected
            if "retention_pending" in row["artifact_status"]
        ],
        "sanity_only_pin_ids": [
            row["artifact_id"] for row in selected if row["consumption_status"] == "sanity_only"
        ],
        "rejected_pin_ids": [
            row["artifact_id"] for row in selected if row["consumption_status"] == "rejected"
        ],
        "authority_boundaries": {
            row["artifact_id"]: row["authority_boundary"] for row in selected
        },
    }


def _status(author_side_satisfied: bool, release_grade_satisfied: bool) -> str:
    if release_grade_satisfied:
        return "closed_by_this_gate"
    if author_side_satisfied:
        return "blocked_release_grade_evidence_missing"
    return "blocked_author_side_evidence_missing"


def _condition(
    *,
    check_id: str,
    residual_id: str,
    closeout_surface: str,
    author_side_satisfied: bool,
    release_grade_satisfied: bool,
    observed_author_side_evidence: dict[str, Any],
    remaining_release_grade_requirements: list[str],
    blocking_summary: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "residual_id": residual_id,
        "closeout_surface": closeout_surface,
        "author_side_satisfied": author_side_satisfied,
        "release_grade_satisfied": release_grade_satisfied,
        "status": _status(author_side_satisfied, release_grade_satisfied),
        "observed_author_side_evidence": observed_author_side_evidence,
        "remaining_release_grade_requirements": remaining_release_grade_requirements,
        "blocking_summary": blocking_summary,
    }


def _closeout_checks(
    *,
    bundle: dict[str, Any],
    refs: dict[str, Path],
    repo_root: Path,
) -> list[dict[str, Any]]:
    pin_rows = _parse_artifact_pin_rows(_read_text(refs["artifact_pin_manifest"]))
    target_assumptions = bundle["target_geometry_assumption_summary"]
    warhead_scope = bundle["warhead_scope_summary"]
    stage_b_snapshot = bundle["validation_benchmark_snapshot_summary"]
    stage_b_result_pack = bundle["validation_result_pack_summary"]
    stage_c_result_pack = bundle[
        "validation_stage_c_component_probability_result_pack_summary"
    ]
    scaffold_summary = bundle["validation_scaffold_summary"]
    mechanism_vector = scaffold_summary["mechanism_load_vector"]

    target_sources = _source_evidence(
        ledger_ref=refs["target_geometry_source_ledger"],
        source_ids=[
            "F16-TG-SRC-001",
            "F16-TG-SRC-002",
            "F16-TG-SRC-004",
            "F16-TG-SRC-005",
            "F16-TG-SRC-012",
        ],
        repo_root=repo_root,
    )
    warhead_sources = _source_evidence(
        ledger_ref=refs["warhead_source_ledger"],
        source_ids=[
            "AIM120-WF-002",
            "AIM120-WF-006",
            "AIM120-WF-007",
            "PHYS-BF-001",
            "PHYS-BF-002",
            "PHYS-BF-006",
        ],
        repo_root=repo_root,
    )
    fragment_sources = _source_evidence(
        ledger_ref=refs["vps_blastfrag_source_ledger"],
        source_ids=[
            "VPS-BFM-001",
            "VPS-BFM-006",
            "VPS-BFM-010",
            "VPS-BFM-011",
            "VPS-BFM-013",
            "VPS-BFM-015",
        ],
        repo_root=repo_root,
    )
    blast_sources = _source_evidence(
        ledger_ref=refs["vps_blastfrag_source_ledger"],
        source_ids=[
            "VPS-BFM-001",
            "VPS-BFM-002",
            "VPS-BFM-003",
            "VPS-BFM-014",
        ],
        repo_root=repo_root,
    )

    source_trace_pass = (
        stage_b_snapshot["all_hard_gates_pass_in_current_snapshot"]
        and "BFM-BM-006" in stage_b_snapshot["reviewed_benchmarks"]
    )
    mechanism_load_fields_present = all(
        key in mechanism_vector
        for key in (
            "blast_scaled_distance_m_kg13",
            "fragment_areal_density_per_m2",
            "surface_incidence_cos",
        )
    )
    stage_c_gate_band_pass = all(
        stage_c_result_pack[key] is True
        for key in (
            "gate_band_contains_primary_fragment_energy",
            "gate_band_contains_primary_penetration_margin",
            "gate_band_contains_primary_blast_impulse",
            "gate_band_contains_primary_surface_incidence",
        )
    )

    return [
        _condition(
            check_id="CLOSEOUT-RES003-001",
            residual_id="RES-003",
            closeout_surface="target_geometry_source_and_assumption_trace",
            author_side_satisfied=(
                target_assumptions["author_status"] == "frozen_for_stage_b_review_only"
                and len(target_sources["missing_source_ids"]) == 0
                and source_trace_pass
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "source_evidence": target_sources,
                "pin_evidence": _pin_evidence(pin_rows, "RES-003"),
                "target_geometry_assumption_summary": target_assumptions,
                "source_trace_gate_pass": source_trace_pass,
            },
            remaining_release_grade_requirements=[
                "row-level geometry provenance and uncertainty bounds for any witness or component projection",
                "independent review that confirms repo hitboxes are engineering scaffolds, not F-16 vulnerability geometry",
                "release-grade decision on whether unsupported material, occlusion and exposed-area truth stay out of scope",
            ],
            blocking_summary=(
                "public F-16 outer-dimension and rough component anchors are recorded, "
                "but internal geometry, material, occlusion and exposed-area truth remain "
                "unsupported; engineering hitboxes are not calibrated vulnerability geometry"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES003-002",
            residual_id="RES-003",
            closeout_surface="engineering_hitbox_authority_boundary",
            author_side_satisfied=(
                target_assumptions["unsupported_row_count"] >= 1
                and target_assumptions["used_by_stage_b_yes_count"] >= 1
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "unsupported_row_count": target_assumptions["unsupported_row_count"],
                "used_by_stage_b_yes_count": target_assumptions[
                    "used_by_stage_b_yes_count"
                ],
                "forbidden_interpretation": (
                    "repo scaffold and beam witness geometry are bookkeeping inputs only"
                ),
            },
            remaining_release_grade_requirements=[
                "reviewer-frozen hitbox usage policy for Stage B and Stage C",
                "explicit error model for coarse witness geometry or a narrower no-geometry authority claim",
            ],
            blocking_summary=(
                "the current assumption manifest marks unsupported geometry rows, "
                "but it has not converted hitbox assumptions into reviewed error bounds"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES004-001",
            residual_id="RES-004",
            closeout_surface="warhead_family_scope_and_public_terms",
            author_side_satisfied=(
                warhead_scope["weapon_class"] == "AIM-120C-class"
                and warhead_scope["weapon_family"] == "blast_fragmentation"
                and len(warhead_sources["missing_source_ids"]) == 0
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "source_evidence": warhead_sources,
                "pin_evidence": _pin_evidence(pin_rows, "RES-004"),
                "warhead_scope_summary": warhead_scope,
            },
            remaining_release_grade_requirements=[
                "reviewer-frozen separation between AIM-120C-class family label and variant-specific warhead truth",
                "release-grade sensitivity envelope that does not consume third-party mass claims as calibrated inputs",
                "explicit no-fuze/no-Pk interlock for any warhead-scope closeout",
            ],
            blocking_summary=(
                "family-level blast-fragmentation scope and public TDD terminology are "
                "recorded, but no admitted source binds AIM-120C-class toy inputs to "
                "variant-specific warhead mass, fragment pattern, TNT equivalent or fuze truth"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES004-002",
            residual_id="RES-004",
            closeout_surface="warhead_numeric_sensitivity_and_rejection_guard",
            author_side_satisfied=(
                warhead_scope["consumed_by_surrogate_yes_count"] >= 1
                and warhead_scope["rejected_rows"] >= 1
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "consumed_by_surrogate_yes_count": warhead_scope[
                    "consumed_by_surrogate_yes_count"
                ],
                "rejected_rows": warhead_scope["rejected_rows"],
                "candidate_input_boundary": bundle["candidate_inputs"]["weapon"][
                    "provenance"
                ],
                "forbidden_interpretation": (
                    "AIM-120C-class repo warhead values remain toy candidate inputs"
                ),
            },
            remaining_release_grade_requirements=[
                "hash-pinned sensitivity configuration for repo toy warhead inputs",
                "reviewer signoff that third-party/forum/game values remain sanity-only or rejected",
            ],
            blocking_summary=(
                "the scope manifest distinguishes toy numeric consumption from rejected "
                "community parameters, but the toy input is still not calibrated "
                "AIM-120C warhead authority"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES005-001",
            residual_id="RES-005",
            closeout_surface="fragment_method_source_chain",
            author_side_satisfied=(
                len(fragment_sources["missing_source_ids"]) == 0
                and "PIN-BFM-002" in _pin_evidence(pin_rows, "RES-005")["pin_ids"]
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "source_evidence": fragment_sources,
                "pin_evidence": _pin_evidence(pin_rows, "RES-005"),
                "stage_b_reviewed_benchmarks": stage_b_snapshot["reviewed_benchmarks"],
            },
            remaining_release_grade_requirements=[
                "official Gurney artifact or explicit exclusion from the release method chain",
                "retained TP-21 artifact ref plus reviewer-frozen debris vocabulary usage boundary",
                "fragment direction pattern, casing breakup and velocity attenuation assumptions with reviewable uncertainty",
            ],
            blocking_summary=(
                "Mott/Marsaglia/debris vocabulary and fragment bookkeeping sources are "
                "present, but the current fragment cloud remains a toy proxy without "
                "validated mass, velocity, direction pattern, areal density or penetration authority"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES005-002",
            residual_id="RES-005",
            closeout_surface="fragment_mechanism_load_evidence",
            author_side_satisfied=(
                stage_b_snapshot["all_hard_gates_pass_in_current_snapshot"]
                and mechanism_load_fields_present
                and stage_b_result_pack["bm005_audit_outcome"]
                in {
                    "candidate_snapshot_only_not_independent_validation",
                    "candidate_hygiene_only_not_independent_validation",
                    "integrated_mechanism_load_hygiene_only",
                }
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "fragment_areal_density_cv": stage_b_snapshot[
                    "fragment_areal_density_cv"
                ],
                "fragment_energy_cv": stage_b_snapshot["fragment_energy_cv"],
                "mechanism_load_vector": mechanism_vector,
                "stage_c_gate_band_fragment_energy_pass": stage_c_result_pack[
                    "gate_band_contains_primary_fragment_energy"
                ],
                "stage_c_gate_band_penetration_pass": stage_c_result_pack[
                    "gate_band_contains_primary_penetration_margin"
                ],
                "bm005_audit_outcome": stage_b_result_pack["bm005_audit_outcome"],
            },
            remaining_release_grade_requirements=[
                "fragment benchmark that compares retained public/reference outputs or measured data under frozen tolerances",
                "independent review that the toy fragment probe is not being used as calibrated fragment authority",
            ],
            blocking_summary=(
                "author-side Stage B/C evidence exercises fragment load fields and "
                "gate bands, but those checks are explicitly toy/integration hygiene, "
                "not calibrated fragment mechanism validation"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES006-001",
            residual_id="RES-006",
            closeout_surface="blast_method_source_chain",
            author_side_satisfied=(
                len(blast_sources["missing_source_ids"]) == 0
                and "PIN-BFM-001" in _pin_evidence(pin_rows, "RES-006")["pin_ids"]
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "source_evidence": blast_sources,
                "pin_evidence": _pin_evidence(pin_rows, "RES-006"),
                "stage_b_reviewed_benchmarks": stage_b_snapshot["reviewed_benchmarks"],
            },
            remaining_release_grade_requirements=[
                "Kingery-Bulmash official artifact or explicit exclusion from release comparison",
                "canonical TP-20/BEC-O retained refs, package/version freeze and comparison-output hashes",
                "reviewed blast applicability envelope for TNT equivalent, airburst geometry, reflection and aircraft coupling",
            ],
            blocking_summary=(
                "IATG/UFC and DENIX TP-20/BEC-O candidate routes are recorded, "
                "but original-report acquisition, retained comparison outputs and "
                "scope-specific blast coupling remain open"
            ),
        ),
        _condition(
            check_id="CLOSEOUT-RES006-002",
            residual_id="RES-006",
            closeout_surface="blast_mechanism_load_evidence",
            author_side_satisfied=(
                stage_b_snapshot["all_hard_gates_pass_in_current_snapshot"]
                and mechanism_load_fields_present
                and source_trace_pass
                and stage_c_gate_band_pass
            ),
            release_grade_satisfied=False,
            observed_author_side_evidence={
                "blast_impulse_cv": stage_b_snapshot["blast_impulse_cv"],
                "mechanism_load_vector": mechanism_vector,
                "stage_c_gate_band_blast_impulse_pass": stage_c_result_pack[
                    "gate_band_contains_primary_blast_impulse"
                ],
                "stage_c_gate_band_surface_incidence_pass": stage_c_result_pack[
                    "gate_band_contains_primary_surface_incidence"
                ],
                "stage_b_all_hard_gates_pass": stage_b_snapshot[
                    "all_hard_gates_pass_in_current_snapshot"
                ],
                "source_trace_gate_pass": source_trace_pass,
            },
            remaining_release_grade_requirements=[
                "blast curve comparison against retained public-tool or reviewed benchmark outputs",
                "independent review that blast toy proxy outputs are not calibrated pressure/impulse authority",
            ],
            blocking_summary=(
                "author-side blast scaled-distance and impulse checks pass the current "
                "toy hard gates, but the blast probe remains a proxy and cannot be "
                "treated as calibrated blast mechanism authority"
            ),
        ),
    ]


def _residual_condition_trace(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for residual_id in RESIDUAL_IDS:
        residual_checks = [row for row in checks if row["residual_id"] == residual_id]
        author_side_ids = [
            row["check_id"] for row in residual_checks if row["author_side_satisfied"]
        ]
        release_blocking_ids = [
            row["check_id"]
            for row in residual_checks
            if not row["release_grade_satisfied"]
        ]
        if residual_checks and not release_blocking_ids:
            gate_result = "closed_by_this_gate"
        elif len(author_side_ids) == len(residual_checks):
            gate_result = "blocked_author_side_review_ready"
        else:
            gate_result = "blocked_author_side_evidence_missing"
        trace.append(
            {
                "residual_id": residual_id,
                "author_side_satisfied_check_ids": author_side_ids,
                "release_grade_blocking_check_ids": release_blocking_ids,
                "gate_result": gate_result,
            }
        )
    return trace


def generate_mechanism_source_closeout_gate(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    refs = _doc_refs(repo_root)
    placeholder_hits = _scan_placeholder_hits(list(refs.values()), repo_root)
    bundle = candidate_bundle.generate_candidate_bundle(repo_root=repo_root)
    checks = _closeout_checks(bundle=bundle, refs=refs, repo_root=repo_root)
    trace = _residual_condition_trace(checks)
    closed_residuals = [
        row["residual_id"] for row in trace if row["gate_result"] == "closed_by_this_gate"
    ]

    return {
        "package_id": PACKAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked_non_authoritative_mechanism_source_closeout_candidate",
        "review_target": "res_003_004_005_006_mechanism_source_closeout_lane",
        "readiness_level": (
            "author_side_evidence_present_but_calibrated_authority_blocked"
        ),
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss_0_35m",
        },
        "doc_refs": {key: _rel(path, repo_root) for key, path in refs.items()},
        "documentation_status": {
            "ready_for_review": not placeholder_hits,
            "placeholder_hits": placeholder_hits,
        },
        "closeout_decision": {
            "mechanism_source_closeout_ready": False,
            "mechanism_source_closeout_blocked": True,
            "author_side_subitems_recorded": all(
                row["gate_result"] == "blocked_author_side_review_ready"
                for row in trace
            ),
            "closed_residual_ids_by_this_gate": closed_residuals,
            "authority_release_included": False,
        },
        "closeout_checks": checks,
        "residual_condition_trace": trace,
        "current_gate_results": {
            row["residual_id"]: row["gate_result"] for row in trace
        },
        "closed_author_side_subitems": {
            "RES-003": [
                "public outer-dimension anchors and rough component-region assumptions are traceable",
                "unsupported material, occlusion and exposed-area rows are explicitly marked out of authority",
            ],
            "RES-004": [
                "AIM-120C-class blast-fragmentation family label is separated from variant-specific truth",
                "third-party and game/forum warhead or fuze values are sanity-only or rejected",
            ],
            "RES-005": [
                "fragment sampler, areal-density bookkeeping and source-trace hard gates pass in the author-side snapshot",
                "Stage C component row gate band covers current fragment-energy and penetration proxy fields",
            ],
            "RES-006": [
                "blast scaled-distance/unit/source-trace hard gates pass in the author-side snapshot",
                "DENIX TP-20/BEC-O public artifact existence and sha256 are recorded as candidate-only evidence",
            ],
        },
        "remaining_release_grade_paths": {
            "RES-003": [
                "freeze row-level geometry provenance and uncertainty bounds",
                "obtain independent review that repo hitboxes are not true F-16 vulnerability geometry",
            ],
            "RES-004": [
                "freeze release-grade warhead class/sensitivity envelope without consuming toy mass as AIM-120C truth",
                "keep deterministic fuze and Pk outside this gate unless a separate evidence chain exists",
            ],
            "RES-005": [
                "resolve Gurney official artifact or explicitly exclude it from the release method chain",
                "freeze fragment pattern, casing, velocity and TP-21 retained/reference-output evidence with reviewer signoff",
            ],
            "RES-006": [
                "resolve Kingery-Bulmash official artifact or explicitly exclude it from release comparison",
                "freeze TP-20/BEC-O retained refs, comparison-output hashes, tolerances and blast applicability envelope",
            ],
        },
        "mechanism_load_evidence_summary": {
            "validation_scaffold_status": bundle["validation_scaffold_summary"][
                "validation_status"
            ],
            "mechanism_load_vector": bundle["validation_scaffold_summary"][
                "mechanism_load_vector"
            ],
            "stage_b_snapshot_status": bundle["validation_benchmark_snapshot_summary"][
                "status"
            ],
            "stage_b_all_hard_gates_pass": bundle[
                "validation_benchmark_snapshot_summary"
            ]["all_hard_gates_pass_in_current_snapshot"],
            "stage_b_review_status": bundle["validation_benchmark_snapshot_summary"][
                "review_status"
            ],
            "stage_b_result_pack_status": bundle["validation_result_pack_summary"][
                "status"
            ],
            "stage_b_bm005_audit_outcome": bundle["validation_result_pack_summary"][
                "bm005_audit_outcome"
            ],
            "stage_c_result_pack_status": bundle[
                "validation_stage_c_component_probability_result_pack_summary"
            ]["status"],
            "stage_c_baseline_component_probability_source": bundle[
                "validation_stage_c_component_probability_result_pack_summary"
            ]["baseline_component_probability_source"],
        },
        "non_authoritative_guards": {
            "stock_descriptor_created": False,
            "stock_database_authority_granted": False,
            "target_geometry_authority_granted": False,
            "aim120c_warhead_authority_granted": False,
            "fragment_mechanism_authority_granted": False,
            "blast_mechanism_authority_granted": False,
            "effect_scale_authority_granted": False,
            "component_failure_probability_authority_granted": False,
            "pk_authority_granted": False,
            "deterministic_fuze_authority_granted": False,
        },
        "behavior_risks": [
            "engineering hitboxes could be mistaken for true vulnerability geometry if the RES-003 boundary is ignored",
            "AIM-120C-class toy inputs could be mistaken for variant-specific warhead or fuze truth if RES-004 is ignored",
            "fragment and blast toy probes could be mistaken for calibrated mechanism authority if Stage B/C author-side status is ignored",
        ],
        "integration_notes": [
            "this gate does not update residual_register.zh.md; it records the current review lane result only",
            "RES-013 Pk and RES-014 deterministic fuze remain outside this mechanism/source closeout lane",
            "any future bundle integration should consume current_gate_results and non_authoritative_guards together",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the A2 blast-fragmentation mechanism/source closeout gate "
            "for RES-003/004/005/006."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_mechanism_source_closeout_gate()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
