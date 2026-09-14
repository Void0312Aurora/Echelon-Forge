#!/usr/bin/env python3
"""Admit the explicit continuous-rod expanding ring-band geometry.

The probe bypasses guidance and fuze decisions.  It evaluates the real
EffectsModel path against the maintained F-16 hitbox/component geometry and
keeps legacy/default compatibility, sampling convergence, and topology as
separate gates.
"""

from __future__ import annotations

import argparse
import hashlib
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
SCHEMA_VERSION = "a2.continuous_rod_ring_band_admission.v1"
STATUS = "continuous_rod_ring_band_admission_generated"
GENERATED_ON = "2026-09-14"
BASE_AZIMUTHAL_SAMPLES = 720
LOW_AZIMUTHAL_SAMPLES = 288
BASE_POLAR_SAMPLES = 5
REFINED_POLAR_SAMPLES = 9
BAND_HALF_ANGLE_DEG = 6.0
HALF_AZIMUTHAL_STEP_DEG = 180.0 / BASE_AZIMUTHAL_SAMPLES
MAX_COVERAGE_DELTA = 0.005
MAX_EFFECT_SCALE_DELTA = 0.01
DEFAULT_OUTPUT_PATH = Path(
  resolve_repo_path(
    "docs",
    "systems",
    "effects",
    "reviews",
    "continuous_rod_ring_band_admission_20260914",
    "review_packets",
    "continuous_rod_ring_band_admission_20260914.json",
  )
)
FRAGMENTATION_REPORT_PATH = Path(
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
  explicit: bool,
  azimuthal_samples: int = BASE_AZIMUTHAL_SAMPLES,
  polar_samples: int = BASE_POLAR_SAMPLES,
  phase_deg: float = 0.0,
) -> list[dict[str, Any]]:
  return [
    common._event_row(
      case,
      seed + index,
      explicit_continuous_rod=explicit,
      continuous_rod_band_half_angle_deg=BAND_HALF_ANGLE_DEG,
      continuous_rod_azimuthal_samples=azimuthal_samples,
      continuous_rod_polar_samples=polar_samples,
      continuous_rod_azimuthal_phase_deg=phase_deg,
    )
    for index, case in enumerate(cases)
  ]


def _index_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
  return {str(row["case_id"]): row for row in rows}


def _event_value(row: dict[str, Any], field: str) -> Any:
  return row["event"][field]


def _compare_sampling_variant(
  baseline_rows: list[dict[str, Any]],
  variant_rows: list[dict[str, Any]],
  *,
  label: str,
  configuration: dict[str, Any],
) -> dict[str, Any]:
  baseline = _index_rows(baseline_rows)
  variant = _index_rows(variant_rows)
  missing_case_ids = sorted(set(baseline) ^ set(variant))
  classification_differences: list[dict[str, Any]] = []
  coverage_deltas: list[float] = []
  effect_deltas: list[float] = []
  for case_id in sorted(set(baseline) & set(variant)):
    baseline_event = baseline[case_id]["event"]
    variant_event = variant[case_id]["event"]
    baseline_hit = bool(baseline_event["continuous_rod_ring_band_intersection"])
    variant_hit = bool(variant_event["continuous_rod_ring_band_intersection"])
    if baseline_hit != variant_hit:
      classification_differences.append(
        {
          "case_id": case_id,
          "baseline_intersection": baseline_hit,
          "variant_intersection": variant_hit,
        }
      )
    coverage_deltas.append(
      abs(
        float(baseline_event["continuous_rod_angular_coverage_fraction"])
        - float(variant_event["continuous_rod_angular_coverage_fraction"])
      )
    )
    effect_deltas.append(
      abs(
        float(baseline_event["spatial_projection_effect_scale"])
        - float(variant_event["spatial_projection_effect_scale"])
      )
    )
  maximum_coverage_delta = max(coverage_deltas, default=math.inf)
  maximum_effect_delta = max(effect_deltas, default=math.inf)
  passed = bool(
    baseline
    and not missing_case_ids
    and not classification_differences
    and maximum_coverage_delta <= MAX_COVERAGE_DELTA + 1.0e-12
    and maximum_effect_delta <= MAX_EFFECT_SCALE_DELTA + 1.0e-12
  )
  return {
    "label": label,
    "status": "passed" if passed else "failed",
    "configuration": configuration,
    "compared_row_count": len(coverage_deltas),
    "missing_case_count": len(missing_case_ids),
    "classification_difference_count": len(classification_differences),
    "maximum_coverage_fraction_delta": maximum_coverage_delta,
    "mean_coverage_fraction_delta": (
      sum(coverage_deltas) / len(coverage_deltas) if coverage_deltas else math.inf
    ),
    "maximum_effect_scale_delta": maximum_effect_delta,
    "mean_effect_scale_delta": (
      sum(effect_deltas) / len(effect_deltas) if effect_deltas else math.inf
    ),
    "limits": {
      "maximum_coverage_fraction_delta": MAX_COVERAGE_DELTA,
      "maximum_effect_scale_delta": MAX_EFFECT_SCALE_DELTA,
      "classification_difference_count": 0,
    },
    "missing_case_ids": missing_case_ids,
    "classification_differences": classification_differences,
  }


