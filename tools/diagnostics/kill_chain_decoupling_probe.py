#!/usr/bin/env python3
"""Generate decoupled kill-chain diagnostics for guidance and proximity slices."""

from __future__ import annotations

import argparse
import contextlib
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
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_abstraction import (  # noqa: E402
  _lethality_chain_decoupling_summary,
  _lethality_chain_stage_abstractions,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_chain import (  # noqa: E402
  _lethality_chain_rows,
)
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.lethality_scalar_ledger import (  # noqa: E402
  SCALAR_LEDGER_SCHEMA_VERSION,
  _effect_summary_scalar_ledger,
  _lethality_chain_scalar_ledger,
  _scalar_coupling_summary,
)


SCHEMA_VERSION = "a2.kill_chain_decoupling_probe.v1"
FACADE_SCHEMA_VERSION = "a2.kill_chain_decoupled_facade.v1"
RUNTIME_FACADE_SCHEMA_VERSION = "a2.kill_chain_runtime_facade.v1"
RUNTIME_PROJECTION_PROFILE_SCHEMA_VERSION = (
  "a2.kill_chain_runtime_projection_profile.v1"
)
CALIBRATION_ADMISSION_SCHEMA_VERSION = "a2.kill_chain_calibration_admission.v1"
CALIBRATION_PLAN_SCHEMA_VERSION = "a2.kill_chain_single_layer_calibration_plan.v1"
CALIBRATION_DELTA_GUARD_SCHEMA_VERSION = "a2.kill_chain_calibration_delta_guard.v1"
CALIBRATION_EVIDENCE_PREFLIGHT_SCHEMA_VERSION = "a2.kill_chain_calibration_evidence_preflight.v1"
COMPLETION_AUDIT_SCHEMA_VERSION = "a2.kill_chain_completion_audit.v1"
CALIBRATION_EVIDENCE_TEMPLATE_SCHEMA_VERSION = "a2.kill_chain_calibration_evidence_template.v1"
CALIBRATION_EVIDENCE_TEMPLATE_CHECK_SCHEMA_VERSION = "a2.kill_chain_calibration_evidence_template_check.v1"
CALIBRATION_EVIDENCE_CONTRACT_SURFACE_SCHEMA_VERSION = "a2.kill_chain_calibration_evidence_contract_surface.v1"
CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_SCHEMA_VERSION = "a2.kill_chain_calibration_supplemental_evidence_contract.v1"
CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_CHECK_SCHEMA_VERSION = "a2.kill_chain_calibration_supplemental_evidence_contract_check.v1"
SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION = "a2.kill_chain_supplemental_authority_evidence.v1"
MLF10_CALIBRATION_ADMISSION_REPORT_SCHEMA_VERSION = "mlf10.calibration_admission_report.v1"
DEFAULT_DATABASE_PATH = Path(resolve_repo_path("examples", "config", "database"))
DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH = (
  REPO_ROOT
  / "docs/task/air_combat/a2_high_fidelity_damage_model/archive/"
  "missile_lethality_calibration_gates/mlf10_calibration_admission_report_20260619.json"
)
DEFAULT_GUIDANCE_CASES = (
  {"case_id": "aim120_16km_left_20deg", "range_m": 16000.0, "bearing_deg": -20.0},
  {"case_id": "aim120_16km_right_20deg", "range_m": 16000.0, "bearing_deg": 20.0},
  {"case_id": "aim120_8km_left_30deg", "range_m": 8000.0, "bearing_deg": -30.0},
  {"case_id": "aim120_8km_right_30deg", "range_m": 8000.0, "bearing_deg": 30.0},
)
GUIDANCE_TUNING_OVERRIDE_FIELDS = frozenset(
  {
    "apn_target_accel_gain",
    "autopilot_damping",
    "autopilot_order",
    "autopilot_tau_s",
    "bearing_filter_tau_s",
    "elevation_filter_tau_s",
    "guidance_update_period_s",
    "max_accel_response_g_per_s",
    "max_lateral_g",
    "nav_gain",
    "range_filter_tau_s",
  }
)
DEFAULT_PROXIMITY_DISTANCES_M = (0.5, 2.0, 4.0, 8.0, 10.96, 12.0, 15.0)
WARHEAD_SPATIAL_PROJECTION_DEFAULTS = {
  "blast": (0.55, 1.0, 20.0),
  "fragmentation": (0.45, 1.0, 18.0),
  "blast_fragmentation": (0.45, 1.0, 18.0),
  "continuous_rod": (0.32, 1.0, 11.0),
  "hit_to_kill": (0.24, 1.0, 6.0),
}
DEFAULT_WARHEAD_SPATIAL_PROJECTION = (0.35, 1.0, 12.0)
LOAD_ONLY_COMPONENT_FIELDS = (
  "direct_hit",
  "distance_m",
  "fragment_energy_j",
  "fragment_density_per_m2",
  "penetration_margin",
  "blast_overpressure_kpa",
  "blast_impulse_kpa_ms",
  "blast_scaled_distance_m_kg13",
  "rod_cut_margin",
  "surface_incidence_cos",
)
RESPONSE_COMPONENT_FIELDS = (
  "component_threshold_scale",
  "component_failure_probability",
  "component_failure_sample",
  "component_failure_primary_mode",
  "component_failure_primary_mode_severity",
  "component_integrity_before",
  "component_integrity_after",
)
AGGREGATE_COUPLED_COMPONENT_LOAD_FIELDS = ("effect_scale",)
CALIBRATION_STAGE_IDS = (
  "approach",
  "fuze_decision",
  "warhead_load_field",
  "component_response",
  "consequence_projection",
)
CALIBRATION_LAYER_SPECS = (
  (
    "fuze_data",
    "fuze_decision",
    "reliability, detection window, delay, detonation probability",
    "fuze profile evidence with no warhead-load or response-curve edits",
    ("deterministic_fuze_authority",),
  ),
  (
    "warhead_data",
    "warhead_load_field",
    "projection radius, fragment mass/count/velocity, blast decay, pattern",
    "warhead evidence with no fuze reliability or component-threshold edits",
    ("effect_scale_authority",),
  ),
  (
    "target_response_data",
    "component_response",
    "component thresholds, armor/exposure, redundancy, failure-mode probability",
    "target response evidence after response owner rows are clean",
    ("component_failure_probability_authority",),
  ),
  (
    "consequence_data",
    "consequence_projection",
    "component-failure to platform loss/reward mapping",
    "consequence mapping evidence with fixed upstream component responses",
    ("pk_authority",),
  ),
)
EVIDENCE_UNBLOCK_ACTIONS = {
  "blocking_residuals_open": "close listed residuals and attach reviewer-visible closeout evidence",
  "component_fragility_provenance_missing": "provide component fragility provenance for the requested response authority",
  "independent_review_not_passed": "complete independent review with pass decision",
  "independent_reviewer_ref_missing": "attach independent reviewer reference",
  "population_sample_count_invalid": "provide a valid release-grade population/sample count",
  "rights_not_release_grade_admitted": "attach release-grade rights and allowed-output signoff",
  "source_gate_not_passed": "pass the source eligibility gate",
  "uncertainty_coverage_missing": "provide uncertainty coverage for the claimed scope",
  "uncertainty_method_missing": "provide uncertainty method and assumptions",
  "uncertainty_residuals_open": "close uncertainty residuals",
  "validation_not_passed": "complete validation package for the claimed authority field",
}
MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS = {
  "component_failure_probability_authority",
  "effect_scale_authority",
}
SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS = {
  "deterministic_fuze_authority",
  "pk_authority",
}
MANDATORY_EVIDENCE_NON_CLAIMS = (
  "real_world_pk",
  "deterministic_fuze_reliability",
  "reward_authority",
  "entity_deletion_authority",
  "out_of_scope_weapon_truth",
  "out_of_scope_target_truth",
)
MLF10_EVIDENCE_REQUIRED_FIELDS = (
  "schema_version",
  "evidence_id",
  "evidence_class",
  "source_kind",
  "source_ref",
  "provenance",
  "rights_status",
  "source_gate_status",
  "validation_status",
  "scope",
  "population",
  "uncertainty",
  "independent_review",
  "authority_requests",
  "non_claims",
  "residuals",
)
MLF10_SCOPE_FIELDS = (
  "target_type",
  "weapon_family",
  "mechanism_family",
  "aspect_bucket",
  "closure_bucket",
  "miss_distance_bucket",
)
MLF10_POPULATION_FIELDS = (
  "identity",
  "denominator_name",
  "sample_count",
  "filters",
  "independence_assumption",
)
SUPPLEMENTAL_EVIDENCE_REQUIRED_FIELDS = (
  "schema_version",
  "evidence_id",
  "layer_id",
  "owner_stage",
  "authority_field",
  "authority_scope",
  "source_kind",
  "source_ref",
  "provenance",
  "rights_status",
  "source_gate_status",
  "validation_status",
  "scope",
  "population",
  "uncertainty",
  "independent_review",
  "stage_delta_requirements",
  "non_claims",
  "residuals",
)


def _finite_float(value: Any, default: float = float("nan")) -> float:
  try:
    out = float(value)
  except Exception:
    return float(default)
  return out if math.isfinite(out) else float(default)


def _finite_or_none(value: Any) -> float | None:
  out = _finite_float(value)
  return out if math.isfinite(out) else None


def _apply_guidance_tuning_overrides(
  tuning: Any,
  overrides: dict[str, float | int] | None,
) -> dict[str, float | int]:
  applied: dict[str, float | int] = {}
  for field, raw_value in sorted(dict(overrides or {}).items()):
    if field not in GUIDANCE_TUNING_OVERRIDE_FIELDS:
      raise ValueError(f"unsupported guidance tuning override: {field}")
    if not hasattr(tuning, field):
      raise ValueError(f"runtime MissileTuning lacks field: {field}")
    value: float | int
    if field in {"autopilot_order"}:
      value = int(raw_value)
    else:
      value = float(raw_value)
      if not math.isfinite(value):
        raise ValueError(f"guidance tuning override must be finite: {field}")
    setattr(tuning, field, value)
    applied[field] = value
  return applied


def _guidance_runtime_trace_sample(
  runtime: dict[str, Any],
  *,
  time_s: float,
  truth_distance_m: float,
  transform_heading_deg: float,
  velocity_heading_deg: float,
) -> dict[str, Any]:
  target_accel = (
    _finite_float(runtime.get("target_track_ax_mps2", 0.0), 0.0),
    _finite_float(runtime.get("target_track_ay_mps2", 0.0), 0.0),
    _finite_float(runtime.get("target_track_az_mps2", 0.0), 0.0),
  )
  commanded = _finite_float(runtime.get("commanded_lateral_accel_mps2", 0.0), 0.0)
  max_lateral_g = _finite_float(runtime.get("guidance_max_lateral_g", 0.0), 0.0)
  max_lateral_accel = max(0.0, max_lateral_g * 9.80665)
  heading_error_deg = velocity_heading_deg - transform_heading_deg
  while heading_error_deg > 180.0:
    heading_error_deg -= 360.0
  while heading_error_deg < -180.0:
    heading_error_deg += 360.0
  return {
    "time_s": float(time_s),
    "truth_distance_m": float(truth_distance_m),
    "transform_heading_deg": float(transform_heading_deg),
    "velocity_heading_deg": float(velocity_heading_deg),
    "heading_velocity_error_deg": float(heading_error_deg),
    "filtered_range_m": _finite_or_none(runtime.get("filtered_range_m")),
    "filtered_bearing_deg": _finite_or_none(runtime.get("filtered_bearing_deg")),
    "filtered_elevation_deg": _finite_or_none(runtime.get("filtered_elevation_deg")),
    "filtered_closing_speed_mps": _finite_or_none(
      runtime.get("filtered_closing_speed_mps")
    ),
    "bearing_rate_deg_s": _finite_or_none(runtime.get("bearing_rate_deg_s")),
    "elevation_rate_deg_s": _finite_or_none(runtime.get("elevation_rate_deg_s")),
    "current_speed_mps": _finite_or_none(runtime.get("current_speed_mps")),
    "commanded_lateral_accel_mps2": commanded,
    "achieved_lateral_accel_mps2": _finite_float(
      runtime.get("achieved_lateral_accel_mps2", 0.0),
      0.0,
    ),
    "guidance_max_lateral_g": max_lateral_g,
    "command_saturated": bool(
      max_lateral_accel > 0.0 and commanded >= 0.995 * max_lateral_accel
    ),
    "guidance_lead_time_s": _finite_or_none(runtime.get("guidance_lead_time_s")),
    "guidance_lead_blend": _finite_or_none(runtime.get("guidance_lead_blend")),
    "guidance_apn_lateral_accel_mps2": _finite_or_none(
      runtime.get("guidance_apn_lateral_accel_mps2")
    ),
    "target_kinematics_valid": bool(runtime.get("target_kinematics_valid")),
    "target_track_accel_mps2": math.sqrt(sum(value * value for value in target_accel)),
    "seeker_mode": int(runtime.get("seeker_mode", 0) or 0),
  }


def _runtime_projection_profile(runtime_state: dict[str, Any]) -> dict[str, Any]:
  family = str(runtime_state.get("warhead_family", "") or "blast_fragmentation")
  default_fraction, default_min_radius, default_max_radius = (
    WARHEAD_SPATIAL_PROJECTION_DEFAULTS.get(
      family,
      DEFAULT_WARHEAD_SPATIAL_PROJECTION,
    )
  )
  lethal_radius_m = _finite_or_none(
    runtime_state.get("warhead_lethal_radius_m")
  )
  fuse_distance_m = _finite_or_none(runtime_state.get("fuse_distance_m"))
  authored_fraction = _finite_or_none(
    runtime_state.get("warhead_projection_radius_fraction")
  )
  authored_min_radius = _finite_or_none(
    runtime_state.get("warhead_projection_min_radius_m")
  )
  authored_max_radius = _finite_or_none(
    runtime_state.get("warhead_projection_max_radius_m")
  )
  radius_fraction = min(
    2.0,
    max(0.05, authored_fraction if authored_fraction is not None else default_fraction),
  )
  min_radius_m = min(
    100.0,
    max(0.0, authored_min_radius if authored_min_radius is not None else default_min_radius),
  )
  max_radius_m = min(
    100.0,
    max(
      min_radius_m,
      authored_max_radius if authored_max_radius is not None else default_max_radius,
    ),
  )
  resolved_radius_m = None
  radius_input_m = lethal_radius_m if lethal_radius_m is not None else fuse_distance_m
  if lethal_radius_m is not None:
    radius_input_source = "warhead_lethal_radius_m"
  elif fuse_distance_m is not None:
    radius_input_source = "fuse_distance_m"
  else:
    radius_input_source = "unavailable"
  if radius_input_m is not None:
    resolved_radius_m = min(
      max_radius_m,
      max(min_radius_m, radius_input_m * radius_fraction),
    )
  return {
    "schema_version": RUNTIME_PROJECTION_PROFILE_SCHEMA_VERSION,
    "effect_family": family,
    "lethal_radius_m": lethal_radius_m,
    "fuse_distance_m": fuse_distance_m,
    "radius_input_m": radius_input_m,
    "radius_input_source": radius_input_source,
    "projection_radius_fraction": radius_fraction,
    "projection_min_radius_m": min_radius_m,
    "projection_max_radius_m": max_radius_m,
    "resolved_projection_radius_m": resolved_radius_m,
    "source": "missile_runtime_state",
  }


def _int_attr(obj: Any, name: str, default: int = 0) -> int:
  try:
    return int(getattr(obj, name, default) or default)
  except Exception:
    return int(default)


def _float_attr(obj: Any, name: str, default: float = float("nan")) -> float | None:
  return _finite_or_none(getattr(obj, name, default))


def _str_attr(obj: Any, name: str, default: str = "") -> str:
  return str(getattr(obj, name, default) or default)


def _bool_attr(obj: Any, name: str, default: bool = False) -> bool:
  return bool(getattr(obj, name, default))


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
  if numerator is None or denominator is None:
    return None
  if abs(float(denominator)) <= 1.0e-12:
    return None
  return float(numerator) / float(denominator)


def _product_or_none(values: tuple[float | None, ...]) -> float | None:
  product = 1.0
  for value in values:
    if value is None:
      return None
    product *= float(value)
  return product


def _field_present(value: Any) -> bool:
  if value is None:
    return False
  if isinstance(value, str):
    return bool(value)
  if isinstance(value, bool):
    return True
  if isinstance(value, (int, float)):
    return math.isfinite(float(value))
  return True


def _present_fields(row: dict[str, Any], names: tuple[str, ...]) -> list[str]:
  return [name for name in names if _field_present(row.get(name))]


def _load_row_response_fields(row: dict[str, Any]) -> list[str]:
  fields: list[str] = []
  if (_finite_or_none(row.get("component_threshold_scale")) not in (None, 1.0)):
    fields.append("component_threshold_scale")
  if (_finite_or_none(row.get("component_failure_probability")) not in (None, 0.0)):
    fields.append("component_failure_probability")
  if (_finite_or_none(row.get("component_failure_sample")) not in (None, 1.0)):
    fields.append("component_failure_sample")
  mode = str(row.get("component_failure_primary_mode", "") or "")
  if mode and mode != "none":
    fields.append("component_failure_primary_mode")
  if (_finite_or_none(row.get("component_failure_primary_mode_severity")) not in (None, 0.0)):
    fields.append("component_failure_primary_mode_severity")
  if (_finite_or_none(row.get("component_integrity_before")) not in (None, 1.0)):
    fields.append("component_integrity_before")
  if (_finite_or_none(row.get("component_integrity_after")) not in (None, 1.0)):
    fields.append("component_integrity_after")
  return fields


def _make_kernel(database_path: Path, *, seed: int) -> ef_py.SimulationKernel:
  sim = ef_py.SimulationKernel()
  sim.reset(int(seed))
  if not sim.load_database(str(database_path)):
    raise RuntimeError(f"failed to load database: {database_path}")
  sim.set_time_step(1.0 / 60.0)
  return sim


def _make_detection(
  target_id: int,
  *,
  range_m: float,
  bearing_deg: float,
  elevation_deg: float = 0.0,
  closing_speed_mps: float = 350.0,
  signal_strength: float = 1.0,
  local_sensor_hit: bool = True,
  timestamp: float = 0.0,
) -> ef_py.Detection:
  det = ef_py.Detection()
  det.target_id = int(target_id)
  det.range = float(range_m)
  det.bearing = float(bearing_deg)
  det.elevation = float(elevation_deg)
  det.closing_speed = float(closing_speed_mps)
  det.signal_strength = float(signal_strength)
  det.local_sensor_hit = bool(local_sensor_hit)
  det.timestamp = float(timestamp)
  return det


def _relative_detection_from_truth(
  sim: ef_py.SimulationKernel,
  observer_id: int,
  target_id: int,
  *,
  timestamp: float,
) -> ef_py.Detection:
  ox, oy, oz = (float(value) for value in sim.get_unit_position(int(observer_id)))
  tx, ty, tz = (float(value) for value in sim.get_unit_position(int(target_id)))
  ovx, ovy, ovz = (float(value) for value in sim.get_unit_velocity(int(observer_id)))
  tvx, tvy, tvz = (float(value) for value in sim.get_unit_velocity(int(target_id)))
  dx = tx - ox
  dy = ty - oy
  dz = tz - oz
  horizontal = math.hypot(dx, dy)
  distance = math.sqrt(dx * dx + dy * dy + dz * dz)
  bearing_nav = math.degrees(math.atan2(dx, dy))
  heading = float(sim.get_unit_heading(int(observer_id)))
  relative_bearing = bearing_nav - heading
  while relative_bearing > 180.0:
    relative_bearing -= 360.0
  while relative_bearing < -180.0:
    relative_bearing += 360.0
  elevation = math.degrees(math.atan2(dz, horizontal)) if horizontal > 1.0e-9 else 0.0
  closing = 0.0
  if distance > 1.0e-9:
    ux = dx / distance
    uy = dy / distance
    uz = dz / distance
    rel_vx = tvx - ovx
    rel_vy = tvy - ovy
    rel_vz = tvz - ovz
    closing = -(rel_vx * ux + rel_vy * uy + rel_vz * uz)
  return _make_detection(
    int(target_id),
    range_m=distance,
    bearing_deg=relative_bearing,
    elevation_deg=elevation,
    closing_speed_mps=closing,
    timestamp=timestamp,
  )


def _spawn_geometry_pair(
  sim: ef_py.SimulationKernel,
  *,
  red_x: float,
  red_y: float,
  red_heading: float,
  red_vx: float,
  red_vy: float,
) -> tuple[int, int]:
  blue_id = int(
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
      250.0,
      0.0,
    )
  )
  red_id = int(
    sim.spawn_unit(
      ef_py.Side.Red,
      "F-16C_Block50",
      red_x,
      red_y,
      5000.0,
      red_heading,
      0.0,
      0.0,
      red_vx,
      red_vy,
      0.0,
    )
  )
  sim.set_unit_ammo(blue_id, 4, 4)
  sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
  sim.set_contact_list(blue_id, [_relative_detection_from_truth(sim, blue_id, red_id, timestamp=0.0)])
  return blue_id, red_id


