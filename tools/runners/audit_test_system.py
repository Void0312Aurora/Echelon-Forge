#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

DEFAULT_PYTEST_SMOKE_SUITE = Path("tests/smoke/ci_smoke_suite.json")
DEFAULT_CONTRACT_SMOKE_SUITE = Path("tests/smoke/ci_contract_suite.json")

OVERSIZED_FILE_LINES = 800
OVERSIZED_TEST_ITEM_LINES = 120
ASSERT_HEAVY_FILE = 120
ASSERT_HEAVY_ITEM = 50
LITERAL_HEAVY_FILE = 250
LITERAL_HEAVY_ITEM = 100
SOURCE_SCAN_REFS = 10


def _repo_path(path: str | Path, root: Path = REPO_ROOT) -> Path:
  candidate = Path(path)
  if candidate.is_absolute():
    return candidate
  return root / candidate


def _git_ls_files(root: Path, pathspec: str) -> list[str]:
  proc = subprocess.run(
    ["git", "ls-files", pathspec],
    cwd=root,
    check=True,
    text=True,
    capture_output=True,
  )
  return [line for line in proc.stdout.splitlines() if line.strip()]


def _is_archive_path(path: str) -> bool:
  return any(part.lower() == "archive" for part in Path(path).parts)


def _active_paths(paths: list[str]) -> list[str]:
  return [path for path in paths if not _is_archive_path(path)]


def _load_json(path: Path) -> dict[str, Any]:
  with path.open("r", encoding="utf-8") as f:
    data = json.load(f)
  if not isinstance(data, dict):
    raise TypeError(f"expected JSON object at {path}")
  return data


def _entry_file(entry: str) -> str:
  return str(entry).strip().partition("::")[0].replace("\\", "/")


def _load_pytest_smoke_files(root: Path, suite_path: Path) -> tuple[set[str], int]:
  path = _repo_path(suite_path, root)
  if not path.exists():
    return set(), 0
  suite = _load_json(path)
  entries = suite.get("paths", [])
  if not isinstance(entries, list):
    raise TypeError(f"pytest suite {path} has non-list 'paths'")
  files = {_entry_file(str(entry)) for entry in entries if isinstance(entry, str)}
  return files, len(entries)


def _load_contract_smoke_specs(root: Path, suite_path: Path) -> set[str]:
  path = _repo_path(suite_path, root)
  if not path.exists():
    return set()
  suite = _load_json(path)
  raw_specs = suite.get("specs", suite.get("paths", []))
  if not isinstance(raw_specs, list):
    raise TypeError(f"contract suite {path} has non-list specs/paths")
  return {str(spec).replace("\\", "/") for spec in raw_specs if isinstance(spec, str)}


def _source_dir(path: str) -> str:
  parts = path.split("/")
  if len(parts) >= 2:
    return "/".join(parts[:2])
  return path


def _constant_counts(node: ast.AST) -> dict[str, int]:
  strings = 0
  numbers = 0
  path_literals = 0
  for child in ast.walk(node):
    if not isinstance(child, ast.Constant):
      continue
    value = child.value
    if isinstance(value, str):
      strings += 1
      if "/" in value or value.endswith((".py", ".cpp", ".h", ".md", ".json", ".yml")):
        path_literals += 1
    elif isinstance(value, (int, float, complex)) and not isinstance(value, bool):
      numbers += 1
  return {
    "string_literals": strings,
    "numeric_literals": numbers,
    "path_literals": path_literals,
    "total_literals": strings + numbers,
  }


def _call_name(node: ast.AST) -> str:
  if isinstance(node, ast.Name):
    return node.id
  if isinstance(node, ast.Attribute):
    parent = _call_name(node.value)
    if parent:
      return f"{parent}.{node.attr}"
    return node.attr
  return ""


def _looks_like_unittest_base(base: ast.AST) -> bool:
  name = _call_name(base)
  return name == "TestCase" or name.endswith(".TestCase")


