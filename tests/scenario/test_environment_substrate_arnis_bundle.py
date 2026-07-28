from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python.scenario.environment_substrate import (  # noqa: E402
    ArnisEnvironmentImportResult,
    canonical_environment_bytes,
    import_arnis_environment_bundle,
    validate_environment_catalog_admission,
    validate_environment_manifest,
)
from python.scenario.environment_substrate.importers.arnis_bundle import (  # noqa: E402
    ARNIS_CONTINUOUS_EXPORTER_PATCH_ID,
    ARNIS_CONTINUOUS_PATCH_SHA256,
)


_EXPECTED_BUNDLE_ROOT = (
    Path(__file__).parent
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "chicago_river_phase1"
    / "expected"
)
_PHASE1_PROJECTION = "arnis_local_scaled_web_mercator_r6371000_normalized_to_local_enu"


def _continuous_lineage() -> dict[str, Any]:
    return {
        "contract": "arnis_continuous_metric.v1",
        "representation": "continuous_metric_2_5d",
        "export_stage": "post_semantic_processing_pre_render_quantization",
        "geometry": {
            "source_stage": "projected_from_wgs84_f64",
            "storage": "json_float64",
            "quantization_step_m": None,
            "block_projection_applied": False,
        },
        "elevation": {
            "source_stage": "postprocessed_metric_dem",
            "storage": "float32_le",
            "vertical_quantization_step_m": None,
            "minecraft_y_transform_applied": False,
            "minecraft_y_roundtrip": False,
        },
        "landcover": {
            "source_stage": "source_classification_metric_grid",
            "block_palette_roundtrip": False,
        },
        "minecraft_world_read": False,
        "anvil_region_read": False,
        "voxelization_applied": False,
    }


def _artifact_lineage(kind: str) -> dict[str, Any]:
    lineage: dict[str, Any] = {"representation": "continuous_metric_2_5d"}
    if kind == "vector_features":
        lineage.update(
            {
                "source_stage": "projected_from_wgs84_f64",
                "storage": "json_float64",
                "quantization_step_m": None,
                "block_projection_applied": False,
            }
        )
    elif kind == "elevation_raster":
        lineage.update(
            {
                "source_stage": "postprocessed_metric_dem",
                "storage": "float32_le",
                "vertical_quantization_step_m": None,
                "minecraft_y_transform_applied": False,
                "minecraft_y_roundtrip": False,
            }
        )
    elif kind == "landcover_raster":
        lineage.update(
            {
                "source_stage": "source_classification_metric_grid",
                "storage": "uint8",
                "block_palette_roundtrip": False,
            }
        )
    elif kind == "provenance":
        lineage.update(
            {
                "source_stage": "continuous_bundle_provenance",
                "storage": "json",
                "block_derived": False,
            }
        )
    else:
        raise AssertionError(f"unsupported test artifact kind {kind!r}")
    return lineage


def _measurement_lineage(*, source_semantics: str = "") -> dict[str, Any]:
    lineage = {
        "source_domain": "metric_semantics_pre_block_conversion",
        "derived_from_block_count": False,
        "derived_from_block_range": False,
    }
    if source_semantics:
        lineage["source_semantics"] = source_semantics
    return lineage


def _semantic_lineage(source_semantics: str) -> dict[str, Any]:
    return {
        "source_domain": "semantic_tags_pre_block_conversion",
        "source_semantics": source_semantics,
        "derived_from_block_count": False,
        "derived_from_block_range": False,
    }


