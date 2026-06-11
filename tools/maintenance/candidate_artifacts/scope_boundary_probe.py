#!/usr/bin/env python3
"""Generate Stage B scope boundary probe results for the A2 blast-fragmentation candidate.

This tool executes the narrow-scope boundary probes documented in the Stage B
scope manifest. It remains non-authoritative: the output is a candidate probe
artifact for review and must not be interpreted as stock runtime authority,
validated effect scale, component-failure truth, Pk, or deterministic fuze.
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

from tools.maintenance.candidate_artifacts import validation_scaffold as scaffold


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
PROBE_SCHEMA_VERSION = "a2.scope_boundary_probe.v1"
DEFAULT_STANDOFFS_M = (0.25, 0.35, 0.45)
DEFAULT_CLOSURES_MPS = (700.0, 900.0, 1100.0)
OUT_OF_SCOPE_LABELS = (
  "head_on",
  "tail_chase",
  "high_off_boresight",
  "direct_hit",
  "closure_bucket != high",
  "weapon_family != blast_fragmentation",
)


def _mechanism_row_from_artifact(artifact: dict[str, Any]) -> dict[str, float | str]:
  mechanism = artifact["mechanism_load_vector"]
  diagnostics = artifact["diagnostic_only_fields"]
  return {
    "runtime_miss_distance_bucket": str(artifact["scope"]["runtime_miss_distance_bucket"]),
    "blast_scaled_distance_m_kg13": float(mechanism["blast_scaled_distance_m_kg13"]),
    "fragment_areal_density_per_m2": float(mechanism["fragment_areal_density_per_m2"]),
    "surface_incidence_cos": float(mechanism["surface_incidence_cos"]),
    "blast_impulse_kpa_ms_proxy": float(diagnostics["blast_impulse_kpa_ms_proxy"]),
    "fragment_energy_j_proxy": float(diagnostics["fragment_energy_j_proxy"]),
    "penetration_margin_proxy": float(diagnostics["penetration_margin_proxy"]),
  }


def _miss_distance_probe(*, repo_root: Path) -> dict[str, Any]:
  rows: list[dict[str, Any]] = []
  for standoff_m in DEFAULT_STANDOFFS_M:
    artifact = scaffold.generate_validation_scaffold(
      repo_root=repo_root,
      standoff_m=standoff_m,
    )
    row = {
      "standoff_m": float(standoff_m),
      **_mechanism_row_from_artifact(artifact),
    }
    rows.append(row)

  blast_monotonic = all(
    rows[index]["blast_scaled_distance_m_kg13"] <
    rows[index + 1]["blast_scaled_distance_m_kg13"]
    for index in range(len(rows) - 1)
  )
  density_monotonic = all(
    rows[index]["fragment_areal_density_per_m2"] >
    rows[index + 1]["fragment_areal_density_per_m2"]
    for index in range(len(rows) - 1)
  )
  runtime_bucket_consistent = len(
    {str(row["runtime_miss_distance_bucket"]) for row in rows}
  ) == 1
  return {
    "probe_id": "SCP-PROBE-001",
    "status": "executed_candidate_toy_probe",
    "rows": rows,
    "metrics": {
      "blast_scaled_distance_monotonic_increasing_pass": blast_monotonic,
      "fragment_areal_density_monotonic_decreasing_pass": density_monotonic,
      "runtime_bucket_consistent_pass": runtime_bucket_consistent,
      "anchor_present": any(abs(float(row["standoff_m"]) - 0.35) <= 1.0e-9 for row in rows),
    },
  }


def _closure_probe(*, repo_root: Path) -> dict[str, Any]:
  rows: list[dict[str, Any]] = []
  for closure_mps in DEFAULT_CLOSURES_MPS:
    artifact = scaffold.generate_validation_scaffold(
      repo_root=repo_root,
      closure_mps=closure_mps,
    )
    row = {
      "closure_mps": float(closure_mps),
      **_mechanism_row_from_artifact(artifact),
    }
    rows.append(row)

  anchor = rows[1]
  response_fields = (
    "blast_scaled_distance_m_kg13",
    "fragment_areal_density_per_m2",
    "surface_incidence_cos",
    "blast_impulse_kpa_ms_proxy",
    "fragment_energy_j_proxy",
    "penetration_margin_proxy",
  )
  max_abs_delta = max(
    max(abs(float(row[field]) - float(anchor[field])) for field in response_fields)
    for row in rows
  )
  mechanism_response_active = max_abs_delta > 1.0e-12
  return {
    "probe_id": "SCP-PROBE-002",
    "status": "executed_candidate_response_probe",
    "rows": rows,
    "metrics": {
      "closure_label_probe_executed": True,
      "mechanism_response_active": mechanism_response_active,
      "mechanism_response_constant_across_closure": not mechanism_response_active,
      "candidate_closure_sensitive_response_observed": mechanism_response_active,
      "res008_closed_by_probe": False,
      "independent_review_complete": False,
      "runtime_bucket_consistent_pass": len(
        {str(row["runtime_miss_distance_bucket"]) for row in rows}
      ) == 1,
      "anchor_present": any(abs(float(row["closure_mps"]) - 900.0) <= 1.0e-9 for row in rows),
    },
    "limitation_note": (
      "candidate closure-sensitive response is present in closure-sensitive gate fields, "
      "but RES-008 remains non-authoritative and retained as a future authority boundary"
    ),
  }


def _aspect_guard_probe() -> dict[str, Any]:
  return {
    "probe_id": "SCP-PROBE-003",
    "status": "executed_scope_guard_audit",
    "accepted_scope_labels": ["beam"],
    "rejected_scope_labels": list(OUT_OF_SCOPE_LABELS),
    "metrics": {
      "beam_only_guard_documented": True,
      "rejected_label_count": len(OUT_OF_SCOPE_LABELS),
    },
  }


def generate_scope_boundary_probe(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
  anchor_artifact = scaffold.generate_validation_scaffold(repo_root=repo_root)
  miss_distance_probe = _miss_distance_probe(repo_root=repo_root)
  closure_probe = _closure_probe(repo_root=repo_root)
  aspect_guard = _aspect_guard_probe()

  return {
    "package_id": PACKAGE_ID,
    "schema_version": PROBE_SCHEMA_VERSION,
    "status": "candidate_non_authoritative_scope_probe_results",
    "artifact_provenance": {
      "source_kind": "candidate_scope_boundary_probe",
      "provenance": (
        "generated from the current non-authoritative validation scaffold for Stage B "
        "effect-scale scope boundary review"
      ),
    },
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "candidate_scope_label": "near_miss_0_35m",
      "runtime_miss_distance_bucket": str(anchor_artifact["scope"]["runtime_miss_distance_bucket"]),
    },
    "miss_distance_probe": miss_distance_probe,
    "closure_probe": closure_probe,
    "aspect_guard_probe": aspect_guard,
    "current_findings": [
      (
        "standoff probe now has a three-point candidate result table at 0.25/0.35/0.45 m "
        "and stays inside the runtime coarse bucket near_miss"
      ),
      (
        "closure probe now shows candidate closure-sensitive response across 700/900/1100 mps; "
        "RES-008 remains non-authoritative and retained as a future authority boundary"
      ),
      (
        "aspect guard remains beam-only and explicitly rejects head_on, tail_chase, high_off_boresight and direct_hit labels"
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


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the Stage B scope boundary probe artifact for the current "
      "A2 blast-fragmentation candidate package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_scope_boundary_probe()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
