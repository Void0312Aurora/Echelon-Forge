"""Held cross-region component segment candidates."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review import bounds_ops, shape_geometry
from tools.geometry.airframe_review.constants import (
  CROSS_REGION_HELD_SEGMENT_SCHEMA_VERSION,
  HELD_SEGMENT_SHAPE_PLACEMENT_OVERRIDES,
  PROMOTED_SHAPE_STATUSES,
)
from tools.geometry.airframe_review.primitives import _round, _round_vec


def _segment_geometry_from_center_dimensions(
  *,
  shape: str,
  axis: str,
  center: list[float],
  dimensions_m: list[float],
) -> dict[str, Any]:
  rule = {
    "shape": shape,
    "axis": axis,
    "dimensions_m": dimensions_m,
  }
  half_extents, _ = shape_geometry._shape_half_extents(
    rule=rule,
    component_bounds=shape_geometry._bounds_from_center_half_extents(
      center,
      [max(value * 0.5, 0.01) for value in dimensions_m],
    ),
  )
  payload = shape_geometry._shape_payload_from_half_extents(
    rule=rule,
    half_extents=half_extents,
    center=center,
  )
  bounds = shape_geometry._bounds_from_center_half_extents(center, half_extents)
  return {
    **payload,
    "center_m": _round_vec(center),
    "half_extents_m": _round_vec(half_extents),
    "bounds": bounds,
    "volume_m3": _round(shape_geometry._shape_volume_m3(rule, half_extents)),
  }


def _held_segment_row(
  *,
  parent_prior: dict[str, Any],
  segment_index: int,
  segment_id: str,
  segment_role: str,
  owner_region_ids: list[str],
  dimensions_m: list[float],
  center_m: list[float],
  source_basis: str,
) -> dict[str, Any]:
  override = HELD_SEGMENT_SHAPE_PLACEMENT_OVERRIDES.get(segment_id, {})
  segment_shape = override.get("shape", parent_prior["prior_shape"])
  segment_axis = override.get("axis", parent_prior["prior_axis"])
  center_offset = override.get("center_offset_m", [0.0, 0.0, 0.0])
  segment_center = [
    center_m[index] + float(center_offset[index]) for index in range(3)
  ]
  geometry = _segment_geometry_from_center_dimensions(
    shape=segment_shape,
    axis=segment_axis,
    center=segment_center,
    dimensions_m=dimensions_m,
  )
  source_basis_values = [source_basis]
  if "source_basis" in override:
    source_basis_values.append(override["source_basis"])
  parent_bounds = parent_prior["constrained_geometry"]["bounds"]
  whole_airframe_bounds = parent_prior["whole_airframe_bounds"]
  parent_outside_fraction = bounds_ops.outside_fraction(geometry["bounds"], parent_bounds)
  whole_airframe_outside_fraction = bounds_ops.outside_fraction(
    geometry["bounds"],
    whole_airframe_bounds,
  )
  return {
    "parent_component_name": parent_prior["component_name"],
    "segment_id": segment_id,
    "segment_index": segment_index,
    "segment_role": segment_role,
    "owner_region_ids": owner_region_ids,
    "segment_shape": segment_shape,
    "segment_axis": segment_axis,
    "source_parent_segment_shape": parent_prior["prior_shape"],
    "shape_promotion_status": override.get(
      "shape_promotion_status",
      "inherited_parent_prior_shape",
    ),
    "center_offset_m": _round_vec(center_offset),
    "nominal_dimensions_m": _round_vec(dimensions_m),
    "geometry": geometry,
    "source_basis": ";".join(source_basis_values),
    "source_parent_prior_bounds": parent_bounds,
    "whole_airframe_bounds": whole_airframe_bounds,
    "parent_component_review_semantics": parent_prior[
      "component_review_semantics"
    ],
    "parent_component_constraint_status": parent_prior["constraint_status"],
    "inside_parent_prior_bounds": parent_outside_fraction <= 1.0e-6,
    "inside_whole_airframe_bounds": whole_airframe_outside_fraction <= 1.0e-6,
    "parent_prior_outside_fraction": _round(parent_outside_fraction, 5),
    "whole_airframe_outside_fraction": _round(
      whole_airframe_outside_fraction,
      5,
    ),
    "runtime_projection_status": (
      "review_only_cross_region_segment_not_runtime_component"
    ),
    "authority_boundary": (
      "synthetic_split_of_held_cross_region_receiver_not_true_internal_structure"
    ),
  }


def _axis_interval_segment(
  *,
  parent_prior: dict[str, Any],
  segment_index: int,
  segment_id: str,
  segment_role: str,
  owner_region_ids: list[str],
  axis_name: str,
  min_value: float,
  max_value: float,
  source_basis: str,
) -> dict[str, Any]:
  axis = shape_geometry._axis_index(axis_name)
  parent_center = list(parent_prior["constrained_geometry"]["center_m"])
  parent_span = parent_prior["constrained_geometry"]["bounds"]["span"]
  dimensions = list(parent_span)
  dimensions[axis] = max_value - min_value
  center = list(parent_center)
  center[axis] = (min_value + max_value) * 0.5
  return _held_segment_row(
    parent_prior=parent_prior,
    segment_index=segment_index,
    segment_id=segment_id,
    segment_role=segment_role,
    owner_region_ids=owner_region_ids,
    dimensions_m=dimensions,
    center_m=center,
    source_basis=source_basis,
  )


def _split_interval_evenly(
  min_value: float,
  max_value: float,
  count: int,
) -> list[tuple[float, float]]:
  step = (max_value - min_value) / float(count)
  return [
    (min_value + step * index, min_value + step * (index + 1))
    for index in range(count)
  ]


def build_cross_region_held_component_segments_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  internal_prior_report: dict[str, Any],
) -> dict[str, Any]:
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  priors_by_name = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  rows: list[dict[str, Any]] = []

  engine_prior = priors_by_name.get("engine_core")
  if engine_prior is not None:
    engine_bounds = engine_prior["constrained_geometry"]["bounds"]
    engine_intervals = _split_interval_evenly(
      engine_bounds["min"][0],
      engine_bounds["max"][0],
      3,
    )
    engine_specs = [
      (
        "engine_core_afterburner_segment",
        "aft_afterburner_and_nozzle_overlap_proxy",
        ["aft_fuselage_engine", "engine_nozzle"],
      ),
      (
        "engine_core_hot_section_segment",
        "main_core_hot_section_proxy",
        ["aft_fuselage_engine"],
      ),
      (
        "engine_core_forward_compressor_segment",
        "forward_compressor_proxy",
        ["aft_fuselage_engine"],
      ),
    ]
    for index, ((min_x, max_x), spec) in enumerate(
      zip(engine_intervals, engine_specs)
    ):
      segment_id, segment_role, owner_region_ids = spec
      rows.append(
        _axis_interval_segment(
          parent_prior=engine_prior,
          segment_index=index,
          segment_id=segment_id,
          segment_role=segment_role,
          owner_region_ids=owner_region_ids,
          axis_name="x",
          min_value=min_x,
          max_value=max_x,
          source_basis=(
            "public_f110_length_split_into_review_segments_preserving_total_span"
          ),
        )
      )

  wing_spar_prior = priors_by_name.get("wing_spar_center")
  if wing_spar_prior is not None:
    spar_bounds = wing_spar_prior["constrained_geometry"]["bounds"]
    spar_min_y = spar_bounds["min"][1]
    spar_max_y = spar_bounds["max"][1]
    center_bounds = proxies_by_region["center_fuselage"]["source_region_bounds"]
    left_root_bounds = proxies_by_region["left_wing_root"]["source_region_bounds"]
    right_root_bounds = proxies_by_region["right_wing_root"]["source_region_bounds"]
    wing_segments = [
      (
        "wing_spar_center_left_inner_wing_segment",
        "left_inner_wing_spar_proxy",
        ["left_wing"],
        max(spar_min_y, proxies_by_region["left_wing"]["source_region_bounds"]["min"][1]),
        left_root_bounds["min"][1],
      ),
      (
        "wing_spar_center_left_root_segment",
        "left_wing_root_spar_proxy",
        ["left_wing_root"],
        left_root_bounds["min"][1],
        center_bounds["min"][1],
      ),
      (
        "wing_spar_center_carrythrough_segment",
        "center_fuselage_carrythrough_box_proxy",
        ["center_fuselage"],
        center_bounds["min"][1],
        center_bounds["max"][1],
      ),
      (
        "wing_spar_center_right_root_segment",
        "right_wing_root_spar_proxy",
        ["right_wing_root"],
        center_bounds["max"][1],
        right_root_bounds["max"][1],
      ),
      (
        "wing_spar_center_right_inner_wing_segment",
        "right_inner_wing_spar_proxy",
        ["right_wing"],
        right_root_bounds["max"][1],
        min(spar_max_y, proxies_by_region["right_wing"]["source_region_bounds"]["max"][1]),
      ),
    ]
    for index, (
      segment_id,
      segment_role,
      owner_region_ids,
      min_y,
      max_y,
    ) in enumerate(wing_segments):
      rows.append(
        _axis_interval_segment(
          parent_prior=wing_spar_prior,
          segment_index=index,
          segment_id=segment_id,
          segment_role=segment_role,
          owner_region_ids=owner_region_ids,
          axis_name="y",
          min_value=min_y,
          max_value=max_y,
          source_basis=(
            "wing_root_and_center_fuselage_mesh_bounds_partition_existing_spar_span"
          ),
        )
      )

  return {
    "schema_version": CROSS_REGION_HELD_SEGMENT_SCHEMA_VERSION,
    "status": "cross_region_held_component_segments_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "held_parent_component_count": len(
        sorted({row["parent_component_name"] for row in rows})
      ),
      "held_segment_count": len(rows),
      "engine_core_segment_count": sum(
        1 for row in rows if row["parent_component_name"] == "engine_core"
      ),
      "wing_spar_center_segment_count": sum(
        1 for row in rows if row["parent_component_name"] == "wing_spar_center"
      ),
      "outside_parent_prior_segment_count": sum(
        1 for row in rows if not row["inside_parent_prior_bounds"]
      ),
      "outside_whole_airframe_segment_count": sum(
        1 for row in rows if not row["inside_whole_airframe_bounds"]
      ),
      "shape_promotion_segment_count": sum(
        1
        for row in rows
        if row["shape_promotion_status"] in PROMOTED_SHAPE_STATUSES
      ),
      "shape_promotion_status_counts": {
        status: sum(1 for row in rows if row["shape_promotion_status"] == status)
        for status in sorted({row["shape_promotion_status"] for row in rows})
      },
      "runtime_active_segment_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review whether the engine_core split should become separate compressor, hot-section, and afterburner receivers before runtime activation.",
      },
      {
        "priority": "high",
        "question": "Review whether the wing_spar_center split should become center carry-through, wing-root, and inner-wing spar receivers.",
      },
      {
        "priority": "high",
        "question": "Keep these segments held; they are a visualization and ownership split candidate, not accepted runtime damage components.",
      },
    ],
    "authority_boundary": {
      **internal_prior_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "cross_region_receiver_ownership_accepted": False,
      "held_component_split_candidate": True,
    },
  }
