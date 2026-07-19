#!/usr/bin/env python3
"""Generate blocked Stage C fragility benchmark evidence for A2.

The current Stage C surface has a right_aileron_actuator candidate curve and a
stock synthetic_sigmoid baseline, but no independent actuator fragility truth.
This tool therefore emits an auditable blocked benchmark manifest and a
runnable author-side comparison/probe only. It must not be used to grant stock
component-probability authority, Pk authority, deterministic-fuze authority, or
baseline replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import resolve_repo_path, ensure_repo_imports, repo_root  # noqa: E402

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_text

from tools.maintenance.candidate_artifacts import component_probability_surface_probe as surface_probe # noqa: E402
from tools.maintenance.candidate_artifacts import ( # noqa: E402
  component_fragility_review_gate as fragility_review_gate,
)

PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
BENCHMARK_SCHEMA_VERSION = "a2.stage_c_fragility_benchmark.v1"
COMPARISON_SCHEMA_VERSION = "a2.stage_c_fragility_benchmark_comparison.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = "a2.stage_c_fragility_benchmark_retained_manifest.v1"
FOCUSED_RESIDUAL_IDS = ("RES-009", "RES-010", "RES-011", "RES-012")
DEFAULT_RETAINED_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "archive"
  / "a2_high_fidelity_damage_model"
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
  / "retained_artifacts"
  / "stage_c_fragility_benchmark_20260531"
)

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def _synthetic_baseline_rows() -> list[dict[str, Any]]:
  source_db = resolve_repo_path("examples", "config", "database")
  rows: list[dict[str, Any]] = []
  for point in surface_probe.PROBE_POINTS:
    event = surface_probe._sample_primary_event(
      database_path=source_db,
      local_point=tuple(point["local_point"]),
      seed=surface_probe.REPEATABILITY_SEEDS[0],
    )
    summary = surface_probe._event_primary_summary(event)
    rows.append(
      {
        "probe_label": str(point["probe_label"]),
        "local_point": list(point["local_point"]),
        "baseline_component_name": summary["component_primary_name"],
        "baseline_probability_source": summary[
          "component_failure_probability_source"
        ],
        "baseline_probability_calibrated": summary[
          "component_failure_probability_calibrated"
        ],
        "baseline_component_failure_probability": summary[
          "component_failure_probability"
        ],
        "baseline_evidence_row_id": summary[
          "component_failure_probability_evidence_row_id"
        ],
        "baseline_evidence_source_ref": summary[
          "component_failure_probability_evidence_source_ref"
        ],
        "baseline_evidence_provenance": summary[
          "component_failure_probability_evidence_provenance"
        ],
      }
    )
  return rows

def _candidate_curve(surface_artifact: dict[str, Any]) -> dict[str, Any]:
  points = []
  for row in surface_artifact["surface_probe_rows"]:
    local_point = list(row["local_point"])
    points.append(
      {
        "benchmark_point_id": f"FRAG-BENCH-CAND-{row['probe_label'].upper()}",
        "probe_label": row["probe_label"],
        "candidate_row_id": row[
          "component_failure_probability_evidence_row_id"
        ],
        "candidate_probability": row["component_failure_probability"],
        "candidate_probability_source": row[
          "component_failure_probability_source"
        ],
        "component_name": row["component_primary_name"],
        "component_system": row["component_primary_system"],
        "component_redundancy_group_id": row[
          "component_primary_redundancy_group_id"
        ],
        "local_point": local_point,
        "standoff_order_key_m": abs(float(local_point[1])),
        "mechanism_loads": {
          "blast_scaled_distance_m_kg13": row[
            "component_primary_mechanism_blast_scaled_distance_m_kg13"
          ],
          "fragment_areal_density_per_m2": row[
            "component_primary_mechanism_fragment_areal_density_per_m2"
          ],
          "fragment_energy_j": row[
            "component_primary_mechanism_fragment_energy_j"
          ],
          "penetration_margin": row[
            "component_primary_mechanism_penetration_margin"
          ],
          "blast_impulse_kpa_ms": row[
            "component_primary_mechanism_blast_impulse_kpa_ms"
          ],
          "surface_incidence_cos": row[
            "component_primary_mechanism_surface_incidence_cos"
          ],
        },
        "truth_role": "candidate_input_not_independent_fragility_truth",
      }
    )

  return {
    "curve_id": "RIGHT-AILERON-ACTUATOR-STAGE-C-CANDIDATE-001",
    "curve_kind": "author_side_three_point_piecewise_linear_candidate",
    "component_name": "right_aileron_actuator",
    "source_tool": (
   "tools/maintenance/damage_model.py candidate-artifacts "
      "component-probability-surface-probe"
    ),
    "point_count": len(points),
    "points": points,
    "monotonic_decreasing_with_standoff": surface_artifact["metrics"][
      "probability_monotonic_decreasing_with_standoff_pass"
    ],
    "benchmark_candidate_status": (
      "candidate_curve_available_but_truth_benchmark_missing"
    ),
    "authority_role": "author_side_benchmark_candidate_only",
  }

def _comparison_rows(
  *,
  candidate_curve: dict[str, Any],
  synthetic_baseline_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  baseline_by_label = {
    row["probe_label"]: row for row in synthetic_baseline_rows
  }
  rows: list[dict[str, Any]] = []
  for point in candidate_curve["points"]:
    baseline = baseline_by_label[str(point["probe_label"])]
    baseline_probability = float(
      baseline["baseline_component_failure_probability"]
    )
    candidate_probability = float(point["candidate_probability"])
    delta = candidate_probability - baseline_probability
    rows.append(
      {
        "probe_label": point["probe_label"],
        "candidate_row_id": point["candidate_row_id"],
        "candidate_probability": candidate_probability,
        "candidate_probability_source": point[
          "candidate_probability_source"
        ],
        "synthetic_sigmoid_probability": baseline_probability,
        "synthetic_sigmoid_probability_source": baseline[
          "baseline_probability_source"
        ],
        "synthetic_sigmoid_calibrated": baseline[
          "baseline_probability_calibrated"
        ],
        "candidate_minus_synthetic_sigmoid": delta,
        "absolute_difference_vs_synthetic_sigmoid": abs(delta),
        "candidate_to_synthetic_sigmoid_ratio": (
          candidate_probability / baseline_probability
          if baseline_probability > 0.0
          else None
        ),
        "comparison_role": (
          "author_side_delta_against_stock_synthetic_baseline_not_truth"
        ),
        "replacement_conclusion": "replacement_blocked_no_independent_truth",
      }
    )
  return rows

def _mean(values: list[float]) -> float:
  # Kept local: empty -> 0.0 (≠ mean_finite nan).
  return sum(values) / float(len(values)) if values else 0.0

def _comparison_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
  absolute_differences = [
    float(row["absolute_difference_vs_synthetic_sigmoid"]) for row in rows
  ]
  candidate_probabilities = [
    float(row["candidate_probability"]) for row in rows
  ]
  baseline_probabilities = [
    float(row["synthetic_sigmoid_probability"]) for row in rows
  ]
  ratios = [
    float(row["candidate_to_synthetic_sigmoid_ratio"])
    for row in rows
    if row["candidate_to_synthetic_sigmoid_ratio"] is not None
  ]
  return {
    "metric_role": (
      "candidate_vs_synthetic_baseline_delta_only_not_calibration_truth"
    ),
    "point_count": len(rows),
    "mean_candidate_probability": _mean(candidate_probabilities),
    "mean_synthetic_sigmoid_probability": _mean(baseline_probabilities),
    "mean_absolute_difference_vs_synthetic_sigmoid": _mean(
      absolute_differences
    ),
    "max_absolute_difference_vs_synthetic_sigmoid": max(
      absolute_differences
    ),
    "min_candidate_to_synthetic_sigmoid_ratio": min(ratios),
    "max_candidate_to_synthetic_sigmoid_ratio": max(ratios),
    "all_candidate_probabilities_exceed_synthetic_sigmoid": all(
      float(row["candidate_probability"])
      > float(row["synthetic_sigmoid_probability"])
      for row in rows
    ),
    "replacement_allowed": False,
    "calibration_interpretation": (
      "large deltas show the candidate rows differ from synthetic_sigmoid, "
      "but cannot prove accuracy without independent fragility truth"
    ),
  }

def _uncertainty_and_calibration_metrics(
  *,
  surface_artifact: dict[str, Any],
  comparison_metrics: dict[str, Any],
) -> dict[str, Any]:
  repeatability = surface_artifact["repeatability_summary"]
  return {
    "metric_status": (
      "blocked_calibration_truth_missing_author_side_metrics_only"
    ),
    "author_side_repeatability": {
      "anchor_probe_label": repeatability["anchor_probe_label"],
      "seed_values": repeatability["seed_values"],
      "seed_count": len(repeatability["seed_values"]),
      "component_failure_probability_cv": repeatability[
        "component_failure_probability"
      ]["cv"],
      "fragment_areal_density_cv": repeatability[
        "fragment_areal_density_per_m2"
      ]["cv"],
      "fragment_energy_cv": repeatability["fragment_energy_j"]["cv"],
      "penetration_margin_cv": repeatability["penetration_margin"]["cv"],
      "blast_impulse_cv": repeatability["blast_impulse_kpa_ms"]["cv"],
      "repeatability_result": "pass_candidate_only",
    },
    "candidate_vs_synthetic_baseline_delta_metrics": comparison_metrics,
    "calibration_scores": [
      {
        "metric_id": "CAL-FRAG-001",
        "metric_name": "brier_score_vs_independent_truth",
        "status": "not_computed",
        "blocked_by": "missing_independent_truth_labels",
        "residual_link": "RES-011",
      },
      {
        "metric_id": "CAL-FRAG-002",
        "metric_name": "log_loss_vs_independent_truth",
        "status": "not_computed",
        "blocked_by": "missing_independent_truth_labels",
        "residual_link": "RES-011",
      },
      {
        "metric_id": "CAL-FRAG-003",
        "metric_name": "calibration_curve_or_ece",
        "status": "not_computed",
        "blocked_by": "missing_independent_truth_distribution",
        "residual_link": "RES-011",
      },
    ],
    "coverage_limits": [
      "three fixed seeds only",
      "three near-miss surface points only",
      "no independent damage/no-damage labels",
      "no reviewer-accepted uncertainty interval",
    ],
    "authority_effect": "continues_to_block_res011_and_replacement",
  }

def _independence_trace(
  *,
  review_artifact: dict[str, Any],
) -> dict[str, Any]:
  return {
    "trace_status": (
      "candidate_inputs_and_synthetic_baseline_separated_but_truth_missing"
    ),
    "candidate_input_layer": [
      {
        "artifact_id": "INPUT-FRAG-BENCH-001",
        "artifact_kind": "stage_c_component_probability_surface_probe_rows",
        "role": "candidate evidence-row curve inputs",
        "forbidden_use": "independent benchmark truth",
      }
    ],
    "synthetic_baseline_layer": [
      {
        "artifact_id": "BASELINE-FRAG-BENCH-001",
        "artifact_kind": "stock_synthetic_sigmoid_component_probability",
        "role": "delta comparator only",
        "forbidden_use": "release-grade fragility truth",
      }
    ],
    "benchmark_output_layer": [
      {
        "artifact_id": "RESULT-FRAG-BENCH-001",
        "artifact_kind": "blocked_stage_c_fragility_benchmark_manifest",
        "role": "author-side blocked comparison and shortest evidence path",
        "current_independence_class": "blocked_manifest_only",
      }
    ],
    "independent_truth_layer": {
      "artifact_present": False,
      "required_artifact": (
        "independent right_aileron_actuator fragility curve/benchmark over "
        "the frozen Stage C load band"
      ),
      "required_owner": "independent_fragility_reviewer",
    },
    "review_gate_independence_context": review_artifact[
      "independence_review"
    ],
    "independent_result_audit_result": "blocked",
    "circularity_guard": (
      "candidate evidence rows are not scored against themselves; "
      "synthetic_sigmoid is retained only as a non-truth comparator"
    ),
    "authority_effect": "continues_to_block_res012",
  }

def _residual_benchmark_evidence_status(
  *,
  review_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
  review_rows = {
    row["residual_id"]: row for row in review_artifact["residual_gate_results"]
  }
  added = {
    "RES-009": [
      "right_aileron_actuator author-side three-point candidate curve",
      "candidate evidence-row vs synthetic_sigmoid delta table",
      "blocked replacement decision",
    ],
    "RES-010": [
      "retained blocked benchmark manifest",
      "runnable author-side comparison/probe entry point",
    ],
    "RES-011": [
      "candidate repeatability metrics",
      "explicitly blocked calibration-score ledger",
    ],
    "RES-012": [
      "candidate/baseline/output/truth independence trace",
      "non-circularity guard for synthetic baseline comparison",
    ],
  }
  status_by_residual = {
    "RES-009": "blocked_missing_independent_fragility_truth",
    "RES-010": "blocked_pending_formal_result_closeout_and_signoff",
    "RES-011": "blocked_missing_truth_labels_and_uncertainty_bounds",
    "RES-012": "blocked_pending_independent_result_level_audit",
  }
  return [
    {
      "residual_id": residual_id,
      "benchmark_evidence_status": status_by_residual[residual_id],
      "gate_result": review_rows[residual_id]["review_gate_result"],
      "blocking_condition_ids": review_rows[residual_id][
        "blocking_condition_ids"
      ],
      "evidence_added_by_this_pack": added[residual_id],
      "missing_evidence": review_rows[residual_id]["missing_evidence"],
      "forced_review_trigger": review_rows[residual_id][
        "forced_review_trigger"
      ],
      "replacement_allowed": False,
      "authority_release_effect": (
        "continues_to_block_stage_c_component_probability_authority"
      ),
    }
    for residual_id in FOCUSED_RESIDUAL_IDS
  ]

def _truth_inventory() -> dict[str, Any]:
  return {
    "external_truth_present": False,
    "truth_status": "missing_independent_right_aileron_actuator_fragility_truth",
    "searched_authority_scopes": [
      "current Stage C component-probability surface probe",
      "current Stage C fragility validation prep and review gate",
      "stock examples/config/database synthetic_sigmoid baseline",
      "retained Stage C author-side artifacts",
    ],
    "blocked_benchmark_manifest_required": True,
    "not_authority_reason": (
      "no independent right_aileron_actuator fragility curve or benchmark "
      "is present in the Stage C artifact chain; candidate rows are "
      "author-side inputs and synthetic_sigmoid is a stock baseline model"
    ),
  }

def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "stock_component_probability_authority": False,
    "pk_authority": False,
    "deterministic_fuze_authority": False,
    "replacement_allowed": False,
  }

def generate_stage_c_fragility_benchmark(
  *,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  surface_artifact = (
    surface_probe.generate_stage_c_component_probability_surface_probe(
      repo_root=repo_root
    )
  )
  review_artifact = fragility_review_gate.generate_stage_c_fragility_review_gate(
    repo_root=repo_root
  )
  candidate_curve = _candidate_curve(surface_artifact)
  synthetic_rows = _synthetic_baseline_rows()
  comparison_rows = _comparison_rows(
    candidate_curve=candidate_curve,
    synthetic_baseline_rows=synthetic_rows,
  )
  comparison_metrics = _comparison_metrics(comparison_rows)
  stage_b_review = review_artifact["stage_b_dependency_interlock_review"]
  authority_guards = _authority_guards()

  return {
    "package_id": PACKAGE_ID,
    "schema_version": BENCHMARK_SCHEMA_VERSION,
    "generated_on": "2026-05-31",
    "status": "blocked_non_authoritative_stage_c_fragility_benchmark",
    "benchmark_target": "right_aileron_actuator_fragility_benchmark_only",
    "focused_residual_ids": list(FOCUSED_RESIDUAL_IDS),
    "scope": dict(surface_artifact["scope"]),
    "truth_inventory": _truth_inventory(),
    "residual_benchmark_evidence_status": (
      _residual_benchmark_evidence_status(review_artifact=review_artifact)
    ),
    "benchmark_candidate_curve": candidate_curve,
    "synthetic_sigmoid_baseline_rows": synthetic_rows,
    "candidate_vs_synthetic_sigmoid_comparison": {
      "comparison_status": (
        "author_side_delta_available_but_not_truth_benchmark"
      ),
      "rows": comparison_rows,
      "metrics": comparison_metrics,
      "replacement_allowed": False,
      "replacement_decision": "blocked_no_independent_fragility_truth",
      "replacement_conclusion": (
        "candidate rows differ from synthetic_sigmoid but cannot replace it "
        "without independent fragility truth, uncertainty closeout and "
        "reviewer signoff"
      ),
    },
    "uncertainty_calibration_metrics": (
      _uncertainty_and_calibration_metrics(
        surface_artifact=surface_artifact,
        comparison_metrics=comparison_metrics,
      )
    ),
    "independence_trace": _independence_trace(
      review_artifact=review_artifact
    ),
    "stage_b_dependency_interlock": {
      "stage_b_status": stage_b_review["stage_b_status"],
      "stage_b_release_target": stage_b_review["stage_b_release_target"],
      "dependency_preserved_as_blocked": stage_b_review[
        "dependency_preserved_as_blocked"
      ],
      "still_blocks_stage_c_authority": stage_b_review[
        "still_blocks_stage_c_authority"
      ],
      "stage_c_authority_promotion_allowed": False,
    },
    "authority_decision": {
      "benchmark_gate_result": "blocked",
      "replacement_allowed": False,
      "stage_c_component_probability_authority_ready": False,
      "stock_component_probability_authority": False,
      "pk_authority": False,
      "deterministic_fuze_authority": False,
      "blocked_residual_ids": list(FOCUSED_RESIDUAL_IDS),
    },
    "authority_guards": authority_guards,
    "remaining_paths": [
      {
        "residual_id": row["residual_id"],
        "benchmark_evidence_status": row["benchmark_evidence_status"],
        "missing_evidence": row["missing_evidence"],
        "forced_review_trigger": row["forced_review_trigger"],
      }
      for row in _residual_benchmark_evidence_status(
        review_artifact=review_artifact
      )
    ],
    "explicit_boundaries": [
      "blocked benchmark manifest only; not independent fragility truth",
      "candidate evidence rows must not replace synthetic_sigmoid now",
      "do not create or update stock descriptors from this artifact",
      "do not promote Stage C component probability while Stage B remains blocked",
      "stock_component_probability_authority=false remains mandatory",
      "pk_authority=false and deterministic_fuze_authority=false remain mandatory",
    ],
  }

def _comparison_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
  return {
    "package_id": artifact["package_id"],
    "schema_version": COMPARISON_SCHEMA_VERSION,
    "generated_on": artifact["generated_on"],
    "status": "blocked_author_side_candidate_vs_synthetic_sigmoid_comparison",
    "scope": artifact["scope"],
    "truth_status": artifact["truth_inventory"]["truth_status"],
    "comparison": artifact["candidate_vs_synthetic_sigmoid_comparison"],
    "uncertainty_calibration_metrics": artifact[
      "uncertainty_calibration_metrics"
    ],
    "independence_trace": artifact["independence_trace"],
    "authority_decision": artifact["authority_decision"],
    "authority_guards": artifact["authority_guards"],
  }

def _retained_manifest(
  *,
  artifact: dict[str, Any],
  artifact_sha256: str,
  comparison_sha256: str,
) -> dict[str, Any]:
  guards = artifact["authority_guards"]
  return {
    "package_id": PACKAGE_ID,
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "status": "blocked_stage_c_fragility_benchmark_manifest_only",
    "retention_scope": "stage_c_fragility_benchmark_author_side_blocked_only",
    "artifact_count": 2,
    "artifacts": [
      {
        "artifact_id": "stage_c_fragility_benchmark",
        "path": "stage_c_fragility_benchmark.json",
        "role": (
          "blocked right_aileron_actuator fragility benchmark evidence "
          "manifest"
        ),
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "sha256": artifact_sha256,
      },
      {
        "artifact_id": "candidate_vs_synthetic_sigmoid_comparison",
        "path": "candidate_vs_synthetic_sigmoid_comparison.json",
        "role": (
          "author-side candidate evidence-row vs synthetic_sigmoid "
          "comparison and blocked calibration ledger"
        ),
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "sha256": comparison_sha256,
      },
    ],
    "authority_granted": False,
    "replacement_allowed": guards["replacement_allowed"],
    "stock_component_probability_authority": guards[
      "stock_component_probability_authority"
    ],
    "pk_authority": guards["pk_authority"],
    "deterministic_fuze_authority": guards["deterministic_fuze_authority"],
    "stage_b_dependency_preserved_as_blocked": artifact[
      "stage_b_dependency_interlock"
    ]["dependency_preserved_as_blocked"],
    "external_truth_present": artifact["truth_inventory"][
      "external_truth_present"
    ],
  }

def write_retained_artifacts(
  artifact: dict[str, Any],
  retained_dir: Path,
) -> dict[str, Any]:
  retained_dir.mkdir(parents=True, exist_ok=True)

  artifact_payload = _canonical_json(artifact) + "\n"
  artifact_path = retained_dir / "stage_c_fragility_benchmark.json"
  artifact_path.write_text(artifact_payload, encoding="utf-8")

  comparison = _comparison_artifact(artifact)
  comparison_payload = _canonical_json(comparison) + "\n"
  comparison_path = retained_dir / "candidate_vs_synthetic_sigmoid_comparison.json"
  comparison_path.write_text(comparison_payload, encoding="utf-8")

  manifest = _retained_manifest(
    artifact=artifact,
    artifact_sha256=_sha256_text(artifact_payload),
    comparison_sha256=_sha256_text(comparison_payload),
  )
  manifest_path = retained_dir / "manifest.json"
  manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
  manifest["manifest_path"] = _display_path(manifest_path, REPO_ROOT)
  return manifest

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate blocked Stage C fragility benchmark evidence for the "
      "right_aileron_actuator candidate."
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
      "Optional retained artifact directory. Writes benchmark, comparison "
      "and manifest JSON files."
    ),
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_c_fragility_benchmark()
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
