#!/usr/bin/env python3
"""Generate KCES before-report rows from the decoupled kill-chain probe."""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports  # noqa: E402


ensure_repo_imports()

from tools.diagnostics import kill_chain_decoupling_probe as decoupling_probe  # noqa: E402
from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.component_detail_projection import (  # noqa: E402
  COMPONENT_DETAIL_SCHEMA_VERSION,
  component_detail_from_runtime_facade,
  component_load_metrics,
  component_response_metrics,
  empty_component_detail,
)


SCHEMA_VERSION = "a2.kill_chain_expectation_before_report.v1"
CASE_GRID_SCHEMA_VERSION = "a2.kill_chain_expectation_case_grid.v1"
HEATMAP_ROW_SCHEMA_VERSION = "a2.kill_chain_expectation_heatmap_row.v1"
PROFILE_ID = "KCES-AIM120C-LIKE-FIGHTER-V0"
DEFAULT_SEED = 20260621
DEFAULT_R_FUZE_M = 15.0
SUPPORTED_RUNTIME_TARGET_MOTION_LAYERS = {"nonmaneuvering_constant_velocity"}
DEFAULT_EFFECT_VARIANTS = (
  "REV-RUNTIME-PROJECTION",
  "REV-EQ-FUZE",
  "REV-SMALLER-LOAD",
)

CV_ANCHOR_CLASSES: dict[float, dict[float, str]] = {
  4.0: {0.0: "N", 15.0: "N", 30.0: "N", 45.0: "N", 60.0: "M", 75.0: "M", 90.0: "O"},
  6.0: {0.0: "N", 15.0: "N", 30.0: "N", 45.0: "N", 60.0: "M", 75.0: "O", 90.0: "O"},
  8.0: {0.0: "N", 15.0: "N", 30.0: "N", 45.0: "M", 60.0: "M", 75.0: "O", 90.0: "O"},
  10.0: {0.0: "N", 15.0: "N", 30.0: "M", 45.0: "M", 60.0: "O", 75.0: "O", 90.0: "O"},
  12.0: {0.0: "N", 15.0: "M", 30.0: "M", 45.0: "O", 60.0: "O", 75.0: "O", 90.0: "O"},
  16.0: {0.0: "M", 15.0: "M", 30.0: "O", 45.0: "O", 60.0: "O", 75.0: "O", 90.0: "O"},
}
MILD_MANEUVER_ANCHOR_CLASSES: dict[float, dict[float, str]] = {
  6.0: {0.0: "N", 30.0: "M", 60.0: "O"},
  8.0: {0.0: "M", 30.0: "M", 60.0: "O"},
  10.0: {0.0: "M", 30.0: "O", 60.0: "O"},
}


def _finite_float(value: Any, default: float = float("nan")) -> float:
  try:
    out = float(value)
  except Exception:
    return float(default)
  return out if math.isfinite(out) else float(default)


def _finite_or_none(value: Any) -> float | None:
  out = _finite_float(value)
  return out if math.isfinite(out) else None


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
  top = _finite_or_none(numerator)
  bottom = _finite_or_none(denominator)
  if top is None or bottom is None or abs(bottom) <= 1.0e-12:
    return None
  return float(top) / float(bottom)


def _token(value: float) -> str:
  text = f"{float(value):g}"
  return text.replace("-", "m").replace(".", "p")


def _signed_bearings(offset_deg: float) -> tuple[float, ...]:
  offset = float(offset_deg)
  if abs(offset) <= 1.0e-9:
    return (0.0,)
  return (-offset, offset)


def _motion_short_name(target_motion_layer: str) -> str:
  if target_motion_layer == "nonmaneuvering_constant_velocity":
    return "cv"
  if target_motion_layer == "mild_maneuver":
    return "mild"
  return str(target_motion_layer).replace("_", "-")


def _case_id(
  *,
  grid_tier: str,
  target_motion_layer: str,
  range_km: float,
  signed_bearing_deg: float,
) -> str:
  sign = "p" if float(signed_bearing_deg) >= 0.0 else "m"
  return (
    f"kces_{grid_tier.replace('-', '_')}_"
    f"{_motion_short_name(target_motion_layer)}_"
    f"{_token(range_km)}km_{sign}{_token(abs(float(signed_bearing_deg)))}deg"
  )


