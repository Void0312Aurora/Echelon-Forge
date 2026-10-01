"""Per-category acceptance-case derivers over the Arnis infantry fixture.

Each deriver turns fixture data into :class:`FixtureCase` routes whose expected
native outcome is predicted by :class:`ArnisInfantryFixture` alone. Shared
construction (segment length, reach/block case assembly, interior-first cell
search) lives here once; the derivers differ only in which region they search
and how they place the start and goal.
"""

from __future__ import annotations

import math
from typing import Any, Iterator, Mapping, Sequence

import numpy as np

from .fixture_case_contract import (
    OBSTACLE_TRANSITION_BLOCKED,
    WATER_TRANSITION_BLOCKED,
    FixtureCase,
    FixtureCaseError,
)
from .fixture_geometry import (
    DIRECTIONS,
    Cell,
    Point,
    in_bounds,
    in_slope_band,
    interior_depth,
    polyline_length,
    polyline_point,
    sample_count,
    shifted,
    straight_run,
    straight_run_valid,
    union_mask,
)
from .fixture_map import ArnisInfantryFixture, PredictedBlock


def case_segment_length_m(fixture: ArnisInfantryFixture, goal_radius_m: float) -> float:
    """Case segment length: one source-native landcover cell plus the goal radius.

    A rollout therefore traverses at least one source-resolution landcover
    cell before it enters the env contract's goal radius.
    """

    return fixture.source_native_resolution_m + float(goal_radius_m)


def _segment_cells(fixture: ArnisInfantryFixture, goal_radius_m: float) -> int:
    return fixture.cells_for_length(case_segment_length_m(fixture, goal_radius_m))


def _run_in(mask: np.ndarray, run: Sequence[Cell]) -> bool:
    return all(mask[cell] for cell in run)


def _cells_by_interior_depth(mask: np.ndarray) -> Iterator[tuple[int, int, int]]:
    """``(row, column, depth)`` of mask cells, most interior first.

    Ties keep raster order (stable sort), so the search is deterministic.
    """

    depth = interior_depth(mask)
    for flat in np.argsort(-depth, axis=None, kind="stable"):
        value = int(depth.flat[flat])
        if value <= 0:
            return
        row, column = divmod(int(flat), mask.shape[1])
        yield row, column, value


def _reach_case(
    fixture: ArnisInfantryFixture,
    *,
    case_id: str,
    category: str,
    start: Point,
    goal: Point,
    derivation: Mapping[str, Any],
    requires_bridge_admission: bool = False,
) -> FixtureCase:
    """A reach case whose direct segment the fixture predicts passable."""

    if fixture.first_block(start, goal) is not None:
        raise FixtureCaseError(f"{case_id}: derived reach segment is predicted blocked")
    return FixtureCase(
        case_id=case_id,
        category=category,
        expected="reach",
        start_xy_m=start,
        waypoints_xy_m=(goal,),
        requires_bridge_admission=requires_bridge_admission,
        derivation=derivation,
    )


def _block_case(
    *,
    case_id: str,
    category: str,
    start: Point,
    goal: Point,
    predicted: PredictedBlock,
    derivation: Mapping[str, Any],
) -> FixtureCase:
    """A block case at the fixture's first predicted blocked sample."""

    return FixtureCase(
        case_id=case_id,
        category=category,
        expected="block",
        expected_block_reason=predicted.reason,
        start_xy_m=start,
        waypoints_xy_m=(goal,),
        block_distance_m=predicted.distance_m,
        approach_xy_m=predicted.approach_xy_m,
        derivation=derivation,
    )


# -- landcover -----------------------------------------------------------------


def _best_straight_segment(
    mask: np.ndarray, depth: np.ndarray, cells: int
) -> tuple[int, int, int, int, int] | None:
    """Most interior straight run of ``cells`` steps; returns (score, r, c, dr, dc)."""

    best: tuple[int, int, int, int, int] | None = None
    for dr, dc in DIRECTIONS:
        valid = straight_run_valid(mask, dr, dc, cells)
        end_depth = shifted(depth, cells * dr, cells * dc, 0)
        score = np.where(valid, np.minimum(depth, end_depth), 0)
        flat = int(np.argmax(score))
        value = int(score.flat[flat])
        if value > 0 and (best is None or value > best[0]):
            row, column = divmod(flat, mask.shape[1])
            best = (value, row, column, dr, dc)
    return best


