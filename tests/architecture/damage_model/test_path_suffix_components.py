"""Unit tests for helpers.path_suffix_components (test-side path matcher).

Registered as a strengthening follow-up to the two Windows-red
retained_pack/manifest.json suffix assertions
(test_candidate_artifact_contracts.py, test_component_probability_artifacts.py;
T6 residual ledger sections 8.9 and 9.3). Those two call sites were repaired
at I65 by full Path-equality against the test-constructed output location --
adjudicated equivalent-or-stronger than this matcher for those sites (it pins
the whole path and rejects the boundary-crossing trap by construction), so
they stay exactly as I65 wrote them. This module keeps the matcher as a
reusable utility for the residual niche Path equality cannot serve: suffix
checks whose full expected path a test cannot construct (variable/unknown
prefix). These tests pin that the matcher accepts both separator conventions
and -- the negative half -- still rejects genuinely-wrong paths under both
Windows and POSIX separators, including the boundary-crossing suffix a raw
``str.endswith`` would have accepted.
"""

from __future__ import annotations

import pytest

from tests.architecture.damage_model.helpers import path_suffix_components

EXPECTED = ("retained_pack", "manifest.json")


@pytest.mark.parametrize(
  "value",
  [
    # Windows-native absolute (the real red's shape: tmp_path fallback).
    "C:\\Users\\u\\AppData\\Local\\Temp\\pytest-1\\t0\\retained_pack\\manifest.json",
    # POSIX absolute (the same tmp_path fallback on a POSIX host).
    "/tmp/pytest-1/t0/retained_pack/manifest.json",
    # Repo-relative POSIX (the in-repo _display_path branch).
    "docs/systems/effects/reviews/retained_pack/manifest.json",
    # Mixed separators (defensive: joined text crossing conventions).
    "C:\\Temp\\pytest-1\\t0/retained_pack/manifest.json",
    # Bare two-component relative path.
    "retained_pack\\manifest.json",
  ],
)
def test_accepts_expected_suffix_under_both_separator_conventions(
  value: str,
) -> None:
  assert path_suffix_components(value, 2) == EXPECTED


@pytest.mark.parametrize(
  "value",
  [
    # Wrong directory component, Windows separators.
    "C:\\Temp\\pytest-1\\t0\\other_pack\\manifest.json",
    # Wrong directory component, POSIX separators.
    "/tmp/pytest-1/t0/other_pack/manifest.json",
    # Wrong filename, Windows separators.
    "C:\\Temp\\pytest-1\\t0\\retained_pack\\manifest_v2.json",
    # Wrong filename, POSIX separators.
    "/tmp/pytest-1/t0/retained_pack/manifest.json.bak",
    # Components in the wrong order, Windows separators.
    "C:\\Temp\\manifest.json\\retained_pack",
    # Components in the wrong order, POSIX separators.
    "/tmp/manifest.json/retained_pack",
  ],
)
def test_rejects_genuinely_wrong_paths(value: str) -> None:
  assert path_suffix_components(value, 2) != EXPECTED


@pytest.mark.parametrize(
  "value",
  [
    "/tmp/pytest-1/t0/not_retained_pack/manifest.json",
    "C:\\Temp\\pytest-1\\t0\\not_retained_pack\\manifest.json",
  ],
)
def test_rejects_boundary_crossing_suffix_that_raw_endswith_accepts(
  value: str,
) -> None:
  # The trap the component comparison closes: raw text endswith matches the
  # "...not_retained_pack/manifest.json" tail (after separator normalization),
  # but "not_retained_pack" is not the "retained_pack" component.
  assert value.replace("\\", "/").endswith("retained_pack/manifest.json")
  assert path_suffix_components(value, 2) != EXPECTED


def test_rejects_path_with_fewer_components_than_requested() -> None:
  assert path_suffix_components("manifest.json", 2) != EXPECTED
  assert path_suffix_components("manifest.json", 2) == ("manifest.json",)


def test_separator_runs_and_leading_separators_are_normalized() -> None:
  # Doubled separators and leading slashes collapse to clean components, so
  # UNC-ish or sloppily joined producer text cannot dodge the comparison.
  assert path_suffix_components("//tmp//t0//retained_pack//manifest.json", 2) == (
    EXPECTED
  )
  assert path_suffix_components("\\\\host\\share\\retained_pack\\manifest.json", 2) == (
    EXPECTED
  )