def _iter_anchor_cells(
  target_motion_layer: str,
) -> tuple[tuple[float, float, str], ...]:
  if target_motion_layer == "nonmaneuvering_constant_velocity":
    table = CV_ANCHOR_CLASSES
  elif target_motion_layer == "mild_maneuver":
    table = MILD_MANEUVER_ANCHOR_CLASSES
  else:
    return ()
  cells: list[tuple[float, float, str]] = []
  for range_km in sorted(table):
    for offset_deg in sorted(table[range_km]):
      cells.append((float(range_km), float(offset_deg), str(table[range_km][offset_deg])))
  return tuple(cells)


def _parse_csv(value: str) -> tuple[str, ...]:
  return tuple(item.strip() for item in str(value).split(",") if item.strip())


def generate_case_grid(
  *,
  grid_tier: str = "anchor-grid",
  target_motion_layers: tuple[str, ...] = ("nonmaneuvering_constant_velocity",),
  seed: int = DEFAULT_SEED,
  case_ids: tuple[str, ...] = (),
  case_limit: int = 0,
) -> list[dict[str, Any]]:
  if grid_tier != "anchor-grid":
    raise ValueError(f"unsupported grid_tier for initial harness: {grid_tier}")

  rows: list[dict[str, Any]] = []
  requested_ids = set(case_ids)
  sample_index = 0
  for layer in target_motion_layers:
    for range_km, offset_deg, launch_class in _iter_anchor_cells(layer):
      for bearing_deg in _signed_bearings(offset_deg):
        case_id = _case_id(
          grid_tier=grid_tier,
          target_motion_layer=layer,
          range_km=range_km,
          signed_bearing_deg=bearing_deg,
        )
        if requested_ids and case_id not in requested_ids:
          continue
        rows.append(
          {
            "schema_version": CASE_GRID_SCHEMA_VERSION,
            "profile_id": PROFILE_ID,
            "case_id": case_id,
            "grid_tier": str(grid_tier),
            "sample_index": sample_index,
            "seed": int(seed),
            "target_motion_layer": str(layer),
            "range_km": float(range_km),
            "range_m": float(range_km) * 1000.0,
            "offset_deg": float(offset_deg),
            "signed_bearing_deg": float(bearing_deg),
            "launch_class": str(launch_class),
            "runtime_supported": layer in SUPPORTED_RUNTIME_TARGET_MOTION_LAYERS,
            "skip_reason": (
              ""
              if layer in SUPPORTED_RUNTIME_TARGET_MOTION_LAYERS
              else "target_motion_layer_not_supported_by_current_probe"
            ),
          }
        )
        sample_index += 1
        if case_limit > 0 and len(rows) >= int(case_limit):
          return rows
  return rows


def _effect_band(rho_effect: float | None) -> str:
  if rho_effect is None:
    return "unclassified_missing_R_effect"
  if rho_effect <= 0.25:
    return "core"
  if rho_effect <= 0.50:
    return "effective"
  if rho_effect <= 0.80:
    return "outer_effective"
  if rho_effect <= 1.00:
    return "edge"
  return "outside_effect"


def _stage_observed(case: dict[str, Any], stage: str) -> dict[str, Any]:
  for row in list(case.get("stage_abstractions", []) or []):
    if str(row.get("abstraction_stage", "") or "") == str(stage):
      value = row.get("observed", {})
      return dict(value) if isinstance(value, dict) else {}
  return {}


def _radius_for_variant(
  variant: str,
  *,
  r_fuze_m: float,
  runtime_facade: dict[str, Any],
  declared_effect_radius_m: float | None,
) -> float | None:
  if variant == "REV-RUNTIME-PROJECTION":
    return _finite_or_none(
      dict(runtime_facade.get("warhead_load_field", {}) or {}).get(
        "lethal_radius_m"
      )
    )
  if variant == "REV-EQ-FUZE":
    return float(r_fuze_m)
  if variant == "REV-SMALLER-LOAD":
    return declared_effect_radius_m
  return None