def _geometry_evaluation(rows: list[dict[str, Any]]) -> dict[str, Any]:
  common_evaluation = common.evaluate_rows(rows)
  configuration_failures: list[dict[str, Any]] = []
  geometry_closure_failures: list[dict[str, Any]] = []
  for row in rows:
    event = row["event"]
    case_id = str(row["case_id"])
    if not (
      bool(event["continuous_rod_ring_band_active"])
      and str(event["continuous_rod_spatial_model"]) == "expanding_ring_band"
      and common._close(
        float(event["continuous_rod_band_half_angle_deg"]), BAND_HALF_ANGLE_DEG
      )
      and int(event["continuous_rod_azimuthal_sample_count"])
      == BASE_AZIMUTHAL_SAMPLES
      and int(event["continuous_rod_polar_sample_count"]) == BASE_POLAR_SAMPLES
    ):
      configuration_failures.append({"case_id": case_id, "event": event})

    intersection = bool(event["continuous_rod_ring_band_intersection"])
    trace_valid = bool(event["spatial_projection_trace_valid"])
    intersecting_count = int(
      event["continuous_rod_intersecting_azimuthal_sample_count"]
    )
    sample_count = int(event["continuous_rod_azimuthal_sample_count"])
    coverage = float(event["continuous_rod_angular_coverage_fraction"])
    nearest_distance = float(event["continuous_rod_nearest_intersection_distance_m"])
    effect_scale = float(event["spatial_projection_effect_scale"])
    expected_coverage = intersecting_count / sample_count if sample_count else 0.0
    closure_pass = bool(
      intersection == (intersecting_count > 0)
      and intersection == trace_valid
      and intersection == (effect_scale > 0.0)
      and common._close(coverage, expected_coverage)
      and ((nearest_distance > 0.0) if intersection else common._close(nearest_distance, 0.0))
      and (
        not trace_valid
        or (
          common._close(float(event["spatial_projection_axis_weight"]), 1.0)
          and common._close(
            float(event["spatial_projection_orientation_weight"]), 1.0
          )
        )
      )
    )
    if not closure_pass:
      geometry_closure_failures.append(
        {
          "case_id": case_id,
          "intersection": intersection,
          "trace_valid": trace_valid,
          "intersecting_azimuthal_sample_count": intersecting_count,
          "coverage_fraction": coverage,
          "expected_coverage_fraction": expected_coverage,
          "nearest_intersection_distance_m": nearest_distance,
          "effect_scale": effect_scale,
        }
      )

  indexed = {
    (
      str(row["direction"]),
      float(row["standoff_m"]),
      float(row["detonation_attitude_deg"][0]),
    ): row
    for row in rows
  }
  half_turn_violations: list[dict[str, Any]] = []
  for direction in common.DIRECTION_ANCHORS:
    for standoff_m in common.STANDOFF_DISTANCES_M:
      for heading_deg in common.ATTITUDES_DEG[:4]:
        first = indexed.get((direction, standoff_m, heading_deg))
        second = indexed.get((direction, standoff_m, heading_deg + 180.0))
        if first is None or second is None:
          continue
        first_event = first["event"]
        second_event = second["event"]
        if not (
          bool(first_event["continuous_rod_ring_band_intersection"])
          == bool(second_event["continuous_rod_ring_band_intersection"])
          and common._close(
            float(first_event["continuous_rod_angular_coverage_fraction"]),
            float(second_event["continuous_rod_angular_coverage_fraction"]),
            tolerance=1.0e-6,
          )
          and common._close(
            float(first_event["spatial_projection_effect_scale"]),
            float(second_event["spatial_projection_effect_scale"]),
            tolerance=1.0e-6,
          )
        ):
          half_turn_violations.append(
            {
              "direction": direction,
              "standoff_m": standoff_m,
              "heading_pair_deg": [heading_deg, heading_deg + 180.0],
            }
          )

  mirror_violations: list[dict[str, Any]] = []
  for standoff_m in common.STANDOFF_DISTANCES_M:
    for heading_deg in common.ATTITUDES_DEG:
      right = indexed.get(("right", standoff_m, heading_deg))
      left = indexed.get(("left", standoff_m, (-heading_deg) % 360.0))
      if right is None or left is None:
        continue
      right_event = right["event"]
      left_event = left["event"]
      if not (
        bool(right_event["continuous_rod_ring_band_intersection"])
        == bool(left_event["continuous_rod_ring_band_intersection"])
        and common._close(
          float(right_event["continuous_rod_angular_coverage_fraction"]),
          float(left_event["continuous_rod_angular_coverage_fraction"]),
          tolerance=1.0e-6,
        )
        and common._close(
          float(right_event["spatial_projection_effect_scale"]),
          float(left_event["spatial_projection_effect_scale"]),
          tolerance=1.0e-6,
        )
      ):
        mirror_violations.append(
          {
            "standoff_m": standoff_m,
            "right_heading_deg": heading_deg,
            "left_heading_deg": (-heading_deg) % 360.0,
          }
        )

  grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
  for row in rows:
    grouped[(str(row["direction"]), float(row["detonation_attitude_deg"][0]))].append(row)
  distance_topology_violations: list[dict[str, Any]] = []
  distance_effect_violations: list[dict[str, Any]] = []
  for (direction, heading_deg), group in grouped.items():
    ordered = sorted(group, key=lambda item: float(item["standoff_m"]))
    for near, far in zip(ordered, ordered[1:]):
      near_event = near["event"]
      far_event = far["event"]
      if not bool(near_event["continuous_rod_ring_band_intersection"]) and bool(
        far_event["continuous_rod_ring_band_intersection"]
      ):
        distance_topology_violations.append(
          {
            "direction": direction,
            "heading_deg": heading_deg,
            "near_standoff_m": near["standoff_m"],
            "far_standoff_m": far["standoff_m"],
          }
        )
      if float(far_event["spatial_projection_effect_scale"]) > float(
        near_event["spatial_projection_effect_scale"]
      ) + 1.0e-9:
        distance_effect_violations.append(
          {
            "direction": direction,
            "heading_deg": heading_deg,
            "near_standoff_m": near["standoff_m"],
            "far_standoff_m": far["standoff_m"],
            "near_effect_scale": near_event["spatial_projection_effect_scale"],
            "far_effect_scale": far_event["spatial_projection_effect_scale"],
          }
        )

  axial_cases = [
    indexed.get((direction, standoff_m, heading_deg))
    for direction, headings in {
      "front": (0.0, 180.0),
      "back": (0.0, 180.0),
      "right": (90.0, 270.0),
      "left": (90.0, 270.0),
    }.items()
    for standoff_m in common.STANDOFF_DISTANCES_M
    for heading_deg in headings
  ]
  vertical_equatorial_cases = [
    indexed.get((direction, standoff_m, heading_deg))
    for direction in ("up", "down")
    for standoff_m in common.STANDOFF_DISTANCES_M
    for heading_deg in common.ATTITUDES_DEG
  ]
  axial_rejection_failure_count = sum(
    1
    for row in axial_cases
    if row is None
    or bool(_event_value(row, "continuous_rod_ring_band_intersection"))
  )
  vertical_equatorial_hit_failure_count = sum(
    1
    for row in vertical_equatorial_cases
    if row is None
    or not bool(_event_value(row, "continuous_rod_ring_band_intersection"))
  )
  hit_count = sum(
    1
    for row in rows
    if bool(_event_value(row, "continuous_rod_ring_band_intersection"))
  )
  minimum_bound_clamp_count = sum(
    1
    for row in rows
    if bool(_event_value(row, "spatial_projection_effect_scale_clamped"))
    and common._close(
      float(_event_value(row, "spatial_projection_effect_scale")),
      float(_event_value(row, "spatial_projection_min_bound")),
    )
  )
  maximum_bound_clamp_count = sum(
    1
    for row in rows
    if bool(_event_value(row, "spatial_projection_effect_scale_clamped"))
    and common._close(
      float(_event_value(row, "spatial_projection_effect_scale")),
      float(_event_value(row, "spatial_projection_max_bound")),
    )
  )
  metrics = {
    "row_count": len(rows),
    "expected_row_count": common.EXPECTED_FAMILY_ROW_COUNT,
    "intersection_count": hit_count,
    "non_intersection_count": len(rows) - hit_count,
    "configuration_failure_count": len(configuration_failures),
    "geometry_closure_failure_count": len(geometry_closure_failures),
    "half_turn_symmetry_violation_count": len(half_turn_violations),
    "left_right_mirror_violation_count": len(mirror_violations),
    "distance_topology_violation_count": len(distance_topology_violations),
    "distance_effect_monotonic_violation_count": len(distance_effect_violations),
    "axial_rejection_failure_count": axial_rejection_failure_count,
    "vertical_equatorial_hit_failure_count": vertical_equatorial_hit_failure_count,
    "minimum_bound_clamp_count": minimum_bound_clamp_count,
    "maximum_bound_clamp_count": maximum_bound_clamp_count,
    "model_owned_trace_valid_count": int(
      common_evaluation["metrics"]["trace_valid_count"]
    ),
  }
  passed = bool(
    len(rows) == common.EXPECTED_FAMILY_ROW_COUNT
    and hit_count > 0
    and hit_count < len(rows)
    and common_evaluation["diagnostic_trace_gate_pass"]
    and all(
      metrics[name] == 0
      for name in (
        "configuration_failure_count",
        "geometry_closure_failure_count",
        "half_turn_symmetry_violation_count",
        "left_right_mirror_violation_count",
        "distance_topology_violation_count",
        "distance_effect_monotonic_violation_count",
        "axial_rejection_failure_count",
        "vertical_equatorial_hit_failure_count",
      )
    )
  )
  return {
    "status": "passed" if passed else "failed",
    "metrics": metrics,
    "common_projection_trace_evaluation": common_evaluation,
    "residuals": {
      "configuration_failures": configuration_failures,
      "geometry_closure_failures": geometry_closure_failures,
      "half_turn_symmetry_violations": half_turn_violations,
      "left_right_mirror_violations": mirror_violations,
      "distance_topology_violations": distance_topology_violations,
      "distance_effect_monotonic_violations": distance_effect_violations,
    },
  }


