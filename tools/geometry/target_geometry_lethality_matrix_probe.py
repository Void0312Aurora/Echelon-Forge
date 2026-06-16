#!/usr/bin/env python3
"""Probe target-geometry lethality deltas across aspect, range, and warhead family."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


SCHEMA_VERSION = "a2.target_geometry_lethality_matrix_probe.v1"
STATUS = "target_geometry_lethality_matrix_probe_generated_20260614"
GENERATED_ON = "2026-06-14"
DEFAULT_DATABASE_PATH = Path(resolve_repo_path("examples", "config", "database"))
PROXY_DATABASE_PATH = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
    "target_geometry_training_proxy_database_20260613",
  )
)
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
    "target_geometry_lethality_matrix_probe_20260614.json",
  )
)

WARHEAD_FAMILIES = ("blast_fragmentation", "continuous_rod")
MISSILE_SPEED_MPS = 900.0
SPLIT_RECEIVER_NAMES = (
  "engine_core_afterburner_segment",
  "engine_core_hot_section_segment",
  "engine_core_forward_compressor_segment",
  "wing_spar_center_left_inner_wing_segment",
  "wing_spar_center_left_root_segment",
  "wing_spar_center_carrythrough_segment",
  "wing_spar_center_right_root_segment",
  "wing_spar_center_right_inner_wing_segment",
)
RETIRED_PARENT_COMPONENTS = ("engine_core", "wing_spar_center")


def missile_velocity_toward_origin(
  local_point_m: tuple[float, float, float] | list[float],
  *,
  speed_mps: float = MISSILE_SPEED_MPS,
) -> tuple[float, float, float]:
  distance_m = math.sqrt(sum(float(value) ** 2 for value in local_point_m))
  if distance_m <= 1.0e-9:
    return (0.0, 0.0, 0.0)
  return tuple(
    -float(value) / distance_m * float(speed_mps) for value in local_point_m
  )


def _case_with_standard_velocity(case: dict[str, Any]) -> dict[str, Any]:
  local_point_m = tuple(float(value) for value in case["local_point_m"])
  return {
    **case,
    "missile_velocity_body_mps": missile_velocity_toward_origin(local_point_m),
  }


CASE_DEFINITIONS: tuple[dict[str, Any], ...] = tuple(
  _case_with_standard_velocity(case)
  for case in (
  {
    "case_id": "right_aileron_direct_center",
    "aspect": "right_beam",
    "range_bucket": "direct_component_center",
    "local_point_m": (-0.8, 4.1, -0.985),
  },
  {
    "case_id": "right_wing_fuel_center",
    "aspect": "right_beam",
    "range_bucket": "direct_component_center",
    "local_point_m": (-0.8, 2.8, -0.985),
  },
  {
    "case_id": "right_beam_near_7m",
    "aspect": "right_beam",
    "range_bucket": "near_miss_7m",
    "local_point_m": (-0.753, 7.1, -0.985),
  },
  {
    "case_id": "right_beam_far_14m",
    "aspect": "right_beam",
    "range_bucket": "near_miss_14m",
    "local_point_m": (-0.753, 14.0, -0.985),
  },
  {
    "case_id": "left_aileron_direct_center",
    "aspect": "left_beam",
    "range_bucket": "direct_component_center",
    "local_point_m": (-0.8, -4.1, -0.985),
  },
  {
    "case_id": "left_beam_near_7m",
    "aspect": "left_beam",
    "range_bucket": "near_miss_7m",
    "local_point_m": (-0.753, -7.1, -0.985),
  },
  {
    "case_id": "center_spar_carrythrough",
    "aspect": "centerline",
    "range_bucket": "direct_structural_center",
    "local_point_m": (-1.2, 0.0, -0.985043),
  },
  {
    "case_id": "engine_afterburner_segment",
    "aspect": "tail_aft_engine",
    "range_bucket": "direct_receiver_edge",
    "local_point_m": (-5.775512, -0.5, -0.404381),
  },
  {
    "case_id": "engine_hot_section_center",
    "aspect": "tail_engine",
    "range_bucket": "direct_receiver_center",
    "local_point_m": (-3.693053, 0.0, -0.904381),
  },
  {
    "case_id": "engine_forward_compressor_center",
    "aspect": "aft_fuselage_engine",
    "range_bucket": "direct_receiver_center",
    "local_point_m": (-2.352966, 0.0, -0.904381),
  },
  {
    "case_id": "nose_cockpit_center",
    "aspect": "nose",
    "range_bucket": "direct_component_center",
    "local_point_m": (6.024, 0.0, 0.0),
  },
  {
    "case_id": "tail_right_near",
    "aspect": "tail_right",
    "range_bucket": "near_tail",
    "local_point_m": (-7.1, 0.753, -0.5),
  },
  )
)

COMPARE_FIELDS = (
  "component_primary_name",
  "component_primary_system",
  "component_hit_count",
  "component_failure_count",
  "projected_hitbox_count",
  "direct_hitbox_intersection",
  "component_primary_integrity",
  "component_failure_probability",
  "component_primary_row_failure_probability",
  "component_primary_row_distance_m",
  "component_primary_row_effect_scale",
  "component_max_failure_probability_component_name",
  "component_primary_mechanism_fragment_energy_j",
  "component_primary_mechanism_fragment_areal_density_per_m2",
  "component_primary_mechanism_blast_overpressure_kpa",
  "component_primary_mechanism_blast_impulse_kpa_ms",
  "component_primary_mechanism_penetration_margin",
  "component_primary_mechanism_rod_cut_margin",
  "component_mechanism_row_names",
  "component_load_event_names",
  "component_damage_event_names",
)


def _relative_path(path: Path) -> str:
  return str(path.resolve().relative_to(REPO_ROOT))


def _configure_runtime_log_level() -> None:
  os.environ.setdefault("CMO_SIM_LOG_LEVEL", "error")
  try:
    ef_py.set_log_level(str(os.environ["CMO_SIM_LOG_LEVEL"]))
  except Exception:
    pass


def _make_warhead_profile(family: str) -> object:
  profile = ef_py.WarheadProfile()
  profile.family = family
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = f"target_geometry_lethality_matrix_probe_{family}"
  return profile


def _spawn_structured_f16_pair(sim: object) -> tuple[int, int]:
  attacker_id = int(
    sim.spawn_unit(
      ef_py.Side.Blue,
      "F-16C_Block50",
      0.0,
      0.0,
      5000.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
    )
  )
  target_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      0.0,
      500.0,
      5000.0,
      180.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _as_float(value: object) -> float:
  return float(value)


def _float_attr(obj: object, name: str, default: float = 0.0) -> float:
  return _as_float(getattr(obj, name, default))


def _str_attr(obj: object, name: str) -> str:
  return str(getattr(obj, name, ""))


def _bool_attr(obj: object, name: str) -> bool:
  return bool(getattr(obj, name, False))


def _int_attr(obj: object, name: str) -> int:
  return int(getattr(obj, name, 0))


def _row_summary(row: object) -> dict[str, Any]:
  return {
    "component_name": _str_attr(row, "component_name"),
    "component_system": _str_attr(row, "component_system"),
    "component_redundancy_group_id": _str_attr(
      row, "component_redundancy_group_id"
    ),
    "direct_hit": _bool_attr(row, "direct_hit"),
    "distance_m": _float_attr(row, "distance_m"),
    "effect_scale": _float_attr(row, "effect_scale"),
    "component_failure_probability": _float_attr(
      row, "component_failure_probability"
    ),
    "mechanism_fragment_energy_j": _float_attr(
      row, "mechanism_fragment_energy_j"
    ),
    "mechanism_fragment_areal_density_per_m2": _float_attr(
      row, "mechanism_fragment_areal_density_per_m2"
    ),
    "mechanism_blast_overpressure_kpa": _float_attr(
      row, "mechanism_blast_overpressure_kpa"
    ),
    "mechanism_blast_impulse_kpa_ms": _float_attr(
      row, "mechanism_blast_impulse_kpa_ms"
    ),
    "mechanism_penetration_margin": _float_attr(
      row, "mechanism_penetration_margin"
    ),
    "mechanism_rod_cut_margin": _float_attr(row, "mechanism_rod_cut_margin"),
  }


def _component_load_summary(load: object) -> dict[str, Any]:
  return {
    "component_name": _str_attr(load, "component_name"),
    "component_system": _str_attr(load, "component_system"),
    "component_redundancy_group_id": _str_attr(
      load, "component_redundancy_group_id"
    ),
    "direct_hit": _bool_attr(load, "direct_hit"),
    "distance_m": _float_attr(load, "distance_m"),
    "effect_scale": _float_attr(load, "effect_scale"),
    "rod_cut_margin": _float_attr(load, "rod_cut_margin"),
    "load_source": _str_attr(load, "load_source"),
  }


def _component_damage_summary(damage: object) -> dict[str, Any]:
  return {
    "component_name": _str_attr(damage, "component_name"),
    "component_system": _str_attr(damage, "component_system"),
    "component_redundancy_group_id": _str_attr(
      damage, "component_redundancy_group_id"
    ),
    "integrity_before": _float_attr(damage, "integrity_before"),
    "integrity_after": _float_attr(damage, "integrity_after"),
    "failure_mode": _str_attr(damage, "failure_mode"),
    "failure_severity": _float_attr(damage, "failure_severity"),
    "failure_probability": _float_attr(damage, "failure_probability"),
    "failure_sample": _float_attr(damage, "failure_sample"),
  }


def _empty_component_probability_row_summary() -> dict[str, Any]:
  return {
    "component_name": "",
    "component_system": "",
    "component_redundancy_group_id": "",
    "direct_hit": False,
    "distance_m": 0.0,
    "effect_scale": 0.0,
    "component_failure_probability": 0.0,
    "mechanism_fragment_energy_j": 0.0,
    "mechanism_fragment_areal_density_per_m2": 0.0,
    "mechanism_blast_overpressure_kpa": 0.0,
    "mechanism_blast_impulse_kpa_ms": 0.0,
    "mechanism_penetration_margin": 0.0,
    "mechanism_rod_cut_margin": 0.0,
  }


def _component_row_for_name(
  rows: list[dict[str, Any]], component_name: str
) -> dict[str, Any]:
  for row in rows:
    if str(row["component_name"]) == component_name:
      return row
  return _empty_component_probability_row_summary()


def _max_probability_component_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
  if not rows:
    return _empty_component_probability_row_summary()
  return max(rows, key=lambda row: float(row["component_failure_probability"]))


def _event_summary(
  *,
  database_path: Path,
  family: str,
  local_point_m: tuple[float, float, float],
  missile_velocity_body_mps: tuple[float, float, float],
  seed: int,
) -> dict[str, Any]:
  sim = ef_py.SimulationKernel()
  sim.reset(int(seed))
  if not sim.load_database(str(database_path)):
    raise RuntimeError(f"failed to load database: {database_path}")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile(family)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local_point_m[0]),
    float(local_point_m[1]),
    float(local_point_m[2]),
    profile,
    float(missile_velocity_body_mps[0]),
    float(missile_velocity_body_mps[1]),
    float(missile_velocity_body_mps[2]),
  )
  if not ok:
    raise RuntimeError("debug profiled local proximity hit failed")

  events = sim.export_recent_engagement_events()
  if len(events.effects_events) != 1:
    raise RuntimeError("expected exactly one effects event")
  effect = events.effects_events[0]
  rows = [
    _row_summary(row)
    for row in effect.component_mechanism_load_rows
    if _str_attr(row, "component_name") or _str_attr(row, "component_system")
  ]
  loads = [_component_load_summary(load) for load in events.component_load_events]
  damages = [
    _component_damage_summary(damage) for damage in events.component_damage_events
  ]
  primary_component_name = _str_attr(effect, "component_primary_name")
  primary_row = _component_row_for_name(rows, primary_component_name)
  max_probability_row = _max_probability_component_row(rows)
  return {
    "database_path": _relative_path(database_path),
    "effect_family": _str_attr(effect, "effect_family"),
    "trigger_type": _str_attr(effect, "trigger_type"),
    "outcome_state": _str_attr(effect, "outcome_state"),
    "miss_distance_m": _float_attr(effect, "miss_distance_m"),
    "closure_mps": _float_attr(effect, "closure_mps"),
    "vulnerability_aspect_bucket": _str_attr(effect, "vulnerability_aspect_bucket"),
    "vulnerability_aspect_scale": _float_attr(effect, "vulnerability_aspect_scale"),
    "spatial_effect_scale": _float_attr(effect, "spatial_effect_scale"),
    "mechanism_effect_scale": _float_attr(effect, "mechanism_effect_scale"),
    "warhead_spatial_hit_estimate": _float_attr(
      effect, "warhead_spatial_hit_estimate"
    ),
    "warhead_spatial_pattern_scale": _float_attr(
      effect, "warhead_spatial_pattern_scale"
    ),
    "warhead_orientation_pattern_scale": _float_attr(
      effect, "warhead_orientation_pattern_scale"
    ),
    "direct_hitbox_intersection": _bool_attr(effect, "direct_hitbox_intersection"),
    "projected_hitbox_count": _int_attr(effect, "projected_hitbox_count"),
    "component_hit_count": _int_attr(effect, "component_hit_count"),
    "component_failure_count": _int_attr(effect, "component_failure_count"),
    "component_primary_name": primary_component_name,
    "component_primary_system": _str_attr(effect, "component_primary_system"),
    "component_primary_redundancy_group_id": _str_attr(
      effect, "component_primary_redundancy_group_id"
    ),
    "component_primary_integrity": _float_attr(
      effect, "component_primary_integrity", 1.0
    ),
    "component_failure_probability": _float_attr(
      effect, "component_failure_probability"
    ),
    "component_failure_probability_event_aggregation": (
      "max_probability_across_component_mechanism_load_rows"
    ),
    "component_failure_probability_source": _str_attr(
      effect, "component_failure_probability_source"
    ),
    "component_primary_row_failure_probability": float(
      primary_row["component_failure_probability"]
    ),
    "component_primary_row_direct_hit": bool(primary_row["direct_hit"]),
    "component_primary_row_distance_m": float(primary_row["distance_m"]),
    "component_primary_row_effect_scale": float(primary_row["effect_scale"]),
    "component_max_failure_probability": float(
      max_probability_row["component_failure_probability"]
    ),
    "component_max_failure_probability_component_name": str(
      max_probability_row["component_name"]
    ),
    "component_max_failure_probability_component_system": str(
      max_probability_row["component_system"]
    ),
    "component_max_failure_probability_distance_m": float(
      max_probability_row["distance_m"]
    ),
    "component_max_failure_probability_effect_scale": float(
      max_probability_row["effect_scale"]
    ),
    "component_primary_mechanism_fragment_energy_j": _float_attr(
      effect, "component_primary_mechanism_fragment_energy_j"
    ),
    "component_primary_mechanism_fragment_areal_density_per_m2": _float_attr(
      effect, "component_primary_mechanism_fragment_areal_density_per_m2"
    ),
    "component_primary_mechanism_blast_overpressure_kpa": _float_attr(
      effect, "component_primary_mechanism_blast_overpressure_kpa"
    ),
    "component_primary_mechanism_blast_impulse_kpa_ms": _float_attr(
      effect, "component_primary_mechanism_blast_impulse_kpa_ms"
    ),
    "component_primary_mechanism_penetration_margin": _float_attr(
      effect, "component_primary_mechanism_penetration_margin"
    ),
    "component_primary_mechanism_rod_cut_margin": _float_attr(
      effect, "component_primary_mechanism_rod_cut_margin"
    ),
    "warhead_profile_synthetic": _bool_attr(effect, "warhead_profile_synthetic"),
    "damage_scalar_synthetic": _bool_attr(effect, "damage_scalar_synthetic"),
    "vulnerability_pk_authority": _bool_attr(effect, "vulnerability_pk_authority"),
    "vulnerability_deterministic_fuze_authority": _bool_attr(
      effect, "vulnerability_deterministic_fuze_authority"
    ),
    "component_mechanism_row_names": [
      row["component_name"] for row in rows if row["component_name"]
    ],
    "component_load_event_names": [
      load["component_name"] for load in loads if load["component_name"]
    ],
    "component_damage_event_names": [
      damage["component_name"] for damage in damages if damage["component_name"]
    ],
    "component_mechanism_load_rows": rows,
    "component_load_events": loads,
    "component_damage_events": damages,
  }


def _values_differ(left: object, right: object) -> bool:
  if isinstance(left, float) or isinstance(right, float):
    return abs(float(left) - float(right)) > 1.0e-9
  return left != right


def _event_names(event: dict[str, Any]) -> set[str]:
  names = set(event["component_mechanism_row_names"])
  names.update(event["component_load_event_names"])
  names.update(event["component_damage_event_names"])
  if event["component_primary_name"]:
    names.add(str(event["component_primary_name"]))
  return names


def _diff_events(
  default_event: dict[str, Any], proxy_event: dict[str, Any]
) -> dict[str, dict[str, Any]]:
  diff: dict[str, dict[str, Any]] = {}
  for field in COMPARE_FIELDS:
    default_value = default_event[field]
    proxy_value = proxy_event[field]
    if _values_differ(default_value, proxy_value):
      diff[field] = {
        "default": default_value,
        "proxy": proxy_value,
      }
  return diff


def _comparison(
  case: dict[str, Any],
  *,
  family: str,
  seed: int,
) -> dict[str, Any]:
  local_point_m = tuple(float(value) for value in case["local_point_m"])
  missile_velocity_body_mps = tuple(
    float(value) for value in case["missile_velocity_body_mps"]
  )
  default_event = _event_summary(
    database_path=DEFAULT_DATABASE_PATH,
    family=family,
    local_point_m=local_point_m,
    missile_velocity_body_mps=missile_velocity_body_mps,
    seed=seed,
  )
  proxy_event = _event_summary(
    database_path=PROXY_DATABASE_PATH,
    family=family,
    local_point_m=local_point_m,
    missile_velocity_body_mps=missile_velocity_body_mps,
    seed=seed,
  )
  diff = _diff_events(default_event, proxy_event)
  default_names = _event_names(default_event)
  proxy_names = _event_names(proxy_event)
  return {
    "case_id": str(case["case_id"]),
    "warhead_family": family,
    "aspect": str(case["aspect"]),
    "range_bucket": str(case["range_bucket"]),
    "local_point_m": list(local_point_m),
    "missile_velocity_body_mps": list(missile_velocity_body_mps),
    "default_event": default_event,
    "proxy_event": proxy_event,
    "diff": diff,
    "geometry_effect_observed": bool(diff),
    "proxy_split_receiver_names_observed": sorted(
      name for name in proxy_names if name in SPLIT_RECEIVER_NAMES
    ),
    "default_retired_parent_names_observed": sorted(
      name for name in default_names if name in RETIRED_PARENT_COMPONENTS
    ),
    "proxy_retired_parent_names_observed": sorted(
      name for name in proxy_names if name in RETIRED_PARENT_COMPONENTS
    ),
  }


def _comparison_by_case(
  comparisons: list[dict[str, Any]], family: str, case_id: str
) -> dict[str, Any]:
  for comparison in comparisons:
    if (
      str(comparison["warhead_family"]) == family
      and str(comparison["case_id"]) == case_id
    ):
      return comparison
  raise KeyError(f"{family}:{case_id}")


def _near_far_monotonic_checks(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
  checks: list[dict[str, Any]] = []
  for family in WARHEAD_FAMILIES:
    near = _comparison_by_case(comparisons, family, "right_beam_near_7m")
    far = _comparison_by_case(comparisons, family, "right_beam_far_14m")
    for database_label in ("default_event", "proxy_event"):
      near_event = near[database_label]
      far_event = far[database_label]
      if family == "continuous_rod":
        near_value = near_event["component_primary_mechanism_rod_cut_margin"]
        far_value = far_event["component_primary_mechanism_rod_cut_margin"]
        metric = "component_primary_mechanism_rod_cut_margin"
      else:
        near_value = near_event["component_primary_mechanism_fragment_energy_j"]
        far_value = far_event["component_primary_mechanism_fragment_energy_j"]
        metric = "component_primary_mechanism_fragment_energy_j"
      checks.append(
        {
          "warhead_family": family,
          "database_label": database_label.removesuffix("_event"),
          "near_case_id": str(near["case_id"]),
          "far_case_id": str(far["case_id"]),
          "metric": metric,
          "near_value": near_value,
          "far_value": far_value,
          "pass": float(near_value) > float(far_value),
        }
      )
  return {
    "checks": checks,
    "all_pass": all(bool(check["pass"]) for check in checks),
  }


def _metrics(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
  changed = [item for item in comparisons if bool(item["geometry_effect_observed"])]
  changed_primary = [
    item
    for item in comparisons
    if "component_primary_name" in item["diff"]
    or "component_primary_system" in item["diff"]
  ]
  changed_rows = [
    item
    for item in comparisons
    if "component_mechanism_row_names" in item["diff"]
    or "component_load_event_names" in item["diff"]
    or "component_damage_event_names" in item["diff"]
  ]
  near_far = _near_far_monotonic_checks(comparisons)
  family_changed_counts = {
    family: sum(
      1
      for item in comparisons
      if str(item["warhead_family"]) == family
      and bool(item["geometry_effect_observed"])
    )
    for family in WARHEAD_FAMILIES
  }
  unchanged_case_ids = sorted(
    str(case["case_id"])
    for case in CASE_DEFINITIONS
    if all(
      not bool(item["geometry_effect_observed"])
      for item in comparisons
      if str(item["case_id"]) == str(case["case_id"])
    )
  )
  return {
    "case_count": len(CASE_DEFINITIONS),
    "warhead_family_count": len(WARHEAD_FAMILIES),
    "comparison_count": len(comparisons),
    "event_run_count": len(comparisons) * 2,
    "changed_comparison_count": len(changed),
    "changed_primary_component_count": len(changed_primary),
    "changed_component_event_row_count": len(changed_rows),
    "changed_case_ids": sorted({str(item["case_id"]) for item in changed}),
    "changed_comparison_ids": sorted(
      f"{item['warhead_family']}:{item['case_id']}" for item in changed
    ),
    "unchanged_comparison_ids": sorted(
      f"{item['warhead_family']}:{item['case_id']}"
      for item in comparisons
      if not bool(item["geometry_effect_observed"])
    ),
    "fully_unchanged_case_ids": unchanged_case_ids,
    "family_changed_comparison_counts": family_changed_counts,
    "proxy_split_receiver_comparison_count": sum(
      1 for item in comparisons if item["proxy_split_receiver_names_observed"]
    ),
    "default_retired_parent_comparison_count": sum(
      1 for item in comparisons if item["default_retired_parent_names_observed"]
    ),
    "proxy_retired_parent_comparison_count": sum(
      1 for item in comparisons if item["proxy_retired_parent_names_observed"]
    ),
    "nose_cockpit_center_unchanged_for_both_families": all(
      not bool(item["geometry_effect_observed"])
      for item in comparisons
      if str(item["case_id"]) == "nose_cockpit_center"
    ),
    "right_beam_near_far_monotonic_checks": near_far,
  }


def generate_report(*, seed: int = 20260614) -> dict[str, Any]:
  _configure_runtime_log_level()
  comparisons = [
    _comparison(case, family=family, seed=seed)
    for family in WARHEAD_FAMILIES
    for case in CASE_DEFINITIONS
  ]
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "target_unit": "F-16C_Block50",
    "seed": seed,
    "database_paths": {
      "default_database_path": _relative_path(DEFAULT_DATABASE_PATH),
      "proxy_database_path": _relative_path(PROXY_DATABASE_PATH),
    },
    "authority_boundary": {
      "debug_profiled_local_hit": True,
      "synthetic_warhead_profiles": True,
      "real_weapon_pk_authority": False,
      "deterministic_fuze_authority": False,
      "true_internal_component_geometry": False,
      "default_database_modified": False,
      "proxy_database_opt_in_only": True,
    },
    "probe_design": {
      "warhead_families": list(WARHEAD_FAMILIES),
      "compare_fields": list(COMPARE_FIELDS),
      "case_ids": [str(case["case_id"]) for case in CASE_DEFINITIONS],
    },
    "metrics": _metrics(comparisons),
    "comparisons": comparisons,
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
  parser.add_argument("--seed", type=int, default=20260614)
  args = parser.parse_args()

  report = generate_report(seed=int(args.seed))
  text = json.dumps(report, indent=2, sort_keys=True)
  if args.output is not None:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
  print(text)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
