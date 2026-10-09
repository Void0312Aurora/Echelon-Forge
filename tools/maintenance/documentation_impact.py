#!/usr/bin/env python3
"""Report and gate narrow code-to-documentation impact decisions.

The matrix is intentionally small and owner-aware. It identifies review work for
high-impact maintained owners; it does not attempt semantic translation or
require documentation edits for every implementation diff.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = (
    REPO_ROOT
    / "docs"
    / "engineering"
    / "documentation"
    / "reference"
    / "documentation_impact_matrix.json"
)
DECISIONS = ("docs-updated", "still-accurate", "candidate-or-historical")


@dataclass(frozen=True)
class ImpactRule:
  id: str
  code_prefixes: tuple[str, ...]
  documentation: tuple[str, ...]
  evidence: tuple[str, ...]
  note: str


@dataclass(frozen=True)
class ImpactReport:
  status: str
  decision: str | None
  changed_paths: tuple[str, ...]
  impacted_rules: tuple[ImpactRule, ...]
  changed_documentation: tuple[str, ...]
  message: str


def _patterns(value: object, *, field: str) -> tuple[str, ...]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
    raise ValueError(f"matrix {field} must be a non-empty string list")
  return tuple(item.replace("\\", "/") for item in value)


def load_matrix(path: Path = MATRIX_PATH) -> tuple[ImpactRule, ...]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  if payload.get("schema_version") != 1:
    raise ValueError("unsupported documentation impact matrix schema")
  rules: list[ImpactRule] = []
  for raw in payload.get("entries", []):
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
      raise ValueError("every matrix entry needs a string id")
    rules.append(
      ImpactRule(
        id=raw["id"],
        code_prefixes=_patterns(raw.get("code_prefixes"), field="code_prefixes"),
        documentation=_patterns(raw.get("documentation"), field="documentation"),
        evidence=_patterns(raw.get("evidence"), field="evidence"),
        note=str(raw.get("note", "")).strip(),
      )
    )
  if not rules or len({rule.id for rule in rules}) != len(rules):
    raise ValueError("documentation impact matrix must contain unique entries")
  return tuple(rules)


def _normalize_path(path: str) -> str:
  normalized = path.replace("\\", "/")
  while normalized.startswith("./"):
    normalized = normalized[2:]
  return normalized


def _matches(path: str, patterns: Iterable[str]) -> bool:
  normalized = _normalize_path(path)
  for pattern in patterns:
    candidate = _normalize_path(pattern)
    if "*" in candidate or "?" in candidate:
      if fnmatchcase(normalized, candidate):
        return True
    elif normalized == candidate or normalized.startswith(candidate.rstrip("/") + "/"):
      return True
  return False


def evaluate(
  changed_paths: Iterable[str],
  *,
  decision: str | None = None,
  reason: str = "",
  matrix: Sequence[ImpactRule] | None = None,
) -> ImpactReport:
  changed = tuple(sorted({_normalize_path(path) for path in changed_paths if path}))
  rules = tuple(matrix) if matrix is not None else load_matrix()
  impacted = tuple(
    rule for rule in rules if any(_matches(path, rule.code_prefixes) for path in changed)
  )
  changed_docs = tuple(
    path
    for path in changed
    if any(_matches(path, rule.documentation) for rule in impacted)
  )
  if not impacted:
    return ImpactReport(
      status="no-impact",
      decision=decision,
      changed_paths=changed,
      impacted_rules=(),
      changed_documentation=(),
      message="no matrix owner matches the changed paths",
    )
  if decision is None:
    return ImpactReport(
      status="review-required",
      decision=None,
      changed_paths=changed,
      impacted_rules=impacted,
      changed_documentation=changed_docs,
      message="choose docs-updated, still-accurate, or candidate-or-historical",
    )
  if decision not in DECISIONS:
    raise ValueError(f"unsupported decision: {decision}")
  if decision == "docs-updated" and not changed_docs:
    return ImpactReport(
      status="invalid",
      decision=decision,
      changed_paths=changed,
      impacted_rules=impacted,
      changed_documentation=changed_docs,
      message="docs-updated requires a changed documentation target from the matched owner rows",
    )
  if decision != "docs-updated" and not reason.strip():
    return ImpactReport(
      status="invalid",
      decision=decision,
      changed_paths=changed,
      impacted_rules=impacted,
      changed_documentation=changed_docs,
      message="a still-accurate or candidate-or-historical decision requires a short reason",
    )
  return ImpactReport(
    status="pass",
    decision=decision,
    changed_paths=changed,
    impacted_rules=impacted,
    changed_documentation=changed_docs,
    message=reason.strip() or "matched documentation targets are included",
  )


def _changed_paths(base: str, head: str) -> tuple[str, ...]:
  result = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}"],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )
  return tuple(line for line in result.stdout.splitlines() if line)


def _json_report(report: ImpactReport) -> dict[str, object]:
  return {
    "status": report.status,
    "decision": report.decision,
    "changed_paths": list(report.changed_paths),
    "impacted_rules": [asdict(rule) for rule in report.impacted_rules],
    "changed_documentation": list(report.changed_documentation),
    "message": report.message,
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--base", required=True, help="git revision at the start of the change")
  parser.add_argument("--head", default="HEAD", help="git revision at the end of the change")
  parser.add_argument("--decision", choices=DECISIONS)
  parser.add_argument("--reason", default="")
  parser.add_argument("--check", action="store_true", help="fail when an impacted change has no valid decision")
  parser.add_argument("--json", action="store_true", dest="as_json")
  args = parser.parse_args(argv)
  report = evaluate(_changed_paths(args.base, args.head), decision=args.decision, reason=args.reason)
  if args.as_json:
    print(json.dumps(_json_report(report), ensure_ascii=False, indent=2))
  else:
    print(f"status: {report.status}")
    print(f"message: {report.message}")
    for rule in report.impacted_rules:
      print(f"impact: {rule.id} — {rule.note}")
    if report.changed_documentation:
      print("documentation: " + ", ".join(report.changed_documentation))
  if args.check and report.status not in {"pass", "no-impact"}:
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
