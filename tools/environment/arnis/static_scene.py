from __future__ import annotations

import copy
import math
from typing import Any, Callable

import numpy as np


STATIC_SCENE_CONTRACT = "cmo.static_scene_geometry.v1"
STATIC_SCENE_RELEASE_STATE = "no_runtime_consumer_release"


class StaticSceneDerivationError(RuntimeError):
    pass


def _point(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise StaticSceneDerivationError(f"{label} must be [x, y]")
    try:
        point = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise StaticSceneDerivationError(f"{label} must contain numeric coordinates") from exc
    if not all(math.isfinite(item) for item in point):
        raise StaticSceneDerivationError(f"{label} must contain finite coordinates")
    return point


def _paths(
    geometry: Any,
) -> tuple[str, list[tuple[str, list[tuple[float, float]]]]]:
    if not isinstance(geometry, dict):
        raise StaticSceneDerivationError("feature geometry must be an object")
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    paths: list[tuple[str, list[tuple[float, float]]]] = []
    if geometry_type == "LineString":
        if not isinstance(coordinates, list):
            raise StaticSceneDerivationError("LineString coordinates must be a list")
        paths.append(("line", [_point(item, "LineString coordinate") for item in coordinates]))
    elif geometry_type == "MultiLineString":
        if not isinstance(coordinates, list):
            raise StaticSceneDerivationError("MultiLineString coordinates must be a list")
        for line in coordinates:
            if not isinstance(line, list):
                raise StaticSceneDerivationError("MultiLineString part must be a list")
            paths.append(("line", [_point(item, "MultiLineString coordinate") for item in line]))
    elif geometry_type == "Polygon":
        if not isinstance(coordinates, list):
            raise StaticSceneDerivationError("Polygon coordinates must be a list")
        for index, ring in enumerate(coordinates):
            if not isinstance(ring, list):
                raise StaticSceneDerivationError("Polygon ring must be a list")
            role = "polygon_outer" if index == 0 else "polygon_hole"
            paths.append((role, [_point(item, "Polygon coordinate") for item in ring]))
    elif geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list):
            raise StaticSceneDerivationError("MultiPolygon coordinates must be a list")
        for polygon_index, polygon in enumerate(coordinates):
            if not isinstance(polygon, list):
                raise StaticSceneDerivationError("MultiPolygon part must be a list")
            for ring_index, ring in enumerate(polygon):
                if not isinstance(ring, list):
                    raise StaticSceneDerivationError("MultiPolygon ring must be a list")
                role = (
                    f"polygon_outer:{polygon_index}"
                    if ring_index == 0
                    else f"polygon_hole:{polygon_index}"
                )
                paths.append((role, [_point(item, "MultiPolygon coordinate") for item in ring]))
    else:
        raise StaticSceneDerivationError(f"unsupported geometry type: {geometry_type!r}")
    for role, path in paths:
        minimum = 2 if role == "line" else 4
        if len(path) < minimum:
            raise StaticSceneDerivationError(f"{role} requires at least {minimum} vertices")
    return str(geometry_type), paths


def _bilinear_sample(
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    points: list[tuple[float, float]],
) -> np.ndarray:
    if not points:
        return np.asarray([], dtype=np.float64)
    coordinates = np.asarray(points, dtype=np.float64)
    fx = (coordinates[:, 0] - x_axis[0]) / (x_axis[1] - x_axis[0])
    fy = (coordinates[:, 1] - y_axis[0]) / (y_axis[1] - y_axis[0])
    valid = (
        (fx >= 0.0) & (fx <= elevation.shape[1] - 1) & (fy >= 0.0) & (fy <= elevation.shape[0] - 1)
    )
    sampled = np.full(len(points), np.nan, dtype=np.float64)
    if not np.any(valid):
        return sampled
    clipped_x = np.clip(fx[valid], 0.0, elevation.shape[1] - 1)
    clipped_y = np.clip(fy[valid], 0.0, elevation.shape[0] - 1)
    x0 = np.floor(clipped_x).astype(int)
    y0 = np.floor(clipped_y).astype(int)
    x1 = np.minimum(x0 + 1, elevation.shape[1] - 1)
    y1 = np.minimum(y0 + 1, elevation.shape[0] - 1)
    tx = clipped_x - x0
    ty = clipped_y - y0
    v00 = elevation[y0, x0].astype(np.float64)
    v10 = elevation[y0, x1].astype(np.float64)
    v01 = elevation[y1, x0].astype(np.float64)
    v11 = elevation[y1, x1].astype(np.float64)
    sampled[valid] = (
        v00 * (1.0 - tx) * (1.0 - ty)
        + v10 * tx * (1.0 - ty)
        + v01 * (1.0 - tx) * ty
        + v11 * tx * ty
    )
    return sampled


