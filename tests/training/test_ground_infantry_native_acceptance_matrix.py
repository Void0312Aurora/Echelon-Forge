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
    build_acceptance_matrix,
    cached_rollout,
    case_failures,
    run_case,
)


# The matrix, its case set, and its rollouts are session fixtures
# (tests/training/conftest.py), shared with the replay and curriculum modules.
@pytest.fixture
def matrix(ground_acceptance_matrix: dict) -> dict:
    return ground_acceptance_matrix


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


def test_native_acceptance_matrix_flags_a_wrong_expectation(
    ground_acceptance_cases, ground_acceptance_seed: int, ground_rollouts: dict, matrix: dict
) -> None:
    control = next(case for case in ground_acceptance_cases if case.case_id.endswith(":off_bridge_control"))
    wrong = replace(control, expected="reach", expected_block_reason=None)
    rollout = cached_rollout(control, seed=ground_acceptance_seed, rollouts=ground_rollouts)
    failures = case_failures(wrong, rollout)
    assert "outcome:block" in failures
    assert any(failure.startswith("preflight_blocked:") for failure in failures)


def test_native_acceptance_matrix_short_horizon_truncates_instead_of_passing(
    ground_acceptance_cases, ground_acceptance_seed: int
) -> None:
    crossing = next(case for case in ground_acceptance_cases if case.case_id.endswith(":crossing"))
    rollout = run_case(crossing, seed=ground_acceptance_seed, max_steps=CONTRACT_BLOCKED_STEP_LIMIT)
    assert rollout.truncation_reason == "max_steps"
    assert "outcome:truncated:max_steps" in case_failures(crossing, rollout)


def test_native_acceptance_matrix_rollout_cache_is_keyed_by_seed_and_route(
    ground_acceptance_cases, ground_acceptance_seed: int, ground_rollouts: dict, matrix: dict
) -> None:
    # One shared rollout per (seed, case route): a hit returns the matrix's own
    # rollout, while another seed or a moved route is a new key, never stale.
    case = next(case for case in ground_acceptance_cases if case.case_id.endswith(":off_bridge_control"))
    cached = cached_rollout(case, seed=ground_acceptance_seed, rollouts=ground_rollouts)
    assert cached is cached_rollout(case, seed=ground_acceptance_seed, rollouts=ground_rollouts)
    assert cached.digest == {row["case_id"]: row for row in matrix["rows"]}[case.case_id]["trace_sha256"]
    scratch = dict(ground_rollouts)
    other_seed = cached_rollout(case, seed=ground_acceptance_seed + 1, rollouts=scratch)
    assert other_seed is not cached and other_seed.seed == ground_acceptance_seed + 1
    moved = replace(
        case,
        expected="reach",
        expected_block_reason=None,
        waypoints_xy_m=(case.approach_xy_m,),
        block_distance_m=None,
        approach_xy_m=None,
    )
    assert cached_rollout(moved, seed=ground_acceptance_seed, rollouts=scratch) is not cached
    assert len(scratch) == len(ground_rollouts) + 2


def test_native_acceptance_matrix_report_is_independent_of_the_rollout_cache(
    ground_acceptance_cases, ground_acceptance_seed: int, ground_infantry_fixture, matrix: dict
) -> None:
    # Same-seed digest identity over the full matrix is checked case by case
    # in the replay-determinism module against independent rollouts; here a
    # cache-free build of a case subset must reproduce the shared report rows.
    subset = [case for case in ground_acceptance_cases if case.category == "water_or_obstacle"]
    assert subset
    again = build_acceptance_matrix(
        seed=ground_acceptance_seed, fixture=ground_infantry_fixture, cases=subset
    )
    rows = {row["case_id"]: row for row in matrix["rows"]}
    assert again["rows"] == [rows[case.case_id] for case in subset]
