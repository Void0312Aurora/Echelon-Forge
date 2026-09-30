#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.runners import audit_test_system
from python.testing.suite_manifest import load_pytest_suite_manifest, pytest_entry_path


REPORT_AUTHORITY = "derived_non_authoritative"
SCHEMA_VERSION = "test_authority_audit.v1"
DEFAULT_MANIFESTS = (
  Path("tests/suites/architecture_guard_suite.json"),
  Path("tests/suites/governance_audit_suite.json"),
)
DEFAULT_RUNNER_MANIFESTS = (
  Path("tests/smoke/ci_smoke_suite.json"),
  Path("tests/smoke/ci_contract_suite.json"),
  *DEFAULT_MANIFESTS,
)
REQUIRED_METADATA = ("owner", "failure_audience", "execution_strategy")


class AuthorityAuditError(ValueError):
  """Raised when a derived report cannot be built from the maintained source."""


def _repo_relative(path: Path, root: Path) -> str:
  try:
    return path.resolve().relative_to(root.resolve()).as_posix()
  except ValueError as exc:
    raise AuthorityAuditError(f"path is outside repository root: {path}") from exc


def _load_json(path: Path) -> dict[str, Any]:
  try:
    payload = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError) as exc:
    raise AuthorityAuditError(f"cannot read suite manifest {path}: {exc}") from exc
  if not isinstance(payload, dict):
    raise AuthorityAuditError(f"suite manifest must contain an object: {path}")
  return payload


def _metadata(payload: dict[str, Any], path: Path) -> dict[str, str]:
  values: dict[str, str] = {}
  missing: list[str] = []
  for key in REQUIRED_METADATA:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
      missing.append(key)
    else:
      values[key] = value.strip()
  if missing:
    raise AuthorityAuditError(
      f"{path} must declare non-empty root metadata: {', '.join(missing)}"
    )
  return values


def _live_architecture_test_files(root: Path) -> set[str]:
  architecture_root = root / "tests" / "architecture"
  return {
    path.relative_to(root).as_posix()
    for path in architecture_root.rglob("test_*.py")
  }


