from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from python.experiment.air_combat_matrix import CONFIG_BASE_ID, MATRIX_DIR, MatrixEntry, RenderStyle
from python.experiment.definition import ConfigComposition, Experiment, ScenarioRef, SeedSpec
from tools.maintenance.experiment_matrix import generate as experiment_matrix_generate

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "experiment_matrix" / "generate.py"

_MATRIX_DIR = "examples/config/training/active/air_combat"

EXPECTED_OUTPUTS = tuple(
  f"{_MATRIX_DIR}/{stem}.json"
  for stem in (
    "air_combat_1v1_f16c_scripted_red_smoke_v1",
    "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1",
    "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1",
    "air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1",
    "air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1",
    "air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1",
    "air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1",
    "air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_state_completed_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1",
    "air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1",
  )
)

EXPECTED_CONFIG_BASE = "air_combat_1v1_hmoe_execution_v1"
EXPECTED_PROTOCOLS = {"smoke", "probe"}

# Full experiment -> scenario pairing, reviewed against the registry's actual
# values (python/experiment/air_combat_matrix.py) at I36. Per-entry existence
# checks alone cannot detect a swap between two experiments that both point at
# real scenario files; this table pins the complete pairing so a swap is a
# gate failure. Regenerate via `generate.py --manifest` if the registry's
# scenario assignments change deliberately.
EXPECTED_EXPERIMENT_SCENARIOS: dict[str, str] = {
  "air_combat_1v1_f16c_scripted_red_smoke_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_f16c_scripted_red_world_batch_probe_8k_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_f16c_scripted_red_world_batch_smoke_v1": "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json",
  "air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json",
  "air_combat_1v1_stage0_drone_weapon_employment_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage0_drone_weapon_employment_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_credit_launch_window_state_completed_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_grouped_stopping_state_completed_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
  "air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
  "air_combat_1v1_stage2_evasive_fighter_c2_roe_hybrid_temporal_event_window_state_completed_world_batch_probe_v1": "scenarios/air_combat/1v1/air_combat_1v1_stage2_evasive_fighter_c2_roe_training_shaped_v1.json",
}


def _run_generator(*args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(GENERATOR), *args],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )


