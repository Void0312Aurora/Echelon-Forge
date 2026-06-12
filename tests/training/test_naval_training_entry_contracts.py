from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from python.env_config import resolve_env_settings
from python.testing.contracts import run_contract
from python.training.bootstrap import validate_declared_training_entry_env_surface


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
FORBIDDEN_REWARD_ACTION_TERMS = (
  "weapon_release",
  "fire_weapon",
  "fire_gun",
  "damage",
  "damage_reward",
  "kill",
  "kill_reward",
  "hit",
  "intercept",
)
FORBIDDEN_CONFIG_TERMS = (
  *FORBIDDEN_ACTION_MODES,
  *FORBIDDEN_MISSION_OBS_MODES,
  *FORBIDDEN_REWARD_ACTION_TERMS,
  "learned_policy",
  "trained_policy",
)


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(path: Path) -> str:
  return path.as_posix()


class NavalTrainingEntryContractTests(unittest.TestCase):
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
        self.assertEqual(env.get("shaping_backend"), "compiled")
        self.assertIsNone(env.get("flight_shaping_backend"))
        self.assertEqual(env.get("step_info_mode"), "terminal")
        self.assertEqual(env.get("mission_obs_mode"), "naval_screen_station_v1")
        self.assertEqual(env.get("action_mode"), "naval_station3")
        self.assertNotIn(env.get("mission_obs_mode"), FORBIDDEN_MISSION_OBS_MODES)
        self.assertNotIn(env.get("action_mode"), FORBIDDEN_ACTION_MODES)
        resolved_env = resolve_env_settings(cfg, SimpleNamespace())
        self.assertEqual(resolved_env.get("flight_shaping_backend"), "compiled")

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
        self.assertEqual(naval_entry.get("scenario_path"), _repo_path(expected["scenario"]))
        self.assertEqual(naval_entry.get("contract_path"), _repo_path(expected["contract"]))
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

        joined_strings = json.dumps(cfg, ensure_ascii=True).lower()
        for term in FORBIDDEN_CONFIG_TERMS:
          self.assertNotIn(term, joined_strings)

  def test_naval_active_configs_reject_air_surface_regressions(self) -> None:
    for filename in NAVAL_ENTRIES:
      config_path = NAVAL_ACTIVE_DIR / filename
      cfg = _load_json(config_path)

      for bad_action_mode in FORBIDDEN_ACTION_MODES:
        with self.subTest(filename=filename, action_mode=bad_action_mode):
          mutated = json.loads(json.dumps(cfg))
          mutated["env"]["action_mode"] = bad_action_mode
          env_settings = resolve_env_settings(mutated, SimpleNamespace())
          error = validate_declared_training_entry_env_surface(
            train_config=mutated,
            env_settings=env_settings,
          )
          self.assertIsNotNone(error)
          self.assertIn("action_mode='naval_station3'", str(error))
          self.assertIn(repr(bad_action_mode), str(error))

      for bad_mission_obs_mode in FORBIDDEN_MISSION_OBS_MODES:
        with self.subTest(filename=filename, mission_obs_mode=bad_mission_obs_mode):
          mutated = json.loads(json.dumps(cfg))
          mutated["env"]["mission_obs_mode"] = bad_mission_obs_mode
          env_settings = resolve_env_settings(mutated, SimpleNamespace())
          error = validate_declared_training_entry_env_surface(
            train_config=mutated,
            env_settings=env_settings,
          )
          self.assertIsNotNone(error)
          self.assertIn("mission_obs_mode='naval_screen_station_v1'", str(error))
          self.assertIn(repr(bad_mission_obs_mode), str(error))

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
        reward_surface_strings = json.dumps(
          {
            "mission_command": mission,
            "rewards": rewards,
            "objectives": scenario.get("objectives"),
          },
          ensure_ascii=True,
        ).lower()
        for term in FORBIDDEN_REWARD_ACTION_TERMS:
          self.assertNotIn(term, reward_surface_strings)
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
    self.assertIn(_repo_path(EXPECTED_SCENARIO), readme)
    self.assertIn(_repo_path(RECOVERY_SCENARIO), readme)
    self.assertIn(_repo_path(EXPECTED_CONTRACT), readme)
    self.assertIn("not a trained naval policy", readme)
    self.assertIn("do not expose a weapon-release action", readme)
    self.assertIn("action_mode=naval_station3", readme)
    self.assertIn("mission_obs_mode=naval_screen_station_v1", readme)
    self.assertIn("naval_station3", readme_zh)
    self.assertIn("naval_screen_station_v1", readme_zh)
    self.assertIn("不暴露武器", readme_zh)