def _same_point(
    left: tuple[float, float],
    right: tuple[float, float],
) -> bool:
    return math.isclose(left[0], right[0], rel_tol=0.0, abs_tol=1.0e-12) and math.isclose(
        left[1], right[1], rel_tol=0.0, abs_tol=1.0e-12
    )


def _deduplicate_polygon(
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    deduplicated: list[tuple[float, float]] = []
    for point in points:
        if not deduplicated or not _same_point(deduplicated[-1], point):
            deduplicated.append(point)
    if len(deduplicated) >= 2 and _same_point(deduplicated[0], deduplicated[-1]):
        deduplicated.pop()
    return deduplicated


def _clip_polygon_edge(
    points: list[tuple[float, float]],
    *,
    inside: Callable[[tuple[float, float]], bool],
    intersection: Callable[[tuple[float, float], tuple[float, float]], tuple[float, float]],
) -> list[tuple[float, float]]:
    if not points:
        return []
    clipped: list[tuple[float, float]] = []
    previous = points[-1]
    previous_inside = inside(previous)
    for current in points:
        current_inside = inside(current)
        if current_inside:
            if not previous_inside:
                clipped.append(intersection(previous, current))
            clipped.append(current)
        elif previous_inside:
            clipped.append(intersection(previous, current))
        previous = current
        previous_inside = current_inside
    return _deduplicate_polygon(clipped)


def _clip_polygon_to_rectangle(
    points: list[tuple[float, float]],
    *,
    minimum_x: float,
    maximum_x: float,
    minimum_y: float,
    maximum_y: float,
) -> list[tuple[float, float]]:
    def vertical_intersection(
        start: tuple[float, float],
        end: tuple[float, float],
        boundary: float,
    ) -> tuple[float, float]:
        delta_x = end[0] - start[0]
        if abs(delta_x) <= 1.0e-15:
            return boundary, start[1]
        ratio = (boundary - start[0]) / delta_x
        return boundary, start[1] + ratio * (end[1] - start[1])

    def horizontal_intersection(
        start: tuple[float, float],
        end: tuple[float, float],
        boundary: float,
    ) -> tuple[float, float]:
        delta_y = end[1] - start[1]
        if abs(delta_y) <= 1.0e-15:
            return start[0], boundary
        ratio = (boundary - start[1]) / delta_y
        return start[0] + ratio * (end[0] - start[0]), boundary

    clipped = _deduplicate_polygon(points)
    clipped = _clip_polygon_edge(
        clipped,
        inside=lambda point: point[0] >= minimum_x,
        intersection=lambda start, end: vertical_intersection(start, end, minimum_x),
    )
    clipped = _clip_polygon_edge(
        clipped,
        inside=lambda point: point[0] <= maximum_x,
        intersection=lambda start, end: vertical_intersection(start, end, maximum_x),
    )
    clipped = _clip_polygon_edge(
        clipped,
        inside=lambda point: point[1] >= minimum_y,
        intersection=lambda start, end: horizontal_intersection(start, end, minimum_y),
    )
    clipped = _clip_polygon_edge(
        clipped,
        inside=lambda point: point[1] <= maximum_y,
        intersection=lambda start, end: horizontal_intersection(start, end, maximum_y),
    )
    return _deduplicate_polygon(clipped)


def _polygon_changed(
    original: list[tuple[float, float]],
    clipped: list[tuple[float, float]],
) -> bool:
    return len(original) != len(clipped) or any(
        not _same_point(left, right) for left, right in zip(original, clipped)
    )


def _required(attributes: dict[str, Any], key: str, feature_id: str) -> Any:
    if key not in attributes:
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} is missing required attribute {key!r}"
        )
    return attributes[key]


