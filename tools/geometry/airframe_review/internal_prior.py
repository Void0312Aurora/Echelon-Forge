"""Internal component prior geometry candidates for airframe review."""

from __future__ import annotations

import math
from typing import Any

from tools.geometry.airframe_review import bounds_ops, shape_geometry
from tools.geometry.airframe_review.constants import (
  CROSS_REGION_REVIEW_SEMANTICS,
  INTERNAL_COMPONENT_PRIOR_RULES,
  INTERNAL_COMPONENT_PRIOR_SCHEMA_VERSION,
  PROMOTED_SHAPE_STATUSES,
)
from tools.geometry.airframe_review.primitives import _round, _round_vec


def _internal_component_prior_rule(component_row: dict[str, Any]) -> dict[str, Any]:
  rule = INTERNAL_COMPONENT_PRIOR_RULES.get(component_row["component_name"])
  if rule is not None:
    return rule
  if component_row.get("critical", False):
    return {
      "shape": "ellipsoid",
      "component_role": "critical_internal_receiver",
      "span_scale": [0.78, 0.78, 0.78],
      "rationale": "default critical receiver prior uses a compact ellipsoid.",
    }
  return {
    "shape": "sphere",
    "component_role": "small_internal_receiver",
    "span_scale": [0.75, 0.75, 0.75],
    "rationale": "default non-critical receiver prior uses a compact sphere.",
  }


