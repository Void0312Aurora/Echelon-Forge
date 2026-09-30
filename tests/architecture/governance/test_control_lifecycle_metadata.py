"""Validate lifecycle metadata attached to the existing suite declarations.

P2-A keeps the lifecycle declaration beside the manifest that executes the
control. This test validates that small shared shape; it is not a second
control registry, generated inventory, or execution authority.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.governance_audit

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFESTS = (
  REPO_ROOT / "tests/smoke/ci_smoke_suite.json",
  REPO_ROOT / "tests/smoke/ci_contract_suite.json",
  REPO_ROOT / "tests/suites/architecture_guard_suite.json",
  REPO_ROOT / "tests/suites/governance_audit_suite.json",
)
REQUIRED_FIELDS = frozenset({
  "id",
  "owner",
  "invariant",
  "kind",
  "created",
  "expiry",
  "successor",
  "renewal_count",
  "removal_proof",
  "coverage",
})
ALLOWED_KINDS = frozenset({"permanent", "renewable", "migratory", "evidentiary"})


def _load(path: Path) -> dict[str, Any]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  assert isinstance(payload, dict), f"{path} must contain an object"
  return payload


def _parse_date(value: Any, field: str, manifest: Path) -> date | None:
  if value is None:
    return None
  assert isinstance(value, str) and value, f"{manifest}: {field} must be ISO date or null"
  try:
    return date.fromisoformat(value)
  except ValueError as exc:
    raise AssertionError(f"{manifest}: {field} is not an ISO date: {value!r}") from exc


def test_existing_suite_manifests_declare_control_lifecycle_metadata() -> None:
  seen_ids: set[str] = set()
  for manifest in MANIFESTS:
    payload = _load(manifest)
    lifecycle = payload.get("control_lifecycle")
    assert isinstance(lifecycle, dict), f"{manifest} lacks control_lifecycle metadata"
    assert lifecycle.get("schema_version") == 1, f"{manifest} has an unknown lifecycle schema"
    controls = lifecycle.get("controls")
    assert isinstance(controls, list) and controls, f"{manifest} declares no controls"
    manifest_paths = set(payload.get("paths", payload.get("specs", [])))
    for control in controls:
      assert isinstance(control, dict), f"{manifest}: control must be an object"
      assert REQUIRED_FIELDS <= control.keys(), (
        f"{manifest}: lifecycle fields missing for {control.get('id')!r}: "
        f"{sorted(REQUIRED_FIELDS - control.keys())}"
      )
      control_id = control["id"]
      assert isinstance(control_id, str) and control_id, f"{manifest}: empty control id"
      assert control_id not in seen_ids, f"duplicate lifecycle control id: {control_id}"
      seen_ids.add(control_id)
      assert isinstance(control["owner"], str) and control["owner"]
      assert isinstance(control["invariant"], str) and control["invariant"]
      kind = control["kind"]
      assert kind in ALLOWED_KINDS, f"{manifest}/{control_id}: invalid kind {kind!r}"
      created = _parse_date(control["created"], "created", manifest)
      expiry = _parse_date(control["expiry"], "expiry", manifest)
      assert created is not None
      if expiry is not None:
        assert created <= expiry, f"{manifest}/{control_id}: expiry precedes creation"
      assert isinstance(control["successor"], (str, type(None)))
      assert isinstance(control["removal_proof"], str) and control["removal_proof"]
      renewal_count = control["renewal_count"]
      assert isinstance(renewal_count, int) and not isinstance(renewal_count, bool)
      assert renewal_count in (0, 1), (
        f"{manifest}/{control_id}: at most one bounded renewal is allowed"
      )
      coverage = control["coverage"]
      assert isinstance(coverage, list) and coverage, f"{manifest}/{control_id}: no coverage"
      for covered in coverage:
        assert isinstance(covered, str) and covered
        if covered == "manifest":
          continue
        assert covered in manifest_paths, (
          f"{manifest}/{control_id}: coverage is not declared by the manifest: {covered}"
        )
        assert (REPO_ROOT / covered).is_file(), (
          f"{manifest}/{control_id}: covered control path is missing: {covered}"
        )
      if kind in {"migratory", "renewable"}:
        assert expiry is not None, f"{manifest}/{control_id}: temporary control needs expiry"
        assert isinstance(control["successor"], str) and control["successor"]
      if kind == "permanent":
        assert expiry is None, f"{manifest}/{control_id}: permanent control cannot expire"
        assert control["successor"] is None, f"{manifest}/{control_id}: permanent control has successor"
      if renewal_count == 1:
        sponsor = control.get("renewal_sponsor")
        forced_removal = _parse_date(control.get("forced_removal_date"), "forced_removal_date", manifest)
        assert isinstance(sponsor, str) and sponsor
        assert forced_removal is not None
        assert expiry is not None and forced_removal <= expiry


def test_migratory_controls_have_a_bounded_removal_route() -> None:
  migratory: list[tuple[str, str]] = []
  for manifest in MANIFESTS:
    payload = _load(manifest)
    for control in payload["control_lifecycle"]["controls"]:
      if control["kind"] == "migratory":
        migratory.append((control["id"], control["successor"]))
  assert migratory
  assert all(successor for _control_id, successor in migratory)


def test_expiry_simulation_requires_disposition_without_silent_renewal() -> None:
  simulated_date = date(2027, 4, 1)
  due_ids: list[str] = []
  for manifest in MANIFESTS:
    payload = _load(manifest)
    for control in payload["control_lifecycle"]["controls"]:
      if control["kind"] != "migratory":
        continue
      expiry = _parse_date(control["expiry"], "expiry", manifest)
      assert expiry is not None and expiry < simulated_date
      assert control["renewal_count"] == 0
      due_ids.append(control["id"])
  assert due_ids == [
    "runtime_facade_compatibility_migration",
    "archive_retirement_transition",
  ]