def _test_item_rows(tree: ast.AST) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
      "test_"
    ):
      rows.append(_test_item_stats(node, node.name, "function"))
    elif isinstance(node, ast.ClassDef):
      for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith(
          "test_"
        ):
          rows.append(_test_item_stats(item, f"{node.name}.{item.name}", "method"))
  return rows


def _test_item_stats(
  node: ast.FunctionDef | ast.AsyncFunctionDef,
  name: str,
  item_kind: str,
) -> dict[str, Any]:
  span = max(1, int(getattr(node, "end_lineno", node.lineno)) - int(node.lineno) + 1)
  literal_counts = _constant_counts(node)
  assert_count = sum(1 for child in ast.walk(node) if isinstance(child, ast.Assert))
  return {
    "name": name,
    "kind": item_kind,
    "line": int(node.lineno),
    "span": span,
    "asserts": assert_count,
    **literal_counts,
  }


def _test_class_rows(tree: ast.AST) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for node in ast.walk(tree):
    if not isinstance(node, ast.ClassDef):
      continue
    methods = [
      item.name
      for item in node.body
      if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
      and item.name.startswith("test_")
    ]
    base_names = [_call_name(base) for base in node.bases]
    is_unittest = any(_looks_like_unittest_base(base) for base in node.bases)
    is_test_named = node.name.startswith("Test") or node.name.endswith("Tests")
    if methods or is_unittest or is_test_named:
      rows.append(
        {
          "name": node.name,
          "line": int(node.lineno),
          "methods": len(methods),
          "bases": base_names,
          "unittest": is_unittest,
          "mixin_bases": [
            base for base in base_names if base and not base.endswith("TestCase")
          ],
        }
      )
  return rows


def _source_scan_refs(tree: ast.AST) -> int:
  refs = 0
  for node in ast.walk(tree):
    if isinstance(node, ast.Call):
      name = _call_name(node.func)
      if name.endswith(".read_text") or name in {"open", "Path"}:
        refs += 1
    elif isinstance(node, ast.Name) and node.id == "REPO_ROOT":
      refs += 1
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
      value = node.value
      if "/" in value or value.endswith((".py", ".cpp", ".h", ".md", ".json", ".yml")):
        refs += 1
  return refs


def _risk_flags(stats: dict[str, Any]) -> list[str]:
  flags: list[str] = []
  if stats["loc"] >= OVERSIZED_FILE_LINES:
    flags.append("oversized_file")
  if stats["max_test_item_span"] >= OVERSIZED_TEST_ITEM_LINES:
    flags.append("oversized_test_item")
  if stats["asserts"] >= ASSERT_HEAVY_FILE or stats["max_test_item_asserts"] >= ASSERT_HEAVY_ITEM:
    flags.append("assert_heavy")
  if stats["literal_count"] >= LITERAL_HEAVY_FILE or stats["max_test_item_literals"] >= LITERAL_HEAVY_ITEM:
    flags.append("literal_heavy")
  if stats["source_scan_refs"] >= SOURCE_SCAN_REFS:
    flags.append("source_scan_guard")
  if stats["mixin_collected_tests"]:
    flags.append("hidden_mixin_tests")
  if stats["mixin_wrapper_file"]:
    flags.append("mixin_wrapper_file")
  if stats["risk_score_without_smoke"] >= 3 and not stats["in_pytest_smoke"]:
    flags.append("not_smoke_gated")
  return flags


def _risk_score(flags: list[str]) -> int:
  weights = {
    "oversized_file": 2,
    "oversized_test_item": 2,
    "assert_heavy": 2,
    "literal_heavy": 2,
    "source_scan_guard": 1,
    "hidden_mixin_tests": 1,
    "mixin_wrapper_file": 1,
    "not_smoke_gated": 1,
  }
  return sum(weights.get(flag, 0) for flag in flags)


