"""Deterministic acceptance cases derived from the Arnis infantry fixture.

Every case here is computed from the verified bundle manifest, its rasters and
vector features, the companion metadata overlay, and the retained field
acceptance report. No coordinate is hand-typed. The derivation *predicts*
where native movement should pass or block, so the native probe can be held
to an independent expectation; the probe remains the authority whose verdict
the acceptance matrix records.

This module is case enumeration for acceptance tests and curriculum tooling
only. It is not a route graph, passability product, cost grid, or planner, and
it carries no runtime authority.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


FIXTURE_CASE_CONTRACT_VERSION = "ground_infantry_fixture_cases.v1"

WATER_TRANSITION_BLOCKED = "water_transition_blocked"
OBSTACLE_TRANSITION_BLOCKED = "obstacle_transition_blocked"

# Landcover legend semantics that the training contract requires to fail
# closed ("unknown terrain semantics cannot silently become passable" and
# "river crossing is only possible through an explicitly admitted crossing").
# Keyed by the bundle legend name and mapped to the native blocked reason the
# probe must report. Every other legend class is expected to be traversable.
BLOCKING_LANDCOVER_SEMANTICS: Mapping[str, str] = {
    "permanent_water": WATER_TRANSITION_BLOCKED,
    "unknown_nodata": OBSTACLE_TRANSITION_BLOCKED,
}

# Raster-index directions (row delta, column delta), in a fixed enumeration
# order that breaks ties deterministically.
_DIRECTIONS: tuple[tuple[int, int], ...] = ((0, 1), (-1, 0), (0, -1), (1, 0))

# Slope bands use the retained field-acceptance percentiles as edges.
_SLOPE_BAND_EDGES: tuple[tuple[str, str | None, str | None], ...] = (
    ("below_p50", None, "slope_p50_deg"),
    ("p50_to_p95", "slope_p50_deg", "slope_p95_deg"),
    ("p95_to_p99", "slope_p95_deg", "slope_p99_deg"),
    ("above_p99", "slope_p99_deg", None),
)

_DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
)


class FixtureCaseError(ValueError):
    """Raised when the fixture cannot populate a required case (fail closed)."""


@dataclass(frozen=True)
class FixtureCase:
    """One start/waypoint case with an independent expected native outcome."""

    case_id: str
    category: str
    expected: str
    start_xy_m: tuple[float, float]
    waypoints_xy_m: tuple[tuple[float, float], ...]
    expected_block_reason: str | None = None
    # Distance from the start to the first predicted blocked sample, and the
    # last predicted passable sample before it. ``None`` for reach cases.
    block_distance_m: float | None = None
    approach_xy_m: tuple[float, float] | None = None
    requires_bridge_admission: bool = False
    derivation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.expected not in ("reach", "block", "held"):
            raise FixtureCaseError(f"{self.case_id}: expected must be reach, block, or held")
        if (self.expected == "block") != (self.expected_block_reason is not None):
            raise FixtureCaseError(f"{self.case_id}: block cases need exactly one reason")

    @property
    def route_distance_m(self) -> float:
        points = (self.start_xy_m,) + self.waypoints_xy_m
        return math.fsum(
            math.hypot(end[0] - start[0], end[1] - start[1])
            for start, end in zip(points, points[1:])
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "expected": self.expected,
            "expected_block_reason": self.expected_block_reason,
            "start_xy_m": list(self.start_xy_m),
            "waypoints_xy_m": [list(point) for point in self.waypoints_xy_m],
            "route_distance_m": self.route_distance_m,
            "block_distance_m": self.block_distance_m,
            "approach_xy_m": None if self.approach_xy_m is None else list(self.approach_xy_m),
            "requires_bridge_admission": self.requires_bridge_admission,
            "derivation": dict(self.derivation),
        }


@dataclass(frozen=True)
class _Feature:
    feature_id: str
    points: tuple[tuple[float, float], ...]
    width_m: float
    polygon: bool
    attributes: Mapping[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FixtureCaseError(f"failed to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FixtureCaseError(f"{path} must contain an object")
    return value


def _llround(value: float) -> int:
    """Round half away from zero, matching the native raster cell lookup."""

    magnitude = math.floor(abs(value) + 0.5)
    return int(magnitude) if value >= 0.0 else -int(magnitude)


def _shifted(grid: np.ndarray, dr: int, dc: int, fill: Any) -> np.ndarray:
    """Return ``out[r, c] = grid[r + dr, c + dc]`` with ``fill`` off-grid."""

    out = np.full_like(grid, fill)
    height, width = grid.shape
    r0, r1 = max(0, -dr), min(height, height - dr)
    c0, c1 = max(0, -dc), min(width, width - dc)
    if r0 < r1 and c0 < c1:
        out[r0:r1, c0:c1] = grid[r0 + dr : r1 + dr, c0 + dc : c1 + dc]
    return out


def _interior_depth(mask: np.ndarray) -> np.ndarray:
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


def _point_in_polygon(x: float, y: float, points: Sequence[tuple[float, float]]) -> bool:
    inside = False
    if len(points) < 3:
        return False
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _distance_squared_to_segment(
    x: float, y: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    dx, dy = x2 - x1, y2 - y1
    length_squared = dx * dx + dy * dy
    projection = (
        min(1.0, max(0.0, ((x - x1) * dx + (y - y1) * dy) / length_squared))
        if length_squared > 0.0
        else 0.0
    )
    offset_x = x - (x1 + projection * dx)
    offset_y = y - (y1 + projection * dy)
    return offset_x * offset_x + offset_y * offset_y


def _straight_run_valid(mask: np.ndarray, dr: int, dc: int, cells: int) -> np.ndarray:
    """True where cells ``k = 0..cells`` along ``(dr, dc)`` all lie in ``mask``."""

    valid = mask.copy()
    for k in range(1, cells + 1):
        valid &= _shifted(mask, k * dr, k * dc, False)
    return valid


class ArnisInfantryFixture:
    """Read-only view over the verified eastern-plain infantry fixture."""

    def __init__(self, fixture_dir: str | Path | None = None) -> None:
        root = Path(fixture_dir) if fixture_dir is not None else _DEFAULT_FIXTURE
        self.fixture_dir = root
        self.bundle_dir = root / "expected"
        self.bundle = _read_json(self.bundle_dir / "bundle.json")
        self.field_acceptance = _read_json(root / "field_acceptance.json")
        self.overlay = _read_json(root / "field_overlay.json")
        if self.field_acceptance.get("valid") is not True:
            raise FixtureCaseError("field acceptance report is not valid; cases fail closed")
        if self.overlay.get("contract_version") != "field_overlay.v1":
            raise FixtureCaseError("unsupported field overlay contract")

        landcover_artifact = self._artifact("landcover_raster")
        elevation_artifact = self._artifact("elevation_raster")
        shape = tuple(int(value) for value in landcover_artifact["shape"])
        if tuple(int(value) for value in elevation_artifact["shape"]) != shape:
            raise FixtureCaseError("landcover and elevation rasters must share a shape")
        metadata = landcover_artifact["metadata"]
        elevation_metadata = elevation_artifact["metadata"]
        if metadata["origin_xy_m"] != elevation_metadata["origin_xy_m"] or (
            metadata["step_xy_m"] != elevation_metadata["step_xy_m"]
        ):
            raise FixtureCaseError("landcover and elevation rasters must share a grid")
        self.shape: tuple[int, int] = (shape[0], shape[1])
        self.origin_xy_m = tuple(float(value) for value in metadata["origin_xy_m"])
        self.step_xy_m = tuple(float(value) for value in metadata["step_xy_m"])
        self.legend = {int(key): str(value) for key, value in metadata["class_legend"].items()}
        self.source_native_resolution_m = float(metadata["source_native_resolution_m"])
        self.landcover = self._raster(landcover_artifact, np.uint8)
        self.elevation = self._raster(elevation_artifact, np.dtype("<f4")).astype(np.float64)

        self.hydrology = self._vector_features("hydrology", bridge=None)
        self.buildings = self._vector_features("building", bridge=None)
        self.bridges = self._vector_features("road", bridge=True)
        if not self.bridges:
            raise FixtureCaseError("fixture declares no bridge road feature")

    # -- bundle access -------------------------------------------------

    def _artifact(self, kind: str) -> Mapping[str, Any]:
        for artifact in self.bundle.get("artifacts", []):
            if isinstance(artifact, dict) and artifact.get("kind") == kind:
                return artifact
        raise FixtureCaseError(f"bundle is missing {kind} artifact")

    def _raster(self, artifact: Mapping[str, Any], dtype: Any) -> np.ndarray:
        path = (self.bundle_dir / str(artifact["path"])).resolve()
        if self.bundle_dir.resolve() not in path.parents:
            raise FixtureCaseError("raster artifact path escapes the bundle")
        values = np.fromfile(path, dtype=dtype)
        if values.size != self.shape[0] * self.shape[1]:
            raise FixtureCaseError(f"raster {path.name} size does not match its shape")
        return values.reshape(self.shape)

    def _vector_features(self, feature_class: str, *, bridge: bool | None) -> tuple[_Feature, ...]:
        artifact = next(
            (
                item
                for item in self.bundle.get("artifacts", [])
                if item.get("kind") == "vector_features" and item.get("feature_class") == feature_class
            ),
            None,
        )
        if artifact is None:
            return ()
        document = _read_json(self.bundle_dir / str(artifact["path"]))
        if document.get("coordinate_frame") != "local_enu_m":
            raise FixtureCaseError(f"{feature_class} vectors must be local_enu_m")
        features: list[_Feature] = []
        for feature in document.get("features", []):
            attributes = feature.get("attributes", {})
            if bridge is not None and bool(attributes.get("bridge", False)) != bridge:
                continue
            geometry = feature["geometry"]
            polygon = geometry["type"] == "Polygon"
            coordinates = geometry["coordinates"][0] if polygon else geometry["coordinates"]
            features.append(
                _Feature(
                    feature_id=str(feature["feature_id"]),
                    points=tuple((float(x), float(y)) for x, y in coordinates),
                    width_m=float(attributes.get("width_m", 0.0) or 0.0),
                    polygon=polygon,
                    attributes=attributes,
                )
            )
        return tuple(features)

    # -- grid geometry -------------------------------------------------

    def cell_origin_xy_m(self, row: int, column: int) -> tuple[float, float]:
        return (
            self.origin_xy_m[0] + column * self.step_xy_m[0],
            self.origin_xy_m[1] + row * self.step_xy_m[1],
        )

    def cell(self, x_m: float, y_m: float) -> tuple[int, int] | None:
        column = _llround((x_m - self.origin_xy_m[0]) / self.step_xy_m[0])
        row = _llround((y_m - self.origin_xy_m[1]) / self.step_xy_m[1])
        if row < 0 or column < 0 or row >= self.shape[0] or column >= self.shape[1]:
            return None
        return row, column

    @property
    def sample_spacing_m(self) -> float:
        return min(abs(self.step_xy_m[0]), abs(self.step_xy_m[1]))

    def cells_for_length(self, length_m: float) -> int:
        """Smallest whole raster-cell count whose length covers ``length_m``."""

        return int(math.ceil(length_m / self.sample_spacing_m))

    @cached_property
    def _axes(self) -> tuple[np.ndarray, np.ndarray]:
        columns = self.origin_xy_m[0] + np.arange(self.shape[1]) * self.step_xy_m[0]
        rows = self.origin_xy_m[1] + np.arange(self.shape[0]) * self.step_xy_m[1]
        return rows, columns

    def _geometry_mask(
        self,
        points: Sequence[tuple[float, float]],
        *,
        polygon: bool,
        width_m: float,
    ) -> np.ndarray:
        """Rasterize one geometry with the native containment rule.

        A cell is inside when its point lies inside the polygon (crossing
        rule) or within half the declared width of any segment.
        """

        mask = np.zeros(self.shape, dtype=bool)
        radius = max(0.0, width_m * 0.5)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        row_axis, column_axis = self._axes
        column_hits = np.nonzero(
            (column_axis >= min(xs) - radius) & (column_axis <= max(xs) + radius)
        )[0]
        row_hits = np.nonzero((row_axis >= min(ys) - radius) & (row_axis <= max(ys) + radius))[0]
        if column_hits.size == 0 or row_hits.size == 0:
            return mask
        r0, r1 = int(row_hits.min()), int(row_hits.max()) + 1
        c0, c1 = int(column_hits.min()), int(column_hits.max()) + 1
        grid_x, grid_y = np.meshgrid(column_axis[c0:c1], row_axis[r0:r1])
        inside = np.zeros(grid_x.shape, dtype=bool)
        if polygon and len(points) >= 3:
            for (xi, yi), (xj, yj) in zip(points, points[-1:] + tuple(points[:-1])):
                if yi == yj:
                    continue
                straddles = (yi > grid_y) != (yj > grid_y)
                crossing_x = (xj - xi) * (grid_y - yi) / (yj - yi) + xi
                inside ^= straddles & (grid_x < crossing_x)
        threshold = radius * radius
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            dx, dy = x2 - x1, y2 - y1
            length_squared = dx * dx + dy * dy
            if length_squared > 0.0:
                projection = np.clip(((grid_x - x1) * dx + (grid_y - y1) * dy) / length_squared, 0.0, 1.0)
            else:
                projection = np.zeros_like(grid_x)
            offset_x = grid_x - (x1 + projection * dx)
            offset_y = grid_y - (y1 + projection * dy)
            inside |= offset_x * offset_x + offset_y * offset_y <= threshold
        mask[r0:r1, c0:c1] = inside
        return mask

    @staticmethod
    def _contains(feature: _Feature, x_m: float, y_m: float) -> bool:
        """Continuous-point containment with the native vector rule."""

        if feature.polygon and _point_in_polygon(x_m, y_m, feature.points):
            return True
        threshold = max(0.0, feature.width_m * 0.5) ** 2
        return any(
            _distance_squared_to_segment(x_m, y_m, x1, y1, x2, y2) <= threshold
            for (x1, y1), (x2, y2) in zip(feature.points, feature.points[1:])
        )

    def _feature_mask(self, feature: _Feature) -> np.ndarray:
        return self._geometry_mask(feature.points, polygon=feature.polygon, width_m=feature.width_m)

    @cached_property
    def hydrology_masks(self) -> tuple[np.ndarray, ...]:
        return tuple(self._feature_mask(feature) for feature in self.hydrology)

    @cached_property
    def hydrology_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=bool)
        for feature_mask in self.hydrology_masks:
            mask |= feature_mask
        return mask

    @cached_property
    def bridge_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=bool)
        for feature in self.bridges:
            mask |= self._feature_mask(feature)
        return mask

    def landcover_block_reason(self, code: int) -> str | None:
        return BLOCKING_LANDCOVER_SEMANTICS.get(self.legend.get(code, "unknown_nodata"))

    @cached_property
    def blocking_landcover_mask(self) -> np.ndarray:
        codes = [code for code in self.legend if self.landcover_block_reason(code) is not None]
        mask = np.isin(self.landcover, np.asarray(codes, dtype=np.uint8))
        # A code missing from the legend is unknown and must not pass.
        mask |= ~np.isin(self.landcover, np.asarray(list(self.legend), dtype=np.uint8))
        return mask

    @cached_property
    def passable_mask(self) -> np.ndarray:
        """Predicted traversable cells: a declared bridge, or dry known landcover."""

        return self.bridge_mask | (~self.hydrology_mask & ~self.blocking_landcover_mask)

    @cached_property
    def underlying_water_mask(self) -> np.ndarray:
        """Water ignoring any bridge deck: the crossing a bridge must admit."""

        water_codes = [
            code
            for code in self.legend
            if self.landcover_block_reason(code) == WATER_TRANSITION_BLOCKED
        ]
        return self.hydrology_mask | np.isin(self.landcover, np.asarray(water_codes, dtype=np.uint8))

    def overlay_polygon_mask(self, kinds: Sequence[str] | None = None) -> np.ndarray:
        """Union of overlay polygons (all, or only ``kinds``); held metadata."""

        row_axis, column_axis = self._axes
        min_x = float(min(column_axis[0], column_axis[-1]))
        min_y = float(min(row_axis[0], row_axis[-1]))
        mask = np.zeros(self.shape, dtype=bool)
        for entry in self.overlay.get("entries", []):
            geometry = entry.get("geometry", {})
            if geometry.get("geometry_type") != "polygon":
                continue
            if kinds is not None and entry.get("overlay_kind") not in kinds:
                continue
            # Overlay coordinates are logical offsets from the raster minimum
            # corner, the same translation the native overlay loader applies.
            points = tuple((min_x + float(x), min_y + float(y)) for x, y in geometry["points"])
            mask |= self._geometry_mask(points, polygon=True, width_m=0.0)
        return mask

    @cached_property
    def building_mask(self) -> np.ndarray:
        mask = np.zeros(self.shape, dtype=bool)
        for feature in self.buildings:
            mask |= self._feature_mask(feature)
        return mask

    # -- point / segment prediction -----------------------------------

    def segment_cells(self, case: FixtureCase) -> tuple[tuple[int, int], ...]:
        """Raster cells sampled at raster spacing along every case segment."""

        cells: list[tuple[int, int]] = []
        points = (case.start_xy_m,) + case.waypoints_xy_m
        for start, end in zip(points, points[1:]):
            distance = math.hypot(end[0] - start[0], end[1] - start[1])
            samples = max(1, int(math.ceil(distance / self.sample_spacing_m)))
            for index in range(samples + 1):
                fraction = index / samples
                cell = self.cell(
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
                if cell is not None and (not cells or cells[-1] != cell):
                    cells.append(cell)
        return tuple(cells)

    def stride_slope_at(self, cell: tuple[int, int]) -> float:
        """Field-acceptance slope at the nearest sample of the acceptance grid."""

        stride = self.slope_stride
        slope = self.stride_slope_deg
        row = min(slope.shape[0] - 1, int(round(cell[0] / stride)))
        column = min(slope.shape[1] - 1, int(round(cell[1] / stride)))
        return float(slope[row, column])

    def block_reason(self, x_m: float, y_m: float) -> str | None:
        # Vector semantics are evaluated at the continuous point and take
        # precedence over the landcover cell, matching the native provider.
        cell = self.cell(x_m, y_m)
        if cell is None:
            return OBSTACLE_TRANSITION_BLOCKED
        if any(self._contains(feature, x_m, y_m) for feature in self.bridges):
            return None
        if any(self._contains(feature, x_m, y_m) for feature in self.hydrology):
            return WATER_TRANSITION_BLOCKED
        code = int(self.landcover[cell])
        if code not in self.legend:
            return OBSTACLE_TRANSITION_BLOCKED
        return self.landcover_block_reason(code)

    def first_block(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[float, str, tuple[float, float]] | None:
        """First predicted blocked sample along a segment at raster spacing."""

        distance = math.hypot(end[0] - start[0], end[1] - start[1])
        samples = max(1, int(math.ceil(distance / self.sample_spacing_m)))
        last_passable = start
        for index in range(samples + 1):
            fraction = index / samples
            point = (
                start[0] + (end[0] - start[0]) * fraction,
                start[1] + (end[1] - start[1]) * fraction,
            )
            reason = self.block_reason(*point)
            if reason is not None:
                return distance * fraction, reason, last_passable
            last_passable = point
        return None

    # -- slope ---------------------------------------------------------

    @cached_property
    def slope_stride(self) -> int:
        return int(self.field_acceptance["terrain"]["sample_stride"])

    @cached_property
    def stride_slope_deg(self) -> np.ndarray:
        """Slope on the field-acceptance sample grid with its own estimator."""

        stride = self.slope_stride
        sampled = self.elevation[::stride, ::stride]
        dx = abs(self.step_xy_m[0]) * stride
        dy = abs(self.step_xy_m[1]) * stride
        gy, gx = np.gradient(sampled, dy, dx)
        return np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))

    def slope_bands(self) -> tuple[tuple[str, float, float], ...]:
        terrain = self.field_acceptance["terrain"]
        bands = []
        for name, low_key, high_key in _SLOPE_BAND_EDGES:
            low = 0.0 if low_key is None else float(terrain[low_key])
            high = math.inf if high_key is None else float(terrain[high_key])
            bands.append((name, low, high))
        return tuple(bands)

    def band_index_grid(self) -> np.ndarray:
        """Full-resolution band index via the nearest field-acceptance sample."""

        stride = self.slope_stride
        slope = self.stride_slope_deg
        band = np.full(slope.shape, -1, dtype=np.int8)
        for index, (_name, low, high) in enumerate(self.slope_bands()):
            band[(slope >= low) & (slope < high)] = index
        rows = np.clip(np.rint(np.arange(self.shape[0]) / stride).astype(int), 0, slope.shape[0] - 1)
        columns = np.clip(np.rint(np.arange(self.shape[1]) / stride).astype(int), 0, slope.shape[1] - 1)
        return band[np.ix_(rows, columns)]


# ---------------------------------------------------------------------------
# Case derivation
# ---------------------------------------------------------------------------


def case_segment_length_m(fixture: ArnisInfantryFixture, goal_radius_m: float) -> float:
    """Case segment length: one source-native landcover cell plus the goal radius.

    A rollout therefore traverses at least one source-resolution landcover
    cell before it enters the env contract's goal radius.
    """

    return fixture.source_native_resolution_m + float(goal_radius_m)


def _best_straight_segment(
    mask: np.ndarray, depth: np.ndarray, cells: int
) -> tuple[int, int, int, int, int] | None:
    """Most interior straight run of ``cells`` steps; returns (score, r, c, dr, dc)."""

    best: tuple[int, int, int, int, int] | None = None
    for dr, dc in _DIRECTIONS:
        valid = _straight_run_valid(mask, dr, dc, cells)
        end_depth = _shifted(depth, cells * dr, cells * dc, 0)
        score = np.where(valid, np.minimum(depth, end_depth), 0)
        flat = int(np.argmax(score))
        value = int(score.flat[flat])
        if value > 0 and (best is None or value > best[0]):
            row, column = divmod(flat, mask.shape[1])
            best = (value, row, column, dr, dc)
    return best


def _straight_case(
    fixture: ArnisInfantryFixture,
    *,
    case_id: str,
    category: str,
    mask: np.ndarray,
    cells: int,
    derivation: Mapping[str, Any],
) -> FixtureCase:
    depth = _interior_depth(mask)
    best = _best_straight_segment(mask, depth, cells)
    if best is None:
        raise FixtureCaseError(f"{case_id}: fixture has no straight {cells}-cell run")
    score, row, column, dr, dc = best
    start = fixture.cell_origin_xy_m(row, column)
    goal = fixture.cell_origin_xy_m(row + cells * dr, column + cells * dc)
    if fixture.first_block(start, goal) is not None:
        raise FixtureCaseError(f"{case_id}: derived reach segment is predicted blocked")
    return FixtureCase(
        case_id=case_id,
        category=category,
        expected="reach",
        start_xy_m=start,
        waypoints_xy_m=(goal,),
        derivation={**derivation, "interior_depth_cells": score, "segment_cells": cells},
    )


def landcover_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """One reach case per traversable landcover class present in the fixture."""

    cells = fixture.cells_for_length(case_segment_length_m(fixture, goal_radius_m))
    cases = []
    counts = fixture.field_acceptance["landcover"]["class_counts"]
    for code in sorted(int(key) for key in counts):
        if fixture.landcover_block_reason(code) is not None:
            continue
        semantic = fixture.legend.get(code)
        if semantic is None:
            raise FixtureCaseError(f"landcover code {code} is missing from the legend")
        mask = (fixture.landcover == code) & ~fixture.hydrology_mask & ~fixture.bridge_mask
        cases.append(
            _straight_case(
                fixture,
                case_id=f"landcover:{semantic}",
                category="landcover",
                mask=mask,
                cells=cells,
                derivation={"source": "landcover_raster.class_legend", "landcover_code": code},
            )
        )
    return cases


def slope_band_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """One reach case starting in each field-acceptance slope band."""

    cells = fixture.cells_for_length(case_segment_length_m(fixture, goal_radius_m))
    stride = fixture.slope_stride
    slope = fixture.stride_slope_deg
    passable = fixture.passable_mask & ~fixture.bridge_mask
    stride_passable = passable[::stride, ::stride]
    band_grid = fixture.band_index_grid()
    cases = []
    for index, (name, low, high) in enumerate(fixture.slope_bands()):
        band = (slope >= low) & (slope < high) & stride_passable
        depth = _interior_depth(band)
        order = np.argsort(-depth, axis=None, kind="stable")
        chosen: tuple[int, int, int, int, float] | None = None
        for flat in order:
            if depth.flat[flat] <= 0:
                break
            stride_row, stride_column = divmod(int(flat), band.shape[1])
            row, column = stride_row * stride, stride_column * stride
            for dr, dc in _DIRECTIONS:
                end_row, end_column = row + cells * dr, column + cells * dc
                if not (0 <= end_row < fixture.shape[0] and 0 <= end_column < fixture.shape[1]):
                    continue
                path = [(row + k * dr, column + k * dc) for k in range(cells + 1)]
                if not all(passable[cell] for cell in path):
                    continue
                in_band = sum(1 for cell in path if band_grid[cell] == index) / len(path)
                if chosen is None or in_band > chosen[4]:
                    chosen = (row, column, dr, dc, in_band)
            if chosen is not None:
                break
        if chosen is None:
            raise FixtureCaseError(f"slope_band:{name}: fixture cannot populate this band")
        row, column, dr, dc, in_band = chosen
        start = fixture.cell_origin_xy_m(row, column)
        goal = fixture.cell_origin_xy_m(row + cells * dr, column + cells * dc)
        if fixture.first_block(start, goal) is not None:
            raise FixtureCaseError(f"slope_band:{name}: derived segment is predicted blocked")
        cases.append(
            FixtureCase(
                case_id=f"slope_band:{name}",
                category="slope_band",
                expected="reach",
                start_xy_m=start,
                waypoints_xy_m=(goal,),
                derivation={
                    "source": "field_acceptance.terrain",
                    "band_low_deg": low,
                    "band_high_deg": None if math.isinf(high) else high,
                    "estimator": "field_acceptance_np_gradient_on_sample_stride",
                    "sample_stride": stride,
                    "start_band_slope_deg": float(slope[row // stride, column // stride]),
                    "segment_in_band_fraction": in_band,
                    "segment_cells": cells,
                },
            )
        )
    return cases


def _approach_block_case(
    fixture: ArnisInfantryFixture,
    *,
    case_id: str,
    category: str,
    region: np.ndarray,
    cells: int,
    goal_radius_m: float,
    derivation: Mapping[str, Any],
) -> FixtureCase:
    """Block case: walk out from the most interior region cell to dry land."""

    if not region.any():
        raise FixtureCaseError(f"{case_id}: fixture has no cell for this region")
    depth = _interior_depth(region)
    order = np.argsort(-depth, axis=None, kind="stable")
    passable = fixture.passable_mask & ~fixture.bridge_mask
    height, width = fixture.shape
    for flat in order:
        if depth.flat[flat] <= 0:
            break
        goal_row, goal_column = divmod(int(flat), width)
        best: tuple[int, int, int] | None = None
        for dr, dc in _DIRECTIONS:
            k = 1
            while (
                0 <= goal_row + k * dr < height
                and 0 <= goal_column + k * dc < width
                and not fixture.passable_mask[goal_row + k * dr, goal_column + k * dc]
            ):
                k += 1
            approach = (goal_row + k * dr, goal_column + k * dc)
            start = (approach[0] + cells * dr, approach[1] + cells * dc)
            if not (0 <= start[0] < height and 0 <= start[1] < width):
                continue
            if not all(passable[approach[0] + j * dr, approach[1] + j * dc] for j in range(cells + 1)):
                continue
            if best is None or k < best[0]:
                best = (k, dr, dc)
        if best is None:
            continue
        k, dr, dc = best
        goal = fixture.cell_origin_xy_m(goal_row, goal_column)
        if k * fixture.sample_spacing_m <= goal_radius_m:
            continue  # the goal radius would be reachable from the bank
        start = fixture.cell_origin_xy_m(goal_row + (k + cells) * dr, goal_column + (k + cells) * dc)
        predicted = fixture.first_block(start, goal)
        if predicted is None:
            raise FixtureCaseError(f"{case_id}: derived block segment is predicted passable")
        block_distance, reason, approach_xy = predicted
        return FixtureCase(
            case_id=case_id,
            category=category,
            expected="block",
            expected_block_reason=reason,
            start_xy_m=start,
            waypoints_xy_m=(goal,),
            block_distance_m=block_distance,
            approach_xy_m=approach_xy,
            derivation={
                **derivation,
                "goal_interior_depth_cells": int(depth[goal_row, goal_column]),
                "approach_cells_from_goal": k,
                "segment_cells_before_approach": cells,
            },
        )
    raise FixtureCaseError(f"{case_id}: no dry approach reaches this region")


def water_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Block cases into landcover water and into each declared hydrology feature."""

    cells = fixture.cells_for_length(case_segment_length_m(fixture, goal_radius_m))
    cases = []
    counts = fixture.field_acceptance["landcover"]["class_counts"]
    for code in sorted(int(key) for key in counts):
        if fixture.landcover_block_reason(code) is None:
            continue
        region = (fixture.landcover == code) & ~fixture.hydrology_mask & ~fixture.bridge_mask
        cases.append(
            _approach_block_case(
                fixture,
                case_id=f"water:landcover:{fixture.legend[code]}",
                category="water_or_obstacle",
                region=region,
                cells=cells,
                goal_radius_m=goal_radius_m,
                derivation={"source": "landcover_raster.class_legend", "landcover_code": code},
            )
        )
    for index, (feature, feature_mask) in enumerate(zip(fixture.hydrology, fixture.hydrology_masks)):
        others = np.zeros(fixture.shape, dtype=bool)
        for other_index, other_mask in enumerate(fixture.hydrology_masks):
            if other_index != index:
                others |= other_mask
        # Cells where this vector is the only reason for water: the native
        # provider must let the declared feature override dry landcover.
        region = feature_mask & ~others & ~fixture.blocking_landcover_mask & ~fixture.bridge_mask
        kind = "polygon" if feature.polygon else "line"
        cases.append(
            _approach_block_case(
                fixture,
                case_id=f"water:hydrology:{index}:{kind}",
                category="water_or_obstacle",
                region=region,
                cells=cells,
                goal_radius_m=goal_radius_m,
                derivation={
                    "source": "hydrology_vector_features",
                    "feature_id": feature.feature_id,
                    "width_m": feature.width_m,
                },
            )
        )
    return cases


