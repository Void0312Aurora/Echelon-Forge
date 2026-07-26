from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from ..catalog import (
    EnvironmentCatalogDescriptor,
    validate_environment_catalog_admission,
    validate_environment_catalog_descriptors,
)
from ..components import (
    EnvironmentComponentDescriptor,
    default_branch_registry,
    default_component_registry,
    default_layer_registry,
)
from ..generator import (
    EnvironmentGeneratorEvidenceRef,
    EnvironmentGeneratorRequest,
    EnvironmentTileScheme,
    validate_environment_generator_request,
)
from ..manifest import (
    EnvironmentBranchMembership,
    EnvironmentComponent,
    EnvironmentGenerationMetadata,
    EnvironmentGeometry,
    EnvironmentManifest,
    EnvironmentObject,
    EnvironmentRegionExtent,
)
from ..validation import validate_environment_manifest


ARNIS_CMO_BUNDLE_CONTRACT_VERSION = "arnis_cmo_bundle.v1"
ARNIS_CMO_IMPORT_CONTRACT_VERSION = "environment_substrate.arnis_import.phase1.v1"
ARNIS_CONTINUOUS_EXPORTER_PATCH_ID = "0001-cmo-continuous-bundle-export-v1"
ARNIS_CONTINUOUS_PATCH_SHA256 = "26536836d46aa7bc3e03da3449b4c52391f096527ab58f365d5dd4b96b9052ee"

_FEATURE_SCHEMA = "arnis_cmo_features"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_PROJECTION = "arnis_local_scaled_web_mercator_r6371000_normalized_to_local_enu"
_CONTINUOUS_LINEAGE_CONTRACT = "arnis_continuous_metric.v1"
_CONTINUOUS_REPRESENTATION = "continuous_metric_2_5d"
_CONTINUOUS_EXPORT_STAGE = "post_semantic_processing_pre_render_quantization"
_CONTINUOUS_GEOMETRY_SOURCE_STAGE = "projected_from_wgs84_f64"
_CONTINUOUS_ELEVATION_SOURCE_STAGE = "postprocessed_metric_dem"
_CONTINUOUS_LANDCOVER_SOURCE_STAGE = "source_classification_metric_grid"
_CONTINUOUS_PROVENANCE_SOURCE_STAGE = "continuous_bundle_provenance"
_CONTINUOUS_MEASUREMENT_SOURCE_DOMAIN = "metric_semantics_pre_block_conversion"
_CONTINUOUS_SEMANTIC_SOURCE_DOMAIN = "semantic_tags_pre_block_conversion"
_BLOCK_DERIVED_WIDTH_SOURCES = frozenset(
    {
        "arnis_highway_block_range",
        "arnis_waterway_block_default",
    }
)
_BLOCK_DERIVED_HEIGHT_SEMANTICS = frozenset(
    {
        "arnis_bicycle_shed_vertical_extent",
        "arnis_parking_generated_top_offset",
        "arnis_rendered_body_height",
        "arnis_roof_thickness",
        "arnis_shelter_vertical_extent",
    }
)


@dataclass(frozen=True)
class ArnisEnvironmentImportResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]
    manifest: EnvironmentManifest | None = None
    catalog_descriptors: tuple[EnvironmentCatalogDescriptor, ...] = ()
    bundle_digest_sha256: str = ""