def _select_weapon_station(sim: ef_py.SimulationKernel, entity_id: int, station_id: int) -> None:
  pilot = ef_py.PilotAction()
  pilot.active = True
  pilot.weapon_select_id = int(station_id)
  sim.set_pilot_action(int(entity_id), pilot)


def _set_unit_truth_state(
  sim: ef_py.SimulationKernel,
  entity_id: int,
  *,
  x: float,
  y: float,
  heading: float,
  vx: float,
  vy: float,
) -> None:
  sim.debug_set_unit_truth_state(
    int(entity_id),
    float(x),
    float(y),
    5000.0,
    float(heading),
    0.0,
    0.0,
    float(vx),
    float(vy),
    0.0,
  )


def _spawn_structured_f16_pair(sim: ef_py.SimulationKernel) -> tuple[int, int]:
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
      250.0,
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
      -250.0,
      0.0,
    )
  )
  return attacker_id, target_id


def _make_fuze_profile() -> ef_py.FuzeProfile:
  profile = ef_py.FuzeProfile()
  profile.type = "radar_proximity"
  profile.trigger_radius_m = 15.0
  profile.delay_s = 0.0
  profile.reliability = 1.0
  profile.trigger_logic = "nearest_approach"
  profile.synthetic = False
  profile.provenance = "kill_chain_decoupling_probe_aim120_offset"
  return profile


def _make_warhead_profile(
  family: str,
  *,
  damage: float,
  radius: float,
  mass_kg: float,
) -> ef_py.WarheadProfile:
  profile = ef_py.WarheadProfile()
  profile.family = str(family)
  profile.mass_kg = float(mass_kg)
  profile.lethal_radius_m = float(radius)
  profile.damage_scalar = float(damage)
  profile.synthetic = False
  profile.damage_scalar_synthetic = False
  profile.provenance = "kill_chain_decoupling_probe_profile"
  return profile


def missile_velocity_toward_origin(
  local_point_m: tuple[float, float, float],
  *,
  speed_mps: float = 900.0,
) -> tuple[float, float, float]:
  distance_m = math.sqrt(sum(float(value) ** 2 for value in local_point_m))
  if distance_m <= 1.0e-9:
    return (0.0, 0.0, 0.0)
  return tuple(-float(value) / distance_m * float(speed_mps) for value in local_point_m)


def _event_effect_summary(effect: Any | None) -> dict[str, Any]:
  if effect is None:
    return {}
  response_rows = list(getattr(effect, "component_response_rows", []) or [])
  max_probability_row = None
  max_probability_effect_scale = None
  if response_rows:
    max_probability_row = max(
      response_rows,
      key=lambda row: _finite_float(
        getattr(row, "failure_probability", float("nan")),
        -1.0,
      ),
    )
    source_row_index = _int_attr(max_probability_row, "source_row_index", -1)
    rows = list(getattr(effect, "component_mechanism_load_rows", []) or [])
    if 0 <= source_row_index < len(rows):
      max_probability_effect_scale = _float_attr(rows[source_row_index], "effect_scale")
  return {
    "event_id": _int_attr(effect, "event_id"),
    "trigger_type": _str_attr(effect, "trigger_type"),
    "outcome_state": _str_attr(effect, "outcome_state"),
    "effect_family": _str_attr(effect, "effect_family"),
    "miss_distance_m": _float_attr(effect, "miss_distance_m"),
    "closure_mps": _float_attr(effect, "closure_mps"),
    "quality": _float_attr(effect, "quality"),
    "confidence": _float_attr(effect, "confidence"),
    "spatial_effect_scale": _float_attr(effect, "spatial_effect_scale"),
    "mechanism_armor_scale": _float_attr(effect, "mechanism_armor_scale"),
    "mechanism_exposure_scale": _float_attr(effect, "mechanism_exposure_scale"),
    "mechanism_effect_scale": _float_attr(effect, "mechanism_effect_scale"),
    "component_threshold_scale": _float_attr(effect, "component_threshold_scale"),
    "projected_hitbox_count": _int_attr(effect, "projected_hitbox_count"),
    "warhead_spatial_hit_estimate": _float_attr(effect, "warhead_spatial_hit_estimate"),
    "warhead_spatial_hit_fraction": _float_attr(effect, "warhead_spatial_hit_fraction"),
    "warhead_spatial_energy_scale": _float_attr(effect, "warhead_spatial_energy_scale"),
    "warhead_spatial_pattern_scale": _float_attr(effect, "warhead_spatial_pattern_scale"),
    "warhead_orientation_pattern_scale": _float_attr(
      effect,
      "warhead_orientation_pattern_scale",
    ),
    "component_hit_count": _int_attr(effect, "component_hit_count"),
    "component_failure_count": _int_attr(effect, "component_failure_count"),
    "component_response_row_count": len(response_rows),
    "component_failure_probability": _float_attr(effect, "component_failure_probability"),
    "component_primary_name": _str_attr(effect, "component_primary_name"),
    "component_primary_system": _str_attr(effect, "component_primary_system"),
    "component_primary_integrity": _float_attr(effect, "component_primary_integrity"),
    "component_max_failure_probability": (
      _float_attr(max_probability_row, "failure_probability")
      if max_probability_row is not None
      else None
    ),
    "component_max_failure_probability_component_name": (
      _str_attr(max_probability_row, "component_name")
      if max_probability_row is not None
      else ""
    ),
    "component_max_failure_probability_effect_scale": max_probability_effect_scale,
    "fragment_energy_j": _float_attr(effect, "mechanism_fragment_energy_j"),
    "fragment_density_per_m2": _float_attr(
      effect,
      "mechanism_fragment_areal_density_per_m2",
    ),
    "blast_overpressure_kpa": _float_attr(effect, "mechanism_blast_overpressure_kpa"),
    "blast_impulse_kpa_ms": _float_attr(effect, "mechanism_blast_impulse_kpa_ms"),
    "penetration_margin": _float_attr(effect, "mechanism_penetration_margin"),
    "rod_cut_margin": _float_attr(effect, "mechanism_rod_cut_margin"),
    "vulnerability_family_scale": _float_attr(effect, "vulnerability_family_scale"),
    "vulnerability_aspect_scale": _float_attr(effect, "vulnerability_aspect_scale"),
    "vulnerability_closure_scale": _float_attr(effect, "vulnerability_closure_scale"),
    "vulnerability_miss_distance_scale": _float_attr(
      effect,
      "vulnerability_miss_distance_scale",
    ),
    "vulnerability_effect_scale": _float_attr(effect, "vulnerability_effect_scale"),
  }


def _component_load_factor_rows(
  effect: Any | None,
  effect_summary: dict[str, Any],
  *,
  case_id: str,
) -> list[dict[str, Any]]:
  if effect is None:
    return []
  rows = list(getattr(effect, "component_mechanism_load_rows", []) or [])
  case_spatial = _finite_or_none(effect_summary.get("spatial_effect_scale"))
  case_armor = _finite_or_none(effect_summary.get("mechanism_armor_scale"))
  case_exposure = _finite_or_none(effect_summary.get("mechanism_exposure_scale"))
  case_mechanism = _finite_or_none(effect_summary.get("mechanism_effect_scale"))
  load_factor_product = _product_or_none((case_spatial, case_armor, case_exposure))

  out: list[dict[str, Any]] = []
  for index, row in enumerate(rows):
    effect_scale = _float_attr(row, "effect_scale")
    residual_to_product = (
      float(effect_scale) - float(load_factor_product)
      if effect_scale is not None and load_factor_product is not None
      else None
    )
    residual_to_spatial = (
      float(effect_scale) - float(case_spatial)
      if effect_scale is not None and case_spatial is not None
      else None
    )
    factor_row = {
      "case_id": str(case_id),
      "row_index": int(index),
      "component_name": _str_attr(row, "component_name"),
      "component_system": _str_attr(row, "component_system"),
      "direct_hit": _bool_attr(row, "direct_hit"),
      "distance_m": _float_attr(row, "distance_m"),
      "effect_scale": effect_scale,
      "fragment_energy_j": _float_attr(row, "mechanism_fragment_energy_j"),
      "fragment_density_per_m2": _float_attr(
        row,
        "mechanism_fragment_areal_density_per_m2",
      ),
      "penetration_margin": _float_attr(row, "mechanism_penetration_margin"),
      "blast_overpressure_kpa": _float_attr(row, "mechanism_blast_overpressure_kpa"),
      "blast_impulse_kpa_ms": _float_attr(row, "mechanism_blast_impulse_kpa_ms"),
      "blast_scaled_distance_m_kg13": _float_attr(
        row,
        "mechanism_blast_scaled_distance_m_kg13",
      ),
      "rod_cut_margin": _float_attr(row, "mechanism_rod_cut_margin"),
      "surface_incidence_cos": _float_attr(row, "mechanism_surface_incidence_cos"),
      "case_spatial_effect_scale": case_spatial,
      "case_mechanism_armor_scale": case_armor,
      "case_mechanism_exposure_scale": case_exposure,
      "case_mechanism_effect_scale": case_mechanism,
      "load_factor_product_proxy": load_factor_product,
      "effect_scale_minus_load_factor_product_proxy": residual_to_product,
      "effect_scale_ratio_to_load_factor_product_proxy": _safe_ratio(
        effect_scale,
        load_factor_product,
      ),
      "effect_scale_minus_case_spatial_effect_scale": residual_to_spatial,
      "effect_scale_ratio_to_case_spatial_effect_scale": _safe_ratio(
        effect_scale,
        case_spatial,
      ),
      "residual_proxy_formula": "effect_scale - spatial_effect_scale * mechanism_armor_scale * mechanism_exposure_scale",
      "authority_boundary": {
        "runtime_parameter_retuning": False,
        "calibration_authority": False,
      },
    }
    factor_row["load_only_fields"] = _present_fields(
      factor_row,
      LOAD_ONLY_COMPONENT_FIELDS,
    )
    factor_row["response_fields"] = _load_row_response_fields(factor_row)
    factor_row["aggregate_coupled_load_fields"] = _present_fields(
      factor_row,
      AGGREGATE_COUPLED_COMPONENT_LOAD_FIELDS,
    )
    factor_row["response_owner_violation_fields"] = list(factor_row["response_fields"])
    factor_row["field_boundary_status"] = "diagnostic_boundary_only"
    out.append(factor_row)
  return out


def _component_load_factor_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
  def finite_values(field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
      value = _finite_or_none(row.get(field))
      if value is not None:
        values.append(float(value))
    return values

  def max_row(field: str) -> dict[str, Any] | None:
    candidates = [
      row for row in rows if _finite_or_none(row.get(field)) is not None
    ]
    if not candidates:
      return None
    return max(candidates, key=lambda row: float(row[field]))

  residuals = [abs(value) for value in finite_values("effect_scale_minus_load_factor_product_proxy")]
  effect_scales = finite_values("effect_scale")
  response_violation_counts: dict[str, int] = {}
  for row in rows:
    for field in list(row.get("response_owner_violation_fields", []) or []):
      key = str(field)
      response_violation_counts[key] = response_violation_counts.get(key, 0) + 1
  max_effect_row = max_row("effect_scale")
  max_residual_row = max(
    (
      row
      for row in rows
      if _finite_or_none(row.get("effect_scale_minus_load_factor_product_proxy")) is not None
    ),
    key=lambda row: abs(float(row["effect_scale_minus_load_factor_product_proxy"])),
    default=None,
  )
  return {
    "row_count": len(rows),
    "effect_scale_min": min(effect_scales) if effect_scales else None,
    "effect_scale_max": max(effect_scales) if effect_scales else None,
    "load_only_field_names_present": sorted(
      {
        str(field)
        for row in rows
        for field in list(row.get("load_only_fields", []) or [])
      }
    ),
    "response_field_names_present_on_load_rows": sorted(
      {
        str(field)
        for row in rows
        for field in list(row.get("response_fields", []) or [])
      }
    ),
    "aggregate_coupled_load_field_names_present": sorted(
      {
        str(field)
        for row in rows
        for field in list(row.get("aggregate_coupled_load_fields", []) or [])
      }
    ),
    "rows_with_response_fields_on_load_row": int(
      sum(1 for row in rows if list(row.get("response_fields", []) or []))
    ),
    "response_owner_violation_field_counts": dict(sorted(response_violation_counts.items())),
    "field_boundary_status": "diagnostic_boundary_only",
    "mean_abs_effect_scale_residual_to_load_factor_product_proxy": (
      sum(residuals) / len(residuals) if residuals else None
    ),
    "max_abs_effect_scale_residual_to_load_factor_product_proxy": (
      max(residuals) if residuals else None
    ),
    "max_effect_scale_component_name": (
      str(max_effect_row.get("component_name", "") or "")
      if max_effect_row is not None
      else ""
    ),
    "max_residual_component_name": (
      str(max_residual_row.get("component_name", "") or "")
      if max_residual_row is not None
      else ""
    ),
    "residual_proxy_formula": "effect_scale - spatial_effect_scale * mechanism_armor_scale * mechanism_exposure_scale",
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "calibration_authority": False,
      "real_world_pk": False,
    },
  }


