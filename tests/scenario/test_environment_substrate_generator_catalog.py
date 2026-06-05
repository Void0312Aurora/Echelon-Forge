from __future__ import annotations

from dataclasses import replace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    EnvironmentBranchMembership,
    EnvironmentCatalogDescriptor,
    EnvironmentComponent,
    EnvironmentGeneratorEvidenceRef,
    EnvironmentGeneratorRequest,
    EnvironmentRegionExtent,
    EnvironmentTileScheme,
    build_deterministic_generated_environment_manifest,
    canonical_environment_bytes,
    default_environment_catalog_descriptors,
    derive_environment_seed,
    validate_environment_catalog_admission,
    validate_environment_catalog_descriptors,
    validate_environment_generator_request,
    validate_environment_manifest,
)


def _request(seed: int = 20260606) -> EnvironmentGeneratorRequest:
    return EnvironmentGeneratorRequest(
        request_id="envgen:test-village-area",
        generator_id="deterministic_fixture_generator",
        generator_version="g0-k.20260606",
        deterministic_seed=seed,
        coordinate_frame="local_enu_m",
        region_extent=EnvironmentRegionExtent(0.0, 0.0, 2000.0, 1000.0),
        tile_scheme=EnvironmentTileScheme(
            tile_scheme_id="village-area-1km",
            origin_x=0.0,
            origin_y=0.0,
            tile_width_m=1000.0,
            tile_height_m=1000.0,
            columns=2,
            rows=1,
            halo_m=50.0,
        ),
        branch_scope=("terrain", "atmosphere_weather"),
        catalog_refs=(
            "catalog:deterministic_hardstand_surface",
            "catalog:deterministic_village_house",
            "catalog:deterministic_fog_bank",
        ),
        realism_target="G1",
        constraints={"fixture": "g0-k"},
        source_inputs=("docs/task/ground/environment_substrate_g0_architecture",),
        evidence_refs=(
            EnvironmentGeneratorEvidenceRef(
                ref_id="docs:environment-substrate-g0-k",
                evidence_kind="task_dispatch",
                provenance_label="g0-k-preflight",
            ),
        ),
        output_manifest_id="envmanifest:g0-k-generated-fixture",
        no_held_capability_release=True,
    )


def test_g0_k_request_validates_tile_seed_and_provenance_contract() -> None:
    validation = validate_environment_generator_request(
        _request(),
        default_environment_catalog_descriptors(),
    )

    assert validation.valid
    assert not validation.fail_closed
    assert validation.rejection_reason == ""


def test_g0_k_request_rejects_missing_generator_id() -> None:
    validation = validate_environment_generator_request(
        replace(_request(), generator_id=""),
        default_environment_catalog_descriptors(),
    )

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_generator_id_required"


def test_g0_k_request_rejects_tile_extent_gap() -> None:
    bad_scheme = replace(_request().tile_scheme, columns=3)

    validation = validate_environment_generator_request(
        replace(_request(), tile_scheme=bad_scheme),
        default_environment_catalog_descriptors(),
    )

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_tile_extent_invalid"


def test_g0_k_tile_extent_rejects_malformed_or_out_of_range_tile_ids() -> None:
    scheme = _request().tile_scheme

    for tile_id in (
        "tile:village-area-1km:r0000",
        "tile:village-area-1km:r0000:c0002",
        "tile:other:r0000:c0000",
    ):
        try:
            scheme.tile_extent(tile_id)
        except ValueError as exc:
            assert "tile_id" in str(exc)
        else:
            raise AssertionError(f"{tile_id!r} should be rejected")


def test_g0_k_request_rejects_catalog_outside_branch_scope() -> None:
    validation = validate_environment_generator_request(
        replace(_request(), branch_scope=("terrain",)),
        default_environment_catalog_descriptors(),
    )

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "environment_substrate_generator_branch_scope_mismatch"
    )


def test_g0_k_catalog_descriptors_validate_and_reject_feature_schema_roots() -> None:
    catalogs = default_environment_catalog_descriptors()

    validation = validate_environment_catalog_descriptors(catalogs)

    assert validation.valid

    invalid_catalog = replace(catalogs[0], schema_root_kind="road_schema_root")
    rejected = validate_environment_catalog_descriptors((invalid_catalog,))

    assert not rejected.valid
    assert rejected.fail_closed
    assert (
        rejected.rejection_reason
        == "environment_substrate_catalog_feature_schema_root_rejected"
    )


