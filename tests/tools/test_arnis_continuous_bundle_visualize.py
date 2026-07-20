from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tools.environment.arnis.visualize import (
    ARNIS_CONTINUOUS_EXPORT_STAGE,
    ARNIS_CONTINUOUS_LINEAGE_CONTRACT,
    ARNIS_CONTINUOUS_REPRESENTATION,
    CONTINUOUS_PREVIEW_TITLE,
    STATIC_SCENE_PREVIEW_TITLE,
    main,
    visualize_continuous_bundle,
)


def _write_bytes(path: Path, data: bytes) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def _write_json(path: Path, value: object) -> tuple[str, int]:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return _write_bytes(path, data)


def _root_lineage() -> dict[str, object]:
    return {
        "contract": ARNIS_CONTINUOUS_LINEAGE_CONTRACT,
        "representation": ARNIS_CONTINUOUS_REPRESENTATION,
        "export_stage": ARNIS_CONTINUOUS_EXPORT_STAGE,
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


def _artifact_lineage(kind: str) -> dict[str, object]:
    lineage: dict[str, object] = {"representation": ARNIS_CONTINUOUS_REPRESENTATION}
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
    else:
        raise AssertionError(f"unsupported synthetic artifact kind {kind!r}")
    return lineage


def _vector_document(feature_class: str, geometry: dict[str, object]) -> dict[str, object]:
    attributes: dict[str, object]
    if feature_class == "road":
        attributes = {
            "vertical_anchor_mode": "terrain_draped",
            "vertical_placement_resolved": True,
            "vertical_anchor_source": "continuous_dem_surface",
            "width_m": 0.6,
            "layer": 0,
            "bridge": False,
            "tunnel": False,
            "covered": False,
        }
    elif feature_class == "building":
        attributes = {
            "vertical_anchor_mode": "terrain_rigid",
            "vertical_placement_resolved": True,
            "vertical_anchor_source": "continuous_dem_foundation",
            "base_offset_m": 1.25,
            "base_offset_source": "synthetic_test",
            "height_m": 12.5,
        }
    elif feature_class == "hydrology":
        attributes = {
            "vertical_anchor_mode": "water_surface_from_dem",
            "vertical_placement_resolved": True,
            "vertical_anchor_source": "continuous_dem_preview_surface",
        }
    else:
        raise AssertionError(feature_class)
    return {
        "schema": "arnis_cmo_features",
        "schema_version": 1,
        "coordinate_frame": "local_enu_m",
        "feature_class": feature_class,
        "features": [
            {
                "feature_id": f"synthetic:{feature_class}:1",
                "geometry": geometry,
                "attributes": attributes,
                "lineage": {
                    "geometry_source_stage": "projected_from_wgs84_f64",
                    "block_projection_applied": False,
                    "measurements": {},
                },
                "provenance": {"source_provider": "synthetic_test"},
            }
        ],
    }


def _build_synthetic_bundle(root: Path) -> Path:
    height, width = 12, 14
    origin = [-3.75, 4.25]
    step = [0.75, -0.75]
    x = origin[0] + np.arange(width, dtype=np.float64) * step[0]
    y = origin[1] + np.arange(height, dtype=np.float64) * step[1]
    mesh_x, mesh_y = np.meshgrid(x, y)
    elevation = (
        101.25
        + 0.19 * mesh_x
        - 0.11 * mesh_y
        + 0.37 * np.sin(mesh_x * 0.55)
        + 0.21 * np.cos(mesh_y * 0.7)
    ).astype("<f4")
    landcover = np.full((height, width), 30, dtype=np.uint8)
    landcover[:, width // 2 :] = 50
    landcover[height // 2 - 1 : height // 2 + 2, :] = 80

    elevation_sha, elevation_size = _write_bytes(
        root / "rasters/elevation.f32le", elevation.tobytes(order="C")
    )
    landcover_sha, landcover_size = _write_bytes(
        root / "rasters/landcover.u8", landcover.tobytes(order="C")
    )
    vector_values = {
        "road": _vector_document(
            "road",
            {
                "type": "LineString",
                "coordinates": [[-2.63, 2.41], [-0.47, 1.13], [2.38, -0.61], [4.27, -2.37]],
            },
        ),
        "building": _vector_document(
            "building",
            {
                "type": "Polygon",
                "coordinates": [
                    [[0.37, 2.63], [1.84, 2.63], [1.84, 1.22], [0.37, 1.22], [0.37, 2.63]]
                ],
            },
        ),
        "hydrology": _vector_document(
            "hydrology",
            {
                "type": "Polygon",
                "coordinates": [
                    [[-3.18, 0.44], [5.12, 0.19], [5.12, -0.72], [-3.18, -0.48], [-3.18, 0.44]]
                ],
            },
        ),
    }
    vector_values["building"]["features"].append(
        {
            "feature_id": "synthetic:building:roof-held",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[-2.41, 3.11], [-1.33, 3.11], [-1.33, 2.27], [-2.41, 2.27], [-2.41, 3.11]]
                ],
            },
            "attributes": {
                "vertical_anchor_mode": "elevated_profile",
                "vertical_placement_resolved": False,
                "vertical_anchor_source": "osm_layer_without_absolute_base",
                "height_m": 3.0,
            },
            "lineage": {
                "geometry_source_stage": "projected_from_wgs84_f64",
                "block_projection_applied": False,
                "measurements": {},
            },
            "provenance": {"source_provider": "synthetic_test"},
        }
    )
    vector_values["road"]["features"].append(
        {
            "feature_id": "synthetic:road:bridge-held",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-2.17, -1.39], [0.61, -1.73], [3.43, -2.11]],
            },
            "attributes": {
                "vertical_anchor_mode": "elevated_profile",
                "vertical_placement_resolved": False,
                "vertical_anchor_source": "osm_bridge_without_deck_elevation",
                "width_m": 6.4,
                "layer": 1,
                "bridge": True,
                "tunnel": False,
                "covered": True,
            },
            "lineage": {
                "geometry_source_stage": "projected_from_wgs84_f64",
                "block_projection_applied": False,
                "measurements": {},
            },
            "provenance": {"source_provider": "synthetic_test"},
        }
    )
    vector_values["road"]["features"].append(
        {
            "feature_id": "synthetic:road:covered-resolved",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-1.91, 3.19], [0.83, 2.87], [3.61, 2.53]],
            },
            "attributes": {
                "vertical_anchor_mode": "terrain_draped",
                "vertical_placement_resolved": True,
                "vertical_anchor_source": "continuous_dem_draped_covered_road_geometry",
                "width_m": 0.4,
                "layer": 0,
                "bridge": False,
                "tunnel": False,
                "covered": True,
            },
            "lineage": {
                "geometry_source_stage": "projected_from_wgs84_f64",
                "block_projection_applied": False,
                "measurements": {},
            },
            "provenance": {"source_provider": "synthetic_test"},
        }
    )
    vector_values["road"]["features"].append(
        {
            "feature_id": "synthetic:road:positive-layer-building-passage-held",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-2.29, -2.89], [0.49, -3.13], [3.17, -3.41]],
            },
            "attributes": {
                "vertical_anchor_mode": "elevated_profile",
                "vertical_placement_resolved": False,
                "vertical_anchor_source": "positive_layer_requires_metric_elevated_profile",
                "width_m": 1.1,
                "layer": 1,
                "bridge": False,
                "tunnel": True,
                "covered": False,
            },
            "lineage": {
                "geometry_source_stage": "projected_from_wgs84_f64",
                "block_projection_applied": False,
                "measurements": {},
            },
            "provenance": {"source_provider": "synthetic_test"},
        }
    )
    artifacts: list[dict[str, object]] = [
        {
            "artifact_id": "artifact:elevation",
            "kind": "elevation_raster",
            "path": "rasters/elevation.f32le",
            "sha256": elevation_sha,
            "byte_length": elevation_size,
            "media_type": "application/vnd.arnis-cmo.raster-f32le",
            "dtype": "float32_le",
            "shape": [height, width],
            "metadata": {
                "origin_xy_m": origin,
                "step_xy_m": step,
                "units": "m",
                "processing_stage": "postprocess_meters_pre_minecraft_scale",
                "minecraft_scaling_applied": False,
                "lineage": _artifact_lineage("elevation_raster"),
            },
        },
        {
            "artifact_id": "artifact:landcover",
            "kind": "landcover_raster",
            "path": "rasters/landcover.u8",
            "sha256": landcover_sha,
            "byte_length": landcover_size,
            "media_type": "application/vnd.arnis-cmo.raster-u8",
            "dtype": "uint8",
            "shape": [height, width],
            "metadata": {
                "origin_xy_m": origin,
                "step_xy_m": step,
                "lineage": _artifact_lineage("landcover_raster"),
            },
        },
    ]
    for feature_class, value in vector_values.items():
        path = root / f"vectors/{feature_class}.json"
        digest, byte_length = _write_json(path, value)
        artifacts.append(
            {
                "artifact_id": f"artifact:{feature_class}",
                "kind": "vector_features",
                "path": f"vectors/{feature_class}.json",
                "sha256": digest,
                "byte_length": byte_length,
                "media_type": "application/vnd.arnis-cmo.features+json",
                "feature_class": feature_class,
                "feature_count": len(value["features"]),
                "metadata": {"lineage": _artifact_lineage("vector_features")},
            }
        )
    bundle = {
        "contract_version": "arnis_cmo_bundle.v1",
        "bundle_id": "synthetic:continuous-bundle",
        "coordinate_frame": "local_enu_m",
        "lineage": _root_lineage(),
        "artifacts": artifacts,
    }
    _write_json(root / "bundle.json", bundle)
    return root