def _stage_observed(
  stage_diagnostics: dict[str, Any],
  abstraction_stage: str,
) -> dict[str, Any]:
  for row in list(stage_diagnostics.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == str(abstraction_stage):
      return dict(row.get("observed", {}) or {})
  return {}


def _runtime_component_load_rows(runtime_facade: Any) -> list[dict[str, Any]]:
  warhead_load = getattr(runtime_facade, "warhead_load_field", None)
  rows = list(getattr(warhead_load, "component_loads", []) or [])
  return [
    {
      "owner_stage": _str_attr(row, "owner_stage", "warhead_load_field"),
      "source_current_owner_stage": "component_load_row",
      "source_row_index": int(index),
      "component_name": _str_attr(row, "component_name"),
      "component_system": _str_attr(row, "component_system"),
      "component_redundancy_group_id": _str_attr(
        row,
        "component_redundancy_group_id",
      ),
      "direct_hit": _bool_attr(row, "direct_hit"),
      "distance_m": _float_attr(row, "distance_m"),
      "effect_scale": _float_attr(row, "effect_scale"),
      "spatial_intersection_fraction": _float_attr(
        row,
        "spatial_intersection_fraction",
      ),
      "pattern_weight": _float_attr(row, "pattern_weight"),
      "orientation_weight": _float_attr(row, "orientation_weight"),
      "receiver_exposure_fraction": _float_attr(
        row,
        "receiver_exposure_fraction",
      ),
      "armor_transmission": _float_attr(row, "armor_transmission"),
      "sampling_confidence": _float_attr(row, "sampling_confidence"),
      "load_intensity_scale": _float_attr(row, "load_intensity_scale"),
      "fragment_energy_j": _float_attr(row, "fragment_energy_j"),
      "fragment_areal_density_per_m2": _float_attr(
        row,
        "fragment_areal_density_per_m2",
      ),
      "penetration_margin": _float_attr(row, "penetration_margin"),
      "blast_overpressure_kpa": _float_attr(row, "blast_overpressure_kpa"),
      "blast_impulse_kpa_ms": _float_attr(row, "blast_impulse_kpa_ms"),
      "blast_scaled_distance_m_kg13": _float_attr(
        row,
        "blast_scaled_distance_m_kg13",
      ),
      "rod_cut_margin": _float_attr(row, "rod_cut_margin"),
      "surface_incidence_cos": _float_attr(row, "surface_incidence_cos"),
    }
    for index, row in enumerate(rows)
  ]


def _runtime_component_response_rows(runtime_facade: Any) -> list[dict[str, Any]]:
  rows = list(getattr(runtime_facade, "component_responses", []) or [])
  out: list[dict[str, Any]] = []
  for index, row in enumerate(rows):
    before = _float_attr(row, "integrity_before")
    after = _float_attr(row, "integrity_after")
    integrity_delta = (
      float(after) - float(before)
      if before is not None and after is not None
      else None
    )
    out.append(
      {
        "owner_stage": _str_attr(row, "owner_stage", "component_response"),
        "source_current_owner_stage": _str_attr(
          row,
          "source_current_owner_stage",
          "component_response_row",
        ),
        "source_row_index": _int_attr(row, "source_row_index", index),
        "component_name": _str_attr(row, "component_name"),
        "component_system": _str_attr(row, "component_system"),
        "component_redundancy_group_id": _str_attr(
          row,
          "component_redundancy_group_id",
        ),
        "component_threshold_scale": _float_attr(row, "threshold_scale"),
        "failure_probability": _float_attr(row, "failure_probability"),
        "failure_sample": _float_attr(row, "failure_sample"),
        "failure_probability_source": _str_attr(row, "failure_probability_source"),
        "failure_probability_calibrated": _bool_attr(
          row,
          "failure_probability_calibrated",
        ),
        "failure_mode": _str_attr(row, "failure_mode"),
        "failure_severity": _float_attr(row, "failure_severity"),
        "integrity_before": before,
        "integrity_after": after,
        "integrity_delta": integrity_delta,
        "owner_boundary_status": "runtime_dto_owner",
      }
    )
  return out


def _runtime_component_response_scalar_ledger(
  runtime_facade: dict[str, Any] | None,
  *,
  episode: int,
  chain_id: int,
) -> list[dict[str, Any]]:
  if not runtime_facade:
    return []
  rows = list(runtime_facade.get("component_responses", []) or [])
  out: list[dict[str, Any]] = []
  for row in rows:
    probability = _finite_or_none(row.get("failure_probability"))
    if probability is not None:
      out.append(
        {
          "schema_version": SCALAR_LEDGER_SCHEMA_VERSION,
          "episode": int(episode),
          "chain_id": int(chain_id),
          "scalar_id": "component_response.failure_probability",
          "current_owner_stage": "component_response",
          "intended_owner_stage": "component_response",
          "producer_stage": "component_response",
          "producer_field": "failure_probability",
          "observed_value": float(probability),
          "observed_value_kind": "float",
          "semantic_role": "runtime component response-row failure probability",
          "consumer_fields": [
            "component_response.sampled_failure",
            "consequence_projection.system_delta",
          ],
          "coupling_flags": [],
          "migration_hint": "runtime owner row; do not infer from component load row",
          "calibration_ready": True,
        }
      )
    before = _finite_or_none(row.get("integrity_before"))
    after = _finite_or_none(row.get("integrity_after"))
    if before is not None and after is not None:
      out.append(
        {
          "schema_version": SCALAR_LEDGER_SCHEMA_VERSION,
          "episode": int(episode),
          "chain_id": int(chain_id),
          "scalar_id": "component_response.integrity_delta",
          "current_owner_stage": "component_response",
          "intended_owner_stage": "component_response",
          "producer_stage": "component_response",
          "producer_field": "integrity_after-before",
          "observed_value": float(after) - float(before),
          "observed_value_kind": "float",
          "semantic_role": "runtime component response-row integrity state change",
          "consumer_fields": ["consequence_projection.system_delta"],
          "coupling_flags": [],
          "migration_hint": "runtime owner row; retain as response state fact",
          "calibration_ready": True,
        }
      )
  return out


def _runtime_facade(effect: Any | None) -> dict[str, Any]:
  base = {
    "schema_name": RUNTIME_FACADE_SCHEMA_VERSION,
    "schema_version": 1,
    "runtime_dto_available": False,
    "runtime_dto_authority": False,
    "runtime_parameter_retuning": False,
    "calibration_authority": False,
    "real_world_pk": False,
    "component_load_row_count": 0,
    "component_response_row_count": 0,
  }
  if effect is None or not hasattr(ef_py, "make_kill_chain_runtime_facade"):
    return base

  facade = ef_py.make_kill_chain_runtime_facade(effect)
  approach = getattr(facade, "approach_fact", None)
  fuze = getattr(facade, "fuze_decision", None)
  warhead = getattr(facade, "warhead_load_field", None)
  susceptibility = getattr(facade, "target_susceptibility", None)
  consequence = getattr(facade, "consequence_projection", None)
  component_loads = _runtime_component_load_rows(facade)
  component_responses = _runtime_component_response_rows(facade)

  return {
    **base,
    "schema_name": _str_attr(facade, "schema_name", RUNTIME_FACADE_SCHEMA_VERSION),
    "schema_version": _int_attr(facade, "schema_version", 1),
    "runtime_dto_available": True,
    "runtime_dto_authority": _bool_attr(facade, "runtime_dto_authority", True),
    "runtime_parameter_retuning": _bool_attr(facade, "runtime_parameter_retuning"),
    "calibration_authority": _bool_attr(facade, "calibration_authority"),
    "real_world_pk": _bool_attr(facade, "real_world_pk"),
    "component_load_row_count": len(component_loads),
    "component_response_row_count": len(component_responses),
    "approach_fact": {
      "owner_stage": _str_attr(approach, "owner_stage", "approach"),
      "closest_distance_m": _float_attr(approach, "closest_distance_m"),
      "closest_point_local_forward_m": _float_attr(
        approach,
        "closest_point_local_forward_m",
      ),
      "closest_point_local_right_m": _float_attr(
        approach,
        "closest_point_local_right_m",
      ),
      "closest_point_local_up_m": _float_attr(
        approach,
        "closest_point_local_up_m",
      ),
      "closure_mps": _float_attr(approach, "closure_mps"),
      "nearest_approach_time_s": _float_attr(approach, "nearest_approach_time_s"),
    },
    "fuze_decision": {
      "owner_stage": _str_attr(fuze, "owner_stage", "fuze_decision"),
      "fuze_type": _str_attr(fuze, "fuze_type"),
      "detonated": _bool_attr(fuze, "detonated"),
      "outcome_state": _str_attr(fuze, "outcome_state"),
      "detonation_time_s": _float_attr(fuze, "detonation_time_s"),
      "detonation_probability": _float_attr(fuze, "detonation_probability"),
      "fuze_quality": _float_attr(fuze, "fuze_quality"),
      "sensor_opportunity_score": _float_attr(fuze, "sensor_opportunity_score"),
      "terminal_track_valid": _bool_attr(fuze, "terminal_track_valid"),
      "target_detected": _bool_attr(fuze, "target_detected"),
      "target_detection_confidence": _float_attr(
        fuze,
        "target_detection_confidence",
      ),
      "target_detection_threshold": _float_attr(
        fuze,
        "target_detection_threshold",
      ),
      "detonation_point_source": _str_attr(fuze, "detonation_point_source"),
    },
    "warhead_load_field": {
      "owner_stage": _str_attr(warhead, "owner_stage", "warhead_load_field"),
      "effect_family": _str_attr(warhead, "effect_family"),
      "warhead_mass_kg": _float_attr(warhead, "warhead_mass_kg"),
      "lethal_radius_m": _float_attr(warhead, "lethal_radius_m"),
      "spatial_effect_scale": _float_attr(warhead, "spatial_effect_scale"),
      "armor_transmission": _float_attr(warhead, "armor_transmission"),
      "receiver_exposure_fraction": _float_attr(
        warhead,
        "receiver_exposure_fraction",
      ),
      "mechanism_effect_scale": _float_attr(warhead, "mechanism_effect_scale"),
      "projected_hitbox_count": _int_attr(warhead, "projected_hitbox_count"),
      "spatial_sample_count": _int_attr(warhead, "spatial_sample_count"),
      "spatial_hit_estimate": _float_attr(warhead, "spatial_hit_estimate"),
      "spatial_hit_fraction": _float_attr(warhead, "spatial_hit_fraction"),
      "spatial_energy_scale": _float_attr(warhead, "spatial_energy_scale"),
      "spatial_pattern_scale": _float_attr(warhead, "spatial_pattern_scale"),
      "orientation_pattern_scale": _float_attr(
        warhead,
        "orientation_pattern_scale",
      ),
      "fragment_energy_j": _float_attr(warhead, "fragment_energy_j"),
      "fragment_areal_density_per_m2": _float_attr(
        warhead,
        "fragment_areal_density_per_m2",
      ),
      "penetration_margin": _float_attr(warhead, "penetration_margin"),
      "blast_overpressure_kpa": _float_attr(warhead, "blast_overpressure_kpa"),
      "blast_impulse_kpa_ms": _float_attr(warhead, "blast_impulse_kpa_ms"),
      "blast_scaled_distance_m_kg13": _float_attr(
        warhead,
        "blast_scaled_distance_m_kg13",
      ),
      "rod_cut_margin": _float_attr(warhead, "rod_cut_margin"),
      "surface_incidence_cos": _float_attr(warhead, "surface_incidence_cos"),
      "component_loads": component_loads,
    },
    "target_susceptibility": {
      "owner_stage": _str_attr(
        susceptibility,
        "owner_stage",
        "target_susceptibility",
      ),
      "vulnerability_profile_present": _bool_attr(
        susceptibility,
        "vulnerability_profile_present",
      ),
      "vulnerability_profile_synthetic": _bool_attr(
        susceptibility,
        "vulnerability_profile_synthetic",
        True,
      ),
      "calibrated_evidence": _bool_attr(susceptibility, "calibrated_evidence"),
      "pk_authority": _bool_attr(susceptibility, "pk_authority"),
      "deterministic_fuze_authority": _bool_attr(
        susceptibility,
        "deterministic_fuze_authority",
      ),
      "calibration_status": _str_attr(susceptibility, "calibration_status"),
      "aspect_bucket": _str_attr(susceptibility, "aspect_bucket"),
      "family_scale": _float_attr(susceptibility, "family_scale"),
      "aspect_scale": _float_attr(susceptibility, "aspect_scale"),
      "closure_scale": _float_attr(susceptibility, "closure_scale"),
      "miss_distance_scale": _float_attr(susceptibility, "miss_distance_scale"),
      "effect_scale": _float_attr(susceptibility, "effect_scale"),
    },
    "component_responses": component_responses,
    "component_response": {
      "owner_stage": "component_response",
      "rows": component_responses,
      "row_count": len(component_responses),
      "probability_owner_source": "effects_event_component_response_rows",
    },
    "consequence_projection": {
      "owner_stage": _str_attr(
        consequence,
        "owner_stage",
        "consequence_projection",
      ),
      "outcome_state": _str_attr(consequence, "outcome_state"),
      "component_hit_count": _int_attr(consequence, "component_hit_count"),
      "component_failure_count": _int_attr(consequence, "component_failure_count"),
      "primary_component_name": _str_attr(consequence, "primary_component_name"),
      "primary_component_system": _str_attr(consequence, "primary_component_system"),
      "primary_component_integrity": _float_attr(
        consequence,
        "primary_component_integrity",
      ),
      "redundancy_group_availability": _float_attr(
        consequence,
        "redundancy_group_availability",
      ),
      "air_system_hit_flags": _str_attr(consequence, "air_system_hit_flags"),
      "air_system_spatial_scales": _str_attr(
        consequence,
        "air_system_spatial_scales",
      ),
      "vulnerability_scale_trace": _str_attr(
        consequence,
        "vulnerability_scale_trace",
      ),
    },
  }


def _decoupled_facade(
  *,
  stage_diagnostics: dict[str, Any],
  effect_summary: dict[str, Any],
  component_load_factor_rows: list[dict[str, Any]],
  runtime_facade: dict[str, Any],
) -> dict[str, Any]:
  runtime_available = bool(runtime_facade.get("runtime_dto_available"))
  component_response_rows = list(runtime_facade.get("component_responses", []) or [])
  component_load_rows = list(
    runtime_facade.get("warhead_load_field", {}).get("component_loads", []) or []
  )
  return {
    "schema_version": FACADE_SCHEMA_VERSION,
    "facade_status": (
      "runtime_dto_backed"
      if runtime_available
      else "runtime_dto_unavailable"
    ),
    "runtime_facade_schema_name": runtime_facade.get("schema_name"),
    "runtime_facade_schema_version": runtime_facade.get("schema_version"),
    "authority_boundary": {
      "runtime_dto_authority": bool(runtime_facade.get("runtime_dto_authority")),
      "runtime_parameter_retuning": False,
      "calibration_authority": False,
      "real_world_pk": False,
    },
    "approach_fact": {
      "owner_stage": "approach",
      "observed": _stage_observed(stage_diagnostics, "approach"),
    },
    "fuze_decision": {
      "owner_stage": "fuze_decision",
      "observed": _stage_observed(stage_diagnostics, "fuze_decision"),
    },
    "warhead_load_field": {
      "owner_stage": "warhead_load_field",
      "observed": _stage_observed(stage_diagnostics, "warhead_load_field"),
      "runtime_component_loads": component_load_rows,
      "runtime_component_load_row_count": len(component_load_rows),
      "component_load_factor_row_count": len(component_load_factor_rows),
      "aggregate_effect_scale_available": True,
      "load_only_field_names_present": sorted(
        {
          str(field)
          for row in component_load_factor_rows
          for field in list(row.get("load_only_fields", []) or [])
        }
      ),
    },
    "component_response": {
      "owner_stage": "component_response",
      "rows": component_response_rows,
      "row_count": len(component_response_rows),
      "probability_owner_source": "effects_event_component_response_rows",
      "runtime_dto_authority": bool(runtime_facade.get("runtime_dto_authority")),
    },
    "consequence_projection": {
      "owner_stage": "consequence_projection",
      "observed": _stage_observed(stage_diagnostics, "consequence_projection"),
    },
    "effect_summary_event_id": effect_summary.get("event_id"),
  }


def _facade_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
  component_response_rows = [
    row
    for case in cases
    for row in list(
      case.get("decoupled_facade", {})
      .get("component_response", {})
      .get("rows", [])
      or []
    )
  ]
  runtime_facades = [
    dict(case.get("runtime_facade", {}) or {})
    for case in cases
    if dict(case.get("runtime_facade", {}) or {}).get("runtime_dto_available")
  ]
  runtime_facades_with_response_rows = [
    facade
    for facade in runtime_facades
    if int(facade.get("component_response_row_count", 0) or 0) > 0
  ]
  return {
    "schema_version": FACADE_SCHEMA_VERSION,
    "runtime_facade_schema_version": RUNTIME_FACADE_SCHEMA_VERSION,
    "case_count": len(cases),
    "component_response_row_count": len(component_response_rows),
    "runtime_facade_case_count": len(runtime_facades),
    "runtime_response_rows_available": bool(runtime_facades_with_response_rows),
    "facade_status": (
      "runtime_dto_backed"
      if cases and len(runtime_facades) == len(cases)
      else "runtime_dto_unavailable"
    ),
    "authority_boundary": {
      "runtime_dto_authority": bool(runtime_facades),
      "runtime_parameter_retuning": False,
      "calibration_authority": False,
    },
  }


def _stage_report_has_required_stages(case: dict[str, Any]) -> bool:
  stages = {
    str(row.get("abstraction_stage", "") or "")
    for row in list(case.get("stage_abstractions", []) or [])
  }
  return {
    "approach",
    "fuze_decision",
    "warhead_load_field",
    "component_response",
    "consequence_projection",
  }.issubset(stages)


def _case_has_no_legacy_fuze_damage_multiplier_surface(case: dict[str, Any]) -> bool:
  effect = dict(case.get("effect", {}) or {})
  runtime_facade = dict(case.get("runtime_facade", {}) or {})
  serialized = json.dumps(
    {
      "effect": effect,
      "runtime_facade": runtime_facade,
    },
    sort_keys=True,
  )
  legacy_tokens = (
    "fuze_quality_damage_multiplier",
    "warhead_damage_scalar_before_fuze_quality",
    "warhead_damage_scalar_after_fuze_quality",
  )
  return not any(token in serialized for token in legacy_tokens)


def _display_repo_path(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT))
  except Exception:
    return str(path)


