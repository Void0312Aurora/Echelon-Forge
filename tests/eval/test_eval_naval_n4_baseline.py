from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.eval.eval_naval_n4_baseline import run_baseline_eval, run_offstation_command_probe  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
