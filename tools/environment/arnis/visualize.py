from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

import numpy as np

try:
    from .static_scene import (
        STATIC_SCENE_CONTRACT,
        STATIC_SCENE_RELEASE_STATE,
        StaticSceneDerivationError,
        derive_static_scene_geometry,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from static_scene import (  # type: ignore[no-redef]
        STATIC_SCENE_CONTRACT,
        STATIC_SCENE_RELEASE_STATE,
        StaticSceneDerivationError,
        derive_static_scene_geometry,
    )


ARNIS_CONTINUOUS_LINEAGE_CONTRACT = "arnis_continuous_metric.v1"
ARNIS_CONTINUOUS_REPRESENTATION = "continuous_metric_2_5d"
ARNIS_CONTINUOUS_EXPORT_STAGE = "post_semantic_processing_pre_render_quantization"
CONTINUOUS_PREVIEW_TITLE = "CMO CONTINUOUS BUNDLE PREVIEW — NOT RUNTIME"
STATIC_SCENE_PREVIEW_TITLE = "CMO STATIC SCENE GEOMETRY PREVIEW — NOT RUNTIME"
_ELEVATION_STAGE = "postprocess_meters_pre_minecraft_scale"
_INTEGER_TOLERANCE = 1.0e-9
_LANDCOVER_COLORS = {
    0: "#000000",
    10: "#006e00",
    20: "#ffbb22",
    30: "#ffff4c",
    40: "#f096ff",
    50: "#fa0000",
    60: "#b4b4b4",
    70: "#f0f0f0",
    80: "#0064c8",
    90: "#0096a0",
    95: "#00cf75",
    100: "#fae6a0",
}


class ContinuousBundleVisualizationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuousBundleVisualizationError(f"failed to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContinuousBundleVisualizationError(f"{path} must contain a JSON object")
    return value


def _safe_artifact_path(root: Path, relative_path: Any) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ContinuousBundleVisualizationError("artifact path must be a non-empty string")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative_path:
        raise ContinuousBundleVisualizationError(f"unsafe artifact path: {relative_path!r}")
    try:
        resolved = root.joinpath(*pure.parts).resolve(strict=True)
        root_resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ContinuousBundleVisualizationError(
            f"failed to resolve artifact {relative_path!r}: {exc}"
        ) from exc
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ContinuousBundleVisualizationError(f"artifact path escapes bundle: {relative_path!r}")
    if not resolved.is_file():
        raise ContinuousBundleVisualizationError(f"artifact is not a file: {relative_path!r}")
    return resolved


def _sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_length = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                byte_length += len(chunk)
    except OSError as exc:
        raise ContinuousBundleVisualizationError(f"failed to hash {path}: {exc}") from exc
    return digest.hexdigest(), byte_length


def _artifact_list(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = bundle.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContinuousBundleVisualizationError("bundle.artifacts must be a non-empty list")
    if not all(isinstance(item, dict) for item in artifacts):
        raise ContinuousBundleVisualizationError("bundle.artifacts entries must be objects")
    return artifacts


def _one_artifact(
    artifacts: Iterable[dict[str, Any]],
    *,
    kind: str,
    feature_class: str | None = None,
) -> dict[str, Any]:
    matches = [
        item
        for item in artifacts
        if item.get("kind") == kind
        and (feature_class is None or item.get("feature_class") == feature_class)
    ]
    label = kind if feature_class is None else f"{kind}/{feature_class}"
    if len(matches) != 1:
        raise ContinuousBundleVisualizationError(
            f"bundle requires exactly one {label} artifact, found {len(matches)}"
        )
    return matches[0]


def _verify_artifact(root: Path, artifact: dict[str, Any]) -> Path:
    path = _safe_artifact_path(root, artifact.get("path"))
    actual_sha, actual_size = _sha256(path)
    expected_sha = artifact.get("sha256")
    expected_size = artifact.get("byte_length")
    if actual_sha != expected_sha:
        raise ContinuousBundleVisualizationError(
            f"artifact SHA-256 mismatch: {artifact.get('path')}"
        )
    if not isinstance(expected_size, int) or actual_size != expected_size:
        raise ContinuousBundleVisualizationError(
            f"artifact byte length mismatch: {artifact.get('path')}"
        )
    return path


def _shape(artifact: dict[str, Any]) -> tuple[int, int]:
    value = artifact.get("shape")
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) and item > 1 for item in value)
    ):
        raise ContinuousBundleVisualizationError("raster artifact requires shape [rows, columns]")
    return int(value[0]), int(value[1])


def _finite_pair(value: Any, label: str, *, nonzero: bool = False) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ContinuousBundleVisualizationError(f"{label} must contain two numbers")
    try:
        pair = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ContinuousBundleVisualizationError(f"{label} must contain two numbers") from exc
    if not all(math.isfinite(item) for item in pair):
        raise ContinuousBundleVisualizationError(f"{label} must be finite")
    if nonzero and (pair[0] == 0.0 or pair[1] == 0.0):
        raise ContinuousBundleVisualizationError(f"{label} values must be non-zero")
    return pair


