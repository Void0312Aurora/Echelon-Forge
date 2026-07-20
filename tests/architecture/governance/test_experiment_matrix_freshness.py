from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


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
