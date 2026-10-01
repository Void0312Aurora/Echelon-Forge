"""Session-shared fixtures for the Ground infantry native acceptance tests.

The derived case set, the native acceptance matrix, and the scripted rollouts
behind it are deterministic for a given seed. Each is built once per session
and shared by the fixture-case, acceptance-matrix, replay-determinism, and
curriculum-stage modules. Determinism is still checked against an independent
build: the replay-determinism module re-runs a case subset without the cache
and compares it with the session matrix.

Imports of ``python.rl.ground`` stay inside the fixtures so that collecting the
other training tests never loads the compiled runtime.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture(scope="session")
def ground_acceptance_seed() -> int:
    """The native probe's own default reset seed."""

    from python.rl.ground.native_probe import GroundInfantryNativeProbe

    return int((GroundInfantryNativeProbe.reset.__kwdefaults__ or {})["seed"])


@pytest.fixture(scope="session")
def ground_infantry_fixture():
    from python.rl.ground.fixture_cases import ArnisInfantryFixture

    return ArnisInfantryFixture()


@pytest.fixture(scope="session")
def ground_acceptance_cases(ground_infantry_fixture):
    from python.rl.ground.acceptance_matrix import CONTRACT_GOAL_RADIUS_M
    from python.rl.ground.fixture_cases import derive_acceptance_cases

    return derive_acceptance_cases(ground_infantry_fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M)


@pytest.fixture(scope="session")
def ground_rollouts() -> dict[Any, Any]:
    """Scripted default-horizon rollouts shared by the matrix and the stages."""

    return {}


@pytest.fixture(scope="session")
def ground_acceptance_matrix(
    ground_acceptance_seed: int,
    ground_infantry_fixture,
    ground_acceptance_cases,
    ground_rollouts: dict[Any, Any],
) -> dict[str, Any]:
    from python.rl.ground.acceptance_matrix import build_acceptance_matrix

    return build_acceptance_matrix(
        seed=ground_acceptance_seed,
        fixture=ground_infantry_fixture,
        cases=ground_acceptance_cases,
        rollouts=ground_rollouts,
    )
