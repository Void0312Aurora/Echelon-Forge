#!/usr/bin/env python3
"""Generate review-only airframe geometry manifests from glTF audit assets.

The manifest produced here is evidence for human geometry review. It is not a
runtime collision mesh, not a vulnerability calibration, and not an authority
source for real internal aircraft structure.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


if __package__ in (None, ""):
  repo_root = Path(__file__).resolve().parents[2]
  if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


from tools.geometry.airframe_review import (
  airframe_constraint,
  component_binding,
  contour_containment,
  filesystem,
  fine_proxy as fine_proxy_builder,
  gltf_io,
  held_segments,
  internal_prior,
  geometry_mapping,
  manifest_builder,
  parent_child_layout,
  report_writers,
  review_packet,
  review_views,
  subcomponent_shape,
  surface_semantic,
  runtime_activation,
)
from tools.geometry.airframe_review.constants import (
  DEFAULT_AIRCRAFT,
  DEFAULT_AUDIT_SCENE,
  DEFAULT_GENERATED_ON,
  DEFAULT_INTAKE_METADATA,
  DEFAULT_OUTPUT_DIR,
  DEFAULT_REGISTRY,
  DEFAULT_VISUAL_GLB,
  REPO_ROOT,
  RETIRED_CURRENT_PACKET_VISUAL_DIRS,
  RETIRED_CURRENT_PACKET_VISUAL_FILES,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Generate a review-only airframe geometry manifest from a glTF audit asset."
  )
  parser.add_argument("--aircraft", type=Path, default=DEFAULT_AIRCRAFT)
  parser.add_argument("--asset", type=Path, default=DEFAULT_AUDIT_SCENE)
  parser.add_argument("--visual-glb", type=Path, default=DEFAULT_VISUAL_GLB)
  parser.add_argument("--intake-metadata", type=Path, default=DEFAULT_INTAKE_METADATA)
  parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
  parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--generated-on", default=DEFAULT_GENERATED_ON)
  parser.add_argument(
    "--stdout-only",
    action="store_true",
    help="Print manifest JSON to stdout instead of writing manifest.json.",
  )
  return parser.parse_args(argv)


def cleanup_retired_current_packet_visual_artifacts(output_dir: Path) -> list[Path]:
  """Remove visual artifacts that are no longer part of the current result.

  JSON/CSV machine evidence is retained, but current packet visuals are
  deliberately contracted to the whole-airframe projected mesh contour
  dashboard and its three SVG views.
  """
  removed: list[Path] = []
  for dirname in RETIRED_CURRENT_PACKET_VISUAL_DIRS:
    target = output_dir / dirname
    if target.exists():
      shutil.rmtree(target)
      removed.append(target)
  for filename in RETIRED_CURRENT_PACKET_VISUAL_FILES:
    target = output_dir / filename
    if target.exists():
      target.unlink()
      removed.append(target)
  return removed


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(sys.argv[1:] if argv is None else argv)
  manifest = manifest_builder.build_airframe_geometry_manifest(
    aircraft_path=args.aircraft,
    audit_scene_path=args.asset,
    visual_glb_path=args.visual_glb,
    intake_metadata_path=args.intake_metadata,
    registry_path=args.registry,
    generated_on=args.generated_on,
  )
  if args.stdout_only:
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    return 0

  output_path = report_writers.write_manifest(manifest, args.out)
  mapping = geometry_mapping.build_geometry_mapping_candidate(manifest)
  mapping_path = report_writers.write_mapping_candidate(mapping, args.out)
  aircraft = gltf_io.load_json(args.aircraft)
  component_report = component_binding.build_component_binding_report(aircraft, mapping)
  component_json_path, component_csv_path = report_writers.write_component_binding_report(
    component_report, args.out
  )
  diagnostics = component_binding.build_review_point_diagnostics(mapping, component_report)
  diagnostics_json_path, diagnostics_csv_path = report_writers.write_review_point_diagnostics(
    diagnostics, args.out
  )
  fine_proxy = fine_proxy_builder.build_fine_geometry_proxy_candidate(
    mapping,
    diagnostics,
    manifest=manifest,
    audit_scene_path=args.asset,
  )
  fine_proxy_path = report_writers.write_fine_geometry_proxy_candidate(fine_proxy, args.out)
  surface_report = surface_semantic.build_surface_component_candidate_report(
    mapping,
    fine_proxy,
    component_report,
  )
  surface_json_path, surface_csv_path = report_writers.write_surface_component_candidate_report(
    surface_report,
    args.out,
  )
  semantic_report = surface_semantic.build_semantic_damage_geometry_candidate(
    mapping,
    fine_proxy,
    surface_report,
  )
  semantic_json_path, semantic_csv_path = report_writers.write_semantic_damage_geometry_candidate(
    semantic_report,
    args.out,
  )
  internal_prior_report = internal_prior.build_internal_component_prior_candidate(
    mapping,
    fine_proxy,
    component_report,
    surface_report,
  )
  internal_prior_json_path, internal_prior_csv_path = (
    report_writers.write_internal_component_prior_candidate(
      internal_prior_report,
      args.out,
    )
  )
  held_segment_report = held_segments.build_cross_region_held_component_segments_report(
    mapping,
    fine_proxy,
    internal_prior_report,
  )
  held_segment_json_path, held_segment_csv_path = (
    report_writers.write_cross_region_held_component_segments_report(
      held_segment_report,
      args.out,
    )
  )
  airframe_constraint_report = airframe_constraint.build_airframe_constraint_correction_candidate_report(
    mapping,
    fine_proxy,
    internal_prior_report,
    held_segment_report,
  )
  airframe_constraint_json_path, airframe_constraint_csv_path = (
    report_writers.write_airframe_constraint_correction_candidate_report(
      airframe_constraint_report,
      args.out,
    )
  )
  whole_airframe_contour_report = (
    contour_containment.build_whole_airframe_contour_containment_report(
      fine_proxy,
      airframe_constraint_report,
    )
  )
  whole_airframe_contour_json_path, whole_airframe_contour_csv_path = (
    report_writers.write_whole_airframe_contour_containment_report(
      whole_airframe_contour_report,
      args.out,
    )
  )
  whole_airframe_contour_svg_paths = review_views.write_whole_airframe_contour_svg_views(
    whole_airframe_contour_report,
    args.out,
  )
  whole_airframe_contour_dashboard_path = (
    review_views.write_whole_airframe_contour_dashboard(
      whole_airframe_contour_report,
      args.out,
    )
  )
  ownership_split_report = runtime_activation.build_cross_region_ownership_split_candidate_report(
    mapping,
    internal_prior_report,
    held_segment_report,
    airframe_constraint_report,
  )
  ownership_split_json_path, ownership_split_csv_path = (
    report_writers.write_cross_region_ownership_split_candidate_report(
      ownership_split_report,
      args.out,
    )
  )
  runtime_activation_report = (
    runtime_activation.build_target_geometry_runtime_activation_candidate_report(
      mapping,
      ownership_split_report,
      aircraft=aircraft,
    )
  )
  runtime_activation_json_path, runtime_activation_csv_path = (
    report_writers.write_target_geometry_runtime_activation_candidate_report(
      runtime_activation_report,
      args.out,
    )
  )
  runtime_behavior_report = (
    runtime_activation.build_target_geometry_runtime_behavior_regression_report(
      aircraft,
      runtime_activation_report,
    )
  )
  runtime_behavior_json_path, runtime_behavior_csv_path = (
    report_writers.write_target_geometry_runtime_behavior_regression_report(
      runtime_behavior_report,
      args.out,
    )
  )
  training_proxy_aircraft, _training_proxy_operations = (
    runtime_activation.build_target_geometry_training_proxy_unit_candidate(
      aircraft,
      runtime_activation_report,
    )
  )
  training_proxy_report = runtime_activation.build_target_geometry_training_proxy_database_report(
    aircraft,
    runtime_activation_report,
    runtime_behavior_report,
    proxy_database_dir=args.out / "target_geometry_training_proxy_database_20260613",
  )
  (
    training_proxy_report,
    training_proxy_json_path,
    training_proxy_database_dir,
    training_proxy_unit_path,
  ) = report_writers.write_target_geometry_training_proxy_database_report(
    training_proxy_report,
    training_proxy_aircraft,
    args.out,
  )
  shape_placement_report = subcomponent_shape.build_subcomponent_shape_placement_candidate_report(
    mapping,
    fine_proxy,
    airframe_constraint_report,
  )
  shape_placement_json_path, shape_placement_csv_path = (
    report_writers.write_subcomponent_shape_placement_candidate_report(
      shape_placement_report,
      args.out,
    )
  )
  parent_child_layout_report = parent_child_layout.build_semantic_parent_child_layout_candidate(
    mapping,
    semantic_report,
    internal_prior_report,
    held_segment_report,
  )
  parent_child_layout_json_path, parent_child_layout_csv_path = (
    report_writers.write_semantic_parent_child_layout_candidate(
      parent_child_layout_report,
      args.out,
    )
  )
  retired_visual_artifact_paths = cleanup_retired_current_packet_visual_artifacts(
    args.out
  )
  scene_path = review_packet.write_review_packet(
    manifest=manifest,
    mapping=mapping,
    component_report=component_report,
    diagnostics=diagnostics,
    fine_proxy=fine_proxy,
    surface_report=surface_report,
    semantic_report=semantic_report,
    internal_prior_report=internal_prior_report,
    held_segment_report=held_segment_report,
    airframe_constraint_report=airframe_constraint_report,
    whole_airframe_contour_report=whole_airframe_contour_report,
    ownership_split_report=ownership_split_report,
    runtime_activation_report=runtime_activation_report,
    runtime_behavior_report=runtime_behavior_report,
    training_proxy_report=training_proxy_report,
    shape_placement_report=shape_placement_report,
    parent_child_layout_report=parent_child_layout_report,
    output_dir=args.out,
  )
  print(
    json.dumps(
      {
        "status": manifest["status"],
        "schema_version": manifest["schema_version"],
        "output": filesystem.display_path(output_path, REPO_ROOT),
        "mapping_output": filesystem.display_path(mapping_path, REPO_ROOT),
        "component_binding_json": filesystem.display_path(component_json_path, REPO_ROOT),
        "component_binding_csv": filesystem.display_path(component_csv_path, REPO_ROOT),
        "review_point_diagnostics_json": filesystem.display_path(
          diagnostics_json_path, REPO_ROOT
        ),
        "review_point_diagnostics_csv": filesystem.display_path(
          diagnostics_csv_path, REPO_ROOT
        ),
        "fine_proxy_json": filesystem.display_path(fine_proxy_path, REPO_ROOT),
        "surface_component_json": filesystem.display_path(surface_json_path, REPO_ROOT),
        "surface_component_csv": filesystem.display_path(surface_csv_path, REPO_ROOT),
        "semantic_damage_geometry_json": filesystem.display_path(
          semantic_json_path,
          REPO_ROOT,
        ),
        "semantic_damage_geometry_csv": filesystem.display_path(
          semantic_csv_path,
          REPO_ROOT,
        ),
        "internal_component_prior_json": filesystem.display_path(
          internal_prior_json_path,
          REPO_ROOT,
        ),
        "internal_component_prior_csv": filesystem.display_path(
          internal_prior_csv_path,
          REPO_ROOT,
        ),
        "cross_region_held_segments_json": filesystem.display_path(
          held_segment_json_path,
          REPO_ROOT,
        ),
        "cross_region_held_segments_csv": filesystem.display_path(
          held_segment_csv_path,
          REPO_ROOT,
        ),
        "airframe_constraint_correction_json": filesystem.display_path(
          airframe_constraint_json_path,
          REPO_ROOT,
        ),
        "airframe_constraint_correction_csv": filesystem.display_path(
          airframe_constraint_csv_path,
          REPO_ROOT,
        ),
        "cross_region_ownership_split_json": filesystem.display_path(
          ownership_split_json_path,
          REPO_ROOT,
        ),
        "cross_region_ownership_split_csv": filesystem.display_path(
          ownership_split_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_activation_json": filesystem.display_path(
          runtime_activation_json_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_activation_csv": filesystem.display_path(
          runtime_activation_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_behavior_json": filesystem.display_path(
          runtime_behavior_json_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_behavior_csv": filesystem.display_path(
          runtime_behavior_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_json": filesystem.display_path(
          training_proxy_json_path,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_database": filesystem.display_path(
          training_proxy_database_dir,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_f16c_unit": filesystem.display_path(
          training_proxy_unit_path,
          REPO_ROOT,
        ),
        "subcomponent_shape_placement_json": filesystem.display_path(
          shape_placement_json_path,
          REPO_ROOT,
        ),
        "subcomponent_shape_placement_csv": filesystem.display_path(
          shape_placement_csv_path,
          REPO_ROOT,
        ),
        "semantic_parent_child_layout_json": filesystem.display_path(
          parent_child_layout_json_path,
          REPO_ROOT,
        ),
        "semantic_parent_child_layout_csv": filesystem.display_path(
          parent_child_layout_csv_path,
          REPO_ROOT,
        ),
        "scene_html": filesystem.display_path(scene_path, REPO_ROOT),
        "current_visual_result": filesystem.display_path(
          whole_airframe_contour_dashboard_path,
          REPO_ROOT,
        ),
        "retired_visual_artifact_count": len(retired_visual_artifact_paths),
        "component_count": component_report["summary"]["component_count"],
        "component_needs_review_count": component_report["summary"][
          "needs_review_count"
        ],
        "fine_proxy_count": fine_proxy["summary"]["proxy_count"],
        "mesh_derived_silhouette_count": fine_proxy["summary"][
          "mesh_derived_silhouette_count"
        ],
        "inflated_fallback_count": fine_proxy["summary"]["inflated_fallback_count"],
        "fine_proxy_support_volume_ratio": fine_proxy["summary"][
          "total_proxy_support_volume_ratio"
        ],
        "surface_component_count": surface_report["summary"][
          "surface_component_count"
        ],
        "surface_component_needs_review_count": surface_report["summary"][
          "needs_review_count"
        ],
        "semantic_damage_volume_count": semantic_report["summary"][
          "semantic_volume_component_count"
        ],
        "semantic_damage_cross_region_handoff_held_count": semantic_report[
          "summary"
        ]["cross_region_handoff_held_count"],
        "internal_component_prior_count": internal_prior_report["summary"][
          "internal_component_prior_count"
        ],
        "internal_component_prior_post_constraint_outside_count": (
          internal_prior_report["summary"]["post_constraint_outside_count"]
        ),
        "internal_component_prior_cross_region_held_count": (
          internal_prior_report["summary"]["cross_region_held_prior_count"]
        ),
        "internal_component_prior_shape_promotion_count": (
          internal_prior_report["summary"]["shape_promotion_count"]
        ),
        "cross_region_held_segment_count": held_segment_report["summary"][
          "held_segment_count"
        ],
        "cross_region_held_segment_outside_airframe_count": held_segment_report[
          "summary"
        ]["outside_whole_airframe_segment_count"],
        "cross_region_held_segment_shape_promotion_count": held_segment_report[
          "summary"
        ]["shape_promotion_segment_count"],
        "airframe_constraint_item_count": airframe_constraint_report["summary"][
          "item_count"
        ],
        "airframe_constraint_silhouette_exposure_item_count": (
          airframe_constraint_report["summary"]["silhouette_exposure_item_count"]
        ),
        "airframe_constraint_center_shift_resolves_item_count": (
          airframe_constraint_report["summary"][
            "center_shift_resolves_item_count"
          ]
        ),
        "airframe_constraint_size_or_shape_review_item_count": (
          airframe_constraint_report["summary"][
            "size_or_shape_review_item_count"
          ]
        ),
        "whole_airframe_contour_method": whole_airframe_contour_report[
          "contour_method"
        ],
        "whole_airframe_contour_tolerance_m": whole_airframe_contour_report[
          "tolerance_m"
        ],
        "whole_airframe_contour_item_count": whole_airframe_contour_report[
          "summary"
        ]["item_count"],
        "whole_airframe_contour_excluded_review_only_split_segment_count": (
          whole_airframe_contour_report["summary"][
            "excluded_review_only_split_segment_count"
          ]
        ),
        "whole_airframe_contour_exceeds_tolerance_item_count": (
          whole_airframe_contour_report["summary"][
            "exceeds_tolerance_item_count"
          ]
        ),
        "whole_airframe_contour_max_outside_distance_m": (
          whole_airframe_contour_report["summary"]["max_outside_distance_m"]
        ),
        "whole_airframe_contour_exceeding_item_ids": whole_airframe_contour_report[
          "summary"
        ]["exceeding_item_ids"],
        "whole_airframe_contour_contours": whole_airframe_contour_report[
          "summary"
        ]["contours"],
        "whole_airframe_contour_json": filesystem.display_path(
          whole_airframe_contour_json_path, REPO_ROOT
        ),
        "whole_airframe_contour_csv": filesystem.display_path(
          whole_airframe_contour_csv_path, REPO_ROOT
        ),
        "whole_airframe_contour_dashboard": filesystem.display_path(
          whole_airframe_contour_dashboard_path, REPO_ROOT
        ),
        "whole_airframe_contour_top_svg": filesystem.display_path(
          whole_airframe_contour_svg_paths[0], REPO_ROOT
        ),
        "whole_airframe_contour_side_svg": filesystem.display_path(
          whole_airframe_contour_svg_paths[1], REPO_ROOT
        ),
        "whole_airframe_contour_front_svg": filesystem.display_path(
          whole_airframe_contour_svg_paths[2], REPO_ROOT
        ),
        "cross_region_ownership_parent_decision_count": (
          ownership_split_report["summary"]["parent_decision_count"]
        ),
        "cross_region_ownership_split_receiver_candidate_count": (
          ownership_split_report["summary"]["split_receiver_candidate_count"]
        ),
        "cross_region_ownership_zero_silhouette_exposure_split_candidate_count": (
          ownership_split_report["summary"][
            "zero_silhouette_exposure_split_candidate_count"
          ]
        ),
        "cross_region_ownership_runtime_active_split_component_count": (
          ownership_split_report["summary"]["runtime_active_split_component_count"]
        ),
        "target_geometry_runtime_activation_candidate_count": (
          runtime_activation_report["summary"]["candidate_component_count"]
        ),
        "target_geometry_runtime_activation_parse_ready_count": (
          runtime_activation_report["summary"][
            "runtime_schema_parse_ready_component_count"
          ]
        ),
        "target_geometry_runtime_activation_patch_component_count": (
          runtime_activation_report["summary"]["unit_database_patch_component_count"]
        ),
        "target_geometry_runtime_activation_parent_retirement_candidate_count": (
          runtime_activation_report["summary"][
            "parent_receiver_retirement_candidate_count"
          ]
        ),
        "target_geometry_runtime_activation_runtime_active_count": (
          runtime_activation_report["summary"]["runtime_active_component_count"]
        ),
        "target_geometry_runtime_behavior_base_component_count": (
          runtime_behavior_report["summary"]["base_component_count"]
        ),
        "target_geometry_runtime_behavior_projected_component_count": (
          runtime_behavior_report["summary"]["projected_component_count"]
        ),
        "target_geometry_runtime_behavior_retired_parent_component_count": (
          runtime_behavior_report["summary"]["retired_parent_component_count"]
        ),
        "target_geometry_runtime_behavior_split_component_added_count": (
          runtime_behavior_report["summary"]["split_component_added_count"]
        ),
        "target_geometry_runtime_behavior_duplicate_component_name_count": (
          runtime_behavior_report["summary"]["duplicate_component_name_count"]
        ),
        "target_geometry_runtime_behavior_regression_pass": (
          runtime_behavior_report["summary"]["behavior_regression_pass"]
        ),
        "target_geometry_training_proxy_default_database_component_count": (
          training_proxy_report["summary"]["default_database_component_count"]
        ),
        "target_geometry_training_proxy_database_component_count": (
          training_proxy_report["summary"]["proxy_database_component_count"]
        ),
        "target_geometry_training_proxy_split_receiver_component_count": (
          training_proxy_report["summary"]["split_receiver_component_count"]
        ),
        "target_geometry_training_proxy_database_materialized": (
          training_proxy_report["summary"]["proxy_database_materialized"]
        ),
        "subcomponent_shape_placement_candidate_count": (
          shape_placement_report["summary"]["shape_placement_candidate_count"]
        ),
        "subcomponent_shape_placement_resolves_count": (
          shape_placement_report["summary"]["candidate_resolves_exposure_count"]
        ),
        "subcomponent_shape_placement_unresolved_count": (
          shape_placement_report["summary"]["candidate_unresolved_exposure_count"]
        ),
        "subcomponent_shape_placement_outside_sample_reduction": (
          shape_placement_report["summary"][
            "candidate_total_outside_sample_reduction"
          ]
        ),
        "subcomponent_centerline_resolves_count": (
          shape_placement_report["summary"][
            "centerline_candidate_resolves_exposure_count"
          ]
        ),
        "subcomponent_centerline_unresolved_count": (
          shape_placement_report["summary"][
            "centerline_candidate_unresolved_exposure_count"
          ]
        ),
        "subcomponent_centerline_outside_sample_count": (
          shape_placement_report["summary"][
            "centerline_candidate_total_outside_sample_count"
          ]
        ),
        "subcomponent_centerline_incremental_reduction": (
          shape_placement_report["summary"][
            "centerline_candidate_incremental_outside_sample_reduction"
          ]
        ),
        "subcomponent_latest_resolves_count": (
          shape_placement_report["summary"][
            "latest_candidate_resolves_exposure_count"
          ]
        ),
        "subcomponent_latest_unresolved_count": (
          shape_placement_report["summary"][
            "latest_candidate_unresolved_exposure_count"
          ]
        ),
        "subcomponent_latest_outside_sample_count": (
          shape_placement_report["summary"][
            "latest_candidate_total_outside_sample_count"
          ]
        ),
        "subcomponent_latest_incremental_reduction": (
          shape_placement_report["summary"][
            "latest_candidate_incremental_outside_sample_reduction"
          ]
        ),
        "semantic_parent_child_layout_parent_count": (
          parent_child_layout_report["summary"]["parent_semantic_component_count"]
        ),
        "semantic_parent_child_layout_receiver_count": (
          parent_child_layout_report["summary"]["bound_receiver_component_count"]
        ),
        "semantic_parent_child_layout_extra_receiver_slot_count": (
          parent_child_layout_report["summary"]["extra_receiver_slot_count"]
        ),
        "semantic_parent_child_layout_cross_region_held_receiver_count": (
          parent_child_layout_report["summary"]["cross_region_held_receiver_count"]
        ),
        "semantic_parent_child_layout_cross_region_held_segment_count": (
          parent_child_layout_report["summary"]["cross_region_held_segment_count"]
        ),
        "semantic_parent_child_layout_cross_region_held_segment_overlay_count": (
          parent_child_layout_report["summary"][
            "cross_region_held_segment_overlay_count"
          ]
        ),
        "review_point_count": diagnostics["summary"]["review_point_count"],
        "inside_outer_region_point_count": diagnostics["summary"][
          "inside_outer_region_point_count"
        ],
        "triangle_count": manifest["gltf_summary"]["triangle_count"],
        "position_accessor_vertex_count": manifest["gltf_summary"][
          "position_accessor_vertex_count"
        ],
      },
      indent=2,
      sort_keys=True,
    )
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
