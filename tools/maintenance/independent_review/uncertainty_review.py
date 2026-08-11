#!/usr/bin/env python3
"""Gate RES-011 uncertainty review for the A2 blast-fragmentation package.

The current evidence has two different shapes:

* Stage B effect scale has an author-side seed-window CV closeout.
* Stage C component probability has repeatability evidence only, while
 release-grade probability uncertainty coverage is still missing.

This tool records that split without promoting any stock/runtime authority.
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

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.a2_packet_paths import (  # noqa: E402
  CANDIDATE_PACKAGE_DIR as A2_CANDIDATE_PACKAGE_DIR,
)

from tools.maintenance.retained_artifacts.manifest_integrity import (
  _sha256_file,
  add_retained_gate_output_args,
  write_and_hash_json,
)
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
GATE_SCHEMA_VERSION = "a2.uncertainty_review_gate.v1"
MANIFEST_SCHEMA_VERSION = "a2.uncertainty_review_retained_artifacts.v1"
GENERATED_ON = "2026-05-31"
PACKAGE_DIR = (
  A2_CANDIDATE_PACKAGE_DIR
)
DEFAULT_RETAINED_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "uncertainty_review_20260531"
)
CV_THRESHOLD = 0.05

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def _payload_sha256(payload: dict[str, Any]) -> str:
  return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

def _read_text(path: Path) -> str:
  if not path.is_file():
    return ""
  return path.read_text(encoding="utf-8")

def _load_json(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  return json.loads(path.read_text(encoding="utf-8"))

def _evidence_record(
  *,
  evidence_id: str,
  path: Path,
  repo_root: Path,
  required_for: str,
  payload: dict[str, Any] | None = None,
  text: str = "",
) -> dict[str, Any]:
  present = path.is_file()
  record: dict[str, Any] = {
    "evidence_id": evidence_id,
    "path": _display_path(path, repo_root),
    "present": present,
    "required_for": required_for,
  }
  if present:
    record["content_sha256"] = _sha256_file(path)
  if payload is not None:
    record["schema_version"] = payload.get("schema_version", "")
    record["status"] = payload.get("status", "")
  elif text:
    record["status"] = "text_present"
  else:
    record["status"] = "missing"
  return record

def _cv_row(metric: str, actual: float) -> dict[str, Any]:
  return {
    "metric": metric,
    "actual": actual,
    "threshold": f"<= {CV_THRESHOLD}",
    "pass": actual <= CV_THRESHOLD,
  }

def _stage_b_review(
  *,
  result_pack: dict[str, Any] | None,
  closeout_doc_text: str,
) -> dict[str, Any]:
  if result_pack is None:
    return {
      "stage": "stage_b_effect_scale",
      "review_result": "fail_closed_missing_result_pack",
      "author_side_closeout_complete": False,
      "seed_window_cv_pass": False,
      "cv_rows": [],
      "release_uncertainty_review_status": "blocked",
      "missing_evidence": [
        "retained Stage B validation result pack",
        "author-side seed-window CV summary",
      ],
    }

  summary = result_pack.get("uncertainty_result_summary", {})
  cv_rows = [
    _cv_row(
      "fragment_areal_density_per_m2.cv",
      float(summary.get("fragment_areal_density_cv", 1.0)),
    ),
    _cv_row(
      "blast_impulse_kpa_ms_proxy.cv",
      float(summary.get("blast_impulse_cv", 1.0)),
    ),
    _cv_row(
      "fragment_energy_j_proxy.cv",
      float(summary.get("fragment_energy_cv", 1.0)),
    ),
    _cv_row(
      "penetration_margin_proxy.cv",
      float(summary.get("penetration_margin_cv", 1.0)),
    ),
  ]
  seed_window_cv_pass = bool(summary.get("seed_window_cv_pass")) and all(
    row["pass"] for row in cv_rows
  )
  doc_records_blocked = (
    "author_side_uncertainty_snapshot_complete_release_blocked"
    in closeout_doc_text
    and "independent review" in closeout_doc_text
  )
  return {
    "stage": "stage_b_effect_scale",
    "review_result": (
      "narrow_author_side_uncertainty_closeout_complete_release_blocked"
      if seed_window_cv_pass and doc_records_blocked
      else "fail_closed_stage_b_uncertainty_evidence_incomplete"
    ),
    "author_side_closeout_complete": seed_window_cv_pass,
    "seed_window_cv_pass": seed_window_cv_pass,
    "cv_rows": cv_rows,
    "result_interpretation": summary.get("result_interpretation", ""),
    "release_uncertainty_review_status": "blocked_pending_independent_coverage_review",
    "narrow_acceptance": (
      "Stage B author-side seed-window CV gate passes for effect-scale "
      "candidate review only"
    ),
    "not_release_grade_because": [
      "coverage interpretation is not independently reviewed",
      "result-level uncertainty audit is absent",
      "independent uncertainty reviewer signoff is absent",
    ],
    "minimum_evidence_path": [
      "retain reviewer-owned uncertainty coverage interpretation for Stage B",
      "attach result-level uncertainty audit to the formal validation closeout",
      "rerun this gate after independent review signoff is present",
    ],
  }

def _stage_c_review(
  *,
  fragility_review: dict[str, Any] | None,
  component_result_pack: dict[str, Any] | None,
  fragility_benchmark: dict[str, Any] | None,
  closeout_doc_text: str,
) -> dict[str, Any]:
  if fragility_review is None:
    return {
      "stage": "stage_c_component_probability",
      "review_result": "blocked_missing_fragility_review_gate",
      "author_repeatability_review_result": "missing",
      "component_failure_probability_cv": None,
      "blocking_condition_ids": ["BLOCK-CP-004"],
      "missing_evidence": ["retained Stage C fragility review gate"],
    }

  uncertainty = fragility_review.get("uncertainty_review", {})
  residual_rows = {
    row.get("residual_id"): row
    for row in fragility_review.get("residual_gate_results", [])
  }
  res011 = residual_rows.get("RES-011", {})
  benchmark_uncertainty = (
    fragility_benchmark or {}
  ).get("uncertainty_calibration_metrics", {})
  component_summary = (
    component_result_pack or {}
  ).get("component_probability_result_summary", {})
  fragility_surface_summary = (
    component_result_pack or {}
  ).get("fragility_surface_summary", {})
  closeout_doc_is_plan = (
    "prepared / candidate / non-authoritative"
    in closeout_doc_text
    and "RES-011" in closeout_doc_text
  )
  return {
    "stage": "stage_c_component_probability",
    "review_result": "blocked_probability_uncertainty_coverage_missing",
    "author_repeatability_review_result": uncertainty.get(
      "author_repeatability_review_result", ""
    ),
    "uncertainty_closeout_result": uncertainty.get(
      "uncertainty_closeout_result", "blocked"
    ),
    "anchor_probe_label": uncertainty.get("anchor_probe_label", ""),
    "seed_values": uncertainty.get("seed_values", []),
    "component_failure_probability_cv": uncertainty.get(
      "component_failure_probability_cv"
    ),
    "component_result_pack_anchor_cv": fragility_surface_summary.get(
      "anchor_seed_window_probability_cv"
    ),
    "component_result_pack_probability_source": component_summary.get(
      "baseline_component_probability_source"
    ),
    "benchmark_uncertainty_metrics": benchmark_uncertainty.get("metrics", {}),
    "benchmark_uncertainty_coverage_limits": benchmark_uncertainty.get(
      "coverage_limits", []
    ),
    "blocking_condition_ids": res011.get("blocking_condition_ids", ["BLOCK-CP-004"]),
    "blocking_conditions": res011.get("blocking_conditions", []),
    "closeout_doc_is_review_package_only": closeout_doc_is_plan,
    "missing_evidence": [
      "independent calibration or coverage scoring",
      "scenario spread beyond fixed author-side probes",
      "reviewer-accepted confidence or coverage interval",
      "release-grade uncertainty budget for stock descriptor admission",
    ],
    "minimum_evidence_path": [
      "run independent Brier/log-loss or calibration-curve scoring for the component-probability surface",
      "extend seed and scenario spread beyond the current author-side probe",
      "record reviewer-accepted uncertainty bounds before any component-probability authority promotion",
    ],
  }

def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "stock_runtime_authority_granted": False,
    "effect_scale_authority_granted": False,
    "effect_scale_authority_in_stock": False,
    "component_failure_probability_authority_granted": False,
    "component_failure_probability_authority_in_stock": False,
    "pk_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "formal_validation_manifest_promoted": False,
    "hard_gate_pass_is_release": False,
  }

def generate_uncertainty_review_gate(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
  stage_b_result_pack_path = (
    package_dir
    / "retained_artifacts"
    / "stage_b_effect_scale_20260530"
    / "stage_b_validation_result_pack.json"
  )
  stage_b_closeout_doc_path = (
    package_dir / "validation_uncertainty_closeout_stage_b_effect_scale_20260531.zh.md"
  )
  stage_c_result_pack_path = (
    package_dir
    / "retained_artifacts"
    / "stage_c_component_probability_20260530"
    / "stage_c_component_probability_result_pack.json"
  )
  stage_c_fragility_review_path = (
    package_dir
    / "retained_artifacts"
    / "stage_c_fragility_review_20260531"
    / "stage_c_fragility_review_gate.json"
  )
  stage_c_fragility_benchmark_path = (
    package_dir
    / "retained_artifacts"
    / "stage_c_fragility_benchmark_20260531"
    / "stage_c_fragility_benchmark.json"
  )
  stage_c_closeout_doc_path = (
    package_dir
    / "validation_uncertainty_closeout_stage_c_component_probability_20260531.zh.md"
  )

  stage_b_result_pack = _load_json(stage_b_result_pack_path)
  stage_c_result_pack = _load_json(stage_c_result_pack_path)
  stage_c_fragility_review = _load_json(stage_c_fragility_review_path)
  stage_c_fragility_benchmark = _load_json(stage_c_fragility_benchmark_path)
  stage_b_closeout_doc_text = _read_text(stage_b_closeout_doc_path)
  stage_c_closeout_doc_text = _read_text(stage_c_closeout_doc_path)

  consumed_evidence = [
    _evidence_record(
      evidence_id="UNC-STAGE-B-RESULT-PACK",
      path=stage_b_result_pack_path,
      repo_root=repo_root,
      required_for="Stage B RES-011 seed-window CV review",
      payload=stage_b_result_pack,
    ),
    _evidence_record(
      evidence_id="UNC-STAGE-B-CLOSEOUT-DOC",
      path=stage_b_closeout_doc_path,
      repo_root=repo_root,
      required_for="Stage B RES-011 closeout interpretation",
      text=stage_b_closeout_doc_text,
    ),
    _evidence_record(
      evidence_id="UNC-STAGE-C-RESULT-PACK",
      path=stage_c_result_pack_path,
      repo_root=repo_root,
      required_for="Stage C probability repeatability summary",
      payload=stage_c_result_pack,
    ),
    _evidence_record(
      evidence_id="UNC-STAGE-C-FRAGILITY-REVIEW",
      path=stage_c_fragility_review_path,
      repo_root=repo_root,
      required_for="Stage C RES-011 blocking condition trace",
      payload=stage_c_fragility_review,
    ),
    _evidence_record(
      evidence_id="UNC-STAGE-C-FRAGILITY-BENCHMARK",
      path=stage_c_fragility_benchmark_path,
      repo_root=repo_root,
      required_for="Stage C candidate-vs-synthetic uncertainty limits",
      payload=stage_c_fragility_benchmark,
    ),
    _evidence_record(
      evidence_id="UNC-STAGE-C-CLOSEOUT-DOC",
      path=stage_c_closeout_doc_path,
      repo_root=repo_root,
      required_for="Stage C RES-011 closeout plan interpretation",
      text=stage_c_closeout_doc_text,
    ),
  ]
  missing_evidence = [
    {
      "evidence_id": row["evidence_id"],
      "path": row["path"],
      "blocker": f"{row['required_for']} evidence is missing",
    }
    for row in consumed_evidence
    if not row["present"]
  ]

  stage_b = _stage_b_review(
    result_pack=stage_b_result_pack,
    closeout_doc_text=stage_b_closeout_doc_text,
  )
  stage_c = _stage_c_review(
    fragility_review=stage_c_fragility_review,
    component_result_pack=stage_c_result_pack,
    fragility_benchmark=stage_c_fragility_benchmark,
    closeout_doc_text=stage_c_closeout_doc_text,
  )
  stage_b_narrow_pass = stage_b["review_result"] == (
    "narrow_author_side_uncertainty_closeout_complete_release_blocked"
  )
  stage_c_blocked = stage_c["review_result"] == (
    "blocked_probability_uncertainty_coverage_missing"
  )
  fail_closed = bool(missing_evidence) or not stage_b_narrow_pass

  return {
    "package_id": PACKAGE_ID,
    "schema_version": GATE_SCHEMA_VERSION,
    "generated_on": GENERATED_ON,
    "status": (
      "uncertainty_review_stage_b_narrow_pass_stage_c_blocked_release_blocked"
      if stage_b_narrow_pass and stage_c_blocked and not missing_evidence
      else "uncertainty_review_fail_closed"
    ),
    "review_target": "RES-011_uncertainty_review_only",
    "release_target": "none_review_gate_record_only",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "candidate_scope_label": "near_miss_0_35m",
    },
    "consumed_evidence": consumed_evidence,
    "missing_evidence": missing_evidence,
    "stage_b_uncertainty_review": stage_b,
    "stage_c_uncertainty_review": stage_c,
    "residual_status": {
      "residual_id": "RES-011",
      "combined_decision": (
        "blocked_release_grade_uncertainty_review"
        if not fail_closed
        else "fail_closed_missing_or_incomplete_uncertainty_evidence"
      ),
      "stage_b_decision": (
        "narrow_author_side_pass_release_blocked"
        if stage_b_narrow_pass
        else "fail_closed"
      ),
      "stage_c_decision": "blocked_probability_uncertainty_coverage_missing",
      "residual_register_status_after_gate": "remains_open_release_blocked",
      "release_blocked": True,
      "review_passed_items": [
        "Stage B seed-window CV rows pass current author-side thresholds",
        "Stage C fixed-seed repeatability is stable enough for reviewer input",
      ],
      "missing_release_grade_items": [
        "independent Stage B uncertainty coverage review",
        "Stage C calibration or coverage scoring",
        "Stage C scenario spread beyond author-side probes",
        "reviewer-accepted uncertainty bounds",
        "formal validation result promotion and signoff",
      ],
      "forced_review_trigger": (
        "rerun after independent uncertainty coverage artifacts and signoff "
        "exist for the intended release target"
      ),
    },
    "review_decision": {
      "stage_b_author_side_uncertainty_closeout_complete": stage_b_narrow_pass,
      "stage_b_release_grade_uncertainty_complete": False,
      "stage_c_author_repeatability_present": stage_c.get(
        "author_repeatability_review_result"
      )
      == "review_passed",
      "stage_c_release_grade_uncertainty_complete": False,
      "res011_release_grade_complete": False,
      "release_ready": False,
      "release_blocked": True,
    },
    "authority_guards": _authority_guards(),
    "explicit_boundaries": [
      "this is an uncertainty review gate only",
      "Stage B author-side CV pass is not release-grade uncertainty coverage",
      "Stage C fixed-seed repeatability is not probability calibration",
      "no stock descriptor, effect-scale authority, component-probability authority, Pk authority or deterministic-fuze authority is released",
    ],
  }

def write_retained_artifacts(
  *,
  output_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
  artifact = generate_uncertainty_review_gate(
    repo_root=repo_root,
    package_dir=package_dir,
  )
  gate_path = output_dir / "uncertainty_review_gate.json"
  gate_content_sha256 = write_and_hash_json(gate_path, artifact)
  manifest = {
    "package_id": PACKAGE_ID,
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "status": "uncertainty_review_retained_release_blocked",
    "generated_on": GENERATED_ON,
    "artifact_dir": _display_path(output_dir, repo_root),
    "retention_scope": "RES-011_uncertainty_review_only",
    "artifacts": [
      {
        "artifact_key": "uncertainty_review_gate",
        "filename": gate_path.name,
        "relative_path": _display_path(gate_path, repo_root),
        "schema_version": GATE_SCHEMA_VERSION,
        "status": artifact["status"],
        "content_sha256": gate_content_sha256,
        "payload_sha256": _payload_sha256(artifact),
        "size_bytes": gate_path.stat().st_size,
        "origin_class": "uncertainty_review_gate_record_only",
        "allowed_claim": "RES-011 uncertainty review state is retained",
        "forbidden_claim": (
          "release readiness, stock runtime authority, component-probability "
          "authority, Pk authority, deterministic-fuze authority or "
          "release-grade uncertainty coverage"
        ),
      }
    ],
    "review_decision": dict(artifact["review_decision"]),
    "authority_guards": _authority_guards(),
  }
  manifest_path = output_dir / "manifest.json"
  write_and_hash_json(manifest_path, manifest)
  return {
    "gate": artifact,
    "manifest": manifest,
    "paths": {"gate": gate_path, "manifest": manifest_path},
  }

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Generate retained RES-011 uncertainty review gate artifacts."
  )
  add_retained_gate_output_args(parser, retained_dir_default=DEFAULT_RETAINED_DIR)
  args = parser.parse_args(argv)

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