def _feature_lineage(
    feature_class: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    measurements: dict[str, Any] = {}
    if feature_class == "road":
        measurements["width_m"] = _measurement_lineage(
            source_semantics=str(attributes.get("width_source") or "")
        )
        for key in ("layer", "bridge", "tunnel", "covered"):
            measurements[key] = _semantic_lineage(f"test_{key}_semantic")
    elif feature_class == "building":
        measurements["height_m"] = _measurement_lineage(
            source_semantics=str(attributes.get("height_source") or "")
        )
        if "layer" in attributes:
            measurements["layer"] = _semantic_lineage("test_layer_semantic")
        if "base_offset_m" in attributes:
            measurements["base_offset_m"] = _measurement_lineage(
                source_semantics=str(attributes.get("base_offset_source") or "")
            )
            measurements["base_offset_source"] = _semantic_lineage(
                str(attributes.get("base_offset_source") or "")
            )
    elif feature_class == "hydrology" and "width_m" in attributes:
        measurements["width_m"] = _measurement_lineage(
            source_semantics=str(attributes.get("width_source") or "")
        )
    anchor_source = str(attributes.get("vertical_anchor_source") or "")
    for key in (
        "vertical_anchor_mode",
        "vertical_placement_resolved",
        "vertical_anchor_source",
    ):
        measurements[key] = _semantic_lineage(anchor_source)
    return {
        "geometry_source_stage": "projected_from_wgs84_f64",
        "block_projection_applied": False,
        "measurements": measurements,
    }


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_json(path: Path, payload: Any) -> None:
    _write_bytes(path, _json_bytes(payload))


def _artifact_descriptor(
    root: Path,
    *,
    artifact_id: str,
    kind: str,
    relative_path: str,
    media_type: str,
    **metadata: Any,
) -> dict[str, Any]:
    payload = (root / relative_path).read_bytes()
    return {
        "artifact_id": artifact_id,
        "byte_length": len(payload),
        "kind": kind,
        "media_type": media_type,
        "path": relative_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        **metadata,
    }


def _feature_payload(
    feature_class: str,
    feature_id: str,
    geometry: dict[str, Any],
    attributes: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "arnis_cmo_features",
        "schema_version": 1,
        "coordinate_frame": "local_enu_m",
        "feature_class": feature_class,
        "features": [
            {
                "feature_id": feature_id,
                "geometry": geometry,
                "attributes": attributes,
                "lineage": _feature_lineage(feature_class, attributes),
                "provenance": {
                    "source_provider": "openstreetmap",
                    "source_feature_type": "way",
                    "source_feature_id": feature_id,
                    "source_tags": {},
                },
            }
        ],
    }


def _build_lightweight_bundle(root: Path) -> Path:
    provenance = {
        "contract_version": "arnis_cmo_bundle.v1",
        "exporter_patch_id": ARNIS_CONTINUOUS_EXPORTER_PATCH_ID,
        "exporter_patch_sha256": ARNIS_CONTINUOUS_PATCH_SHA256,
        "exporter_version": "cmo.phase1.test",
        "generator": {
            "id": "arnis",
            "upstream_revision": "a" * 40,
            "version": "3.0.0",
        },
        "source_inputs": [
            {
                "kind": "osm_json",
                "provider": "openstreetmap",
                "sha256": "b" * 64,
            }
        ],
        "lineage": _continuous_lineage(),
        "capability_boundary": {"no_held_capability_release": True},
    }
    road = _feature_payload(
        "road",
        "openstreetmap:way:1:road",
        {
            "type": "LineString",
            "coordinates": [[-0.75, 0.0], [0.75, 0.0]],
        },
        {
            "bridge": False,
            "connectivity": "source_geometry",
            "covered": False,
            "highway_type": "residential",
            "layer": 0,
            "surface_class": "asphalt",
            "tunnel": False,
            "vertical_anchor_mode": "terrain_draped",
            "vertical_anchor_source": "test_dem_polyline_drape",
            "vertical_placement_resolved": True,
            "width_m": 6.0,
            "width_source": "test_fixture",
        },
    )
    building = _feature_payload(
        "building",
        "openstreetmap:way:2:building",
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-0.5, -0.5],
                    [0.0, -0.5],
                    [0.0, 0.0],
                    [-0.5, 0.0],
                    [-0.5, -0.5],
                ]
            ],
        },
        {
            "building_type": "yes",
            "footprint": "polygon",
            "height_m": 8.0,
            "height_semantics": "metric_body_height",
            "height_source": "test_fixture",
            "material": "unspecified",
            "base_offset_m": 0.0,
            "base_offset_source": "test_dem_footprint_min",
            "vertical_anchor_mode": "terrain_rigid",
            "vertical_anchor_source": "test_dem_footprint_min",
            "vertical_placement_resolved": True,
        },
    )
    hydrology = _feature_payload(
        "hydrology",
        "openstreetmap:way:3:hydrology",
        {
            "type": "LineString",
            "coordinates": [[-0.75, -0.75], [0.75, 0.75]],
        },
        {
            "geometry_role": "centerline",
            "state": "static_source_geometry",
            "vertical_anchor_mode": "water_surface_from_dem",
            "vertical_anchor_source": "test_dem_water_surface",
            "vertical_placement_resolved": True,
            "water_kind": "stream",
            "width_m": 2.0,
            "width_source": "test_fixture_metric",
        },
    )

    _write_json(root / "provenance.json", provenance)
    _write_bytes(root / "rasters" / "elevation.f32le", struct.pack("<4f", 0, 1, 2, 3))
    _write_bytes(root / "rasters" / "landcover.u8", bytes((10, 30, 50, 80)))
    _write_json(root / "vectors" / "roads.cmo.json", road)
    _write_json(root / "vectors" / "buildings.cmo.json", building)
    _write_json(root / "vectors" / "hydrology.cmo.json", hydrology)

    raster_grid = {
        "grid_registration": "point",
        "origin_xy_m": [-1.0, 1.0],
        "step_xy_m": [2.0, -2.0],
    }
    artifacts = [
        _artifact_descriptor(
            root,
            artifact_id="artifact:provenance",
            kind="provenance",
            relative_path="provenance.json",
            media_type="application/json",
            metadata={"lineage": _artifact_lineage("provenance")},
        ),
        _artifact_descriptor(
            root,
            artifact_id="artifact:elevation",
            kind="elevation_raster",
            relative_path="rasters/elevation.f32le",
            media_type="application/vnd.arnis-cmo.raster-f32le",
            dtype="float32_le",
            shape=[2, 2],
            metadata={
                **raster_grid,
                "lineage": _artifact_lineage("elevation_raster"),
                "semantics": "test_elevation",
                "source_provider": "test_dem",
                "contributing_sources": {"test_dem": 1},
                "missing_source_units": 0,
                "uncertainty_status": "not_reported",
                "units": "m",
                "vertical_datum": "test_datum",
            },
        ),
        _artifact_descriptor(
            root,
            artifact_id="artifact:landcover",
            kind="landcover_raster",
            relative_path="rasters/landcover.u8",
            media_type="application/vnd.arnis-cmo.raster-u8",
            dtype="uint8",
            shape=[2, 2],
            metadata={
                **raster_grid,
                "lineage": _artifact_lineage("landcover_raster"),
                "semantics": "test_landcover",
                "classification_scheme": "ESA_WorldCover_2021_v200",
                "class_legend": {
                    "10": "tree_cover",
                    "30": "grassland",
                    "50": "built_up",
                    "80": "permanent_water",
                },
            },
        ),
        _artifact_descriptor(
            root,
            artifact_id="artifact:road",
            kind="vector_features",
            relative_path="vectors/roads.cmo.json",
            media_type="application/vnd.arnis-cmo.features+json",
            feature_class="road",
            feature_count=1,
            metadata={"lineage": _artifact_lineage("vector_features")},
        ),
        _artifact_descriptor(
            root,
            artifact_id="artifact:building",
            kind="vector_features",
            relative_path="vectors/buildings.cmo.json",
            media_type="application/vnd.arnis-cmo.features+json",
            feature_class="building",
            feature_count=1,
            metadata={"lineage": _artifact_lineage("vector_features")},
        ),
        _artifact_descriptor(
            root,
            artifact_id="artifact:hydrology",
            kind="vector_features",
            relative_path="vectors/hydrology.cmo.json",
            media_type="application/vnd.arnis-cmo.features+json",
            feature_class="hydrology",
            feature_count=1,
            metadata={"lineage": _artifact_lineage("vector_features")},
        ),
    ]
    bundle = {
        "artifacts": artifacts,
        "bbox_wgs84": {
            "min_lon": 0.0,
            "min_lat": 0.0,
            "max_lon": 0.001,
            "max_lat": 0.001,
        },
        "bundle_id": "arnis-cmo-bundle:test-phase1",
        "capability_claims": [],
        "content_digest_sha256": "0" * 64,
        "contract_version": "arnis_cmo_bundle.v1",
        "coordinate_frame": "local_enu_m",
        "lineage": _continuous_lineage(),
        "generator": {
            "exporter_version": "cmo.phase1.test",
            "exporter_patch_id": ARNIS_CONTINUOUS_EXPORTER_PATCH_ID,
            "exporter_patch_sha256": ARNIS_CONTINUOUS_PATCH_SHA256,
            "id": "arnis",
            "upstream_revision": "a" * 40,
            "version": "3.0.0",
        },
        "no_held_capability_release": True,
        "region_extent": {
            "min_x": -1.0,
            "min_y": -1.0,
            "max_x": 1.0,
            "max_y": 1.0,
        },
        "request": {
            "deterministic_seed": 0,
            "overture": False,
            "projection": _PHASE1_PROJECTION,
            "request_id": "arnis-import:test-phase1",
            "rotation_deg": 0.0,
            "scale": 1.0,
            "source_input_sha256": "b" * 64,
        },
        "tile_scheme": {
            "columns": 1,
            "halo_m": 0.0,
            "rows": 1,
            "tile_id": "tile:arnis-test:r0000:c0000",
            "tile_scheme_id": "arnis-test",
        },
    }
    _write_json(root / "bundle.json", bundle)
    return root


