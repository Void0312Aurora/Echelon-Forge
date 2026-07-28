#!/usr/bin/env python3
"""Generate or verify all checked-in DTO artifacts from declarative schemas.

One command covers every generated product: the C++ X-macro .inc fragments,
the Python builder modules under gym_envs/scenario_loader/_generated/, and
that package's __init__.py.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import difflib
import functools
import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.dto_schema import python_builder  # noqa: E402
from tools.maintenance.dto_schema.model import DtoSchema  # noqa: E402
from tools.maintenance.dto_schema.schemas import SCHEMA_MODULES  # noqa: E402


def _load_schema(module_name: str) -> DtoSchema:
  module: ModuleType = importlib.import_module(module_name)
  schema = getattr(module, "SCHEMA", None)
  if not isinstance(schema, DtoSchema):
    raise TypeError(f"{module_name} must export SCHEMA: DtoSchema")
  return schema


def load_schemas() -> tuple[tuple[str, DtoSchema], ...]:
  registrations = tuple(
    (module_name, _load_schema(module_name)) for module_name in SCHEMA_MODULES
  )
  output_paths = [schema.output_path for _, schema in registrations]
  duplicates = sorted(
    path for path, count in Counter(output_paths).items() if count > 1
  )
  if duplicates:
    raise ValueError(f"duplicate generated output registrations: {duplicates}")
  return registrations


def render_schema(schema: DtoSchema, line_ending: str = "\n") -> bytes:
  if line_ending not in {"\n", "\r\n"}:
    raise ValueError(f"unsupported line ending: {line_ending!r}")
  parts = [schema.file_header]
  for field in schema.fields:
    if field.comment:
      parts.append(f"// {field.comment}\n")
    parts.append(
      f"{field.group}({field.cpp_type}, {field.name}, {field.default})\n"
    )
  parts.append(schema.file_footer)
  text = "".join(parts)
  if line_ending != "\n":
    text = text.replace("\n", line_ending)
  return text.encode("utf-8")


def artifact_renderers(
  registrations: tuple[tuple[str, DtoSchema], ...],
) -> tuple[tuple[str, Callable[[str], bytes]], ...]:
  """All generated artifacts as (repo-relative path, render(line_ending)) pairs."""
  artifacts: list[tuple[str, Callable[[str], bytes]]] = []
  for _, schema in registrations:
    artifacts.append((schema.output_path, functools.partial(render_schema, schema)))
  for _, schema in registrations:
    artifacts.append(
      (
        python_builder.builder_output_path(schema),
        functools.partial(python_builder.render_builder_bytes, schema),
      )
    )
  artifacts.append(
    (python_builder.PACKAGE_INIT_PATH, python_builder.render_package_init_bytes)
  )
  paths = [path for path, _ in artifacts]
  duplicates = sorted(path for path, count in Counter(paths).items() if count > 1)
  if duplicates:
    raise ValueError(f"duplicate generated artifact paths: {duplicates}")
  return tuple(artifacts)


def manifest_payload(
  registrations: tuple[tuple[str, DtoSchema], ...],
) -> dict[str, object]:
  schemas: list[dict[str, object]] = []
  for module_name, schema in registrations:
    group_counts = Counter(field.group for field in schema.fields)
    schemas.append(
      {
        "name": schema.name,
        "schema": module_name.replace(".", "/") + ".py",
        "output": schema.output_path,
        "python_builder": python_builder.builder_output_path(schema),
        "field_count": len(schema.fields),
        "groups": dict(sorted(group_counts.items())),
      }
    )
  return {
    "version": 2,
    "generator": "tools/maintenance/dto_schema/generate.py",
    "canonical_line_ending": "LF",
    "schemas": schemas,
    "python_builder_package_init": python_builder.PACKAGE_INIT_PATH,
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


def check_outputs(
  registrations: tuple[tuple[str, DtoSchema], ...],
  output_root: Path,
) -> int:
  stale = False
  for path, render in artifact_renderers(registrations):
    target = output_root / path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render(line_ending or "\n")
    if actual == expected:
      print(f"up-to-date: {path}")
      continue
    stale = True
    print(f"stale: {path}")
    print(_diff_summary(path, actual, expected))
  return 1 if stale else 0


def write_outputs(
  registrations: tuple[tuple[str, DtoSchema], ...],
  output_root: Path,
) -> int:
  for path, render in artifact_renderers(registrations):
    target = output_root / path
    actual = target.read_bytes() if target.is_file() else b""
    line_ending = _uniform_line_ending(actual)
    expected = render(line_ending or "\n")
    if target.is_file() and actual == expected:
      print(f"unchanged: {path}")
      continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(expected)
    print(f"wrote: {path}")
  return 0


def _build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description=(
      "Generate checked-in DTO artifacts: X-macro fragments, Python "
      "builders, and the _generated package __init__."
    )
  )
  action = parser.add_mutually_exclusive_group(required=True)
  action.add_argument("--check", action="store_true", help="fail on stale outputs")
  action.add_argument("--write", action="store_true", help="write generated outputs")
  action.add_argument(
    "--manifest",
    action="store_true",
    help="print the registered schema/output manifest as JSON",
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
  registrations = load_schemas()
  if args.manifest:
    print(json.dumps(manifest_payload(registrations), indent=2, sort_keys=True))
    return 0
  if args.write:
    return write_outputs(registrations, args.repo_root)
  return check_outputs(registrations, args.repo_root)


if __name__ == "__main__":
  raise SystemExit(main())
