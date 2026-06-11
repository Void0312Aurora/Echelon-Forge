from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import ( # noqa: E402
  DEFAULT_BRANCH_IDS,
  EnvironmentBranchMembership,
  EnvironmentCatalogDescriptor,
  EnvironmentComponent,
  EnvironmentDerivedProductRequest,
  EnvironmentGeneratorEvidenceRef,
  EnvironmentGeneratorRequest,
  EnvironmentManifest,
  EnvironmentRegionExtent,
  EnvironmentTileScheme,
  build_deterministic_environment_fixture,
  build_deterministic_generated_environment_manifest,
  build_environment_derived_products,
  canonical_environment_bytes,
  default_environment_catalog_descriptors,
  derive_environment_seed,
  validate_environment_catalog_admission,
  validate_environment_catalog_descriptors,
  validate_environment_generator_request,
  validate_environment_manifest,
)


def _manifest_from_metadata(metadata: dict) -> EnvironmentManifest:
  return EnvironmentManifest(**deepcopy(metadata))


def _environment_fixture() -> EnvironmentManifest:
  manifest = build_deterministic_environment_fixture()
  assert validate_environment_manifest(manifest).valid
  return manifest


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


def test_g0_j_static_environment_fixture_validates_deterministically() -> None:
  fixture_a = build_deterministic_environment_fixture()
  fixture_b = build_deterministic_environment_fixture()

  validation = validate_environment_manifest(fixture_a)

  assert validation.valid
  assert not validation.fail_closed
  assert validation.rejection_reason == ""
  assert fixture_a.to_metadata() == fixture_b.to_metadata()
  branch_ids = {
    branch["branch_id"] for branch in fixture_a.to_metadata()["branch_registry"]
  }
  assert set(DEFAULT_BRANCH_IDS) <= branch_ids
  assert fixture_a.to_metadata()["objects"][1]["components"][0]["family"] == "structure"


def test_g0_j_manifest_requires_the_shared_environment_branch_registry() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["branch_registry"] = [
    branch
    for branch in metadata["branch_registry"]
    if branch["branch_id"] != "hydrology"
  ]
  manifest = _manifest_from_metadata(metadata)

  validation = validate_environment_manifest(manifest)

  assert not validation.valid
  assert validation.fail_closed
  assert validation.rejection_reason == "environment_substrate_required_branch_missing"
  assert "hydrology" in validation.errors[0]


def test_g0_j_manifest_rejects_behavior_semantics_in_untyped_properties() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["objects"][0]["properties"]["speed_multiplier"] = 0.8
  manifest = _manifest_from_metadata(metadata)

  validation = validate_environment_manifest(manifest)

  assert not validation.valid
  assert validation.fail_closed
  assert validation.rejection_reason == "environment_substrate_untyped_behavior_property"


def test_g0_j_manifest_rejects_held_runtime_capability_claims() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["capability_claims"] = ["movement"]
  manifest = _manifest_from_metadata(metadata)

  validation = validate_environment_manifest(manifest)

  assert not validation.valid
  assert validation.fail_closed
  assert validation.rejection_reason == "environment_substrate_held_capability_claim"


def test_g0_j_manifest_rejects_missing_required_component_attributes() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  del metadata["objects"][0]["components"][0]["attributes"]["surface"]
  manifest = _manifest_from_metadata(metadata)

  validation = validate_environment_manifest(manifest)

  assert not validation.valid
  assert validation.fail_closed
  assert (
    validation.rejection_reason
    == "environment_substrate_missing_required_component_attribute"
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


def test_g0_m_builds_deterministic_metadata_only_derived_product_bundle() -> None:
  manifest = _environment_fixture()
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
    _environment_fixture(),
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
    _environment_fixture(),
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
    _environment_fixture(),
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
