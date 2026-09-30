#!/usr/bin/env python3
"""Admit continuous-rod component-load topology after P7.1 decoupling."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root, resolve_repo_path  # noqa: E402

ensure_repo_imports()
from tools.geometry import warhead_spatial_structural_admission as common  # noqa: E402


REPO_ROOT = Path(repo_root())
SCHEMA_VERSION = "a2.continuous_rod_component_load_admission.v1"
STATUS = "continuous_rod_component_load_admission_generated"
GENERATED_ON = "2026-09-14"
CURVE_FLOOR_EFFECT_SCALE = 0.05
BASELINE_MIN_EFFECT_SCALE = 0.05
DECOUPLED_MIN_EFFECT_SCALE = 0.0
TOLERANCE = 1.0e-9
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "artifacts",
    "kill_chain",
    "20260915",
    "raw_review_packets",
    "continuous_rod_component_load_admission_20260914",
    "continuous_rod_component_load_admission_20260914.json",
  )
)


def _relative_path(path: Path) -> str:
  try:
    return str(path.resolve().relative_to(REPO_ROOT))
  except ValueError:
    return str(path.resolve())


def _rod_cases() -> list[dict[str, Any]]:
  return [
    case
    for case in common._case_definitions()
    if str(case["warhead_family"]) == "continuous_rod"
  ]


def _run_rows(
  cases: list[dict[str, Any]],
  *,
  seed: int,
  minimum_effect_scale: float,
) -> list[dict[str, Any]]:
  return [
    common._event_row(
      case,
      seed + index,
      explicit_continuous_rod=True,
      continuous_rod_band_half_angle_deg=6.0,
      continuous_rod_azimuthal_samples=720,
      continuous_rod_polar_samples=5,
      continuous_rod_azimuthal_phase_deg=0.0,
      projection_min_effect_scale=minimum_effect_scale,
      projection_curve_floor_effect_scale=CURVE_FLOOR_EFFECT_SCALE,
    )
    for index, case in enumerate(cases)
  ]


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
  return (
    str(row["component_name"]),
    str(row["component_system"]),
    str(row["component_redundancy_group_id"]),
  )


def _finite_range(
  value: object, *, minimum: float | None = None, maximum: float | None = None
) -> bool:
  number = float(value)
  return (
    math.isfinite(number)
    and (minimum is None or number >= minimum - TOLERANCE)
    and (maximum is None or number <= maximum + TOLERANCE)
  )


def _variant_validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
  residuals: dict[str, list[dict[str, Any]]] = {
    "load_response_identity": [],
    "load_scalar_range": [],
    "response_scalar_range": [],
    "primary_trace": [],
    "redundancy_group": [],
  }
  total_loads = 0
  total_responses = 0
  group_systems: dict[str, set[str]] = defaultdict(set)
  group_components: dict[str, set[str]] = defaultdict(set)

  for row in rows:
    event = row["event"]
    case_id = str(row["case_id"])
    loads = list(event["component_mechanism_load_rows"])
    responses = list(event["component_response_rows"])
    total_loads += len(loads)
    total_responses += len(responses)
    load_keys = [_key(load) for load in loads]
    response_keys = [_key(response) for response in responses]
    if len(load_keys) != len(set(load_keys)):
      residuals["load_response_identity"].append(
        {"case_id": case_id, "reason": "duplicate_load_key"}
      )
    if len(response_keys) != len(set(response_keys)):
      residuals["load_response_identity"].append(
        {"case_id": case_id, "reason": "duplicate_response_key"}
      )
    if set(load_keys) != set(response_keys):
      residuals["load_response_identity"].append(
        {
          "case_id": case_id,
          "reason": "load_response_key_set_changed",
          "load_keys": [list(value) for value in load_keys],
          "response_keys": [list(value) for value in response_keys],
        }
      )
    load_by_key = {key: load for key, load in zip(load_keys, loads)}
    load_index_by_key = {key: index for index, key in enumerate(load_keys)}
    for response in responses:
      key = _key(response)
      load = load_by_key.get(key)
      expected_source_row_index = load_index_by_key.get(key)
      if load is None or int(response["source_row_index"]) != expected_source_row_index:
        residuals["load_response_identity"].append(
          {
            "case_id": case_id,
            "reason": "response_source_row_mismatch",
            "key": list(key),
            "expected_source_row_index": expected_source_row_index,
            "actual_source_row_index": int(response["source_row_index"]),
          }
        )
      if str(response["source_current_owner_stage"]) != "component_response_row":
        residuals["load_response_identity"].append(
          {"case_id": case_id, "reason": "unexpected_response_owner_stage", "key": list(key)}
        )
      if load is not None and key != _key(load):
        residuals["load_response_identity"].append(
          {"case_id": case_id, "reason": "response_load_key_mismatch", "key": list(key)}
        )

    if not loads and (event["component_primary_name"] or responses):
      residuals["primary_trace"].append(
        {"case_id": case_id, "reason": "primary_or_response_without_load"}
      )
    if loads:
      primary_key = (
        str(event["component_primary_name"]),
        str(event["component_primary_system"]),
        str(event["component_primary_redundancy_group_id"]),
      )
      if primary_key not in load_by_key:
        residuals["primary_trace"].append(
          {
            "case_id": case_id,
            "reason": "primary_key_not_in_load_rows",
            "primary_key": list(primary_key),
          }
        )
      else:
        primary_load = load_by_key[primary_key]
        if not math.isclose(
          float(event["component_primary_mechanism_rod_cut_margin"]),
          float(primary_load["mechanism_rod_cut_margin"]),
          rel_tol=1.0e-8,
          abs_tol=TOLERANCE,
        ):
          residuals["primary_trace"].append(
            {"case_id": case_id, "reason": "primary_rod_margin_mismatch"}
          )
    for load in loads:
      key = _key(load)
      group = key[2]
      if not all(key):
        residuals["redundancy_group"].append(
          {"case_id": case_id, "reason": "incomplete_component_key", "key": list(key)}
        )
      group_systems[group].add(key[1])
      group_components[group].add(key[0])
      if not _finite_range(load["distance_m"], minimum=0.0):
        residuals["load_scalar_range"].append(
          {"case_id": case_id, "reason": "distance_out_of_range", "key": list(key)}
        )
      for field, minimum, maximum in (
        ("effect_scale", 0.0, 1.5),
        ("mechanism_rod_cut_margin", 0.0, 8.0),
        ("mechanism_penetration_margin", 0.0, 10.0),
        ("component_dependency_threshold", 0.0, 10.0),
        ("component_dependency_delay_s", 0.0, 3600.0),
        ("component_dependency_source_availability", 0.0, 1.0),
        ("component_dependency_effective_scale", 0.0, 1.5),
      ):
        if not _finite_range(load[field], minimum=minimum, maximum=maximum):
          residuals["load_scalar_range"].append(
            {"case_id": case_id, "reason": f"{field}_out_of_range", "key": list(key)}
          )
    for response in responses:
      key = _key(response)
      for field, minimum, maximum in (
        ("threshold_scale", 0.0, 2.0),
        ("failure_probability", 0.0, 1.0),
        ("failure_sample", 0.0, 1.0),
        ("failure_severity", 0.0, 1.0),
        ("integrity_before", 0.0, 1.0),
        ("integrity_after", 0.0, 1.0),
        ("redundancy_group_availability_before", 0.0, 1.0),
        ("redundancy_group_availability_after", 0.0, 1.0),
      ):
        if not _finite_range(response[field], minimum=minimum, maximum=maximum):
          residuals["response_scalar_range"].append(
            {"case_id": case_id, "reason": f"{field}_out_of_range", "key": list(key)}
          )

  inconsistent_groups = [
    {"group_id": group, "systems": sorted(systems)}
    for group, systems in sorted(group_systems.items())
    if len(systems) != 1
  ]
  residuals["redundancy_group"].extend(inconsistent_groups)
  return {
    "metrics": {
      "row_count": len(rows),
      "load_row_count": total_loads,
      "response_row_count": total_responses,
      "unique_redundancy_group_count": len(group_systems),
      "unique_component_count": len(
        {(component, system) for group, components in group_components.items() for component in components for system in group_systems[group]}
      ),
      "load_response_identity_residual_count": len(residuals["load_response_identity"]),
      "load_scalar_range_residual_count": len(residuals["load_scalar_range"]),
      "response_scalar_range_residual_count": len(residuals["response_scalar_range"]),
      "primary_trace_residual_count": len(residuals["primary_trace"]),
      "redundancy_group_residual_count": len(residuals["redundancy_group"]),
    },
    "residuals": residuals,
  }


def _pair_validation(
  baseline_rows: list[dict[str, Any]], variant_rows: list[dict[str, Any]]
) -> dict[str, Any]:
  variant_by_id = {str(row["case_id"]): row for row in variant_rows}
  residuals: dict[str, list[dict[str, Any]]] = {
    "load_topology": [],
    "response_topology": [],
    "dependency_topology": [],
    "projection_propagation": [],
  }
  load_pair_count = 0
  response_pair_count = 0
  changed_load_count = 0
  changed_response_probability_count = 0
  changed_response_integrity_count = 0
  changed_dependency_availability_count = 0
  changed_dependency_effective_scale_count = 0
  changed_event_ids: set[str] = set()
  clamped_event_ids: set[str] = set()

  for baseline_row in baseline_rows:
    case_id = str(baseline_row["case_id"])
    variant_row = variant_by_id.get(case_id)
    if variant_row is None:
      residuals["load_topology"].append({"case_id": case_id, "reason": "missing_variant_row"})
      continue
    baseline_event = baseline_row["event"]
    variant_event = variant_row["event"]
    baseline_loads = {_key(row): row for row in baseline_event["component_mechanism_load_rows"]}
    variant_loads = {_key(row): row for row in variant_event["component_mechanism_load_rows"]}
    baseline_responses = {_key(row): row for row in baseline_event["component_response_rows"]}
    variant_responses = {_key(row): row for row in variant_event["component_response_rows"]}
    if set(baseline_loads) != set(variant_loads):
      residuals["load_topology"].append(
        {"case_id": case_id, "reason": "load_key_set_changed"}
      )
    if set(baseline_responses) != set(variant_responses):
      residuals["response_topology"].append(
        {"case_id": case_id, "reason": "response_key_set_changed"}
      )
    if bool(baseline_event["spatial_projection_effect_scale_clamped"]):
      clamped_event_ids.add(case_id)
    for key in sorted(set(baseline_loads) & set(variant_loads)):
      left = baseline_loads[key]
      right = variant_loads[key]
      load_pair_count += 1
      effect_delta = float(left["effect_scale"]) - float(right["effect_scale"])
      if abs(effect_delta) > TOLERANCE:
        changed_load_count += 1
        changed_event_ids.add(case_id)
        if not bool(baseline_event["spatial_projection_effect_scale_clamped"]):
          residuals["projection_propagation"].append(
            {"case_id": case_id, "key": list(key), "reason": "non_clamped_load_changed"}
          )
      if not math.isclose(
        float(left["mechanism_rod_cut_margin"]),
        float(right["mechanism_rod_cut_margin"]),
        rel_tol=1.0e-8,
        abs_tol=TOLERANCE,
      ):
        residuals["dependency_topology"].append(
          {"case_id": case_id, "key": list(key), "reason": "rod_cut_margin_changed"}
        )
      for field in (
        "direct_hit",
        "component_dependency_propagation_count",
        "component_dependency_target_system",
        "component_dependency_edge_type",
        "component_dependency_threshold",
        "component_dependency_delay_s",
        "component_dependency_direction",
        "component_dependency_provenance",
        "component_dependency_propagated",
      ):
        equal = left[field] == right[field]
        if isinstance(left[field], (int, float)) and isinstance(right[field], (int, float)):
          equal = math.isclose(float(left[field]), float(right[field]), rel_tol=1.0e-8, abs_tol=TOLERANCE)
        if not equal:
          residuals["dependency_topology"].append(
            {"case_id": case_id, "key": list(key), "field": field, "reason": "dependency_field_changed"}
          )
      if abs(
        float(left["component_dependency_source_availability"])
        - float(right["component_dependency_source_availability"])
      ) > TOLERANCE:
        changed_dependency_availability_count += 1
      if abs(
        float(left["component_dependency_effective_scale"])
        - float(right["component_dependency_effective_scale"])
      ) > TOLERANCE:
        changed_dependency_effective_scale_count += 1
    for key in sorted(set(baseline_responses) & set(variant_responses)):
      left = baseline_responses[key]
      right = variant_responses[key]
      response_pair_count += 1
      if abs(float(left["failure_probability"]) - float(right["failure_probability"])) > TOLERANCE:
        changed_response_probability_count += 1
      if abs(float(left["integrity_after"]) - float(right["integrity_after"])) > TOLERANCE:
        changed_response_integrity_count += 1
      for field in (
        "source_row_index",
        "owner_stage",
        "source_current_owner_stage",
        "failure_mode",
        "failure_mode_names",
        "failure_mode_source",
        "failure_mode_authority",
      ):
        if left[field] != right[field]:
          residuals["response_topology"].append(
            {"case_id": case_id, "key": list(key), "field": field, "reason": "response_topology_changed"}
          )
  return {
    "metrics": {
      "load_pair_count": load_pair_count,
      "response_pair_count": response_pair_count,
      "changed_load_effect_count": changed_load_count,
      "changed_response_probability_count": changed_response_probability_count,
      "changed_response_integrity_count": changed_response_integrity_count,
      "changed_dependency_availability_count": changed_dependency_availability_count,
      "changed_dependency_effective_scale_count": changed_dependency_effective_scale_count,
      "changed_event_count": len(changed_event_ids),
      "baseline_clamped_event_count": len(clamped_event_ids),
    },
    "residuals": residuals,
  }


def _component_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    for load in row["event"]["component_mechanism_load_rows"]:
      grouped[_key(load)].append(
        {
          "case_id": str(row["case_id"]),
          "direction": str(row["direction"]),
          "standoff_m": float(row["standoff_m"]),
          "heading_deg": float(row["detonation_attitude_deg"][0]),
          "effect_scale": float(load["effect_scale"]),
          "rod_cut_margin": float(load["mechanism_rod_cut_margin"]),
          "distance_m": float(load["distance_m"]),
        }
      )
  summary = []
  for key, values in sorted(grouped.items()):
    summary.append(
      {
        "component_name": key[0],
        "component_system": key[1],
        "component_redundancy_group_id": key[2],
        "row_count": len(values),
        "directions": sorted({item["direction"] for item in values}),
        "standoff_min_m": min(item["standoff_m"] for item in values),
        "standoff_max_m": max(item["standoff_m"] for item in values),
        "effect_scale_min": min(item["effect_scale"] for item in values),
        "effect_scale_max": max(item["effect_scale"] for item in values),
        "rod_cut_margin_min": min(item["rod_cut_margin"] for item in values),
        "rod_cut_margin_max": max(item["rod_cut_margin"] for item in values),
      }
    )
  return summary


def generate_report(*, seed: int = 20260914, limit: int | None = None) -> dict[str, Any]:
  common._configure_runtime_log_level()
  cases = _rod_cases()
  if limit is not None:
    cases = cases[: max(0, int(limit))]
  baseline_rows = _run_rows(
    cases, seed=seed, minimum_effect_scale=BASELINE_MIN_EFFECT_SCALE
  )
  variant_rows = _run_rows(
    cases, seed=seed, minimum_effect_scale=DECOUPLED_MIN_EFFECT_SCALE
  )
  baseline_validation = _variant_validation(baseline_rows)
  variant_validation = _variant_validation(variant_rows)
  pair_validation = _pair_validation(baseline_rows, variant_rows)
  variant_by_id = {str(row["case_id"]): row for row in variant_rows}
  gates = {
    "complete_matrix": (
      "passed"
      if len(baseline_rows) == common.EXPECTED_FAMILY_ROW_COUNT
      and len(variant_rows) == common.EXPECTED_FAMILY_ROW_COUNT
      else "failed"
    ),
    "baseline_load_response_identity": (
      "passed"
      if baseline_validation["metrics"]["load_response_identity_residual_count"] == 0
      else "failed"
    ),
    "variant_load_response_identity": (
      "passed"
      if variant_validation["metrics"]["load_response_identity_residual_count"] == 0
      else "failed"
    ),
    "component_load_scalar_range": (
      "passed"
      if baseline_validation["metrics"]["load_scalar_range_residual_count"] == 0
      and variant_validation["metrics"]["load_scalar_range_residual_count"] == 0
      else "failed"
    ),
    "component_response_scalar_range": (
      "passed"
      if baseline_validation["metrics"]["response_scalar_range_residual_count"] == 0
      and variant_validation["metrics"]["response_scalar_range_residual_count"] == 0
      else "failed"
    ),
    "primary_trace_closure": (
      "passed"
      if baseline_validation["metrics"]["primary_trace_residual_count"] == 0
      and variant_validation["metrics"]["primary_trace_residual_count"] == 0
      else "failed"
    ),
    "redundancy_group_closure": (
      "passed"
      if baseline_validation["metrics"]["redundancy_group_residual_count"] == 0
      and variant_validation["metrics"]["redundancy_group_residual_count"] == 0
      else "failed"
    ),
    "component_load_topology_stability": (
      "passed" if not pair_validation["residuals"]["load_topology"] else "failed"
    ),
    "response_topology_stability": (
      "passed" if not pair_validation["residuals"]["response_topology"] else "failed"
    ),
    "dependency_topology_stability": (
      "passed" if not pair_validation["residuals"]["dependency_topology"] else "failed"
    ),
    "spatial_to_component_propagation": (
      "passed"
      if pair_validation["metrics"]["changed_load_effect_count"] > 0
      and not pair_validation["residuals"]["projection_propagation"]
      else "failed"
    ),
  }
  gates["component_load_admission"] = (
    "passed" if all(value == "passed" for value in gates.values()) else "held"
  )
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
    "ablation": {
      "baseline": {
        "projection_min_effect_scale": BASELINE_MIN_EFFECT_SCALE,
        "projection_curve_floor_effect_scale": CURVE_FLOOR_EFFECT_SCALE,
      },
      "decoupled_variant": {
        "projection_min_effect_scale": DECOUPLED_MIN_EFFECT_SCALE,
        "projection_curve_floor_effect_scale": CURVE_FLOOR_EFFECT_SCALE,
      },
      "controlled_variables": [
        "same 192-case matrix",
        "same per-case seed",
        "same explicit expanding-ring-band settings",
        "same target database and component geometry",
      ],
    },
    "matrix": {
      "target_unit": "F-16C_Block50",
      "standoff_reference": "distance outward from the selected hitbox-envelope face",
      "directions": list(common.DIRECTION_ANCHORS),
      "standoff_distances_m": list(common.STANDOFF_DISTANCES_M),
      "detonation_headings_deg": list(common.ATTITUDES_DEG),
      "case_count": len(cases),
    },
    "admission_decision": {
      **gates,
      "next_gate": "P9 vulnerability/consequence admission",
      "blockers": [
        "all values remain synthetic structural evidence, not calibrated weapon data",
        "vulnerability/consequence authority remains separate from component-load topology",
        "integrated guidance-fuze-warhead Pk authority is not evaluated",
      ],
    },
    "evaluation": {
      "metrics": {
        "baseline": baseline_validation["metrics"],
        "decoupled_variant": variant_validation["metrics"],
        "paired": pair_validation["metrics"],
      },
      "gates": gates,
      "residuals": {
        "baseline": baseline_validation["residuals"],
        "decoupled_variant": variant_validation["residuals"],
        "paired": pair_validation["residuals"],
      },
    },
    "component_summary": _component_summary(baseline_rows),
    "pairs": [
      {
        "case_id": str(baseline["case_id"]),
        "direction": baseline["direction"],
        "standoff_m": float(baseline["standoff_m"]),
        "heading_deg": float(baseline["detonation_attitude_deg"][0]),
        "baseline_event": baseline["event"],
        "decoupled_event": variant_by_id[str(baseline["case_id"])]["event"],
      }
      for baseline in baseline_rows
    ],
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
  parser.add_argument("--seed", type=int, default=20260914)
  parser.add_argument("--limit", type=int, default=None, help="run only the first N rows")
  args = parser.parse_args()
  report = generate_report(seed=args.seed, limit=args.limit)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(
    json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
  )
  print(
    json.dumps(
      {
        "output": _relative_path(args.output),
        "admission_decision": report["admission_decision"],
        "metrics": report["evaluation"]["metrics"],
      },
      indent=2,
    )
  )
  return 0 if report["admission_decision"]["component_load_admission"] == "passed" else 2


if __name__ == "__main__":
  raise SystemExit(main())
