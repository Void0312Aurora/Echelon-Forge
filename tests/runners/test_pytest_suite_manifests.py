from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from tools.runners import run_pytest_suite, run_scenario_contract


REPO_ROOT = Path(run_pytest_suite.REPO_ROOT)
PYTEST_SUITE_MANIFESTS = (
  REPO_ROOT / "tests" / "smoke" / "ci_smoke_suite.json",
  REPO_ROOT / "tests" / "suites" / "architecture_guard_suite.json",
  REPO_ROOT / "tests" / "suites" / "governance_audit_suite.json",
)
CONTRACT_SUITE_MANIFESTS = (
  REPO_ROOT / "tests" / "smoke" / "ci_contract_suite.json",
)
ARCHITECTURE_GUARD_SUITE = PYTEST_SUITE_MANIFESTS[1]
GOVERNANCE_AUDIT_SUITE = PYTEST_SUITE_MANIFESTS[2]
CR2_STRICT_NUMERIC_NODE = (
  "tests/architecture/runtime_profiles/test_cuda_resident_counter_evidence.py::"
  "test_cr2_5b_counter_reports_reject_equal_valued_non_json_types"
)


def _load_json(path: Path) -> dict[str, Any]:
  data = json.loads(path.read_text(encoding="utf-8"))
  assert isinstance(data, dict), f"{path} must contain a JSON object"
  return data


def test_pytest_suite_manifest_entries_resolve_to_existing_base_paths() -> None:
  for manifest_path in PYTEST_SUITE_MANIFESTS:
    suite = _load_json(manifest_path)
    entries = suite.get("paths")
    assert isinstance(entries, list) and entries, f"{manifest_path} has no paths"
    for entry in entries:
      assert isinstance(entry, str) and entry.strip(), (
        f"{manifest_path} contains an invalid pytest entry: {entry!r}"
      )
      _, check_path = run_pytest_suite._resolve_pytest_entry(entry)
      assert Path(check_path).exists(), (
        f"{manifest_path} contains a stale pytest entry: {entry}"
      )


def test_contract_suite_manifest_entries_resolve_to_existing_specs() -> None:
  for manifest_path in CONTRACT_SUITE_MANIFESTS:
    specs = run_scenario_contract._load_suite_specs(
      manifest_path.relative_to(REPO_ROOT).as_posix(),
      str(REPO_ROOT),
    )
    assert specs, f"{manifest_path} has no specs"
    for spec_path in specs:
      assert Path(spec_path).exists(), (
        f"{manifest_path} contains a stale contract spec entry: {spec_path}"
      )


def test_no_capitalized_archive_dir_under_contracts() -> None:
  assert not (REPO_ROOT / "tests" / "contracts" / "Archive").exists()


def test_ci_smoke_uses_nodeids_for_broad_runtime_facade_layering_guard() -> None:
  entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
  broad_runtime_facade_files = (
    "tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py",
    "tests/architecture/runtime_facade/test_runtime_escape_hatches.py",
    "tests/architecture/runtime_facade/test_runtime_facade_contract_boundaries.py",
  )
  for broad_runtime_facade_file in broad_runtime_facade_files:
    assert broad_runtime_facade_file not in entries

  selected_nodes = [
    entry
    for entry in entries
    if any(entry.startswith(path + "::") for path in broad_runtime_facade_files)
  ]
  assert selected_nodes, "ci smoke should keep representative runtime facade nodeids"
  assert all("::" in entry for entry in selected_nodes)


def test_ci_smoke_keeps_cr2_counter_strict_numeric_gate_registered() -> None:
  entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
  assert CR2_STRICT_NUMERIC_NODE in entries


def test_ci_smoke_takes_no_governance_audit_files_wholesale() -> None:
  """Audit-tier files may contribute hand-picked node ids to the smoke
  suite, but never whole files: the suite runner applies no marker filter,
  so a wholesale entry would silently pull the on-demand audit tier back
  into every PR run.
  """
  smoke_entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
  audit_files = set(_load_json(GOVERNANCE_AUDIT_SUITE)["paths"])
  wholesale = [
    entry for entry in smoke_entries if "::" not in entry and entry in audit_files
  ]
  assert not wholesale, (
    "ci smoke must reference governance-audit files by node id only: "
    f"{wholesale}"
  )


