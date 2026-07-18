from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

REPO_ROOT = Path(__file__).resolve().parents[2]

SMOKE_SCENARIO = {
  "scenario_name": "evaluate_entry_world_batch_smoke",
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
}


class EvaluateEntrySmokeTests(unittest.TestCase):
  def test_evaluate_entry_loads_model_via_shared_loader_and_runs_episode(self) -> None:
    """`evaluate.py` must load checkpoints through `load_sb3_policy` and complete a run."""
    from stable_baselines3 import PPO

    from evaluate import _build_evaluation_env
    from python.rl.control.wrappers import get_action_wrapper_spec

    with tempfile.TemporaryDirectory() as tmpdir:
      scenario_path = Path(tmpdir) / "scenario.json"
      config_path = Path(tmpdir) / "train_config.json"
      model_path = Path(tmpdir) / "final_model.zip"
      scenario_path.write_text(json.dumps(SMOKE_SCENARIO, ensure_ascii=True), encoding="utf-8")
      config_path.write_text(json.dumps(SMOKE_TRAIN_CONFIG, ensure_ascii=True), encoding="utf-8")

      wrapper_class, wrapper_kwargs = get_action_wrapper_spec(SMOKE_TRAIN_CONFIG)
      env = _build_evaluation_env(
        str(scenario_path),
        dict(SMOKE_TRAIN_CONFIG["env"]),
        wrapper_class=wrapper_class,
        wrapper_kwargs=wrapper_kwargs,
        worker_threads=1,
      )
      try:
        model = PPO("MultiInputPolicy", env, n_steps=2, batch_size=2, device="cpu")
        model.save(str(model_path)[: -len(".zip")])
      finally:
        env.close()

      proc = subprocess.run(
        [
          sys.executable,
          str(REPO_ROOT / "evaluate.py"),
          "--scenario",
          str(scenario_path),
          "--model",
          str(model_path),
          "--train_config",
          str(config_path),
          "--episodes",
          "1",
          "--seed",
          "20260719",
        ],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=dict(os.environ),
      )

      self.assertEqual(proc.returncode, 0, msg=proc.stdout)
      self.assertNotIn("Error loading model", proc.stdout)
      self.assertIn("EVALUATION SUMMARY", proc.stdout)
      self.assertIn("Episode 1/1", proc.stdout)


if __name__ == "__main__":
  unittest.main()