def _raster_axes(
    artifact: dict[str, Any],
    shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    metadata = artifact.get("metadata")
    if not isinstance(metadata, dict):
        raise ContinuousBundleVisualizationError("raster artifact metadata must be an object")
    origin_x, origin_y = _finite_pair(metadata.get("origin_xy_m"), "origin_xy_m")
    step_x, step_y = _finite_pair(metadata.get("step_xy_m"), "step_xy_m", nonzero=True)
    height, width = shape
    x = origin_x + np.arange(width, dtype=np.float64) * step_x
    y = origin_y + np.arange(height, dtype=np.float64) * step_y
    return x, y


def _read_elevation(
    root: Path,
    artifact: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if artifact.get("dtype") != "float32_le":
        raise ContinuousBundleVisualizationError("elevation dtype must be float32_le")
    metadata = artifact.get("metadata")
    if not isinstance(metadata, dict):
        raise ContinuousBundleVisualizationError("elevation metadata must be an object")
    if metadata.get("processing_stage") != _ELEVATION_STAGE:
        raise ContinuousBundleVisualizationError(
            f"elevation processing_stage must be {_ELEVATION_STAGE!r}"
        )
    if metadata.get("minecraft_scaling_applied") is not False:
        raise ContinuousBundleVisualizationError(
            "elevation metadata must state minecraft_scaling_applied=false"
        )
    shape = _shape(artifact)
    path = _verify_artifact(root, artifact)
    expected_size = shape[0] * shape[1] * np.dtype("<f4").itemsize
    if path.stat().st_size != expected_size:
        raise ContinuousBundleVisualizationError(
            "elevation byte length does not match dtype and shape"
        )
    values = np.fromfile(path, dtype="<f4").reshape(shape)
    x, y = _raster_axes(artifact, shape)
    if not np.isfinite(values).any():
        raise ContinuousBundleVisualizationError("elevation contains no finite samples")
    return values, x, y


def _read_landcover(
    root: Path,
    artifact: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if artifact.get("dtype") != "uint8":
        raise ContinuousBundleVisualizationError("land-cover dtype must be uint8")
    shape = _shape(artifact)
    path = _verify_artifact(root, artifact)
    expected_size = shape[0] * shape[1]
    if path.stat().st_size != expected_size:
        raise ContinuousBundleVisualizationError(
            "land-cover byte length does not match dtype and shape"
        )
    values = np.fromfile(path, dtype=np.uint8).reshape(shape)
    x, y = _raster_axes(artifact, shape)
    return values, x, y


def _read_vector_file(
    root: Path,
    artifact: dict[str, Any],
    feature_class: str,
) -> dict[str, Any]:
    path = _verify_artifact(root, artifact)
    value = _load_json(path)
    if value.get("coordinate_frame") != "local_enu_m":
        raise ContinuousBundleVisualizationError(
            f"{feature_class} vector coordinate_frame must be local_enu_m"
        )
    if value.get("feature_class") != feature_class:
        raise ContinuousBundleVisualizationError(f"{feature_class} vector class mismatch")
    features = value.get("features")
    if not isinstance(features, list):
        raise ContinuousBundleVisualizationError(f"{feature_class}.features must be a list")
    if artifact.get("feature_count") != len(features):
        raise ContinuousBundleVisualizationError(f"{feature_class} feature count mismatch")
    return value


def _require_lineage_value(
    payload: dict[str, Any],
    key: str,
    expected: Any,
    label: str,
) -> None:
    if key not in payload or payload[key] != expected:
        actual = payload.get(key, "<missing>")
        raise ContinuousBundleVisualizationError(
            f"{label} lineage field {key!r} must be {expected!r}, got {actual!r}"
        )


def _lineage_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContinuousBundleVisualizationError(
            f"bundle root requires fail-closed lineage: {label} must be an object"
        )
    return value


def _validate_lineage(bundle: dict[str, Any]) -> dict[str, Any]:
    if bundle.get("coordinate_frame") != "local_enu_m":
        raise ContinuousBundleVisualizationError("bundle coordinate_frame must be local_enu_m")
    lineage = _lineage_object(bundle.get("lineage"), "lineage")
    for key, expected in (
        ("contract", ARNIS_CONTINUOUS_LINEAGE_CONTRACT),
        ("representation", ARNIS_CONTINUOUS_REPRESENTATION),
        ("export_stage", ARNIS_CONTINUOUS_EXPORT_STAGE),
        ("minecraft_world_read", False),
        ("anvil_region_read", False),
        ("voxelization_applied", False),
    ):
        _require_lineage_value(lineage, key, expected, "bundle")

    geometry = _lineage_object(lineage.get("geometry"), "lineage.geometry")
    for key, expected in (
        ("source_stage", "projected_from_wgs84_f64"),
        ("storage", "json_float64"),
        ("quantization_step_m", None),
        ("block_projection_applied", False),
    ):
        _require_lineage_value(geometry, key, expected, "bundle geometry")

    elevation = _lineage_object(lineage.get("elevation"), "lineage.elevation")
    for key, expected in (
        ("source_stage", "postprocessed_metric_dem"),
        ("storage", "float32_le"),
        ("vertical_quantization_step_m", None),
        ("minecraft_y_transform_applied", False),
        ("minecraft_y_roundtrip", False),
    ):
        _require_lineage_value(elevation, key, expected, "bundle elevation")

    landcover = _lineage_object(lineage.get("landcover"), "lineage.landcover")
    for key, expected in (
        ("source_stage", "source_classification_metric_grid"),
        ("block_palette_roundtrip", False),
    ):
        _require_lineage_value(landcover, key, expected, "bundle landcover")

    return {**lineage, "accepted": True}


def _point(value: Any) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ContinuousBundleVisualizationError("vector coordinate must be [x, y]")
    try:
        point = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ContinuousBundleVisualizationError("vector coordinate must be numeric") from exc
    if not all(math.isfinite(item) for item in point):
        raise ContinuousBundleVisualizationError("vector coordinate must be finite")
    return point


def _geometry_paths(geometry: Any) -> list[tuple[str, list[tuple[float, float]]]]:
    if not isinstance(geometry, dict):
        raise ContinuousBundleVisualizationError("feature geometry must be an object")
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    paths: list[tuple[str, list[tuple[float, float]]]] = []
    if geometry_type == "LineString":
        if not isinstance(coordinates, list):
            raise ContinuousBundleVisualizationError("LineString coordinates must be a list")
        paths.append(("line", [_point(item) for item in coordinates]))
    elif geometry_type == "MultiLineString":
        if not isinstance(coordinates, list):
            raise ContinuousBundleVisualizationError("MultiLineString coordinates must be a list")
        for line in coordinates:
            if not isinstance(line, list):
                raise ContinuousBundleVisualizationError("MultiLineString part must be a list")
            paths.append(("line", [_point(item) for item in line]))
    elif geometry_type == "Polygon":
        if not isinstance(coordinates, list):
            raise ContinuousBundleVisualizationError("Polygon coordinates must be a list")
        for index, ring in enumerate(coordinates):
            if not isinstance(ring, list):
                raise ContinuousBundleVisualizationError("Polygon ring must be a list")
            paths.append(
                ("polygon_outer" if index == 0 else "polygon_hole", [_point(item) for item in ring])
            )
    elif geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list):
            raise ContinuousBundleVisualizationError("MultiPolygon coordinates must be a list")
        for polygon in coordinates:
            if not isinstance(polygon, list):
                raise ContinuousBundleVisualizationError("MultiPolygon part must be a list")
            for index, ring in enumerate(polygon):
                if not isinstance(ring, list):
                    raise ContinuousBundleVisualizationError("MultiPolygon ring must be a list")
                paths.append(
                    (
                        "polygon_outer" if index == 0 else "polygon_hole",
                        [_point(item) for item in ring],
                    )
                )
    else:
        raise ContinuousBundleVisualizationError(
            f"unsupported continuous vector geometry type: {geometry_type!r}"
        )
    for role, path in paths:
        minimum = 2 if role == "line" else 4
        if len(path) < minimum:
            raise ContinuousBundleVisualizationError(f"{role} requires at least {minimum} vertices")
    return paths


def _feature_paths(document: dict[str, Any]) -> list[tuple[str, list[tuple[float, float]]]]:
    paths: list[tuple[str, list[tuple[float, float]]]] = []
    for feature in document.get("features", []):
        if not isinstance(feature, dict):
            raise ContinuousBundleVisualizationError("vector feature must be an object")
        paths.extend(_geometry_paths(feature.get("geometry")))
    return paths


def _coordinate_metrics(document: dict[str, Any]) -> dict[str, Any]:
    paths = _feature_paths(document)
    coordinates = np.asarray([point for _role, path in paths for point in path], dtype=np.float64)
    if coordinates.size == 0:
        raise ContinuousBundleVisualizationError("vector class contains no coordinates")
    residual_x = np.abs(coordinates[:, 0] - np.rint(coordinates[:, 0]))
    residual_y = np.abs(coordinates[:, 1] - np.rint(coordinates[:, 1]))
    nearest_grid_distance = np.hypot(residual_x, residual_y)
    return {
        "feature_count": len(document.get("features", [])),
        "path_count": len(paths),
        "vertex_count": int(coordinates.shape[0]),
        "integer_x_ratio": float(np.mean(residual_x <= _INTEGER_TOLERANCE)),
        "integer_y_ratio": float(np.mean(residual_y <= _INTEGER_TOLERANCE)),
        "nearest_1m_grid_rmse_m": float(np.sqrt(np.mean(nearest_grid_distance**2))),
    }


def _elevation_metrics(values: np.ndarray) -> dict[str, Any]:
    finite_mask = np.isfinite(values)
    finite = values[finite_mask].astype(np.float64)
    return {
        "shape": [int(values.shape[0]), int(values.shape[1])],
        "sample_count": int(values.size),
        "finite_count": int(finite.size),
        "finite_ratio": float(finite.size / values.size),
        "min_m": float(np.min(finite)),
        "max_m": float(np.max(finite)),
        "mean_m": float(np.mean(finite)),
        "standard_deviation_m": float(np.std(finite)),
        "non_integer_ratio": float(np.mean(np.abs(finite - np.rint(finite)) > 1.0e-6)),
    }


def _landcover_metrics(values: np.ndarray) -> dict[str, Any]:
    classes, counts = np.unique(values, return_counts=True)
    return {
        "shape": [int(values.shape[0]), int(values.shape[1])],
        "class_counts": {str(int(key)): int(count) for key, count in zip(classes, counts)},
        "render_interpolation": "nearest_categorical",
        "numeric_interpolation_applied": False,
    }


def _extent(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    dx = float(x[1] - x[0])
    dy = float(y[1] - y[0])
    x_edges = x[0] - dx * 0.5, x[-1] + dx * 0.5
    y_edges = y[0] - dy * 0.5, y[-1] + dy * 0.5
    return min(x_edges), max(x_edges), min(y_edges), max(y_edges)


def _bilinear_sample(
    values: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    points: list[tuple[float, float]],
) -> np.ndarray:
    coordinates = np.asarray(points, dtype=np.float64)
    fx = (coordinates[:, 0] - x_axis[0]) / (x_axis[1] - x_axis[0])
    fy = (coordinates[:, 1] - y_axis[0]) / (y_axis[1] - y_axis[0])
    valid = (fx >= 0.0) & (fx <= values.shape[1] - 1) & (fy >= 0.0) & (fy <= values.shape[0] - 1)
    sampled = np.full(len(points), np.nan, dtype=np.float64)
    if not np.any(valid):
        return sampled
    clipped_x = np.clip(fx[valid], 0.0, values.shape[1] - 1)
    clipped_y = np.clip(fy[valid], 0.0, values.shape[0] - 1)
    x0 = np.floor(clipped_x).astype(int)
    y0 = np.floor(clipped_y).astype(int)
    x1 = np.minimum(x0 + 1, values.shape[1] - 1)
    y1 = np.minimum(y0 + 1, values.shape[0] - 1)
    tx = clipped_x - x0
    ty = clipped_y - y0
    v00 = values[y0, x0].astype(np.float64)
    v10 = values[y0, x1].astype(np.float64)
    v01 = values[y1, x0].astype(np.float64)
    v11 = values[y1, x1].astype(np.float64)
    sampled[valid] = (
        v00 * (1.0 - tx) * (1.0 - ty)
        + v10 * tx * (1.0 - ty)
        + v01 * (1.0 - tx) * ty
        + v11 * tx * ty
    )
    return sampled


def _ensure_matplotlib() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import cm
        from matplotlib.colors import BoundaryNorm, LightSource, ListedColormap, Normalize
        from matplotlib.patches import Patch, Polygon
        from matplotlib.ticker import FuncFormatter
    except ImportError as exc:
        raise ContinuousBundleVisualizationError(
            "continuous bundle visualization requires matplotlib"
        ) from exc
    return (
        plt,
        cm,
        (BoundaryNorm, LightSource, ListedColormap, Normalize),
        (Patch, Polygon),
        FuncFormatter,
        matplotlib,
    )


def _contour_levels(minimum: float, maximum: float) -> np.ndarray:
    span = maximum - minimum
    if span <= 0.0:
        return np.asarray([], dtype=np.float64)
    interval = 0.5 if span <= 20.0 else max(1.0, 10 ** math.floor(math.log10(span / 12.0)))
    start = math.ceil(minimum / interval) * interval
    levels = np.arange(start, maximum, interval, dtype=np.float64)
    if levels.size > 24:
        levels = levels[:: math.ceil(levels.size / 24)]
    return levels


def _draw_plan_vectors(
    ax: Any, vector_documents: dict[str, dict[str, Any]], polygon_type: Any
) -> None:
    styles = {
        "road": {"color": "#f4a340", "linewidth": 1.05, "zorder": 7},
        "building": {"edgecolor": "#222222", "facecolor": "#b8b8b8", "alpha": 0.62, "zorder": 6},
        "hydrology": {"edgecolor": "#0066cc", "facecolor": "#42a5f5", "alpha": 0.52, "zorder": 5},
    }
    for feature_class in ("hydrology", "building", "road"):
        for role, path in _feature_paths(vector_documents[feature_class]):
            coordinates = np.asarray(path, dtype=np.float64)
            if role == "line":
                ax.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    color=styles[feature_class].get(
                        "color", styles[feature_class].get("edgecolor")
                    ),
                    linewidth=styles[feature_class].get("linewidth", 0.8),
                    zorder=styles[feature_class]["zorder"],
                )
            elif role == "polygon_outer":
                ax.add_patch(
                    polygon_type(
                        coordinates,
                        closed=True,
                        edgecolor=styles[feature_class]["edgecolor"],
                        facecolor=styles[feature_class]["facecolor"],
                        linewidth=0.65,
                        alpha=styles[feature_class]["alpha"],
                        zorder=styles[feature_class]["zorder"],
                    )
                )
            else:
                ax.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    color=styles[feature_class]["edgecolor"],
                    linewidth=0.55,
                    linestyle="--",
                    zorder=styles[feature_class]["zorder"] + 1,
                )


def _draw_draped_vectors(
    ax: Any,
    vector_documents: dict[str, dict[str, Any]],
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    minimum: float,
    vertical_exaggeration: float,
) -> int:
    colors = {"road": "#ff9f1c", "building": "#202020", "hydrology": "#0066cc"}
    offsets = {"road": 0.12, "building": 0.18, "hydrology": 0.08}
    drawn = 0
    for feature_class in ("hydrology", "building", "road"):
        for _role, path in _feature_paths(vector_documents[feature_class]):
            coordinates = np.asarray(path, dtype=np.float64)
            sampled = _bilinear_sample(elevation, x_axis, y_axis, path)
            display_z = (
                minimum + (sampled - minimum) * vertical_exaggeration + offsets[feature_class]
            )
            if np.isfinite(display_z).sum() < 2:
                continue
            ax.plot(
                coordinates[:, 0],
                coordinates[:, 1],
                display_z,
                color=colors[feature_class],
                linewidth=1.15 if feature_class == "road" else 0.9,
                alpha=0.95,
            )
            drawn += 1
    return drawn


def _render_figure(
    image_path: Path,
    *,
    bundle: dict[str, Any],
    elevation: np.ndarray,
    elevation_x: np.ndarray,
    elevation_y: np.ndarray,
    landcover: np.ndarray,
    landcover_x: np.ndarray,
    landcover_y: np.ndarray,
    vectors: dict[str, dict[str, Any]],
    metrics: dict[str, Any],
    vertical_exaggeration: float,
) -> int:
    plt, cm, color_types, patch_types, FuncFormatter, _matplotlib = _ensure_matplotlib()
    BoundaryNorm, LightSource, ListedColormap, Normalize = color_types
    Patch, Polygon = patch_types
    finite = elevation[np.isfinite(elevation)].astype(np.float64)
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    filled = np.where(np.isfinite(elevation), elevation, np.mean(finite)).astype(np.float64)
    dx = abs(float(elevation_x[1] - elevation_x[0]))
    dy = abs(float(elevation_y[1] - elevation_y[0]))
    light = LightSource(azdeg=315, altdeg=42)
    terrain = plt.get_cmap("terrain")
    shaded = light.shade(filled, cmap=terrain, vert_exag=1.0, dx=dx, dy=dy, blend_mode="soft")

    figure = plt.figure(figsize=(16, 10), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=(3.2, 1.15), width_ratios=(1.55, 1.0))
    plan = figure.add_subplot(grid[0, 0])
    surface = figure.add_subplot(grid[0, 1], projection="3d")
    profiles = figure.add_subplot(grid[1, 0])
    evidence = figure.add_subplot(grid[1, 1])
    figure.suptitle(
        f"{CONTINUOUS_PREVIEW_TITLE}\nVertical exaggeration: {vertical_exaggeration:g}× (3D panel only)",
        fontsize=15,
        fontweight="bold",
    )

    elevation_extent = _extent(elevation_x, elevation_y)
    plan.imshow(
        shaded,
        extent=elevation_extent,
        origin="lower" if elevation_y[-1] > elevation_y[0] else "upper",
        interpolation="bilinear",
        zorder=1,
    )
    present_classes = sorted(int(value) for value in np.unique(landcover))
    landcover_colors = [_LANDCOVER_COLORS.get(value, "#ff00ff") for value in present_classes]
    boundaries = np.asarray(
        [present_classes[0] - 0.5]
        + [(left + right) * 0.5 for left, right in zip(present_classes, present_classes[1:])]
        + [present_classes[-1] + 0.5],
        dtype=np.float64,
    )
    landcover_cmap = ListedColormap(landcover_colors)
    landcover_norm = BoundaryNorm(boundaries, landcover_cmap.N)
    plan.imshow(
        landcover,
        extent=_extent(landcover_x, landcover_y),
        origin="lower" if landcover_y[-1] > landcover_y[0] else "upper",
        cmap=landcover_cmap,
        norm=landcover_norm,
        interpolation="nearest",
        alpha=0.16,
        zorder=2,
    )
    levels = _contour_levels(minimum, maximum)
    if levels.size:
        contour = plan.contour(
            elevation_x,
            elevation_y,
            filled,
            levels=levels,
            colors="#2d2d2d",
            linewidths=0.42,
            alpha=0.62,
            zorder=3,
        )
        plan.clabel(contour, inline=True, fontsize=6, fmt="%.1f m")
    _draw_plan_vectors(plan, vectors, Polygon)
    plan.set_title("Continuous metre DEM, categorical land cover, and source vectors")
    plan.set_xlabel("East (m)")
    plan.set_ylabel("North (m)")
    plan.set_aspect("equal", adjustable="box")
    plan.set_xlim(elevation_extent[0], elevation_extent[1])
    plan.set_ylim(elevation_extent[2], elevation_extent[3])
    scalar = cm.ScalarMappable(norm=Normalize(vmin=minimum, vmax=maximum), cmap=terrain)
    scalar.set_array([])
    figure.colorbar(scalar, ax=plan, shrink=0.72, pad=0.02, label="Elevation (m)")
    legend_handles = [
        Patch(facecolor="#b8b8b8", edgecolor="#222222", label="Buildings"),
        Patch(facecolor="#42a5f5", edgecolor="#0066cc", label="Hydrology"),
        Patch(facecolor="#f4a340", edgecolor="#f4a340", label="Road centerlines"),
    ]
    plan.legend(handles=legend_handles, loc="lower right", fontsize=8, framealpha=0.88)

    stride = max(1, math.ceil(max(elevation.shape) / 180))
    mesh_x, mesh_y = np.meshgrid(elevation_x[::stride], elevation_y[::stride])
    mesh_z = minimum + (filled[::stride, ::stride] - minimum) * vertical_exaggeration
    surface.plot_surface(
        mesh_x,
        mesh_y,
        mesh_z,
        cmap=terrain,
        linewidth=0,
        antialiased=True,
        alpha=0.92,
    )
    draped_path_count = _draw_draped_vectors(
        surface,
        vectors,
        elevation,
        elevation_x,
        elevation_y,
        minimum,
        vertical_exaggeration,
    )
    surface.set_title("Bilinear DEM drape (vector paths remain line/polygon)")
    surface.set_xlabel("East (m)")
    surface.set_ylabel("North (m)")
    surface.zaxis.set_major_formatter(
        FuncFormatter(
            lambda value, _position: f"{minimum + (value - minimum) / vertical_exaggeration:.1f}"
        )
    )
    surface.view_init(elev=34, azim=-132)

    middle_row = elevation.shape[0] // 2
    middle_column = elevation.shape[1] // 2
    profiles.plot(
        elevation_x - elevation_x[0],
        elevation[middle_row, :],
        color="#d95f02",
        linewidth=1.5,
        label="E–W middle-row profile",
    )
    profiles.plot(
        np.abs(elevation_y - elevation_y[0]),
        elevation[:, middle_column],
        color="#1b9e77",
        linewidth=1.5,
        label="N–S middle-column profile",
    )
    profiles.set_title("Continuous elevation profiles")
    profiles.set_xlabel("Distance from profile origin (m)")
    profiles.set_ylabel("Elevation (m)")
    profiles.grid(alpha=0.25)
    profiles.legend(fontsize=8)

    coordinate_metrics = metrics["coordinate_metrics"]
    evidence.axis("off")
    lines = [
        "Machine evidence",
        f"lineage accepted: {metrics['lineage_flags']['accepted']}",
        f"DEM finite: {metrics['dem']['finite_ratio']:.6f}",
        f"DEM range: {metrics['dem']['min_m']:.3f}–{metrics['dem']['max_m']:.3f} m",
        "Land cover: nearest categorical (no numeric interpolation)",
    ]
    for feature_class in ("road", "building", "hydrology"):
        item = coordinate_metrics[feature_class]
        lines.append(
            f"{feature_class}: int-x={item['integer_x_ratio']:.3f}, "
            f"int-y={item['integer_y_ratio']:.3f}, grid-RMSE={item['nearest_1m_grid_rmse_m']:.3f} m"
        )
    lines.extend(
        [
            f"3D draped paths: {draped_path_count}",
            f"bundle: {bundle.get('bundle_id', '<unidentified>')}",
        ]
    )
    evidence.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        ha="left",
        family="monospace",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "#f7f7f7", "edgecolor": "#555555"},
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(image_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return draped_path_count


def _static_scene_limits(
    static_scene: dict[str, Any], elevation: np.ndarray
) -> tuple[float, float]:
    finite = elevation[np.isfinite(elevation)].astype(np.float64)
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    for item in static_scene["objects"]:
        geometry = item.get("static_geometry")
        if item.get("status") != "resolved" or not isinstance(geometry, dict):
            continue
        if geometry.get("kind") == "rigid_prism":
            maximum = max(maximum, float(geometry["top_elevation_m"]))
            minimum = min(minimum, float(geometry["base_elevation_m"]))
    return minimum, maximum


def _draw_static_building(
    ax: Any,
    item: dict[str, Any],
    poly3d_collection: Any,
) -> int:
    geometry = item["static_geometry"]
    base = float(geometry["base_elevation_m"])
    top = float(geometry["top_elevation_m"])
    faces: list[list[tuple[float, float, float]]] = []
    outer_count = 0
    for role, path in _geometry_paths(geometry["footprint_geometry_xy"]):
        if role != "polygon_outer":
            continue
        open_path = path[:-1] if path[0] == path[-1] else path
        if len(open_path) < 3:
            continue
        roof = [(point[0], point[1], top) for point in open_path]
        faces.append(roof)
        for start, end in zip(open_path, open_path[1:] + open_path[:1]):
            faces.append(
                [
                    (start[0], start[1], base),
                    (end[0], end[1], base),
                    (end[0], end[1], top),
                    (start[0], start[1], top),
                ]
            )
        outer_count += 1
    if faces:
        ax.add_collection3d(
            poly3d_collection(
                faces,
                facecolors="#a6a6a6",
                edgecolors="#3a3a3a",
                linewidths=0.28,
                alpha=0.76,
            )
        )
    return outer_count


def _draw_static_scene_3d(
    ax: Any,
    *,
    static_scene: dict[str, Any],
    elevation: np.ndarray,
    elevation_x: np.ndarray,
    elevation_y: np.ndarray,
) -> dict[str, int]:
    try:
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError as exc:  # pragma: no cover - imported with matplotlib
        raise ContinuousBundleVisualizationError(
            "static scene visualization requires mpl_toolkits.mplot3d"
        ) from exc

    finite = elevation[np.isfinite(elevation)].astype(np.float64)
    filled = np.where(np.isfinite(elevation), elevation, np.mean(finite)).astype(np.float64)
    stride = max(1, math.ceil(max(elevation.shape) / 150))
    mesh_x, mesh_y = np.meshgrid(elevation_x[::stride], elevation_y[::stride])
    ax.plot_surface(
        mesh_x,
        mesh_y,
        filled[::stride, ::stride],
        cmap="terrain",
        linewidth=0,
        antialiased=True,
        alpha=0.52,
    )
    drawn = {
        "building_prisms": 0,
        "road_corridor_quads": 0,
        "bridge_deck_quads": 0,
        "hydrology_paths": 0,
    }
    road_faces: list[list[tuple[float, float, float]]] = []
    bridge_faces: list[list[tuple[float, float, float]]] = []
    hydrology_faces: list[list[tuple[float, float, float]]] = []
    for item in static_scene["objects"]:
        if item.get("status") != "resolved":
            continue
        geometry = item.get("static_geometry")
        if not isinstance(geometry, dict):
            continue
        kind = geometry.get("kind")
        if kind == "rigid_prism":
            drawn["building_prisms"] += _draw_static_building(ax, item, Poly3DCollection)
        elif kind == "terrain_draped_corridor":
            for segment in geometry["corridor_segments"]:
                road_faces.append([tuple(point) for point in segment["polygon_xyz"]])
                drawn["road_corridor_quads"] += 1
        elif kind == "abutment_interpolated_deck":
            for segment in geometry["corridor_segments"]:
                bridge_faces.append([tuple(point) for point in segment["polygon_xyz"]])
                drawn["bridge_deck_quads"] += 1
        elif kind == "source_geometry_dem_display_drape":
            for path in geometry["display_paths_xyz"]:
                coordinates = [tuple(point) for point in path["coordinates_xyz"]]
                role = path["role"]
                if role == "polygon_outer" or role.startswith("polygon_outer:"):
                    hydrology_faces.append(coordinates)
                else:
                    array = np.asarray(coordinates, dtype=np.float64)
                    ax.plot(
                        array[:, 0],
                        array[:, 1],
                        array[:, 2],
                        color="#0077cc",
                        linewidth=0.9,
                        alpha=0.9,
                    )
                drawn["hydrology_paths"] += 1
    if road_faces:
        ax.add_collection3d(
            Poly3DCollection(
                road_faces,
                facecolors="#f4a340",
                edgecolors="#d57c08",
                linewidths=0.18,
                alpha=0.82,
            )
        )
    if bridge_faces:
        ax.add_collection3d(
            Poly3DCollection(
                bridge_faces,
                facecolors="#8fd0d0",
                edgecolors="#3f9c9c",
                linewidths=0.24,
                alpha=0.9,
            )
        )
    if hydrology_faces:
        ax.add_collection3d(
            Poly3DCollection(
                hydrology_faces,
                facecolors="#42a5f5",
                edgecolors="#0066cc",
                linewidths=0.3,
                alpha=0.58,
            )
        )
    return drawn


def _draw_static_plan(
    ax: Any,
    static_scene: dict[str, Any],
    elevation: np.ndarray,
    elevation_x: np.ndarray,
    elevation_y: np.ndarray,
    polygon_type: Any,
) -> None:
    finite = elevation[np.isfinite(elevation)].astype(np.float64)
    filled = np.where(np.isfinite(elevation), elevation, np.mean(finite)).astype(np.float64)
    ax.imshow(
        filled,
        extent=_extent(elevation_x, elevation_y),
        origin="lower" if elevation_y[-1] > elevation_y[0] else "upper",
        cmap="terrain",
        interpolation="bilinear",
        alpha=0.78,
    )
    for item in static_scene["objects"]:
        status = item["status"]
        feature_class = item["feature_class"]
        geometry = item["source_geometry_xy"]
        for role, path in _geometry_paths(geometry):
            coordinates = np.asarray(path, dtype=np.float64)
            if status == "held":
                ax.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    color="#d62728",
                    linewidth=0.65,
                    linestyle="--",
                    alpha=0.8,
                )
            elif feature_class == "road":
                ax.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    color="#f4a340",
                    linewidth=0.85,
                    alpha=0.82,
                )
            elif role == "polygon_outer":
                colors = {
                    "building": ("#b8b8b8", "#222222"),
                    "hydrology": ("#42a5f5", "#0066cc"),
                }
                face, edge = colors[feature_class]
                ax.add_patch(
                    polygon_type(
                        coordinates,
                        closed=True,
                        facecolor=face,
                        edgecolor=edge,
                        linewidth=0.45,
                        alpha=0.55,
                    )
                )
            else:
                ax.plot(
                    coordinates[:, 0],
                    coordinates[:, 1],
                    color="#0066cc",
                    linewidth=0.7,
                    alpha=0.8,
                )
    ax.set_title("Resolved source XY; held objects dashed red")
    ax.set_xlabel("East (m)")
    ax.set_ylabel("North (m)")
    ax.set_aspect("equal", adjustable="box")