class _ImportFailure(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _failure(
    code: str,
    message: str,
    *,
    bundle_digest_sha256: str = "",
) -> ArnisEnvironmentImportResult:
    return ArnisEnvironmentImportResult(
        valid=False,
        fail_closed=True,
        rejection_reason=code,
        errors=(message,),
        bundle_digest_sha256=bundle_digest_sha256,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return _sha256_bytes(data), len(data)


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _ImportFailure(code, f"failed to read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise _ImportFailure(code, f"{path.name} must contain a JSON object")
    return value


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _positive_number(value: Any) -> bool:
    return _finite_number(value) and float(value) > 0.0


def _strict_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _integer(value: Any) -> bool:
    return type(value) is int


def _lineage_required(message: str) -> None:
    raise _ImportFailure(
        "environment_substrate_arnis_continuous_lineage_required",
        message,
    )


def _block_derived(message: str) -> None:
    raise _ImportFailure(
        "environment_substrate_arnis_block_derived_rejected",
        message,
    )


def _lineage_mismatch(message: str) -> None:
    raise _ImportFailure(
        "environment_substrate_arnis_lineage_mismatch",
        message,
    )


def _required_lineage_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _lineage_required(f"{label} continuous lineage object is required")
    return value


def _require_lineage_value(
    payload: dict[str, Any],
    key: str,
    expected: Any,
    label: str,
    *,
    block_derived_on_mismatch: bool = True,
) -> None:
    if key not in payload:
        _lineage_required(f"{label} continuous lineage field {key!r} is required")
    if payload[key] != expected:
        message = (
            f"{label} continuous lineage field {key!r} must be {expected!r}, "
            f"got {payload[key]!r}"
        )
        if block_derived_on_mismatch:
            _block_derived(message)
        _lineage_mismatch(message)


def _validate_root_continuous_lineage(value: Any) -> dict[str, Any]:
    lineage = _required_lineage_object(value, "bundle")
    _require_lineage_value(
        lineage,
        "contract",
        _CONTINUOUS_LINEAGE_CONTRACT,
        "bundle",
        block_derived_on_mismatch=False,
    )
    _require_lineage_value(
        lineage,
        "representation",
        _CONTINUOUS_REPRESENTATION,
        "bundle",
    )
    _require_lineage_value(
        lineage,
        "export_stage",
        _CONTINUOUS_EXPORT_STAGE,
        "bundle",
    )
    for key in (
        "minecraft_world_read",
        "anvil_region_read",
        "voxelization_applied",
    ):
        _require_lineage_value(lineage, key, False, "bundle")

    geometry = _required_lineage_object(lineage.get("geometry"), "bundle geometry")
    _require_lineage_value(
        geometry,
        "source_stage",
        _CONTINUOUS_GEOMETRY_SOURCE_STAGE,
        "bundle geometry",
    )
    _require_lineage_value(
        geometry,
        "storage",
        "json_float64",
        "bundle geometry",
    )
    _require_lineage_value(
        geometry,
        "quantization_step_m",
        None,
        "bundle geometry",
    )
    _require_lineage_value(
        geometry,
        "block_projection_applied",
        False,
        "bundle geometry",
    )

    elevation = _required_lineage_object(lineage.get("elevation"), "bundle elevation")
    _require_lineage_value(
        elevation,
        "source_stage",
        _CONTINUOUS_ELEVATION_SOURCE_STAGE,
        "bundle elevation",
    )
    _require_lineage_value(
        elevation,
        "storage",
        "float32_le",
        "bundle elevation",
    )
    _require_lineage_value(
        elevation,
        "vertical_quantization_step_m",
        None,
        "bundle elevation",
    )
    for key in ("minecraft_y_transform_applied", "minecraft_y_roundtrip"):
        _require_lineage_value(elevation, key, False, "bundle elevation")

    landcover = _required_lineage_object(lineage.get("landcover"), "bundle landcover")
    _require_lineage_value(
        landcover,
        "source_stage",
        _CONTINUOUS_LANDCOVER_SOURCE_STAGE,
        "bundle landcover",
    )
    _require_lineage_value(
        landcover,
        "block_palette_roundtrip",
        False,
        "bundle landcover",
    )
    return lineage


def _validate_artifact_continuous_lineage(artifact: dict[str, Any]) -> dict[str, Any]:
    artifact_id = str(artifact.get("artifact_id") or "artifact")
    metadata = artifact.get("metadata")
    if not isinstance(metadata, dict):
        _lineage_required(f"artifact {artifact_id} metadata is required for lineage")
    lineage = _required_lineage_object(
        metadata.get("lineage"),
        f"artifact {artifact_id}",
    )
    _require_lineage_value(
        lineage,
        "representation",
        _CONTINUOUS_REPRESENTATION,
        f"artifact {artifact_id}",
    )

    kind = artifact.get("kind")
    if kind == "vector_features":
        expected = {
            "source_stage": _CONTINUOUS_GEOMETRY_SOURCE_STAGE,
            "storage": "json_float64",
            "quantization_step_m": None,
            "block_projection_applied": False,
        }
    elif kind == "elevation_raster":
        expected = {
            "source_stage": _CONTINUOUS_ELEVATION_SOURCE_STAGE,
            "storage": "float32_le",
            "vertical_quantization_step_m": None,
            "minecraft_y_transform_applied": False,
            "minecraft_y_roundtrip": False,
        }
    elif kind == "landcover_raster":
        expected = {
            "source_stage": _CONTINUOUS_LANDCOVER_SOURCE_STAGE,
            "storage": "uint8",
            "block_palette_roundtrip": False,
        }
    elif kind == "provenance":
        expected = {
            "source_stage": _CONTINUOUS_PROVENANCE_SOURCE_STAGE,
            "storage": "json",
            "block_derived": False,
        }
    else:
        _lineage_mismatch(f"artifact {artifact_id} has unsupported kind {kind!r}")
        raise AssertionError("unreachable")

    for key, expected_value in expected.items():
        _require_lineage_value(
            lineage,
            key,
            expected_value,
            f"artifact {artifact_id}",
        )
    return lineage


def _validate_feature_continuous_lineage(
    feature: dict[str, Any],
    feature_class: str,
    feature_id: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    lineage = _required_lineage_object(
        feature.get("lineage"),
        f"feature {feature_id}",
    )
    _require_lineage_value(
        lineage,
        "geometry_source_stage",
        _CONTINUOUS_GEOMETRY_SOURCE_STAGE,
        f"feature {feature_id}",
    )
    _require_lineage_value(
        lineage,
        "block_projection_applied",
        False,
        f"feature {feature_id}",
    )
    if feature_class == "road" and attributes.get("width_source") in _BLOCK_DERIVED_WIDTH_SOURCES:
        _block_derived(f"road feature {feature_id} width source is block-derived")
    if (
        feature_class == "building"
        and attributes.get("height_semantics") in _BLOCK_DERIVED_HEIGHT_SEMANTICS
    ):
        _block_derived(f"building feature {feature_id} height semantics are block-derived")
    if (
        feature_class == "hydrology"
        and "width_m" in attributes
        and attributes.get("width_source") in _BLOCK_DERIVED_WIDTH_SOURCES
    ):
        _block_derived(f"hydrology feature {feature_id} width source is block-derived")
    measurements = _required_lineage_object(
        lineage.get("measurements"),
        f"feature {feature_id} measurements",
    )
    metric_measurements = {
        "road": {"width_m"},
        "building": {"height_m"},
        "hydrology": {"width_m"} if "width_m" in attributes else set(),
    }[feature_class]
    semantic_measurements = {
        "vertical_anchor_mode",
        "vertical_placement_resolved",
        "vertical_anchor_source",
    }
    if feature_class == "road":
        semantic_measurements.update(("layer", "bridge", "tunnel", "covered"))
    if feature_class == "building" and "layer" in attributes:
        semantic_measurements.add("layer")
    if feature_class == "building" and "base_offset_m" in attributes:
        metric_measurements.add("base_offset_m")
        semantic_measurements.add("base_offset_source")
    expected_measurements = metric_measurements | semantic_measurements
    if set(measurements) != expected_measurements:
        _lineage_mismatch(
            f"feature {feature_id} measurement lineage must cover "
            f"{sorted(expected_measurements)}, got {sorted(measurements)}"
        )
    for measurement_name in sorted(expected_measurements):
        measurement = _required_lineage_object(
            measurements.get(measurement_name),
            f"feature {feature_id} measurement {measurement_name}",
        )
        expected_domain = (
            _CONTINUOUS_MEASUREMENT_SOURCE_DOMAIN
            if measurement_name in metric_measurements
            else _CONTINUOUS_SEMANTIC_SOURCE_DOMAIN
        )
        _require_lineage_value(
            measurement,
            "source_domain",
            expected_domain,
            f"feature {feature_id} measurement {measurement_name}",
        )
        _require_lineage_value(
            measurement,
            "derived_from_block_count",
            False,
            f"feature {feature_id} measurement {measurement_name}",
        )
        _require_lineage_value(
            measurement,
            "derived_from_block_range",
            False,
            f"feature {feature_id} measurement {measurement_name}",
        )
        expected_source_semantics = {
            "width_m": attributes.get("width_source"),
            "height_m": attributes.get("height_source"),
            "base_offset_m": attributes.get("base_offset_source"),
            "base_offset_source": attributes.get("base_offset_source"),
            "vertical_anchor_mode": attributes.get("vertical_anchor_source"),
            "vertical_placement_resolved": attributes.get("vertical_anchor_source"),
            "vertical_anchor_source": attributes.get("vertical_anchor_source"),
        }.get(measurement_name)
        if expected_source_semantics is not None:
            _require_lineage_value(
                measurement,
                "source_semantics",
                expected_source_semantics,
                f"feature {feature_id} measurement {measurement_name}",
                block_derived_on_mismatch=False,
            )
        elif (
            not isinstance(measurement.get("source_semantics"), str)
            or not measurement["source_semantics"].strip()
        ):
            _lineage_required(
                f"feature {feature_id} measurement {measurement_name} requires "
                "non-empty source_semantics"
            )

    return lineage


def _safe_artifact_path(bundle_root: Path, relative_path: Any) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            "artifact path must be a non-empty string",
        )
    if "\\" in relative_path:
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            f"artifact path is not portable: {relative_path!r}",
        )
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts:
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            f"artifact path escapes the bundle: {relative_path!r}",
        )
    candidate = bundle_root.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            f"artifact does not exist: {relative_path!r}",
        ) from exc
    root = bundle_root.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            f"artifact resolves outside the bundle: {relative_path!r}",
        )
    if not resolved.is_file():
        raise _ImportFailure(
            "environment_substrate_arnis_artifact_path_invalid",
            f"artifact is not a regular file: {relative_path!r}",
        )
    return resolved


def _extent_from_bundle(bundle: dict[str, Any]) -> EnvironmentRegionExtent:
    extent = bundle.get("region_extent")
    if not isinstance(extent, dict):
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            "region_extent must be an object",
        )
    keys = ("min_x", "min_y", "max_x", "max_y")
    if not all(_finite_number(extent.get(key)) for key in keys):
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            "region_extent coordinates must be finite",
        )
    result = EnvironmentRegionExtent(*(float(extent[key]) for key in keys))
    if result.max_x <= result.min_x or result.max_y <= result.min_y:
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            "region_extent must have positive width and height",
        )
    return result


