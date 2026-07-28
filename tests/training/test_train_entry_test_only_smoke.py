from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

REPO_ROOT = Path(__file__).resolve().parents[2]

SMOKE_SCENARIO = {
  "scenario_name": "train_entry_test_only_world_batch_smoke",
  "meta": {"max_steps": 2},
  "environment": {
    "time_step": 0.05,
    "terrain_type": "flat",
    "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
  },
  "mission_command": {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "waypoints": [{"x": 3000.0, "y": 0.0, "z": 1200.0}],
  },
  "entities": [
    {
      "name": "Lead",
      "type": "Aircraft",
      "side": "Blue",
      "is_agent": True,
      "pos": [0.0, 0.0, 1200.0],
      "vel": [0.0, 180.0, 0.0],
      "heading": 90.0,
    }
  ],
}

SMOKE_TRAIN_CONFIG = {
  "agent_layer": "execution",
  "algo": "PPO",
  "policy": "MultiInputPolicy",
  "total_timesteps": 2,
  "n_envs": 1,
  "env": {
    "include_visual": False,
    "include_proprio": True,
    "mission_obs_mode": "nav_v2",
    "execution_step_runtime_mode": "compiled",
    "step_info_mode": "terminal",
    "action_mode": "full",
  },
  "runtime": {
    "world_batch_vec_env": True,
    "world_batch_threads": 1,
    "batch_observation_backend": "compiled",
    "batch_visual_backend": "compiled",
  },
  "hyperparameters": {
    "learning_rate": 3.0e-4,
    "n_steps": 2,
    "batch_size": 2,
    "n_epochs": 1,
    "gamma": 0.99,
    "device": "cpu",
  },
}


class TrainEntryTestOnlySmokeTests(unittest.TestCase):
  def test_execution_test_only_runs_world_batch_vec_env_from_factory(self) -> None:
    """`--test_only` must build the world-batch execution env via the factory and step it."""
    from stable_baselines3 import PPO

    from python.env_config import resolve_env_settings
    from python.training.vec_env_factory import build_execution_world_batch_vec_env

    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = Path(tmpdir) / "scenario.json"
      config_path = Path(tmpdir) / "train_config.json"
      output_base = Path(tmpdir) / "runs"
      run_name = "test_only_smoke"
      exp_dir = output_base / run_name
      exp_dir.mkdir(parents=True)
      scenario_path.write_text(json.dumps(SMOKE_SCENARIO, ensure_ascii=True), encoding="utf-8")
      config_path.write_text(json.dumps(SMOKE_TRAIN_CONFIG, ensure_ascii=True), encoding="utf-8")

      cli_overrides = SimpleNamespace(
        include_visual=None,
        include_proprio=None,
        action_mode=None,
        mission_obs_mode=None,
        visual_downsample=None,
        visual_update_interval=None,
        temporal_history_len=None,
      )
      bootstrap = SimpleNamespace(
        train_config=SMOKE_TRAIN_CONFIG,
        runtime_cfg=dict(SMOKE_TRAIN_CONFIG["runtime"]),
        env_settings=resolve_env_settings(SMOKE_TRAIN_CONFIG, cli_overrides),
        scenario_path=str(scenario_path),
        n_envs=1,
        training_seed=20260719,
      )
      vec_env = build_execution_world_batch_vec_env(bootstrap)
      self.assertIsNotNone(vec_env)
      try:
        model = PPO("MultiInputPolicy", vec_env, n_steps=2, batch_size=2, device="cpu")
        model.save(str(exp_dir / "final_model"))
      finally:
        vec_env.close()

      proc = subprocess.run(
        [
          sys.executable,
          str(REPO_ROOT / "train.py"),
          "--scenario",
          str(scenario_path),
          "--train_config",
          str(config_path),
          "--output_base",
          str(output_base),
          "--run_name",
          run_name,
          "--test_only",
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=dict(os.environ),
      )

      self.assertEqual(proc.returncode, 0, msg=proc.stdout)
      self.assertIn("Agent layer: execution", proc.stdout)
      self.assertIn("World batch runtime:", proc.stdout)
      self.assertIn("Loading model for testing:", proc.stdout)
      self.assertIn("Step 0:", proc.stdout)
      self.assertIn("Episode Done.", proc.stdout)
      self.assertNotIn("Traceback", proc.stdout)


if __name__ == "__main__":
  unittest.main()
