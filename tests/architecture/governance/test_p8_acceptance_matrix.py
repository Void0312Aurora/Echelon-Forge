from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.rl.runtime.rollout_gate import FileRolloutDecisionStore
from python.rl.runtime.rollout_gate import RolloutAdmissionError
from python.rl.runtime.rollout_gate import build_rollout_decision_envelope


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
  assert matrix["decision"] == "accepted"
  assert "outside the current acceptance boundary" in matrix["decision_reason"]
  p8_01 = next(item for item in matrix["requirements"] if item["id"] == "P8-01-caller-platform-topology")
  assert any("p5d_owner_acceptance_and_rebuild_retirement_20260927.md" in path for path in p8_01["evidence"])
  assert "production caller cutover remain partial" not in p8_01["residual"]


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
    assert row["verification"]
    if row["support"] == "unsupported":
      assert row["fail_closed"] is True


def test_topology_matrix_verification_points_to_executable_gates() -> None:
  matrix = _load()
  for row in matrix["topology_matrix"]:
    for reference in row["verification"]:
      relative, symbol = reference.split("::", 1)
      path = REPO_ROOT / relative
      assert path.is_file(), reference
      assert symbol in path.read_text(encoding="utf-8"), reference


def test_unsupported_topology_admission_is_executable_fail_closed(tmp_path: Path) -> None:
  key = b"p8-topology-test-key-0123456789abcdef"
  payload = {
    "authority_kind": "rollout_decision",
    "schema_version": "echelon_forge.rollout_decision.v1",
    "contract_version": "echelon_forge.rollout_decision_contract.v1",
    "writer_role": "release_controller",
    "decision_id": "p8-topology-decision-0",
    "release_id": "p8-topology-release",
    "manifest_sha256": "a" * 64,
    "plan_sha256": "b" * 64,
    "plan_reader_generation_min": "1",
    "plan_reader_generation_max": "1",
    "predecessor_decision_id": "",
    "state": "prepared",
    "writer_generation": "1",
    "decision_sequence": "0",
    "cohort": "local-in-process",
    "rollback_deadline": "2026-12-31T00:00:00Z",
    "checkpoint_id": "",
    "irreversible_write_boundary": "none",
  }
  store = FileRolloutDecisionStore(
    tmp_path / "rollout.json",
    writer_id="p8-topology-test-writer",
    signing_key=key,
    key_id="p8-topology-test-key",
  )
  store.commit(build_rollout_decision_envelope(
    payload,
    key_id="p8-topology-test-key",
    signing_key=key,
  ))
  for topology in ("multi-process", "external-host", "cuda"):
    with pytest.raises(RolloutAdmissionError, match="only the admitted local in-process topology"):
      store.read(topology=topology)


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


def test_bounded_acceptance_does_not_require_independent_review() -> None:
  matrix = _load()
  assert matrix["review"] == {
    "required": False,
    "status": "not-required",
    "reason": "User-directed bounded acceptance; main-thread verification is authoritative and no independent agent is required.",
  }
  assert matrix["decision"] == "accepted"