def _external_calibration_evidence_status(
  report_path: Path | str | None,
) -> dict[str, Any]:
  if report_path is None or not str(report_path).strip():
    return {
      "source_ref": "",
      "report_available": False,
      "report_schema_version": "",
      "record_count": 0,
      "decision_counts": {},
      "admitted_record_count": 0,
      "admitted_authority_fields": [],
      "missing_authority_fields": [],
      "layer_gap_summary": [],
      "evidence_unblock_queue": [],
      "external_calibration_evidence_present": False,
      "blocked_by": ["external_calibration_evidence_report_not_configured"],
    }

  path = Path(report_path)
  if not path.is_absolute():
    path = REPO_ROOT / path
  source_ref = _display_repo_path(path)
  if not path.exists():
    return {
      "source_ref": source_ref,
      "report_available": False,
      "report_schema_version": "",
      "record_count": 0,
      "decision_counts": {},
      "admitted_record_count": 0,
      "admitted_authority_fields": [],
      "missing_authority_fields": [],
      "layer_gap_summary": [],
      "evidence_unblock_queue": [],
      "external_calibration_evidence_present": False,
      "blocked_by": ["external_calibration_evidence_report_missing"],
    }

  try:
    payload = json.loads(path.read_text(encoding="utf-8"))
  except Exception as exc:
    return {
      "source_ref": source_ref,
      "report_available": True,
      "report_schema_version": "",
      "record_count": 0,
      "decision_counts": {},
      "admitted_record_count": 0,
      "admitted_authority_fields": [],
      "missing_authority_fields": [],
      "layer_gap_summary": [],
      "evidence_unblock_queue": [],
      "external_calibration_evidence_present": False,
      "blocked_by": [f"external_calibration_evidence_report_unreadable:{type(exc).__name__}"],
    }
  if not isinstance(payload, dict):
    return {
      "source_ref": source_ref,
      "report_available": True,
      "report_schema_version": "",
      "record_count": 0,
      "decision_counts": {},
      "admitted_record_count": 0,
      "admitted_authority_fields": [],
      "missing_authority_fields": [],
      "layer_gap_summary": [],
      "evidence_unblock_queue": [],
      "external_calibration_evidence_present": False,
      "blocked_by": ["external_calibration_evidence_report_not_object"],
    }

  decision_counts = dict(payload.get("decision_counts", {}) or {})
  authority_boundary = dict(payload.get("authority_boundary", {}) or {})
  decisions = [
    dict(row)
    for row in list(payload.get("decisions", []) or [])
    if isinstance(row, dict)
  ]
  engineering_proxy_records = [
    row for row in decisions
    if str(row.get("classification", "") or "") in {
      "engineering_proxy",
      "retained_non_authoritative",
    }
    and str(row.get("gate_status", "") or "") in {"not_requested", "passed", ""}
  ]
  engineering_proxy_layer_ids = [
    layer_id for layer_id, _owner_stage, _scope, _evidence, _authorities in CALIBRATION_LAYER_SPECS
  ] if engineering_proxy_records else []
  admitted_from_counts = int(decision_counts.get("admitted", 0) or 0)
  admitted_from_boundary = int(
    authority_boundary.get("admitted_record_count", admitted_from_counts) or 0
  )
  admitted_count = max(admitted_from_counts, admitted_from_boundary)
  admitted_authority_fields = sorted(
    {
      str(row.get("authority_field", "") or "")
      for row in list(payload.get("admitted_authorities", []) or [])
      if isinstance(row, dict) and str(row.get("authority_field", "") or "")
    }
  )
  blockers: list[str] = []
  real_world_authority_blockers: list[str] = []
  schema = str(payload.get("schema_version", "") or "")
  if schema != MLF10_CALIBRATION_ADMISSION_REPORT_SCHEMA_VERSION:
    blockers.append("external_calibration_evidence_report_schema_invalid")
    real_world_authority_blockers.append("external_calibration_evidence_report_schema_invalid")
  if admitted_count <= 0:
    real_world_authority_blockers.append("no_admitted_external_calibration_evidence")
  if admitted_count > 0 and not admitted_authority_fields:
    blockers.append("admitted_external_evidence_without_authority_fields")
    real_world_authority_blockers.append("admitted_external_evidence_without_authority_fields")
  if engineering_proxy_records:
    blockers = [
      blocker for blocker in blockers
      if blocker != "no_admitted_external_calibration_evidence"
    ]
  layer_gap_summary = _external_evidence_layer_gap_summary(
    payload,
    admitted_authority_fields=set(admitted_authority_fields),
  )
  missing_authority_fields = sorted(
    {
      field
      for row in layer_gap_summary
      for field in list(row.get("missing_authority_fields", []) or [])
    }
  )

  return {
    "source_ref": source_ref,
    "report_available": True,
    "report_schema_version": schema,
    "source_manifest_ref": str(payload.get("source_manifest_ref", "") or ""),
    "record_count": int(payload.get("record_count", 0) or 0),
    "decision_counts": decision_counts,
    "admitted_record_count": admitted_count,
    "admitted_authority_fields": admitted_authority_fields,
    "missing_authority_fields": missing_authority_fields,
    "layer_gap_summary": layer_gap_summary,
    "evidence_unblock_queue": _external_evidence_unblock_queue(payload),
    "engineering_proxy_evidence_present": bool(engineering_proxy_records),
    "engineering_proxy_record_count": len(engineering_proxy_records),
    "engineering_proxy_record_ids": [
      str(row.get("evidence_id", "") or "")
      for row in engineering_proxy_records
      if str(row.get("evidence_id", "") or "")
    ],
    "engineering_proxy_layer_ids": engineering_proxy_layer_ids,
    "engineering_proxy_admission_mode": (
      "repository_engineering_proxy"
      if engineering_proxy_records else "not_available"
    ),
    "real_world_authority_blocked_by": sorted(set(real_world_authority_blockers)),
    "external_calibration_evidence_present": bool(engineering_proxy_records) or not blockers,
    "blocked_by": blockers,
  }


def _authority_to_layer_map() -> dict[str, dict[str, str]]:
  mapping: dict[str, dict[str, str]] = {}
  for layer_id, owner_stage, _scope, _evidence, required_authorities in CALIBRATION_LAYER_SPECS:
    for authority in required_authorities:
      mapping[str(authority)] = {
        "layer_id": str(layer_id),
        "owner_stage": str(owner_stage),
      }
  return mapping


def _external_evidence_unblock_queue(payload: dict[str, Any]) -> list[dict[str, Any]]:
  authority_to_layer = _authority_to_layer_map()
  decisions = [
    dict(row)
    for row in list(payload.get("decisions", []) or [])
    if isinstance(row, dict)
  ]
  queue: list[dict[str, Any]] = []
  for decision in decisions:
    classification = str(decision.get("classification", "") or "")
    if classification not in {"blocked", "rejected"}:
      continue
    authority_decisions = dict(decision.get("authority_decisions", {}) or {})
    requested_authority_fields: list[str] = []
    target_layer_ids: list[str] = []
    target_stage_ids: list[str] = []
    authority_blockers: set[str] = set()
    for authority, authority_decision_raw in authority_decisions.items():
      authority_name = str(authority or "")
      if authority_name not in authority_to_layer:
        continue
      authority_decision = dict(authority_decision_raw or {})
      requested = bool(authority_decision.get("requested"))
      decision_name = str(authority_decision.get("decision", "") or "")
      if not requested and decision_name == "not_requested":
        continue
      requested_authority_fields.append(authority_name)
      target_layer_ids.append(authority_to_layer[authority_name]["layer_id"])
      target_stage_ids.append(authority_to_layer[authority_name]["owner_stage"])
      for reason in list(authority_decision.get("reasons", []) or []):
        if str(reason or ""):
          authority_blockers.add(str(reason))
    if not requested_authority_fields:
      continue

    blocking_reasons = {
      str(reason)
      for reason in list(decision.get("blocking_reasons", []) or [])
      if str(reason or "")
    }
    all_reasons = sorted(blocking_reasons | authority_blockers)
    residuals = [
      str(residual)
      for residual in list(decision.get("residuals", []) or [])
      if str(residual or "")
    ]
    unblock_actions = [
      {
        "reason": reason,
        "required_closeout": EVIDENCE_UNBLOCK_ACTIONS.get(
          reason, "replace or re-audit evidence for this blocker"
        ),
      }
      for reason in all_reasons
    ]
    if residuals and "blocking_residuals_open" not in all_reasons:
      unblock_actions.append(
        {
          "reason": "residuals_present",
          "required_closeout": "close listed residuals before admission",
        }
      )

    queue.append(
      {
        "evidence_id": str(decision.get("evidence_id", "") or ""),
        "classification": classification,
        "gate_status": str(decision.get("gate_status", "") or ""),
        "target_layer_ids": sorted(set(target_layer_ids)),
        "target_stage_ids": sorted(set(target_stage_ids)),
        "requested_authority_fields": sorted(set(requested_authority_fields)),
        "blocking_reasons": all_reasons,
        "residuals": residuals,
        "unblock_actions": unblock_actions,
        "replacement_required": classification == "rejected",
        "admission_candidate_after_closeout": classification == "blocked",
        "open_item_count": len(all_reasons) + len(residuals),
      }
    )

  return sorted(
    queue,
    key=lambda row: (
      int(row.get("open_item_count", 0) or 0),
      ",".join(list(row.get("target_layer_ids", []) or [])),
      str(row.get("evidence_id", "") or ""),
    ),
  )


def _external_evidence_layer_gap_summary(
  payload: dict[str, Any],
  *,
  admitted_authority_fields: set[str],
) -> list[dict[str, Any]]:
  decisions = [
    dict(row)
    for row in list(payload.get("decisions", []) or [])
    if isinstance(row, dict)
  ]
  out: list[dict[str, Any]] = []
  for (
    layer_id,
    owner_stage,
    _allowed_scope,
    required_evidence,
    required_authorities,
  ) in CALIBRATION_LAYER_SPECS:
    required = set(required_authorities)
    admitted_for_layer = sorted(required & admitted_authority_fields)
    missing = sorted(required - admitted_authority_fields)
    related_ids: list[str] = []
    blocked_ids: list[str] = []
    reason_counts: dict[str, int] = {}
    for decision in decisions:
      authority_decisions = dict(decision.get("authority_decisions", {}) or {})
      evidence_id = str(decision.get("evidence_id", "") or "")
      related = False
      for authority in required:
        authority_decision = dict(authority_decisions.get(authority, {}) or {})
        authority_decision_name = str(authority_decision.get("decision", "") or "")
        if (
          bool(authority_decision.get("requested"))
          or (
            authority_decision_name
            and authority_decision_name != "not_requested"
          )
        ):
          related = True
          for reason in list(authority_decision.get("reasons", []) or []):
            key = str(reason or "")
            if key:
              reason_counts[key] = reason_counts.get(key, 0) + 1
      if not related:
        continue
      if evidence_id:
        related_ids.append(evidence_id)
      if str(decision.get("classification", "") or "") in {"blocked", "rejected"}:
        if evidence_id:
          blocked_ids.append(evidence_id)
        for reason in list(decision.get("blocking_reasons", []) or []):
          key = str(reason or "")
          if key:
            reason_counts[key] = reason_counts.get(key, 0) + 1
    out.append(
      {
        "layer_id": layer_id,
        "owner_stage": owner_stage,
        "required_authority_fields": list(required_authorities),
        "admitted_authority_fields": admitted_for_layer,
        "missing_authority_fields": missing,
        "related_evidence_ids": sorted(set(related_ids)),
        "blocked_evidence_ids": sorted(set(blocked_ids)),
        "blocking_reason_counts": dict(sorted(reason_counts.items())),
        "next_required_evidence": required_evidence,
        "gap_status": "admitted" if not missing else "missing_admitted_authority",
      }
    )
  return out