def edge_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Outbound (must block) and edge-parallel (must reach) cases per raster edge."""

    cells = fixture.cells_for_length(case_segment_length_m(fixture, goal_radius_m))
    height, width = fixture.shape
    passable = fixture.passable_mask & ~fixture.bridge_mask
    # (name, fixed axis, fixed index, inward (dr, dc), along (dr, dc))
    edges = (
        ("west", "column", 0, (0, 1), (1, 0)),
        ("east", "column", width - 1, (0, -1), (1, 0)),
        ("north", "row", 0, (1, 0), (0, 1)),
        ("south", "row", height - 1, (-1, 0), (0, 1)),
    )
    cases = []
    for name, axis, fixed, inward, along in edges:
        span = height if axis == "column" else width
        middle = (span - 1) / 2.0

        def edge_cell(index: int, fixed: int = fixed, axis: str = axis) -> tuple[int, int]:
            return (index, fixed) if axis == "column" else (fixed, index)

        outbound = None
        for index in sorted(range(span), key=lambda value: (abs(value - middle), value)):
            row, column = edge_cell(index)
            run = [(row + k * inward[0], column + k * inward[1]) for k in range(cells + 1)]
            if all(passable[cell] for cell in run):
                outbound = (row, column)
                break
        if outbound is None:
            raise FixtureCaseError(f"edge:{name}: no passable inward run reaches this edge")
        row, column = outbound
        start = fixture.cell_origin_xy_m(row + cells * inward[0], column + cells * inward[1])
        goal = fixture.cell_origin_xy_m(row - cells * inward[0], column - cells * inward[1])
        predicted = fixture.first_block(start, goal)
        if predicted is None or predicted[1] != OBSTACLE_TRANSITION_BLOCKED:
            raise FixtureCaseError(f"edge:{name}: outbound segment must leave the raster")
        cases.append(
            FixtureCase(
                case_id=f"edge:{name}:outbound",
                category="raster_edge",
                expected="block",
                expected_block_reason=predicted[1],
                start_xy_m=start,
                waypoints_xy_m=(goal,),
                block_distance_m=predicted[0],
                approach_xy_m=predicted[2],
                derivation={"source": "elevation_raster.shape_origin_step", "edge": name, "segment_cells": cells},
            )
        )

        parallel = None
        for index in sorted(range(span - cells), key=lambda value: (abs(value + cells / 2.0 - middle), value)):
            run = [edge_cell(index + k) for k in range(cells + 1)]
            if all(passable[cell] for cell in run):
                parallel = run
                break
        if parallel is None:
            raise FixtureCaseError(f"edge:{name}: no passable run along this edge")
        start = fixture.cell_origin_xy_m(*parallel[0])
        goal = fixture.cell_origin_xy_m(*parallel[-1])
        if fixture.first_block(start, goal) is not None:
            raise FixtureCaseError(f"edge:{name}: parallel segment is predicted blocked")
        cases.append(
            FixtureCase(
                case_id=f"edge:{name}:parallel",
                category="raster_edge",
                expected="reach",
                start_xy_m=start,
                waypoints_xy_m=(goal,),
                derivation={"source": "elevation_raster.shape_origin_step", "edge": name, "segment_cells": cells},
            )
        )
    return cases


def _polyline_point(points: Sequence[tuple[float, float]], distance_m: float) -> tuple[float, float]:
    remaining = distance_m
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        length = math.hypot(x2 - x1, y2 - y1)
        if remaining <= length or (x2, y2) == points[-1]:
            fraction = 0.0 if length == 0.0 else min(1.0, remaining / length)
            return (x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction)
        remaining -= length
    return points[-1]


def bridge_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Crossing via each declared bridge, plus an off-bridge control that must block."""

    length_m = case_segment_length_m(fixture, goal_radius_m)
    cases = []
    for bridge_index, bridge in enumerate(fixture.bridges):
        points = bridge.points
        total = math.fsum(
            math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(points, points[1:])
        )
        samples = max(1, int(math.ceil(total / fixture.sample_spacing_m)))
        intervals: list[list[float]] = []
        previous_water = False
        for index in range(samples + 1):
            distance = total * index / samples
            cell = fixture.cell(*_polyline_point(points, distance))
            water = cell is not None and bool(fixture.underlying_water_mask[cell])
            if water and not previous_water:
                intervals.append([distance, distance])
            elif water:
                intervals[-1][1] = distance
            previous_water = water
        if not intervals:
            raise FixtureCaseError(f"bridge:{bridge_index}: declared bridge crosses no water")
        for interval_index, (water_start, water_end) in enumerate(intervals):
            if water_start - length_m < 0.0 or water_end + length_m > total:
                raise FixtureCaseError(
                    f"bridge:{bridge_index}:{interval_index}: crossing too close to the bridge end"
                )
            start = _polyline_point(points, water_start - length_m)
            goal = _polyline_point(points, water_end + length_m)
            if fixture.first_block(start, goal) is not None:
                raise FixtureCaseError(
                    f"bridge:{bridge_index}:{interval_index}: direct crossing leaves the bridge deck"
                )
            derivation = {
                "source": "road_vector_features.bridge",
                "feature_id": bridge.feature_id,
                "bridge_width_m": bridge.width_m,
                "water_interval_m": [water_start, water_end],
                "approach_length_m": length_m,
            }
            cases.append(
                FixtureCase(
                    case_id=f"bridge:{bridge_index}:{interval_index}:crossing",
                    category="bridge",
                    expected="reach",
                    start_xy_m=start,
                    waypoints_xy_m=(goal,),
                    requires_bridge_admission=True,
                    derivation=derivation,
                )
            )
            dx, dy = goal[0] - start[0], goal[1] - start[1]
            norm = math.hypot(dx, dy)
            normal = (-dy / norm, dx / norm)
            offset = bridge.width_m * 0.5 + length_m
            control = None
            for sign in (1.0, -1.0):
                control_start = (start[0] + sign * offset * normal[0], start[1] + sign * offset * normal[1])
                control_goal = (goal[0] + sign * offset * normal[0], goal[1] + sign * offset * normal[1])
                if fixture.block_reason(*control_start) or fixture.block_reason(*control_goal):
                    continue
                predicted = fixture.first_block(control_start, control_goal)
                if predicted is None or predicted[1] != WATER_TRANSITION_BLOCKED:
                    continue
                control = (control_start, control_goal, predicted, sign)
                break
            if control is None:
                raise FixtureCaseError(
                    f"bridge:{bridge_index}:{interval_index}: no dry off-bridge control exists"
                )
            control_start, control_goal, predicted, sign = control
            cases.append(
                FixtureCase(
                    case_id=f"bridge:{bridge_index}:{interval_index}:off_bridge_control",
                    category="bridge",
                    expected="block",
                    expected_block_reason=predicted[1],
                    start_xy_m=control_start,
                    waypoints_xy_m=(control_goal,),
                    block_distance_m=predicted[0],
                    approach_xy_m=predicted[2],
                    derivation={**derivation, "perpendicular_offset_m": sign * offset},
                )
            )
    return cases


