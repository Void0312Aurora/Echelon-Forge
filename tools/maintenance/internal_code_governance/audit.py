"""Audit added or selected lines for opaque repository-internal codes."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .policy import (
  COMPATIBILITY_MARKER,
  PHASE_IDENTIFIER_RE,
  PHASE_PROSE_RE,
  POLICY_DOCUMENTS,
  SOURCE_SUFFIXES,
  TRACKING_CODE_RE,
  TRACKING_CODE_TOKEN_RE,
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


@dataclass(frozen=True)
class _TextSpan:
  start: int
  end: int
  token: str


@dataclass(frozen=True)
class _LineLexicalRanges:
  comments: tuple[tuple[int, int], ...]
  strings: tuple[tuple[int, int], ...]


_IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_IDENTIFIER_SEGMENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_CAMEL_BOUNDARY_RE = re.compile(
  r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
)
_ACRONYM_TRACKING_CODE_RE = re.compile(r"(?:RB|CR|WP|TM|MLF|RES)\d+|I\d{2,}")
_ACRONYM_PHASE_RE = re.compile(r"PHASE[A-D]")
_CPP_RAW_STRING_START_RE = re.compile(
  r'R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\('
)


def _find_unescaped(text: str, needle: str, start: int) -> int:
  offset = text.find(needle, start)
  while offset >= 0:
    backslashes = 0
    cursor = offset - 1
    while cursor >= 0 and text[cursor] == "\\":
      backslashes += 1
      cursor -= 1
    if backslashes % 2 == 0:
      return offset
    offset = text.find(needle, offset + 1)
  return -1


def _quoted_string_end(line: str, start: int) -> int:
  quote = line[start]
  cursor = start + 1
  while cursor < len(line):
    if line[cursor] == "\\":
      cursor += 2
      continue
    if line[cursor] == quote:
      return cursor + 1
    cursor += 1
  return len(line)


def _python_lexical_ranges(lines: list[str]) -> list[_LineLexicalRanges]:
  result: list[_LineLexicalRanges] = []
  triple_delimiter: str | None = None
  for line in lines:
    comments: list[tuple[int, int]] = []
    strings: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(line):
      if triple_delimiter is not None:
        end = _find_unescaped(line, triple_delimiter, cursor)
        if end < 0:
          strings.append((cursor, len(line)))
          cursor = len(line)
        else:
          strings.append((cursor, end + len(triple_delimiter)))
          cursor = end + len(triple_delimiter)
          triple_delimiter = None
        continue
      delimiter = next(
        (candidate for candidate in ('"""', "'''") if line.startswith(candidate, cursor)),
        None,
      )
      if delimiter is not None:
        end = _find_unescaped(line, delimiter, cursor + len(delimiter))
        if end < 0:
          strings.append((cursor, len(line)))
          triple_delimiter = delimiter
          cursor = len(line)
        else:
          strings.append((cursor, end + len(delimiter)))
          cursor = end + len(delimiter)
        continue
      if line[cursor] in {'"', "'"}:
        end = _quoted_string_end(line, cursor)
        strings.append((cursor, end))
        cursor = end
        continue
      if line[cursor] == "#":
        comments.append((cursor, len(line)))
        break
      cursor += 1
    result.append(_LineLexicalRanges(tuple(comments), tuple(strings)))
  return result