def _render_static_scene(
    image_path: Path,
    *,
    static_scene: dict[str, Any],
    elevation: np.ndarray,
    elevation_x: np.ndarray,
    elevation_y: np.ndarray,
) -> dict[str, int]:
    plt, _cm, _color_types, patch_types, _formatter, _matplotlib = _ensure_matplotlib()
    _patch, Polygon = patch_types
    figure = plt.figure(figsize=(16, 9), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, width_ratios=(1.7, 1.0), height_ratios=(1.45, 1.0))
    scene = figure.add_subplot(grid[:, 0], projection="3d")
    plan = figure.add_subplot(grid[0, 1])
    evidence = figure.add_subplot(grid[1, 1])
    figure.suptitle(
        f"{STATIC_SCENE_PREVIEW_TITLE}\nTrue metre Z scale; no vertical exaggeration",
        fontsize=15,
        fontweight="bold",
    )
    drawn = _draw_static_scene_3d(
        scene,
        static_scene=static_scene,
        elevation=elevation,
        elevation_x=elevation_x,
        elevation_y=elevation_y,
    )
    minimum_z, maximum_z = _static_scene_limits(static_scene, elevation)
    x_extent = _extent(elevation_x, elevation_y)
    span_x = x_extent[1] - x_extent[0]
    span_y = x_extent[3] - x_extent[2]
    span_z = max(maximum_z - minimum_z, 1.0)
    scene.set_xlim(x_extent[0], x_extent[1])
    scene.set_ylim(x_extent[2], x_extent[3])
    scene.set_zlim(minimum_z, maximum_z + max(span_z * 0.025, 0.25))
    scene.set_box_aspect((span_x, span_y, span_z))
    scene.set_title("Derived static geometry at actual metre proportions")
    scene.set_xlabel("East (m)")
    scene.set_ylabel("North (m)")
    scene.set_zlabel("Elevation (m)")
    scene.view_init(elev=28, azim=-128)
    _draw_static_plan(plan, static_scene, elevation, elevation_x, elevation_y, Polygon)

    summary = static_scene["summary"]
    evidence.axis("off")
    lines = [
        "Static scene derivation evidence",
        f"release: {static_scene['release']['state']}",
        f"resolved: {summary['resolved']} / {summary['total']}",
        f"held: {summary['held']} / {summary['total']}",
    ]
    for feature_class in ("building", "road", "hydrology"):
        counts = summary["by_feature_class"][feature_class]
        lines.append(f"{feature_class}: resolved={counts['resolved']}, held={counts['held']}")
    lines.extend(
        [
            f"building prisms drawn: {drawn['building_prisms']}",
            f"road corridor polygons drawn: {drawn['road_corridor_quads']}",
            f"hydrology paths drawn: {drawn['hydrology_paths']}",
            "building XY: source footprint unchanged",
            "building base: median(vertices + centroid DEM)",
            "roads: per-segment corridor, DEM-extent clipped and draped",
            "hydrology Z: preview-only DEM sample",
            "collision / LOS / pathfinding: NOT RELEASED",
        ]
    )
    evidence.text(
        0.02,
        0.98,
        "\n".join(lines),
        va="top",
        ha="left",
        family="monospace",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "#f7f7f7", "edgecolor": "#555555"},
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(image_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return drawn


def visualize_continuous_bundle(
    bundle_root: Path,
    output_dir: Path,
    *,
    vertical_exaggeration: float = 8.0,
) -> dict[str, Any]:
    bundle_root = bundle_root.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not math.isfinite(vertical_exaggeration) or vertical_exaggeration <= 0.0:
        raise ContinuousBundleVisualizationError(
            "vertical exaggeration must be finite and positive"
        )
    bundle = _load_json(bundle_root / "bundle.json")
    lineage_flags = _validate_lineage(bundle)
    artifacts = _artifact_list(bundle)
    elevation_artifact = _one_artifact(artifacts, kind="elevation_raster")
    landcover_artifact = _one_artifact(artifacts, kind="landcover_raster")
    elevation, elevation_x, elevation_y = _read_elevation(bundle_root, elevation_artifact)
    landcover, landcover_x, landcover_y = _read_landcover(bundle_root, landcover_artifact)
    vector_artifacts = {
        feature_class: _one_artifact(
            artifacts,
            kind="vector_features",
            feature_class=feature_class,
        )
        for feature_class in ("road", "building", "hydrology")
    }
    vectors = {
        feature_class: _read_vector_file(
            bundle_root,
            vector_artifacts[feature_class],
            feature_class,
        )
        for feature_class in ("road", "building", "hydrology")
    }
    try:
        static_scene = derive_static_scene_geometry(
            bundle=bundle,
            elevation=elevation,
            elevation_x=elevation_x,
            elevation_y=elevation_y,
            elevation_artifact=elevation_artifact,
            vectors=vectors,
            vector_artifacts=vector_artifacts,
        )
    except StaticSceneDerivationError as exc:
        raise ContinuousBundleVisualizationError(
            f"static scene derivation failed closed: {exc}"
        ) from exc
    metrics: dict[str, Any] = {
        "contract_version": "cmo.continuous_bundle_preview_metrics.v1",
        "bundle_id": bundle.get("bundle_id"),
        "coordinate_frame": bundle.get("coordinate_frame"),
        "lineage_flags": lineage_flags,
        "coordinate_metrics": {
            feature_class: _coordinate_metrics(document)
            for feature_class, document in vectors.items()
        },
        "dem": _elevation_metrics(elevation),
        "landcover": _landcover_metrics(landcover),
        "visualization": {
            "title": CONTINUOUS_PREVIEW_TITLE,
            "vertical_exaggeration": float(vertical_exaggeration),
            "vertical_exaggeration_scope": "3d_panel_only",
            "runtime_authority": False,
        },
        "static_scene": {
            "contract_version": STATIC_SCENE_CONTRACT,
            "release_state": STATIC_SCENE_RELEASE_STATE,
            "runtime_authority": False,
            "preview_title": STATIC_SCENE_PREVIEW_TITLE,
            "summary": static_scene["summary"],
            "methods": static_scene["methods"],
        },
    }
    image_path = output_dir / "continuous_field_overlay.png"
    metrics_path = output_dir / "continuous_field_metrics.json"
    static_geometry_path = output_dir / "static_scene_geometry.json"
    static_preview_path = output_dir / "static_scene_preview.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    static_geometry_path.write_text(
        json.dumps(static_scene, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    draped_path_count = _render_figure(
        image_path,
        bundle=bundle,
        elevation=elevation,
        elevation_x=elevation_x,
        elevation_y=elevation_y,
        landcover=landcover,
        landcover_x=landcover_x,
        landcover_y=landcover_y,
        vectors=vectors,
        metrics=metrics,
        vertical_exaggeration=vertical_exaggeration,
    )
    metrics["visualization"]["draped_vector_path_count"] = draped_path_count
    static_drawn = _render_static_scene(
        static_preview_path,
        static_scene=static_scene,
        elevation=elevation,
        elevation_x=elevation_x,
        elevation_y=elevation_y,
    )
    metrics["static_scene"]["preview_drawn"] = static_drawn
    metrics["static_scene"]["geometry_path"] = static_geometry_path.name
    metrics["static_scene"]["preview_path"] = static_preview_path.name
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "image_path": image_path,
        "metrics": metrics,
        "metrics_path": metrics_path,
        "static_geometry_path": static_geometry_path,
        "static_preview_path": static_preview_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a fail-closed continuous Arnis/CMO bundle preview"
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--vertical-exaggeration", type=float, default=8.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = visualize_continuous_bundle(
            args.bundle,
            args.output_dir,
            vertical_exaggeration=args.vertical_exaggeration,
        )
    except ContinuousBundleVisualizationError as exc:
        print(f"Arnis continuous preview failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "image": str(result["image_path"]),
                "metrics": str(result["metrics_path"]),
                "static_geometry": str(result["static_geometry_path"]),
                "static_preview": str(result["static_preview_path"]),
                "valid": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
