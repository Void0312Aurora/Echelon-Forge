#!/usr/bin/env python3
"""Trace TG-P7 split receiver visibility through runtime damage events."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path, repo_root, configure_sim_log_level
from tools.geometry import target_geometry_lethality_matrix_probe as matrix_probe


ensure_repo_imports()

REPO_ROOT = Path(repo_root())
import ef_py  # noqa: E402


SCHEMA_VERSION = "a2.target_geometry_damage_event_trace.v1"
STATUS = "target_geometry_damage_event_trace_generated_tg_p7_r5"
GENERATED_ON = "2026-06-14"
DEFAULT_DATABASE_PATH = Path(resolve_repo_path("examples", "config", "database"))
PROXY_DATABASE_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "f16c_target_geometry_20260614",
    "review_packets",
    "f16c_20260611",
    "target_geometry_training_proxy_database_20260613",
  )
)
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "f16c_target_geometry_20260614",
    "review_packets",
    "f16c_20260611",
    "target_geometry_damage_event_trace_20260614.json",
  )
)
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


def _trace_case_with_standard_velocity(case: dict[str, Any]) -> dict[str, Any]:
  local_point_m = tuple(float(value) for value in case["local_point_m"])
  return {
    **case,
    "missile_velocity_body_mps": matrix_probe.missile_velocity_toward_origin(
      local_point_m
    ),
  }


TRACE_CASES: tuple[dict[str, Any], ...] = tuple(
  _trace_case_with_standard_velocity(case)
  for case in (
  {
    "case_id": "engine_afterburner_segment_direct_trace",
    "expected_split_receiver": "engine_core_afterburner_segment",
    "retired_parent_component": "engine_core",
    "local_point_m": (-5.775512, -0.5, -0.404381),
  },
  {
    "case_id": "engine_hot_section_spatial_trace",
    "expected_split_receiver": "engine_core_hot_section_segment",
    "retired_parent_component": "engine_core",
    "local_point_m": (-4.193053, -0.5, -1.354381),
  },
  {
    "case_id": "engine_forward_compressor_spatial_trace",
    "expected_split_receiver": "engine_core_forward_compressor_segment",
    "retired_parent_component": "engine_core",
    "local_point_m": (-2.852966, -0.5, -1.354381),
  },
  {
    "case_id": "left_inner_wing_spar_trace",
    "expected_split_receiver": "wing_spar_center_left_inner_wing_segment",
    "retired_parent_component": "wing_spar_center",
    "local_point_m": (-1.55, -1.7, -0.7),
  },
  {
    "case_id": "left_root_spar_trace",
    "expected_split_receiver": "wing_spar_center_left_root_segment",
    "retired_parent_component": "wing_spar_center",
    "local_point_m": (-0.85, -0.9, -1.1),
  },
  {
    "case_id": "center_carrythrough_spar_trace",
    "expected_split_receiver": "wing_spar_center_carrythrough_segment",
    "retired_parent_component": "wing_spar_center",
    "local_point_m": (-1.292842, -0.5, -1.785043),
  },
  {
    "case_id": "right_root_spar_trace",
    "expected_split_receiver": "wing_spar_center_right_root_segment",
    "retired_parent_component": "wing_spar_center",
    "local_point_m": (-0.85, 0.9, -1.1),
  },
  {
    "case_id": "right_inner_wing_spar_trace",
    "expected_split_receiver": "wing_spar_center_right_inner_wing_segment",
    "retired_parent_component": "wing_spar_center",
    "local_point_m": (-1.55, 1.7, -0.7),
  },
  )
)


def _relative_path(path: Path) -> str:
  # Kept local: str(resolve.relative_to); differs from manifest_integrity._display_path (as_posix/fallback).
  return str(path.resolve().relative_to(REPO_ROOT))


def _configure_runtime_log_level() -> None:
  # Preserve setdefault('error') semantics; owner applies level to ef_py.
  os.environ.setdefault("CMO_SIM_LOG_LEVEL", "error")
  configure_sim_log_level(str(os.environ["CMO_SIM_LOG_LEVEL"]))


def _load_unit(database_path: Path) -> dict[str, Any]:
  unit_path = database_path / "aircraft" / "units" / "f16c_block50.json"
  return json.loads(unit_path.read_text(encoding="utf-8"))


def _component_names(database_path: Path) -> list[str]:
  names: list[str] = []
  unit = _load_unit(database_path)
  for hitbox in unit["damage_model"]["hitboxes"]:
    for component in hitbox.get("components", []):
      names.append(str(component.get("name", "")))
  return names


def _make_warhead_profile() -> object:
  profile = ef_py.WarheadProfile()
  profile.family = "blast_fragmentation"
  profile.mass_kg = 12.0
  profile.lethal_radius_m = 35.0
  profile.damage_scalar = 90.0
  profile.synthetic = True
  profile.damage_scalar_synthetic = True
  profile.provenance = "tg_p7_damage_event_trace_synthetic_blast_fragmentation"
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


def _as_float(value: object) -> float:
  return float(value)


def _response_for_load_row(effect: object, load_row: object) -> object | None:
  load_key = (
    str(load_row.component_name),
    str(load_row.component_system),
    str(load_row.component_redundancy_group_id),
  )
  for response in getattr(effect, "component_response_rows", []) or []:
    response_key = (
      str(response.component_name),
      str(response.component_system),
      str(response.component_redundancy_group_id),
    )
    if response_key == load_key:
      return response
  return None


def _row_summary(effect: object, row: object) -> dict[str, Any]:
  response = _response_for_load_row(effect, row)
  return {
    "component_name": str(row.component_name),
    "component_system": str(row.component_system),
    "component_redundancy_group_id": str(row.component_redundancy_group_id),
    "direct_hit": bool(row.direct_hit),
    "distance_m": _as_float(row.distance_m),
    "effect_scale": _as_float(row.effect_scale),
    "component_failure_probability": (
      _as_float(response.failure_probability) if response is not None else 0.0
    ),
    "component_failure_probability_source": (
      str(response.failure_probability_source) if response is not None else "none"
    ),
    "component_failure_sample": (
      _as_float(response.failure_sample) if response is not None else 1.0
    ),
    "mechanism_fragment_energy_j": _as_float(row.mechanism_fragment_energy_j),
    "mechanism_fragment_areal_density_per_m2": _as_float(
      row.mechanism_fragment_areal_density_per_m2
    ),
    "mechanism_blast_overpressure_kpa": _as_float(
      row.mechanism_blast_overpressure_kpa
    ),
    "mechanism_blast_impulse_kpa_ms": _as_float(row.mechanism_blast_impulse_kpa_ms),
    "mechanism_penetration_margin": _as_float(row.mechanism_penetration_margin),
  }


def _component_load_summary(load: object) -> dict[str, Any]:
  return {
    "component_name": str(load.component_name),
    "component_system": str(load.component_system),
    "component_redundancy_group_id": str(load.component_redundancy_group_id),
    "direct_hit": bool(load.direct_hit),
    "distance_m": _as_float(load.distance_m),
    "effect_scale": _as_float(load.effect_scale),
    "load_source": str(load.load_source),
  }


def _component_damage_summary(damage: object) -> dict[str, Any]:
  return {
    "component_name": str(damage.component_name),
    "component_system": str(damage.component_system),
    "component_redundancy_group_id": str(damage.component_redundancy_group_id),
    "integrity_before": _as_float(damage.integrity_before),
    "integrity_after": _as_float(damage.integrity_after),
    "failure_mode": str(damage.failure_mode),
    "failure_severity": _as_float(damage.failure_severity),
    "failure_probability": _as_float(damage.failure_probability),
    "failure_sample": _as_float(damage.failure_sample),
  }


def _event_component_names(summary: dict[str, Any]) -> set[str]:
  names = set(summary["component_mechanism_row_names"])
  names.update(summary["component_load_event_names"])
  names.update(summary["component_damage_event_names"])
  if summary["component_primary_name"]:
    names.add(str(summary["component_primary_name"]))
  return names


def _run_trace_event(
  *,
  database_path: Path,
  local_point_m: tuple[float, float, float],
  missile_velocity_body_mps: tuple[float, float, float],
  seed: int,
) -> dict[str, Any]:
  sim = ef_py.SimulationKernel()
  sim.reset(seed)
  if not sim.load_database(str(database_path)):
    raise RuntimeError(f"failed to load database: {database_path}")
  attacker_id, target_id = _spawn_structured_f16_pair(sim)
  profile = _make_warhead_profile()
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
  rows = [_row_summary(effect, row) for row in effect.component_mechanism_load_rows]
  loads = [_component_load_summary(load) for load in events.component_load_events]
  damages = [
    _component_damage_summary(damage) for damage in events.component_damage_events
  ]
  return {
    "database_path": _relative_path(database_path),
    "component_primary_name": str(effect.component_primary_name),
    "component_primary_system": str(effect.component_primary_system),
    "component_hit_count": int(effect.component_hit_count),
    "component_failure_count": int(effect.component_failure_count),
    "projected_hitbox_count": int(effect.projected_hitbox_count),
    "direct_hitbox_intersection": bool(effect.direct_hitbox_intersection),
    "effect_family": str(effect.effect_family),
    "trigger_type": str(effect.trigger_type),
    "outcome_state": str(effect.outcome_state),
    "warhead_profile_synthetic": bool(effect.warhead_profile_synthetic),
    "damage_scalar_synthetic": bool(effect.damage_scalar_synthetic),
    "vulnerability_calibrated_evidence": bool(effect.vulnerability_calibrated_evidence),
    "vulnerability_pk_authority": bool(effect.vulnerability_pk_authority),
    "vulnerability_deterministic_fuze_authority": bool(
      effect.vulnerability_deterministic_fuze_authority
    ),
    "component_failure_probability_source": str(
      effect.component_failure_probability_source
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


def _trace_case(case: dict[str, Any], *, seed: int) -> dict[str, Any]:
  default_event = _run_trace_event(
    database_path=DEFAULT_DATABASE_PATH,
    local_point_m=tuple(case["local_point_m"]),
    missile_velocity_body_mps=tuple(case["missile_velocity_body_mps"]),
    seed=seed,
  )
  proxy_event = _run_trace_event(
    database_path=PROXY_DATABASE_PATH,
    local_point_m=tuple(case["local_point_m"]),
    missile_velocity_body_mps=tuple(case["missile_velocity_body_mps"]),
    seed=seed,
  )
  expected_split = str(case["expected_split_receiver"])
  retired_parent = str(case["retired_parent_component"])
  default_names = _event_component_names(default_event)
  proxy_names = _event_component_names(proxy_event)
  checks = {
    "default_split_receiver_absent": expected_split not in default_names,
    "proxy_split_receiver_observed": expected_split in proxy_names,
    "proxy_retired_parent_absent": retired_parent not in proxy_names,
    "proxy_trace_uses_synthetic_non_authoritative_warhead": (
      bool(proxy_event["warhead_profile_synthetic"])
      and bool(proxy_event["damage_scalar_synthetic"])
      and not bool(proxy_event["vulnerability_pk_authority"])
      and not bool(proxy_event["vulnerability_deterministic_fuze_authority"])
    ),
  }
  checks["case_pass"] = all(checks.values())
  return {
    **case,
    "local_point_m": list(case["local_point_m"]),
    "missile_velocity_body_mps": list(case["missile_velocity_body_mps"]),
    "default_event": default_event,
    "proxy_event": proxy_event,
    "checks": checks,
  }


def generate_report(*, seed: int = 20260614) -> dict[str, Any]:
  _configure_runtime_log_level()
  default_component_names = _component_names(DEFAULT_DATABASE_PATH)
  proxy_component_names = _component_names(PROXY_DATABASE_PATH)
  trace_cases = [_trace_case(case, seed=seed) for case in TRACE_CASES]
  observed_split_receivers = sorted(
    {
      str(case["expected_split_receiver"])
      for case in trace_cases
      if bool(case["checks"]["proxy_split_receiver_observed"])
    }
  )
  default_observed_split_receivers = sorted(
    {
      name
      for case in trace_cases
      for name in _event_component_names(case["default_event"])
      if name in SPLIT_RECEIVER_NAMES
    }
  )
  proxy_observed_retired_parents = sorted(
    {
      name
      for case in trace_cases
      for name in _event_component_names(case["proxy_event"])
      if name in RETIRED_PARENT_COMPONENTS
    }
  )
  metrics = {
    "trace_case_count": len(trace_cases),
    "split_receiver_component_count": len(SPLIT_RECEIVER_NAMES),
    "proxy_observed_split_receiver_count": len(observed_split_receivers),
    "proxy_observed_split_receivers": observed_split_receivers,
    "default_observed_split_receivers": default_observed_split_receivers,
    "proxy_observed_retired_parent_components": proxy_observed_retired_parents,
    "all_expected_split_receivers_observed_in_proxy": (
      set(observed_split_receivers) == set(SPLIT_RECEIVER_NAMES)
    ),
    "no_expected_split_receiver_observed_in_default": (
      len(default_observed_split_receivers) == 0
    ),
    "proxy_retired_parent_rows_absent": len(proxy_observed_retired_parents) == 0,
    "all_trace_cases_pass": all(
      bool(case["checks"]["case_pass"]) for case in trace_cases
    ),
  }
  inventory = {
    "default_database_component_count": len(default_component_names),
    "proxy_database_component_count": len(proxy_component_names),
    "component_count_delta": len(proxy_component_names) - len(default_component_names),
    "default_split_receiver_count": sum(
      1 for name in default_component_names if name in SPLIT_RECEIVER_NAMES
    ),
    "proxy_split_receiver_count": sum(
      1 for name in proxy_component_names if name in SPLIT_RECEIVER_NAMES
    ),
    "default_retired_parent_count": sum(
      1 for name in default_component_names if name in RETIRED_PARENT_COMPONENTS
    ),
    "proxy_retired_parent_count": sum(
      1 for name in proxy_component_names if name in RETIRED_PARENT_COMPONENTS
    ),
    "duplicate_proxy_component_names": sorted(
      {
        name
        for name in proxy_component_names
        if proxy_component_names.count(name) > 1
      }
    ),
  }
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
      "synthetic_blast_fragmentation_warhead": True,
      "real_weapon_pk_authority": False,
      "deterministic_fuze_authority": False,
      "true_internal_component_geometry": False,
      "default_database_modified": False,
      "proxy_database_opt_in_only": True,
    },
    "acceptance_gate": [
      "default_database_component_count_equals_26",
      "proxy_database_component_count_equals_32",
      "proxy_split_receiver_count_equals_8",
      "proxy_retired_parent_count_equals_0",
      "default_split_receiver_count_equals_0",
      "all_8_split_receivers_observed_in_proxy_component_event_names",
      "no_split_receivers_observed_in_default_component_event_names",
      "proxy_events_do_not_fall_back_to_retired_parent_component_names",
      "trace_events_remain_synthetic_non_authoritative_damage_probes",
    ],
    "component_inventory": inventory,
    "metrics": metrics,
    "trace_cases": trace_cases,
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=None)
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
