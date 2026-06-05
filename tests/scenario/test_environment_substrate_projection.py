from __future__ import annotations

from copy import deepcopy

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    EnvironmentManifest,
    build_deterministic_environment_fixture,
    project_manifest_to_compatibility_setup,
)


def _manifest_from_metadata(metadata: dict) -> EnvironmentManifest:
    return EnvironmentManifest(**deepcopy(metadata))


def test_g0_j_projection_contract_emits_explicit_world_zone_evidence() -> None:
    fixture = build_deterministic_environment_fixture()

    projection = project_manifest_to_compatibility_setup(
        fixture,
        profile_id="terrain-rect-surface-v1",
    )

    assert projection.valid
    assert not projection.fail_closed
    assert projection.rejection_reason == ""
    assert len(projection.zones) == 1
    assert projection.zones[0].source_object_id == "envobj:test-hardstand"
    assert projection.zones[0].surface == "Concrete"
    assert projection.evidence is not None
    assert projection.evidence.no_held_capability_release
    assert projection.evidence.source_object_ids == ("envobj:test-hardstand",)
    assert projection.evidence.dropped_attributes == ()


def test_g0_j_projection_rejects_rich_components_without_dropped_attribute_permission() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["objects"][0]["components"].append(
        {
            "component_id": "component:test-hardstand-road-network",
            "family": "network",
            "schema_version": "1",
            "attributes": {
                "width_m": 6.0,
                "connectivity": "local_track",
                "surface_class": "concrete",
            },
        }
    )
    manifest = _manifest_from_metadata(metadata)

    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not projection.valid
    assert projection.fail_closed
    assert (
        projection.rejection_reason
        == "environment_substrate_dropped_attribute_without_permission"
    )
    assert "network" in projection.errors[0]


def test_g0_j_projection_rejects_misspelled_surface_type_instead_of_defaulting() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["objects"][0]["components"][0]["attributes"] = {"surface_type": "Concrete"}
    manifest = _manifest_from_metadata(metadata)

    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not projection.valid
    assert projection.fail_closed
    assert (
        projection.rejection_reason
        == "environment_substrate_missing_required_component_attribute"
    )


def test_g0_j_projection_rejects_non_rect_geometry_for_world_zone_target() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["objects"][0]["geometry"] = {
        "geometry_type": "polygon",
        "coordinates": {
            "points": [
                [0.0, 0.0],
                [100.0, 0.0],
                [100.0, 100.0],
                [0.0, 100.0],
            ]
        },
    }
    manifest = _manifest_from_metadata(metadata)

    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not projection.valid
    assert projection.fail_closed
    assert projection.rejection_reason == "environment_substrate_unsupported_geometry"


def test_g0_j_projection_rejects_unreleased_runtime_targets() -> None:
    metadata = build_deterministic_environment_fixture().to_metadata()
    metadata["projection_profiles"][0]["target"] = "weather_runtime"
    manifest = _manifest_from_metadata(metadata)

    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not projection.valid
    assert projection.fail_closed
    assert projection.rejection_reason == "environment_substrate_unsupported_target_field"