def analyze_python_test_file(
  root: Path,
  relpath: str,
  *,
  pytest_smoke_files: set[str],
) -> dict[str, Any]:
  path = root / relpath
  text = path.read_text(encoding="utf-8", errors="replace")
  tree = ast.parse(text, filename=relpath)
  lines = text.splitlines()
  test_items = _test_item_rows(tree)
  test_classes = _test_class_rows(tree)
  file_literals = _constant_counts(tree)
  path_name = Path(relpath).name
  is_test_file = path_name.startswith("test_")
  mixin_collected_tests = bool(test_items) and not is_test_file
  mixin_wrapper_file = (
    is_test_file
    and not test_items
    and any(row["mixin_bases"] for row in test_classes)
  )
  max_test_item_span = max([row["span"] for row in test_items], default=0)
  max_test_item_asserts = max([row["asserts"] for row in test_items], default=0)
  max_test_item_literals = max([row["total_literals"] for row in test_items], default=0)
  source_scan_refs = _source_scan_refs(tree)
  stats: dict[str, Any] = {
    "path": relpath,
    "directory": _source_dir(relpath),
    "loc": len(lines),
    "in_pytest_smoke": relpath in pytest_smoke_files,
    "is_test_file": is_test_file,
    "test_items": len(test_items),
    "test_classes": len(test_classes),
    "unittest_classes": sum(1 for row in test_classes if row["unittest"]),
    "asserts": sum(row["asserts"] for row in test_items),
    "literal_count": file_literals["total_literals"],
    "path_literal_count": file_literals["path_literals"],
    "source_scan_refs": source_scan_refs,
    "max_test_item_span": max_test_item_span,
    "max_test_item_asserts": max_test_item_asserts,
    "max_test_item_literals": max_test_item_literals,
    "mixin_collected_tests": mixin_collected_tests,
    "mixin_wrapper_file": mixin_wrapper_file,
    "top_test_items": sorted(
      test_items,
      key=lambda row: (row["span"], row["total_literals"], row["asserts"]),
      reverse=True,
    )[:5],
  }
  base_flags = _risk_flags({**stats, "risk_score_without_smoke": 0})
  stats["risk_score_without_smoke"] = _risk_score(base_flags)
  flags = _risk_flags(stats)
  stats["risk_flags"] = flags
  stats["risk_score"] = _risk_score(flags)
  return stats


def _contract_group(path: str) -> str:
  parts = path.split("/")
  if len(parts) >= 3:
    return "/".join(parts[:3])
  return path


def analyze_contract_file(
  root: Path,
  relpath: str,
  *,
  contract_smoke_specs: set[str],
) -> dict[str, Any]:
  path = root / relpath
  text = path.read_text(encoding="utf-8")
  data = json.loads(text)
  if not isinstance(data, dict):
    raise TypeError(f"expected contract JSON object at {relpath}")
  return {
    "path": relpath,
    "group": _contract_group(relpath),
    "loc": len(text.splitlines()),
    "in_contract_smoke": relpath in contract_smoke_specs,
    "type": data.get("type"),
    "check_kind": data.get("check_kind"),
    "case_count": len(data.get("cases", [])) if isinstance(data.get("cases"), list) else 0,
    "top_level_keys": sorted(data.keys()),
  }


