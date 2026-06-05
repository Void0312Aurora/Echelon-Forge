from __future__ import annotations

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    EnvironmentDerivedProductRequest,
    EnvironmentManifest,
    build_deterministic_environment_fixture,
    build_environment_derived_products,
    canonical_environment_bytes,
    validate_environment_manifest,
)


def _fixture() -> EnvironmentManifest:
    manifest = build_deterministic_environment_fixture()
    assert validate_environment_manifest(manifest).valid
    return manifest


def test_g0_m_builds_deterministic_metadata_only_derived_product_bundle() -> None:
    manifest = _fixture()
    request = EnvironmentDerivedProductRequest(
        request_id="g0-m-fixture",
        product_kinds=("surface_zone_index", "occlusion_candidate_index"),
        source_projection_profile_id="terrain-rect-surface-v1",
    )

    result_a = build_environment_derived_products(manifest, request)
    result_b = build_environment_derived_products(manifest, request)

    assert result_a.valid
    assert not result_a.fail_closed
    assert result_a.bundle is not None
    assert canonical_environment_bytes(result_a.to_metadata()) == canonical_environment_bytes(
        result_b.to_metadata()
    )

    bundle = result_a.bundle.to_metadata()
    assert bundle["no_runtime_consumer_release"] is True
    assert bundle["no_held_capability_release"] is True
    products = {product["product_kind"]: product for product in bundle["products"]}
    assert set(products) == {"surface_zone_index", "occlusion_candidate_index"}

    surface_entries = products["surface_zone_index"]["entries"]
    assert surface_entries == [
        {
            "index": 0,
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
            "runtime_consumer_release": False,
        }
    ]

    occlusion_entries = products["occlusion_candidate_index"]["entries"]
    assert occlusion_entries == [
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
            "runtime_consumer_release": False,
            "height_m": 5.5,
        }
    ]
    assert products["occlusion_candidate_index"]["evidence"]["no_los_runtime_release"] is True
    assert products["occlusion_candidate_index"]["evidence"]["no_cover_runtime_release"] is True


def test_g0_m_rejects_held_derived_product_kinds() -> None:
    result = build_environment_derived_products(
        _fixture(),
        EnvironmentDerivedProductRequest(
            request_id="g0-m-held-product",
            product_kinds=("passability_mask",),
        ),
    )

    assert not result.valid
    assert result.fail_closed
    assert result.bundle is None
    assert result.rejection_reason == "environment_substrate_derived_product_held_capability"


def test_g0_m_rejects_held_capability_claims() -> None:
    result = build_environment_derived_products(
        _fixture(),
        EnvironmentDerivedProductRequest(
            request_id="g0-m-held-claim",
            product_kinds=("occlusion_candidate_index",),
            capability_claims=("line_of_sight",),
        ),
    )

    assert not result.valid
    assert result.fail_closed
    assert result.bundle is None
    assert result.rejection_reason == "environment_substrate_derived_product_held_capability"


def test_g0_m_surface_zone_index_requires_projection_profile() -> None:
    result = build_environment_derived_products(
        _fixture(),
        EnvironmentDerivedProductRequest(
            request_id="g0-m-missing-profile",
            product_kinds=("surface_zone_index",),
        ),
    )

    assert not result.valid
    assert result.fail_closed
    assert result.bundle is None
    assert (
        result.rejection_reason
        == "environment_substrate_derived_projection_profile_required"
    )
