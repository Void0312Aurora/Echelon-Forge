#!/usr/bin/env python3
"""Generate or verify Experiment-owned run-config matrices.

Each registered matrix is a set of checked-in run-config files that are
projections of typed Experiment definitions (one config base plus a
per-experiment delta). This tool re-expands every registered entry and either
verifies byte parity (--check), rewrites the files (--write), or prints the
machine-readable registration manifest (--manifest) used by the architecture
freshness gates. ``--matrix`` selects the matrix; the default stays the
original 24-file air-combat set:

- ``air_combat``: examples/config/training/active/air_combat/ (24 files),
  owned by python/experiment/air_combat_matrix.py.
- ``cooperative_flight``: the cooperative flight-shaping and P4b entries at
  examples/config/training/active/ (12 files), owned by
  python/experiment/cooperative_flight_matrix.py.

Canonical serialization is LF with a trailing newline; when a checked-out file
is uniformly CRLF (Windows autocrlf checkouts), its line ending is preserved,
mirroring tools/maintenance/dto_schema/generate.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import difflib
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from python.experiment import cooperative_flight_matrix  # noqa: E402
from python.experiment.air_combat_matrix import (  # noqa: E402
  CONFIG_BASE_ID,
  MATRIX_DIR,
  MATRIX_ENTRIES,
  composed_config,
)
from python.experiment.matrix_projection import MatrixEntryBase  # noqa: E402


@dataclass(frozen=True)
class MatrixSpec:
  """One selectable matrix: its owner module plus the projection callables."""

  name: str
  owner_module: str
  matrix_dir: str
  config_base_ids: tuple[str, ...]
  entries: Callable[[], Sequence[MatrixEntryBase]]
  composed_config: Callable[[MatrixEntryBase], dict[str, Any]]


# The air-combat callables read this module's globals at call time so the
# existing test seam (monkeypatching MATRIX_ENTRIES on this module) keeps
# steering the default matrix.
MATRIX_SPECS: Mapping[str, MatrixSpec] = {
  "air_combat": MatrixSpec(
    name="air_combat",
    owner_module="python/experiment/air_combat_matrix.py",
    matrix_dir=MATRIX_DIR,
    config_base_ids=(CONFIG_BASE_ID,),
    entries=lambda: MATRIX_ENTRIES,
    composed_config=lambda entry: composed_config(entry),
  ),
  "cooperative_flight": MatrixSpec(
    name="cooperative_flight",
    owner_module="python/experiment/cooperative_flight_matrix.py",
    matrix_dir=cooperative_flight_matrix.MATRIX_DIR,
    config_base_ids=tuple(cooperative_flight_matrix.CONFIG_BASES),
    entries=lambda: cooperative_flight_matrix.MATRIX_ENTRIES,
    composed_config=cooperative_flight_matrix.composed_config,
  ),
}

DEFAULT_MATRIX = "air_combat"


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
  entry: MatrixEntryBase,
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


def render_entry_bytes(
  entry: MatrixEntryBase,
  line_ending: str = "\n",
  compose: Callable[[MatrixEntryBase], dict[str, Any]] = composed_config,
) -> bytes:
  if line_ending not in {"\n", "\r\n"}:
    raise ValueError(f"unsupported line ending: {line_ending!r}")
  text = _render_value(compose(entry), 0, entry, ()) + "\n"
  if line_ending != "\n":
    text = text.replace("\n", line_ending)
  return text.encode("utf-8")


def manifest_payload(matrix: str = DEFAULT_MATRIX) -> dict[str, object]:
  spec = MATRIX_SPECS[matrix]
  entries = []
  for entry in sorted(spec.entries(), key=lambda item: item.experiment.experiment_id):
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
  payload: dict[str, object] = {
    "version": 1,
    "generator": "tools/maintenance/experiment_matrix/generate.py",
    "matrix": spec.name,
    "owner_module": spec.owner_module,
    "config_bases": list(spec.config_base_ids),
    "matrix_dir": spec.matrix_dir,
    "canonical_line_ending": "LF",
    "entries": entries,
  }
  if len(spec.config_base_ids) == 1:
    # Single-base matrices keep the original scalar field alongside the
    # general list so existing manifest consumers stay valid.
    payload["config_base"] = spec.config_base_ids[0]
  return payload


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


def check_outputs(output_root: Path, matrix: str = DEFAULT_MATRIX) -> int:
  spec = MATRIX_SPECS[matrix]
  stale = False
  for entry in spec.entries():
    target = output_root / entry.output_path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render_entry_bytes(entry, line_ending or "\n", spec.composed_config)
    if actual == expected:
      print(f"up-to-date: {entry.output_path}")
      continue
    stale = True
    print(f"stale: {entry.output_path}")
    print(_diff_summary(entry.output_path, actual, expected))
  return 1 if stale else 0


def write_outputs(output_root: Path, matrix: str = DEFAULT_MATRIX) -> int:
  spec = MATRIX_SPECS[matrix]
  for entry in spec.entries():
    target = output_root / entry.output_path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render_entry_bytes(entry, line_ending or "\n", spec.composed_config)
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
      "Expand a typed Experiment matrix into its checked-in run-config "
      "files, or verify they are byte-identical."
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
    "--matrix",
    choices=sorted(MATRIX_SPECS),
    default=DEFAULT_MATRIX,
    help=f"which registered matrix to operate on (default: {DEFAULT_MATRIX})",
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
    print(json.dumps(manifest_payload(args.matrix), indent=2, sort_keys=True))
    return 0
  if args.write:
    return write_outputs(args.repo_root, args.matrix)
  return check_outputs(args.repo_root, args.matrix)


if __name__ == "__main__":
  raise SystemExit(main())
