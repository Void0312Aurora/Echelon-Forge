from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from python.training import build_train_arg_parser, prepare_training_bootstrap


class TrainBootstrapTests(unittest.TestCase):
    def test_prepare_training_bootstrap_sets_run_layout_and_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scenario_path = root / "scenario.json"
            train_config_path = root / "train.json"
            output_base = root / "runs"

            scenario = {
                "scenario_name": "bootstrap_smoke",
                "meta": {"max_steps": 2},
                "environment": {
                    "time_step": 0.05,
                    "terrain_type": "flat",
                    "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
                },
                "mission_command": {
                    "command_code": 2,
                    "target_heading": 90.0,
                    "target_altitude": 1200.0,
                    "target_speed": 180.0,
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
            train_cfg = {
                "agent_layer": "execution",
                "policy": "MultiInputPolicy",
                "n_envs": 3,
                "seed": 1234,
                "env": {
                    "include_proprio": True,
                    "mission_obs_mode": "nav_v2",
                    "step_info_mode": "terminal",
                    "action_mode": "takeoff4",
                },
                "runtime": {
                    "torch_threads": 1,
                },
                "hyperparameters": {
                    "n_steps": 8,
                },
            }
            scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
            train_config_path.write_text(json.dumps(train_cfg, ensure_ascii=True), encoding="utf-8")

            parser = build_train_arg_parser()
            args = parser.parse_args(
                [
                    "--scenario",
                    str(scenario_path),
                    "--train_config",
                    str(train_config_path),
                    "--output_base",
                    str(output_base),
                    "--run_name",
                    "bootstrap_case",
                ]
            )
            bootstrap = prepare_training_bootstrap(args)

            self.assertIsNotNone(bootstrap)
            assert bootstrap is not None
            self.assertEqual(bootstrap.agent_layer, "execution")
            self.assertEqual(bootstrap.run_name, "bootstrap_case")
            self.assertEqual(Path(bootstrap.exp_dir), output_base / "bootstrap_case")
            self.assertEqual(Path(bootstrap.ckpt_dir), output_base / "bootstrap_case" / "checkpoints")
            self.assertEqual(Path(bootstrap.log_dir), output_base / "bootstrap_case" / "logs")
            self.assertEqual(bootstrap.n_envs, 3)
            self.assertEqual(bootstrap.training_seed, 1234)
            self.assertIsNotNone(bootstrap.env_settings)
            self.assertTrue((output_base / "bootstrap_case" / "train_config_backup.json").exists())
            self.assertTrue((output_base / "bootstrap_case" / "scenario_backup.json").exists())
            bootstrap.exp_lock.close()


if __name__ == "__main__":
    unittest.main()
