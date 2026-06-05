from __future__ import annotations

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    EnvironmentComponent,
    EnvironmentManifest,
    build_deterministic_environment_fixture,
    build_world_zone_projection_setup_payload,
    canonical_environment_bytes,
    validate_environment_manifest,
)


def _fixture() -> EnvironmentManifest:
    manifest = build_deterministic_environment_fixture()
    assert validate_environment_manifest(manifest).valid
    return manifest


def test_g0_l_world_zone_projection_setup_payload_is_deterministic_and_inert() -> None:
    manifest = _fixture()

    result_a = build_world_zone_projection_setup_payload(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )
    result_b = build_world_zone_projection_setup_payload(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert result_a.valid
    assert not result_a.fail_closed
    assert result_a.payload is not None
    assert canonical_environment_bytes(result_a.to_metadata()) == canonical_environment_bytes(
        result_b.to_metadata()
    )
    payload = result_a.payload.to_metadata()
    assert payload["target"] == "world_zone_definition"
    assert payload["no_held_capability_release"] is True
    assert payload["zones"] == [
        {
            "name": "catalog:port_hardstand",
            "x": 250.0,
            "y": -125.0,
            "width": 80.0,
            "length": 140.0,
            "heading": 15.0,
            "surface": "Concrete",
        }
    ]
    assert payload["zone_evidence"][0]["source_manifest_id"] == manifest.manifest_id
    assert payload["zone_evidence"][0]["source_object_id"] == "envobj:test-hardstand"
    assert payload["zone_evidence"][0]["catalog_ref"] == "catalog:port_hardstand"
    assert payload["zone_evidence"][0]["component_ids"] == [
        "component:test-hardstand-surface"
    ]
    assert "world_index" not in payload["zones"][0]


def test_g0_l_projection_setup_rejects_unknown_profile_before_payload_creation() -> None:
    result = build_world_zone_projection_setup_payload(
        _fixture(),
        profile_id="terrain-zone-missing",
    )

    assert not result.valid
    assert result.fail_closed
    assert result.payload is None
    assert result.rejection_reason == "environment_substrate_unknown_projection_profile"


def test_g0_l_projection_setup_rejects_invalid_runtime_surface_code() -> None:
    metadata = _fixture().to_metadata()
    metadata["projection_profiles"][0]["surface_code_mapping"]["Concrete"] = "Mud"
    manifest = EnvironmentManifest(**metadata)

    result = build_world_zone_projection_setup_payload(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not result.valid
    assert result.fail_closed
    assert result.payload is None
    assert (
        result.rejection_reason
        == "environment_substrate_projection_invalid_surface_code"
    )


def test_g0_l_projection_setup_rejects_dropped_rich_attributes_even_when_recorded() -> None:
    metadata = _fixture().to_metadata()
    metadata["projection_profiles"][0]["dropped_attribute_policy"] = "record"
    metadata["objects"][0]["components"].append(
        EnvironmentComponent(
            component_id="component:test-hardstand-network",
            family="network",
            attributes={
                "width_m": 5.0,
                "connectivity": "local",
                "surface_class": "hardstand",
            },
        ).to_metadata()
    )
    manifest = EnvironmentManifest(**metadata)

    result = build_world_zone_projection_setup_payload(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not result.valid
    assert result.fail_closed
    assert result.payload is None
    assert (
        result.rejection_reason
        == "environment_substrate_projection_derived_product_forbidden"
    )


def test_g0_l_projection_setup_rejects_held_runtime_claims_through_manifest_validation() -> None:
    metadata = _fixture().to_metadata()
    metadata["capability_claims"] = ["movement"]
    manifest = EnvironmentManifest(**metadata)

    result = build_world_zone_projection_setup_payload(
        manifest,
        profile_id="terrain-rect-surface-v1",
    )

    assert not result.valid
    assert result.fail_closed
    assert result.payload is None
    assert result.rejection_reason == "environment_substrate_held_capability_claim"
