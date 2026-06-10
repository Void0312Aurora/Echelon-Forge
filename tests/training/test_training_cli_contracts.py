from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TrainingCliContractTests(unittest.TestCase):
    def test_train_py_accepts_cooperative_execution_agent_layer(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir) / "cooperative_scenario.json"
            config_path = Path(tmpdir) / "cooperative_train.json"

            scenario = {
                "scenario_name": "train_entry_cooperative_smoke",
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
                    "formation_id": 17,
                    "form_offset_x": 180.0,
                    "form_offset_y": -90.0,
                    "form_offset_z": 30.0,
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
                    },
                    {
                        "name": "Wing",
                        "type": "Aircraft",
                        "side": "Blue",
                        "is_agent": True,
                        "pos": [-120.0, -180.0, 1200.0],
                        "vel": [0.0, 180.0, 0.0],
                        "heading": 90.0,
                    },
                ],
                "cooperative_roster": {
                    "policy_route": "shared_execution",
                    "members": [
                        {"entity": "Lead", "policy_route": "shared_execution"},
                        {"entity": "Wing", "reference_entity": "Lead", "policy_route": "shared_execution"},
                    ],
                },
            }
            train_cfg = {
                "agent_layer": "cooperative_execution",
                "algo": "PPO",
                "policy": "MultiInputPolicy",
                "total_timesteps": 1,
                "n_envs": 1,
                "env": {
                    "include_proprio": True,
                    "mission_obs_mode": "nav_v2_formation_role_v1",
                    "step_info_mode": "terminal",
                    "action_mode": "full",
                },
                "runtime": {
                    "batch_observation_backend": "compiled",
                    "batch_visual_backend": "compiled",
                },
                "hyperparameters": {
                    "learning_rate": 3.0e-4,
                    "n_steps": 1,
                    "batch_size": 1,
                    "n_epochs": 1,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "clip_range": 0.2,
                    "normalize_advantage": True,
                    "ent_coef": 0.0,
                    "vf_coef": 0.5,
                    "max_grad_norm": 0.5,
                    "device": "cpu",
                },
            }
            scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
            config_path.write_text(json.dumps(train_cfg, ensure_ascii=True), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "train.py"),
                    "--scenario",
                    str(scenario_path),
                    "--train_config",
                    str(config_path),
                    "--test_only",
                ],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            self.assertNotIn("unknown agent_layer", proc.stdout)
            self.assertIn("Cooperative observation runtime:", proc.stdout)

    def test_train_py_accepts_nonfinite_probe_flag_in_training_mode(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir) / "cooperative_scenario.json"
            config_path = Path(tmpdir) / "cooperative_train.json"
            output_base = Path(tmpdir) / "runs"

            scenario = {
                "scenario_name": "train_entry_cooperative_probe_smoke",
                "meta": {"max_steps": 4},
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
                    "formation_id": 17,
                    "form_offset_x": 180.0,
                    "form_offset_y": -90.0,
                    "form_offset_z": 30.0,
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
                    },
                    {
                        "name": "Wing",
                        "type": "Aircraft",
                        "side": "Blue",
                        "is_agent": True,
                        "pos": [-120.0, -180.0, 1200.0],
                        "vel": [0.0, 180.0, 0.0],
                        "heading": 90.0,
                    },
                ],
                "cooperative_roster": {
                    "policy_route": "shared_execution",
                    "members": [
                        {"entity": "Lead", "policy_route": "shared_execution"},
                        {"entity": "Wing", "reference_entity": "Lead", "policy_route": "shared_execution"},
                    ],
                },
            }
            train_cfg = {
                "agent_layer": "cooperative_execution",
                "algo": "PPO",
                "policy": "SquashedMultiInputPolicy",
                "total_timesteps": 2,
                "n_envs": 1,
                "env": {
                    "include_proprio": True,
                    "mission_obs_mode": "nav_v2_formation_role_v1",
                    "step_info_mode": "terminal",
                    "action_mode": "full",
                },
                "runtime": {
                    "batch_observation_backend": "compiled",
                    "batch_visual_backend": "compiled",
                },
                "hyperparameters": {
                    "learning_rate": 3.0e-4,
                    "n_steps": 2,
                    "batch_size": 2,
                    "n_epochs": 1,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "clip_range": 0.2,
                    "normalize_advantage": True,
                    "ent_coef": 0.0,
                    "vf_coef": 0.5,
                    "max_grad_norm": 0.5,
                    "device": "cpu",
                    "policy_kwargs": {
                        "features_extractor_class": "TransformerExtractor",
                        "features_extractor_kwargs": {
                            "features_dim": 64,
                            "n_heads": 4,
                            "n_layers": 1,
                            "use_amp": False,
                            "use_checkpointing": False,
                        },
                        "net_arch": {"pi": [64], "vf": [64]},
                    },
                },
            }
            scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
            config_path.write_text(json.dumps(train_cfg, ensure_ascii=True), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "train.py"),
                    "--scenario",
                    str(scenario_path),
                    "--train_config",
                    str(config_path),
                    "--nonfinite_probe",
                    "--output_base",
                    str(output_base),
                    "--run_name",
                    "probe_smoke",
                ],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            self.assertNotIn("unknown agent_layer", proc.stdout)
            self.assertIn("Cooperative observation runtime:", proc.stdout)
            self.assertIn("Non-finite probe: enabled=1", proc.stdout)

    def test_train_py_accepts_hmoe_execution_policy_name(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir) / "cooperative_scenario.json"
            config_path = Path(tmpdir) / "cooperative_train.json"

            scenario = {
                "scenario_name": "train_entry_hmoe_policy_smoke",
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
                    "formation_id": 17,
                    "form_offset_x": 180.0,
                    "form_offset_y": -90.0,
                    "form_offset_z": 30.0,
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
                    },
                    {
                        "name": "Wing",
                        "type": "Aircraft",
                        "side": "Blue",
                        "is_agent": True,
                        "pos": [-120.0, -180.0, 1200.0],
                        "vel": [0.0, 180.0, 0.0],
                        "heading": 90.0,
                    },
                ],
                "cooperative_roster": {
                    "policy_route": "shared_execution",
                    "members": [
                        {"entity": "Lead", "policy_route": "shared_execution"},
                        {"entity": "Wing", "reference_entity": "Lead", "policy_route": "shared_execution"},
                    ],
                },
            }
            train_cfg = {
                "agent_layer": "cooperative_execution",
                "algo": "PPO",
                "policy": "HierarchicalMoEExecutionPolicy",
                "total_timesteps": 2,
                "n_envs": 1,
                "env": {
                    "include_proprio": True,
                    "mission_obs_mode": "nav_v2_formation_role_v1",
                    "step_info_mode": "terminal",
                    "action_mode": "full",
                },
                "runtime": {
                    "batch_observation_backend": "compiled",
                    "batch_visual_backend": "compiled",
                },
                "hyperparameters": {
                    "learning_rate": 3.0e-4,
                    "n_steps": 2,
                    "batch_size": 2,
                    "n_epochs": 1,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "clip_range": 0.2,
                    "normalize_advantage": True,
                    "ent_coef": 0.0,
                    "vf_coef": 0.5,
                    "max_grad_norm": 0.5,
                    "device": "cpu",
                    "policy_kwargs": {
                        "features_extractor_class": "TransformerExtractor",
                        "features_extractor_kwargs": {
                            "features_dim": 64,
                            "n_heads": 4,
                            "n_layers": 1,
                            "use_amp": False,
                            "use_checkpointing": False,
                        },
                        "net_arch": {"pi": [64], "vf": [64]},
                    },
                },
            }
            scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")
            config_path.write_text(json.dumps(train_cfg, ensure_ascii=True), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "train.py"),
                    "--scenario",
                    str(scenario_path),
                    "--train_config",
                    str(config_path),
                    "--test_only",
                ],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            self.assertNotIn("unknown agent_layer", proc.stdout)
            self.assertIn("Cooperative observation runtime:", proc.stdout)


if __name__ == "__main__":
    unittest.main()