def _finite_number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise StaticSceneDerivationError(f"{label} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise StaticSceneDerivationError(f"{label} must be numeric") from exc
    if not math.isfinite(number) or (positive and number <= 0.0):
        qualifier = "finite and positive" if positive else "finite"
        raise StaticSceneDerivationError(f"{label} must be {qualifier}")
    return number


def _anchor(attributes: dict[str, Any], feature_id: str) -> dict[str, Any]:
    mode = _required(attributes, "vertical_anchor_mode", feature_id)
    resolved = _required(attributes, "vertical_placement_resolved", feature_id)
    source = _required(attributes, "vertical_anchor_source", feature_id)
    if not isinstance(mode, str) or not mode:
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} vertical_anchor_mode must be a non-empty string"
        )
    if not isinstance(resolved, bool):
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} vertical_placement_resolved must be boolean"
        )
    if not isinstance(source, str) or not source:
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} vertical_anchor_source must be a non-empty string"
        )
    return {"mode": mode, "placement_resolved": resolved, "source": source}


def _feature_identity(feature: dict[str, Any], feature_class: str) -> tuple[str, dict[str, Any]]:
    feature_id = feature.get("feature_id")
    attributes = feature.get("attributes")
    if not isinstance(feature_id, str) or not feature_id:
        raise StaticSceneDerivationError(f"{feature_class} feature_id must be a non-empty string")
    if not isinstance(attributes, dict):
        raise StaticSceneDerivationError(f"feature {feature_id!r} attributes must be an object")
    return feature_id, attributes


def _base_entry(
    feature: dict[str, Any],
    feature_class: str,
    anchor: dict[str, Any],
    vector_artifact: dict[str, Any],
    elevation_artifact: dict[str, Any],
) -> dict[str, Any]:
    feature_id = str(feature["feature_id"])
    return {
        "object_id": f"static:{feature_id}",
        "source_feature_id": feature_id,
        "feature_class": feature_class,
        "coordinate_frame": "local_enu_m",
        "anchor": anchor,
        "source_geometry_xy": copy.deepcopy(feature.get("geometry")),
        "lineage": {
            "source_vector_artifact_id": vector_artifact.get("artifact_id"),
            "source_vector_sha256": vector_artifact.get("sha256"),
            "source_elevation_artifact_id": elevation_artifact.get("artifact_id"),
            "source_elevation_sha256": elevation_artifact.get("sha256"),
            "xy_source_geometry_unchanged": True,
            "runtime_authority": False,
        },
    }


def _held(entry: dict[str, Any], reason: str) -> dict[str, Any]:
    entry.update(
        {
            "status": "held",
            "hold_reason": reason,
            "static_geometry": None,
        }
    )
    return entry