def _constraint_region_ids(component_row: dict[str, Any]) -> list[str]:
  semantic_ids = [
    region_id
    for region_id in component_row.get("semantic_region_ids", [])
    if region_id
  ]
  if component_row["review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS and semantic_ids:
    return semantic_ids
  return [component_row["bound_region_id"]]


def _constrain_prior_to_bounds(
  *,
  center: list[float],
  half_extents: list[float],
  constraint_bounds: dict[str, list[float]],
  margin_m: float,
  allow_size_shrink: bool,
) -> dict[str, Any]:
  usable_min = [constraint_bounds["min"][index] + margin_m for index in range(3)]
  usable_max = [constraint_bounds["max"][index] - margin_m for index in range(3)]
  usable_span = [
    max(usable_max[index] - usable_min[index], 0.02) for index in range(3)
  ]
  shrink_candidates = [
    usable_span[index] / (2.0 * half_extents[index])
    for index in range(3)
    if half_extents[index] > 1.0e-9
  ]
  required_fit_scale = min([1.0] + shrink_candidates)
  applied_size_scale = required_fit_scale if allow_size_shrink else 1.0
  constrained_half = [
    half_extents[index] * applied_size_scale for index in range(3)
  ]
  constrained_center: list[float] = []
  for index in range(3):
    low = usable_min[index] + constrained_half[index]
    high = usable_max[index] - constrained_half[index]
    if low <= high:
      constrained_center.append(min(max(center[index], low), high))
    else:
      constrained_center.append((usable_min[index] + usable_max[index]) * 0.5)
      constrained_half[index] = max(usable_span[index] * 0.5, 0.01)
  bounds = shape_geometry._bounds_from_center_half_extents(constrained_center, constrained_half)
  center_shift = math.sqrt(
    sum((constrained_center[index] - center[index]) ** 2 for index in range(3))
  )
  return {
    "center_m": _round_vec(constrained_center),
    "half_extents_m": _round_vec(constrained_half),
    "bounds": bounds,
    "shrink_scale": _round(applied_size_scale, 5),
    "required_fit_scale": _round(required_fit_scale, 5),
    "size_shrink_allowed": allow_size_shrink,
    "size_preserved": applied_size_scale >= 0.99999,
    "center_shift_m": _round(center_shift),
  }


def _clamp_center_to_bounds(
  center: list[float],
  bounds: dict[str, list[float]],
) -> list[float]:
  return [
    min(max(center[index], bounds["min"][index]), bounds["max"][index])
    for index in range(3)
  ]


def _rule_initial_center(
  *,
  rule: dict[str, Any],
  component_row: dict[str, Any],
  proxies_by_region: dict[str, dict[str, Any]],
) -> list[float]:
  if "center_m" in rule:
    return [float(value) for value in rule["center_m"]]
  center_region_ids = [
    region_id
    for region_id in rule.get("center_region_ids", [])
    if region_id in proxies_by_region
  ]
  if not center_region_ids:
    return component_row["component_bounds"]["center"]
  center_bounds_source = rule.get("center_bounds_source", "source_region_bounds")
  center_bounds = bounds_ops.merge_bounds(
    proxies_by_region[region_id][center_bounds_source]
    for region_id in center_region_ids
  )
  center = list(center_bounds["center"])
  for axis_name, axis_region_ids in rule.get("center_axis_region_ids", {}).items():
    axis_index = shape_geometry._axis_index(axis_name)
    resolved_region_ids = [
      region_id
      for region_id in axis_region_ids
      if region_id in proxies_by_region
    ]
    if not resolved_region_ids:
      continue
    axis_bounds = bounds_ops.merge_bounds(
      proxies_by_region[region_id][center_bounds_source]
      for region_id in resolved_region_ids
    )
    center[axis_index] = axis_bounds["center"][axis_index]
  return center


def build_internal_component_prior_candidate(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  surface_report: dict[str, Any],
) -> dict[str, Any]:
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  whole_airframe_bounds = bounds_ops.merge_bounds(
    proxy["source_region_bounds"] for proxy in proxies_by_region.values()
  )
  airframe_projection_hulls = shape_geometry._whole_airframe_containment_hulls(fine_proxy)
  surface_rows_by_component: dict[str, list[dict[str, Any]]] = {}
  for surface_row in surface_report["rows"]:
    for link in surface_row["linked_internal_components"]:
      surface_rows_by_component.setdefault(link["component_name"], []).append(surface_row)

  rows: list[dict[str, Any]] = []
  for component_row in component_report["rows"]:
    rule = _internal_component_prior_rule(component_row)
    configured_region_ids = rule.get("constraint_region_ids")
    region_ids = [
      region_id
      for region_id in (
        configured_region_ids
        if configured_region_ids is not None
        else _constraint_region_ids(component_row)
      )
      if region_id in proxies_by_region
    ]
    if not region_ids:
      region_ids = [component_row["bound_region_id"]]
    placement_bounds_source = rule.get("constraint_bounds_source", "support_bounds")
    placement_bounds = bounds_ops.merge_bounds(
      proxies_by_region[region_id][placement_bounds_source]
      for region_id in region_ids
    )
    constraint_bounds = whole_airframe_bounds
    constraint_bounds_source = "whole_airframe_source_region_union_bounds"
    margin_m = float(rule.get("constraint_margin_m", 0.03))
    initial_half, _ = shape_geometry._shape_half_extents(
      rule=rule,
      component_bounds=component_row["component_bounds"],
    )
    initial_center = _rule_initial_center(
      rule=rule,
      component_row=component_row,
      proxies_by_region=proxies_by_region,
    )
    initial_bounds = shape_geometry._bounds_from_center_half_extents(initial_center, initial_half)
    placement_center = _clamp_center_to_bounds(initial_center, placement_bounds)
    constrained = _constrain_prior_to_bounds(
      center=placement_center,
      half_extents=initial_half,
      constraint_bounds=constraint_bounds,
      margin_m=margin_m,
      allow_size_shrink=bool(rule.get("allow_constraint_shrink", True)),
    )
    projection_adjustment = {
      "center_m": constrained["center_m"],
      "center_shift_m": 0.0,
    }
    if rule.get("airframe_projection_adjustment", True):
      projection_adjustment = shape_geometry._projection_adjust_center_to_airframe_hulls(
        center=constrained["center_m"],
        half_extents=constrained["half_extents_m"],
        airframe_projection_hulls=airframe_projection_hulls,
      )
    if (
      rule.get("airframe_projection_adjustment", True)
      and projection_adjustment["center_shift_m"] > 0.0
    ):
      constrained = _constrain_prior_to_bounds(
        center=projection_adjustment["center_m"],
        half_extents=constrained["half_extents_m"],
        constraint_bounds=constraint_bounds,
        margin_m=margin_m,
        allow_size_shrink=bool(rule.get("allow_constraint_shrink", True)),
      )
    constrained_shape_payload = shape_geometry._shape_payload_from_half_extents(
      rule=rule,
      half_extents=constrained["half_extents_m"],
      center=constrained["center_m"],
    )
    placement_outside_fraction = bounds_ops.outside_fraction(
      initial_bounds,
      placement_bounds,
    )
    pre_outside_fraction = bounds_ops.outside_fraction(initial_bounds, constraint_bounds)
    post_outside_fraction = bounds_ops.outside_fraction(
      constrained["bounds"],
      constraint_bounds,
    )
    if post_outside_fraction > 1.0e-4:
      if component_row["review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS:
        constraint_status = "cross_region_nominal_size_exceeds_airframe_held"
      elif (
        constrained["required_fit_scale"] < 0.99999
        and constrained["size_preserved"]
      ):
        constraint_status = "nominal_size_exceeds_airframe_needs_review"
      else:
        constraint_status = "constraint_failed_needs_review"
    elif component_row["review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS:
      constraint_status = "cross_region_prior_constrained_inside_airframe_held"
    elif placement_outside_fraction > 1.0e-6:
      constraint_status = "placed_inside_airframe_exceeds_parent_shell_review"
    elif pre_outside_fraction > 1.0e-6 or constrained["center_shift_m"] > 0.0 or constrained["shrink_scale"] < 0.99999:
      constraint_status = "constrained_inside_whole_airframe"
    else:
      constraint_status = "already_inside_whole_airframe"

    linked_surface_ids = [
      surface_row["surface_component_id"]
      for surface_row in surface_rows_by_component.get(
        component_row["component_name"],
        [],
      )
    ]
    rows.append(
      {
        "component_name": component_row["component_name"],
        "system": component_row["system"],
        "critical": component_row["critical"],
        "component_role": rule["component_role"],
        "prior_shape": rule["shape"],
        "prior_axis": rule.get("axis", ""),
        "prior_rationale": rule["rationale"],
        "size_basis": rule.get(
          "size_basis",
          "component_aabb_scaled_prior",
        ),
        "shape_promotion_status": rule.get(
          "shape_promotion_status",
          "not_promoted_from_subcomponent_shape_candidate",
        ),
        "size_evidence_level": rule.get(
          "size_evidence_level",
          "synthetic_scaled_from_runtime_aabb",
        ),
        "size_source_urls": rule.get("size_source_urls", []),
        "nominal_dimensions_m": _round_vec(
          [value * 2.0 for value in initial_half]
        ),
        "bound_region_id": component_row["bound_region_id"],
        "constraint_region_ids": region_ids,
        "constraint_mode": (
          f"multi_region_placement_{placement_bounds_source}_whole_airframe_constraint"
          if len(region_ids) > 1
          else f"single_parent_placement_{placement_bounds_source}_whole_airframe_constraint"
        ),
        "constraint_bounds": constraint_bounds,
        "constraint_bounds_source": constraint_bounds_source,
        "placement_bounds": placement_bounds,
        "placement_bounds_source": placement_bounds_source,
        "whole_airframe_bounds": whole_airframe_bounds,
        "constraint_margin_m": margin_m,
        "linked_surface_component_ids": sorted(set(linked_surface_ids)),
        "component_review_status": component_row["review_status"],
        "component_review_semantics": component_row["review_semantics"],
        "component_review_severity": component_row["review_severity"],
        "original_aabb_bounds": component_row["component_bounds"],
        "original_aabb_containment_fraction": _round(
          bounds_ops.bounds_containment_fraction(
            component_row["component_bounds"],
            placement_bounds,
          ),
          5,
        ),
        "prior_unconstrained_geometry": {
          **shape_geometry._shape_payload_from_half_extents(
            rule=rule,
            half_extents=initial_half,
            center=initial_center,
          ),
          "center_m": _round_vec(initial_center),
          "half_extents_m": _round_vec(initial_half),
          "bounds": initial_bounds,
          "volume_m3": _round(shape_geometry._shape_volume_m3(rule, initial_half)),
        },
        "placement_geometry": {
          **shape_geometry._shape_payload_from_half_extents(
            rule=rule,
            half_extents=initial_half,
            center=placement_center,
          ),
          "center_m": _round_vec(placement_center),
          "half_extents_m": _round_vec(initial_half),
          "bounds": shape_geometry._bounds_from_center_half_extents(
            placement_center,
            initial_half,
          ),
          "volume_m3": _round(shape_geometry._shape_volume_m3(rule, initial_half)),
        },
        "constrained_geometry": {
          **constrained_shape_payload,
          "center_m": constrained["center_m"],
          "half_extents_m": constrained["half_extents_m"],
          "bounds": constrained["bounds"],
          "volume_m3": _round(
            shape_geometry._shape_volume_m3(rule, constrained["half_extents_m"])
          ),
        },
        "constraint_adjustment": {
          "shrink_scale": constrained["shrink_scale"],
          "required_fit_scale": constrained["required_fit_scale"],
          "size_shrink_allowed": constrained["size_shrink_allowed"],
          "size_preserved": constrained["size_preserved"],
          "center_shift_m": constrained["center_shift_m"],
          "airframe_projection_center_shift_m": projection_adjustment[
            "center_shift_m"
          ],
          "placement_outside_fraction": _round(placement_outside_fraction, 5),
          "pre_constraint_outside_fraction": _round(pre_outside_fraction, 5),
          "post_constraint_outside_fraction": _round(post_outside_fraction, 5),
        },
        "constraint_status": constraint_status,
        "runtime_projection_status": (
          "runtime_schema_candidate_not_activated_prior_shape_review_required"
        ),
        "aabb_runtime_fallback_candidate": {
          "name": component_row["component_name"],
          "system": component_row["system"],
          "offset": constrained["bounds"]["center"],
          "size": constrained["bounds"]["span"],
          "geometry_primitive": "aabb",
          "geometry": {
            "source": "a2_internal_component_prior_constrained_bounds",
            "source_region_id": component_row["bound_region_id"],
            "constraint_region_ids": region_ids,
            "prior_shape": rule["shape"],
            "runtime_projection_status": (
              "aabb_fallback_only_not_shape_exact"
            ),
          },
          "critical": component_row["critical"],
        },
        "authority_boundary": (
          "synthetic_internal_component_prior_candidate_not_true_internal_geometry"
        ),
      }
    )

  return {
    "schema_version": INTERNAL_COMPONENT_PRIOR_SCHEMA_VERSION,
    "status": "internal_component_prior_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_mapping_schema_version": mapping["schema_version"],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "source_component_binding_schema_version": component_report["schema_version"],
    "source_surface_component_schema_version": surface_report["schema_version"],
    "whole_airframe_bounds": whole_airframe_bounds,
    "summary": {
      "internal_component_prior_count": len(rows),
      "runtime_active_component_count": 0,
      "post_constraint_outside_count": sum(
        1
        for row in rows
        if row["constraint_adjustment"]["post_constraint_outside_fraction"] > 0.0
      ),
      "constrained_inside_count": sum(
        1
        for row in rows
        if row["constraint_status"]
        in {
          "constrained_inside_parent_shell",
          "cross_region_prior_constrained_inside_union_held",
          "already_inside_parent_shell",
          "constrained_inside_whole_airframe",
          "placed_inside_airframe_exceeds_parent_shell_review",
          "cross_region_prior_constrained_inside_airframe_held",
          "already_inside_whole_airframe",
        }
      ),
      "nominal_size_fit_issue_count": sum(
        1
        for row in rows
        if row["constraint_status"]
        in {
          "nominal_size_exceeds_parent_shell_needs_review",
          "cross_region_nominal_size_exceeds_union_held",
          "nominal_size_exceeds_airframe_needs_review",
          "cross_region_nominal_size_exceeds_airframe_held",
          "constraint_failed_needs_review",
        }
      ),
      "parent_shell_exceed_review_count": sum(
        1
        for row in rows
        if row["constraint_status"]
        == "placed_inside_airframe_exceeds_parent_shell_review"
      ),
      "cross_region_held_prior_count": sum(
        1
        for row in rows
        if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
      ),
      "shape_counts": {
        shape: sum(1 for row in rows if row["prior_shape"] == shape)
        for shape in sorted({row["prior_shape"] for row in rows})
      },
      "shape_promotion_count": sum(
        1
        for row in rows
        if row["shape_promotion_status"] in PROMOTED_SHAPE_STATUSES
      ),
      "shape_promotion_status_counts": {
        status: sum(1 for row in rows if row["shape_promotion_status"] == status)
        for status in sorted({row["shape_promotion_status"] for row in rows})
      },
      "size_evidence_level_counts": {
        level: sum(1 for row in rows if row["size_evidence_level"] == level)
        for level in sorted({row["size_evidence_level"] for row in rows})
      },
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review constrained prior geometry before replacing old receiver AABBs.",
      },
      {
        "priority": "high",
        "question": "Keep engine_core and wing_spar_center held unless their multi-region ownership is explicitly accepted or split.",
      },
      {
        "priority": "medium",
        "question": "Use public-size evidence levels before treating any receiver prior as true F-16 internal engineering geometry.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_schema_parse_ready_candidate": True,
      "true_internal_component_geometry": False,
      "public_size_reference_seeded_geometry": True,
    },
  }