def _artifact_inventory(
    bundle_root: Path,
    bundle: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    artifacts = bundle.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            "bundle artifacts must be a non-empty list",
        )
    by_id: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    seen_paths: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                "artifact descriptors must be objects",
            )
        artifact_id = str(artifact.get("artifact_id") or "").strip()
        relative_path = str(artifact.get("path") or "").strip()
        expected_sha = str(artifact.get("sha256") or "").strip()
        if not artifact_id or artifact_id in by_id:
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                f"artifact ID is missing or duplicated: {artifact_id!r}",
            )
        if relative_path in seen_paths:
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                f"artifact path is duplicated: {relative_path!r}",
            )
        if not _HEX64.fullmatch(expected_sha):
            raise _ImportFailure(
                "environment_substrate_arnis_checksum_mismatch",
                f"artifact {artifact_id} has an invalid SHA-256",
            )
        artifact_path = _safe_artifact_path(bundle_root, relative_path)
        actual_sha, actual_size = _sha256_file(artifact_path)
        if actual_sha != expected_sha:
            raise _ImportFailure(
                "environment_substrate_arnis_checksum_mismatch",
                f"artifact checksum mismatch: {relative_path}",
            )
        try:
            expected_size = int(artifact.get("byte_length"))
        except (TypeError, ValueError) as exc:
            raise _ImportFailure(
                "environment_substrate_arnis_checksum_mismatch",
                f"artifact byte length is invalid: {relative_path}",
            ) from exc
        if expected_size != actual_size:
            raise _ImportFailure(
                "environment_substrate_arnis_checksum_mismatch",
                f"artifact byte length mismatch: {relative_path}",
            )
        by_id[artifact_id] = artifact
        paths[artifact_id] = artifact_path
        seen_paths.add(relative_path)
    return by_id, paths


def _artifact_by_kind(
    artifacts: Iterable[dict[str, Any]],
    kind: str,
) -> dict[str, Any]:
    matches = [artifact for artifact in artifacts if artifact.get("kind") == kind]
    if len(matches) != 1:
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            f"bundle requires exactly one {kind} artifact",
        )
    return matches[0]


def _vector_artifact(
    artifacts: Iterable[dict[str, Any]],
    feature_class: str,
) -> dict[str, Any]:
    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("kind") == "vector_features"
        and artifact.get("feature_class") == feature_class
    ]
    if len(matches) != 1:
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            f"bundle requires exactly one {feature_class} vector artifact",
        )
    return matches[0]


def _validate_raster(
    artifact: dict[str, Any],
    path: Path,
    extent: EnvironmentRegionExtent,
    *,
    expected_dtype: str,
) -> None:
    shape = artifact.get("shape")
    if (
        not isinstance(shape, list)
        or len(shape) != 2
        or any(type(value) is not int or value <= 1 for value in shape)
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} has invalid raster shape",
        )
    dtype = artifact.get("dtype")
    if dtype != expected_dtype:
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} requires dtype {expected_dtype}",
        )
    bytes_per_sample = {"float32_le": 4, "uint8": 1}.get(dtype)
    if bytes_per_sample is None:
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} has unsupported dtype {dtype!r}",
        )
    if int(artifact["byte_length"]) != shape[0] * shape[1] * bytes_per_sample:
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} byte length does not match shape",
        )
    metadata = artifact.get("metadata")
    if not isinstance(metadata, dict):
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} metadata is required",
        )
    origin = metadata.get("origin_xy_m")
    step = metadata.get("step_xy_m")
    if (
        not isinstance(origin, list)
        or len(origin) != 2
        or not isinstance(step, list)
        or len(step) != 2
        or not all(_finite_number(value) for value in (*origin, *step))
        or float(step[0]) <= 0.0
        or float(step[1]) >= 0.0
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_raster_metadata_invalid",
            f"artifact {artifact.get('artifact_id')} has invalid grid origin or step",
        )
    end_x = float(origin[0]) + float(step[0]) * (shape[1] - 1)
    end_y = float(origin[1]) + float(step[1]) * (shape[0] - 1)
    tolerance = 1.0e-6 * max(
        1.0,
        extent.max_x - extent.min_x,
        extent.max_y - extent.min_y,
    )
    expected = (extent.min_x, extent.max_y, extent.max_x, extent.min_y)
    actual = (float(origin[0]), float(origin[1]), end_x, end_y)
    if any(not math.isclose(a, b, abs_tol=tolerance) for a, b in zip(actual, expected)):
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            f"artifact {artifact.get('artifact_id')} grid does not cover region_extent",
        )
    data = path.read_bytes()
    if dtype == "float32_le":
        source_provider = str(metadata.get("source_provider") or "").strip()
        contributing_sources = metadata.get("contributing_sources")
        if (
            not source_provider
            or not isinstance(contributing_sources, dict)
            or set(contributing_sources) != {source_provider}
            or type(contributing_sources.get(source_provider)) is not int
            or contributing_sources[source_provider] <= 0
            or metadata.get("missing_source_units") != 0
        ):
            raise _ImportFailure(
                "environment_substrate_arnis_raster_metadata_invalid",
                f"artifact {artifact.get('artifact_id')} requires one exclusive elevation source",
            )
        if any(not math.isfinite(value[0]) for value in struct.iter_unpack("<f", data)):
            raise _ImportFailure(
                "environment_substrate_arnis_raster_metadata_invalid",
                f"artifact {artifact.get('artifact_id')} contains non-finite elevation values",
            )
    else:
        legend = metadata.get("class_legend")
        if not isinstance(legend, dict):
            raise _ImportFailure(
                "environment_substrate_arnis_raster_metadata_invalid",
                f"artifact {artifact.get('artifact_id')} requires a class legend",
            )
        try:
            admitted_classes = {int(value) for value in legend}
        except (TypeError, ValueError) as exc:
            raise _ImportFailure(
                "environment_substrate_arnis_raster_metadata_invalid",
                f"artifact {artifact.get('artifact_id')} has invalid class legend keys",
            ) from exc
        unknown_classes = sorted(set(data) - admitted_classes)
        if unknown_classes:
            raise _ImportFailure(
                "environment_substrate_arnis_raster_metadata_invalid",
                f"artifact {artifact.get('artifact_id')} contains classes absent from its legend: {unknown_classes}",
            )


def _point(value: Any, extent: EnvironmentRegionExtent) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(_finite_number(item) for item in value)
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            "vector coordinates must contain finite [x, y] points",
        )
    x, y = float(value[0]), float(value[1])
    tolerance = 1.0e-7
    if not (
        extent.min_x - tolerance <= x <= extent.max_x + tolerance
        and extent.min_y - tolerance <= y <= extent.max_y + tolerance
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            f"vector point [{x}, {y}] is outside region_extent",
        )
    return [x, y]


def _deduplicate_consecutive(points: Iterable[list[float]]) -> list[list[float]]:
    result: list[list[float]] = []
    for point in points:
        if not result or point != result[-1]:
            result.append(point)
    return result


def _signed_area(points: list[list[float]]) -> float:
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def _normalize_ring(
    value: Any,
    extent: EnvironmentRegionExtent,
    *,
    clockwise: bool,
) -> list[list[float]]:
    if not isinstance(value, list):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            "polygon rings must be lists",
        )
    points = _deduplicate_consecutive(_point(point, extent) for point in value)
    if len(points) >= 2 and points[0] == points[-1]:
        points.pop()
    if len({(point[0], point[1]) for point in points}) < 3:
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            "polygon rings require at least three distinct points",
        )
    area = _signed_area(points)
    if math.isclose(area, 0.0, abs_tol=1.0e-9):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            "polygon ring area must be non-zero",
        )
    if clockwise == (area > 0.0):
        points.reverse()
    return points


