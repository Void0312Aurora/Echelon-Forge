"""Component binding and review-point diagnostics for airframe review."""

from __future__ import annotations

import math
from typing import Any, Iterable

from tools.geometry.airframe_review import bounds_ops
from tools.geometry.airframe_review.constants import (
  COMPONENT_BINDING_SCHEMA_VERSION,
  COMPONENT_SEMANTIC_REVIEW_RULES,
  CROSS_REGION_REVIEW_SEMANTICS,
  GEOMETRY_REVIEW_SEMANTICS,
  HARD_BLOCKER_REVIEW_SEMANTICS,
  INVALID_COMPONENT_REGION_BINDINGS,
  REVIEW_POINT_COMPONENT_RADIUS_M,
  REVIEW_POINT_DIAGNOSTICS_SCHEMA_VERSION,
)
from tools.geometry.airframe_review.primitives import _round, _round_vec


def _iter_damage_components(aircraft: dict[str, Any]) -> Iterable[dict[str, Any]]:
  for hitbox_index, hitbox in enumerate(aircraft.get("damage_model", {}).get("hitboxes", [])):
    hitbox_bounds = bounds_ops.box_from_center_size(
      [float(value) for value in hitbox["offset"]],
      [float(value) for value in hitbox["size"]],
    )
    for component in hitbox.get("components", []):
      component_bounds = bounds_ops.box_from_center_size(
        [float(value) for value in component["offset"]],
        [float(value) for value in component["size"]],
      )
      yield {
        "hitbox_index": hitbox_index,
        "hitbox_systems": hitbox.get("systems", []),
        "hitbox_bounds": hitbox_bounds,
        "component": component,
        "component_bounds": component_bounds,
      }


def _rank_region_bindings(
  component_bounds: dict[str, list[float]],
  regions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  component_volume = max(bounds_ops.volume(component_bounds), 1e-9)
  ranked: list[dict[str, Any]] = []
  for region in regions:
    region_bounds = region["bounds"]
    intersection = bounds_ops.intersection_bounds(component_bounds, region_bounds)
    overlap_volume = 0.0 if intersection is None else bounds_ops.volume(intersection)
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "component_overlap_fraction": _round(overlap_volume / component_volume, 5),
        "region_overlap_fraction": _round(overlap_volume / max(bounds_ops.volume(region_bounds), 1e-9), 5),
        "center_inside_region": bounds_ops.contains_point(region_bounds, component_bounds["center"]),
        "center_distance_m": _round(bounds_ops.bounds_center_distance(component_bounds, region_bounds)),
        "region_center_y_m": region_bounds["center"][1],
      }
    )
  ranked.sort(
    key=lambda row: (
      row["component_overlap_fraction"],
      row["center_inside_region"],
      -row["center_distance_m"],
    ),
    reverse=True,
  )
  return ranked


def _declared_side(value: str) -> str | None:
  if value.startswith("left_") or "_left_" in value:
    return "left"
  if value.startswith("right_") or "_right_" in value:
    return "right"
  return None


def _y_sign(value: float, *, tolerance: float = 1e-6) -> str:
  if value > tolerance:
    return "positive_y"
  if value < -tolerance:
    return "negative_y"
  return "centerline_y"


def _component_side_relation(
  *,
  component_name: str,
  component_bounds: dict[str, list[float]],
  best: dict[str, Any],
) -> dict[str, Any]:
  component_side = _declared_side(component_name)
  region_side = _declared_side(best["region_id"])
  mismatch = (
    component_side is not None
    and region_side is not None
    and component_side != region_side
  )
  return {
    "component_declared_side": component_side or "none",
    "bound_region_declared_side": region_side or "none",
    "component_center_y_m": component_bounds["center"][1],
    "bound_region_center_y_m": best["region_center_y_m"],
    "component_center_y_sign": _y_sign(component_bounds["center"][1]),
    "bound_region_center_y_sign": _y_sign(best["region_center_y_m"]),
    "side_sign_mismatch": mismatch,
  }