def _guidance_expectation_status(
  *,
  launch_class: str,
  entered_r_fuze: bool | None,
  load_metrics: dict[str, Any],
  response_metrics: dict[str, Any],
) -> str:
  if entered_r_fuze is None:
    return "missing_guidance_fact"
  if launch_class == "N":
    return "satisfied" if entered_r_fuze else "guidance_or_model_residual"
  if launch_class == "M":
    return "observed_marginal"
  if launch_class == "O":
    strong_load = (
      _finite_or_none(load_metrics.get("strongest_component_effect_scale")) or 0.0
    ) > 0.0
    response_seen = (
      _finite_or_none(response_metrics.get("max_failure_probability")) or 0.0
    ) > 0.0
    if entered_r_fuze or strong_load or response_seen:
      return "negative_control_alert"
    return "negative_control_satisfied"
  return "unknown_launch_class"


def _authority_boundary_status(report: dict[str, Any], runtime_facade: dict[str, Any]) -> str:
  authority = dict(report.get("authority_boundary", {}) or {})
  runtime_retuning = bool(runtime_facade.get("runtime_parameter_retuning")) or bool(
    authority.get("runtime_parameter_retuning")
  )
  calibration = bool(runtime_facade.get("calibration_authority")) or bool(
    authority.get("calibration_authority")
  )
  real_pk = bool(runtime_facade.get("real_world_pk")) or bool(authority.get("real_world_pk"))
  deterministic_fuze = bool(authority.get("deterministic_fuze_authority"))
  if runtime_retuning or calibration or real_pk or deterministic_fuze:
    return "authority_violation"
  return "engineering_proxy_guarded"


def _scalar_guard_status(case: dict[str, Any]) -> str:
  load_summary = dict(case.get("component_load_factor_summary", {}) or {})
  if int(load_summary.get("rows_with_response_fields_on_load_row", 0) or 0) > 0:
    return "response_owner_violation"
  scalar_summary = dict(case.get("scalar_coupling_summary", {}) or {})
  if int(scalar_summary.get("scalar_count", 0) or 0) > 0:
    return "diagnostic_current"
  return "missing_scalar_ledger"


