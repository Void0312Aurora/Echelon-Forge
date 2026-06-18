#!/usr/bin/env python3
"""Constants and review rules for airframe geometry packet generation."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
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
# Whole-airframe contour containment tolerance. A receiver sample point is
# treated as "inside the airframe contour" when it is inside the projected mesh
# polygon or within this distance of a contour edge. This is an engineering
# review margin (mesh / proxy quantization noise), not a physical clearance.
SILHOUETTE_CONTAINMENT_TOLERANCE_M = 0.05
# Per-view alpha for the whole-airframe alpha-shape, as a fraction of the
# longer projected axis span. alpha = 1 / (span * fraction). Smaller fraction
# => smaller alpha radius => tighter (more concave) contour.
WHOLE_AIRFRAME_ALPHA_AXIS_FRACTION = 0.35
WHOLE_AIRFRAME_CONTOUR_SCHEMA_VERSION = (
  "a2.target_geometry_whole_airframe_contour_containment.v1"
)
RETIRED_CURRENT_PACKET_VISUAL_DIRS = (
  "component_review_views",
  "semantic_damage_geometry_views",
  "internal_component_prior_views",
  "semantic_parent_child_layout_views",
  "subcomponent_shape_placement_views",
)
RETIRED_CURRENT_PACKET_VISUAL_FILES = (
  "top.svg",
  "side.svg",
  "front.svg",
  "fine_proxy_top.svg",
  "fine_proxy_side.svg",
  "fine_proxy_front.svg",
  "fine_proxy_review_dashboard.html",
  "human_review_triage.html",
)
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
    "center_m": [3.787559, 0.0, -0.67538],
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
      "R21 promotes a slightly lower canopy/forward-fuselage crew-envelope "
      "placement because it preserves the nominal crew envelope and clears "
      "the projected side-view silhouette exposure."
    ),
  },
  "inertial_navigation_unit": {
    "shape": "ellipsoid",
    "component_role": "small_avionics_receiver",
    "dimensions_m": [_inch(9.8), _inch(7.0), _inch(7.0)],
    "center_m": [2.6, 0.0, -0.1],
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
      "the R17 rounded-LRU ellipsoid candidate and fixes the avionics LRU on "
      "a lower forward-fuselage shelf because it preserves nominal dimensions "
      "and removes projected side-view silhouette exposure."
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
    "center_m": [3.39, 0.0, -0.64],
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
    "center_m": [-3.693053, 0.0, -0.904381],
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
    "rationale": "engine core uses public F110-GE-129 engine length and maximum diameter; R21 promotes the rounded lower centerline capsule candidate at the aft-fuselage engine shelf, while ownership remains cross-region held.",
  },
  "afterburner_nozzle": {
    "shape": "frustum",
    "axis": "x",
    "component_role": "nozzle_receiver",
    "dimensions_m": [0.75, _inch(46.5), _inch(46.5)],
    "negative_axis_radius_m": 0.45,
    "positive_axis_radius_m": _inch(46.5) * 0.5,
    "center_m": [-5.75, 0.0, -0.75],
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
    "rationale": "nozzle diameter follows public F110 maximum diameter; nozzle length remains a mesh-region estimate; R22 replaces the ellipsoid with an axis-aligned tapered frustum proxy so the aft nozzle is not modeled as a closed oval volume.",
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
    "shape": "thin_prism",
    "component_role": "wing_fuel_cell_receiver",
    "dimensions_m": [2.0, 2.2, 0.15],
    "center_m": [-2.075, -1.685, -0.985],
    "footprint_points_m": [
      [-3.0, -2.55],
      [-2.95, -1.05],
      [-1.25, -0.82],
      [-1.15, -1.95],
    ],
    "size_basis": "f16_internal_fuel_capacity_partition_estimate",
    "size_evidence_level": "public_total_capacity_partition_estimate",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "wing fuel cell size is capacity-informed; exact F-16 wing-cell boundaries are not public in the packet source set; R22 replaces the ellipsoid with a swept thin-prism footprint that follows the wing planform and stays inside the projected top contour.",
  },
  "right_wing_fuel_cell": {
    "shape": "thin_prism",
    "component_role": "wing_fuel_cell_receiver",
    "dimensions_m": [2.0, 2.2, 0.15],
    "center_m": [-2.075, 1.685, -0.985],
    "footprint_points_m": [
      [-3.0, 2.55],
      [-2.95, 1.05],
      [-1.25, 0.82],
      [-1.15, 1.95],
    ],
    "size_basis": "f16_internal_fuel_capacity_partition_estimate",
    "size_evidence_level": "public_total_capacity_partition_estimate",
    "size_source_urls": [
      "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/104505/f-16-fighting-falcon/",
    ],
    "constraint_bounds_source": "source_region_bounds",
    "allow_constraint_shrink": False,
    "shape_promotion_status": R21_LATEST_PROMOTION_STATUS,
    "rationale": "wing fuel cell size is capacity-informed; exact F-16 wing-cell boundaries are not public in the packet source set; R22 replaces the ellipsoid with a swept thin-prism footprint that follows the wing planform and stays inside the projected top contour.",
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
    "shape": "thin_prism",
    "axis": "",
    "component_role": "cross_region_structural_receiver",
    "dimensions_m": [0.5, 5.8, 0.18],
    "center_m": [-1.2, 0.0, -0.985043],
    "footprint_points_m": [
      [-1.45, -2.9],
      [-0.95, -2.9],
      [-0.95, 2.9],
      [-1.45, 2.9],
    ],
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
    "rationale": "wing spar center uses the existing cross-region receiver semantics but R22 replaces the single capsule with a symmetric thin-prism carry-through / inner-wing strip; this avoids the prior one-sided swept-strip artifact while remaining review-only pending true spar/wing-box data.",
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
    "center_offset_m": [0.6, 0.0, -0.2],
    "source_basis": "R19_local_centerline_search_radius_1m_step_0p1m",
    "placement_policy": (
      "preserve_nozzle_dimensions_and_test_aft_lower_centerline_candidate"
    ),
    "rationale": (
      "local silhouette search clears exposure with a larger aft/down "
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




__all__ = tuple(name for name in globals() if name.isupper())