def _component_anomalies(
  *,
  component_name: str,
  component_bounds: dict[str, list[float]],
  outer_envelope: dict[str, list[float]],
  best: dict[str, Any],
) -> list[str]:
  anomalies: list[str] = []
  envelope_fraction = bounds_ops.bounds_containment_fraction(component_bounds, outer_envelope)
  if envelope_fraction < 0.99:
    anomalies.append("component_extends_outside_outer_envelope")
  if best["component_overlap_fraction"] <= 0.0:
    anomalies.append("no_outer_region_overlap")
  elif best["component_overlap_fraction"] < 0.50:
    anomalies.append("low_outer_region_overlap")
  if not best["center_inside_region"]:
    anomalies.append("component_center_outside_bound_region")
  if component_name.startswith("left_") and best["region_id"].startswith("right_"):
    anomalies.append("left_name_bound_to_positive_y_region_sign_review")
  if component_name.startswith("right_") and best["region_id"].startswith("left_"):
    anomalies.append("right_name_bound_to_negative_y_region_sign_review")
  return anomalies


def _component_review_classification(
  *,
  component_name: str,
  best: dict[str, Any],
  raw_anomalies: list[str],
  side_relation: dict[str, Any],
) -> dict[str, Any]:
  anomalies = list(raw_anomalies)
  notes: list[str] = []
  blocked_region_binding = {
    "blocked": False,
    "blocked_region_id": "",
    "preferred_region_ids": [],
  }
  if side_relation["side_sign_mismatch"]:
    return {
      "review_status": "needs_review",
      "review_semantics": "side_sign_mismatch_hard_blocker",
      "review_severity": "hard_blocker",
      "anomalies": anomalies,
      "geometry_observations": raw_anomalies,
      "semantic_region_ids": [],
      "suppressed_anomalies": [],
      "blocked_region_binding": blocked_region_binding,
      "review_notes": [
        "component declared side and bound region declared side disagree",
        "systemic side-sign blocker; do not infer the correct side by visual inspection alone",
      ],
    }

  invalid_rule = INVALID_COMPONENT_REGION_BINDINGS.get(component_name)
  if invalid_rule and best["region_id"] in invalid_rule["blocked_region_ids"]:
    if "blocked_invalid_region_binding_rule" not in anomalies:
      anomalies.append("blocked_invalid_region_binding_rule")
    blocked_region_binding = {
      "blocked": True,
      "blocked_region_id": best["region_id"],
      "preferred_region_ids": list(invalid_rule["preferred_region_ids"]),
    }
    return {
      "review_status": "needs_review",
      "review_semantics": invalid_rule["review_semantics"],
      "review_severity": invalid_rule["review_severity"],
      "anomalies": anomalies,
      "geometry_observations": raw_anomalies,
      "semantic_region_ids": list(invalid_rule["preferred_region_ids"]),
      "suppressed_anomalies": [],
      "blocked_region_binding": blocked_region_binding,
      "review_notes": list(invalid_rule["notes"]),
    }

  semantic_rule = COMPONENT_SEMANTIC_REVIEW_RULES.get(component_name)
  if (
    semantic_rule
    and best["region_id"] in semantic_rule["applicable_bound_region_ids"]
    and any(item in anomalies for item in semantic_rule["suppressed_anomalies"])
    and best["center_inside_region"]
  ):
    suppressed = [
      item for item in anomalies if item in semantic_rule["suppressed_anomalies"]
    ]
    anomalies = [
      item for item in anomalies if item not in semantic_rule["suppressed_anomalies"]
    ]
    notes.extend(semantic_rule["notes"])
    notes.extend(f"suppressed geometry observation: {item}" for item in suppressed)
    return {
      "review_status": semantic_rule["review_status"],
      "review_semantics": semantic_rule["review_semantics"],
      "review_severity": semantic_rule["review_severity"],
      "anomalies": anomalies,
      "geometry_observations": raw_anomalies,
      "semantic_region_ids": list(semantic_rule["semantic_region_ids"]),
      "suppressed_anomalies": suppressed,
      "blocked_region_binding": blocked_region_binding,
      "review_notes": notes,
    }

  if anomalies:
    return {
      "review_status": "needs_review",
      "review_semantics": "geometry_review_required",
      "review_severity": "needs_review",
      "anomalies": anomalies,
      "geometry_observations": raw_anomalies,
      "semantic_region_ids": [],
      "suppressed_anomalies": [],
      "blocked_region_binding": blocked_region_binding,
      "review_notes": ["component geometry or placement needs human review"],
    }

  return {
    "review_status": "candidate_binding",
    "review_semantics": "candidate_direct_region_binding",
    "review_severity": "candidate",
    "anomalies": anomalies,
    "geometry_observations": raw_anomalies,
    "semantic_region_ids": [],
    "suppressed_anomalies": [],
    "blocked_region_binding": blocked_region_binding,
    "review_notes": ["candidate direct binding after visual review"],
  }


