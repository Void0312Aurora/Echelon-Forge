"""Native acceptance matrix over the Arnis-derived infantry fixture map.

Every case is derived from the verified bundle/overlay by
``python.rl.ground.fixture_cases``; this module drives each one through the
compiled native probe (via ``GroundInfantryNativeEnv``) under the scripted
heading-to-goal controller and checks the fixture expectation fails closed.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from python.rl.ground.acceptance_matrix import (
    CONTRACT_BLOCKED_STEP_LIMIT,
    CONTRACT_GOAL_RADIUS_M,
    build_acceptance_matrix,
    case_failures,
    run_case,
)
from python.rl.ground.fixture_cases import ArnisInfantryFixture, derive_acceptance_cases


_SEED = 42


@pytest.fixture(scope="module")
def fixture() -> ArnisInfantryFixture:
    return ArnisInfantryFixture()


@pytest.fixture(scope="module")
def matrix(fixture: ArnisInfantryFixture) -> dict:
    return build_acceptance_matrix(seed=_SEED, fixture=fixture)


def test_native_acceptance_matrix_has_every_derived_category(matrix: dict) -> None:
    assert matrix["authority"] == "native_probe_only"
    assert matrix["production_boundary"] == "not_world_batch"
    assert set(matrix["summary"]) == {
        "landcover",
        "slope_band",
        "water_or_obstacle",
        "raster_edge",
        "bridge",
        "held_semantic",
    }
    assert {"route_planning", "line_of_sight", "cover"} <= set(matrix["does_not_claim"])


def test_native_acceptance_matrix_every_case_matches_the_fixture_expectation(matrix: dict) -> None:
    failing = {row["case_id"]: row["failures"] for row in matrix["rows"] if row["verdict"] != "pass"}
    assert not failing, failing
    assert matrix["valid"] is True


def test_native_acceptance_matrix_every_rollout_ends_with_an_explicit_reason(matrix: dict) -> None:
    for row in matrix["rows"]:
        assert (row["termination_reason"] is None) != (row["truncation_reason"] is None), row
        assert row["steps"] <= row["max_steps"]


def test_native_acceptance_matrix_blocked_cases_fail_closed(matrix: dict) -> None:
    blocked = [row for row in matrix["rows"] if row["expected"] == "block"]
    assert blocked
    for row in blocked:
        assert row["preflight_passable"] is False
        assert row["preflight_blocked_reason"] == row["expected_block_reason"]
        assert row["truncation_reason"] == "blocked_step_limit"
        assert row["blocked_reasons"] == [row["expected_block_reason"]]


def test_native_acceptance_matrix_bridge_crossing_is_admitted_and_control_blocks(matrix: dict) -> None:
    rows = {row["case_id"]: row for row in matrix["rows"] if row["category"] == "bridge"}
    crossings = [row for case_id, row in rows.items() if case_id.endswith(":crossing")]
    controls = [row for case_id, row in rows.items() if case_id.endswith(":off_bridge_control")]
    assert crossings and controls
    for row in crossings:
        assert row["outcome"] == "reach"
        assert row["bridge_admitted_steps"] > 0
    for row in controls:
        assert row["outcome"] == "block"
        assert row["bridge_admitted_steps"] == 0


def test_native_acceptance_matrix_records_held_building_behaviour(matrix: dict) -> None:
    held = [row for row in matrix["rows"] if row["category"] == "held_semantic"]
    assert held
    # Native movement does not consume building footprints. The outcome is
    # recorded as evidence and must not be promoted into a stage.
    for row in held:
        assert row["expected"] == "held"
        assert row["outcome"] in {"reach", "block"}


def test_native_acceptance_matrix_flags_a_wrong_expectation(fixture: ArnisInfantryFixture) -> None:
    cases = derive_acceptance_cases(fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M)
    control = next(case for case in cases if case.case_id.endswith(":off_bridge_control"))
    wrong = replace(control, expected="reach", expected_block_reason=None)
    rollout = run_case(control, seed=_SEED)
    failures = case_failures(wrong, rollout)
    assert "outcome:block" in failures
    assert any(failure.startswith("preflight_blocked:") for failure in failures)


def test_native_acceptance_matrix_short_horizon_truncates_instead_of_passing(
    fixture: ArnisInfantryFixture,
) -> None:
    cases = derive_acceptance_cases(fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M)
    crossing = next(case for case in cases if case.case_id.endswith(":crossing"))
    rollout = run_case(crossing, seed=_SEED, max_steps=CONTRACT_BLOCKED_STEP_LIMIT)
    assert rollout.truncation_reason == "max_steps"
    assert "outcome:truncated:max_steps" in case_failures(crossing, rollout)
