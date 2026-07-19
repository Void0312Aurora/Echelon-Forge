#!/usr/bin/env python3
"""Dense proxy-only standoff grid probe for external detonation trends."""

from __future__ import annotations

import argparse
import json
import math
import sys
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.runtime_bootstrap import resolve_repo_path
from tools.geometry import target_geometry_lethality_matrix_probe as matrix_probe


SCHEMA_VERSION = "a2.target_geometry_proxy_standoff_grid_probe.v1"
STATUS = "target_geometry_proxy_standoff_grid_probe_generated_20260615"
GENERATED_ON = "2026-06-15"
WARHEAD_FAMILIES = ("blast_fragmentation", "continuous_rod")
STANDOFF_DISTANCES_M = (0.5, 1.0, 2.0, 4.0, 8.0, 14.0)
DEFAULT_LOCAL_UP_M = 0.0
LOCAL_UP_LEVELS_M = (-2.0, -1.0, 0.0, 1.0, 2.0)
CENTERLINE_Z_LEVELS_M = (-6.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0, 6.0)
CENTERLINE_FORWARD_M = 0.0
CENTERLINE_RIGHT_M = 0.0
XY_GRID_LEVELS_M = tuple(float(value) for value in range(-12, 13, 2))
XY_GRID_LOCAL_UP_M = 0.0
SUPPORT_PROJECTION_TOLERANCE_M = 1.0e-6
MATRIX_PROBE_PATH = Path(
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
CONTOUR_PATH = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
    "whole_airframe_contour_containment_20260614.json",
  )
)
PROXY_UNIT_PATH = (
  matrix_probe.PROXY_DATABASE_PATH / "aircraft" / "units" / "f16c_block50.json"
)
DEFAULT_OUTPUT_DIR = Path(
  resolve_repo_path(
    "docs",
    "task",
    "air_combat",
    "a2_high_fidelity_damage_model",
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
  )
)
SQRT_HALF = math.sqrt(0.5)
ASPECT_DIRECTIONS: tuple[tuple[str, tuple[float, float]], ...] = (
  ("nose", (1.0, 0.0)),
  ("nose_right", (SQRT_HALF, SQRT_HALF)),
  ("right_beam", (0.0, 1.0)),
  ("tail_right", (-SQRT_HALF, SQRT_HALF)),
  ("tail", (-1.0, 0.0)),
  ("tail_left", (-SQRT_HALF, -SQRT_HALF)),
  ("left_beam", (0.0, -1.0)),
  ("nose_left", (SQRT_HALF, -SQRT_HALF)),
)


def _relative_path(path: Path) -> str:
  resolved = path.resolve()
  try:
    return str(resolved.relative_to(REPO_ROOT))
  except ValueError:
    return str(resolved)


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _bounds_from_center_size(
  center: list[float], size: list[float]
) -> dict[str, list[float]]:
  half = [float(value) * 0.5 for value in size]
  return {
    "min": [float(center[idx]) - half[idx] for idx in range(3)],
    "max": [float(center[idx]) + half[idx] for idx in range(3)],
  }


def _proxy_aabbs() -> dict[str, list[dict[str, Any]]]:
  unit = _load_json(PROXY_UNIT_PATH)
  hitboxes: list[dict[str, Any]] = []
  components: list[dict[str, Any]] = []
  for hitbox_index, hitbox in enumerate(unit["damage_model"]["hitboxes"]):
    hitbox_center = [float(value) for value in hitbox["offset"]]
    hitbox_size = [float(value) for value in hitbox["size"]]
    hitboxes.append(
      {
        "kind": "hitbox",
        "name": f"hitbox_{hitbox_index}",
        "center": hitbox_center,
        "size": hitbox_size,
        "bounds": _bounds_from_center_size(hitbox_center, hitbox_size),
      }
    )
    for component in hitbox.get("components", []):
      if "offset" not in component or "size" not in component:
        continue
      component_center = [float(value) for value in component["offset"]]
      component_size = [float(value) for value in component["size"]]
      components.append(
        {
          "kind": "component",
          "name": str(component.get("name", "")),
          "system": str(component.get("system", "")),
          "center": component_center,
          "size": component_size,
          "bounds": _bounds_from_center_size(component_center, component_size),
        }
      )
  return {
    "hitboxes": hitboxes,
    "components": components,
  }


def _point_in_aabb(point: list[float], bounds: dict[str, list[float]]) -> bool:
  return all(
    float(bounds["min"][idx]) <= float(point[idx]) <= float(bounds["max"][idx])
    for idx in range(3)
  )


def _point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
  x, y = point
  inside = False
  count = len(polygon)
  j = count - 1
  for i in range(count):
    xi, yi = float(polygon[i][0]), float(polygon[i][1])
    xj, yj = float(polygon[j][0]), float(polygon[j][1])
    intersects = (yi > y) != (yj > y) and (
      x < (xj - xi) * (y - yi) / ((yj - yi) or 1.0e-12) + xi
    )
    if intersects:
      inside = not inside
    j = i
  return inside


def _point_segment_distance(
  point: tuple[float, float],
  start: tuple[float, float],
  end: tuple[float, float],
) -> float:
  px, py = point
  sx, sy = start
  ex, ey = end
  vx = ex - sx
  vy = ey - sy
  length_sq = vx * vx + vy * vy
  if length_sq <= 1.0e-18:
    return math.hypot(px - sx, py - sy)
  t = max(0.0, min(1.0, ((px - sx) * vx + (py - sy) * vy) / length_sq))
  nearest_x = sx + t * vx
  nearest_y = sy + t * vy
  return math.hypot(px - nearest_x, py - nearest_y)


def _polygon_distance(point: tuple[float, float], polygon: list[list[float]]) -> float:
  distances: list[float] = []
  for idx, start in enumerate(polygon):
    end = polygon[(idx + 1) % len(polygon)]
    distances.append(
      _point_segment_distance(
        point,
        (float(start[0]), float(start[1])),
        (float(end[0]), float(end[1])),
      )
    )
  return min(distances) if distances else math.nan


def _top_contour_points() -> list[list[float]]:
  contour = _load_json(CONTOUR_PATH)
  return [[float(x), float(y)] for x, y in contour["contours"]["top"]["points_m"]]


