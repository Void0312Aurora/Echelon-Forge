#!/usr/bin/env python3
"""Independent structural admission probe for the warhead spatial field.

The probe bypasses guidance and fuze decisions.  Every row is produced by the
real EffectsModel event path and includes the model-owned projection trace.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import (  # noqa: E402
  configure_sim_log_level,
  ensure_repo_imports,
  repo_root,
  resolve_repo_path,
)

ensure_repo_imports()
from tools.geometry import target_geometry_lethality_matrix_probe as matrix_probe  # noqa: E402


REPO_ROOT = Path(repo_root())
SCHEMA_VERSION = "a2.warhead_spatial_angular_field_admission.v1"
STATUS = "warhead_spatial_angular_field_admission_generated"
GENERATED_ON = "2026-09-14"
DEFAULT_DATABASE_PATH = Path(resolve_repo_path("examples", "config", "database"))
F16_UNIT_PATH = DEFAULT_DATABASE_PATH / "aircraft" / "units" / "f16c_block50.json"
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "warhead_spatial_angular_field_admission_20260914",
    "review_packets",
    "warhead_spatial_angular_field_admission_20260914.json",
  )
)
BASELINE_REPORT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "warhead_spatial_structural_admission_20260913",
    "review_packets",
    "warhead_spatial_structural_admission_baseline_20260913.json",
  )
)

WARHEAD_FAMILIES = ("blast_fragmentation", "continuous_rod")
STANDOFF_DISTANCES_M = (0.5, 2.0, 6.0, 10.0)
ATTITUDES_DEG = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
MISSILE_SPEED_MPS = 900.0


def _target_hitbox_envelope() -> dict[str, list[float]]:
  unit = json.loads(F16_UNIT_PATH.read_text(encoding="utf-8"))
  hitboxes = list(unit["damage_model"]["hitboxes"])
  minimum = [math.inf, math.inf, math.inf]
  maximum = [-math.inf, -math.inf, -math.inf]
  for hitbox in hitboxes:
    center = [float(value) for value in hitbox["offset"]]
    half_size = [0.5 * float(value) for value in hitbox["size"]]
    for axis in range(3):
      minimum[axis] = min(minimum[axis], center[axis] - half_size[axis])
      maximum[axis] = max(maximum[axis], center[axis] + half_size[axis])
  return {"min": minimum, "max": maximum}


TARGET_HITBOX_ENVELOPE = _target_hitbox_envelope()
# Each anchor lies on one face of the maintained target hitbox envelope.  The
# requested standoff is added along that face normal.
DIRECTION_ANCHORS: dict[str, tuple[float, float, float]] = {
  "front": (TARGET_HITBOX_ENVELOPE["max"][0], 0.0, 0.0),
  "back": (TARGET_HITBOX_ENVELOPE["min"][0], 0.0, 0.0),
  "right": (0.0, TARGET_HITBOX_ENVELOPE["max"][1], 0.0),
  "left": (0.0, TARGET_HITBOX_ENVELOPE["min"][1], 0.0),
  "up": (0.0, 0.0, TARGET_HITBOX_ENVELOPE["max"][2]),
  "down": (0.0, 0.0, TARGET_HITBOX_ENVELOPE["min"][2]),
}
EXPECTED_FAMILY_ROW_COUNT = len(DIRECTION_ANCHORS) * len(STANDOFF_DISTANCES_M) * len(ATTITUDES_DEG)


def _relative_path(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT))
  except ValueError:
    return str(path.resolve())


def _configure_runtime_log_level() -> None:
  os.environ.setdefault("CMO_SIM_LOG_LEVEL", "error")
  configure_sim_log_level(str(os.environ["CMO_SIM_LOG_LEVEL"]))


def _local_point(direction: str, standoff_m: float) -> tuple[float, float, float]:
  anchor = DIRECTION_ANCHORS[direction]
  signs = tuple(
    0.0 if abs(value) <= 1.0e-9 else math.copysign(1.0, value)
    for value in anchor
  )
  return tuple(float(anchor[idx]) + signs[idx] * float(standoff_m) for idx in range(3))


def _velocity_toward_origin(point: tuple[float, float, float]) -> tuple[float, float, float]:
  magnitude = math.sqrt(sum(value * value for value in point))
  if magnitude <= 1.0e-12:
    return (0.0, 0.0, 0.0)
  return tuple(-value / magnitude * MISSILE_SPEED_MPS for value in point)


def _case_definitions() -> Iterable[dict[str, Any]]:
  for family in WARHEAD_FAMILIES:
    for direction in DIRECTION_ANCHORS:
      for standoff_m in STANDOFF_DISTANCES_M:
        point = _local_point(direction, standoff_m)
        velocity = _velocity_toward_origin(point)
        for heading_deg in ATTITUDES_DEG:
          yield {
            "case_id": (
              f"{family}:{direction}:standoff_{str(standoff_m).replace('.', 'p')}m:"
              f"heading_{int(heading_deg)}"
            ),
            "warhead_family": family,
            "direction": direction,
            "standoff_m": float(standoff_m),
            "local_point_m": list(point),
            "missile_velocity_body_mps": list(velocity),
            "detonation_attitude_deg": [heading_deg, 0.0, 0.0],
          }


def _close(left: float, right: float, tolerance: float = 1.0e-9) -> bool:
  return math.isclose(float(left), float(right), rel_tol=1.0e-8, abs_tol=tolerance)


def _event_row(
  case: dict[str, Any],
  seed: int,
  *,
  directional_fragmentation: bool = True,
  near_field_floor_enabled: bool = True,
  explicit_continuous_rod: bool = False,
  continuous_rod_band_half_angle_deg: float = 6.0,
  continuous_rod_azimuthal_samples: int = 720,
  continuous_rod_polar_samples: int = 5,
  continuous_rod_azimuthal_phase_deg: float = 0.0,
  projection_min_effect_scale: float | None = None,
  projection_curve_floor_effect_scale: float | None = None,
  advance_simulation: bool = False,
) -> dict[str, Any]:
  sim = matrix_probe.ef_py.SimulationKernel()
  sim.reset(int(seed))
  if not sim.load_database(str(DEFAULT_DATABASE_PATH)):
    raise RuntimeError(f"failed to load database: {DEFAULT_DATABASE_PATH}")
  attacker_id, target_id = matrix_probe._spawn_structured_f16_pair(sim)
  profile = matrix_probe._make_warhead_profile(str(case["warhead_family"]))
  profile.projection_near_field_floor_enabled = bool(near_field_floor_enabled)
  if directional_fragmentation and str(case["warhead_family"]) == "blast_fragmentation":
    profile.fragment_angular_distribution = "polar_azimuthal"
    profile.fragment_polar_concentration = 0.5
    profile.fragment_isotropic_fraction = 0.55
    profile.fragment_azimuthal_modulation = 0.10
    profile.fragment_azimuthal_lobes = 2
    profile.fragment_azimuthal_phase_deg = 0.0
  if explicit_continuous_rod and str(case["warhead_family"]) == "continuous_rod":
    profile.continuous_rod_spatial_model = "expanding_ring_band"
    profile.continuous_rod_band_half_angle_deg = float(
      continuous_rod_band_half_angle_deg
    )
    profile.continuous_rod_azimuthal_samples = int(
      continuous_rod_azimuthal_samples
    )
    profile.continuous_rod_polar_samples = int(continuous_rod_polar_samples)
    profile.continuous_rod_azimuthal_phase_deg = float(
      continuous_rod_azimuthal_phase_deg
    )
  if projection_min_effect_scale is not None:
    profile.projection_min_effect_scale = float(projection_min_effect_scale)
  if projection_curve_floor_effect_scale is not None:
    profile.projection_curve_floor_effect_scale = float(
      projection_curve_floor_effect_scale
    )
  point = [float(value) for value in case["local_point_m"]]
  velocity = [float(value) for value in case["missile_velocity_body_mps"]]
  attitude = [float(value) for value in case["detonation_attitude_deg"]]
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
    attacker_id,
    target_id,
    point[0],
    point[1],
    point[2],
    profile,
    velocity[0],
    velocity[1],
    velocity[2],
    attitude[0],
    attitude[1],
    attitude[2],
  )
  if not ok:
    raise RuntimeError(f"debug profiled local proximity hit failed: {case['case_id']}")
  if advance_simulation:
    # StructuralFailureUpdate consumes ComponentDamageState during ECS progress.
    sim.step()
  events = sim.export_recent_engagement_events()
  if not events.effects_events:
    raise RuntimeError(f"missing effects event: {case['case_id']}")
  effect = events.effects_events[-1]
  float_fields = (
    "miss_distance_m",
    "spatial_effect_scale",
    "spatial_projection_effect_scale",
    "spatial_projection_base_scale",
    "spatial_projection_curve_floor_scale",
    "spatial_projection_near_field_floor",
    "spatial_projection_floor_selected_scale",
    "spatial_projection_preclamp_scale",
    "spatial_projection_min_bound",
    "spatial_projection_max_bound",
    "spatial_projection_axis_weight",
    "spatial_projection_orientation_weight",
    "spatial_projection_armor_scale",
    "spatial_projection_exposure_scale",
    "spatial_projection_sampling_scale",
    "mechanism_fragment_areal_density_per_m2",
    "mechanism_fragment_energy_j",
    "mechanism_blast_overpressure_kpa",
    "mechanism_rod_cut_margin",
    "mechanism_effect_scale",
    "warhead_spatial_hit_estimate",
    "warhead_spatial_hit_fraction",
    "warhead_spatial_energy_scale",
    "warhead_spatial_pattern_scale",
    "warhead_orientation_axis_forward",
    "warhead_orientation_axis_right",
    "warhead_orientation_axis_up",
    "warhead_orientation_pattern_scale",
    "fragment_angular_signed_polar_cosine",
    "fragment_angular_polar_angle_deg",
    "fragment_angular_azimuth_deg",
    "fragment_angular_polar_density",
    "fragment_angular_azimuth_density",
    "fragment_angular_density",
    "continuous_rod_band_half_angle_deg",
    "continuous_rod_angular_coverage_fraction",
    "continuous_rod_nearest_intersection_distance_m",
  )
  def component_load_row_summary(load: object) -> dict[str, Any]:
    row = matrix_probe._row_summary(effect, load)
    row.update(
      {
        "component_dependency_propagation_count": int(
          load.component_dependency_propagation_count
        ),
        "component_dependency_target_system": str(
          load.component_dependency_target_system
        ),
        "component_dependency_edge_type": str(load.component_dependency_edge_type),
        "component_dependency_threshold": float(load.component_dependency_threshold),
        "component_dependency_delay_s": float(load.component_dependency_delay_s),
        "component_dependency_direction": str(load.component_dependency_direction),
        "component_dependency_provenance": str(load.component_dependency_provenance),
        "component_dependency_source_availability": float(
          load.component_dependency_source_availability
        ),
        "component_dependency_effective_scale": float(
          load.component_dependency_effective_scale
        ),
        "component_dependency_propagated": bool(load.component_dependency_propagated),
      }
    )
    return row

  def component_response_row_summary(response: object) -> dict[str, Any]:
    return {
      "owner_stage": str(response.owner_stage),
      "source_current_owner_stage": str(response.source_current_owner_stage),
      "source_row_index": int(response.source_row_index),
      "component_name": str(response.component_name),
      "component_system": str(response.component_system),
      "component_redundancy_group_id": str(response.component_redundancy_group_id),
      "threshold_scale": float(response.threshold_scale),
      "failure_probability": float(response.failure_probability),
      "failure_sample": float(response.failure_sample),
      "failure_probability_source": str(response.failure_probability_source),
      "failure_probability_calibrated": bool(response.failure_probability_calibrated),
      "failure_probability_authority": bool(response.failure_probability_authority),
      "failure_probability_component_specific": bool(
        response.failure_probability_component_specific
      ),
      "failure_probability_weapon_family": str(response.failure_probability_weapon_family),
      "failure_probability_aspect_bucket": str(response.failure_probability_aspect_bucket),
      "failure_probability_closure_bucket": str(response.failure_probability_closure_bucket),
      "failure_probability_miss_distance_bucket": str(
        response.failure_probability_miss_distance_bucket
      ),
      "failure_mode": str(response.failure_mode),
      "failure_severity": float(response.failure_severity),
      "failure_mode_names": [str(value) for value in response.failure_mode_names],
      "failure_mode_severities": [float(value) for value in response.failure_mode_severities],
      "failure_mode_source": str(response.failure_mode_source),
      "failure_mode_authority": bool(response.failure_mode_authority),
      "integrity_before": float(response.integrity_before),
      "integrity_after": float(response.integrity_after),
      "redundancy_group_availability_before": float(
        response.redundancy_group_availability_before
      ),
      "redundancy_group_availability_after": float(
        response.redundancy_group_availability_after
      ),
    }

  damages = [
    matrix_probe._component_damage_summary(damage)
    for damage in events.component_damage_events
  ]
  reports = [
    matrix_probe._damage_report_summary(report) for report in events.damage_reports
  ]
  consequences = [
    matrix_probe._platform_consequence_summary(event)
    for event in getattr(events, "platform_consequence_events", [])
  ]

  event = {
    "effect_family": str(effect.effect_family),
    "spatial_projection_trace_valid": bool(effect.spatial_projection_trace_valid),
    "spatial_projection_near_field_floor_applied": bool(
      effect.spatial_projection_near_field_floor_applied
    ),
    "spatial_projection_effect_scale_clamped": bool(
      effect.spatial_projection_effect_scale_clamped
    ),
    "projected_hitbox_count": int(effect.projected_hitbox_count),
    "component_primary_name": str(effect.component_primary_name),
    "component_primary_system": str(effect.component_primary_system),
    "component_primary_redundancy_group": float(effect.component_primary_redundancy_group),
    "component_primary_critical": bool(effect.component_primary_critical),
    "component_primary_redundancy_group_id": str(
      effect.component_primary_redundancy_group_id
    ),
    "component_primary_integrity": float(effect.component_primary_integrity),
    "component_failure_probability": float(effect.component_failure_probability),
    "component_failure_probability_source": str(
      effect.component_failure_probability_source
    ),
    "component_failure_count": int(effect.component_failure_count),
    "component_primary_mechanism_rod_cut_margin": float(
      effect.component_primary_mechanism_rod_cut_margin
    ),
    "component_redundancy_group_availability": float(
      effect.component_redundancy_group_availability
    ),
    "component_redundancy_group_member_count": int(
      effect.component_redundancy_group_member_count
    ),
    "component_redundancy_group_failed_count": int(
      effect.component_redundancy_group_failed_count
    ),
    "warhead_spatial_sample_count": int(effect.warhead_spatial_sample_count),
    "fragment_angular_distribution_active": bool(
      effect.fragment_angular_distribution_active
    ),
    "fragment_angular_distribution": str(effect.fragment_angular_distribution),
    "continuous_rod_ring_band_active": bool(effect.continuous_rod_ring_band_active),
    "continuous_rod_ring_band_intersection": bool(
      effect.continuous_rod_ring_band_intersection
    ),
    "continuous_rod_spatial_model": str(effect.continuous_rod_spatial_model),
    "continuous_rod_azimuthal_sample_count": int(
      effect.continuous_rod_azimuthal_sample_count
    ),
    "continuous_rod_polar_sample_count": int(effect.continuous_rod_polar_sample_count),
    "continuous_rod_intersecting_azimuthal_sample_count": int(
      effect.continuous_rod_intersecting_azimuthal_sample_count
    ),
    "component_damage_event_count": len(damages),
    "component_failure_event_count": matrix_probe._component_failure_event_count(damages),
    "damage_report_count": len(reports),
    "platform_consequence_event_count": len(consequences),
    "component_damage_events": damages,
    "damage_reports": reports,
    "platform_consequence_events": consequences,
    "vulnerability_profile_present": bool(effect.vulnerability_profile_present),
    "vulnerability_profile_synthetic": bool(effect.vulnerability_profile_synthetic),
    "vulnerability_calibrated_evidence": bool(effect.vulnerability_calibrated_evidence),
    "vulnerability_pk_authority": bool(effect.vulnerability_pk_authority),
    "vulnerability_deterministic_fuze_authority": bool(
      effect.vulnerability_deterministic_fuze_authority
    ),
    "vulnerability_evidence_dataset_valid": bool(
      effect.vulnerability_evidence_dataset_valid
    ),
    "vulnerability_evidence_dataset_ref": str(effect.vulnerability_evidence_dataset_ref),
    "vulnerability_calibration_status": str(effect.vulnerability_calibration_status),
    "vulnerability_provenance": str(effect.vulnerability_provenance),
    "vulnerability_evidence_schema_version": str(
      effect.vulnerability_evidence_schema_version
    ),
    "vulnerability_evidence_source_kind": str(effect.vulnerability_evidence_source_kind),
    "vulnerability_evidence_source_ref": str(effect.vulnerability_evidence_source_ref),
    "vulnerability_evidence_validation_status": str(
      effect.vulnerability_evidence_validation_status
    ),
    "vulnerability_aspect_bucket": str(effect.vulnerability_aspect_bucket),
    "vulnerability_family_scale": float(effect.vulnerability_family_scale),
    "vulnerability_aspect_scale": float(effect.vulnerability_aspect_scale),
    "vulnerability_closure_mps": float(effect.vulnerability_closure_mps),
    "vulnerability_closure_scale": float(effect.vulnerability_closure_scale),
    "vulnerability_miss_distance_scale": float(effect.vulnerability_miss_distance_scale),
    "vulnerability_effect_scale": float(effect.vulnerability_effect_scale),
    "vulnerability_effect_scale_source": str(effect.vulnerability_effect_scale_source),
    "vulnerability_effect_scale_evidence_row_id": str(
      effect.vulnerability_effect_scale_evidence_row_id
    ),
    "vulnerability_effect_scale_evidence_source_ref": str(
      effect.vulnerability_effect_scale_evidence_source_ref
    ),
    "vulnerability_effect_scale_evidence_provenance": str(
      effect.vulnerability_effect_scale_evidence_provenance
    ),
    "vulnerability_scale_trace": str(effect.vulnerability_scale_trace),
    "component_mechanism_load_rows": [
      component_load_row_summary(load)
      for load in effect.component_mechanism_load_rows
      if str(load.component_name) or str(load.component_system)
    ],
    "component_response_rows": [
      component_response_row_summary(response)
      for response in effect.component_response_rows
      if str(response.component_name) or str(response.component_system)
    ],
  }
  event.update({name: float(getattr(effect, name)) for name in float_fields})
  return {**case, "event": event}


def _trace_closure(row: dict[str, Any]) -> dict[str, Any]:
  event = row["event"]
  if not bool(event["spatial_projection_trace_valid"]):
    return {
      "trace_valid": False,
      "post_closure": None,
      "preclamp_decomposition": None,
      "flag_closure": None,
      "candidate_aggregate_match": None,
    }
  base = float(event["spatial_projection_base_scale"])
  floor = float(event["spatial_projection_near_field_floor"])
  selected = float(event["spatial_projection_floor_selected_scale"])
  preclamp = float(event["spatial_projection_preclamp_scale"])
  minimum = float(event["spatial_projection_min_bound"])
  maximum = float(event["spatial_projection_max_bound"])
  expected_selected = max(base, floor)
  expected_preclamp = (
    expected_selected
    * float(event["spatial_projection_axis_weight"])
    * float(event["spatial_projection_orientation_weight"])
    * float(event["spatial_projection_armor_scale"])
    * float(event["spatial_projection_exposure_scale"])
    * float(event["spatial_projection_sampling_scale"])
  )
  expected_post = min(max(preclamp, minimum), maximum)
  expected_floor_applied = floor > base
  expected_clamped = not _close(expected_post, preclamp)
  return {
    "trace_valid": True,
    "post_closure": _close(float(event["spatial_projection_effect_scale"]), expected_post),
    "preclamp_decomposition": _close(selected, expected_selected)
    and _close(preclamp, expected_preclamp),
    "flag_closure": bool(event["spatial_projection_near_field_floor_applied"])
    == expected_floor_applied
    and bool(event["spatial_projection_effect_scale_clamped"]) == expected_clamped,
    "candidate_aggregate_match": _close(
      float(event["spatial_effect_scale"]),
      float(event["spatial_projection_effect_scale"]),
    ),
  }


def _rod_baseline_regression(rows: list[dict[str, Any]]) -> dict[str, Any]:
  """Compare continuous-rod trace/mechanism values with the retained baseline."""
  rod_rows = [row for row in rows if str(row["warhead_family"]) == "continuous_rod"]
  if not rod_rows:
    return {
      "status": "not_evaluated",
      "baseline_path": _relative_path(BASELINE_REPORT_PATH),
      "compared_row_count": 0,
      "missing_baseline_row_count": 0,
      "mismatch_count": 0,
      "mismatches": [],
    }
  if not BASELINE_REPORT_PATH.exists():
    return {
      "status": "not_evaluated",
      "baseline_path": _relative_path(BASELINE_REPORT_PATH),
      "compared_row_count": 0,
      "missing_baseline_row_count": len(rod_rows),
      "mismatch_count": 0,
      "mismatches": [{"reason": "baseline_report_missing"}],
    }
  baseline_payload = json.loads(BASELINE_REPORT_PATH.read_text(encoding="utf-8"))
  baseline_rows = {
    str(row["case_id"]): row
    for row in baseline_payload.get("rows", [])
    if str(row.get("warhead_family")) == "continuous_rod"
  }
  fields = (
    "spatial_effect_scale",
    "spatial_projection_effect_scale",
    "spatial_projection_base_scale",
    "spatial_projection_near_field_floor",
    "spatial_projection_floor_selected_scale",
    "spatial_projection_preclamp_scale",
    "spatial_projection_axis_weight",
    "spatial_projection_orientation_weight",
    "spatial_projection_armor_scale",
    "spatial_projection_exposure_scale",
    "spatial_projection_sampling_scale",
    "warhead_spatial_hit_estimate",
    "warhead_spatial_hit_fraction",
    "warhead_spatial_energy_scale",
    "warhead_spatial_pattern_scale",
    "mechanism_effect_scale",
    "mechanism_rod_cut_margin",
  )
  mismatches: list[dict[str, Any]] = []
  trace_selection_mismatch_count = 0
  trace_selection_fields = {
    "spatial_projection_base_scale",
    "spatial_projection_near_field_floor",
    "spatial_projection_floor_selected_scale",
    "spatial_projection_preclamp_scale",
    "spatial_projection_axis_weight",
    "spatial_projection_orientation_weight",
    "spatial_projection_armor_scale",
    "spatial_projection_exposure_scale",
    "spatial_projection_sampling_scale",
  }
  missing_count = 0
  compared_count = 0
  mismatch_count = 0
  for row in rod_rows:
    case_id = str(row["case_id"])
    baseline = baseline_rows.get(case_id)
    if baseline is None:
      missing_count += 1
      if len(mismatches) < 20:
        mismatches.append({"case_id": case_id, "reason": "baseline_row_missing"})
      continue
    compared_count += 1
    current_event = row["event"]
    baseline_event = baseline["event"]
    for field in fields:
      if not _close(float(current_event[field]), float(baseline_event[field])):
        if (
          field in trace_selection_fields
          and bool(current_event.get("spatial_projection_effect_scale_clamped", False))
          and bool(baseline_event.get("spatial_projection_effect_scale_clamped", False))
          and _close(
            float(current_event["spatial_projection_effect_scale"]),
            float(baseline_event["spatial_projection_effect_scale"]),
          )
        ):
          trace_selection_mismatch_count += 1
          continue
        mismatch_count += 1
        if len(mismatches) < 20:
          mismatches.append(
            {
              "case_id": case_id,
              "field": field,
              "current": float(current_event[field]),
              "baseline": float(baseline_event[field]),
            }
          )
  mismatch_count += missing_count
  return {
    "status": "passed" if mismatch_count == 0 and compared_count > 0 else "failed",
    "baseline_path": _relative_path(BASELINE_REPORT_PATH),
    "compared_row_count": compared_count,
    "missing_baseline_row_count": missing_count,
    "mismatch_count": mismatch_count,
    "trace_selection_mismatch_count": trace_selection_mismatch_count,
    "mismatches": mismatches,
  }


def _floor_ablation_report(*, seed: int) -> dict[str, Any]:
  """Run a small paired matrix to prove the near-field floor is switchable."""
  cases = [
    case
    for case in _case_definitions()
    if _close(float(case["standoff_m"]), 0.5)
    and float(case["detonation_attitude_deg"][0]) in (0.0, 180.0)
  ]
  pairs: list[dict[str, Any]] = []
  for index, case in enumerate(cases):
    enabled = _event_row(case, seed + index * 2, near_field_floor_enabled=True)["event"]
    disabled = _event_row(case, seed + index * 2 + 1, near_field_floor_enabled=False)["event"]
    enabled_effect = float(enabled["spatial_projection_effect_scale"])
    disabled_effect = float(disabled["spatial_projection_effect_scale"])
    pairs.append(
      {
        "case_id": case["case_id"],
        "family": case["warhead_family"],
        "direction": case["direction"],
        "heading_deg": case["detonation_attitude_deg"][0],
        "floor_enabled_applied": bool(enabled["spatial_projection_near_field_floor_applied"]),
        "floor_disabled_applied": bool(disabled["spatial_projection_near_field_floor_applied"]),
        "enabled_effect_scale": enabled_effect,
        "disabled_effect_scale": disabled_effect,
        "absolute_effect_delta": abs(enabled_effect - disabled_effect),
      }
    )
  return {
    "status": "passed"
    if pairs
    and sum(1 for pair in pairs if pair["floor_disabled_applied"]) == 0
    and sum(1 for pair in pairs if pair["floor_enabled_applied"]) > 0
    and any(pair["absolute_effect_delta"] > 1.0e-9 for pair in pairs)
    else "failed",
    "pair_count": len(pairs),
    "floor_enabled_applied_count": sum(1 for pair in pairs if pair["floor_enabled_applied"]),
    "floor_disabled_applied_count": sum(1 for pair in pairs if pair["floor_disabled_applied"]),
    "effect_delta_count": sum(
      1 for pair in pairs if pair["absolute_effect_delta"] > 1.0e-9
    ),
    "max_absolute_effect_delta": max(
      (float(pair["absolute_effect_delta"]) for pair in pairs), default=0.0
    ),
    "pairs": pairs,
  }


def evaluate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
  closure_rows = [_trace_closure(row) for row in rows]
  valid_closures = [row for row in closure_rows if row["trace_valid"]]
  groups: dict[tuple[str, str, tuple[float, float, float]], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    groups[
      (
        str(row["warhead_family"]),
        str(row["direction"]),
        tuple(float(value) for value in row["detonation_attitude_deg"]),
      )
    ].append(row)
  monotonic_violations: list[dict[str, Any]] = []
  for key, group in groups.items():
    ordered = sorted(group, key=lambda item: float(item["standoff_m"]))
    for near, far in zip(ordered, ordered[1:]):
      near_value = float(near["event"]["spatial_projection_effect_scale"])
      far_value = float(far["event"]["spatial_projection_effect_scale"])
      if bool(near["event"]["spatial_projection_trace_valid"]) and bool(
        far["event"]["spatial_projection_trace_valid"]
      ) and far_value > near_value + 1.0e-9:
        monotonic_violations.append(
          {
            "group": [key[0], key[1], list(key[2])],
            "near_standoff_m": near["standoff_m"],
            "far_standoff_m": far["standoff_m"],
            "near_effect_scale": near_value,
            "far_effect_scale": far_value,
          }
        )

  family_difference_count = 0
  for direction in DIRECTION_ANCHORS:
    for standoff_m in STANDOFF_DISTANCES_M:
      for heading_deg in ATTITUDES_DEG:
        family_rows = [
          row
          for row in rows
          if str(row["direction"]) == direction
          and _close(float(row["standoff_m"]), standoff_m)
          and _close(float(row["detonation_attitude_deg"][0]), heading_deg)
        ]
        if len(family_rows) == 2 and not _close(
          float(family_rows[0]["event"]["spatial_projection_effect_scale"]),
          float(family_rows[1]["event"]["spatial_projection_effect_scale"]),
        ):
          family_difference_count += 1

  orientation_sign_collapses = []
  for family in WARHEAD_FAMILIES:
    for direction in DIRECTION_ANCHORS:
      for standoff_m in STANDOFF_DISTANCES_M:
        pair = [
          row
          for row in rows
          if str(row["warhead_family"]) == family
          and str(row["direction"]) == direction
          and _close(float(row["standoff_m"]), standoff_m)
          and float(row["detonation_attitude_deg"][0]) in (0.0, 180.0)
        ]
        if len(pair) == 2 and all(
          bool(row["event"]["spatial_projection_trace_valid"]) for row in pair
        ) and _close(
          float(pair[0]["event"]["spatial_projection_orientation_weight"]),
          float(pair[1]["event"]["spatial_projection_orientation_weight"]),
        ):
          orientation_sign_collapses.append(
            {"family": family, "direction": direction, "standoff_m": standoff_m}
          )

  orientation_sign_collapse_count_by_family = {
    family: sum(1 for item in orientation_sign_collapses if item["family"] == family)
    for family in WARHEAD_FAMILIES
  }
  axial_orientation_sign_collapses = [
    item
    for item in orientation_sign_collapses
    if item["direction"] in {"front", "back"}
  ]
  axial_orientation_sign_collapse_count_by_family = {
    family: sum(1 for item in axial_orientation_sign_collapses if item["family"] == family)
    for family in WARHEAD_FAMILIES
  }

  mirror_violations: list[dict[str, Any]] = []
  rotation_steps: list[dict[str, Any]] = []
  for family in WARHEAD_FAMILIES:
    for standoff_m in STANDOFF_DISTANCES_M:
      for heading_deg in ATTITUDES_DEG:
        reflected_heading = (-float(heading_deg)) % 360.0
        mirror_rows = [
          row
          for row in rows
          if str(row["warhead_family"]) == family
          and str(row["direction"]) in {"right", "left"}
          and _close(float(row["standoff_m"]), standoff_m)
          and (
            (
              str(row["direction"]) == "right"
              and _close(float(row["detonation_attitude_deg"][0]), heading_deg)
            )
            or (
              str(row["direction"]) == "left"
              and _close(
                float(row["detonation_attitude_deg"][0]), reflected_heading
              )
            )
          )
        ]
        if len(mirror_rows) != 2:
          continue
        right_row = next(row for row in mirror_rows if row["direction"] == "right")
        left_row = next(row for row in mirror_rows if row["direction"] == "left")
        right_value = float(right_row["event"]["spatial_projection_effect_scale"])
        left_value = float(left_row["event"]["spatial_projection_effect_scale"])
        if abs(right_value - left_value) > 1.0e-6:
          mirror_violations.append(
            {
              "family": family,
              "standoff_m": standoff_m,
              "right_heading_deg": heading_deg,
              "left_heading_deg": reflected_heading,
              "right_effect_scale": right_value,
              "left_effect_scale": left_value,
            }
          )
    for direction in DIRECTION_ANCHORS:
      for standoff_m in STANDOFF_DISTANCES_M:
        ordered = [
          next(
            (
              row
              for row in rows
              if str(row["warhead_family"]) == family
              and str(row["direction"]) == direction
              and _close(float(row["standoff_m"]), standoff_m)
              and _close(float(row["detonation_attitude_deg"][0]), heading_deg)
            ),
            None,
          )
          for heading_deg in ATTITUDES_DEG
        ]
        if any(row is None for row in ordered):
          continue
        for index, current in enumerate(ordered):
          following = ordered[(index + 1) % len(ordered)]
          assert current is not None and following is not None
          current_value = float(current["event"]["spatial_projection_effect_scale"])
          following_value = float(following["event"]["spatial_projection_effect_scale"])
          rotation_steps.append(
            {
              "family": family,
              "direction": direction,
              "standoff_m": standoff_m,
              "heading_deg": float(current["detonation_attitude_deg"][0]),
              "next_heading_deg": float(following["detonation_attitude_deg"][0]),
              "absolute_effect_scale_delta": abs(following_value - current_value),
            }
          )

  metrics = {
    "row_count": len(rows),
    "trace_valid_count": sum(1 for item in closure_rows if item["trace_valid"]),
    "trace_invalid_count": sum(1 for item in closure_rows if not item["trace_valid"]),
    "near_field_floor_applied_count": sum(
      1
      for row in rows
      if bool(row["event"]["spatial_projection_near_field_floor_applied"])
    ),
    "effect_scale_clamped_count": sum(
      1 for row in rows if bool(row["event"]["spatial_projection_effect_scale_clamped"])
    ),
    "post_closure_failure_count": sum(
      1 for item in valid_closures if item["post_closure"] is not True
    ),
    "preclamp_decomposition_failure_count": sum(
      1 for item in valid_closures if item["preclamp_decomposition"] is not True
    ),
    "candidate_aggregate_mismatch_count": sum(
      1 for item in valid_closures if item["candidate_aggregate_match"] is not True
    ),
    "flag_closure_failure_count": sum(
      1 for item in valid_closures if item["flag_closure"] is not True
    ),
    "distance_monotonic_violation_count": len(monotonic_violations),
    "family_difference_count": family_difference_count,
    "orientation_sign_collapse_count": len(orientation_sign_collapses),
    "orientation_sign_collapse_count_by_family": orientation_sign_collapse_count_by_family,
    "axial_orientation_sign_collapse_count": len(axial_orientation_sign_collapses),
    "axial_orientation_sign_collapse_count_by_family": axial_orientation_sign_collapse_count_by_family,
    "fragmentation_angular_distribution_active_count": sum(
      1
      for row in rows
      if str(row["warhead_family"]) == "blast_fragmentation"
      and bool(row["event"].get("fragment_angular_distribution_active", False))
    ),
    "mirror_symmetry_violation_count": len(mirror_violations),
    "rotation_step_count": len(rotation_steps),
    "rotation_max_adjacent_effect_scale_delta": max(
      (float(item["absolute_effect_scale_delta"]) for item in rotation_steps),
      default=0.0,
    ),
  }
  hard_pass = all(
    metrics[name] == 0
    for name in (
      "post_closure_failure_count",
      "preclamp_decomposition_failure_count",
      "candidate_aggregate_mismatch_count",
      "flag_closure_failure_count",
    )
  ) and metrics["trace_valid_count"] > 0
  return {
    "metrics": metrics,
    "diagnostic_trace_gate_pass": hard_pass,
    "structural_residuals": {
      "distance_monotonic_violations": monotonic_violations,
      "orientation_sign_collapses": orientation_sign_collapses,
      "axial_orientation_sign_collapses": axial_orientation_sign_collapses,
      "mirror_symmetry_violations": mirror_violations,
      "rotation_steps": rotation_steps,
      "family_difference_count": family_difference_count,
    },
  }


def generate_report(*, seed: int = 20260913, limit: int | None = None) -> dict[str, Any]:
  _configure_runtime_log_level()
  cases = list(_case_definitions())
  if limit is not None:
    cases = cases[: max(0, int(limit))]
  rows = [_event_row(case, seed + index) for index, case in enumerate(cases)]
  evaluation = evaluate_rows(rows)
  trace_gate_pass = bool(evaluation["diagnostic_trace_gate_pass"])
  family_evaluations = {
    family: evaluate_rows(
      [row for row in rows if str(row["warhead_family"]) == family]
    )
    for family in WARHEAD_FAMILIES
  }
  rod_regression = _rod_baseline_regression(rows)
  floor_ablation = (
    _floor_ablation_report(seed=seed + len(rows) + 1000)
    if limit is None
    else {"status": "not_evaluated", "reason": "limited_probe", "pair_count": 0, "pairs": []}
  )
  blast_rows = [row for row in rows if str(row["warhead_family"]) == "blast_fragmentation"]
  blast_metrics = family_evaluations["blast_fragmentation"]["metrics"]
  fragmentation_admission_pass = bool(
    len(blast_rows) == EXPECTED_FAMILY_ROW_COUNT
    and family_evaluations["blast_fragmentation"]["diagnostic_trace_gate_pass"]
    and evaluation["metrics"]["fragmentation_angular_distribution_active_count"]
    == len(blast_rows)
    and blast_metrics["distance_monotonic_violation_count"] == 0
    and blast_metrics["axial_orientation_sign_collapse_count"] == 0
    and blast_metrics["mirror_symmetry_violation_count"] == 0
  )
  blockers = [
    "continuous rod remains a side-sweep surrogate without explicit expanding ring-band intersection",
    "component-load admission requires a separate response-topology gate after the field model changes",
  ]
  if len(blast_rows) != EXPECTED_FAMILY_ROW_COUNT:
    blockers.insert(0, "fragmentation admission requires the complete six-direction matrix")
  if not fragmentation_admission_pass:
    blockers.insert(0, "fragmentation angular-field admission residuals are not closed")
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "authority_boundary": {
      "guidance_bypassed": True,
      "fuze_decision_authority": False,
      "synthetic_warhead_profile": True,
      "default_database_modified": False,
      "real_weapon_pk_authority": False,
      "integrated_kill_chain_admission": False,
    },
    "matrix": {
      "target_unit": "F-16C_Block50",
      "target_hitbox_envelope_m": TARGET_HITBOX_ENVELOPE,
      "warhead_families": list(WARHEAD_FAMILIES),
      "directions": list(DIRECTION_ANCHORS),
      "standoff_distances_m": list(STANDOFF_DISTANCES_M),
      "detonation_headings_deg": list(ATTITUDES_DEG),
      "case_count": len(cases),
    },
    "admission_decision": {
      "diagnostic_trace_gate": "passed" if trace_gate_pass else "failed",
      "fragmentation_angular_field_admission":
        "passed" if fragmentation_admission_pass else "held",
      "continuous_rod_baseline_regression": rod_regression["status"],
      "warhead_spatial_field_admission": "held",
      "component_load_admission": "not_evaluated",
      "integrated_kill_chain_admission": "not_evaluated",
      "blockers": blockers,
    },
    **evaluation,
    "family_evaluations": family_evaluations,
    "continuous_rod_baseline_regression": rod_regression,
    "near_field_floor_ablation": floor_ablation,
    "rows": rows,
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
  parser.add_argument("--seed", type=int, default=20260913)
  parser.add_argument("--limit", type=int, default=None, help="run only the first N rows")
  args = parser.parse_args()
  report = generate_report(seed=args.seed, limit=args.limit)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
  print(json.dumps({"output": _relative_path(args.output), **report["metrics"]}, indent=2))
  return 0 if report["diagnostic_trace_gate_pass"] else 2


if __name__ == "__main__":
  raise SystemExit(main())