def build_component_binding_report(
  aircraft: dict[str, Any],
  mapping: dict[str, Any],
) -> dict[str, Any]:
  regions = mapping["outer_regions"]
  outer_envelope = mapping["outer_envelope"]["bounds"]
  rows: list[dict[str, Any]] = []
  for item in _iter_damage_components(aircraft):
    component = item["component"]
    component_bounds = item["component_bounds"]
    rankings = _rank_region_bindings(component_bounds, regions)
    best = rankings[0]
    anomalies = _component_anomalies(
      component_name=component["name"],
      component_bounds=component_bounds,
      outer_envelope=outer_envelope,
      best=best,
    )
    side_relation = _component_side_relation(
      component_name=component["name"],
      component_bounds=component_bounds,
      best=best,
    )
    review_classification = _component_review_classification(
      component_name=component["name"],
      best=best,
      raw_anomalies=anomalies,
      side_relation=side_relation,
    )
    rows.append(
      {
        "component_name": component["name"],
        "system": component.get("system", ""),
        "critical": bool(component.get("critical", False)),
        "hitbox_index": item["hitbox_index"],
        "component_bounds": component_bounds,
        "parent_hitbox_bounds": item["hitbox_bounds"],
        "bound_region_id": best["region_id"],
        "bound_region_role": best["region_role"],
        "component_overlap_fraction": best["component_overlap_fraction"],
        "region_overlap_fraction": best["region_overlap_fraction"],
        "center_inside_bound_region": best["center_inside_region"],
        "center_distance_m": best["center_distance_m"],
        "outer_envelope_containment_fraction": _round(
          bounds_ops.bounds_containment_fraction(component_bounds, outer_envelope), 5
        ),
        "candidate_regions": rankings[:5],
        "review_status": review_classification["review_status"],
        "review_semantics": review_classification["review_semantics"],
        "review_severity": review_classification["review_severity"],
        "anomalies": review_classification["anomalies"],
        "geometry_observations": review_classification["geometry_observations"],
        "suppressed_anomalies": review_classification["suppressed_anomalies"],
        "semantic_region_ids": review_classification["semantic_region_ids"],
        "side_sign_relation": side_relation,
        "blocked_region_binding": review_classification["blocked_region_binding"],
        "review_notes": review_classification["review_notes"],
        "authority_boundary": "review_only_not_true_internal_component_geometry",
      }
    )

  needs_review = [row for row in rows if row["review_status"] == "needs_review"]
  return {
    "schema_version": COMPONENT_BINDING_SCHEMA_VERSION,
    "status": "component_binding_report_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "summary": {
      "component_count": len(rows),
      "bound_component_count": len(rows) - sum(
        1 for row in rows if "no_outer_region_overlap" in row["anomalies"]
      ),
      "needs_review_count": len(needs_review),
      "side_sign_review_count": sum(
        1
        for row in rows
        if row["review_semantics"] == "side_sign_mismatch_hard_blocker"
      ),
      "hard_blocker_count": sum(
        1
        for row in rows
        if row["review_semantics"] in HARD_BLOCKER_REVIEW_SEMANTICS
      ),
      "invalid_region_binding_blocked_count": sum(
        1
        for row in rows
        if row["review_semantics"] == "invalid_region_binding_blocked"
      ),
      "cross_region_semantic_candidate_count": sum(
        1
        for row in rows
        if row["review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
      ),
      "geometry_review_required_count": sum(
        1
        for row in rows
        if row["review_semantics"] in GEOMETRY_REVIEW_SEMANTICS
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Check every needs_review component before using outer regions in runtime projection.",
      },
      {
        "priority": "high",
        "question": "Resolve left/right sign convention before treating wing bindings as authoritative.",
      },
      {
        "priority": "medium",
        "question": "Review large components such as wing_spar_center for intentional multi-region coverage.",
      },
    ],
    "authority_boundary": mapping["authority_boundary"],
  }


