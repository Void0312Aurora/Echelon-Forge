#!/usr/bin/env python3
"""Audit git worktree hygiene: placement, reachability, and untracked residue.

The audit is read-only: it never creates, moves, prunes, or repairs a worktree.
Findings map to the repair procedures in
`docs/engineering/workspace/worktree_and_path_policy.md`.

A worktree whose directory is owned by another principal (the usual outcome of
creating it from an elevated shell on Windows) makes plain `git status` fail
with `detected dubious ownership`. That failure is the finding this audit is
built to surface, so every status probe falls back to a
`git -c safe.directory=*` retry: the fallback keeps the audit itself running
against a broken tree instead of crashing, while the first probe records what an
ordinary session actually sees.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_SUBDIRECTORY = ".worktrees"
GIT_TIMEOUT_SECONDS = 120


class WorktreeAuditError(RuntimeError):
  """Raised when the worktree inventory itself cannot be read."""


@dataclass(frozen=True)
class WorktreeEntry:
  path: str
  head: str = ""
  branch: str = ""
  bare: bool = False
  detached: bool = False
  locked: bool = False
  prunable: bool = False


@dataclass(frozen=True)
class StatusProbe:
  reachable: bool
  untracked: int = 0
  error: str = ""
  needed_ownership_override: bool = False


@dataclass(frozen=True)
class Finding:
  code: str
  worktree: str
  message: str
  detail: str = ""


@dataclass(frozen=True)
class WorktreeReport:
  path: str
  branch: str
  inside_policy_root: bool
  status_reachable: bool
  needed_ownership_override: bool
  untracked: int


@dataclass(frozen=True)
class AuditResult:
  main_worktree: str
  policy_root: str
  worktrees_checked: int
  worktrees: list[WorktreeReport]
  findings: list[Finding]


def _normalize(path: str) -> str:
  return os.path.normcase(os.path.normpath(os.path.abspath(str(path))))


def _is_within(child: str, parent: str) -> bool:
  try:
    return os.path.commonpath([child, parent]) == parent
  except ValueError:  # Different drives on Windows.
    return False


def parse_worktree_list(text: str) -> list[WorktreeEntry]:
  """Parse `git worktree list --porcelain` output into entries."""
  entries: list[WorktreeEntry] = []
  current: dict[str, object] = {}

  def flush() -> None:
    if current.get("path"):
      entries.append(WorktreeEntry(**current))  # type: ignore[arg-type]
    current.clear()

  for raw_line in text.splitlines():
    line = raw_line.strip()
    if not line:
      flush()
      continue
    key, _, value = line.partition(" ")
    if key == "worktree":
      flush()
      current["path"] = value
    elif key == "HEAD":
      current["head"] = value
    elif key == "branch":
      current["branch"] = value
    elif key in {"bare", "detached", "locked", "prunable"}:
      current[key] = True
  flush()
  return entries


def _run_git(args: Sequence[str], *, timeout: int) -> subprocess.CompletedProcess[str] | None:
  try:
    return subprocess.run(
      ["git", *args],
      capture_output=True,
      text=True,
      encoding="utf-8",
      errors="replace",
      timeout=timeout,
      check=False,
    )
  except (OSError, subprocess.SubprocessError):
    return None


def _first_error_line(process: subprocess.CompletedProcess[str] | None) -> str:
  if process is None:
    return "git could not be invoked"
  for line in (process.stderr or "").splitlines():
    if line.strip():
      return line.strip()
  return "git exited non-zero without a message"


def count_untracked(status_output: str) -> int:
  return sum(1 for line in status_output.splitlines() if line.startswith("?? "))


def probe_worktree_status(path: str, *, timeout: int = GIT_TIMEOUT_SECONDS) -> StatusProbe:
  """Report whether `git status` works in `path`, and how much residue it holds."""
  if not os.path.isdir(path):
    return StatusProbe(reachable=False, error="worktree path is missing on disk")

  plain = _run_git(["-C", path, "status", "--porcelain"], timeout=timeout)
  if plain is not None and plain.returncode == 0:
    return StatusProbe(reachable=True, untracked=count_untracked(plain.stdout))

  error = _first_error_line(plain)
  override = _run_git(
    ["-c", "safe.directory=*", "-C", path, "status", "--porcelain"],
    timeout=timeout,
  )
  if override is not None and override.returncode == 0:
    return StatusProbe(
      reachable=False,
      untracked=count_untracked(override.stdout),
      error=error,
      needed_ownership_override=True,
    )
  return StatusProbe(reachable=False, error=error)


def list_repository_worktrees(repo_root: Path, *, timeout: int = GIT_TIMEOUT_SECONDS) -> list[WorktreeEntry]:
  process = _run_git(["-C", str(repo_root), "worktree", "list", "--porcelain"], timeout=timeout)
  if process is not None and process.returncode == 0:
    return parse_worktree_list(process.stdout)

  # An ownership-blocked entry point must not abort the whole audit: retry
  # with the restricted override so the inventory itself still loads, and
  # leave the per-worktree status probes to report the ownership findings.
  error = _first_error_line(process)
  override = _run_git(
    ["-c", "safe.directory=*", "-C", str(repo_root), "worktree", "list", "--porcelain"],
    timeout=timeout,
  )
  if override is not None and override.returncode == 0:
    return parse_worktree_list(override.stdout)
  raise WorktreeAuditError(f"cannot list worktrees from {repo_root}: {error}")


def is_inside_policy_root(path: str, main_root: str, allowed_paths: Sequence[str] = ()) -> bool:
  target = _normalize(path)
  if target == _normalize(main_root):
    return True
  if any(target == _normalize(allowed) for allowed in allowed_paths):
    return True
  return _is_within(target, _normalize(os.path.join(str(main_root), POLICY_SUBDIRECTORY)))


def build_audit(
  entries: Sequence[WorktreeEntry],
  *,
  main_root: str,
  allowed_paths: Sequence[str] = (),
  max_untracked: int = 0,
  probe: Callable[[str], StatusProbe] | None = None,
) -> AuditResult:
  """Classify an already-collected worktree inventory.

  `probe` is injected so callers can classify without touching a real
  repository; the default probe shells out to git.
  """
  run_probe = probe or probe_worktree_status
  findings: list[Finding] = []
  reports: list[WorktreeReport] = []
  policy_root = os.path.join(str(main_root), POLICY_SUBDIRECTORY)

  for entry in entries:
    inside = is_inside_policy_root(entry.path, main_root, allowed_paths)
    if not inside:
      findings.append(
        Finding(
          code="worktree-outside-policy-root",
          worktree=entry.path,
          message="worktree lives outside the main repository root and its .worktrees/ directory",
          detail=f"expected the main root or a child of {Path(policy_root).as_posix()}",
        )
      )

    status = run_probe(entry.path)
    if not status.reachable:
      findings.append(
        Finding(
          code="worktree-status-unavailable",
          worktree=entry.path,
          message="git status does not run in this worktree for the current user",
          detail=status.error,
        )
      )
    if status.untracked > max_untracked:
      findings.append(
        Finding(
          code="worktree-untracked-residue",
          worktree=entry.path,
          message="worktree carries untracked files that are neither committed nor ignored",
          detail=f"{status.untracked} untracked entries (budget {max_untracked})",
        )
      )

    reports.append(
      WorktreeReport(
        path=entry.path,
        branch=entry.branch,
        inside_policy_root=inside,
        status_reachable=status.reachable,
        needed_ownership_override=status.needed_ownership_override,
        untracked=status.untracked,
      )
    )

  return AuditResult(
    main_worktree=str(main_root),
    policy_root=Path(policy_root).as_posix(),
    worktrees_checked=len(entries),
    worktrees=reports,
    findings=findings,
  )


def audit_repository(
  repo_root: Path,
  *,
  allowed_paths: Sequence[str] = (),
  max_untracked: int = 0,
  probe: Callable[[str], StatusProbe] | None = None,
  list_worktrees: Callable[[Path], list[WorktreeEntry]] | None = None,
) -> AuditResult:
  entries = (list_worktrees or list_repository_worktrees)(repo_root)
  if not entries:
    raise WorktreeAuditError(f"git reported no worktrees for {repo_root}")
  # git lists the main worktree first, including when invoked from a linked one.
  main_root = entries[0].path
  return build_audit(
    entries,
    main_root=main_root,
    allowed_paths=allowed_paths,
    max_untracked=max_untracked,
    probe=probe,
  )


def format_text_report(result: AuditResult) -> str:
  lines = [f"main worktree: {result.main_worktree}", f"policy root: {result.policy_root}", ""]
  for report in result.worktrees:
    flags = []
    if not report.inside_policy_root:
      flags.append("outside-policy-root")
    if not report.status_reachable:
      flags.append("status-unavailable")
    if report.needed_ownership_override:
      flags.append("needed-safe-directory-override")
    marker = "FAIL" if flags else "ok  "
    branch = report.branch or "(detached)"
    lines.append(f"{marker} {report.path}")
    lines.append(f"       branch={branch} untracked={report.untracked} {' '.join(flags)}".rstrip())
  lines.append("")
  for finding in result.findings:
    lines.append(f"{finding.code}: {finding.worktree}")
    lines.append(f"  {finding.message}")
    if finding.detail:
      lines.append(f"  detail: {finding.detail}")
  lines.append("")
  lines.append(f"worktrees_checked: {result.worktrees_checked}")
  lines.append(f"findings: {len(result.findings)}")
  return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Audit git worktree placement, reachability, and untracked residue.",
  )
  parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository or worktree to audit from.")
  parser.add_argument(
    "--allow-path",
    action="append",
    default=[],
    metavar="PATH",
    help="Worktree path exempt from the placement rule; repeatable, empty by default.",
  )
  parser.add_argument(
    "--max-untracked",
    type=int,
    default=0,
    help="Untracked entries tolerated per worktree before a finding is raised.",
  )
  parser.add_argument("--format", choices=("text", "json"), default="text")
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  try:
    result = audit_repository(
      Path(args.repo_root),
      allowed_paths=args.allow_path,
      max_untracked=args.max_untracked,
    )
  except WorktreeAuditError as error:
    print(f"worktree audit failed: {error}", file=sys.stderr)
    return 2

  if args.format == "json":
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
  else:
    print(format_text_report(result))
  return 1 if result.findings else 0


if __name__ == "__main__":
  sys.exit(main())