def _refresh_artifact_descriptor(root: Path, artifact_id: str) -> None:
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    artifact = next(item for item in bundle["artifacts"] if item["artifact_id"] == artifact_id)
    payload = (root / artifact["path"]).read_bytes()
    artifact["byte_length"] = len(payload)
    artifact["sha256"] = hashlib.sha256(payload).hexdigest()
    _write_json(bundle_path, bundle)


def _rewrite_single_feature(
    root: Path,
    feature_class: str,
    *,
    attribute_updates: dict[str, Any] | None = None,
    remove_attributes: tuple[str, ...] = (),
    remove_measurements: tuple[str, ...] = (),
) -> None:
    plural = {"road": "roads", "building": "buildings", "hydrology": "hydrology"}[feature_class]
    path = root / "vectors" / f"{plural}.cmo.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    feature = payload["features"][0]
    for key in remove_attributes:
        feature["attributes"].pop(key, None)
    feature["attributes"].update(attribute_updates or {})
    feature["lineage"] = _feature_lineage(feature_class, feature["attributes"])
    for key in remove_measurements:
        feature["lineage"]["measurements"].pop(key, None)
    _write_json(path, payload)
    _refresh_artifact_descriptor(root, f"artifact:{feature_class}")


@pytest.fixture(scope="module")
def continuous_expected_bundle_root() -> Path:
    return _EXPECTED_BUNDLE_ROOT