def _calibration_layer_rows(
  *,
  response_fields_on_load_rows: int,
  admitted_authority_fields: set[str],
  engineering_proxy_layer_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  proxy_layers = set(engineering_proxy_layer_ids or set())
  for layer_id, owner_stage, allowed_scope, required_evidence, required_authorities in CALIBRATION_LAYER_SPECS:
    admitted_for_layer = sorted(set(required_authorities) & admitted_authority_fields)
    proxy_admitted = str(layer_id) in proxy_layers
    blockers: list[str] = []
    if not admitted_for_layer and not proxy_admitted:
      blockers.append("external_calibration_evidence_missing")
    if layer_id == "target_response_data" and response_fields_on_load_rows > 0:
      blockers.append("p5_load_rows_still_carry_response_fields")
    rows.append(
      {
        "layer_id": layer_id,
        "owner_stage": owner_stage,
        "admission_granted": not blockers,
        "allowed_parameter_scope": allowed_scope,
        "required_evidence": required_evidence,
        "required_authority_fields": list(required_authorities),
        "admitted_authority_fields": admitted_for_layer,
        "engineering_proxy_admission_granted": proxy_admitted,
        "engineering_proxy_source": (
          "repository_engineering_proxy" if proxy_admitted else ""
        ),
        "admission_source": (
          "external_authority" if admitted_for_layer
          else ("engineering_proxy" if proxy_admitted else "missing")
        ),
        "single_layer_mutation_required": True,
        "stage_report_required": True,
        "blocked_by": blockers,
      }
    )
  return rows


def _single_layer_calibration_plan(
  *,
  layer_rows: list[dict[str, Any]],
  external_evidence_status: dict[str, Any],
  stage_report_available: bool,
  legacy_fuze_multiplier_removed: bool,
  runtime_dto_authority: bool,
  component_response_rows_available: bool,
  load_response_owner_clean: bool,
) -> dict[str, Any]:
  admitted_layers = [
    row for row in layer_rows if bool(row.get("admission_granted"))
  ]
  prerequisite_blockers: list[str] = []
  if not stage_report_available:
    prerequisite_blockers.append("stage_report_missing")
  if not runtime_dto_authority:
    prerequisite_blockers.append("runtime_dto_authority_missing")
  if not component_response_rows_available:
    prerequisite_blockers.append("component_response_rows_missing")
  if not legacy_fuze_multiplier_removed:
    prerequisite_blockers.append("legacy_fuze_quality_damage_multiplier_surface_present")
  if not load_response_owner_clean:
    prerequisite_blockers.append("p5_load_rows_still_carry_response_fields")
  external_blockers = list(external_evidence_status.get("blocked_by", []) or [])
  blockers = sorted(
    {
      *prerequisite_blockers,
      *([] if admitted_layers else ["external_calibration_evidence_missing"]),
      *external_blockers,
    }
  )

  plans: list[dict[str, Any]] = []
  for row in admitted_layers:
    owner_stage = str(row.get("owner_stage", "") or "")
    frozen_stage_ids = [
      stage_id for stage_id in CALIBRATION_STAGE_IDS if stage_id != owner_stage
    ]
    plans.append(
      {
        "layer_id": str(row.get("layer_id", "") or ""),
        "owner_stage": owner_stage,
        "target_stage_id": owner_stage,
        "admitted_authority_fields": list(
          row.get("admitted_authority_fields", []) or []
        ),
        "allowed_parameter_scope": str(row.get("allowed_parameter_scope", "") or ""),
        "mutation_scope": "single_layer_only",
        "dry_run_only": True,
        "runtime_parameter_retuning": False,
        "default_database_modified": False,
        "before_after_stage_report_required": True,
        "delta_guard_schema_version": CALIBRATION_DELTA_GUARD_SCHEMA_VERSION,
        "delta_guard_required": True,
        "frozen_stage_ids": frozen_stage_ids,
        "reject_if_changed_stage_ids": frozen_stage_ids,
        "required_comparison": {
          "before_stage_report_required": True,
          "after_stage_report_required": True,
          "target_stage_delta_required": True,
          "unrelated_stage_delta_allowed": False,
        },
        "blocked_by": [],
      }
    )

  return {
    "schema_version": CALIBRATION_PLAN_SCHEMA_VERSION,
    "plan_available": bool(plans),
    "dry_run_only": True,
    "delta_guard_schema_version": CALIBRATION_DELTA_GUARD_SCHEMA_VERSION,
    "delta_guard_required": True,
    "admitted_layer_count": len(plans),
    "blocked_by": blockers,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
    "plans": plans,
  }


def external_evidence_preflight(
  report_path: Path | str | None = DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH,
) -> dict[str, Any]:
  external_status = _external_calibration_evidence_status(report_path)
  admitted_authority_fields = {
    str(field)
    for field in list(external_status.get("admitted_authority_fields", []) or [])
    if str(field)
  }
  layer_rows = _calibration_layer_rows(
    response_fields_on_load_rows=0,
    admitted_authority_fields=admitted_authority_fields,
    engineering_proxy_layer_ids=set(
      str(layer_id)
      for layer_id in list(external_status.get("engineering_proxy_layer_ids", []) or [])
    ),
  )
  admitted_layers = [
    row for row in layer_rows if bool(row.get("admission_granted"))
  ]
  missing_layers = [
    row for row in layer_rows if not bool(row.get("admission_granted"))
  ]
  unblock_queue = list(external_status.get("evidence_unblock_queue", []) or [])
  blockers = sorted(
    {
      *list(external_status.get("blocked_by", []) or []),
      *([] if admitted_layers else ["external_calibration_evidence_missing"]),
    }
  )
  return {
    "schema_version": CALIBRATION_EVIDENCE_PREFLIGHT_SCHEMA_VERSION,
    "status": "admitted_evidence_available" if admitted_layers else "blocked_or_missing_evidence",
    "source_ref": str(external_status.get("source_ref", "") or ""),
    "blocked_by": blockers,
    "external_evidence": external_status,
    "layer_admission_if_runtime_prerequisites_clean": layer_rows,
    "admitted_layer_count": len(admitted_layers),
    "missing_layer_count": len(missing_layers),
    "evidence_unblock_queue_count": len(unblock_queue),
    "next_action": (
      "run full kill-chain report and delta guard for admitted layers"
      if admitted_layers
      else "close evidence_unblock_queue items or use repository engineering proxy inputs"
    ),
    "runtime_prerequisites_assumed_clean": True,
    "simulation_run_required_for_final_admission": True,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _audit_row(
  item_id: str,
  *,
  requirement: str,
  closed: bool,
  evidence: dict[str, Any],
  blocked_by: list[str] | None = None,
  partial_surface_closed: bool = False,
  remaining_boundary: str = "",
) -> dict[str, Any]:
  blockers = sorted({str(item) for item in list(blocked_by or []) if str(item)})
  if closed:
    status = "closed"
  elif partial_surface_closed:
    status = "blocked_external_evidence"
  else:
    status = "incomplete"
  return {
    "item_id": str(item_id),
    "requirement": str(requirement),
    "status": status,
    "closed": bool(closed),
    "partial_surface_closed": bool(partial_surface_closed),
    "evidence": evidence,
    "blocked_by": blockers,
    "remaining_boundary": str(remaining_boundary),
  }


def kill_chain_completion_audit(report: dict[str, Any]) -> dict[str, Any]:
  guidance_cases = list(report.get("guidance_cases", []) or [])
  proximity_cases = list(report.get("proximity_sweep", []) or [])
  all_cases = [*guidance_cases, *proximity_cases]
  scalar_summary = dict(report.get("scalar_coupling_summary", {}) or {})
  flag_counts = dict(scalar_summary.get("coupling_flag_counts", {}) or {})
  load_summary = dict(report.get("component_load_factor_summary", {}) or {})
  facade_summary = dict(report.get("decoupled_facade_summary", {}) or {})
  admission = dict(report.get("calibration_admission", {}) or {})
  prerequisites = dict(admission.get("prerequisites", {}) or {})
  external_evidence = dict(admission.get("external_evidence", {}) or {})
  contract_surface = dict(admission.get("external_evidence_contract_surface", {}) or {})
  plan = dict(admission.get("single_layer_calibration_plan", {}) or {})

  stage_reports_closed = bool(all_cases) and all(
    _stage_report_has_required_stages(case) for case in all_cases
  )
  p0_closed = int(scalar_summary.get("scalar_count", 0) or 0) > 0 and int(
    scalar_summary.get("calibration_ready_scalar_count", 0) or 0
  ) > 0
  p1_closed = (
    int(report.get("guidance_case_count", 0) or 0) >= 4
    and int(report.get("proximity_case_count", 0) or 0) >= 7
    and stage_reports_closed
  )
  p2_closed = (
    str(facade_summary.get("runtime_facade_schema_version", "") or "")
    == RUNTIME_FACADE_SCHEMA_VERSION
    and bool(facade_summary.get("authority_boundary", {}).get("runtime_dto_authority"))
    and int(facade_summary.get("runtime_facade_case_count", 0) or 0) == len(all_cases)
  )
  p3_closed = bool(prerequisites.get("legacy_fuze_quality_damage_multiplier_removed"))
  p4_closed = int(flag_counts.get("component_load_named_factor_available", 0) or 0) > 0
  p5_closed = (
    int(load_summary.get("rows_with_response_fields_on_load_row", 0) or 0) == 0
    and int(facade_summary.get("component_response_row_count", 0) or 0) > 0
    and bool(facade_summary.get("runtime_response_rows_available"))
  )
  p6_surface_closed = (
    str(admission.get("schema_version", "") or "") == CALIBRATION_ADMISSION_SCHEMA_VERSION
    and bool(prerequisites.get("stage_report_available"))
    and bool(prerequisites.get("runtime_dto_authority"))
    and bool(prerequisites.get("component_response_rows_available"))
    and bool(prerequisites.get("legacy_fuze_quality_damage_multiplier_removed"))
    and bool(prerequisites.get("load_rows_response_owner_clean"))
    and str(plan.get("delta_guard_schema_version", "") or "")
    == CALIBRATION_DELTA_GUARD_SCHEMA_VERSION
    and "evidence_unblock_queue" in external_evidence
    and bool(contract_surface.get("contract_surface_closed"))
  )
  p6_closed = bool(admission.get("admission_granted"))
  p6_blockers = sorted(
    {
      *list(admission.get("blocked_by", []) or []),
      *list(external_evidence.get("blocked_by", []) or []),
      *list(plan.get("blocked_by", []) or []),
    }
  )

  rows = [
    _audit_row(
      "P0",
      requirement="scalar producer/owner/consumer coupling ledger exists",
      closed=p0_closed,
      evidence={
        "scalar_count": int(scalar_summary.get("scalar_count", 0) or 0),
        "calibration_ready_scalar_count": int(
          scalar_summary.get("calibration_ready_scalar_count", 0) or 0
        ),
      },
      remaining_boundary="diagnostic ledger only; no calibration authority released",
    ),
    _audit_row(
      "P1",
      requirement="guidance/proximity stage abstractions cover required baseline cases",
      closed=p1_closed,
      evidence={
        "guidance_case_count": int(report.get("guidance_case_count", 0) or 0),
        "proximity_case_count": int(report.get("proximity_case_count", 0) or 0),
        "stage_reports_closed": stage_reports_closed,
      },
      remaining_boundary="does not change default lethality result",
    ),
    _audit_row(
      "P2",
      requirement="runtime facade exposes DTO-backed kill-chain surface",
      closed=p2_closed,
      evidence={
        "runtime_facade_schema_version": str(
          facade_summary.get("runtime_facade_schema_version", "") or ""
        ),
        "runtime_dto_authority": bool(
          facade_summary.get("authority_boundary", {}).get("runtime_dto_authority")
        ),
        "runtime_facade_case_count": int(
          facade_summary.get("runtime_facade_case_count", 0) or 0
        ),
      },
      remaining_boundary="load-row response compatibility projection removed",
    ),
    _audit_row(
      "P3",
      requirement="legacy fuze-quality damage multiplier surface removed",
      closed=p3_closed,
      evidence={
        "legacy_fuze_quality_damage_multiplier_removed": bool(
          prerequisites.get("legacy_fuze_quality_damage_multiplier_removed")
        ),
      },
      remaining_boundary="does not claim deterministic fuze reliability",
    ),
    _audit_row(
      "P4",
      requirement="component load rows expose named load factors",
      closed=p4_closed,
      evidence={
        "component_load_named_factor_available": int(
          flag_counts.get("component_load_named_factor_available", 0) or 0
        ),
        "component_factor_rows": int(load_summary.get("row_count", 0) or 0),
      },
      remaining_boundary="aggregate effect_scale remains current load scalar; named factors available",
    ),
    _audit_row(
      "P5",
      requirement="component response owner migrated away from load rows",
      closed=p5_closed,
      evidence={
        "rows_with_response_fields_on_load_row": int(
          load_summary.get("rows_with_response_fields_on_load_row", 0) or 0
        ),
        "component_response_row_count": int(
          facade_summary.get("component_response_row_count", 0) or 0
        ),
        "runtime_response_rows_available": bool(
          facade_summary.get("runtime_response_rows_available")
        ),
      },
      remaining_boundary="load-row response fields and projection fallback physically removed",
    ),
    _audit_row(
      "P6",
      requirement="single-layer data calibration is admitted and guarded",
      closed=p6_closed,
      partial_surface_closed=p6_surface_closed,
      evidence={
        "admission_granted": bool(admission.get("admission_granted")),
        "admitted_record_count": int(
          external_evidence.get("admitted_record_count", 0) or 0
        ),
        "missing_authority_fields": list(
          external_evidence.get("missing_authority_fields", []) or []
        ),
        "evidence_unblock_queue_count": len(
          list(external_evidence.get("evidence_unblock_queue", []) or [])
        ),
        "engineering_proxy_evidence_present": bool(
          external_evidence.get("engineering_proxy_evidence_present")
        ),
        "engineering_proxy_record_count": int(
          external_evidence.get("engineering_proxy_record_count", 0) or 0
        ),
        "engineering_proxy_layer_ids": list(
          external_evidence.get("engineering_proxy_layer_ids", []) or []
        ),
        "single_layer_plan_available": bool(plan.get("plan_available")),
        "delta_guard_schema_version": str(
          plan.get("delta_guard_schema_version", "") or ""
        ),
        "contract_surface_schema_version": str(
          contract_surface.get("schema_version", "") or ""
        ),
        "contract_surface_closed": bool(
          contract_surface.get("contract_surface_closed")
        ),
        "supplemental_contract_authority_fields": list(
          contract_surface.get("supplemental_contract_authority_fields", []) or []
        ),
      },
      blocked_by=p6_blockers,
      remaining_boundary="engineering-proxy calibration only; real-world authority remains false",
    ),
  ]
  closed_count = sum(1 for row in rows if bool(row.get("closed")))
  incomplete_rows = [row for row in rows if not bool(row.get("closed"))]
  return {
    "schema_version": COMPLETION_AUDIT_SCHEMA_VERSION,
    "objective_ref": "kill_chain_mechanism_decoupling_analysis_20260621.P0-P6",
    "goal_complete": not incomplete_rows,
    "overall_status": "complete" if not incomplete_rows else "incomplete",
    "closed_item_count": closed_count,
    "total_item_count": len(rows),
    "blocked_item_ids": [
      str(row.get("item_id", ""))
      for row in incomplete_rows
      if str(row.get("status", "")) == "blocked_external_evidence"
    ],
    "incomplete_item_ids": [str(row.get("item_id", "")) for row in incomplete_rows],
    "items": rows,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _supplemental_contract_authority_scope(authority_field: str) -> str:
  if authority_field == "deterministic_fuze_authority":
    return "fuze_decision_model_only"
  if authority_field == "pk_authority":
    return "simulation_consequence_projection_only"
  return "unsupported"


def _layer_spec_by_id() -> dict[str, tuple[str, str, str, str, tuple[str, ...]]]:
  return {
    layer_id: (
      layer_id,
      owner_stage,
      allowed_scope,
      required_evidence,
      tuple(required_authorities),
    )
    for (
      layer_id,
      owner_stage,
      allowed_scope,
      required_evidence,
      required_authorities,
    ) in CALIBRATION_LAYER_SPECS
  }


def _supplemental_contract_record_template(
  *,
  layer_id: str,
  owner_stage: str,
  authority_field: str,
) -> dict[str, Any]:
  frozen_stage_ids = [
    stage_id for stage_id in CALIBRATION_STAGE_IDS if stage_id != owner_stage
  ]
  return {
    "schema_version": SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION,
    "evidence_id": f"REPLACE-WITH-STABLE-ID-{layer_id}",
    "layer_id": layer_id,
    "owner_stage": owner_stage,
    "authority_field": authority_field,
    "authority_scope": _supplemental_contract_authority_scope(authority_field),
    "source_kind": "external_authority_package",
    "source_ref": "REPLACE-WITH-STABLE-URL-OR-ARTIFACT-REF",
    "provenance": "REPLACE-WITH-ACQUISITION-GENERATION-RETENTION-TRANSFORMATION-SUMMARY",
    "rights_status": "release_grade_admitted",
    "source_gate_status": "passed",
    "validation_status": "passed",
    "scope": {
      "target_type": "REPLACE-WITH-EXACT-TARGET-TYPE-OR-CONSEQUENCE-SCOPE",
      "weapon_family": "REPLACE-WITH-EXACT-WEAPON-FAMILY",
      "mechanism_family": "REPLACE-WITH-EXACT-MECHANISM-FAMILY",
      "aspect_bucket": "REPLACE-WITH-EXACT-ASPECT-BUCKET",
      "closure_bucket": "REPLACE-WITH-EXACT-CLOSURE-BUCKET",
      "miss_distance_bucket": "REPLACE-WITH-EXACT-MISS-DISTANCE-BUCKET",
      "decision_scope": "REPLACE-WITH-FUZE-OR-CONSEQUENCE-DECISION-SCOPE",
    },
    "population": {
      "identity": "REPLACE-WITH-POPULATION-IDENTITY",
      "denominator_name": "REPLACE-WITH-NAMED-DENOMINATOR",
      "sample_count": "REPLACE-WITH-POSITIVE-INTEGER",
      "filters": "REPLACE-WITH-EXPLICIT-FILTERS",
      "independence_assumption": "REPLACE-WITH-INDEPENDENCE-ASSUMPTION",
    },
    "uncertainty": {
      "method": "REPLACE-WITH-UNCERTAINTY-METHOD",
      "coverage": "REPLACE-WITH-COVERAGE-STATEMENT",
      "residuals": [],
    },
    "independent_review": {
      "status": "passed",
      "reviewer_ref": "REPLACE-WITH-STABLE-REVIEWER-SIGNOFF-REF",
    },
    "stage_delta_requirements": {
      "target_stage_id": owner_stage,
      "frozen_stage_ids": frozen_stage_ids,
      "reject_if_changed_stage_ids": frozen_stage_ids,
      "before_after_stage_report_required": True,
      "delta_guard_schema_version": CALIBRATION_DELTA_GUARD_SCHEMA_VERSION,
    },
    "non_claims": list(MANDATORY_EVIDENCE_NON_CLAIMS),
    "residuals": [],
  }


def _calibration_evidence_contract_surface() -> dict[str, Any]:
  layer_contracts: list[dict[str, Any]] = []
  for (
    layer_id,
    owner_stage,
    _allowed_scope,
    _required_evidence,
    required_authorities,
  ) in CALIBRATION_LAYER_SPECS:
    authority_fields = list(required_authorities)
    mlf10_fields = [
      field for field in authority_fields if field in MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS
    ]
    supplemental_fields = [
      field for field in authority_fields if field in SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS
    ]
    unsupported_fields = sorted(
      set(authority_fields) - set(mlf10_fields) - set(supplemental_fields)
    )
    layer_contracts.append(
      {
        "layer_id": layer_id,
        "owner_stage": owner_stage,
        "required_authority_fields": authority_fields,
        "mlf10_v1_authority_fields": mlf10_fields,
        "supplemental_contract_authority_fields": supplemental_fields,
        "unsupported_authority_fields": unsupported_fields,
        "contract_status": "contracted" if not unsupported_fields else "unsupported",
      }
    )

  supplemental_fields = sorted(
    {
      field
      for row in layer_contracts
      for field in list(row.get("supplemental_contract_authority_fields", []) or [])
    }
  )
  unsupported_fields = sorted(
    {
      field
      for row in layer_contracts
      for field in list(row.get("unsupported_authority_fields", []) or [])
    }
  )
  return {
    "schema_version": CALIBRATION_EVIDENCE_CONTRACT_SURFACE_SCHEMA_VERSION,
    "mlf10_v1_template_schema_version": CALIBRATION_EVIDENCE_TEMPLATE_SCHEMA_VERSION,
    "mlf10_v1_template_check_schema_version": CALIBRATION_EVIDENCE_TEMPLATE_CHECK_SCHEMA_VERSION,
    "supplemental_contract_schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_SCHEMA_VERSION,
    "supplemental_contract_check_schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_CHECK_SCHEMA_VERSION,
    "supplemental_record_schema_version": SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION,
    "mlf10_v1_eligible_authority_fields": sorted(MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS),
    "supplemental_contract_authority_fields": supplemental_fields,
    "unsupported_authority_fields": unsupported_fields,
    "contract_surface_closed": not unsupported_fields,
    "layer_contracts": layer_contracts,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def external_evidence_supplemental_contract() -> dict[str, Any]:
  records: list[dict[str, Any]] = []
  layer_notes: list[dict[str, Any]] = []
  for (
    layer_id,
    owner_stage,
    allowed_scope,
    required_evidence,
    required_authorities,
  ) in CALIBRATION_LAYER_SPECS:
    supplemental_fields = [
      field
      for field in required_authorities
      if field in SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS
    ]
    if not supplemental_fields:
      continue
    layer_notes.append(
      {
        "layer_id": layer_id,
        "owner_stage": owner_stage,
        "allowed_parameter_scope": allowed_scope,
        "required_evidence": required_evidence,
        "supplemental_contract_authority_fields": supplemental_fields,
      }
    )
    for authority_field in supplemental_fields:
      records.append(
        _supplemental_contract_record_template(
          layer_id=layer_id,
          owner_stage=owner_stage,
          authority_field=authority_field,
        )
      )

  return {
    "schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_SCHEMA_VERSION,
    "status": "template_only_not_evidence",
    "purpose": "Supplemental P6 authority evidence contract for fields outside MLF-10 v1 manifest records",
    "record_schema_version": SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION,
    "contract_record_count": len(records),
    "layer_contracts": layer_notes,
    "contract_records": records,
    "next_commands": {
      "check_contract_or_record": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--external-evidence-supplemental-contract-check <contract_or_record.json> "
        "--output <contract_check.json>"
      ),
      "full_report_after_authority_admission": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--external-evidence-report <admission_report.json> --output <kill_chain_report.json>"
      ),
      "delta_guard_after_layer_update": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--delta-guard-before <before.json> --delta-guard-after <after.json> "
        "--delta-guard-layer <layer_id> --output <delta_guard.json>"
      ),
    },
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def external_evidence_template() -> dict[str, Any]:
  layer_templates: list[dict[str, Any]] = []
  for (
    layer_id,
    owner_stage,
    allowed_scope,
    required_evidence,
    required_authorities,
  ) in CALIBRATION_LAYER_SPECS:
    authority_fields = list(required_authorities)
    eligible_fields = [
      field for field in authority_fields if field in MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS
    ]
    separate_contract_fields = [
      field for field in authority_fields if field not in MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS
    ]
    supplemental_contract_templates = [
      _supplemental_contract_record_template(
        layer_id=layer_id,
        owner_stage=owner_stage,
        authority_field=field,
      )
      for field in separate_contract_fields
      if field in SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS
    ]
    record_template: dict[str, Any] | None = None
    if eligible_fields:
      record_template = {
        "schema_version": "mlf10.calibration_evidence.v1",
        "evidence_id": f"REPLACE-WITH-STABLE-ID-{layer_id}",
        "evidence_class": "calibration_candidate",
        "source_kind": "external_calibration_dataset",
        "source_ref": "REPLACE-WITH-STABLE-URL-OR-ARTIFACT-REF",
        "provenance": "REPLACE-WITH-ACQUISITION-GENERATION-RETENTION-TRANSFORMATION-SUMMARY",
        "rights_status": "release_grade_admitted",
        "source_gate_status": "passed",
        "validation_status": "passed",
        "scope": {
          "target_type": "REPLACE-WITH-EXACT-TARGET-TYPE",
          "weapon_family": "REPLACE-WITH-EXACT-WEAPON-FAMILY",
          "mechanism_family": "REPLACE-WITH-EXACT-MECHANISM-FAMILY",
          "aspect_bucket": "REPLACE-WITH-EXACT-ASPECT-BUCKET",
          "closure_bucket": "REPLACE-WITH-EXACT-CLOSURE-BUCKET",
          "miss_distance_bucket": "REPLACE-WITH-EXACT-MISS-DISTANCE-BUCKET",
        },
        "population": {
          "identity": "REPLACE-WITH-POPULATION-IDENTITY",
          "denominator_name": "REPLACE-WITH-NAMED-DENOMINATOR",
          "sample_count": "REPLACE-WITH-POSITIVE-INTEGER",
          "filters": "REPLACE-WITH-EXPLICIT-FILTERS",
          "independence_assumption": "REPLACE-WITH-INDEPENDENCE-ASSUMPTION",
        },
        "uncertainty": {
          "method": "REPLACE-WITH-UNCERTAINTY-METHOD",
          "coverage": "REPLACE-WITH-COVERAGE-STATEMENT",
          "residuals": [],
        },
        "independent_review": {
          "status": "passed",
          "reviewer_ref": "REPLACE-WITH-STABLE-REVIEWER-SIGNOFF-REF",
        },
        "authority_requests": {
          field: True for field in eligible_fields
        },
        "non_claims": list(MANDATORY_EVIDENCE_NON_CLAIMS),
        "residuals": [],
      }
    layer_templates.append(
      {
        "layer_id": layer_id,
        "owner_stage": owner_stage,
        "allowed_parameter_scope": allowed_scope,
        "required_evidence": required_evidence,
        "required_authority_fields": authority_fields,
        "mlf10_v1_eligible_authority_fields": eligible_fields,
        "separate_contract_required_authority_fields": separate_contract_fields,
        "mlf10_v1_manifest_record_template": record_template,
        "supplemental_contract_templates": supplemental_contract_templates,
        "admission_path": (
          "fill manifest record, rerun MLF-10 admission audit, then run kill-chain preflight/full report/delta guard"
          if eligible_fields
          else "fill supplemental contract, run supplemental contract check, then refresh the external admission path"
        ),
      }
    )

  return {
    "schema_version": CALIBRATION_EVIDENCE_TEMPLATE_SCHEMA_VERSION,
    "status": "template_only_not_evidence",
    "purpose": "P6 external evidence input contract for moving blocked layers toward admitted evidence",
    "manifest_schema_version": "mlf10.calibration_evidence_manifest.v1",
    "record_schema_version": "mlf10.calibration_evidence.v1",
    "admission_report_schema_version": MLF10_CALIBRATION_ADMISSION_REPORT_SCHEMA_VERSION,
    "mandatory_non_claims": list(MANDATORY_EVIDENCE_NON_CLAIMS),
    "mlf10_v1_eligible_authority_fields": sorted(MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS),
    "supplemental_contract_schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_SCHEMA_VERSION,
    "supplemental_record_schema_version": SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION,
    "supplemental_contract_authority_fields": sorted(SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS),
    "layer_templates": layer_templates,
    "next_commands": {
      "supplemental_contract": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--external-evidence-supplemental-contract --output <supplemental_contract.json>"
      ),
      "preflight_after_admission_report_refresh": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--external-evidence-preflight --external-evidence-report <admission_report.json> "
        "--output <preflight.json>"
      ),
      "full_report_after_preflight": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--external-evidence-report <admission_report.json> --output <kill_chain_report.json>"
      ),
      "delta_guard_after_layer_update": (
        "./.venv/bin/python tools/diagnostics/kill_chain_decoupling_probe.py "
        "--delta-guard-before <before.json> --delta-guard-after <after.json> "
        "--delta-guard-layer <layer_id> --output <delta_guard.json>"
      ),
    },
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _placeholder_paths(value: Any, path: str = "$") -> list[str]:
  paths: list[str] = []
  if isinstance(value, str):
    if value.startswith("REPLACE-") or value.startswith("<") or value.endswith(">"):
      paths.append(path)
    return paths
  if isinstance(value, dict):
    for key, child in value.items():
      paths.extend(_placeholder_paths(child, f"{path}.{key}"))
    return paths
  if isinstance(value, list):
    for idx, child in enumerate(value):
      paths.extend(_placeholder_paths(child, f"{path}[{idx}]"))
  return paths