def build_audit(
  *,
  root: Path = REPO_ROOT,
  test_files: list[str] | None = None,
  pytest_smoke_suite: Path = DEFAULT_PYTEST_SMOKE_SUITE,
  contract_smoke_suite: Path = DEFAULT_CONTRACT_SMOKE_SUITE,
) -> dict[str, Any]:
  if test_files is None:
    test_files = _git_ls_files(root, "tests")
  active_files = _active_paths(test_files)
  pytest_smoke_files, pytest_smoke_entries = _load_pytest_smoke_files(
    root, pytest_smoke_suite
  )
  contract_smoke_specs = _load_contract_smoke_specs(root, contract_smoke_suite)

  py_files = [path for path in active_files if path.endswith(".py")]
  json_contracts = [
    path
    for path in active_files
    if path.startswith("tests/contracts/") and path.endswith(".json")
  ]
  py_stats = [
    analyze_python_test_file(root, path, pytest_smoke_files=pytest_smoke_files)
    for path in py_files
  ]
  contract_stats = [
    analyze_contract_file(root, path, contract_smoke_specs=contract_smoke_specs)
    for path in json_contracts
  ]

  directories: dict[str, dict[str, Any]] = defaultdict(
    lambda: {
      "files": 0,
      "python_files": 0,
      "loc": 0,
      "test_items": 0,
      "asserts": 0,
      "source_scan_refs": 0,
      "risk_flags": Counter(),
    }
  )
  for path in active_files:
    directories[_source_dir(path)]["files"] += 1
  for stats in py_stats:
    row = directories[stats["directory"]]
    row["python_files"] += 1
    row["loc"] += stats["loc"]
    row["test_items"] += stats["test_items"]
    row["asserts"] += stats["asserts"]
    row["source_scan_refs"] += stats["source_scan_refs"]
    row["risk_flags"].update(stats["risk_flags"])

  directory_rows = []
  for directory, row in directories.items():
    directory_rows.append(
      {
        "directory": directory,
        "files": row["files"],
        "python_files": row["python_files"],
        "loc": row["loc"],
        "test_items": row["test_items"],
        "asserts": row["asserts"],
        "source_scan_refs": row["source_scan_refs"],
        "risk_flags": dict(row["risk_flags"]),
      }
    )

  risk_files = sorted(
    [stats for stats in py_stats if stats["risk_flags"]],
    key=lambda row: (row["risk_score"], row["loc"], row["max_test_item_span"]),
    reverse=True,
  )
  contract_groups: dict[str, dict[str, Any]] = defaultdict(
    lambda: {"files": 0, "smoke_files": 0, "loc": 0, "check_kinds": Counter()}
  )
  for stats in contract_stats:
    group = contract_groups[stats["group"]]
    group["files"] += 1
    group["loc"] += stats["loc"]
    group["smoke_files"] += int(bool(stats["in_contract_smoke"]))
    if stats["check_kind"]:
      group["check_kinds"].update([str(stats["check_kind"])])

  return {
    "schema_version": "test_system_audit.v1",
    "scope": {
      "root": str(root),
      "archive_paths_excluded": True,
      "pytest_smoke_suite": str(pytest_smoke_suite),
      "contract_smoke_suite": str(contract_smoke_suite),
    },
    "summary": {
      "active_files": len(active_files),
      "active_python_files": len(py_files),
      "active_test_py_files": sum(
        1 for path in py_files if Path(path).name.startswith("test_")
      ),
      "static_test_items": sum(stats["test_items"] for stats in py_stats),
      "pytest_smoke_entries": pytest_smoke_entries,
      "pytest_smoke_files": len(pytest_smoke_files),
      "contract_json_files": len(json_contracts),
      "contract_smoke_specs": len(contract_smoke_specs),
      "risk_file_count": len(risk_files),
      "hidden_mixin_test_files": sum(
        1 for stats in py_stats if stats["mixin_collected_tests"]
      ),
      "mixin_wrapper_files": sum(1 for stats in py_stats if stats["mixin_wrapper_file"]),
    },
    "directories": sorted(
      directory_rows,
      key=lambda row: (row["loc"], row["files"], row["directory"]),
      reverse=True,
    ),
    "top_risk_files": risk_files[:50],
    "contracts": {
      "groups": [
        {
          "group": group,
          "files": row["files"],
          "smoke_files": row["smoke_files"],
          "loc": row["loc"],
          "check_kinds": dict(row["check_kinds"]),
        }
        for group, row in sorted(
          contract_groups.items(),
          key=lambda item: (item[1]["files"], item[1]["loc"], item[0]),
          reverse=True,
        )
      ],
      "files": sorted(
        contract_stats,
        key=lambda row: (not row["in_contract_smoke"], row["group"], row["path"]),
      ),
    },
  }