def _open_ring(path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(path) >= 2 and path[0] == path[-1]:
        return path[:-1]
    return path


def _ring_centroid(path: list[tuple[float, float]]) -> tuple[float, float]:
    points = _open_ring(path)
    if len(points) < 3:
        raise StaticSceneDerivationError("building outer ring requires three distinct vertices")
    twice_area = 0.0
    weighted_x = 0.0
    weighted_y = 0.0
    for start, end in zip(points, points[1:] + points[:1]):
        cross = start[0] * end[1] - end[0] * start[1]
        twice_area += cross
        weighted_x += (start[0] + end[0]) * cross
        weighted_y += (start[1] + end[1]) * cross
    if abs(twice_area) <= 1.0e-12:
        return (
            float(sum(point[0] for point in points) / len(points)),
            float(sum(point[1] for point in points) / len(points)),
        )
    return weighted_x / (3.0 * twice_area), weighted_y / (3.0 * twice_area)


def _derive_building(
    feature: dict[str, Any],
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    vector_artifact: dict[str, Any],
    elevation_artifact: dict[str, Any],
) -> dict[str, Any]:
    feature_id, attributes = _feature_identity(feature, "building")
    anchor = _anchor(attributes, feature_id)
    geometry_type, paths = _paths(feature.get("geometry"))
    entry = _base_entry(feature, "building", anchor, vector_artifact, elevation_artifact)
    if not anchor["placement_resolved"]:
        return _held(entry, "vertical_placement_unresolved")
    if anchor["mode"] != "terrain_rigid":
        return _held(entry, "unsupported_building_vertical_anchor_mode")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        return _held(entry, "building_footprint_not_polygonal")

    base_offset = _finite_number(
        _required(attributes, "base_offset_m", feature_id),
        f"feature {feature_id!r} base_offset_m",
    )
    if base_offset < 0.0:
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} base_offset_m must be non-negative"
        )
    base_offset_source = _required(attributes, "base_offset_source", feature_id)
    if not isinstance(base_offset_source, str) or not base_offset_source:
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} base_offset_source must be a non-empty string"
        )
    height = _finite_number(
        _required(attributes, "height_m", feature_id),
        f"feature {feature_id!r} height_m",
        positive=True,
    )
    entry["anchor"]["base_offset_m"] = base_offset
    entry["anchor"]["base_offset_source"] = base_offset_source

    sample_points: list[tuple[float, float]] = []
    for role, path in paths:
        sample_points.extend(_open_ring(path))
        if role == "polygon_outer" or role.startswith("polygon_outer:"):
            sample_points.append(_ring_centroid(path))
    sampled = _bilinear_sample(elevation, x_axis, y_axis, sample_points)
    if not np.isfinite(sampled).all():
        return _held(entry, "building_foundation_outside_finite_dem")
    terrain_anchor = float(np.median(sampled))
    base_elevation = terrain_anchor + base_offset
    entry.update(
        {
            "status": "resolved",
            "static_geometry": {
                "kind": "rigid_prism",
                "footprint_geometry_xy": copy.deepcopy(feature.get("geometry")),
                "xy_interpolation_applied": False,
                "base_elevation_m": base_elevation,
                "top_elevation_m": base_elevation + height,
                "height_m": height,
                "foundation": {
                    "method": "median_of_footprint_vertices_and_outer_centroids_bilinear_dem",
                    "sample_count": int(sampled.size),
                    "terrain_sample_min_m": float(np.min(sampled)),
                    "terrain_sample_max_m": float(np.max(sampled)),
                    "terrain_sample_median_m": terrain_anchor,
                    "relief_m": float(np.max(sampled) - np.min(sampled)),
                },
            },
        }
    )
    return entry


def _polyline_arc_lengths(path: list[tuple[float, float]]) -> list[float] | None:
    lengths = [0.0]
    for start, end in zip(path, path[1:]):
        step = math.hypot(end[0] - start[0], end[1] - start[1])
        if step <= 1.0e-12:
            return None
        lengths.append(lengths[-1] + step)
    return lengths


def _derive_bridge_deck(
    entry: dict[str, Any],
    paths: list[tuple[str, list[tuple[float, float]]]],
    width: float,
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
) -> dict[str, Any]:
    """Resolve a bridge deck by interpolating between abutment DEM anchors.

    The only trusted vertical references for an OSM bridge are the two points
    where the deck meets the terrain-connected road network. Both centerline
    endpoints are sampled from the DEM and the deck elevation is interpolated
    linearly along the centerline arc length (simply-supported approximation).
    No measured deck elevation is claimed; lineage records the interpolation.
    Corridor polygons reuse the per-segment width expansion but take their Z
    from the interpolated deck profile instead of the terrain.
    """

    half_width = width * 0.5
    centerline_parts_xyz: list[list[list[float]]] = []
    corridor_segments: list[dict[str, Any]] = []
    abutments: list[dict[str, Any]] = []
    for part_index, (_role, path) in enumerate(paths):
        lengths = _polyline_arc_lengths(path)
        if lengths is None:
            return _held(entry, "bridge_contains_degenerate_segment")
        total_length = lengths[-1]
        if total_length <= 1.0e-9:
            return _held(entry, "bridge_centerline_degenerate")
        anchors = _bilinear_sample(elevation, x_axis, y_axis, [path[0], path[-1]])
        if not np.isfinite(anchors).all():
            return _held(entry, "bridge_abutment_outside_finite_dem")
        start_z = float(anchors[0])
        end_z = float(anchors[1])
        deck_z = [
            start_z + (end_z - start_z) * (length / total_length)
            for length in lengths
        ]
        abutments.append(
            {
                "part_index": part_index,
                "start_elevation_m": start_z,
                "end_elevation_m": end_z,
                "span_length_m": total_length,
            }
        )
        centerline_parts_xyz.append(
            [[point[0], point[1], z] for point, z in zip(path, deck_z)]
        )
        for segment_index, (start, end) in enumerate(zip(path, path[1:])):
            delta_x = end[0] - start[0]
            delta_y = end[1] - start[1]
            length = math.hypot(delta_x, delta_y)
            normal_x = -delta_y / length * half_width
            normal_y = delta_x / length * half_width
            z_start = deck_z[segment_index]
            z_end = deck_z[segment_index + 1]
            corridor_segments.append(
                {
                    "source_part_index": part_index,
                    "source_segment_index": segment_index,
                    "clipped_to_dem_extent": False,
                    "polygon_xyz": [
                        [start[0] + normal_x, start[1] + normal_y, z_start],
                        [start[0] - normal_x, start[1] - normal_y, z_start],
                        [end[0] - normal_x, end[1] - normal_y, z_end],
                        [end[0] + normal_x, end[1] + normal_y, z_end],
                    ],
                }
            )
    entry.update(
        {
            "status": "resolved",
            "static_geometry": {
                "kind": "abutment_interpolated_deck",
                "width_m": width,
                "centerline_geometry_xy": copy.deepcopy(entry.get("source_geometry_xy")),
                "centerline_xy_interpolation_applied": False,
                "centerline_parts_xyz": centerline_parts_xyz,
                "corridor_segments": corridor_segments,
                "corridor_clipped_to_dem_extent": False,
                "clipped_segment_count": 0,
                "skipped_segment_count": 0,
                "deck_profile": {
                    "method": "linear_interpolation_between_abutment_dem_anchors",
                    "abutments": abutments,
                    "deck_elevation_measured": False,
                },
                "drape_method": (
                    "abutment_dem_anchors_with_linear_arc_length_deck_interpolation"
                ),
            },
        }
    )
    return entry