def _geometry(
    raw_geometry: Any,
    extent: EnvironmentRegionExtent,
) -> tuple[EnvironmentGeometry, str]:
    if not isinstance(raw_geometry, dict):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            "feature geometry must be an object",
        )
    geometry_type = raw_geometry.get("type")
    coordinates = raw_geometry.get("coordinates")
    if geometry_type == "LineString":
        if not isinstance(coordinates, list):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                "LineString coordinates must be a list",
            )
        points = _deduplicate_consecutive(_point(point, extent) for point in coordinates)
        if len({(point[0], point[1]) for point in points}) < 2:
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                "LineString requires at least two distinct points",
            )
        return EnvironmentGeometry("line", {"points": points}), "line"
    if geometry_type == "Polygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                "Polygon coordinates require at least one ring",
            )
        outer = _normalize_ring(coordinates[0], extent, clockwise=False)
        holes = [_normalize_ring(ring, extent, clockwise=True) for ring in coordinates[1:]]
        payload: dict[str, Any] = {"points": outer}
        if holes:
            payload["holes"] = holes
        return EnvironmentGeometry("polygon", payload), "polygon"
    raise _ImportFailure(
        "environment_substrate_arnis_vector_invalid",
        f"unsupported feature geometry type {geometry_type!r}",
    )


def _load_feature_file(
    path: Path,
    artifact: dict[str, Any],
    extent: EnvironmentRegionExtent,
) -> list[dict[str, Any]]:
    payload = _load_json(path, code="environment_substrate_arnis_vector_invalid")
    feature_class = artifact.get("feature_class")
    if (
        payload.get("schema") != _FEATURE_SCHEMA
        or payload.get("schema_version") != 1
        or payload.get("coordinate_frame") != "local_enu_m"
        or payload.get("feature_class") != feature_class
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            f"vector artifact {artifact.get('path')} has an incompatible header",
        )
    features = payload.get("features")
    if not isinstance(features, list):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            f"vector artifact {artifact.get('path')} features must be a list",
        )
    if artifact.get("feature_count") != len(features):
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            f"vector artifact {artifact.get('path')} feature count mismatch",
        )
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                "features must be objects",
            )
        feature_id = str(feature.get("feature_id") or "").strip()
        if not feature_id or feature_id in seen_ids:
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                f"feature ID is missing or duplicated: {feature_id!r}",
            )
        geometry, geometry_type = _geometry(feature.get("geometry"), extent)
        attributes = feature.get("attributes")
        provenance = feature.get("provenance")
        if not isinstance(attributes, dict) or not isinstance(provenance, dict):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                f"feature {feature_id} requires attributes and provenance objects",
            )
        lineage = _validate_feature_continuous_lineage(
            feature,
            str(feature_class),
            feature_id,
            attributes,
        )
        normalized.append(
            {
                "feature_id": feature_id,
                "geometry": geometry,
                "geometry_type": geometry_type,
                "attributes": attributes,
                "provenance": provenance,
                "lineage": lineage,
            }
        )
        seen_ids.add(feature_id)
    return sorted(normalized, key=lambda feature: feature["feature_id"])


def _component_registries() -> tuple[tuple[Any, ...], tuple[Any, ...], tuple[Any, ...]]:
    components = default_component_registry() + (
        EnvironmentComponentDescriptor(
            "elevation_field",
            required_attributes=(
                "artifact_ref",
                "checksum_sha256",
                "dtype",
                "shape",
                "resolution_m",
                "units",
                "vertical_datum",
                "uncertainty_status",
            ),
            consumer_tags=("terrain_manifest",),
            minimum_realism_grade="G1",
        ),
        EnvironmentComponentDescriptor(
            "landcover_field",
            required_attributes=(
                "artifact_ref",
                "checksum_sha256",
                "dtype",
                "shape",
                "resolution_m",
                "classification_scheme",
            ),
            consumer_tags=("terrain_manifest",),
            minimum_realism_grade="G1",
        ),
    )
    branches = tuple(
        replace(
            branch,
            allowed_components=tuple(branch.allowed_components)
            + ("elevation_field", "landcover_field"),
        )
        if branch.branch_id == "terrain"
        else branch
        for branch in default_branch_registry()
    )
    return branches, components, default_layer_registry()


