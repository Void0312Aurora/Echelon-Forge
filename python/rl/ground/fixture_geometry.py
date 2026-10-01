"""Planar geometry and raster-mask morphology for fixture case derivation.

Points are ``(x, y)`` in the bundle's local ENU metres; raster masks are boolean
arrays indexed ``[row, column]``. The containment rule mirrors the native Arnis
vector rule (``RasterGrid::contains``): a point is inside a feature when it lies
inside the polygon by the crossing rule, or within half the declared width of
any segment. One implementation serves both a single continuous point and a
whole grid of cell points, so the per-point prediction and the rasterized masks
cannot drift apart.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Iterator, Sequence

import numpy as np


Point = tuple[float, float]
Cell = tuple[int, int]

# Raster-index directions (row delta, column delta), in a fixed enumeration
# order that breaks ties deterministically.
DIRECTIONS: tuple[Cell, ...] = ((0, 1), (-1, 0), (0, -1), (1, 0))


def llround(value: float) -> int:
    """Round half away from zero, matching the native raster cell lookup."""

    magnitude = math.floor(abs(value) + 0.5)
    return int(magnitude) if value >= 0.0 else -int(magnitude)


def polyline_length(points: Sequence[Point]) -> float:
    return math.fsum(
        math.hypot(end[0] - start[0], end[1] - start[1]) for start, end in zip(points, points[1:])
    )


def sample_count(length_m: float, spacing_m: float) -> int:
    """Intervals needed to sample ``length_m`` at no more than ``spacing_m``."""

    return max(1, int(math.ceil(length_m / spacing_m)))


def interpolate(start: Point, end: Point, fraction: float) -> Point:
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


def segment_samples(start: Point, end: Point, spacing_m: float) -> Iterator[tuple[float, Point]]:
    """``(distance from start, point)`` at both ends and every ``spacing_m`` between."""

    distance = math.hypot(end[0] - start[0], end[1] - start[1])
    samples = sample_count(distance, spacing_m)
    for index in range(samples + 1):
        fraction = index / samples
        yield distance * fraction, interpolate(start, end, fraction)


def polyline_point(points: Sequence[Point], distance_m: float) -> Point:
    """Point at ``distance_m`` along a polyline, clamped to its last vertex."""

    remaining = distance_m
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        if remaining <= length or (x2, y2) == points[-1]:
            fraction = 0.0 if length == 0.0 else min(1.0, remaining / length)
            return (x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction)
        remaining -= length
    return points[-1]


def contains(x: Any, y: Any, points: Sequence[Point], *, polygon: bool, width_m: float) -> Any:
    """Native vector containment for a scalar point or for arrays of points.

    ``x``/``y`` are either floats (returns ``bool``) or equal-shape arrays
    (returns a boolean array). The arithmetic is identical in both forms.
    """

    points = tuple(points)
    vectorized = isinstance(x, np.ndarray)
    inside: Any = np.zeros(x.shape, dtype=bool) if vectorized else False
    if polygon and len(points) >= 3:
        for (xi, yi), (xj, yj) in zip(points, points[-1:] + points[:-1]):
            if yi == yj:
                continue  # a horizontal edge never straddles the scan line
            straddles = (yi > y) != (yj > y)
            crossing_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            inside ^= straddles & (x < crossing_x)
    radius = max(0.0, width_m * 0.5)
    threshold = radius * radius
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        dx, dy = x2 - x1, y2 - y1
        length_squared = dx * dx + dy * dy
        projection: Any = 0.0
        if length_squared > 0.0:
            projection = ((x - x1) * dx + (y - y1) * dy) / length_squared
            projection = np.clip(projection, 0.0, 1.0) if vectorized else min(1.0, max(0.0, projection))
        offset_x = x - (x1 + projection * dx)
        offset_y = y - (y1 + projection * dy)
        inside = inside | (offset_x * offset_x + offset_y * offset_y <= threshold)
    return inside


# -- raster masks ------------------------------------------------------------


def union_mask(shape: tuple[int, int], masks: Iterable[np.ndarray]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    for item in masks:
        mask |= item
    return mask


def in_bounds(shape: tuple[int, int], cell: Cell) -> bool:
    return 0 <= cell[0] < shape[0] and 0 <= cell[1] < shape[1]


def straight_run(row: int, column: int, dr: int, dc: int, cells: int) -> list[Cell]:
    """Cells ``k = 0..cells`` from ``(row, column)`` along ``(dr, dc)``."""

    return [(row + k * dr, column + k * dc) for k in range(cells + 1)]


def shifted(grid: np.ndarray, dr: int, dc: int, fill: Any) -> np.ndarray:
    """Return ``out[r, c] = grid[r + dr, c + dc]`` with ``fill`` off-grid."""

    out = np.full_like(grid, fill)
    height, width = grid.shape
    r0, r1 = max(0, -dr), min(height, height - dr)
    c0, c1 = max(0, -dc), min(width, width - dc)
    if r0 < r1 and c0 < c1:
        out[r0:r1, c0:c1] = grid[r0 + dr : r1 + dr, c0 + dc : c1 + dc]
    return out


def interior_depth(mask: np.ndarray) -> np.ndarray:
    """Four-neighbour erosion depth; raster-border cells never exceed depth 1."""

    depth = np.zeros(mask.shape, dtype=np.int32)
    current = mask.copy()
    level = 0
    while current.any():
        level += 1
        depth[current] = level
        eroded = current.copy()
        eroded[1:, :] &= current[:-1, :]
        eroded[:-1, :] &= current[1:, :]
        eroded[:, 1:] &= current[:, :-1]
        eroded[:, :-1] &= current[:, 1:]
        eroded[0, :] = False
        eroded[-1, :] = False
        eroded[:, 0] = False
        eroded[:, -1] = False
        current = eroded
    return depth


def straight_run_valid(mask: np.ndarray, dr: int, dc: int, cells: int) -> np.ndarray:
    """True where cells ``k = 0..cells`` along ``(dr, dc)`` all lie in ``mask``."""

    valid = mask.copy()
    for k in range(1, cells + 1):
        valid &= shifted(mask, k * dr, k * dc, False)
    return valid


def in_slope_band(slope_deg: np.ndarray, low_deg: float, high_deg: float) -> np.ndarray:
    """Half-open band membership ``low <= slope < high``."""

    return (slope_deg >= low_deg) & (slope_deg < high_deg)


__all__ = [
    "Cell",
    "DIRECTIONS",
    "Point",
    "contains",
    "in_bounds",
    "in_slope_band",
    "interior_depth",
    "interpolate",
    "llround",
    "polyline_length",
    "polyline_point",
    "sample_count",
    "segment_samples",
    "shifted",
    "straight_run",
    "straight_run_valid",
    "union_mask",
]
