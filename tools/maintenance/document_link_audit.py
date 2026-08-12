#!/usr/bin/env python3
"""Validate repository-local links on the maintained documentation surface."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

try:
  from tools.maintenance.document_scope import filter_paths, is_english_work_doc
except ModuleNotFoundError:  # Direct script execution from tools/maintenance.
  from document_scope import filter_paths, is_english_work_doc


REPO_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
FENCED_CODE_RE = re.compile(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_ABSOLUTE_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


@dataclass(frozen=True)
class LinkIssue:
  code: str
  source: str
  line: int
  target: str
  message: str


@dataclass(frozen=True)
class AuditResult:
  documents_checked: int
  links_checked: int
  issues: list[LinkIssue]


def _blank_preserving_lines(match: re.Match[str]) -> str:
  return re.sub(r"[^\n]", " ", match.group(0))


def mask_non_prose(text: str) -> str:
  masked = FENCED_CODE_RE.sub(_blank_preserving_lines, text)
  masked = HTML_COMMENT_RE.sub(_blank_preserving_lines, masked)
  return INLINE_CODE_RE.sub(_blank_preserving_lines, masked)


def extract_link_target(raw_target: str) -> str:
  value = raw_target.strip()
  if value.startswith("<"):
    end = value.find(">", 1)
    return value[1:end] if end >= 0 else value[1:]
  return value.split(maxsplit=1)[0] if value else ""


def is_external_or_anchor(target: str) -> bool:
  lowered = target.lower()
  if not target or target.startswith("#") or target.startswith("//"):
    return True
  if WINDOWS_ABSOLUTE_RE.match(target):
    return False
  return bool(URI_SCHEME_RE.match(lowered))


def select_documents(repo_root: Path, *, full_tree: bool = False) -> list[Path]:
  repo_root = repo_root.resolve()
  docs_root = repo_root / "docs"
  selected = [
    path
    for path in (repo_root / "README.md", repo_root / "README.zh.md")
    if path.is_file()
  ]
  if docs_root.is_dir():
    markdown = [path for path in docs_root.rglob("*.md") if path.is_file()]
    selected.extend(
      filter_paths(
        markdown,
        include_local_only=False,
        root=docs_root,
        strict_bilingual_only=not full_tree,
      )
    )
    if not full_tree:
      # The link-audit scope is wider than the bilingual scope: maintained
      # English work-layer documents stay link-audited by default even though
      # they carry no bilingual SLA.
      selected.extend(
        path
        for path in filter_paths(markdown, include_local_only=False)
        if is_english_work_doc(path, docs_root)
      )
  return sorted(set(selected))


def audit_document(repo_root: Path, source: Path) -> tuple[int, list[LinkIssue]]:
  repo_root = repo_root.resolve()
  source = source.resolve()
  text = source.read_text(encoding="utf-8", errors="ignore")
  masked = mask_non_prose(text)
  issues: list[LinkIssue] = []
  links_checked = 0

  for match in MARKDOWN_LINK_RE.finditer(masked):
    raw_target = match.group(1).strip()
    target = extract_link_target(raw_target)
    if is_external_or_anchor(target):
      continue
    links_checked += 1
    line = masked.count("\n", 0, match.start()) + 1
    source_name = source.relative_to(repo_root).as_posix()

    if target.startswith("/") or WINDOWS_ABSOLUTE_RE.match(target):
      issues.append(
        LinkIssue(
          code="machine-absolute-path",
          source=source_name,
          line=line,
          target=raw_target,
          message="repository links must be relative, not machine-absolute",
        )
      )
      continue

    path_target = unquote(target.split("#", 1)[0].split("?", 1)[0]).strip()
    if not path_target:
      continue
    resolved = (source.parent / path_target).resolve()
    try:
      resolved.relative_to(repo_root)
    except ValueError:
      issues.append(
        LinkIssue(
          code="path-escapes-repository",
          source=source_name,
          line=line,
          target=raw_target,
          message="repository-local link resolves outside the repository",
        )
      )
      continue
    docs_root = (repo_root / "docs").resolve()
    if resolved.is_dir():
      try:
        resolved.relative_to(docs_root)
      except ValueError:
        pass
      else:
        issues.append(
          LinkIssue(
            code="documentation-directory-target",
            source=source_name,
            line=line,
            target=raw_target,
            message="documentation directory links must target an explicit README",
          )
        )
        continue
    if not resolved.exists():
      issues.append(
        LinkIssue(
          code="missing-target",
          source=source_name,
          line=line,
          target=raw_target,
          message="repository-local link target does not exist",
        )
      )

  return links_checked, issues


def audit_repository(repo_root: Path, *, full_tree: bool = False) -> AuditResult:
  repo_root = repo_root.resolve()
  documents = select_documents(repo_root, full_tree=full_tree)
  links_checked = 0
  issues: list[LinkIssue] = []
  for source in documents:
    document_links, document_issues = audit_document(repo_root, source)
    links_checked += document_links
    issues.extend(document_issues)
  return AuditResult(
    documents_checked=len(documents),
    links_checked=links_checked,
    issues=sorted(issues, key=lambda issue: (issue.source, issue.line, issue.target)),
  )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Audit repository-local links on maintained Markdown documents.",
  )
  parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root to audit.")
  parser.add_argument(
    "--full-tree",
    action="store_true",
    help="Audit all shared docs outside archive/local-only source directories.",
  )
  parser.add_argument("--format", choices=("text", "json"), default="text")
  return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  result = audit_repository(Path(args.repo_root), full_tree=args.full_tree)
  if args.format == "json":
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
  else:
    for issue in result.issues:
      print(f"{issue.source}:{issue.line}: {issue.code}: {issue.target} ({issue.message})")
    print(f"documents_checked: {result.documents_checked}")
    print(f"links_checked: {result.links_checked}")
    print(f"issues: {len(result.issues)}")
  return 1 if result.issues else 0


if __name__ == "__main__":
  sys.exit(main())
