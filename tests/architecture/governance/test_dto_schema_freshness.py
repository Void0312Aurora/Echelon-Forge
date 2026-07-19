from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "dto_schema" / "generate.py"
SCHEMAS_DIR = GENERATOR.parent / "schemas"

EXPECTED_REGISTRATIONS = {
  "tools/maintenance/dto_schema/schemas/effects_event_fields.py": (
    "src/runtime/contracts/detail/effects_event_fields.inc",
    135,
  ),
  "tools/maintenance/dto_schema/schemas/flight_shaping_shared_fields.py": (
    "src/core/mission/runtime/detail/flight_shaping_shared_fields.inc",
    89,
  ),
}


def _run_generator(*args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(GENERATOR), *args],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )


def test_dto_schema_generated_outputs_are_fresh_and_registered(
  tmp_path: Path,
) -> None:
  check_result = _run_generator("--check")
  assert check_result.returncode == 0, (
    "DTO schema outputs are stale or the generator failed:\n"
    f"{check_result.stdout}{check_result.stderr}"
  )

  manifest_result = _run_generator("--manifest")
  assert manifest_result.returncode == 0, (
    "DTO schema manifest generation failed:\n"
    f"{manifest_result.stdout}{manifest_result.stderr}"
  )
  manifest = json.loads(manifest_result.stdout)
  entries = manifest["schemas"]

  registrations = {
    entry["schema"]: (entry["output"], entry["field_count"])
    for entry in entries
  }
  assert registrations == EXPECTED_REGISTRATIONS
  assert len({entry["output"] for entry in entries}) == len(entries)

  schema_modules = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in SCHEMAS_DIR.glob("*.py")
    if path.name != "__init__.py"
  }
  assert schema_modules == set(registrations)
  assert all(REPO_ROOT.joinpath(entry["output"]).is_file() for entry in entries)

  isolated_root = tmp_path / "checkout"
  for entry in entries:
    source = REPO_ROOT / entry["output"]
    target = isolated_root / entry["output"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())

  stale_path = isolated_root / EXPECTED_REGISTRATIONS[
    "tools/maintenance/dto_schema/schemas/flight_shaping_shared_fields.py"
  ][0]
  original = stale_path.read_bytes()
  modified = original.replace(
    b"EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 0.0)",
    b"EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 1.0)",
    1,
  )
  assert modified != original
  stale_path.write_bytes(modified)

  stale_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert stale_result.returncode == 1
  assert (
    "stale: src/core/mission/runtime/detail/flight_shaping_shared_fields.inc"
    in stale_result.stdout
  )
  assert "-EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 1.0)" in (
    stale_result.stdout
  )