def _derive_road(
    feature: dict[str, Any],
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    vector_artifact: dict[str, Any],
    elevation_artifact: dict[str, Any],
) -> dict[str, Any]:
    feature_id, attributes = _feature_identity(feature, "road")
    anchor = _anchor(attributes, feature_id)
    width = _finite_number(
        _required(attributes, "width_m", feature_id),
        f"feature {feature_id!r} width_m",
        positive=True,
    )
    layer = _required(attributes, "layer", feature_id)
    if (
        isinstance(layer, bool)
        or not isinstance(layer, (int, float))
        or not math.isfinite(float(layer))
        or not float(layer).is_integer()
    ):
        raise StaticSceneDerivationError(f"feature {feature_id!r} layer must be a finite integer")
    bridge = _required(attributes, "bridge", feature_id)
    tunnel = _required(attributes, "tunnel", feature_id)
    covered = _required(attributes, "covered", feature_id)
    if (
        not isinstance(bridge, bool)
        or not isinstance(tunnel, bool)
        or not isinstance(covered, bool)
    ):
        raise StaticSceneDerivationError(
            f"feature {feature_id!r} bridge, tunnel, and covered must be boolean"
        )
    geometry_type, paths = _paths(feature.get("geometry"))
    entry = _base_entry(feature, "road", anchor, vector_artifact, elevation_artifact)
    entry["anchor"].update({"layer": layer, "bridge": bridge, "tunnel": tunnel, "covered": covered})
    if anchor["mode"] == "elevated_profile" or float(layer) > 0.0:
        # Phase 2: bridges gain a deterministic deck derived from the two
        # abutment DEM anchors. Non-bridge elevated profiles (for example
        # positive-layer building passages) still lack a trustworthy vertical
        # reference and remain held.
        if (
            bridge
            and not tunnel
            and float(layer) > 0.0
            and geometry_type in {"LineString", "MultiLineString"}
        ):
            return _derive_bridge_deck(
                entry,
                paths,
                width,
                elevation,
                x_axis,
                y_axis,
            )
        return _held(entry, "elevated_profile_unresolved")
    if bridge:
        return _held(entry, "bridge_elevation_profile_unresolved")
    if anchor["mode"] == "subsurface_profile" or tunnel or float(layer) < 0.0:
        return _held(entry, "subsurface_profile_unresolved")
    if not anchor["placement_resolved"]:
        return _held(entry, "vertical_placement_unresolved")
    if anchor["mode"] != "terrain_draped":
        return _held(entry, "unsupported_road_vertical_anchor_mode")
    if geometry_type not in {"LineString", "MultiLineString"}:
        return _held(entry, "road_centerline_not_linear")

    centerline_parts_xyz: list[list[list[float]]] = []
    corridor_segments: list[dict[str, Any]] = []
    clipped_segment_count = 0
    skipped_segment_count = 0
    half_width = width * 0.5
    minimum_x = float(min(x_axis[0], x_axis[-1]))
    maximum_x = float(max(x_axis[0], x_axis[-1]))
    minimum_y = float(min(y_axis[0], y_axis[-1]))
    maximum_y = float(max(y_axis[0], y_axis[-1]))
    for part_index, (_role, path) in enumerate(paths):
        centerline_z = _bilinear_sample(elevation, x_axis, y_axis, path)
        if not np.isfinite(centerline_z).all():
            return _held(entry, "road_centerline_outside_finite_dem")
        centerline_parts_xyz.append(
            [[point[0], point[1], float(z)] for point, z in zip(path, centerline_z)]
        )
        for segment_index, (start, end) in enumerate(zip(path, path[1:])):
            delta_x = end[0] - start[0]
            delta_y = end[1] - start[1]
            length = math.hypot(delta_x, delta_y)
            if length <= 1.0e-12:
                return _held(entry, "road_contains_degenerate_segment")
            normal_x = -delta_y / length * half_width
            normal_y = delta_x / length * half_width
            quad_xy = [
                (start[0] + normal_x, start[1] + normal_y),
                (start[0] - normal_x, start[1] - normal_y),
                (end[0] - normal_x, end[1] - normal_y),
                (end[0] + normal_x, end[1] + normal_y),
            ]
            corridor_xy = _clip_polygon_to_rectangle(
                quad_xy,
                minimum_x=minimum_x,
                maximum_x=maximum_x,
                minimum_y=minimum_y,
                maximum_y=maximum_y,
            )
            clipped_to_extent = _polygon_changed(quad_xy, corridor_xy)
            if clipped_to_extent:
                clipped_segment_count += 1
            if len(corridor_xy) < 3:
                skipped_segment_count += 1
                continue
            corridor_z = _bilinear_sample(elevation, x_axis, y_axis, corridor_xy)
            if not np.isfinite(corridor_z).all():
                skipped_segment_count += 1
                continue
            corridor_segments.append(
                {
                    "source_part_index": part_index,
                    "source_segment_index": segment_index,
                    "clipped_to_dem_extent": clipped_to_extent,
                    "polygon_xyz": [
                        [point[0], point[1], float(z)] for point, z in zip(corridor_xy, corridor_z)
                    ],
                }
            )
    entry.update(
        {
            "status": "resolved",
            "static_geometry": {
                "kind": "terrain_draped_corridor",
                "width_m": width,
                "centerline_geometry_xy": copy.deepcopy(feature.get("geometry")),
                "centerline_xy_interpolation_applied": False,
                "centerline_parts_xyz": centerline_parts_xyz,
                "corridor_segments": corridor_segments,
                "corridor_clipped_to_dem_extent": clipped_segment_count > 0,
                "clipped_segment_count": clipped_segment_count,
                "skipped_segment_count": skipped_segment_count,
                "dem_clip_extent_xy_m": [minimum_x, maximum_x, minimum_y, maximum_y],
                "drape_method": (
                    "deterministic_dem_extent_clipping_then_bilinear_dem_at_"
                    "corridor_polygon_vertices"
                ),
            },
        }
    )
    return entry


