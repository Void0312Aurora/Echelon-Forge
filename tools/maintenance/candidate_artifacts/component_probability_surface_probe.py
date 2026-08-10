#!/usr/bin/env python3
"""Generate a Stage C component-probability surface probe for A2.

This tool expands the current Stage C candidate from a single positive-path row
into a small runtime-aligned surface probe inside the same narrow near-miss
scope. It remains explicitly non-authoritative: the output is a candidate
fragility-surface and repeatability snapshot only, not validated fragility
truth, stock runtime authority, Pk, or deterministic-fuze authority.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any


_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import resolve_repo_path, ensure_repo_imports, repo_root

ensure_repo_imports()
REPO_ROOT = Path(repo_root())

from tools.maintenance.candidate_artifacts import runtime_authority_exercise as authority_pack


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SURFACE_PROBE_SCHEMA_VERSION = "a2.stage_c_component_probability_surface_probe.v1"
PROBE_POINTS = (
  {"probe_label": "inner", "local_point": (-0.753, 5.5, 0.0), "probability": 0.52},
  {"probe_label": "middle", "local_point": (-0.753, 5.8, 0.0), "probability": 0.37},
  {"probe_label": "outer", "local_point": (-0.753, 6.0, 0.0), "probability": 0.21},
)
REPEATABILITY_SEEDS = (20260526, 20260527, 20260528)
DEFAULT_DAMAGE = authority_pack.DEFAULT_DAMAGE
DEFAULT_RADIUS_M = authority_pack.DEFAULT_RADIUS_M
DEFAULT_MISSILE_VELOCITY = authority_pack.DEFAULT_MISSILE_VELOCITY
PRIMARY_COMPONENT_NAME = "right_aileron_actuator"
PRIMARY_COMPONENT_SYSTEM = "flight_control"
PRIMARY_COMPONENT_REDUNDANCY_GROUP = "lateral_flight_control_actuators"


def _copy_database_with_f16_vulnerability(
  tmpdir: str,
  vulnerability_patch: dict[str, Any],
  *,
  descriptor: dict[str, Any],
) -> str:
  source_db = Path(resolve_repo_path("examples", "config", "database"))
  db_dir = Path(tmpdir) / "database"
  shutil.copytree(source_db, db_dir)

  unit_path = db_dir / "aircraft" / "units" / "f16c_block50.json"
  unit = json.loads(unit_path.read_text(encoding="utf-8"))
  vulnerability = dict(unit["damage_model"].get("vulnerability", {}))
  vulnerability.update(vulnerability_patch)
  unit["damage_model"]["vulnerability"] = vulnerability
  unit_path.write_text(json.dumps(unit), encoding="utf-8")

  evidence_dir = db_dir / "damage" / "vulnerability_evidence"
  evidence_dir.mkdir(parents=True, exist_ok=True)
  descriptor_data = dict(descriptor)
  dataset_id = str(descriptor_data["dataset_id"])
  if descriptor_data.get("calibration_status") == "calibrated":
    descriptor_data.setdefault("schema_version", "a2.vulnerability_evidence.v1")
    descriptor_data.setdefault("source_ref", f"fixture://descriptor/{dataset_id}")
  descriptor_path = evidence_dir / f"{dataset_id}.json"
  descriptor_path.write_text(json.dumps(descriptor_data), encoding="utf-8")
  return str(db_dir)


def _midpoint(lhs: float, rhs: float) -> float:
  return (float(lhs) + float(rhs)) / 2.0


def _sample_primary_event(
  *,
  database_path: str,
  local_point: tuple[float, float, float],
  seed: int,
) -> object:
  return authority_pack._sample_stock_near_miss_event(
    database_path=database_path,
    local_point=local_point,
    missile_velocity=DEFAULT_MISSILE_VELOCITY,
    damage=DEFAULT_DAMAGE,
    radius_m=DEFAULT_RADIUS_M,
    seed=seed,
  )


def _event_primary_summary(event: object) -> dict[str, Any]:
  return {
    "component_primary_name": str(event.component_primary_name),
    "component_primary_system": str(event.component_primary_system),
    "component_primary_redundancy_group_id": str(
      event.component_primary_redundancy_group_id
    ),
    "component_failure_probability": float(event.component_failure_probability),
    "component_failure_probability_source": str(event.component_failure_probability_source),
    "component_failure_probability_calibrated": bool(
      event.component_failure_probability_calibrated
    ),
    "component_failure_probability_evidence_row_id": str(
      event.component_failure_probability_evidence_row_id
    ),
    "component_failure_probability_evidence_source_ref": str(
      event.component_failure_probability_evidence_source_ref
    ),
    "component_failure_probability_evidence_provenance": str(
      event.component_failure_probability_evidence_provenance
    ),
    "component_primary_mechanism_blast_scaled_distance_m_kg13": float(
      event.component_primary_mechanism_blast_scaled_distance_m_kg13
    ),
    "component_primary_mechanism_fragment_areal_density_per_m2": float(
      event.component_primary_mechanism_fragment_areal_density_per_m2
    ),
    "component_primary_mechanism_fragment_energy_j": float(
      event.component_primary_mechanism_fragment_energy_j
    ),
    "component_primary_mechanism_penetration_margin": float(
      event.component_primary_mechanism_penetration_margin
    ),
    "component_primary_mechanism_blast_impulse_kpa_ms": float(
      event.component_primary_mechanism_blast_impulse_kpa_ms
    ),
    "component_primary_mechanism_surface_incidence_cos": float(
      event.component_primary_mechanism_surface_incidence_cos
    ),
  }


def _build_surface_probe_descriptor(
  *,
  inner_event: object,
  middle_event: object,
  outer_event: object,
) -> dict[str, Any]:
  anchor_artifact = authority_pack.generate_runtime_aligned_authority_pack(
    local_point=PROBE_POINTS[0]["local_point"]
  )
  descriptor = dict(anchor_artifact["component_failure_probability_descriptor_candidate"])
  descriptor["dataset_id"] = (
    "unit_test_a2_blastfrag_runtime_aligned_component_probability_surface_probe"
  )
  descriptor["validation_artifact_ref"] = (
    "fixture://a2-blastfrag/runtime-aligned-component-probability-surface-probe"
  )

  inner_summary = _event_primary_summary(inner_event)
  middle_summary = _event_primary_summary(middle_event)
  outer_summary = _event_primary_summary(outer_event)

  rows = [
    {
      "row_id": "global-fallback",
      "source_ref": "fixture://stage-c-surface-probe/global-fallback",
      "provenance": "author-side global fallback row for Stage C surface probe only",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss",
      "component_failure_probability": 0.09,
    },
    {
      "row_id": "component-inner",
      "source_ref": "fixture://stage-c-surface-probe/component-inner",
      "provenance": "author-side inner-bucket component row for Stage C surface probe only",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss",
      "component_name": PRIMARY_COMPONENT_NAME,
      "component_system": PRIMARY_COMPONENT_SYSTEM,
      "component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
      "max_blast_scaled_distance_m_kg13": _midpoint(
        inner_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
        middle_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
      ),
      "min_fragment_areal_density_per_m2": _midpoint(
        inner_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
        middle_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
      ),
      "min_fragment_energy_j": _midpoint(
        inner_summary["component_primary_mechanism_fragment_energy_j"],
        middle_summary["component_primary_mechanism_fragment_energy_j"],
      ),
      "min_penetration_margin": _midpoint(
        inner_summary["component_primary_mechanism_penetration_margin"],
        middle_summary["component_primary_mechanism_penetration_margin"],
      ),
      "min_blast_impulse_kpa_ms": _midpoint(
        inner_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
        middle_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
      ),
      "min_surface_incidence_cos": 0.0,
      "component_failure_probability": float(PROBE_POINTS[0]["probability"]),
    },
    {
      "row_id": "component-middle",
      "source_ref": "fixture://stage-c-surface-probe/component-middle",
      "provenance": "author-side middle-bucket component row for Stage C surface probe only",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss",
      "component_name": PRIMARY_COMPONENT_NAME,
      "component_system": PRIMARY_COMPONENT_SYSTEM,
      "component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
      "min_blast_scaled_distance_m_kg13": _midpoint(
        inner_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
        middle_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
      ),
      "max_blast_scaled_distance_m_kg13": _midpoint(
        middle_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
        outer_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
      ),
      "min_fragment_areal_density_per_m2": _midpoint(
        middle_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
        outer_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
      ),
      "max_fragment_areal_density_per_m2": _midpoint(
        inner_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
        middle_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
      ),
      "min_fragment_energy_j": _midpoint(
        middle_summary["component_primary_mechanism_fragment_energy_j"],
        outer_summary["component_primary_mechanism_fragment_energy_j"],
      ),
      "max_fragment_energy_j": _midpoint(
        inner_summary["component_primary_mechanism_fragment_energy_j"],
        middle_summary["component_primary_mechanism_fragment_energy_j"],
      ),
      "min_penetration_margin": _midpoint(
        middle_summary["component_primary_mechanism_penetration_margin"],
        outer_summary["component_primary_mechanism_penetration_margin"],
      ),
      "max_penetration_margin": _midpoint(
        inner_summary["component_primary_mechanism_penetration_margin"],
        middle_summary["component_primary_mechanism_penetration_margin"],
      ),
      "min_blast_impulse_kpa_ms": _midpoint(
        middle_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
        outer_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
      ),
      "max_blast_impulse_kpa_ms": _midpoint(
        inner_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
        middle_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
      ),
      "min_surface_incidence_cos": 0.0,
      "component_failure_probability": float(PROBE_POINTS[1]["probability"]),
    },
    {
      "row_id": "component-outer",
      "source_ref": "fixture://stage-c-surface-probe/component-outer",
      "provenance": "author-side outer-bucket component row for Stage C surface probe only",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss",
      "component_name": PRIMARY_COMPONENT_NAME,
      "component_system": PRIMARY_COMPONENT_SYSTEM,
      "component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
      "min_blast_scaled_distance_m_kg13": _midpoint(
        middle_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
        outer_summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
      ),
      "max_fragment_areal_density_per_m2": _midpoint(
        middle_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
        outer_summary["component_primary_mechanism_fragment_areal_density_per_m2"],
      ),
      "max_fragment_energy_j": _midpoint(
        middle_summary["component_primary_mechanism_fragment_energy_j"],
        outer_summary["component_primary_mechanism_fragment_energy_j"],
      ),
      "max_penetration_margin": _midpoint(
        middle_summary["component_primary_mechanism_penetration_margin"],
        outer_summary["component_primary_mechanism_penetration_margin"],
      ),
      "max_blast_impulse_kpa_ms": _midpoint(
        middle_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
        outer_summary["component_primary_mechanism_blast_impulse_kpa_ms"],
      ),
      "min_surface_incidence_cos": 0.0,
      "component_failure_probability": float(PROBE_POINTS[2]["probability"]),
    },
  ]
  descriptor["rows"] = rows
  return descriptor


def _candidate_row_by_id(descriptor: dict[str, Any], row_id: str) -> dict[str, Any]:
  for row in descriptor["rows"]:
    if str(row.get("row_id", "")) == row_id:
      return row
  raise AssertionError(f"component probability surface probe row {row_id!r} not found")


def _in_gate(row: dict[str, Any], field_name: str, value: float) -> bool:
  lower_key = f"min_{field_name}"
  upper_key = f"max_{field_name}"
  if lower_key in row and float(value) < float(row[lower_key]):
    return False
  if upper_key in row and float(value) > float(row[upper_key]):
    return False
  return True


def _selected_row_covers_primary_loads(row: dict[str, Any], summary: dict[str, Any]) -> bool:
  return all(
    (
      _in_gate(
        row,
        "blast_scaled_distance_m_kg13",
        summary["component_primary_mechanism_blast_scaled_distance_m_kg13"],
      ),
      _in_gate(
        row,
        "fragment_areal_density_per_m2",
        summary["component_primary_mechanism_fragment_areal_density_per_m2"],
      ),
      _in_gate(
        row,
        "fragment_energy_j",
        summary["component_primary_mechanism_fragment_energy_j"],
      ),
      _in_gate(
        row,
        "penetration_margin",
        summary["component_primary_mechanism_penetration_margin"],
      ),
      _in_gate(
        row,
        "blast_impulse_kpa_ms",
        summary["component_primary_mechanism_blast_impulse_kpa_ms"],
      ),
      _in_gate(
        row,
        "surface_incidence_cos",
        summary["component_primary_mechanism_surface_incidence_cos"],
      ),
    )
  )


def _component_specific_rows(descriptor: dict[str, Any]) -> list[dict[str, Any]]:
  return [row for row in descriptor["rows"] if row.get("component_name")]


def _stock_baseline_probe_summary(
  *, stock_summaries: list[dict[str, Any]]
) -> dict[str, Any]:
  probability_sources = [
    str(summary["component_failure_probability_source"])
    for summary in stock_summaries
  ]
  calibrated_flags = [
    bool(summary["component_failure_probability_calibrated"])
    for summary in stock_summaries
  ]
  return {
    "source_database": "examples/config/database",
    "probe_labels": [str(point["probe_label"]) for point in PROBE_POINTS],
    "component_primary_names": [
      str(summary["component_primary_name"]) for summary in stock_summaries
    ],
    "component_probability_sources": probability_sources,
    "all_probability_sources_are_synthetic_sigmoid": all(
      source == "synthetic_sigmoid" for source in probability_sources
    ),
    "any_calibrated_component_probability": any(calibrated_flags),
    "calibrated_component_probability_flags": calibrated_flags,
  }


def _component_scope_audit(
  *,
  descriptor: dict[str, Any],
  probe_rows: list[dict[str, Any]],
) -> dict[str, Any]:
  component_rows = _component_specific_rows(descriptor)
  global_fallback = _candidate_row_by_id(descriptor, "global-fallback")
  return {
    "candidate_component_name": PRIMARY_COMPONENT_NAME,
    "candidate_component_system": PRIMARY_COMPONENT_SYSTEM,
    "candidate_component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
    "component_specific_row_ids": [
      str(row["row_id"]) for row in component_rows
    ],
    "component_specific_rows_scope_locked_to_primary_component": all(
      row.get("component_name") == PRIMARY_COMPONENT_NAME
      and row.get("component_system") == PRIMARY_COMPONENT_SYSTEM
      and row.get("component_redundancy_group_id")
      == PRIMARY_COMPONENT_REDUNDANCY_GROUP
      for row in component_rows
    ),
    "selected_rows_scope_locked_to_primary_component": all(
      bool(row["selected_row_matches_component_specific_scope"])
      for row in probe_rows
    ),
    "global_fallback_row_id": str(global_fallback["row_id"]),
    "global_fallback_row_has_no_component_identity": not any(
      key in global_fallback
      for key in (
        "component_name",
        "component_system",
        "component_redundancy_group_id",
      )
    ),
  }


def _cv_summary(values: list[float]) -> dict[str, float]:
  if not values:
    return {"min": 0.0, "max": 0.0, "mean": 0.0, "cv": 0.0}
  mean_value = sum(values) / float(len(values))
  cv = 0.0 if abs(mean_value) <= 1.0e-9 else statistics.pstdev(values) / mean_value
  return {
    "min": float(min(values)),
    "max": float(max(values)),
    "mean": float(mean_value),
    "cv": float(cv),
  }


def generate_stage_c_component_probability_surface_probe(
  *,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  source_db = resolve_repo_path("examples", "config", "database")
  stock_events = [
    _sample_primary_event(
      database_path=source_db,
      local_point=tuple(point["local_point"]),
      seed=REPEATABILITY_SEEDS[0],
    )
    for point in PROBE_POINTS
  ]
  stock_summaries = [_event_primary_summary(event) for event in stock_events]
  descriptor = _build_surface_probe_descriptor(
    inner_event=stock_events[0],
    middle_event=stock_events[1],
    outer_event=stock_events[2],
  )
  vulnerability_patch = {
    "synthetic": False,
    "calibrated": True,
    "pk_authority": False,
    "deterministic_fuze_authority": False,
    "evidence_dataset_ref": descriptor["dataset_id"],
    "calibration_status": "calibrated",
    "provenance": (
      "author-side Stage C component probability surface probe only; "
      "non-authoritative and test-local"
    ),
  }

  with tempfile.TemporaryDirectory(prefix="cmo_a2_stage_c_surface_probe_") as tmpdir:
    database_path = _copy_database_with_f16_vulnerability(
      tmpdir,
      vulnerability_patch,
      descriptor=descriptor,
    )
    probe_rows: list[dict[str, Any]] = []
    for point in PROBE_POINTS:
      event = _sample_primary_event(
        database_path=database_path,
        local_point=tuple(point["local_point"]),
        seed=REPEATABILITY_SEEDS[0],
      )
      summary = _event_primary_summary(event)
      selected_row_id = summary["component_failure_probability_evidence_row_id"]
      selected_row = _candidate_row_by_id(descriptor, selected_row_id)
      probe_rows.append(
        {
          "probe_label": str(point["probe_label"]),
          "local_point": list(point["local_point"]),
          "selected_row_id": selected_row_id,
          "selected_row_probability": float(summary["component_failure_probability"]),
          "selected_row_matches_component_specific_scope": bool(
            selected_row.get("component_name") == PRIMARY_COMPONENT_NAME
            and selected_row.get("component_system") == PRIMARY_COMPONENT_SYSTEM
            and selected_row.get("component_redundancy_group_id")
            == PRIMARY_COMPONENT_REDUNDANCY_GROUP
          ),
          "selected_row_covers_primary_loads": _selected_row_covers_primary_loads(
            selected_row, summary
          ),
          **summary,
        }
      )

    repeatability_rows = [
      _event_primary_summary(
        _sample_primary_event(
          database_path=database_path,
          local_point=tuple(PROBE_POINTS[1]["local_point"]),
          seed=seed,
        )
      )
      for seed in REPEATABILITY_SEEDS
    ]

  probabilities = [float(row["selected_row_probability"]) for row in probe_rows]
  selected_row_ids = [str(row["selected_row_id"]) for row in probe_rows]
  repeatability_probabilities = [
    float(row["component_failure_probability"]) for row in repeatability_rows
  ]
  repeatability_fragment_density = [
    float(row["component_primary_mechanism_fragment_areal_density_per_m2"])
    for row in repeatability_rows
  ]
  repeatability_fragment_energy = [
    float(row["component_primary_mechanism_fragment_energy_j"])
    for row in repeatability_rows
  ]
  repeatability_penetration_margin = [
    float(row["component_primary_mechanism_penetration_margin"])
    for row in repeatability_rows
  ]
  repeatability_blast_impulse = [
    float(row["component_primary_mechanism_blast_impulse_kpa_ms"])
    for row in repeatability_rows
  ]

  metrics = {
    "primary_component_identity_stable_pass": all(
      row["component_primary_name"] == PRIMARY_COMPONENT_NAME for row in probe_rows
    ),
    "component_specific_precedence_pass": all(
      row["selected_row_matches_component_specific_scope"] for row in probe_rows
    ),
    "selected_rows_cover_primary_loads_pass": all(
      bool(row["selected_row_covers_primary_loads"]) for row in probe_rows
    ),
    "probability_monotonic_decreasing_with_standoff_pass": probabilities == sorted(
      probabilities, reverse=True
    ),
    "selected_row_ids_are_distinct_pass": len(set(selected_row_ids)) == len(selected_row_ids),
    "anchor_seed_window_cv_pass": _cv_summary(repeatability_probabilities)["cv"] <= 0.05,
  }

  return {
    "package_id": PACKAGE_ID,
    "schema_version": SURFACE_PROBE_SCHEMA_VERSION,
    "status": "candidate_non_authoritative_stage_c_component_probability_surface_probe",
    "artifact_provenance": {
      "source_kind": "candidate_stage_c_component_probability_surface_probe",
      "runtime_aligned_authority_pack_ref": (
    "tools/maintenance/damage_model.py candidate-artifacts "
        "runtime-authority-exercise"
      ),
      "narrow_scope_ref": (
        "docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/"
        "narrow_scope_authority_loop_aim120c_blastfrag_f16c_block50_20260529.zh.md"
      ),
      "descriptor_origin": (
        "runtime-aligned component-probability descriptor candidate expanded into "
        "a three-point author-side surface probe"
      ),
    },
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "candidate_scope_label": "near_miss_0_35m",
      "runtime_miss_distance_bucket": "near_miss",
      "component_name": PRIMARY_COMPONENT_NAME,
      "component_system": PRIMARY_COMPONENT_SYSTEM,
      "component_redundancy_group_id": PRIMARY_COMPONENT_REDUNDANCY_GROUP,
    },
    "descriptor_candidate_summary": {
      "dataset_id": descriptor["dataset_id"],
      "source_kind": descriptor["source_kind"],
      "calibration_status": descriptor["calibration_status"],
      "component_failure_probability_authority": descriptor[
        "component_failure_probability_authority"
      ],
      "row_count": len(descriptor["rows"]),
      "component_specific_row_count": sum(
        1 for row in descriptor["rows"] if row.get("component_name")
      ),
      "global_fallback_row_id": "global-fallback",
    },
    "determinism_summary": {
      "probe_labels_are_fixed": [
        str(point["probe_label"]) for point in PROBE_POINTS
      ],
      "probe_local_points_are_fixed": [
        list(point["local_point"]) for point in PROBE_POINTS
      ],
      "runtime_seed_values_are_fixed": list(REPEATABILITY_SEEDS),
      "descriptor_gate_bands_use_stock_seed": REPEATABILITY_SEEDS[0],
      "json_output_uses_sort_keys": True,
      "runtime_database_copy_is_temporary": True,
    },
    "stock_baseline_probe_summary": _stock_baseline_probe_summary(
      stock_summaries=stock_summaries
    ),
    "component_scope_audit": _component_scope_audit(
      descriptor=descriptor,
      probe_rows=probe_rows,
    ),
    "surface_probe_rows": probe_rows,
    "metrics": metrics,
    "repeatability_summary": {
      "anchor_probe_label": str(PROBE_POINTS[1]["probe_label"]),
      "seed_values": list(REPEATABILITY_SEEDS),
      "selected_row_ids": [
        str(row["component_failure_probability_evidence_row_id"])
        for row in repeatability_rows
      ],
      "component_failure_probability": _cv_summary(repeatability_probabilities),
      "fragment_areal_density_per_m2": _cv_summary(repeatability_fragment_density),
      "fragment_energy_j": _cv_summary(repeatability_fragment_energy),
      "penetration_margin": _cv_summary(repeatability_penetration_margin),
      "blast_impulse_kpa_ms": _cv_summary(repeatability_blast_impulse),
    },
    "current_findings": [
      (
        "the current Stage C candidate now exposes a three-point "
        "component-specific surface probe inside the same narrow near-miss scope"
      ),
      (
        "the selected component probability rows stay component-specific, "
        "cover the projected primary load vector and decrease monotonically "
        "from inner to outer bucket points"
      ),
      (
        "the repeatability summary is still only a candidate runtime-aligned "
        "snapshot; it does not close fragility truth, uncertainty authority "
        "or independent review"
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
      "Generate the Stage C component-probability candidate surface probe "
      "for the current A2 blast-fragmentation package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_stage_c_component_probability_surface_probe()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
