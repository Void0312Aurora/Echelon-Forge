from __future__ import annotations

import json
import tempfile
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.rl.multi_agent_benchmark import run_benchmark  # noqa: E402


def _cooperative_scenario() -> dict:
    return {
        "scenario_name": "multi_agent_benchmark_smoke",
        "meta": {"max_steps": 8},
        "environment": {
            "time_step": 0.05,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
            "zones": [],
        },
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1400.0,
            "target_speed": 210.0,
            "formation_id": 17,
            "form_offset_x": 180.0,
            "form_offset_y": -90.0,
            "form_offset_z": 30.0,
        },
        "entities": [
            {
                "name": "Lead",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [0.0, 0.0, 1400.0],
                "vel": [210.0, 0.0, 0.0],
                "heading": 90.0,
            },
            {
                "name": "Wing",
                "type": "F-16C_Block50",
                "side": "Blue",
                "is_agent": True,
                "pos": [-120.0, -180.0, 1400.0],
                "vel": [210.0, 0.0, 0.0],
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


class _Args:
    include_visual = None
    include_proprio = None
    action_mode = None
    mission_obs_mode = None
    visual_downsample = None
    visual_update_interval = None
    step_info_mode = None
    execution_step_runtime_mode = None
    flight_shaping_backend = None


class MultiAgentBenchmarkTests(unittest.TestCase):
    def test_benchmark_single_and_cooperative_smoke(self) -> None:
        train_cfg = {
            "agent_layer": "cooperative_execution",
            "env": {
                "include_visual": False,
                "include_proprio": True,
                "action_mode": "full",
                "mission_obs_mode": "nav_v2_formation_v1",
                "step_info_mode": "terminal",
            },
            "leader_env": {
                "execution_backend": "scripted",
                "decision_interval_steps": 4,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = f"{tmpdir}/scenario.json"
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(_cooperative_scenario(), f, ensure_ascii=True)

            single = run_benchmark(
                scenario_path=scenario_path,
                train_config=train_cfg,
                mode="single_agent",
                steps=2,
                seed=7,
                n_envs=1,
                args=_Args(),
            )
            coop = run_benchmark(
                scenario_path=scenario_path,
                train_config=train_cfg,
                mode="cooperative_execution",
                steps=2,
                seed=7,
                n_envs=1,
                args=_Args(),
            )

            self.assertGreaterEqual(float(single.metrics.get("step_time_ms", 0.0)), 0.0)
            self.assertIn("obs_build_ms", single.metrics)
            self.assertGreaterEqual(float(coop.metrics.get("step_time_ms", 0.0)), 0.0)
            self.assertEqual(int(coop.slot_count), 2)
            self.assertIn("per_agent_step_time_ms", coop.metrics)


if __name__ == "__main__":
    unittest.main()