@pytest.fixture(scope="module")
def imported_expected_bundle(
    continuous_expected_bundle_root: Path,
) -> ArnisEnvironmentImportResult:
    result = import_arnis_environment_bundle(continuous_expected_bundle_root)
    assert result.valid, result.errors
    assert not result.fail_closed
    assert result.manifest is not None
    return result


def test_arnis_phase1_expected_bundle_imports_objects_and_components(
    imported_expected_bundle: ArnisEnvironmentImportResult,
    continuous_expected_bundle_root: Path,
) -> None:
    result = imported_expected_bundle
    manifest = result.manifest
    assert manifest is not None

    assert (
        result.bundle_digest_sha256
        == hashlib.sha256(
            (continuous_expected_bundle_root / "bundle.json").read_bytes()
        ).hexdigest()
    )
    assert len(manifest.objects) == 511
    assert Counter(item.catalog_ref for item in manifest.objects) == {
        "catalog:arnis_elevation_tile": 1,
        "catalog:arnis_landcover_tile": 1,
        "catalog:arnis_road": 425,
        "catalog:arnis_building": 76,
        "catalog:arnis_hydrology": 8,
    }
    assert Counter(
        component.family for item in manifest.objects for component in item.components
    ) == {
        "elevation_field": 1,
        "landcover_field": 1,
        "network": 425,
        "surface_material": 213,
        "structure": 76,
        "hydrology": 8,
        "elevation_anchor": 509,
    }

    elevation = next(
        item for item in manifest.objects if item.catalog_ref == "catalog:arnis_elevation_tile"
    )
    elevation_attributes = elevation.components[0].attributes
    assert elevation.geometry.geometry_type == "rect"
    assert elevation_attributes["dtype"] == "float32_le"
    assert elevation_attributes["shape"] == [334, 332]
    assert elevation_attributes["units"] == "m"

    landcover = next(
        item for item in manifest.objects if item.catalog_ref == "catalog:arnis_landcover_tile"
    )
    landcover_attributes = landcover.components[0].attributes
    assert landcover_attributes["dtype"] == "uint8"
    assert landcover_attributes["classification_scheme"] == "ESA_WorldCover_2021_v200"
    assert landcover_attributes["class_legend"]["80"] == "permanent_water"

    buildings = [item for item in manifest.objects if item.catalog_ref == "catalog:arnis_building"]
    way_source_ids = [
        item.provenance["source_feature_id"]
        for item in buildings
        if item.provenance["source_feature_type"] == "way"
    ]
    assert len(way_source_ids) == len(set(way_source_ids))
    assert all(item.components[0].attributes["height_semantics"] for item in buildings)
    assert all(
        item.provenance["continuous_lineage"] == _continuous_lineage()
        and item.provenance["artifact_lineage"]["representation"] == "continuous_metric_2_5d"
        for item in manifest.objects
    )
    assert all("feature_lineage" in item.provenance for item in buildings)
    assert manifest.validation_evidence[0]["continuous_lineage"] == _continuous_lineage()
    assert manifest.validation_evidence[0]["exporter_patch_sha256"] == (
        ARNIS_CONTINUOUS_PATCH_SHA256
    )
    anchor_counts = manifest.validation_evidence[0]["elevation_anchor_counts"]
    assert anchor_counts["total"] == 509
    assert anchor_counts["resolved"] + anchor_counts["held"] == 509
    assert anchor_counts["held"] > 0

    assert validate_environment_manifest(manifest).valid
    assert validate_environment_catalog_admission(
        manifest,
        result.catalog_descriptors,
    ).valid


def test_arnis_phase1_expected_bundle_preserves_continuous_metric_geometry() -> None:
    bundle = json.loads((_EXPECTED_BUNDLE_ROOT / "bundle.json").read_text(encoding="utf-8"))
    extent = bundle["region_extent"]
    assert math.isclose(extent["max_x"] - extent["min_x"], 331.1168754437471)
    assert math.isclose(extent["max_y"] - extent["min_y"], 333.58478003334514)

    for feature_class in ("roads", "buildings", "hydrology"):
        payload = json.loads(
            (_EXPECTED_BUNDLE_ROOT / "vectors" / f"{feature_class}.cmo.json").read_text(
                encoding="utf-8"
            )
        )
        points: list[tuple[float, float]] = []

        def collect(value: Any) -> None:
            if isinstance(value, list):
                if len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
                    points.append((float(value[0]), float(value[1])))
                else:
                    for item in value:
                        collect(item)

        for feature in payload["features"]:
            collect(feature["geometry"]["coordinates"])
            assert feature["lineage"]["block_projection_applied"] is False
            for measurement in feature["lineage"]["measurements"].values():
                assert measurement["derived_from_block_count"] is False
                assert measurement["derived_from_block_range"] is False

        assert points
        assert sum(abs(x - round(x)) <= 1.0e-9 for x, _ in points) / len(points) < 0.05
        assert sum(abs(y - round(y)) <= 1.0e-9 for _, y in points) / len(points) < 0.05
        nearest_grid_rmse = math.sqrt(
            sum((x - round(x)) ** 2 + (y - round(y)) ** 2 for x, y in points) / (2.0 * len(points))
        )
        assert nearest_grid_rmse > 0.1