def _truthy_requested_authorities(authority_requests: dict[str, Any]) -> list[str]:
  return sorted(
    str(field)
    for field, value in authority_requests.items()
    if isinstance(value, bool) and value
  )


def _evidence_record_template_check(record: dict[str, Any], *, record_index: int) -> dict[str, Any]:
  blockers: set[str] = set()
  warnings: set[str] = set()
  missing_fields = [
    field for field in MLF10_EVIDENCE_REQUIRED_FIELDS if field not in record
  ]
  if missing_fields:
    blockers.add("required_fields_missing")
  placeholder_paths = _placeholder_paths(record)
  if placeholder_paths:
    blockers.add("placeholder_values_present")
  if str(record.get("schema_version", "") or "") != "mlf10.calibration_evidence.v1":
    blockers.add("record_schema_invalid")

  authority_requests = dict(record.get("authority_requests", {}) or {})
  malformed_authority_fields = sorted(
    str(field)
    for field, value in authority_requests.items()
    if not isinstance(value, bool)
  )
  if malformed_authority_fields:
    blockers.add("authority_request_value_not_boolean")
  requested_authorities = _truthy_requested_authorities(authority_requests)
  forbidden_authorities = sorted(
    field for field in requested_authorities if field not in MLF10_V1_ELIGIBLE_AUTHORITY_FIELDS
  )
  if forbidden_authorities:
    blockers.add("authority_field_requires_separate_contract")
  if not requested_authorities:
    warnings.add("no_authority_requested")
    return {
      "record_index": int(record_index),
      "evidence_id": str(record.get("evidence_id", "") or ""),
      "authority_candidate": False,
      "requested_authority_fields": [],
      "forbidden_authority_fields": [],
      "ready_for_mlf10_audit": False,
      "blocked_by": [],
      "warnings": sorted(warnings),
      "missing_required_fields": missing_fields,
      "placeholder_paths": placeholder_paths,
      "missing_scope_fields": [],
      "missing_population_fields": [],
      "sample_count_valid": None,
      "malformed_authority_fields": malformed_authority_fields,
      "missing_non_claims": [],
    }

  scope = dict(record.get("scope", {}) or {})
  missing_scope_fields = [
    field for field in MLF10_SCOPE_FIELDS if not str(scope.get(field, "") or "").strip()
  ]
  if missing_scope_fields:
    blockers.add("scope_fields_missing")

  population = dict(record.get("population", {}) or {})
  missing_population_fields = [
    field
    for field in MLF10_POPULATION_FIELDS
    if field != "sample_count" and not str(population.get(field, "") or "").strip()
  ]
  sample_count = population.get("sample_count")
  sample_count_valid = (
    isinstance(sample_count, int)
    and not isinstance(sample_count, bool)
    and int(sample_count) > 0
  )
  if missing_population_fields or not sample_count_valid:
    blockers.add("population_fields_invalid")

  uncertainty = dict(record.get("uncertainty", {}) or {})
  uncertainty_residuals = list(uncertainty.get("residuals", []) or [])
  if not str(uncertainty.get("method", "") or "").strip():
    blockers.add("uncertainty_method_missing")
  if not str(uncertainty.get("coverage", "") or "").strip():
    blockers.add("uncertainty_coverage_missing")
  if uncertainty_residuals:
    blockers.add("uncertainty_residuals_open")

  independent_review = dict(record.get("independent_review", {}) or {})
  if str(independent_review.get("status", "") or "") != "passed":
    blockers.add("independent_review_not_passed")
  if not str(independent_review.get("reviewer_ref", "") or "").strip():
    blockers.add("independent_reviewer_ref_missing")

  if str(record.get("rights_status", "") or "") != "release_grade_admitted":
    blockers.add("rights_not_release_grade_admitted")
  if str(record.get("source_gate_status", "") or "") != "passed":
    blockers.add("source_gate_not_passed")
  if str(record.get("validation_status", "") or "") != "passed":
    blockers.add("validation_not_passed")
  if list(record.get("residuals", []) or []):
    blockers.add("blocking_residuals_open")

  non_claims = {str(value) for value in list(record.get("non_claims", []) or [])}
  missing_non_claims = [
    claim for claim in MANDATORY_EVIDENCE_NON_CLAIMS if claim not in non_claims
  ]
  if missing_non_claims:
    blockers.add("mandatory_non_claims_missing")

  source_kind = str(record.get("source_kind", "") or "")
  if requested_authorities and source_kind not in {
    "external_calibration_dataset",
    "validated_physics_surrogate",
  }:
    blockers.add("source_kind_not_authority_eligible")

  return {
    "record_index": int(record_index),
    "evidence_id": str(record.get("evidence_id", "") or ""),
    "authority_candidate": bool(requested_authorities),
    "requested_authority_fields": requested_authorities,
    "forbidden_authority_fields": forbidden_authorities,
    "ready_for_mlf10_audit": not blockers,
    "blocked_by": sorted(blockers),
    "warnings": sorted(warnings),
    "missing_required_fields": missing_fields,
    "placeholder_paths": placeholder_paths,
    "missing_scope_fields": missing_scope_fields,
    "missing_population_fields": missing_population_fields,
    "sample_count_valid": sample_count_valid,
    "malformed_authority_fields": malformed_authority_fields,
    "missing_non_claims": missing_non_claims,
  }