def _support_point(
  polygon: list[list[float]],
  direction: tuple[float, float],
) -> tuple[float, float]:
  dx, dy = direction
  projections = [
    (float(point[0]) * dx + float(point[1]) * dy, float(point[0]), float(point[1]))
    for point in polygon
  ]
  best_projection = max(projection for projection, _x, _y in projections)
  support_points = [
    (x, y)
    for projection, x, y in projections
    if projection >= best_projection - SUPPORT_PROJECTION_TOLERANCE_M
  ]
  if not support_points:
    return 0.0, 0.0
  return (
    (min(x for x, _y in support_points) + max(x for x, _y in support_points)) * 0.5,
    (min(y for _x, y in support_points) + max(y for _x, y in support_points)) * 0.5,
  )


def _case_id(
  aspect: str,
  standoff_m: float,
  local_up_m: float,
) -> str:
  standoff_label = str(standoff_m).replace(".", "p")
  if abs(float(local_up_m) - DEFAULT_LOCAL_UP_M) <= 1.0e-9:
    return f"{aspect}_standoff_{standoff_label}m"
  z_prefix = "zp" if local_up_m > 0.0 else "zm"
  z_label = str(abs(float(local_up_m))).replace(".", "p")
  return f"{aspect}_{z_prefix}{z_label}m_standoff_{standoff_label}m"


def _z_label(value: float) -> str:
  prefix = "zp" if value > 0.0 else "zm" if value < 0.0 else "z0"
  if abs(value) <= 1.0e-9:
    return prefix
  return f"{prefix}{str(abs(float(value))).replace('.', 'p')}m"


def _coord_label(value: float) -> str:
  prefix = "p" if value > 0.0 else "m" if value < 0.0 else "0"
  if abs(value) <= 1.0e-9:
    return prefix
  return f"{prefix}{str(abs(float(value))).replace('.', 'p')}m"


