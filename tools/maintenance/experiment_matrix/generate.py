#!/usr/bin/env python3
"""Generate or verify the air-combat run-config matrix from its Experiment owner.

The 24 checked-in files under examples/config/training/active/air_combat/ are
projections of python/experiment/air_combat_matrix.py (one config base plus a
per-experiment delta). This tool re-expands every registered entry and either
verifies byte parity (--check), rewrites the files (--write), or prints the
machine-readable registration manifest (--manifest) used by the architecture
freshness gate.

Canonical serialization is LF with a trailing newline; when a checked-out file
is uniformly CRLF (Windows autocrlf checkouts), its line ending is preserved,
mirroring tools/maintenance/dto_schema/generate.py.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.experiment.air_combat_matrix import (  # noqa: E402
  CONFIG_BASE_ID,
  MATRIX_DIR,
  MATRIX_ENTRIES,
  MatrixEntry,
  composed_config,
)


def _strict_json_equal(actual: Any, expected: Any) -> bool:
  """Structural equality that treats bool/int/float as distinct types.

  Plain ``==`` conflates ``True == 1`` and ``1 == 1.0``, so a literal override
  of the wrong scalar type (e.g. a boolean literal overriding an int field)
  could silently pass a bare ``!=`` comparison. Recurses through JSON
  containers so nested literal overrides get the same guarantee.
  """
  if isinstance(actual, Mapping) and isinstance(expected, Mapping):
    return actual.keys() == expected.keys() and all(
      _strict_json_equal(actual[key], expected[key]) for key in actual
    )
  if isinstance(actual, list) and isinstance(expected, list):
    return len(actual) == len(expected) and all(
      _strict_json_equal(a, b) for a, b in zip(actual, expected)
    )
  return type(actual) is type(expected) and actual == expected


def _render_value(
  value: Any,
  indent: int,
  entry: MatrixEntry,
  path: tuple[str, ...],
) -> str:
  overrides = entry.render.literal_overrides
  if path in overrides:
    literal = overrides[path]
    if not _strict_json_equal(json.loads(literal), value):
      raise ValueError(
        f"literal override at {'.'.join(path)} does not equal the composed "
        f"value: {literal!r} vs {value!r}"
      )
    return literal
  pad = "  " * indent
  pad_in = "  " * (indent + 1)
  if isinstance(value, Mapping):
    if not value:
      return "{}"
    items = [
      f"{pad_in}{json.dumps(key)}: {_render_value(child, indent + 1, entry, path + (key,))}"
      for key, child in value.items()
    ]
    return "{\n" + ",\n".join(items) + "\n" + pad + "}"
  if isinstance(value, list):
    if not value:
      return "[]"
    scalars = all(not isinstance(child, (Mapping, list)) for child in value)
    if scalars and entry.render.scalar_array_layout == "inline":
      return "[" + ", ".join(json.dumps(child) for child in value) + "]"
    items = [
      f"{pad_in}{_render_value(child, indent + 1, entry, path + (f'[{index}]',))}"
      for index, child in enumerate(value)
    ]
    return "[\n" + ",\n".join(items) + "\n" + pad + "]"
  return json.dumps(value)


def render_entry_bytes(entry: MatrixEntry, line_ending: str = "\n") -> bytes:
  if line_ending not in {"\n", "\r\n"}:
    raise ValueError(f"unsupported line ending: {line_ending!r}")
  text = _render_value(composed_config(entry), 0, entry, ()) + "\n"
  if line_ending != "\n":
    text = text.replace("\n", line_ending)
  return text.encode("utf-8")


def manifest_payload() -> dict[str, object]:
  entries = []
  for entry in sorted(MATRIX_ENTRIES, key=lambda item: item.experiment.experiment_id):
    experiment = entry.experiment
    entries.append(
      {
        "experiment_id": experiment.experiment_id,
        "scenario": experiment.scenario.path,
        "config_base": experiment.config.base_id,
        "seeds": list(experiment.seeds.values),
        "evaluation_protocol": experiment.evaluation_protocol,
        "output": entry.output_path,
        "scalar_array_layout": entry.render.scalar_array_layout,
        "literal_overrides": {
          ".".join(path): literal
          for path, literal in entry.render.literal_overrides.items()
        },
      }
    )
  return {
    "version": 1,
    "generator": "tools/maintenance/experiment_matrix/generate.py",
    "owner_module": "python/experiment/air_combat_matrix.py",
    "config_base": CONFIG_BASE_ID,
    "matrix_dir": MATRIX_DIR,
    "canonical_line_ending": "LF",
    "entries": entries,
  }


def _uniform_line_ending(content: bytes) -> str | None:
  without_crlf = content.replace(b"\r\n", b"")
  if b"\r" in without_crlf or b"\n" in without_crlf:
    return None
  return "\r\n" if b"\r\n" in content else "\n"


def _diff_summary(path: str, actual: bytes, expected: bytes) -> str:
  actual_lines = actual.decode("utf-8", errors="replace").splitlines()
  expected_lines = expected.decode("utf-8", errors="replace").splitlines()
  diff = list(
    difflib.unified_diff(
      actual_lines,
      expected_lines,
      fromfile=f"{path} (checked in)",
      tofile=f"{path} (generated)",
      lineterm="",
      n=2,
    )
  )
  if not diff:
    actual_hash = hashlib.sha256(actual).hexdigest()[:12]
    expected_hash = hashlib.sha256(expected).hexdigest()[:12]
    return (
      "  byte content differs (likely line endings or final newline): "
      f"checked-in={actual_hash}, generated={expected_hash}"
    )
  limit = 80
  summary = "\n".join(diff[:limit])
  if len(diff) > limit:
    summary += f"\n... {len(diff) - limit} additional diff lines omitted"
  return summary


def check_outputs(output_root: Path) -> int:
  stale = False
  for entry in MATRIX_ENTRIES:
    target = output_root / entry.output_path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render_entry_bytes(entry, line_ending or "\n")
    if actual == expected:
      print(f"up-to-date: {entry.output_path}")
      continue
    stale = True
    print(f"stale: {entry.output_path}")
    print(_diff_summary(entry.output_path, actual, expected))
  return 1 if stale else 0


def write_outputs(output_root: Path) -> int:
  for entry in MATRIX_ENTRIES:
    target = output_root / entry.output_path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render_entry_bytes(entry, line_ending or "\n")
    if target.is_file() and actual == expected:
      print(f"unchanged: {entry.output_path}")
      continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(expected)
    print(f"wrote: {entry.output_path}")
  return 0


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description=(
      "Expand the typed air-combat Experiment matrix into its checked-in "
      "run-config files, or verify they are byte-identical."
    )
  )
  action = parser.add_mutually_exclusive_group(required=True)
  action.add_argument("--check", action="store_true", help="fail on stale outputs")
  action.add_argument("--write", action="store_true", help="write generated outputs")
  action.add_argument(
    "--manifest",
    action="store_true",
    help="print the registered experiment/output manifest as JSON",
  )
  parser.add_argument(
    "--repo-root",
    type=Path,
    default=REPO_ROOT,
    help="override the output root (primarily for isolated checks)",
  )
  return parser


def main(argv: list[str] | None = None) -> int:
  args = _build_parser().parse_args(argv)
  if args.manifest:
    print(json.dumps(manifest_payload(), indent=2, sort_keys=True))
    return 0
  if args.write:
    return write_outputs(args.repo_root)
  return check_outputs(args.repo_root)


if __name__ == "__main__":
  raise SystemExit(main())