def test_experiment_matrix_outputs_are_fresh_and_registered(tmp_path: Path) -> None:
  check_result = _run_generator("--check")
  assert check_result.returncode == 0, (
    "the air-combat matrix drifted from its Experiment definition "
    "(python/experiment/air_combat_matrix.py):\n"
    f"{check_result.stdout}{check_result.stderr}"
  )

  manifest_result = _run_generator("--manifest")
  assert manifest_result.returncode == 0, (
    "experiment matrix manifest generation failed:\n"
    f"{manifest_result.stdout}{manifest_result.stderr}"
  )
  manifest = json.loads(manifest_result.stdout)
  assert manifest["config_base"] == EXPECTED_CONFIG_BASE
  assert manifest["matrix_dir"] == _MATRIX_DIR

  entries = manifest["entries"]
  outputs = [entry["output"] for entry in entries]
  assert sorted(outputs) == sorted(EXPECTED_OUTPUTS)
  assert len(set(outputs)) == len(outputs)

  experiment_ids = [entry["experiment_id"] for entry in entries]
  assert len(set(experiment_ids)) == len(experiment_ids)
  for entry in entries:
    assert entry["output"] == f"{_MATRIX_DIR}/{entry['experiment_id']}.json"
    assert entry["config_base"] == EXPECTED_CONFIG_BASE
    assert entry["evaluation_protocol"] in EXPECTED_PROTOCOLS
    assert entry["seeds"] == []
    assert (REPO_ROOT / entry["scenario"]).is_file(), entry["scenario"]

  experiment_scenarios = {entry["experiment_id"]: entry["scenario"] for entry in entries}
  assert experiment_scenarios == EXPECTED_EXPERIMENT_SCENARIOS, (
    "an Experiment -> scenario pairing drifted from the reviewed mapping; "
    "per-entry existence checks cannot catch a swap between two experiments "
    "that both reference real scenario files"
  )

  on_disk = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in (REPO_ROOT / _MATRIX_DIR).glob("*.json")
  }
  assert on_disk == set(EXPECTED_OUTPUTS), (
    "the matrix directory and the Experiment registry must list the same "
    "files; register new entries instead of adding unmanaged configs"
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
  modified = original.replace(b'"total_timesteps": 512', b'"total_timesteps": 513', 1)
  assert modified != original
  stale_path.write_bytes(modified)

  stale_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert stale_result.returncode == 1
  assert f"stale: {EXPECTED_OUTPUTS[0]}" in stale_result.stdout
  assert '-  "total_timesteps": 513,' in stale_result.stdout
  assert '+  "total_timesteps": 512,' in stale_result.stdout

  stale_path.write_bytes(original)
  restored_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert restored_result.returncode == 0


def test_experiment_scenario_pairing_swap_is_caught_only_by_the_full_table() -> None:
  """I30 review residual: existence-only checks miss a scenario swap.

  Two experiments that each reference a real, existing scenario file can be
  swapped without any single-entry ``is_file()`` check going red. Only the
  complete experiment -> scenario pairing table (asserted in the freshness
  test above) detects the drift.
  """
  first_id = "air_combat_1v1_f16c_scripted_red_smoke_v1"
  second_id = "air_combat_1v1_stage0_drone_weapon_employment_temporal_world_batch_probe_v1"
  assert (
    EXPECTED_EXPERIMENT_SCENARIOS[first_id] != EXPECTED_EXPERIMENT_SCENARIOS[second_id]
  )

  swapped = dict(EXPECTED_EXPERIMENT_SCENARIOS)
  swapped[first_id], swapped[second_id] = swapped[second_id], swapped[first_id]

  for scenario in (swapped[first_id], swapped[second_id]):
    assert (REPO_ROOT / scenario).is_file(), scenario

  assert swapped != EXPECTED_EXPERIMENT_SCENARIOS


def _synthetic_matrix_entry(
  experiment_id: str,
  delta: dict[str, object],
  render: RenderStyle,
) -> MatrixEntry:
  experiment = Experiment(
    experiment_id,
    ScenarioRef("scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"),
    ConfigComposition(CONFIG_BASE_ID, delta),
    SeedSpec(),
    "probe",
  )
  return MatrixEntry(
    experiment=experiment,
    output_path=f"{MATRIX_DIR}/{experiment_id}.json",
    render=render,
  )


def test_generator_escapes_object_keys_containing_quotes() -> None:
  """I30 review residual: object keys serialized without ``json.dumps``.

  A hand-written ``f'"{key}"'`` interpolation (the pre-fix approach) produces
  illegal JSON for any key containing a quote character.
  """
  key = 'weird "quoted" key'
  entry = _synthetic_matrix_entry(
    "synthetic_quote_key_probe_v1",
    {key: 1},
    RenderStyle(),
  )

  rendered = experiment_matrix_generate.render_entry_bytes(entry).decode("utf-8")
  parsed = json.loads(rendered)
  assert parsed[key] == 1

  naive_key_fragment = '"' + key + '"'
  with pytest.raises(json.JSONDecodeError):
    json.loads("{" + naive_key_fragment + ": 1}")


def test_generator_literal_override_rejects_type_drifted_scalars() -> None:
  """I30 review residual: literal-override comparison ignored scalar type.

  ``json.loads(literal) != value`` alone would accept a boolean literal
  override for an int field (or vice versa) because Python's ``==`` treats
  ``True == 1``. The generator must reject the mismatch instead.
  """
  assert json.loads("true") == 1

  entry = _synthetic_matrix_entry(
    "synthetic_literal_drift_probe_v1",
    {"synthetic_flag": 1},
    RenderStyle(literal_overrides={("synthetic_flag",): "true"}),
  )

  with pytest.raises(ValueError, match="does not equal the composed"):
    experiment_matrix_generate.render_entry_bytes(entry)
