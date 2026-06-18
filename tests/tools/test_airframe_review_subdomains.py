from __future__ import annotations

from pathlib import Path

import pytest

from tools.geometry.airframe_review import asset_projection
from tools.geometry.airframe_review import constants
from tools.geometry.airframe_review import gltf_io
from tools.geometry.airframe_review import optional_deps
from tools.geometry.airframe_review import projection_geometry
from tools.geometry.airframe_review import review_packet
from tools.geometry.airframe_review import review_views


def test_airframe_review_constants_are_subdomain_authority() -> None:
  assert constants.REPO_ROOT == Path(__file__).resolve().parents[2]
  assert constants.DEFAULT_AIRCRAFT.is_file()
  assert constants.DEFAULT_AUDIT_SCENE.is_file()
  assert constants.DEFAULT_OUTPUT_DIR.parts[-3:] == (
    "missile_lethality_target_geometry",
    "review_packets",
    "f16c_20260611",
  )
  assert constants.SURFACE_COMPONENT_RULES
  assert constants.INTERNAL_COMPONENT_PRIOR_RULES


def test_airframe_review_optional_dependency_guard_is_import_safe() -> None:
  if optional_deps.GEOMETRY_DEPS_AVAILABLE:
    optional_deps.require_geometry_deps()
    return

  with pytest.raises(RuntimeError, match="optional geometry dependency group"):
    optional_deps.require_geometry_deps()


def test_airframe_review_gltf_io_is_direct_subdomain() -> None:
  summary = gltf_io.summarize_gltf_scene(constants.DEFAULT_AUDIT_SCENE)

  assert summary["triangle_count"] == 4504
  assert summary["position_accessor_vertex_count"] == 13415
  assert summary["mesh_node_bounds"][0]["node_name"].startswith("Object_")


def test_airframe_review_asset_projection_is_direct_subdomain() -> None:
  gltf_summary = gltf_io.summarize_gltf_scene(constants.DEFAULT_AUDIT_SCENE)
  manifest = {
    "gltf_summary": gltf_summary,
    "public_dimension_check": {"registry_scale": 0.01},
  }

  records = asset_projection.extract_gltf_sim_vertex_records(
    constants.DEFAULT_AUDIT_SCENE,
    manifest,
  )

  assert len(records) == gltf_summary["position_accessor_vertex_count"]
  assert records[0]["node_name"].startswith("Object_")
  assert len(records[0]["point_m"]) == 3


def test_airframe_review_projection_geometry_axis_sampling_is_direct_subdomain() -> None:
  samples = projection_geometry.projected_shape_sample_points(
    (0.0, 0.0, 2.0, 4.0),
    axes=(0, 2),
    shape="capsule",
    axis="x",
  )

  assert len(samples) == 9
  assert samples[0] == (1.0, 2.0)


def test_airframe_review_view_writers_are_direct_subdomain(tmp_path: Path) -> None:
  contour_ring = [[-10.0, -5.0], [10.0, -5.0], [10.0, 5.0], [-10.0, 5.0]]
  contour_report = {
    "schema_version": "smoke",
    "contour_method": "projected_mesh_triangle_union",
    "tolerance_m": 0.05,
    "summary": {
      "item_count": 1,
      "exceeds_tolerance_item_count": 0,
      "max_outside_distance_m": 0.0,
      "contours": {
        view: {
          "status": "projected_mesh_triangle_union",
          "source_triangle_count": 1,
          "polygon_count": 1,
          "contour_point_count": len(contour_ring),
        }
        for view in ("top", "side", "front")
      },
    },
    "contours": {
      view: {"points_m": contour_ring, "polygons_m": [contour_ring]}
      for view in ("top", "side", "front")
    },
    "rows": [
      {
        "item_id": "smoke_receiver",
        "record_type": "prior",
        "component_name": "smoke_receiver",
        "parent_component_name": "",
        "system": "smoke",
        "prior_shape": "obb",
        "prior_axis": "x",
        "nominal_dimensions_m": [1.0, 1.0, 1.0],
        "owner_region_ids": [],
        "outside_views": [],
        "outside_sample_count": 0,
        "max_outside_distance_m": 0.0,
        "exceeds_tolerance": False,
        "current_geometry": {
          "shape": "obb",
          "axis": "x",
          "bounds": {
            "min": [-1.0, -1.0, -1.0],
            "max": [1.0, 1.0, 1.0],
            "center": [0.0, 0.0, 0.0],
            "span": [2.0, 2.0, 2.0],
          },
        },
      }
    ],
  }

  svg_paths = review_views.write_whole_airframe_contour_svg_views(
    contour_report,
    tmp_path,
  )
  dashboard = review_views.write_whole_airframe_contour_dashboard(
    contour_report,
    tmp_path,
  )
  packet = review_packet.write_review_packet(
    manifest={"source": {"uid": "smoke"}},
    mapping={"generated_on": "smoke"},
    component_report={"rows": [], "summary": {"component_count": 0}},
    diagnostics={"rows": [], "summary": {"review_point_count": 0}},
    whole_airframe_contour_report=contour_report,
    output_dir=tmp_path,
  )

  assert [path.name for path in svg_paths] == [
    "whole_airframe_contour_top.svg",
    "whole_airframe_contour_side.svg",
    "whole_airframe_contour_front.svg",
  ]
  assert dashboard.name == "whole_airframe_contour_dashboard.html"
  assert packet.name == "scene.html"
  assert packet.read_text(encoding="utf-8").startswith("<!doctype html>")