def _topology_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  summary: list[dict[str, Any]] = []
  for direction in common.DIRECTION_ANCHORS:
    for standoff_m in common.STANDOFF_DISTANCES_M:
      group = [
        row
        for row in rows
        if str(row["direction"]) == direction
        and common._close(float(row["standoff_m"]), standoff_m)
      ]
      effects = [float(_event_value(row, "spatial_projection_effect_scale")) for row in group]
      coverages = [
        float(_event_value(row, "continuous_rod_angular_coverage_fraction"))
        for row in group
      ]
      summary.append(
        {
          "direction": direction,
          "standoff_m": standoff_m,
          "intersection_count": sum(
            1
            for row in group
            if bool(_event_value(row, "continuous_rod_ring_band_intersection"))
          ),
          "heading_count": len(group),
          "mean_effect_scale": sum(effects) / len(effects) if effects else 0.0,
          "maximum_effect_scale": max(effects, default=0.0),
          "mean_angular_coverage_fraction": (
            sum(coverages) / len(coverages) if coverages else 0.0
          ),
          "maximum_angular_coverage_fraction": max(coverages, default=0.0),
        }
      )
  return summary


def _fragmentation_evidence() -> dict[str, Any]:
  if not FRAGMENTATION_REPORT_PATH.exists():
    return {
      "status": "not_evaluated",
      "path": _relative_path(FRAGMENTATION_REPORT_PATH),
      "reason": "retained_fragmentation_report_missing",
    }
  payload_bytes = FRAGMENTATION_REPORT_PATH.read_bytes()
  payload = json.loads(payload_bytes.decode("utf-8"))
  decision = str(
    payload.get("admission_decision", {}).get(
      "fragmentation_angular_field_admission", "not_evaluated"
    )
  )
  return {
    "status": decision,
    "path": _relative_path(FRAGMENTATION_REPORT_PATH),
    "sha256": hashlib.sha256(payload_bytes).hexdigest(),
    "generated_on": payload.get("generated_on"),
    "schema_version": payload.get("schema_version"),
  }


