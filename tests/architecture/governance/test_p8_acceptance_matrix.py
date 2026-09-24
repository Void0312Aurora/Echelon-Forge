from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.governance_audit

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = (
  REPO_ROOT
  / "docs"
  / "architecture"
  / "work"
  / "active"
  / "long_horizon_architecture_governance"
  / "evidence"
  / "p8_acceptance_matrix_20260924.json"
)
AUTHORITY_PATH = REPO_ROOT / "docs/architecture/work/active/long_horizon_architecture_governance/long_horizon_architecture_governance_acceptance_20260825.md"


def _load() -> dict:
  return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_matrix_declares_acceptance_contract_as_authority() -> None:
  matrix = _load()
  assert matrix["kind"] == "derived_acceptance_matrix"
  assert matrix["authority"] == AUTHORITY_PATH.relative_to(REPO_ROOT).as_posix()
  assert AUTHORITY_PATH.is_file()
  assert matrix["decision"] != "accepted"


def test_p8_requirements_are_complete_and_residual_bearing() -> None:
  matrix = _load()
  requirements = matrix["requirements"]
  assert [item["id"] for item in requirements] == [
    "P8-01-caller-platform-topology",
    "P8-02-contract-replay-packaging",
    "P8-03-operations-security-restore",
    "P8-04-sustainability",
    "P8-05-independent-review",
    "P8-06-promoted-authority-history",
  ]
  assert all(item["owner"] and item["claim"] and item["residual"] for item in requirements)
  assert all(item["status"] in {"pass", "partial", "open", "not_eligible"} for item in requirements)


def test_open_requirements_cannot_have_empty_evidence_without_an_explicit_boundary() -> None:
  matrix = _load()
  for item in matrix["requirements"]:
    if item["status"] == "open":
      assert item["residual"]
      if not item["evidence"]:
        assert item["id"] == "P8-05-independent-review"


def test_topology_matrix_fails_closed_for_every_unsupported_row() -> None:
  matrix = _load()
  rows = matrix["topology_matrix"]
  assert {row["id"] for row in rows} == {
    "windows-msvc-cpu-in-process",
    "linux-cpu-in-process",
    "multi-process",
    "external-host",
    "cuda-canonical",
  }
  for row in rows:
    assert row["platform"] and row["process_topology"]
    assert row["support"] in {"pass", "partial", "unsupported"}
    assert isinstance(row["fail_closed"], bool)
    if row["support"] == "unsupported":
      assert row["fail_closed"] is True


def test_matrix_evidence_paths_are_tracked_or_are_the_authority_file() -> None:
  matrix = _load()
  paths = [
    path
    for item in matrix["requirements"]
    for path in item["evidence"]
  ] + [
    path
    for row in matrix["topology_matrix"]
    for path in row["evidence"]
  ]
  assert paths
  for relative in paths:
    assert (REPO_ROOT / relative).is_file(), relative


def test_review_pause_does_not_change_acceptance_decision() -> None:
  matrix = _load()
  assert matrix["review"] == {
    "required": True,
    "status": "paused",
    "reason": "upstream instability; main-thread implementation is not review-blocked",
  }
  assert matrix["decision"] == "not_eligible"
