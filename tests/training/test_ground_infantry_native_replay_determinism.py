"""Replay determinism over the fixture-derived native acceptance cases.

Same seed must give a byte-identical canonical trace, the probe replay
entrypoint must reproduce the env rollout exactly, and the only trace content
allowed to change with the reset seed is the recorded seed itself.
"""

from __future__ import annotations

import pytest

from python.rl.ground.acceptance_matrix import (
    CONTRACT_GOAL_RADIUS_M,
    difference_paths,
    replay_determinism,
)
from python.rl.ground.fixture_cases import ArnisInfantryFixture, derive_acceptance_cases


_SEED = 42
_ALTERNATE_SEED = 43
# The reset trace records the seed it was given; that is the only content the
# native probe surfaces as seed-dependent for the single-soldier slice.
_SEED_RECORD_PATHS = {"[].trace.seed"}


@pytest.fixture(scope="module")
def fixture() -> ArnisInfantryFixture:
    return ArnisInfantryFixture()


@pytest.fixture(scope="module")
def cases(fixture: ArnisInfantryFixture):
    return derive_acceptance_cases(fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M)


def _walked_distance_m(case) -> float:
    return case.block_distance_m if case.block_distance_m is not None else case.route_distance_m


def _representatives(cases):
    """The shortest-walk case of each category (one replay set per category).

    Full-length cases (such as the bridge crossing) are covered for same-seed
    identity by the matrix digest re-run in the acceptance-matrix module.
    """

    chosen = {}
    for case in cases:
        current = chosen.get(case.category)
        if current is None or _walked_distance_m(case) < _walked_distance_m(current):
            chosen[case.category] = case
    return [chosen[category] for category in sorted(chosen)]


def test_difference_paths_collapses_list_indices() -> None:
    left = [{"trace": {"seed": 1, "action": [0.0, 1.0]}}, {"trace": {"seed": 1}}]
    right = [{"trace": {"seed": 2, "action": [0.0, 1.0]}}, {"trace": {"seed": 2}}]
    assert difference_paths(left, right) == {"[].trace.seed"}
    assert difference_paths([1, 2], [1]) == {"[]#length"}


@pytest.mark.parametrize("category_index", range(6))
def test_native_case_replay_is_byte_identical_and_seed_only_changes_the_seed_field(
    cases, category_index: int
) -> None:
    representatives = _representatives(cases)
    assert len(representatives) == 6
    case = representatives[category_index]
    evidence = replay_determinism(case, seed=_SEED, alternate_seed=_ALTERNATE_SEED)

    assert evidence["same_seed_identical"] is True, evidence
    assert evidence["same_seed_first_divergent_record"] is None
    assert evidence["probe_replay_identical"] is True, evidence
    assert evidence["cross_seed_outcome_identical"] is True, evidence
    assert set(evidence["cross_seed_difference_paths"]) == _SEED_RECORD_PATHS, evidence