def _cpp_lexical_ranges(lines: list[str]) -> list[_LineLexicalRanges]:
  result: list[_LineLexicalRanges] = []
  in_block_comment = False
  raw_string_end: str | None = None
  for line in lines:
    comments: list[tuple[int, int]] = []
    strings: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(line):
      if raw_string_end is not None:
        end = line.find(raw_string_end, cursor)
        if end < 0:
          strings.append((cursor, len(line)))
          cursor = len(line)
        else:
          strings.append((cursor, end + len(raw_string_end)))
          cursor = end + len(raw_string_end)
          raw_string_end = None
        continue
      if in_block_comment:
        end = line.find("*/", cursor)
        if end < 0:
          comments.append((cursor, len(line)))
          cursor = len(line)
        else:
          comments.append((cursor, end + 2))
          in_block_comment = False
          cursor = end + 2
        continue
      raw_start = _CPP_RAW_STRING_START_RE.match(line, cursor)
      if raw_start is not None:
        raw_string_end = f'){raw_start.group("delimiter")}"'
        end = line.find(raw_string_end, raw_start.end())
        if end < 0:
          strings.append((cursor, len(line)))
          cursor = len(line)
        else:
          strings.append((cursor, end + len(raw_string_end)))
          cursor = end + len(raw_string_end)
          raw_string_end = None
        continue
      if line[cursor] in {'"', "'"}:
        end = _quoted_string_end(line, cursor)
        strings.append((cursor, end))
        cursor = end
        continue
      if line.startswith("//", cursor):
        comments.append((cursor, len(line)))
        break
      if line.startswith("/*", cursor):
        end = line.find("*/", cursor + 2)
        if end < 0:
          comments.append((cursor, len(line)))
          in_block_comment = True
          cursor = len(line)
        else:
          comments.append((cursor, end + 2))
          cursor = end + 2
        continue
      cursor += 1
    result.append(_LineLexicalRanges(tuple(comments), tuple(strings)))
  return result


def _source_lexical_ranges(path: str, lines: list[str]) -> list[_LineLexicalRanges]:
  if Path(path).suffix.lower() == ".py":
    return _python_lexical_ranges(lines)
  return _cpp_lexical_ranges(lines)


def _inside_ranges(ranges: tuple[tuple[int, int], ...], offset: int) -> bool:
  return any(start <= offset < end for start, end in ranges)


def _identifier_token_groups(text: str) -> tuple[tuple[_TextSpan, ...], ...]:
  groups: list[tuple[_TextSpan, ...]] = []
  for identifier in _IDENTIFIER_RE.finditer(text):
    tokens: list[_TextSpan] = []
    for segment in _IDENTIFIER_SEGMENT_RE.finditer(identifier.group(0)):
      segment_text = segment.group(0)
      boundaries = [0]
      boundaries.extend(match.start() for match in _CAMEL_BOUNDARY_RE.finditer(segment_text))
      boundaries.append(len(segment_text))
      for start, end in zip(boundaries, boundaries[1:]):
        absolute_start = identifier.start() + segment.start() + start
        absolute_end = identifier.start() + segment.start() + end
        tokens.append(_TextSpan(absolute_start, absolute_end, text[absolute_start:absolute_end]))
    if tokens:
      groups.append(tuple(tokens))
  return tuple(groups)


def _overlaps(span: _TextSpan, others: list[_TextSpan]) -> bool:
  return any(span.start < other.end and other.start < span.end for other in others)


def _has_high_confidence_acronym_context(
  identifier: str,
  match: re.Match[str],
) -> bool:
  prefix = identifier[:match.start()]
  suffix = identifier[match.end():]
  return (
    len(prefix) >= 2
    and prefix.isupper()
    and (not suffix or suffix[0].isupper())
  )


def _tracking_code_spans(text: str) -> tuple[_TextSpan, ...]:
  spans = [
    _TextSpan(match.start(), match.end(), match.group(0))
    for match in TRACKING_CODE_RE.finditer(text)
  ]
  for group in _identifier_token_groups(text):
    for token in group:
      if (
        len(group) > 1
        and re.fullmatch(r"I\d{2,}", token.token, re.IGNORECASE)
      ):
        continue
      if TRACKING_CODE_TOKEN_RE.fullmatch(token.token) and not _overlaps(token, spans):
        spans.append(token)
  for identifier in _IDENTIFIER_RE.finditer(text):
    for match in _ACRONYM_TRACKING_CODE_RE.finditer(identifier.group(0)):
      if not _has_high_confidence_acronym_context(identifier.group(0), match):
        continue
      candidate = _TextSpan(
        identifier.start() + match.start(),
        identifier.start() + match.end(),
        match.group(0),
      )
      if not _overlaps(candidate, spans):
        spans.append(candidate)
  return tuple(sorted(spans, key=lambda span: (span.start, span.end, span.token)))


