"""Freshness gate for the cooperative flight-shaping run-config matrix.

Sibling of ``test_experiment_matrix_freshness.py``: the twelve run-config
files at the active-training root are projections of
``python/experiment/cooperative_flight_matrix.py`` (two config bases plus
per-experiment deltas) and must stay byte-identical to what the generator
produces. Regenerate via
``tools/maintenance/experiment_matrix/generate.py --matrix cooperative_flight --write``.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from python.experiment.cooperative_flight_matrix import (
  COOPERATIVE_CONFIG_BASE_ID,
  P4B_CONFIG_BASE_ID,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "experiment_matrix" / "generate.py"

_MATRIX = "cooperative_flight"
_MATRIX_DIR = "examples/config/training/active"

EXPECTED_OUTPUTS = tuple(
  f"{_MATRIX_DIR}/{stem}.json"
  for stem in (
    "cooperative_cruise_nav_v2_formation_v1",
    "cooperative_interval_takeoff_departure_nav_v1",
    "cooperative_takeoff_to_cruise_landing_hmoe_v1",
    "cooperative_takeoff_to_cruise_landing_hmoe_v1_resume_128k_from_32768",
    "cooperative_takeoff_to_cruise_landing_nav_v1",
    "cooperative_takeoff_to_cruise_nav_hmoe_fair_v1",
    "cooperative_takeoff_to_cruise_nav_hmoe_v1",
    "cooperative_takeoff_to_cruise_nav_shared_fair_v1",
    "cooperative_takeoff_to_cruise_nav_v1",
    "p4b_cruise_to_landing_hmoe_reopen_v1",
    "p4b_cruise_to_landing_hmoe_v1",
    "p4b_cruise_to_landing_shared_reopen_v1",
  )
)

EXPECTED_CONFIG_BASES = (COOPERATIVE_CONFIG_BASE_ID, P4B_CONFIG_BASE_ID)
EXPECTED_PROTOCOLS = {"training_line"}

# Full experiment -> scenario pairing, reviewed against the directory README
# (examples/config/training/active/README.md) when this matrix was brought
# under typed Experiment ownership in this iteration. Per-entry existence
# checks alone cannot detect a swap between two experiments that both point
# at real scenario files; this table pins the complete pairing so a swap is
# a gate failure. Regenerate via
# `generate.py --matrix cooperative_flight --manifest` if the registry's
# scenario assignments change deliberately.
EXPECTED_EXPERIMENT_SCENARIOS: dict[str, str] = {
  "cooperative_cruise_nav_v2_formation_v1": "scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json",
  "cooperative_interval_takeoff_departure_nav_v1": "scenarios/takeoff/cooperative_interval_takeoff_departure_navv2_train_v1.json",
  "cooperative_takeoff_to_cruise_landing_hmoe_v1": "scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json",
  "cooperative_takeoff_to_cruise_landing_hmoe_v1_resume_128k_from_32768": "scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json",
  "cooperative_takeoff_to_cruise_landing_nav_v1": "scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json",
  "cooperative_takeoff_to_cruise_nav_hmoe_fair_v1": "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json",
  "cooperative_takeoff_to_cruise_nav_hmoe_v1": "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json",
  "cooperative_takeoff_to_cruise_nav_shared_fair_v1": "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json",
  "cooperative_takeoff_to_cruise_nav_v1": "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json",
  "p4b_cruise_to_landing_hmoe_reopen_v1": "scenarios/combined/cruise_to_landing_continuous_train_v1.json",
  "p4b_cruise_to_landing_hmoe_v1": "scenarios/combined/cruise_to_landing_continuous_train_v1.json",
  "p4b_cruise_to_landing_shared_reopen_v1": "scenarios/combined/cruise_to_landing_continuous_train_v1.json",
}

# The per-experiment config-base assignment is part of the reviewed surface:
# a lane swap (a p4b entry silently composed from the cooperative base, or
# vice versa) could still render valid JSON.
EXPECTED_EXPERIMENT_BASES: dict[str, str] = {
  experiment_id: (
    P4B_CONFIG_BASE_ID
    if experiment_id.startswith("p4b_")
    else COOPERATIVE_CONFIG_BASE_ID
  )
  for experiment_id in EXPECTED_EXPERIMENT_SCENARIOS
}


def _run_generator(*args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(GENERATOR), "--matrix", _MATRIX, *args],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )


def test_cooperative_flight_matrix_outputs_are_fresh_and_registered(tmp_path: Path) -> None:
  check_result = _run_generator("--check")
  assert check_result.returncode == 0, (
    "the cooperative flight-shaping matrix drifted from its Experiment "
    "definition (python/experiment/cooperative_flight_matrix.py):\n"
    f"{check_result.stdout}{check_result.stderr}"
  )

  manifest_result = _run_generator("--manifest")
  assert manifest_result.returncode == 0, (
    "cooperative flight matrix manifest generation failed:\n"
    f"{manifest_result.stdout}{manifest_result.stderr}"
  )
  manifest = json.loads(manifest_result.stdout)
  assert manifest["matrix"] == _MATRIX
  assert manifest["config_bases"] == list(EXPECTED_CONFIG_BASES)
  assert manifest["matrix_dir"] == _MATRIX_DIR

  entries = manifest["entries"]
  outputs = [entry["output"] for entry in entries]
  assert sorted(outputs) == sorted(EXPECTED_OUTPUTS)
  assert len(set(outputs)) == len(outputs)

  experiment_ids = [entry["experiment_id"] for entry in entries]
  assert len(set(experiment_ids)) == len(experiment_ids)
  for entry in entries:
    assert entry["output"] == f"{_MATRIX_DIR}/{entry['experiment_id']}.json"
    assert entry["config_base"] in EXPECTED_CONFIG_BASES
    assert entry["evaluation_protocol"] in EXPECTED_PROTOCOLS
    assert entry["seeds"] == []
    assert (REPO_ROOT / entry["scenario"]).is_file(), entry["scenario"]

  experiment_scenarios = {entry["experiment_id"]: entry["scenario"] for entry in entries}
  assert experiment_scenarios == EXPECTED_EXPERIMENT_SCENARIOS, (
    "an Experiment -> scenario pairing drifted from the reviewed mapping; "
    "per-entry existence checks cannot catch a swap between two experiments "
    "that both reference real scenario files"
  )

  experiment_bases = {entry["experiment_id"]: entry["config_base"] for entry in entries}
  assert experiment_bases == EXPECTED_EXPERIMENT_BASES, (
    "an Experiment -> config-base assignment drifted from the reviewed "
    "two-lane mapping (cooperative flight-shaping vs p4b cruise-to-landing)"
  )

  on_disk = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in (REPO_ROOT / _MATRIX_DIR).glob("*.json")
  }
  assert on_disk == set(EXPECTED_OUTPUTS), (
    "the active-training root and the Experiment registry must list the "
    "same files; register new entries instead of adding unmanaged configs"
  )

  isolated_root = tmp_path / "checkout"
  for path in EXPECTED_OUTPUTS:
    source = REPO_ROOT / path
    target = isolated_root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())

  clean_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert clean_result.returncode == 0, (
    "isolated artifact copy should be fresh; a stale entry here means the "
    "registry does not cover every generated file:\n"
    f"{clean_result.stdout}{clean_result.stderr}"
  )

  stale_path = isolated_root / EXPECTED_OUTPUTS[0]
  original = stale_path.read_bytes()
  modified = original.replace(b'"total_timesteps": 65536', b'"total_timesteps": 65537', 1)
  assert modified != original
  stale_path.write_bytes(modified)

  stale_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert stale_result.returncode == 1
  assert f"stale: {EXPECTED_OUTPUTS[0]}" in stale_result.stdout
  assert '-  "total_timesteps": 65537,' in stale_result.stdout
  assert '+  "total_timesteps": 65536,' in stale_result.stdout

  stale_path.write_bytes(original)
  restored_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert restored_result.returncode == 0


def test_default_generator_surface_still_owns_the_air_combat_matrix() -> None:
  """Adding a second matrix must not steer the pre-existing default: a bare
  ``--manifest`` (no ``--matrix``) still projects the air-combat registry."""
  result = subprocess.run(
    [sys.executable, str(GENERATOR), "--manifest"],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  manifest = json.loads(result.stdout)
  assert manifest["matrix"] == "air_combat"
  assert manifest["config_base"] == "air_combat_1v1_hmoe_execution_v1"
  assert manifest["matrix_dir"] == "examples/config/training/active/air_combat"
