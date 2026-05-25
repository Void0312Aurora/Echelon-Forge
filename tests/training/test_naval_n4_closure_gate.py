from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
N4_DOC_DIR = REPO_ROOT / "docs" / "task" / "naval" / "n4_threat_roe_bridge"
ACTIVE_NAVAL_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval"
N4_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"
N4_CONTRACT = REPO_ROOT / "tests" / "contracts" / "unit" / "naval" / "naval_screen_threat_roe_geometry.json"
ACTIVE_CONFIGS = (
    ACTIVE_NAVAL_DIR / "naval_contact_report_threat_roe_smoke_v1.json",
    ACTIVE_NAVAL_DIR / "naval_screen_station_hold_threat_aware_smoke_v1.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class NavalN4ClosureGateTests(unittest.TestCase):
    def test_closure_documents_record_n4_closed_and_n5_blocked(self) -> None:
        closure = (N4_DOC_DIR / "naval_n4_closure_20260525.md").read_text(encoding="utf-8")
        closure_zh = (N4_DOC_DIR / "naval_n4_closure_20260525.zh.md").read_text(encoding="utf-8")
        readme = (N4_DOC_DIR / "README.md").read_text(encoding="utf-8")
        readme_zh = (N4_DOC_DIR / "README.zh.md").read_text(encoding="utf-8")

        for text in (closure, closure_zh):
            self.assertIn("ddg51_take1_screen_threat_roe_v1", text)
            self.assertIn("naval_screen_threat_roe_geometry", text)
            self.assertIn("naval_contact_report_threat_roe_v1", text)
            self.assertIn("naval_screen_station_hold_threat_aware_v1", text)
            self.assertIn("naval_limited_engagement_v1", text)
            self.assertIn("N5", text)
            self.assertIn("N6", text)

        self.assertIn("closed", closure.lower())
        self.assertIn("not mean", closure)
        self.assertIn("learned naval policy", closure)
        self.assertIn("weapon release", closure)
        self.assertIn("damage outcome", closure)
        self.assertIn("已闭合", closure_zh)
        self.assertIn("不意味着", closure_zh)
        self.assertIn("learned naval policy", closure_zh)
        self.assertIn("weapon release", closure_zh)
        self.assertIn("damage outcome", closure_zh)

        self.assertIn("naval_n4_closure_20260525.md", readme)
        self.assertIn("naval_n4_closure_20260525.zh.md", readme_zh)

    def test_n4_active_entries_match_closure_boundary(self) -> None:
        for path in ACTIVE_CONFIGS:
            with self.subTest(path=path.name):
                cfg = _load_json(path)
                naval_entry = cfg.get("naval_entry")
                self.assertIsInstance(naval_entry, dict)

                self.assertEqual(naval_entry.get("scenario_path"), "scenarios/naval/ddg51_take1_screen_threat_roe_v1.json")
                self.assertEqual(
                    naval_entry.get("contract_path"),
                    "tests/contracts/unit/naval/naval_screen_threat_roe_geometry.json",
                )
                self.assertEqual(naval_entry.get("realism_grade"), "N4_pre_fire_bridge")
                self.assertEqual(naval_entry.get("entry_status"), "active_smoke_probe")
                self.assertEqual(naval_entry.get("claim_level"), "entry_and_gate_only")
                self.assertEqual(naval_entry.get("engagement_scope"), "pre_fire_only")
                self.assertEqual(naval_entry.get("current_action_surface"), "no_release_probe")

                env = cfg.get("env")
                self.assertIsInstance(env, dict)
                self.assertEqual(env.get("action_mode"), "takeoff4")

                gate_groups = set(map(str, naval_entry.get("required_gate_groups", [])))
                self.assertIn("screen_geometry", gate_groups)
                self.assertIn("surface_contact", gate_groups)
                self.assertIn("threat_roe", gate_groups)
                self.assertIn("assigned_target_provenance", gate_groups)
                self.assertTrue({"report_chain", "station_hold"} & gate_groups)

    def test_n4_scenario_and_contract_stay_pre_fire(self) -> None:
        scenario = _load_json(N4_SCENARIO)
        contract = _load_json(N4_CONTRACT)
        description = str(scenario.get("description", "")).lower()
        self.assertIn("pre-fire", description)
        self.assertIn("does not model or require weapons release", description)
        self.assertIn("damage", description)
        self.assertIn("kill", description)

        mission = scenario.get("mission_command")
        self.assertIsInstance(mission, dict)
        self.assertEqual(mission.get("tasking_profile"), "naval")
        self.assertEqual(mission.get("roe_state"), 1)
        self.assertFalse(bool(mission.get("authorization_to_fire")))
        self.assertIn("engagement_authority_holder_id", mission)
        self.assertIn("engagement_authority_grantor_id", mission)
        self.assertEqual(mission.get("assigned_target_name"), "Red_Surface_Contact")

        rewards = scenario.get("rewards")
        self.assertIsInstance(rewards, dict)
        self.assertEqual(scenario.get("objectives"), [])
        forbidden_reward_keys = {"weapon", "launch", "damage", "kill", "hit", "intercept"}
        self.assertTrue(forbidden_reward_keys.isdisjoint({str(key).lower() for key in rewards.keys()}))

        contract_text = json.dumps(contract, ensure_ascii=True).lower()
        self.assertIn("authorization_to_fire", contract_text)
        self.assertIn("roe_state", contract_text)
        self.assertIn("assigned_target", contract_text)
        self.assertNotIn("damage_reward", contract_text)
        self.assertNotIn("kill_reward", contract_text)


if __name__ == "__main__":
    unittest.main()
