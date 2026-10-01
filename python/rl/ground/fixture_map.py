"""Read-only view over the verified Arnis eastern-plain infantry fixture.

:class:`ArnisInfantryFixture` loads the bundle manifest, its landcover and
elevation rasters and vector features, the companion metadata overlay, and the
retained field-acceptance report. It exposes the raster grid, the rasterized
vector semantics, the field-acceptance slope grid, and a point/segment
prediction of where native movement should pass or block. It never calls the
native runtime: the prediction is an independent restatement of the native
rule, so the native probe can be held to it.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Mapping, NamedTuple, Sequence

import numpy as np

from .fixture_case_contract import (
    BLOCKING_LANDCOVER_SEMANTICS,
    OBSTACLE_TRANSITION_BLOCKED,
    WATER_TRANSITION_BLOCKED,
    FixtureCase,
    FixtureCaseError,
)
from .fixture_geometry import (
    Cell,
    Point,
    contains,
    in_slope_band,
    llround,
    segment_samples,
    union_mask,
)


# Slope bands use the retained field-acceptance percentiles as edges; the
# outer edges are the slope domain itself, [0, inf).
_SLOPE_BAND_EDGES: tuple[tuple[str, str | None, str | None], ...] = (
    ("below_p50", None, "slope_p50_deg"),
    ("p50_to_p95", "slope_p50_deg", "slope_p95_deg"),
    ("p95_to_p99", "slope_p95_deg", "slope_p99_deg"),
    ("above_p99", "slope_p99_deg", None),
)

DEFAULT_FIXTURE_DIR = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
)


@dataclass(frozen=True)
class VectorFeature:
    feature_id: str
    points: tuple[Point, ...]
    width_m: float
    polygon: bool
    attributes: Mapping[str, Any]

    def contains(self, x_m: float, y_m: float) -> bool:
        """Continuous-point containment with the native vector rule."""

        return bool(contains(x_m, y_m, self.points, polygon=self.polygon, width_m=self.width_m))


class PredictedBlock(NamedTuple):
    """First predicted blocked sample along a segment."""

    distance_m: float
    reason: str
    # The last predicted passable sample before it.
    approach_xy_m: Point


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FixtureCaseError(f"failed to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FixtureCaseError(f"{path} must contain an object")
    return value


class ArnisInfantryFixture:
    """Read-only view over the verified eastern-plain infantry fixture."""

    def __init__(self, fixture_dir: str | Path | None = None) -> None:
        root = Path(fixture_dir) if fixture_dir is not None else DEFAULT_FIXTURE_DIR
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

    def _vector_features(self, feature_class: str, *, bridge: bool | None) -> tuple[VectorFeature, ...]:
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
        features: list[VectorFeature] = []
        for feature in document.get("features", []):
            attributes = feature.get("attributes", {})
            if bridge is not None and bool(attributes.get("bridge", False)) != bridge:
                continue
            geometry = feature["geometry"]
            polygon = geometry["type"] == "Polygon"
            coordinates = geometry["coordinates"][0] if polygon else geometry["coordinates"]
            features.append(
                VectorFeature(
                    feature_id=str(feature["feature_id"]),
                    points=tuple((float(x), float(y)) for x, y in coordinates),
                    width_m=float(attributes.get("width_m", 0.0) or 0.0),
                    polygon=polygon,
                    attributes=attributes,
                )
            )
        return tuple(features)

    @property
    def present_landcover_codes(self) -> tuple[int, ...]:
        """Landcover codes the field-acceptance report counts, ascending."""

        return tuple(sorted(int(key) for key in self.field_acceptance["landcover"]["class_counts"]))

    # -- grid geometry -------------------------------------------------

    def cell_origin_xy_m(self, row: int, column: int) -> Point:
        return (
            self.origin_xy_m[0] + column * self.step_xy_m[0],
            self.origin_xy_m[1] + row * self.step_xy_m[1],
        )

    def cell(self, x_m: float, y_m: float) -> Cell | None:
        column = llround((x_m - self.origin_xy_m[0]) / self.step_xy_m[0])
        row = llround((y_m - self.origin_xy_m[1]) / self.step_xy_m[1])
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

    # -- rasterized vector semantics ----------------------------------

    def _geometry_mask(
        self,
        points: Sequence[Point],
        *,
        polygon: bool,
        width_m: float,
    ) -> np.ndarray:
        """Cells whose point the native containment rule places inside a geometry.

        Only the cells inside the geometry's bounding box, widened by half its
        width, are evaluated; every other cell is outside by construction.
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
        mask[r0:r1, c0:c1] = contains(grid_x, grid_y, points, polygon=polygon, width_m=width_m)
        return mask

    def _feature_mask(self, feature: VectorFeature) -> np.ndarray:
        return self._geometry_mask(feature.points, polygon=feature.polygon, width_m=feature.width_m)

    @cached_property
    def hydrology_masks(self) -> tuple[np.ndarray, ...]:
        return tuple(self._feature_mask(feature) for feature in self.hydrology)

    @cached_property
    def hydrology_mask(self) -> np.ndarray:
        return union_mask(self.shape, self.hydrology_masks)

    @cached_property
    def bridge_mask(self) -> np.ndarray:
        return union_mask(self.shape, (self._feature_mask(feature) for feature in self.bridges))

    @cached_property
    def building_mask(self) -> np.ndarray:
        return union_mask(self.shape, (self._feature_mask(feature) for feature in self.buildings))

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
    def dry_passable_mask(self) -> np.ndarray:
        """Predicted traversable cells off every bridge deck."""

        return self.passable_mask & ~self.bridge_mask

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

    # -- point / segment prediction -----------------------------------

    def segment_cells(self, case: FixtureCase) -> tuple[Cell, ...]:
        """Raster cells sampled at raster spacing along every case segment."""

        cells: list[Cell] = []
        points = (case.start_xy_m,) + case.waypoints_xy_m
        for start, end in zip(points, points[1:]):
            for _distance, point in segment_samples(start, end, self.sample_spacing_m):
                cell = self.cell(*point)
                if cell is not None and (not cells or cells[-1] != cell):
                    cells.append(cell)
        return tuple(cells)

    def block_reason(self, x_m: float, y_m: float) -> str | None:
        # Vector semantics are evaluated at the continuous point and take
        # precedence over the landcover cell, matching the native provider.
        cell = self.cell(x_m, y_m)
        if cell is None:
            return OBSTACLE_TRANSITION_BLOCKED
        if any(feature.contains(x_m, y_m) for feature in self.bridges):
            return None
        if any(feature.contains(x_m, y_m) for feature in self.hydrology):
            return WATER_TRANSITION_BLOCKED
        code = int(self.landcover[cell])
        if code not in self.legend:
            return OBSTACLE_TRANSITION_BLOCKED
        return self.landcover_block_reason(code)

    def first_block(self, start: Point, end: Point) -> PredictedBlock | None:
        """First predicted blocked sample along a segment at raster spacing."""

        last_passable = start
        for distance, point in segment_samples(start, end, self.sample_spacing_m):
            reason = self.block_reason(*point)
            if reason is not None:
                return PredictedBlock(distance, reason, last_passable)
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

    def _stride_index(self, index: Any, axis: int) -> Any:
        """Nearest field-acceptance sample index for full-resolution ``index``."""

        last = self.stride_slope_deg.shape[axis] - 1
        return np.clip(np.rint(np.asarray(index) / self.slope_stride).astype(int), 0, last)

    def stride_slope_at(self, cell: Cell) -> float:
        """Field-acceptance slope at the nearest sample of the acceptance grid."""

        row = int(self._stride_index(cell[0], 0))
        column = int(self._stride_index(cell[1], 1))
        return float(self.stride_slope_deg[row, column])

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

        slope = self.stride_slope_deg
        band = np.full(slope.shape, -1, dtype=np.int8)
        for index, (_name, low, high) in enumerate(self.slope_bands()):
            band[in_slope_band(slope, low, high)] = index
        rows = self._stride_index(np.arange(self.shape[0]), 0)
        columns = self._stride_index(np.arange(self.shape[1]), 1)
        return band[np.ix_(rows, columns)]


__all__ = [
    "ArnisInfantryFixture",
    "DEFAULT_FIXTURE_DIR",
    "PredictedBlock",
    "VectorFeature",
]
