from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.eval.eval_sb3 import _build_single_env  # noqa: E402
from tools.eval.eval_naval_n4_baseline import run_baseline_eval, run_offstation_command_probe  # noqa: E402
from tools.eval.sb3_eval_base import load_sb3_policy  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"
RECOVERY_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_offstation_recovery_v1.json"
CONTACT_CONFIG = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval" / "naval_contact_report_threat_roe_smoke_v1.json"
HOLD_CONFIG = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval" / "naval_screen_station_hold_threat_aware_smoke_v1.json"
RECOVERY_CONFIG = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval" / "naval_screen_station_recovery_threat_aware_smoke_v1.json"
FORBIDDEN_ACTION_MODES = (
    "takeoff2",
    "takeoff4",
)
FORBIDDEN_MISSION_OBS_MODES = (
    "basic",
    "nav_v1",
    "nav_v2",
    "nav_v2_formation_v1",
    "nav_v2_formation_role_v1",
    "nav_v2_cooperative_takeoff_v1",
)
FORBIDDEN_REWARD_TERMS = {
    "weapon_release",
    "fire_weapon",
    "fire_gun",
    "damage",
    "damage_reward",
    "kill",
    "kill_reward",
    "hit",
    "intercept",
}


def _assert_reward_surface_clean(testcase: unittest.TestCase, payload: dict[str, object]) -> None:
    reward_terms_sum = set(map(str, dict(payload.get("reward_terms_sum", {}) or {}).keys()))
    reward_terms_last = set(map(str, dict(payload.get("reward_terms_last", {}) or {}).keys()))
    testcase.assertTrue(
        FORBIDDEN_REWARD_TERMS.isdisjoint(reward_terms_sum | reward_terms_last),
        payload,
    )


