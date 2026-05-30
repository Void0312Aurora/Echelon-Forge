#!/usr/bin/env python3
"""Build the current A2 blast-fragmentation candidate package bundle.

This tool assembles the narrow-scope candidate package into one
machine-readable artifact for review. It intentionally stays below runtime
authority: the bundle records candidate docs, residuals, scaffold outputs and
test-local authority exercises, but it does not create or grant stock runtime
authority.
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

from tools.maintenance import a2_blastfrag_runtime_aligned_authority_pack as authority_pack
from tools.maintenance import a2_blastfrag_scope_boundary_probe as scope_probe
from tools.maintenance import a2_blastfrag_stage_b_effect_scale_snapshot as stage_b_snapshot
from tools.maintenance import a2_blastfrag_validation_scaffold as scaffold


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
BUNDLE_ID = f"{PACKAGE_ID}_candidate_bundle_v0"
SCHEMA_VERSION = "a2.vps_candidate_bundle.v1"

PACKAGE_DIR = (
    REPO_ROOT
    / "docs"
    / "task"
    / "air_combat"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
A2_ROOT = (
    REPO_ROOT / "docs" / "task" / "air_combat" / "a2_high_fidelity_damage_model"
)

DOC_REFS = {
    "package_readme": PACKAGE_DIR / "README.zh.md",
    "source_ledger": PACKAGE_DIR / "source_ledger.zh.md",
    "surrogate_model_card": PACKAGE_DIR / "surrogate_model_card.zh.md",
    "validation_manifest_draft": PACKAGE_DIR / "validation_manifest_draft_blastfrag_20260528.zh.md",
    "validation_report_draft": PACKAGE_DIR / "validation_report_draft.zh.md",
    "validation_metrics_and_acceptance_criteria": (
        PACKAGE_DIR / "validation_metrics_and_acceptance_criteria_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_scope_and_independence_manifest": (
        PACKAGE_DIR / "validation_scope_and_independence_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_scope_probe_report": (
        PACKAGE_DIR / "validation_scope_boundary_probe_report_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_benchmark_snapshot": (
        PACKAGE_DIR / "validation_benchmark_snapshot_stage_b_effect_scale_20260530.zh.md"
    ),
    "validation_review_readiness_record": (
        PACKAGE_DIR / "validation_review_readiness_record_stage_b_effect_scale_20260530.zh.md"
    ),
    "artifact_pin_manifest": (
        PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "surrogate_identity_manifest": (
        PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "target_geometry_assumptions": (
        PACKAGE_DIR / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md"
    ),
    "warhead_scope_and_sensitivity": (
        PACKAGE_DIR / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md"
    ),
    "residual_register": PACKAGE_DIR / "residual_register.zh.md",
    "narrow_scope_task": A2_ROOT / "narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md",
    "schema_rule": A2_ROOT / "vulnerability_evidence_schema_v1.zh.md",
    "source_admission_rule": A2_ROOT / "data_collection" / "source_admission_rules_20260528.zh.md",
}

SOURCE_GROUPS = (
    {
        "group_id": "target_geometry",
        "ledger_ref": (
            A2_ROOT / "data_collection" / "f16c_block50_target_geometry" / "source_ledger.zh.md"
        ),
        "selected_source_ids": [
            "F16-TG-SRC-001",
            "F16-TG-SRC-002",
            "F16-TG-SRC-004",
            "F16-TG-SRC-005",
            "F16-TG-SRC-012",
        ],
    },
    {
        "group_id": "warhead_and_fuze",
        "ledger_ref": (
            A2_ROOT / "data_collection" / "aim120c_warhead_fuze" / "source_ledger.zh.md"
        ),
        "selected_source_ids": [
            "AIM120-WF-002",
            "AIM120-WF-006",
            "AIM120-WF-007",
            "PHYS-BF-001",
            "PHYS-BF-002",
            "PHYS-BF-006",
            "PHYS-BF-013",
            "PHYS-BF-014",
            "PHYS-BF-015",
        ],
    },
    {
        "group_id": "mechanism_load_methods",
        "ledger_ref": (
            A2_ROOT
            / "data_collection"
            / "vps_blast_fragmentation_methods"
            / "source_ledger.zh.md"
        ),
        "selected_source_ids": [
            "VPS-BFM-001",
            "VPS-BFM-002",
            "VPS-BFM-006",
            "VPS-BFM-010",
            "VPS-BFM-011",
            "VPS-BFM-013",
            "VPS-BFM-014",
            "VPS-BFM-015",
        ],
    },
    {
        "group_id": "component_fragility_methods",
        "ledger_ref": (
            A2_ROOT
            / "data_collection"
            / "component_fragility_benchmark_methods"
            / "source_ledger.zh.md"
        ),
        "selected_source_ids": [
            "CFBM-FOI-001",
            "CFBM-LFTE-001",
            "CFBM-LFTE-002",
            "CFBM-LFTE-003",
            "CFBM-MSVV-001",
            "CFBM-MSVV-002",
            "CFBM-PAPER-001",
            "CFBM-PAPER-002",
            "CFBM-PAPER-003",
            "CFBM-PAPER-004",
        ],
    },
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _parse_open_residual_ids(path: Path) -> list[str]:
    residuals: list[str] = []
    for line in _read_text(path).splitlines():
        match = re.search(r"\|\s*`(RES-\d+)`\s*\|.*\|\s*open\s*\|", line)
        if match:
            residuals.append(match.group(1))
    return residuals


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
                hits.append(
                    {
                        "path": _rel(path),
                        "line": line_no,
                        "content": line.strip(),
                    }
                )
    return hits


def _validation_manifest_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    return {
        "schema_version": extract("schema_version"),
        "validation_status": extract("validation_status"),
        "target_type": extract("target_type"),
        "weapon_class": extract("weapon_class"),
        "weapon_family": extract("weapon_family"),
        "aspect_bucket": extract("aspect_bucket"),
        "closure_bucket": extract("closure_bucket"),
        "miss_distance_bucket": extract("miss_distance_bucket"),
    }


def _validation_acceptance_criteria_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*{re.escape(field)}\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    hard_gate_benchmarks = sorted(
        {
            match.group(1)
            for match in re.finditer(
                r"\|\s*`BFM-CRIT-ES-\d+`\s*\|\s*`(BFM-BM-\d+)`\s*\|",
                text,
            )
        }
    )
    deferred_items = sorted(
        match.group(1)
        for match in re.finditer(
            r"\|\s*`(BFM-DEF-\d+)`\s*\|",
            text,
        )
    )
    return {
        "artifact_ref": _rel(path),
        "criteria_status": extract("`criteria_status`"),
        "primary_release_scope": extract("`primary_release_scope`"),
        "component_probability_release_status": extract(
            "`component_probability_release_status`"
        ),
        "review_status": extract("`review_status`"),
        "runtime_descriptor_action": extract("`runtime_descriptor_action`"),
        "hard_gate_benchmarks": hard_gate_benchmarks,
        "deferred_items": deferred_items,
    }


def _validation_scope_and_independence_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*{re.escape(field)}\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    boundary_probes = sorted(
        match.group(1)
        for match in re.finditer(
            r"\|\s*`(SCP-PROBE-\d+)`\s*\|",
            text,
        )
    )
    out_of_scope_labels = sorted(
        match.group(1)
        for match in re.finditer(
            r"\|\s*`SCP-REJ-\d+`\s*\|\s*`([^`]+)`\s*\|",
            text,
        )
    )
    documented_benchmarks = sorted(
        {
            match.group(1)
            for match in re.finditer(
                r"\|\s*`(BFM-BM-\d+)`\s*\|",
                text,
            )
        }
    )
    return {
        "artifact_ref": _rel(path),
        "scope_manifest_status": extract("`scope_manifest_status`"),
        "primary_release_scope": extract("`primary_release_scope`"),
        "independence_status": extract("`independence_status`"),
        "runtime_bucket_note": extract("`runtime_bucket_note`"),
        "review_status": extract("`review_status`"),
        "boundary_probes": boundary_probes,
        "out_of_scope_labels": out_of_scope_labels,
        "documented_benchmarks": documented_benchmarks,
    }


def _validation_scope_probe_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    miss_distance_probe = artifact["miss_distance_probe"]
    closure_probe = artifact["closure_probe"]
    aspect_guard_probe = artifact["aspect_guard_probe"]
    return {
        "status": artifact["status"],
        "scope": artifact["scope"],
        "miss_distance_probe": {
            "probe_id": miss_distance_probe["probe_id"],
            "row_count": len(miss_distance_probe["rows"]),
            "metrics": miss_distance_probe["metrics"],
            "standoff_values_m": [
                float(row["standoff_m"]) for row in miss_distance_probe["rows"]
            ],
        },
        "closure_probe": {
            "probe_id": closure_probe["probe_id"],
            "row_count": len(closure_probe["rows"]),
            "metrics": closure_probe["metrics"],
            "closure_values_mps": [
                float(row["closure_mps"]) for row in closure_probe["rows"]
            ],
            "limitation_note": closure_probe["limitation_note"],
        },
        "aspect_guard_probe": {
            "probe_id": aspect_guard_probe["probe_id"],
            "accepted_scope_labels": list(aspect_guard_probe["accepted_scope_labels"]),
            "rejected_scope_labels": list(aspect_guard_probe["rejected_scope_labels"]),
            "metrics": aspect_guard_probe["metrics"],
        },
    }


def _validation_benchmark_snapshot_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    summary = artifact["summary"]
    bm005 = artifact["benchmark_snapshot"]["BFM-BM-005"]
    return {
        "status": artifact["status"],
        "scope": artifact["scope"],
        "all_hard_gates_pass_in_current_snapshot": summary[
            "all_hard_gates_pass_in_current_snapshot"
        ],
        "failed_criteria_ids": list(summary["failed_criteria_ids"]),
        "reviewed_benchmarks": list(summary["reviewed_benchmarks"]),
        "review_status": summary["review_status"],
        "fragment_areal_density_cv": float(
            bm005["uncertainty_summary"]["fragment_areal_density_per_m2"]["cv"]
        ),
        "fragment_energy_cv": float(
            bm005["uncertainty_summary"]["fragment_energy_j_proxy"]["cv"]
        ),
        "penetration_margin_cv": float(
            bm005["uncertainty_summary"]["penetration_margin_proxy"]["cv"]
        ),
    }


def _validation_review_readiness_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    review_ids = sorted(
        match.group(1)
        for match in re.finditer(r"\|\s*`(RR-ES-\d+)`\s*\|", text)
    )
    return {
        "artifact_ref": _rel(path),
        "review_readiness_status": extract("review_readiness_status"),
        "primary_release_scope": extract("primary_release_scope"),
        "independent_review_status": extract("independent_review_status"),
        "benchmark_snapshot_status": extract("benchmark_snapshot_status"),
        "stock_runtime_action": extract("stock_runtime_action"),
        "review_ids": review_ids,
    }


def _artifact_pin_manifest_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    statuses = {
        "acquired_for_candidate": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`acquired_for_candidate`\s*\|", text)
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
    return {
        "artifact_ref": _rel(path),
        "manifest_status": extract("manifest_status"),
        "primary_release_scope": extract("primary_release_scope"),
        "third_party_policy": extract("third_party_policy"),
        "forbidden_release_action": extract("forbidden_release_action"),
        "status_counts": statuses,
    }


def _surrogate_identity_manifest_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    output_anchor_count = len(
        re.findall(r"/tmp/a2_[^|`]+\.json", text)
    )
    return {
        "artifact_ref": _rel(path),
        "model_ref": extract("model_ref"),
        "model_version": extract("model_version"),
        "repo_commit": extract("repo_commit"),
        "worktree_state": extract("worktree_state"),
        "current_validation_status": extract("current_validation_status"),
        "primary_release_scope": extract("primary_release_scope"),
        "output_anchor_count": output_anchor_count,
    }


def _target_geometry_assumption_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    return {
        "artifact_ref": _rel(path),
        "author_status": extract("author_status"),
        "target_type": extract("target_type"),
        "used_by_stage_b_yes_count": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`yes`\s*\|", text)
        ),
        "unsupported_row_count": len(
            re.findall(r"\|\s*`[^`]+`\s*\|.*\|\s*`unsupported`\s*\|", text)
        ),
    }


def _warhead_scope_summary(path: Path) -> dict[str, Any]:
    text = _read_text(path)

    def extract(field: str) -> str:
        match = re.search(
            rf"\|\s*`{re.escape(field)}`\s*\|\s*`?([^|`]+?)`?\s*\|",
            text,
        )
        return match.group(1).strip() if match else ""

    return {
        "artifact_ref": _rel(path),
        "weapon_class": extract("weapon_class"),
        "weapon_family": extract("weapon_family"),
        "consumed_by_surrogate_yes_count": len(
            re.findall(r"\|\s*`WAR-\d+`\s*\|.*\|\s*`yes`\s*\|", text)
        ),
        "rejected_rows": len(
            re.findall(r"\|\s*`WAR-\d+`\s*\|.*\|\s*rejected", text)
        ),
    }


def _runtime_aligned_exercise_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    effect_descriptor = artifact["effect_scale_descriptor_candidate"]
    component_descriptor = artifact["component_failure_probability_descriptor_candidate"]
    return {
        "package_id": artifact["package_id"],
        "status": artifact["status"],
        "authority_boundary": artifact["authority_boundary"],
        "baseline_event_summary": artifact["baseline_event_summary"],
        "baseline_component_row_count": len(artifact["baseline_component_rows"]),
        "effect_scale_descriptor_candidate": {
            "dataset_id": effect_descriptor["dataset_id"],
            "source_kind": effect_descriptor["source_kind"],
            "calibration_status": effect_descriptor["calibration_status"],
            "effect_scale_authority": effect_descriptor["effect_scale_authority"],
            "component_failure_probability_authority": effect_descriptor[
                "component_failure_probability_authority"
            ],
            "row_count": len(effect_descriptor["rows"]),
        },
        "component_failure_probability_descriptor_candidate": {
            "dataset_id": component_descriptor["dataset_id"],
            "source_kind": component_descriptor["source_kind"],
            "calibration_status": component_descriptor["calibration_status"],
            "effect_scale_authority": component_descriptor["effect_scale_authority"],
            "component_failure_probability_authority": component_descriptor[
                "component_failure_probability_authority"
            ],
            "row_count": len(component_descriptor["rows"]),
        },
    }


def generate_candidate_bundle(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    doc_refs = {key: _rel(path) for key, path in DOC_REFS.items()}
    placeholder_hits = _scan_placeholder_hits(
        [
            DOC_REFS["source_ledger"],
            DOC_REFS["surrogate_model_card"],
            DOC_REFS["validation_report_draft"],
            DOC_REFS["validation_metrics_and_acceptance_criteria"],
            DOC_REFS["validation_scope_and_independence_manifest"],
            DOC_REFS["validation_scope_probe_report"],
            DOC_REFS["validation_benchmark_snapshot"],
            DOC_REFS["validation_review_readiness_record"],
            DOC_REFS["artifact_pin_manifest"],
            DOC_REFS["surrogate_identity_manifest"],
            DOC_REFS["target_geometry_assumptions"],
            DOC_REFS["warhead_scope_and_sensitivity"],
        ]
    )
    scaffold_artifact = scaffold.generate_validation_scaffold(repo_root=repo_root)
    scope_probe_artifact = scope_probe.generate_scope_boundary_probe(repo_root=repo_root)
    stage_b_snapshot_artifact = stage_b_snapshot.generate_stage_b_effect_scale_snapshot(
        repo_root=repo_root
    )
    authority_artifact = authority_pack.generate_runtime_aligned_authority_pack(
        repo_root=repo_root
    )
    source_groups = [
        {
            "group_id": entry["group_id"],
            "ledger_ref": _rel(entry["ledger_ref"]),
            "selected_source_ids": list(entry["selected_source_ids"]),
        }
        for entry in SOURCE_GROUPS
    ]
    open_residual_ids = _parse_open_residual_ids(DOC_REFS["residual_register"])

    return {
        "bundle_id": BUNDLE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "candidate_non_authoritative_bundle",
        "package_id": PACKAGE_ID,
        "scope": {
            "target_type": "F-16C_Block50",
            "weapon_class": "AIM-120C-class",
            "weapon_family": "blast_fragmentation",
            "aspect_bucket": "beam",
            "closure_bucket": "high",
            "miss_distance_bucket": "near_miss_0_35m",
        },
        "authority_boundary": {
            "stock_descriptor_created": False,
            "stock_database_authority_granted": False,
            "effect_scale_authority_in_stock": False,
            "component_failure_probability_authority_in_stock": False,
            "pk_authority": False,
            "deterministic_fuze_authority": False,
            "candidate_bundle_role": "review_and_packaging_only",
        },
        "documentation_status": {
            "ready_for_review": not placeholder_hits,
            "placeholder_hits": placeholder_hits,
        },
        "doc_refs": doc_refs,
        "source_groups": source_groups,
        "open_residual_ids": open_residual_ids,
        "validation_manifest_summary": _validation_manifest_summary(
            DOC_REFS["validation_manifest_draft"]
        ),
        "validation_acceptance_criteria_summary": _validation_acceptance_criteria_summary(
            DOC_REFS["validation_metrics_and_acceptance_criteria"]
        ),
        "validation_scope_and_independence_summary": _validation_scope_and_independence_summary(
            DOC_REFS["validation_scope_and_independence_manifest"]
        ),
        "validation_scope_probe_summary": _validation_scope_probe_summary(
            scope_probe_artifact
        ),
        "validation_benchmark_snapshot_summary": _validation_benchmark_snapshot_summary(
            stage_b_snapshot_artifact
        ),
        "validation_review_readiness_summary": _validation_review_readiness_summary(
            DOC_REFS["validation_review_readiness_record"]
        ),
        "artifact_pin_manifest_summary": _artifact_pin_manifest_summary(
            DOC_REFS["artifact_pin_manifest"]
        ),
        "surrogate_identity_manifest_summary": _surrogate_identity_manifest_summary(
            DOC_REFS["surrogate_identity_manifest"]
        ),
        "target_geometry_assumption_summary": _target_geometry_assumption_summary(
            DOC_REFS["target_geometry_assumptions"]
        ),
        "warhead_scope_summary": _warhead_scope_summary(
            DOC_REFS["warhead_scope_and_sensitivity"]
        ),
        "validation_scaffold_summary": {
            "package_id": scaffold_artifact["package_id"],
            "schema_version": scaffold_artifact["schema_version"],
            "validation_status": scaffold_artifact["validation_status"],
            "current_authority_boundary": scaffold_artifact["current_authority_boundary"],
            "implemented_benchmarks": sorted(scaffold_artifact["benchmarks"].keys()),
            "mechanism_load_vector": scaffold_artifact["mechanism_load_vector"],
            "draft_descriptor_status": scaffold_artifact["vulnerability_evidence_draft"][
                "status"
            ],
        },
        "runtime_aligned_authority_exercise_summary": _runtime_aligned_exercise_summary(
            authority_artifact
        ),
        "candidate_inputs": scaffold_artifact["candidate_inputs"],
        "next_graduation_step": (
            "review the frozen stage-b effect-scale criteria, snapshot, provenance "
            "and scope artifacts, then close provenance, bucket-definition and "
            "result-record residuals before "
            "any stock database authority is granted"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assemble the current A2 blast-fragmentation candidate package bundle "
            "for narrow-scope review."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    artifact = generate_candidate_bundle()
    payload = json.dumps(artifact, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
