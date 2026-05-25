from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
NAVAL_ACTIVE_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval"
NAVAL_ENTRIES = {
    "naval_contact_report_threat_roe_smoke_v1.json": "naval_contact_report_threat_roe_v1",
    "naval_screen_station_hold_threat_aware_smoke_v1.json": "naval_screen_station_hold_threat_aware_v1",
}
EXPECTED_SCENARIO = Path("scenarios/naval/ddg51_take1_screen_threat_roe_v1.json")
EXPECTED_CONTRACT = Path("tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json")
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
        for filename, expected_task_id in NAVAL_ENTRIES.items():
            with self.subTest(filename=filename):
                config_path = NAVAL_ACTIVE_DIR / filename
                cfg = _load_json(config_path)
                naval_entry = cfg.get("naval_entry")
                self.assertIsInstance(naval_entry, dict)

                self.assertEqual(cfg.get("agent_layer"), "execution")
                self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
                self.assertEqual(cfg.get("policy"), "SquashedMultiInputPolicy")
                self.assertEqual(int(cfg.get("n_envs")), 1)
                self.assertEqual(int(cfg.get("total_timesteps")), 512)

                runtime = cfg.get("runtime")
                self.assertIsInstance(runtime, dict)
                self.assertTrue(runtime.get("world_batch_vec_env"))
                self.assertEqual(runtime.get("batch_observation_backend"), "compiled")

                env = cfg.get("env")
                self.assertIsInstance(env, dict)
                self.assertEqual(env.get("execution_step_runtime_mode"), "compiled")
                self.assertEqual(env.get("flight_shaping_backend"), "compiled")
                self.assertEqual(env.get("step_info_mode"), "terminal")
                self.assertEqual(env.get("mission_obs_mode"), "nav_v2_formation_role_v1")
                self.assertEqual(env.get("action_mode"), "takeoff4")

                self.assertEqual(naval_entry.get("task_id"), expected_task_id)
                self.assertEqual(naval_entry.get("scenario_path"), str(EXPECTED_SCENARIO))
                self.assertEqual(naval_entry.get("contract_path"), str(EXPECTED_CONTRACT))
                self.assertEqual(naval_entry.get("realism_grade"), "N4_pre_fire_bridge")
                self.assertEqual(naval_entry.get("claim_level"), "entry_and_gate_only")
                self.assertEqual(naval_entry.get("engagement_scope"), "pre_fire_only")
                self.assertEqual(naval_entry.get("current_action_surface"), "no_release_probe")
                self.assertEqual(
                    naval_entry.get("cooperative_runtime_status"),
                    "pending_non_agent_roster_slot_gate",
                )

                self.assertTrue((REPO_ROOT / naval_entry["scenario_path"]).exists())
                self.assertTrue((REPO_ROOT / naval_entry["contract_path"]).exists())
                self.assertTrue((REPO_ROOT / naval_entry["source_preflight"]).exists())

                joined_strings = "\n".join(_walk_strings(cfg)).lower()
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, joined_strings)

    def test_n4_scenario_keeps_weapons_and_damage_out_of_task_objective(self) -> None:
        scenario = _load_json(REPO_ROOT / EXPECTED_SCENARIO)
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
        self.assertEqual(scenario.get("objectives"), [])

    def test_train_bootstrap_accepts_naval_active_entries_on_maintained_world_batch_path(self) -> None:
        for filename in NAVAL_ENTRIES:
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as tmpdir:
                    proc = subprocess.run(
                        [
                            sys.executable,
                            str(REPO_ROOT / "train.py"),
                            "--scenario",
                            str(REPO_ROOT / EXPECTED_SCENARIO),
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
                self.assertIn("Agent layer: execution", proc.stdout)
                self.assertIn("world_batch_vec_env=True", proc.stdout)
                self.assertIn("Effective env settings: action_mode=takeoff4", proc.stdout)
                self.assertIn("World batch runtime:", proc.stdout)
                self.assertIn("Error: --test_only requires --resume_path", proc.stdout)

    def test_readme_documents_cli_pairings_and_non_claims(self) -> None:
        readme = (NAVAL_ACTIVE_DIR / "README.md").read_text(encoding="utf-8")
        readme_zh = (NAVAL_ACTIVE_DIR / "README.zh.md").read_text(encoding="utf-8")
        for filename in NAVAL_ENTRIES:
            self.assertIn(filename, readme)
            self.assertIn(filename, readme_zh)
        self.assertIn(str(EXPECTED_SCENARIO), readme)
        self.assertIn(str(EXPECTED_CONTRACT), readme)
        self.assertIn("not a trained naval policy", readme)
        self.assertIn("do not expose a weapon-release action", readme)
        self.assertIn("不暴露武器", readme_zh)


if __name__ == "__main__":
    unittest.main()