def _rewrite_vector_artifact(
    bundle_root: Path,
    feature_class: str,
    document: dict[str, object],
) -> None:
    vector_path = bundle_root / f"vectors/{feature_class}.json"
    digest, byte_length = _write_json(vector_path, document)
    bundle_path = bundle_root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    artifact = next(
        item
        for item in bundle["artifacts"]
        if item.get("kind") == "vector_features" and item.get("feature_class") == feature_class
    )
    artifact["sha256"] = digest
    artifact["byte_length"] = byte_length
    _write_json(bundle_path, bundle)


def test_synthetic_continuous_bundle_writes_preview_and_metrics(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    bundle_root = _build_synthetic_bundle(tmp_path / "bundle")
    output_dir = tmp_path / "preview"

    result = visualize_continuous_bundle(
        bundle_root,
        output_dir,
        vertical_exaggeration=6.0,
    )

    image_path = output_dir / "continuous_field_overlay.png"
    metrics_path = output_dir / "continuous_field_metrics.json"
    static_geometry_path = output_dir / "static_scene_geometry.json"
    static_preview_path = output_dir / "static_scene_preview.png"
    assert result["image_path"] == image_path
    assert result["metrics_path"] == metrics_path
    assert result["static_geometry_path"] == static_geometry_path
    assert result["static_preview_path"] == static_preview_path
    assert image_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert image_path.stat().st_size > 10_000
    assert static_preview_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert static_preview_path.stat().st_size > 10_000

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["visualization"]["title"] == CONTINUOUS_PREVIEW_TITLE
    assert metrics["visualization"]["vertical_exaggeration"] == 6.0
    assert metrics["visualization"]["draped_vector_path_count"] == 7
    assert metrics["lineage_flags"]["accepted"] is True
    assert metrics["lineage_flags"]["contract"] == ARNIS_CONTINUOUS_LINEAGE_CONTRACT
    assert metrics["lineage_flags"]["representation"] == ARNIS_CONTINUOUS_REPRESENTATION
    assert metrics["lineage_flags"]["export_stage"] == ARNIS_CONTINUOUS_EXPORT_STAGE
    assert metrics["lineage_flags"]["geometry"]["block_projection_applied"] is False
    assert metrics["lineage_flags"]["elevation"]["minecraft_y_transform_applied"] is False
    assert metrics["lineage_flags"]["landcover"]["block_palette_roundtrip"] is False
    assert metrics["dem"]["finite_ratio"] == 1.0
    assert metrics["dem"]["min_m"] < metrics["dem"]["max_m"]
    assert metrics["landcover"]["render_interpolation"] == "nearest_categorical"
    assert metrics["landcover"]["numeric_interpolation_applied"] is False
    for feature_class in ("road", "building", "hydrology"):
        coordinate_metrics = metrics["coordinate_metrics"][feature_class]
        assert coordinate_metrics["integer_x_ratio"] == 0.0
        assert coordinate_metrics["integer_y_ratio"] == 0.0
        assert coordinate_metrics["nearest_1m_grid_rmse_m"] > 0.1

    static_scene = json.loads(static_geometry_path.read_text(encoding="utf-8"))
    assert static_scene["contract_version"] == "cmo.static_scene_geometry.v1"
    assert static_scene["release"]["state"] == "no_runtime_consumer_release"
    assert static_scene["release"]["runtime_authority"] is False
    assert static_scene["source_bundle"]["bundle_id"] == "synthetic:continuous-bundle"
    assert static_scene["source_bundle"]["elevation_artifact"]["sha256"]
    assert set(static_scene["source_bundle"]["vector_artifacts"]) == {
        "road",
        "building",
        "hydrology",
    }
    assert static_scene["summary"] == {
        "total": 7,
        "resolved": 5,
        "held": 2,
        "by_feature_class": {
            "building": {"total": 2, "resolved": 1, "held": 1},
            "road": {"total": 4, "resolved": 3, "held": 1},
            "hydrology": {"total": 1, "resolved": 1, "held": 0},
        },
    }
    assert metrics["static_scene"]["summary"] == static_scene["summary"]
    assert metrics["static_scene"]["preview_title"] == STATIC_SCENE_PREVIEW_TITLE
    assert metrics["static_scene"]["preview_path"] == "static_scene_preview.png"

    by_id = {item["source_feature_id"]: item for item in static_scene["objects"]}
    building = by_id["synthetic:building:1"]
    source_building = json.loads(
        (bundle_root / "vectors/building.json").read_text(encoding="utf-8")
    )["features"][0]
    assert building["status"] == "resolved"
    assert building["source_geometry_xy"] == source_building["geometry"]
    assert building["static_geometry"]["footprint_geometry_xy"] == source_building["geometry"]
    assert building["static_geometry"]["xy_interpolation_applied"] is False
    assert building["static_geometry"]["height_m"] == 12.5
    assert building["static_geometry"]["foundation"]["sample_count"] == 5
    assert building["static_geometry"]["foundation"]["relief_m"] >= 0.0

    road = by_id["synthetic:road:1"]
    source_road = json.loads((bundle_root / "vectors/road.json").read_text(encoding="utf-8"))[
        "features"
    ][0]
    assert road["status"] == "resolved"
    assert road["source_geometry_xy"] == source_road["geometry"]
    assert road["static_geometry"]["centerline_geometry_xy"] == source_road["geometry"]
    assert road["static_geometry"]["centerline_xy_interpolation_applied"] is False
    assert len(road["static_geometry"]["corridor_segments"]) == 3
    assert all(
        len(segment["polygon_xyz"]) == 4 for segment in road["static_geometry"]["corridor_segments"]
    )
    assert road["static_geometry"]["corridor_clipped_to_dem_extent"] is False
    assert road["static_geometry"]["clipped_segment_count"] == 0
    assert road["static_geometry"]["skipped_segment_count"] == 0
    assert by_id["synthetic:building:roof-held"]["status"] == "held"
    assert by_id["synthetic:building:roof-held"]["static_geometry"] is None
    bridge = by_id["synthetic:road:bridge-held"]
    assert bridge["status"] == "resolved"
    assert bridge["anchor"]["covered"] is True
    bridge_geometry = bridge["static_geometry"]
    assert bridge_geometry["kind"] == "abutment_interpolated_deck"
    assert bridge_geometry["deck_profile"]["method"] == (
        "linear_interpolation_between_abutment_dem_anchors"
    )
    assert bridge_geometry["deck_profile"]["deck_elevation_measured"] is False
    assert len(bridge_geometry["deck_profile"]["abutments"]) == 1
    bridge_abutment = bridge_geometry["deck_profile"]["abutments"][0]
    assert bridge_abutment["span_length_m"] > 0.0
    assert bridge_geometry["corridor_clipped_to_dem_extent"] is False
    assert len(bridge_geometry["corridor_segments"]) == 2
    deck_z = [point[2] for part in bridge_geometry["centerline_parts_xyz"] for point in part]
    assert deck_z[0] == pytest.approx(bridge_abutment["start_elevation_m"])
    assert deck_z[-1] == pytest.approx(bridge_abutment["end_elevation_m"])
    covered = by_id["synthetic:road:covered-resolved"]
    assert covered["status"] == "resolved"
    assert covered["anchor"]["covered"] is True
    assert covered["static_geometry"]["kind"] == "terrain_draped_corridor"
    building_passage = by_id["synthetic:road:positive-layer-building-passage-held"]
    assert building_passage["status"] == "held"
    assert building_passage["hold_reason"] == "elevated_profile_unresolved"
    assert building_passage["anchor"]["layer"] == 1
    assert building_passage["anchor"]["tunnel"] is True
    assert building_passage["static_geometry"] is None


def test_boundary_road_corridor_is_clipped_without_changing_source_centerline(
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    bundle_root = _build_synthetic_bundle(tmp_path / "bundle")
    road_path = bundle_root / "vectors/road.json"
    road_document = json.loads(road_path.read_text(encoding="utf-8"))
    boundary_geometry = {
        "type": "LineString",
        "coordinates": [[-3.75, 4.0], [0.23, 4.0], [5.9, 4.0]],
    }
    road_document["features"][0]["geometry"] = boundary_geometry
    road_document["features"][0]["attributes"]["width_m"] = 1.5
    _rewrite_vector_artifact(bundle_root, "road", road_document)
    output_dir = tmp_path / "preview"

    visualize_continuous_bundle(bundle_root, output_dir, vertical_exaggeration=2.0)

    static_scene = json.loads(
        (output_dir / "static_scene_geometry.json").read_text(encoding="utf-8")
    )
    boundary_road = next(
        item for item in static_scene["objects"] if item["source_feature_id"] == "synthetic:road:1"
    )
    assert boundary_road["status"] == "resolved"
    assert boundary_road["source_geometry_xy"] == boundary_geometry
    geometry = boundary_road["static_geometry"]
    assert geometry["centerline_geometry_xy"] == boundary_geometry
    assert geometry["centerline_xy_interpolation_applied"] is False
    assert geometry["corridor_clipped_to_dem_extent"] is True
    assert geometry["clipped_segment_count"] == 2
    assert geometry["skipped_segment_count"] == 0
    assert len(geometry["corridor_segments"]) == 2
    minimum_x, maximum_x, minimum_y, maximum_y = geometry["dem_clip_extent_xy_m"]
    for segment in geometry["corridor_segments"]:
        assert segment["clipped_to_dem_extent"] is True
        assert len(segment["polygon_xyz"]) >= 3
        for x, y, z in segment["polygon_xyz"]:
            assert minimum_x <= x <= maximum_x
            assert minimum_y <= y <= maximum_y
            assert np.isfinite(z)


def test_cli_fails_closed_without_root_lineage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bundle_root = _build_synthetic_bundle(tmp_path / "bundle")
    bundle_path = bundle_root / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    del bundle["lineage"]
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    output_dir = tmp_path / "preview"

    assert main(["--bundle", str(bundle_root), "--output-dir", str(output_dir)]) == 1

    captured = capsys.readouterr()
    assert "requires fail-closed lineage" in captured.err
    assert not (output_dir / "continuous_field_overlay.png").exists()
    assert not (output_dir / "continuous_field_metrics.json").exists()
    assert not (output_dir / "static_scene_geometry.json").exists()
    assert not (output_dir / "static_scene_preview.png").exists()


@pytest.mark.parametrize("missing_attribute", ["vertical_anchor_source", "covered"])
def test_cli_fails_closed_when_required_static_placement_metadata_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    missing_attribute: str,
) -> None:
    bundle_root = _build_synthetic_bundle(tmp_path / "bundle")
    road_path = bundle_root / "vectors/road.json"
    road = json.loads(road_path.read_text(encoding="utf-8"))
    del road["features"][0]["attributes"][missing_attribute]
    _rewrite_vector_artifact(bundle_root, "road", road)
    output_dir = tmp_path / "preview"

    assert main(["--bundle", str(bundle_root), "--output-dir", str(output_dir)]) == 1

    captured = capsys.readouterr()
    assert "static scene derivation failed closed" in captured.err
    assert missing_attribute in captured.err
    assert not output_dir.exists()


@pytest.mark.parametrize(
    ("feature_class", "attribute", "invalid_value", "expected_error"),
    [
        ("building", "base_offset_m", -0.25, "base_offset_m must be non-negative"),
        ("road", "layer", 0.5, "layer must be a finite integer"),
    ],
)
def test_cli_fails_closed_for_invalid_resolved_vertical_measurements(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    feature_class: str,
    attribute: str,
    invalid_value: object,
    expected_error: str,
) -> None:
    bundle_root = _build_synthetic_bundle(tmp_path / "bundle")
    vector_path = bundle_root / f"vectors/{feature_class}.json"
    document = json.loads(vector_path.read_text(encoding="utf-8"))
    document["features"][0]["attributes"][attribute] = invalid_value
    _rewrite_vector_artifact(bundle_root, feature_class, document)
    output_dir = tmp_path / "preview"

    assert main(["--bundle", str(bundle_root), "--output-dir", str(output_dir)]) == 1

    captured = capsys.readouterr()
    assert "static scene derivation failed closed" in captured.err
    assert expected_error in captured.err
    assert not output_dir.exists()
