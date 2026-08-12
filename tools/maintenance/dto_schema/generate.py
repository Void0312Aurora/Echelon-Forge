#!/usr/bin/env python3
"""Generate or verify all checked-in DTO artifacts from declarative schemas.

One command covers every generated product: the C++ X-macro .inc fragments,
the Python builder modules under gym_envs/scenario_loader/_generated/, and
that package's __init__.py.

Beyond per-file byte comparison, the CLI is self-contained on two integrity
properties so no separate test is needed to trust a green --check:

- the schemas/ directory and the SCHEMA_MODULES registry must agree (a
  schema module that exists on disk but is unregistered, or registered but
  missing, aborts every command);
- gym_envs/scenario_loader/_generated/ is a fully generated directory, so
  *.py files there that no registered schema owns fail --check and are
  removed by --write. Ownership is compared case-insensitively where the
  platform folds case (os.path.normcase): a directory entry that matches a
  registered artifact except for spelling case is reported as a case
  mismatch and is never deleted, because on a case-insensitive filesystem
  it is the same file the write loop manages.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Collection, Iterable
import difflib
import functools
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.dto_schema import python_builder  # noqa: E402
from tools.maintenance.dto_schema.model import DtoSchema  # noqa: E402
from tools.maintenance.dto_schema.schemas import SCHEMA_MODULES  # noqa: E402


SCHEMAS_PACKAGE = "tools.maintenance.dto_schema.schemas"
SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


def _load_schema(module_name: str) -> DtoSchema:
  module: ModuleType = importlib.import_module(module_name)
  schema = getattr(module, "SCHEMA", None)
  if not isinstance(schema, DtoSchema):
    raise TypeError(f"{module_name} must export SCHEMA: DtoSchema")
  return schema


def registry_inconsistencies(
  registered_modules: tuple[str, ...],
  schemas_dir: Path,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
  """Compare the SCHEMA_MODULES registry against the schemas/ directory.

  Returns (unregistered, missing): schema modules present on disk but absent
  from the registry, and registered module names without a backing file.
  """
  on_disk = {
    f"{SCHEMAS_PACKAGE}.{path.stem}"
    for path in schemas_dir.glob("*.py")
    if path.name != "__init__.py"
  }
  registered = set(registered_modules)
  return (
    tuple(sorted(on_disk - registered)),
    tuple(sorted(registered - on_disk)),
  )


def load_schemas() -> tuple[tuple[str, DtoSchema], ...]:
  unregistered, missing = registry_inconsistencies(SCHEMA_MODULES, SCHEMAS_DIR)
  if unregistered or missing:
    problems = []
    if unregistered:
      problems.append(
        "schema modules on disk but not in SCHEMA_MODULES: "
        f"{list(unregistered)}"
      )
    if missing:
      problems.append(
        f"registered schema modules missing on disk: {list(missing)}"
      )
    raise ValueError("; ".join(problems))
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


def classify_generated_files(
  owned: Collection[str],
  found: Iterable[str],
  normalize: Callable[[str], str] = os.path.normcase,
) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
  """Split scanned generated-package paths into orphans and case mismatches.

  Ownership is decided on normalize-folded paths (os.path.normcase by
  default, so case is folded exactly where the platform folds it). A found
  path that folds onto a registered artifact but differs in exact spelling
  is a (actual, registered) case mismatch: on a case-insensitive filesystem
  it is the very directory entry the write loop manages, so it must never
  be classified as a deletable orphan. Only paths that fold onto nothing
  registered are orphans.
  """
  owned_by_norm = {normalize(path): path for path in owned}
  unexpected: list[str] = []
  mismatched: list[tuple[str, str]] = []
  for path in found:
    canonical = owned_by_norm.get(normalize(path))
    if canonical is None:
      unexpected.append(path)
    elif canonical != path:
      mismatched.append((path, canonical))
  return tuple(sorted(unexpected)), tuple(sorted(mismatched))


def scan_generated_package(
  registrations: tuple[tuple[str, DtoSchema], ...],
  output_root: Path,
) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
  """Classify the generated package's top-level *.py files.

  The generated package directory holds only generator output, so any other
  Python file there is a stale or hand-added artifact. Only regular files at
  the directory's top level are scanned; directories (even ones named like
  x.py), __pycache__, and non-.py entries are ignored.
  """
  package_dir = output_root / python_builder.GENERATED_PACKAGE_DIR
  if not package_dir.is_dir():
    return ((), ())
  owned = {
    python_builder.builder_output_path(schema) for _, schema in registrations
  }
  owned.add(python_builder.PACKAGE_INIT_PATH)
  found = tuple(
    f"{python_builder.GENERATED_PACKAGE_DIR}/{path.name}"
    for path in package_dir.glob("*.py")
    if path.is_file()
  )
  return classify_generated_files(owned, found)


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
  unexpected, case_mismatched = scan_generated_package(
    registrations, output_root
  )
  for path in unexpected:
    stale = True
    print(f"unexpected: {path}")
    print(
      "  file is not owned by any registered schema; remove it or run "
      "generate.py --write"
    )
  for actual, registered in case_mismatched:
    stale = True
    print(f"case-mismatch: {actual}")
    print(
      f"  directory entry differs from registered artifact {registered} "
      "only by case; rename it by hand (generate.py never deletes it)"
    )
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
  unexpected, case_mismatched = scan_generated_package(
    registrations, output_root
  )
  for path in unexpected:
    (output_root / path).unlink()
    print(f"removed: {path}")
  for actual, registered in case_mismatched:
    print(f"case mismatch (not removed): {actual}")
    print(
      f"  directory entry differs from registered artifact {registered} "
      "only by case; refusing to delete, rename it by hand"
    )
  return 1 if case_mismatched else 0


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