def held_semantic_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Cases into each declared building footprint.

    Native movement reads only hydrology and bridge-flagged road vectors, so a
    building footprint is a held semantic (collision/cover owner pending). The
    matrix records what native movement does there; these cases are never
    admitted into a curriculum stage.
    """

    length_m = case_segment_length_m(fixture, goal_radius_m)
    cases = []
    for index, building in enumerate(fixture.buildings):
        xs = [point[0] for point in building.points]
        ys = [point[1] for point in building.points]
        centroid = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
        chosen = None
        for start in ((min(xs) - length_m, centroid[1]), (max(xs) + length_m, centroid[1])):
            if fixture.block_reason(*start) is None and fixture.first_block(start, centroid) is None:
                chosen = start
                break
        if chosen is None:
            raise FixtureCaseError(f"held:building:{index}: no dry approach to the footprint")
        cases.append(
            FixtureCase(
                case_id=f"held:building:{index}",
                category="held_semantic",
                expected="held",
                start_xy_m=chosen,
                waypoints_xy_m=(centroid,),
                derivation={
                    "source": "building_vector_features",
                    "feature_id": building.feature_id,
                    "held_owner": "collision_and_cover",
                },
            )
        )
    return cases


def derive_acceptance_cases(
    fixture: ArnisInfantryFixture, *, goal_radius_m: float
) -> tuple[FixtureCase, ...]:
    """Every acceptance-matrix case, in a stable category order."""

    cases = (
        *landcover_cases(fixture, goal_radius_m=goal_radius_m),
        *slope_band_cases(fixture, goal_radius_m=goal_radius_m),
        *water_cases(fixture, goal_radius_m=goal_radius_m),
        *edge_cases(fixture, goal_radius_m=goal_radius_m),
        *bridge_cases(fixture, goal_radius_m=goal_radius_m),
        *held_semantic_cases(fixture, goal_radius_m=goal_radius_m),
    )
    identifiers = [case.case_id for case in cases]
    if len(set(identifiers)) != len(identifiers):
        raise FixtureCaseError("derived case identifiers must be unique")
    return cases


__all__ = [
    "ArnisInfantryFixture",
    "BLOCKING_LANDCOVER_SEMANTICS",
    "FIXTURE_CASE_CONTRACT_VERSION",
    "FixtureCase",
    "FixtureCaseError",
    "OBSTACLE_TRANSITION_BLOCKED",
    "WATER_TRANSITION_BLOCKED",
    "bridge_cases",
    "case_segment_length_m",
    "derive_acceptance_cases",
    "edge_cases",
    "held_semantic_cases",
    "landcover_cases",
    "slope_band_cases",
    "water_cases",
]
