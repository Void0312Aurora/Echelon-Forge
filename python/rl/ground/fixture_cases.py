"""Deterministic acceptance cases derived from the Arnis infantry fixture.

Every case here is computed from the verified bundle manifest, its rasters and
vector features, the companion metadata overlay, and the retained field
acceptance report. No coordinate is hand-typed. The derivation *predicts*
where native movement should pass or block, so the native probe can be held
to an independent expectation; the probe remains the authority whose verdict
the acceptance matrix records.

This module is the stable public import path. The implementation is split by
concern:

* :mod:`.fixture_case_contract` -- the :class:`FixtureCase` contract, the
  native blocked-reason vocabulary, and the case-parameter digest;
* :mod:`.fixture_geometry` -- planar geometry, the native containment rule,
  and raster-mask morphology;
* :mod:`.fixture_map` -- :class:`ArnisInfantryFixture`, the read-only bundle
  view and its point/segment prediction;
* :mod:`.fixture_case_derivers` -- one deriver per case category.

It is case enumeration for acceptance tests and curriculum tooling only. It is
not a route graph, passability product, cost grid, or planner, and it carries
no runtime authority.
"""

from __future__ import annotations

from .fixture_case_contract import (
    BLOCKING_LANDCOVER_SEMANTICS,
    FIXTURE_CASE_CONTRACT_VERSION,
    OBSTACLE_TRANSITION_BLOCKED,
    WATER_TRANSITION_BLOCKED,
    FixtureCase,
    FixtureCaseError,
    case_parameters_digest,
)
from .fixture_case_derivers import (
    bridge_cases,
    case_segment_length_m,
    edge_cases,
    held_semantic_cases,
    landcover_cases,
    slope_band_cases,
    water_cases,
)
from .fixture_map import ArnisInfantryFixture, PredictedBlock, VectorFeature


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
    "PredictedBlock",
    "VectorFeature",
    "WATER_TRANSITION_BLOCKED",
    "bridge_cases",
    "case_parameters_digest",
    "case_segment_length_m",
    "derive_acceptance_cases",
    "edge_cases",
    "held_semantic_cases",
    "landcover_cases",
    "slope_band_cases",
    "water_cases",
]