def _derive_hydrology(
    feature: dict[str, Any],
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    vector_artifact: dict[str, Any],
    elevation_artifact: dict[str, Any],
) -> dict[str, Any]:
    feature_id, attributes = _feature_identity(feature, "hydrology")
    anchor = _anchor(attributes, feature_id)
    _geometry_type, paths = _paths(feature.get("geometry"))
    entry = _base_entry(feature, "hydrology", anchor, vector_artifact, elevation_artifact)
    if not anchor["placement_resolved"]:
        return _held(entry, "water_surface_vertical_placement_unresolved")
    if anchor["mode"] != "water_surface_from_dem":
        return _held(entry, "unsupported_hydrology_vertical_anchor_mode")
    display_paths: list[dict[str, Any]] = []
    for role, path in paths:
        sampled = _bilinear_sample(elevation, x_axis, y_axis, path)
        if not np.isfinite(sampled).all():
            return _held(entry, "hydrology_geometry_outside_finite_dem")
        display_paths.append(
            {
                "role": role,
                "coordinates_xyz": [
                    [point[0], point[1], float(z)] for point, z in zip(path, sampled)
                ],
            }
        )
    entry.update(
        {
            "status": "resolved",
            "static_geometry": {
                "kind": "source_geometry_dem_display_drape",
                "geometry_xy": copy.deepcopy(feature.get("geometry")),
                "xy_interpolation_applied": False,
                "display_paths_xyz": display_paths,
                "drape_method": "bilinear_dem_for_preview_z_only",
                "water_surface_elevation_resolved": False,
                "runtime_authority": False,
            },
        }
    )
    return entry


