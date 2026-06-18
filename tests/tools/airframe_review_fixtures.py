from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tools.geometry.airframe_review import (
  airframe_constraint,
  constants,
  component_binding,
  contour_containment,
  fine_proxy,
  geometry_mapping,
  gltf_io,
  held_segments,
  internal_prior,
  manifest_builder,
  parent_child_layout,
  runtime_activation,
  subcomponent_shape,
  surface_semantic,
)


def require_airframe_geometry_extra() -> None:
  pytest.importorskip("scipy")
  pytest.importorskip("shapely")


def build_airframe_review_bundle(
  *,
  proxy_database_dir: Path | None = None,
) -> dict[str, Any]:
  manifest = manifest_builder.build_airframe_geometry_manifest()
  aircraft = gltf_io.load_json(constants.DEFAULT_AIRCRAFT)
  mapping = geometry_mapping.build_geometry_mapping_candidate(manifest)
  report = component_binding.build_component_binding_report(aircraft, mapping)
  diagnostics = component_binding.build_review_point_diagnostics(mapping, report)
  fine_proxy_report = fine_proxy.build_fine_geometry_proxy_candidate(
    mapping, diagnostics, manifest=manifest
  )
  surface_report = surface_semantic.build_surface_component_candidate_report(
    mapping, fine_proxy_report, report
  )
  semantic_report = surface_semantic.build_semantic_damage_geometry_candidate(
    mapping, fine_proxy_report, surface_report
  )
  internal_prior_report = (
    internal_prior.build_internal_component_prior_candidate(
      mapping, fine_proxy_report, report, surface_report
    )
  )
  held_segment_report = (
    held_segments.build_cross_region_held_component_segments_report(
      mapping, fine_proxy_report, internal_prior_report
    )
  )
  airframe_constraint_report = (
    airframe_constraint.build_airframe_constraint_correction_candidate_report(
      mapping, fine_proxy_report, internal_prior_report, held_segment_report
    )
  )
  ownership_split_report = (
    runtime_activation.build_cross_region_ownership_split_candidate_report(
      mapping,
      internal_prior_report,
      held_segment_report,
      airframe_constraint_report,
    )
  )
  runtime_activation_report = (
    runtime_activation.build_target_geometry_runtime_activation_candidate_report(
      mapping,
      ownership_split_report,
      aircraft=aircraft,
    )
  )
  runtime_behavior_report = (
    runtime_activation.build_target_geometry_runtime_behavior_regression_report(
      aircraft,
      runtime_activation_report,
    )
  )
  training_proxy_aircraft, training_proxy_operations = (
    runtime_activation.build_target_geometry_training_proxy_unit_candidate(
      aircraft,
      runtime_activation_report,
    )
  )
  if proxy_database_dir is None:
    proxy_database_dir = (
      constants.DEFAULT_OUTPUT_DIR
      / "target_geometry_training_proxy_database_20260613"
    )
  training_proxy_report = (
    runtime_activation.build_target_geometry_training_proxy_database_report(
      aircraft,
      runtime_activation_report,
      runtime_behavior_report,
      proxy_database_dir=proxy_database_dir,
    )
  )
  shape_placement_report = (
    subcomponent_shape.build_subcomponent_shape_placement_candidate_report(
      mapping, fine_proxy_report, airframe_constraint_report
    )
  )
  parent_child_layout_report = (
    parent_child_layout.build_semantic_parent_child_layout_candidate(
      mapping, semantic_report, internal_prior_report, held_segment_report
    )
  )
  contour_report = (
    contour_containment.build_whole_airframe_contour_containment_report(
      fine_proxy_report,
      airframe_constraint_report,
    )
  )
  return {
    "manifest": manifest,
    "aircraft": aircraft,
    "mapping": mapping,
    "component_binding_report": report,
    "diagnostics": diagnostics,
    "fine_proxy": fine_proxy_report,
    "surface_report": surface_report,
    "semantic_report": semantic_report,
    "internal_prior_report": internal_prior_report,
    "held_segment_report": held_segment_report,
    "airframe_constraint_report": airframe_constraint_report,
    "ownership_split_report": ownership_split_report,
    "runtime_activation_report": runtime_activation_report,
    "runtime_behavior_report": runtime_behavior_report,
    "training_proxy_aircraft": training_proxy_aircraft,
    "training_proxy_operations": training_proxy_operations,
    "training_proxy_report": training_proxy_report,
    "shape_placement_report": shape_placement_report,
    "parent_child_layout_report": parent_child_layout_report,
    "contour_report": contour_report,
  }
