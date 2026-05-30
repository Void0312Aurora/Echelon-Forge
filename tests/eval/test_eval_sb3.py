from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from argparse import Namespace
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports
from tools.eval.eval_sb3 import _build_single_env
from tools.eval.sb3_eval_base import load_sb3_policy


ensure_repo_imports()


class EvalSB3Tests(unittest.TestCase):
    def test_single_eval_builds_world_batch_runtime_for_maintained_execution_entry(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        train_config_path = repo_root / "examples" / "config" / "training" / "frozen" / "execution" / "p3_takeoff_to_cruise_retrain_v1.json"
        train_config = json.loads(train_config_path.read_text(encoding="utf-8"))

        scenario = {
            "scenario_name": "eval_sb3_single_world_batch_smoke",
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

        args = Namespace(
            include_visual=None,
            include_proprio=None,
            action_mode=None,
            mission_obs_mode=None,
            visual_downsample=None,
            visual_update_interval=None,
            temporal_history_len=None,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir) / "scenario.json"
            scenario_path.write_text(json.dumps(scenario, ensure_ascii=True), encoding="utf-8")

            env, env_settings = _build_single_env(str(scenario_path), train_config, args)
            try:
                self.assertTrue(bool(train_config.get("runtime", {}).get("world_batch_vec_env")))
                self.assertEqual(env_settings.get("execution_step_runtime_mode"), "compiled")
                handle = getattr(env, "_handle", env)
                self.assertIsNotNone(getattr(handle, "world_vec", None))
            finally:
                env.close()

    def test_load_sb3_policy_supports_historical_shared_and_hmoe_models(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        cases = [
            (
                repo_root / "experiments" / "coop_takeoff_to_cruise_landing_formal_20260514" / "final_model.zip",
                "SquashedMultiInputPolicy",
            ),
            (
                repo_root
                / "experiments"
                / "20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1"
                / "checkpoints"
                / "model_130048_steps.zip",
                "HierarchicalMoEExecutionPolicy",
            ),
        ]

        for model_path, expected_policy_name in cases:
            if not model_path.exists():
                self.skipTest(f"historical checkpoint is not present: {model_path}")
            model = load_sb3_policy(str(model_path), algo="auto", device="cpu")
            self.assertEqual(type(model.policy).__name__, expected_policy_name)

    def test_tool_reports_slot_summary_for_cooperative_policy(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        model_path = repo_root / "experiments" / "coop_cruise_navv2_formation_role_v1_formal_20260512_gpu" / "final_model.zip"
        if not model_path.exists():
            self.skipTest("cooperative formal checkpoint is not present in workspace")

        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "coop_eval.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "tools" / "eval" / "eval_sb3.py"),
                    "--mode",
                    "cooperative",
                    "--scenario",
                    str(repo_root / "scenarios" / "cruise" / "cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json"),
                    "--train_config",
                    str(repo_root / "examples" / "config" / "training" / "active" / "cooperative_cruise_nav_v2_formation_v1.json"),
                    "--model",
                    str(model_path),
                    "--episodes",
                    "1",
                    "--seed",
                    "100",
                    "--json_out",
                    str(json_out),
                ],
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                env=dict(os.environ, PYTHONPATH=str(repo_root / "build-workshop")),
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stdout)
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("mode"), "cooperative")
            self.assertIn("slot_summary", payload)
            self.assertGreaterEqual(len(payload["slot_summary"]), 2)
            self.assertIn("policy_routes", payload)
            self.assertIn("shared_execution", payload["policy_routes"])
            slot_names = set(payload["slot_summary"].keys())
            self.assertTrue(any("ElementLead" in name for name in slot_names))
            self.assertTrue(any("Wingman" in name for name in slot_names))
            for summary in payload["slot_summary"].values():
                self.assertIn("termination_counts", summary)
                self.assertIn("shared_world_reset_rate", summary)


if __name__ == "__main__":
    unittest.main()
