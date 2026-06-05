from __future__ import annotations

from examples.viz.runtime.environment_overlays import (
    ENVIRONMENT_OVERLAY_CONTRACT_VERSION,
    build_environment_overlay_payload,
)


def test_g0_viz_environment_zones_become_surface_overlay_layer() -> None:
    payload = build_environment_overlay_payload(
        {
            "environment": {
                "zones": [
                    {
                        "name": "VillageHardstand",
                        "x": 250.0,
                        "y": -125.0,
                        "width": 80.0,
                        "length": 140.0,
                        "heading": 15.0,
                        "surface": "Concrete",
                    }
                ]
            }
        }
    )

    assert payload["contract_version"] == ENVIRONMENT_OVERLAY_CONTRACT_VERSION
    assert payload["evidence"] == {
        "source": "scenario.environment",
        "no_runtime_setup_application": True,
        "no_runtime_consumer_release": True,
        "no_movement_release": True,
        "no_los_cover_release": True,
        "no_held_capability_release": True,
    }
    assert payload["skipped_products"] == []

    assert len(payload["layers"]) == 1
    layer = payload["layers"][0]
    assert layer["layer_id"] == "scenario_environment_zones"
    assert layer["overlay_kind"] == "surface_zone"
    assert layer["evidence"]["no_runtime_setup_application"] is True
    assert layer["evidence"]["no_runtime_consumer_release"] is True

    entry = layer["entries"][0]
    assert entry == {
        "overlay_id": "environment.zone.0",
        "overlay_kind": "surface_zone",
        "label": "VillageHardstand",
        "geometry": {
            "geometry_type": "rect",
            "x": 250.0,
            "y": -125.0,
            "width": 80.0,
            "length": 140.0,
            "heading": 15.0,
        },
        "attributes": {
            "surface": "Concrete",
            "source": "environment.zones",
            "zone_index": 0,
        },
        "evidence": {
            "runtime_consumer_release": False,
            "no_runtime_setup_application": True,
            "no_held_capability_release": True,
        },
    }


def test_g0_viz_accepts_metadata_only_derived_products_and_skips_held_products() -> None:
    payload = build_environment_overlay_payload(
        {
            "environment": {
                "environment_substrate": {
                    "derived_product_bundle": {
                        "products": [
                            {
                                "product_kind": "surface_zone_index",
                                "entries": [
                                    {
                                        "source_object_id": "envobj:test-hardstand",
                                        "zone_name": "catalog:port_hardstand",
                                        "surface": "Concrete",
                                        "rect": {
                                            "x": 250.0,
                                            "y": -125.0,
                                            "width": 80.0,
                                            "length": 140.0,
                                            "heading": 15.0,
                                        },
                                    }
                                ],
                            },
                            {
                                "product_kind": "occlusion_candidate_index",
                                "entries": [
                                    {
                                        "source_object_id": "envobj:test-village-house",
                                        "catalog_ref": "catalog:village_house_light",
                                        "component_id": "component:test-house-structure",
                                        "component_family": "structure",
                                        "bounds_kind": "aabb",
                                        "bounds": {
                                            "min_x": 300.0,
                                            "min_y": 300.0,
                                            "max_x": 312.0,
                                            "max_y": 310.0,
                                        },
                                        "layer_membership": ["built_structure"],
                                        "height_m": 5.5,
                                    }
                                ],
                            },
                            {
                                "product_kind": "passability_mask",
                                "entries": [{"cell": [0, 0], "passable": True}],
                            },
                        ]
                    }
                }
            }
        }
    )

    layers = {layer["layer_id"]: layer for layer in payload["layers"]}
    assert set(layers) == {"surface_zone_index", "occlusion_candidate_index"}
    assert payload["skipped_products"] == [
        {
            "product_kind": "passability_mask",
            "reason": "not_released_for_g0_viz_overlay",
        }
    ]

    surface_entry = layers["surface_zone_index"]["entries"][0]
    assert surface_entry["attributes"]["source"] == "g0_m.surface_zone_index"
    assert surface_entry["evidence"]["runtime_consumer_release"] is False
    assert surface_entry["evidence"]["no_runtime_consumer_release"] is True

    candidate_layer = layers["occlusion_candidate_index"]
    assert candidate_layer["evidence"]["no_los_runtime_release"] is True
    assert candidate_layer["evidence"]["no_cover_runtime_release"] is True
    candidate_entry = candidate_layer["entries"][0]
    assert candidate_entry["overlay_kind"] == "occlusion_candidate"
    assert candidate_entry["geometry"] == {
        "geometry_type": "aabb",
        "min_x": 300.0,
        "min_y": 300.0,
        "max_x": 312.0,
        "max_y": 310.0,
    }
    assert candidate_entry["attributes"]["height_m"] == 5.5
    assert candidate_entry["evidence"]["no_los_runtime_release"] is True
    assert candidate_entry["evidence"]["no_cover_runtime_release"] is True
