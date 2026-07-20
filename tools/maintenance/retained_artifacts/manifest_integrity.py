#!/usr/bin/env python3
"""Check retained A2 manifest artifact hashes and authority guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_PACKAGE_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "archive"
  / "a2_high_fidelity_damage_model"
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
DEFAULT_MANIFEST_GLOB = "retained_artifacts/**/manifest.json"

PATH_FIELDS = ("path", "relative_path", "filename")
HASH_FIELDS = ("sha256", "content_sha256", "content_hash")
GUARD_TERMS = ("authority", "stock", "pk", "fuze")
SAFE_AGGREGATE_GUARD_MARKERS = ("all_false", "none_granted", "not_granted")


@dataclass(frozen=True)
class ManifestFinding:
  manifest_path: Path
  row_path: str
  field: str
  expected: str
  actual: str
  target_path: str
  fixable: bool = False


def _sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    while True:
      chunk = handle.read(1024 * 1024)
      if not chunk:
        break
      digest.update(chunk)
  return digest.hexdigest()


def _sha256_text(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_and_hash_json(
  path: Path,
  payload: dict[str, Any],
  *,
  ensure_ascii: bool = True,
  indent: int = 2,
  sort_keys: bool = True,
  encoding: str = "utf-8",
) -> str:
  """Write *payload* as JSON with trailing newline and return the sha256 of the written file."""
  path.parent.mkdir(parents=True, exist_ok=True)
  text = json.dumps(payload, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys) + "\n"
  path.write_text(text, encoding=encoding)
  return _sha256_file(path)


def add_retained_gate_output_args(
  parser: argparse.ArgumentParser,
  *,
  retained_dir_default: Path,
  output_dir_help: str = "Directory for retained JSON artifacts.",
  stdout_help: str = "Also print the gate JSON to stdout after writing retained artifacts.",
) -> None:
  """Add the shared "always write retained gate, optionally echo" CLI options.

  Covers ``--output-dir`` (defaults to *retained_dir_default*) and
  ``--stdout``, shared verbatim by the independent-review retained-gate CLIs
  (review closeout, scope-bucket review, uncertainty review). Each caller's
  own help text stays an explicit override where it diverges from the most
  common wording.
  """
  parser.add_argument("--output-dir", type=Path, default=retained_dir_default, help=output_dir_help)
  parser.add_argument("--stdout", action="store_true", help=stdout_help)


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
  except ValueError:
    return str(path)


def _is_relative_to(path: Path, base: Path) -> bool:
  try:
    path.resolve().relative_to(base.resolve())
  except ValueError:
    return False
  return True


def _iter_dict_rows(value: Any, row_path: str = "$"):
  if isinstance(value, dict):
    yield row_path, value
    for key, child in value.items():
      yield from _iter_dict_rows(child, f"{row_path}.{key}")
  elif isinstance(value, list):
    for index, child in enumerate(value):
      yield from _iter_dict_rows(child, f"{row_path}[{index}]")


def _iter_true_guards(value: Any, row_path: str = "$"):
  if isinstance(value, dict):
    for key, child in value.items():
      child_path = f"{row_path}.{key}"
      key_lower = str(key).lower()
      if (
        isinstance(child, bool)
        and child is True
        and any(term in key_lower for term in GUARD_TERMS)
        and not any(
          marker in key_lower for marker in SAFE_AGGREGATE_GUARD_MARKERS
        )
      ):
        yield child_path
      yield from _iter_true_guards(child, child_path)
  elif isinstance(value, list):
    for index, child in enumerate(value):
      yield from _iter_true_guards(child, f"{row_path}[{index}]")


def _path_field_for_row(row: dict[str, Any]) -> str | None:
  for field in PATH_FIELDS:
    value = row.get(field)
    if isinstance(value, str) and value.strip():
      return field
  return None


def _hash_fields_for_row(row: dict[str, Any]) -> list[str]:
  return [
    field
    for field in HASH_FIELDS
    if isinstance(row.get(field), str) and str(row[field]).strip()
  ]


def _resolve_manifest_target(
  *,
  path_value: str,
  path_field: str,
  manifest_path: Path,
  repo_root: Path,
) -> Path:
  raw = Path(path_value)
  if raw.is_absolute():
    return raw

  if path_field == "filename":
    return manifest_path.parent / raw

  repo_candidate = repo_root / raw
  if repo_candidate.exists():
    return repo_candidate

  if raw.parent == Path("."):
    return manifest_path.parent / raw

  return repo_candidate


def _normalize_hash(value: str) -> str:
  text = value.strip().lower()
  if text.startswith("sha256:"):
    return text.split(":", 1)[1]
  return text


def _hash_value_for_field(field: str, digest: str, previous_value: str) -> str:
  if field == "content_hash" and previous_value.strip().lower().startswith("sha256:"):
    return f"sha256:{digest}"
  return digest


def _collect_manifest_findings(
  *,
  manifest_path: Path,
  repo_root: Path,
  payload: dict[str, Any],
) -> tuple[list[ManifestFinding], list[ManifestFinding], list[str]]:
  missing: list[ManifestFinding] = []
  mismatches: list[ManifestFinding] = []
  guards = list(_iter_true_guards(payload))

  for row_path, row in _iter_dict_rows(payload):
    path_field = _path_field_for_row(row)
    hash_fields = _hash_fields_for_row(row)
    if path_field is None or not hash_fields:
      continue

    path_value = str(row[path_field])
    target = _resolve_manifest_target(
      path_value=path_value,
      path_field=path_field,
      manifest_path=manifest_path,
      repo_root=repo_root,
    )
    target_display = _display_path(target, repo_root)
    fixable = _is_relative_to(target, manifest_path.parent)
    if not target.is_file():
      missing.append(
        ManifestFinding(
          manifest_path=manifest_path,
          row_path=row_path,
          field=path_field,
          expected="file_exists",
          actual="missing",
          target_path=target_display,
          fixable=False,
        )
      )
      continue

    digest = _sha256_file(target)
    for hash_field in hash_fields:
      actual = str(row[hash_field])
      if _normalize_hash(actual) != digest:
        mismatches.append(
          ManifestFinding(
            manifest_path=manifest_path,
            row_path=row_path,
            field=hash_field,
            expected=digest,
            actual=actual,
            target_path=target_display,
            fixable=fixable,
          )
        )

  return missing, mismatches, guards


def _apply_manifest_fixes(
  *,
  manifest_path: Path,
  repo_root: Path,
  payload: dict[str, Any],
) -> int:
  fixed = 0
  for _, row in _iter_dict_rows(payload):
    path_field = _path_field_for_row(row)
    hash_fields = _hash_fields_for_row(row)
    if path_field is None or not hash_fields:
      continue

    target = _resolve_manifest_target(
      path_value=str(row[path_field]),
      path_field=path_field,
      manifest_path=manifest_path,
      repo_root=repo_root,
    )
    if not target.is_file() or not _is_relative_to(target, manifest_path.parent):
      continue

    digest = _sha256_file(target)
    for hash_field in hash_fields:
      previous = str(row[hash_field])
      if _normalize_hash(previous) == digest:
        continue
      row[hash_field] = _hash_value_for_field(hash_field, digest, previous)
      fixed += 1
  return fixed


def _manifest_paths(package_dir: Path) -> list[Path]:
  return sorted(package_dir.glob(DEFAULT_MANIFEST_GLOB))


def check_retained_manifest_integrity(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = CANDIDATE_PACKAGE_DIR,
  manifest_paths: list[Path] | None = None,
  fix: bool = False,
) -> dict[str, Any]:
  manifests = manifest_paths if manifest_paths is not None else _manifest_paths(package_dir)
  loaded: list[tuple[Path, dict[str, Any]]] = []
  for manifest_path in manifests:
    loaded.append(
      (
        manifest_path,
        json.loads(manifest_path.read_text(encoding="utf-8")),
      )
    )

  fixed_hash_fields = 0
  if fix:
    for manifest_path, payload in loaded:
      fixed_for_manifest = _apply_manifest_fixes(
        manifest_path=manifest_path,
        repo_root=repo_root,
        payload=payload,
      )
      if fixed_for_manifest:
        manifest_path.write_text(
          json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
          encoding="utf-8",
        )
        fixed_hash_fields += fixed_for_manifest

    loaded = [
      (
        manifest_path,
        json.loads(manifest_path.read_text(encoding="utf-8")),
      )
      for manifest_path, _ in loaded
    ]

  all_missing: list[ManifestFinding] = []
  all_mismatches: list[ManifestFinding] = []
  all_guards: list[tuple[Path, str]] = []
  for manifest_path, payload in loaded:
    missing, mismatches, guards = _collect_manifest_findings(
      manifest_path=manifest_path,
      repo_root=repo_root,
      payload=payload,
    )
    all_missing.extend(missing)
    all_mismatches.extend(mismatches)
    all_guards.extend((manifest_path, guard) for guard in guards)

  return {
    "manifest_count": len(loaded),
    "missing_total": len(all_missing),
    "sha_mismatch_total": len(all_mismatches),
    "guard_true_total": len(all_guards),
    "fixed_hash_fields": fixed_hash_fields,
    "missing": [
      {
        "manifest": _display_path(finding.manifest_path, repo_root),
        "row": finding.row_path,
        "target": finding.target_path,
      }
      for finding in all_missing
    ],
    "sha_mismatches": [
      {
        "manifest": _display_path(finding.manifest_path, repo_root),
        "row": finding.row_path,
        "field": finding.field,
        "target": finding.target_path,
        "expected": finding.expected,
        "actual": finding.actual,
        "fixable": finding.fixable,
      }
      for finding in all_mismatches
    ],
    "guard_true": [
      {
        "manifest": _display_path(manifest_path, repo_root),
        "field": guard_path,
      }
      for manifest_path, guard_path in all_guards
    ],
  }


def _summary_failed(summary: dict[str, Any]) -> bool:
  return any(
    summary[field] != 0
    for field in ("missing_total", "sha_mismatch_total", "guard_true_total")
  )


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Check retained damage-model candidate manifest artifact integrity."
  )
  parser.add_argument(
    "--fix",
    action="store_true",
    help=(
      "Update mismatched hash fields only when the referenced artifact is "
      "inside the manifest directory."
    ),
  )
  args = parser.parse_args(argv)

  summary = check_retained_manifest_integrity(fix=args.fix)
  print(json.dumps(summary, indent=2, ensure_ascii=False))
  return 1 if _summary_failed(summary) else 0


if __name__ == "__main__":
  raise SystemExit(main())