def _format_markdown(audit: dict[str, Any], *, limit: int) -> str:
  summary = audit["summary"]
  lines = [
    "# Test System Audit",
    "",
    "## Scope",
    "",
    f"- Archive paths excluded: `{audit['scope']['archive_paths_excluded']}`",
    f"- Pytest smoke suite: `{audit['scope']['pytest_smoke_suite']}`",
    f"- Contract smoke suite: `{audit['scope']['contract_smoke_suite']}`",
    "",
    "## Summary",
    "",
    f"- Active test files: `{summary['active_files']}`",
    f"- Active Python files: `{summary['active_python_files']}`",
    f"- `test_*.py` files: `{summary['active_test_py_files']}`",
    f"- Static test items: `{summary['static_test_items']}`",
    f"- Pytest smoke entries/files: `{summary['pytest_smoke_entries']}` / `{summary['pytest_smoke_files']}`",
    f"- Contract JSON files/smoke specs: `{summary['contract_json_files']}` / `{summary['contract_smoke_specs']}`",
    f"- Risk-flagged Python files: `{summary['risk_file_count']}`",
    f"- Hidden mixin test files: `{summary['hidden_mixin_test_files']}`",
    f"- Mixin wrapper files: `{summary['mixin_wrapper_files']}`",
    "",
    "## Directory Load",
    "",
    "| Directory | Files | Python | LOC | Test Items | Asserts | Source-Scan Refs | Risk Flags |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
  ]
  for row in audit["directories"][:limit]:
    flags = ", ".join(f"{key}:{value}" for key, value in row["risk_flags"].items())
    lines.append(
      f"| `{row['directory']}` | {row['files']} | {row['python_files']} | "
      f"{row['loc']} | {row['test_items']} | {row['asserts']} | "
      f"{row['source_scan_refs']} | {flags or '-'} |"
    )
  lines.extend(
    [
      "",
      "## Top Risk Files",
      "",
      "| Score | Path | LOC | Items | Max Span | Asserts | Literals | Flags |",
      "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
  )
  for row in audit["top_risk_files"][:limit]:
    lines.append(
      f"| {row['risk_score']} | `{row['path']}` | {row['loc']} | "
      f"{row['test_items']} | {row['max_test_item_span']} | {row['asserts']} | "
      f"{row['literal_count']} | {', '.join(row['risk_flags'])} |"
    )
  lines.extend(
    [
      "",
      "## Contract Groups",
      "",
      "| Group | Files | Smoke | LOC | Check Kinds |",
      "| --- | ---: | ---: | ---: | --- |",
    ]
  )
  for row in audit["contracts"]["groups"][:limit]:
    kinds = ", ".join(f"{key}:{value}" for key, value in row["check_kinds"].items())
    lines.append(
      f"| `{row['group']}` | {row['files']} | {row['smoke_files']} | "
      f"{row['loc']} | {kinds or '-'} |"
    )
  lines.append("")
  return "\n".join(lines)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Audit active non-archive pytest and JSON contract test surfaces."
  )
  parser.add_argument(
    "--format",
    choices=("json", "markdown"),
    default="json",
    help="Output format.",
  )
  parser.add_argument(
    "--output",
    help="Optional output file. Defaults to stdout.",
  )
  parser.add_argument(
    "--limit",
    type=int,
    default=20,
    help="Rows to include in markdown tables.",
  )
  parser.add_argument(
    "--pytest-smoke-suite",
    default=str(DEFAULT_PYTEST_SMOKE_SUITE),
    help="Checked-in pytest smoke suite manifest.",
  )
  parser.add_argument(
    "--contract-smoke-suite",
    default=str(DEFAULT_CONTRACT_SMOKE_SUITE),
    help="Checked-in JSON contract smoke suite manifest.",
  )
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  audit = build_audit(
    pytest_smoke_suite=Path(str(args.pytest_smoke_suite)),
    contract_smoke_suite=Path(str(args.contract_smoke_suite)),
  )
  if args.format == "markdown":
    content = _format_markdown(audit, limit=max(1, int(args.limit)))
  else:
    content = json.dumps(audit, indent=2, sort_keys=True) + "\n"
  if args.output:
    _repo_path(args.output).write_text(content, encoding="utf-8")
  else:
    print(content, end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
