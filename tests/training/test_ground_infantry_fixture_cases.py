"""Offline checks for the fixture-derived Ground infantry acceptance cases.

These tests need no compiled runtime: they pin that the case set is derived
from the verified Arnis bundle/overlay and fails closed when the fixture
cannot populate a category.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import pytest

from python.rl.ground.fixture_cases import (
    ArnisInfantryFixture,
    FixtureCaseError,
    OBSTACLE_TRANSITION_BLOCKED,
    WATER_TRANSITION_BLOCKED,
    case_segment_length_m,
    derive_acceptance_cases,
)


_FIXTURE_DIR = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
)
# The native probe's own goal-radius default; no matrix-local coefficient.
_GOAL_RADIUS_M = 5.0


@pytest.fixture(scope="module")
def fixture() -> ArnisInfantryFixture:
    return ArnisInfantryFixture(_FIXTURE_DIR)


@pytest.fixture(scope="module")
def cases(fixture: ArnisInfantryFixture):
    return derive_acceptance_cases(fixture, goal_radius_m=_GOAL_RADIUS_M)


def test_case_derivation_is_deterministic(cases) -> None:
    again = derive_acceptance_cases(ArnisInfantryFixture(_FIXTURE_DIR), goal_radius_m=_GOAL_RADIUS_M)
    assert json.dumps([case.as_dict() for case in cases], sort_keys=True) == json.dumps(
        [case.as_dict() for case in again], sort_keys=True
    )


def test_every_traversable_landcover_class_present_has_one_reach_case(
    fixture: ArnisInfantryFixture, cases
) -> None:
    counts = fixture.field_acceptance["landcover"]["class_counts"]
    traversable = {
        fixture.legend[int(code)]
        for code in counts
        if fixture.landcover_block_reason(int(code)) is None
    }
    landcover = [case for case in cases if case.category == "landcover"]
    assert {case.case_id.split(":", 1)[1] for case in landcover} == traversable
    minimum_length = case_segment_length_m(fixture, _GOAL_RADIUS_M)
    for case in landcover:
        assert case.expected == "reach"
        assert case.route_distance_m >= minimum_length - 1.0e-6
        assert fixture.block_reason(*case.start_xy_m) is None


def test_slope_bands_come_from_the_field_acceptance_percentiles(
    fixture: ArnisInfantryFixture, cases
) -> None:
    terrain = fixture.field_acceptance["terrain"]
    bands = fixture.slope_bands()
    assert [band[1] for band in bands[1:]] == [
        terrain["slope_p50_deg"],
        terrain["slope_p95_deg"],
        terrain["slope_p99_deg"],
    ]
    slope_cases = [case for case in cases if case.category == "slope_band"]
    assert len(slope_cases) == len(bands)
    for case, (_name, low, high) in zip(slope_cases, bands):
        assert low <= case.derivation["start_band_slope_deg"] < high


def test_water_cases_cover_landcover_water_and_each_hydrology_feature(
    fixture: ArnisInfantryFixture, cases
) -> None:
    water = [case for case in cases if case.category == "water_or_obstacle"]
    hydrology = [case for case in water if case.derivation["source"] == "hydrology_vector_features"]
    assert len(hydrology) == len(fixture.hydrology)
    assert any(case.derivation["source"] == "landcover_raster.class_legend" for case in water)
    for case in water:
        assert case.expected == "block"
        assert case.expected_block_reason == WATER_TRANSITION_BLOCKED
        assert fixture.block_reason(*case.start_xy_m) is None
        assert case.block_distance_m is not None and case.block_distance_m > 0.0


def test_edge_cases_block_outbound_and_reach_along_each_raster_edge(cases) -> None:
    edges = [case for case in cases if case.category == "raster_edge"]
    assert {case.case_id for case in edges} == {
        f"edge:{name}:{kind}"
        for name in ("west", "east", "north", "south")
        for kind in ("outbound", "parallel")
    }
    for case in edges:
        if case.case_id.endswith(":outbound"):
            assert case.expected_block_reason == OBSTACLE_TRANSITION_BLOCKED
        else:
            assert case.expected == "reach"


def test_bridge_crossing_spans_the_river_and_has_an_off_bridge_control(cases) -> None:
    bridge = [case for case in cases if case.category == "bridge"]
    crossings = [case for case in bridge if case.case_id.endswith(":crossing")]
    controls = [case for case in bridge if case.case_id.endswith(":off_bridge_control")]
    assert crossings and len(crossings) == len(controls)
    for crossing in crossings:
        assert crossing.requires_bridge_admission is True
        water_start, water_end = crossing.derivation["water_interval_m"]
        assert water_end > water_start
        assert crossing.route_distance_m > water_end - water_start
    for control in controls:
        assert control.expected_block_reason == WATER_TRANSITION_BLOCKED
        assert abs(control.derivation["perpendicular_offset_m"]) > control.derivation["bridge_width_m"] * 0.5


def test_held_building_footprints_are_enumerated_but_never_admitted(
    fixture: ArnisInfantryFixture, cases
) -> None:
    held = [case for case in cases if case.category == "held_semantic"]
    assert len(held) == len(fixture.buildings)
    assert all(case.expected == "held" for case in held)


def test_case_coordinates_are_finite(cases) -> None:
    for case in cases:
        for point in (case.start_xy_m, *case.waypoints_xy_m):
            assert all(math.isfinite(value) for value in point)


def _copy_fixture(tmp_path: Path) -> Path:
    copy = tmp_path / "fixture"
    shutil.copytree(_FIXTURE_DIR, copy, ignore=shutil.ignore_patterns("preview"))
    return copy


def test_missing_bridge_fails_closed(tmp_path: Path) -> None:
    copy = _copy_fixture(tmp_path)
    roads = copy / "expected" / "vectors" / "roads.cmo.json"
    document = json.loads(roads.read_text(encoding="utf-8"))
    for feature in document["features"]:
        feature["attributes"]["bridge"] = False
    roads.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(FixtureCaseError, match="no bridge"):
        ArnisInfantryFixture(copy)


def test_invalid_field_acceptance_report_fails_closed(tmp_path: Path) -> None:
    copy = _copy_fixture(tmp_path)
    report_path = copy / "field_acceptance.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["valid"] = False
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(FixtureCaseError, match="not valid"):
        ArnisInfantryFixture(copy)