def _project_heatmap_rows(
  *,
  grid_case: dict[str, Any],
  probe_case: dict[str, Any] | None,
  probe_report: dict[str, Any],
  effect_variants: tuple[str, ...],
  r_fuze_m: float,
  declared_effect_radius_m: float | None,
) -> list[dict[str, Any]]:
  if probe_case is None:
    return [
      {
        "schema_version": HEATMAP_ROW_SCHEMA_VERSION,
        "identity": {
          "schema_version": HEATMAP_ROW_SCHEMA_VERSION,
          "profile_id": PROFILE_ID,
          "case_id": grid_case["case_id"],
          "grid_tier": grid_case["grid_tier"],
          "sample_index": int(grid_case["sample_index"]),
          "seed": int(grid_case["seed"]),
        },
        "launch_window": {
          "target_motion_layer": grid_case["target_motion_layer"],
          "range_km": grid_case["range_km"],
          "offset_deg": grid_case["offset_deg"],
          "signed_bearing_deg": grid_case["signed_bearing_deg"],
          "launch_class": grid_case["launch_class"],
        },
        "run_status": "not_run",
        "skip_reason": grid_case.get("skip_reason", "case_not_run"),
        "guidance_approach": {"guidance_expectation_status": "not_run"},
        "fuze_decision": {},
        "warhead_load_field": {
          "R_effect_variant": "not_evaluated",
          "R_effect_m": None,
          "rho_effect_case": None,
          "effect_band": "not_evaluated",
        },
        "component_response": {},
        "component_detail": empty_component_detail(
          r_effect_variant="not_evaluated",
          r_effect_m=None,
        ),
        "consequence_projection": {},
        "guards": {
          "scalar_owner_guard_status": "not_run",
          "unexpected_stage_delta": "not_applicable_before_report",
          "authority_boundary_status": "engineering_proxy_guarded",
          "runtime_parameter_retuning": False,
        },
      }
    ]

  runtime_facade = dict(probe_case.get("runtime_facade", {}) or {})
  approach = dict(runtime_facade.get("approach_fact", {}) or {})
  fuze = dict(runtime_facade.get("fuze_decision", {}) or {})
  consequence = dict(runtime_facade.get("consequence_projection", {}) or {})
  consequence_observed = _stage_observed(probe_case, "consequence_projection")
  nearest_distance = _finite_or_none(probe_case.get("nearest_miss_distance_m"))
  if nearest_distance is None:
    nearest_distance = _finite_or_none(probe_case.get("truth_min_distance_m"))
  rho_fuze = _safe_ratio(nearest_distance, r_fuze_m)
  entered_r_fuze = None if rho_fuze is None else bool(rho_fuze <= 1.0)
  load = component_load_metrics(runtime_facade)
  response = component_response_metrics(runtime_facade)
  guidance_status = _guidance_expectation_status(
    launch_class=str(grid_case["launch_class"]),
    entered_r_fuze=entered_r_fuze,
    load_metrics=load,
    response_metrics=response,
  )
  base = {
    "schema_version": HEATMAP_ROW_SCHEMA_VERSION,
    "identity": {
      "schema_version": HEATMAP_ROW_SCHEMA_VERSION,
      "profile_id": PROFILE_ID,
      "case_id": grid_case["case_id"],
      "grid_tier": grid_case["grid_tier"],
      "sample_index": int(grid_case["sample_index"]),
      "seed": int(grid_case["seed"]),
    },
    "launch_window": {
      "target_motion_layer": grid_case["target_motion_layer"],
      "range_km": grid_case["range_km"],
      "offset_deg": grid_case["offset_deg"],
      "signed_bearing_deg": grid_case["signed_bearing_deg"],
      "launch_class": grid_case["launch_class"],
    },
    "run_status": "generated",
    "guidance_approach": {
      "nearest_distance_m": nearest_distance,
      "nearest_approach_time_s": _finite_or_none(
        approach.get("nearest_approach_time_s")
      ),
      "closure_mps": _finite_or_none(approach.get("closure_mps"))
      or _finite_or_none(dict(probe_case.get("effect", {}) or {}).get("closure_mps")),
      "max_achieved_lateral_g": _finite_or_none(
        probe_case.get("max_achieved_lateral_g")
      ),
      "R_fuze_m": float(r_fuze_m),
      "rho_fuze": rho_fuze,
      "entered_R_fuze": entered_r_fuze,
      "guidance_expectation_status": guidance_status,
    },
    "fuze_decision": {
      "fuze_triggered": bool(probe_case.get("fuze_triggered")),
      "fuze_reason": str(probe_case.get("fuze_reason", "") or ""),
      "detonated": bool(fuze.get("detonated")),
      "detonation_probability": _finite_or_none(fuze.get("detonation_probability")),
      "fuze_quality": _finite_or_none(fuze.get("fuze_quality")),
      "terminal_track_valid": bool(fuze.get("terminal_track_valid")),
      "target_detected": bool(fuze.get("target_detected")),
      "detonation_point_source": str(fuze.get("detonation_point_source", "") or ""),
    },
    "component_response": response,
    "consequence_projection": {
      "outcome_state": str(consequence.get("outcome_state", "") or ""),
      "component_hit_count": int(consequence.get("component_hit_count", 0) or 0),
      "component_failure_count": int(
        consequence.get("component_failure_count", 0) or 0
      ),
      "primary_component_system": str(
        consequence.get("primary_component_system", "") or ""
      ),
      "mission_kill": bool(consequence_observed.get("mission_kill")),
      "mobility_kill": bool(consequence_observed.get("mobility_kill")),
      "sensor_kill": bool(consequence_observed.get("sensor_kill")),
      "destroyed": bool(consequence_observed.get("destroyed")),
    },
    "guards": {
      "scalar_owner_guard_status": _scalar_guard_status(probe_case),
      "unexpected_stage_delta": "not_applicable_before_report",
      "authority_boundary_status": _authority_boundary_status(
        probe_report,
        runtime_facade,
      ),
      "runtime_parameter_retuning": bool(
        runtime_facade.get("runtime_parameter_retuning")
      ),
    },
  }

  rows: list[dict[str, Any]] = []
  for variant in effect_variants:
    r_effect_m = _radius_for_variant(
      str(variant),
      r_fuze_m=r_fuze_m,
      runtime_facade=runtime_facade,
      declared_effect_radius_m=declared_effect_radius_m,
    )
    rho_effect_case = _safe_ratio(nearest_distance, r_effect_m)
    row = dict(base)
    row["warhead_load_field"] = {
      "R_effect_variant": str(variant),
      "R_effect_m": r_effect_m,
      "rho_effect_case": rho_effect_case,
      "effect_band": _effect_band(rho_effect_case),
      **load,
    }
    row["component_detail"] = component_detail_from_runtime_facade(
      runtime_facade=runtime_facade,
      r_effect_variant=str(variant),
      r_effect_m=r_effect_m,
    )
    rows.append(row)
  return rows


