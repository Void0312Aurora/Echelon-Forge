from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PRIMARY_LANES = {"fast", "qualification", "nightly", "release", "research"}


def _configured_build() -> Path | None:
  candidates: list[Path] = []
  configured = os.environ.get("CMO_BUILD_DIR")
  if configured:
    candidates.append(Path(configured))
  candidates.extend(
    REPO_ROOT / name
    for name in ("build-workshop", "build-long-horizon-p5c-shared", "build")
  )
  for candidate in candidates:
    path = candidate if candidate.is_absolute() else REPO_ROOT / candidate
    if (path / "CTestTestfile.cmake").is_file():
      return path
  return None


def _ctest_inventory() -> list[dict[str, object]]:
  build = _configured_build()
  ctest = shutil.which("ctest")
  if build is None or ctest is None:
    pytest.skip("a configured CTest build and ctest executable are required")
  result = subprocess.run(
    [ctest, "--test-dir", str(build), "-N", "-C", "Release", "--show-only=json-v1"],
    cwd=REPO_ROOT,
    capture_output=True,
    text=True,
    check=False,
  )
  assert result.returncode == 0, f"ctest inventory failed:\n{result.stdout}\n{result.stderr}"
  payload = json.loads(result.stdout)
  tests = payload.get("tests")
  assert isinstance(tests, list) and tests, "configured CTest inventory is empty"
  return [row for row in tests if isinstance(row, dict)]


def _labels(row: dict[str, object]) -> set[str]:
  labels: set[str] = set()
  properties = row.get("properties", [])
  for item in properties if isinstance(properties, list) else []:
    if not isinstance(item, dict) or item.get("name") != "LABELS":
      continue
    value = item.get("value")
    if isinstance(value, list):
      labels.update(str(label) for label in value)
    elif value is not None:
      labels.add(str(value))
  return labels


def test_every_native_ctest_entry_declares_one_primary_lane() -> None:
  tests = _ctest_inventory()
  assert tests
  missing: list[str] = []
  invalid: list[tuple[str, list[str]]] = []
  for row in tests:
    name = str(row.get("name", ""))
    labels = _labels(row)
    if not labels & PRIMARY_LANES:
      missing.append(name)
    if not labels:
      invalid.append((name, sorted(labels)))
  assert not missing, f"CTest entries without a primary lane label: {missing}"
  assert not invalid, f"CTest entries without labels: {invalid}"


def test_native_lane_labels_cover_the_declared_lane_audiences() -> None:
  tests = _ctest_inventory()
  labels: set[str] = set()
  for row in tests:
    labels.update(_labels(row))
  assert PRIMARY_LANES <= labels
  assert "native" in labels
