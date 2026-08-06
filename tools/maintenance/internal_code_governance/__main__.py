"""Command-line entry point for incremental internal-code governance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import AuditResult, audit_changed_lines, audit_paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Audit new source and documentation lines for opaque internal codes.",
  )
  parser.add_argument("--repo-root", default=".", help="Repository root to audit.")
  scope = parser.add_mutually_exclusive_group(required=True)
  scope.add_argument(
    "--changed-from",
    metavar="GIT_REF",
    help="Audit only lines added relative to a Git base revision.",
  )
  scope.add_argument(
    "--paths",
    nargs="+",
    help="Audit complete repository-relative files.",
  )
  parser.add_argument("--format", choices=("text", "json"), default="text")
  parser.add_argument(
    "--fail-on",
    choices=("error", "warning", "never"),
    default="error",
    help="Select the minimum finding severity that produces a non-zero exit.",
  )
  return parser.parse_args(argv)


def _print_text(result: AuditResult) -> None:
  for finding in result.findings:
    print(
      f"{finding.path}:{finding.line}: {finding.severity}: "
      f"{finding.code}: {finding.token} ({finding.message})"
    )
  print(f"files_checked: {result.files_checked}")
  print(f"lines_checked: {result.lines_checked}")
  print(f"errors: {len(result.errors)}")
  print(f"warnings: {len(result.warnings)}")


def exit_code(result: AuditResult, fail_on: str) -> int:
  if fail_on == "never":
    return 0
  if fail_on == "warning":
    return 1 if result.findings else 0
  return 1 if result.errors else 0


def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  repo_root = Path(args.repo_root)
  if args.changed_from:
    result = audit_changed_lines(repo_root, args.changed_from)
  else:
    result = audit_paths(repo_root, args.paths)
  if args.format == "json":
    print(result.to_json())
  else:
    _print_text(result)
  return exit_code(result, args.fail_on)


if __name__ == "__main__":
  sys.exit(main())