N4_DOC_DIR = REPO_ROOT / "docs" / "task" / "naval" / "archive" / "n4_threat_roe_bridge"
ACTIVE_NAVAL_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "naval"
N4_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_v1.json"
N4_RECOVERY_SCENARIO = REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_threat_roe_offstation_recovery_v1.json"
N4_CONTRACT = REPO_ROOT / "tests" / "contracts" / "unit" / "naval" / "naval_screen_threat_roe_geometry.json"
ACTIVE_CONFIGS = (
  ACTIVE_NAVAL_DIR / "naval_contact_report_threat_roe_smoke_v1.json",
  ACTIVE_NAVAL_DIR / "naval_screen_station_hold_threat_aware_smoke_v1.json",
  ACTIVE_NAVAL_DIR / "naval_screen_station_recovery_threat_aware_smoke_v1.json",
)


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


class NavalTrainingClosureContractTests(unittest.TestCase):
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
      self.assertIn("naval_screen_station_recovery_threat_aware_v1", text)
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

        self.assertTrue(str(naval_entry.get("scenario_path")).startswith("scenarios/naval/ddg51_take1_screen_threat_roe"))
        self.assertTrue(str(naval_entry.get("contract_path")).startswith("tests/contracts/unit/naval/naval_screen_threat_roe"))
        self.assertEqual(naval_entry.get("realism_grade"), "N4_pre_fire_bridge")
        self.assertEqual(naval_entry.get("entry_status"), "active_smoke_probe")
        self.assertEqual(naval_entry.get("claim_level"), "entry_and_gate_only")
        self.assertEqual(naval_entry.get("engagement_scope"), "pre_fire_only")
        self.assertEqual(naval_entry.get("current_action_surface"), "naval_station_order_probe")

        env = cfg.get("env")
        self.assertIsInstance(env, dict)
        self.assertEqual(env.get("action_mode"), "naval_station3")

        gate_groups = set(map(str, naval_entry.get("required_gate_groups", [])))
        self.assertIn("screen_geometry", gate_groups)
        self.assertIn("surface_contact", gate_groups)
        self.assertIn("threat_roe", gate_groups)
        self.assertIn("assigned_target_provenance", gate_groups)
        self.assertTrue({"report_chain", "station_hold", "station_recovery"} & gate_groups)

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
    self.assertTrue(bool(rewards.get("naval_reward_enabled")))
    self.assertFalse(bool(rewards.get("naval_suppress_off_runway_penalty")))
    self.assertIn("naval_station_error_weight", rewards)
    self.assertIn("naval_report_chain_bonus", rewards)
    self.assertIn("naval_pre_fire_roe_hold_bonus", rewards)

    contract_text = json.dumps(contract, ensure_ascii=True).lower()
    self.assertIn("authorization_to_fire", contract_text)
    self.assertIn("roe_state", contract_text)
    self.assertIn("assigned_target", contract_text)
    self.assertNotIn("damage_reward", contract_text)
    self.assertNotIn("kill_reward", contract_text)

  def test_n4_recovery_scenario_stays_pre_fire_and_off_station(self) -> None:
    scenario = _load_json(N4_RECOVERY_SCENARIO)
    description = str(scenario.get("description", "")).lower()
    self.assertIn("off-station", description)
    self.assertIn("pre-fire", description)
    self.assertIn("does not model or require weapons release", description)

    entities = {str(entity.get("name")): entity for entity in list(scenario.get("entities", []) or [])}
    screen = entities["Blue_Screen_DDG51"]
    hvu = entities["Blue_HVU_TAKE1"]
    screen_pos = list(screen.get("pos", []))
    hvu_pos = list(hvu.get("pos", []))
    separation_m = ((float(screen_pos[0]) - float(hvu_pos[0])) ** 2 + (float(screen_pos[1]) - float(hvu_pos[1])) ** 2) ** 0.5
    station_radius_m = float(dict(scenario.get("task_order", {}) or {}).get("station_radius_m", 0.0))
    self.assertAlmostEqual(separation_m, 13016.0, delta=1.0)
    self.assertAlmostEqual(station_radius_m - separation_m, 1800.0, delta=1.0)

    rewards = scenario.get("rewards")
    self.assertIsInstance(rewards, dict)
    self.assertGreater(float(rewards.get("naval_station_recovery_progress_weight", 0.0)), 0.0)
    forbidden_reward_keys = {"weapon", "launch", "damage", "kill", "hit", "intercept"}
    self.assertTrue(forbidden_reward_keys.isdisjoint({str(key).lower() for key in rewards.keys()}))