def test_arnis_phase1_import_is_canonical_and_deterministic(
    imported_expected_bundle: ArnisEnvironmentImportResult,
    continuous_expected_bundle_root: Path,
) -> None:
    second = import_arnis_environment_bundle(continuous_expected_bundle_root)
    assert second.valid, second.errors
    assert second.manifest is not None
    assert imported_expected_bundle.manifest is not None

    first_bytes = canonical_environment_bytes(imported_expected_bundle.manifest.to_metadata())
    second_bytes = canonical_environment_bytes(second.manifest.to_metadata())
    assert first_bytes == second_bytes
    assert imported_expected_bundle.bundle_digest_sha256 == second.bundle_digest_sha256
    assert [item.object_id for item in second.manifest.objects] == sorted(
        item.object_id for item in second.manifest.objects
    )


def test_arnis_v1_import_materializes_required_elevation_anchor_components(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")

    result = import_arnis_environment_bundle(root)

    assert result.valid, result.errors
    assert result.manifest is not None
    objects = {item.catalog_ref: item for item in result.manifest.objects}
    anchors = {
        catalog_ref: next(
            component for component in item.components if component.family == "elevation_anchor"
        )
        for catalog_ref, item in objects.items()
        if catalog_ref
        in {
            "catalog:arnis_road",
            "catalog:arnis_building",
            "catalog:arnis_hydrology",
        }
    }
    assert anchors["catalog:arnis_road"].attributes == {
        "mode": "terrain_draped",
        "resolved": True,
        "source": "test_dem_polyline_drape",
        "layer": 0,
        "bridge": False,
        "tunnel": False,
        "covered": False,
    }
    assert anchors["catalog:arnis_building"].attributes == {
        "mode": "terrain_rigid",
        "resolved": True,
        "source": "test_dem_footprint_min",
        "base_offset_m": 0.0,
        "base_offset_source": "test_dem_footprint_min",
    }
    assert anchors["catalog:arnis_hydrology"].attributes == {
        "mode": "water_surface_from_dem",
        "resolved": True,
        "source": "test_dem_water_surface",
    }
    road_network = next(
        component
        for component in objects["catalog:arnis_road"].components
        if component.family == "network"
    )
    assert {
        key: road_network.attributes[key] for key in ("bridge", "tunnel", "covered", "layer")
    } == {
        "bridge": False,
        "tunnel": False,
        "covered": False,
        "layer": 0,
    }
    for catalog_ref, anchor in anchors.items():
        assert objects[catalog_ref].provenance["static_placement"] == anchor.attributes

    component_descriptor = next(
        component
        for component in result.manifest.component_registry
        if component.family == "elevation_anchor"
    )
    assert component_descriptor.required_attributes == ("mode", "resolved", "source")
    branches = {branch.branch_id: branch for branch in result.manifest.branch_registry}
    assert "elevation_anchor" in branches["terrain"].allowed_components
    assert "elevation_anchor" in branches["hydrology"].allowed_components
    for catalog in result.catalog_descriptors:
        if catalog.catalog_id in anchors:
            assert "elevation_anchor" in catalog.required_components
    assert result.manifest.validation_evidence[0]["elevation_anchor_counts"] == {
        "total": 3,
        "resolved": 3,
        "held": 0,
    }
    assert result.manifest.capability_claims == ()
    assert all(
        item.provenance["no_held_capability_release"] is True for item in result.manifest.objects
    )


def test_arnis_v1_import_preserves_unresolved_layered_building_anchor(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    _rewrite_single_feature(
        root,
        "building",
        attribute_updates={
            "layer": 2,
            "vertical_anchor_mode": "elevated_profile",
            "vertical_anchor_source": "osm_layer_requires_elevated_profile",
            "vertical_placement_resolved": False,
        },
        remove_attributes=("base_offset_m", "base_offset_source"),
        remove_measurements=("base_offset_m",),
    )

    result = import_arnis_environment_bundle(root)

    assert result.valid, result.errors
    assert result.manifest is not None
    building = next(
        item for item in result.manifest.objects if item.catalog_ref == "catalog:arnis_building"
    )
    anchor = next(
        component for component in building.components if component.family == "elevation_anchor"
    )
    assert anchor.attributes == {
        "mode": "elevated_profile",
        "resolved": False,
        "source": "osm_layer_requires_elevated_profile",
        "layer": 2,
    }
    assert building.provenance["static_placement"] == anchor.attributes
    assert result.manifest.validation_evidence[0]["elevation_anchor_counts"] == {
        "total": 3,
        "resolved": 2,
        "held": 1,
    }


def test_arnis_v1_import_preserves_unresolved_bridge_anchor(tmp_path: Path) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    _rewrite_single_feature(
        root,
        "road",
        attribute_updates={
            "bridge": True,
            "covered": True,
            "layer": 1,
            "vertical_anchor_mode": "elevated_profile",
            "vertical_anchor_source": "osm_bridge_layer_requires_profile",
            "vertical_placement_resolved": False,
        },
    )

    result = import_arnis_environment_bundle(root)

    assert result.valid, result.errors
    assert result.manifest is not None
    road = next(
        item for item in result.manifest.objects if item.catalog_ref == "catalog:arnis_road"
    )
    anchor = next(
        component for component in road.components if component.family == "elevation_anchor"
    )
    assert anchor.attributes == {
        "mode": "elevated_profile",
        "resolved": False,
        "source": "osm_bridge_layer_requires_profile",
        "layer": 1,
        "bridge": True,
        "tunnel": False,
        "covered": True,
    }
    network = next(component for component in road.components if component.family == "network")
    assert network.attributes["bridge"] is True
    assert network.attributes["covered"] is True
    assert network.attributes["tunnel"] is False
    assert network.attributes["layer"] == 1
    assert road.provenance["static_placement"] == anchor.attributes
    assert result.manifest.validation_evidence[0]["elevation_anchor_counts"]["held"] == 1


@pytest.mark.parametrize(
    ("attribute_updates", "expected_anchor"),
    (
        (
            {
                "layer": 2,
                "vertical_anchor_mode": "elevated_profile",
                "vertical_anchor_source": "osm_positive_layer_requires_profile",
                "vertical_placement_resolved": False,
            },
            {
                "mode": "elevated_profile",
                "resolved": False,
                "source": "osm_positive_layer_requires_profile",
                "layer": 2,
                "bridge": False,
                "tunnel": False,
                "covered": False,
            },
        ),
        (
            {
                "layer": 0,
                "tunnel": True,
                "vertical_anchor_mode": "subsurface_profile",
                "vertical_anchor_source": "osm_tunnel_requires_profile",
                "vertical_placement_resolved": False,
            },
            {
                "mode": "subsurface_profile",
                "resolved": False,
                "source": "osm_tunnel_requires_profile",
                "layer": 0,
                "bridge": False,
                "tunnel": True,
                "covered": False,
            },
        ),
        (
            {
                "layer": 1,
                "tunnel": True,
                "vertical_anchor_mode": "elevated_profile",
                "vertical_anchor_source": "osm_positive_layer_overrides_building_passage",
                "vertical_placement_resolved": False,
            },
            {
                "mode": "elevated_profile",
                "resolved": False,
                "source": "osm_positive_layer_overrides_building_passage",
                "layer": 1,
                "bridge": False,
                "tunnel": True,
                "covered": False,
            },
        ),
        (
            {
                "bridge": True,
                "layer": 0,
                "tunnel": True,
                "vertical_anchor_mode": "elevated_profile",
                "vertical_anchor_source": "osm_bridge_precedence_over_tunnel_tag",
                "vertical_placement_resolved": False,
            },
            {
                "mode": "elevated_profile",
                "resolved": False,
                "source": "osm_bridge_precedence_over_tunnel_tag",
                "layer": 0,
                "bridge": True,
                "tunnel": True,
                "covered": False,
            },
        ),
        (
            {
                "covered": True,
            },
            {
                "mode": "terrain_draped",
                "resolved": True,
                "source": "test_dem_polyline_drape",
                "layer": 0,
                "bridge": False,
                "tunnel": False,
                "covered": True,
            },
        ),
    ),
    ids=(
        "positive-layer-elevated-road",
        "explicit-tunnel-zero-layer-road",
        "positive-layer-building-passage-road",
        "bridge-precedence-over-tunnel-tag-road",
        "covered-arcade-terrain-road",
    ),
)
def test_arnis_v1_import_preserves_road_profile_evidence(
    tmp_path: Path,
    attribute_updates: dict[str, Any],
    expected_anchor: dict[str, Any],
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    _rewrite_single_feature(
        root,
        "road",
        attribute_updates=attribute_updates,
    )

    result = import_arnis_environment_bundle(root)

    assert result.valid, result.errors
    assert result.manifest is not None
    road = next(
        item for item in result.manifest.objects if item.catalog_ref == "catalog:arnis_road"
    )
    anchor = next(
        component for component in road.components if component.family == "elevation_anchor"
    )
    assert anchor.attributes == expected_anchor
    assert road.provenance["static_placement"] == expected_anchor
    network = next(component for component in road.components if component.family == "network")
    assert {key: network.attributes[key] for key in ("bridge", "tunnel", "covered", "layer")} == {
        key: expected_anchor[key] for key in ("bridge", "tunnel", "covered", "layer")
    }
    assert result.manifest.validation_evidence[0]["elevation_anchor_counts"]["held"] == (
        0 if expected_anchor["resolved"] else 1
    )


@pytest.mark.parametrize(
    ("feature_class", "attribute_updates", "remove_attributes", "remove_measurements"),
    (
        (
            "building",
            {},
            ("base_offset_m", "base_offset_source"),
            ("base_offset_m",),
        ),
        ("building", {"base_offset_m": -1.0}, (), ()),
        ("building", {"base_offset_m": float("nan")}, (), ()),
        ("building", {"vertical_placement_resolved": "true"}, (), ()),
        (
            "building",
            {
                "vertical_anchor_mode": "elevated_profile",
                "vertical_anchor_source": "osm_layer_requires_elevated_profile",
                "vertical_placement_resolved": False,
            },
            ("base_offset_m", "base_offset_source"),
            ("base_offset_m",),
        ),
        (
            "road",
            {
                "bridge": True,
                "layer": 1,
                "vertical_anchor_mode": "terrain_draped",
                "vertical_placement_resolved": True,
            },
            (),
            (),
        ),
        (
            "road",
            {
                "covered": True,
                "vertical_anchor_mode": "subsurface_profile",
                "vertical_placement_resolved": False,
            },
            (),
            (),
        ),
        (
            "road",
            {
                "bridge": True,
                "tunnel": True,
                "layer": 0,
                "vertical_anchor_mode": "subsurface_profile",
                "vertical_placement_resolved": False,
            },
            (),
            (),
        ),
        (
            "road",
            {
                "bridge": False,
                "tunnel": True,
                "layer": 1,
                "vertical_anchor_mode": "subsurface_profile",
                "vertical_placement_resolved": False,
            },
            (),
            (),
        ),
        (
            "road",
            {
                "bridge": True,
                "layer": 1,
                "vertical_anchor_mode": "elevated_profile",
                "vertical_placement_resolved": True,
            },
            (),
            (),
        ),
        (
            "hydrology",
            {"vertical_placement_resolved": False},
            (),
            (),
        ),
        (
            "hydrology",
            {"vertical_anchor_mode": "terrain_draped"},
            (),
            (),
        ),
    ),
    ids=(
        "resolved-building-missing-base-offset",
        "negative-building-base-offset",
        "nan-building-base-offset",
        "nonboolean-resolved-state",
        "unresolved-elevated-building-missing-layer",
        "terrain-draped-bridge-contradiction",
        "covered-does-not-imply-subsurface",
        "subsurface-bridge-contradiction",
        "subsurface-positive-layer-contradiction",
        "resolved-bridge-missing-profile",
        "unresolved-water-surface",
        "wrong-hydrology-anchor-mode",
    ),
)
def test_arnis_v1_import_rejects_invalid_elevation_anchor_claims(
    tmp_path: Path,
    feature_class: str,
    attribute_updates: dict[str, Any],
    remove_attributes: tuple[str, ...],
    remove_measurements: tuple[str, ...],
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    _rewrite_single_feature(
        root,
        feature_class,
        attribute_updates=attribute_updates,
        remove_attributes=remove_attributes,
        remove_measurements=remove_measurements,
    )

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == ("environment_substrate_arnis_elevation_anchor_invalid")


def test_arnis_v1_old_shape_is_not_admitted_as_continuous(tmp_path: Path) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    del bundle["lineage"]
    bundle["generator"].pop("exporter_patch_sha256")
    bundle["generator"]["exporter_patch_id"] = "0001-cmo-bundle-export-v1"
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == ("environment_substrate_arnis_continuous_lineage_required")


def test_arnis_v1_continuous_bundle_rejects_missing_root_lineage(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    del bundle["lineage"]
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_continuous_lineage_required")


def test_arnis_v1_continuous_bundle_rejects_unallowlisted_exporter_patch_sha(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["generator"]["exporter_patch_sha256"] = "0" * 64
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_exporter_identity_mismatch")


def test_arnis_v1_continuous_bundle_rejects_missing_artifact_lineage(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    road = next(item for item in bundle["artifacts"] if item["artifact_id"] == "artifact:road")
    del road["metadata"]["lineage"]
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_continuous_lineage_required")


def test_arnis_v1_continuous_bundle_rejects_missing_feature_lineage(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    road_path = root / "vectors" / "roads.cmo.json"
    roads = json.loads(road_path.read_text(encoding="utf-8"))
    del roads["features"][0]["lineage"]
    _write_json(road_path, roads)
    _refresh_artifact_descriptor(root, "artifact:road")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_continuous_lineage_required")


def test_arnis_v1_continuous_bundle_rejects_provenance_lineage_mismatch(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    provenance_path = root / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["lineage"]["export_stage"] = "processed_node_block_grid"
    _write_json(provenance_path, provenance)
    _refresh_artifact_descriptor(root, "artifact:provenance")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == "environment_substrate_arnis_lineage_mismatch"


def test_arnis_v1_continuous_bundle_accepts_legitimate_integer_coordinates(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    road_path = root / "vectors" / "roads.cmo.json"
    roads = json.loads(road_path.read_text(encoding="utf-8"))
    roads["features"][0]["geometry"]["coordinates"] = [[-1, 0], [1, 0]]
    _write_json(road_path, roads)
    _refresh_artifact_descriptor(root, "artifact:road")

    result = import_arnis_environment_bundle(root)

    assert result.valid, result.errors
    assert result.manifest is not None
    road = next(
        item for item in result.manifest.objects if item.catalog_ref == "catalog:arnis_road"
    )
    assert road.geometry.coordinates["points"] == [[-1.0, 0.0], [1.0, 0.0]]


def test_arnis_v1_continuous_bundle_rejects_road_width_from_block_range(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    road_path = root / "vectors" / "roads.cmo.json"
    roads = json.loads(road_path.read_text(encoding="utf-8"))
    roads["features"][0]["attributes"]["width_source"] = "arnis_highway_block_range"
    _write_json(road_path, roads)
    _refresh_artifact_descriptor(root, "artifact:road")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_block_derived_rejected")


def test_arnis_v1_continuous_bundle_rejects_building_height_from_block_count(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    building_path = root / "vectors" / "buildings.cmo.json"
    buildings = json.loads(building_path.read_text(encoding="utf-8"))
    buildings["features"][0]["lineage"]["measurements"]["height_m"]["derived_from_block_count"] = (
        True
    )
    _write_json(building_path, buildings)
    _refresh_artifact_descriptor(root, "artifact:building")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_block_derived_rejected")


def test_arnis_v1_continuous_bundle_rejects_rendered_block_height_semantics(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    building_path = root / "vectors" / "buildings.cmo.json"
    buildings = json.loads(building_path.read_text(encoding="utf-8"))
    buildings["features"][0]["attributes"]["height_semantics"] = "arnis_rendered_body_height"
    _write_json(building_path, buildings)
    _refresh_artifact_descriptor(root, "artifact:building")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_block_derived_rejected")


def test_arnis_v1_continuous_bundle_rejects_hydrology_width_from_block_default(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    hydrology_path = root / "vectors" / "hydrology.cmo.json"
    hydrology = json.loads(hydrology_path.read_text(encoding="utf-8"))
    hydrology["features"][0]["attributes"]["width_source"] = "arnis_waterway_block_default"
    _write_json(hydrology_path, hydrology)
    _refresh_artifact_descriptor(root, "artifact:hydrology")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_block_derived_rejected")


def test_arnis_v1_continuous_bundle_rejects_minecraft_y_elevation_roundtrip(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    elevation = next(
        item for item in bundle["artifacts"] if item["artifact_id"] == "artifact:elevation"
    )
    elevation["metadata"]["lineage"]["minecraft_y_roundtrip"] = True
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.rejection_reason == ("environment_substrate_arnis_block_derived_rejected")


def test_arnis_phase1_checksum_tamper_fails_closed(tmp_path: Path) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    landcover = root / "rasters" / "landcover.u8"
    landcover.write_bytes(landcover.read_bytes() + b"\xff")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.manifest is None
    assert result.rejection_reason == "environment_substrate_arnis_checksum_mismatch"


def test_arnis_phase1_artifact_path_traversal_fails_closed(tmp_path: Path) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["artifacts"][0]["path"] = "../provenance.json"
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == "environment_substrate_arnis_artifact_path_invalid"


def test_arnis_phase1_rejects_mixed_or_missing_elevation_sources(
    tmp_path: Path,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    elevation = next(
        item for item in bundle["artifacts"] if item["artifact_id"] == "artifact:elevation"
    )
    elevation["metadata"]["contributing_sources"]["aws_terrain"] = 1
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == "environment_substrate_arnis_raster_metadata_invalid"


@pytest.mark.parametrize(
    ("request_key", "invalid_value"),
    (
        ("scale", 2.0),
        ("rotation_deg", 15.0),
        ("projection", "web_mercator"),
        ("overture", True),
    ),
)
def test_arnis_phase1_rejects_non_phase1_coordinate_parameters(
    tmp_path: Path,
    request_key: str,
    invalid_value: Any,
) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    bundle_path = root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["request"][request_key] = invalid_value
    _write_json(bundle_path, bundle)

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == "environment_substrate_arnis_coordinate_frame_unsupported"


def test_arnis_phase1_rejects_vector_outside_region_extent(tmp_path: Path) -> None:
    root = _build_lightweight_bundle(tmp_path / "bundle")
    road_path = root / "vectors" / "roads.cmo.json"
    roads = json.loads(road_path.read_text(encoding="utf-8"))
    roads["features"][0]["geometry"]["coordinates"][0] = [2.0, 0.0]
    _write_json(road_path, roads)
    _refresh_artifact_descriptor(root, "artifact:road")

    result = import_arnis_environment_bundle(root)

    assert not result.valid
    assert result.fail_closed
    assert result.rejection_reason == "environment_substrate_arnis_extent_mismatch"


def test_arnis_phase1_import_releases_no_capability_or_projection(
    imported_expected_bundle: ArnisEnvironmentImportResult,
) -> None:
    manifest = imported_expected_bundle.manifest
    assert manifest is not None

    assert manifest.capability_claims == ()
    assert manifest.projection_profiles == ()
    assert all(not item.projection_profile_ids for item in manifest.objects)
    assert all(
        membership.role == "metadata_only"
        for item in manifest.objects
        for membership in item.branch_membership
    )
    assert all(item.provenance["no_held_capability_release"] is True for item in manifest.objects)
    assert manifest.validation_evidence[0]["no_held_capability_release"] is True