def test_g0_k_catalog_admission_rejects_unknown_catalog_ref() -> None:
    manifest = build_deterministic_generated_environment_manifest(
        _request(),
        default_environment_catalog_descriptors(),
    )
    metadata = manifest.to_metadata()
    metadata["catalogs"].append("catalog:unknown")
    manifest_with_unknown = type(manifest)(**metadata)

    validation = validate_environment_catalog_admission(
        manifest_with_unknown,
        default_environment_catalog_descriptors(),
    )

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "environment_substrate_catalog_ref_unknown"


def test_g0_k_catalog_admission_rejects_branch_mismatch() -> None:
    manifest = build_deterministic_generated_environment_manifest(
        _request(),
        default_environment_catalog_descriptors(),
    )
    metadata = manifest.to_metadata()
    item = metadata["objects"][0]
    item["branch_membership"] = [{"branch_id": "wind_field", "role": "metadata_only"}]
    item["components"] = [
        {
            "component_id": "component:wind-field",
            "family": "wind_field",
            "attributes": {"direction_from_deg": 270.0, "speed_mps": 4.0},
        }
    ]
    manifest_with_branch_mismatch = type(manifest)(**metadata)

    validation = validate_environment_catalog_admission(
        manifest_with_branch_mismatch,
        default_environment_catalog_descriptors(),
    )

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "environment_substrate_catalog_branch_layer_mismatch"
    )


def test_g0_k_generated_manifest_is_canonical_and_deterministic() -> None:
    request = _request()
    catalogs = default_environment_catalog_descriptors()

    manifest_a = build_deterministic_generated_environment_manifest(request, catalogs)
    manifest_b = build_deterministic_generated_environment_manifest(request, catalogs)

    assert manifest_a.to_metadata() == manifest_b.to_metadata()
    assert canonical_environment_bytes(manifest_a.to_metadata()) == canonical_environment_bytes(
        manifest_b.to_metadata()
    )
    assert validate_environment_manifest(manifest_a).valid
    assert validate_environment_catalog_admission(manifest_a, catalogs).valid
    for item in manifest_a.objects:
        assert item.provenance["request_id"] == request.request_id
        assert item.provenance["generator_id"] == request.generator_id
        assert item.provenance["tile_id"] in request.tile_scheme.tile_ids()
        assert item.provenance["no_held_capability_release"] is True


def test_g0_k_different_seed_changes_generated_output_but_preserves_lineage() -> None:
    catalogs = default_environment_catalog_descriptors()
    manifest_a = build_deterministic_generated_environment_manifest(_request(1), catalogs)
    manifest_b = build_deterministic_generated_environment_manifest(_request(2), catalogs)

    assert canonical_environment_bytes(manifest_a.to_metadata()) != canonical_environment_bytes(
        manifest_b.to_metadata()
    )
    assert manifest_a.catalogs == manifest_b.catalogs
    assert manifest_a.generation.generator_id == manifest_b.generation.generator_id
    assert manifest_a.objects[0].catalog_ref == manifest_b.objects[0].catalog_ref


def test_g0_k_seed_derivation_is_stage_tile_and_catalog_scoped() -> None:
    request = _request()
    tile_a, tile_b = request.tile_scheme.tile_ids()

    seed_a = derive_environment_seed(
        request,
        stage_id="stage-a",
        tile_id=tile_a,
        catalog_ref="catalog:deterministic_hardstand_surface",
        local_key="0",
    )
    seed_b = derive_environment_seed(
        request,
        stage_id="stage-a",
        tile_id=tile_b,
        catalog_ref="catalog:deterministic_hardstand_surface",
        local_key="0",
    )
    seed_c = derive_environment_seed(
        request,
        stage_id="stage-b",
        tile_id=tile_a,
        catalog_ref="catalog:deterministic_hardstand_surface",
        local_key="0",
    )

    assert seed_a == derive_environment_seed(
        request,
        stage_id="stage-a",
        tile_id=tile_a,
        catalog_ref="catalog:deterministic_hardstand_surface",
        local_key="0",
    )
    assert seed_a != seed_b
    assert seed_a != seed_c


def test_g0_k_catalog_rejects_missing_required_component_template() -> None:
    invalid_catalog = EnvironmentCatalogDescriptor(
        catalog_id="catalog:bad-road",
        schema_version="1",
        branch_membership=(
            EnvironmentBranchMembership(branch_id="terrain", role="projectable"),
        ),
        layer_membership=("infrastructure_network",),
        geometry_types=("line",),
        required_components=("network",),
        component_templates=(
            EnvironmentComponent(
                component_id="component-template:surface",
                family="surface_material",
                attributes={"surface": "HardPacked"},
            ),
        ),
    )

    validation = validate_environment_catalog_descriptors((invalid_catalog,))

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "environment_substrate_catalog_required_component_missing"
    )