def _manifest_rows(
  root: Path,
  manifest_paths: Sequence[Path],
  live_files: set[str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
  rows: list[dict[str, Any]] = []
  path_index: dict[str, dict[str, Any]] = {}

  for manifest_path in manifest_paths:
    resolved_manifest = manifest_path if manifest_path.is_absolute() else root / manifest_path
    payload = _load_json(resolved_manifest)
    metadata = _metadata(payload, resolved_manifest)
    raw_paths = payload.get("paths")
    if not isinstance(raw_paths, list) or not raw_paths:
      raise AuthorityAuditError(f"{resolved_manifest} must contain a non-empty paths list")

    try:
      manifest = load_pytest_suite_manifest(resolved_manifest, root)
    except (OSError, TypeError, ValueError) as exc:
      raise AuthorityAuditError(f"invalid pytest suite manifest {resolved_manifest}: {exc}") from exc

    seen_entries: set[str] = set()
    seen_paths: Counter[str] = Counter()
    relative_manifest = _repo_relative(resolved_manifest, root)
    suite_name = payload.get("name", manifest.name)
    if not isinstance(suite_name, str) or not suite_name.strip():
      raise AuthorityAuditError(f"{resolved_manifest} must declare a non-empty name")
    for entry in manifest.entries:
      if entry.raw in seen_entries:
        raise AuthorityAuditError(f"{resolved_manifest} lists duplicate entry: {entry.raw}")
      seen_entries.add(entry.raw)
      relpath = pytest_entry_path(entry.raw)
      if Path(relpath).is_absolute():
        raise AuthorityAuditError(
          f"{resolved_manifest} must use repository-relative entries: {entry.raw}"
        )
      relpath = Path(relpath).as_posix()
      if not relpath.startswith("tests/architecture/") or not relpath.endswith(".py"):
        raise AuthorityAuditError(
          f"{resolved_manifest} contains a non-architecture test entry: {entry.raw}"
        )
      if relpath not in live_files:
        raise AuthorityAuditError(
          f"{resolved_manifest} contains a stale architecture test entry: {entry.raw}"
        )
      seen_paths[relpath] += 1
      existing = path_index.get(relpath)
      if existing is not None and existing["manifest"] != relative_manifest:
        raise AuthorityAuditError(
          "architecture test is assigned to multiple tier manifests: "
          f"{relpath} ({existing['manifest']}, {relative_manifest})"
        )
      path_index[relpath] = {
        "path": relpath,
        "suite": suite_name.strip(),
        "manifest": relative_manifest,
        **metadata,
      }
      rows.append(
        {
          "path": relpath,
          "entry": entry.raw,
          "suite": suite_name.strip(),
          "manifest": relative_manifest,
          **metadata,
        }
      )

    duplicate_paths = sorted(path for path, count in seen_paths.items() if count > 1)
    if duplicate_paths:
      raise AuthorityAuditError(
        f"{resolved_manifest} assigns multiple entries to the same test file: {duplicate_paths}"
      )

  assigned = set(path_index)
  missing = sorted(live_files - assigned)
  if missing:
    raise AuthorityAuditError(
      "architecture test files are missing from tier manifests: " + ", ".join(missing)
    )
  stale = sorted(assigned - live_files)
  if stale:
    raise AuthorityAuditError(
      "tier manifests contain non-live architecture test files: " + ", ".join(stale)
    )
  return rows, path_index


def _pytest_smoke_files(root: Path) -> set[str]:
  smoke_path = root / "tests" / "smoke" / "ci_smoke_suite.json"
  if not smoke_path.exists():
    return set()
  try:
    manifest = load_pytest_suite_manifest(smoke_path, root, allow_empty=True)
  except (OSError, TypeError, ValueError):
    return set()
  return {pytest_entry_path(entry.raw) for entry in manifest.entries}


def _source_scan_row(stats: dict[str, Any]) -> dict[str, Any]:
  risk_flags = list(stats.get("risk_flags", []))
  return {
    "references": int(stats.get("source_scan_refs", 0)),
    "residual": "source_scan_guard" in risk_flags,
    "risk_flags": risk_flags,
  }


def _runner_manifest_rows(
  root: Path,
  manifest_paths: Sequence[Path],
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for manifest_path in manifest_paths:
    resolved = manifest_path if manifest_path.is_absolute() else root / manifest_path
    payload = _load_json(resolved)
    metadata = _metadata(payload, resolved)
    if isinstance(payload.get("paths"), list):
      entry_kind = "pytest"
      entry_count = len(payload["paths"])
    elif isinstance(payload.get("specs"), list):
      entry_kind = "contract"
      entry_count = len(payload["specs"])
    else:
      raise AuthorityAuditError(
        f"{resolved} must contain a non-empty paths or specs list"
      )
    if entry_count == 0:
      raise AuthorityAuditError(f"{resolved} must contain a non-empty execution list")
    name = payload.get("name", resolved.stem)
    if not isinstance(name, str) or not name.strip():
      raise AuthorityAuditError(f"{resolved} must declare a non-empty name")
    rows.append(
      {
        "name": name.strip(),
        "manifest": _repo_relative(resolved, root),
        "kind": entry_kind,
        "entry_count": entry_count,
        **metadata,
      }
    )
  return sorted(rows, key=lambda row: row["manifest"])


def build_inventory(
  *,
  root: Path = REPO_ROOT,
  manifest_paths: Sequence[Path] | None = None,
  live_test_files: Iterable[str] | None = None,
) -> dict[str, Any]:
  root = root.resolve()
  manifests = tuple(manifest_paths or DEFAULT_MANIFESTS)
  runner_manifests = _runner_manifest_rows(
    root,
    tuple(manifest_paths) if manifest_paths is not None else DEFAULT_RUNNER_MANIFESTS,
  )
  live_files = {
    Path(path).as_posix()
    for path in (live_test_files if live_test_files is not None else _live_architecture_test_files(root))
  }
  rows, _ = _manifest_rows(root, manifests, live_files)
  smoke_files = _pytest_smoke_files(root)

  report_rows: list[dict[str, Any]] = []
  for row in rows:
    stats = audit_test_system.analyze_python_test_file(
      root,
      row["path"],
      pytest_smoke_files=smoke_files,
    )
    report_rows.append(
      {
        **row,
        "in_pytest_smoke": bool(stats["in_pytest_smoke"]),
        "test_items": int(stats["test_items"]),
        "source_scan": _source_scan_row(stats),
      }
    )

  report_rows.sort(key=lambda row: row["path"])
  suite_rows = []
  for manifest_path in manifests:
    resolved = manifest_path if manifest_path.is_absolute() else root / manifest_path
    payload = _load_json(resolved)
    metadata = _metadata(payload, resolved)
    suite_rows.append(
      {
        "name": str(payload.get("name", resolved.stem)),
        "manifest": _repo_relative(resolved, root),
        **metadata,
        "file_count": sum(
          1 for row in report_rows if row["manifest"] == _repo_relative(resolved, root)
        ),
      }
    )
  suite_rows.sort(key=lambda row: row["manifest"])

  owner_counts = Counter(row["owner"] for row in report_rows)
  strategy_counts = Counter(row["execution_strategy"] for row in report_rows)
  source_scan_reference_files = sum(
    1 for row in report_rows if row["source_scan"]["references"] > 0
  )
  source_scan_residual_files = sum(
    1 for row in report_rows if row["source_scan"]["residual"]
  )
  return {
    "schema_version": SCHEMA_VERSION,
    "report_authority": REPORT_AUTHORITY,
    "source_of_truth": [row["manifest"] for row in suite_rows],
    "runner_manifests": runner_manifests,
    "scope": {
      "root": str(root),
      "architecture_test_files_only": True,
      "archive_policy_changed": False,
      "archive_paths_excluded": False,
    },
    "summary": {
      "architecture_test_files": len(report_rows),
      "manifest_entries": len(rows),
      "suite_count": len(suite_rows),
      "runner_manifest_count": len(runner_manifests),
      "owner_count": len(owner_counts),
      "execution_strategy_count": len(strategy_counts),
      "source_scan_reference_files": source_scan_reference_files,
      "source_scan_residual_files": source_scan_residual_files,
      "smoke_selected_files": sum(1 for row in report_rows if row["in_pytest_smoke"]),
    },
    "suites": suite_rows,
    "tests": report_rows,
  }


def _escape(value: object) -> str:
  return str(value).replace("|", "\\|").replace("\n", " ")


def format_markdown(report: dict[str, Any], *, limit: int = 200) -> str:
  summary = report["summary"]
  lines = [
    "# Test Authority Audit",
    "",
    f"- Report authority: `{report['report_authority']}`",
    f"- Source of truth: {', '.join(f'`{path}`' for path in report['source_of_truth'])}",
    "- This report is derived from the maintained manifests; it is not a second registry.",
    "",
    "## Summary",
    "",
    f"- Architecture test files: `{summary['architecture_test_files']}`",
    f"- Manifest entries: `{summary['manifest_entries']}`",
    f"- Runner manifests with owner/lane metadata: `{summary['runner_manifest_count']}`",
    f"- Owners / execution strategies: `{summary['owner_count']}` / `{summary['execution_strategy_count']}`",
    f"- Files with source-scan references: `{summary['source_scan_reference_files']}`",
    f"- Files retaining a source-scan residual flag: `{summary['source_scan_residual_files']}`",
    f"- Files selected by the pytest smoke manifest: `{summary['smoke_selected_files']}`",
    "- Archive policy changed by this audit: `False`",
    "",
    "## Suites",
    "",
    "| Suite | Manifest | Owner | Failure audience | Execution strategy | Files |",
    "| --- | --- | --- | --- | --- | ---: |",
  ]
  for suite in report["suites"]:
    lines.append(
      "| " + " | ".join(
        [
          _escape(suite["name"]),
          f"`{suite['manifest']}`",
          _escape(suite["owner"]),
          _escape(suite["failure_audience"]),
          _escape(suite["execution_strategy"]),
          str(suite["file_count"]),
        ]
      ) + " |"
    )
  lines.extend(
    [
      "",
      "## Runner Manifests",
      "",
      "| Name | Manifest | Kind | Owner | Failure audience | Execution strategy | Entries |",
      "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
  )
  for manifest in report["runner_manifests"]:
    lines.append(
      "| " + " | ".join(
        [
          _escape(manifest["name"]),
          f"`{manifest['manifest']}`",
          manifest["kind"],
          _escape(manifest["owner"]),
          _escape(manifest["failure_audience"]),
          _escape(manifest["execution_strategy"]),
          str(manifest["entry_count"]),
        ]
      ) + " |"
    )
  lines.extend(
    [
      "",
      "## Test Assignment",
      "",
      "| Path | Suite | Owner | Execution strategy | Source-scan refs | Residual | Smoke |",
      "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
  )
  for row in report["tests"][: max(1, limit)]:
    lines.append(
      "| " + " | ".join(
        [
          f"`{row['path']}`",
          _escape(row["suite"]),
          _escape(row["owner"]),
          _escape(row["execution_strategy"]),
          str(row["source_scan"]["references"]),
          "yes" if row["source_scan"]["residual"] else "no",
          "yes" if row["in_pytest_smoke"] else "no",
        ]
      ) + " |"
    )
  lines.append("")
  return "\n".join(lines)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Derive a non-authoritative ownership and execution audit from architecture tier manifests."
  )
  parser.add_argument("--format", choices=("json", "markdown"), default="json")
  parser.add_argument("--output", help="Optional output file; defaults to stdout.")
  parser.add_argument("--limit", type=int, default=200)
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  report = build_inventory()
  content = (
    format_markdown(report, limit=max(1, int(args.limit)))
    if args.format == "markdown"
    else json.dumps(report, indent=2, sort_keys=True) + "\n"
  )
  if args.output:
    output = Path(args.output)
    if not output.is_absolute():
      output = REPO_ROOT / output
    output.write_text(content, encoding="utf-8")
  else:
    print(content, end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