def _catalogs() -> tuple[EnvironmentCatalogDescriptor, ...]:
    terrain_membership = (EnvironmentBranchMembership(branch_id="terrain", role="metadata_only"),)
    hydrology_membership = (
        EnvironmentBranchMembership(branch_id="hydrology", role="metadata_only"),
    )
    return (
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:arnis_elevation_tile",
            schema_version="1",
            branch_membership=terrain_membership,
            layer_membership=("physical_base",),
            geometry_types=("rect",),
            required_components=("elevation_field",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:arnis-elevation",
                    family="elevation_field",
                    attributes={
                        "artifact_ref": "bundle-artifact",
                        "checksum_sha256": "0" * 64,
                        "dtype": "float32_le",
                        "shape": [2, 2],
                        "resolution_m": [1.0, 1.0],
                        "units": "m",
                        "vertical_datum": "source_provider_native_unspecified",
                        "uncertainty_status": "not_reported",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:arnis_landcover_tile",
            schema_version="1",
            branch_membership=terrain_membership,
            layer_membership=("terrain_surface",),
            geometry_types=("rect",),
            required_components=("landcover_field",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:arnis-landcover",
                    family="landcover_field",
                    attributes={
                        "artifact_ref": "bundle-artifact",
                        "checksum_sha256": "0" * 64,
                        "dtype": "uint8",
                        "shape": [2, 2],
                        "resolution_m": [1.0, 1.0],
                        "classification_scheme": "ESA_WorldCover_2021_v200",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:arnis_road",
            schema_version="1",
            branch_membership=terrain_membership,
            layer_membership=("infrastructure_network",),
            geometry_types=("line",),
            required_components=("network", "elevation_anchor"),
            optional_components=("surface_material",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:arnis-road",
                    family="network",
                    attributes={
                        "width_m": 1.0,
                        "connectivity": "source_geometry",
                        "surface_class": "unspecified",
                        "bridge": False,
                        "tunnel": False,
                        "covered": False,
                        "layer": 0,
                    },
                ),
                EnvironmentComponent(
                    component_id="component-template:arnis-road-elevation-anchor",
                    family="elevation_anchor",
                    attributes={
                        "mode": "terrain_draped",
                        "resolved": True,
                        "source": "bundle_feature_attributes",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:arnis_building",
            schema_version="1",
            branch_membership=terrain_membership,
            layer_membership=("built_structure",),
            geometry_types=("polygon",),
            required_components=("structure", "elevation_anchor"),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:arnis-building",
                    family="structure",
                    attributes={
                        "footprint": "polygon",
                        "height_m": 1.0,
                        "material": "unspecified",
                    },
                ),
                EnvironmentComponent(
                    component_id="component-template:arnis-building-elevation-anchor",
                    family="elevation_anchor",
                    attributes={
                        "mode": "terrain_rigid",
                        "resolved": True,
                        "source": "bundle_feature_attributes",
                        "base_offset_m": 0.0,
                        "base_offset_source": "bundle_feature_attributes",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:arnis_hydrology",
            schema_version="1",
            branch_membership=hydrology_membership,
            layer_membership=("hydrology",),
            geometry_types=("line", "polygon"),
            required_components=("hydrology", "elevation_anchor"),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:arnis-hydrology",
                    family="hydrology",
                    attributes={"state": "static_source_geometry"},
                ),
                EnvironmentComponent(
                    component_id="component-template:arnis-hydrology-elevation-anchor",
                    family="elevation_anchor",
                    attributes={
                        "mode": "water_surface_from_dem",
                        "resolved": True,
                        "source": "bundle_feature_attributes",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
    )


def _generator_version(bundle: dict[str, Any]) -> str:
    generator = bundle["generator"]
    return (
        f"{str(generator['version'])}+{str(generator['upstream_revision'])[:12]}."
        f"{str(generator['exporter_version'])}"
    )


def _object_provenance(
    *,
    catalog: EnvironmentCatalogDescriptor,
    bundle: dict[str, Any],
    bundle_digest: str,
    artifact: dict[str, Any],
    source_provider: str,
    source_feature_type: str,
    source_feature_id: str,
    source_tags: Any,
    feature_lineage: dict[str, Any] | None = None,
    static_placement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tile_id = bundle["tile_scheme"]["tile_id"]
    return {
        "catalog_id": catalog.catalog_id,
        "catalog_schema_version": catalog.schema_version,
        "generator_id": "arnis",
        "generator_version": _generator_version(bundle),
        "request_id": bundle["request"]["request_id"],
        "source_inputs": [
            bundle["bundle_id"],
            f"sha256:{bundle['request']['source_input_sha256']}",
        ],
        "bundle_id": bundle["bundle_id"],
        "bundle_digest_sha256": bundle_digest,
        "source_provider": source_provider,
        "source_feature_type": source_feature_type,
        "source_feature_id": source_feature_id,
        "source_tags": source_tags if isinstance(source_tags, dict) else {},
        "source_artifact_ref": artifact["path"],
        "source_artifact_sha256": artifact["sha256"],
        "continuous_lineage": bundle["lineage"],
        "artifact_lineage": artifact["metadata"]["lineage"],
        **({"feature_lineage": feature_lineage} if isinstance(feature_lineage, dict) else {}),
        **({"static_placement": static_placement} if isinstance(static_placement, dict) else {}),
        "tile_id": tile_id,
        "covered_tile_ids": [tile_id],
        "no_held_capability_release": True,
    }


def _raster_component_attributes(artifact: dict[str, Any]) -> dict[str, Any]:
    metadata = artifact["metadata"]
    step = metadata["step_xy_m"]
    attributes = {
        "artifact_ref": artifact["path"],
        "checksum_sha256": artifact["sha256"],
        "media_type": artifact["media_type"],
        "dtype": artifact["dtype"],
        "shape": list(artifact["shape"]),
        "resolution_m": [abs(float(step[0])), abs(float(step[1]))],
        "grid_origin_xy_m": list(metadata["origin_xy_m"]),
        "grid_step_xy_m": list(step),
        "grid_registration": metadata["grid_registration"],
        "semantics": metadata["semantics"],
    }
    for key in (
        "units",
        "vertical_datum",
        "uncertainty_status",
        "source_provider",
        "classification_scheme",
        "source_native_resolution_m",
        "class_legend",
        "contributing_sources",
        "missing_source_units",
    ):
        if key in metadata:
            attributes[key] = metadata[key]
    return attributes


def _raster_object(
    *,
    bundle: dict[str, Any],
    extent: EnvironmentRegionExtent,
    bundle_digest: str,
    artifact: dict[str, Any],
    catalog: EnvironmentCatalogDescriptor,
    family: str,
    layer: str,
) -> EnvironmentObject:
    center_x = (extent.min_x + extent.max_x) / 2.0
    center_y = (extent.min_y + extent.max_y) / 2.0
    source_provider = str(
        artifact["metadata"].get("source_provider")
        or artifact["metadata"].get("classification_scheme")
        or "arnis"
    )
    return EnvironmentObject(
        object_id=f"envobj:arnis:{bundle['bundle_id'].split(':')[-1]}:{family}",
        catalog_ref=catalog.catalog_id,
        geometry=EnvironmentGeometry(
            "rect",
            {
                "x": center_x,
                "y": center_y,
                "width": extent.max_x - extent.min_x,
                "length": extent.max_y - extent.min_y,
                "heading": 0.0,
            },
        ),
        branch_membership=catalog.branch_membership,
        components=(
            EnvironmentComponent(
                component_id=f"component:arnis:{family}",
                family=family,
                attributes=_raster_component_attributes(artifact),
            ),
        ),
        layer_membership=(layer,),
        properties={},
        provenance=_object_provenance(
            catalog=catalog,
            bundle=bundle,
            bundle_digest=bundle_digest,
            artifact=artifact,
            source_provider=source_provider,
            source_feature_type="raster",
            source_feature_id=artifact["artifact_id"],
            source_tags={},
        ),
    )


def _required_text(attributes: dict[str, Any], key: str, feature_id: str) -> str:
    value = str(attributes.get(key) or "").strip()
    if not value:
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            f"feature {feature_id} is missing {key}",
        )
    return value


def _elevation_anchor_invalid(feature_id: str, message: str) -> None:
    raise _ImportFailure(
        "environment_substrate_arnis_elevation_anchor_invalid",
        f"feature {feature_id} elevation anchor is invalid: {message}",
    )


def _optional_anchor_layer(attributes: dict[str, Any], feature_id: str) -> int | None:
    if "layer" not in attributes:
        return None
    value = attributes["layer"]
    if not _strict_finite_number(value) or float(value) != int(float(value)):
        _elevation_anchor_invalid(feature_id, "layer must be a finite integer")
    return int(float(value))


def _optional_anchor_flag(
    attributes: dict[str, Any],
    key: str,
    feature_id: str,
) -> bool:
    if key not in attributes:
        return False
    value = attributes[key]
    if not isinstance(value, bool):
        _elevation_anchor_invalid(feature_id, f"{key} must be boolean")
    return value


def _normalized_elevation_anchor(
    feature_class: str,
    attributes: dict[str, Any],
    feature_id: str,
) -> dict[str, Any]:
    raw_mode = attributes.get("vertical_anchor_mode")
    raw_source = attributes.get("vertical_anchor_source")
    mode = raw_mode.strip() if isinstance(raw_mode, str) else ""
    source = raw_source.strip() if isinstance(raw_source, str) else ""
    resolved = attributes.get("vertical_placement_resolved")
    if not mode:
        _elevation_anchor_invalid(feature_id, "vertical_anchor_mode is required")
    if not isinstance(resolved, bool):
        _elevation_anchor_invalid(
            feature_id,
            "vertical_placement_resolved must be boolean",
        )
    if not source:
        _elevation_anchor_invalid(feature_id, "vertical_anchor_source is required")

    layer = _optional_anchor_layer(attributes, feature_id)
    bridge = _optional_anchor_flag(attributes, "bridge", feature_id)
    tunnel = _optional_anchor_flag(attributes, "tunnel", feature_id)
    covered = _optional_anchor_flag(attributes, "covered", feature_id)

    has_base_offset = "base_offset_m" in attributes
    has_base_offset_source = "base_offset_source" in attributes
    base_offset_m: float | None = None
    base_offset_source = ""
    if has_base_offset:
        if not _strict_finite_number(attributes["base_offset_m"]):
            _elevation_anchor_invalid(feature_id, "base_offset_m must be finite")
        base_offset_m = float(attributes["base_offset_m"])
        if base_offset_m < 0.0:
            _elevation_anchor_invalid(feature_id, "base_offset_m must be non-negative")
        raw_base_offset_source = attributes.get("base_offset_source")
        base_offset_source = (
            raw_base_offset_source.strip() if isinstance(raw_base_offset_source, str) else ""
        )
        if not base_offset_source:
            _elevation_anchor_invalid(
                feature_id,
                "base_offset_source is required when base_offset_m is present",
            )
    elif has_base_offset_source:
        _elevation_anchor_invalid(
            feature_id,
            "base_offset_source cannot be declared without base_offset_m",
        )

    if feature_class == "building":
        if mode == "terrain_rigid":
            if not resolved:
                _elevation_anchor_invalid(
                    feature_id,
                    "terrain_rigid building placement must be resolved",
                )
            if base_offset_m is None:
                _elevation_anchor_invalid(
                    feature_id,
                    "resolved terrain_rigid building requires base_offset_m",
                )
            if bridge or tunnel:
                _elevation_anchor_invalid(
                    feature_id,
                    "terrain_rigid building cannot be marked bridge or tunnel",
                )
        elif mode == "elevated_profile":
            if resolved:
                _elevation_anchor_invalid(
                    feature_id,
                    "elevated_profile building cannot claim resolved placement",
                )
            if layer is None or layer <= 0:
                _elevation_anchor_invalid(
                    feature_id,
                    "unresolved elevated_profile building requires a positive layer",
                )
            if has_base_offset or has_base_offset_source:
                _elevation_anchor_invalid(
                    feature_id,
                    "unresolved elevated_profile building cannot declare a base offset",
                )
            if bridge or tunnel:
                _elevation_anchor_invalid(
                    feature_id,
                    "elevated building cannot be marked bridge or tunnel",
                )
        else:
            _elevation_anchor_invalid(
                feature_id,
                f"building mode {mode!r} is unsupported",
            )
    elif feature_class == "road":
        if mode == "terrain_draped":
            if not resolved:
                _elevation_anchor_invalid(
                    feature_id,
                    "terrain_draped road placement must be resolved",
                )
            if bridge or tunnel or (layer is not None and layer != 0):
                _elevation_anchor_invalid(
                    feature_id,
                    "terrain_draped road cannot declare bridge, tunnel, or nonzero layer",
                )
        elif mode == "elevated_profile":
            if resolved:
                _elevation_anchor_invalid(
                    feature_id,
                    "elevated_profile road cannot claim resolved placement",
                )
            if not (bridge or (layer is not None and layer > 0)):
                _elevation_anchor_invalid(
                    feature_id,
                    "elevated_profile road requires bridge=true or a positive layer",
                )
        elif mode == "subsurface_profile":
            if resolved:
                _elevation_anchor_invalid(
                    feature_id,
                    "subsurface_profile road cannot claim resolved placement",
                )
            if (
                bridge
                or (layer is not None and layer > 0)
                or not (tunnel or (layer is not None and layer < 0))
            ):
                _elevation_anchor_invalid(
                    feature_id,
                    "subsurface_profile road requires no bridge or positive layer and must have tunnel=true or a negative layer",
                )
        else:
            _elevation_anchor_invalid(feature_id, f"road mode {mode!r} is unsupported")
    elif feature_class == "hydrology":
        if mode != "water_surface_from_dem":
            _elevation_anchor_invalid(
                feature_id,
                f"hydrology mode {mode!r} is unsupported",
            )
        if not resolved:
            _elevation_anchor_invalid(
                feature_id,
                "water_surface_from_dem placement must be resolved",
            )
        if bridge or tunnel or (layer is not None and layer != 0):
            _elevation_anchor_invalid(
                feature_id,
                "water_surface_from_dem cannot declare bridge, tunnel, or nonzero layer",
            )
    else:
        _elevation_anchor_invalid(feature_id, f"feature class {feature_class!r} is unsupported")

    anchor: dict[str, Any] = {
        "mode": mode,
        "resolved": resolved,
        "source": source,
    }
    if base_offset_m is not None:
        anchor["base_offset_m"] = base_offset_m
        anchor["base_offset_source"] = base_offset_source
    if layer is not None:
        anchor["layer"] = layer
    if "bridge" in attributes:
        anchor["bridge"] = bridge
    if "tunnel" in attributes:
        anchor["tunnel"] = tunnel
    if "covered" in attributes:
        anchor["covered"] = covered
    return anchor


def _vector_object(
    *,
    bundle: dict[str, Any],
    bundle_digest: str,
    artifact: dict[str, Any],
    feature_class: str,
    feature: dict[str, Any],
    catalog: EnvironmentCatalogDescriptor,
) -> EnvironmentObject:
    feature_id = feature["feature_id"]
    attributes = feature["attributes"]
    source = feature["provenance"]
    elevation_anchor = _normalized_elevation_anchor(
        feature_class,
        attributes,
        feature_id,
    )
    components: list[EnvironmentComponent] = []
    layer: str
    if feature_class == "road":
        if feature["geometry_type"] != "line" or not _positive_number(attributes.get("width_m")):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                f"road feature {feature_id} requires line geometry and positive width_m",
            )
        surface_class = _required_text(attributes, "surface_class", feature_id)
        components.append(
            EnvironmentComponent(
                component_id=f"component:{feature_id}:network",
                family="network",
                attributes={
                    "width_m": float(attributes["width_m"]),
                    "connectivity": _required_text(attributes, "connectivity", feature_id),
                    "surface_class": surface_class,
                    "highway_type": _required_text(attributes, "highway_type", feature_id),
                    "bridge": elevation_anchor.get("bridge", False),
                    "tunnel": elevation_anchor.get("tunnel", False),
                    "covered": elevation_anchor.get("covered", False),
                    "layer": elevation_anchor.get("layer", 0),
                    "width_source": str(attributes.get("width_source") or "source"),
                },
            )
        )
        if surface_class != "unspecified":
            components.append(
                EnvironmentComponent(
                    component_id=f"component:{feature_id}:surface",
                    family="surface_material",
                    attributes={"surface": surface_class},
                )
            )
        layer = "infrastructure_network"
    elif feature_class == "building":
        if feature["geometry_type"] != "polygon" or not _positive_number(
            attributes.get("height_m")
        ):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                f"building feature {feature_id} requires polygon geometry and positive height_m",
            )
        components.append(
            EnvironmentComponent(
                component_id=f"component:{feature_id}:structure",
                family="structure",
                attributes={
                    "footprint": _required_text(attributes, "footprint", feature_id),
                    "height_m": float(attributes["height_m"]),
                    "material": _required_text(attributes, "material", feature_id),
                    "height_source": str(attributes.get("height_source") or "unspecified"),
                    "height_semantics": _required_text(attributes, "height_semantics", feature_id),
                    "building_type": str(attributes.get("building_type") or "unspecified"),
                },
            )
        )
        layer = "built_structure"
    elif feature_class == "hydrology":
        if feature["geometry_type"] not in {"line", "polygon"}:
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                f"hydrology feature {feature_id} requires line or polygon geometry",
            )
        hydrology_attributes = {
            "state": _required_text(attributes, "state", feature_id),
            "water_kind": _required_text(attributes, "water_kind", feature_id),
            "geometry_role": _required_text(attributes, "geometry_role", feature_id),
        }
        if "width_m" in attributes:
            if not _positive_number(attributes["width_m"]):
                raise _ImportFailure(
                    "environment_substrate_arnis_vector_invalid",
                    f"hydrology feature {feature_id} width_m must be positive",
                )
            hydrology_attributes["width_m"] = float(attributes["width_m"])
        components.append(
            EnvironmentComponent(
                component_id=f"component:{feature_id}:hydrology",
                family="hydrology",
                attributes=hydrology_attributes,
            )
        )
        layer = "hydrology"
    else:
        raise _ImportFailure(
            "environment_substrate_arnis_vector_invalid",
            f"unsupported feature class {feature_class!r}",
        )

    components.append(
        EnvironmentComponent(
            component_id=f"component:{feature_id}:elevation-anchor",
            family="elevation_anchor",
            attributes=elevation_anchor,
        )
    )

    return EnvironmentObject(
        object_id=f"envobj:arnis:{feature_class}:{feature_id}",
        catalog_ref=catalog.catalog_id,
        geometry=feature["geometry"],
        branch_membership=catalog.branch_membership,
        components=tuple(components),
        layer_membership=(layer,),
        properties={},
        provenance=_object_provenance(
            catalog=catalog,
            bundle=bundle,
            bundle_digest=bundle_digest,
            artifact=artifact,
            source_provider=str(source.get("source_provider") or "unknown"),
            source_feature_type=str(source.get("source_feature_type") or "unknown"),
            source_feature_id=str(source.get("source_feature_id") or feature_id),
            source_tags=source.get("source_tags"),
            feature_lineage=feature["lineage"],
            static_placement=elevation_anchor,
        ),
    )


def _validate_bundle_header(bundle: dict[str, Any]) -> dict[str, Any]:
    if bundle.get("contract_version") != ARNIS_CMO_BUNDLE_CONTRACT_VERSION:
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_contract_mismatch",
            "unsupported Arnis CMO bundle contract version",
        )
    if bundle.get("coordinate_frame") != "local_enu_m":
        raise _ImportFailure(
            "environment_substrate_arnis_coordinate_frame_unsupported",
            "Arnis bundle coordinate_frame must be local_enu_m",
        )
    request = bundle.get("request")
    generator = bundle.get("generator")
    tile_scheme = bundle.get("tile_scheme")
    if (
        not isinstance(request, dict)
        or not isinstance(generator, dict)
        or not isinstance(tile_scheme, dict)
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            "bundle requires request, generator, and tile_scheme objects",
        )
    continuous_lineage = _validate_root_continuous_lineage(bundle.get("lineage"))
    if (
        generator.get("exporter_patch_id") != ARNIS_CONTINUOUS_EXPORTER_PATCH_ID
        or generator.get("exporter_patch_sha256") != ARNIS_CONTINUOUS_PATCH_SHA256
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_exporter_identity_mismatch",
            "bundle exporter patch identity is not admitted for continuous import",
        )
    scale = request.get("scale")
    rotation_deg = request.get("rotation_deg")
    if (
        request.get("projection") != _SUPPORTED_PROJECTION
        or not _finite_number(scale)
        or not math.isclose(float(scale), 1.0)
        or not _finite_number(rotation_deg)
        or not math.isclose(float(rotation_deg), 0.0)
        or request.get("overture") is not False
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_coordinate_frame_unsupported",
            "phase 1 requires normalized projection, scale=1, rotation=0, overture=false",
        )
    if (
        bundle.get("capability_claims") not in ([], ())
        or bundle.get("no_held_capability_release") is not True
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            "bundle must not claim held runtime capabilities",
        )
    if (
        tile_scheme.get("columns") != 1
        or tile_scheme.get("rows") != 1
        or not str(tile_scheme.get("tile_id") or "").strip()
        or not str(tile_scheme.get("tile_scheme_id") or "").strip()
        or not _finite_number(tile_scheme.get("halo_m", 0.0))
        or float(tile_scheme.get("halo_m", 0.0)) < 0.0
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_extent_mismatch",
            "phase 1 requires one deterministic tile",
        )
    if (
        not str(bundle.get("bundle_id") or "").strip()
        or not _HEX64.fullmatch(str(bundle.get("content_digest_sha256") or ""))
        or not str(request.get("request_id") or "").strip()
        or not _integer(request.get("deterministic_seed", 0))
        or generator.get("id") != "arnis"
        or not str(generator.get("version") or "").strip()
        or not re.fullmatch(r"[0-9a-f]{40}", str(generator.get("upstream_revision") or ""))
        or not str(generator.get("exporter_version") or "").strip()
        or not _HEX64.fullmatch(str(request.get("source_input_sha256") or ""))
    ):
        raise _ImportFailure(
            "environment_substrate_arnis_bundle_invalid",
            "bundle generator and frozen source identity are required",
        )
    return continuous_lineage


def import_arnis_environment_bundle(
    bundle_root: str | Path,
) -> ArnisEnvironmentImportResult:
    root = Path(bundle_root)
    bundle_path = root / "bundle.json"
    bundle_digest = ""
    try:
        if not root.is_dir() or not bundle_path.is_file():
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                "bundle root must contain bundle.json",
            )
        bundle_bytes = bundle_path.read_bytes()
        bundle_digest = _sha256_bytes(bundle_bytes)
        try:
            bundle = json.loads(bundle_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                f"bundle.json is invalid: {exc}",
            ) from exc
        if not isinstance(bundle, dict):
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                "bundle.json must contain an object",
            )
        continuous_lineage = _validate_bundle_header(bundle)
        extent = _extent_from_bundle(bundle)
        artifacts_by_id, artifact_paths = _artifact_inventory(root, bundle)
        artifacts = tuple(artifacts_by_id.values())
        elevation_artifact = _artifact_by_kind(artifacts, "elevation_raster")
        landcover_artifact = _artifact_by_kind(artifacts, "landcover_raster")
        provenance_artifact = _artifact_by_kind(artifacts, "provenance")
        road_artifact = _vector_artifact(artifacts, "road")
        building_artifact = _vector_artifact(artifacts, "building")
        hydrology_artifact = _vector_artifact(artifacts, "hydrology")
        artifact_lineages = {
            artifact["artifact_id"]: _validate_artifact_continuous_lineage(artifact)
            for artifact in sorted(artifacts, key=lambda item: item["artifact_id"])
        }
        _validate_raster(
            elevation_artifact,
            artifact_paths[elevation_artifact["artifact_id"]],
            extent,
            expected_dtype="float32_le",
        )
        _validate_raster(
            landcover_artifact,
            artifact_paths[landcover_artifact["artifact_id"]],
            extent,
            expected_dtype="uint8",
        )
        provenance_payload = _load_json(
            artifact_paths[provenance_artifact["artifact_id"]],
            code="environment_substrate_arnis_bundle_invalid",
        )
        if (
            provenance_payload.get("contract_version") != ARNIS_CMO_BUNDLE_CONTRACT_VERSION
            or provenance_payload.get("generator")
            != {
                "id": bundle["generator"]["id"],
                "version": bundle["generator"]["version"],
                "upstream_revision": bundle["generator"]["upstream_revision"],
            }
            or provenance_payload.get("exporter_version") != bundle["generator"]["exporter_version"]
            or provenance_payload.get("exporter_patch_id")
            != bundle["generator"]["exporter_patch_id"]
            or provenance_payload.get("exporter_patch_sha256")
            != bundle["generator"]["exporter_patch_sha256"]
            or provenance_payload.get("capability_boundary", {}).get("no_held_capability_release")
            is not True
        ):
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                "provenance artifact does not preserve the phase 1 capability boundary",
            )
        if "lineage" not in provenance_payload:
            _lineage_required("provenance continuous lineage is required")
        if provenance_payload["lineage"] != continuous_lineage:
            _lineage_mismatch("provenance continuous lineage does not match bundle lineage")
        provenance_inputs = provenance_payload.get("source_inputs")
        if (
            not isinstance(provenance_inputs, list)
            or len(provenance_inputs) != 1
            or not isinstance(provenance_inputs[0], dict)
            or provenance_inputs[0].get("sha256") != bundle["request"]["source_input_sha256"]
            or provenance_inputs[0].get("kind") != "osm_json"
            or provenance_inputs[0].get("provider") != "openstreetmap"
        ):
            raise _ImportFailure(
                "environment_substrate_arnis_bundle_invalid",
                "provenance artifact does not match the frozen OSM input",
            )

        vector_features = {
            "road": _load_feature_file(
                artifact_paths[road_artifact["artifact_id"]], road_artifact, extent
            ),
            "building": _load_feature_file(
                artifact_paths[building_artifact["artifact_id"]],
                building_artifact,
                extent,
            ),
            "hydrology": _load_feature_file(
                artifact_paths[hydrology_artifact["artifact_id"]],
                hydrology_artifact,
                extent,
            ),
        }
        all_feature_ids = [
            feature["feature_id"] for features in vector_features.values() for feature in features
        ]
        if len(all_feature_ids) != len(set(all_feature_ids)):
            raise _ImportFailure(
                "environment_substrate_arnis_vector_invalid",
                "feature IDs must be unique across vector artifacts",
            )

        branches, components, layers = _component_registries()
        catalogs = _catalogs()
        catalog_validation = validate_environment_catalog_descriptors(
            catalogs,
            branch_registry=branches,
            component_registry=components,
            layer_registry=layers,
        )
        if not catalog_validation.valid:
            raise _ImportFailure(
                "environment_substrate_arnis_catalog_invalid",
                catalog_validation.errors[0],
            )
        catalog_map = {catalog.catalog_id: catalog for catalog in catalogs}
        tile_scheme = bundle["tile_scheme"]
        request = EnvironmentGeneratorRequest(
            request_id=bundle["request"]["request_id"],
            generator_id="arnis",
            generator_version=_generator_version(bundle),
            deterministic_seed=int(bundle["request"].get("deterministic_seed", 0)),
            coordinate_frame="local_enu_m",
            region_extent=extent,
            tile_scheme=EnvironmentTileScheme(
                tile_scheme_id=tile_scheme["tile_scheme_id"],
                origin_x=extent.min_x,
                origin_y=extent.min_y,
                tile_width_m=extent.max_x - extent.min_x,
                tile_height_m=extent.max_y - extent.min_y,
                columns=1,
                rows=1,
                halo_m=float(tile_scheme.get("halo_m", 0.0)),
            ),
            catalog_refs=tuple(catalog_map),
            evidence_refs=(
                EnvironmentGeneratorEvidenceRef(
                    ref_id=f"sha256:{provenance_artifact['sha256']}",
                    evidence_kind="arnis_bundle_provenance",
                    provenance_label=ARNIS_CMO_IMPORT_CONTRACT_VERSION,
                ),
            ),
            output_manifest_id=(f"envmanifest:arnis:{bundle['bundle_id'].split(':')[-1]}"),
            branch_scope=("terrain", "hydrology"),
            realism_target="G1",
            constraints={
                "static_environment_data_only": True,
                "single_tile_phase1": True,
            },
            source_inputs=(
                bundle["bundle_id"],
                f"sha256:{bundle['request']['source_input_sha256']}",
            ),
            capability_claims=(),
            no_held_capability_release=True,
        )
        request_validation = validate_environment_generator_request(request, catalogs)
        if not request_validation.valid:
            raise _ImportFailure(
                "environment_substrate_arnis_request_invalid",
                request_validation.errors[0],
            )

        objects: list[EnvironmentObject] = [
            _raster_object(
                bundle=bundle,
                extent=extent,
                bundle_digest=bundle_digest,
                artifact=elevation_artifact,
                catalog=catalog_map["catalog:arnis_elevation_tile"],
                family="elevation_field",
                layer="physical_base",
            ),
            _raster_object(
                bundle=bundle,
                extent=extent,
                bundle_digest=bundle_digest,
                artifact=landcover_artifact,
                catalog=catalog_map["catalog:arnis_landcover_tile"],
                family="landcover_field",
                layer="terrain_surface",
            ),
        ]
        vector_specs = (
            ("road", road_artifact, catalog_map["catalog:arnis_road"]),
            ("building", building_artifact, catalog_map["catalog:arnis_building"]),
            ("hydrology", hydrology_artifact, catalog_map["catalog:arnis_hydrology"]),
        )
        for feature_class, artifact, catalog in vector_specs:
            objects.extend(
                _vector_object(
                    bundle=bundle,
                    bundle_digest=bundle_digest,
                    artifact=artifact,
                    feature_class=feature_class,
                    feature=feature,
                    catalog=catalog,
                )
                for feature in vector_features[feature_class]
            )

        elevation_anchors = [
            component
            for item in objects
            for component in item.components
            if component.family == "elevation_anchor"
        ]
        resolved_anchor_count = sum(
            component.attributes["resolved"] is True for component in elevation_anchors
        )
        elevation_anchor_counts = {
            "total": len(elevation_anchors),
            "resolved": resolved_anchor_count,
            "held": len(elevation_anchors) - resolved_anchor_count,
        }

        manifest = EnvironmentManifest(
            manifest_id=request.output_manifest_id,
            schema_version="1",
            coordinate_frame="local_enu_m",
            region_extent=extent,
            generation=EnvironmentGenerationMetadata(
                generator_id="arnis",
                generator_version=_generator_version(bundle),
                deterministic_seed=request.deterministic_seed,
                source_inputs=request.source_inputs,
            ),
            objects=tuple(sorted(objects, key=lambda item: item.object_id)),
            branch_registry=branches,
            component_registry=components,
            layer_registry=layers,
            catalogs=tuple(catalog_map),
            validation_evidence=(
                {
                    "kind": "arnis_cmo_bundle_import",
                    "contract_version": ARNIS_CMO_IMPORT_CONTRACT_VERSION,
                    "bundle_id": bundle["bundle_id"],
                    "bundle_digest_sha256": bundle_digest,
                    "artifact_checksums": {
                        artifact["artifact_id"]: artifact["sha256"]
                        for artifact in sorted(artifacts, key=lambda item: item["artifact_id"])
                    },
                    "tile_scheme": request.tile_scheme.to_metadata(),
                    "continuous_lineage": continuous_lineage,
                    "artifact_lineage": artifact_lineages,
                    "exporter_patch_id": bundle["generator"]["exporter_patch_id"],
                    "exporter_patch_sha256": bundle["generator"]["exporter_patch_sha256"],
                    "elevation_anchor_counts": elevation_anchor_counts,
                    "no_held_capability_release": True,
                },
            ),
            capability_claims=(),
        )
        manifest_validation = validate_environment_manifest(manifest)
        if not manifest_validation.valid:
            raise _ImportFailure(
                "environment_substrate_arnis_manifest_invalid",
                manifest_validation.errors[0],
            )
        admission = validate_environment_catalog_admission(manifest, catalogs)
        if not admission.valid:
            raise _ImportFailure(
                "environment_substrate_arnis_catalog_invalid",
                admission.errors[0],
            )
        return ArnisEnvironmentImportResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
            manifest=manifest,
            catalog_descriptors=catalogs,
            bundle_digest_sha256=bundle_digest,
        )
    except _ImportFailure as exc:
        return _failure(
            exc.code,
            str(exc),
            bundle_digest_sha256=bundle_digest,
        )
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
        return _failure(
            "environment_substrate_arnis_bundle_invalid",
            f"Arnis bundle import failed closed: {exc}",
            bundle_digest_sha256=bundle_digest,
        )


__all__ = [
    "ARNIS_CMO_BUNDLE_CONTRACT_VERSION",
    "ARNIS_CMO_IMPORT_CONTRACT_VERSION",
    "ARNIS_CONTINUOUS_EXPORTER_PATCH_ID",
    "ARNIS_CONTINUOUS_PATCH_SHA256",
    "ArnisEnvironmentImportResult",
    "import_arnis_environment_bundle",
]
