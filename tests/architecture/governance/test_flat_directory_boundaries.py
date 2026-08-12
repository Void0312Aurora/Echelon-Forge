"""Keep generated schema/include directories below the flatness threshold.

The 2026-08-04 directory audit treats 20 files at one level as a confirmed
flat-directory concern. These checks cover only the three directories selected
for immediate or near-term remediation; test, RL, and core-engine watch items
remain outside this gate until their documented thresholds are crossed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FLAT_DIRECTORY_THRESHOLD = 20
RUNTIME_DETAIL_INCLUDE = re.compile(
  r'#include\s+"(runtime/(?:contracts|facade)/detail/[^"]+\.inc)"'
)

SCHEMA_ROOT = REPO_ROOT / "tools" / "maintenance" / "dto_schema" / "schemas"
SCHEMA_DOMAINS = frozenset(
  {
    "batch",
    "damage",
    "engagement",
    "kill_chain",
    "learning",
    "platform",
    "runtime",
    "scenario",
    "tasking",
    "window",
  }
)

INC_LAYOUTS = (
  (
    REPO_ROOT / "src" / "runtime" / "contracts" / "detail",
    frozenset(
      {
        "damage",
        "engagement",
        "kill_chain",
        "learning",
        "platform",
        "scenario",
        "tasking",
      }
    ),
  ),
  (
    REPO_ROOT / "src" / "runtime" / "facade" / "detail",
    frozenset({"batch", "runtime", "window"}),
  ),
)


def _source_directories(root: Path) -> list[Path]:
  return [
    root,
    *sorted(
      (
        path
        for path in root.rglob("*")
        if path.is_dir() and path.name != "__pycache__"
      ),
      key=lambda path: path.as_posix(),
    ),
  ]


def _assert_below_flatness_threshold(root: Path, suffix: str) -> None:
  for directory in _source_directories(root):
    files = sorted(
      path.name
      for path in directory.iterdir()
      if path.is_file() and path.suffix == suffix
    )
    assert len(files) < FLAT_DIRECTORY_THRESHOLD, (
      f"{directory.relative_to(REPO_ROOT).as_posix()} has {len(files)} "
      f"{suffix} files at one level; split it before reaching "
      f"{FLAT_DIRECTORY_THRESHOLD}: {files}"
    )


def _direct_subdirectories(root: Path) -> frozenset[str]:
  return frozenset(
    path.name
    for path in root.iterdir()
    if path.is_dir() and path.name != "__pycache__"
  )


def test_dto_schemas_use_domain_packages_below_flatness_threshold() -> None:
  assert _direct_subdirectories(SCHEMA_ROOT) == SCHEMA_DOMAINS
  assert sorted(path.name for path in SCHEMA_ROOT.glob("*.py")) == ["__init__.py"]

  for directory in _source_directories(SCHEMA_ROOT):
    if directory != SCHEMA_ROOT:
      assert (directory / "__init__.py").is_file(), (
        f"schema package is missing __init__.py: "
        f"{directory.relative_to(REPO_ROOT).as_posix()}"
      )

  _assert_below_flatness_threshold(SCHEMA_ROOT, ".py")


@pytest.mark.parametrize(("root", "expected_domains"), INC_LAYOUTS)
def test_runtime_detail_includes_use_bounded_domain_directories(
  root: Path,
  expected_domains: frozenset[str],
) -> None:
  assert _direct_subdirectories(root) == expected_domains
  assert not list(root.glob("*.inc")), (
    f"generated includes must live below a domain directory: "
    f"{root.relative_to(REPO_ROOT).as_posix()}"
  )
  _assert_below_flatness_threshold(root, ".inc")


def test_runtime_detail_include_references_resolve() -> None:
  references: list[tuple[Path, str]] = []
  for suffix in ("*.cpp", "*.h"):
    for source in (REPO_ROOT / "src").rglob(suffix):
      text = source.read_text(encoding="utf-8")
      references.extend(
        (source, match.group(1))
        for match in RUNTIME_DETAIL_INCLUDE.finditer(text)
      )

  assert references, "expected maintained runtime detail include references"
  missing = [
    f"{source.relative_to(REPO_ROOT).as_posix()}: {include}"
    for source, include in references
    if not (REPO_ROOT / "src" / include).is_file()
  ]
  assert not missing, "runtime detail includes reference missing files:\n" + "\n".join(
    missing
  )