def _classify_point(
  point: list[float],
  *,
  top_contour: list[list[float]],
  aabbs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
  top_point = (float(point[0]), float(point[1]))
  inside_hitboxes = [
    item["name"] for item in aabbs["hitboxes"] if _point_in_aabb(point, item["bounds"])
  ]
  inside_components = [
    item["name"]
    for item in aabbs["components"]
    if _point_in_aabb(point, item["bounds"])
  ]
  inside_top = _point_in_polygon(top_point, top_contour)
  distance = _polygon_distance(top_point, top_contour)
  return {
    "inside_top_contour": inside_top,
    "top_contour_signed_distance_m": -distance if inside_top else distance,
    "inside_hitbox_count": len(inside_hitboxes),
    "inside_hitbox_names": inside_hitboxes,
    "inside_component_count": len(inside_components),
    "inside_component_names": inside_components,
    "detonation_position_class": (
      "inside_component_debug"
      if inside_components
      else "inside_hitbox_debug"
      if inside_hitboxes
      else "inside_top_projection_debug"
      if inside_top
      else "external_top_contour_standoff"
    ),
  }


def _legacy_case_classification(
  *,
  top_contour: list[list[float]],
  aabbs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
  if not MATRIX_PROBE_PATH.exists():
    return []
  probe = _load_json(MATRIX_PROBE_PATH)
  by_case: dict[str, dict[str, Any]] = {}
  for comparison in probe["comparisons"]:
    case_id = str(comparison["case_id"])
    if case_id in by_case:
      continue
    point = [float(value) for value in comparison["local_point_m"]]
    by_case[case_id] = {
      "case_id": case_id,
      "aspect": str(comparison["aspect"]),
      "range_bucket": str(comparison["range_bucket"]),
      "local_point_m": point,
      **_classify_point(point, top_contour=top_contour, aabbs=aabbs),
    }
  return [by_case[case_id] for case_id in sorted(by_case)]


def _external_grid_cases(
  top_contour: list[list[float]],
  *,
  local_up_levels_m: tuple[float, ...] = LOCAL_UP_LEVELS_M,
) -> list[dict[str, Any]]:
  cases: list[dict[str, Any]] = []
  for aspect, direction in ASPECT_DIRECTIONS:
    boundary_x, boundary_y = _support_point(top_contour, direction)
    dx, dy = direction
    for local_up_m in local_up_levels_m:
      for standoff in STANDOFF_DISTANCES_M:
        local_point = [
          boundary_x + dx * float(standoff),
          boundary_y + dy * float(standoff),
          float(local_up_m),
        ]
        cases.append(
          {
            "case_id": _case_id(aspect, float(standoff), float(local_up_m)),
            "aspect": aspect,
            "standoff_distance_m": float(standoff),
            "local_up_m": float(local_up_m),
            "top_contour_support_point_m": [boundary_x, boundary_y],
            "local_point_m": local_point,
            "missile_velocity_body_mps": list(
              matrix_probe.missile_velocity_toward_origin(local_point)
            ),
          }
        )
  return cases


def _centerline_z_cases() -> list[dict[str, Any]]:
  cases: list[dict[str, Any]] = []
  for local_up_m in CENTERLINE_Z_LEVELS_M:
    local_point = [
      CENTERLINE_FORWARD_M,
      CENTERLINE_RIGHT_M,
      float(local_up_m),
    ]
    cases.append(
      {
        "case_id": f"centerline_{_z_label(float(local_up_m))}",
        "aspect": "centerline_vertical",
        "standoff_distance_m": 0.0,
        "local_up_m": float(local_up_m),
        "centerline_forward_m": CENTERLINE_FORWARD_M,
        "centerline_right_m": CENTERLINE_RIGHT_M,
        "vertical_offset_m": abs(float(local_up_m)),
        "top_contour_support_point_m": [CENTERLINE_FORWARD_M, CENTERLINE_RIGHT_M],
        "local_point_m": local_point,
        "missile_velocity_body_mps": list(
          matrix_probe.missile_velocity_toward_origin(local_point)
        ),
      }
    )
  return cases


def _xy_grid_cases(
  *,
  top_contour: list[list[float]],
  aabbs: dict[str, list[dict[str, Any]]],
  local_up_m: float = XY_GRID_LOCAL_UP_M,
) -> list[dict[str, Any]]:
  cases: list[dict[str, Any]] = []
  for local_forward_m in XY_GRID_LEVELS_M:
    for local_right_m in XY_GRID_LEVELS_M:
      local_point = [
        float(local_forward_m),
        float(local_right_m),
        float(local_up_m),
      ]
      cases.append(
        {
          "case_id": (
            f"xy_grid_{_z_label(float(local_up_m))}_"
            f"x{_coord_label(float(local_forward_m))}_"
            f"y{_coord_label(float(local_right_m))}"
          ),
          "local_forward_m": float(local_forward_m),
          "local_right_m": float(local_right_m),
          "local_up_m": float(local_up_m),
          "local_point_m": local_point,
          **_classify_point(local_point, top_contour=top_contour, aabbs=aabbs),
        }
      )
  return cases


def _event_record(
  case: dict[str, Any],
  *,
  family: str,
  seed: int,
  top_contour: list[list[float]],
  aabbs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
  event = matrix_probe._event_summary(
    database_path=matrix_probe.PROXY_DATABASE_PATH,
    family=family,
    local_point_m=tuple(float(value) for value in case["local_point_m"]),
    missile_velocity_body_mps=tuple(
      float(value) for value in case["missile_velocity_body_mps"]
    ),
    seed=seed,
  )
  classification = _classify_point(
    [float(value) for value in case["local_point_m"]],
    top_contour=top_contour,
    aabbs=aabbs,
  )
  return {
    **case,
    "warhead_family": family,
    "seed": seed,
    **classification,
    "proxy_component_primary_name": str(event["component_primary_name"]) or "(none)",
    "proxy_component_primary_system": str(event["component_primary_system"]),
    "proxy_component_primary_failure_probability": float(
      event["component_primary_row_failure_probability"]
    ),
    "proxy_component_primary_distance_m": float(
      event["component_primary_row_distance_m"]
    ),
    "proxy_component_primary_effect_scale": float(
      event["component_primary_row_effect_scale"]
    ),
    "proxy_component_primary_direct_hit": bool(event["component_primary_row_direct_hit"]),
    "proxy_component_max_failure_probability": float(
      event["component_max_failure_probability"]
    ),
    "proxy_component_max_failure_probability_component_name": str(
      event["component_max_failure_probability_component_name"]
    )
    or "(none)",
    "proxy_component_max_failure_probability_component_system": str(
      event["component_max_failure_probability_component_system"]
    ),
    "proxy_component_max_failure_probability_distance_m": float(
      event["component_max_failure_probability_distance_m"]
    ),
    "proxy_component_max_failure_probability_effect_scale": float(
      event["component_max_failure_probability_effect_scale"]
    ),
    "proxy_component_failure_probability": float(
      event["component_primary_row_failure_probability"]
    ),
    "proxy_event_max_component_failure_probability": float(
      event["component_failure_probability"]
    ),
    "proxy_component_failure_probability_source": str(
      event["component_failure_probability_source"]
    ),
    "proxy_component_primary_integrity": float(event["component_primary_integrity"]),
    "proxy_component_primary_rod_cut_margin": float(
      event["component_primary_mechanism_rod_cut_margin"]
    ),
    "proxy_component_primary_fragment_energy_j": float(
      event["component_primary_mechanism_fragment_energy_j"]
    ),
    "proxy_component_hit_count": int(event["component_hit_count"]),
    "proxy_component_failure_count": int(event["component_failure_count"]),
    "proxy_projected_hitbox_count": int(event["projected_hitbox_count"]),
    "proxy_direct_hitbox_intersection": bool(event["direct_hitbox_intersection"]),
    "proxy_component_damage_event_count": int(event["component_damage_event_count"]),
    "proxy_component_failure_event_count": int(event["component_failure_event_count"]),
    "proxy_component_failure_observed": bool(event["component_failure_observed"]),
    "proxy_component_damage_event_names": list(event["component_damage_event_names"]),
    "proxy_system_health_delta": float(event["system_health_delta"]),
    "proxy_structure_hit": bool(event["structure_hit"]),
    "proxy_structure_spatial_scale": float(event["structure_spatial_scale"]),
    "proxy_structure_integrity_after": float(event["structure_integrity_after"]),
    "proxy_structure_damage_delta": float(event["structure_damage_delta"]),
    "proxy_structure_damage_observed": bool(event["structure_damage_observed"]),
    "proxy_aircraft_damage_state_delta": str(event["aircraft_damage_state_delta"]),
    "proxy_structural_breakup_event_count": int(
      event["structural_breakup_event_count"]
    ),
    "proxy_structural_breakup_observed": bool(event["structural_breakup_observed"]),
    "proxy_structural_breakup_modes": list(event["structural_breakup_modes"]),
    "proxy_structural_breakup_part_refs": list(event["structural_breakup_part_refs"]),
  }


def _records_by_family(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
  return {
    family: [record for record in records if str(record["warhead_family"]) == family]
    for family in WARHEAD_FAMILIES
  }


def _heatmap_matrix(
  records: list[dict[str, Any]],
  *,
  local_up_m: float = DEFAULT_LOCAL_UP_M,
) -> dict[str, Any]:
  aspects = [aspect for aspect, _direction in ASPECT_DIRECTIONS]
  distances = [float(value) for value in STANDOFF_DISTANCES_M]
  by_cell = {
    (str(record["aspect"]), float(record["standoff_distance_m"])): record
    for record in records
    if abs(float(record["local_up_m"]) - float(local_up_m)) <= 1.0e-9
  }
  matrix: list[list[float | None]] = []
  primary_matrix: list[list[str]] = []
  primary_distance_matrix: list[list[float | None]] = []
  event_max_matrix: list[list[float | None]] = []
  event_max_component_matrix: list[list[str]] = []
  component_failure_observed_matrix: list[list[bool | None]] = []
  structure_damage_delta_matrix: list[list[float | None]] = []
  structure_damage_observed_matrix: list[list[bool | None]] = []
  structural_breakup_observed_matrix: list[list[bool | None]] = []
  for aspect in aspects:
    values: list[float | None] = []
    primaries: list[str] = []
    primary_distances: list[float | None] = []
    event_max_values: list[float | None] = []
    event_max_components: list[str] = []
    component_failure_observed_values: list[bool | None] = []
    structure_damage_delta_values: list[float | None] = []
    structure_damage_observed_values: list[bool | None] = []
    structural_breakup_observed_values: list[bool | None] = []
    for distance in distances:
      record = by_cell.get((aspect, distance))
      if record is None:
        values.append(None)
        primaries.append("")
        primary_distances.append(None)
        event_max_values.append(None)
        event_max_components.append("")
        component_failure_observed_values.append(None)
        structure_damage_delta_values.append(None)
        structure_damage_observed_values.append(None)
        structural_breakup_observed_values.append(None)
      else:
        values.append(float(record["proxy_component_failure_probability"]))
        primaries.append(str(record["proxy_component_primary_name"]))
        primary_distances.append(float(record["proxy_component_primary_distance_m"]))
        event_max_values.append(
          float(record["proxy_event_max_component_failure_probability"])
        )
        event_max_components.append(
          str(record["proxy_component_max_failure_probability_component_name"])
        )
        component_failure_observed_values.append(
          bool(record["proxy_component_failure_observed"])
        )
        structure_damage_delta_values.append(
          float(record["proxy_structure_damage_delta"])
        )
        structure_damage_observed_values.append(
          bool(record["proxy_structure_damage_observed"])
        )
        structural_breakup_observed_values.append(
          bool(record["proxy_structural_breakup_observed"])
        )
    matrix.append(values)
    primary_matrix.append(primaries)
    primary_distance_matrix.append(primary_distances)
    event_max_matrix.append(event_max_values)
    event_max_component_matrix.append(event_max_components)
    component_failure_observed_matrix.append(component_failure_observed_values)
    structure_damage_delta_matrix.append(structure_damage_delta_values)
    structure_damage_observed_matrix.append(structure_damage_observed_values)
    structural_breakup_observed_matrix.append(structural_breakup_observed_values)
  return {
    "aspects": aspects,
    "standoff_distances_m": distances,
    "local_up_m": float(local_up_m),
    "probability_matrix": matrix,
    "primary_component_matrix": primary_matrix,
    "primary_component_distance_m_matrix": primary_distance_matrix,
    "event_max_probability_matrix": event_max_matrix,
    "event_max_probability_component_matrix": event_max_component_matrix,
    "component_failure_observed_matrix": component_failure_observed_matrix,
    "structure_damage_delta_matrix": structure_damage_delta_matrix,
    "structure_damage_observed_matrix": structure_damage_observed_matrix,
    "structural_breakup_observed_matrix": structural_breakup_observed_matrix,
  }


def _centerline_z_matrix(records: list[dict[str, Any]]) -> dict[str, Any]:
  z_levels = [float(value) for value in CENTERLINE_Z_LEVELS_M]
  by_cell = {
    (str(record["warhead_family"]), float(record["local_up_m"])): record
    for record in records
  }
  probability_matrix: list[list[float | None]] = []
  primary_matrix: list[list[str]] = []
  class_matrix: list[list[str]] = []
  primary_distance_matrix: list[list[float | None]] = []
  for family in WARHEAD_FAMILIES:
    values: list[float | None] = []
    primaries: list[str] = []
    classes: list[str] = []
    distances: list[float | None] = []
    for local_up_m in z_levels:
      record = by_cell.get((family, local_up_m))
      if record is None:
        values.append(None)
        primaries.append("")
        classes.append("")
        distances.append(None)
        continue
      values.append(float(record["proxy_component_failure_probability"]))
      primaries.append(str(record["proxy_component_primary_name"]))
      classes.append(str(record["detonation_position_class"]))
      distances.append(float(record["proxy_component_primary_distance_m"]))
    probability_matrix.append(values)
    primary_matrix.append(primaries)
    class_matrix.append(classes)
    primary_distance_matrix.append(distances)
  return {
    "warhead_families": list(WARHEAD_FAMILIES),
    "local_up_levels_m": z_levels,
    "probability_matrix": probability_matrix,
    "primary_component_matrix": primary_matrix,
    "detonation_position_class_matrix": class_matrix,
    "primary_component_distance_m_matrix": primary_distance_matrix,
  }


def _xy_position_class_matrix(cases: list[dict[str, Any]]) -> dict[str, Any]:
  forward_levels = [float(value) for value in XY_GRID_LEVELS_M]
  right_levels = [float(value) for value in XY_GRID_LEVELS_M]
  by_cell = {
    (float(case["local_forward_m"]), float(case["local_right_m"])): case
    for case in cases
  }
  class_matrix: list[list[str]] = []
  inside_top_matrix: list[list[bool | None]] = []
  component_names_matrix: list[list[list[str]]] = []
  hitbox_names_matrix: list[list[list[str]]] = []
  signed_distance_matrix: list[list[float | None]] = []
  for local_forward_m in forward_levels:
    class_row: list[str] = []
    inside_top_row: list[bool | None] = []
    component_names_row: list[list[str]] = []
    hitbox_names_row: list[list[str]] = []
    signed_distance_row: list[float | None] = []
    for local_right_m in right_levels:
      case = by_cell.get((local_forward_m, local_right_m))
      if case is None:
        class_row.append("")
        inside_top_row.append(None)
        component_names_row.append([])
        hitbox_names_row.append([])
        signed_distance_row.append(None)
        continue
      class_row.append(str(case["detonation_position_class"]))
      inside_top_row.append(bool(case["inside_top_contour"]))
      component_names_row.append([str(name) for name in case["inside_component_names"]])
      hitbox_names_row.append([str(name) for name in case["inside_hitbox_names"]])
      signed_distance_row.append(float(case["top_contour_signed_distance_m"]))
    class_matrix.append(class_row)
    inside_top_matrix.append(inside_top_row)
    component_names_matrix.append(component_names_row)
    hitbox_names_matrix.append(hitbox_names_row)
    signed_distance_matrix.append(signed_distance_row)
  return {
    "local_forward_levels_m": forward_levels,
    "local_right_levels_m": right_levels,
    "local_up_m": float(XY_GRID_LOCAL_UP_M),
    "detonation_position_class_matrix": class_matrix,
    "inside_top_contour_matrix": inside_top_matrix,
    "inside_component_names_matrix": component_names_matrix,
    "inside_hitbox_names_matrix": hitbox_names_matrix,
    "top_contour_signed_distance_m_matrix": signed_distance_matrix,
  }


def _mean(values: list[float]) -> float:
  return sum(values) / len(values) if values else math.nan


def _compact_outcome_record(record: dict[str, Any]) -> dict[str, Any]:
  return {
    "case_id": str(record["case_id"]),
    "warhead_family": str(record["warhead_family"]),
    "aspect": str(record["aspect"]),
    "standoff_distance_m": float(record["standoff_distance_m"]),
    "local_up_m": float(record["local_up_m"]),
    "local_point_m": [float(value) for value in record["local_point_m"]],
    "detonation_position_class": str(record["detonation_position_class"]),
    "proxy_component_primary_name": str(record["proxy_component_primary_name"]),
    "proxy_component_primary_system": str(record["proxy_component_primary_system"]),
    "proxy_component_failure_probability": float(
      record["proxy_component_failure_probability"]
    ),
    "proxy_event_max_component_failure_probability": float(
      record["proxy_event_max_component_failure_probability"]
    ),
    "proxy_component_failure_observed": bool(
      record["proxy_component_failure_observed"]
    ),
    "proxy_component_damage_event_names": list(
      record["proxy_component_damage_event_names"]
    ),
    "proxy_system_health_delta": float(record["proxy_system_health_delta"]),
    "proxy_structure_damage_delta": float(record["proxy_structure_damage_delta"]),
    "proxy_structure_integrity_after": float(
      record["proxy_structure_integrity_after"]
    ),
    "proxy_structure_damage_observed": bool(
      record["proxy_structure_damage_observed"]
    ),
    "proxy_structural_breakup_event_count": int(
      record["proxy_structural_breakup_event_count"]
    ),
    "proxy_structural_breakup_modes": list(record["proxy_structural_breakup_modes"]),
    "proxy_structural_breakup_part_refs": list(
      record["proxy_structural_breakup_part_refs"]
    ),
  }


def _aggregate_rows(
  records: list[dict[str, Any]],
  *,
  field: str,
  levels: list[float | str],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for level in levels:
    level_records = [record for record in records if record[field] == level]
    if not level_records:
      continue
    primary_probabilities = [
      float(record["proxy_component_failure_probability"])
      for record in level_records
    ]
    event_probabilities = [
      float(record["proxy_event_max_component_failure_probability"])
      for record in level_records
    ]
    structure_deltas = [
      float(record["proxy_structure_damage_delta"]) for record in level_records
    ]
    rows.append(
      {
        field: level,
        "record_count": len(level_records),
        "mean_proxy_component_failure_probability": _mean(primary_probabilities),
        "max_proxy_component_failure_probability": max(primary_probabilities),
        "mean_proxy_event_max_component_failure_probability": _mean(
          event_probabilities
        ),
        "max_proxy_event_max_component_failure_probability": max(event_probabilities),
        "mean_proxy_structure_damage_delta": _mean(structure_deltas),
        "min_proxy_structure_damage_delta": min(structure_deltas),
        "component_failure_observed_count": sum(
          1
          for record in level_records
          if bool(record["proxy_component_failure_observed"])
        ),
        "structure_damage_observed_count": sum(
          1
          for record in level_records
          if bool(record["proxy_structure_damage_observed"])
        ),
        "structural_breakup_observed_count": sum(
          1
          for record in level_records
          if bool(record["proxy_structural_breakup_observed"])
        ),
      }
    )
  return rows


def _outcome_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
  by_family: dict[str, dict[str, Any]] = {}
  aspects = [aspect for aspect, _direction in ASPECT_DIRECTIONS]
  distances = [float(value) for value in STANDOFF_DISTANCES_M]
  for family in WARHEAD_FAMILIES:
    family_records = [
      record for record in records if str(record["warhead_family"]) == family
    ]
    if not family_records:
      continue
    default_z_records = [
      record
      for record in family_records
      if abs(float(record["local_up_m"]) - DEFAULT_LOCAL_UP_M) <= 1.0e-9
    ]
    top_primary = max(
      family_records,
      key=lambda record: float(record["proxy_component_failure_probability"]),
    )
    top_event = max(
      family_records,
      key=lambda record: float(
        record["proxy_event_max_component_failure_probability"]
      ),
    )
    top_structure_loss = min(
      family_records,
      key=lambda record: float(record["proxy_structure_damage_delta"]),
    )
    by_family[family] = {
      "record_count": len(family_records),
      "default_z_record_count": len(default_z_records),
      "component_failure_observed_record_count": sum(
        1
        for record in family_records
        if bool(record["proxy_component_failure_observed"])
      ),
      "structure_damage_observed_record_count": sum(
        1
        for record in family_records
        if bool(record["proxy_structure_damage_observed"])
      ),
      "structural_breakup_observed_record_count": sum(
        1
        for record in family_records
        if bool(record["proxy_structural_breakup_observed"])
      ),
      "max_primary_component_failure_probability_record": _compact_outcome_record(
        top_primary
      ),
      "max_event_component_failure_probability_record": _compact_outcome_record(
        top_event
      ),
      "max_structure_damage_record": _compact_outcome_record(top_structure_loss),
      "by_standoff_distance_m": _aggregate_rows(
        family_records,
        field="standoff_distance_m",
        levels=distances,
      ),
      "by_aspect": _aggregate_rows(
        family_records,
        field="aspect",
        levels=aspects,
      ),
      "default_z_by_standoff_distance_m": _aggregate_rows(
        default_z_records,
        field="standoff_distance_m",
        levels=distances,
      ),
      "default_z_by_aspect": _aggregate_rows(
        default_z_records,
        field="aspect",
        levels=aspects,
      ),
    }
  return {
    "status": "standoff_aspect_distance_outcomes_reported",
    "record_count": len(records),
    "warhead_family_count": len(by_family),
    "component_failure_observed_record_count": sum(
      1 for record in records if bool(record["proxy_component_failure_observed"])
    ),
    "structure_damage_observed_record_count": sum(
      1 for record in records if bool(record["proxy_structure_damage_observed"])
    ),
    "structural_breakup_observed_record_count": sum(
      1 for record in records if bool(record["proxy_structural_breakup_observed"])
    ),
    "by_family": by_family,
  }


def generate_report(*, seed: int = 20260615) -> dict[str, Any]:
  matrix_probe._configure_runtime_log_level()
  top_contour = _top_contour_points()
  aabbs = _proxy_aabbs()
  grid_cases = _external_grid_cases(top_contour)
  centerline_z_cases = _centerline_z_cases()
  xy_grid_cases = _xy_grid_cases(top_contour=top_contour, aabbs=aabbs)
  records = [
    _event_record(
      case,
      family=family,
      seed=seed,
      top_contour=top_contour,
      aabbs=aabbs,
    )
    for family in WARHEAD_FAMILIES
    for case in grid_cases
  ]
  centerline_z_records = [
    _event_record(
      case,
      family=family,
      seed=seed,
      top_contour=top_contour,
      aabbs=aabbs,
    )
    for family in WARHEAD_FAMILIES
    for case in centerline_z_cases
  ]
  records_by_family = _records_by_family(records)
  matrices = {
    family: _heatmap_matrix(family_records, local_up_m=DEFAULT_LOCAL_UP_M)
    for family, family_records in records_by_family.items()
  }
  z_layer_matrices = {
    family: {
      f"{local_up_m:g}": _heatmap_matrix(
        family_records,
        local_up_m=float(local_up_m),
      )
      for local_up_m in LOCAL_UP_LEVELS_M
    }
    for family, family_records in records_by_family.items()
  }
  contour_x = [point[0] for point in top_contour]
  contour_y = [point[1] for point in top_contour]
  legacy = _legacy_case_classification(top_contour=top_contour, aabbs=aabbs)
  external_records = [
    record
    for record in records
    if str(record["detonation_position_class"]) == "external_top_contour_standoff"
  ]
  return {
    "schema_version": SCHEMA_VERSION,
    "status": STATUS,
    "generated_on": GENERATED_ON,
    "target_unit": "F-16C_Block50",
    "seed": seed,
    "database_path": _relative_path(matrix_probe.PROXY_DATABASE_PATH),
    "authority_boundary": {
      "database_scope": "proxy_only",
      "debug_profiled_local_hit": True,
      "synthetic_warhead_profiles": True,
      "probability_field": "proxy_event.component_primary_row_failure_probability",
      "primary_probability_field": (
        "proxy_event.component_primary_row_failure_probability"
      ),
      "event_probability_field": (
        "proxy_event.component_failure_probability "
        "(max across component rows)"
      ),
      "real_weapon_pk_authority": False,
      "deterministic_fuze_authority": False,
    },
    "aircraft_scale_reference": {
      "top_contour_source": _relative_path(CONTOUR_PATH),
      "top_contour_point_count": len(top_contour),
      "top_contour_bounds_m": {
        "forward_min": min(contour_x),
        "forward_max": max(contour_x),
        "right_min": min(contour_y),
        "right_max": max(contour_y),
      },
      "runtime_hitbox_count": len(aabbs["hitboxes"]),
      "runtime_component_aabb_count": len(aabbs["components"]),
      "external_grid_default_local_up_m": DEFAULT_LOCAL_UP_M,
      "external_grid_local_up_levels_m": [float(value) for value in LOCAL_UP_LEVELS_M],
      "centerline_z_levels_m": [float(value) for value in CENTERLINE_Z_LEVELS_M],
      "centerline_xy_m": [CENTERLINE_FORWARD_M, CENTERLINE_RIGHT_M],
      "xy_grid_levels_m": [float(value) for value in XY_GRID_LEVELS_M],
      "xy_grid_local_up_m": XY_GRID_LOCAL_UP_M,
      "missile_velocity_rule": (
        "all probability probes use body velocity pointing from the detonation "
        "sample toward local origin at 900 m/s; the exact origin sample keeps "
        "zero velocity as a diagnostic inside-component point"
      ),
      "external_grid_position_rule": (
        "centered support point on actual top-view mesh contour plus outward "
        "standoff"
      ),
    },
    "independent_variables": [
      "warhead_family",
      "aspect",
      "standoff_distance_m",
      "local_up_m",
      "local_point_m",
      "missile_velocity_body_mps",
      "xy_grid.local_forward_m",
      "xy_grid.local_right_m",
    ],
    "dependent_variables": [
      "proxy_component_failure_probability",
      "proxy_component_primary_failure_probability",
      "proxy_component_primary_distance_m",
      "proxy_component_primary_effect_scale",
      "proxy_event_max_component_failure_probability",
      "proxy_component_primary_name",
      "proxy_component_primary_rod_cut_margin",
      "proxy_component_primary_fragment_energy_j",
      "proxy_component_failure_observed",
      "proxy_component_failure_event_count",
      "proxy_component_damage_event_names",
      "proxy_system_health_delta",
      "proxy_structure_damage_delta",
      "proxy_structure_integrity_after",
      "proxy_structure_damage_observed",
      "proxy_structural_breakup_event_count",
      "proxy_structural_breakup_observed",
      "proxy_structural_breakup_part_refs",
      "detonation_position_class",
      "inside_component_names",
      "inside_hitbox_names",
      "inside_top_contour",
    ],
    "metrics": {
      "aspect_count": len(ASPECT_DIRECTIONS),
      "standoff_distance_count": len(STANDOFF_DISTANCES_M),
      "local_up_level_count": len(LOCAL_UP_LEVELS_M),
      "warhead_family_count": len(WARHEAD_FAMILIES),
      "event_record_count": len(records),
      "centerline_z_record_count": len(centerline_z_records),
      "centerline_z_level_count": len(CENTERLINE_Z_LEVELS_M),
      "xy_grid_case_count": len(xy_grid_cases),
      "xy_grid_axis_level_count": len(XY_GRID_LEVELS_M),
      "xy_grid_inside_component_case_count": sum(
        1 for row in xy_grid_cases if int(row["inside_component_count"]) > 0
      ),
      "xy_grid_inside_hitbox_case_count": sum(
        1 for row in xy_grid_cases if int(row["inside_hitbox_count"]) > 0
      ),
      "xy_grid_inside_top_projection_case_count": sum(
        1 for row in xy_grid_cases if bool(row["inside_top_contour"])
      ),
      "external_top_contour_record_count": len(external_records),
      "non_external_record_count": len(records) - len(external_records),
      "primary_probability_differs_from_event_max_count": sum(
        1
        for row in records
        if abs(
          float(row["proxy_component_primary_failure_probability"])
          - float(row["proxy_event_max_component_failure_probability"])
        )
        > 1.0e-9
      ),
      "legacy_case_count": len(legacy),
      "legacy_inside_component_case_count": sum(
        1 for row in legacy if int(row["inside_component_count"]) > 0
      ),
      "legacy_inside_top_projection_case_count": sum(
        1 for row in legacy if bool(row["inside_top_contour"])
      ),
      "probability_source_values": sorted(
        {str(row["proxy_component_failure_probability_source"]) for row in records}
      ),
      "component_failure_observed_record_count": sum(
        1 for row in records if bool(row["proxy_component_failure_observed"])
      ),
      "structure_damage_observed_record_count": sum(
        1 for row in records if bool(row["proxy_structure_damage_observed"])
      ),
      "structural_breakup_observed_record_count": sum(
        1 for row in records if bool(row["proxy_structural_breakup_observed"])
      ),
    },
    "outcome_summary": _outcome_summary(records),
    "standoff_grid_cases": grid_cases,
    "centerline_z_cases": centerline_z_cases,
    "xy_grid_cases": xy_grid_cases,
    "records": records,
    "centerline_z_records": centerline_z_records,
    "matrices": matrices,
    "z_layer_matrices": z_layer_matrices,
    "centerline_z_matrix": _centerline_z_matrix(centerline_z_records),
    "xy_position_class_matrix": _xy_position_class_matrix(xy_grid_cases),
    "legacy_manual_case_position_classification": legacy,
  }


def _ensure_matplotlib() -> Any:
  import matplotlib

  matplotlib.use("Agg")
  import matplotlib.pyplot as plt
  import numpy as np

  return plt, np


def _case_primary_short(name: str) -> str:
  labels = {
    "(none)": "none",
    "cockpit_crew_station": "cockpit",
    "left_aileron_actuator": "L ail",
    "right_aileron_actuator": "R ail",
    "left_wing_fuel_cell": "L fuel",
    "right_wing_fuel_cell": "R fuel",
    "center_fuselage_fuel_cell": "ctr fuel",
    "electrical_power_bus": "power",
    "dedicated_canopy_surface_component": "canopy",
    "wing_spar_center_carrythrough_segment": "carrythr",
    "mission_computer": "mission",
    "flight_control_computer": "fcc",
    "left_leading_edge_flap_actuator": "L LEF",
    "right_leading_edge_flap_actuator": "R LEF",
    "engine_core_afterburner_segment": "AB seg",
    "engine_core_hot_section_segment": "hot seg",
    "engine_core_forward_compressor_segment": "comp seg",
    "rudder_actuator": "rudder",
    "right_horizontal_tail_actuator_or_surface_component": "R tail",
    "left_horizontal_tail_actuator_or_surface_component": "L tail",
  }
  return labels.get(name, textwrap.shorten(name, width=8, placeholder=".."))


def render_z_layer_heatmap(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, str]:
  plt, np = _ensure_matplotlib()
  fig, axes = plt.subplots(
    len(WARHEAD_FAMILIES),
    len(LOCAL_UP_LEVELS_M),
    figsize=(20.0, 9.5),
    constrained_layout=True,
    sharex=True,
    sharey=True,
  )
  last_image = None
  for row_idx, family in enumerate(WARHEAD_FAMILIES):
    for col_idx, local_up_m in enumerate(LOCAL_UP_LEVELS_M):
      axis = axes[row_idx][col_idx]
      matrix_info = report["z_layer_matrices"][family][f"{local_up_m:g}"]
      matrix = np.array(
        [
          [float(value) if value is not None else np.nan for value in row]
          for row in matrix_info["probability_matrix"]
        ],
        dtype=float,
      )
      cmap = plt.get_cmap("viridis").copy()
      cmap.set_bad(color="#eef2f7")
      last_image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap=cmap, aspect="auto")
      if row_idx == 0:
        axis.set_title(f"z={local_up_m:g} m", fontsize=11, pad=8)
      if col_idx == 0:
        axis.set_ylabel(f"{family}\naspect", fontsize=9)
        axis.set_yticks(range(len(matrix_info["aspects"])))
        axis.set_yticklabels(matrix_info["aspects"], fontsize=7)
      else:
        axis.set_yticks(range(len(matrix_info["aspects"])))
        axis.set_yticklabels([])
      if row_idx == len(WARHEAD_FAMILIES) - 1:
        axis.set_xticks(range(len(matrix_info["standoff_distances_m"])))
        axis.set_xticklabels(
          [f"{value:g}" for value in matrix_info["standoff_distances_m"]],
          fontsize=7,
        )
        axis.set_xlabel("standoff m", fontsize=8)
      else:
        axis.set_xticks(range(len(matrix_info["standoff_distances_m"])))
        axis.set_xticklabels([])
      axis.set_xticks(
        [idx + 0.5 for idx in range(len(matrix_info["standoff_distances_m"]) - 1)],
        minor=True,
      )
      axis.set_yticks(
        [idx + 0.5 for idx in range(len(matrix_info["aspects"]) - 1)],
        minor=True,
      )
      axis.grid(which="minor", color="white", linewidth=0.5)
      axis.tick_params(axis="both", length=0)
      for y_idx, row in enumerate(matrix_info["probability_matrix"]):
        for x_idx, value in enumerate(row):
          if value is None:
            continue
          color = "white" if float(value) > 0.52 else "#111827"
          axis.text(
            x_idx,
            y_idx,
            f"{float(value):.2f}",
            ha="center",
            va="center",
            fontsize=5.2,
            color=color,
          )
  if last_image is not None:
    cbar = fig.colorbar(last_image, ax=axes.ravel().tolist(), fraction=0.018, pad=0.01)
    cbar.ax.set_ylabel("Primary P(fail)", rotation=270, labelpad=14, fontsize=9)
  fig.suptitle(
    "Proxy-only vertical standoff layers: primary-component failure probability\n"
    "Each panel is aspect x outward standoff; z is target local up in meters",
    fontsize=14,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  png_path = output_dir / "target_geometry_proxy_standoff_grid_z_layers_20260615.png"
  svg_path = output_dir / "target_geometry_proxy_standoff_grid_z_layers_20260615.svg"
  fig.savefig(png_path, dpi=180, bbox_inches="tight")
  fig.savefig(svg_path, bbox_inches="tight")
  plt.close(fig)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def _class_short(name: str) -> str:
  labels = {
    "inside_component_debug": "in-comp",
    "inside_hitbox_debug": "in-box",
    "inside_top_projection_debug": "in-top",
    "external_top_contour_standoff": "external",
  }
  return labels.get(name, textwrap.shorten(name, width=8, placeholder=".."))


def render_xy_position_class_grid(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, str]:
  plt, _np = _ensure_matplotlib()
  fig, axis = plt.subplots(figsize=(10.4, 8.4), constrained_layout=True)
  contour = _top_contour_points()
  contour_x = [point[0] for point in contour] + [contour[0][0]]
  contour_y = [point[1] for point in contour] + [contour[0][1]]
  axis.plot(contour_x, contour_y, color="#111827", linewidth=1.3, label="top contour")
  style_by_class = {
    "inside_component_debug": {
      "label": "C inside component",
      "short": "C",
      "color": "#ef4444",
    },
    "inside_hitbox_debug": {
      "label": "B inside hitbox",
      "short": "B",
      "color": "#f59e0b",
    },
    "inside_top_projection_debug": {
      "label": "T inside top projection",
      "short": "T",
      "color": "#2563eb",
    },
    "external_top_contour_standoff": {
      "label": "E external",
      "short": "E",
      "color": "#e5e7eb",
    },
  }
  cases = list(report["xy_grid_cases"])
  for class_name, style in style_by_class.items():
    class_cases = [
      case
      for case in cases
      if str(case["detonation_position_class"]) == class_name
    ]
    if not class_cases:
      continue
    axis.scatter(
      [float(case["local_forward_m"]) for case in class_cases],
      [float(case["local_right_m"]) for case in class_cases],
      s=94,
      marker="s",
      c=str(style["color"]),
      edgecolors="#111827",
      linewidths=0.35,
      label=str(style["label"]),
      zorder=3,
    )
    for case in class_cases:
      text_color = "white" if class_name != "external_top_contour_standoff" else "#111827"
      axis.text(
        float(case["local_forward_m"]),
        float(case["local_right_m"]),
        str(style["short"]),
        ha="center",
        va="center",
        fontsize=6.0,
        fontweight="bold",
        color=text_color,
        zorder=4,
      )
  axis.set_xticks([float(value) for value in XY_GRID_LEVELS_M])
  axis.set_yticks([float(value) for value in XY_GRID_LEVELS_M])
  axis.set_xlim(min(XY_GRID_LEVELS_M) - 1.0, max(XY_GRID_LEVELS_M) + 1.0)
  axis.set_ylim(min(XY_GRID_LEVELS_M) - 1.0, max(XY_GRID_LEVELS_M) + 1.0)
  axis.set_xlabel("x = local_forward_m")
  axis.set_ylabel("y = local_right_m")
  axis.set_aspect("equal", adjustable="box")
  axis.grid(True, color="#d1d5db", linewidth=0.65, alpha=0.85)
  axis.axhline(0.0, color="#374151", linewidth=0.9)
  axis.axvline(0.0, color="#374151", linewidth=0.9)
  axis.legend(
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    borderaxespad=0.0,
    fontsize=8,
    frameon=True,
  )
  axis.set_title(
    "Proxy position-class grid at z=0 m\n"
    "13x13 samples: x,y=-12..12 m at 2 m spacing; labels C/B/T/E mark position class",
    fontsize=13,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  png_path = output_dir / "target_geometry_proxy_xy_position_class_grid_20260615.png"
  svg_path = output_dir / "target_geometry_proxy_xy_position_class_grid_20260615.svg"
  fig.savefig(png_path, dpi=180, bbox_inches="tight")
  fig.savefig(svg_path, bbox_inches="tight")
  plt.close(fig)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def render_centerline_z_heatmap(
  report: dict[str, Any],
  *,
  output_dir: Path,
) -> dict[str, str]:
  plt, np = _ensure_matplotlib()
  matrix_info = report["centerline_z_matrix"]
  matrix = np.array(
    [
      [float(value) if value is not None else np.nan for value in row]
      for row in matrix_info["probability_matrix"]
    ],
    dtype=float,
  )
  fig, axis = plt.subplots(figsize=(12.5, 3.6), constrained_layout=True)
  cmap = plt.get_cmap("viridis").copy()
  cmap.set_bad(color="#eef2f7")
  image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap=cmap, aspect="auto")
  axis.set_yticks(range(len(matrix_info["warhead_families"])))
  axis.set_yticklabels(matrix_info["warhead_families"], fontsize=9)
  axis.set_xticks(range(len(matrix_info["local_up_levels_m"])))
  axis.set_xticklabels(
    [f"{float(value):g}" for value in matrix_info["local_up_levels_m"]],
    fontsize=9,
  )
  axis.set_xlabel("local_up_m at x=0, y=0")
  axis.set_ylabel("warhead family")
  axis.set_xticks(
    [idx + 0.5 for idx in range(len(matrix_info["local_up_levels_m"]) - 1)],
    minor=True,
  )
  axis.set_yticks(
    [idx + 0.5 for idx in range(len(matrix_info["warhead_families"]) - 1)],
    minor=True,
  )
  axis.grid(which="minor", color="white", linewidth=0.8)
  axis.tick_params(axis="both", length=0)
  for y_idx, row in enumerate(matrix_info["probability_matrix"]):
    for x_idx, value in enumerate(row):
      if value is None:
        continue
      primary = matrix_info["primary_component_matrix"][y_idx][x_idx]
      position_class = matrix_info["detonation_position_class_matrix"][y_idx][x_idx]
      color = "white" if float(value) > 0.52 else "#111827"
      axis.text(
        x_idx,
        y_idx,
        f"{float(value):.3f}\n"
        f"{_case_primary_short(str(primary))}\n"
        f"{_class_short(str(position_class))}",
        ha="center",
        va="center",
        fontsize=6.8,
        color=color,
      )
  cbar = fig.colorbar(image, ax=axis, fraction=0.028, pad=0.02)
  cbar.ax.set_ylabel("Primary P(fail)", rotation=270, labelpad=14, fontsize=9)
  fig.suptitle(
    "Proxy-only centerline vertical detonation probe\n"
    "Fixed x=0, y=0; velocity points toward origin; cells label receiver and position class",
    fontsize=13,
  )
  output_dir.mkdir(parents=True, exist_ok=True)
  png_path = output_dir / "target_geometry_proxy_centerline_z_heatmap_20260615.png"
  svg_path = output_dir / "target_geometry_proxy_centerline_z_heatmap_20260615.svg"
  fig.savefig(png_path, dpi=180, bbox_inches="tight")
  fig.savefig(svg_path, bbox_inches="tight")
  plt.close(fig)
  return {
    "png_path": _relative_path(png_path),
    "svg_path": _relative_path(svg_path),
  }


def write_report(report: dict[str, Any], *, output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "target_geometry_proxy_standoff_grid_probe_20260615.json"
  output_path.write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return output_path


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--seed", type=int, default=20260615)
  parser.add_argument("--no-render", action="store_true")
  args = parser.parse_args()

  report = generate_report(seed=int(args.seed))
  if not args.no_render:
    report["rendered_figures"] = {
      "z_layer_heatmap": render_z_layer_heatmap(
        report,
        output_dir=args.output_dir,
      ),
      "centerline_z_heatmap": render_centerline_z_heatmap(
        report,
        output_dir=args.output_dir,
      ),
      "xy_position_class_grid": render_xy_position_class_grid(
        report,
        output_dir=args.output_dir,
      ),
    }
  output_path = write_report(report, output_dir=args.output_dir)
  print(json.dumps(report, indent=2, sort_keys=True))
  print(f"\nwrote {_relative_path(output_path)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
