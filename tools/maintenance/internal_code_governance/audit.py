"""Audit added or selected lines for opaque repository-internal codes."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .policy import (
  COMPATIBILITY_MARKER,
  PHASE_IDENTIFIER_RE,
  PHASE_PROSE_RE,
  POLICY_DOCUMENTS,
  SOURCE_SUFFIXES,
  STRING_LITERAL_RE,
  TRACKING_CODE_RE,
  is_document,
  is_production_source,
  normalize_path,
)


@dataclass(frozen=True)
class Finding:
  code: str
  severity: str
  path: str
  line: int
  token: str
  message: str


@dataclass(frozen=True)
class AuditResult:
  files_checked: int
  lines_checked: int
  findings: tuple[Finding, ...]

  @property
  def errors(self) -> tuple[Finding, ...]:
    return tuple(finding for finding in self.findings if finding.severity == "error")

  @property
  def warnings(self) -> tuple[Finding, ...]:
    return tuple(finding for finding in self.findings if finding.severity == "warning")

  def to_json(self) -> str:
    payload = {
      "files_checked": self.files_checked,
      "lines_checked": self.lines_checked,
      "errors": len(self.errors),
      "warnings": len(self.warnings),
      "findings": [asdict(finding) for finding in self.findings],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _inside_string_literal(line: str, offset: int) -> bool:
  return any(match.start() <= offset < match.end() for match in STRING_LITERAL_RE.finditer(line))


def _comment_offset(path: str, line: str) -> int | None:
  suffix = Path(path).suffix.lower()
  markers = ("#",) if suffix == ".py" else ("//",)
  positions: list[int] = []
  for marker in markers:
    start = 0
    while True:
      offset = line.find(marker, start)
      if offset < 0:
        break
      if not _inside_string_literal(line, offset):
        positions.append(offset)
      start = offset + len(marker)
  return min(positions) if positions else None


def _inside_comment(path: str, line: str, offset: int) -> bool:
  comment_offset = _comment_offset(path, line)
  return comment_offset is not None and comment_offset <= offset


def _has_compatibility_marker(lines: list[str], index: int) -> bool:
  current = lines[index].lower()
  previous = lines[index - 1].lower() if index else ""
  return COMPATIBILITY_MARKER in current or COMPATIBILITY_MARKER in previous


def _is_document_definition(line: str, match: re.Match[str]) -> bool:
  tail = line[match.end():].strip()
  if re.match(r"^(?::|：|=|—|–|->|→)\s*\S", tail):
    return True
  if tail.startswith("|") and tail.strip("| "):
    return True
  lowered = line.lower()
  return any(
    marker in lowered
    for marker in (
      " means ",
      " stands for ",
      " defined as ",
      "表示",
      "是指",
      "定义为",
      "即：",
      "即 ",
    )
  )


def _source_findings(path: str, lines: list[str], index: int) -> list[Finding]:
  line = lines[index]
  line_number = index + 1
  compatibility = _has_compatibility_marker(lines, index)
  findings: list[Finding] = []

  for match in TRACKING_CODE_RE.finditer(line):
    if compatibility:
      continue
    if _inside_comment(path, line, match.start()):
      severity = "warning"
      code = "source-tracking-code-comment"
      message = "source comments should explain behavior without work-tracking codes"
    elif _inside_string_literal(line, match.start()):
      severity = "error"
      code = "runtime-tracking-code"
      message = "runtime or diagnostic strings must use semantic capability names"
    else:
      severity = "error"
      code = "source-tracking-code"
      message = "production identifiers must not encode work packages or iterations"
    findings.append(
      Finding(code, severity, path, line_number, match.group(0), message)
    )

  for match in PHASE_IDENTIFIER_RE.finditer(line):
    if compatibility:
      continue
    in_comment = _inside_comment(path, line, match.start())
    findings.append(
      Finding(
        "opaque-phase-comment" if in_comment else "opaque-phase-identifier",
        "warning" if in_comment else "error",
        path,
        line_number,
        match.group(0),
        (
          "source comments should lead with the semantic stage name"
          if in_comment
          else "implementation identifiers must lead with a semantic stage name"
        ),
      )
    )
  for match in PHASE_PROSE_RE.finditer(line):
    if compatibility:
      continue
    in_comment = _inside_comment(path, line, match.start())
    in_string = _inside_string_literal(line, match.start())
    if in_comment:
      code = "opaque-phase-comment"
      severity = "warning"
      message = "source comments should lead with the semantic stage name"
    elif in_string:
      code = "opaque-phase-runtime-string"
      severity = "error"
      message = "runtime or diagnostic strings must use semantic stage names"
    else:
      code = "opaque-phase-label"
      severity = "error"
      message = "production source must not introduce an unexplained lettered stage"
    findings.append(
      Finding(code, severity, path, line_number, match.group(0), message)
    )
  return findings


def _document_findings(path: str, line: str, line_number: int) -> list[Finding]:
  if path in POLICY_DOCUMENTS:
    return []
  findings: list[Finding] = []
  matches = list(TRACKING_CODE_RE.finditer(line)) + list(PHASE_PROSE_RE.finditer(line))
  for match in matches:
    if _is_document_definition(line, match):
      continue
    findings.append(
      Finding(
        "document-bare-internal-code",
        "warning",
        path,
        line_number,
        match.group(0),
        "maintained prose should expand an internal code at its first local use",
      )
    )
  return findings


def scan_text(
  path: str,
  text: str,
  *,
  line_numbers: set[int] | None = None,
) -> AuditResult:
  normalized = normalize_path(path)
  if not is_production_source(normalized) and not is_document(normalized):
    return AuditResult(files_checked=0, lines_checked=0, findings=())
  lines = text.splitlines()
  requested = set(range(1, len(lines) + 1)) if line_numbers is None else line_numbers
  selected = {number for number in requested if 1 <= number <= len(lines)}
  findings: list[Finding] = []
  for line_number in sorted(selected):
    index = line_number - 1
    if is_production_source(normalized):
      findings.extend(_source_findings(normalized, lines, index))
    elif is_document(normalized):
      findings.extend(_document_findings(normalized, lines[index], line_number))
  return AuditResult(
    files_checked=1,
    lines_checked=len(selected),
    findings=tuple(findings),
  )


def scan_path_name(path: str) -> tuple[Finding, ...]:
  normalized = normalize_path(path)
  if not is_production_source(normalized):
    return ()
  match = PHASE_IDENTIFIER_RE.search(Path(normalized).stem)
  if match is None:
    return ()
  return (
    Finding(
      "opaque-phase-path",
      "error",
      normalized,
      0,
      match.group(0),
      "new production paths must lead with a semantic stage name",
    ),
  )


def _combine(results: Iterable[AuditResult]) -> AuditResult:
  materialized = list(results)
  findings = sorted(
    (finding for result in materialized for finding in result.findings),
    key=lambda finding: (finding.path, finding.line, finding.code, finding.token),
  )
  return AuditResult(
    files_checked=sum(result.files_checked for result in materialized),
    lines_checked=sum(result.lines_checked for result in materialized),
    findings=tuple(findings),
  )


def audit_paths(repo_root: Path, paths: Iterable[str]) -> AuditResult:
  repo_root = repo_root.resolve()
  results: list[AuditResult] = []
  path_findings: list[Finding] = []
  for raw_path in sorted(set(paths)):
    path = (repo_root / raw_path).resolve()
    try:
      relative = path.relative_to(repo_root).as_posix()
    except ValueError as error:
      raise ValueError(f"path is outside repository: {raw_path}") from error
    if not path.is_file():
      continue
    if Path(relative).suffix.lower() not in SOURCE_SUFFIXES and not is_document(relative):
      continue
    result = scan_text(relative, path.read_text(encoding="utf-8", errors="ignore"))
    if result.files_checked:
      results.append(result)
      path_findings.extend(scan_path_name(relative))
  combined = _combine(results)
  return AuditResult(
    files_checked=combined.files_checked,
    lines_checked=combined.lines_checked,
    findings=tuple(sorted(
      (*combined.findings, *path_findings),
      key=lambda finding: (finding.path, finding.line, finding.code, finding.token),
    )),
  )


def parse_added_line_numbers(diff: str) -> dict[str, set[int]]:
  added: dict[str, set[int]] = {}
  current_path: str | None = None
  next_line: int | None = None
  for line in diff.splitlines():
    if line.startswith("+++ b/"):
      current_path = normalize_path(line[6:])
      added.setdefault(current_path, set())
      next_line = None
      continue
    if line.startswith("@@ "):
      match = re.search(r"\+(\d+)(?:,(\d+))?", line)
      next_line = int(match.group(1)) if match else None
      continue
    if current_path is None or next_line is None:
      continue
    if line.startswith("+") and not line.startswith("+++"):
      added[current_path].add(next_line)
      next_line += 1
    elif line.startswith("-") and not line.startswith("---"):
      continue
    elif line.startswith(" "):
      next_line += 1
  return {path: numbers for path, numbers in added.items() if numbers}


def _git_text(repo_root: Path, arguments: list[str]) -> str:
  completed = subprocess.run(
    ["git", "-c", "core.quotePath=false", *arguments],
    cwd=repo_root,
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
  )
  return completed.stdout


def _untracked_paths(repo_root: Path) -> set[str]:
  output = _git_text(
    repo_root,
    ["ls-files", "--others", "--exclude-standard", "-z"],
  )
  return {normalize_path(path) for path in output.split("\0") if path}


def parse_added_or_renamed_paths(name_status: str) -> set[str]:
  tokens = name_status.split("\0")
  paths: set[str] = set()
  index = 0
  while index < len(tokens) and tokens[index]:
    status = tokens[index]
    index += 1
    if status.startswith("R"):
      if index + 1 >= len(tokens):
        break
      index += 1
      paths.add(normalize_path(tokens[index]))
      index += 1
    else:
      if index >= len(tokens):
        break
      paths.add(normalize_path(tokens[index]))
      index += 1
  return paths


def _added_or_renamed_paths(repo_root: Path, base_ref: str) -> set[str]:
  output = _git_text(
    repo_root,
    ["diff", "--name-status", "-z", "--diff-filter=AR", base_ref, "--"],
  )
  return parse_added_or_renamed_paths(output)


def audit_changed_lines(repo_root: Path, base_ref: str) -> AuditResult:
  repo_root = repo_root.resolve()
  diff = _git_text(repo_root, [
    "diff",
    "--unified=0",
    "--no-ext-diff",
    "--no-color",
    "--diff-filter=ACMR",
    base_ref,
    "--",
  ])
  changed = parse_added_line_numbers(diff)
  untracked = _untracked_paths(repo_root)
  new_paths = _added_or_renamed_paths(repo_root, base_ref) | untracked
  for relative in untracked:
    path = repo_root / relative
    if path.is_file():
      line_count = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
      changed[relative] = set(range(1, line_count + 1))
  results: list[AuditResult] = []
  path_findings: list[Finding] = []
  for relative in sorted(set(changed) | new_paths):
    path = repo_root / relative
    if not path.is_file():
      continue
    result = scan_text(
      relative,
      path.read_text(encoding="utf-8", errors="ignore"),
      line_numbers=changed.get(relative, set()),
    )
    if result.files_checked:
      results.append(result)
    if relative in new_paths:
      path_findings.extend(scan_path_name(relative))
  combined = _combine(results)
  return AuditResult(
    files_checked=combined.files_checked,
    lines_checked=combined.lines_checked,
    findings=tuple(sorted(
      (*combined.findings, *path_findings),
      key=lambda finding: (finding.path, finding.line, finding.code, finding.token),
    )),
  )
