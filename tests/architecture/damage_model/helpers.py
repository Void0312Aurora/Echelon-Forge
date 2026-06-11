from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from tests.architecture.helpers import PYTHON_EXECUTABLE, REPO_ROOT


EXPECTED_BECO_SHA256 = (
  "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
)
EXPECTED_TP20_SHA256 = (
  "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f"
)
EXPECTED_TP21_SHA256 = (
  "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
)

HEX64 = re.compile(r"^[a-f0-9]{64}$")


def assert_hex64(value: str) -> None:
  assert HEX64.fullmatch(value)


def walk_payload(payload: Any) -> list[Any]:
  values = [payload]
  if isinstance(payload, dict):
    for value in payload.values():
      values.extend(walk_payload(value))
  elif isinstance(payload, list):
    for value in payload:
      values.extend(walk_payload(value))
  return values


def assert_authority_guards_false(
  payload: dict[str, Any],
  *,
  guards_key: str = "authority_guards",
) -> None:
  if "authority_guards_all_false" in payload:
    assert payload["authority_guards_all_false"] is True
  assert not any(payload[guards_key].values())


def assert_no_keys_anywhere(payload: Any, forbidden_keys: set[str]) -> None:
  for value in walk_payload(payload):
    if isinstance(value, dict):
      assert not (forbidden_keys & set(value))


def run_maintenance_cli(
  script: str,
  *args: str | Path,
  capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
  script_args = shlex.split(script)
  return subprocess.run(
    [
      PYTHON_EXECUTABLE,
      f"tools/maintenance/{script_args[0]}",
      *script_args[1:],
      *(str(arg) for arg in args),
    ],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    capture_output=capture_output,
  )


def run_maintenance_json_cli(script: str, *args: str | Path) -> Any:
  return json.loads(run_maintenance_cli(script, *args).stdout)


def assert_retained_manifest_clean(
  integrity_module: Any,
  manifest_path: Path,
) -> dict[str, Any]:
  summary = integrity_module.check_retained_manifest_integrity(
    manifest_paths=[manifest_path],
  )
  assert summary["missing_total"] == 0
  assert summary["sha_mismatch_total"] == 0
  assert summary["guard_true_total"] == 0
  return summary
