from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.runners import run_pytest_suite


REPO_ROOT = Path(run_pytest_suite.REPO_ROOT)
PYTEST_SUITE_MANIFESTS = (
  REPO_ROOT / "tests" / "smoke" / "ci_smoke_suite.json",
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