class NavalN4BaselineEvalTests(unittest.TestCase):
    def test_n4_baseline_eval_reports_cooperative_support_roster_and_reward_terms(self) -> None:
        payload = run_baseline_eval(
            scenario_path=str(SCENARIO),
            train_config_path=str(HOLD_CONFIG),
            steps=32,
            seed=20260525,
            worker_threads=1,
        )

        self.assertTrue(bool(payload.get("passed")), payload)
        self.assertEqual(payload.get("mode"), "naval_n4_cooperative_zero_action_baseline")
        self.assertEqual(int(payload.get("slots_per_world")), 1)
        self.assertEqual(int(payload.get("policy_slot_count")), 1)
        self.assertGreaterEqual(int(payload.get("active_roster_count")), 2)
        self.assertGreaterEqual(int(payload.get("non_agent_roster_count")), 1)
        self.assertGreater(float(payload.get("reward_total")), 0.0)
        self.assertEqual(payload.get("forbidden_reward_terms_present"), [])
        self.assertEqual(payload.get("required_reward_terms_missing"), [])

        reward_terms = dict(payload.get("reward_terms_sum", {}) or {})
        self.assertIn("naval_station_error_penalty", reward_terms)
        self.assertIn("naval_contact_maintained_bonus", reward_terms)
        self.assertIn("naval_shared_track_bonus", reward_terms)
        self.assertNotIn("off_runway_penalty", reward_terms)
        self.assertNotIn("speed_reward", reward_terms)
        self.assertNotIn("damage_reward", reward_terms)
        _assert_reward_surface_clean(self, payload)

        roster = list(payload.get("active_roster", []) or [])
        self.assertEqual([(member["entity_name"], member["is_agent"]) for member in roster[:2]], [
            ("Blue_Screen_DDG51", True),
            ("Blue_HVU_TAKE1", False),
        ])

    def test_n4_baseline_eval_cli_writes_json_for_each_active_entry(self) -> None:
        pairings = (
            (CONTACT_CONFIG, SCENARIO),
            (HOLD_CONFIG, SCENARIO),
            (RECOVERY_CONFIG, RECOVERY_SCENARIO),
        )
        for config_path, scenario_path in pairings:
            with self.subTest(config=config_path.name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    json_out = Path(tmpdir) / "baseline.json"
                    proc = subprocess.run(
                        [
                            sys.executable,
                            str(REPO_ROOT / "tools" / "eval" / "eval_naval_n4_baseline.py"),
                            "--scenario",
                            str(scenario_path),
                            "--train_config",
                            str(config_path),
                            "--steps",
                            "16",
                            "--seed",
                            "20260525",
                            "--json_out",
                            str(json_out),
                        ],
                        cwd=str(REPO_ROOT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        check=False,
                    )

                    self.assertEqual(proc.returncode, 0, msg=proc.stdout)
                    payload = json.loads(json_out.read_text(encoding="utf-8"))
                    self.assertTrue(bool(payload.get("passed")), payload)
                    self.assertEqual(int(payload.get("executed_steps")), 16)
                    self.assertEqual(int(payload.get("policy_slot_count")), 1)
                    self.assertEqual(payload.get("forbidden_reward_terms_present"), [])
                    _assert_reward_surface_clean(self, payload)

    def test_n4_baseline_eval_rejects_mismatched_declared_scenario(self) -> None:
        with self.assertRaisesRegex(ValueError, "naval_entry\\.scenario_path"):
            run_baseline_eval(
                scenario_path=str(SCENARIO),
                train_config_path=str(RECOVERY_CONFIG),
                steps=4,
                seed=20260525,
                worker_threads=1,
            )

    def test_n4_baseline_eval_cli_writes_json_for_declared_scenario_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "mismatch.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "eval" / "eval_naval_n4_baseline.py"),
                    "--scenario",
                    str(SCENARIO),
                    "--train_config",
                    str(RECOVERY_CONFIG),
                    "--steps",
                    "4",
                    "--seed",
                    "20260525",
                    "--json_out",
                    str(json_out),
                ],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            self.assertNotEqual(proc.returncode, 0, msg=proc.stdout)
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertFalse(bool(payload.get("passed")))
            self.assertIn("naval_entry.scenario_path", str(payload.get("error", "")))
            self.assertIn("does not match --scenario", str(payload.get("error", "")))

    def test_n4_baseline_eval_rejects_naval_entry_without_naval_env_surface(self) -> None:
        for bad_value in FORBIDDEN_ACTION_MODES:
            with self.subTest(env_key="action_mode", bad_value=bad_value):
                with tempfile.TemporaryDirectory() as tmpdir:
                    config_path = Path(tmpdir) / "bad_surface.json"
                    cfg = json.loads(HOLD_CONFIG.read_text(encoding="utf-8"))
                    cfg["env"]["action_mode"] = bad_value
                    config_path.write_text(json.dumps(cfg, ensure_ascii=True), encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, "action_mode='naval_station3'"):
                        run_baseline_eval(
                            scenario_path=str(SCENARIO),
                            train_config_path=str(config_path),
                            steps=4,
                            seed=20260525,
                            worker_threads=1,
                        )
        for bad_value in FORBIDDEN_MISSION_OBS_MODES:
            with self.subTest(env_key="mission_obs_mode", bad_value=bad_value):
                with tempfile.TemporaryDirectory() as tmpdir:
                    config_path = Path(tmpdir) / "bad_surface.json"
                    cfg = json.loads(HOLD_CONFIG.read_text(encoding="utf-8"))
                    cfg["env"]["mission_obs_mode"] = bad_value
                    config_path.write_text(json.dumps(cfg, ensure_ascii=True), encoding="utf-8")

                    with self.assertRaisesRegex(ValueError, "mission_obs_mode='naval_screen_station_v1'"):
                        run_baseline_eval(
                            scenario_path=str(SCENARIO),
                            train_config_path=str(config_path),
                            steps=4,
                            seed=20260525,
                            worker_threads=1,
                        )

    def test_n4_offstation_probe_reports_reward_reference_closure(self) -> None:
        payload = run_offstation_command_probe(
            scenario_path=str(SCENARIO),
            train_config_path=str(HOLD_CONFIG),
            steps=64,
            seed=20260525,
            worker_threads=1,
        )

        self.assertTrue(bool(payload.get("passed")), payload)
        self.assertEqual(payload.get("mode"), "naval_n4_offstation_station_order_probe")
        min_delta = float(payload.get("minimum_recovery_delta_m"))
        self.assertLess(float(payload.get("reward_delta_matched_minus_zero")), 0.0)
        self.assertLess(float(payload.get("zero_station_error_delta_final_minus_first")), -min_delta)
        self.assertGreater(float(payload.get("final_station_error_delta_matched_minus_zero")), min_delta)
        self.assertEqual(payload.get("forbidden_reward_terms_present"), [])
        matched = dict(payload.get("matched_radius_action", {}) or {})
        terms = dict(matched.get("reward_terms_sum", {}) or {})
        last_terms = dict(matched.get("reward_terms_last", {}) or {})
        zero_terms = dict(dict(payload.get("zero_action", {}) or {}).get("reward_terms_sum", {}) or {})
        self.assertGreater(float(zero_terms.get("naval_station_recovery_progress_bonus", 0.0)), 0.0)
        self.assertIn("naval_station_action_radius_penalty", terms)
        self.assertNotIn("naval_station_band_bonus", last_terms)
        _assert_reward_surface_clean(self, matched)
        _assert_reward_surface_clean(self, dict(payload.get("zero_action", {}) or {}))
        final_status = list(matched.get("final_mission_status", []) or [])
        self.assertGreater(float(final_status[0]), 1000.0)

    def test_n4_offstation_probe_uses_maintained_recovery_scenario_directly(self) -> None:
        payload = run_offstation_command_probe(
            scenario_path=str(RECOVERY_SCENARIO),
            train_config_path=str(RECOVERY_CONFIG),
            steps=64,
            seed=20260525,
            worker_threads=1,
        )

        self.assertTrue(bool(payload.get("passed")), payload)
        derived = dict(payload.get("derived", {}) or {})
        self.assertIsNone(derived.get("derived_scenario"))
        self.assertEqual(Path(str(derived.get("source_scenario"))), RECOVERY_SCENARIO)
        self.assertGreater(float(derived.get("initial_station_error_m", 0.0)), 1000.0)
        zero_terms = dict(dict(payload.get("zero_action", {}) or {}).get("reward_terms_sum", {}) or {})
        self.assertGreater(float(zero_terms.get("naval_station_recovery_progress_bonus", 0.0)), 0.0)
        _assert_reward_surface_clean(self, dict(payload.get("zero_action", {}) or {}))
        _assert_reward_surface_clean(self, dict(payload.get("matched_radius_action", {}) or {}))

    def test_n4_offstation_probe_cli_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "offstation.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "eval" / "eval_naval_n4_baseline.py"),
                    "--mode",
                    "offstation_probe",
                    "--scenario",
                    str(SCENARIO),
                    "--train_config",
                    str(HOLD_CONFIG),
                    "--steps",
                    "32",
                    "--seed",
                    "20260525",
                    "--json_out",
                    str(json_out),
                ],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stdout)
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertTrue(bool(payload.get("passed")), payload)
            self.assertEqual(payload.get("mode"), "naval_n4_offstation_station_order_probe")
            self.assertLess(float(payload.get("reward_delta_matched_minus_zero")), 0.0)
            self.assertLess(
                float(payload.get("zero_station_error_delta_final_minus_first")),
                -float(payload.get("minimum_recovery_delta_m")),
            )
            _assert_reward_surface_clean(self, dict(payload.get("zero_action", {}) or {}))
            _assert_reward_surface_clean(self, dict(payload.get("matched_radius_action", {}) or {}))


