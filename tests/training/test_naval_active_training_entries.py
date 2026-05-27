from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from python.testing.scenario_contract_runner import run_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
NAVAL_ACTIVE_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval"
NAVAL_ENTRIES = {
    "naval_contact_report_threat_roe_smoke_v1.json": {
        "task_id": "naval_contact_report_threat_roe_v1",
        "scenario": Path("scenarios/naval/ddg51_take1_screen_threat_roe_v1.json"),
        "contract": Path("tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json"),
        "gate_group": "report_chain",
    },
    "naval_screen_station_hold_threat_aware_smoke_v1.json": {
        "task_id": "naval_screen_station_hold_threat_aware_v1",
        "scenario": Path("scenarios/naval/ddg51_take1_screen_threat_roe_v1.json"),
        "contract": Path("tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json"),
        "gate_group": "station_hold",
    },
    "naval_screen_station_recovery_threat_aware_smoke_v1.json": {
        "task_id": "naval_screen_station_recovery_threat_aware_v1",
        "scenario": Path("scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json"),
        "contract": Path("tests/contracts/unit/naval/naval_screen_threat_roe_offstation_recovery.json"),
        "gate_group": "station_recovery",
    },
}
EXPECTED_SCENARIO = Path("scenarios/naval/ddg51_take1_screen_threat_roe_v1.json")
EXPECTED_CONTRACT = Path("tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json")
RECOVERY_SCENARIO = Path("scenarios/naval/ddg51_take1_screen_threat_roe_offstation_recovery_v1.json")
FORBIDDEN_TERMS = (
    "weapon_release",
    "fire_weapon",
    "fire_gun",
    "damage_reward",
    "kill_reward",
    "learned_policy",
    "trained_policy",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            strings.extend(_walk_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_strings(item))
    return strings


class NavalActiveTrainingEntryTests(unittest.TestCase):
    def test_naval_active_configs_are_n4_pre_fire_entry_gates(self) -> None:
        for filename, expected in NAVAL_ENTRIES.items():
            with self.subTest(filename=filename):
                config_path = NAVAL_ACTIVE_DIR / filename
                cfg = _load_json(config_path)
                naval_entry = cfg.get("naval_entry")
                self.assertIsInstance(naval_entry, dict)

                expected_task_id = str(expected["task_id"])
                station_command_entry = expected_task_id in {
                    "naval_screen_station_hold_threat_aware_v1",
                    "naval_screen_station_recovery_threat_aware_v1",
                }
                self.assertEqual(cfg.get("agent_layer"), "cooperative_execution")
                self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
                self.assertEqual(cfg.get("policy"), "SquashedMultiInputPolicy")
                self.assertEqual(int(cfg.get("n_envs")), 1)
                self.assertEqual(int(cfg.get("total_timesteps")), 512)
                hyperparams = cfg.get("hyperparameters")
                self.assertIsInstance(hyperparams, dict)

                runtime = cfg.get("runtime")
                self.assertIsInstance(runtime, dict)
                self.assertNotIn("world_batch_vec_env", runtime)
                cooperative_execution = cfg.get("cooperative_execution")
                self.assertIsInstance(cooperative_execution, dict)
                self.assertEqual(cooperative_execution.get("policy_route"), "shared_execution")
                self.assertEqual(runtime.get("batch_observation_backend"), "compiled")

                env = cfg.get("env")
                self.assertIsInstance(env, dict)
                self.assertEqual(env.get("execution_step_runtime_mode"), "compiled")
                self.assertEqual(env.get("flight_shaping_backend"), "compiled")
                self.assertEqual(env.get("step_info_mode"), "terminal")
                self.assertEqual(env.get("mission_obs_mode"), "naval_screen_station_v1")
                self.assertEqual(env.get("action_mode"), "naval_station3")

                if station_command_entry:
                    self.assertEqual(float(hyperparams.get("learning_rate")), 1.0e-4)
                    self.assertEqual(int(hyperparams.get("n_steps")), 128)
                    self.assertEqual(int(hyperparams.get("batch_size")), 128)
                    self.assertEqual(float(hyperparams.get("action_mean_regularization_coef", 0.0)), 500.0)
                    self.assertEqual(hyperparams.get("action_mean_regularization_target"), [0.0, 0.0, 0.0])
                    policy_kwargs = hyperparams.get("policy_kwargs")
                    self.assertIsInstance(policy_kwargs, dict)
                    self.assertFalse(bool(policy_kwargs.get("share_features_extractor", True)))
                    self.assertEqual(float(policy_kwargs.get("log_std_init")), -4.0)
                else:
                    self.assertNotIn("action_mean_regularization_coef", hyperparams)
                    self.assertNotIn("action_mean_regularization_target", hyperparams)

                self.assertEqual(naval_entry.get("task_id"), expected_task_id)
                self.assertEqual(naval_entry.get("scenario_path"), str(expected["scenario"]))
                self.assertEqual(naval_entry.get("contract_path"), str(expected["contract"]))
                self.assertEqual(naval_entry.get("realism_grade"), "N4_pre_fire_bridge")
                self.assertEqual(naval_entry.get("claim_level"), "entry_and_gate_only")
                self.assertEqual(naval_entry.get("engagement_scope"), "pre_fire_only")
                self.assertEqual(naval_entry.get("current_action_surface"), "naval_station_order_probe")
                self.assertEqual(
                    naval_entry.get("cooperative_runtime_status"),
                    "agent_slot_with_non_agent_support_roster_accepted",
                )

                self.assertTrue((REPO_ROOT / naval_entry["scenario_path"]).exists())
                self.assertTrue((REPO_ROOT / naval_entry["contract_path"]).exists())
                self.assertTrue((REPO_ROOT / naval_entry["source_preflight"]).exists())
                contract = _load_json(REPO_ROOT / naval_entry["contract_path"])
                self.assertEqual(contract.get("scenario"), naval_entry.get("scenario_path"))
                gate_groups = set(map(str, naval_entry.get("required_gate_groups", [])))
                self.assertIn(str(expected["gate_group"]), gate_groups)

                joined_strings = "\n".join(_walk_strings(cfg)).lower()
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, joined_strings)

    def test_naval_active_declared_contracts_execute_successfully(self) -> None:
        contract_paths = sorted({REPO_ROOT / entry["contract"] for entry in NAVAL_ENTRIES.values()})
        for contract_path in contract_paths:
            with self.subTest(contract=contract_path.name):
                ok, message = run_contract(str(contract_path))
                self.assertTrue(ok, message)

    def test_n4_scenarios_keep_weapons_and_damage_out_of_task_objective(self) -> None:
        for scenario_rel in {Path(str(entry["scenario"])) for entry in NAVAL_ENTRIES.values()}:
            with self.subTest(scenario=scenario_rel.name):
                scenario = _load_json(REPO_ROOT / scenario_rel)
                mission = scenario.get("mission_command")
                self.assertIsInstance(mission, dict)
                self.assertEqual(mission.get("tasking_profile"), "naval")
                self.assertEqual(mission.get("roe_state"), 1)
                self.assertFalse(bool(mission.get("authorization_to_fire")))
                self.assertEqual(mission.get("assigned_target_name"), "Red_Surface_Contact")

                rewards = scenario.get("rewards")
                self.assertIsInstance(rewards, dict)
                forbidden_reward_keys = {"damage", "damage_reward", "kill", "kill_reward", "hit", "intercept"}
                self.assertTrue(forbidden_reward_keys.isdisjoint(set(map(str, rewards.keys()))))
                self.assertTrue(bool(rewards.get("naval_reward_enabled")))
                self.assertFalse(bool(rewards.get("naval_suppress_off_runway_penalty")))
                self.assertIn("naval_station_error_weight", rewards)
                self.assertIn("naval_contact_maintained_bonus", rewards)
                self.assertIn("naval_pre_fire_roe_hold_bonus", rewards)
                if scenario_rel == EXPECTED_SCENARIO:
                    self.assertNotIn("naval_station_recovery_progress_weight", rewards)
                if scenario_rel == RECOVERY_SCENARIO:
                    self.assertGreater(float(rewards.get("naval_station_recovery_progress_weight", 0.0)), 0.0)
                self.assertEqual(scenario.get("objectives"), [])

    def test_train_bootstrap_accepts_naval_active_entries_on_current_runtime_paths(self) -> None:
        for filename, expected in NAVAL_ENTRIES.items():
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as tmpdir:
                    proc = subprocess.run(
                        [
                            sys.executable,
                            str(REPO_ROOT / "train.py"),
                            "--scenario",
                            str(REPO_ROOT / expected["scenario"]),
                            "--train_config",
                            str(NAVAL_ACTIVE_DIR / filename),
                            "--output_base",
                            tmpdir,
                            "--run_name",
                            f"{Path(filename).stem}_bootstrap",
                            "--test_only",
                        ],
                        cwd=str(REPO_ROOT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        check=False,
                    )

                self.assertNotIn("unknown agent_layer", proc.stdout)
                self.assertIn("Agent layer: cooperative_execution", proc.stdout)
                self.assertIn("Cooperative env settings: action_mode=naval_station3", proc.stdout)
                self.assertIn("mission_obs_mode=naval_screen_station_v1", proc.stdout)
                self.assertIn("Cooperative runtime:", proc.stdout)
                self.assertIn("slots_per_world=1", proc.stdout)
                self.assertIn("total_slots=1", proc.stdout)
                self.assertIn("Error: --test_only requires --resume_path", proc.stdout)

    def test_train_bootstrap_rejects_mismatched_naval_active_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "train.py"),
                    "--scenario",
                    str(REPO_ROOT / EXPECTED_SCENARIO),
                    "--train_config",
                    str(NAVAL_ACTIVE_DIR / "naval_screen_station_recovery_threat_aware_smoke_v1.json"),
                    "--output_base",
                    tmpdir,
                    "--run_name",
                    "naval_recovery_mismatch_bootstrap",
                    "--test_only",
                ],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

        self.assertIn("naval_entry.scenario_path", proc.stdout)
        self.assertIn("does not match --scenario", proc.stdout)
        self.assertNotIn("Cooperative runtime:", proc.stdout)

    def test_readme_documents_cli_pairings_and_non_claims(self) -> None:
        readme = (NAVAL_ACTIVE_DIR / "README.md").read_text(encoding="utf-8")
        readme_zh = (NAVAL_ACTIVE_DIR / "README.zh.md").read_text(encoding="utf-8")
        for filename in NAVAL_ENTRIES:
            self.assertIn(filename, readme)
            self.assertIn(filename, readme_zh)
        self.assertIn(str(EXPECTED_SCENARIO), readme)
        self.assertIn(str(RECOVERY_SCENARIO), readme)
        self.assertIn(str(EXPECTED_CONTRACT), readme)
        self.assertIn("not a trained naval policy", readme)
        self.assertIn("do not expose a weapon-release action", readme)
        self.assertIn("action_mode=naval_station3", readme)
        self.assertIn("mission_obs_mode=naval_screen_station_v1", readme)
        self.assertIn("naval_station3", readme_zh)
        self.assertIn("naval_screen_station_v1", readme_zh)
        self.assertIn("不暴露武器", readme_zh)


if __name__ == "__main__":
    unittest.main()