def _phase_identifier_spans(text: str) -> tuple[_TextSpan, ...]:
  spans = [
    _TextSpan(match.start(), match.end(), match.group(0))
    for match in PHASE_IDENTIFIER_RE.finditer(text)
  ]
  for group in _identifier_token_groups(text):
    for first, second in zip(group, group[1:]):
      if first.token.lower() != "phase" or second.token.lower() not in {"a", "b", "c", "d"}:
        continue
      candidate = _TextSpan(first.start, second.end, text[first.start:second.end])
      if not _overlaps(candidate, spans):
        spans.append(candidate)
  for identifier in _IDENTIFIER_RE.finditer(text):
    for match in _ACRONYM_PHASE_RE.finditer(identifier.group(0)):
      if not _has_high_confidence_acronym_context(identifier.group(0), match):
        continue
      candidate = _TextSpan(
        identifier.start() + match.start(),
        identifier.start() + match.end(),
        match.group(0),
      )
      if not _overlaps(candidate, spans):
        spans.append(candidate)
  return tuple(sorted(spans, key=lambda span: (span.start, span.end, span.token)))


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


def _source_findings(
  path: str,
  lines: list[str],
  index: int,
  lexical_ranges: _LineLexicalRanges,
) -> list[Finding]:
  line = lines[index]
  line_number = index + 1
  compatibility = _has_compatibility_marker(lines, index)
  findings: list[Finding] = []

  for match in _tracking_code_spans(line):
    if compatibility:
      continue
    if _inside_ranges(lexical_ranges.comments, match.start):
      severity = "warning"
      code = "source-tracking-code-comment"
      message = "source comments should explain behavior without work-tracking codes"
    elif _inside_ranges(lexical_ranges.strings, match.start):
      severity = "error"
      code = "runtime-tracking-code"
      message = "runtime or diagnostic strings must use semantic capability names"
    else:
      severity = "error"
      code = "source-tracking-code"
      message = "production identifiers must not encode work packages or iterations"
    findings.append(
      Finding(code, severity, path, line_number, match.token, message)
    )

  for match in _phase_identifier_spans(line):
    if compatibility:
      continue
    in_comment = _inside_ranges(lexical_ranges.comments, match.start)
    findings.append(
      Finding(
        "opaque-phase-comment" if in_comment else "opaque-phase-identifier",
        "warning" if in_comment else "error",
        path,
        line_number,
        match.token,
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
    in_comment = _inside_ranges(lexical_ranges.comments, match.start())
    in_string = _inside_ranges(lexical_ranges.strings, match.start())
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
  lexical_ranges = _source_lexical_ranges(normalized, lines) if is_production_source(normalized) else []
  for line_number in sorted(selected):
    index = line_number - 1
    if is_production_source(normalized):
      findings.extend(_source_findings(normalized, lines, index, lexical_ranges[index]))
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
  findings: list[Finding] = []
  for component in PurePosixPath(normalized).parts:
    for match in _tracking_code_spans(component):
      findings.append(
        Finding(
          "source-tracking-code-path",
          "error",
          normalized,
          0,
          match.token,
          "new production paths must not encode work packages or iterations",
        )
      )
    phase_spans = list(_phase_identifier_spans(component))
    phase_spans.extend(
      _TextSpan(match.start(), match.end(), match.group(0))
      for match in PHASE_PROSE_RE.finditer(component)
    )
    seen_phase_spans: set[tuple[int, int]] = set()
    for match in sorted(phase_spans, key=lambda span: (span.start, span.end, span.token)):
      location = (match.start, match.end)
      if location in seen_phase_spans:
        continue
      seen_phase_spans.add(location)
      findings.append(
        Finding(
          "opaque-phase-path",
          "error",
          normalized,
          0,
          match.token,
          "new production paths must lead with a semantic stage name",
        )
      )
  return tuple(findings)


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
      line_numbers=None if relative in new_paths else changed.get(relative, set()),
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
