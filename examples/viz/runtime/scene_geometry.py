"""Display-only unified scene geometry for the viz frontend.

Converts a pinned ``arnis_cmo_bundle.v1`` directory into one compact payload
the tactical map (2D) and inspection scene (3D) can render: a downsampled
terrain heightfield with land-cover classes plus the resolved static-scene
vectors (building prisms, DEM-draped road centerlines, hydrology surfaces).

The bundle is loaded through the fail-closed readers maintained in
``tools.environment.arnis.visualize`` (SHA-256 + lineage validation) and the
geometry derivation reuses ``cmo.static_scene_geometry.v1``. Held objects are
reported as counts only and never rendered. Nothing here feeds back into the
runtime: the payload carries the same display-only evidence flags as the
existing G0 viz overlays.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from tools.environment.arnis.static_scene import derive_static_scene_geometry
from tools.environment.arnis.visualize import (
    ContinuousBundleVisualizationError,
    _artifact_list,
    _load_json,
    _one_artifact,
    _read_elevation,
    _read_landcover,
    _read_vector_file,
    _validate_lineage,
)

VIZ_SCENE_GEOMETRY_CONTRACT_VERSION = "examples.viz.scene_geometry.arnis_static_scene.v1"

# Keep the transported heightfield small enough for a single REST response;
# the source DEM stays authoritative inside the bundle.
MAX_TERRAIN_GRID_DIM = 168

_EVIDENCE = {
    "source": "arnis_cmo_bundle.static_scene_geometry",
    "display_only": True,
    "no_runtime_setup_application": True,
    "no_runtime_consumer_release": True,
    "no_movement_release": True,
    "no_los_cover_release": True,
    "no_held_capability_release": True,
}


class SceneGeometryError(RuntimeError):
    pass


def _round3(value: float) -> float:
    return round(float(value), 3)


def _points_xy(path: list[list[float]]) -> list[list[float]]:
    return [[_round3(point[0]), _round3(point[1])] for point in path]


def _points_xyz(path: list[list[float]]) -> list[list[float]]:
    return [[_round3(point[0]), _round3(point[1]), _round3(point[2])] for point in path]


def _bilinear_resample(grid: np.ndarray, row_pos: np.ndarray, col_pos: np.ndarray) -> np.ndarray:
    r0 = np.floor(row_pos).astype(int)
    c0 = np.floor(col_pos).astype(int)
    r1 = np.minimum(r0 + 1, grid.shape[0] - 1)
    c1 = np.minimum(c0 + 1, grid.shape[1] - 1)
    tr = (row_pos - r0)[:, None]
    tc = (col_pos - c0)[None, :]
    return (
        grid[np.ix_(r0, c0)] * (1.0 - tr) * (1.0 - tc)
        + grid[np.ix_(r0, c1)] * (1.0 - tr) * tc
        + grid[np.ix_(r1, c0)] * tr * (1.0 - tc)
        + grid[np.ix_(r1, c1)] * tr * tc
    )


def _terrain_payload(
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    landcover: np.ndarray | None,
    landcover_legend: dict[str, str],
    *,
    max_dim: int = MAX_TERRAIN_GRID_DIM,
) -> dict[str, Any]:
    rows, cols = elevation.shape
    finite = elevation[np.isfinite(elevation)]
    if finite.size == 0:
        raise SceneGeometryError("terrain heightfield contains no finite samples")
    filled = np.where(np.isfinite(elevation), elevation, float(np.min(finite)))

    # Per-axis endpoint-preserving resample onto a uniform target grid: a
    # single shared stride would collapse long, narrow rasters to one sample
    # wide and drop the final east/south samples. Bilinear resampling keeps
    # both endpoints exactly and stays uniform, so the frontend's
    # origin+step*i coordinate model remains valid.
    target_rows = int(min(rows, max_dim))
    target_cols = int(min(cols, max_dim))
    row_pos = np.linspace(0.0, rows - 1.0, target_rows)
    col_pos = np.linspace(0.0, cols - 1.0, target_cols)
    heights = _bilinear_resample(filled, row_pos, col_pos)

    x_start, x_end = float(x_axis[0]), float(x_axis[-1])
    y_start, y_end = float(y_axis[0]), float(y_axis[-1])

    payload: dict[str, Any] = {
        "rows": int(target_rows),
        "cols": int(target_cols),
        "origin_x": _round3(x_start),
        "origin_y": _round3(y_start),
        "step_x": (x_end - x_start) / max(1, target_cols - 1),
        "step_y": (y_end - y_start) / max(1, target_rows - 1),
        "source_shape": [int(rows), int(cols)],
        "downsample_step": max(
            1, int(math.ceil(rows / float(target_rows))), int(math.ceil(cols / float(target_cols)))
        ),
        "sampling": "bilinear_endpoint_preserving_per_axis",
        "min_m": _round3(np.min(finite)),
        "max_m": _round3(np.max(finite)),
        "heights": [[_round3(v) for v in row] for row in heights.tolist()],
    }
    if landcover is not None:
        # Categories resample nearest-neighbor onto the same target grid so
        # land cover stays aligned with the height samples.
        row_idx = np.round(row_pos).astype(int)
        col_idx = np.round(col_pos).astype(int)
        classes = landcover[np.ix_(row_idx, col_idx)]
        payload["landcover"] = {
            "legend": dict(landcover_legend),
            "sampling": "nearest_category_only",
            "values": [[int(v) for v in row] for row in classes.tolist()],
        }
    return payload


def _geodetic_anchor(bundle: dict[str, Any]) -> dict[str, Any] | None:
    """Bind the local ENU frame to the globe.

    Strategic/operational-scale views will eventually place many local
    scenes on one geodetic globe; carrying the anchor now means every
    payload produced today stays placeable later. The Arnis projection
    normalizes the WGS84 bbox center to the local origin, so the bbox
    midpoint is the anchor of the ENU frame.
    """
    bbox = bundle.get("bbox_wgs84")
    if not isinstance(bbox, dict):
        return None
    try:
        min_lat = float(bbox["min_lat"])
        max_lat = float(bbox["max_lat"])
        min_lon = float(bbox["min_lon"])
        max_lon = float(bbox["max_lon"])
    except (KeyError, TypeError, ValueError):
        return None
    request = bundle.get("request") if isinstance(bundle.get("request"), dict) else {}
    return {
        "frame": "local_enu_m",
        "anchor_lat_deg": (min_lat + max_lat) / 2.0,
        "anchor_lon_deg": (min_lon + max_lon) / 2.0,
        "bbox_wgs84": {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        },
        "projection": str(request.get("projection") or ""),
        "source": "arnis_bundle_bbox_wgs84",
    }


def _held_summary(objects: list[dict[str, Any]]) -> dict[str, Any]:
    by_reason: dict[str, int] = {}
    for item in objects:
        if item.get("status") != "held":
            continue
        reason = str(item.get("hold_reason") or "unspecified")
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "total": int(sum(by_reason.values())),
        "by_reason": dict(sorted(by_reason.items())),
        "rendered": False,
    }


def _building_entry(item: dict[str, Any]) -> dict[str, Any] | None:
    geometry = item.get("static_geometry") or {}
    if geometry.get("kind") != "rigid_prism":
        return None
    footprint = geometry.get("footprint_geometry_xy") or {}
    rings: list[dict[str, Any]] = []
    geometry_type = footprint.get("type")
    coordinates = footprint.get("coordinates")
    if geometry_type == "Polygon" and isinstance(coordinates, list):
        polygons = [coordinates]
    elif geometry_type == "MultiPolygon" and isinstance(coordinates, list):
        polygons = coordinates
    else:
        return None
    for polygon_index, polygon in enumerate(polygons):
        if not isinstance(polygon, list) or not polygon:
            continue
        for ring_index, ring in enumerate(polygon):
            if not isinstance(ring, list):
                continue
            rings.append(
                {
                    "role": "outer" if ring_index == 0 else "hole",
                    # MultiPolygon grouping: holes belong to their own outer
                    # ring, not to whichever outer happens to come first.
                    "polygon": int(polygon_index),
                    "points": _points_xy(ring),
                }
            )
    if not rings:
        return None
    return {
        "id": str(item.get("object_id") or item.get("source_feature_id") or ""),
        "base_m": _round3(geometry.get("base_elevation_m", 0.0)),
        "top_m": _round3(geometry.get("top_elevation_m", 0.0)),
        "height_m": _round3(geometry.get("height_m", 0.0)),
        "rings": rings,
    }


_ROAD_KINDS = {
    "terrain_draped_corridor": "terrain_draped",
    "abutment_interpolated_deck": "bridge_deck",
}


def _corridor_polygons(geometry: dict[str, Any]) -> list[list[list[float]]]:
    segments = geometry.get("corridor_segments")
    if not isinstance(segments, list):
        return []
    polygons: list[list[list[float]]] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        polygon = segment.get("polygon_xyz")
        if isinstance(polygon, list) and len(polygon) >= 3:
            polygons.append(_points_xyz(polygon))
    return polygons


def _road_entry(item: dict[str, Any], attributes_by_feature: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    geometry = item.get("static_geometry") or {}
    kind = _ROAD_KINDS.get(str(geometry.get("kind") or ""))
    if kind is None:
        return None
    parts = geometry.get("centerline_parts_xyz")
    if not isinstance(parts, list) or not parts:
        return None
    source_attributes = attributes_by_feature.get(str(item.get("source_feature_id") or ""), {})
    return {
        "id": str(item.get("object_id") or item.get("source_feature_id") or ""),
        "kind": kind,
        "width_m": _round3(geometry.get("width_m", 2.0)),
        "highway_type": str(source_attributes.get("highway_type") or ""),
        "parts": [_points_xyz(part) for part in parts if isinstance(part, list)],
        "corridor": _corridor_polygons(geometry),
    }


def _water_entry(
    item: dict[str, Any], attributes_by_feature: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    geometry = item.get("static_geometry") or {}
    if geometry.get("kind") != "source_geometry_dem_display_drape":
        return None
    display_paths = geometry.get("display_paths_xyz")
    if not isinstance(display_paths, list) or not display_paths:
        return None
    source_attributes = attributes_by_feature.get(str(item.get("source_feature_id") or ""), {})
    # Linear watercourses (rivers/streams as LineStrings) carry an authored
    # width; polygon surfaces do not need one.
    try:
        width_m = float(source_attributes.get("width_m", 0.0) or 0.0)
    except (TypeError, ValueError):
        width_m = 0.0
    paths = []
    for path in display_paths:
        if not isinstance(path, dict):
            continue
        coordinates = path.get("coordinates_xyz")
        if not isinstance(coordinates, list):
            continue
        paths.append(
            {
                "role": str(path.get("role") or ""),
                "points": _points_xyz(coordinates),
            }
        )
    if not paths:
        return None
    entry: dict[str, Any] = {
        "id": str(item.get("object_id") or item.get("source_feature_id") or ""),
        "paths": paths,
    }
    if width_m > 0.0:
        entry["width_m"] = _round3(width_m)
    return entry


def load_scene_geometry_payload(
    bundle_ref: str,
    *,
    max_terrain_dim: int = MAX_TERRAIN_GRID_DIM,
) -> dict[str, Any]:
    """Load an arnis bundle directory into the display-only viz payload."""

    bundle_dir = Path(str(bundle_ref)).resolve()
    if not bundle_dir.is_dir():
        raise SceneGeometryError(f"environment bundle directory not found: {bundle_ref}")
    manifest_path = bundle_dir / "bundle.json"
    if not manifest_path.is_file():
        raise SceneGeometryError(f"bundle.json not found in environment bundle: {bundle_ref}")

    try:
        bundle = _load_json(manifest_path)
        _validate_lineage(bundle)
        artifacts = _artifact_list(bundle)
        elevation_artifact = _one_artifact(artifacts, kind="elevation_raster")
        elevation, x_axis, y_axis = _read_elevation(bundle_dir, elevation_artifact)
        landcover_artifact = _one_artifact(artifacts, kind="landcover_raster")
        landcover, _lc_x, _lc_y = _read_landcover(bundle_dir, landcover_artifact)
        vectors: dict[str, dict[str, Any]] = {}
        vector_artifacts: dict[str, dict[str, Any]] = {}
        for feature_class in ("road", "building", "hydrology"):
            artifact = _one_artifact(artifacts, kind="vector_features", feature_class=feature_class)
            vector_artifacts[feature_class] = artifact
            vectors[feature_class] = _read_vector_file(bundle_dir, artifact, feature_class)
        static_scene = derive_static_scene_geometry(
            bundle=bundle,
            elevation=elevation,
            elevation_x=x_axis,
            elevation_y=y_axis,
            elevation_artifact=elevation_artifact,
            vectors=vectors,
            vector_artifacts=vector_artifacts,
        )
    except ContinuousBundleVisualizationError as exc:
        raise SceneGeometryError(f"environment bundle rejected: {exc}") from exc

    legend = {}
    landcover_metadata = landcover_artifact.get("metadata")
    if isinstance(landcover_metadata, dict) and isinstance(
        landcover_metadata.get("class_legend"), dict
    ):
        legend = {str(k): str(v) for k, v in landcover_metadata["class_legend"].items()}

    road_attributes: dict[str, dict[str, Any]] = {}
    for feature in vectors["road"].get("features", []):
        if isinstance(feature, dict) and isinstance(feature.get("attributes"), dict):
            road_attributes[str(feature.get("feature_id") or "")] = feature["attributes"]

    water_attributes: dict[str, dict[str, Any]] = {}
    for feature in vectors["hydrology"].get("features", []):
        if isinstance(feature, dict) and isinstance(feature.get("attributes"), dict):
            water_attributes[str(feature.get("feature_id") or "")] = feature["attributes"]

    objects = static_scene.get("objects", [])
    buildings = []
    roads = []
    water = []
    for item in objects:
        if not isinstance(item, dict) or item.get("status") != "resolved":
            continue
        feature_class = item.get("feature_class")
        if feature_class == "building":
            entry = _building_entry(item)
            if entry is not None:
                buildings.append(entry)
        elif feature_class == "road":
            entry = _road_entry(item, road_attributes)
            if entry is not None:
                roads.append(entry)
        elif feature_class == "hydrology":
            entry = _water_entry(item, water_attributes)
            if entry is not None:
                water.append(entry)

    region_extent = bundle.get("region_extent") or {}

    return {
        "contract_version": VIZ_SCENE_GEOMETRY_CONTRACT_VERSION,
        "coordinate_frame": "local_enu_m",
        "bundle": {
            "path": os.path.relpath(bundle_dir, os.getcwd()) if bundle_dir.is_absolute() else str(bundle_dir),
            "bundle_id": str(bundle.get("bundle_id") or ""),
            "content_digest_sha256": str(bundle.get("content_digest_sha256") or ""),
            "static_scene_contract": str(static_scene.get("contract_version") or ""),
        },
        "region_extent": {
            "min_x": _round3(region_extent.get("min_x", 0.0)),
            "max_x": _round3(region_extent.get("max_x", 0.0)),
            "min_y": _round3(region_extent.get("min_y", 0.0)),
            "max_y": _round3(region_extent.get("max_y", 0.0)),
        },
        "geodetic_anchor": _geodetic_anchor(bundle),
        "terrain": _terrain_payload(
            elevation,
            x_axis,
            y_axis,
            landcover,
            legend,
            max_dim=max_terrain_dim,
        ),
        "buildings": buildings,
        "roads": roads,
        "water": water,
        "held": _held_summary(objects),
        "summary": static_scene.get("summary", {}),
        "evidence": dict(_EVIDENCE),
    }


__all__ = [
    "VIZ_SCENE_GEOMETRY_CONTRACT_VERSION",
    "MAX_TERRAIN_GRID_DIM",
    "SceneGeometryError",
    "load_scene_geometry_payload",
]
