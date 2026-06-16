"""Whole-airframe projected contour containment diagnostics."""

from __future__ import annotations

from typing import Any

from tools.geometry.airframe_review import contours
from tools.geometry.airframe_review.constants import (
  DEFAULT_GENERATED_ON,
  SILHOUETTE_CONTAINMENT_TOLERANCE_M,
  WHOLE_AIRFRAME_CONTOUR_SCHEMA_VERSION,
)
from tools.geometry.airframe_review.primitives import _round


def build_whole_airframe_contour_containment_report(
  fine_proxy: dict[str, Any],
  airframe_constraint_report: dict[str, Any],
  *,
  tolerance_m: float = SILHOUETTE_CONTAINMENT_TOLERANCE_M,
) -> dict[str, Any]:
  """Whole-airframe projected mesh contour containment report.

  Promotes the silhouette-containment facts already computed by
  ``build_airframe_constraint_correction_candidate_report`` into a standalone
  review surface that records the contour method (projected glTF triangle
  union over the full audit mesh), the per-view contour geometry, the
  tolerance, and the per-item outside distances. This report is a diagnostic
  overlay: it does not change runtime behavior.

  ``fine_proxy`` supplies cached mesh triangle records used to rebuild the
  projected mesh contours for the per-view metadata block. Cached vertices are
  accepted as a lower-fidelity alpha-shape source; missing caches fail fast.
  """
  sim_triangle_records = fine_proxy.get("_sim_triangle_records", [])
  sim_vertex_records = fine_proxy.get("_sim_vertex_records", [])
  if sim_triangle_records:
    airframe_contours = contours.projected_mesh_triangle_union_contours(
      sim_triangle_records
    )
    contour_method = "projected_mesh_triangle_union"
  elif sim_vertex_records:
    airframe_contours = contours.whole_airframe_alpha_contours(sim_vertex_records)
    contour_method = "alpha_shape"
  else:
    raise ValueError(
      "fine_proxy must include glTF contour caches; build it with manifest and audit scene paths"
    )
  rows: list[dict[str, Any]] = []
  excluded_review_only_split_segment_count = 0
  for row in airframe_constraint_report["rows"]:
    if row["record_type"] == "held_split_segment":
      excluded_review_only_split_segment_count += 1
      continue
    silhouette = row["current_silhouette"]
    max_outside = float(silhouette.get("max_outside_distance_m", 0.0))
    exceeds = max_outside > tolerance_m
    view_rows: list[dict[str, Any]] = []
    for view, view_diag in silhouette["views"].items():
      view_max = float(view_diag.get("max_outside_distance_m", 0.0))
      view_rows.append(
        {
          "view": view,
          "outside_sample_count": view_diag["outside_sample_count"],
          "max_outside_distance_m": view_diag["max_outside_distance_m"],
          "exceeds_tolerance": view_max > tolerance_m,
        }
      )
    rows.append(
      {
        "item_id": row["item_id"],
        "record_type": row["record_type"],
        "component_name": row["component_name"],
        "parent_component_name": row["parent_component_name"],
        "system": row["system"],
        "prior_shape": row["prior_shape"],
        "prior_axis": row["prior_axis"],
        "nominal_dimensions_m": row["nominal_dimensions_m"],
        "owner_region_ids": row["owner_region_ids"],
        "outside_sample_count": silhouette["outside_sample_count"],
        "outside_view_count": silhouette["outside_view_count"],
        "outside_views": silhouette["outside_views"],
        "max_outside_distance_m": silhouette["max_outside_distance_m"],
        "exceeds_tolerance": exceeds,
        "views": view_rows,
        "constraint_triage_status": row["triage_status"],
        "current_geometry": row["current_geometry"],
      }
    )
  rows.sort(
    key=lambda item: (
      not item["exceeds_tolerance"],
      -item["max_outside_distance_m"],
      item["item_id"],
    )
  )
  max_outside_overall = max(
    (row["max_outside_distance_m"] for row in rows),
    default=0.0,
  )
  exceeders = [row for row in rows if row["exceeds_tolerance"]]
  return {
    "schema_version": WHOLE_AIRFRAME_CONTOUR_SCHEMA_VERSION,
    "status": "whole_airframe_contour_containment_generated_review_only",
    "generated_on": fine_proxy.get("generated_on", DEFAULT_GENERATED_ON),
    "asset_ref": fine_proxy.get("asset_ref", {}),
    "coordinate_frame": fine_proxy.get("coordinate_frame", {}),
    "source_airframe_constraint_schema_version": airframe_constraint_report[
      "schema_version"
    ],
    "contour_method": contour_method,
    "tolerance_m": _round(tolerance_m),
    "tolerance_basis": (
      "engineering_review_margin_for_mesh_and_proxy_quantization_not_physical_clearance"
    ),
    "summary": {
      "item_count": len(rows),
      "excluded_review_only_split_segment_count": (
        excluded_review_only_split_segment_count
      ),
      "exceeds_tolerance_item_count": len(exceeders),
      "inside_contour_item_count": len(rows) - len(exceeders),
      "max_outside_distance_m": _round(max_outside_overall),
      "contours": {
        view: {
          "status": contour["status"],
          "alpha": contour.get("alpha", 0.0),
          "alpha_radius_m": contour.get("alpha_radius_m", 0.0),
          "source_vertex_count": contour.get("source_vertex_count", 0),
          "source_triangle_count": contour.get("source_triangle_count", 0),
          "polygon_count": contour.get("polygon_count", 1),
          "contour_point_count": contour["contour_point_count"],
        }
        for view, contour in airframe_contours.items()
      },
      "exceeding_item_ids": [row["item_id"] for row in exceeders],
    },
    "contours": {
      view: {
        "points_m": contour["points_m"],
        "polygons_m": contour.get("polygons_m", [contour["points_m"]]),
      }
      for view, contour in airframe_contours.items()
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": (
          "Review every item whose max_outside_distance_m exceeds the "
          "tolerance; the projected mesh contour is stricter than the legacy "
          "per-region hull union and follows the audit triangle silhouette."
        ),
      },
      {
        "priority": "medium",
        "question": (
          "Confirm the projected mesh silhouette still reflects the intended "
          "audit asset orientation before treating an outside result as a true "
          "protrusion rather than a mesh/source artifact."
        ),
      },
    ],
    "authority_boundary": {
      "projected_mesh_contour_diagnostic_only": True,
      "not_runtime_collision_mesh": True,
      "not_true_f16_engineering_geometry": True,
      "review_only_split_segments_excluded_from_final_surface": True,
      "tolerance_is_engineering_review_margin_not_physical_clearance": True,
      "runtime_active_component": False,
      "runtime_damage_model": False,
      "real_weapon_pk_authority": False,
    },
  }