def _summarize(
  *,
  case_grid: list[dict[str, Any]],
  heatmap_rows: list[dict[str, Any]],
) -> dict[str, Any]:
  launch_counts = Counter(str(row.get("launch_class", "") or "") for row in case_grid)
  guidance_counts = Counter(
    str(
      dict(row.get("guidance_approach", {}) or {}).get(
        "guidance_expectation_status",
        "",
      )
      or ""
    )
    for row in heatmap_rows
  )
  effect_band_counts = Counter(
    str(dict(row.get("warhead_load_field", {}) or {}).get("effect_band", "") or "")
    for row in heatmap_rows
  )
  authority_counts = Counter(
    str(dict(row.get("guards", {}) or {}).get("authority_boundary_status", "") or "")
    for row in heatmap_rows
  )
  runnable = [case for case in case_grid if bool(case.get("runtime_supported"))]
  return {
    "case_count": len(case_grid),
    "runnable_case_count": len(runnable),
    "unsupported_case_count": len(case_grid) - len(runnable),
    "heatmap_row_count": len(heatmap_rows),
    "launch_class_counts": dict(sorted(launch_counts.items())),
    "guidance_expectation_status_counts": dict(sorted(guidance_counts.items())),
    "effect_band_counts": dict(sorted(effect_band_counts.items())),
    "authority_boundary_status_counts": dict(sorted(authority_counts.items())),
  }


def generate_before_report(
  *,
  grid_tier: str = "anchor-grid",
  target_motion_layers: tuple[str, ...] = ("nonmaneuvering_constant_velocity",),
  effect_variants: tuple[str, ...] = DEFAULT_EFFECT_VARIANTS,
  seed: int = DEFAULT_SEED,
  case_ids: tuple[str, ...] = (),
  case_limit: int = 0,
  database_path: Path = decoupling_probe.DEFAULT_DATABASE_PATH,
  external_evidence_report_path: Path | str | None = decoupling_probe.DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH,
  r_fuze_m: float = DEFAULT_R_FUZE_M,
  declared_effect_radius_m: float | None = None,
  case_grid_only: bool = False,
  include_raw_probe: bool = False,
) -> dict[str, Any]:
  case_grid = generate_case_grid(
    grid_tier=grid_tier,
    target_motion_layers=target_motion_layers,
    seed=seed,
    case_ids=case_ids,
    case_limit=case_limit,
  )
  runnable_cases = [
    case for case in case_grid if bool(case.get("runtime_supported"))
  ]
  probe_report: dict[str, Any] = {}
  if not case_grid_only and runnable_cases:
    probe_report = decoupling_probe.generate_report(
      database_path=database_path,
      external_evidence_report_path=external_evidence_report_path,
      guidance_cases=tuple(
        {
          "case_id": str(case["case_id"]),
          "range_m": float(case["range_m"]),
          "bearing_deg": float(case["signed_bearing_deg"]),
        }
        for case in runnable_cases
      ),
      proximity_distances_m=(),
      include_guidance=True,
      include_proximity=False,
      seed=seed,
    )
  probe_cases = {
    str(case.get("case_id", "") or ""): dict(case)
    for case in list(probe_report.get("guidance_cases", []) or [])
    if isinstance(case, dict)
  }
  heatmap_rows = [] if case_grid_only else [
    projected
    for case in case_grid
    for projected in _project_heatmap_rows(
      grid_case=case,
      probe_case=probe_cases.get(str(case["case_id"])),
      probe_report=probe_report,
      effect_variants=effect_variants,
      r_fuze_m=float(r_fuze_m),
      declared_effect_radius_m=declared_effect_radius_m,
    )
  ]
  report = {
    "schema_version": SCHEMA_VERSION,
    "status": (
      "case_grid_generated"
      if case_grid_only
      else "before_report_generated"
    ),
    "profile_id": PROFILE_ID,
    "grid_tier": str(grid_tier),
    "seed": int(seed),
    "effect_variants": list(effect_variants),
    "radius_policy": {
      "R_fuze_m": float(r_fuze_m),
      "R_fuze_source": "kill_chain_decoupling_probe_missile_tuning.fuse_distance",
      "declared_effect_radius_m": declared_effect_radius_m,
      "R_effect_policy": "independent_review_variable",
    },
    "authority_boundary": {
      "runtime_parameter_retuning": False,
      "default_database_modified": False,
      "real_world_pk": False,
      "deterministic_fuze_authority": False,
      "calibration_authority": False,
    },
    "case_grid": case_grid,
    "heatmap_rows": heatmap_rows,
    "summary": _summarize(case_grid=case_grid, heatmap_rows=heatmap_rows),
    "source_probe": {
      "schema_version": probe_report.get("schema_version", ""),
      "status": probe_report.get("status", ""),
      "guidance_case_count": int(probe_report.get("guidance_case_count", 0) or 0),
      "proximity_case_count": int(probe_report.get("proximity_case_count", 0) or 0),
      "completion_audit_goal_complete": bool(
        dict(probe_report.get("completion_audit", {}) or {}).get("goal_complete")
      ),
    },
  }
  if include_raw_probe:
    report["raw_probe_report"] = probe_report
  return report