def landcover_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """One reach case per traversable landcover class present in the fixture."""

    cells = _segment_cells(fixture, goal_radius_m)
    cases = []
    for code in fixture.present_landcover_codes:
        if fixture.landcover_block_reason(code) is not None:
            continue
        semantic = fixture.legend.get(code)
        if semantic is None:
            raise FixtureCaseError(f"landcover code {code} is missing from the legend")
        case_id = f"landcover:{semantic}"
        mask = (fixture.landcover == code) & ~fixture.hydrology_mask & ~fixture.bridge_mask
        best = _best_straight_segment(mask, interior_depth(mask), cells)
        if best is None:
            raise FixtureCaseError(f"{case_id}: fixture has no straight {cells}-cell run")
        score, row, column, dr, dc = best
        cases.append(
            _reach_case(
                fixture,
                case_id=case_id,
                category="landcover",
                start=fixture.cell_origin_xy_m(row, column),
                goal=fixture.cell_origin_xy_m(row + cells * dr, column + cells * dc),
                derivation={
                    "source": "landcover_raster.class_legend",
                    "landcover_code": code,
                    "interior_depth_cells": score,
                    "segment_cells": cells,
                },
            )
        )
    return cases


# -- slope bands ---------------------------------------------------------------


def slope_band_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """One reach case starting in each field-acceptance slope band."""

    cells = _segment_cells(fixture, goal_radius_m)
    stride = fixture.slope_stride
    slope = fixture.stride_slope_deg
    passable = fixture.dry_passable_mask
    stride_passable = passable[::stride, ::stride]
    band_grid = fixture.band_index_grid()
    cases = []
    for index, (name, low, high) in enumerate(fixture.slope_bands()):
        band = in_slope_band(slope, low, high) & stride_passable
        chosen: tuple[int, int, int, int, float] | None = None
        for stride_row, stride_column, _depth in _cells_by_interior_depth(band):
            row, column = stride_row * stride, stride_column * stride
            for dr, dc in DIRECTIONS:
                if not in_bounds(fixture.shape, (row + cells * dr, column + cells * dc)):
                    continue
                path = straight_run(row, column, dr, dc, cells)
                if not _run_in(passable, path):
                    continue
                in_band = sum(1 for cell in path if band_grid[cell] == index) / len(path)
                if chosen is None or in_band > chosen[4]:
                    chosen = (row, column, dr, dc, in_band)
            if chosen is not None:
                break
        if chosen is None:
            raise FixtureCaseError(f"slope_band:{name}: fixture cannot populate this band")
        row, column, dr, dc, in_band = chosen
        cases.append(
            _reach_case(
                fixture,
                case_id=f"slope_band:{name}",
                category="slope_band",
                start=fixture.cell_origin_xy_m(row, column),
                goal=fixture.cell_origin_xy_m(row + cells * dr, column + cells * dc),
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


# -- water ---------------------------------------------------------------------


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
    passable = fixture.dry_passable_mask
    for goal_row, goal_column, goal_depth in _cells_by_interior_depth(region):
        best: tuple[int, int, int] | None = None
        for dr, dc in DIRECTIONS:
            k = 1
            while in_bounds(fixture.shape, (goal_row + k * dr, goal_column + k * dc)) and not (
                fixture.passable_mask[goal_row + k * dr, goal_column + k * dc]
            ):
                k += 1
            approach = (goal_row + k * dr, goal_column + k * dc)
            if not in_bounds(fixture.shape, (approach[0] + cells * dr, approach[1] + cells * dc)):
                continue
            if not _run_in(passable, straight_run(approach[0], approach[1], dr, dc, cells)):
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
        return _block_case(
            case_id=case_id,
            category=category,
            start=start,
            goal=goal,
            predicted=predicted,
            derivation={
                **derivation,
                "goal_interior_depth_cells": goal_depth,
                "approach_cells_from_goal": k,
                "segment_cells_before_approach": cells,
            },
        )
    raise FixtureCaseError(f"{case_id}: no dry approach reaches this region")


def water_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Block cases into landcover water and into each declared hydrology feature."""

    cells = _segment_cells(fixture, goal_radius_m)
    cases = []
    for code in fixture.present_landcover_codes:
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
    masks = fixture.hydrology_masks
    for index, (feature, feature_mask) in enumerate(zip(fixture.hydrology, masks)):
        others = union_mask(fixture.shape, (mask for other, mask in enumerate(masks) if other != index))
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


# -- raster edges ----------------------------------------------------------------


def edge_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Outbound (must block) and edge-parallel (must reach) cases per raster edge."""

    cells = _segment_cells(fixture, goal_radius_m)
    height, width = fixture.shape
    passable = fixture.dry_passable_mask
    # (name, fixed axis, fixed index, inward (dr, dc))
    edges = (
        ("west", "column", 0, (0, 1)),
        ("east", "column", width - 1, (0, -1)),
        ("north", "row", 0, (1, 0)),
        ("south", "row", height - 1, (-1, 0)),
    )
    cases = []
    for name, axis, fixed, inward in edges:
        span = height if axis == "column" else width
        middle = (span - 1) / 2.0

        def edge_cell(index: int, fixed: int = fixed, axis: str = axis) -> Cell:
            return (index, fixed) if axis == "column" else (fixed, index)

        derivation = {"source": "elevation_raster.shape_origin_step", "edge": name, "segment_cells": cells}
        outbound = None
        for index in sorted(range(span), key=lambda value: (abs(value - middle), value)):
            row, column = edge_cell(index)
            if _run_in(passable, straight_run(row, column, inward[0], inward[1], cells)):
                outbound = (row, column)
                break
        if outbound is None:
            raise FixtureCaseError(f"edge:{name}: no passable inward run reaches this edge")
        row, column = outbound
        start = fixture.cell_origin_xy_m(row + cells * inward[0], column + cells * inward[1])
        goal = fixture.cell_origin_xy_m(row - cells * inward[0], column - cells * inward[1])
        predicted = fixture.first_block(start, goal)
        if predicted is None or predicted.reason != OBSTACLE_TRANSITION_BLOCKED:
            raise FixtureCaseError(f"edge:{name}: outbound segment must leave the raster")
        cases.append(
            _block_case(
                case_id=f"edge:{name}:outbound",
                category="raster_edge",
                start=start,
                goal=goal,
                predicted=predicted,
                derivation=dict(derivation),
            )
        )

        parallel = None
        for index in sorted(range(span - cells), key=lambda value: (abs(value + cells / 2.0 - middle), value)):
            run = [edge_cell(index + k) for k in range(cells + 1)]
            if _run_in(passable, run):
                parallel = run
                break
        if parallel is None:
            raise FixtureCaseError(f"edge:{name}: no passable run along this edge")
        cases.append(
            _reach_case(
                fixture,
                case_id=f"edge:{name}:parallel",
                category="raster_edge",
                start=fixture.cell_origin_xy_m(*parallel[0]),
                goal=fixture.cell_origin_xy_m(*parallel[-1]),
                derivation=dict(derivation),
            )
        )
    return cases


# -- bridges ---------------------------------------------------------------------


def _water_intervals(fixture: ArnisInfantryFixture, points: Sequence[Point]) -> list[list[float]]:
    """``[start, end]`` distances along a polyline over underlying water."""

    total = polyline_length(points)
    samples = sample_count(total, fixture.sample_spacing_m)
    intervals: list[list[float]] = []
    previous_water = False
    for index in range(samples + 1):
        distance = total * index / samples
        cell = fixture.cell(*polyline_point(points, distance))
        water = cell is not None and bool(fixture.underlying_water_mask[cell])
        if water and not previous_water:
            intervals.append([distance, distance])
        elif water:
            intervals[-1][1] = distance
        previous_water = water
    return intervals


def bridge_cases(fixture: ArnisInfantryFixture, *, goal_radius_m: float) -> list[FixtureCase]:
    """Crossing via each declared bridge, plus an off-bridge control that must block."""

    length_m = case_segment_length_m(fixture, goal_radius_m)
    cases = []
    for bridge_index, bridge in enumerate(fixture.bridges):
        points = bridge.points
        total = polyline_length(points)
        intervals = _water_intervals(fixture, points)
        if not intervals:
            raise FixtureCaseError(f"bridge:{bridge_index}: declared bridge crosses no water")
        for interval_index, (water_start, water_end) in enumerate(intervals):
            prefix = f"bridge:{bridge_index}:{interval_index}"
            if water_start - length_m < 0.0 or water_end + length_m > total:
                raise FixtureCaseError(f"{prefix}: crossing too close to the bridge end")
            start = polyline_point(points, water_start - length_m)
            goal = polyline_point(points, water_end + length_m)
            derivation = {
                "source": "road_vector_features.bridge",
                "feature_id": bridge.feature_id,
                "bridge_width_m": bridge.width_m,
                "water_interval_m": [water_start, water_end],
                "approach_length_m": length_m,
            }
            cases.append(
                _reach_case(
                    fixture,
                    case_id=f"{prefix}:crossing",
                    category="bridge",
                    start=start,
                    goal=goal,
                    derivation=derivation,
                    requires_bridge_admission=True,
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
                if predicted is None or predicted.reason != WATER_TRANSITION_BLOCKED:
                    continue
                control = (control_start, control_goal, predicted, sign)
                break
            if control is None:
                raise FixtureCaseError(f"{prefix}: no dry off-bridge control exists")
            control_start, control_goal, predicted, sign = control
            cases.append(
                _block_case(
                    case_id=f"{prefix}:off_bridge_control",
                    category="bridge",
                    start=control_start,
                    goal=control_goal,
                    predicted=predicted,
                    derivation={**derivation, "perpendicular_offset_m": sign * offset},
                )
            )
    return cases


# -- held semantics --------------------------------------------------------------


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


__all__ = [
    "bridge_cases",
    "case_segment_length_m",
    "edge_cases",
    "held_semantic_cases",
    "landcover_cases",
    "slope_band_cases",
    "water_cases",
]
