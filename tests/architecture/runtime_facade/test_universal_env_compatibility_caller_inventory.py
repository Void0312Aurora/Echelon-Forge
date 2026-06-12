from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
  REPO_ROOT
  / "tests"
  / "architecture"
  / "fixtures"
  / "universal_env_runtime_compatibility_callers_20260612.json"
)


def _load_fixture() -> dict:
  return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _entries() -> list[dict]:
  return list(_load_fixture()["entries"])


def _relative(path: Path) -> str:
  return path.relative_to(REPO_ROOT).as_posix()


def _is_excluded(path: Path) -> bool:
  rel = _relative(path)
  return (
    rel.startswith("tests/archive/")
    or rel.startswith("tools/archive/")
    or "/__pycache__/" in f"/{rel}/"
  )


def _is_true_constant(node: ast.AST) -> bool:
  return isinstance(node, ast.Constant) and node.value is True


def _runtime_compatibility_true_call_count(path: Path) -> int:
  tree = ast.parse(path.read_text(encoding="utf-8"))
  count = 0
  for node in ast.walk(tree):
    if isinstance(node, ast.Call):
      count += sum(
        1
        for keyword in node.keywords
        if keyword.arg == "runtime_compatibility_enabled"
        and _is_true_constant(keyword.value)
      )
    if isinstance(node, ast.Dict):
      count += sum(
        1
        for key, value in zip(node.keys, node.values)
        if isinstance(key, ast.Constant)
        and key.value == "runtime_compatibility_enabled"
        and _is_true_constant(value)
      )
  return count


def _active_runtime_compatibility_true_counts() -> Counter[str]:
  counts: Counter[str] = Counter()
  for root_name in _load_fixture()["scan_roots"]:
    root = REPO_ROOT / root_name
    for path in sorted(root.rglob("*.py")):
      if _is_excluded(path):
        continue
      count = _runtime_compatibility_true_call_count(path)
      if count:
        counts[_relative(path)] = count
  return counts


def test_inventory_uses_canonical_classification_and_disposition_vocabulary() -> None:
  fixture = _load_fixture()
  allowed_classifications = set(fixture["allowed_classifications"])
  allowed_dispositions = set(fixture["allowed_dispositions"])

  assert allowed_classifications == {
    "runtime_regression_raw_env",
    "manual_diagnostics_raw_env",
    "negative_rejection_guard",
  }
  assert allowed_dispositions == {
    "retain_runtime_regression_until_world_batch_or_facade_equivalent_exists",
    "retain_manual_diagnostics_until_tool_migrated_or_archived",
    "retain_negative_guard",
  }

  for entry in _entries():
    assert entry["classification"] in allowed_classifications
    assert entry["disposition"] in allowed_dispositions
    if "occurrence_groups" in entry:
      grouped_count = sum(int(group["call_count"]) for group in entry["occurrence_groups"])
      assert grouped_count == int(entry["call_count"])
      for group in entry["occurrence_groups"]:
        assert group["classification"] in allowed_classifications
        assert group["disposition"] in allowed_dispositions


def test_inventory_entries_reference_real_files_and_evidence_markers() -> None:
  for entry in _entries():
    path = REPO_ROOT / entry["path"]
    assert path.is_file(), f"missing inventory path: {entry['path']}"
    source = path.read_text(encoding="utf-8")
    for marker in entry["evidence_markers"]:
      assert marker in source, f"{entry['path']} missing evidence marker: {marker}"
    assert str(entry["surface"]).strip()
    assert str(entry["migration_target"]).strip()
    assert str(entry["next_action"]).strip()


def test_active_runtime_compatibility_true_callers_are_fully_inventoried() -> None:
  expected = Counter(
    {str(entry["path"]): int(entry["call_count"]) for entry in _entries()}
  )
  actual = _active_runtime_compatibility_true_counts()

  assert actual == expected


def test_inventory_keeps_rejection_guards_separate_from_raw_env_opt_ins() -> None:
  guard_paths = {
    entry["path"]
    for entry in _entries()
    if entry["classification"] == "negative_rejection_guard"
  }

  assert guard_paths == set()

  for entry in _entries():
    if entry["classification"] == "negative_rejection_guard":
      assert entry["disposition"] == "retain_negative_guard"
      assert entry["migration_target"].startswith("none;")


def test_inventory_counts_remaining_registered_surfaces() -> None:
  disposition_counts: Counter[str] = Counter()
  for entry in _entries():
    if "occurrence_groups" in entry:
      for group in entry["occurrence_groups"]:
        disposition_counts[group["disposition"]] += int(group["call_count"])
    else:
      disposition_counts[entry["disposition"]] += int(entry["call_count"])

  assert disposition_counts == {
    "retain_runtime_regression_until_world_batch_or_facade_equivalent_exists": 6,
    "retain_manual_diagnostics_until_tool_migrated_or_archived": 1,
  }


def test_visualization_session_uses_maintained_world_batch_runtime() -> None:
  source = (REPO_ROOT / "examples" / "viz" / "runtime" / "viz_session.py").read_text(
    encoding="utf-8"
  )

  assert "from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv" in source
  assert "WorldBatchVecEnv(" in source
  assert "from gym_envs.universal_env import" not in source
  assert "UniversalEnv(" not in source
  assert "runtime_compatibility_enabled=True" not in source
