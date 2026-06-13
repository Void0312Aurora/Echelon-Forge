#!/usr/bin/env python3
"""Generate review-only airframe geometry manifests from glTF audit assets.

The manifest produced here is evidence for human geometry review. It is not a
runtime collision mesh, not a vulnerability calibration, and not an authority
source for real internal aircraft structure.
"""

from __future__ import annotations

import argparse
import base64
import copy
import csv
import hashlib
import html
import json
import math
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "a2.target_geometry_manifest.v1"
MAPPING_SCHEMA_VERSION = "a2.target_geometry_mapping_candidate.v1"
COMPONENT_BINDING_SCHEMA_VERSION = "a2.target_geometry_component_binding_report.v1"
REVIEW_POINT_DIAGNOSTICS_SCHEMA_VERSION = (
  "a2.target_geometry_review_point_diagnostics.v1"
)
FINE_PROXY_SCHEMA_VERSION = "a2.target_geometry_fine_proxy_candidate.v1"
SURFACE_COMPONENT_SCHEMA_VERSION = (
  "a2.target_geometry_surface_component_candidate.v1"
)
SEMANTIC_DAMAGE_GEOMETRY_SCHEMA_VERSION = (
  "a2.target_geometry_semantic_damage_geometry_candidate.v1"
)
INTERNAL_COMPONENT_PRIOR_SCHEMA_VERSION = (
  "a2.target_geometry_internal_component_prior_candidate.v1"
)
SEMANTIC_PARENT_CHILD_LAYOUT_SCHEMA_VERSION = (
  "a2.target_geometry_semantic_parent_child_layout_candidate.v1"
)
CROSS_REGION_HELD_SEGMENT_SCHEMA_VERSION = (
  "a2.target_geometry_cross_region_held_component_segments.v1"
)
CROSS_REGION_OWNERSHIP_SPLIT_SCHEMA_VERSION = (
  "a2.target_geometry_cross_region_ownership_split_candidate.v1"
)
TARGET_GEOMETRY_RUNTIME_ACTIVATION_SCHEMA_VERSION = (
  "a2.target_geometry_runtime_activation_candidate.v1"
)
TARGET_GEOMETRY_RUNTIME_BEHAVIOR_SCHEMA_VERSION = (
  "a2.target_geometry_runtime_behavior_regression.v1"
)
TARGET_GEOMETRY_TRAINING_PROXY_SCHEMA_VERSION = (
  "a2.target_geometry_training_proxy_database.v1"
)
AIRFRAME_CONSTRAINT_CORRECTION_SCHEMA_VERSION = (
  "a2.target_geometry_airframe_constraint_correction_candidate.v1"
)
SUBCOMPONENT_SHAPE_PLACEMENT_SCHEMA_VERSION = (
  "a2.target_geometry_subcomponent_shape_placement_candidate.v1"
)
DEFAULT_GENERATED_ON = "2026-06-11"
REVIEW_POINT_COMPONENT_RADIUS_M = 2.0
INCH_TO_M = 0.0254
US_GALLON_TO_M3 = 0.003785411784


def _inch(value: float) -> float:
  return value * INCH_TO_M

FINE_PROXY_KIND_BY_REGION = {
  "nose_radome": "convex_hull",
  "forward_fuselage": "obb",
  "canopy": "convex_hull",
  "center_fuselage": "obb",
  "intake": "convex_hull",
  "aft_fuselage_engine": "obb",
  "engine_nozzle": "obb",
  "left_wing": "thin_prism",
  "right_wing": "thin_prism",
  "left_wing_root": "convex_hull",
  "right_wing_root": "convex_hull",
  "left_horizontal_tail": "thin_prism",
  "right_horizontal_tail": "thin_prism",
  "vertical_tail": "thin_prism",
}
SILHOUETTE_VIEW_AXES = {
  "top": (0, 1),
  "side": (0, 2),
  "front": (1, 2),
}
CURATED_MESH_SILHOUETTE_SOURCE_NODES = {
  "nose_radome": ["Object_4"],
  "forward_fuselage": ["Object_4"],
  "canopy": ["Object_6", "Object_8", "Object_16"],
  "center_fuselage": ["Object_4", "Object_14"],
  "intake": ["Object_10", "Object_12"],
  "aft_fuselage_engine": ["Object_4", "Object_38"],
  "engine_nozzle": ["Object_38"],
  "left_wing": ["Object_34", "Object_22"],
  "right_wing": ["Object_32", "Object_20"],
  "left_wing_root": ["Object_4", "Object_34"],
  "right_wing_root": ["Object_4", "Object_32"],
  "left_horizontal_tail": ["Object_36", "Object_28", "Object_30"],
  "right_horizontal_tail": ["Object_18", "Object_24", "Object_26"],
  "vertical_tail": ["Object_40"],
}
SURFACE_COMPONENT_RULES = {
  "nose_radome": {
    "surface_component_id": "surface_nose_radome",
    "surface_role": "radome",
    "expected_damage_modes": [
      "perforation",
      "surface_tearing",
      "sensor_aperture_damage_candidate",
    ],
    "expected_internal_components": [
      "apg68_radar_array",
      "iff_interrogator",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "forward_fuselage": {
    "surface_component_id": "surface_forward_fuselage_skin",
    "surface_role": "fuselage_skin",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "cockpit_or_avionics_exposure_candidate",
    ],
    "expected_internal_components": [
      "cockpit_crew_station",
      "nose_avionics_bay",
      "inertial_navigation_unit",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "canopy": {
    "surface_component_id": "surface_canopy",
    "surface_role": "canopy",
    "expected_damage_modes": [
      "transparent_surface_fracture",
      "perforation",
      "cockpit_exposure_candidate",
    ],
    "expected_internal_components": [
      "dedicated_canopy_surface_component",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "center_fuselage": {
    "surface_component_id": "surface_center_fuselage_skin",
    "surface_role": "fuselage_skin",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "fuel_or_avionics_exposure_candidate",
    ],
    "expected_internal_components": [
      "center_fuselage_fuel_cell",
      "mission_computer",
      "data_link_terminal",
      "flight_control_computer",
      "wing_spar_center",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "intake": {
    "surface_component_id": "surface_intake_lip_and_duct",
    "surface_role": "intake",
    "expected_damage_modes": [
      "intake_lip_damage",
      "perforation",
      "airflow_path_damage_candidate",
    ],
    "expected_internal_components": [
      "dedicated_intake_lip_or_duct_component",
      "engine_core",
      "engine_fuel_control_unit",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "aft_fuselage_engine": {
    "surface_component_id": "surface_aft_engine_bay_skin",
    "surface_role": "engine_bay_skin",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "engine_bay_exposure_candidate",
    ],
    "expected_internal_components": [
      "electrical_power_bus",
      "engine_core",
      "tail_hydraulic_pump",
      "engine_fuel_control_unit",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "engine_nozzle": {
    "surface_component_id": "surface_engine_nozzle",
    "surface_role": "nozzle",
    "expected_damage_modes": [
      "nozzle_petal_damage",
      "perforation",
      "exhaust_area_change_candidate",
    ],
    "expected_internal_components": [
      "afterburner_nozzle",
      "engine_core",
      "engine_fuel_control_unit",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "left_wing": {
    "surface_component_id": "surface_left_wing_skin",
    "surface_role": "lifting_surface",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "surface_area_loss",
      "control_surface_damage_candidate",
    ],
    "expected_internal_components": [
      "left_wing_fuel_cell",
      "left_aileron_actuator",
      "left_leading_edge_flap_actuator",
      "wing_spar_center",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "right_wing": {
    "surface_component_id": "surface_right_wing_skin",
    "surface_role": "lifting_surface",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "surface_area_loss",
      "control_surface_damage_candidate",
    ],
    "expected_internal_components": [
      "right_wing_fuel_cell",
      "right_aileron_actuator",
      "right_leading_edge_flap_actuator",
      "wing_spar_center",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "left_wing_root": {
    "surface_component_id": "surface_left_wing_root_fairing",
    "surface_role": "structural_transition",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "spar_or_fuel_cell_exposure_candidate",
    ],
    "expected_internal_components": [
      "left_leading_edge_flap_actuator",
      "left_wing_fuel_cell",
      "wing_spar_center",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "right_wing_root": {
    "surface_component_id": "surface_right_wing_root_fairing",
    "surface_role": "structural_transition",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "spar_or_fuel_cell_exposure_candidate",
    ],
    "expected_internal_components": [
      "right_leading_edge_flap_actuator",
      "right_wing_fuel_cell",
      "wing_spar_center",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "left_horizontal_tail": {
    "surface_component_id": "surface_left_horizontal_tail_skin",
    "surface_role": "tail_surface",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "surface_area_loss",
      "control_surface_damage_candidate",
    ],
    "expected_internal_components": [
      "left_horizontal_tail_actuator_or_surface_component",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "right_horizontal_tail": {
    "surface_component_id": "surface_right_horizontal_tail_skin",
    "surface_role": "tail_surface",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "surface_area_loss",
      "control_surface_damage_candidate",
    ],
    "expected_internal_components": [
      "right_horizontal_tail_actuator_or_surface_component",
    ],
    "missing_existing_runtime_component_relations": [],
  },
  "vertical_tail": {
    "surface_component_id": "surface_vertical_tail_skin",
    "surface_role": "tail_surface",
    "expected_damage_modes": [
      "perforation",
      "skin_tearing",
      "surface_area_loss",
      "rudder_damage_candidate",
    ],
    "expected_internal_components": ["rudder_actuator"],
    "missing_existing_runtime_component_relations": [],
  },
}
SEMANTIC_DAMAGE_VOLUME_RULES = {
  "nose_radome": {
    "semantic_component_id": "semantic_nose_radome_volume",
    "volume_role": "radome_volume",
    "runtime_system": "airframe_radome",
    "armor_mm": 2.5,
    "threshold_scale": 1.05,
  },
  "forward_fuselage": {
    "semantic_component_id": "semantic_forward_fuselage_skin_volume",
    "volume_role": "forward_fuselage_skin_volume",
    "runtime_system": "airframe_skin",
    "armor_mm": 4.0,
    "threshold_scale": 1.0,
  },
  "canopy": {
    "semantic_component_id": "semantic_canopy_surface_volume",
    "volume_role": "canopy_surface_volume",
    "runtime_system": "canopy_surface",
    "armor_mm": 1.5,
    "threshold_scale": 0.9,
  },
  "center_fuselage": {
    "semantic_component_id": "semantic_center_fuselage_skin_volume",
    "volume_role": "center_fuselage_skin_volume",
    "runtime_system": "airframe_skin",
    "armor_mm": 4.5,
    "threshold_scale": 1.05,
  },
  "intake": {
    "semantic_component_id": "semantic_intake_lip_and_duct_volume",
    "volume_role": "intake_lip_and_duct_volume",
    "runtime_system": "intake_geometry",
    "armor_mm": 2.0,
    "threshold_scale": 0.95,
  },
  "aft_fuselage_engine": {
    "semantic_component_id": "semantic_aft_engine_bay_skin_volume",
    "volume_role": "aft_engine_bay_skin_volume",
    "runtime_system": "airframe_skin",
    "armor_mm": 4.5,
    "threshold_scale": 1.05,
  },
  "engine_nozzle": {
    "semantic_component_id": "semantic_engine_nozzle_volume",
    "volume_role": "engine_nozzle_volume",
    "runtime_system": "engine_nozzle_geometry",
    "armor_mm": 3.0,
    "threshold_scale": 1.0,
  },
  "left_wing": {
    "semantic_component_id": "semantic_left_wing_skin_volume",
    "volume_role": "left_wing_skin_volume",
    "runtime_system": "wing_skin",
    "armor_mm": 2.5,
    "threshold_scale": 0.95,
  },
  "right_wing": {
    "semantic_component_id": "semantic_right_wing_skin_volume",
    "volume_role": "right_wing_skin_volume",
    "runtime_system": "wing_skin",
    "armor_mm": 2.5,
    "threshold_scale": 0.95,
  },
  "left_wing_root": {
    "semantic_component_id": "semantic_left_wing_root_fairing_volume",
    "volume_role": "left_wing_root_fairing_volume",
    "runtime_system": "wing_root_fairing",
    "armor_mm": 3.5,
    "threshold_scale": 1.0,
  },
  "right_wing_root": {
    "semantic_component_id": "semantic_right_wing_root_fairing_volume",
    "volume_role": "right_wing_root_fairing_volume",
    "runtime_system": "wing_root_fairing",
    "armor_mm": 3.5,
    "threshold_scale": 1.0,
  },
  "left_horizontal_tail": {
    "semantic_component_id": "semantic_left_horizontal_tail_skin_volume",
    "volume_role": "left_horizontal_tail_skin_volume",
    "runtime_system": "tail_surface_skin",
    "armor_mm": 2.0,
    "threshold_scale": 0.95,
  },
  "right_horizontal_tail": {
    "semantic_component_id": "semantic_right_horizontal_tail_skin_volume",
    "volume_role": "right_horizontal_tail_skin_volume",
    "runtime_system": "tail_surface_skin",
    "armor_mm": 2.0,
    "threshold_scale": 0.95,
  },
  "vertical_tail": {
    "semantic_component_id": "semantic_vertical_tail_skin_volume",
    "volume_role": "vertical_tail_skin_volume",
    "runtime_system": "tail_surface_skin",
    "armor_mm": 2.5,
    "threshold_scale": 1.0,
  },
}
COMPONENT_SEMANTIC_REVIEW_RULES = {
  "engine_core": {
    "review_status": "review_only_cross_region_boundary_candidate",
    "review_semantics": "cross_region_boundary_candidate_review_only",
    "review_severity": "review_only_candidate",
    "applicable_bound_region_ids": ["aft_fuselage_engine"],
    "semantic_region_ids": ["aft_fuselage_engine", "engine_nozzle", "intake"],
    "suppressed_anomalies": ["low_outer_region_overlap"],
    "notes": [
      "engine_core spans the review boundary between intake/aft engine bay/nozzle semantics",
      "low outer-region overlap is not treated as bad geometry while center remains in aft_fuselage_engine",
      "review-only candidate, not accepted runtime damage integration",
    ],
  },
  "wing_spar_center": {
    "review_status": "review_only_cross_region_semantic_hold",
    "review_semantics": "cross_region_structural_semantic_hold",
    "review_severity": "review_only_hold",
    "applicable_bound_region_ids": ["center_fuselage"],
    "semantic_region_ids": [
      "center_fuselage",
      "left_wing_root",
      "right_wing_root",
      "left_wing",
      "right_wing",
    ],
    "suppressed_anomalies": ["low_outer_region_overlap"],
    "notes": [
      "wing_spar_center is a broad thin structural component crossing fuselage and wing-root semantics",
      "low single-region overlap is held as a cross-region semantic candidate, not a bad box by itself",
      "review-only hold, not accepted runtime damage integration",
    ],
  },
}
R18_SHAPE_PROMOTION_STATUS = "r18_promoted_from_subcomponent_shape_candidate"
R21_LATEST_PROMOTION_STATUS = "r21_promoted_from_latest_subcomponent_candidate"
PROMOTED_SHAPE_STATUSES = {
  R18_SHAPE_PROMOTION_STATUS,
  R21_LATEST_PROMOTION_STATUS,
}
INTERNAL_COMPONENT_PRIOR_RULES = {
  "apg68_radar_array": {
    "shape": "ellipsoid",
    "component_role": "sensor_aperture_receiver",
    "dimensions_m": [_inch(4.0), _inch(29.0), _inch(19.0)],
    "center_m": [4.187559, 0.0, -0.52538],
    "constraint_region_ids": ["nose_radome", "forward_fuselage"],
    "size_basis": "public_related_apg66_antenna_dimensions",
    "size_evidence_level": "public_related_family_dimension_not_apg68_exact",
    "size_source_urls": [
      "https://www.radartutorial.eu/19.kartei/08.airborne/karte018.en.html",
      "https://www.forecastinternational.com/archive/disp_pdf.cfm?DACH_RECNO=1039",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": (
      "radar aperture uses the public APG-66 planar antenna size as a related "
      "F-16 radar-family bound because exact APG-68 antenna dimensions are not "
      "public in the packet source set; R21 promotes the R20 radome/forward-fuselage "
      "aperture placement candidate because it preserves nominal dimensions and "
      "clears sampled whole-airframe silhouette exposure."
    ),
  },
  "iff_interrogator": {
    "shape": "ellipsoid",
    "component_role": "small_avionics_receiver",
    "dimensions_m": [_inch(14.5), _inch(6.0), _inch(8.26)],
    "size_basis": "public_apx_family_lru_dimensions",
    "size_evidence_level": "public_lru_dimension_related_f16_iff_family",
    "size_source_urls": [
      "https://www.baesystems.com/en/product/apx-125-advanced-identification-friend-or-foe",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R18_SHAPE_PROMOTION_STATUS,
    "rationale": (
      "IFF receiver uses public APX-family interrogator LRU dimensions; R18 "
      "promotes the R17 rounded-LRU ellipsoid candidate because it preserves "
      "nominal dimensions and removes whole-airframe silhouette exposure."
    ),
  },
  "cockpit_crew_station": {
    "shape": "ellipsoid",
    "component_role": "crew_volume_receiver",
    "dimensions_m": [1.25, _inch(20.0), 1.15],
    "center_m": [3.787559, 0.0, -0.62538],
    "constraint_region_ids": ["canopy", "forward_fuselage"],
    "size_basis": "public_aces_ii_seat_width_plus_crew_envelope_estimate",
    "size_evidence_level": "public_partial_dimension_engineering_envelope",
    "size_source_urls": [
      "https://www.ejectionsite.com/acesii.htm",
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": (
      "crew station is not a single hardware box; width is anchored to public "
      "ACES II seat dimensions while length/height remain a crew-envelope estimate; "
      "R21 promotes the R20 canopy/forward-fuselage crew-envelope placement candidate "
      "because it preserves the nominal crew envelope and clears sampled silhouette exposure."
    ),
  },
  "inertial_navigation_unit": {
    "shape": "ellipsoid",
    "component_role": "small_avionics_receiver",
    "dimensions_m": [_inch(9.8), _inch(7.0), _inch(7.0)],
    "size_basis": "public_honeywell_h764g_egi_dimensions",
    "size_evidence_level": "public_lru_dimension",
    "size_source_urls": [
      "https://aerospace.honeywell.com/us/en/products-and-services/product/hardware-and-systems/navigation-and-radios/h-764g-embedded-gps-inertial-navigation-system",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R18_SHAPE_PROMOTION_STATUS,
    "rationale": (
      "INS receiver uses public H-764G EGI package dimensions; R18 promotes "
      "the R17 rounded-LRU ellipsoid candidate because it preserves nominal "
      "dimensions and removes whole-airframe silhouette exposure."
    ),
  },
  "nose_avionics_bay": {
    "shape": "obb",
    "component_role": "avionics_bay_receiver",
    "dimensions_m": [_inch(12.62), _inch(4.88), _inch(5.65)],
    "size_basis": "standard_half_atr_avionics_enclosure_proxy",
    "size_evidence_level": "standard_enclosure_proxy_not_true_f16_bay",
    "size_source_urls": [
      "https://www.elma.com/en/products/systems/atr-cases/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": (
      "nose avionics bay is a semantic receiver rather than one public LRU; "
      "a half-ATR avionics enclosure proxy is used until F-16 bay dimensions are available."
    ),
  },
  "dedicated_canopy_surface_component": {
    "shape": "ellipsoid",
    "component_role": "surface_receiver",
    "span_scale": [0.88, 0.88, 0.56],
    "size_basis": "mesh_semantic_surface_span",
    "size_evidence_level": "asset_mesh_derived_surface_not_public_engineering_dimension",
    "size_source_urls": [
      "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": True,
    "rationale": "canopy receiver is a surface receiver; its size follows the semantic canopy mesh, not an internal box.",
  },
  "center_fuselage_fuel_cell": {
    "shape": "ellipsoid",
    "component_role": "fuel_cell_receiver",
    "dimensions_m": [2.6, 0.9, 0.72],
    "center_m": [-0.278842, 0.0, -0.600971],
    "size_basis": "f16_internal_fuel_capacity_partition_estimate",
    "size_evidence_level": "public_total_capacity_partition_estimate",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": (
      "fuel cell dimensions are capacity-informed because public sources give "
      "total internal fuel capacity, not exact cell boundaries; R21 promotes the "
      "R19 latest centerline candidate because it preserves the nominal fuel volume "
      "and clears sampled whole-airframe silhouette exposure."
    ),
  },
  "mission_computer": {
    "shape": "obb",
    "component_role": "avionics_box_receiver",
    "dimensions_m": [_inch(12.62), _inch(4.88), _inch(5.65)],
    "size_basis": "standard_half_atr_avionics_enclosure_proxy",
    "size_evidence_level": "standard_enclosure_proxy_pending_f16_mmc_dimensions",
    "size_source_urls": [
      "https://www.elma.com/en/products/systems/atr-cases/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "mission computer exact F-16 MMC size is not in the packet source set; use a standard avionics enclosure proxy.",
  },
  "data_link_terminal": {
    "shape": "obb",
    "component_role": "small_avionics_receiver",
    "dimensions_m": [_inch(13.5), _inch(7.5), _inch(7.6)],
    "size_basis": "public_mids_lvt_terminal_dimensions",
    "size_evidence_level": "public_lru_dimension",
    "size_source_urls": [
      "https://www.datalinksolutions.net/products/mids-lvt/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "data-link receiver uses public MIDS-LVT terminal dimensions.",
  },
  "flight_control_computer": {
    "shape": "obb",
    "component_role": "avionics_box_receiver",
    "dimensions_m": [_inch(12.62), _inch(4.88), _inch(5.65)],
    "size_basis": "standard_half_atr_avionics_enclosure_proxy",
    "size_evidence_level": "standard_enclosure_proxy_pending_f16_flcc_dimensions",
    "size_source_urls": [
      "https://www.elma.com/en/products/systems/atr-cases/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "flight-control computer exact F-16 FLCC size is not in the packet source set; use a standard avionics enclosure proxy.",
  },
  "dedicated_intake_lip_or_duct_component": {
    "shape": "ellipsoid",
    "component_role": "duct_receiver",
    "dimensions_m": [1.0, 0.58, 1.1],
    "size_basis": "mesh_semantic_intake_region_measurement",
    "size_evidence_level": "asset_mesh_derived_duct_dimension_not_public_engineering_dimension",
    "size_source_urls": [
      "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "intake duct receiver follows the measured semantic intake region because public F-16 duct dimensions are not available here.",
  },
  "electrical_power_bus": {
    "shape": "capsule",
    "axis": "x",
    "component_role": "electrical_bus_receiver",
    "dimensions_m": [0.45, 0.06, 0.06],
    "size_basis": "engineering_proxy_no_public_f16_bus_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 power bus geometry was not found; this remains a low-confidence compact run proxy.",
  },
  "engine_core": {
    "shape": "capsule",
    "axis": "x",
    "component_role": "cross_region_engine_receiver",
    "dimensions_m": [_inch(181.9), _inch(46.5), _inch(46.5)],
    "center_m": [-3.693053, 0.0, -0.554381],
    "center_region_ids": ["aft_fuselage_engine"],
    "center_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "size_basis": "public_f110_ge_129_engine_dimensions",
    "size_evidence_level": "public_engine_dimension",
    "size_source_urls": [
      "https://www.geaerospace.com/propulsion/military/f110",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "engine core uses public F110-GE-129 engine length and maximum diameter; R21 promotes the rounded lower centerline capsule candidate, while ownership remains cross-region held.",
  },
  "afterburner_nozzle": {
    "shape": "ellipsoid",
    "axis": "",
    "component_role": "nozzle_receiver",
    "dimensions_m": [0.75, _inch(46.5), _inch(46.5)],
    "center_m": [-5.75, -0.2, -0.7],
    "constraint_region_ids": ["engine_nozzle", "aft_fuselage_engine"],
    "size_basis": "f110_diameter_plus_nozzle_region_length_estimate",
    "size_evidence_level": "public_engine_diameter_mesh_length_estimate",
    "size_source_urls": [
      "https://www.geaerospace.com/propulsion/military/f110",
      "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "nozzle diameter follows public F110 maximum diameter; nozzle length remains a mesh-region estimate; R21 promotes the aft/lower/lateral ellipsoid candidate as a review-only tapered-nozzle proxy.",
  },
  "tail_hydraulic_pump": {
    "shape": "obb",
    "component_role": "small_hydraulic_receiver",
    "dimensions_m": [0.25, 0.18, 0.18],
    "size_basis": "engineering_proxy_no_public_f16_pump_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 tail hydraulic pump dimensions were not found; this remains a low-confidence pump proxy.",
  },
  "engine_fuel_control_unit": {
    "shape": "obb",
    "component_role": "small_engine_control_receiver",
    "dimensions_m": [_inch(12.62), _inch(4.88), _inch(5.65)],
    "size_basis": "standard_half_atr_control_box_proxy",
    "size_evidence_level": "standard_enclosure_proxy_pending_f110_control_unit_dimensions",
    "size_source_urls": [
      "https://www.elma.com/en/products/systems/atr-cases/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "engine fuel-control exact installed dimensions are not public in the packet source set; use a standard control-box proxy.",
  },
  "rudder_actuator": {
    "shape": "capsule",
    "axis": "z",
    "component_role": "control_surface_actuator_receiver",
    "dimensions_m": [0.08, 0.08, 0.45],
    "size_basis": "engineering_proxy_no_public_f16_rudder_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 rudder actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "left_horizontal_tail_actuator_or_surface_component": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "tail_surface_receiver",
    "dimensions_m": [0.08, 0.65, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_tail_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public horizontal-tail actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "right_horizontal_tail_actuator_or_surface_component": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "tail_surface_receiver",
    "dimensions_m": [0.08, 0.65, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_tail_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public horizontal-tail actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "left_wing_fuel_cell": {
    "shape": "ellipsoid",
    "component_role": "wing_fuel_cell_receiver",
    "dimensions_m": [2.0, 2.2, 0.15],
    "center_m": [-1.4, -2.3, -0.985],
    "size_basis": "f16_internal_fuel_capacity_partition_estimate",
    "size_evidence_level": "public_total_capacity_partition_estimate",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "wing fuel cell size is capacity-informed; exact F-16 wing-cell boundaries are not public in the packet source set; R21 promotes the inboard/aft ellipsoid candidate as review-only conformal bladder geometry.",
  },
  "right_wing_fuel_cell": {
    "shape": "ellipsoid",
    "component_role": "wing_fuel_cell_receiver",
    "dimensions_m": [2.0, 2.2, 0.15],
    "center_m": [-1.4, 2.3, -0.985],
    "size_basis": "f16_internal_fuel_capacity_partition_estimate",
    "size_evidence_level": "public_total_capacity_partition_estimate",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "wing fuel cell size is capacity-informed; exact F-16 wing-cell boundaries are not public in the packet source set; R21 promotes the inboard/aft ellipsoid candidate as review-only conformal bladder geometry.",
  },
  "left_aileron_actuator": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "control_surface_actuator_receiver",
    "dimensions_m": [0.08, 0.45, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_aileron_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 aileron actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "right_aileron_actuator": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "control_surface_actuator_receiver",
    "dimensions_m": [0.08, 0.45, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_aileron_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 aileron actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "wing_spar_center": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "cross_region_structural_receiver",
    "dimensions_m": [0.18, 6.6, 0.18],
    "center_region_ids": ["left_wing_root", "right_wing_root"],
    "center_axis_region_ids": {
      "z": ["left_wing", "right_wing"],
    },
    "center_bounds_source": "source_region_bounds",
    "airframe_projection_adjustment": False,
    "size_basis": "center_wing_box_runtime_span_with_wing_root_mesh_center",
    "size_evidence_level": "cross_region_structure_proxy_pending_true_spar_dimensions",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
      "examples/config/database/aircraft/units/f16c_block50.json",
      "examples/viz/web_viz/static/assets/air/audit/f16_c_falcon_carlos_maciel/gltf/scene.gltf",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "wing spar center uses the existing cross-region receiver span and wing-root mesh center as a carry-through proxy; it remains held until split into true spar segments.",
  },
  "left_leading_edge_flap_actuator": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "control_surface_actuator_receiver",
    "dimensions_m": [0.08, 0.55, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_lef_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 leading-edge flap actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
  "right_leading_edge_flap_actuator": {
    "shape": "capsule",
    "axis": "y",
    "component_role": "control_surface_actuator_receiver",
    "dimensions_m": [0.08, 0.55, 0.08],
    "size_basis": "engineering_proxy_no_public_f16_lef_actuator_dimensions",
    "size_evidence_level": "low_confidence_engineering_proxy",
    "size_source_urls": [],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "rationale": "public F-16 leading-edge flap actuator dimensions were not found; this remains a low-confidence actuator proxy.",
  },
}
SUBCOMPONENT_SHAPE_PLACEMENT_DESIGN_RULES = {
  "apg68_radar_array": {
    "candidate_shape_family": "oblate_radar_aperture_ellipsoid",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_public_related_aperture_dimensions_and_retest_as_rounded_receiver_volume"
    ),
    "rationale": (
      "radar antenna damage receiver should behave like a thin aperture volume, "
      "not a corner-dominated box."
    ),
  },
  "cockpit_crew_station": {
    "candidate_shape_family": "crew_envelope_ellipsoid",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_current_crew_envelope_dimensions_then_require_multi_region_cockpit_review"
    ),
    "rationale": (
      "crew station already uses an ellipsoid; remaining exposure means placement "
      "or envelope dimensions need review, not a box-to-rounding fix."
    ),
  },
  "engine_core": {
    "candidate_shape_family": "rounded_engine_axis_capsule",
    "evaluation_shape": "capsule",
    "evaluation_axis": "x",
    "placement_policy": (
      "preserve_public_engine_length_and_diameter_while_testing_rounded_axial_envelope"
    ),
    "rationale": (
      "engine receiver should preserve the public F110 axial length/diameter "
      "semantics; a rounded capsule is a safer candidate than an arbitrary box."
    ),
  },
  "afterburner_nozzle": {
    "candidate_shape_family": "tapered_nozzle_ellipsoid_proxy",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_current_nozzle_dimensions_as_a_rounded_proxy_pending_frustum_model"
    ),
    "rationale": (
      "a true nozzle should become a tapered/frustum-like receiver, but the first "
      "review candidate uses a rounded proxy without shrinking dimensions."
    ),
  },
  "engine_core_afterburner_segment": {
    "candidate_shape_family": "segmented_engine_afterburner_capsule",
    "evaluation_shape": "capsule",
    "evaluation_axis": "x",
    "placement_policy": (
      "preserve_segment_length_and_diameter_then_apply_only_the_R16_center_shift_candidate"
    ),
    "rationale": (
      "afterburner segment is still axial engine geometry; use a rounded capsule "
      "plus the measured center shift rather than accepting the red cylinder block."
    ),
  },
  "engine_core_hot_section_segment": {
    "candidate_shape_family": "segmented_engine_hot_section_ellipsoid",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_segment_dimensions_and_retest_hot_section_as_rounded_receiver_volume"
    ),
    "rationale": (
      "hot-section split is a damage receiver proxy; a rounded volume removes the "
      "single side-view exposure without changing the nominal dimensions."
    ),
  },
  "engine_core_forward_compressor_segment": {
    "candidate_shape_family": "segmented_engine_compressor_ellipsoid",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_segment_dimensions_and_retest_forward_compressor_as_rounded_receiver_volume"
    ),
    "rationale": (
      "the forward compressor segment needs a rounded candidate before any further "
      "diameter or intake-transition modeling."
    ),
  },
  "wing_spar_center_left_inner_wing_segment": {
    "candidate_shape_family": "wing_following_spar_ellipsoid_proxy",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_segment_span_but_mark_for_wing_following_polycapsule_centerline"
    ),
    "rationale": (
      "inner-wing spar should follow the wing plane; the ellipsoid proxy measures "
      "how much a rounded segment helps before implementing a polyline capsule."
    ),
  },
  "wing_spar_center_right_inner_wing_segment": {
    "candidate_shape_family": "wing_following_spar_ellipsoid_proxy",
    "evaluation_shape": "ellipsoid",
    "evaluation_axis": "",
    "placement_policy": (
      "preserve_segment_span_but_mark_for_wing_following_polycapsule_centerline"
    ),
    "rationale": (
      "inner-wing spar should follow the wing plane; the ellipsoid proxy measures "
      "how much a rounded segment helps before implementing a polyline capsule."
    ),
  },
}
SUBCOMPONENT_CENTERLINE_PLACEMENT_RULES = {
  "apg68_radar_array": {
    "center_offset_m": [0.0, 0.0, 0.1],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_radar_aperture_dimensions_and_test_small_vertical_centerline_shift"
    ),
    "rationale": (
      "local silhouette search shows a small upward shift reduces but does not "
      "clear the side-view exposure; radar aperture still needs a radome cross-section model."
    ),
  },
  "cockpit_crew_station": {
    "center_offset_m": [-0.5, 0.0, 0.1],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_crew_envelope_dimensions_and_test_limited_aft_upward_centerline_shift"
    ),
    "rationale": (
      "local silhouette search reduces exposure but cannot clear the cockpit "
      "envelope; this remains a canopy/forward-fuselage envelope modeling issue."
    ),
  },
  "center_fuselage_fuel_cell": {
    "center_offset_m": [0.0, 0.0, -0.3],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_fuel_cell_volume_and_shift_centerline_down_within_center_fuselage"
    ),
    "rationale": (
      "local silhouette search clears the single side-view exposure by moving "
      "the bladder proxy downward without changing nominal volume dimensions."
    ),
  },
  "engine_core": {
    "center_offset_m": [0.0, 0.0, -0.1],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_public_engine_length_and_diameter_and_test_slight_lower_centerline"
    ),
    "rationale": (
      "local silhouette search clears the rounded engine envelope with a small "
      "downward centerline correction, but cross-region ownership remains held."
    ),
  },
  "afterburner_nozzle": {
    "center_offset_m": [0.6, -0.2, -0.2],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_nozzle_dimensions_and_test_aft_lower_lateral_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears exposure with a larger aft/down/lateral "
      "shift; this should stay review-only until a tapered nozzle/frustum model is added."
    ),
  },
  "left_wing_fuel_cell": {
    "center_offset_m": [-0.6, 0.5, 0.0],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_fuel_cell_volume_and_test_inboard_aft_wing_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears exposure by moving the fuel proxy inboard "
      "and aft along the wing planform; a true wing-following bladder envelope is still needed."
    ),
  },
  "right_wing_fuel_cell": {
    "center_offset_m": [-0.6, -0.5, 0.0],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_fuel_cell_volume_and_test_inboard_aft_wing_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears exposure by moving the fuel proxy inboard "
      "and aft along the wing planform; a true wing-following bladder envelope is still needed."
    ),
  },
  "engine_core_forward_compressor_segment": {
    "center_offset_m": [-0.1, 0.0, -0.1],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_forward_compressor_segment_dimensions_and_test_aft_lower_centerline"
    ),
    "rationale": (
      "local silhouette search clears the remaining side-view exposure with a "
      "small aft/down centerline correction."
    ),
  },
  "wing_spar_center_left_inner_wing_segment": {
    "center_offset_m": [0.0, 0.8, 0.0],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_inner_spar_segment_span_and_test_inboard_wing_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears the front-view exposure by moving the "
      "left inner spar segment inboard; true spar modeling should use a wing-following centerline."
    ),
  },
  "wing_spar_center_right_inner_wing_segment": {
    "center_offset_m": [0.0, -0.8, 0.0],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_inner_spar_segment_span_and_test_inboard_wing_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears the front-view exposure by moving the "
      "right inner spar segment inboard; true spar modeling should use a wing-following centerline."
    ),
  },
}
SUBCOMPONENT_LATEST_PLACEMENT_RULES = {
  "apg68_radar_array": {
    "stage": "R20_radome_forward_fuselage_aperture_section_candidate",
    "center_offset_from_centerline_m": [-1.1, 0.0, 0.2],
    "source_basis": "R20_cross_region_radome_forward_fuselage_aperture_section_search",
    "placement_policy": (
      "preserve_radar_aperture_dimensions_and_place_the_aperture_at_the_radome_forward_fuselage_interface"
    ),
    "rationale": (
      "radar antenna damage should be represented by an aperture behind the "
      "radome rather than a tip-centered radome block; the R20 cross-region "
      "centerline clears the sampled whole-airframe silhouettes without shrinking the nominal aperture dimensions."
    ),
  },
  "cockpit_crew_station": {
    "stage": "R20_canopy_forward_fuselage_crew_envelope_candidate",
    "center_offset_from_centerline_m": [-1.0, 0.0, 0.1],
    "source_basis": "R20_cross_region_canopy_forward_fuselage_crew_envelope_search",
    "placement_policy": (
      "preserve_crew_envelope_dimensions_and_place_the_receiver_under_the_canopy_forward_fuselage_envelope"
    ),
    "rationale": (
      "crew station damage is a canopy/forward-fuselage envelope, not a "
      "radome-side point receiver; the R20 cross-region centerline clears the sampled silhouettes while preserving the crew envelope dimensions."
    ),
  },
}
HELD_SEGMENT_SHAPE_PLACEMENT_OVERRIDES = {
  "engine_core_afterburner_segment": {
    "shape": "capsule",
    "axis": "x",
    "center_offset_m": [0.207628, 0.0, 0.0],
    "shape_promotion_status": R18_SHAPE_PROMOTION_STATUS,
    "source_basis": (
      "R18_promoted_R17_segmented_engine_afterburner_capsule_with_center_shift"
    ),
  },
  "engine_core_hot_section_segment": {
    "shape": "ellipsoid",
    "axis": "",
    "center_offset_m": [0.0, 0.0, 0.0],
    "shape_promotion_status": R18_SHAPE_PROMOTION_STATUS,
    "source_basis": (
      "R18_promoted_R17_segmented_engine_hot_section_ellipsoid"
    ),
  },
  "engine_core_forward_compressor_segment": {
    "shape": "ellipsoid",
    "axis": "",
    "center_offset_m": [-0.2, 0.0, 0.0],
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "source_basis": (
      "R21_promoted_forward_compressor_local_silhouette_clearance_ellipsoid"
    ),
  },
  "wing_spar_center_left_inner_wing_segment": {
    "shape": "ellipsoid",
    "axis": "",
    "center_offset_m": [0.0, 0.8, 0.0],
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "source_basis": (
      "R21_promoted_R19_left_inner_wing_spar_latest_centerline_ellipsoid"
    ),
  },
  "wing_spar_center_right_inner_wing_segment": {
    "shape": "ellipsoid",
    "axis": "",
    "center_offset_m": [0.0, -0.8, 0.0],
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "source_basis": (
      "R21_promoted_R19_right_inner_wing_spar_latest_centerline_ellipsoid"
    ),
  },
}
INVALID_COMPONENT_REGION_BINDINGS = {
  "afterburner_nozzle": {
    "blocked_region_ids": ["vertical_tail"],
    "preferred_region_ids": ["engine_nozzle", "aft_fuselage_engine"],
    "review_semantics": "invalid_region_binding_blocked",
    "review_severity": "hard_blocker",
    "notes": [
      "afterburner_nozzle must not bind to vertical_tail even when coarse overlap ranks it first",
      "keep this as a tool-rule blocker until the component box or region mapping is repaired",
    ],
  },
}
CROSS_REGION_REVIEW_SEMANTICS = {
  "cross_region_boundary_candidate_review_only",
  "cross_region_structural_semantic_hold",
}
HARD_BLOCKER_REVIEW_SEMANTICS = {
  "side_sign_mismatch_hard_blocker",
  "invalid_region_binding_blocked",
}
GEOMETRY_REVIEW_SEMANTICS = {
  "geometry_review_required",
}

DEFAULT_AIRCRAFT = (
  REPO_ROOT / "examples" / "config" / "database" / "aircraft" / "units" / "f16c_block50.json"
)
DEFAULT_RUNTIME_DATABASE = REPO_ROOT / "examples" / "config" / "database"
TARGET_GEOMETRY_PROXY_TRAINING_CONFIG = (
  REPO_ROOT
  / "examples"
  / "config"
  / "training"
  / "active"
  / "air_combat"
  / "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json"
)
DEFAULT_AUDIT_SCENE = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "audit"
  / "f16_c_falcon_carlos_maciel"
  / "gltf"
  / "scene.gltf"
)
DEFAULT_VISUAL_GLB = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "f16_c_falcon_carlos_maciel"
  / "f16_c_falcon_carlos_maciel.glb"
)
DEFAULT_INTAKE_METADATA = (
  REPO_ROOT
  / "examples"
  / "viz"
  / "web_viz"
  / "static"
  / "assets"
  / "air"
  / "f16_c_falcon_carlos_maciel"
  / "intake_metadata.json"
)
DEFAULT_REGISTRY = REPO_ROOT / "examples" / "viz" / "assets" / "registry" / "default.json"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "a2_high_fidelity_damage_model"
  / "missile_lethality_target_geometry"
  / "review_packets"
  / "f16c_20260611"
)

COMPONENT_TYPE_FORMATS = {
  5120: "b",
  5121: "B",
  5122: "h",
  5123: "H",
  5125: "I",
  5126: "f",
}
TYPE_COUNTS = {
  "SCALAR": 1,
  "VEC2": 2,
  "VEC3": 3,
  "VEC4": 4,
  "MAT2": 4,
  "MAT3": 9,
  "MAT4": 16,
}
TRIANGLE_MODE = 4


@dataclass
class Bounds:
  minimum: list[float]
  maximum: list[float]

  @classmethod
  def empty(cls) -> "Bounds":
    inf = float("inf")
    return cls([inf, inf, inf], [-inf, -inf, -inf])

  def include(self, point: Iterable[float]) -> None:
    for index, value in enumerate(point):
      self.minimum[index] = min(self.minimum[index], float(value))
      self.maximum[index] = max(self.maximum[index], float(value))

  def span(self) -> list[float]:
    return [self.maximum[index] - self.minimum[index] for index in range(3)]

  def center(self) -> list[float]:
    return [
      (self.minimum[index] + self.maximum[index]) / 2.0 for index in range(3)
    ]

  def to_record(self) -> dict[str, list[float]]:
    return {
      "min": _round_vec(self.minimum),
      "max": _round_vec(self.maximum),
      "span": _round_vec(self.span()),
      "center": _round_vec(self.center()),
    }


def _round(value: float, digits: int = 6) -> float:
  if math.isfinite(value):
    return round(float(value), digits)
  return value


def _round_vec(values: Iterable[float], digits: int = 6) -> list[float]:
  return [_round(value, digits) for value in values]


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return str(path)


def _sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _identity() -> list[list[float]]:
  return [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
  ]


def _mat_mul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
  return [
    [
      sum(left[row][k] * right[k][col] for k in range(4))
      for col in range(4)
    ]
    for row in range(4)
  ]


def _transform_point(matrix: list[list[float]], point: tuple[float, float, float]) -> tuple[float, float, float]:
  x, y, z = point
  return (
    matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3],
    matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3],
    matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3],
  )


def _matrix_from_gltf(values: list[float]) -> list[list[float]]:
  if len(values) != 16:
    raise ValueError("glTF node matrix must contain 16 values")
  return [
    [values[0], values[4], values[8], values[12]],
    [values[1], values[5], values[9], values[13]],
    [values[2], values[6], values[10], values[14]],
    [values[3], values[7], values[11], values[15]],
  ]


def _translation_matrix(values: list[float]) -> list[list[float]]:
  matrix = _identity()
  matrix[0][3], matrix[1][3], matrix[2][3] = values
  return matrix


def _scale_matrix(values: list[float]) -> list[list[float]]:
  matrix = _identity()
  matrix[0][0], matrix[1][1], matrix[2][2] = values
  return matrix


def _rotation_matrix(quaternion: list[float]) -> list[list[float]]:
  x, y, z, w = quaternion
  xx, yy, zz = x * x, y * y, z * z
  xy, xz, yz = x * y, x * z, y * z
  wx, wy, wz = w * x, w * y, w * z
  return [
    [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy), 0.0],
    [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx), 0.0],
    [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy), 0.0],
    [0.0, 0.0, 0.0, 1.0],
  ]


def _node_local_matrix(node: dict[str, Any]) -> list[list[float]]:
  if "matrix" in node:
    return _matrix_from_gltf([float(value) for value in node["matrix"]])

  translation = [float(value) for value in node.get("translation", [0.0, 0.0, 0.0])]
  rotation = [float(value) for value in node.get("rotation", [0.0, 0.0, 0.0, 1.0])]
  scale = [float(value) for value in node.get("scale", [1.0, 1.0, 1.0])]
  return _mat_mul(_mat_mul(_translation_matrix(translation), _rotation_matrix(rotation)), _scale_matrix(scale))


def _load_buffer(gltf_path: Path, buffer_def: dict[str, Any]) -> bytes:
  uri = buffer_def.get("uri", "")
  if uri.startswith("data:"):
    _, encoded = uri.split(",", 1)
    return base64.b64decode(encoded)
  buffer_path = gltf_path.parent / uri
  return buffer_path.read_bytes()


def _accessor_values(
  *,
  gltf: dict[str, Any],
  buffers: list[bytes],
  accessor_index: int,
) -> list[tuple[float, ...]]:
  accessor = gltf["accessors"][accessor_index]
  if "sparse" in accessor:
    raise ValueError("Sparse glTF accessors are not supported by this review tool")

  component_type = accessor["componentType"]
  type_name = accessor["type"]
  fmt = COMPONENT_TYPE_FORMATS[component_type]
  component_count = TYPE_COUNTS[type_name]
  component_size = struct.calcsize("<" + fmt)
  element_size = component_size * component_count

  buffer_view = gltf["bufferViews"][accessor["bufferView"]]
  buffer_data = buffers[buffer_view["buffer"]]
  base_offset = int(buffer_view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
  stride = int(buffer_view.get("byteStride", element_size))
  count = int(accessor["count"])
  unpack = struct.Struct("<" + fmt * component_count).unpack_from

  values: list[tuple[float, ...]] = []
  for index in range(count):
    offset = base_offset + index * stride
    values.append(tuple(float(value) for value in unpack(buffer_data, offset)))
  return values


def _scene_root_nodes(gltf: dict[str, Any]) -> list[int]:
  scene_index = int(gltf.get("scene", 0))
  scenes = gltf.get("scenes", [])
  if scenes:
    return [int(index) for index in scenes[scene_index].get("nodes", [])]
  return list(range(len(gltf.get("nodes", []))))


def _walk_nodes(
  gltf: dict[str, Any],
  node_indices: Iterable[int],
  parent_matrix: list[list[float]],
) -> Iterable[tuple[int, dict[str, Any], list[list[float]]]]:
  nodes = gltf.get("nodes", [])
  for node_index in node_indices:
    node = nodes[node_index]
    world_matrix = _mat_mul(parent_matrix, _node_local_matrix(node))
    yield node_index, node, world_matrix
    yield from _walk_nodes(gltf, node.get("children", []), world_matrix)


def summarize_gltf_scene(gltf_path: Path) -> dict[str, Any]:
  gltf = _load_json(gltf_path)
  buffers = [_load_buffer(gltf_path, buffer_def) for buffer_def in gltf.get("buffers", [])]
  raw_bounds = Bounds.empty()
  transformed_bounds = Bounds.empty()
  node_bounds: list[dict[str, Any]] = []
  position_accessor_vertex_count = 0
  triangle_count = 0
  primitive_count = 0

  for node_index, node, world_matrix in _walk_nodes(gltf, _scene_root_nodes(gltf), _identity()):
    mesh_index = node.get("mesh")
    if mesh_index is None:
      continue
    mesh = gltf["meshes"][mesh_index]
    current_node_bounds = Bounds.empty()
    current_node_vertices = 0
    current_node_triangles = 0
    for primitive in mesh.get("primitives", []):
      attributes = primitive.get("attributes", {})
      if "POSITION" not in attributes:
        continue
      primitive_count += 1
      positions = _accessor_values(
        gltf=gltf,
        buffers=buffers,
        accessor_index=int(attributes["POSITION"]),
      )
      position_accessor_vertex_count += len(positions)
      current_node_vertices += len(positions)
      for position in positions:
        point = (position[0], position[1], position[2])
        raw_bounds.include(point)
        transformed = _transform_point(world_matrix, point)
        transformed_bounds.include(transformed)
        current_node_bounds.include(transformed)
      if int(primitive.get("mode", TRIANGLE_MODE)) == TRIANGLE_MODE:
        indices = primitive.get("indices")
        if indices is not None:
          triangle_count += int(gltf["accessors"][indices]["count"]) // 3
          current_node_triangles += int(gltf["accessors"][indices]["count"]) // 3
        else:
          triangle_count += len(positions) // 3
          current_node_triangles += len(positions) // 3
    if current_node_vertices:
      node_bounds.append(
        {
          "node_index": node_index,
          "node_name": node.get("name", f"node_{node_index}"),
          "mesh_index": mesh_index,
          "mesh_name": mesh.get("name", f"mesh_{mesh_index}"),
          "position_accessor_vertex_count": current_node_vertices,
          "triangle_count": current_node_triangles,
          "bounds": current_node_bounds.to_record(),
        }
      )

  notable_names = [
    record["node_name"]
    for record in node_bounds
    if any(
      token.lower() in record["node_name"].lower()
      for token in ("canopy", "pilot", "elevator", "aileron", "volet", "engine", "rudder")
    )
  ][:16]

  return {
    "asset": {
      "version": gltf.get("asset", {}).get("version", ""),
      "generator": gltf.get("asset", {}).get("generator", ""),
      "copyright": gltf.get("asset", {}).get("copyright", ""),
    },
    "node_count": len(gltf.get("nodes", [])),
    "mesh_count": len(gltf.get("meshes", [])),
    "material_count": len(gltf.get("materials", [])),
    "primitive_count": primitive_count,
    "triangle_count": triangle_count,
    "position_accessor_vertex_count": position_accessor_vertex_count,
    "raw_accessor_bounds": raw_bounds.to_record(),
    "transformed_bounds": transformed_bounds.to_record(),
    "notable_node_names": notable_names,
    "mesh_node_bounds": node_bounds,
  }


def extract_gltf_sim_vertex_records(
  gltf_path: Path,
  manifest: dict[str, Any],
) -> list[dict[str, Any]]:
  gltf = _load_json(gltf_path)
  buffers = [_load_buffer(gltf_path, buffer_def) for buffer_def in gltf.get("buffers", [])]
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  records: list[dict[str, Any]] = []

  for node_index, node, world_matrix in _walk_nodes(gltf, _scene_root_nodes(gltf), _identity()):
    mesh_index = node.get("mesh")
    if mesh_index is None:
      continue
    mesh = gltf["meshes"][mesh_index]
    for primitive in mesh.get("primitives", []):
      attributes = primitive.get("attributes", {})
      if "POSITION" not in attributes:
        continue
      positions = _accessor_values(
        gltf=gltf,
        buffers=buffers,
        accessor_index=int(attributes["POSITION"]),
      )
      for position in positions:
        transformed = _transform_point(
          world_matrix,
          (position[0], position[1], position[2]),
        )
        records.append(
          {
            "point_m": _round_vec(
              _sim_point_from_asset(
                [transformed[0], transformed[1], transformed[2]],
                asset_center=asset_center,
                scale=scale,
              )
            ),
            "node_index": node_index,
            "node_name": node.get("name", f"node_{node_index}"),
            "mesh_index": mesh_index,
            "mesh_name": mesh.get("name", f"mesh_{mesh_index}"),
          }
        )
  return records


def extract_gltf_sim_vertices(gltf_path: Path, manifest: dict[str, Any]) -> list[list[float]]:
  return [
    record["point_m"]
    for record in extract_gltf_sim_vertex_records(gltf_path, manifest)
  ]


def _find_registry_entry(registry: dict[str, Any], visual_glb: Path, repo_root: Path) -> dict[str, Any]:
  expected_suffix = "/" + _display_path(visual_glb, repo_root).split("examples/viz/web_viz/", 1)[-1]
  expected_suffix = expected_suffix.replace("/static/", "/static/")
  for entry in registry.get("entries", []):
    asset_path = entry.get("visual", {}).get("asset_path", "")
    if asset_path and asset_path.endswith(visual_glb.name):
      return entry
    if asset_path == expected_suffix:
      return entry
  return {}


def _hitbox_envelope(hitboxes: list[dict[str, Any]]) -> dict[str, Any]:
  bounds = Bounds.empty()
  component_count = 0
  systems: set[str] = set()
  for hitbox in hitboxes:
    offset = [float(value) for value in hitbox["offset"]]
    size = [float(value) for value in hitbox["size"]]
    for axis in range(3):
      bounds.minimum[axis] = min(bounds.minimum[axis], offset[axis] - size[axis] / 2.0)
      bounds.maximum[axis] = max(bounds.maximum[axis], offset[axis] + size[axis] / 2.0)
    systems.update(str(system) for system in hitbox.get("systems", []))
    components = hitbox.get("components", [])
    component_count += len(components)
    for component in components:
      if "system" in component:
        systems.add(str(component["system"]))
  return {
    "hitbox_count": len(hitboxes),
    "component_count": component_count,
    "systems": sorted(systems),
    "combined_envelope": bounds.to_record(),
  }


def _percent_error(actual: float, expected: float) -> float:
  if expected == 0.0:
    return 0.0
  return ((actual - expected) / expected) * 100.0


def _bounds_from_min_max(minimum: list[float], maximum: list[float]) -> dict[str, list[float]]:
  bounds = Bounds(minimum[:], maximum[:])
  return bounds.to_record()


def _box_from_center_size(center: list[float], size: list[float]) -> dict[str, list[float]]:
  minimum = [center[index] - size[index] / 2.0 for index in range(3)]
  maximum = [center[index] + size[index] / 2.0 for index in range(3)]
  return _bounds_from_min_max(minimum, maximum)


def _sim_point_from_asset(
  point: list[float], *, asset_center: list[float], scale: float
) -> list[float]:
  # Project local aircraft review coordinates use x forward, y right, z up.
  return [
    -(point[2] - asset_center[2]) * scale,
    (point[0] - asset_center[0]) * scale,
    (point[1] - asset_center[1]) * scale,
  ]


def _sim_bounds_from_asset_bounds(
  asset_bounds: dict[str, list[float]], *, asset_center: list[float], scale: float
) -> dict[str, list[float]]:
  bounds = Bounds.empty()
  min_values = asset_bounds["min"]
  max_values = asset_bounds["max"]
  for x in (min_values[0], max_values[0]):
    for y in (min_values[1], max_values[1]):
      for z in (min_values[2], max_values[2]):
        bounds.include(_sim_point_from_asset([x, y, z], asset_center=asset_center, scale=scale))
  return bounds.to_record()


def _merge_bounds(bounds_records: Iterable[dict[str, list[float]]]) -> dict[str, list[float]]:
  merged = Bounds.empty()
  count = 0
  for bounds in bounds_records:
    count += 1
    merged.include(bounds["min"])
    merged.include(bounds["max"])
  if count == 0:
    raise ValueError("Cannot merge an empty bounds collection")
  return merged.to_record()


def _pad_bounds(
  bounds: dict[str, list[float]],
  margins_m: list[float],
) -> dict[str, list[float]]:
  minimum = [bounds["min"][index] - margins_m[index] for index in range(3)]
  maximum = [bounds["max"][index] + margins_m[index] for index in range(3)]
  return _bounds_from_min_max(minimum, maximum)


def _mesh_node_sim_bounds_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, list[float]]]:
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  return {
    mesh_node["node_name"]: _sim_bounds_from_asset_bounds(
      mesh_node["bounds"], asset_center=asset_center, scale=scale
    )
    for mesh_node in manifest["gltf_summary"]["mesh_node_bounds"]
  }


def _curated_mesh_bounds(
  manifest: dict[str, Any],
  *,
  node_names: list[str],
  margins_m: list[float],
) -> dict[str, list[float]]:
  bounds_by_name = _mesh_node_sim_bounds_by_name(manifest)
  missing = [node_name for node_name in node_names if node_name not in bounds_by_name]
  if missing:
    raise ValueError(
      "Curated mesh geometry source nodes are missing from the audit scene: "
      + ", ".join(missing)
    )
  return _pad_bounds(
    _merge_bounds(bounds_by_name[node_name] for node_name in node_names),
    margins_m,
  )


def _volume(bounds: dict[str, list[float]]) -> float:
  span = bounds["span"]
  return max(span[0], 0.0) * max(span[1], 0.0) * max(span[2], 0.0)


def _bounds_center_distance(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> float:
  return math.sqrt(
    sum(
      (first["center"][index] - second["center"][index]) ** 2 for index in range(3)
    )
  )


def _contains_point(bounds: dict[str, list[float]], point: list[float]) -> bool:
  return all(bounds["min"][index] <= point[index] <= bounds["max"][index] for index in range(3))


def _bounds_containment_fraction(
  inner: dict[str, list[float]], outer: dict[str, list[float]]
) -> float:
  intersection = _intersection_bounds(inner, outer)
  if intersection is None:
    return 0.0
  return _volume(intersection) / max(_volume(inner), 1e-9)


def _outside_fraction(
  inner: dict[str, list[float]], outer: dict[str, list[float]]
) -> float:
  return min(max(1.0 - _bounds_containment_fraction(inner, outer), 0.0), 1.0)


def _intersection_bounds(
  first: dict[str, list[float]], second: dict[str, list[float]]
) -> dict[str, list[float]] | None:
  minimum = [max(first["min"][index], second["min"][index]) for index in range(3)]
  maximum = [min(first["max"][index], second["max"][index]) for index in range(3)]
  if any(maximum[index] <= minimum[index] for index in range(3)):
    return None
  return _bounds_from_min_max(minimum, maximum)


def _mesh_node_candidates(
  manifest: dict[str, Any],
  region_bounds: dict[str, list[float]],
  *,
  limit: int = 6,
) -> list[dict[str, Any]]:
  asset_center = manifest["gltf_summary"]["transformed_bounds"]["center"]
  scale = float(manifest["public_dimension_check"]["registry_scale"])
  scored: list[dict[str, Any]] = []
  region_volume = max(_volume(region_bounds), 1e-9)
  for mesh_node in manifest["gltf_summary"]["mesh_node_bounds"]:
    sim_bounds = _sim_bounds_from_asset_bounds(
      mesh_node["bounds"], asset_center=asset_center, scale=scale
    )
    intersection = _intersection_bounds(region_bounds, sim_bounds)
    if intersection is None:
      continue
    intersection_volume = _volume(intersection)
    node_volume = max(_volume(sim_bounds), 1e-9)
    scored.append(
      {
        "node_name": mesh_node["node_name"],
        "mesh_name": mesh_node["mesh_name"],
        "triangle_count": mesh_node["triangle_count"],
        "coverage_fraction_of_region_box": _round(intersection_volume / region_volume, 5),
        "coverage_fraction_of_node_box": _round(intersection_volume / node_volume, 5),
        "sim_bounds": sim_bounds,
      }
    )
  scored.sort(
    key=lambda row: (
      row["coverage_fraction_of_node_box"],
      row["coverage_fraction_of_region_box"],
      row["triangle_count"],
    ),
    reverse=True,
  )
  return scored[:limit]


def _region_record(
  *,
  region_id: str,
  label: str,
  role: str,
  minimum: list[float],
  maximum: list[float],
  rationale: str,
  manifest: dict[str, Any],
  mesh_silhouette_source_nodes: list[str] | None = None,
  source_basis: str = "scaled_outer_envelope_fraction_plus_manual_review_seed",
) -> dict[str, Any]:
  bounds = _bounds_from_min_max(minimum, maximum)
  record: dict[str, Any] = {
    "id": region_id,
    "label": label,
    "role": role,
    "bounds_kind": "review_aabb_sim_m",
    "bounds": bounds,
    "source_basis": source_basis,
    "source_mesh_node_candidates": _mesh_node_candidates(manifest, bounds),
    "confidence": "low_initial_review_candidate",
    "manual_review_required": True,
    "rationale": rationale,
  }
  if mesh_silhouette_source_nodes:
    record["mesh_silhouette_source_nodes"] = mesh_silhouette_source_nodes
  return record


def _outer_region_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
  dims = manifest["public_dimension_check"]["scaled_review_dimensions"]
  half_length = float(dims["length_m"]) / 2.0
  half_width = float(dims["wingspan_m"]) / 2.0
  half_height = float(dims["height_m"]) / 2.0
  fuselage_half_width = min(0.85, half_width * 0.18)
  nose_half_width = min(0.48, half_width * 0.10)
  source_nodes = CURATED_MESH_SILHOUETTE_SOURCE_NODES
  mesh_aligned_source = "curated_audit_mesh_node_bounds_plus_manual_review_margin"
  nose_bounds = _bounds_from_min_max(
    [0.67 * half_length, -nose_half_width, -0.42 * half_height],
    [half_length, nose_half_width, -0.15 * half_height],
  )
  canopy_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["canopy"],
    margins_m=[0.05, 0.06, 0.05],
  )
  intake_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["intake"],
    margins_m=[0.08, 0.07, 0.08],
  )
  aft_engine_bounds = _bounds_from_min_max(
    [-0.78 * half_length, -0.90, -0.54 * half_height],
    [-0.20 * half_length, 0.90, 0.15 * half_height],
  )
  engine_nozzle_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["engine_nozzle"],
    margins_m=[0.10, 0.06, 0.10],
  )
  left_wing_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["left_wing"],
    margins_m=[0.07, 0.17, 0.04],
  )
  right_wing_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["right_wing"],
    margins_m=[0.07, 0.17, 0.04],
  )
  left_wing_root_bounds = _bounds_from_min_max(
    [-0.38 * half_length, -1.45, -0.48 * half_height],
    [0.09 * half_length, -0.25, -0.13 * half_height],
  )
  right_wing_root_bounds = _bounds_from_min_max(
    [-0.38 * half_length, 0.25, -0.48 * half_height],
    [0.09 * half_length, 1.45, -0.13 * half_height],
  )
  left_horizontal_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["left_horizontal_tail"],
    margins_m=[0.07, 0.07, 0.05],
  )
  right_horizontal_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["right_horizontal_tail"],
    margins_m=[0.07, 0.07, 0.05],
  )
  vertical_tail_bounds = _curated_mesh_bounds(
    manifest,
    node_names=source_nodes["vertical_tail"],
    margins_m=[0.03, 0.33, 0.08],
  )

  return [
    _region_record(
      region_id="nose_radome",
      label="nose_radome",
      role="outer_skin",
      minimum=nose_bounds["min"],
      maximum=nose_bounds["max"],
      rationale="Forward-most narrow body area; height corrected from audit mesh nose slice instead of expanded selection.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["nose_radome"],
      source_basis="audit_mesh_aligned_nose_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="forward_fuselage",
      label="forward_fuselage",
      role="outer_skin",
      minimum=[0.30 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.72 * half_length, fuselage_half_width, 0.36 * half_height],
      rationale="Forward fuselage and avionics/cockpit support area; covers the old 4 m/6 m nose test zone.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["forward_fuselage"],
    ),
    _region_record(
      region_id="canopy",
      label="canopy",
      role="raised_outer_skin",
      minimum=canopy_bounds["min"],
      maximum=canopy_bounds["max"],
      rationale="Canopy candidate aligned to the audit mesh canopy nodes; kept separate because old hitboxes understate shape.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["canopy"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="center_fuselage",
      label="center_fuselage",
      role="outer_skin",
      minimum=[-0.25 * half_length, -fuselage_half_width, -0.34 * half_height],
      maximum=[0.32 * half_length, fuselage_half_width, 0.34 * half_height],
      rationale="Main body core around fuel, avionics, and flight-control components.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["center_fuselage"],
    ),
    _region_record(
      region_id="intake",
      label="intake",
      role="outer_skin",
      minimum=intake_bounds["min"],
      maximum=intake_bounds["max"],
      rationale="Lower intake candidate aligned to the audit mesh intake nodes for underside proximity review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["intake"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="aft_fuselage_engine",
      label="aft_fuselage_engine",
      role="outer_skin",
      minimum=aft_engine_bounds["min"],
      maximum=aft_engine_bounds["max"],
      rationale="Aft fuselage and engine bay candidate for tail-aspect blast/fragment review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["aft_fuselage_engine"],
      source_basis="audit_mesh_aligned_aft_body_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="engine_nozzle",
      label="engine_nozzle",
      role="outer_skin",
      minimum=engine_nozzle_bounds["min"],
      maximum=engine_nozzle_bounds["max"],
      rationale="Rear nozzle candidate aligned to the audit mesh nozzle node for tail-on shot diagnostics.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["engine_nozzle"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="left_wing",
      label="left_wing",
      role="lifting_surface",
      minimum=left_wing_bounds["min"],
      maximum=left_wing_bounds["max"],
      rationale="Left wing lifting surface aligned to the audit mesh wing nodes; sign naming remains review-only.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_wing"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="right_wing",
      label="right_wing",
      role="lifting_surface",
      minimum=right_wing_bounds["min"],
      maximum=right_wing_bounds["max"],
      rationale="Right wing lifting surface aligned to the audit mesh wing nodes; sign naming remains review-only.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_wing"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="left_wing_root",
      label="left_wing_root",
      role="structural_transition",
      minimum=left_wing_root_bounds["min"],
      maximum=left_wing_root_bounds["max"],
      rationale="Left wing root transition corrected toward the audit mesh wing plane; useful for grazing-warhead review.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_wing_root"],
      source_basis="audit_mesh_aligned_wing_root_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="right_wing_root",
      label="right_wing_root",
      role="structural_transition",
      minimum=right_wing_root_bounds["min"],
      maximum=right_wing_root_bounds["max"],
      rationale="Right wing root transition corrected toward the audit mesh wing plane; mirrored from left wing root candidate.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_wing_root"],
      source_basis="audit_mesh_aligned_wing_root_slice_plus_public_length_scale",
    ),
    _region_record(
      region_id="left_horizontal_tail",
      label="left_horizontal_tail",
      role="tail_surface",
      minimum=left_horizontal_tail_bounds["min"],
      maximum=left_horizontal_tail_bounds["max"],
      rationale="Left horizontal tail candidate aligned to audit mesh tail-plane nodes for aft control-surface exposure.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["left_horizontal_tail"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="right_horizontal_tail",
      label="right_horizontal_tail",
      role="tail_surface",
      minimum=right_horizontal_tail_bounds["min"],
      maximum=right_horizontal_tail_bounds["max"],
      rationale="Right horizontal tail candidate aligned to audit mesh tail-plane nodes for aft control-surface exposure.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["right_horizontal_tail"],
      source_basis=mesh_aligned_source,
    ),
    _region_record(
      region_id="vertical_tail",
      label="vertical_tail",
      role="tail_surface",
      minimum=vertical_tail_bounds["min"],
      maximum=vertical_tail_bounds["max"],
      rationale="Vertical tail candidate; separated because old damage boxes omit most aircraft height.",
      manifest=manifest,
      mesh_silhouette_source_nodes=source_nodes["vertical_tail"],
      source_basis=mesh_aligned_source,
    ),
  ]


def build_geometry_mapping_candidate(manifest: dict[str, Any]) -> dict[str, Any]:
  regions = _outer_region_records(manifest)
  return {
    "schema_version": MAPPING_SCHEMA_VERSION,
    "status": "outer_region_candidate_generated_review_only",
    "generated_on": manifest["generated_on"],
    "asset_ref": {
      "source_uid": manifest["source"]["uid"],
      "runtime_visual_glb": manifest["paths"]["runtime_visual_glb"],
      "audit_scene_gltf": manifest["paths"]["audit_scene_gltf"],
      "manifest_schema_version": manifest["schema_version"],
    },
    "coordinate_frame": {
      "frame": "sim_local_m_review",
      "x_positive": "nose_forward",
      "y_positive": "right_or_left_by_project_sign_review_only",
      "z_positive": "up",
      "source_axis_map": manifest["axis_alignment"],
      "origin": "center_of_audit_asset_transformed_bounds_after_registry_scale",
    },
    "outer_envelope": {
      "bounds_kind": "review_aabb_sim_m",
      "bounds": _sim_bounds_from_asset_bounds(
        manifest["gltf_summary"]["transformed_bounds"],
        asset_center=manifest["gltf_summary"]["transformed_bounds"]["center"],
        scale=float(manifest["public_dimension_check"]["registry_scale"]),
      ),
      "scaled_review_dimensions": manifest["public_dimension_check"][
        "scaled_review_dimensions"
      ],
    },
    "mesh_node_name_quality": {
      "actual_scene_node_pattern": "generic_Object_nodes",
      "semantic_hints_from_intake_metadata": manifest["source_geometry_hints"][
        "metadata_notable_node_names"
      ],
      "decision": "do_not_auto_classify_regions_from_node_names_only",
    },
    "outer_regions": regions,
    "legacy_damage_geometry_overlay": manifest["current_damage_geometry"]["summary"],
    "manual_review_queue": [
      {
        "question": "Do the generated nose and forward-fuselage regions cover the 4 m and 6 m nose test points without creating a hard edge?",
        "priority": "high",
      },
      {
        "question": "Do canopy, intake, and vertical-tail regions correct the legacy hitbox height gap without overstating true internal component boundaries?",
        "priority": "high",
      },
      {
        "question": "Are left/right wing signs aligned with the runtime local-coordinate convention before component binding?",
        "priority": "medium",
      },
    ],
    "authority_boundary": manifest["authority_boundary"],
  }


def _iter_damage_components(aircraft: dict[str, Any]) -> Iterable[dict[str, Any]]:
  for hitbox_index, hitbox in enumerate(aircraft.get("damage_model", {}).get("hitboxes", [])):
    hitbox_bounds = _box_from_center_size(
      [float(value) for value in hitbox["offset"]],
      [float(value) for value in hitbox["size"]],
    )
    for component in hitbox.get("components", []):
      component_bounds = _box_from_center_size(
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
  component_volume = max(_volume(component_bounds), 1e-9)
  ranked: list[dict[str, Any]] = []
  for region in regions:
    region_bounds = region["bounds"]
    intersection = _intersection_bounds(component_bounds, region_bounds)
    overlap_volume = 0.0 if intersection is None else _volume(intersection)
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "component_overlap_fraction": _round(overlap_volume / component_volume, 5),
        "region_overlap_fraction": _round(overlap_volume / max(_volume(region_bounds), 1e-9), 5),
        "center_inside_region": _contains_point(region_bounds, component_bounds["center"]),
        "center_distance_m": _round(_bounds_center_distance(component_bounds, region_bounds)),
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
  envelope_fraction = _bounds_containment_fraction(component_bounds, outer_envelope)
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
          _bounds_containment_fraction(component_bounds, outer_envelope), 5
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


def _point_box_distance(point: list[float], bounds: dict[str, list[float]]) -> float:
  squared = 0.0
  for axis in range(3):
    value = point[axis]
    if value < bounds["min"][axis]:
      squared += (bounds["min"][axis] - value) ** 2
    elif value > bounds["max"][axis]:
      squared += (value - bounds["max"][axis]) ** 2
  return math.sqrt(squared)


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
    distance = _point_box_distance(point, region["bounds"])
    ranked.append(
      {
        "region_id": region["id"],
        "region_role": region["role"],
        "distance_m": _round(distance),
        "contains_point": _contains_point(region["bounds"], point),
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
    distance = _point_box_distance(point, row["component_bounds"])
    ranked.append(
      {
        "component_name": row["component_name"],
        "system": row["system"],
        "critical": row["critical"],
        "bound_region_id": row["bound_region_id"],
        "distance_m": _round(distance),
        "contains_point": _contains_point(row["component_bounds"], point),
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


def _resize_bounds_about_center(
  bounds: dict[str, list[float]],
  factors: list[float],
) -> dict[str, list[float]]:
  center = bounds["center"]
  span = bounds["span"]
  minimum = [
    center[index] - span[index] * factors[index] / 2.0 for index in range(3)
  ]
  maximum = [
    center[index] + span[index] * factors[index] / 2.0 for index in range(3)
  ]
  return _bounds_from_min_max(minimum, maximum)


def _bounds_corners(bounds: dict[str, list[float]]) -> list[list[float]]:
  return [
    _round_vec([x, y, z])
    for x in (bounds["min"][0], bounds["max"][0])
    for y in (bounds["min"][1], bounds["max"][1])
    for z in (bounds["min"][2], bounds["max"][2])
  ]


def _cross_2d(
  origin: tuple[float, float],
  first: tuple[float, float],
  second: tuple[float, float],
) -> float:
  return (
    (first[0] - origin[0]) * (second[1] - origin[1])
    - (first[1] - origin[1]) * (second[0] - origin[0])
  )


def _convex_hull_2d(points: Iterable[tuple[float, float]]) -> list[list[float]]:
  unique = sorted({(_round(point[0]), _round(point[1])) for point in points})
  if len(unique) <= 2:
    return [[point[0], point[1]] for point in unique]

  lower: list[tuple[float, float]] = []
  for point in unique:
    while len(lower) >= 2 and _cross_2d(lower[-2], lower[-1], point) <= 0.0:
      lower.pop()
    lower.append(point)

  upper: list[tuple[float, float]] = []
  for point in reversed(unique):
    while len(upper) >= 2 and _cross_2d(upper[-2], upper[-1], point) <= 0.0:
      upper.pop()
    upper.append(point)

  hull = lower[:-1] + upper[:-1]
  return [[point[0], point[1]] for point in hull]


def _mesh_silhouette_for_region(
  region: dict[str, Any],
  sim_vertex_records: list[dict[str, Any]],
) -> dict[str, Any]:
  source_node_names = set(region.get("mesh_silhouette_source_nodes", []))
  candidate_records = [
    record
    for record in sim_vertex_records
    if not source_node_names or record["node_name"] in source_node_names
  ]
  selection_bounds = region["bounds"]
  selected_records = [
    record
    for record in candidate_records
    if _contains_point(selection_bounds, record["point_m"])
  ]
  selected = [record["point_m"] for record in selected_records]
  hulls: dict[str, Any] = {}
  for view, axes in SILHOUETTE_VIEW_AXES.items():
    projected = [(vertex[axes[0]], vertex[axes[1]]) for vertex in selected]
    hull = _convex_hull_2d(projected)
    hulls[view] = {
      "axes": ["xyz"[axes[0]], "xyz"[axes[1]]],
      "point_count": len(hull),
      "points_m": hull,
    }

  status = "mesh_silhouette_extracted_from_curated_mesh_nodes"
  if not source_node_names:
    status = "mesh_silhouette_extracted_from_region_bounds"
  if len(selected) < 3 or any(hull["point_count"] < 3 for hull in hulls.values()):
    status = "insufficient_region_vertices_for_closed_silhouette"
  node_counts: dict[str, int] = {}
  for record in selected_records:
    node_counts[record["node_name"]] = node_counts.get(record["node_name"], 0) + 1
  return {
    "status": status,
    "source": "audit_gltf_vertices_filtered_by_curated_mesh_nodes_and_region_bounds",
    "source_vertex_count": len(sim_vertex_records),
    "candidate_vertex_count": len(candidate_records),
    "region_vertex_count": len(selected),
    "selection_strategy": "curated_mesh_node_whitelist_and_source_region_bounds",
    "fallback_policy": "disabled_no_bounds_expansion",
    "source_node_names": sorted(source_node_names),
    "selected_node_vertex_counts": dict(sorted(node_counts.items())),
    "selection_bounds": selection_bounds,
    "hulls": hulls,
  }


def _fine_proxy_support_bounds(region: dict[str, Any], proxy_kind: str) -> dict[str, list[float]]:
  region_id = region["id"]
  bounds = region["bounds"]
  if proxy_kind == "thin_prism":
    if region_id == "vertical_tail":
      return _resize_bounds_about_center(bounds, [0.90, 0.24, 0.96])
    return _resize_bounds_about_center(bounds, [0.94, 0.88, 0.36])
  if proxy_kind == "convex_hull":
    factors_by_region = {
      "nose_radome": [0.92, 0.58, 0.72],
      "canopy": [0.82, 0.76, 0.82],
      "intake": [0.84, 0.70, 0.76],
      "left_wing_root": [0.84, 0.72, 0.72],
      "right_wing_root": [0.84, 0.72, 0.72],
    }
    return _resize_bounds_about_center(
      bounds,
      factors_by_region.get(region_id, [0.86, 0.70, 0.74]),
    )
  if region_id == "engine_nozzle":
    return _resize_bounds_about_center(bounds, [0.90, 0.78, 0.84])
  return _resize_bounds_about_center(bounds, [0.96, 0.88, 0.88])


def _convex_proxy_vertices(
  region_id: str,
  support_bounds: dict[str, list[float]],
) -> list[list[float]]:
  bounds = support_bounds
  min_x, min_y, min_z = bounds["min"]
  max_x, max_y, max_z = bounds["max"]
  center = bounds["center"]
  if region_id == "nose_radome":
    return [
      _round_vec([max_x, center[1], center[2]]),
      _round_vec([min_x, min_y, min_z]),
      _round_vec([min_x, min_y, max_z]),
      _round_vec([min_x, max_y, min_z]),
      _round_vec([min_x, max_y, max_z]),
      _round_vec([(min_x + max_x) / 2.0, center[1], min_z]),
      _round_vec([(min_x + max_x) / 2.0, center[1], max_z]),
    ]
  if region_id == "canopy":
    return [
      _round_vec([min_x, min_y, min_z]),
      _round_vec([min_x, max_y, min_z]),
      _round_vec([max_x, min_y, min_z]),
      _round_vec([max_x, max_y, min_z]),
      _round_vec([min_x + (max_x - min_x) * 0.35, center[1], max_z]),
      _round_vec([min_x + (max_x - min_x) * 0.75, center[1], max_z * 0.98]),
    ]
  return _bounds_corners(bounds)


def _fine_proxy_record(
  region: dict[str, Any],
  *,
  sim_vertex_records: list[dict[str, Any]],
) -> dict[str, Any]:
  region_id = region["id"]
  proxy_kind = FINE_PROXY_KIND_BY_REGION.get(region_id, "obb")
  source_bounds = region["bounds"]
  support_bounds = _fine_proxy_support_bounds(region, proxy_kind)
  support_span = support_bounds["span"]
  source_volume = _volume(source_bounds)
  support_volume = _volume(support_bounds)
  record: dict[str, Any] = {
    "source_region_id": region_id,
    "source_region_role": region["role"],
    "proxy_kind": proxy_kind,
    "source_basis": "review_mapping_plus_audit_mesh_silhouette_candidate",
    "source_region_bounds": source_bounds,
    "support_bounds": support_bounds,
    "mesh_derived_review_geometry": _mesh_silhouette_for_region(
      region, sim_vertex_records
    ),
    "vertices_m": (
      _convex_proxy_vertices(region_id, support_bounds)
      if proxy_kind == "convex_hull"
      else _bounds_corners(support_bounds)
    ),
    "fit_metrics": {
      "source_aabb_volume_m3": _round(source_volume),
      "proxy_support_volume_m3": _round(support_volume),
      "aabb_volume_ratio": _round(support_volume / max(source_volume, 1e-9), 5),
      "max_support_surface_inset_m": _round(
        max(
          (source_bounds["span"][axis] - support_span[axis]) / 2.0
          for axis in range(3)
        )
      ),
    },
    "runtime_allowed_use": [
      "distance_diagnostic_candidate",
      "review_visualization_input",
    ],
    "runtime_prohibited_use": [
      "runtime_collision_mesh",
      "real_f16_engineering_geometry",
      "true_internal_component_boundary",
      "real_weapon_pk",
      "structural_breakup_or_debris_claim",
    ],
    "review_status": "manual_review_required",
    "manual_review_notes": [
      "First-pass fine proxy for TG-P6 review only.",
      "Use support_bounds for distance sanity until a later audited hull or shell exists.",
    ],
  }
  if proxy_kind in {"obb", "thin_prism"}:
    record["obb"] = {
      "center_m": support_bounds["center"],
      "axes": [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
      ],
      "half_extents_m": _round_vec([value / 2.0 for value in support_span]),
    }
  if proxy_kind == "thin_prism":
    thin_axis = 1 if region_id == "vertical_tail" else 2
    record["thin_prism"] = {
      "thin_axis": ["x", "y", "z"][thin_axis],
      "nominal_thickness_m": _round(support_span[thin_axis]),
      "thickness_basis": "review_candidate_reduces_air_volume_from_outer_region_aabb",
    }
  if proxy_kind == "convex_hull":
    record["convex_hull"] = {
      "vertex_source": "simplified_review_support_points_not_raw_mesh_vertices",
      "vertex_count": len(record["vertices_m"]),
      "simplification_error_m": None,
    }
  if "wing" in region_id or "tail" in region_id:
    record["manual_review_notes"].append(
      "Left/right coordinate sign and thin-surface orientation remain explicit review items."
    )
  if region.get("mesh_silhouette_source_nodes"):
    record["manual_review_notes"].append(
      "Mesh-derived silhouette uses a curated audit-node whitelist; missing nodes fail review instead of using expanded bounds."
    )
  return record


def _rank_point_to_fine_proxies(
  point: list[float],
  fine_proxy: dict[str, Any],
) -> list[dict[str, Any]]:
  ranked: list[dict[str, Any]] = []
  for proxy in fine_proxy["proxies"]:
    distance = _point_box_distance(point, proxy["support_bounds"])
    ranked.append(
      {
        "source_region_id": proxy["source_region_id"],
        "proxy_kind": proxy["proxy_kind"],
        "distance_m": _round(distance),
        "contains_point": _contains_point(proxy["support_bounds"], point),
        "source_aabb_distance_m": _round(
          _point_box_distance(point, proxy["source_region_bounds"])
        ),
      }
    )
  ranked.sort(
    key=lambda row: (
      row["distance_m"],
      row["source_aabb_distance_m"],
      row["source_region_id"],
    )
  )
  return ranked


def build_fine_geometry_proxy_candidate(
  mapping: dict[str, Any],
  diagnostics: dict[str, Any],
  *,
  manifest: dict[str, Any] | None = None,
  audit_scene_path: Path | None = None,
) -> dict[str, Any]:
  sim_vertex_records: list[dict[str, Any]] = []
  if manifest is not None:
    if audit_scene_path is None:
      audit_scene_path = REPO_ROOT / manifest["paths"]["audit_scene_gltf"]
    sim_vertex_records = extract_gltf_sim_vertex_records(audit_scene_path, manifest)
  proxies = [
    _fine_proxy_record(region, sim_vertex_records=sim_vertex_records)
    for region in mapping["outer_regions"]
  ]
  fine_proxy: dict[str, Any] = {
    "schema_version": FINE_PROXY_SCHEMA_VERSION,
    "status": "fine_geometry_proxy_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "outer_envelope": mapping["outer_envelope"],
    "source_mapping_schema_version": mapping["schema_version"],
    "proxies": proxies,
    "review_point_distance_deltas": [],
  }
  distance_rows: list[dict[str, Any]] = []
  for row in diagnostics["rows"]:
    point = [float(value) for value in row["point_m"]]
    rankings = _rank_point_to_fine_proxies(point, fine_proxy)
    nearest = rankings[0]
    distance_rows.append(
      {
        "point_id": row["point_id"],
        "aspect": row["aspect"],
        "point_m": row["point_m"],
        "nearest_source_aabb_region_id": row["nearest_outer_region_id"],
        "nearest_source_aabb_distance_m": row["nearest_outer_distance_m"],
        "nearest_fine_proxy_region_id": nearest["source_region_id"],
        "nearest_fine_proxy_kind": nearest["proxy_kind"],
        "nearest_fine_proxy_distance_m": nearest["distance_m"],
        "fine_minus_source_distance_delta_m": _round(
          nearest["distance_m"] - row["nearest_outer_distance_m"]
        ),
        "inside_fine_proxy_count": sum(1 for item in rankings if item["contains_point"]),
        "fine_proxy_rankings": rankings[:5],
        "authority_boundary": "review_only_distance_sanity_not_runtime_lethality_decision",
      }
    )
  kind_counts: dict[str, int] = {}
  for proxy in proxies:
    kind_counts[proxy["proxy_kind"]] = kind_counts.get(proxy["proxy_kind"], 0) + 1
  source_volume = sum(_volume(proxy["source_region_bounds"]) for proxy in proxies)
  support_volume = sum(_volume(proxy["support_bounds"]) for proxy in proxies)
  mesh_silhouette_count = sum(
    1
    for proxy in proxies
    if proxy["mesh_derived_review_geometry"]["status"].startswith(
      "mesh_silhouette_extracted"
    )
  )
  fine_proxy["summary"] = {
    "source_outer_region_count": len(mapping["outer_regions"]),
    "proxy_count": len(proxies),
    "held_region_count": len(proxies) - mesh_silhouette_count,
    "mesh_derived_silhouette_count": mesh_silhouette_count,
    "mesh_source_vertex_count": len(sim_vertex_records),
    "inflated_fallback_count": 0,
    "fallback_policy": "disabled_no_bounds_expansion",
    "proxy_kind_counts": kind_counts,
    "total_source_aabb_volume_m3": _round(source_volume),
    "total_proxy_support_volume_m3": _round(support_volume),
    "total_proxy_support_volume_ratio": _round(
      support_volume / max(source_volume, 1e-9),
      5,
    ),
    "review_point_count": len(distance_rows),
    "review_status": "manual_review_required",
  }
  fine_proxy["review_point_distance_deltas"] = distance_rows
  fine_proxy["manual_review_queue"] = [
    {
      "priority": "high",
      "question": "Confirm thin wing and tail proxies do not hide left/right coordinate sign issues.",
    },
    {
      "priority": "high",
      "question": "Review nose, canopy, and intake convex-hull candidates before any path intersection use.",
    },
    {
      "priority": "medium",
      "question": "Compare fine-minus-source distance deltas for nose, beam, above, and below points.",
    },
  ]
  fine_proxy["authority_boundary"] = mapping["authority_boundary"]
  return fine_proxy


def _surface_rule_for_region(region: dict[str, Any]) -> dict[str, Any]:
  rule = SURFACE_COMPONENT_RULES.get(region["id"])
  if rule is not None:
    return rule
  return {
    "surface_component_id": f'surface_{region["id"]}',
    "surface_role": region["role"],
    "expected_damage_modes": ["perforation", "skin_tearing"],
    "expected_internal_components": [],
    "missing_existing_runtime_component_relations": [],
  }


def _candidate_region_rank(
  component_row: dict[str, Any],
  region_id: str,
) -> dict[str, Any] | None:
  for rank, candidate in enumerate(component_row["candidate_regions"], start=1):
    if candidate["region_id"] == region_id:
      return {
        "rank": rank,
        "component_overlap_fraction": candidate["component_overlap_fraction"],
        "region_overlap_fraction": candidate["region_overlap_fraction"],
        "center_inside_region": candidate["center_inside_region"],
        "center_distance_m": candidate["center_distance_m"],
      }
  return None


def _surface_component_link_record(
  *,
  region_id: str,
  component_row: dict[str, Any],
  expected_component_names: set[str],
) -> dict[str, Any]:
  relations: list[str] = []
  blocked_binding = (
    component_row["blocked_region_binding"]["blocked"]
    and component_row["blocked_region_binding"]["blocked_region_id"] == region_id
  )
  if component_row["bound_region_id"] == region_id and blocked_binding:
    relations.append("blocked_invalid_region_binding")
  elif component_row["bound_region_id"] == region_id:
    relations.append("bound_to_this_outer_region")
  if component_row["component_name"] in expected_component_names:
    relations.append("expected_surface_effect_path")
  candidate_rank = _candidate_region_rank(component_row, region_id)
  if candidate_rank is not None:
    relations.append("ranked_region_candidate")
  if not relations:
    relations.append("nearby_review_candidate")
  return {
    "component_name": component_row["component_name"],
    "system": component_row["system"],
    "critical": component_row["critical"],
    "relations": relations,
    "bound_region_id": component_row["bound_region_id"],
    "component_review_status": component_row["review_status"],
    "component_review_semantics": component_row["review_semantics"],
    "component_review_severity": component_row["review_severity"],
    "component_overlap_fraction": component_row["component_overlap_fraction"],
    "center_distance_m": component_row["center_distance_m"],
    "candidate_region_rank": candidate_rank,
    "anomalies": component_row["anomalies"],
    "geometry_observations": component_row["geometry_observations"],
    "suppressed_anomalies": component_row["suppressed_anomalies"],
    "semantic_region_ids": component_row["semantic_region_ids"],
    "side_sign_relation": component_row["side_sign_relation"],
    "blocked_region_binding": component_row["blocked_region_binding"],
    "review_notes": component_row["review_notes"],
  }


def _surface_component_review_flags(
  *,
  geometry: dict[str, Any],
  links: list[dict[str, Any]],
  missing_existing_runtime_component_relations: list[str],
) -> list[str]:
  flags: list[str] = []
  if not geometry.get("status", "").startswith("mesh_silhouette_extracted"):
    flags.append("mesh_silhouette_needs_review")
  if not links:
    flags.append("no_internal_component_link")
  if missing_existing_runtime_component_relations:
    flags.append("missing_existing_runtime_component_relation")
    flags.append("missing_runtime_link/held")
  if any(link["component_review_status"] == "needs_review" for link in links):
    flags.append("linked_component_needs_review")
  if any(
    link["component_review_semantics"] in GEOMETRY_REVIEW_SEMANTICS
    for link in links
  ):
    flags.append("linked_component_geometry_needs_review")
  if any(
    link["component_review_semantics"] == "invalid_region_binding_blocked"
    for link in links
  ):
    flags.append("invalid_region_binding_blocked")
  if any(
    link["component_review_semantics"] == "cross_region_boundary_candidate_review_only"
    for link in links
  ):
    flags.append("cross_region_boundary_candidate_review_only")
  if any(
    link["component_review_semantics"] == "cross_region_structural_semantic_hold"
    for link in links
  ):
    flags.append("cross_region_semantic_hold")
  if any(
    link["component_review_semantics"] == "side_sign_mismatch_hard_blocker"
    for link in links
  ):
    flags.append("side_sign_review")
    flags.append("side_sign_mismatch_hard_blocker")
  if any(
    "expected_surface_effect_path" in link["relations"]
    and link["bound_region_id"] != link.get("source_region_id", "")
    for link in links
  ):
    flags.append("expected_component_bound_elsewhere")
  if not any("bound_to_this_outer_region" in link["relations"] for link in links):
    flags.append("no_direct_component_bound_to_surface_region")
  if not flags:
    flags.append("candidate_surface_component")
  return flags


def _surface_component_review_status(flags: list[str]) -> str:
  hard_flags = {
    "missing_runtime_link/held",
    "side_sign_mismatch_hard_blocker",
    "invalid_region_binding_blocked",
    "linked_component_geometry_needs_review",
    "mesh_silhouette_needs_review",
    "no_internal_component_link",
  }
  if any(flag in hard_flags for flag in flags):
    return "needs_human_review"
  if "cross_region_semantic_hold" in flags:
    return "review_only_cross_region_semantic_hold"
  if "cross_region_boundary_candidate_review_only" in flags:
    return "review_only_cross_region_boundary_candidate"
  if flags == ["candidate_surface_component"]:
    return "candidate_surface_component"
  return "needs_human_review"


def _surface_component_review_semantics(flags: list[str]) -> str:
  if "missing_runtime_link/held" in flags:
    return "missing_runtime_link/held"
  if "side_sign_mismatch_hard_blocker" in flags:
    return "side_sign_mismatch_hard_blocker"
  if "invalid_region_binding_blocked" in flags:
    return "invalid_region_binding_blocked"
  if "linked_component_geometry_needs_review" in flags:
    return "linked_component_geometry_needs_review"
  if "cross_region_semantic_hold" in flags:
    return "cross_region_semantic_hold"
  if "cross_region_boundary_candidate_review_only" in flags:
    return "cross_region_boundary_candidate_review_only"
  return "candidate_surface_component"


def build_surface_component_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
) -> dict[str, Any]:
  regions_by_id = {region["id"]: region for region in mapping["outer_regions"]}
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = {
    row["component_name"]: row for row in component_report["rows"]
  }
  rows: list[dict[str, Any]] = []
  for region_id in regions_by_id:
    region = regions_by_id[region_id]
    proxy = proxies_by_region[region_id]
    rule = _surface_rule_for_region(region)
    expected_names = set(rule["expected_internal_components"])
    direct_names = {
      row["component_name"]
      for row in component_report["rows"]
      if row["bound_region_id"] == region_id
    }
    linked_names = sorted(direct_names | expected_names)
    missing_expected_component_names = [
      name for name in sorted(expected_names) if name not in rows_by_component
    ]
    links = [
      _surface_component_link_record(
        region_id=region_id,
        component_row=rows_by_component[name],
        expected_component_names=expected_names,
      )
      for name in linked_names
      if name in rows_by_component
    ]
    for link in links:
      link["source_region_id"] = region_id
    missing_relations = list(rule["missing_existing_runtime_component_relations"])
    flags = _surface_component_review_flags(
      geometry=proxy["mesh_derived_review_geometry"],
      links=links,
      missing_existing_runtime_component_relations=missing_relations,
    )
    review_status = _surface_component_review_status(flags)
    review_semantics = _surface_component_review_semantics(flags)
    clean_link_count = sum(
      1
      for link in links
      if link["component_review_status"] == "candidate_binding"
      and "bound_to_this_outer_region" in link["relations"]
    )
    clean_direct_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_status"] == "candidate_binding"
      and "bound_to_this_outer_region" in link["relations"]
    ]
    cross_region_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
    ]
    blocked_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in HARD_BLOCKER_REVIEW_SEMANTICS
    ]
    bad_geometry_component_names = [
      link["component_name"]
      for link in links
      if link["component_review_semantics"] in GEOMETRY_REVIEW_SEMANTICS
    ]
    runtime_relation_status = (
      "missing_runtime_link/held"
      if missing_relations
      else "runtime_relation_review_only_candidate"
    )
    rows.append(
      {
        "surface_component_id": rule["surface_component_id"],
        "source_region_id": region_id,
        "source_region_role": region["role"],
        "surface_role": rule["surface_role"],
        "source_region_bounds": region["bounds"],
        "support_bounds": proxy["support_bounds"],
        "proxy_kind": proxy["proxy_kind"],
        "mesh_source_nodes": proxy["mesh_derived_review_geometry"][
          "source_node_names"
        ],
        "mesh_region_vertex_count": proxy["mesh_derived_review_geometry"][
          "region_vertex_count"
        ],
        "expected_damage_modes": rule["expected_damage_modes"],
        "linked_internal_components": links,
        "linked_internal_component_count": len(links),
        "clean_direct_link_count": clean_link_count,
        "clean_direct_component_names": clean_direct_component_names,
        "cross_region_semantic_component_names": cross_region_component_names,
        "blocked_component_names": blocked_component_names,
        "bad_geometry_component_names": bad_geometry_component_names,
        "missing_expected_component_names": missing_expected_component_names,
        "missing_existing_runtime_component_relations": missing_relations,
        "runtime_relation_status": runtime_relation_status,
        "review_flags": flags,
        "review_status": review_status,
        "review_semantics": review_semantics,
        "authority_boundary": (
          "review_only_surface_component_candidate_not_runtime_damage_model"
        ),
      }
    )

  needs_review = [row for row in rows if row["review_status"] == "needs_human_review"]
  return {
    "schema_version": SURFACE_COMPONENT_SCHEMA_VERSION,
    "status": "surface_component_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_mapping_schema_version": mapping["schema_version"],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "surface_component_count": len(rows),
      "needs_review_count": len(needs_review),
      "missing_existing_runtime_component_relation_count": sum(
        1
        for row in rows
        if row["missing_existing_runtime_component_relations"]
      ),
      "no_direct_component_bound_count": sum(
        1
        for row in rows
        if "no_direct_component_bound_to_surface_region" in row["review_flags"]
      ),
      "linked_component_needs_review_count": sum(
        1
        for row in rows
        if "linked_component_needs_review" in row["review_flags"]
      ),
      "missing_runtime_link_held_count": sum(
        1
        for row in rows
        if row["runtime_relation_status"] == "missing_runtime_link/held"
      ),
      "side_sign_hard_blocker_count": sum(
        1
        for row in rows
        if "side_sign_mismatch_hard_blocker" in row["review_flags"]
      ),
      "invalid_region_binding_blocked_count": sum(
        1
        for row in rows
        if "invalid_region_binding_blocked" in row["review_flags"]
      ),
      "cross_region_semantic_hold_count": sum(
        1
        for row in rows
        if row["review_semantics"]
        in {
          "cross_region_semantic_hold",
          "cross_region_boundary_candidate_review_only",
        }
      ),
      "candidate_surface_component_count": sum(
        1
        for row in rows
        if row["review_status"] == "candidate_surface_component"
      ),
      "review_status": "manual_review_required",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review every surface component with old internal components that are drifted or sign-mismatched before runtime use.",
      },
      {
        "priority": "high",
        "question": "Add explicit canopy, intake, and horizontal-tail runtime component links if their surface damage should affect flight or sensors.",
      },
      {
        "priority": "medium",
        "question": "Use this report as the handoff table from outer-shape hits to component-damage propagation.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "true_surface_component_boundaries": False,
    },
  }


def _semantic_damage_volume_rule(region_id: str, surface_role: str) -> dict[str, Any]:
  rule = SEMANTIC_DAMAGE_VOLUME_RULES.get(region_id)
  if rule is not None:
    return rule
  return {
    "semantic_component_id": f"semantic_{region_id}_volume",
    "volume_role": f"{surface_role}_volume",
    "runtime_system": "airframe_skin",
    "armor_mm": 3.0,
    "threshold_scale": 1.0,
  }


def _runtime_geometry_payload(proxy: dict[str, Any]) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "primitive": proxy["proxy_kind"],
    "source": "a2_mesh_proxy_support_volume",
    "source_region_id": proxy["source_region_id"],
    "source_proxy_kind": proxy["proxy_kind"],
    "support_bounds": proxy["support_bounds"],
    "source_region_bounds": proxy["source_region_bounds"],
    "vertices_m": proxy["vertices_m"],
  }
  if "obb" in proxy:
    payload["obb"] = proxy["obb"]
  if "thin_prism" in proxy:
    payload["thin_prism"] = proxy["thin_prism"]
  if "convex_hull" in proxy:
    payload["convex_hull"] = proxy["convex_hull"]
  return payload


def _runtime_component_candidate(
  *,
  rule: dict[str, Any],
  row: dict[str, Any],
  proxy: dict[str, Any],
) -> dict[str, Any]:
  geometry = _runtime_geometry_payload(proxy)
  return {
    "name": rule["semantic_component_id"],
    "system": rule["runtime_system"],
    "offset": proxy["support_bounds"]["center"],
    "size": proxy["support_bounds"]["span"],
    "armor": rule["armor_mm"],
    "threshold_scale": rule["threshold_scale"],
    "geometry_primitive": proxy["proxy_kind"],
    "geometry": {
      **geometry,
      "surface_component_id": row["surface_component_id"],
      "volume_role": rule["volume_role"],
      "direct_receiver_components": row["clean_direct_component_names"],
      "cross_region_receiver_components": row[
        "cross_region_semantic_component_names"
      ],
      "runtime_projection_status": (
        "runtime_schema_parse_ready_candidate_not_activated"
      ),
    },
    "failure_modes": row["expected_damage_modes"],
    "dependencies": [
      {
        "system": rule["runtime_system"],
        "target_system": receiver,
        "edge_type": "semantic_surface_handoff_candidate",
        "scale": 0.35,
        "provenance": (
          "A2 target-geometry semantic volume handoff candidate; "
          "mesh-proxy review geometry, non-authoritative"
        ),
      }
      for receiver in row["clean_direct_component_names"]
    ],
    "redundancy_group_id": rule["semantic_component_id"],
    "redundancy_group": 0.0,
    "redundancy_weight": 0.35,
    "critical": False,
  }


def _semantic_receiver_handoff_status(row: dict[str, Any]) -> str:
  if row["blocked_component_names"] or row["bad_geometry_component_names"]:
    return "blocked_receiver_review_required"
  if row["cross_region_semantic_component_names"]:
    return "direct_receivers_parse_ready_cross_region_receivers_held"
  if row["clean_direct_component_names"]:
    return "direct_receivers_parse_ready"
  return "no_direct_receiver_review_required"


def build_semantic_damage_geometry_candidate(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  surface_report: dict[str, Any],
) -> dict[str, Any]:
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows: list[dict[str, Any]] = []
  for row in surface_report["rows"]:
    region_id = row["source_region_id"]
    proxy = proxies_by_region[region_id]
    rule = _semantic_damage_volume_rule(region_id, row["surface_role"])
    geometry = _runtime_geometry_payload(proxy)
    handoff_status = _semantic_receiver_handoff_status(row)
    rows.append(
      {
        "semantic_component_id": rule["semantic_component_id"],
        "surface_component_id": row["surface_component_id"],
        "source_region_id": region_id,
        "source_region_role": row["source_region_role"],
        "surface_role": row["surface_role"],
        "volume_component_role": rule["volume_role"],
        "runtime_system": rule["runtime_system"],
        "geometry_primitive": proxy["proxy_kind"],
        "source_proxy_kind": proxy["proxy_kind"],
        "support_bounds": proxy["support_bounds"],
        "source_region_bounds": proxy["source_region_bounds"],
        "mesh_source_nodes": row["mesh_source_nodes"],
        "mesh_region_vertex_count": row["mesh_region_vertex_count"],
        "mesh_silhouette_hulls": proxy["mesh_derived_review_geometry"]["hulls"],
        "runtime_geometry": geometry,
        "direct_receiver_components": row["clean_direct_component_names"],
        "direct_receiver_count": len(row["clean_direct_component_names"]),
        "cross_region_receiver_components": row[
          "cross_region_semantic_component_names"
        ],
        "cross_region_receiver_count": len(
          row["cross_region_semantic_component_names"]
        ),
        "blocked_receiver_components": row["blocked_component_names"],
        "bad_geometry_receiver_components": row["bad_geometry_component_names"],
        "expected_damage_modes": row["expected_damage_modes"],
        "surface_review_status": row["review_status"],
        "surface_review_semantics": row["review_semantics"],
        "surface_review_flags": row["review_flags"],
        "receiver_handoff_status": handoff_status,
        "runtime_projection_status": (
          "runtime_schema_parse_ready_candidate_not_activated"
        ),
        "runtime_component_json_candidate": _runtime_component_candidate(
          rule=rule,
          row=row,
          proxy=proxy,
        ),
        "authority_boundary": (
          "semantic_mesh_proxy_volume_candidate_not_active_runtime_damage_model"
        ),
      }
    )

  return {
    "schema_version": SEMANTIC_DAMAGE_GEOMETRY_SCHEMA_VERSION,
    "status": "semantic_damage_geometry_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_mapping_schema_version": mapping["schema_version"],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "source_surface_component_schema_version": surface_report["schema_version"],
    "summary": {
      "semantic_volume_component_count": len(rows),
      "runtime_parse_ready_component_count": len(rows),
      "runtime_active_component_count": 0,
      "direct_receiver_component_reference_count": sum(
        row["direct_receiver_count"] for row in rows
      ),
      "cross_region_receiver_reference_count": sum(
        row["cross_region_receiver_count"] for row in rows
      ),
      "cross_region_handoff_held_count": sum(
        1
        for row in rows
        if row["receiver_handoff_status"]
        == "direct_receivers_parse_ready_cross_region_receivers_held"
      ),
      "blocked_receiver_count": sum(
        len(row["blocked_receiver_components"]) for row in rows
      ),
      "bad_geometry_receiver_count": sum(
        len(row["bad_geometry_receiver_components"]) for row in rows
      ),
      "geometry_primitive_counts": {
        primitive: sum(1 for row in rows if row["geometry_primitive"] == primitive)
        for primitive in sorted({row["geometry_primitive"] for row in rows})
      },
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review each semantic volume page before copying runtime_component_json_candidate into an active unit damage model.",
      },
      {
        "priority": "high",
        "question": "Keep engine_core and wing_spar_center cross-region receiver ownership held until split or explicitly accepted.",
      },
      {
        "priority": "medium",
        "question": "Use runtime_geometry.support_bounds plus primitive/source fields as the first parse-ready handoff from shell geometry to component damage.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_schema_parse_ready_candidate": True,
      "runtime_active_component": False,
      "true_surface_component_boundaries": False,
      "true_internal_component_geometry": False,
    },
  }


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


def _axis_index(axis_name: str | None) -> int:
  return {"x": 0, "y": 1, "z": 2}.get(axis_name or "x", 0)


def _bounds_from_center_half_extents(
  center: list[float],
  half_extents: list[float],
) -> dict[str, list[float]]:
  return _bounds_from_min_max(
    [center[index] - half_extents[index] for index in range(3)],
    [center[index] + half_extents[index] for index in range(3)],
  )


def _shape_half_extents(
  *,
  rule: dict[str, Any],
  component_bounds: dict[str, list[float]],
) -> tuple[list[float], dict[str, Any]]:
  shape = rule["shape"]
  if "dimensions_m" in rule:
    scaled_span = [max(float(value), 0.02) for value in rule["dimensions_m"]]
  else:
    span_scale = rule.get("span_scale", [0.78, 0.78, 0.78])
    scaled_span = [
      max(component_bounds["span"][index] * float(span_scale[index]), 0.02)
      for index in range(3)
    ]
  if shape == "sphere":
    radius = max(min(scaled_span) * 0.5, 0.02)
    return [radius, radius, radius], {
      "shape": "sphere",
      "radius_m": _round(radius),
    }

  if shape in {"cylinder", "capsule"}:
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = max(min(scaled_span[index] for index in radial_axes) * 0.5, 0.02)
    half_extents = [radius, radius, radius]
    if shape == "capsule":
      half_extents[axis] = max(scaled_span[axis] * 0.5, radius)
    else:
      half_extents[axis] = max(scaled_span[axis] * 0.5, 0.01)
    payload = {
      "shape": shape,
      "axis": ["x", "y", "z"][axis],
      "radius_m": _round(radius),
      "axis_half_extent_m": _round(half_extents[axis]),
    }
    if shape == "capsule":
      payload["cylinder_half_length_m"] = _round(
        max(half_extents[axis] - radius, 0.0)
      )
    return half_extents, payload

  half_extents = [value * 0.5 for value in scaled_span]
  if shape == "ellipsoid":
    return half_extents, {
      "shape": "ellipsoid",
      "radii_m": _round_vec(half_extents),
    }
  return half_extents, {
    "shape": "obb",
    "half_extents_m": _round_vec(half_extents),
  }


def _shape_payload_from_half_extents(
  *,
  rule: dict[str, Any],
  half_extents: list[float],
) -> dict[str, Any]:
  shape = rule["shape"]
  if shape == "sphere":
    return {
      "shape": "sphere",
      "radius_m": _round(min(half_extents)),
    }
  if shape in {"cylinder", "capsule"}:
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    payload = {
      "shape": shape,
      "axis": ["x", "y", "z"][axis],
      "radius_m": _round(radius),
      "axis_half_extent_m": _round(half_extents[axis]),
    }
    if shape == "capsule":
      payload["cylinder_half_length_m"] = _round(
        max(half_extents[axis] - radius, 0.0)
      )
    return payload
  if shape == "ellipsoid":
    return {
      "shape": "ellipsoid",
      "radii_m": _round_vec(half_extents),
    }
  return {
    "shape": "obb",
    "half_extents_m": _round_vec(half_extents),
  }


def _shape_volume_m3(rule: dict[str, Any], half_extents: list[float]) -> float:
  shape = rule["shape"]
  if shape == "sphere":
    radius = min(half_extents)
    return 4.0 * math.pi * radius**3 / 3.0
  if shape == "ellipsoid":
    return 4.0 * math.pi * half_extents[0] * half_extents[1] * half_extents[2] / 3.0
  if shape == "cylinder":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    return math.pi * radius**2 * (2.0 * half_extents[axis])
  if shape == "capsule":
    axis = _axis_index(rule.get("axis"))
    radial_axes = [index for index in range(3) if index != axis]
    radius = min(half_extents[index] for index in radial_axes)
    cylinder_half_length = max(half_extents[axis] - radius, 0.0)
    return (
      math.pi * radius**2 * (2.0 * cylinder_half_length)
      + 4.0 * math.pi * radius**3 / 3.0
    )
  return 8.0 * half_extents[0] * half_extents[1] * half_extents[2]


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
  bounds = _bounds_from_center_half_extents(constrained_center, constrained_half)
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
  center_bounds = _merge_bounds(
    proxies_by_region[region_id][center_bounds_source]
    for region_id in center_region_ids
  )
  center = list(center_bounds["center"])
  for axis_name, axis_region_ids in rule.get("center_axis_region_ids", {}).items():
    axis_index = _axis_index(axis_name)
    resolved_region_ids = [
      region_id
      for region_id in axis_region_ids
      if region_id in proxies_by_region
    ]
    if not resolved_region_ids:
      continue
    axis_bounds = _merge_bounds(
      proxies_by_region[region_id][center_bounds_source]
      for region_id in resolved_region_ids
    )
    center[axis_index] = axis_bounds["center"][axis_index]
  return center


def _whole_airframe_projection_hulls(
  fine_proxy: dict[str, Any],
) -> dict[str, list[list[list[float]]]]:
  hulls: dict[str, list[list[list[float]]]] = {}
  for view in SILHOUETTE_VIEW_AXES:
    view_hulls: list[list[list[float]]] = []
    for proxy in fine_proxy["proxies"]:
      view_points = (
        proxy["mesh_derived_review_geometry"]
        .get("hulls", {})
        .get(view, {})
        .get("points_m", [])
      )
      if len(view_points) >= 3:
        view_hulls.append(view_points)
    hulls[view] = view_hulls
  return hulls


def _projection_adjust_center_to_airframe_hulls(
  *,
  center: list[float],
  half_extents: list[float],
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  adjusted_center = [float(value) for value in center]
  for _ in range(2):
    for view, axes in SILHOUETTE_VIEW_AXES.items():
      view_hulls = airframe_projection_hulls.get(view, [])
      if not view_hulls:
        continue
      projected_bounds = _project_bounds(
        _bounds_from_center_half_extents(adjusted_center, half_extents),
        axes,
      )
      current_center = (
        (projected_bounds[0] + projected_bounds[2]) * 0.5,
        (projected_bounds[1] + projected_bounds[3]) * 0.5,
      )
      shifted_candidates: list[tuple[float, tuple[float, float, float, float]]] = []
      for hull_points in view_hulls:
        hull_bounds = _projected_hull_bounds(hull_points)
        if hull_bounds is None:
          continue
        candidate_bounds = _shift_bounds_inside_parent_projection_preserve_size(
          projected_bounds,
          hull_bounds,
          hull_points=hull_points,
        )
        candidate_center = (
          (candidate_bounds[0] + candidate_bounds[2]) * 0.5,
          (candidate_bounds[1] + candidate_bounds[3]) * 0.5,
        )
        shift = math.hypot(
          candidate_center[0] - current_center[0],
          candidate_center[1] - current_center[1],
        )
        shifted_candidates.append((shift, candidate_bounds))
      if not shifted_candidates:
        continue
      shifted_bounds = min(shifted_candidates, key=lambda item: item[0])[1]
      adjusted_center[axes[0]] = (shifted_bounds[0] + shifted_bounds[2]) * 0.5
      adjusted_center[axes[1]] = (shifted_bounds[1] + shifted_bounds[3]) * 0.5
  shift_m = math.sqrt(
    sum((adjusted_center[index] - center[index]) ** 2 for index in range(3))
  )
  return {
    "center_m": _round_vec(adjusted_center),
    "center_shift_m": _round(shift_m),
  }


def _projected_bounds_sample_points(
  bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  return [
    (min_x, min_y),
    (center_x, min_y),
    (max_x, min_y),
    (min_x, center_y),
    (center_x, center_y),
    (max_x, center_y),
    (min_x, max_y),
    (center_x, max_y),
    (max_x, max_y),
  ]


def _projected_ellipse_sample_points(
  bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  return [
    (center_x, center_y),
    (min_x, center_y),
    (max_x, center_y),
    (center_x, min_y),
    (center_x, max_y),
  ]


def _projected_capsule_sample_points(
  bounds: tuple[float, float, float, float],
  *,
  projected_axis_position: int | None,
) -> list[tuple[float, float]]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  if projected_axis_position == 0:
    return [
      (center_x, center_y),
      (min_x, center_y),
      (max_x, center_y),
      (center_x, min_y),
      (center_x, max_y),
      ((min_x + center_x) * 0.5, min_y),
      ((min_x + center_x) * 0.5, max_y),
      ((max_x + center_x) * 0.5, min_y),
      ((max_x + center_x) * 0.5, max_y),
    ]
  if projected_axis_position == 1:
    return [
      (center_x, center_y),
      (center_x, min_y),
      (center_x, max_y),
      (min_x, center_y),
      (max_x, center_y),
      (min_x, (min_y + center_y) * 0.5),
      (max_x, (min_y + center_y) * 0.5),
      (min_x, (max_y + center_y) * 0.5),
      (max_x, (max_y + center_y) * 0.5),
    ]
  return _projected_ellipse_sample_points(bounds)


def _projected_shape_sample_points(
  bounds: tuple[float, float, float, float],
  *,
  axes: tuple[int, int],
  shape: str,
  axis: str,
) -> list[tuple[float, float]]:
  if shape in {"sphere", "ellipsoid"}:
    return _projected_ellipse_sample_points(bounds)
  if shape in {"cylinder", "capsule"}:
    axis_index = _axis_index(axis)
    projected_axis_position = (
      axes.index(axis_index) if axis_index in axes else None
    )
    if shape == "capsule":
      return _projected_capsule_sample_points(
        bounds,
        projected_axis_position=projected_axis_position,
      )
    if projected_axis_position is None:
      return _projected_ellipse_sample_points(bounds)
    return _projected_bounds_sample_points(bounds)
  return _projected_bounds_sample_points(bounds)


def _point_in_any_projected_hull(
  point: tuple[float, float],
  view_hulls: list[list[list[float]]],
  *,
  boundary_tolerance_m: float = 0.02,
) -> bool:
  for hull_points in view_hulls:
    hull_bounds = _projected_hull_bounds(hull_points)
    if hull_bounds is None:
      continue
    min_x, min_y, max_x, max_y = hull_bounds
    if (
      point[0] < min_x - boundary_tolerance_m
      or point[0] > max_x + boundary_tolerance_m
      or point[1] < min_y - boundary_tolerance_m
      or point[1] > max_y + boundary_tolerance_m
    ):
      continue
    if _point_in_projected_polygon(point, hull_points):
      return True
    if (
      _distance_to_projected_polygon_edges(point, hull_points)
      <= boundary_tolerance_m
    ):
      return True
  return False


def _airframe_silhouette_view_diagnostic(
  bounds: dict[str, list[float]],
  *,
  view: str,
  view_hulls: list[list[list[float]]],
  shape: str,
  axis: str,
) -> dict[str, Any]:
  axes = SILHOUETTE_VIEW_AXES[view]
  projected_bounds = _project_bounds(bounds, axes)
  sample_points = _projected_shape_sample_points(
    projected_bounds,
    axes=axes,
    shape=shape,
    axis=axis,
  )
  inside = [
    _point_in_any_projected_hull(point, view_hulls) for point in sample_points
  ]
  inside_count = sum(1 for value in inside if value)
  outside_count = len(sample_points) - inside_count
  return {
    "view": view,
    "projected_bounds": [_round(value) for value in projected_bounds],
    "sample_count": len(sample_points),
    "inside_sample_count": inside_count,
    "outside_sample_count": outside_count,
    "inside_sample_fraction": _round(inside_count / len(sample_points), 5),
    "fully_inside_silhouette": outside_count == 0,
  }


def _airframe_silhouette_diagnostics(
  geometry: dict[str, Any],
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  bounds = geometry["bounds"]
  shape = geometry.get("shape", "obb")
  axis = geometry.get("axis", "")
  views = {
    view: _airframe_silhouette_view_diagnostic(
      bounds,
      view=view,
      view_hulls=airframe_projection_hulls.get(view, []),
      shape=shape,
      axis=axis,
    )
    for view in SILHOUETTE_VIEW_AXES
  }
  outside_views = [
    view
    for view, diagnostic in views.items()
    if not diagnostic["fully_inside_silhouette"]
  ]
  outside_sample_count = sum(
    diagnostic["outside_sample_count"] for diagnostic in views.values()
  )
  sample_count = sum(diagnostic["sample_count"] for diagnostic in views.values())
  return {
    "views": views,
    "outside_views": outside_views,
    "outside_view_count": len(outside_views),
    "outside_sample_count": outside_sample_count,
    "sample_count": sample_count,
    "inside_sample_fraction": _round(
      (sample_count - outside_sample_count) / max(sample_count, 1),
      5,
    ),
    "fully_inside_all_views": outside_sample_count == 0,
  }


def _silhouette_fit_candidate(
  *,
  geometry: dict[str, Any],
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  center = geometry["center_m"]
  half_extents = geometry["half_extents_m"]
  before = _airframe_silhouette_diagnostics(
    geometry,
    airframe_projection_hulls,
  )
  adjustment = _projection_adjust_center_to_airframe_hulls(
    center=center,
    half_extents=half_extents,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  candidate_bounds = _bounds_from_center_half_extents(
    adjustment["center_m"],
    half_extents,
  )
  candidate_geometry = {
    **geometry,
    "center_m": adjustment["center_m"],
    "bounds": candidate_bounds,
  }
  after = _airframe_silhouette_diagnostics(
    candidate_geometry,
    airframe_projection_hulls,
  )
  return {
    "current_silhouette": before,
    "center_shift_candidate_m": adjustment["center_shift_m"],
    "candidate_center_m": adjustment["center_m"],
    "candidate_bounds": candidate_bounds,
    "candidate_silhouette": after,
    "outside_sample_reduction": (
      before["outside_sample_count"] - after["outside_sample_count"]
    ),
  }


def build_internal_component_prior_candidate(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  surface_report: dict[str, Any],
) -> dict[str, Any]:
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  whole_airframe_bounds = _merge_bounds(
    proxy["source_region_bounds"] for proxy in proxies_by_region.values()
  )
  airframe_projection_hulls = _whole_airframe_projection_hulls(fine_proxy)
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
    placement_bounds = _merge_bounds(
      proxies_by_region[region_id][placement_bounds_source]
      for region_id in region_ids
    )
    constraint_bounds = whole_airframe_bounds
    constraint_bounds_source = "whole_airframe_source_region_union_bounds"
    margin_m = float(rule.get("constraint_margin_m", 0.03))
    initial_half, initial_shape_payload = _shape_half_extents(
      rule=rule,
      component_bounds=component_row["component_bounds"],
    )
    initial_center = _rule_initial_center(
      rule=rule,
      component_row=component_row,
      proxies_by_region=proxies_by_region,
    )
    initial_bounds = _bounds_from_center_half_extents(initial_center, initial_half)
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
      projection_adjustment = _projection_adjust_center_to_airframe_hulls(
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
    constrained_shape_payload = _shape_payload_from_half_extents(
      rule=rule,
      half_extents=constrained["half_extents_m"],
    )
    placement_outside_fraction = _outside_fraction(
      initial_bounds,
      placement_bounds,
    )
    pre_outside_fraction = _outside_fraction(initial_bounds, constraint_bounds)
    post_outside_fraction = _outside_fraction(
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
          _bounds_containment_fraction(
            component_row["component_bounds"],
            placement_bounds,
          ),
          5,
        ),
        "prior_unconstrained_geometry": {
          **initial_shape_payload,
          "center_m": _round_vec(initial_center),
          "half_extents_m": _round_vec(initial_half),
          "bounds": initial_bounds,
          "volume_m3": _round(_shape_volume_m3(rule, initial_half)),
        },
        "placement_geometry": {
          **initial_shape_payload,
          "center_m": _round_vec(placement_center),
          "half_extents_m": _round_vec(initial_half),
          "bounds": _bounds_from_center_half_extents(
            placement_center,
            initial_half,
          ),
          "volume_m3": _round(_shape_volume_m3(rule, initial_half)),
        },
        "constrained_geometry": {
          **constrained_shape_payload,
          "center_m": constrained["center_m"],
          "half_extents_m": constrained["half_extents_m"],
          "bounds": constrained["bounds"],
          "volume_m3": _round(
            _shape_volume_m3(rule, constrained["half_extents_m"])
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
  half_extents, _ = _shape_half_extents(
    rule=rule,
    component_bounds=_bounds_from_center_half_extents(
      center,
      [max(value * 0.5, 0.01) for value in dimensions_m],
    ),
  )
  payload = _shape_payload_from_half_extents(
    rule=rule,
    half_extents=half_extents,
  )
  bounds = _bounds_from_center_half_extents(center, half_extents)
  return {
    **payload,
    "center_m": _round_vec(center),
    "half_extents_m": _round_vec(half_extents),
    "bounds": bounds,
    "volume_m3": _round(_shape_volume_m3(rule, half_extents)),
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
  parent_outside_fraction = _outside_fraction(geometry["bounds"], parent_bounds)
  whole_airframe_outside_fraction = _outside_fraction(
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
  axis = _axis_index(axis_name)
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


def _ownership_split_policy(parent_component_name: str) -> dict[str, str]:
  if parent_component_name == "engine_core":
    return {
      "recommended_ownership_decision": (
        "split_into_engine_section_receivers_and_keep_intake_duct_receiver_separate"
      ),
      "parent_receiver_runtime_policy": (
        "retire_parent_engine_core_damage_receiver_when_split_receivers_are_accepted"
      ),
      "decision_rationale": (
        "The public-size engine proxy spans multiple semantic regions; the R15/R21 "
        "segments isolate afterburner/nozzle overlap, hot section, and forward "
        "compressor envelopes while leaving the intake airflow path on the existing "
        "dedicated intake receiver."
      ),
    }
  if parent_component_name == "wing_spar_center":
    return {
      "recommended_ownership_decision": (
        "split_into_center_carrythrough_root_and_inner_wing_spar_receivers"
      ),
      "parent_receiver_runtime_policy": (
        "retire_parent_wing_spar_center_damage_receiver_when_split_receivers_are_accepted"
      ),
      "decision_rationale": (
        "The carry-through spar proxy crosses center fuselage, wing roots, and inner "
        "wing skins; the R15/R21 segments provide owner-region receiver candidates "
        "without accepting a monolithic cross-region runtime receiver."
      ),
    }
  return {
    "recommended_ownership_decision": (
      "keep_cross_region_receiver_held_until_specific_split_policy_exists"
    ),
    "parent_receiver_runtime_policy": (
      "keep_parent_receiver_non_runtime_until_ownership_is_explicit"
    ),
    "decision_rationale": (
      "No component-specific ownership policy exists for this held receiver."
    ),
  }


def _segment_aabb_runtime_candidate(
  *,
  segment_row: dict[str, Any],
  parent_prior: dict[str, Any],
) -> dict[str, Any]:
  segment_bounds = segment_row["geometry"]["bounds"]
  return {
    "name": segment_row["segment_id"],
    "system": parent_prior["system"],
    "offset": segment_bounds["center"],
    "size": segment_bounds["span"],
    "geometry_primitive": "aabb",
    "geometry": {
      "primitive": "aabb",
      "source": "a2_cross_region_ownership_split_candidate",
      "source_parent_component_name": segment_row["parent_component_name"],
      "source_segment_id": segment_row["segment_id"],
      "owner_region_ids": segment_row["owner_region_ids"],
      "prior_shape": segment_row["segment_shape"],
      "prior_axis": segment_row["segment_axis"],
      "shape_promotion_status": segment_row["shape_promotion_status"],
      "segment_role": segment_row["segment_role"],
      "runtime_projection_status": "parse_ready_candidate_not_runtime_active",
    },
    "critical": parent_prior["critical"],
  }


def build_cross_region_ownership_split_candidate_report(
  mapping: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any],
  airframe_constraint_report: dict[str, Any],
) -> dict[str, Any]:
  prior_rows_by_name = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  constraint_rows_by_id = {
    row["item_id"]: row for row in airframe_constraint_report["rows"]
  }
  parent_names = sorted(
    {row["parent_component_name"] for row in held_segment_report["rows"]}
  )
  rows: list[dict[str, Any]] = []
  for parent_name in parent_names:
    parent_prior = prior_rows_by_name[parent_name]
    segments = [
      row
      for row in held_segment_report["rows"]
      if row["parent_component_name"] == parent_name
    ]
    segments.sort(key=lambda row: row["segment_index"])
    segment_entries: list[dict[str, Any]] = []
    for segment in segments:
      constraint_row = constraint_rows_by_id.get(segment["segment_id"], {})
      current_silhouette = constraint_row.get(
        "current_silhouette",
        {"outside_sample_count": None, "outside_views": []},
      )
      segment_entries.append(
        {
          "segment_id": segment["segment_id"],
          "segment_role": segment["segment_role"],
          "owner_region_ids": segment["owner_region_ids"],
          "segment_shape": segment["segment_shape"],
          "segment_axis": segment["segment_axis"],
          "nominal_dimensions_m": segment["nominal_dimensions_m"],
          "inside_whole_airframe_bounds": segment["inside_whole_airframe_bounds"],
          "whole_airframe_outside_fraction": segment[
            "whole_airframe_outside_fraction"
          ],
          "shape_promotion_status": segment["shape_promotion_status"],
          "silhouette_outside_sample_count": current_silhouette[
            "outside_sample_count"
          ],
          "silhouette_outside_views": current_silhouette["outside_views"],
          "airframe_triage_status": constraint_row.get("triage_status", ""),
          "runtime_component_json_candidate": _segment_aabb_runtime_candidate(
            segment_row=segment,
            parent_prior=parent_prior,
          ),
        }
      )

    policy = _ownership_split_policy(parent_name)
    owner_region_ids = sorted(
      {
        owner_region_id
        for segment in segments
        for owner_region_id in segment["owner_region_ids"]
      }
    )
    candidate_names = [
      entry["runtime_component_json_candidate"]["name"] for entry in segment_entries
    ]
    rows.append(
      {
        "parent_component_name": parent_name,
        "parent_system": parent_prior["system"],
        "parent_component_role": parent_prior["component_role"],
        "parent_review_semantics": parent_prior["component_review_semantics"],
        "parent_constraint_status": parent_prior["constraint_status"],
        "parent_receiver_runtime_policy": policy["parent_receiver_runtime_policy"],
        "recommended_ownership_decision": policy[
          "recommended_ownership_decision"
        ],
        "decision_rationale": policy["decision_rationale"],
        "decision_status": (
          "candidate_split_ready_for_runtime_tests_not_accepted"
        ),
        "runtime_activation_status": (
          "not_active_pending_ownership_review_and_runtime_tests"
        ),
        "parent_receiver_retirement_required_before_activation": True,
        "candidate_runtime_component_names": candidate_names,
        "owner_region_ids": owner_region_ids,
        "segment_count": len(segment_entries),
        "segment_entries": segment_entries,
        "parse_ready_runtime_candidate_count": len(segment_entries),
        "runtime_active_split_component_count": 0,
        "silhouette_exposure_segment_count": sum(
          1
          for entry in segment_entries
          if (entry["silhouette_outside_sample_count"] or 0) > 0
        ),
        "outside_whole_airframe_segment_count": sum(
          1
          for segment in segments
          if not segment["inside_whole_airframe_bounds"]
        ),
        "shape_promotion_segment_count": sum(
          1
          for segment in segments
          if segment["shape_promotion_status"] in PROMOTED_SHAPE_STATUSES
        ),
        "acceptance_checks_required": [
          "human_accepts_or_rejects_parent_receiver_retirement",
          "runtime_component_schema_parse_test_for_split_candidates",
          "component_damage_regression_for_parent_vs_split_receiver_behavior",
          "no_runtime_activation_without_explicit_tg_p7_decision",
        ],
        "authority_boundary": (
          "ownership_split_candidate_not_runtime_damage_ownership_acceptance"
        ),
      }
    )

  split_receiver_count = sum(row["segment_count"] for row in rows)
  return {
    "schema_version": CROSS_REGION_OWNERSHIP_SPLIT_SCHEMA_VERSION,
    "status": "cross_region_ownership_split_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": held_segment_report[
      "schema_version"
    ],
    "source_airframe_constraint_schema_version": airframe_constraint_report[
      "schema_version"
    ],
    "summary": {
      "parent_decision_count": len(rows),
      "split_candidate_parent_count": sum(
        1
        for row in rows
        if row["recommended_ownership_decision"].startswith("split_into")
      ),
      "split_receiver_candidate_count": split_receiver_count,
      "engine_core_split_receiver_candidate_count": sum(
        row["segment_count"]
        for row in rows
        if row["parent_component_name"] == "engine_core"
      ),
      "wing_spar_center_split_receiver_candidate_count": sum(
        row["segment_count"]
        for row in rows
        if row["parent_component_name"] == "wing_spar_center"
      ),
      "zero_silhouette_exposure_split_candidate_count": sum(
        1
        for row in rows
        for entry in row["segment_entries"]
        if entry["silhouette_outside_sample_count"] == 0
      ),
      "outside_whole_airframe_split_candidate_count": sum(
        row["outside_whole_airframe_segment_count"] for row in rows
      ),
      "parent_receiver_retirement_required_count": sum(
        1
        for row in rows
        if row["parent_receiver_retirement_required_before_activation"]
      ),
      "runtime_parse_ready_split_candidate_count": split_receiver_count,
      "runtime_active_split_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Accept, reject, or keep held the proposed parent receiver retirement for engine_core and wing_spar_center.",
      },
      {
        "priority": "high",
        "question": "Run TG-P7 parse and behavior tests before activating any split receiver candidate.",
      },
      {
        "priority": "medium",
        "question": "Keep split receiver payloads as AABB fallback candidates until exact capsule or ellipsoid runtime intersection is separately implemented.",
      },
    ],
    "authority_boundary": {
      **internal_prior_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_split_receiver_activation": False,
      "runtime_schema_parse_ready_candidate": True,
      "parent_receiver_retirement_accepted": False,
      "cross_region_receiver_ownership_accepted": False,
      "true_internal_component_geometry": False,
    },
  }


def _runtime_loader_contract_status(candidate: dict[str, Any]) -> str:
  required_fields = {
    "name",
    "system",
    "offset",
    "size",
    "geometry_primitive",
    "geometry",
    "critical",
  }
  if not required_fields.issubset(candidate):
    return "missing_required_runtime_loader_fields"
  if candidate["geometry_primitive"] != "aabb":
    return "unsupported_runtime_loader_fallback_primitive"
  if candidate["geometry"].get("primitive") != "aabb":
    return "unsupported_nested_geometry_primitive"
  if len(candidate["offset"]) != 3 or len(candidate["size"]) != 3:
    return "invalid_offset_or_size_vector"
  if any(value <= 0 for value in candidate["size"]):
    return "invalid_non_positive_size"
  return "parse_ready_existing_loader_fields"


def _damage_component_locations_by_name(
  aircraft: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
  if not aircraft:
    return {}
  locations: dict[str, dict[str, Any]] = {}
  for hitbox_index, hitbox in enumerate(
    aircraft.get("damage_model", {}).get("hitboxes", [])
  ):
    for component_index, component in enumerate(hitbox.get("components", [])):
      component_name = component.get("name")
      if not component_name:
        continue
      locations[component_name] = {
        "hitbox_index": hitbox_index,
        "component_index": component_index,
        "target_path": f"damage_model.hitboxes[{hitbox_index}].components",
      }
  return locations


def _runtime_patch_location_for_parent(
  parent_component_name: str,
  component_locations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
  return component_locations.get(
    parent_component_name,
    {
      "hitbox_index": None,
      "component_index": None,
      "target_path": "damage_model.hitboxes[].components",
    },
  )


def build_target_geometry_runtime_activation_candidate_report(
  mapping: dict[str, Any],
  ownership_split_report: dict[str, Any],
  aircraft: dict[str, Any] | None = None,
) -> dict[str, Any]:
  component_locations = _damage_component_locations_by_name(aircraft)
  rows: list[dict[str, Any]] = []
  patch_additions: list[dict[str, Any]] = []
  patch_component_additions: list[dict[str, Any]] = []
  patch_component_removals: list[dict[str, Any]] = []
  parent_retirement_plan: list[dict[str, Any]] = []

  for parent_row in ownership_split_report["rows"]:
    parent_location = _runtime_patch_location_for_parent(
      parent_row["parent_component_name"],
      component_locations,
    )
    parent_retirement_plan.append(
      {
        "parent_component_name": parent_row["parent_component_name"],
        "target_hitbox_index": parent_location["hitbox_index"],
        "target_component_index": parent_location["component_index"],
        "target_path": parent_location["target_path"],
        "recommended_ownership_decision": parent_row[
          "recommended_ownership_decision"
        ],
        "parent_receiver_runtime_policy": parent_row[
          "parent_receiver_runtime_policy"
        ],
        "candidate_runtime_component_names": parent_row[
          "candidate_runtime_component_names"
        ],
        "retirement_application_status": (
          "not_applied_pending_explicit_tg_p7_acceptance"
        ),
      }
    )
    patch_component_removals.append(
      {
        "operation": "remove_component_by_name",
        "component_name": parent_row["parent_component_name"],
        "target_hitbox_index": parent_location["hitbox_index"],
        "target_component_index": parent_location["component_index"],
        "target_path": parent_location["target_path"],
        "application_status": "not_applied_to_repository_unit_database",
      }
    )
    for segment_entry in parent_row["segment_entries"]:
      candidate = copy.deepcopy(
        segment_entry["runtime_component_json_candidate"]
      )
      candidate["geometry"]["runtime_activation_candidate_status"] = (
        "tg_p7_parse_ready_not_applied"
      )
      candidate["geometry"]["activation_parent_component_name"] = parent_row[
        "parent_component_name"
      ]
      candidate["geometry"]["activation_parent_runtime_policy"] = parent_row[
        "parent_receiver_runtime_policy"
      ]
      candidate["geometry"]["activation_feature_flag"] = (
        "A2_TARGET_GEOMETRY_PROXY_F16C_R22"
      )
      loader_status = _runtime_loader_contract_status(candidate)
      patch_additions.append(candidate)
      patch_component_additions.append(
        {
          "operation": "append_component",
          "component_name": candidate["name"],
          "parent_component_name": parent_row["parent_component_name"],
          "target_hitbox_index": parent_location["hitbox_index"],
          "target_path": parent_location["target_path"],
          "application_status": "not_applied_to_repository_unit_database",
          "value": candidate,
        }
      )
      rows.append(
        {
          "candidate_component_name": candidate["name"],
          "parent_component_name": parent_row["parent_component_name"],
          "target_hitbox_index": parent_location["hitbox_index"],
          "unit_database_patch_path": parent_location["target_path"],
          "parent_system": parent_row["parent_system"],
          "recommended_ownership_decision": parent_row[
            "recommended_ownership_decision"
          ],
          "parent_receiver_runtime_policy": parent_row[
            "parent_receiver_runtime_policy"
          ],
          "segment_role": segment_entry["segment_role"],
          "owner_region_ids": segment_entry["owner_region_ids"],
          "geometry_primitive": candidate["geometry_primitive"],
          "offset_m": candidate["offset"],
          "size_m": candidate["size"],
          "runtime_loader_contract_status": loader_status,
          "runtime_activation_status": "not_applied_to_unit_database",
          "behavior_test_status": "required_before_activation",
          "feature_flag": "A2_TARGET_GEOMETRY_PROXY_F16C_R22",
          "runtime_component_json_candidate": candidate,
        }
      )

  loader_ready_count = sum(
    1
    for row in rows
    if row["runtime_loader_contract_status"]
    == "parse_ready_existing_loader_fields"
  )
  behavior_required_count = sum(
    1
    for row in rows
    if row["behavior_test_status"] == "required_before_activation"
  )
  return {
    "schema_version": TARGET_GEOMETRY_RUNTIME_ACTIVATION_SCHEMA_VERSION,
    "status": "target_geometry_runtime_activation_candidate_generated_tg_p7_r1",
    "generated_on": "2026-06-13",
    "source_geometry_generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_cross_region_ownership_split_schema_version": (
      ownership_split_report["schema_version"]
    ),
    "activation_policy": {
      "activation_scope": "f16c_block50_initial_training_geometry_proxy",
      "activation_mode": "unit_database_patch_candidate_not_applied",
      "target_unit": "F-16C_Block50",
      "target_path": "damage_model.hitboxes[].components",
      "requires_feature_flag": True,
      "feature_flag": "A2_TARGET_GEOMETRY_PROXY_F16C_R22",
      "parent_receiver_retirement_required_before_activation": True,
      "runtime_behavior_regression_required_before_activation": True,
    },
    "runtime_loader_contract": {
      "required_top_level_fields": [
        "name",
        "system",
        "offset",
        "size",
        "geometry_primitive",
        "geometry",
        "critical",
      ],
      "accepted_fallback_geometry_primitive": "aabb",
      "loader_status_required_for_activation": (
        "parse_ready_existing_loader_fields"
      ),
    },
    "summary": {
      "candidate_component_count": len(rows),
      "runtime_schema_parse_ready_component_count": loader_ready_count,
      "runtime_active_component_count": 0,
      "parent_receiver_retirement_candidate_count": len(
        parent_retirement_plan
      ),
      "parent_receiver_retirement_applied_count": 0,
      "aabb_fallback_component_count": sum(
        1 for row in rows if row["geometry_primitive"] == "aabb"
      ),
      "unit_database_patch_component_count": len(patch_additions),
      "behavior_test_required_count": behavior_required_count,
      "activation_blocker_count": len(rows) - loader_ready_count,
      "review_status": "tg_p7_parse_ready_activation_candidate_not_applied",
    },
    "rows": rows,
    "parent_receiver_retirement_plan": parent_retirement_plan,
    "unit_database_patch_candidate": {
      "target_unit": "F-16C_Block50",
      "target_path": "damage_model.hitboxes[].components",
      "operation": "remove_parent_components_and_append_split_receivers",
      "remove": patch_component_removals,
      "add": patch_additions,
      "add_components": patch_component_additions,
      "parent_receiver_retirement_plan": parent_retirement_plan,
      "patch_application_status": "not_applied_to_repository_unit_database",
    },
    "acceptance_gate": [
      "candidate_component_count_equals_8",
      "runtime_schema_parse_ready_component_count_equals_8",
      "parent_receiver_retirement_plan_exists_for_2_parents",
      "unit_database_patch_candidate_contains_8_component_records",
      "runtime_active_component_count_equals_0_until_explicit_activation",
      "behavior_tests_required_before_activation",
    ],
    "authority_boundary": {
      **ownership_split_report["authority_boundary"],
      "unit_database_modified": False,
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_activation_candidate": True,
      "training_proxy_feature_flag_required": True,
      "parent_receiver_retirement_accepted": False,
      "true_internal_component_geometry": False,
    },
  }


def _damage_component_names(aircraft: dict[str, Any]) -> list[str]:
  names: list[str] = []
  for hitbox in aircraft.get("damage_model", {}).get("hitboxes", []):
    for component in hitbox.get("components", []):
      component_name = component.get("name")
      if component_name:
        names.append(component_name)
  return names


def _duplicate_names(names: list[str]) -> list[str]:
  counts: dict[str, int] = {}
  for name in names:
    counts[name] = counts.get(name, 0) + 1
  return sorted(name for name, count in counts.items() if count > 1)


def _apply_runtime_activation_patch_candidate(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  patched_aircraft = copy.deepcopy(aircraft)
  operations: list[dict[str, Any]] = []
  hitboxes = patched_aircraft.get("damage_model", {}).get("hitboxes", [])

  for removal in runtime_activation_report["unit_database_patch_candidate"][
    "remove"
  ]:
    hitbox_index = removal["target_hitbox_index"]
    if hitbox_index is None or hitbox_index >= len(hitboxes):
      operations.append({**removal, "result": "target_hitbox_missing"})
      continue
    components = hitboxes[hitbox_index].get("components", [])
    before_count = len(components)
    kept_components = [
      component
      for component in components
      if component.get("name") != removal["component_name"]
    ]
    hitboxes[hitbox_index]["components"] = kept_components
    operations.append(
      {
        **removal,
        "result": (
          "removed"
          if len(kept_components) < before_count
          else "component_not_found"
        ),
        "component_count_before": before_count,
        "component_count_after": len(kept_components),
      }
    )

  for addition in runtime_activation_report["unit_database_patch_candidate"][
    "add_components"
  ]:
    hitbox_index = addition["target_hitbox_index"]
    if hitbox_index is None or hitbox_index >= len(hitboxes):
      operations.append({**addition, "value": None, "result": "target_hitbox_missing"})
      continue
    components = hitboxes[hitbox_index].setdefault("components", [])
    before_count = len(components)
    components.append(copy.deepcopy(addition["value"]))
    operations.append(
      {
        **{key: value for key, value in addition.items() if key != "value"},
        "result": "appended",
        "component_count_before": before_count,
        "component_count_after": len(components),
      }
    )

  return patched_aircraft, operations


def build_target_geometry_runtime_behavior_regression_report(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> dict[str, Any]:
  base_component_names = _damage_component_names(aircraft)
  patched_aircraft, operations = _apply_runtime_activation_patch_candidate(
    aircraft,
    runtime_activation_report,
  )
  patched_component_names = _damage_component_names(patched_aircraft)
  parent_names = [
    row["parent_component_name"]
    for row in runtime_activation_report["parent_receiver_retirement_plan"]
  ]
  split_names = [
    row["candidate_component_name"] for row in runtime_activation_report["rows"]
  ]
  duplicate_names = _duplicate_names(patched_component_names)
  rows: list[dict[str, Any]] = []
  for parent_row in runtime_activation_report["parent_receiver_retirement_plan"]:
    parent_name = parent_row["parent_component_name"]
    target_hitbox_index = parent_row["target_hitbox_index"]
    base_hitboxes = aircraft.get("damage_model", {}).get("hitboxes", [])
    patched_hitboxes = patched_aircraft.get("damage_model", {}).get("hitboxes", [])
    base_hitbox_component_count = (
      len(base_hitboxes[target_hitbox_index].get("components", []))
      if target_hitbox_index is not None and target_hitbox_index < len(base_hitboxes)
      else 0
    )
    patched_hitbox_component_count = (
      len(patched_hitboxes[target_hitbox_index].get("components", []))
      if target_hitbox_index is not None and target_hitbox_index < len(patched_hitboxes)
      else 0
    )
    split_component_names = [
      row["candidate_component_name"]
      for row in runtime_activation_report["rows"]
      if row["parent_component_name"] == parent_name
    ]
    rows.append(
      {
        "parent_component_name": parent_name,
        "target_hitbox_index": target_hitbox_index,
        "target_path": parent_row["target_path"],
        "base_hitbox_component_count": base_hitbox_component_count,
        "patched_hitbox_component_count": patched_hitbox_component_count,
        "parent_present_before_patch": parent_name in base_component_names,
        "parent_absent_after_patch": parent_name not in patched_component_names,
        "split_component_names": split_component_names,
        "split_component_present_count": sum(
          1 for name in split_component_names if name in patched_component_names
        ),
        "duplicate_component_name_count": sum(
          1 for name in split_component_names if name in duplicate_names
        ),
        "behavior_status": (
          "pass"
          if parent_name in base_component_names
          and parent_name not in patched_component_names
          and all(name in patched_component_names for name in split_component_names)
          else "fail"
        ),
      }
    )

  expected_projected_count = (
    len(base_component_names) - len(parent_names) + len(split_names)
  )
  behavior_pass = (
    len(patched_component_names) == expected_projected_count
    and all(parent_name not in patched_component_names for parent_name in parent_names)
    and all(split_name in patched_component_names for split_name in split_names)
    and not duplicate_names
    and all(row["behavior_status"] == "pass" for row in rows)
  )
  return {
    "schema_version": TARGET_GEOMETRY_RUNTIME_BEHAVIOR_SCHEMA_VERSION,
    "status": "target_geometry_runtime_behavior_regression_generated_tg_p7_r2",
    "generated_on": "2026-06-13",
    "source_runtime_activation_schema_version": runtime_activation_report[
      "schema_version"
    ],
    "target_unit": runtime_activation_report["activation_policy"]["target_unit"],
    "feature_flag": runtime_activation_report["activation_policy"][
      "feature_flag"
    ],
    "summary": {
      "base_component_count": len(base_component_names),
      "expected_projected_component_count": expected_projected_count,
      "projected_component_count": len(patched_component_names),
      "retired_parent_component_count": sum(
        1 for parent_name in parent_names if parent_name not in patched_component_names
      ),
      "split_component_added_count": sum(
        1 for split_name in split_names if split_name in patched_component_names
      ),
      "duplicate_component_name_count": len(duplicate_names),
      "parent_retirement_behavior_pass_count": sum(
        1 for row in rows if row["behavior_status"] == "pass"
      ),
      "behavior_regression_pass": behavior_pass,
      "runtime_active_component_count": 0,
      "unit_database_modified": False,
    },
    "rows": rows,
    "patch_operations": operations,
    "projected_component_names": patched_component_names,
    "duplicate_component_names": duplicate_names,
    "acceptance_gate": [
      "base_component_count_equals_26",
      "retired_parent_component_count_equals_2",
      "split_component_added_count_equals_8",
      "projected_component_count_equals_32",
      "duplicate_component_name_count_equals_0",
      "runtime_active_component_count_equals_0_until_training_path_activation",
    ],
    "authority_boundary": {
      **runtime_activation_report["authority_boundary"],
      "runtime_behavior_regression_candidate": True,
      "unit_database_modified": False,
      "runtime_active_component": False,
      "training_path_wired": False,
    },
  }


def build_target_geometry_training_proxy_unit_candidate(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  return _apply_runtime_activation_patch_candidate(
    aircraft,
    runtime_activation_report,
  )


def build_target_geometry_training_proxy_database_report(
  aircraft: dict[str, Any],
  runtime_activation_report: dict[str, Any],
  runtime_behavior_report: dict[str, Any],
  *,
  database_source_path: Path = DEFAULT_RUNTIME_DATABASE,
  proxy_database_dir: Path | None = None,
) -> dict[str, Any]:
  patched_aircraft, operations = build_target_geometry_training_proxy_unit_candidate(
    aircraft,
    runtime_activation_report,
  )
  base_component_names = _damage_component_names(aircraft)
  proxy_component_names = _damage_component_names(patched_aircraft)
  parent_names = [
    row["parent_component_name"]
    for row in runtime_activation_report["parent_receiver_retirement_plan"]
  ]
  split_names = [
    row["candidate_component_name"] for row in runtime_activation_report["rows"]
  ]
  duplicate_names = _duplicate_names(proxy_component_names)
  source_database_path = Path(database_source_path)
  source_unit_path = source_database_path / "aircraft" / "units" / "f16c_block50.json"
  rows = [
    {
      "parent_component_name": row["parent_component_name"],
      "target_hitbox_index": row["target_hitbox_index"],
      "target_path": row["target_path"],
      "base_hitbox_component_count": row["base_hitbox_component_count"],
      "proxy_hitbox_component_count": row["patched_hitbox_component_count"],
      "parent_absent_after_proxy_patch": row["parent_absent_after_patch"],
      "split_component_names": row["split_component_names"],
      "split_component_present_count": row["split_component_present_count"],
      "duplicate_component_name_count": row["duplicate_component_name_count"],
      "behavior_status": row["behavior_status"],
      "proxy_database_status": "ready_for_opt_in_training_database_path",
    }
    for row in runtime_behavior_report["rows"]
  ]
  return {
    "schema_version": TARGET_GEOMETRY_TRAINING_PROXY_SCHEMA_VERSION,
    "status": "target_geometry_training_proxy_database_generated_tg_p7_r3",
    "generated_on": "2026-06-13",
    "source_runtime_activation_schema_version": runtime_activation_report[
      "schema_version"
    ],
    "source_runtime_behavior_schema_version": runtime_behavior_report[
      "schema_version"
    ],
    "target_unit": runtime_activation_report["activation_policy"]["target_unit"],
    "feature_flag": runtime_activation_report["activation_policy"][
      "feature_flag"
    ],
    "runtime_database": {
      "source_database_path": _display_path(source_database_path, REPO_ROOT),
      "source_f16c_unit_path": _display_path(source_unit_path, REPO_ROOT),
      "proxy_database_path": (
        _display_path(proxy_database_dir, REPO_ROOT)
        if proxy_database_dir is not None
        else ""
      ),
      "proxy_f16c_unit_path": (
        _display_path(
          proxy_database_dir / "aircraft" / "units" / "f16c_block50.json",
          REPO_ROOT,
        )
        if proxy_database_dir is not None
        else ""
      ),
      "source_f16c_unit_sha256": (
        _sha256_file(source_unit_path) if source_unit_path.is_file() else ""
      ),
      "proxy_f16c_unit_sha256": "",
    },
    "training_runtime_contract": {
      "runtime_config_key": "runtime.database_path",
      "feature_flag": runtime_activation_report["activation_policy"][
        "feature_flag"
      ],
      "target_path": runtime_activation_report["activation_policy"][
        "target_path"
      ],
      "maintained_execution_entrypoint": (
        "python.rl.runtime.world_batch_vec_env.WorldBatchVecEnv"
      ),
      "maintained_cooperative_entrypoint": (
        "python.rl.runtime.cooperative_world_batch_vec_env.CooperativeWorldBatchVecEnv"
      ),
      "default_database_path_remains": _display_path(
        DEFAULT_RUNTIME_DATABASE,
        REPO_ROOT,
      ),
      "opt_in_training_config_required": True,
      "opt_in_training_config_path": _display_path(
        TARGET_GEOMETRY_PROXY_TRAINING_CONFIG,
        REPO_ROOT,
      ),
      "training_path_wired": True,
    },
    "summary": {
      "default_database_component_count": len(base_component_names),
      "proxy_database_component_count": len(proxy_component_names),
      "component_count_delta": (
        len(proxy_component_names) - len(base_component_names)
      ),
      "retired_parent_component_count": sum(
        1 for parent_name in parent_names if parent_name not in proxy_component_names
      ),
      "split_receiver_component_count": sum(
        1 for split_name in split_names if split_name in proxy_component_names
      ),
      "duplicate_component_name_count": len(duplicate_names),
      "behavior_regression_pass": bool(
        runtime_behavior_report["summary"]["behavior_regression_pass"]
      ),
      "proxy_database_materialized": proxy_database_dir is not None,
      "repository_unit_database_modified": False,
      "default_runtime_split_receiver_active_count": 0,
      "proxy_runtime_split_receiver_active_count": sum(
        1 for split_name in split_names if split_name in proxy_component_names
      ),
      "training_database_path_ready": proxy_database_dir is not None,
    },
    "rows": rows,
    "patch_operations": operations,
    "proxy_component_names": proxy_component_names,
    "duplicate_component_names": duplicate_names,
    "acceptance_gate": [
      "default_database_component_count_equals_26",
      "proxy_database_component_count_equals_32",
      "retired_parent_component_count_equals_2",
      "split_receiver_component_count_equals_8",
      "duplicate_component_name_count_equals_0",
      "behavior_regression_pass_is_true",
      "repository_unit_database_modified_is_false",
      "runtime_database_path_override_required_for_training_proxy",
    ],
    "authority_boundary": {
      **runtime_behavior_report["authority_boundary"],
      "unit_database_modified": False,
      "default_runtime_active_component": False,
      "training_proxy_database_generated": proxy_database_dir is not None,
      "training_proxy_runtime_active_component": proxy_database_dir is not None,
      "training_proxy_feature_flag_required": True,
      "training_path_wired": True,
      "true_internal_component_geometry": False,
    },
  }


def _airframe_constraint_triage_status(
  *,
  current: dict[str, Any],
  candidate: dict[str, Any],
  item_review_semantics: str,
  size_evidence_level: str,
) -> str:
  if current["outside_sample_count"] == 0:
    if "low_confidence" in size_evidence_level:
      return "inside_airframe_low_confidence_size_review"
    if item_review_semantics in CROSS_REGION_REVIEW_SEMANTICS:
      return "inside_airframe_cross_region_ownership_held"
    return "inside_airframe_candidate"
  if candidate["outside_sample_count"] == 0:
    return "center_shift_candidate_resolves_silhouette_exposure"
  if candidate["outside_sample_count"] < current["outside_sample_count"]:
    return "center_shift_candidate_reduces_silhouette_exposure"
  return "silhouette_exposure_requires_size_or_shape_review"


def _airframe_constraint_recommended_action(status: str) -> str:
  if status == "inside_airframe_candidate":
    return "no_geometry_correction_required_before_human_size_review"
  if status == "inside_airframe_low_confidence_size_review":
    return "replace_low_confidence_engineering_proxy_with_better_size_source"
  if status == "inside_airframe_cross_region_ownership_held":
    return "keep_cross_region_receiver_held_until_ownership_is_split_or_accepted"
  if status == "center_shift_candidate_resolves_silhouette_exposure":
    return "review_candidate_center_shift_before_applying_to_prior_rule"
  if status == "center_shift_candidate_reduces_silhouette_exposure":
    return "review_center_shift_plus_component_specific_size_or_shape_change"
  return "research_size_shape_or_multi_region_placement_before_acceptance"


def _airframe_constraint_row(
  *,
  item_id: str,
  record_type: str,
  component_name: str,
  parent_component_name: str,
  system: str,
  component_role: str,
  geometry: dict[str, Any],
  prior_shape: str,
  prior_axis: str,
  nominal_dimensions_m: list[float],
  size_basis: str,
  size_evidence_level: str,
  bound_region_id: str,
  owner_region_ids: list[str],
  component_review_semantics: str,
  constraint_status: str,
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  fit = _silhouette_fit_candidate(
    geometry=geometry,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  status = _airframe_constraint_triage_status(
    current=fit["current_silhouette"],
    candidate=fit["candidate_silhouette"],
    item_review_semantics=component_review_semantics,
    size_evidence_level=size_evidence_level,
  )
  return {
    "item_id": item_id,
    "record_type": record_type,
    "component_name": component_name,
    "parent_component_name": parent_component_name,
    "system": system,
    "component_role": component_role,
    "prior_shape": prior_shape,
    "prior_axis": prior_axis,
    "nominal_dimensions_m": nominal_dimensions_m,
    "size_basis": size_basis,
    "size_evidence_level": size_evidence_level,
    "bound_region_id": bound_region_id,
    "owner_region_ids": owner_region_ids,
    "component_review_semantics": component_review_semantics,
    "constraint_status": constraint_status,
    "current_geometry": geometry,
    "current_silhouette": fit["current_silhouette"],
    "candidate_center_shift_m": fit["center_shift_candidate_m"],
    "candidate_center_m": fit["candidate_center_m"],
    "candidate_bounds": fit["candidate_bounds"],
    "candidate_silhouette": fit["candidate_silhouette"],
    "outside_sample_reduction": fit["outside_sample_reduction"],
    "triage_status": status,
    "recommended_action": _airframe_constraint_recommended_action(status),
    "runtime_projection_status": (
      "review_only_airframe_constraint_correction_candidate_not_runtime_active"
    ),
    "authority_boundary": (
      "silhouette_constraint_diagnostic_and_center_shift_candidate_only"
    ),
  }


def build_airframe_constraint_correction_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any],
) -> dict[str, Any]:
  airframe_projection_hulls = _whole_airframe_projection_hulls(fine_proxy)
  rows: list[dict[str, Any]] = []
  for prior_row in internal_prior_report["rows"]:
    rows.append(
      _airframe_constraint_row(
        item_id=prior_row["component_name"],
        record_type="receiver_prior",
        component_name=prior_row["component_name"],
        parent_component_name=prior_row["component_name"],
        system=prior_row["system"],
        component_role=prior_row["component_role"],
        geometry=prior_row["constrained_geometry"],
        prior_shape=prior_row["prior_shape"],
        prior_axis=prior_row["prior_axis"],
        nominal_dimensions_m=prior_row["nominal_dimensions_m"],
        size_basis=prior_row["size_basis"],
        size_evidence_level=prior_row["size_evidence_level"],
        bound_region_id=prior_row["bound_region_id"],
        owner_region_ids=prior_row["constraint_region_ids"],
        component_review_semantics=prior_row["component_review_semantics"],
        constraint_status=prior_row["constraint_status"],
        airframe_projection_hulls=airframe_projection_hulls,
      )
    )
  prior_rows_by_name = {
    row["component_name"]: row for row in internal_prior_report["rows"]
  }
  for segment_row in held_segment_report["rows"]:
    parent_prior = prior_rows_by_name[segment_row["parent_component_name"]]
    rows.append(
      _airframe_constraint_row(
        item_id=segment_row["segment_id"],
        record_type="held_split_segment",
        component_name=segment_row["segment_id"],
        parent_component_name=segment_row["parent_component_name"],
        system=parent_prior["system"],
        component_role=segment_row["segment_role"],
        geometry=segment_row["geometry"],
        prior_shape=segment_row["segment_shape"],
        prior_axis=segment_row["segment_axis"],
        nominal_dimensions_m=segment_row["nominal_dimensions_m"],
        size_basis=segment_row["source_basis"],
        size_evidence_level="held_segment_split_proxy",
        bound_region_id=parent_prior["bound_region_id"],
        owner_region_ids=segment_row["owner_region_ids"],
        component_review_semantics=segment_row["parent_component_review_semantics"],
        constraint_status=segment_row["parent_component_constraint_status"],
        airframe_projection_hulls=airframe_projection_hulls,
      )
    )

  status_values = sorted({row["triage_status"] for row in rows})
  return {
    "schema_version": AIRFRAME_CONSTRAINT_CORRECTION_SCHEMA_VERSION,
    "status": "airframe_constraint_correction_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": held_segment_report[
      "schema_version"
    ],
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "item_count": len(rows),
      "receiver_prior_count": sum(
        1 for row in rows if row["record_type"] == "receiver_prior"
      ),
      "held_split_segment_count": sum(
        1 for row in rows if row["record_type"] == "held_split_segment"
      ),
      "silhouette_exposure_item_count": sum(
        1
        for row in rows
        if row["current_silhouette"]["outside_sample_count"] > 0
      ),
      "center_shift_resolves_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "center_shift_candidate_resolves_silhouette_exposure"
      ),
      "center_shift_reduces_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "center_shift_candidate_reduces_silhouette_exposure"
      ),
      "size_or_shape_review_item_count": sum(
        1
        for row in rows
        if row["triage_status"]
        == "silhouette_exposure_requires_size_or_shape_review"
      ),
      "low_confidence_inside_item_count": sum(
        1
        for row in rows
        if row["triage_status"] == "inside_airframe_low_confidence_size_review"
      ),
      "triage_status_counts": {
        status: sum(1 for row in rows if row["triage_status"] == status)
        for status in status_values
      },
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review items with silhouette exposure before accepting their size or placement priors.",
      },
      {
        "priority": "high",
        "question": "Apply center-shift candidates only after confirming the movement matches component semantics.",
      },
      {
        "priority": "medium",
        "question": "Replace low-confidence engineering proxies with better dimensions before runtime activation.",
      },
    ],
    "authority_boundary": {
      **internal_prior_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "airframe_silhouette_constraint_diagnostic": True,
      "center_shift_candidate_not_applied": True,
    },
  }


def _subcomponent_shape_design_rule(row: dict[str, Any]) -> dict[str, Any]:
  rule = SUBCOMPONENT_SHAPE_PLACEMENT_DESIGN_RULES.get(row["item_id"])
  if rule is not None:
    return rule
  item_id = row["item_id"]
  if "fuel_cell" in item_id:
    return {
      "candidate_shape_family": "conformal_fuel_bladder_ellipsoid",
      "evaluation_shape": "ellipsoid",
      "evaluation_axis": "",
      "placement_policy": (
        "preserve_capacity_informed_dimensions_and_retest_as_rounded_fuel_volume"
      ),
      "rationale": (
        "fuel cells should be conformal bladder-like receivers; a rounded volume "
        "is a better first candidate than a rectangular block."
      ),
    }
  if row["prior_shape"] == "obb":
    return {
      "candidate_shape_family": "rounded_lru_ellipsoid",
      "evaluation_shape": "ellipsoid",
      "evaluation_axis": "",
      "placement_policy": (
        "preserve_public_or_standard_LRU_dimensions_and_replace_box_corners_with_rounded_receiver_proxy"
      ),
      "rationale": (
        "small avionics/control receivers are represented as damage volumes; an "
        "ellipsoid proxy tests whether the exposure is only a box-corner artifact."
      ),
    }
  if row["prior_shape"] == "capsule":
    return {
      "candidate_shape_family": "rounded_capsule_recheck",
      "evaluation_shape": "capsule",
      "evaluation_axis": row["prior_axis"] or "x",
      "placement_policy": (
        "preserve_current_capsule_dimensions_and_recheck_with_airframe_silhouette"
      ),
      "rationale": (
        "current capsule is already rounded; remaining exposure likely needs a "
        "better centerline or multi-region placement model."
      ),
    }
  return {
    "candidate_shape_family": "current_shape_recheck",
    "evaluation_shape": row["prior_shape"],
    "evaluation_axis": row["prior_axis"],
    "placement_policy": "preserve_current_dimensions_and_shape_for_recheck",
    "rationale": (
      "no component-specific replacement rule exists yet; keep the current shape "
      "and record the residual exposure for follow-up."
    ),
  }


def _geometry_from_existing_half_extents(
  *,
  source_geometry: dict[str, Any],
  shape: str,
  axis: str,
  center: list[float] | None = None,
) -> dict[str, Any]:
  resolved_center = center or source_geometry["center_m"]
  half_extents = source_geometry["half_extents_m"]
  rule = {
    "shape": shape,
    "axis": axis,
  }
  payload = _shape_payload_from_half_extents(
    rule=rule,
    half_extents=half_extents,
  )
  bounds = _bounds_from_center_half_extents(resolved_center, half_extents)
  return {
    **payload,
    "center_m": _round_vec(resolved_center),
    "half_extents_m": _round_vec(half_extents),
    "bounds": bounds,
    "volume_m3": _round(_shape_volume_m3(rule, half_extents)),
  }


def _geometry_with_center_offset(
  *,
  source_geometry: dict[str, Any],
  center_offset_m: list[float],
) -> dict[str, Any]:
  center = [
    float(source_geometry["center_m"][index]) + float(center_offset_m[index])
    for index in range(3)
  ]
  half_extents = source_geometry["half_extents_m"]
  bounds = _bounds_from_center_half_extents(center, half_extents)
  return {
    **source_geometry,
    "center_m": _round_vec(center),
    "bounds": bounds,
  }


def _subcomponent_centerline_rule(row: dict[str, Any]) -> dict[str, Any]:
  return SUBCOMPONENT_CENTERLINE_PLACEMENT_RULES.get(
    row["item_id"],
    {
      "center_offset_m": [0.0, 0.0, 0.0],
      "source_basis": "no_R19_centerline_candidate_rule",
      "placement_policy": (
        "no_centerline_candidate_available_keep_shape_candidate_for_review"
      ),
      "rationale": (
        "no local centerline search rule exists for this item; keep the shape "
        "candidate as the review artifact."
      ),
    },
  )


def _subcomponent_latest_rule(row: dict[str, Any]) -> dict[str, Any]:
  return SUBCOMPONENT_LATEST_PLACEMENT_RULES.get(
    row["item_id"],
    {
      "stage": "R19_centerline_candidate",
      "center_offset_from_centerline_m": [0.0, 0.0, 0.0],
      "source_basis": "R19_local_centerline_candidate",
      "placement_policy": row.get(
        "centerline_candidate_placement_policy",
        "preserve_dimensions_and_use_latest_centerline_candidate",
      ),
      "rationale": row.get(
        "centerline_candidate_rationale",
        "R19 centerline candidate already clears sampled silhouette exposure.",
      ),
    },
  )


def _subcomponent_shape_design_status(
  *,
  current_outside_count: int,
  candidate_outside_count: int,
  center_shift_m: float,
) -> str:
  if candidate_outside_count == 0 and center_shift_m > 0.0:
    return "shape_and_center_shift_candidate_resolves_silhouette_exposure"
  if candidate_outside_count == 0:
    return "shape_candidate_resolves_silhouette_exposure"
  if candidate_outside_count < current_outside_count:
    return "shape_candidate_reduces_exposure_requires_followup_geometry"
  return "shape_candidate_does_not_reduce_exposure_requires_new_placement_model"


def _subcomponent_centerline_design_status(
  *,
  candidate_outside_count: int,
  centerline_outside_count: int,
) -> str:
  if centerline_outside_count == 0:
    return "centerline_candidate_resolves_silhouette_exposure_review_required"
  if centerline_outside_count < candidate_outside_count:
    return "centerline_candidate_reduces_exposure_requires_followup_geometry"
  return "centerline_candidate_does_not_reduce_exposure_requires_new_geometry"


def _subcomponent_latest_status(outside_count: int) -> str:
  if outside_count == 0:
    return "latest_candidate_resolves_silhouette_exposure_review_required"
  return "latest_candidate_still_exposes_silhouette_requires_geometry_model"


def _subcomponent_centerline_recommended_action(status: str) -> str:
  if status == "centerline_candidate_resolves_silhouette_exposure_review_required":
    return "review_centerline_semantics_before_promoting_to_prior_or_segment_rule"
  if status == "centerline_candidate_reduces_exposure_requires_followup_geometry":
    return "keep_centerline_candidate_as_intermediate_and_research_cross_section_or_true_centerline"
  return "design_new_size_cross_section_or_multi_region_centerline_model"


def _subcomponent_latest_recommended_action(status: str) -> str:
  if status == "latest_candidate_resolves_silhouette_exposure_review_required":
    return "review_latest_candidate_semantics_before_promoting_to_prior_or_segment_rule"
  return "keep_runtime_inactive_and_design_new_section_or_envelope_model"


def _subcomponent_shape_design_recommended_action(status: str) -> str:
  if status == "shape_candidate_resolves_silhouette_exposure":
    return "review_shape_semantics_then_promote_to_next_internal_prior_rule"
  if status == "shape_and_center_shift_candidate_resolves_silhouette_exposure":
    return "review_shape_semantics_and_center_shift_before_applying_to_prior_rule"
  if status == "shape_candidate_reduces_exposure_requires_followup_geometry":
    return "keep_candidate_as_intermediate_and_research_size_cross_section_or_multi_region_centerline"
  return "design_new_size_or_centerline_model_before_runtime_activation"


def _subcomponent_shape_candidate_row(
  row: dict[str, Any],
  *,
  airframe_projection_hulls: dict[str, list[list[list[float]]]],
) -> dict[str, Any]:
  rule = _subcomponent_shape_design_rule(row)
  current_geometry = row["current_geometry"]
  candidate_seed = _geometry_from_existing_half_extents(
    source_geometry=current_geometry,
    shape=rule["evaluation_shape"],
    axis=rule["evaluation_axis"],
  )
  fit = _silhouette_fit_candidate(
    geometry=candidate_seed,
    airframe_projection_hulls=airframe_projection_hulls,
  )
  candidate_geometry = _geometry_from_existing_half_extents(
    source_geometry=current_geometry,
    shape=rule["evaluation_shape"],
    axis=rule["evaluation_axis"],
    center=fit["candidate_center_m"],
  )
  centerline_rule = _subcomponent_centerline_rule(row)
  centerline_geometry = _geometry_with_center_offset(
    source_geometry=candidate_geometry,
    center_offset_m=centerline_rule["center_offset_m"],
  )
  centerline_silhouette = _airframe_silhouette_diagnostics(
    centerline_geometry,
    airframe_projection_hulls,
  )
  latest_rule = _subcomponent_latest_rule(
    {
      **row,
      "centerline_candidate_placement_policy": centerline_rule[
        "placement_policy"
      ],
      "centerline_candidate_rationale": centerline_rule["rationale"],
    }
  )
  latest_geometry = _geometry_with_center_offset(
    source_geometry=centerline_geometry,
    center_offset_m=latest_rule["center_offset_from_centerline_m"],
  )
  latest_silhouette = _airframe_silhouette_diagnostics(
    latest_geometry,
    airframe_projection_hulls,
  )
  current_outside_count = row["current_silhouette"]["outside_sample_count"]
  candidate_outside_count = fit["candidate_silhouette"]["outside_sample_count"]
  centerline_outside_count = centerline_silhouette["outside_sample_count"]
  latest_outside_count = latest_silhouette["outside_sample_count"]
  status = _subcomponent_shape_design_status(
    current_outside_count=current_outside_count,
    candidate_outside_count=candidate_outside_count,
    center_shift_m=fit["center_shift_candidate_m"],
  )
  centerline_status = _subcomponent_centerline_design_status(
    candidate_outside_count=candidate_outside_count,
    centerline_outside_count=centerline_outside_count,
  )
  centerline_shift_m = math.sqrt(
    sum(float(value) ** 2 for value in centerline_rule["center_offset_m"])
  )
  latest_incremental_shift_m = math.sqrt(
    sum(
      float(value) ** 2
      for value in latest_rule["center_offset_from_centerline_m"]
    )
  )
  latest_total_center_offset = [
    float(centerline_rule["center_offset_m"][index])
    + float(latest_rule["center_offset_from_centerline_m"][index])
    for index in range(3)
  ]
  latest_status = _subcomponent_latest_status(latest_outside_count)
  return {
    "item_id": row["item_id"],
    "record_type": row["record_type"],
    "parent_component_name": row["parent_component_name"],
    "system": row["system"],
    "component_role": row["component_role"],
    "bound_region_id": row["bound_region_id"],
    "owner_region_ids": row["owner_region_ids"],
    "current_shape": row["prior_shape"],
    "current_axis": row["prior_axis"],
    "candidate_shape_family": rule["candidate_shape_family"],
    "candidate_evaluation_shape": rule["evaluation_shape"],
    "candidate_evaluation_axis": rule["evaluation_axis"],
    "nominal_dimensions_m": row["nominal_dimensions_m"],
    "dimension_policy": (
      "preserve_nominal_public_or_declared_prior_dimensions_no_shrink"
    ),
    "size_basis": row["size_basis"],
    "size_evidence_level": row["size_evidence_level"],
    "placement_policy": rule["placement_policy"],
    "design_rationale": rule["rationale"],
    "current_geometry": current_geometry,
    "candidate_geometry": candidate_geometry,
    "centerline_candidate_geometry": centerline_geometry,
    "latest_candidate_geometry": latest_geometry,
    "current_silhouette": row["current_silhouette"],
    "candidate_silhouette": fit["candidate_silhouette"],
    "centerline_candidate_silhouette": centerline_silhouette,
    "latest_candidate_silhouette": latest_silhouette,
    "candidate_center_shift_m": fit["center_shift_candidate_m"],
    "centerline_candidate_center_offset_m": _round_vec(
      centerline_rule["center_offset_m"]
    ),
    "centerline_candidate_shift_m": _round(centerline_shift_m),
    "centerline_candidate_source_basis": centerline_rule["source_basis"],
    "centerline_candidate_placement_policy": (
      centerline_rule["placement_policy"]
    ),
    "centerline_candidate_rationale": centerline_rule["rationale"],
    "latest_candidate_stage": latest_rule["stage"],
    "latest_candidate_center_offset_from_centerline_m": _round_vec(
      latest_rule["center_offset_from_centerline_m"]
    ),
    "latest_candidate_total_center_offset_m": _round_vec(
      latest_total_center_offset
    ),
    "latest_candidate_incremental_shift_m": _round(
      latest_incremental_shift_m
    ),
    "latest_candidate_source_basis": latest_rule["source_basis"],
    "latest_candidate_placement_policy": latest_rule["placement_policy"],
    "latest_candidate_rationale": latest_rule["rationale"],
    "outside_sample_reduction": (
      current_outside_count - candidate_outside_count
    ),
    "centerline_outside_sample_reduction": (
      current_outside_count - centerline_outside_count
    ),
    "centerline_incremental_outside_sample_reduction": (
      candidate_outside_count - centerline_outside_count
    ),
    "latest_outside_sample_reduction": (
      current_outside_count - latest_outside_count
    ),
    "latest_incremental_outside_sample_reduction": (
      centerline_outside_count - latest_outside_count
    ),
    "shape_design_status": status,
    "centerline_candidate_status": centerline_status,
    "latest_candidate_status": latest_status,
    "recommended_action": _subcomponent_shape_design_recommended_action(status),
    "centerline_candidate_recommended_action": (
      _subcomponent_centerline_recommended_action(centerline_status)
    ),
    "latest_candidate_recommended_action": (
      _subcomponent_latest_recommended_action(latest_status)
    ),
    "runtime_projection_status": (
      "review_only_subcomponent_shape_candidate_not_runtime_active"
    ),
    "authority_boundary": (
      "shape_design_candidate_preserves_nominal_dimensions_but_is_not_true_internal_engineering_geometry"
    ),
  }


def build_subcomponent_shape_placement_candidate_report(
  mapping: dict[str, Any],
  fine_proxy: dict[str, Any],
  airframe_constraint_report: dict[str, Any],
) -> dict[str, Any]:
  airframe_projection_hulls = _whole_airframe_projection_hulls(fine_proxy)
  rows = [
    _subcomponent_shape_candidate_row(
      row,
      airframe_projection_hulls=airframe_projection_hulls,
    )
    for row in airframe_constraint_report["rows"]
    if row["current_silhouette"]["outside_sample_count"] > 0
  ]
  status_values = sorted({row["shape_design_status"] for row in rows})
  centerline_status_values = sorted(
    {row["centerline_candidate_status"] for row in rows}
  )
  latest_status_values = sorted({row["latest_candidate_status"] for row in rows})
  shape_families = sorted({row["candidate_shape_family"] for row in rows})
  if rows:
    manual_review_queue = [
      {
        "priority": "high",
        "question": "Review any remaining shape-placement candidates before applying them to the internal prior or held-segment rules.",
      },
      {
        "priority": "high",
        "question": "For unresolved candidates, research better true dimensions, tapered cross-sections, or cross-region centerlines rather than shrinking nominal dimensions.",
      },
      {
        "priority": "high",
        "question": "Review R19 centerline candidates separately; they preserve dimensions but change semantic placement and are not accepted runtime geometry.",
      },
      {
        "priority": "high",
        "question": "R20 latest candidates promoted in R21 are retained here only when new exposure remains after the review-only rule update.",
      },
      {
        "priority": "medium",
        "question": "Keep runtime damage behavior unchanged until these shape candidates are explicitly accepted.",
      },
    ]
  else:
    manual_review_queue = [
      {
        "priority": "high",
        "question": "No remaining shape-placement candidates after R21 review-only rule promotion; continue to hold runtime activation for explicit ownership decisions.",
      },
      {
        "priority": "medium",
        "question": "Keep runtime damage behavior unchanged until the promoted review-only rules are explicitly accepted, split, or deliberately held with tests.",
      },
    ]
  return {
    "schema_version": SUBCOMPONENT_SHAPE_PLACEMENT_SCHEMA_VERSION,
    "status": "subcomponent_shape_placement_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_airframe_constraint_correction_schema_version": (
      airframe_constraint_report["schema_version"]
    ),
    "source_fine_proxy_schema_version": fine_proxy["schema_version"],
    "summary": {
      "source_constraint_item_count": airframe_constraint_report["summary"][
        "item_count"
      ],
      "source_silhouette_exposure_item_count": airframe_constraint_report[
        "summary"
      ]["silhouette_exposure_item_count"],
      "shape_placement_candidate_count": len(rows),
      "nominal_dimension_preserved_count": len(rows),
      "candidate_reduces_exposure_count": sum(
        1 for row in rows if row["outside_sample_reduction"] > 0
      ),
      "candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "candidate_no_improvement_count": sum(
        1 for row in rows if row["outside_sample_reduction"] <= 0
      ),
      "current_total_outside_sample_count": sum(
        row["current_silhouette"]["outside_sample_count"] for row in rows
      ),
      "candidate_total_outside_sample_count": sum(
        row["candidate_silhouette"]["outside_sample_count"] for row in rows
      ),
      "candidate_total_outside_sample_reduction": sum(
        row["outside_sample_reduction"] for row in rows
      ),
      "centerline_candidate_count": len(rows),
      "centerline_candidate_reduces_exposure_count": sum(
        1
        for row in rows
        if row["centerline_incremental_outside_sample_reduction"] > 0
      ),
      "centerline_candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["centerline_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "centerline_candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["centerline_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "centerline_candidate_total_outside_sample_count": sum(
        row["centerline_candidate_silhouette"]["outside_sample_count"]
        for row in rows
      ),
      "centerline_candidate_total_outside_sample_reduction": sum(
        row["centerline_outside_sample_reduction"] for row in rows
      ),
      "centerline_candidate_incremental_outside_sample_reduction": sum(
        row["centerline_incremental_outside_sample_reduction"]
        for row in rows
      ),
      "latest_candidate_count": len(rows),
      "latest_candidate_resolves_exposure_count": sum(
        1
        for row in rows
        if row["latest_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "latest_candidate_unresolved_exposure_count": sum(
        1
        for row in rows
        if row["latest_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "latest_candidate_total_outside_sample_count": sum(
        row["latest_candidate_silhouette"]["outside_sample_count"]
        for row in rows
      ),
      "latest_candidate_total_outside_sample_reduction": sum(
        row["latest_outside_sample_reduction"] for row in rows
      ),
      "latest_candidate_incremental_outside_sample_reduction": sum(
        row["latest_incremental_outside_sample_reduction"] for row in rows
      ),
      "candidate_shape_family_counts": {
        family: sum(1 for row in rows if row["candidate_shape_family"] == family)
        for family in shape_families
      },
      "shape_design_status_counts": {
        status: sum(1 for row in rows if row["shape_design_status"] == status)
        for status in status_values
      },
      "centerline_candidate_status_counts": {
        status: sum(
          1 for row in rows if row["centerline_candidate_status"] == status
        )
        for status in centerline_status_values
      },
      "latest_candidate_status_counts": {
        status: sum(
          1 for row in rows if row["latest_candidate_status"] == status
        )
        for status in latest_status_values
      },
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": manual_review_queue,
    "authority_boundary": {
      **airframe_constraint_report["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "nominal_dimensions_preserved": True,
      "shape_candidate_not_applied_to_internal_prior_rules": False,
      "centerline_candidate_not_applied_to_internal_prior_rules": False,
      "latest_candidate_not_applied_to_internal_prior_rules": False,
      "latest_candidate_promoted_to_internal_prior_or_segment_rules": True,
    },
  }


def _child_prior_projection_role(index: int, child_count: int) -> str:
  if child_count <= 1:
    return "single_receiver_overlay"
  if index == 0:
    return "primary_receiver_overlay"
  return "extra_receiver_overlay"


def build_semantic_parent_child_layout_candidate(
  mapping: dict[str, Any],
  semantic_report: dict[str, Any],
  internal_prior_report: dict[str, Any],
  held_segment_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
  priors_by_region: dict[str, list[dict[str, Any]]] = {}
  for prior_row in internal_prior_report["rows"]:
    priors_by_region.setdefault(prior_row["bound_region_id"], []).append(prior_row)
  held_segments_by_parent: dict[str, list[dict[str, Any]]] = {}
  held_segments_by_owner_region: dict[str, list[dict[str, Any]]] = {}
  if held_segment_report is not None:
    for segment_row in held_segment_report["rows"]:
      held_segments_by_parent.setdefault(
        segment_row["parent_component_name"],
        [],
      ).append(segment_row)
      for owner_region_id in segment_row["owner_region_ids"]:
        held_segments_by_owner_region.setdefault(owner_region_id, []).append(
          segment_row
        )

  rows: list[dict[str, Any]] = []
  for semantic_row in semantic_report["rows"]:
    region_id = semantic_row["source_region_id"]
    child_priors = priors_by_region.get(region_id, [])
    child_count = len(child_priors)
    child_receiver_priors = []
    for index, prior_row in enumerate(child_priors):
      held_segments = held_segments_by_parent.get(
        prior_row["component_name"],
        [],
      )
      child_receiver_priors.append(
        {
          "component_name": prior_row["component_name"],
          "system": prior_row["system"],
          "component_role": prior_row["component_role"],
          "prior_shape": prior_row["prior_shape"],
          "prior_axis": prior_row["prior_axis"],
          "size_basis": prior_row["size_basis"],
          "size_evidence_level": prior_row["size_evidence_level"],
          "size_source_urls": prior_row["size_source_urls"],
          "nominal_dimensions_m": prior_row["nominal_dimensions_m"],
          "constraint_status": prior_row["constraint_status"],
          "component_review_semantics": prior_row["component_review_semantics"],
          "layout_role": _child_prior_projection_role(index, child_count),
          "is_cross_region_held": (
            prior_row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          ),
          "constraint_region_ids": prior_row["constraint_region_ids"],
          "placement_bounds": prior_row["placement_bounds"],
          "placement_bounds_source": prior_row["placement_bounds_source"],
          "whole_airframe_bounds": prior_row["whole_airframe_bounds"],
          "constrained_geometry": prior_row["constrained_geometry"],
          "held_segments": held_segments,
          "held_segment_count": len(held_segments),
          "constraint_adjustment": prior_row["constraint_adjustment"],
          "runtime_projection_status": prior_row["runtime_projection_status"],
        }
      )
    child_names = {prior_row["component_name"] for prior_row in child_priors}
    cross_region_held_segment_overlays = [
      segment_row
      for segment_row in held_segments_by_owner_region.get(region_id, [])
      if segment_row["parent_component_name"] not in child_names
    ]
    rows.append(
      {
        "parent_semantic_component_id": semantic_row["semantic_component_id"],
        "parent_surface_component_id": semantic_row["surface_component_id"],
        "source_region_id": region_id,
        "volume_component_role": semantic_row["volume_component_role"],
        "geometry_primitive": semantic_row["geometry_primitive"],
        "source_proxy_kind": semantic_row["source_proxy_kind"],
        "support_bounds": semantic_row["support_bounds"],
        "source_region_bounds": semantic_row["source_region_bounds"],
        "whole_airframe_bounds": internal_prior_report["whole_airframe_bounds"],
        "parent_runtime_projection_status": semantic_row[
          "runtime_projection_status"
        ],
        "parent_receiver_handoff_status": semantic_row["receiver_handoff_status"],
        "bound_receiver_count": child_count,
        "extra_receiver_slot_count": max(child_count - 1, 0),
        "primary_receiver_component_name": (
          child_priors[0]["component_name"] if child_priors else ""
        ),
        "extra_receiver_component_names": [
          prior_row["component_name"] for prior_row in child_priors[1:]
        ],
        "cross_region_held_receiver_names": [
          prior_row["component_name"]
          for prior_row in child_priors
          if prior_row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
        ],
        "cross_region_held_segment_overlays": cross_region_held_segment_overlays,
        "cross_region_held_segment_overlay_count": len(
          cross_region_held_segment_overlays
        ),
        "child_receiver_priors": child_receiver_priors,
        "layout_policy": (
          "one_parent_semantic_shell_view_with_receiver_priors_overlaid"
        ),
        "runtime_projection_status": (
          "review_only_visual_layout_not_runtime_activation"
        ),
        "authority_boundary": (
          "display_grouping_only_parent_child_damage_ownership_not_accepted"
        ),
      }
    )

  return {
    "schema_version": SEMANTIC_PARENT_CHILD_LAYOUT_SCHEMA_VERSION,
    "status": "semantic_parent_child_layout_candidate_generated_review_only",
    "generated_on": mapping["generated_on"],
    "asset_ref": mapping["asset_ref"],
    "coordinate_frame": mapping["coordinate_frame"],
    "source_semantic_damage_geometry_schema_version": semantic_report[
      "schema_version"
    ],
    "source_internal_component_prior_schema_version": internal_prior_report[
      "schema_version"
    ],
    "source_cross_region_held_segment_schema_version": (
      held_segment_report["schema_version"] if held_segment_report else ""
    ),
    "summary": {
      "parent_semantic_component_count": len(rows),
      "bound_receiver_component_count": sum(
        row["bound_receiver_count"] for row in rows
      ),
      "extra_receiver_slot_count": sum(
        row["extra_receiver_slot_count"] for row in rows
      ),
      "parent_without_receiver_count": sum(
        1 for row in rows if row["bound_receiver_count"] == 0
      ),
      "cross_region_held_receiver_count": sum(
        len(row["cross_region_held_receiver_names"]) for row in rows
      ),
      "cross_region_held_segment_count": (
        held_segment_report["summary"]["held_segment_count"]
        if held_segment_report
        else 0
      ),
      "cross_region_held_segment_overlay_count": sum(
        row["cross_region_held_segment_overlay_count"] for row in rows
      ),
      "runtime_active_component_count": 0,
      "review_status": "manual_review_required_before_activation",
    },
    "rows": rows,
    "manual_review_queue": [
      {
        "priority": "high",
        "question": "Review the 14 parent shell pages as the primary geometry surface; do not review the 26 receiver priors as independent top-level parts.",
      },
      {
        "priority": "high",
        "question": "Treat extra receiver slots as overlays inside the parent shell, not as accepted parent-child damage ownership.",
      },
      {
        "priority": "high",
        "question": "Keep red cross-region held receivers unactivated until engine_core and wing_spar_center ownership is split or explicitly accepted.",
      },
    ],
    "authority_boundary": {
      **mapping["authority_boundary"],
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "public_size_reference_seeded_geometry": True,
      "parent_child_damage_ownership": False,
    },
  }


def _source_metadata(intake_metadata: dict[str, Any]) -> dict[str, Any]:
  user = intake_metadata.get("user", {})
  license_record = intake_metadata.get("license", {})
  return {
    "title": intake_metadata.get("name", ""),
    "uid": intake_metadata.get("uid", ""),
    "viewer_url": intake_metadata.get("viewerUrl", ""),
    "author": user.get("displayName", ""),
    "author_profile": user.get("profileUrl", ""),
    "license": {
      "label": license_record.get("label", ""),
      "full_name": license_record.get("fullName", ""),
      "url": license_record.get("url", ""),
      "requirements": license_record.get("requirements", ""),
    },
    "created_at": intake_metadata.get("createdAt", ""),
    "published_at": intake_metadata.get("publishedAt", ""),
    "downloaded_at": intake_metadata.get("downloadedAt", ""),
  }


def build_airframe_geometry_manifest(
  *,
  aircraft_path: Path = DEFAULT_AIRCRAFT,
  audit_scene_path: Path = DEFAULT_AUDIT_SCENE,
  visual_glb_path: Path = DEFAULT_VISUAL_GLB,
  intake_metadata_path: Path = DEFAULT_INTAKE_METADATA,
  registry_path: Path = DEFAULT_REGISTRY,
  repo_root: Path = REPO_ROOT,
  generated_on: str = DEFAULT_GENERATED_ON,
) -> dict[str, Any]:
  aircraft = _load_json(aircraft_path)
  intake_metadata = _load_json(intake_metadata_path)
  registry = _load_json(registry_path)
  gltf_summary = summarize_gltf_scene(audit_scene_path)
  registry_entry = _find_registry_entry(registry, visual_glb_path, repo_root)

  public_dimensions = {
    "length_m": float(aircraft["airframe"]["length_m"]),
    "wingspan_m": float(aircraft["airframe"]["wingspan_m"]),
    "height_m": float(aircraft["airframe"]["height_m"]),
    "reference_area_m2": float(aircraft["airframe"]["reference_area"]),
  }
  transformed_span = gltf_summary["transformed_bounds"]["span"]
  registry_scale = float(registry_entry.get("visual", {}).get("scale", 1.0))
  length_fit_scale = public_dimensions["length_m"] / transformed_span[2]
  scaled_review_dimensions = {
    "length_m": transformed_span[2] * registry_scale,
    "wingspan_m": transformed_span[0] * registry_scale,
    "height_m": transformed_span[1] * registry_scale,
  }
  dimension_errors = {
    key: _round(_percent_error(scaled_review_dimensions[key], public_dimensions[key]))
    for key in ("length_m", "wingspan_m", "height_m")
  }

  hitbox_summary = _hitbox_envelope(aircraft.get("damage_model", {}).get("hitboxes", []))
  hitbox_span = hitbox_summary["combined_envelope"]["span"]

  manifest = {
    "schema_version": SCHEMA_VERSION,
    "status": "target_geometry_manifest_generated_review_only",
    "generated_on": generated_on,
    "asset_source_status": "verified_redistributable_visual_reference",
    "review_scope": "f16c_outer_shape_scale_axis_manifest_only",
    "source": _source_metadata(intake_metadata),
    "source_geometry_hints": {
      "face_count": intake_metadata.get("faceCount"),
      "vertex_count": intake_metadata.get("vertexCount"),
      "metadata_notable_node_names": intake_metadata.get("localGeometrySummary", {}).get(
        "notableNodeNames", []
      ),
      "metadata_scene": intake_metadata.get("localGeometrySummary", {}).get("scene", ""),
      "note": (
        "The retained glTF scene may use generic Object_* node names; source "
        "metadata hints are review aids and must not be treated as true "
        "component boundaries."
      ),
    },
    "paths": {
      "aircraft_database": _display_path(aircraft_path, repo_root),
      "runtime_visual_glb": _display_path(visual_glb_path, repo_root),
      "audit_scene_gltf": _display_path(audit_scene_path, repo_root),
      "intake_metadata": _display_path(intake_metadata_path, repo_root),
      "registry": _display_path(registry_path, repo_root),
    },
    "file_hashes": {
      "runtime_visual_glb_sha256": _sha256_file(visual_glb_path),
      "audit_scene_gltf_sha256": _sha256_file(audit_scene_path),
      "intake_metadata_sha256": _sha256_file(intake_metadata_path),
      "aircraft_database_sha256": _sha256_file(aircraft_path),
    },
    "registry_entry": {
      "id": registry_entry.get("id", ""),
      "label": registry_entry.get("label", ""),
      "asset_path": registry_entry.get("visual", {}).get("asset_path", ""),
      "scale": registry_scale,
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "realism_note": registry_entry.get("realism_note", ""),
    },
    "gltf_summary": gltf_summary,
    "axis_alignment": {
      "convention": "project_review_axis_map_v1",
      "asset_x": "sim_right",
      "asset_y": "sim_up",
      "asset_z_negative": "sim_forward",
      "nose_direction": "negative_asset_z",
      "tail_engine_direction": "positive_asset_z",
      "yaw_correction_deg": registry_entry.get("visual", {}).get("yaw_correction_deg", 0.0),
      "runtime_registry_scale": registry_scale,
    },
    "public_dimension_check": {
      "public_dimensions": public_dimensions,
      "asset_transformed_span": {
        "asset_x_right_span": _round(transformed_span[0]),
        "asset_y_up_span": _round(transformed_span[1]),
        "asset_z_forward_length_span": _round(transformed_span[2]),
      },
      "length_fit_scale": _round(length_fit_scale),
      "registry_scale": registry_scale,
      "scale_delta_percent": _round(_percent_error(registry_scale, length_fit_scale)),
      "scaled_review_dimensions": {
        key: _round(value) for key, value in scaled_review_dimensions.items()
      },
      "scaled_dimension_error_percent": dimension_errors,
      "scale_basis": "registry_scale_matches_public_length_order_and_preserves_frontend_visual_size",
    },
    "current_damage_geometry": {
      "source": "damage_model.hitboxes",
      "summary": hitbox_summary,
      "public_dimension_error_percent": {
        "length_m": _round(_percent_error(hitbox_span[0], public_dimensions["length_m"])),
        "wingspan_m": _round(_percent_error(hitbox_span[1], public_dimensions["wingspan_m"])),
        "height_m": _round(_percent_error(hitbox_span[2], public_dimensions["height_m"])),
      },
      "known_gap": "current_axis_aligned_hitboxes_cover_core_damage_scaffold_but_understate_full_aircraft_height",
    },
    "authority_boundary": {
      "runtime_collision_mesh": False,
      "true_f16_engineering_geometry": False,
      "true_internal_component_boundaries": False,
      "real_weapon_pk_authority": False,
      "structural_breakup_or_debris_claim": False,
      "allowed_use": [
        "outer_shape_review",
        "scale_and_axis_audit",
        "component_binding_review_input",
        "test_point_distance_diagnostic_input",
      ],
    },
  }
  return manifest


def write_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "manifest.json"
  output_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_mapping_candidate(mapping: dict[str, Any], output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "f16c_geometry_mapping_candidate_20260611.json"
  output_path.write_text(
    json.dumps(mapping, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_component_binding_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "component_binding_report_20260611.json"
  csv_path = output_dir / "component_binding_report_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "component_name",
    "system",
    "critical",
    "hitbox_index",
    "bound_region_id",
    "bound_region_role",
    "component_overlap_fraction",
    "region_overlap_fraction",
    "center_inside_bound_region",
    "center_distance_m",
    "outer_envelope_containment_fraction",
    "review_status",
    "review_semantics",
    "review_severity",
    "anomalies",
    "geometry_observations",
    "suppressed_anomalies",
    "semantic_region_ids",
    "side_sign_mismatch",
    "blocked_region_binding",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(row[key])
            if key
            in {
              "anomalies",
              "geometry_observations",
              "suppressed_anomalies",
              "semantic_region_ids",
            }
            else row["side_sign_relation"]["side_sign_mismatch"]
            if key == "side_sign_mismatch"
            else json.dumps(row[key], sort_keys=True)
            if key == "blocked_region_binding"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def write_review_point_diagnostics(
  diagnostics: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "review_point_diagnostics_20260611.json"
  csv_path = output_dir / "review_point_diagnostics_20260611.csv"
  json_path.write_text(
    json.dumps(diagnostics, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "point_index",
    "point_id",
    "aspect",
    "point_m",
    "nearest_outer_region_id",
    "nearest_outer_distance_m",
    "inside_outer_region_count",
    "nearest_component_name",
    "nearest_component_distance_m",
    "inside_component_count",
    "candidate_component_count",
    "interpretation",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in diagnostics["rows"]:
      writer.writerow(
        {
          key: (
            ";".join(str(value) for value in row[key])
            if key == "point_m"
            else row[key]
          )
          for key in fieldnames
        }
      )
  return json_path, csv_path


def write_fine_geometry_proxy_candidate(
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / "fine_geometry_proxy_candidate_20260611.json"
  output_path.write_text(
    json.dumps(fine_proxy, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )
  return output_path


def write_surface_component_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "surface_component_candidate_20260611.json"
  csv_path = output_dir / "surface_component_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "surface_component_id",
    "source_region_id",
    "source_region_role",
    "surface_role",
    "proxy_kind",
    "linked_internal_component_count",
    "clean_direct_link_count",
    "clean_direct_component_names",
    "cross_region_semantic_component_names",
    "blocked_component_names",
    "bad_geometry_component_names",
    "missing_existing_runtime_component_relations",
    "runtime_relation_status",
    "review_status",
    "review_semantics",
    "review_flags",
    "expected_damage_modes",
    "linked_internal_components",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "surface_component_id": row["surface_component_id"],
          "source_region_id": row["source_region_id"],
          "source_region_role": row["source_region_role"],
          "surface_role": row["surface_role"],
          "proxy_kind": row["proxy_kind"],
          "linked_internal_component_count": row[
            "linked_internal_component_count"
          ],
          "clean_direct_link_count": row["clean_direct_link_count"],
          "clean_direct_component_names": ";".join(
            row["clean_direct_component_names"]
          ),
          "cross_region_semantic_component_names": ";".join(
            row["cross_region_semantic_component_names"]
          ),
          "blocked_component_names": ";".join(row["blocked_component_names"]),
          "bad_geometry_component_names": ";".join(
            row["bad_geometry_component_names"]
          ),
          "missing_existing_runtime_component_relations": ";".join(
            row["missing_existing_runtime_component_relations"]
          ),
          "runtime_relation_status": row["runtime_relation_status"],
          "review_status": row["review_status"],
          "review_semantics": row["review_semantics"],
          "review_flags": ";".join(row["review_flags"]),
          "expected_damage_modes": ";".join(row["expected_damage_modes"]),
          "linked_internal_components": ";".join(
            link["component_name"] for link in row["linked_internal_components"]
          ),
        }
      )
  return json_path, csv_path


def write_semantic_damage_geometry_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "semantic_damage_geometry_candidate_20260611.json"
  csv_path = output_dir / "semantic_damage_geometry_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "semantic_component_id",
    "surface_component_id",
    "source_region_id",
    "volume_component_role",
    "runtime_system",
    "geometry_primitive",
    "direct_receiver_components",
    "cross_region_receiver_components",
    "receiver_handoff_status",
    "runtime_projection_status",
    "support_center_m",
    "support_span_m",
    "mesh_region_vertex_count",
    "surface_review_semantics",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "semantic_component_id": row["semantic_component_id"],
          "surface_component_id": row["surface_component_id"],
          "source_region_id": row["source_region_id"],
          "volume_component_role": row["volume_component_role"],
          "runtime_system": row["runtime_system"],
          "geometry_primitive": row["geometry_primitive"],
          "direct_receiver_components": ";".join(
            row["direct_receiver_components"]
          ),
          "cross_region_receiver_components": ";".join(
            row["cross_region_receiver_components"]
          ),
          "receiver_handoff_status": row["receiver_handoff_status"],
          "runtime_projection_status": row["runtime_projection_status"],
          "support_center_m": ";".join(
            str(value) for value in row["support_bounds"]["center"]
          ),
          "support_span_m": ";".join(
            str(value) for value in row["support_bounds"]["span"]
          ),
          "mesh_region_vertex_count": row["mesh_region_vertex_count"],
          "surface_review_semantics": row["surface_review_semantics"],
        }
      )
  return json_path, csv_path


def write_internal_component_prior_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "internal_component_prior_candidate_20260611.json"
  csv_path = output_dir / "internal_component_prior_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "component_name",
    "system",
    "component_role",
    "prior_shape",
    "prior_axis",
    "shape_promotion_status",
    "size_basis",
    "size_evidence_level",
    "nominal_dimensions_m",
    "size_source_urls",
    "bound_region_id",
    "constraint_region_ids",
    "constraint_mode",
    "constraint_bounds_source",
    "placement_bounds_source",
    "constraint_status",
    "original_aabb_containment_fraction",
    "shrink_scale",
    "required_fit_scale",
    "size_preserved",
    "center_shift_m",
    "airframe_projection_center_shift_m",
    "placement_outside_fraction",
    "pre_constraint_outside_fraction",
    "post_constraint_outside_fraction",
    "constrained_center_m",
    "constrained_span_m",
    "component_review_semantics",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "component_name": row["component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "prior_shape": row["prior_shape"],
          "prior_axis": row["prior_axis"],
          "shape_promotion_status": row["shape_promotion_status"],
          "size_basis": row["size_basis"],
          "size_evidence_level": row["size_evidence_level"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_source_urls": ";".join(row["size_source_urls"]),
          "bound_region_id": row["bound_region_id"],
          "constraint_region_ids": ";".join(row["constraint_region_ids"]),
          "constraint_mode": row["constraint_mode"],
          "constraint_bounds_source": row["constraint_bounds_source"],
          "placement_bounds_source": row["placement_bounds_source"],
          "constraint_status": row["constraint_status"],
          "original_aabb_containment_fraction": row[
            "original_aabb_containment_fraction"
          ],
          "shrink_scale": row["constraint_adjustment"]["shrink_scale"],
          "required_fit_scale": row["constraint_adjustment"]["required_fit_scale"],
          "size_preserved": row["constraint_adjustment"]["size_preserved"],
          "center_shift_m": row["constraint_adjustment"]["center_shift_m"],
          "airframe_projection_center_shift_m": row["constraint_adjustment"][
            "airframe_projection_center_shift_m"
          ],
          "placement_outside_fraction": row["constraint_adjustment"][
            "placement_outside_fraction"
          ],
          "pre_constraint_outside_fraction": row["constraint_adjustment"][
            "pre_constraint_outside_fraction"
          ],
          "post_constraint_outside_fraction": row["constraint_adjustment"][
            "post_constraint_outside_fraction"
          ],
          "constrained_center_m": ";".join(
            str(value) for value in row["constrained_geometry"]["center_m"]
          ),
          "constrained_span_m": ";".join(
            str(value) for value in row["constrained_geometry"]["bounds"]["span"]
          ),
          "component_review_semantics": row["component_review_semantics"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_cross_region_held_component_segments_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "cross_region_held_component_segments_20260611.json"
  csv_path = output_dir / "cross_region_held_component_segments_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "segment_id",
    "segment_index",
    "segment_role",
    "owner_region_ids",
    "segment_shape",
    "segment_axis",
    "source_parent_segment_shape",
    "shape_promotion_status",
    "center_offset_m",
    "nominal_dimensions_m",
    "center_m",
    "span_m",
    "inside_parent_prior_bounds",
    "inside_whole_airframe_bounds",
    "parent_prior_outside_fraction",
    "whole_airframe_outside_fraction",
    "source_basis",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "segment_id": row["segment_id"],
          "segment_index": row["segment_index"],
          "segment_role": row["segment_role"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "segment_shape": row["segment_shape"],
          "segment_axis": row["segment_axis"],
          "source_parent_segment_shape": row["source_parent_segment_shape"],
          "shape_promotion_status": row["shape_promotion_status"],
          "center_offset_m": ";".join(
            str(value) for value in row["center_offset_m"]
          ),
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "center_m": ";".join(str(value) for value in row["geometry"]["center_m"]),
          "span_m": ";".join(
            str(value) for value in row["geometry"]["bounds"]["span"]
          ),
          "inside_parent_prior_bounds": row["inside_parent_prior_bounds"],
          "inside_whole_airframe_bounds": row["inside_whole_airframe_bounds"],
          "parent_prior_outside_fraction": row["parent_prior_outside_fraction"],
          "whole_airframe_outside_fraction": row[
            "whole_airframe_outside_fraction"
          ],
          "source_basis": row["source_basis"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_cross_region_ownership_split_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "cross_region_ownership_split_candidate_20260611.json"
  csv_path = output_dir / "cross_region_ownership_split_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "parent_system",
    "parent_review_semantics",
    "recommended_ownership_decision",
    "decision_status",
    "parent_receiver_runtime_policy",
    "segment_count",
    "candidate_runtime_component_names",
    "owner_region_ids",
    "parse_ready_runtime_candidate_count",
    "silhouette_exposure_segment_count",
    "outside_whole_airframe_segment_count",
    "shape_promotion_segment_count",
    "runtime_active_split_component_count",
    "runtime_activation_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "parent_system": row["parent_system"],
          "parent_review_semantics": row["parent_review_semantics"],
          "recommended_ownership_decision": row[
            "recommended_ownership_decision"
          ],
          "decision_status": row["decision_status"],
          "parent_receiver_runtime_policy": row["parent_receiver_runtime_policy"],
          "segment_count": row["segment_count"],
          "candidate_runtime_component_names": ";".join(
            row["candidate_runtime_component_names"]
          ),
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "parse_ready_runtime_candidate_count": row[
            "parse_ready_runtime_candidate_count"
          ],
          "silhouette_exposure_segment_count": row[
            "silhouette_exposure_segment_count"
          ],
          "outside_whole_airframe_segment_count": row[
            "outside_whole_airframe_segment_count"
          ],
          "shape_promotion_segment_count": row["shape_promotion_segment_count"],
          "runtime_active_split_component_count": row[
            "runtime_active_split_component_count"
          ],
          "runtime_activation_status": row["runtime_activation_status"],
        }
      )
  return json_path, csv_path


def write_target_geometry_runtime_activation_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "target_geometry_runtime_activation_candidate_20260613.json"
  csv_path = output_dir / "target_geometry_runtime_activation_candidate_20260613.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "candidate_component_name",
    "parent_component_name",
    "parent_system",
    "recommended_ownership_decision",
    "parent_receiver_runtime_policy",
    "segment_role",
    "owner_region_ids",
    "geometry_primitive",
    "offset_m",
    "size_m",
    "runtime_loader_contract_status",
    "runtime_activation_status",
    "behavior_test_status",
    "feature_flag",
    "unit_database_patch_path",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "candidate_component_name": row["candidate_component_name"],
          "parent_component_name": row["parent_component_name"],
          "parent_system": row["parent_system"],
          "recommended_ownership_decision": row[
            "recommended_ownership_decision"
          ],
          "parent_receiver_runtime_policy": row[
            "parent_receiver_runtime_policy"
          ],
          "segment_role": row["segment_role"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "geometry_primitive": row["geometry_primitive"],
          "offset_m": ";".join(str(value) for value in row["offset_m"]),
          "size_m": ";".join(str(value) for value in row["size_m"]),
          "runtime_loader_contract_status": row[
            "runtime_loader_contract_status"
          ],
          "runtime_activation_status": row["runtime_activation_status"],
          "behavior_test_status": row["behavior_test_status"],
          "feature_flag": row["feature_flag"],
          "unit_database_patch_path": row["unit_database_patch_path"],
        }
      )
  return json_path, csv_path


def write_target_geometry_runtime_behavior_regression_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "target_geometry_runtime_behavior_regression_20260613.json"
  csv_path = output_dir / "target_geometry_runtime_behavior_regression_20260613.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_component_name",
    "target_hitbox_index",
    "target_path",
    "base_hitbox_component_count",
    "patched_hitbox_component_count",
    "parent_present_before_patch",
    "parent_absent_after_patch",
    "split_component_names",
    "split_component_present_count",
    "duplicate_component_name_count",
    "behavior_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_component_name": row["parent_component_name"],
          "target_hitbox_index": row["target_hitbox_index"],
          "target_path": row["target_path"],
          "base_hitbox_component_count": row[
            "base_hitbox_component_count"
          ],
          "patched_hitbox_component_count": row[
            "patched_hitbox_component_count"
          ],
          "parent_present_before_patch": row["parent_present_before_patch"],
          "parent_absent_after_patch": row["parent_absent_after_patch"],
          "split_component_names": ";".join(row["split_component_names"]),
          "split_component_present_count": row["split_component_present_count"],
          "duplicate_component_name_count": row[
            "duplicate_component_name_count"
          ],
          "behavior_status": row["behavior_status"],
        }
      )
  return json_path, csv_path


def write_target_geometry_training_proxy_database_report(
  report: dict[str, Any],
  proxy_aircraft: dict[str, Any],
  output_dir: Path,
  *,
  source_database_path: Path = DEFAULT_RUNTIME_DATABASE,
) -> tuple[dict[str, Any], Path, Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  proxy_database_dir = output_dir / "target_geometry_training_proxy_database_20260613"
  if proxy_database_dir.exists():
    shutil.rmtree(proxy_database_dir)
  shutil.copytree(source_database_path, proxy_database_dir)

  proxy_unit_path = proxy_database_dir / "aircraft" / "units" / "f16c_block50.json"
  proxy_unit_path.write_text(
    json.dumps(proxy_aircraft, indent=2, sort_keys=True, ensure_ascii=False)
    + "\n",
    encoding="utf-8",
  )

  materialized_report = copy.deepcopy(report)
  materialized_report["runtime_database"].update(
    {
      "proxy_database_path": _display_path(proxy_database_dir, REPO_ROOT),
      "proxy_f16c_unit_path": _display_path(proxy_unit_path, REPO_ROOT),
      "proxy_f16c_unit_sha256": _sha256_file(proxy_unit_path),
    }
  )
  materialized_report["summary"]["proxy_database_materialized"] = True
  materialized_report["summary"]["training_database_path_ready"] = True
  materialized_report["authority_boundary"][
    "training_proxy_database_generated"
  ] = True
  materialized_report["authority_boundary"][
    "training_proxy_runtime_active_component"
  ] = True

  json_path = output_dir / "target_geometry_training_proxy_database_20260613.json"
  json_path.write_text(
    json.dumps(materialized_report, indent=2, sort_keys=True, ensure_ascii=False)
    + "\n",
    encoding="utf-8",
  )
  return materialized_report, json_path, proxy_database_dir, proxy_unit_path


def write_airframe_constraint_correction_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "airframe_constraint_correction_candidate_20260611.json"
  csv_path = output_dir / "airframe_constraint_correction_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "item_id",
    "record_type",
    "parent_component_name",
    "system",
    "component_role",
    "prior_shape",
    "prior_axis",
    "nominal_dimensions_m",
    "size_evidence_level",
    "bound_region_id",
    "owner_region_ids",
    "current_outside_views",
    "current_outside_sample_count",
    "candidate_outside_views",
    "candidate_outside_sample_count",
    "outside_sample_reduction",
    "candidate_center_shift_m",
    "candidate_center_m",
    "triage_status",
    "recommended_action",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "item_id": row["item_id"],
          "record_type": row["record_type"],
          "parent_component_name": row["parent_component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "prior_shape": row["prior_shape"],
          "prior_axis": row["prior_axis"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_evidence_level": row["size_evidence_level"],
          "bound_region_id": row["bound_region_id"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "current_outside_views": ";".join(
            row["current_silhouette"]["outside_views"]
          ),
          "current_outside_sample_count": row["current_silhouette"][
            "outside_sample_count"
          ],
          "candidate_outside_views": ";".join(
            row["candidate_silhouette"]["outside_views"]
          ),
          "candidate_outside_sample_count": row["candidate_silhouette"][
            "outside_sample_count"
          ],
          "outside_sample_reduction": row["outside_sample_reduction"],
          "candidate_center_shift_m": row["candidate_center_shift_m"],
          "candidate_center_m": ";".join(
            str(value) for value in row["candidate_center_m"]
          ),
          "triage_status": row["triage_status"],
          "recommended_action": row["recommended_action"],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_subcomponent_shape_placement_candidate_report(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "subcomponent_shape_placement_candidate_20260611.json"
  csv_path = output_dir / "subcomponent_shape_placement_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "item_id",
    "record_type",
    "parent_component_name",
    "system",
    "component_role",
    "current_shape",
    "current_axis",
    "candidate_shape_family",
    "candidate_evaluation_shape",
    "candidate_evaluation_axis",
    "nominal_dimensions_m",
    "size_evidence_level",
    "bound_region_id",
    "owner_region_ids",
    "current_outside_views",
    "current_outside_sample_count",
    "candidate_outside_views",
    "candidate_outside_sample_count",
    "outside_sample_reduction",
    "candidate_center_shift_m",
    "candidate_center_m",
    "centerline_candidate_outside_views",
    "centerline_candidate_outside_sample_count",
    "centerline_candidate_center_offset_m",
    "centerline_candidate_center_m",
    "centerline_candidate_shift_m",
    "centerline_incremental_outside_sample_reduction",
    "centerline_outside_sample_reduction",
    "latest_candidate_stage",
    "latest_candidate_outside_views",
    "latest_candidate_outside_sample_count",
    "latest_candidate_center_m",
    "latest_candidate_total_center_offset_m",
    "latest_candidate_incremental_shift_m",
    "latest_incremental_outside_sample_reduction",
    "latest_outside_sample_reduction",
    "shape_design_status",
    "centerline_candidate_status",
    "latest_candidate_status",
    "recommended_action",
    "centerline_candidate_recommended_action",
    "latest_candidate_recommended_action",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "item_id": row["item_id"],
          "record_type": row["record_type"],
          "parent_component_name": row["parent_component_name"],
          "system": row["system"],
          "component_role": row["component_role"],
          "current_shape": row["current_shape"],
          "current_axis": row["current_axis"],
          "candidate_shape_family": row["candidate_shape_family"],
          "candidate_evaluation_shape": row["candidate_evaluation_shape"],
          "candidate_evaluation_axis": row["candidate_evaluation_axis"],
          "nominal_dimensions_m": ";".join(
            str(value) for value in row["nominal_dimensions_m"]
          ),
          "size_evidence_level": row["size_evidence_level"],
          "bound_region_id": row["bound_region_id"],
          "owner_region_ids": ";".join(row["owner_region_ids"]),
          "current_outside_views": ";".join(
            row["current_silhouette"]["outside_views"]
          ),
          "current_outside_sample_count": row["current_silhouette"][
            "outside_sample_count"
          ],
          "candidate_outside_views": ";".join(
            row["candidate_silhouette"]["outside_views"]
          ),
          "candidate_outside_sample_count": row["candidate_silhouette"][
            "outside_sample_count"
          ],
          "outside_sample_reduction": row["outside_sample_reduction"],
          "candidate_center_shift_m": row["candidate_center_shift_m"],
          "candidate_center_m": ";".join(
            str(value) for value in row["candidate_geometry"]["center_m"]
          ),
          "centerline_candidate_outside_views": ";".join(
            row["centerline_candidate_silhouette"]["outside_views"]
          ),
          "centerline_candidate_outside_sample_count": row[
            "centerline_candidate_silhouette"
          ]["outside_sample_count"],
          "centerline_candidate_center_offset_m": ";".join(
            str(value)
            for value in row["centerline_candidate_center_offset_m"]
          ),
          "centerline_candidate_center_m": ";".join(
            str(value)
            for value in row["centerline_candidate_geometry"]["center_m"]
          ),
          "centerline_candidate_shift_m": row[
            "centerline_candidate_shift_m"
          ],
          "centerline_incremental_outside_sample_reduction": row[
            "centerline_incremental_outside_sample_reduction"
          ],
          "centerline_outside_sample_reduction": row[
            "centerline_outside_sample_reduction"
          ],
          "latest_candidate_stage": row["latest_candidate_stage"],
          "latest_candidate_outside_views": ";".join(
            row["latest_candidate_silhouette"]["outside_views"]
          ),
          "latest_candidate_outside_sample_count": row[
            "latest_candidate_silhouette"
          ]["outside_sample_count"],
          "latest_candidate_center_m": ";".join(
            str(value) for value in row["latest_candidate_geometry"]["center_m"]
          ),
          "latest_candidate_total_center_offset_m": ";".join(
            str(value) for value in row["latest_candidate_total_center_offset_m"]
          ),
          "latest_candidate_incremental_shift_m": row[
            "latest_candidate_incremental_shift_m"
          ],
          "latest_incremental_outside_sample_reduction": row[
            "latest_incremental_outside_sample_reduction"
          ],
          "latest_outside_sample_reduction": row[
            "latest_outside_sample_reduction"
          ],
          "shape_design_status": row["shape_design_status"],
          "centerline_candidate_status": row[
            "centerline_candidate_status"
          ],
          "latest_candidate_status": row["latest_candidate_status"],
          "recommended_action": row["recommended_action"],
          "centerline_candidate_recommended_action": row[
            "centerline_candidate_recommended_action"
          ],
          "latest_candidate_recommended_action": row[
            "latest_candidate_recommended_action"
          ],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def write_semantic_parent_child_layout_candidate(
  report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  json_path = output_dir / "semantic_parent_child_layout_candidate_20260611.json"
  csv_path = output_dir / "semantic_parent_child_layout_candidate_20260611.csv"
  json_path.write_text(
    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
  )

  fieldnames = [
    "parent_semantic_component_id",
    "parent_surface_component_id",
    "source_region_id",
    "volume_component_role",
    "geometry_primitive",
    "bound_receiver_count",
    "extra_receiver_slot_count",
    "primary_receiver_component_name",
    "extra_receiver_component_names",
    "cross_region_held_receiver_names",
    "cross_region_held_segment_overlay_count",
    "cross_region_held_segment_overlay_ids",
    "child_receiver_prior_shapes",
    "held_segment_count",
    "parent_receiver_handoff_status",
    "runtime_projection_status",
  ]
  with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
      writer.writerow(
        {
          "parent_semantic_component_id": row["parent_semantic_component_id"],
          "parent_surface_component_id": row["parent_surface_component_id"],
          "source_region_id": row["source_region_id"],
          "volume_component_role": row["volume_component_role"],
          "geometry_primitive": row["geometry_primitive"],
          "bound_receiver_count": row["bound_receiver_count"],
          "extra_receiver_slot_count": row["extra_receiver_slot_count"],
          "primary_receiver_component_name": row[
            "primary_receiver_component_name"
          ],
          "extra_receiver_component_names": ";".join(
            row["extra_receiver_component_names"]
          ),
          "cross_region_held_receiver_names": ";".join(
            row["cross_region_held_receiver_names"]
          ),
          "cross_region_held_segment_overlay_count": row[
            "cross_region_held_segment_overlay_count"
          ],
          "cross_region_held_segment_overlay_ids": ";".join(
            segment["segment_id"]
            for segment in row["cross_region_held_segment_overlays"]
          ),
          "child_receiver_prior_shapes": ";".join(
            (
              f'{child["component_name"]}:{child["prior_shape"]}'
              f':segments={child["held_segment_count"]}'
            )
            for child in row["child_receiver_priors"]
          ),
          "held_segment_count": sum(
            child["held_segment_count"] for child in row["child_receiver_priors"]
          ),
          "parent_receiver_handoff_status": row[
            "parent_receiver_handoff_status"
          ],
          "runtime_projection_status": row["runtime_projection_status"],
        }
      )
  return json_path, csv_path


def _project_bounds(bounds: dict[str, list[float]], axes: tuple[int, int]) -> tuple[float, float, float, float]:
  x_axis, y_axis = axes
  return (
    bounds["min"][x_axis],
    bounds["min"][y_axis],
    bounds["max"][x_axis],
    bounds["max"][y_axis],
  )


def _svg_color(index: int) -> str:
  palette = [
    "#2f6f9f",
    "#b24d3e",
    "#4f8a4b",
    "#8a5a9f",
    "#b27a2f",
    "#2f827d",
    "#6f6f6f",
  ]
  return palette[index % len(palette)]


def _svg_project_point(
  *,
  point: tuple[float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> tuple[float, float]:
  value_x, value_y = point
  view_min_x, view_min_y, view_max_x, view_max_y = view_bounds
  span_x = view_max_x - view_min_x
  span_y = view_max_y - view_min_y
  x = ((value_x - view_min_x) / span_x) * width
  y = height - ((value_y - view_min_y) / span_y) * height
  return x, y


def _svg_rect(
  *,
  bounds: tuple[float, float, float, float],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.18,
  stroke_width: float = 1.2,
  stroke_dasharray: str = "",
  label_visible: bool = True,
) -> str:
  min_x, min_y, max_x, max_y = bounds
  x, y = _svg_project_point(
    point=(min_x, max_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  max_screen_x, min_screen_y = _svg_project_point(
    point=(max_x, min_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  rect_width = max(max_screen_x - x, 1.0)
  rect_height = max(min_screen_y - y, 1.0)
  text_x = x + 4.0
  text_y = y + 13.0
  dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
  escaped_label = html.escape(label)
  text = ""
  if label_visible:
    text = (
      f'\n<text x="{text_x:.2f}" y="{text_y:.2f}" font-size="10" '
      f'font-family="monospace" fill="{color}">{escaped_label}</text>'
    )
  fill_attr = (
    'fill="none"'
    if fill_opacity <= 0.0
    else f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  )
  return (
    f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
    f'height="{rect_height:.2f}" {fill_attr} '
    f'stroke="{color}" stroke-width="{stroke_width:.2f}"{dash_attr}>'
    f'<title>{escaped_label}</title></rect>'
    f'{text}'
  )


def _svg_point(
  *,
  point: list[float],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  index: int,
) -> str:
  screen_x, screen_y = _svg_project_point(
    point=(point[axes[0]], point[axes[1]]),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  escaped_label = html.escape(label)
  return (
    f'<circle cx="{screen_x:.2f}" cy="{screen_y:.2f}" r="4.5" fill="{color}" '
    f'stroke="#ffffff" stroke-width="1.2"><title>{escaped_label}</title></circle>\n'
    f'<text x="{screen_x + 6.0:.2f}" y="{screen_y - 6.0:.2f}" font-size="10" '
    f'font-family="monospace" fill="{color}">{index}</text>'
  )


def _svg_polygon(
  *,
  points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.22,
  stroke_width: float = 1.5,
  label_visible: bool = True,
) -> str:
  if len(points) < 3:
    return ""
  screen_points = [
    _svg_project_point(
      point=(point[0], point[1]),
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
    for point in points
  ]
  point_text = " ".join(f"{point[0]:.2f},{point[1]:.2f}" for point in screen_points)
  centroid_x = sum(point[0] for point in screen_points) / len(screen_points)
  centroid_y = sum(point[1] for point in screen_points) / len(screen_points)
  escaped_label = html.escape(label)
  fill_attr = (
    'fill="none"'
    if fill_opacity <= 0.0
    else f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  )
  polygon = (
    f'<polygon points="{point_text}" {fill_attr} '
    f'stroke="{color}" stroke-width="{stroke_width:.2f}">'
    f'<title>{escaped_label}</title></polygon>'
  )
  if not label_visible:
    return polygon
  return (
    polygon
    + "\n"
    f'<text x="{centroid_x + 4.0:.2f}" y="{centroid_y + 4.0:.2f}" '
    f'font-size="10" font-family="monospace" fill="{color}">{escaped_label}</text>'
  )


def _svg_polygon_projected(
  *,
  points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.24,
  stroke_width: float = 1.5,
  label_visible: bool = True,
) -> str:
  return _svg_polygon(
    points=points,
    view_bounds=view_bounds,
    width=width,
    height=height,
    color=color,
    label=label,
    fill_opacity=fill_opacity,
    stroke_width=stroke_width,
    label_visible=label_visible,
  )


def _legacy_hitbox_rows(component_report: dict[str, Any] | None) -> list[dict[str, Any]]:
  if component_report is None:
    return []
  rows: dict[int, dict[str, Any]] = {}
  for row in component_report["rows"]:
    rows.setdefault(
      int(row["hitbox_index"]),
      {
        "hitbox_index": int(row["hitbox_index"]),
        "bounds": row["parent_hitbox_bounds"],
      },
    )
  return [rows[index] for index in sorted(rows)]


def _svg_for_view(
  mapping: dict[str, Any],
  view: str,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  envelope = mapping["outer_envelope"]["bounds"]
  view_bounds_raw = _project_bounds(envelope, (axis_x, axis_y))
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.08, 0.5)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  elements = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 outer-region candidate {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; review-only boxes, component overlays, and review points</text>',
    _svg_rect(
      bounds=view_bounds_raw,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#111111",
      label="outer_envelope",
      fill_opacity=0.03,
      stroke_width=1.5,
    ),
  ]
  for legacy in _legacy_hitbox_rows(component_report):
    elements.append(
      _svg_rect(
        bounds=_project_bounds(legacy["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#c47a00",
        label=f'legacy_hitbox_{legacy["hitbox_index"]}',
        fill_opacity=0.02,
        stroke_width=1.2,
        stroke_dasharray="5 4",
        label_visible=False,
      )
    )
  for index, region in enumerate(mapping["outer_regions"]):
    elements.append(
      _svg_rect(
        bounds=_project_bounds(region["bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=_svg_color(index),
        label=region["id"],
      )
    )
  if component_report is not None:
    for row in component_report["rows"]:
      color = "#9b1c31" if row["review_status"] == "needs_review" else "#5b3f93"
      elements.append(
        _svg_rect(
          bounds=_project_bounds(row["component_bounds"], (axis_x, axis_y)),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{row["component_name"]} -> {row["bound_region_id"]}',
          fill_opacity=0.05,
          stroke_width=0.9,
          label_visible=False,
        )
      )
  if diagnostics is not None:
    for row in diagnostics["rows"]:
      elements.append(
        _svg_point(
          point=row["point_m"],
          axes=(axis_x, axis_y),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#0f172a",
          label=f'{row["point_index"]}: {row["point_id"]}',
          index=int(row["point_index"]),
        )
      )
  elements.extend(
    [
      '<text x="24" y="716" font-size="11" font-family="monospace" fill="#555555">'
      'Legend: black envelope, colored outer regions, orange dashed legacy boxes, '
      'purple/red component boxes, numbered review points</text>',
      '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only geometry; not a runtime collision mesh or real F-16 engineering model</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_svg_views(
  mapping: dict[str, Any],
  output_dir: Path,
  *,
  component_report: dict[str, Any] | None = None,
  diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"{view}.svg"
    path.write_text(
      _svg_for_view(
        mapping,
        view,
        component_report=component_report,
        diagnostics=diagnostics,
      ),
      encoding="utf-8",
    )
    paths.append(path)
  return paths


def _svg_for_fine_proxy_view(fine_proxy: dict[str, Any], view: str) -> str:
  axes_by_view = {
    "top": (0, 1, "x forward (m)", "y lateral (m)"),
    "side": (0, 2, "x forward (m)", "z up (m)"),
    "front": (1, 2, "y lateral (m)", "z up (m)"),
  }
  axis_x, axis_y, label_x, label_y = axes_by_view[view]
  width, height = 1200, 760
  envelope = fine_proxy["outer_envelope"]["bounds"]
  view_bounds_raw = _project_bounds(envelope, (axis_x, axis_y))
  margin_x = max((view_bounds_raw[2] - view_bounds_raw[0]) * 0.08, 0.5)
  margin_y = max((view_bounds_raw[3] - view_bounds_raw[1]) * 0.14, 0.75)
  view_bounds = (
    view_bounds_raw[0] - margin_x,
    view_bounds_raw[1] - margin_y,
    view_bounds_raw[2] + margin_x,
    view_bounds_raw[3] + margin_y,
  )
  elements = [
    '<rect x="0" y="0" width="1200" height="760" fill="#ffffff"/>',
    f'<text x="24" y="34" font-size="18" font-family="monospace" fill="#202020">'
    f'F-16 mesh-derived fine geometry proxy candidate {view} view</text>',
    f'<text x="24" y="58" font-size="12" font-family="monospace" fill="#555555">'
    f'{label_x}; {label_y}; dashed source AABB, dotted support bounds, solid mesh-derived silhouette</text>',
    _svg_rect(
      bounds=view_bounds_raw,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#111111",
      label="outer_envelope",
      fill_opacity=0.0,
      stroke_width=1.5,
      label_visible=False,
    ),
  ]
  for index, proxy in enumerate(fine_proxy["proxies"]):
    color = _svg_color(index)
    elements.append(
      _svg_rect(
        bounds=_project_bounds(proxy["source_region_bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label=f'{proxy["source_region_id"]} source_aabb',
        fill_opacity=0.0,
        stroke_width=0.9,
        stroke_dasharray="6 4",
        label_visible=False,
      )
    )
    elements.append(
      _svg_rect(
        bounds=_project_bounds(proxy["support_bounds"], (axis_x, axis_y)),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label=f'{proxy["source_region_id"]} support_bounds',
        fill_opacity=0.0,
        stroke_width=0.9,
        stroke_dasharray="2 3",
        label_visible=False,
      )
    )
    hull = proxy.get("mesh_derived_review_geometry", {}).get("hulls", {}).get(view, {})
    hull_points = hull.get("points_m", [])
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{proxy["source_region_id"]} {proxy["proxy_kind"]} mesh_silhouette',
          label_visible=False,
        )
      )
    else:
      elements.append(
        _svg_rect(
          bounds=_project_bounds(proxy["support_bounds"], (axis_x, axis_y)),
          view_bounds=view_bounds,
          width=width,
          height=height,
          color=color,
          label=f'{proxy["source_region_id"]} {proxy["proxy_kind"]} support_bounds_no_mesh_silhouette',
          fill_opacity=0.15,
          stroke_width=1.4,
        )
      )
  for index, row in enumerate(fine_proxy["review_point_distance_deltas"], start=1):
    elements.append(
      _svg_point(
        point=row["point_m"],
        axes=(axis_x, axis_y),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#0f172a",
        label=f'{index}: {row["point_id"]}',
        index=index,
      )
    )
  elements.extend(
    [
      '<text x="24" y="716" font-size="11" font-family="monospace" fill="#555555">'
      'Legend: dashed boxes are TG-P2 source AABBs; dotted boxes are support bounds; solid polygons are mesh-derived silhouettes</text>',
      '<text x="24" y="736" font-size="11" font-family="monospace" fill="#555555">'
      'Review-only fine proxy candidates; not a runtime collision mesh or real F-16 engineering model</text>',
    ]
  )
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" '
    'viewBox="0 0 1200 760">\n'
    + "\n".join(elements)
    + "\n</svg>\n"
  )


def write_fine_proxy_svg_views(
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> list[Path]:
  output_dir.mkdir(parents=True, exist_ok=True)
  paths: list[Path] = []
  for view in ("top", "side", "front"):
    path = output_dir / f"fine_proxy_{view}.svg"
    path.write_text(_svg_for_fine_proxy_view(fine_proxy, view), encoding="utf-8")
    paths.append(path)
  return paths


def _component_rows_for_region(
  component_report: dict[str, Any],
  region_id: str,
) -> list[dict[str, Any]]:
  return [
    row for row in component_report["rows"] if row["bound_region_id"] == region_id
  ]


def _fine_proxy_review_flags(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
) -> list[str]:
  geometry = proxy["mesh_derived_review_geometry"]
  hull_counts = [
    view["point_count"] for view in geometry.get("hulls", {}).values()
  ]
  flags: list[str] = []
  if geometry.get("status") == "insufficient_region_vertices_for_closed_silhouette":
    flags.append("insufficient_mesh_silhouette")
  if hull_counts and min(hull_counts) <= 4:
    flags.append("low_hull_point_count")
  if any(row["review_status"] == "needs_review" for row in component_rows):
    flags.append("component_binding_needs_review")
  if "wing" in proxy["source_region_id"] or "tail" in proxy["source_region_id"]:
    flags.append("surface_sign_or_thickness_review")
  if not flags:
    flags.append("candidate_accept_visual_check")
  return flags


def _fine_proxy_review_status(flags: list[str]) -> str:
  if "insufficient_mesh_silhouette" in flags:
    return "hold_for_human_review"
  if "component_binding_needs_review" in flags or "low_hull_point_count" in flags:
    return "needs_human_review"
  return "candidate_accept_after_visual_check"


def _projected_view_bounds_for_proxy(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  axes: tuple[int, int],
  extra_points: list[list[float]] | None = None,
) -> tuple[float, float, float, float]:
  projected: list[tuple[float, float, float, float]] = [
    _project_bounds(proxy["source_region_bounds"], axes),
    _project_bounds(proxy["support_bounds"], axes),
  ]
  geometry = proxy["mesh_derived_review_geometry"]
  if "selection_bounds" in geometry:
    projected.append(_project_bounds(geometry["selection_bounds"], axes))
  for row in component_rows:
    projected.append(_project_bounds(row["component_bounds"], axes))
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  for point in extra_points or []:
    projected.append((point[axes[0]], point[axes[1]], point[axes[0]], point[axes[1]]))
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _fine_proxy_review_mini_svg(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  view: str,
  review_points: list[dict[str, Any]] | None = None,
  component_labels_visible: bool = False,
  width: int = 420,
  height: int = 260,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  point_values = [row["point_m"] for row in review_points or []]
  view_bounds = _projected_view_bounds_for_proxy(
    proxy,
    component_rows,
    axes,
    extra_points=point_values,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  color = "#2563eb"
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">{view} ({view_label})</text>',
    _svg_rect(
      bounds=_project_bounds(proxy["source_region_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#f59e0b",
      label="source_region_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="6 4",
      label_visible=False,
    ),
    _svg_rect(
      bounds=_project_bounds(proxy["support_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#64748b",
      label="support_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="2 3",
      label_visible=False,
    ),
  ]
  for row in component_rows:
    component_color = "#be123c" if row["review_status"] == "needs_review" else "#7c3aed"
    elements.append(
      _svg_rect(
        bounds=_project_bounds(row["component_bounds"], axes),
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=component_color,
        label=f'{row["component_name"]} {row["review_status"]}',
        fill_opacity=0.08,
        stroke_width=0.9,
        label_visible=component_labels_visible,
      )
    )
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        label="mesh_silhouette",
        fill_opacity=0.28,
        stroke_width=1.6,
      )
    )
  for index, row in enumerate(review_points or [], start=1):
    elements.append(
      _svg_point(
        point=row["point_m"],
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#0f172a",
        label=f'{row.get("point_id", "review_point")}',
        index=int(row.get("point_index", index)),
      )
    )
  elements.append(
    f'<text x="12" y="{height - 14}" font-size="10" font-family="monospace" fill="#475569">'
    'orange=source, gray=support, purple/red=components, blue=mesh, black=point</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _component_rows_by_name(
  component_report: dict[str, Any],
) -> dict[str, dict[str, Any]]:
  return {row["component_name"]: row for row in component_report["rows"]}


def _triage_mini_view_grid(
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  review_points: list[dict[str, Any]] | None = None,
) -> str:
  return (
    '<div class="mini-views">'
    + "".join(
      _fine_proxy_review_mini_svg(
        proxy,
        component_rows,
        view,
        review_points=review_points,
        component_labels_visible=True,
      )
      for view in ("top", "side", "front")
    )
    + "</div>"
  )


def _triage_list(items: Iterable[Any]) -> str:
  values = [str(item) for item in items if str(item)]
  if not values:
    return "<ul><li>none</li></ul>"
  return "<ul>" + "".join(f"<li>{html.escape(value)}</li>" for value in values) + "</ul>"


def _triage_card(
  *,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  severity: str,
  review_points: list[dict[str, Any]] | None = None,
) -> str:
  return f"""
    <article class="triage-card {html.escape(severity)}">
      <div class="triage-head">
        <h3>{html.escape(title)}</h3>
        <span>{html.escape(subtitle)}</span>
      </div>
      <div class="decision-box">
        <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
        <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
        <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
      </div>
      {_triage_list(details)}
      {_triage_mini_view_grid(proxy, component_rows, review_points=review_points)}
    </article>
  """


def _review_slug(value: str) -> str:
  cleaned = [
    char.lower() if char.isalnum() else "-"
    for char in value.replace("_", "-")
  ]
  slug = "".join(cleaned).strip("-")
  while "--" in slug:
    slug = slug.replace("--", "-")
  return slug or "item"


def _relative_to(path: Path, parent: Path) -> str:
  return path.relative_to(parent).as_posix()


def _isolated_view_page(
  *,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  svg_filenames: dict[str, str],
  back_href: str,
) -> str:
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} isolated geometry view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 25px;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    .decision-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px;
      margin-top: 14px;
    }}
    .decision-box strong {{
      display: block;
      color: #0f172a;
      font-size: 12px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .decision-box p {{
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
      margin: 4px 0 0;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    .views {{
      display: grid;
      gap: 18px;
    }}
    figure {{
      margin: 0;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="{html.escape(back_href)}">Back to isolated review index</a></p>
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">{html.escape(subtitle)}</p>
    <div class="decision-box">
      <div><strong>Review question</strong><p>{html.escape(question)}</p></div>
      <div><strong>Look at</strong><p>{html.escape(look_at)}</p></div>
      <div><strong>Decision needed</strong><p>{html.escape(decision)}</p></div>
    </div>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list(details)}
  </section>
  <section class="views">
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(title)} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def _write_isolated_review_entry(
  *,
  root_dir: Path,
  category: str,
  slug: str,
  title: str,
  subtitle: str,
  question: str,
  look_at: str,
  decision: str,
  details: list[str],
  proxy: dict[str, Any],
  component_rows: list[dict[str, Any]],
  review_points: list[dict[str, Any]] | None = None,
  priority: str,
) -> dict[str, Any]:
  category_dir = root_dir / category
  category_dir.mkdir(parents=True, exist_ok=True)
  safe_slug = _review_slug(slug)
  svg_filenames: dict[str, str] = {}
  for view in ("top", "side", "front"):
    svg_filename = f"{safe_slug}_{view}.svg"
    svg_path = category_dir / svg_filename
    svg_path.write_text(
      _fine_proxy_review_mini_svg(
        proxy,
        component_rows,
        view,
        review_points=review_points,
        component_labels_visible=True,
        width=960,
        height=620,
      ),
      encoding="utf-8",
    )
    svg_filenames[view] = svg_filename
  html_path = category_dir / f"{safe_slug}.html"
  html_path.write_text(
    "\n".join(
      line.rstrip()
      for line in _isolated_view_page(
        title=title,
        subtitle=subtitle,
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        svg_filenames=svg_filenames,
        back_href="../index.html",
      ).splitlines()
    )
    + "\n",
    encoding="utf-8",
  )
  return {
    "category": category,
    "slug": safe_slug,
    "title": title,
    "subtitle": subtitle,
    "priority": priority,
    "html": _relative_to(html_path, root_dir),
    "svg": {
      view: _relative_to(category_dir / filename, root_dir)
      for view, filename in svg_filenames.items()
    },
    "details": details,
    "component_names": [row["component_name"] for row in component_rows],
    "review_point_ids": [row["point_id"] for row in review_points or []],
    "source_region_id": proxy["source_region_id"],
    "review_question": question,
    "decision_needed": decision,
  }


def _write_isolated_review_index(root_dir: Path, entries: list[dict[str, Any]]) -> Path:
  groups = {
    "components": "Component Binding Views",
    "surface_links": "Surface Handoff Component Views",
    "review_point_candidates": "Review Point Candidate Views",
  }
  sections: list[str] = []
  for category, label in groups.items():
    category_entries = [entry for entry in entries if entry["category"] == category]
    sections.append(
      f"""
      <section>
        <h2>{html.escape(label)} <span>{len(category_entries)}</span></h2>
        <div class="entry-grid">
          {''.join(
            f'<article class="{html.escape(entry["priority"])}"><h3><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h3><p>{html.escape(entry["subtitle"])}</p><p>{html.escape(entry["decision_needed"])}</p></article>'
            for entry in category_entries
          ) or '<p class="empty">No current entries.</p>'}
        </div>
      </section>
      """
    )
  index_path = root_dir / "index.html"
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Isolated Component Review Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2, h3 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      font-size: 20px;
      margin-bottom: 12px;
    }}
    h2 span {{
      color: #475569;
      font-family: monospace;
      font-size: 15px;
    }}
    p {{
      color: #475569;
      margin: 8px 0 0;
      line-height: 1.35;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #d97706;
      border-radius: 6px;
      padding: 12px;
      background: #fffdf7;
    }}
    article.critical {{
      border-left-color: #be123c;
      background: #fff7f7;
    }}
    article.warning {{
      border-left-color: #d97706;
    }}
    article.info {{
      border-left-color: #2563eb;
      background: #f8fbff;
    }}
    a {{
      color: #1d4ed8;
    }}
    .empty {{
      color: #64748b;
      font-family: monospace;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Isolated Component Review Views</h1>
    <p>Each page isolates one component, surface-to-component handoff, or review-point candidate. These are review-only visual artifacts and are not runtime geometry.</p>
    <div class="summary">
      <div>total isolated views: {len(entries)}</div>
      <div>component views: {sum(1 for entry in entries if entry["category"] == "components")}</div>
      <div>surface-link views: {sum(1 for entry in entries if entry["category"] == "surface_links")}</div>
      <div>review-point views: {sum(1 for entry in entries if entry["category"] == "review_point_candidates")}</div>
      <div><a href="../human_review_triage.html">triage dashboard</a></div>
      <div><a href="../scene.html">overview packet</a></div>
    </div>
  </header>
  {''.join(sections)}
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def write_isolated_component_review_views(
  *,
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  surface_report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "component_review_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  fine_rows_by_point = {
    row["point_id"]: row for row in fine_proxy["review_point_distance_deltas"]
  }
  entries: list[dict[str, Any]] = []

  for row in component_report["rows"]:
    proxy = proxies_by_region.get(row["bound_region_id"])
    if proxy is None:
      continue
    question, look_at, decision = _component_triage_prompts(row)
    if row["review_severity"] == "hard_blocker":
      priority = "critical"
    elif row["review_status"] == "needs_review":
      priority = "warning"
    elif row["review_status"].startswith("review_only"):
      priority = "info"
    else:
      priority = "info"
    entries.append(
      _write_isolated_review_entry(
        root_dir=root_dir,
        category="components",
        slug=row["component_name"],
        title=row["component_name"],
        subtitle=f'component binding -> {row["bound_region_id"]}',
        question=question,
        look_at=look_at,
        decision=decision,
        details=[
          f'component: {row["component_name"]}',
          f'system: {row["system"]}',
          f'bound outer region: {row["bound_region_id"]}',
          f'review semantics: {row["review_semantics"]}',
          f'review severity: {row["review_severity"]}',
          f'component center distance to region: {row["center_distance_m"]} m',
          "anomalies: " + ", ".join(row["anomalies"]),
          "geometry observations: " + ", ".join(row["geometry_observations"]),
          "suppressed anomalies: " + (", ".join(row["suppressed_anomalies"]) or "none"),
          "semantic regions: " + (", ".join(row["semantic_region_ids"]) or "none"),
          "side relation: "
          + json.dumps(row["side_sign_relation"], sort_keys=True),
          "blocked region binding: "
          + json.dumps(row["blocked_region_binding"], sort_keys=True),
          "review notes: " + " | ".join(row["review_notes"]),
        ],
        proxy=proxy,
        component_rows=[row],
        priority=priority,
      )
    )

  for row in surface_report["rows"]:
    if row["review_status"] == "candidate_surface_component":
      continue
    proxy = proxies_by_region.get(row["source_region_id"])
    if proxy is None:
      continue
    question, look_at, decision = _surface_triage_prompts(row)
    priority = (
      "critical"
      if row["review_semantics"]
      in {
        "missing_runtime_link/held",
        "side_sign_mismatch_hard_blocker",
        "invalid_region_binding_blocked",
      }
      else "warning"
    )
    linked_names = [
      link["component_name"] for link in row["linked_internal_components"]
    ]
    for component_name in linked_names:
      component_row = rows_by_component.get(component_name)
      component_rows = [component_row] if component_row is not None else []
      entries.append(
        _write_isolated_review_entry(
          root_dir=root_dir,
          category="surface_links",
          slug=f'{row["surface_component_id"]}__{component_name}',
          title=f'{row["surface_component_id"]} -> {component_name}',
          subtitle=f'surface handoff -> {row["source_region_id"]}',
          question=question,
          look_at=look_at,
          decision=decision,
          details=[
            f'surface component: {row["surface_component_id"]}',
            f'outer region: {row["source_region_id"]}',
            f'surface role: {row["surface_role"]}',
            f'isolated linked component: {component_name}',
            f'review semantics: {row["review_semantics"]}',
            f'runtime relation status: {row["runtime_relation_status"]}',
            "clean direct components: "
            + (", ".join(row["clean_direct_component_names"]) or "none"),
            "cross-region semantic components: "
            + (", ".join(row["cross_region_semantic_component_names"]) or "none"),
            "blocked components: "
            + (", ".join(row["blocked_component_names"]) or "none"),
            "bad geometry components: "
            + (", ".join(row["bad_geometry_component_names"]) or "none"),
            "review flags: " + ", ".join(row["review_flags"]),
            "missing runtime links: "
            + (", ".join(row["missing_existing_runtime_component_relations"]) or "none"),
          ],
          proxy=proxy,
          component_rows=component_rows,
          priority=priority,
        )
      )
    for missing in row["missing_existing_runtime_component_relations"]:
      entries.append(
        _write_isolated_review_entry(
          root_dir=root_dir,
          category="surface_links",
          slug=f'{row["surface_component_id"]}__missing__{missing}',
          title=f'{row["surface_component_id"]} -> missing {missing}',
          subtitle=f'surface handoff -> {row["source_region_id"]}',
          question=question,
          look_at=look_at,
          decision=decision,
          details=[
            f'surface component: {row["surface_component_id"]}',
            f'outer region: {row["source_region_id"]}',
            f'surface role: {row["surface_role"]}',
            f'missing runtime component relation: {missing}',
            f'review semantics: {row["review_semantics"]}',
            f'runtime relation status: {row["runtime_relation_status"]}',
            "review flags: " + ", ".join(row["review_flags"]),
          ],
          proxy=proxy,
          component_rows=[],
          priority="critical",
        )
      )
    if not linked_names and not row["missing_existing_runtime_component_relations"]:
      entries.append(
        _write_isolated_review_entry(
          root_dir=root_dir,
          category="surface_links",
          slug=row["surface_component_id"],
          title=row["surface_component_id"],
          subtitle=f'surface handoff -> {row["source_region_id"]}',
          question=question,
          look_at=look_at,
          decision=decision,
          details=[
            f'surface component: {row["surface_component_id"]}',
            f'outer region: {row["source_region_id"]}',
            f'surface role: {row["surface_role"]}',
            "linked components: none",
            "review flags: " + ", ".join(row["review_flags"]),
          ],
          proxy=proxy,
          component_rows=[],
          priority=priority,
        )
      )

  point_focus_ids = {
    "nose_axis_4m",
    "nose_axis_6m",
    "right_beam_4m",
    "left_beam_4m",
    "above_4m",
    "below_4m",
  }
  for row in diagnostics["rows"]:
    if row["point_id"] not in point_focus_ids:
      continue
    proxy = proxies_by_region.get(row["nearest_outer_region_id"])
    if proxy is None:
      continue
    question, look_at, decision = _point_triage_prompts(row)
    fine_row = fine_rows_by_point.get(row["point_id"], {})
    candidates = row["candidate_components"] or [
      {"component_name": "no_near_component_candidate"}
    ]
    for candidate in candidates:
      component_name = candidate["component_name"]
      component_row = rows_by_component.get(component_name)
      component_rows = [component_row] if component_row is not None else []
      entries.append(
        _write_isolated_review_entry(
          root_dir=root_dir,
          category="review_point_candidates",
          slug=f'{row["point_id"]}__{component_name}',
          title=f'{row["point_id"]} -> {component_name}',
          subtitle="review point candidate",
          question=question,
          look_at=look_at,
          decision=decision,
          details=[
            f'point: {row["point_id"]} at {row["point_m"]}',
            f'nearest outer region: {row["nearest_outer_region_id"]}',
            f'nearest outer distance: {row["nearest_outer_distance_m"]} m',
            "nearest fine proxy: "
            + str(fine_row.get("nearest_fine_proxy_region_id", "unknown")),
            f'isolated candidate component: {component_name}',
            f'nearest component: {row["nearest_component_name"]}',
            f'nearest component distance: {row["nearest_component_distance_m"]} m',
            f'candidate component count: {row["candidate_component_count"]}',
            f'interpretation: {row["interpretation"]}',
          ],
          proxy=proxy,
          component_rows=component_rows,
          review_points=[row],
          priority="critical" if "beam" in row["point_id"] else "warning",
        )
      )

  index_path = _write_isolated_review_index(root_dir, entries)
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_isolated_component_review_views.v1",
    "status": "isolated_component_review_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_collision_mesh": False,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "component_entry_count": sum(
        1 for entry in entries if entry["category"] == "components"
      ),
      "surface_link_entry_count": sum(
        1 for entry in entries if entry["category"] == "surface_links"
      ),
      "review_point_candidate_entry_count": sum(
        1 for entry in entries if entry["category"] == "review_point_candidates"
      ),
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _write_semantic_damage_geometry_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  semantic_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Semantic Damage Geometry Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #2563eb;
      border-radius: 6px;
      padding: 12px;
      background: #f8fbff;
    }}
    article.warning {{
      border-left-color: #d97706;
      background: #fffdf7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Semantic Damage Geometry Views</h1>
    <p>Each page isolates one semantic outer-shell volume, its mesh-proxy geometry, and the current direct or held receiver components. These pages are parse-ready candidates, not active runtime damage components.</p>
    <div class="summary">
      <div>semantic volumes: {semantic_report["summary"]["semantic_volume_component_count"]}</div>
      <div>runtime parse-ready candidates: {semantic_report["summary"]["runtime_parse_ready_component_count"]}</div>
      <div>runtime active components: {semantic_report["summary"]["runtime_active_component_count"]}</div>
      <div>cross-region held handoffs: {semantic_report["summary"]["cross_region_handoff_held_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../fine_proxy_review_dashboard.html">region dashboard</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def write_semantic_damage_geometry_review_views(
  *,
  semantic_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "semantic_damage_geometry_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  entries: list[dict[str, Any]] = []
  for row in semantic_report["rows"]:
    proxy = proxies_by_region[row["source_region_id"]]
    receiver_names = (
      row["direct_receiver_components"] + row["cross_region_receiver_components"]
    )
    component_rows = [
      rows_by_component[name] for name in receiver_names if name in rows_by_component
    ]
    has_cross_region_receivers = bool(row["cross_region_receiver_components"])
    entries.append(
      _write_isolated_review_entry(
        root_dir=root_dir,
        category="volumes",
        slug=row["semantic_component_id"],
        title=row["semantic_component_id"],
        subtitle=f'semantic volume -> {row["source_region_id"]}',
        question=(
          f'Can {row["semantic_component_id"]} be promoted from mesh-proxy candidate to an active damage component?'
        ),
        look_at=(
          "Compare the blue mesh silhouette/support volume with the linked receiver component boxes in all three views."
        ),
        decision=(
          "Keep cross-region receivers held or split them before runtime activation."
          if has_cross_region_receivers
          else "Candidate is parse-ready; activation still needs explicit damage-model review."
        ),
        details=[
          f'semantic component: {row["semantic_component_id"]}',
          f'surface component: {row["surface_component_id"]}',
          f'outer region: {row["source_region_id"]}',
          f'volume role: {row["volume_component_role"]}',
          f'geometry primitive: {row["geometry_primitive"]}',
          f'runtime system candidate: {row["runtime_system"]}',
          "direct receivers: "
          + (", ".join(row["direct_receiver_components"]) or "none"),
          "cross-region receivers: "
          + (", ".join(row["cross_region_receiver_components"]) or "none"),
          f'receiver handoff: {row["receiver_handoff_status"]}',
          f'runtime projection: {row["runtime_projection_status"]}',
          f'mesh region vertices: {row["mesh_region_vertex_count"]}',
          f'surface review semantics: {row["surface_review_semantics"]}',
        ],
        proxy=proxy,
        component_rows=component_rows,
        priority="warning" if has_cross_region_receivers else "info",
      )
    )

  index_path = _write_semantic_damage_geometry_index(
    root_dir,
    entries,
    semantic_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_semantic_damage_geometry_views.v1",
    "status": "semantic_damage_geometry_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "runtime_schema_parse_ready_candidate": True,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "semantic_volume_entry_count": len(entries),
      "cross_region_receiver_entry_count": sum(
        1
        for row in semantic_report["rows"]
        if row["cross_region_receiver_components"]
      ),
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_internal_prior(
  proxy: dict[str, Any],
  component_row: dict[str, Any],
  prior_row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    _project_bounds(proxy["source_region_bounds"], axes),
    _project_bounds(proxy["support_bounds"], axes),
    _project_bounds(component_row["component_bounds"], axes),
    _project_bounds(prior_row["constraint_bounds"], axes),
    _project_bounds(prior_row["constrained_geometry"]["bounds"], axes),
  ]
  geometry = proxy["mesh_derived_review_geometry"]
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _internal_prior_mini_svg(
  proxy: dict[str, Any],
  component_row: dict[str, Any],
  prior_row: dict[str, Any],
  view: str,
  *,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_internal_prior(
    proxy,
    component_row,
    prior_row,
    axes,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">{view} ({view_label})</text>',
    _svg_rect(
      bounds=_project_bounds(proxy["support_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#f59e0b",
      label="parent_surface_support_bounds",
      fill_opacity=0.02,
      stroke_width=1.1,
      stroke_dasharray="6 4",
      label_visible=False,
    ),
    _svg_rect(
      bounds=_project_bounds(prior_row["constraint_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#64748b",
      label="shell_constraint_bounds",
      fill_opacity=0.02,
      stroke_width=1.2,
      stroke_dasharray="2 3",
      label_visible=True,
    ),
    _svg_rect(
      bounds=_project_bounds(component_row["component_bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#7c3aed",
      label=f'{prior_row["component_name"]} old_aabb',
      fill_opacity=0.08,
      stroke_width=0.9,
      label_visible=True,
    ),
    _svg_rect(
      bounds=_project_bounds(prior_row["constrained_geometry"]["bounds"], axes),
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#0891b2",
      label=f'{prior_row["component_name"]} constrained_{prior_row["prior_shape"]}',
      fill_opacity=0.18,
      stroke_width=1.4,
      label_visible=True,
    ),
  ]
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        label="mesh_silhouette",
        fill_opacity=0.24,
        stroke_width=1.4,
      )
    )
  elements.append(
    f'<text x="12" y="{height - 14}" font-size="10" font-family="monospace" fill="#475569">'
    'orange=parent support, gray=constraint, purple=old AABB, cyan=constrained prior, blue=mesh</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_internal_component_prior_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  prior_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  shape_counts = ", ".join(
    f"{shape}:{count}"
    for shape, count in prior_report["summary"]["shape_counts"].items()
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Internal Component Prior Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #0891b2;
      border-radius: 6px;
      padding: 12px;
      background: #f7fdff;
    }}
    article.warning {{
      border-left-color: #d97706;
      background: #fffdf7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Internal Component Prior Views</h1>
    <p>Each page isolates one current receiver component, its old AABB placement, and a constrained synthetic prior shape. These are review-only internal geometry priors, not true engineering structure.</p>
    <div class="summary">
      <div>component priors: {prior_report["summary"]["internal_component_prior_count"]}</div>
      <div>post-constraint outside: {prior_report["summary"]["post_constraint_outside_count"]}</div>
      <div>cross-region held priors: {prior_report["summary"]["cross_region_held_prior_count"]}</div>
      <div>shape counts: {html.escape(shape_counts)}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../semantic_damage_geometry_views/index.html">semantic shell views</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _internal_prior_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["component_name"])} internal prior view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to internal prior index</a></p>
    <h1>{html.escape(row["component_name"])}</h1>
    <p class="subtitle">{html.escape(row["prior_shape"])} prior -> {html.escape(row["bound_region_id"])}; constraint status {html.escape(row["constraint_status"])}</p>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list([
      f'component: {row["component_name"]}',
      f'system: {row["system"]}',
      f'role: {row["component_role"]}',
      f'prior shape: {row["prior_shape"]} axis={row["prior_axis"] or "none"}',
      f'bound region: {row["bound_region_id"]}',
      "constraint regions: " + ", ".join(row["constraint_region_ids"]),
      f'constraint mode: {row["constraint_mode"]}',
      f'constraint status: {row["constraint_status"]}',
      f'old AABB containment: {row["original_aabb_containment_fraction"]}',
      "adjustment: " + json.dumps(row["constraint_adjustment"], sort_keys=True),
      f'component review semantics: {row["component_review_semantics"]}',
      f'rationale: {row["prior_rationale"]}',
      f'runtime projection: {row["runtime_projection_status"]}',
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["component_name"])} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_internal_component_prior_review_views(
  *,
  prior_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "internal_component_prior_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  component_dir = root_dir / "components"
  component_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  entries: list[dict[str, Any]] = []
  for row in prior_report["rows"]:
    component_row = rows_by_component[row["component_name"]]
    proxy = proxies_by_region[row["bound_region_id"]]
    safe_slug = _review_slug(row["component_name"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = component_dir / svg_filename
      svg_path.write_text(
        _internal_prior_mini_svg(
          proxy,
          component_row,
          row,
          view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = component_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _internal_prior_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    entries.append(
      {
        "category": "components",
        "slug": safe_slug,
        "title": row["component_name"],
        "subtitle": (
          f'{row["prior_shape"]} prior constrained by '
          f'{",".join(row["constraint_region_ids"])}'
        ),
        "priority": (
          "warning"
          if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          else "info"
        ),
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(component_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "component_name": row["component_name"],
        "prior_shape": row["prior_shape"],
        "constraint_status": row["constraint_status"],
        "decision_needed": (
          "Keep held until multi-region ownership is split or accepted."
          if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
          else "Review constrained prior before replacing the old AABB receiver."
        ),
      }
    )

  index_path = _write_internal_component_prior_index(
    root_dir,
    entries,
    prior_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_internal_component_prior_views.v1",
    "status": "internal_component_prior_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "component_prior_entry_count": len(entries),
      "cross_region_held_entry_count": sum(
        1 for row in prior_report["rows"]
        if row["component_review_semantics"] in CROSS_REGION_REVIEW_SEMANTICS
      ),
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_shape_placement(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    _project_bounds(row["latest_candidate_geometry"]["bounds"], axes),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      hull_bounds = _projected_hull_bounds(hull_points)
      if hull_bounds is not None:
        projected.append(hull_bounds)
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.08,
    min_y - span_y * 0.08,
    max_x + span_x * 0.08,
    max_y + span_y * 0.08,
  )


def _projected_view_bounds_for_shape_placement_overview(
  *,
  fine_proxy: dict[str, Any],
  rows: list[dict[str, Any]],
  view: str,
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    _project_bounds(row["latest_candidate_geometry"]["bounds"], axes)
    for row in rows
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      hull_bounds = _projected_hull_bounds(hull_points)
      if hull_bounds is not None:
        projected.append(hull_bounds)
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.08,
    min_y - span_y * 0.08,
    max_x + span_x * 0.08,
    max_y + span_y * 0.08,
  )


def _svg_shape_label_badge(
  *,
  label: str,
  bounds: dict[str, list[float]],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  offset_index: int,
) -> str:
  projected_bounds = _project_bounds(bounds, axes)
  min_x, min_y, max_x, max_y = projected_bounds
  screen_x, screen_y = _svg_project_point(
    point=((min_x + max_x) * 0.5, (min_y + max_y) * 0.5),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  offsets = [
    (0.0, 0.0),
    (12.0, -12.0),
    (-12.0, -12.0),
    (12.0, 12.0),
    (-12.0, 12.0),
  ]
  delta_x, delta_y = offsets[offset_index % len(offsets)]
  badge_x = min(max(screen_x + delta_x, 18.0), width - 18.0)
  badge_y = min(max(screen_y + delta_y, 34.0), height - 42.0)
  escaped_label = html.escape(label)
  return (
    f'<circle cx="{badge_x:.2f}" cy="{badge_y:.2f}" r="12" '
    f'fill="#ffffff" fill-opacity="0.92" stroke="#1e3a8a" '
    f'stroke-width="1.6"><title>{escaped_label}</title></circle>\n'
    f'<text x="{badge_x:.2f}" y="{badge_y + 4.2:.2f}" '
    f'text-anchor="middle" font-size="11" font-weight="700" '
    f'font-family="monospace" fill="#1e3a8a">{escaped_label}</text>'
  )


def _projected_view_bounds_for_latest_component_zoom(
  row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = _project_bounds(
    row["latest_candidate_geometry"]["bounds"],
    axes,
  )
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  component_span_x = max(max_x - min_x, 1.0e-6)
  component_span_y = max(max_y - min_y, 1.0e-6)
  span_x = max(component_span_x * 1.35, 0.08)
  span_y = max(component_span_y * 1.35, 0.08)
  return (
    center_x - span_x * 0.5,
    center_y - span_y * 0.5,
    center_x + span_x * 0.5,
    center_y + span_y * 0.5,
  )


def _fit_view_bounds_to_screen_aspect(
  bounds: tuple[float, float, float, float],
  *,
  width: int,
  height: int,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  span_x = max(max_x - min_x, 1.0e-6)
  span_y = max(max_y - min_y, 1.0e-6)
  target_aspect = width / max(height, 1)
  current_aspect = span_x / span_y
  if current_aspect < target_aspect:
    span_x = span_y * target_aspect
  else:
    span_y = span_x / target_aspect
  return (
    center_x - span_x * 0.5,
    center_y - span_y * 0.5,
    center_x + span_x * 0.5,
    center_y + span_y * 0.5,
  )


def _svg_scale_bar(
  *,
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> str:
  span_x = max(view_bounds[2] - view_bounds[0], 1.0e-6)
  target = span_x * 0.24
  candidates = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
  scale_m = candidates[0]
  for candidate in candidates:
    if candidate <= target:
      scale_m = candidate
  pixel_length = max((scale_m / span_x) * width, 18.0)
  x0 = width - pixel_length - 16.0
  x1 = width - 16.0
  y = height - 18.0
  label = f"{scale_m:g} m"
  return (
    f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<line x1="{x0:.2f}" y1="{y - 4:.2f}" x2="{x0:.2f}" y2="{y + 4:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<line x1="{x1:.2f}" y1="{y - 4:.2f}" x2="{x1:.2f}" y2="{y + 4:.2f}" '
    f'stroke="#111827" stroke-width="2"/>\n'
    f'<text x="{(x0 + x1) * 0.5:.2f}" y="{y - 7:.2f}" '
    f'text-anchor="middle" font-size="10" font-family="monospace" '
    f'fill="#111827">{label}</text>'
  )


def _subcomponent_latest_overview_svg(
  *,
  fine_proxy: dict[str, Any],
  shape_report: dict[str, Any],
  view: str,
  width: int = 1500,
  height: int = 860,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  rows = shape_report["rows"]
  view_bounds = _projected_view_bounds_for_shape_placement_overview(
    fine_proxy=fine_proxy,
    rows=rows,
    view=view,
    axes=axes,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="18" y="28" font-size="18" font-weight="700" '
      f'font-family="Arial, sans-serif" fill="#111827">'
      f'R20 latest subcomponent candidates / {view} ({view_label})</text>'
    ),
    (
      f'<text x="18" y="52" font-size="12" font-family="monospace" '
      f'fill="#475569">gray=whole-airframe wireframe; '
      f'blue=latest subcomponent candidate; numbers match the item list</text>'
    ),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  for index, row in enumerate(rows, start=1):
    child = {
      "prior_shape": row["candidate_evaluation_shape"],
      "constrained_geometry": row["latest_candidate_geometry"],
    }
    elements.append(
      _svg_projected_prior_shape(
        child=child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        fill_opacity=0.28,
        stroke_width=2.4,
        stroke_color="#1e3a8a",
        label=f'{index}. {row["item_id"]}',
        label_visible=False,
      )
    )
  for index, row in enumerate(rows, start=1):
    elements.append(
      _svg_shape_label_badge(
        label=str(index),
        bounds=row["latest_candidate_geometry"]["bounds"],
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        offset_index=index,
      )
    )
  item_lines = [
    f'{index}. {row["item_id"]}'
    for index, row in enumerate(rows, start=1)
  ]
  line_height = 15
  start_y = height - 18 - line_height * len(item_lines)
  for index, item_line in enumerate(item_lines):
    elements.append(
      f'<text x="18" y="{start_y + index * line_height:.2f}" '
      f'font-size="11" font-family="monospace" fill="#334155">'
      f'{html.escape(item_line)}</text>'
    )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _subcomponent_latest_tile_elements(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  width: int,
  height: int,
  label: str,
) -> list[str]:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_latest_component_zoom(
    row,
    axes,
  )
  view_bounds = _fit_view_bounds_to_screen_aspect(
    view_bounds,
    width=width,
    height=height,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" '
    f'fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>',
    (
      f'<text x="8" y="18" font-size="12" font-family="monospace" '
      f'fill="#334155">{html.escape(view)} local zoom ({view_label})</text>'
    ),
  ]
  latest_child = {
    "prior_shape": row["candidate_evaluation_shape"],
    "constrained_geometry": row["latest_candidate_geometry"],
  }
  component_shape = (
    _svg_projected_prior_shape(
      child=latest_child,
      axes=axes,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color="#2563eb",
      fill_opacity=0.72,
      stroke_width=4.0,
      stroke_color="#1e3a8a",
      label=f'{label}. {row["item_id"]}',
      label_visible=False,
    )
  )
  elements.append(component_shape)
  elements.append(
    _svg_scale_bar(
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
  )
  return elements


def _subcomponent_latest_by_component_atlas_svg(
  *,
  fine_proxy: dict[str, Any],
  rows: list[dict[str, Any]],
  start_index: int,
  part_label: str,
  width: int = 1880,
  label_width: int = 430,
  tile_width: int = 460,
  tile_height: int = 250,
  header_height: int = 78,
  row_gap: int = 18,
  gutter: int = 12,
) -> str:
  row_height = tile_height + row_gap
  height = header_height + len(rows) * row_height + 26
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="18" y="28" font-size="18" font-weight="700" '
      f'font-family="Arial, sans-serif" fill="#111827">'
      f'R20 latest subcomponents by component / {html.escape(part_label)}</text>'
    ),
    (
      f'<text x="18" y="52" font-size="12" font-family="monospace" '
      f'fill="#475569">one row = one latest subcomponent; '
      f'columns = top / side / front local zoom; '
      f'blue=that row latest candidate; each panel includes a meter scale bar; '
      f'airframe context is omitted here so the subcomponent body is visible</text>'
    ),
  ]
  for row_offset, row in enumerate(rows):
    item_index = start_index + row_offset
    row_y = header_height + row_offset * row_height
    elements.append(
      f'<rect x="12" y="{row_y - 8}" width="{width - 24}" '
      f'height="{tile_height + 12}" fill="#f8fafc" '
      f'stroke="#e2e8f0" stroke-width="1"/>'
    )
    label_y = row_y + 24
    elements.extend(
      [
        (
          f'<text x="22" y="{label_y}" font-size="15" font-weight="700" '
          f'font-family="monospace" fill="#111827">'
          f'{item_index}. {html.escape(row["item_id"])}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 22}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'shape={html.escape(row["candidate_evaluation_shape"])}; '
          f'outside={row["latest_candidate_silhouette"]["outside_sample_count"]}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 40}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'dims_m={html.escape(str(row["nominal_dimensions_m"]))}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 58}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'center={html.escape(str(row["latest_candidate_geometry"]["center_m"]))}</text>'
        ),
        (
          f'<text x="22" y="{label_y + 76}" font-size="11" '
          f'font-family="monospace" fill="#475569">'
          f'{html.escape(row["latest_candidate_stage"])}</text>'
        ),
      ]
    )
    for view_index, view in enumerate(("top", "side", "front")):
      tile_x = label_width + view_index * (tile_width + gutter)
      tile_elements = _subcomponent_latest_tile_elements(
        fine_proxy=fine_proxy,
        row=row,
        view=view,
        width=tile_width,
        height=tile_height,
        label=str(item_index),
      )
      elements.append(
        f'<g transform="translate({tile_x},{row_y})">'
        + "\n".join(tile_elements)
        + "</g>"
      )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>\n"
  )


def _subcomponent_shape_placement_mini_svg(
  *,
  fine_proxy: dict[str, Any],
  row: dict[str, Any],
  view: str,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_shape_placement(
    fine_proxy=fine_proxy,
    row=row,
    view=view,
    axes=axes,
  )
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">'
      f'{html.escape(row["item_id"])} latest subcomponent candidate / {view} ({view_label})</text>'
    ),
  ]
  for proxy in fine_proxy["proxies"]:
    hull_points = (
      proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  latest_child = {
    "prior_shape": row["candidate_evaluation_shape"],
    "constrained_geometry": row["latest_candidate_geometry"],
  }
  latest_color = "#2563eb"
  elements.append(
    _svg_projected_prior_shape(
      child=latest_child,
      axes=axes,
      view_bounds=view_bounds,
      width=width,
      height=height,
      color=latest_color,
      fill_opacity=0.34,
      stroke_width=3.0,
      stroke_color="#1e3a8a",
      label=(
        f'{row["item_id"]} latest '
        f'{row["latest_candidate_stage"]}'
      ),
      label_visible=False,
    )
  )
  elements.append(
    f'<text x="12" y="{height - 28}" font-size="10" font-family="monospace" fill="#475569">'
    f'latest outside={row["latest_candidate_silhouette"]["outside_sample_count"]}; '
    f'latest stage={html.escape(row["latest_candidate_stage"])}; '
    f'total offset={row["latest_candidate_total_center_offset_m"]}</text>'
  )
  elements.append(
    f'<text x="12" y="{height - 12}" font-size="10" font-family="monospace" fill="#475569">'
    'gray=whole-airframe wireframe; blue=latest subcomponent candidate</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_subcomponent_shape_placement_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  shape_report: dict[str, Any],
  overview_triptych_svg: Path,
  latest_component_atlas_svgs: list[Path],
) -> Path:
  index_path = root_dir / "index.html"
  atlas_images = "\n".join(
    f'<img src="{html.escape(path.name)}" '
    f'alt="R20 latest subcomponent candidates by component {index}">'
    for index, path in enumerate(latest_component_atlas_svgs, start=1)
  )
  if atlas_images:
    atlas_note = (
      "Each row is one R20 latest subcomponent candidate, with top, side, "
      "and front local-zoom views shown separately. Historical current/shape/"
      "centerline layers are intentionally absent here."
    )
  else:
    atlas_note = (
      "R21 promotion leaves no remaining subcomponent shape-placement rows; "
      "top, side, and front overview views are retained as the audit trace."
    )
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  if not cards:
    cards = (
      '<p>No remaining subcomponent shape-placement candidates after '
      'R21 review-only rule promotion.</p>'
    )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Subcomponent Shape Placement Candidates</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      margin-top: 12px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #d97706;
      border-radius: 6px;
      padding: 12px;
      background: #fffdf7;
    }}
    article.resolved {{
      border-left-color: #16a34a;
      background: #f8fff9;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Subcomponent Shape Placement Candidates</h1>
    <p>Review-only latest subcomponent candidates for items that previously exposed samples outside the whole-airframe top/side/front silhouettes. Nominal dimensions are preserved; older current/shape/centerline layers are retained only as trace data, and none are active runtime damage components.</p>
    <div class="summary">
      <div>shape candidates: {shape_report["summary"]["shape_placement_candidate_count"]}</div>
      <div>latest resolved candidates: {shape_report["summary"]["latest_candidate_resolves_exposure_count"]}</div>
      <div>latest unresolved candidates: {shape_report["summary"]["latest_candidate_unresolved_exposure_count"]}</div>
      <div>latest outside samples: {shape_report["summary"]["latest_candidate_total_outside_sample_count"]}</div>
      <div>latest total reduction: {shape_report["summary"]["latest_candidate_total_outside_sample_reduction"]}</div>
      <div>runtime active: {shape_report["summary"]["runtime_active_component_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
    </div>
  </header>
  <section>
    <h2>Latest Candidate Atlas</h2>
    <p>{html.escape(atlas_note)}</p>
    {atlas_images}
  </section>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _subcomponent_shape_placement_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["item_id"])} shape placement candidate</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to shape placement index</a></p>
    <h1>{html.escape(row["item_id"])}</h1>
    <p class="subtitle">{html.escape(row["current_shape"])} -> {html.escape(row["candidate_shape_family"])}; {html.escape(row["shape_design_status"])}</p>
  </header>
  <section>
    <h2>Candidate Details</h2>
    {_triage_list([
      f'item: {row["item_id"]}',
      f'type: {row["record_type"]}',
      f'system: {row["system"]}',
      f'role: {row["component_role"]}',
      f'current shape: {row["current_shape"]} axis={row["current_axis"] or "none"}',
      f'candidate evaluation shape: {row["candidate_evaluation_shape"]} axis={row["candidate_evaluation_axis"] or "none"}',
      f'nominal dimensions m: {row["nominal_dimensions_m"]}',
      f'dimension policy: {row["dimension_policy"]}',
      f'placement policy: {row["placement_policy"]}',
      f'current outside samples: {row["current_silhouette"]["outside_sample_count"]}',
      f'candidate outside samples: {row["candidate_silhouette"]["outside_sample_count"]}',
      f'candidate center shift m: {row["candidate_center_shift_m"]}',
      f'centerline candidate offset m: {row["centerline_candidate_center_offset_m"]}',
      f'centerline candidate center m: {row["centerline_candidate_geometry"]["center_m"]}',
      f'centerline candidate outside samples: {row["centerline_candidate_silhouette"]["outside_sample_count"]}',
      f'centerline candidate status: {row["centerline_candidate_status"]}',
      f'centerline candidate action: {row["centerline_candidate_recommended_action"]}',
      f'latest candidate stage: {row["latest_candidate_stage"]}',
      f'latest candidate center m: {row["latest_candidate_geometry"]["center_m"]}',
      f'latest candidate outside samples: {row["latest_candidate_silhouette"]["outside_sample_count"]}',
      f'latest candidate status: {row["latest_candidate_status"]}',
      f'latest candidate action: {row["latest_candidate_recommended_action"]}',
      f'recommended action: {row["recommended_action"]}',
      f'rationale: {row["design_rationale"]}',
      f'centerline rationale: {row["centerline_candidate_rationale"]}',
      f'latest rationale: {row["latest_candidate_rationale"]}',
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["item_id"])} {html.escape(view)} shape candidate"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_subcomponent_shape_placement_review_views(
  *,
  shape_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "subcomponent_shape_placement_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  component_dir = root_dir / "components"
  component_dir.mkdir(parents=True, exist_ok=True)
  overview_svg_paths: dict[str, Path] = {}
  for view in ("top", "side", "front"):
    overview_svg_path = root_dir / f"overview_latest_{view}.svg"
    overview_svg_path.write_text(
      _subcomponent_latest_overview_svg(
        fine_proxy=fine_proxy,
        shape_report=shape_report,
        view=view,
      ),
      encoding="utf-8",
    )
    overview_svg_paths[view] = overview_svg_path
  overview_width = 1500
  overview_height = 860
  overview_triptych_path = root_dir / "overview_latest_triptych.svg"
  triptych_width = overview_width * 3
  triptych_parts = [
    f'<rect x="0" y="0" width="{triptych_width}" height="{overview_height}" fill="#ffffff"/>',
  ]
  for index, view in enumerate(("top", "side", "front")):
    svg_text = overview_svg_paths[view].read_text(encoding="utf-8")
    body_start = svg_text.find(">") + 1
    body_end = svg_text.rfind("</svg>")
    triptych_parts.append(
      f'<g transform="translate({index * overview_width},0)">'
      + svg_text[body_start:body_end]
      + "</g>"
    )
  overview_triptych_path.write_text(
    (
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{triptych_width}" '
      f'height="{overview_height}" viewBox="0 0 {triptych_width} {overview_height}">'
      + "\n".join(triptych_parts)
      + "</svg>\n"
    ),
    encoding="utf-8",
  )
  latest_component_atlas_paths: list[Path] = []
  atlas_part_size = 5
  for part_index, start in enumerate(
    range(0, len(shape_report["rows"]), atlas_part_size),
    start=1,
  ):
    part_rows = shape_report["rows"][start:start + atlas_part_size]
    atlas_path = root_dir / f"overview_latest_by_component_part{part_index}.svg"
    atlas_path.write_text(
      _subcomponent_latest_by_component_atlas_svg(
        fine_proxy=fine_proxy,
        rows=part_rows,
        start_index=start + 1,
        part_label=f"part {part_index}",
      ),
      encoding="utf-8",
    )
    latest_component_atlas_paths.append(atlas_path)
  entries: list[dict[str, Any]] = []
  for row in shape_report["rows"]:
    safe_slug = _review_slug(row["item_id"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = component_dir / svg_filename
      svg_path.write_text(
        _subcomponent_shape_placement_mini_svg(
          fine_proxy=fine_proxy,
          row=row,
          view=view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = component_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _subcomponent_shape_placement_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    resolved = row["latest_candidate_silhouette"]["outside_sample_count"] == 0
    entries.append(
      {
        "category": "subcomponent_shape_candidates",
        "slug": safe_slug,
        "title": row["item_id"],
        "subtitle": (
          f'{row["latest_candidate_stage"]}; '
          f'latest outside {row["latest_candidate_silhouette"]["outside_sample_count"]}'
        ),
        "priority": "resolved" if resolved else "warning",
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(component_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "item_id": row["item_id"],
        "candidate_shape_family": row["candidate_shape_family"],
        "shape_design_status": row["shape_design_status"],
        "centerline_candidate_status": row["centerline_candidate_status"],
        "latest_candidate_status": row["latest_candidate_status"],
        "decision_needed": row["latest_candidate_recommended_action"],
      }
    )
  index_path = _write_subcomponent_shape_placement_index(
    root_dir,
    entries,
    shape_report,
    overview_triptych_path,
    latest_component_atlas_paths,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_subcomponent_shape_placement_views.v1",
    "status": "subcomponent_shape_placement_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
    },
    "summary": {
      "entry_count": len(entries),
      "overview_view_count": len(overview_svg_paths),
      "latest_component_atlas_entry_count": len(shape_report["rows"]),
      "latest_component_atlas_part_count": len(latest_component_atlas_paths),
      "resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["latest_candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "unresolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["latest_candidate_silhouette"]["outside_sample_count"] > 0
      ),
      "shape_candidate_resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["candidate_silhouette"]["outside_sample_count"] == 0
      ),
      "centerline_candidate_resolved_entry_count": sum(
        1 for row in shape_report["rows"]
        if row["centerline_candidate_silhouette"]["outside_sample_count"] == 0
      ),
    },
    "index_html": "index.html",
    "overview_svg": {
      view: _relative_to(path, root_dir)
      for view, path in overview_svg_paths.items()
    },
    "overview_triptych_svg": _relative_to(overview_triptych_path, root_dir),
    "latest_component_atlas_svg": [
      _relative_to(path, root_dir) for path in latest_component_atlas_paths
    ],
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _projected_view_bounds_for_parent_child_layout(
  proxy: dict[str, Any],
  row: dict[str, Any],
  axes: tuple[int, int],
) -> tuple[float, float, float, float]:
  projected = [
    _project_bounds(proxy["source_region_bounds"], axes),
    _project_bounds(proxy["support_bounds"], axes),
    _project_bounds(row["source_region_bounds"], axes),
    _project_bounds(row["support_bounds"], axes),
    _project_bounds(row["whole_airframe_bounds"], axes),
  ]
  for child in row["child_receiver_priors"]:
    projected.append(
      _project_bounds(child["constrained_geometry"]["bounds"], axes)
    )
    for segment in child.get("held_segments", []):
      projected.append(_project_bounds(segment["geometry"]["bounds"], axes))
  for segment in row.get("cross_region_held_segment_overlays", []):
    projected.append(_project_bounds(segment["geometry"]["bounds"], axes))
  geometry = proxy["mesh_derived_review_geometry"]
  for view_record in geometry.get("hulls", {}).values():
    points = view_record.get("points_m", [])
    if points:
      projected.append(
        (
          min(point[0] for point in points),
          min(point[1] for point in points),
          max(point[0] for point in points),
          max(point[1] for point in points),
        )
      )
  min_x = min(bounds[0] for bounds in projected)
  min_y = min(bounds[1] for bounds in projected)
  max_x = max(bounds[2] for bounds in projected)
  max_y = max(bounds[3] for bounds in projected)
  span_x = max(max_x - min_x, 0.5)
  span_y = max(max_y - min_y, 0.5)
  return (
    min_x - span_x * 0.12,
    min_y - span_y * 0.12,
    max_x + span_x * 0.12,
    max_y + span_y * 0.12,
  )


def _svg_projected_prior_shape(
  *,
  child: dict[str, Any],
  axes: tuple[int, int],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
  color: str,
  label: str,
  fill_opacity: float = 0.2,
  stroke_width: float = 1.5,
  stroke_color: str | None = None,
  projected_bounds: tuple[float, float, float, float] | None = None,
  label_visible: bool = True,
) -> str:
  bounds = projected_bounds or _project_bounds(
    child["constrained_geometry"]["bounds"],
    axes,
  )
  min_x, min_y, max_x, max_y = bounds
  x, y = _svg_project_point(
    point=(min_x, max_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  max_screen_x, min_screen_y = _svg_project_point(
    point=(max_x, min_y),
    view_bounds=view_bounds,
    width=width,
    height=height,
  )
  rect_width = max(max_screen_x - x, 1.0)
  rect_height = max(min_screen_y - y, 1.0)
  center_x = x + rect_width * 0.5
  center_y = y + rect_height * 0.5
  escaped_label = html.escape(label)
  fill = f'fill="{color}" fill-opacity="{fill_opacity:.2f}"'
  stroke = stroke_color or color
  common = (
    f'{fill} stroke="{stroke}" stroke-width="{stroke_width:.2f}">'
    f'<title>{escaped_label}</title>'
  )
  shape = child["prior_shape"]
  if shape in {"sphere", "ellipsoid"}:
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" '
      f'rx="{rect_width * 0.5:.2f}" ry="{rect_height * 0.5:.2f}" '
      f'{common}</rect>'
    )
  elif shape == "capsule":
    radius = min(rect_width, rect_height) * 0.5
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" rx="{radius:.2f}" ry="{radius:.2f}" '
      f'{common}</rect>'
    )
  else:
    body = (
      f'<rect x="{x:.2f}" y="{y:.2f}" width="{rect_width:.2f}" '
      f'height="{rect_height:.2f}" {common}</rect>'
    )
  if not label_visible:
    return body
  return (
    body
    + "\n"
    f'<text x="{x + 4.0:.2f}" y="{y + 13.0:.2f}" font-size="10" '
    f'font-family="monospace" fill="{color}">{escaped_label}</text>'
  )


def _projected_hull_bounds(
  hull_points: list[list[float]],
) -> tuple[float, float, float, float] | None:
  if len(hull_points) < 3:
    return None
  return (
    min(point[0] for point in hull_points),
    min(point[1] for point in hull_points),
    max(point[0] for point in hull_points),
    max(point[1] for point in hull_points),
  )


def _fit_bounds_inside_parent_projection(
  bounds: tuple[float, float, float, float],
  parent_bounds: tuple[float, float, float, float],
  *,
  hull_points: list[list[float]] | None = None,
  child_index: int = 0,
  child_count: int = 1,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  parent_min_x, parent_min_y, parent_max_x, parent_max_y = parent_bounds
  parent_width = max(parent_max_x - parent_min_x, 1.0e-6)
  parent_height = max(parent_max_y - parent_min_y, 1.0e-6)
  max_ratio = 0.34 if child_count <= 2 else 0.24
  width = min(max(max_x - min_x, parent_width * 0.08), parent_width * max_ratio)
  height = min(max(max_y - min_y, parent_height * 0.08), parent_height * max_ratio)
  raw_center_x = (min_x + max_x) * 0.5
  raw_center_y = (min_y + max_y) * 0.5
  center_x = min(
    max(raw_center_x, parent_min_x + width * 0.5),
    parent_max_x - width * 0.5,
  )
  center_y = min(
    max(raw_center_y, parent_min_y + height * 0.5),
    parent_max_y - height * 0.5,
  )
  if hull_points:
    safe_center_x, safe_center_y, safe_distance = _projected_polygon_safe_point(
      hull_points,
      parent_bounds,
    )
    raw_candidate = (center_x, center_y)
    raw_distance = (
      _distance_to_projected_polygon_edges(raw_candidate, hull_points)
      if _point_in_projected_polygon(raw_candidate, hull_points)
      else 0.0
    )
    if child_count > 1:
      offset_slots = [
        (-0.42, 0.0),
        (0.42, 0.0),
        (0.0, -0.42),
        (0.0, 0.42),
        (0.0, 0.0),
      ]
      offset_x, offset_y = offset_slots[child_index % len(offset_slots)]
      candidate_center = (
        safe_center_x + safe_distance * offset_x,
        safe_center_y + safe_distance * offset_y,
      )
    elif raw_distance >= safe_distance * 0.35:
      candidate_center = raw_candidate
    else:
      candidate_center = (safe_center_x, safe_center_y)
    if not _point_in_projected_polygon(candidate_center, hull_points):
      candidate_center = (safe_center_x, safe_center_y)
    center_x, center_y = candidate_center
    edge_distance = _distance_to_projected_polygon_edges(
      (center_x, center_y),
      hull_points,
    )
    safe_half_diagonal = max(edge_distance * 0.62, 1.0e-6)
    safe_axis_span = max(safe_half_diagonal * math.sqrt(2.0), 1.0e-6)
    width = min(width, safe_axis_span)
    height = min(height, safe_axis_span)
  return (
    center_x - width * 0.5,
    center_y - height * 0.5,
    center_x + width * 0.5,
    center_y + height * 0.5,
  )


def _shift_bounds_inside_parent_projection_preserve_size(
  bounds: tuple[float, float, float, float],
  parent_bounds: tuple[float, float, float, float],
  *,
  hull_points: list[list[float]] | None = None,
  child_index: int = 0,
  child_count: int = 1,
) -> tuple[float, float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  width = max(max_x - min_x, 1.0e-6)
  height = max(max_y - min_y, 1.0e-6)
  parent_min_x, parent_min_y, parent_max_x, parent_max_y = parent_bounds
  center_x = (min_x + max_x) * 0.5
  center_y = (min_y + max_y) * 0.5
  if hull_points:
    safe_center_x, safe_center_y, safe_distance = _projected_polygon_safe_point(
      hull_points,
      parent_bounds,
    )
    candidate_center = (center_x, center_y)
    if not _point_in_projected_polygon(candidate_center, hull_points):
      candidate_center = (safe_center_x, safe_center_y)
    if child_count > 1 and safe_distance > 1.0e-6:
      offset_slots = [
        (-0.35, 0.0),
        (0.35, 0.0),
        (0.0, -0.35),
        (0.0, 0.35),
        (0.0, 0.0),
      ]
      offset_x, offset_y = offset_slots[child_index % len(offset_slots)]
      offset_candidate = (
        safe_center_x + safe_distance * offset_x,
        safe_center_y + safe_distance * offset_y,
      )
      if _point_in_projected_polygon(offset_candidate, hull_points):
        candidate_center = offset_candidate
    center_x, center_y = candidate_center
  if width <= parent_max_x - parent_min_x:
    center_x = min(
      max(center_x, parent_min_x + width * 0.5),
      parent_max_x - width * 0.5,
    )
  if height <= parent_max_y - parent_min_y:
    center_y = min(
      max(center_y, parent_min_y + height * 0.5),
      parent_max_y - height * 0.5,
    )
  return (
    center_x - width * 0.5,
    center_y - height * 0.5,
    center_x + width * 0.5,
    center_y + height * 0.5,
  )


def _projected_polygon_safe_point(
  points: list[list[float]],
  bounds: tuple[float, float, float, float],
) -> tuple[float, float, float]:
  min_x, min_y, max_x, max_y = bounds
  centroid = _projected_polygon_centroid(points)
  candidates: list[tuple[float, float]] = [
    centroid,
    ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5),
  ]
  steps = (0.18, 0.30, 0.42, 0.50, 0.58, 0.70, 0.82)
  for x_fraction in steps:
    for y_fraction in steps:
      candidates.append(
        (
          min_x + (max_x - min_x) * x_fraction,
          min_y + (max_y - min_y) * y_fraction,
        )
      )
  best_point = centroid
  best_distance = -1.0
  for candidate in candidates:
    if not _point_in_projected_polygon(candidate, points):
      continue
    distance = _distance_to_projected_polygon_edges(candidate, points)
    if distance > best_distance:
      best_point = candidate
      best_distance = distance
  if best_distance >= 0.0:
    return best_point[0], best_point[1], best_distance
  return centroid[0], centroid[1], 0.0


def _projected_polygon_centroid(
  points: list[list[float]],
) -> tuple[float, float]:
  if not points:
    return 0.0, 0.0
  return (
    sum(point[0] for point in points) / len(points),
    sum(point[1] for point in points) / len(points),
  )


def _point_in_projected_polygon(
  point: tuple[float, float],
  polygon: list[list[float]],
) -> bool:
  if len(polygon) < 3:
    return False
  x, y = point
  inside = False
  previous = polygon[-1]
  for current in polygon:
    x1, y1 = previous[0], previous[1]
    x2, y2 = current[0], current[1]
    crosses = (y1 > y) != (y2 > y)
    if crosses:
      x_intersection = (x2 - x1) * (y - y1) / (y2 - y1 + 1.0e-12) + x1
      if x < x_intersection:
        inside = not inside
    previous = current
  return inside


def _distance_to_projected_polygon_edges(
  point: tuple[float, float],
  polygon: list[list[float]],
) -> float:
  if len(polygon) < 2:
    return 0.0
  point_x, point_y = point
  distances: list[float] = []
  previous = polygon[-1]
  for current in polygon:
    x1, y1 = previous[0], previous[1]
    x2, y2 = current[0], current[1]
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 1.0e-12:
      distances.append(math.hypot(point_x - x1, point_y - y1))
    else:
      t = max(
        0.0,
        min(1.0, ((point_x - x1) * dx + (point_y - y1) * dy) / length_sq),
      )
      closest_x = x1 + t * dx
      closest_y = y1 + t * dy
      distances.append(math.hypot(point_x - closest_x, point_y - closest_y))
    previous = current
  return min(distances) if distances else 0.0


def _svg_clip_path_for_hull(
  *,
  clip_id: str,
  hull_points: list[list[float]],
  view_bounds: tuple[float, float, float, float],
  width: int,
  height: int,
) -> str:
  screen_points = [
    _svg_project_point(
      point=(point[0], point[1]),
      view_bounds=view_bounds,
      width=width,
      height=height,
    )
    for point in hull_points
  ]
  point_text = " ".join(
    f"{point[0]:.2f},{point[1]:.2f}" for point in screen_points
  )
  return (
    f'<defs><clipPath id="{html.escape(clip_id)}" clipPathUnits="userSpaceOnUse">'
    f'<polygon points="{point_text}"/></clipPath></defs>'
  )


def _semantic_parent_child_layout_mini_svg(
  proxy: dict[str, Any],
  airframe_proxies: list[dict[str, Any]],
  row: dict[str, Any],
  view: str,
  *,
  width: int = 960,
  height: int = 620,
) -> str:
  axes_by_view = {
    "top": (0, 1, "x/y"),
    "side": (0, 2, "x/z"),
    "front": (1, 2, "y/z"),
  }
  axis_x, axis_y, view_label = axes_by_view[view]
  axes = (axis_x, axis_y)
  view_bounds = _projected_view_bounds_for_parent_child_layout(
    proxy,
    row,
    axes,
  )
  geometry = proxy["mesh_derived_review_geometry"]
  hull_points = geometry.get("hulls", {}).get(view, {}).get("points_m", [])
  elements = [
    f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    (
      f'<text x="12" y="20" font-size="13" font-family="monospace" fill="#111827">'
      f'{html.escape(row["source_region_id"])} parent + receiver priors / {view} ({view_label})</text>'
    ),
  ]
  for airframe_proxy in airframe_proxies:
    airframe_hull_points = (
      airframe_proxy["mesh_derived_review_geometry"]
      .get("hulls", {})
      .get(view, {})
      .get("points_m", [])
    )
    if len(airframe_hull_points) >= 3:
      elements.append(
        _svg_polygon_projected(
          points=airframe_hull_points,
          view_bounds=view_bounds,
          width=width,
          height=height,
          color="#94a3b8",
          label="whole_airframe_region",
          fill_opacity=0.0,
          stroke_width=1.0,
          label_visible=False,
        )
      )
  if len(hull_points) >= 3:
    elements.append(
      _svg_polygon_projected(
        points=hull_points,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#2563eb",
        label="parent_mesh_region",
        fill_opacity=0.0,
        stroke_width=2.5,
        label_visible=False,
      )
    )
  child_elements: list[str] = []
  child_count = len(row["child_receiver_priors"])
  for child_index, child in enumerate(row["child_receiver_priors"]):
    if child["is_cross_region_held"]:
      color = "#be123c"
      role_label = "held-segment"
    elif child["layout_role"] in {
      "single_receiver_overlay",
      "primary_receiver_overlay",
    }:
      color = "#16a34a"
      role_label = "primary"
    else:
      color = "#0891b2"
      role_label = "extra"
    if child["is_cross_region_held"] and child.get("held_segments"):
      for segment in child["held_segments"]:
        segment_child = {
          "prior_shape": segment["segment_shape"],
          "constrained_geometry": segment["geometry"],
        }
        child_elements.append(
          _svg_projected_prior_shape(
            child=segment_child,
            axes=axes,
            view_bounds=view_bounds,
            width=width,
            height=height,
            color=color,
            fill_opacity=0.78,
            stroke_width=3.0,
            stroke_color="#7f1d1d",
            label=(
              f'{child["component_name"]}:{segment["segment_id"]} '
              f'{segment["segment_shape"]} {role_label}'
            ),
            projected_bounds=_project_bounds(segment["geometry"]["bounds"], axes),
            label_visible=False,
          )
        )
      continue
    projected_bounds = _project_bounds(child["constrained_geometry"]["bounds"], axes)
    child_elements.append(
      _svg_projected_prior_shape(
        child=child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color=color,
        fill_opacity=0.92,
        stroke_width=2.2,
        label=(
          f'{child["component_name"]} '
          f'{child["prior_shape"]} {role_label}'
        ),
        projected_bounds=projected_bounds,
        label_visible=False,
      )
    )
  for segment in row.get("cross_region_held_segment_overlays", []):
    segment_child = {
      "prior_shape": segment["segment_shape"],
      "constrained_geometry": segment["geometry"],
    }
    child_elements.append(
      _svg_projected_prior_shape(
        child=segment_child,
        axes=axes,
        view_bounds=view_bounds,
        width=width,
        height=height,
        color="#be123c",
        fill_opacity=0.52,
        stroke_width=2.6,
        stroke_color="#7f1d1d",
        label=(
          f'{segment["parent_component_name"]}:{segment["segment_id"]} '
          "external held-segment"
        ),
        projected_bounds=_project_bounds(segment["geometry"]["bounds"], axes),
        label_visible=False,
      )
    )
  elements.extend(child_elements)
  elements.append(
    f'<text x="12" y="{height - 12}" font-size="10" font-family="monospace" fill="#475569">'
    'gray=whole-airframe wireframe; blue=parent semantic region; green/cyan=actual-size receiver prior; red=held split segment</text>'
  )
  return (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    + "\n".join(elements)
    + "</svg>"
  )


def _write_semantic_parent_child_layout_index(
  root_dir: Path,
  entries: list[dict[str, Any]],
  layout_report: dict[str, Any],
) -> Path:
  index_path = root_dir / "index.html"
  cards = "".join(
    f"""
    <article class="{html.escape(entry["priority"])}">
      <h2><a href="{html.escape(entry["html"])}">{html.escape(entry["title"])}</a></h2>
      <p>{html.escape(entry["subtitle"])}</p>
      <p>{html.escape(entry["decision_needed"])}</p>
    </article>
    """
    for entry in entries
  )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Semantic Parent-Child Component Layout Views</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      font-size: 18px;
    }}
    p {{
      color: #475569;
      line-height: 1.35;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .entry-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    article {{
      border: 1px solid #cbd5e1;
      border-left: 5px solid #16a34a;
      border-radius: 6px;
      padding: 12px;
      background: #f8fff9;
    }}
    article.warning {{
      border-left-color: #be123c;
      background: #fff7f7;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>F-16 Semantic Parent-Child Component Layout Views</h1>
    <p>Primary review view: 14 mesh-derived parent shell parts, with actual-size receiver priors overlaid where public dimensions or explicitly graded engineering proxies exist. The extra receiver slots are visual overlays, not accepted runtime ownership.</p>
    <div class="summary">
      <div>parent shell parts: {layout_report["summary"]["parent_semantic_component_count"]}</div>
      <div>receiver priors overlaid: {layout_report["summary"]["bound_receiver_component_count"]}</div>
      <div>extra receiver slots: {layout_report["summary"]["extra_receiver_slot_count"]}</div>
      <div>cross-region held receivers: {layout_report["summary"]["cross_region_held_receiver_count"]}</div>
      <div>held split segments: {layout_report["summary"]["cross_region_held_segment_count"]}</div>
      <div>external held segment overlays: {layout_report["summary"]["cross_region_held_segment_overlay_count"]}</div>
      <div>runtime active components: {layout_report["summary"]["runtime_active_component_count"]}</div>
      <div><a href="../scene.html">overview packet</a></div>
      <div><a href="../semantic_damage_geometry_views/index.html">semantic shell views</a></div>
      <div><a href="../internal_component_prior_views/index.html">receiver prior views</a></div>
    </div>
  </header>
  <section>
    <div class="entry-grid">
      {cards}
    </div>
  </section>
</main>
</body>
</html>
"""
  index_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return index_path


def _semantic_parent_child_layout_view_page(
  *,
  row: dict[str, Any],
  svg_filenames: dict[str, str],
) -> str:
  child_lines = [
    (
      f'{child["layout_role"]}: {child["component_name"]} '
      f'{child["prior_shape"]} dims={child["nominal_dimensions_m"]}m '
      f'evidence={child["size_evidence_level"]} '
      f'segments={child["held_segment_count"]} -> {child["constraint_status"]}'
    )
    for child in row["child_receiver_priors"]
  ]
  external_segment_lines = [
    (
      f'{segment["parent_component_name"]}:{segment["segment_id"]} '
      f'{segment["segment_shape"]} owners={segment["owner_region_ids"]} '
      f'dims={segment["nominal_dimensions_m"]}m'
    )
    for segment in row["cross_region_held_segment_overlays"]
  ]
  return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(row["parent_semantic_component_id"])} parent-child layout view</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0;
    }}
    .subtitle {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-top: 8px;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 5px 12px;
      margin: 0;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    figure {{
      margin: 0 0 18px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px;
    }}
    figcaption {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
  <header>
    <p><a href="../index.html">Back to parent-child layout index</a></p>
    <h1>{html.escape(row["parent_semantic_component_id"])}</h1>
    <p class="subtitle">{html.escape(row["geometry_primitive"])} parent -> {html.escape(row["source_region_id"])}; receiver overlays {row["bound_receiver_count"]}; extra slots {row["extra_receiver_slot_count"]}</p>
  </header>
  <section>
    <h2>Trace Details</h2>
    {_triage_list([
      f'parent semantic component: {row["parent_semantic_component_id"]}',
      f'parent surface component: {row["parent_surface_component_id"]}',
      f'outer model region: {row["source_region_id"]}',
      f'volume role: {row["volume_component_role"]}',
      f'geometry primitive: {row["geometry_primitive"]}',
      f'primary receiver: {row["primary_receiver_component_name"] or "none"}',
      "extra receivers: " + (", ".join(row["extra_receiver_component_names"]) or "none"),
      "cross-region held receivers: " + (", ".join(row["cross_region_held_receiver_names"]) or "none"),
      "external held split segments: " + (
        ", ".join(
          segment["segment_id"]
          for segment in row["cross_region_held_segment_overlays"]
        )
        or "none"
      ),
      f'parent handoff: {row["parent_receiver_handoff_status"]}',
      f'layout policy: {row["layout_policy"]}',
      f'runtime projection: {row["runtime_projection_status"]}',
      "child overlays:",
      *child_lines,
      "external held segment overlays:",
      *external_segment_lines,
    ])}
  </section>
  <section>
    {''.join(
      f'<figure><figcaption>{html.escape(view)} view</figcaption><img src="{html.escape(filename)}" alt="{html.escape(row["parent_semantic_component_id"])} {html.escape(view)} view"></figure>'
      for view, filename in svg_filenames.items()
    )}
  </section>
</main>
</body>
</html>
"""


def write_semantic_parent_child_layout_review_views(
  *,
  layout_report: dict[str, Any],
  fine_proxy: dict[str, Any],
  output_dir: Path,
) -> tuple[Path, Path]:
  root_dir = output_dir / "semantic_parent_child_layout_views"
  if root_dir.exists():
    shutil.rmtree(root_dir)
  root_dir.mkdir(parents=True, exist_ok=True)
  parent_dir = root_dir / "parents"
  parent_dir.mkdir(parents=True, exist_ok=True)
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  entries: list[dict[str, Any]] = []
  for row in layout_report["rows"]:
    proxy = proxies_by_region[row["source_region_id"]]
    safe_slug = _review_slug(row["parent_semantic_component_id"])
    svg_filenames: dict[str, str] = {}
    for view in ("top", "side", "front"):
      svg_filename = f"{safe_slug}_{view}.svg"
      svg_path = parent_dir / svg_filename
      svg_path.write_text(
        _semantic_parent_child_layout_mini_svg(
          proxy,
          fine_proxy["proxies"],
          row,
          view,
        ),
        encoding="utf-8",
      )
      svg_filenames[view] = svg_filename
    html_path = parent_dir / f"{safe_slug}.html"
    html_path.write_text(
      "\n".join(
        line.rstrip()
        for line in _semantic_parent_child_layout_view_page(
          row=row,
          svg_filenames=svg_filenames,
        ).splitlines()
      )
      + "\n",
      encoding="utf-8",
    )
    entries.append(
      {
        "category": "parent_shells",
        "slug": safe_slug,
        "title": row["parent_semantic_component_id"],
        "subtitle": (
          f'{row["source_region_id"]}: '
          f'{row["bound_receiver_count"]} receiver overlays, '
          f'{row["extra_receiver_slot_count"]} extra, '
          f'{row["cross_region_held_segment_overlay_count"]} external held segments'
        ),
        "priority": (
          "warning"
          if (
            row["cross_region_held_receiver_names"]
            or row["cross_region_held_segment_overlay_count"] > 0
          )
          else "info"
        ),
        "html": _relative_to(html_path, root_dir),
        "svg": {
          view: _relative_to(parent_dir / filename, root_dir)
          for view, filename in svg_filenames.items()
        },
        "parent_semantic_component_id": row["parent_semantic_component_id"],
        "source_region_id": row["source_region_id"],
        "bound_receiver_count": row["bound_receiver_count"],
        "extra_receiver_slot_count": row["extra_receiver_slot_count"],
        "child_receiver_component_names": [
          child["component_name"] for child in row["child_receiver_priors"]
        ],
        "cross_region_held_receiver_names": row[
          "cross_region_held_receiver_names"
        ],
        "cross_region_held_segment_overlay_ids": [
          segment["segment_id"]
          for segment in row["cross_region_held_segment_overlays"]
        ],
        "decision_needed": (
          "Review red held overlays before runtime ownership decisions."
          if (
            row["cross_region_held_receiver_names"]
            or row["cross_region_held_segment_overlay_count"] > 0
          )
          else "Review receiver overlays inside this parent before activation."
        ),
      }
    )

  index_path = _write_semantic_parent_child_layout_index(
    root_dir,
    entries,
    layout_report,
  )
  manifest_path = root_dir / "manifest.json"
  manifest = {
    "schema_version": "a2.target_geometry_semantic_parent_child_layout_views.v1",
    "status": "semantic_parent_child_layout_views_generated_review_only",
    "authority_boundary": {
      "runtime_damage_model": False,
      "runtime_active_component": False,
      "true_internal_component_geometry": False,
      "parent_child_damage_ownership": False,
    },
    "summary": {
      "entry_count": len(entries),
      "parent_entry_count": len(entries),
      "bound_receiver_component_count": layout_report["summary"][
        "bound_receiver_component_count"
      ],
      "extra_receiver_slot_count": layout_report["summary"][
        "extra_receiver_slot_count"
      ],
      "cross_region_held_receiver_count": layout_report["summary"][
        "cross_region_held_receiver_count"
      ],
      "cross_region_held_segment_count": layout_report["summary"][
        "cross_region_held_segment_count"
      ],
      "cross_region_held_segment_overlay_count": layout_report["summary"][
        "cross_region_held_segment_overlay_count"
      ],
    },
    "index_html": "index.html",
    "entries": entries,
  }
  manifest_path.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  return index_path, manifest_path


def _surface_component_rows(
  surface_row: dict[str, Any],
  rows_by_component: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for link in surface_row["linked_internal_components"]:
    row = rows_by_component.get(link["component_name"])
    if row is not None:
      rows.append(row)
  return rows


def _component_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  anomalies = row["anomalies"]
  component_name = row["component_name"]
  region_id = row["bound_region_id"]
  semantics = row.get("review_semantics", "")
  if semantics == "side_sign_mismatch_hard_blocker":
    return (
      f"Does {component_name} belong on the opposite side from the {region_id} proxy, or are the left/right region labels flipped?",
      "In the top and front views, compare the red component box label with the blue mesh silhouette and orange source bounds for the wing or wing root.",
      "Choose one before TG-P7: swap/fix the coordinate-side convention, move the component box, or hold wing/root runtime use.",
    )
  if semantics == "invalid_region_binding_blocked":
    return (
      f"Why did {component_name} rank against blocked region {region_id}?",
      "Check whether the red component box is detached from its expected engine/nozzle surface and incorrectly overlapping a tail surface.",
      "Do not use this binding; repair the component box or mapping before runtime handoff.",
    )
  if semantics == "cross_region_boundary_candidate_review_only":
    return (
      f"Is {component_name} acceptable as a review-only cross-region boundary candidate?",
      "Check whether the red box center remains in the aft engine bay while its span crosses neighboring intake/nozzle semantics.",
      "Keep as review-only candidate or split it; do not treat this as accepted runtime integration.",
    )
  if semantics == "cross_region_structural_semantic_hold":
    return (
      f"Should {component_name} remain a held cross-region structural semantic candidate?",
      "Check the broad thin box across center fuselage and wing-root surfaces before assigning a single receiver.",
      "Hold or split the semantic receiver before runtime projection; low overlap alone is not a bad-box verdict.",
    )
  if "no_outer_region_overlap" in anomalies:
    return (
      f"Why does {component_name} not overlap its assigned outer region {region_id}?",
      "In all three views, check whether the red component box sits outside the blue silhouette or merely misses the orange source AABB due to height/axis drift.",
      "Decide whether to repair the current component box, change the outer-region mapping, or keep this component out of runtime handoff.",
    )
  if "low_outer_region_overlap" in anomalies:
    return (
      f"Is the low overlap for {component_name} intentional multi-region coverage or stale component geometry?",
      "Check whether the red box straddles a sensible neighboring surface or is visibly detached from the blue mesh silhouette.",
      "Accept only if the overlap is explainable; otherwise split/move the component box or mark the handoff held.",
    )
  return (
    f"Does {component_name} visibly match its assigned outer region {region_id}?",
    "Compare red component box, orange source bounds, gray support bounds, and blue mesh silhouette.",
    "Accept, repair component placement, or hold runtime use for this region.",
  )


def _surface_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  flags = row["review_flags"]
  surface_id = row["surface_component_id"]
  region_id = row["source_region_id"]
  missing = ", ".join(row["missing_existing_runtime_component_relations"]) or "none"
  semantics = row.get("review_semantics", "")
  if semantics == "missing_runtime_link/held":
    return (
      f"What runtime component should receive a hit on {surface_id}?",
      "The blue silhouette shows the outer surface; red/purple boxes show current internal components, if any. Empty or offset boxes mean the handoff is not explicit.",
      f"Add/identify the missing runtime relation ({missing}), or explicitly hold this surface from runtime projection.",
    )
  if semantics == "side_sign_mismatch_hard_blocker":
    return (
      f"Are the linked components for {surface_id} on the correct aircraft side?",
      "Use the top and front views to compare linked red boxes with the surface proxy side and the left/right names.",
      "Resolve side naming before accepting this surface handoff.",
    )
  if semantics == "invalid_region_binding_blocked":
    return (
      f"Which invalid component binding is polluting {surface_id}?",
      "Look for any red component linked through a blocked rule rather than a clean direct receiver.",
      "Block that relation in the review handoff and repair the source component or region mapping separately.",
    )
  if semantics in {
    "cross_region_semantic_hold",
    "cross_region_boundary_candidate_review_only",
  }:
    return (
      f"Which links for {surface_id} are clean direct receivers versus review-only cross-region semantics?",
      "Compare clean purple/red boxes with the cross-region component names listed in the trace details.",
      "Keep clean direct links separate, and keep cross-region links held or review-only until runtime ownership is explicit.",
    )
  if "linked_component_needs_review" in flags:
    return (
      f"Can {surface_id} hand off to its linked components while those component boxes still need review?",
      "Look for red labels inside or near the blue silhouette; red means the linked component's own binding is not clean.",
      "Fix or accept the linked component boxes first, then revisit this surface handoff.",
    )
  if "no_direct_component_bound_to_surface_region" in flags:
    return (
      f"Should {surface_id} have a direct internal component bound to {region_id}?",
      "Check whether any red/purple component box is actually colocated with the surface proxy.",
      "Accept an empty/non-direct surface only if damage should intentionally bypass current component records.",
    )
  return (
    f"Is {surface_id} a clean surface-to-component handoff?",
    "Confirm the surface proxy and linked component boxes occupy the same plausible aircraft area.",
    "Accept visually, or mark the handoff held.",
  )


def _point_triage_prompts(row: dict[str, Any]) -> tuple[str, str, str]:
  point_id = row["point_id"]
  if "beam" in point_id:
    return (
      f"Does {point_id} expose a left/right coordinate-sign problem?",
      "The black point is the review point; compare its lateral side with the nearest wing silhouette and the red candidate component labels.",
      "Do not use beam/wing projection at runtime until point side, wing side, and component names agree.",
    )
  if point_id.startswith("nose_axis"):
    return (
      f"Does {point_id} explain the nose close-to-shape behavior without relying on direct-hit boxes?",
      "The black point should be read against the nose/forward-fuselage blue silhouette and nearby red component boxes.",
      "Decide whether this point has a valid candidate-component path, or whether nose proximity must remain held.",
    )
  return (
    f"Does {point_id} have a plausible outer-surface and component interpretation?",
    "Compare the black point with the blue silhouette and any nearby red/purple component boxes.",
    "Accept as diagnostic-only, add missing component candidates, or hold runtime use.",
  )


def write_human_review_triage_dashboard(
  *,
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  surface_report: dict[str, Any],
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  path = output_dir / "human_review_triage.html"
  proxies_by_region = {
    proxy["source_region_id"]: proxy for proxy in fine_proxy["proxies"]
  }
  rows_by_component = _component_rows_by_name(component_report)
  surface_rows_by_region = {
    row["source_region_id"]: row for row in surface_report["rows"]
  }
  fine_rows_by_point = {
    row["point_id"]: row for row in fine_proxy["review_point_distance_deltas"]
  }

  sign_cards: list[str] = []
  placement_cards: list[str] = []
  for row in component_report["rows"]:
    if row["review_status"] == "candidate_binding":
      continue
    proxy = proxies_by_region.get(row["bound_region_id"])
    if proxy is None:
      continue
    details = [
      f'component: {row["component_name"]}',
      f'system: {row["system"]}',
      f'bound outer region: {row["bound_region_id"]}',
      f'review semantics: {row["review_semantics"]}',
      f'review severity: {row["review_severity"]}',
      f'component center distance to region: {row["center_distance_m"]} m',
      "anomalies: " + ", ".join(row["anomalies"]),
      "geometry observations: " + ", ".join(row["geometry_observations"]),
      "suppressed anomalies: " + (", ".join(row["suppressed_anomalies"]) or "none"),
      "semantic regions: " + (", ".join(row["semantic_region_ids"]) or "none"),
      "side relation: " + json.dumps(row["side_sign_relation"], sort_keys=True),
      "blocked region binding: "
      + json.dumps(row["blocked_region_binding"], sort_keys=True),
      "review notes: " + " | ".join(row["review_notes"]),
    ]
    question, look_at, decision = _component_triage_prompts(row)
    severity = (
      "critical"
      if row["review_severity"] == "hard_blocker"
      else "warning"
      if row["review_status"] == "needs_review"
      else "info"
    )
    card = _triage_card(
      title=row["component_name"],
      subtitle=f'component binding -> {row["bound_region_id"]}',
      question=question,
      look_at=look_at,
      decision=decision,
      details=details,
      proxy=proxy,
      component_rows=[row],
      severity=severity,
    )
    if row["review_semantics"] == "side_sign_mismatch_hard_blocker":
      sign_cards.append(card)
    else:
      placement_cards.append(card)

  surface_cards: list[str] = []
  for row in surface_report["rows"]:
    if row["review_status"] == "candidate_surface_component":
      continue
    proxy = proxies_by_region.get(row["source_region_id"])
    if proxy is None:
      continue
    component_rows = _surface_component_rows(row, rows_by_component)
    details = [
      f'surface component: {row["surface_component_id"]}',
      f'outer region: {row["source_region_id"]}',
      f'surface role: {row["surface_role"]}',
      f'proxy kind: {row["proxy_kind"]}',
      f'linked current components: {row["linked_internal_component_count"]}',
      f'clean direct links: {row["clean_direct_link_count"]}',
      f'review semantics: {row["review_semantics"]}',
      f'runtime relation status: {row["runtime_relation_status"]}',
      "clean direct components: "
      + (", ".join(row["clean_direct_component_names"]) or "none"),
      "cross-region semantic components: "
      + (", ".join(row["cross_region_semantic_component_names"]) or "none"),
      "blocked components: " + (", ".join(row["blocked_component_names"]) or "none"),
      "bad geometry components: "
      + (", ".join(row["bad_geometry_component_names"]) or "none"),
      "review flags: " + ", ".join(row["review_flags"]),
      "missing runtime links: "
      + (", ".join(row["missing_existing_runtime_component_relations"]) or "none"),
      "linked components: "
      + (
        ", ".join(link["component_name"] for link in row["linked_internal_components"])
        or "none"
      ),
    ]
    severity = (
      "critical"
      if row["review_semantics"]
      in {
        "missing_runtime_link/held",
        "side_sign_mismatch_hard_blocker",
        "invalid_region_binding_blocked",
      }
      else "warning"
    )
    question, look_at, decision = _surface_triage_prompts(row)
    surface_cards.append(
      _triage_card(
        title=row["surface_component_id"],
        subtitle=f'surface handoff -> {row["source_region_id"]}',
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        proxy=proxy,
        component_rows=component_rows,
        severity=severity,
      )
    )

  point_focus_ids = {
    "nose_axis_4m",
    "nose_axis_6m",
    "right_beam_4m",
    "left_beam_4m",
    "above_4m",
    "below_4m",
  }
  point_cards: list[str] = []
  for row in diagnostics["rows"]:
    if row["point_id"] not in point_focus_ids:
      continue
    fine_row = fine_rows_by_point.get(row["point_id"], {})
    region_id = row["nearest_outer_region_id"]
    proxy = proxies_by_region.get(region_id)
    if proxy is None:
      continue
    component_rows = [
      rows_by_component[item["component_name"]]
      for item in row["candidate_components"]
      if item["component_name"] in rows_by_component
    ]
    details = [
      f'point: {row["point_id"]} at {row["point_m"]}',
      f'nearest outer region: {row["nearest_outer_region_id"]}',
      f'nearest outer distance: {row["nearest_outer_distance_m"]} m',
      "nearest fine proxy: "
      + str(fine_row.get("nearest_fine_proxy_region_id", "unknown")),
      f'nearest component: {row["nearest_component_name"]}',
      f'nearest component distance: {row["nearest_component_distance_m"]} m',
      f'candidate component count: {row["candidate_component_count"]}',
      f'interpretation: {row["interpretation"]}',
    ]
    question, look_at, decision = _point_triage_prompts(row)
    point_cards.append(
      _triage_card(
        title=row["point_id"],
        subtitle="review point geometry sanity",
        question=question,
        look_at=look_at,
        decision=decision,
        details=details,
        proxy=proxy,
        component_rows=component_rows,
        severity="critical" if "beam" in row["point_id"] else "warning",
        review_points=[row],
      )
    )

  def section(title: str, intro: str, cards: list[str]) -> str:
    return f"""
      <section>
        <h2>{html.escape(title)} <span>{len(cards)}</span></h2>
        <p>{html.escape(intro)}</p>
        <div class="card-stack">
          {"".join(cards) if cards else '<p class="empty">No current items.</p>'}
        </div>
      </section>
    """

  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Human Review Triage</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 24px;
    }}
    header, section {{
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
      margin: 0 0 18px;
      padding: 18px;
    }}
    h1, h2, h3 {{
      margin: 0;
    }}
    h1 {{
      font-size: 26px;
    }}
    h2 {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      font-size: 20px;
      margin-bottom: 8px;
    }}
    h2 span {{
      color: #475569;
      font-family: monospace;
      font-size: 15px;
    }}
    p {{
      color: #475569;
      margin: 8px 0 0;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 14px;
      margin-top: 14px;
      font-family: monospace;
      font-size: 13px;
    }}
    .triage-card {{
      border: 2px solid #d97706;
      border-radius: 6px;
      margin: 0 0 16px;
      padding: 14px;
      background: #fffdf7;
    }}
    .triage-card.critical {{
      border-color: #be123c;
      background: #fff7f7;
    }}
    .triage-card.warning {{
      border-color: #d97706;
    }}
    .triage-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 8px;
    }}
    .triage-head span {{
      color: #475569;
      font-family: monospace;
      font-size: 13px;
    }}
    .decision-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 10px;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 10px;
      margin: 0 0 12px;
    }}
    .decision-box strong {{
      display: block;
      color: #0f172a;
      font-size: 12px;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .decision-box p {{
      color: #1f2937;
      font-size: 13px;
      line-height: 1.35;
      margin: 4px 0 0;
    }}
    ul {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 5px 12px;
      margin: 0 0 12px;
      padding-left: 20px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
    }}
    .mini-views {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 12px;
    }}
    svg {{
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      background: #ffffff;
    }}
    .empty {{
      color: #64748b;
      font-family: monospace;
    }}
    a {{
      color: #1d4ed8;
    }}
  </style>
</head>
<body>
<main>
	  <header>
	    <h1>F-16 Human Review Triage</h1>
	    <p>Answer the review question at the top of each card. The local top, side, and front overlays show exactly where to inspect before accepting, repairing, or holding the item.</p>
    <div class="summary">
      <div>component binding issues: {len(sign_cards) + len(placement_cards)}</div>
      <div>coordinate sign issues: {len(sign_cards)}</div>
      <div>surface handoff issues: {len(surface_cards)}</div>
      <div>focused review points: {len(point_cards)}</div>
      <div><a href="scene.html">overview packet</a></div>
      <div><a href="fine_proxy_review_dashboard.html">region dashboard</a></div>
      <div><a href="component_review_views/index.html">isolated component views</a></div>
    </div>
  </header>
  {section(
    "Coordinate Sign Review",
    "These cards are the left/right naming versus local-coordinate cases. Resolve them before trusting wing or wing-root handoff.",
    sign_cards,
  )}
  {section(
    "Component Box Placement Review",
    "These current internal components have low or missing overlap with the corrected outer region.",
    placement_cards,
  )}
  {section(
    "Surface Handoff Review",
    "These outer-surface candidates do not yet have clean, explicit links to current runtime damage components.",
    surface_cards,
  )}
  {section(
    "Review Point Geometry Sanity",
    "These points are the geometry cases that should be understood before any near-fuze, rod, or fragment runtime interface decision.",
    point_cards,
  )}
</main>
</body>
</html>
"""
  path.write_text("\n".join(line.rstrip() for line in body.splitlines()) + "\n", encoding="utf-8")
  return path


def write_fine_proxy_review_dashboard(
  fine_proxy: dict[str, Any],
  component_report: dict[str, Any],
  output_dir: Path,
  surface_report: dict[str, Any] | None = None,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  path = output_dir / "fine_proxy_review_dashboard.html"
  surface_rows_by_region = {
    row["source_region_id"]: row for row in (surface_report or {}).get("rows", [])
  }
  cards: list[str] = []
  for proxy in fine_proxy["proxies"]:
    region_id = proxy["source_region_id"]
    components = _component_rows_for_region(component_report, region_id)
    surface_row = surface_rows_by_region.get(region_id)
    flags = _fine_proxy_review_flags(proxy, components)
    status = _fine_proxy_review_status(flags)
    geometry = proxy["mesh_derived_review_geometry"]
    hull_counts = {
      view: record["point_count"] for view, record in geometry["hulls"].items()
    }
    component_list = ", ".join(
      f'{row["component_name"]}:{row["review_status"]}/{row["review_semantics"]}'
      for row in components
    ) or "none"
    if surface_row is None:
      surface_line = "surface component: not generated"
      surface_flags = "surface flags: not generated"
      surface_missing = "missing links: not generated"
    else:
      surface_line = (
        "surface component: "
        f'{surface_row["surface_component_id"]} ({surface_row["surface_role"]})'
      )
      surface_flags = (
        "surface flags: " + ", ".join(surface_row["review_flags"])
      )
      surface_missing = (
        "missing links: "
        + (
          ", ".join(surface_row["missing_existing_runtime_component_relations"])
          or "none"
        )
      )
      surface_line += f' semantics={surface_row["review_semantics"]}'
    card_class = "hold" if status == "hold_for_human_review" else (
      "review" if status == "needs_human_review" else "candidate"
    )
    cards.append(
      f"""
      <section class="region-card {card_class}">
        <div class="region-head">
          <h2>{html.escape(region_id)} <span>{html.escape(proxy["proxy_kind"])}</span></h2>
          <strong>{html.escape(status)}</strong>
        </div>
        <div class="metrics">
          <div>strategy: {html.escape(geometry.get("selection_strategy", ""))}</div>
          <div>fallback: {html.escape(geometry.get("fallback_policy", ""))}</div>
          <div>vertices: {geometry.get("region_vertex_count", 0)}</div>
          <div>source nodes: {html.escape(", ".join(geometry.get("source_node_names", [])) or "all")}</div>
          <div>hull points: top {hull_counts.get("top", 0)} / side {hull_counts.get("side", 0)} / front {hull_counts.get("front", 0)}</div>
          <div>flags: {html.escape(", ".join(flags))}</div>
          <div>components: {html.escape(component_list)}</div>
          <div>{html.escape(surface_line)}</div>
          <div>{html.escape(surface_flags)}</div>
          <div>{html.escape(surface_missing)}</div>
        </div>
        <div class="mini-views">
          {_fine_proxy_review_mini_svg(proxy, components, "top")}
          {_fine_proxy_review_mini_svg(proxy, components, "side")}
          {_fine_proxy_review_mini_svg(proxy, components, "front")}
        </div>
      </section>
      """
    )
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Fine Proxy Human Review Dashboard</title>
  <style>
    body {{
      margin: 0;
      background: #f8fafc;
      color: #111827;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
    }}
    .summary {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      padding: 14px 16px;
      margin-bottom: 18px;
      font-family: monospace;
      font-size: 13px;
    }}
    .region-card {{
      background: #ffffff;
      border: 2px solid #cbd5e1;
      margin: 0 0 18px;
      padding: 14px;
    }}
    .region-card.hold {{
      border-color: #dc2626;
    }}
    .region-card.review {{
      border-color: #d97706;
    }}
    .region-card.candidate {{
      border-color: #16a34a;
    }}
    .region-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: baseline;
      margin-bottom: 8px;
    }}
    h2 {{
      margin: 0;
      font-size: 18px;
    }}
    h2 span {{
      color: #475569;
      font-size: 13px;
      font-family: monospace;
      font-weight: 400;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 6px 12px;
      font-family: monospace;
      font-size: 12px;
      color: #334155;
      margin-bottom: 12px;
    }}
    .mini-views {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 12px;
    }}
    svg {{
      width: 100%;
      height: auto;
      border: 1px solid #cbd5e1;
      background: #ffffff;
    }}
  </style>
</head>
<body>
<main>
  <h1>F-16 Fine Proxy Human Review Dashboard</h1>
  <div class="summary">
    schema: {html.escape(fine_proxy["schema_version"])}<br>
    proxy_count: {fine_proxy["summary"]["proxy_count"]};
    mesh_silhouettes: {fine_proxy["summary"]["mesh_derived_silhouette_count"]};
    source_vertices: {fine_proxy["summary"]["mesh_source_vertex_count"]};
    review_status: {html.escape(fine_proxy["summary"]["review_status"])}<br>
    Review-only visual diagnostics. This is not a runtime collision mesh, not true F-16 engineering geometry, and not weapon lethality evidence.
  </div>
  {"".join(cards)}
</main>
</body>
</html>
"""
  body = "\n".join(line.rstrip() for line in body.splitlines()) + "\n"
  path.write_text(body, encoding="utf-8")
  return path


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
  header_html = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
  row_html = []
  for row in rows:
    row_html.append(
      "<tr>"
      + "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
      + "</tr>"
    )
  return (
    '<table>\n<thead><tr>'
    + header_html
    + "</tr></thead>\n<tbody>\n"
    + "\n".join(row_html)
    + "\n</tbody>\n</table>"
  )


def write_review_packet(
  *,
  manifest: dict[str, Any],
  mapping: dict[str, Any],
  component_report: dict[str, Any],
  diagnostics: dict[str, Any],
  fine_proxy: dict[str, Any] | None = None,
  surface_report: dict[str, Any] | None = None,
  semantic_report: dict[str, Any] | None = None,
  internal_prior_report: dict[str, Any] | None = None,
  held_segment_report: dict[str, Any] | None = None,
  airframe_constraint_report: dict[str, Any] | None = None,
  ownership_split_report: dict[str, Any] | None = None,
  runtime_activation_report: dict[str, Any] | None = None,
  runtime_behavior_report: dict[str, Any] | None = None,
  training_proxy_report: dict[str, Any] | None = None,
  shape_placement_report: dict[str, Any] | None = None,
  parent_child_layout_report: dict[str, Any] | None = None,
  output_dir: Path,
) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  html_path = output_dir / "scene.html"
  component_rows = [
    [
      row["component_name"],
      row["system"],
      row["bound_region_id"],
      row["review_status"],
      ";".join(row["anomalies"]),
    ]
    for row in component_report["rows"]
  ]
  diagnostic_rows = [
    [
      row["point_index"],
      row["point_id"],
      row["point_m"],
      row["nearest_outer_region_id"],
      row["nearest_outer_distance_m"],
      row["nearest_component_name"],
      row["nearest_component_distance_m"],
      row["candidate_component_count"],
      row["interpretation"],
    ]
    for row in diagnostics["rows"]
  ]
  surface_component_section = ""
  if surface_report is not None:
    surface_rows = [
      [
        row["surface_component_id"],
        row["source_region_id"],
        row["surface_role"],
        row["proxy_kind"],
        row["linked_internal_component_count"],
        row["clean_direct_link_count"],
        ",".join(row["clean_direct_component_names"]),
        ",".join(row["cross_region_semantic_component_names"]),
        ",".join(row["blocked_component_names"]),
        row["runtime_relation_status"],
        row["review_status"],
        row["review_semantics"],
        ";".join(row["review_flags"]),
      ]
      for row in surface_report["rows"]
    ]
    surface_component_section = f"""
  <section>
    <h2>Surface Component Candidates</h2>
    <p class="note">Review-only handoff layer from outer-shape hits to current component damage records. It does not replace the runtime damage model.</p>
    {_html_table(
      [
        "surface_component",
        "outer_region",
        "surface_role",
        "proxy_kind",
        "linked_components",
        "clean_direct_links",
        "clean_direct_components",
        "cross_region_components",
        "blocked_components",
        "runtime_relation_status",
        "status",
        "semantics",
        "flags",
      ],
      surface_rows,
    )}
  </section>
"""
  semantic_damage_geometry_section = ""
  if semantic_report is not None:
    semantic_rows = [
      [
        row["semantic_component_id"],
        row["source_region_id"],
        row["volume_component_role"],
        row["geometry_primitive"],
        ",".join(row["direct_receiver_components"]),
        ",".join(row["cross_region_receiver_components"]),
        row["receiver_handoff_status"],
        row["runtime_projection_status"],
      ]
      for row in semantic_report["rows"]
    ]
    semantic_damage_geometry_section = f"""
  <section>
    <h2>Semantic Damage Geometry Volumes</h2>
    <p class="note">Parse-ready outer-shell volume component candidates generated from TG-P6 mesh proxies and TG-P6 surface handoffs. These are not activated in the current runtime damage model.</p>
    <p class="note"><a href="semantic_damage_geometry_views/index.html">Open isolated semantic volume views</a>.</p>
    {_html_table(
      [
        "semantic_component",
        "outer_region",
        "volume_role",
        "primitive",
        "direct_receivers",
        "cross_region_receivers",
        "handoff_status",
        "runtime_status",
      ],
      semantic_rows,
    )}
  </section>
"""
  internal_component_prior_section = ""
  if internal_prior_report is not None:
    internal_rows = [
      [
        row["component_name"],
        row["system"],
        row["prior_shape"],
        row["prior_axis"],
        row["bound_region_id"],
        ",".join(row["constraint_region_ids"]),
        row["constraint_status"],
        row["constraint_adjustment"]["pre_constraint_outside_fraction"],
        row["constraint_adjustment"]["post_constraint_outside_fraction"],
        row["runtime_projection_status"],
      ]
      for row in internal_prior_report["rows"]
    ]
    internal_component_prior_section = f"""
  <section>
    <h2>Internal Component Prior Geometry</h2>
    <p class="note">Review-only synthetic receiver geometry generated from simple priors such as sphere, cylinder, capsule, and ellipsoid, then constrained inside parent shell support bounds.</p>
    <p class="note"><a href="internal_component_prior_views/index.html">Open isolated internal component prior views</a>.</p>
    {_html_table(
      [
        "component",
        "system",
        "prior_shape",
        "axis",
        "bound_region",
        "constraint_regions",
        "constraint_status",
        "pre_outside",
        "post_outside",
        "runtime_status",
      ],
      internal_rows,
    )}
  </section>
"""
  held_segment_section = ""
  if held_segment_report is not None:
    held_segment_rows = [
      [
        row["parent_component_name"],
        row["segment_id"],
        row["segment_role"],
        ",".join(row["owner_region_ids"]),
        row["segment_shape"],
        row["segment_axis"],
        ",".join(str(value) for value in row["nominal_dimensions_m"]),
        row["inside_whole_airframe_bounds"],
        row["runtime_projection_status"],
      ]
      for row in held_segment_report["rows"]
    ]
    held_segment_section = f"""
  <section>
    <h2>Cross-Region Held Split Segments</h2>
    <p class="note">Review-only split of held receivers (`engine_core`, `wing_spar_center`) into smaller owner-region segments. These red segments replace the monolithic held block in the parent-child visual views; runtime behavior is unchanged.</p>
    {_html_table(
      [
        "parent_component",
        "segment",
        "role",
        "owner_regions",
        "shape",
        "axis",
        "dims_m",
        "inside_airframe",
        "runtime_status",
      ],
      held_segment_rows,
    )}
  </section>
"""
  airframe_constraint_section = ""
  if airframe_constraint_report is not None:
    correction_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["prior_shape"],
        row["size_evidence_level"],
        ",".join(row["current_silhouette"]["outside_views"]),
        row["current_silhouette"]["outside_sample_count"],
        row["candidate_silhouette"]["outside_sample_count"],
        row["candidate_center_shift_m"],
        row["triage_status"],
        row["recommended_action"],
      ]
      for row in airframe_constraint_report["rows"]
      if (
        row["current_silhouette"]["outside_sample_count"] > 0
        or row["triage_status"] == "inside_airframe_low_confidence_size_review"
      )
    ]
    airframe_constraint_section = f"""
  <section>
    <h2>Airframe Constraint Correction Candidates</h2>
    <p class="note">Review-only R16 diagnostics for actual-size receiver priors and held split segments. The tool samples each item's top/side/front projected shape against the whole-airframe silhouette union and records whether a center shift alone can reduce exposure. It does not shrink dimensions or activate runtime components.</p>
    {_html_table(
      [
        "item",
        "type",
        "shape",
        "size_evidence",
        "outside_views",
        "outside_samples",
        "candidate_outside_samples",
        "candidate_shift_m",
        "triage_status",
        "recommended_action",
      ],
      correction_rows,
    )}
  </section>
"""
  ownership_split_section = ""
  if ownership_split_report is not None:
    ownership_rows = [
      [
        row["parent_component_name"],
        row["recommended_ownership_decision"],
        row["segment_count"],
        ",".join(row["candidate_runtime_component_names"]),
        ",".join(row["owner_region_ids"]),
        row["silhouette_exposure_segment_count"],
        row["parent_receiver_runtime_policy"],
        row["runtime_activation_status"],
      ]
      for row in ownership_split_report["rows"]
    ]
    ownership_split_section = f"""
  <section>
    <h2>Cross-Region Ownership Split Candidates</h2>
    <p class="note">Review-only R22 ownership decision packet for the two held cross-region receivers. Candidate payloads are parse-ready AABB fallback receiver records with preserved shape metadata; no split receiver is runtime active.</p>
    {_html_table(
      [
        "parent_component",
        "recommended_decision",
        "segments",
        "candidate_receivers",
        "owner_regions",
        "silhouette_exposure_segments",
        "parent_runtime_policy",
        "runtime_status",
      ],
      ownership_rows,
    )}
  </section>
"""
  runtime_activation_section = ""
  if runtime_activation_report is not None:
    activation_rows = [
      [
        row["candidate_component_name"],
        row["parent_component_name"],
        row["segment_role"],
        ",".join(row["owner_region_ids"]),
        row["geometry_primitive"],
        row["runtime_loader_contract_status"],
        row["runtime_activation_status"],
        row["behavior_test_status"],
        row["feature_flag"],
      ]
      for row in runtime_activation_report["rows"]
    ]
    runtime_activation_section = f"""
  <section>
    <h2>TG-P7 Runtime Activation Candidate</h2>
    <p class="note">TG-P7-R1 unit-database patch candidate for the eight R22 split receivers. The payload uses fields already parsed by the runtime unit loader, but it is not applied to the repository unit database and still requires behavior regression before activation.</p>
    <p class="note">parse-ready candidates: {runtime_activation_report["summary"]["runtime_schema_parse_ready_component_count"]}; patch additions: {runtime_activation_report["summary"]["unit_database_patch_component_count"]}; runtime active: {runtime_activation_report["summary"]["runtime_active_component_count"]}</p>
    {_html_table(
      [
        "candidate_component",
        "parent_component",
        "segment_role",
        "owner_regions",
        "primitive",
        "loader_contract",
        "runtime_status",
        "behavior_status",
        "feature_flag",
      ],
      activation_rows,
    )}
  </section>
"""
  runtime_behavior_section = ""
  if runtime_behavior_report is not None:
    behavior_rows = [
      [
        row["parent_component_name"],
        row["target_hitbox_index"],
        row["target_path"],
        row["base_hitbox_component_count"],
        row["patched_hitbox_component_count"],
        row["parent_absent_after_patch"],
        ",".join(row["split_component_names"]),
        row["split_component_present_count"],
        row["duplicate_component_name_count"],
        row["behavior_status"],
      ]
      for row in runtime_behavior_report["rows"]
    ]
    runtime_behavior_section = f"""
  <section>
    <h2>TG-P7 Runtime Behavior Regression Candidate</h2>
    <p class="note">TG-P7-R2 in-memory patch regression: parent receiver components are removed from their current hitbox component arrays and the eight split receiver candidates are appended to those same component arrays. The repository unit database is not modified.</p>
    <p class="note">base components: {runtime_behavior_report["summary"]["base_component_count"]}; projected components: {runtime_behavior_report["summary"]["projected_component_count"]}; retired parents: {runtime_behavior_report["summary"]["retired_parent_component_count"]}; split additions: {runtime_behavior_report["summary"]["split_component_added_count"]}; duplicate names: {runtime_behavior_report["summary"]["duplicate_component_name_count"]}; pass: {runtime_behavior_report["summary"]["behavior_regression_pass"]}</p>
    {_html_table(
      [
        "parent_component",
        "hitbox",
        "target_path",
        "base_hitbox_components",
        "patched_hitbox_components",
        "parent_absent_after_patch",
        "split_components",
        "split_present",
        "duplicates",
        "status",
      ],
      behavior_rows,
    )}
  </section>
"""
  training_proxy_section = ""
  if training_proxy_report is not None:
    proxy_rows = [
      [
        "default_database_component_count",
        training_proxy_report["summary"]["default_database_component_count"],
      ],
      [
        "proxy_database_component_count",
        training_proxy_report["summary"]["proxy_database_component_count"],
      ],
      [
        "split_receiver_component_count",
        training_proxy_report["summary"]["split_receiver_component_count"],
      ],
      [
        "proxy_database_materialized",
        training_proxy_report["summary"]["proxy_database_materialized"],
      ],
      [
        "database_path",
        training_proxy_report["runtime_database"]["proxy_database_path"],
      ],
    ]
    training_proxy_section = f"""
  <section>
    <h2>TG-P7 Training Proxy Database</h2>
    <p class="note">TG-P7-R3 materialized opt-in runtime database for initial training with the split-receiver proxy. The default repository database remains unchanged.</p>
    <p class="note">default components: {training_proxy_report["summary"]["default_database_component_count"]}; proxy components: {training_proxy_report["summary"]["proxy_database_component_count"]}; split receivers: {training_proxy_report["summary"]["split_receiver_component_count"]}</p>
    {_html_table(["field", "value"], proxy_rows)}
  </section>
"""
  shape_placement_section = ""
  if shape_placement_report is not None:
    shape_rows = [
      [
        row["item_id"],
        row["record_type"],
        row["current_shape"],
        row["candidate_shape_family"],
        row["candidate_evaluation_shape"],
        row["current_silhouette"]["outside_sample_count"],
        row["candidate_silhouette"]["outside_sample_count"],
        row["centerline_candidate_silhouette"]["outside_sample_count"],
        row["latest_candidate_silhouette"]["outside_sample_count"],
        row["outside_sample_reduction"],
        row["centerline_incremental_outside_sample_reduction"],
        row["latest_incremental_outside_sample_reduction"],
        row["candidate_center_shift_m"],
        row["centerline_candidate_shift_m"],
        row["latest_candidate_status"],
      ]
      for row in shape_placement_report["rows"]
    ]
    shape_placement_section = f"""
  <section>
    <h2>Subcomponent Shape Placement Candidates</h2>
    <p class="note">Review-only latest subcomponent candidates for the exposed items. Nominal public or declared dimensions are preserved; older current/shape/centerline layers are trace data only, and all candidates remain inactive at runtime.</p>
    <p class="note">latest resolved candidates: {shape_placement_report["summary"]["latest_candidate_resolves_exposure_count"]}; latest unresolved candidates: {shape_placement_report["summary"]["latest_candidate_unresolved_exposure_count"]}; latest outside samples: {shape_placement_report["summary"]["latest_candidate_total_outside_sample_count"]}</p>
    <p class="note"><a href="subcomponent_shape_placement_views/index.html">Open subcomponent shape placement views</a>.</p>
    {_html_table(
      [
        "item",
        "type",
        "current_shape",
        "candidate_family",
        "eval_shape",
        "current_outside",
        "shape_outside",
        "centerline_outside",
        "latest_outside",
        "shape_reduction",
        "centerline_incremental_reduction",
        "latest_incremental_reduction",
        "shape_shift_m",
        "centerline_shift_m",
        "latest_status",
      ],
      shape_rows,
    )}
  </section>
"""
  parent_child_layout_section = ""
  if parent_child_layout_report is not None:
    parent_child_rows = [
      [
        row["parent_semantic_component_id"],
        row["source_region_id"],
        row["geometry_primitive"],
        row["bound_receiver_count"],
        row["extra_receiver_slot_count"],
        row["primary_receiver_component_name"],
        ",".join(row["extra_receiver_component_names"]),
        ",".join(row["cross_region_held_receiver_names"]),
        row["cross_region_held_segment_overlay_count"],
        row["runtime_projection_status"],
      ]
      for row in parent_child_layout_report["rows"]
    ]
    parent_child_layout_section = f"""
  <section>
    <h2>Semantic Parent-Child Component Layout</h2>
    <p class="note">Primary visual review surface: `14` mesh-derived parent shell parts with all `26` current receiver priors overlaid inside their parent region; the `12` extra receiver slots are display overlays, not accepted runtime ownership.</p>
    <p class="note"><a href="semantic_parent_child_layout_views/index.html">Open 14 parent-child layout views</a>.</p>
    {_html_table(
      [
        "parent_component",
        "outer_region",
        "primitive",
        "receiver_overlays",
        "extra_slots",
        "primary_receiver",
        "extra_receivers",
        "held_receivers",
        "external_held_segments",
        "runtime_status",
      ],
      parent_child_rows,
    )}
  </section>
"""
  fine_proxy_section = ""
  if fine_proxy is not None:
    fine_proxy_rows = [
      [
        row["point_id"],
        row["nearest_source_aabb_region_id"],
        row["nearest_source_aabb_distance_m"],
        row["nearest_fine_proxy_region_id"],
        row["nearest_fine_proxy_kind"],
        row["nearest_fine_proxy_distance_m"],
        row["fine_minus_source_distance_delta_m"],
      ]
      for row in fine_proxy["review_point_distance_deltas"]
    ]
    fine_proxy_section = f"""
  <section>
    <h2>Fine Geometry Proxy Overlay</h2>
    <p class="note">TG-P6 review-only proxy candidates. Dashed rectangles show source AABB regions, dotted rectangles show support bounds, and solid polygons show mesh-derived silhouettes from filtered audit-glTF vertices.</p>
    <p class="note"><a href="fine_proxy_review_dashboard.html">Open the per-region human review dashboard</a>.</p>
    <p class="note"><a href="human_review_triage.html">Open the visual human review triage</a>.</p>
    <p class="note"><a href="component_review_views/index.html">Open isolated component review views</a>.</p>
    <p class="note"><a href="semantic_damage_geometry_views/index.html">Open isolated semantic damage geometry views</a>.</p>
    <p class="note"><a href="semantic_parent_child_layout_views/index.html">Open 14 parent-child component layout views</a>.</p>
    <div class="views">
      <img src="fine_proxy_top.svg" alt="Top view fine proxy overlay">
      <img src="fine_proxy_side.svg" alt="Side view fine proxy overlay">
      <img src="fine_proxy_front.svg" alt="Front view fine proxy overlay">
    </div>
  </section>
  <section>
    <h2>Fine Proxy Distance Deltas</h2>
    {_html_table(
      [
        "point",
        "source_region",
        "source_dist_m",
        "fine_region",
        "fine_kind",
        "fine_dist_m",
        "delta_m",
      ],
      fine_proxy_rows,
    )}
  </section>
"""
  body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>F-16 Target Geometry Review Packet</title>
  <style>
    body {{
      margin: 0;
      background: #f6f7f9;
      color: #202124;
      font-family: Arial, sans-serif;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      font-weight: 700;
    }}
    section {{
      margin: 0 0 24px;
      padding: 18px;
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 6px;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 8px 16px;
      font-family: monospace;
      font-size: 13px;
    }}
    .views {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }}
    img {{
      width: 100%;
      height: auto;
      border: 1px solid #cdd3dd;
      background: #ffffff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border: 1px solid #d8dde6;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef2f7;
    }}
    .note {{
      color: #4b5563;
      font-size: 13px;
    }}
  </style>
</head>
<body>
<main>
  <section>
    <h1>F-16 Target Geometry Review Packet</h1>
    <p class="note">Review-only geometry. This packet is not a runtime collision mesh, not a real F-16 engineering model, and not a real-weapon lethality claim.</p>
    <div class="meta">
      <div>generated_on: {html.escape(mapping["generated_on"])}</div>
      <div>source_uid: {html.escape(manifest["source"]["uid"])}</div>
      <div>outer_regions: {len(mapping["outer_regions"])}</div>
      <div>components: {component_report["summary"]["component_count"]}</div>
      <div>review_points: {diagnostics["summary"]["review_point_count"]}</div>
      <div>needs_review_components: {component_report["summary"]["needs_review_count"]}</div>
    </div>
  </section>
  <section>
    <h2>Three-View Overlay</h2>
    <div class="views">
      <img src="top.svg" alt="Top view geometry overlay">
      <img src="side.svg" alt="Side view geometry overlay">
      <img src="front.svg" alt="Front view geometry overlay">
    </div>
  </section>
{fine_proxy_section}
{semantic_damage_geometry_section}
{internal_component_prior_section}
{held_segment_section}
{airframe_constraint_section}
{ownership_split_section}
{runtime_activation_section}
{runtime_behavior_section}
{training_proxy_section}
{shape_placement_section}
{parent_child_layout_section}
{surface_component_section}
  <section>
    <h2>Review Point Diagnostics</h2>
    {_html_table(
      [
        "index",
        "point",
        "local_m",
        "outer_region",
        "outer_dist_m",
        "nearest_component",
        "component_dist_m",
        "candidate_count",
        "interpretation",
      ],
      diagnostic_rows,
    )}
  </section>
  <section>
    <h2>Component Binding Summary</h2>
    {_html_table(
      ["component", "system", "bound_region", "status", "anomalies"],
      component_rows,
    )}
  </section>
</main>
</body>
</html>
"""
  html_path.write_text(
    "\n".join(line.rstrip() for line in body.splitlines()) + "\n",
    encoding="utf-8",
  )
  return html_path


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


def main(argv: list[str] | None = None) -> int:
  args = _parse_args(sys.argv[1:] if argv is None else argv)
  manifest = build_airframe_geometry_manifest(
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

  output_path = write_manifest(manifest, args.out)
  mapping = build_geometry_mapping_candidate(manifest)
  mapping_path = write_mapping_candidate(mapping, args.out)
  aircraft = _load_json(args.aircraft)
  component_report = build_component_binding_report(aircraft, mapping)
  component_json_path, component_csv_path = write_component_binding_report(
    component_report, args.out
  )
  diagnostics = build_review_point_diagnostics(mapping, component_report)
  diagnostics_json_path, diagnostics_csv_path = write_review_point_diagnostics(
    diagnostics, args.out
  )
  fine_proxy = build_fine_geometry_proxy_candidate(
    mapping,
    diagnostics,
    manifest=manifest,
    audit_scene_path=args.asset,
  )
  fine_proxy_path = write_fine_geometry_proxy_candidate(fine_proxy, args.out)
  surface_report = build_surface_component_candidate_report(
    mapping,
    fine_proxy,
    component_report,
  )
  surface_json_path, surface_csv_path = write_surface_component_candidate_report(
    surface_report,
    args.out,
  )
  semantic_report = build_semantic_damage_geometry_candidate(
    mapping,
    fine_proxy,
    surface_report,
  )
  semantic_json_path, semantic_csv_path = write_semantic_damage_geometry_candidate(
    semantic_report,
    args.out,
  )
  internal_prior_report = build_internal_component_prior_candidate(
    mapping,
    fine_proxy,
    component_report,
    surface_report,
  )
  internal_prior_json_path, internal_prior_csv_path = (
    write_internal_component_prior_candidate(
      internal_prior_report,
      args.out,
    )
  )
  held_segment_report = build_cross_region_held_component_segments_report(
    mapping,
    fine_proxy,
    internal_prior_report,
  )
  held_segment_json_path, held_segment_csv_path = (
    write_cross_region_held_component_segments_report(
      held_segment_report,
      args.out,
    )
  )
  airframe_constraint_report = build_airframe_constraint_correction_candidate_report(
    mapping,
    fine_proxy,
    internal_prior_report,
    held_segment_report,
  )
  airframe_constraint_json_path, airframe_constraint_csv_path = (
    write_airframe_constraint_correction_candidate_report(
      airframe_constraint_report,
      args.out,
    )
  )
  ownership_split_report = build_cross_region_ownership_split_candidate_report(
    mapping,
    internal_prior_report,
    held_segment_report,
    airframe_constraint_report,
  )
  ownership_split_json_path, ownership_split_csv_path = (
    write_cross_region_ownership_split_candidate_report(
      ownership_split_report,
      args.out,
    )
  )
  runtime_activation_report = (
    build_target_geometry_runtime_activation_candidate_report(
      mapping,
      ownership_split_report,
      aircraft=aircraft,
    )
  )
  runtime_activation_json_path, runtime_activation_csv_path = (
    write_target_geometry_runtime_activation_candidate_report(
      runtime_activation_report,
      args.out,
    )
  )
  runtime_behavior_report = (
    build_target_geometry_runtime_behavior_regression_report(
      aircraft,
      runtime_activation_report,
    )
  )
  runtime_behavior_json_path, runtime_behavior_csv_path = (
    write_target_geometry_runtime_behavior_regression_report(
      runtime_behavior_report,
      args.out,
    )
  )
  training_proxy_aircraft, _training_proxy_operations = (
    build_target_geometry_training_proxy_unit_candidate(
      aircraft,
      runtime_activation_report,
    )
  )
  training_proxy_report = build_target_geometry_training_proxy_database_report(
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
  ) = write_target_geometry_training_proxy_database_report(
    training_proxy_report,
    training_proxy_aircraft,
    args.out,
  )
  shape_placement_report = build_subcomponent_shape_placement_candidate_report(
    mapping,
    fine_proxy,
    airframe_constraint_report,
  )
  shape_placement_json_path, shape_placement_csv_path = (
    write_subcomponent_shape_placement_candidate_report(
      shape_placement_report,
      args.out,
    )
  )
  parent_child_layout_report = build_semantic_parent_child_layout_candidate(
    mapping,
    semantic_report,
    internal_prior_report,
    held_segment_report,
  )
  parent_child_layout_json_path, parent_child_layout_csv_path = (
    write_semantic_parent_child_layout_candidate(
      parent_child_layout_report,
      args.out,
    )
  )
  svg_paths = write_svg_views(
    mapping,
    args.out,
    component_report=component_report,
    diagnostics=diagnostics,
  )
  fine_proxy_svg_paths = write_fine_proxy_svg_views(fine_proxy, args.out)
  fine_proxy_dashboard_path = write_fine_proxy_review_dashboard(
    fine_proxy,
    component_report,
    args.out,
    surface_report=surface_report,
  )
  human_review_triage_path = write_human_review_triage_dashboard(
    fine_proxy=fine_proxy,
    component_report=component_report,
    diagnostics=diagnostics,
    surface_report=surface_report,
    output_dir=args.out,
  )
  isolated_review_index_path, isolated_review_manifest_path = (
    write_isolated_component_review_views(
      fine_proxy=fine_proxy,
      component_report=component_report,
      diagnostics=diagnostics,
      surface_report=surface_report,
      output_dir=args.out,
    )
  )
  semantic_review_index_path, semantic_review_manifest_path = (
    write_semantic_damage_geometry_review_views(
      semantic_report=semantic_report,
      fine_proxy=fine_proxy,
      component_report=component_report,
      output_dir=args.out,
    )
  )
  internal_prior_review_index_path, internal_prior_review_manifest_path = (
    write_internal_component_prior_review_views(
      prior_report=internal_prior_report,
      fine_proxy=fine_proxy,
      component_report=component_report,
      output_dir=args.out,
    )
  )
  (
    parent_child_layout_review_index_path,
    parent_child_layout_review_manifest_path,
  ) = write_semantic_parent_child_layout_review_views(
    layout_report=parent_child_layout_report,
    fine_proxy=fine_proxy,
    output_dir=args.out,
  )
  (
    shape_placement_review_index_path,
    shape_placement_review_manifest_path,
  ) = write_subcomponent_shape_placement_review_views(
    shape_report=shape_placement_report,
    fine_proxy=fine_proxy,
    output_dir=args.out,
  )
  scene_path = write_review_packet(
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
        "output": _display_path(output_path, REPO_ROOT),
        "mapping_output": _display_path(mapping_path, REPO_ROOT),
        "component_binding_json": _display_path(component_json_path, REPO_ROOT),
        "component_binding_csv": _display_path(component_csv_path, REPO_ROOT),
        "review_point_diagnostics_json": _display_path(
          diagnostics_json_path, REPO_ROOT
        ),
        "review_point_diagnostics_csv": _display_path(
          diagnostics_csv_path, REPO_ROOT
        ),
        "fine_proxy_json": _display_path(fine_proxy_path, REPO_ROOT),
        "surface_component_json": _display_path(surface_json_path, REPO_ROOT),
        "surface_component_csv": _display_path(surface_csv_path, REPO_ROOT),
        "semantic_damage_geometry_json": _display_path(
          semantic_json_path,
          REPO_ROOT,
        ),
        "semantic_damage_geometry_csv": _display_path(
          semantic_csv_path,
          REPO_ROOT,
        ),
        "internal_component_prior_json": _display_path(
          internal_prior_json_path,
          REPO_ROOT,
        ),
        "internal_component_prior_csv": _display_path(
          internal_prior_csv_path,
          REPO_ROOT,
        ),
        "cross_region_held_segments_json": _display_path(
          held_segment_json_path,
          REPO_ROOT,
        ),
        "cross_region_held_segments_csv": _display_path(
          held_segment_csv_path,
          REPO_ROOT,
        ),
        "airframe_constraint_correction_json": _display_path(
          airframe_constraint_json_path,
          REPO_ROOT,
        ),
        "airframe_constraint_correction_csv": _display_path(
          airframe_constraint_csv_path,
          REPO_ROOT,
        ),
        "cross_region_ownership_split_json": _display_path(
          ownership_split_json_path,
          REPO_ROOT,
        ),
        "cross_region_ownership_split_csv": _display_path(
          ownership_split_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_activation_json": _display_path(
          runtime_activation_json_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_activation_csv": _display_path(
          runtime_activation_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_behavior_json": _display_path(
          runtime_behavior_json_path,
          REPO_ROOT,
        ),
        "target_geometry_runtime_behavior_csv": _display_path(
          runtime_behavior_csv_path,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_json": _display_path(
          training_proxy_json_path,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_database": _display_path(
          training_proxy_database_dir,
          REPO_ROOT,
        ),
        "target_geometry_training_proxy_f16c_unit": _display_path(
          training_proxy_unit_path,
          REPO_ROOT,
        ),
        "subcomponent_shape_placement_json": _display_path(
          shape_placement_json_path,
          REPO_ROOT,
        ),
        "subcomponent_shape_placement_csv": _display_path(
          shape_placement_csv_path,
          REPO_ROOT,
        ),
        "semantic_parent_child_layout_json": _display_path(
          parent_child_layout_json_path,
          REPO_ROOT,
        ),
        "semantic_parent_child_layout_csv": _display_path(
          parent_child_layout_csv_path,
          REPO_ROOT,
        ),
        "scene_html": _display_path(scene_path, REPO_ROOT),
        "svg_outputs": [_display_path(path, REPO_ROOT) for path in svg_paths],
        "fine_proxy_svg_outputs": [
          _display_path(path, REPO_ROOT) for path in fine_proxy_svg_paths
        ],
        "fine_proxy_review_dashboard": _display_path(
          fine_proxy_dashboard_path, REPO_ROOT
        ),
        "human_review_triage": _display_path(human_review_triage_path, REPO_ROOT),
        "isolated_component_review_index": _display_path(
          isolated_review_index_path, REPO_ROOT
        ),
        "isolated_component_review_manifest": _display_path(
          isolated_review_manifest_path, REPO_ROOT
        ),
        "semantic_damage_geometry_review_index": _display_path(
          semantic_review_index_path, REPO_ROOT
        ),
        "semantic_damage_geometry_review_manifest": _display_path(
          semantic_review_manifest_path, REPO_ROOT
        ),
        "internal_component_prior_review_index": _display_path(
          internal_prior_review_index_path, REPO_ROOT
        ),
        "internal_component_prior_review_manifest": _display_path(
          internal_prior_review_manifest_path, REPO_ROOT
        ),
        "semantic_parent_child_layout_review_index": _display_path(
          parent_child_layout_review_index_path, REPO_ROOT
        ),
        "semantic_parent_child_layout_review_manifest": _display_path(
          parent_child_layout_review_manifest_path, REPO_ROOT
        ),
        "subcomponent_shape_placement_review_index": _display_path(
          shape_placement_review_index_path, REPO_ROOT
        ),
        "subcomponent_shape_placement_review_manifest": _display_path(
          shape_placement_review_manifest_path, REPO_ROOT
        ),
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