def test_ci_smoke_uses_explicit_files_or_nodeids_not_directories() -> None:
  entries = _load_json(PYTEST_SUITE_MANIFESTS[0])["paths"]
  directory_entries = []
  for entry in entries:
    _, check_path = run_pytest_suite._resolve_pytest_entry(entry)
    if Path(check_path).is_dir():
      directory_entries.append(entry)

  assert not directory_entries, (
    "ci smoke should list explicit files or nodeids so new tests are not "
    f"promoted accidentally: {directory_entries}"
  )


def _architecture_test_files() -> set[str]:
  return {
    path.relative_to(REPO_ROOT).as_posix()
    for path in (REPO_ROOT / "tests" / "architecture").rglob("test_*.py")
  }


def _tier_suite_paths(manifest_path: Path) -> list[str]:
  """Load a tier manifest's paths and reject duplicate entries up front."""
  paths = _load_json(manifest_path)["paths"]
  duplicates = sorted(
    entry for entry, count in Counter(paths).items() if count > 1
  )
  assert not duplicates, (
    f"{manifest_path} lists duplicate entries: {duplicates}"
  )
  return paths


def _collected_governance_audit_files() -> set[str]:
  """Files that pytest actually selects for ``-m governance_audit``.

  Runs a real collection in a subprocess so the check observes the marker the
  same way developers do (module-level ``pytestmark`` and the
  runtime_profiles conftest tagging alike). A source-text scan would keep
  passing if a marker line were commented out or the conftest hook stopped
  running.
  """
  result = subprocess.run(
    [
      sys.executable,
      "-m",
      "pytest",
      "--collect-only",
      "-q",
      "-m",
      "governance_audit",
      "-p",
      "no:cacheprovider",
      "tests/architecture",
    ],
    cwd=REPO_ROOT,
    env=os.environ.copy(),
    capture_output=True,
    text=True,
    check=False,
  )
  assert result.returncode == 0, (
    "collecting governance_audit-marked tests failed "
    f"(exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
  )
  collected = {
    line.split("::", 1)[0].replace("\\", "/")
    for line in result.stdout.splitlines()
    if "::" in line and line.startswith("tests/architecture/")
  }
  assert collected, "collection returned no governance_audit-marked tests"
  return collected


def test_architecture_tier_suites_partition_the_architecture_test_files() -> None:
  guard = set(_tier_suite_paths(ARCHITECTURE_GUARD_SUITE))
  audit = set(_tier_suite_paths(GOVERNANCE_AUDIT_SUITE))

  overlap = guard & audit
  assert not overlap, f"tier suites must stay disjoint: {sorted(overlap)}"

  missing = _architecture_test_files() - guard - audit
  assert not missing, (
    "every tests/architecture test file must be assigned to exactly one tier "
    f"suite manifest: {sorted(missing)}"
  )

  stale = (guard | audit) - _architecture_test_files()
  assert not stale, f"tier suites contain non-architecture entries: {sorted(stale)}"


def test_governance_audit_suite_stays_in_lockstep_with_the_collected_marker() -> None:
  audit = set(_tier_suite_paths(GOVERNANCE_AUDIT_SUITE))
  collected = _collected_governance_audit_files()

  unmarked_entries = audit - collected
  assert not unmarked_entries, (
    "governance audit suite entries must be collected under -m "
    "governance_audit (module-level pytestmark or runtime_profiles conftest "
    f"tagging): {sorted(unmarked_entries)}"
  )

  unlisted_marked = collected - audit
  assert not unlisted_marked, (
    "files collected under -m governance_audit must be listed in the "
    f"governance audit suite manifest: {sorted(unlisted_marked)}"
  )
