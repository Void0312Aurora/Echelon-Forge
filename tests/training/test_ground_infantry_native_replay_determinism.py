"""Replay determinism over the fixture-derived native acceptance cases.

Same seed must give a byte-identical canonical trace, the probe replay
entrypoint must reproduce the env rollout exactly, and the only trace content
allowed to change with the reset seed is the recorded seed itself.

The same-seed check compares two independent builds: the session acceptance
matrix's rollout (tests/training/conftest.py) and a fresh rollout here, for
one case per derived (category, expected outcome) pair.
"""

from __future__ import annotations

import pytest

from python.rl.ground.acceptance_matrix import (
    cached_rollout,
    difference_paths,
    replay_determinism,
    run_case,
)


# The reset trace records the seed it was given; that is the only content the
# native probe surfaces as seed-dependent for the single-soldier slice.
_SEED_RECORD_PATHS = {"[].trace.seed"}
# Every (category, expected outcome) pair the fixture derivation produces.
# ``test_replay_subset_covers_every_derived_outcome_pair`` fails if the
# derivation adds or drops one, so this list cannot silently go stale.
_OUTCOME_PAIRS = (
    ("landcover", "reach"),
    ("slope_band", "reach"),
    ("water_or_obstacle", "block"),
    ("raster_edge", "block"),
    ("raster_edge", "reach"),
    ("bridge", "block"),
    ("bridge", "reach"),
    ("held_semantic", "held"),
)


def _walked_distance_m(case) -> float:
    return case.block_distance_m if case.block_distance_m is not None else case.route_distance_m


def _representative(cases, category: str, expected: str):
    """The shortest-walk case of one (category, expected) pair."""

    matching = [case for case in cases if (case.category, case.expected) == (category, expected)]
    assert matching, (category, expected)
    return min(matching, key=_walked_distance_m)


def test_difference_paths_collapses_list_indices() -> None:
    left = [{"trace": {"seed": 1, "action": [0.0, 1.0]}}, {"trace": {"seed": 1}}]
    right = [{"trace": {"seed": 2, "action": [0.0, 1.0]}}, {"trace": {"seed": 2}}]
    assert difference_paths(left, right) == {"[].trace.seed"}
    assert difference_paths([1, 2], [1]) == {"[]#length"}
    assert difference_paths({"a": 1}, {"b": 1}) == {"a", "b"}
    assert difference_paths({"a": [1.0]}, {"a": [1.0]}) == set()


def test_replay_subset_covers_every_derived_outcome_pair(ground_acceptance_cases) -> None:
    assert {(case.category, case.expected) for case in ground_acceptance_cases} == set(_OUTCOME_PAIRS)
    subset = [_representative(ground_acceptance_cases, *pair) for pair in _OUTCOME_PAIRS]
    assert any(case.requires_bridge_admission for case in subset)


@pytest.mark.parametrize(("category", "expected"), _OUTCOME_PAIRS)
def test_native_case_replay_is_byte_identical_and_seed_only_changes_the_seed_field(
    ground_acceptance_cases,
    ground_acceptance_seed: int,
    ground_rollouts: dict,
    ground_acceptance_matrix: dict,
    category: str,
    expected: str,
) -> None:
    case = _representative(ground_acceptance_cases, category, expected)
    reference = cached_rollout(case, seed=ground_acceptance_seed, rollouts=ground_rollouts)
    rows = {row["case_id"]: row for row in ground_acceptance_matrix["rows"]}
    assert reference.digest == rows[case.case_id]["trace_sha256"]
    evidence = replay_determinism(
        case,
        seed=ground_acceptance_seed,
        alternate_seed=ground_acceptance_seed + 1,
        reference=reference,
    )

    assert evidence["same_seed_reference"] == "supplied_rollout"
    assert evidence["same_seed_identical"] is True, evidence
    assert evidence["same_seed_first_divergent_record"] is None
    assert evidence["probe_replay_identical"] is True, evidence
    assert evidence["cross_seed_outcome_identical"] is True, evidence
    assert set(evidence["cross_seed_difference_paths"]) == _SEED_RECORD_PATHS, evidence


def test_replay_determinism_without_a_reference_compares_two_fresh_rollouts(
    ground_acceptance_cases, ground_acceptance_seed: int
) -> None:
    case = _representative(ground_acceptance_cases, "landcover", "reach")
    evidence = replay_determinism(
        case, seed=ground_acceptance_seed, alternate_seed=ground_acceptance_seed + 1
    )
    assert evidence["same_seed_reference"] == "second_rollout"
    assert evidence["same_seed_identical"] is True, evidence
    # The line-skipping cross-seed walk equals the plain full-trace walk.
    first = run_case(case, seed=ground_acceptance_seed, keep_records=True)
    alternate = run_case(case, seed=ground_acceptance_seed + 1, keep_records=True)
    assert set(evidence["cross_seed_difference_paths"]) == difference_paths(
        list(first.records), list(alternate.records)
    )


def test_replay_determinism_flags_a_mismatched_reference(
    ground_acceptance_cases, ground_acceptance_seed: int, ground_rollouts: dict
) -> None:
    case = _representative(ground_acceptance_cases, "landcover", "reach")
    other = _representative(ground_acceptance_cases, "slope_band", "reach")
    wrong = cached_rollout(other, seed=ground_acceptance_seed, rollouts=ground_rollouts)
    with pytest.raises(ValueError, match="reference rollout"):
        replay_determinism(
            case, seed=ground_acceptance_seed, alternate_seed=ground_acceptance_seed + 1, reference=wrong
        )