def _default_review_points() -> list[dict[str, Any]]:
  return [
    {
      "id": "nose_axis_4m",
      "label": "nose x=4m",
      "point": [4.0, 0.0, 0.0],
      "aspect": "nose",
      "rationale": "Known close-to-shape nose review point that previously lacked component explanation.",
    },
    {
      "id": "nose_axis_6m",
      "label": "nose x=6m",
      "point": [6.0, 0.0, 0.0],
      "aspect": "nose",
      "rationale": "Forward nose review point used to compare the old 4 m / 6 m discontinuity.",
    },
    {
      "id": "tail_axis_4m",
      "label": "tail x=-4m",
      "point": [-4.0, 0.0, 0.0],
      "aspect": "tail",
      "rationale": "Aft approach point for engine and tail-control exposure review.",
    },
    {
      "id": "tail_axis_6m",
      "label": "tail x=-6m",
      "point": [-6.0, 0.0, 0.0],
      "aspect": "tail",
      "rationale": "Rear nozzle and engine-bay review point.",
    },
    {
      "id": "right_beam_4m",
      "label": "beam y=4m",
      "point": [0.0, 4.0, 0.0],
      "aspect": "beam",
      "rationale": "Lateral wing exposure review point on positive-y side.",
    },
    {
      "id": "right_beam_6m",
      "label": "beam y=6m",
      "point": [0.0, 6.0, 0.0],
      "aspect": "beam",
      "rationale": "Outer lateral miss point on positive-y side.",
    },
    {
      "id": "left_beam_4m",
      "label": "beam y=-4m",
      "point": [0.0, -4.0, 0.0],
      "aspect": "beam",
      "rationale": "Lateral wing exposure review point on negative-y side.",
    },
    {
      "id": "left_beam_6m",
      "label": "beam y=-6m",
      "point": [0.0, -6.0, 0.0],
      "aspect": "beam",
      "rationale": "Outer lateral miss point on negative-y side.",
    },
    {
      "id": "above_4m",
      "label": "above z=4m",
      "point": [0.0, 0.0, 4.0],
      "aspect": "above",
      "rationale": "Top-side review point for height and vertical-tail coverage.",
    },
    {
      "id": "below_4m",
      "label": "below z=-4m",
      "point": [0.0, 0.0, -4.0],
      "aspect": "below",
      "rationale": "Underside review point for intake and low-fuselage coverage.",
    },
  ]


def _rank_point_to_regions(
  point: list[float],
  regions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for region in regions:
    distance = bounds_ops.point_box_distance(point, region["bounds"])
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "distance_m": _round(distance),
        "contains_point": bounds_ops.contains_point(region["bounds"], point),
        "center_distance_m": _round(
          math.sqrt(
            sum(
              (point[axis] - region["bounds"]["center"][axis]) ** 2
              for axis in range(3)
            )
          )
        ),
      }
    )
  ranked.sort(key=lambda row: (row["distance_m"], row["center_distance_m"]))
  return ranked