@contextlib.contextmanager
def _native_stdout_to_stderr():
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
    description="Generate KCES case grids and before-report heatmap rows."
  )
  parser.add_argument("--database", default=str(decoupling_probe.DEFAULT_DATABASE_PATH))
  parser.add_argument("--grid", default="anchor-grid", choices=("anchor-grid",))
  parser.add_argument(
    "--target-motion-layers",
    default="nonmaneuvering_constant_velocity",
    help="Comma-separated target motion layers. Initial runtime support is CV only.",
  )
  parser.add_argument(
    "--effect-variants",
    default=",".join(DEFAULT_EFFECT_VARIANTS),
    help="Comma-separated R_effect variants to evaluate offline per runtime case.",
  )
  parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
  parser.add_argument("--case-limit", type=int, default=0)
  parser.add_argument(
    "--case-id",
    action="append",
    default=[],
    help="Run only the named case id. Can be repeated.",
  )
  parser.add_argument(
    "--r-fuze-m",
    type=float,
    default=DEFAULT_R_FUZE_M,
    help="Declared fuze radius used for rho_fuze derivation.",
  )
  parser.add_argument(
    "--declared-effect-radius-m",
    type=float,
    default=float("nan"),
    help="Required by REV-SMALLER-LOAD; omitted values produce unclassified rows.",
  )
  parser.add_argument(
    "--external-evidence-report",
    default=str(decoupling_probe.DEFAULT_EXTERNAL_EVIDENCE_REPORT_PATH),
  )
  parser.add_argument("--case-grid-only", action="store_true")
  parser.add_argument("--include-raw-probe", action="store_true")
  parser.add_argument("--output", default="", help="Optional JSON output path.")
  return parser


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  declared_effect_radius = _finite_or_none(args.declared_effect_radius_m)
  with _native_stdout_to_stderr():
    report = generate_before_report(
      grid_tier=str(args.grid),
      target_motion_layers=_parse_csv(args.target_motion_layers),
      effect_variants=_parse_csv(args.effect_variants),
      seed=int(args.seed),
      case_ids=tuple(str(value) for value in list(args.case_id or [])),
      case_limit=int(args.case_limit),
      database_path=Path(args.database),
      external_evidence_report_path=Path(args.external_evidence_report),
      r_fuze_m=float(args.r_fuze_m),
      declared_effect_radius_m=declared_effect_radius,
      case_grid_only=bool(args.case_grid_only),
      include_raw_probe=bool(args.include_raw_probe),
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