def _artifact_binding(artifact: dict[str, Any], feature_class: str | None = None) -> dict[str, Any]:
    binding = {
        "artifact_id": artifact.get("artifact_id"),
        "sha256": artifact.get("sha256"),
    }
    if feature_class is not None:
        binding["feature_class"] = feature_class
    if not all(isinstance(binding[key], str) and binding[key] for key in ("artifact_id", "sha256")):
        raise StaticSceneDerivationError("source artifact binding requires artifact_id and sha256")
    return binding


def derive_static_scene_geometry(
    *,
    bundle: dict[str, Any],
    elevation: np.ndarray,
    elevation_x: np.ndarray,
    elevation_y: np.ndarray,
    elevation_artifact: dict[str, Any],
    vectors: dict[str, dict[str, Any]],
    vector_artifacts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    bundle_id = bundle.get("bundle_id")
    if not isinstance(bundle_id, str) or not bundle_id:
        raise StaticSceneDerivationError("bundle_id must be a non-empty string")
    if set(vectors) != {"road", "building", "hydrology"} or set(vector_artifacts) != set(vectors):
        raise StaticSceneDerivationError(
            "static scene derivation requires road, building, and hydrology documents and artifacts"
        )

    objects: list[dict[str, Any]] = []
    derivation = {
        "building": _derive_building,
        "road": _derive_road,
        "hydrology": _derive_hydrology,
    }
    for feature_class in ("building", "road", "hydrology"):
        features = vectors[feature_class].get("features")
        if not isinstance(features, list):
            raise StaticSceneDerivationError(f"{feature_class}.features must be a list")
        for feature in features:
            if not isinstance(feature, dict):
                raise StaticSceneDerivationError(f"{feature_class} feature must be an object")
            objects.append(
                derivation[feature_class](
                    feature,
                    elevation,
                    elevation_x,
                    elevation_y,
                    vector_artifacts[feature_class],
                    elevation_artifact,
                )
            )

    counts: dict[str, dict[str, int]] = {}
    for feature_class in ("building", "road", "hydrology"):
        selected = [item for item in objects if item["feature_class"] == feature_class]
        counts[feature_class] = {
            "total": len(selected),
            "resolved": sum(item["status"] == "resolved" for item in selected),
            "held": sum(item["status"] == "held" for item in selected),
        }
    summary = {
        "total": len(objects),
        "resolved": sum(item["status"] == "resolved" for item in objects),
        "held": sum(item["status"] == "held" for item in objects),
        "by_feature_class": counts,
    }
    return {
        "contract_version": STATIC_SCENE_CONTRACT,
        "coordinate_frame": "local_enu_m",
        "source_bundle": {
            "bundle_id": bundle_id,
            "elevation_artifact": _artifact_binding(elevation_artifact),
            "vector_artifacts": {
                feature_class: _artifact_binding(vector_artifacts[feature_class], feature_class)
                for feature_class in ("road", "building", "hydrology")
            },
        },
        "release": {
            "state": STATIC_SCENE_RELEASE_STATE,
            "runtime_authority": False,
            "runtime_consumers_enabled": [],
            "scope": "offline_static_geometry_derivation_and_preview_only",
        },
        "methods": {
            "building": "rigid_prism_with_median_vertex_and_centroid_dem_foundation",
            "road": (
                "per_segment_width_corridor_with_deterministic_dem_extent_clipping_"
                "and_bilinear_dem_drape"
            ),
            "bridge": (
                "abutment_dem_anchor_deck_with_linear_arc_length_interpolation_"
                "no_measured_deck_elevation"
            ),
            "hydrology": "source_geometry_with_bilinear_dem_preview_z_only",
            "xy_geometry_policy": "source_xy_preserved_without_interpolation",
        },
        "summary": summary,
        "objects": objects,
    }