def generate_report(*, seed: int = 20260914, limit: int | None = None) -> dict[str, Any]:
  common._configure_runtime_log_level()
  cases = _rod_cases()
  if limit is not None:
    cases = cases[: max(0, int(limit))]
  rows = _run_rows(cases, seed=seed, explicit=True)
  geometry_evaluation = _geometry_evaluation(rows)

  if limit is None:
    low_resolution_rows = _run_rows(
      cases,
      seed=seed,
      explicit=True,
      azimuthal_samples=LOW_AZIMUTHAL_SAMPLES,
    )
    phase_shift_rows = _run_rows(
      cases,
      seed=seed,
      explicit=True,
      phase_deg=HALF_AZIMUTHAL_STEP_DEG,
    )
    refined_polar_rows = _run_rows(
      cases,
      seed=seed,
      explicit=True,
      polar_samples=REFINED_POLAR_SAMPLES,
    )
    sampling_convergence = {
      "status": "pending",
      "variants": [
        _compare_sampling_variant(
          rows,
          low_resolution_rows,
          label="azimuthal_resolution_288_vs_720",
          configuration={
            "azimuthal_samples": LOW_AZIMUTHAL_SAMPLES,
            "polar_samples": BASE_POLAR_SAMPLES,
            "phase_deg": 0.0,
          },
        ),
        _compare_sampling_variant(
          rows,
          phase_shift_rows,
          label="azimuthal_half_step_phase_shift",
          configuration={
            "azimuthal_samples": BASE_AZIMUTHAL_SAMPLES,
            "polar_samples": BASE_POLAR_SAMPLES,
            "phase_deg": HALF_AZIMUTHAL_STEP_DEG,
          },
        ),
        _compare_sampling_variant(
          rows,
          refined_polar_rows,
          label="polar_resolution_5_vs_9",
          configuration={
            "azimuthal_samples": BASE_AZIMUTHAL_SAMPLES,
            "polar_samples": REFINED_POLAR_SAMPLES,
            "phase_deg": 0.0,
          },
        ),
      ],
    }
    sampling_convergence["status"] = (
      "passed"
      if all(item["status"] == "passed" for item in sampling_convergence["variants"])
      else "failed"
    )
    legacy_rows = _run_rows(cases, seed=seed, explicit=False)
    legacy_regression = common._rod_baseline_regression(legacy_rows)
    legacy_regression["explicit_ring_band_active_count"] = sum(
      1
      for row in legacy_rows
      if bool(_event_value(row, "continuous_rod_ring_band_active"))
    )
    if legacy_regression["explicit_ring_band_active_count"] != 0:
      legacy_regression["status"] = "failed"
  else:
    sampling_convergence = {
      "status": "not_evaluated",
      "reason": "limited_probe",
      "variants": [],
    }
    legacy_regression = {
      "status": "not_evaluated",
      "reason": "limited_probe",
    }

  fragmentation_evidence = _fragmentation_evidence()
  rod_admission_pass = bool(
    geometry_evaluation["status"] == "passed"
    and sampling_convergence["status"] == "passed"
    and legacy_regression["status"] == "passed"
  )
  explicit_family_topology_pass = bool(
    rod_admission_pass and fragmentation_evidence["status"] == "passed"
  )
  blockers = [
    "the 6 degree band width is a synthetic structural-admission parameter, not a calibrated weapon profile",
    "default weapon data still uses the legacy side-sweep model until profile promotion is separately approved",
    (
      f"the projection minimum bound clamps "
      f"{geometry_evaluation['metrics']['minimum_bound_clamp_count']} surviving 10 m cases; "
      "P7 floor/clamp admission remains open"
    ),
    "component-load response topology and vulnerability/consequence remain separate admission gates",
    "integrated guidance-fuze-warhead Pk authority is not evaluated",
  ]
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
      "target_hitbox_envelope_m": common.TARGET_HITBOX_ENVELOPE,
      "standoff_reference": "distance outward from the selected hitbox-envelope face",
      "directions": list(common.DIRECTION_ANCHORS),
      "standoff_distances_m": list(common.STANDOFF_DISTANCES_M),
      "detonation_headings_deg": list(common.ATTITUDES_DEG),
      "band_half_angle_deg": BAND_HALF_ANGLE_DEG,
      "azimuthal_samples": BASE_AZIMUTHAL_SAMPLES,
      "polar_samples": BASE_POLAR_SAMPLES,
      "case_count": len(cases),
    },
    "admission_decision": {
      "continuous_rod_expanding_ring_band_admission": (
        "passed" if rod_admission_pass else "held"
      ),
      "explicit_warhead_family_topology_gate": (
        "passed" if explicit_family_topology_pass else "held"
      ),
      "continuous_rod_projection_floor_clamp_admission": "held",
      "warhead_spatial_field_structural_admission": "held",
      "legacy_default_compatibility": legacy_regression["status"],
      "default_profile_promotion": "not_evaluated",
      "component_load_admission": "not_evaluated",
      "vulnerability_consequence_admission": "not_evaluated",
      "integrated_kill_chain_admission": "not_evaluated",
      "blockers": blockers,
    },
    "geometry_evaluation": geometry_evaluation,
    "sampling_convergence": sampling_convergence,
    "legacy_default_regression": legacy_regression,
    "retained_fragmentation_evidence": fragmentation_evidence,
    "topology_summary": _topology_summary(rows),
    "rows": rows,
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
        "geometry_metrics": report["geometry_evaluation"]["metrics"],
        "sampling_convergence": report["sampling_convergence"]["status"],
      },
      indent=2,
    )
  )
  return (
    0
    if report["admission_decision"]["continuous_rod_expanding_ring_band_admission"]
    == "passed"
    else 2
  )


if __name__ == "__main__":
  raise SystemExit(main())