def external_evidence_template_check(path: Path | str) -> dict[str, Any]:
  payload = _load_json_report(path)
  schema = str(payload.get("schema_version", "") or "")
  records: list[dict[str, Any]] = []
  non_record_layer_notes: list[dict[str, Any]] = []
  if schema == CALIBRATION_EVIDENCE_TEMPLATE_SCHEMA_VERSION:
    for row in list(payload.get("layer_templates", []) or []):
      if not isinstance(row, dict):
        continue
      template_record = row.get("mlf10_v1_manifest_record_template")
      if isinstance(template_record, dict):
        records.append(dict(template_record))
      else:
        non_record_layer_notes.append(
          {
            "layer_id": str(row.get("layer_id", "") or ""),
            "reason": "no_mlf10_v1_record_template",
            "separate_contract_required_authority_fields": list(
              row.get("separate_contract_required_authority_fields", []) or []
            ),
          }
        )
  elif schema == "mlf10.calibration_evidence_manifest.v1":
    records = [
      dict(row)
      for row in list(payload.get("evidence_records", []) or [])
      if isinstance(row, dict)
    ]
  elif schema == "mlf10.calibration_evidence.v1":
    records = [payload]
  else:
    return {
      "schema_version": CALIBRATION_EVIDENCE_TEMPLATE_CHECK_SCHEMA_VERSION,
      "status": "unsupported_input_schema",
      "source_ref": _display_repo_path(Path(path)),
      "input_schema_version": schema,
      "ready_for_mlf10_audit": False,
      "record_count": 0,
      "ready_record_count": 0,
      "blocked_record_count": 0,
      "blocked_by": ["unsupported_input_schema"],
      "records": [],
      "non_record_layer_notes": [],
      "authority_boundary": {
        "runtime_parameter_retuning": False,
        "default_database_modified": False,
        "real_world_pk": False,
        "deterministic_fuze_authority": False,
        "calibration_authority": False,
      },
    }

  checked_records = [
    _evidence_record_template_check(record, record_index=idx)
    for idx, record in enumerate(records)
  ]
  authority_candidate_records = [
    row for row in checked_records if bool(row.get("authority_candidate"))
  ]
  ready_record_count = sum(
    1 for row in authority_candidate_records if bool(row.get("ready_for_mlf10_audit"))
  )
  blocked_record_count = len(authority_candidate_records) - ready_record_count
  top_blockers = sorted(
    {
      blocker
      for row in authority_candidate_records
      for blocker in list(row.get("blocked_by", []) or [])
    }
  )
  return {
    "schema_version": CALIBRATION_EVIDENCE_TEMPLATE_CHECK_SCHEMA_VERSION,
    "status": "ready_for_mlf10_audit" if records and not top_blockers else "blocked_or_template_only",
    "source_ref": _display_repo_path(Path(path)),
    "input_schema_version": schema,
    "ready_for_mlf10_audit": bool(authority_candidate_records) and not top_blockers,
    "record_count": len(checked_records),
    "authority_candidate_record_count": len(authority_candidate_records),
    "ready_record_count": ready_record_count,
    "blocked_record_count": blocked_record_count,
    "blocked_by": top_blockers,
    "records": checked_records,
    "non_record_layer_notes": non_record_layer_notes,
    "next_action": (
      "run tools/diagnostics/calibration_admission_audit.py on a manifest containing the ready records"
      if records and not top_blockers
      else "replace placeholders, close blockers, and keep forbidden authorities in separate contracts"
    ),
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _supplemental_contract_record_check(
  record: dict[str, Any],
  *,
  record_index: int,
) -> dict[str, Any]:
  blockers: set[str] = set()
  missing_fields = [
    field for field in SUPPLEMENTAL_EVIDENCE_REQUIRED_FIELDS if field not in record
  ]
  if missing_fields:
    blockers.add("required_fields_missing")
  placeholder_paths = _placeholder_paths(record)
  if placeholder_paths:
    blockers.add("placeholder_values_present")
  if str(record.get("schema_version", "") or "") != SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION:
    blockers.add("record_schema_invalid")

  layer_id = str(record.get("layer_id", "") or "")
  owner_stage = str(record.get("owner_stage", "") or "")
  authority_field = str(record.get("authority_field", "") or "")
  layer_specs = _layer_spec_by_id()
  expected_spec = layer_specs.get(layer_id)
  expected_owner_stage = ""
  expected_authorities: tuple[str, ...] = ()
  if not expected_spec:
    blockers.add("layer_id_unknown")
  else:
    expected_owner_stage = expected_spec[1]
    expected_authorities = expected_spec[4]
    if owner_stage != expected_owner_stage:
      blockers.add("owner_stage_mismatch")
    if authority_field not in expected_authorities:
      blockers.add("authority_field_not_required_by_layer")
  if authority_field not in SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS:
    blockers.add("authority_field_not_supplemental_contract_eligible")
  if (
    authority_field in SUPPLEMENTAL_CONTRACT_AUTHORITY_FIELDS
    and str(record.get("authority_scope", "") or "")
    != _supplemental_contract_authority_scope(authority_field)
  ):
    blockers.add("authority_scope_invalid")

  scope = dict(record.get("scope", {}) or {})
  missing_scope_fields = [
    field for field in (*MLF10_SCOPE_FIELDS, "decision_scope")
    if not str(scope.get(field, "") or "").strip()
  ]
  if missing_scope_fields:
    blockers.add("scope_fields_missing")

  population = dict(record.get("population", {}) or {})
  missing_population_fields = [
    field
    for field in MLF10_POPULATION_FIELDS
    if field != "sample_count" and not str(population.get(field, "") or "").strip()
  ]
  sample_count = population.get("sample_count")
  sample_count_valid = (
    isinstance(sample_count, int)
    and not isinstance(sample_count, bool)
    and int(sample_count) > 0
  )
  if missing_population_fields or not sample_count_valid:
    blockers.add("population_fields_invalid")

  uncertainty = dict(record.get("uncertainty", {}) or {})
  uncertainty_residuals = list(uncertainty.get("residuals", []) or [])
  if not str(uncertainty.get("method", "") or "").strip():
    blockers.add("uncertainty_method_missing")
  if not str(uncertainty.get("coverage", "") or "").strip():
    blockers.add("uncertainty_coverage_missing")
  if uncertainty_residuals:
    blockers.add("uncertainty_residuals_open")

  independent_review = dict(record.get("independent_review", {}) or {})
  if str(independent_review.get("status", "") or "") != "passed":
    blockers.add("independent_review_not_passed")
  if not str(independent_review.get("reviewer_ref", "") or "").strip():
    blockers.add("independent_reviewer_ref_missing")

  if str(record.get("rights_status", "") or "") != "release_grade_admitted":
    blockers.add("rights_not_release_grade_admitted")
  if str(record.get("source_gate_status", "") or "") != "passed":
    blockers.add("source_gate_not_passed")
  if str(record.get("validation_status", "") or "") != "passed":
    blockers.add("validation_not_passed")
  if str(record.get("source_kind", "") or "") not in {
    "external_authority_package",
    "validated_physics_surrogate",
  }:
    blockers.add("source_kind_not_authority_eligible")
  if list(record.get("residuals", []) or []):
    blockers.add("blocking_residuals_open")

  non_claims = {str(value) for value in list(record.get("non_claims", []) or [])}
  missing_non_claims = [
    claim for claim in MANDATORY_EVIDENCE_NON_CLAIMS if claim not in non_claims
  ]
  if missing_non_claims:
    blockers.add("mandatory_non_claims_missing")

  stage_delta = dict(record.get("stage_delta_requirements", {}) or {})
  expected_frozen = [
    stage_id for stage_id in CALIBRATION_STAGE_IDS if stage_id != expected_owner_stage
  ]
  if str(stage_delta.get("target_stage_id", "") or "") != expected_owner_stage:
    blockers.add("stage_delta_target_mismatch")
  if sorted(list(stage_delta.get("frozen_stage_ids", []) or [])) != sorted(expected_frozen):
    blockers.add("stage_delta_frozen_stage_mismatch")
  if sorted(list(stage_delta.get("reject_if_changed_stage_ids", []) or [])) != sorted(expected_frozen):
    blockers.add("stage_delta_reject_stage_mismatch")
  if not bool(stage_delta.get("before_after_stage_report_required")):
    blockers.add("before_after_stage_report_not_required")
  if (
    str(stage_delta.get("delta_guard_schema_version", "") or "")
    != CALIBRATION_DELTA_GUARD_SCHEMA_VERSION
  ):
    blockers.add("delta_guard_schema_missing")

  return {
    "record_index": int(record_index),
    "evidence_id": str(record.get("evidence_id", "") or ""),
    "layer_id": layer_id,
    "owner_stage": owner_stage,
    "authority_field": authority_field,
    "ready_for_authority_admission": not blockers,
    "blocked_by": sorted(blockers),
    "missing_required_fields": missing_fields,
    "placeholder_paths": placeholder_paths,
    "missing_scope_fields": missing_scope_fields,
    "missing_population_fields": missing_population_fields,
    "sample_count_valid": sample_count_valid,
    "missing_non_claims": missing_non_claims,
  }


def external_evidence_supplemental_contract_check(path: Path | str) -> dict[str, Any]:
  payload = _load_json_report(path)
  schema = str(payload.get("schema_version", "") or "")
  if schema == CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_SCHEMA_VERSION:
    records = [
      dict(row)
      for row in list(payload.get("contract_records", []) or [])
      if isinstance(row, dict)
    ]
  elif schema == SUPPLEMENTAL_EVIDENCE_RECORD_SCHEMA_VERSION:
    records = [payload]
  else:
    return {
      "schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_CHECK_SCHEMA_VERSION,
      "status": "unsupported_input_schema",
      "source_ref": _display_repo_path(Path(path)),
      "input_schema_version": schema,
      "ready_for_authority_admission": False,
      "record_count": 0,
      "ready_record_count": 0,
      "blocked_record_count": 0,
      "blocked_by": ["unsupported_input_schema"],
      "records": [],
      "authority_boundary": {
        "runtime_parameter_retuning": False,
        "default_database_modified": False,
        "real_world_pk": False,
        "deterministic_fuze_authority": False,
        "calibration_authority": False,
      },
    }

  checked_records = [
    _supplemental_contract_record_check(record, record_index=idx)
    for idx, record in enumerate(records)
  ]
  ready_record_count = sum(
    1 for row in checked_records if bool(row.get("ready_for_authority_admission"))
  )
  blocked_record_count = len(checked_records) - ready_record_count
  top_blockers = sorted(
    {
      blocker
      for row in checked_records
      for blocker in list(row.get("blocked_by", []) or [])
    }
  )
  return {
    "schema_version": CALIBRATION_SUPPLEMENTAL_EVIDENCE_CONTRACT_CHECK_SCHEMA_VERSION,
    "status": "ready_for_authority_admission" if records and not top_blockers else "blocked_or_template_only",
    "source_ref": _display_repo_path(Path(path)),
    "input_schema_version": schema,
    "ready_for_authority_admission": bool(records) and not top_blockers,
    "record_count": len(checked_records),
    "ready_record_count": ready_record_count,
    "blocked_record_count": blocked_record_count,
    "blocked_by": top_blockers,
    "records": checked_records,
    "next_action": (
      "refresh external admission report, then run full kill-chain report and delta guard"
      if records and not top_blockers
      else "replace placeholders, close blockers, and rerun this supplemental contract check"
    ),
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _normalize_guard_value(value: Any) -> Any:
  if isinstance(value, float):
    if not math.isfinite(value):
      return None
    return round(float(value), 12)
  if isinstance(value, dict):
    return {
      str(key): _normalize_guard_value(value[key])
      for key in sorted(value)
      if _normalize_guard_value(value[key]) is not None
    }
  if isinstance(value, list):
    return [
      normalized
      for normalized in (_normalize_guard_value(item) for item in value)
      if normalized is not None
    ]
  return value


def _stage_rows_by_id(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
  rows = list(case.get("stage_abstractions", []) or [])
  return {
    str(row.get("abstraction_stage", "") or ""): dict(row)
    for row in rows
    if str(row.get("abstraction_stage", "") or "")
  }


def _case_id(case: dict[str, Any]) -> str:
  return str(case.get("case_id", "") or "")


def _report_cases_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
  cases = [
    *list(report.get("guidance_cases", []) or []),
    *list(report.get("proximity_sweep", []) or []),
  ]
  return {_case_id(case): dict(case) for case in cases if _case_id(case)}


def _stage_guard_payload(row: dict[str, Any] | None) -> Any:
  if not row:
    return None
  return _normalize_guard_value(
    {
      "present": row.get("present"),
      "status": row.get("status"),
      "observed": dict(row.get("observed", {}) or {}),
      "coupling_flags": list(row.get("coupling_flags", []) or []),
    }
  )


def _plan_for_layer(report: dict[str, Any], layer_id: str) -> dict[str, Any] | None:
  plans = (
    report.get("calibration_admission", {})
    .get("single_layer_calibration_plan", {})
    .get("plans", [])
  )
  for plan in list(plans or []):
    if isinstance(plan, dict) and str(plan.get("layer_id", "") or "") == str(layer_id):
      return dict(plan)
  return None


def calibration_delta_guard(
  before_report: dict[str, Any],
  after_report: dict[str, Any],
  *,
  layer_id: str,
) -> dict[str, Any]:
  plan = _plan_for_layer(before_report, layer_id) or _plan_for_layer(after_report, layer_id)
  if not plan:
    return {
      "schema_version": CALIBRATION_DELTA_GUARD_SCHEMA_VERSION,
      "guard_passed": False,
      "layer_id": str(layer_id),
      "target_stage_id": "",
      "checked_case_count": 0,
      "changed_stage_ids": [],
      "stage_deltas": [],
      "blocked_by": ["single_layer_calibration_plan_missing"],
      "authority_boundary": {
        "runtime_parameter_retuning": False,
        "default_database_modified": False,
        "real_world_pk": False,
        "deterministic_fuze_authority": False,
        "calibration_authority": False,
      },
    }

  target_stage_id = str(plan.get("target_stage_id", "") or plan.get("owner_stage", "") or "")
  reject_if_changed = {
    str(stage_id)
    for stage_id in list(plan.get("reject_if_changed_stage_ids", []) or [])
    if str(stage_id)
  }
  before_cases = _report_cases_by_id(before_report)
  after_cases = _report_cases_by_id(after_report)
  common_case_ids = sorted(set(before_cases) & set(after_cases))
  stage_deltas: list[dict[str, Any]] = []
  changed_stage_ids: set[str] = set()
  target_stage_changed = False
  blockers: set[str] = set()
  if not common_case_ids:
    blockers.add("stage_report_case_overlap_missing")

  for cid in common_case_ids:
    before_stages = _stage_rows_by_id(before_cases[cid])
    after_stages = _stage_rows_by_id(after_cases[cid])
    stage_ids = sorted(set(before_stages) | set(after_stages))
    for stage_id in stage_ids:
      before_payload = _stage_guard_payload(before_stages.get(stage_id))
      after_payload = _stage_guard_payload(after_stages.get(stage_id))
      if before_payload == after_payload:
        continue
      changed_stage_ids.add(stage_id)
      if stage_id == target_stage_id:
        target_stage_changed = True
      if stage_id in reject_if_changed:
        blockers.add(f"frozen_stage_changed:{stage_id}")
      stage_deltas.append(
        {
          "case_id": cid,
          "stage_id": stage_id,
          "target_stage": stage_id == target_stage_id,
          "frozen_stage": stage_id in reject_if_changed,
        }
      )

  if target_stage_id and not target_stage_changed:
    blockers.add("target_stage_delta_missing")
  if not target_stage_id:
    blockers.add("target_stage_id_missing")

  return {
    "schema_version": CALIBRATION_DELTA_GUARD_SCHEMA_VERSION,
    "guard_passed": not blockers,
    "layer_id": str(layer_id),
    "target_stage_id": target_stage_id,
    "checked_case_count": len(common_case_ids),
    "changed_stage_ids": sorted(changed_stage_ids),
    "stage_deltas": stage_deltas,
    "blocked_by": sorted(blockers),
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
  }


def _calibration_admission_report(
  cases: list[dict[str, Any]],
  *,
  scalar_summary: dict[str, Any],
  component_load_factor_summary: dict[str, Any],
  decoupled_facade_summary: dict[str, Any],
  external_evidence_status: dict[str, Any],
) -> dict[str, Any]:
  response_fields_on_load_rows = int(
    component_load_factor_summary.get("rows_with_response_fields_on_load_row", 0)
    or 0
  )
  stage_report_available = bool(cases) and all(
    _stage_report_has_required_stages(case) for case in cases
  )
  legacy_fuze_multiplier_removed = bool(cases) and all(
    _case_has_no_legacy_fuze_damage_multiplier_surface(case) for case in cases
  )
  runtime_dto_authority = bool(
    decoupled_facade_summary.get("authority_boundary", {}).get("runtime_dto_authority")
  )
  component_response_rows_available = bool(
    decoupled_facade_summary.get("runtime_response_rows_available")
  )
  load_response_owner_clean = response_fields_on_load_rows == 0
  admitted_authority_fields = {
    str(field)
    for field in list(external_evidence_status.get("admitted_authority_fields", []) or [])
    if str(field)
  }
  layer_admission = _calibration_layer_rows(
    response_fields_on_load_rows=response_fields_on_load_rows,
    admitted_authority_fields=admitted_authority_fields,
    engineering_proxy_layer_ids=set(
      str(layer_id)
      for layer_id in list(
        external_evidence_status.get("engineering_proxy_layer_ids", []) or []
      )
    ),
  )
  external_calibration_evidence_present = any(
    bool(row.get("admission_granted")) for row in layer_admission
  )
  calibration_plan = _single_layer_calibration_plan(
    layer_rows=layer_admission,
    external_evidence_status=external_evidence_status,
    stage_report_available=stage_report_available,
    legacy_fuze_multiplier_removed=legacy_fuze_multiplier_removed,
    runtime_dto_authority=runtime_dto_authority,
    component_response_rows_available=component_response_rows_available,
    load_response_owner_clean=load_response_owner_clean,
  )

  blocker_checks = {
    "external_calibration_evidence_missing": not external_calibration_evidence_present,
    "p5_load_rows_still_carry_response_fields": not load_response_owner_clean,
    "stage_report_missing": not stage_report_available,
    "runtime_dto_authority_missing": not runtime_dto_authority,
    "component_response_rows_missing": not component_response_rows_available,
    "legacy_fuze_quality_damage_multiplier_surface_present": (
      not legacy_fuze_multiplier_removed
    ),
  }
  blockers = [name for name, active in blocker_checks.items() if active]
  admission_granted = not blockers
  engineering_proxy_evidence_present = bool(
    external_evidence_status.get("engineering_proxy_evidence_present")
  )
  if admission_granted and engineering_proxy_evidence_present and not admitted_authority_fields:
    admission_mode = "engineering_proxy_single_layer_guarded"
  elif admission_granted:
    admission_mode = "admitted_single_layer_guarded"
  elif blockers == ["external_calibration_evidence_missing"]:
    admission_mode = "fail_closed_until_external_evidence"
  else:
    admission_mode = "fail_closed_until_external_evidence_and_clean_owner_rows"

  return {
    "schema_version": CALIBRATION_ADMISSION_SCHEMA_VERSION,
    "admission_granted": admission_granted,
    "admission_mode": admission_mode,
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
    "prerequisites": {
      "stage_report_available": stage_report_available,
      "runtime_dto_authority": runtime_dto_authority,
      "component_response_rows_available": component_response_rows_available,
      "legacy_fuze_quality_damage_multiplier_removed": legacy_fuze_multiplier_removed,
      "load_rows_response_owner_clean": load_response_owner_clean,
      "external_calibration_evidence_present": external_calibration_evidence_present,
    },
    "cross_layer_leakage_guard": {
      "single_layer_mutation_required": True,
      "stage_report_required": True,
      "before_after_stage_delta_required": True,
      "blocked_if_unrelated_stage_changes": True,
    },
    "blocked_by": blockers,
    "layer_admission": layer_admission,
    "external_evidence": external_evidence_status,
    "external_evidence_contract_surface": _calibration_evidence_contract_surface(),
    "single_layer_calibration_plan": calibration_plan,
    "evidence_summary": {
      "case_count": len(cases),
      "scalar_count": int(scalar_summary.get("scalar_count", 0) or 0),
      "calibration_ready_scalar_count": int(
        scalar_summary.get("calibration_ready_scalar_count", 0) or 0
      ),
      "component_response_row_count": int(
        decoupled_facade_summary.get("component_response_row_count", 0) or 0
      ),
      "rows_with_response_fields_on_load_row": response_fields_on_load_rows,
      "external_evidence_source_ref": str(
        external_evidence_status.get("source_ref", "") or ""
      ),
      "external_admitted_record_count": int(
        external_evidence_status.get("admitted_record_count", 0) or 0
      ),
      "external_admitted_authority_fields": sorted(admitted_authority_fields),
      "engineering_proxy_record_count": int(
        external_evidence_status.get("engineering_proxy_record_count", 0) or 0
      ),
      "engineering_proxy_layer_ids": list(
        external_evidence_status.get("engineering_proxy_layer_ids", []) or []
      ),
    },
  }


def _stage_diagnostics_from_events(
  events: Any,
  *,
  sim_time_s: float,
  step: int,
  effect_summary: dict[str, Any] | None = None,
  runtime_facade: dict[str, Any] | None = None,
) -> dict[str, Any]:
  rows = _lethality_chain_rows(
    episode=0,
    step=int(step),
    sim_time_s=float(sim_time_s),
    engagement_events=events,
  )
  abstractions = _lethality_chain_stage_abstractions(rows)
  scalar_ledger = _lethality_chain_scalar_ledger(rows)
  if effect_summary:
    chain_id = 0
    if scalar_ledger:
      chain_id = int(scalar_ledger[0].get("chain_id", 0) or 0)
    scalar_ledger.extend(
      _effect_summary_scalar_ledger(
        effect_summary=effect_summary,
        episode=0,
        chain_id=chain_id,
      )
    )
    scalar_ledger.extend(
      _runtime_component_response_scalar_ledger(
        runtime_facade,
        episode=0,
        chain_id=chain_id,
      )
    )
  return {
    "row_count": len(rows),
    "source_stages": sorted({str(row.get("stage", "") or "") for row in rows}),
    "stage_abstractions": abstractions,
    "decoupling_summary": _lethality_chain_decoupling_summary(abstractions),
    "scalar_coupling_ledger": scalar_ledger,
    "scalar_coupling_summary": _scalar_coupling_summary(scalar_ledger),
  }


def _last_or_none(items: Any) -> Any | None:
  values = list(items or [])
  return values[-1] if values else None


def run_guidance_case(
  *,
  database_path: Path = DEFAULT_DATABASE_PATH,
  case_id: str,
  range_m: float,
  bearing_deg: float,
  seed: int = 20260621,
  max_steps: int = 4200,
  guidance_tuning_overrides: dict[str, float | int] | None = None,
  collect_guidance_runtime_trace: bool = False,
  guidance_trace_stride: int = 1,
) -> dict[str, Any]:
  sim = _make_kernel(database_path, seed=seed)
  tuning = ef_py.MissileTuning()
  tuning.sensor_scan_period = 1.0e9
  tuning.sensor_detection_prob = 0.0
  tuning.sensor_track_memory_s = 0.0
  tuning.seeker_fov_deg = 180.0
  tuning.seeker_lock_range = 1.0e6
  tuning.fuse_distance = 15.0
  tuning.max_flight_time_s = 45.0
  tuning.fuze_profile = _make_fuze_profile()
  tuning.has_fuze_profile = True
  applied_guidance_tuning_overrides = _apply_guidance_tuning_overrides(
    tuning,
    guidance_tuning_overrides,
  )
  sim.set_missile_tuning(tuning)

  bearing_rad = math.radians(float(bearing_deg))
  initial_x = float(range_m) * math.sin(bearing_rad)
  initial_y = float(range_m) * math.cos(bearing_rad)
  target_vx = 0.0
  target_vy = -250.0
  blue_id, red_id = _spawn_geometry_pair(
    sim,
    red_x=initial_x,
    red_y=initial_y,
    red_heading=180.0,
    red_vx=target_vx,
    red_vy=target_vy,
  )
  _select_weapon_station(sim, blue_id, 1)
  missile_id = int(sim.fire_missile(blue_id, red_id))
  if missile_id <= 0:
    raise RuntimeError(f"missile launch failed for {case_id}")
  missile_runtime_projection = _runtime_projection_profile(
    dict(sim.debug_get_missile_runtime_state(missile_id))
  )

  dt = float(sim.get_time_step())
  min_truth_distance_m = math.inf
  max_achieved_lateral_g = 0.0
  guidance_runtime_trace: list[dict[str, Any]] = []
  trace_stride = max(1, int(guidance_trace_stride))
  step_idx = 0
  time_s = 0.0
  for step_idx in range(int(max_steps)):
    time_s = step_idx * dt
    _set_unit_truth_state(
      sim,
      red_id,
      x=initial_x + target_vx * time_s,
      y=initial_y + target_vy * time_s,
      heading=180.0,
      vx=target_vx,
      vy=target_vy,
    )
    if not sim.is_unit_active(missile_id):
      break
    missile_pos = tuple(float(value) for value in sim.get_unit_position(missile_id))
    target_pos = tuple(float(value) for value in sim.get_unit_position(red_id))
    min_truth_distance_m = min(min_truth_distance_m, math.dist(missile_pos, target_pos))
    sim.set_contact_list(
      missile_id,
      [_relative_detection_from_truth(sim, missile_id, red_id, timestamp=time_s)],
    )
    sim.step()
    if sim.is_unit_active(missile_id):
      runtime = dict(sim.debug_get_missile_runtime_state(missile_id))
      max_achieved_lateral_g = max(
        max_achieved_lateral_g,
        _finite_float(runtime.get("achieved_lateral_accel_mps2", 0.0), 0.0) / 9.80665,
      )
      if collect_guidance_runtime_trace and step_idx % trace_stride == 0:
        missile_pos = tuple(float(value) for value in sim.get_unit_position(missile_id))
        target_pos = tuple(float(value) for value in sim.get_unit_position(red_id))
        missile_velocity = tuple(float(value) for value in sim.get_unit_velocity(missile_id))
        velocity_heading_deg = math.degrees(
          math.atan2(missile_velocity[0], missile_velocity[1])
        )
        guidance_runtime_trace.append(
          _guidance_runtime_trace_sample(
            runtime,
            time_s=(step_idx + 1) * dt,
            truth_distance_m=math.dist(missile_pos, target_pos),
            transform_heading_deg=float(sim.get_unit_heading(missile_id)),
            velocity_heading_deg=velocity_heading_deg,
          )
        )

  events = sim.export_recent_engagement_events()
  effect = _last_or_none(getattr(events, "effects_events", []))
  effect_summary = _event_effect_summary(effect)
  runtime_facade = _runtime_facade(effect)
  component_load_factor_rows = _component_load_factor_rows(
    effect,
    effect_summary,
    case_id=str(case_id),
  )
  nearest = _last_or_none(getattr(events, "nearest_approach_events", []))
  fuze = _last_or_none(getattr(events, "fuze_evaluation_events", []))
  stage_diagnostics = _stage_diagnostics_from_events(
    events,
    sim_time_s=time_s,
    step=step_idx,
    effect_summary=effect_summary,
    runtime_facade=runtime_facade,
  )
  decoupled_facade = _decoupled_facade(
    stage_diagnostics=stage_diagnostics,
    effect_summary=effect_summary,
    component_load_factor_rows=component_load_factor_rows,
    runtime_facade=runtime_facade,
  )
  result = {
    "case_id": str(case_id),
    "case_type": "aim120_offset_guidance",
    "range_m": float(range_m),
    "bearing_deg": float(bearing_deg),
    "seed": int(seed),
    "guidance_tuning_overrides": applied_guidance_tuning_overrides,
    "missile_id": int(missile_id),
    "missile_runtime_projection": missile_runtime_projection,
    "target_id": int(red_id),
    "target_active": bool(sim.is_unit_active(red_id)),
    "missile_active": bool(sim.is_unit_active(missile_id)),
    "sim_time_s": float(time_s),
    "step": int(step_idx),
    "truth_min_distance_m": _finite_or_none(min_truth_distance_m),
    "nearest_miss_distance_m": _float_attr(nearest, "miss_distance_m"),
    "nearest_reason": _str_attr(getattr(nearest, "header", None), "reason"),
    "fuze_reason": _str_attr(getattr(fuze, "header", None), "reason"),
    "fuze_triggered": _bool_attr(fuze, "triggered"),
    "fuze_expected_detonation_probability": _float_attr(
      fuze,
      "expected_detonation_probability",
    ),
    "max_achieved_lateral_g": max_achieved_lateral_g,
    "effect": effect_summary,
    "runtime_facade": runtime_facade,
    "component_load_factor_rows": component_load_factor_rows,
    "component_load_factor_summary": _component_load_factor_summary(
      component_load_factor_rows
    ),
    "decoupled_facade": decoupled_facade,
    **stage_diagnostics,
  }
  if collect_guidance_runtime_trace:
    result["guidance_runtime_trace"] = guidance_runtime_trace
  return result


def run_proximity_case(
  *,
  database_path: Path = DEFAULT_DATABASE_PATH,
  distance_m: float,
  family: str = "blast_fragmentation",
  damage: float = 180.0,
  radius: float = 15.0,
  mass_kg: float = 18.144,
  seed: int = 20260621,
) -> dict[str, Any]:
  sim = _make_kernel(database_path, seed=seed)
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  local_point = (0.0, float(distance_m), 0.0)
  velocity = missile_velocity_toward_origin(local_point)
  ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
    attacker_id,
    target_id,
    float(local_point[0]),
    float(local_point[1]),
    float(local_point[2]),
    _make_warhead_profile(family, damage=damage, radius=radius, mass_kg=mass_kg),
    float(velocity[0]),
    float(velocity[1]),
    float(velocity[2]),
  )
  if not ok:
    raise RuntimeError(f"profiled proximity hit failed at {distance_m} m")

  # Let consequence/structural systems consume the immediate component state.
  sim.step()
  events = sim.export_recent_engagement_events()
  effect = _last_or_none(getattr(events, "effects_events", []))
  effect_summary = _event_effect_summary(effect)
  runtime_facade = _runtime_facade(effect)
  component_load_factor_rows = _component_load_factor_rows(
    effect,
    effect_summary,
    case_id=f"{family}_{distance_m:g}m",
  )
  stage_diagnostics = _stage_diagnostics_from_events(
    events,
    sim_time_s=float(sim.get_time_step()),
    step=1,
    effect_summary=effect_summary,
    runtime_facade=runtime_facade,
  )
  decoupled_facade = _decoupled_facade(
    stage_diagnostics=stage_diagnostics,
    effect_summary=effect_summary,
    component_load_factor_rows=component_load_factor_rows,
    runtime_facade=runtime_facade,
  )
  return {
    "case_id": f"{family}_{distance_m:g}m",
    "case_type": "profiled_local_proximity",
    "distance_m": float(distance_m),
    "family": str(family),
    "damage": float(damage),
    "radius_m": float(radius),
    "mass_kg": float(mass_kg),
    "seed": int(seed),
    "target_active": bool(sim.is_unit_active(target_id)),
    "effect": effect_summary,
    "runtime_facade": runtime_facade,
    "component_load_factor_rows": component_load_factor_rows,
    "component_load_factor_summary": _component_load_factor_summary(
      component_load_factor_rows
    ),
    "decoupled_facade": decoupled_facade,
    **stage_diagnostics,
  }


def generate_report(
  *,
  database_path: Path = DEFAULT_DATABASE_PATH,
  external_evidence_report_path: Path | str | None = DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH,
  guidance_cases: tuple[dict[str, float | str], ...] = DEFAULT_GUIDANCE_CASES,
  proximity_distances_m: tuple[float, ...] = DEFAULT_PROXIMITY_DISTANCES_M,
  include_guidance: bool = True,
  include_proximity: bool = True,
  seed: int = 20260621,
) -> dict[str, Any]:
  guidance_results = [
    run_guidance_case(
      database_path=database_path,
      case_id=str(case["case_id"]),
      range_m=float(case["range_m"]),
      bearing_deg=float(case["bearing_deg"]),
      seed=seed,
    )
    for case in tuple(guidance_cases)
  ] if include_guidance else []
  proximity_results = [
    run_proximity_case(
      database_path=database_path,
      distance_m=float(distance),
      seed=seed,
    )
    for distance in tuple(proximity_distances_m)
  ] if include_proximity else []
  scalar_ledger = [
    row
    for case in [*guidance_results, *proximity_results]
    for row in list(case.get("scalar_coupling_ledger", []) or [])
  ]
  component_load_factor_rows = [
    row
    for case in [*guidance_results, *proximity_results]
    for row in list(case.get("component_load_factor_rows", []) or [])
  ]
  all_cases = [*guidance_results, *proximity_results]
  scalar_summary = _scalar_coupling_summary(scalar_ledger)
  component_load_factor_summary = _component_load_factor_summary(component_load_factor_rows)
  decoupled_facade_summary = _facade_summary(all_cases)
  external_evidence_status = _external_calibration_evidence_status(
    external_evidence_report_path
  )
  report = {
    "schema_version": SCHEMA_VERSION,
    "status": "generated",
    "database_path": str(database_path),
    "seed": int(seed),
    "authority_boundary": {
      "runtime_dto_authority": True,
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
    "guidance_case_count": len(guidance_results),
    "proximity_case_count": len(proximity_results),
    "scalar_coupling_summary": scalar_summary,
    "component_load_factor_summary": component_load_factor_summary,
    "decoupled_facade_summary": decoupled_facade_summary,
    "calibration_admission": _calibration_admission_report(
      all_cases,
      scalar_summary=scalar_summary,
      component_load_factor_summary=component_load_factor_summary,
      decoupled_facade_summary=decoupled_facade_summary,
      external_evidence_status=external_evidence_status,
    ),
    "guidance_cases": guidance_results,
    "proximity_sweep": proximity_results,
  }
  report["completion_audit"] = kill_chain_completion_audit(report)
  return report


def _parse_distances(value: str) -> tuple[float, ...]:
  if not str(value).strip():
    return DEFAULT_PROXIMITY_DISTANCES_M
  return tuple(float(item.strip()) for item in str(value).split(",") if item.strip())


def _load_json_report(path: Path | str) -> dict[str, Any]:
  with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
  if not isinstance(payload, dict):
    raise ValueError(f"JSON report must be an object: {path}")
  return payload


@contextlib.contextmanager
def _native_stdout_to_stderr():
  """Keep CLI stdout machine-readable while native runtime logs are emitted."""
  sys.stdout.flush()
  saved_stdout_fd = os.dup(1)
  try:
    os.dup2(2, 1)
    yield
  finally:
    sys.stdout.flush()
    os.dup2(saved_stdout_fd, 1)
    os.close(saved_stdout_fd)


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Generate decoupled kill-chain diagnostics for guidance/proximity slices."
  )
  parser.add_argument(
    "--database",
    default=str(DEFAULT_DATABASE_PATH),
    help="Runtime database directory.",
  )
  parser.add_argument(
    "--mode",
    choices=("all", "guidance", "proximity"),
    default="all",
    help="Subset to run.",
  )
  parser.add_argument(
    "--proximity-distances-m",
    default=",".join(str(value) for value in DEFAULT_PROXIMITY_DISTANCES_M),
    help="Comma-separated local proximity distances for the sweep.",
  )
  parser.add_argument("--seed", type=int, default=20260621)
  parser.add_argument(
    "--external-evidence-report",
    default=str(DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH),
    help="Optional MLF-10 calibration admission report used by the P6 gate.",
  )
  parser.add_argument(
    "--external-evidence-preflight",
    action="store_true",
    help="Only inspect the external evidence report and emit P6 admission preflight JSON.",
  )
  parser.add_argument(
    "--external-evidence-template",
    action="store_true",
    help="Emit a P6 external evidence input template without rerunning simulation.",
  )
  parser.add_argument(
    "--external-evidence-template-check",
    default="",
    help="Validate a P6 evidence template, manifest draft, or evidence record for MLF-10 audit readiness.",
  )
  parser.add_argument(
    "--external-evidence-supplemental-contract",
    action="store_true",
    help="Emit supplemental P6 evidence contracts for authority fields outside MLF-10 v1.",
  )
  parser.add_argument(
    "--external-evidence-supplemental-contract-check",
    default="",
    help="Validate a supplemental P6 evidence contract or record for authority admission readiness.",
  )
  parser.add_argument(
    "--completion-audit-report",
    default="",
    help="Existing kill-chain report JSON to audit for P0-P6 completion without rerunning simulation.",
  )
  parser.add_argument(
    "--delta-guard-before",
    default="",
    help="Existing before-report JSON for P6 single-layer calibration delta guard.",
  )
  parser.add_argument(
    "--delta-guard-after",
    default="",
    help="Existing after-report JSON for P6 single-layer calibration delta guard.",
  )
  parser.add_argument(
    "--delta-guard-layer",
    default="",
    help="Layer id to validate for --delta-guard-before/--delta-guard-after.",
  )
  parser.add_argument("--output", default="", help="Optional JSON output path.")
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  if args.delta_guard_before or args.delta_guard_after or args.delta_guard_layer:
    if not (args.delta_guard_before and args.delta_guard_after and args.delta_guard_layer):
      raise SystemExit(
        "--delta-guard-before, --delta-guard-after, and --delta-guard-layer must be provided together"
      )
    report = calibration_delta_guard(
      _load_json_report(Path(args.delta_guard_before)),
      _load_json_report(Path(args.delta_guard_after)),
      layer_id=str(args.delta_guard_layer),
    )
  elif str(args.completion_audit_report).strip():
    report = kill_chain_completion_audit(
      _load_json_report(Path(args.completion_audit_report))
    )
  elif bool(args.external_evidence_template):
    report = external_evidence_template()
  elif str(args.external_evidence_template_check).strip():
    report = external_evidence_template_check(
      Path(args.external_evidence_template_check)
    )
  elif bool(args.external_evidence_supplemental_contract):
    report = external_evidence_supplemental_contract()
  elif str(args.external_evidence_supplemental_contract_check).strip():
    report = external_evidence_supplemental_contract_check(
      Path(args.external_evidence_supplemental_contract_check)
    )
  elif bool(args.external_evidence_preflight):
    report = external_evidence_preflight(Path(args.external_evidence_report))
  else:
    with _native_stdout_to_stderr():
      report = generate_report(
        database_path=Path(args.database),
        proximity_distances_m=_parse_distances(args.proximity_distances_m),
        include_guidance=str(args.mode) in {"all", "guidance"},
        include_proximity=str(args.mode) in {"all", "proximity"},
        seed=int(args.seed),
        external_evidence_report_path=Path(args.external_evidence_report),
      )
  text = json.dumps(report, indent=2, ensure_ascii=True)
  if args.output:
    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
      handle.write(text)
      handle.write("\n")
  print(text)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