class EvalSB3Tests(unittest.TestCase):
    def test_single_eval_builds_world_batch_runtime_for_maintained_execution_entry(self) -> None:
        train_config_path = (
            REPO_ROOT
            / "examples"
            / "config"
            / "training"
            / "frozen"
            / "execution"
            / "p3_takeoff_to_cruise_retrain_v1.json"
        )
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
        cases = [
            (
                REPO_ROOT / "experiments" / "coop_takeoff_to_cruise_landing_formal_20260514" / "final_model.zip",
                "SquashedMultiInputPolicy",
            ),
            (
                REPO_ROOT
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
        model_path = (
            REPO_ROOT
            / "experiments"
            / "coop_cruise_navv2_formation_role_v1_formal_20260512_gpu"
            / "final_model.zip"
        )
        if not model_path.exists():
            self.skipTest("cooperative formal checkpoint is not present in workspace")

        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "coop_eval.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "eval" / "eval_sb3.py"),
                    "--mode",
                    "cooperative",
                    "--scenario",
                    str(
                        REPO_ROOT
                        / "scenarios"
                        / "cruise"
                        / "cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json"
                    ),
                    "--train_config",
                    str(
                        REPO_ROOT
                        / "examples"
                        / "config"
                        / "training"
                        / "active"
                        / "cooperative_cruise_nav_v2_formation_v1.json"
                    ),
                    "--model",
                    str(model_path),
                    "--episodes",
                    "1",
                    "--seed",
                    "100",
                    "--json_out",
                    str(json_out),
                ],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                env=dict(os.environ, PYTHONPATH=str(REPO_ROOT / "build-workshop")),
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