def _rank_point_to_components(
  point: list[float],
  rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for row in rows:
    distance = bounds_ops.point_box_distance(point, row["component_bounds"])
    ranked.append(
      {
        "component_name": row["component_name"],
        "system": row["system"],
        "critical": row["critical"],
        "bound_region_id": row["bound_region_id"],
        "distance_m": _round(distance),
        "contains_point": bounds_ops.contains_point(row["component_bounds"], point),
        "review_status": row["review_status"],
      }
    )
  ranked.sort(key=lambda row: (row["distance_m"], row["component_name"]))
  return ranked


def _diagnostic_interpretation(
  *,
  inside_outer_count: int,
  inside_component_count: int,
  candidate_component_count: int,
) -> str:
  if inside_component_count:
    return "point_inside_component_box_review_only"
  if inside_outer_count and candidate_component_count:
    return "inside_outer_shape_with_nearby_component_candidates_review_only"
  if inside_outer_count:
    return "inside_outer_shape_but_no_component_candidate_within_review_radius"
  if candidate_component_count:
    return "outside_outer_shape_but_near_component_candidate_review_only"
  return "outside_outer_shape_no_near_component_candidate_review_only"


def build_review_point_diagnostics(
  mapping: dict[str, Any],
  component_report: dict[str, Any],
  *,
  review_points: list[dict[str, Any]] | None = None,
  candidate_radius_m: float = REVIEW_POINT_COMPONENT_RADIUS_M,
) -> dict[str, Any]:
  points = review_points if review_points is not None else _default_review_points()
  rows: list[dict[str, Any]] = []
  for index, point_record in enumerate(points, start=1):
    point = [float(value) for value in point_record["point"]]
    outer_rankings = _rank_point_to_regions(point, mapping["outer_regions"])
    component_rankings = _rank_point_to_components(point, component_report["rows"])
    inside_outer_count = sum(1 for row in outer_rankings if row["contains_point"])
    inside_component_count = sum(1 for row in component_rankings if row["contains_point"])
    nearby_components = [
      row for row in component_rankings if row["distance_m"] <= candidate_radius_m
    ]
    rows.append(
      {
        "point_index": index,
        "point_id": point_record["id"],
        "label": point_record["label"],
        "aspect": point_record["aspect"],
        "point_m": _round_vec(point),
        "nearest_outer_region_id": outer_rankings[0]["region_id"],
        "nearest_outer_region_role": outer_rankings[0]["region_role"],
        "nearest_outer_distance_m": outer_rankings[0]["distance_m"],
        "inside_outer_region_count": inside_outer_count,
        "nearest_component_name": component_rankings[0]["component_name"],
        "nearest_component_system": component_rankings[0]["system"],
        "nearest_component_distance_m": component_rankings[0]["distance_m"],
        "inside_component_count": inside_component_count,
        "candidate_component_radius_m": candidate_radius_m,
        "candidate_component_count": len(nearby_components),
        "candidate_components": nearby_components[:8],
        "outer_region_rankings": outer_rankings[:5],
        "component_rankings": component_rankings[:8],
        "interpretation": _diagnostic_interpretation(
          inside_outer_count=inside_outer_count,
          inside_component_count=inside_component_count,
          candidate_component_count=len(nearby_components),
        ),
        "rationale": point_record["rationale"],
        "authority_boundary": "review_only_not_runtime_lethality_decision",
      }
    )

  return {
    "schema_version": REVIEW_POINT_DIAGNOSTICS_SCHEMA_VERSION,
    "status": "review_point_distance_diagnostics_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "candidate_component_radius_m": candidate_radius_m,
    "summary": {
      "review_point_count": len(rows),
      "inside_outer_region_point_count": sum(
        1 for row in rows if row["inside_outer_region_count"] > 0
      ),
      "inside_component_point_count": sum(
        1 for row in rows if row["inside_component_count"] > 0
      ),
      "zero_outer_distance_without_component_candidate_count": sum(
        1
        for row in rows
        if row["nearest_outer_distance_m"] == 0.0
        and row["candidate_component_count"] == 0
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review nose_axis_4m and nose_axis_6m before using these boxes for runtime near-fuze projection.",
      },
      {
        "priority": "high",
        "question": "Confirm beam left/right sign before treating wing candidates as authoritative.",
      },
      {
        "priority": "medium",
        "question": "Use TG-P6 finer geometry before any path or swept intersection decision.",
      },
    ],
    "authority_boundary": mapping["authority_boundary"],
  }
