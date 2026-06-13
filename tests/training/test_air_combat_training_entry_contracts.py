from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from python.rl.policy_algo.model_contracts import (
  FaultStage,
  MechanismRole,
  active_model_contracts_for_config,
  validate_training_config_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AIR_COMBAT_ACTIVE_DIR = REPO_ROOT / "examples" / "config" / "training" / "active" / "air_combat"
F16_SCRIPTED_RED_TG_P7_PROXY_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_v1.json"
)
F16_SCRIPTED_RED_BASELINE_32K_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_f16c_scripted_red_world_batch_probe_32k_v1.json"
)
F16_SCRIPTED_RED_TG_P7_PROXY_32K_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_f16c_scripted_red_tg_p7_target_geometry_proxy_world_batch_probe_32k_v1.json"
)
STAGE1_CONFIG = AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_world_batch_probe_v1.json"
STAGE1_TEMPORAL_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_temporal_world_batch_probe_v1.json"
)
STAGE1_HYBRID_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_world_batch_probe_v1.json"
)
STAGE1_HYBRID_TEMPORAL_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_world_batch_probe_v1.json"
)
STAGE1_HYBRID_SHAPED_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_shaped_world_batch_probe_v1.json"
)
STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_hybrid_temporal_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_DEADLINE_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_EVENT_HEAD_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_LAUNCH_WINDOW_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_A7_EVENT_CREDIT_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_A7_STATE_COMPLETED_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_M3S1_GROUPED_STOPPING_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json"
)
STAGE1_C2_ROE_TEMPORAL_M3S2_EVENT_WINDOW_CONFIG = (
  AIR_COMBAT_ACTIVE_DIR
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s2_event_window_state_completed_world_batch_probe_v1.json"
)
F16_SCRIPTED_RED_SCENARIO = (
  REPO_ROOT
  / "scenarios"
  / "air_combat"
  / "air_combat_1v1_headon_sensor_smoke_v1.json"
)
STAGE1_SCENARIO = REPO_ROOT / "scenarios" / "air_combat" / "1v1" / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json"
STAGE1_SHAPED_SCENARIO = (
  REPO_ROOT
  / "scenarios"
  / "air_combat"
  / "1v1"
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_training_shaped_v1.json"
)
STAGE1_C2_ROE_SCENARIO = (
  REPO_ROOT
  / "scenarios"
  / "air_combat"
  / "1v1"
  / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json"
)


def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))


def _damage_component_names(unit: dict[str, Any]) -> list[str]:
  return [
    component["name"]
    for hitbox in unit.get("damage_model", {}).get("hitboxes", [])
    for component in hitbox.get("components", [])
    if isinstance(component, dict) and component.get("name")
  ]


def _violation_dicts(config: dict[str, Any]) -> list[dict[str, Any]]:
  return [violation.as_dict() for violation in validate_training_config_contract(config)]


class AirCombatTrainingEntryContractTests(unittest.TestCase):
  def test_f16_tg_p7_target_geometry_proxy_config_uses_opt_in_database(self) -> None:
    cfg = _load_json(F16_SCRIPTED_RED_TG_P7_PROXY_CONFIG)
    runtime = cfg.get("runtime")
    self.assertIsInstance(runtime, dict)
    assert isinstance(runtime, dict)

    self.assertEqual(cfg.get("agent_layer"), "execution")
    self.assertTrue(bool(runtime.get("world_batch_vec_env")))
    self.assertEqual(runtime.get("batch_observation_backend"), "compiled")
    self.assertEqual(runtime.get("batch_visual_backend"), "compiled")
    self.assertEqual(runtime.get("observation_return_mode"), "copy")
    self.assertEqual(
      runtime.get("database_path"),
      "docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613",
    )
    proxy_cfg = runtime.get("target_geometry_proxy")
    self.assertIsInstance(proxy_cfg, dict)
    assert isinstance(proxy_cfg, dict)
    self.assertEqual(proxy_cfg.get("feature_flag"), "A2_TARGET_GEOMETRY_PROXY_F16C_R22")
    self.assertEqual(proxy_cfg.get("target_unit"), "F-16C_Block50")
    self.assertEqual(int(proxy_cfg.get("default_component_count")), 26)
    self.assertEqual(int(proxy_cfg.get("proxy_component_count")), 32)
    self.assertEqual(int(proxy_cfg.get("split_receiver_component_count")), 8)
    self.assertEqual(int(proxy_cfg.get("retired_parent_component_count")), 2)

    proxy_manifest = _load_json(REPO_ROOT / str(proxy_cfg["source_manifest"]))
    self.assertEqual(
      proxy_manifest["schema_version"],
      "a2.target_geometry_training_proxy_database.v1",
    )
    self.assertEqual(
      proxy_manifest["summary"]["proxy_database_component_count"],
      32,
    )
    proxy_unit_path = (
      REPO_ROOT
      / str(runtime["database_path"])
      / "aircraft"
      / "units"
      / "f16c_block50.json"
    )
    self.assertTrue(proxy_unit_path.is_file())
    proxy_component_names = _damage_component_names(_load_json(proxy_unit_path))
    self.assertEqual(len(proxy_component_names), 32)
    self.assertNotIn("engine_core", proxy_component_names)
    self.assertNotIn("wing_spar_center", proxy_component_names)
    self.assertIn("engine_core_afterburner_segment", proxy_component_names)
    self.assertIn("wing_spar_center_carrythrough_segment", proxy_component_names)

  def test_f16_tg_p7_target_geometry_proxy_32k_pairs_with_default_baseline(self) -> None:
    baseline = _load_json(F16_SCRIPTED_RED_BASELINE_32K_CONFIG)
    proxy = _load_json(F16_SCRIPTED_RED_TG_P7_PROXY_32K_CONFIG)

    self.assertEqual(int(baseline.get("total_timesteps")), 32768)
    self.assertEqual(int(proxy.get("total_timesteps")), 32768)
    self.assertEqual(int(baseline.get("save_freq")), 8192)
    self.assertEqual(int(proxy.get("save_freq")), 8192)
    self.assertEqual(baseline.get("agent_layer"), proxy.get("agent_layer"))
    self.assertEqual(baseline.get("algo"), proxy.get("algo"))
    self.assertEqual(baseline.get("policy"), proxy.get("policy"))
    self.assertEqual(baseline.get("n_envs"), proxy.get("n_envs"))
    self.assertEqual(baseline.get("env"), proxy.get("env"))
    self.assertEqual(baseline.get("early_stop"), proxy.get("early_stop"))
    self.assertEqual(baseline.get("diagnostics"), proxy.get("diagnostics"))
    self.assertEqual(baseline.get("hmoe"), proxy.get("hmoe"))
    self.assertEqual(baseline.get("hyperparameters"), proxy.get("hyperparameters"))

    baseline_runtime = dict(baseline.get("runtime", {}))
    proxy_runtime = dict(proxy.get("runtime", {}))
    self.assertNotIn("database_path", baseline_runtime)
    proxy_database_path = proxy_runtime.pop("database_path")
    proxy_metadata = proxy_runtime.pop("target_geometry_proxy")
    self.assertEqual(proxy_runtime, baseline_runtime)
    self.assertEqual(
      proxy_database_path,
      "docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_target_geometry/review_packets/f16c_20260611/target_geometry_training_proxy_database_20260613",
    )
    self.assertEqual(proxy_metadata.get("feature_flag"), "A2_TARGET_GEOMETRY_PROXY_F16C_R22")
    self.assertEqual(int(proxy_metadata.get("default_component_count")), 26)
    self.assertEqual(int(proxy_metadata.get("proxy_component_count")), 32)
    self.assertEqual(int(proxy_metadata.get("split_receiver_component_count")), 8)

  def test_stage1_bvr_probe_config_matches_maintained_world_batch_surface(self) -> None:
    cfg = _load_json(STAGE1_CONFIG)
    scenario = _load_json(STAGE1_SCENARIO)

    self.assertEqual(cfg.get("agent_layer"), "execution")
    self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
    self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
    self.assertEqual(int(cfg.get("n_envs")), 4)
    self.assertEqual(int(cfg.get("total_timesteps")), 8192)

    runtime = cfg.get("runtime")
    self.assertIsInstance(runtime, dict)
    self.assertTrue(bool(runtime.get("world_batch_vec_env")))
    self.assertEqual(int(runtime.get("world_batch_threads")), 4)
    self.assertEqual(runtime.get("batch_observation_backend"), "compiled")
    self.assertEqual(runtime.get("batch_visual_backend"), "compiled")
    self.assertTrue(bool(runtime.get("policy_observation_torch_bridge")))

    env = cfg.get("env")
    self.assertIsInstance(env, dict)
    self.assertEqual(env.get("action_mode"), "full")
    self.assertEqual(env.get("mission_obs_mode"), "basic")
    self.assertEqual(env.get("step_info_mode"), "terminal")
    self.assertEqual(env.get("execution_step_runtime_mode"), "compiled")
    self.assertEqual(env.get("flight_shaping_backend"), "compiled")

    hyperparams = cfg.get("hyperparameters")
    self.assertIsInstance(hyperparams, dict)
    self.assertEqual(int(hyperparams.get("n_steps")), 256)
    self.assertEqual(int(hyperparams.get("batch_size")), 512)
    self.assertEqual(hyperparams.get("policy_kwargs", {}).get("features_extractor_class"), "TransformerExtractor")

    realism = scenario.get("realism_gradient")
    self.assertIsInstance(realism, dict)
    self.assertEqual(realism.get("domain"), "air_combat")
    self.assertEqual(realism.get("workline"), "1v1")
    self.assertEqual(realism.get("stage"), "A1-S1")
    self.assertEqual(scenario.get("mission_command", {}).get("assigned_target_name"), "Red_Target")
    self.assertTrue(bool(scenario.get("mission_command", {}).get("authorization_to_fire")))
    self.assertEqual(scenario.get("entities", [])[1].get("ammo", {}).get("missiles_remaining"), 0)

  def test_stage1_bvr_temporal_probe_pairs_with_reactive_baseline(self) -> None:
    reactive = _load_json(STAGE1_CONFIG)
    temporal = _load_json(STAGE1_TEMPORAL_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(temporal.get(key), reactive.get(key), key)
    self.assertEqual(temporal.get("runtime"), reactive.get("runtime"))
    self.assertEqual(temporal.get("early_stop"), reactive.get("early_stop"))
    self.assertEqual(temporal.get("diagnostics"), reactive.get("diagnostics"))
    self.assertEqual(temporal.get("hmoe"), reactive.get("hmoe"))

    reactive_env = dict(reactive.get("env", {}))
    temporal_env = dict(temporal.get("env", {}))
    self.assertEqual(int(temporal_env.pop("temporal_history_len")), 16)
    self.assertEqual(temporal_env, reactive_env)

    reactive_hyper = dict(reactive.get("hyperparameters", {}))
    temporal_hyper = dict(temporal.get("hyperparameters", {}))
    reactive_policy_kwargs = dict(reactive_hyper.pop("policy_kwargs"))
    temporal_policy_kwargs = dict(temporal_hyper.pop("policy_kwargs"))
    self.assertEqual(temporal_hyper, reactive_hyper)
    self.assertEqual(
      temporal_policy_kwargs.get("features_extractor_class"),
      "TemporalTransformerExtractor",
    )
    self.assertEqual(
      reactive_policy_kwargs.get("features_extractor_class"),
      "TransformerExtractor",
    )
    self.assertEqual(temporal_policy_kwargs.get("family_subexpert_counts"), reactive_policy_kwargs.get("family_subexpert_counts"))
    self.assertEqual(temporal_policy_kwargs.get("net_arch"), reactive_policy_kwargs.get("net_arch"))
    temporal_extractor = temporal_policy_kwargs.get("features_extractor_kwargs", {})
    self.assertEqual(int(temporal_extractor.get("features_dim")), 192)
    self.assertEqual(int(temporal_extractor.get("temporal_n_heads")), 4)
    self.assertEqual(int(temporal_extractor.get("temporal_n_layers")), 2)

  def test_stage1_bvr_hybrid_probe_pairs_with_full_action_baseline(self) -> None:
    full = _load_json(STAGE1_CONFIG)
    hybrid = _load_json(STAGE1_HYBRID_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(hybrid.get(key), full.get(key), key)
    self.assertEqual(hybrid.get("runtime"), full.get("runtime"))
    self.assertEqual(hybrid.get("early_stop"), full.get("early_stop"))
    self.assertEqual(hybrid.get("diagnostics"), full.get("diagnostics"))
    self.assertEqual(hybrid.get("hmoe"), full.get("hmoe"))

    full_env = dict(full.get("env", {}))
    hybrid_env = dict(hybrid.get("env", {}))
    self.assertEqual(full_env.pop("action_mode"), "full")
    self.assertEqual(hybrid_env.pop("action_mode"), "air_combat_hybrid_v1")
    self.assertEqual(hybrid_env, full_env)

    hybrid_policy_kwargs = hybrid.get("hyperparameters", {}).get("policy_kwargs", {})
    self.assertEqual(hybrid_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
    self.assertEqual(hybrid_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")

  def test_stage1_bvr_hybrid_temporal_probe_pairs_with_hybrid_reactive_baseline(self) -> None:
    hybrid = _load_json(STAGE1_HYBRID_CONFIG)
    hybrid_temporal = _load_json(STAGE1_HYBRID_TEMPORAL_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(hybrid_temporal.get(key), hybrid.get(key), key)
    self.assertEqual(hybrid_temporal.get("runtime"), hybrid.get("runtime"))
    self.assertEqual(hybrid_temporal.get("early_stop"), hybrid.get("early_stop"))
    self.assertEqual(hybrid_temporal.get("diagnostics"), hybrid.get("diagnostics"))
    self.assertEqual(hybrid_temporal.get("hmoe"), hybrid.get("hmoe"))

    hybrid_env = dict(hybrid.get("env", {}))
    hybrid_temporal_env = dict(hybrid_temporal.get("env", {}))
    self.assertEqual(int(hybrid_temporal_env.pop("temporal_history_len")), 16)
    self.assertEqual(hybrid_temporal_env, hybrid_env)

    hybrid_hyper = dict(hybrid.get("hyperparameters", {}))
    hybrid_temporal_hyper = dict(hybrid_temporal.get("hyperparameters", {}))
    hybrid_policy_kwargs = dict(hybrid_hyper.pop("policy_kwargs"))
    hybrid_temporal_policy_kwargs = dict(hybrid_temporal_hyper.pop("policy_kwargs"))
    self.assertEqual(hybrid_temporal_hyper, hybrid_hyper)
    self.assertEqual(hybrid_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(hybrid_temporal_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(hybrid_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
    self.assertEqual(hybrid_temporal_policy_kwargs.get("features_extractor_class"), "TemporalTransformerExtractor")
    self.assertEqual(
      hybrid_temporal_policy_kwargs.get("family_subexpert_counts"),
      hybrid_policy_kwargs.get("family_subexpert_counts"),
    )
    self.assertEqual(hybrid_temporal_policy_kwargs.get("net_arch"), hybrid_policy_kwargs.get("net_arch"))

  def test_stage1_bvr_hybrid_shaped_probe_uses_training_shaped_scenario_contract(self) -> None:
    hybrid = _load_json(STAGE1_HYBRID_CONFIG)
    shaped = _load_json(STAGE1_HYBRID_SHAPED_CONFIG)
    scenario = _load_json(STAGE1_SHAPED_SCENARIO)

    for key in ("agent_layer", "algo", "policy", "n_envs"):
      self.assertEqual(shaped.get(key), hybrid.get(key), key)
    self.assertEqual(int(shaped.get("total_timesteps")), 32768)
    self.assertEqual(int(shaped.get("save_freq")), 8192)
    self.assertEqual(shaped.get("runtime"), hybrid.get("runtime"))
    self.assertEqual(shaped.get("env"), hybrid.get("env"))
    self.assertEqual(shaped.get("early_stop"), hybrid.get("early_stop"))
    self.assertEqual(shaped.get("diagnostics"), hybrid.get("diagnostics"))
    self.assertEqual(shaped.get("hmoe"), hybrid.get("hmoe"))
    wrapper_cfg = shaped.get("wrappers", {}).get("multi_timescale_action", {})
    self.assertTrue(bool(wrapper_cfg.get("enabled")))
    self.assertEqual(wrapper_cfg.get("scripted_baseline_mode"), "stable_flight")
    self.assertEqual(wrapper_cfg.get("scripted_blend_indices"), [0, 1, 2, 3])
    self.assertEqual(wrapper_cfg.get("scripted_lock_indices"), [])
    self.assertEqual(wrapper_cfg.get("low_freq_indices"), [])
    self.assertEqual(wrapper_cfg.get("snap_binary_indices"), [])
    self.assertEqual(wrapper_cfg.get("binary_hysteresis_indices"), [])

    shaped_policy_kwargs = dict(shaped.get("hyperparameters", {}).get("policy_kwargs", {}))
    hybrid_policy_kwargs = dict(hybrid.get("hyperparameters", {}).get("policy_kwargs", {}))
    self.assertLess(
      float(shaped_policy_kwargs.pop("log_std_init")),
      float(hybrid_policy_kwargs.pop("log_std_init")),
    )
    self.assertEqual(shaped_policy_kwargs, hybrid_policy_kwargs)

    self.assertIn("training_shaped", scenario.get("realism_gradient", {}).get("stage_name", ""))
    rewards = scenario.get("rewards", {})
    self.assertTrue(bool(rewards.get("air_combat_release_shaping_enabled")))
    self.assertGreater(float(rewards.get("air_combat_first_release_bonus", 0.0)), 0.0)
    self.assertLess(float(rewards.get("air_combat_invalid_fire_penalty", 0.0)), 0.0)
    self.assertLess(float(rewards.get("air_combat_repeat_release_penalty", 0.0)), 0.0)
    self.assertEqual(scenario.get("entities", [])[0].get("ammo", {}).get("missiles_remaining"), 4)
    self.assertEqual(scenario.get("entities", [])[1].get("ammo", {}).get("missiles_remaining"), 0)

  def test_stage1_c2_roe_probe_entry_is_discoverable_without_mutating_m1_baselines(self) -> None:
    c2_roe_configs = sorted(AIR_COMBAT_ACTIVE_DIR.glob("*c2_roe*.json"))
    c2_roe_scenarios = sorted((REPO_ROOT / "scenarios" / "air_combat" / "1v1").glob("*c2_roe*.json"))
    self.assertIn(STAGE1_C2_ROE_CONFIG, c2_roe_configs)
    self.assertIn(STAGE1_C2_ROE_TEMPORAL_CONFIG, c2_roe_configs)
    self.assertIn(STAGE1_C2_ROE_TEMPORAL_DEADLINE_CONFIG, c2_roe_configs)
    self.assertIn(STAGE1_C2_ROE_TEMPORAL_A7_EVENT_CREDIT_CONFIG, c2_roe_configs)
    self.assertIn(STAGE1_C2_ROE_SCENARIO, c2_roe_scenarios)

    cfg = _load_json(STAGE1_C2_ROE_CONFIG)
    scenario = _load_json(STAGE1_C2_ROE_SCENARIO)

    env = cfg.get("env")
    self.assertIsInstance(env, dict)
    self.assertEqual(env.get("mission_obs_mode"), "air_combat_c2_roe_v1")
    self.assertEqual(env.get("action_mode"), "air_combat_hybrid_v1")
    self.assertEqual(env.get("step_info_mode"), "full")
    self.assertEqual(env.get("execution_step_runtime_mode"), "compiled")
    self.assertEqual(env.get("flight_shaping_backend"), "compiled")
    self.assertTrue(bool(cfg.get("runtime", {}).get("world_batch_vec_env")))

    policy_kwargs = cfg.get("hyperparameters", {}).get("policy_kwargs", {})
    self.assertEqual(policy_kwargs.get("family_subexpert_counts"), [3, 2, 3, 1, 3])
    self.assertAlmostEqual(float(policy_kwargs.get("hmoe_head_lr_scale")), 0.35, places=6)
    self.assertAlmostEqual(float(policy_kwargs.get("hmoe_residual_start_factor")), 0.25, places=6)

    for baseline_path in (
      STAGE1_CONFIG,
      STAGE1_TEMPORAL_CONFIG,
      STAGE1_HYBRID_CONFIG,
      STAGE1_HYBRID_TEMPORAL_CONFIG,
      STAGE1_HYBRID_SHAPED_CONFIG,
      STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG,
    ):
      baseline_env = _load_json(baseline_path).get("env", {})
      self.assertEqual(baseline_env.get("mission_obs_mode"), "basic", baseline_path.name)

    realism = scenario.get("realism_gradient")
    self.assertIsInstance(realism, dict)
    self.assertEqual(realism.get("domain"), "air_combat")
    self.assertEqual(realism.get("workline"), "1v1")
    self.assertEqual(realism.get("stage"), "A1-S1")
    self.assertIn("c2_roe", realism.get("stage_name", ""))
    self.assertEqual(tuple(realism.get("engagement_range_m", [])), (20000.0, 40000.0))

    mission = scenario.get("mission_command")
    self.assertIsInstance(mission, dict)
    self.assertEqual(mission.get("assigned_target_name"), "Red_Target")
    self.assertEqual(int(mission.get("roe_state")), 2)
    self.assertEqual(int(mission.get("wcs_state")), 2)
    self.assertTrue(bool(mission.get("authorization_to_fire")))
    self.assertEqual(int(mission.get("engage_order_state")), 2)
    self.assertEqual(int(mission.get("target_identity_state")), 3)
    self.assertEqual(int(mission.get("shot_policy_state")), 1)
    self.assertEqual(int(mission.get("shot_budget_remaining")), 1)
    self.assertFalse(bool(mission.get("pending_assessment")))
    self.assertEqual(int(mission.get("own_missiles_in_flight_count")), 0)

    rewards = scenario.get("rewards", {})
    self.assertTrue(bool(rewards.get("air_combat_release_shaping_enabled")))
    self.assertTrue(bool(rewards.get("air_combat_c2_roe_release_discipline_enabled")))
    self.assertGreater(float(rewards.get("air_combat_first_release_bonus", 0.0)), 0.0)
    self.assertLess(float(rewards.get("air_combat_repeat_release_penalty", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_repeat_release_penalty", 0.0)), -50.0)
    self.assertEqual(float(rewards.get("air_combat_invalid_fire_penalty", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_valid_authorized_release_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_first_release_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_radar_active_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_tms_up_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_master_arm_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_weapon_selected_bonus", 0.0)), 0.0)
    self.assertGreater(float(rewards.get("air_combat_roe_authorized_fire_attempt_bonus", 0.0)), 0.0)
    self.assertLess(float(rewards.get("air_combat_roe_authorized_fire_no_release_penalty", 0.0)), 0.0)
    self.assertEqual(float(rewards.get("air_combat_roe_authorized_fire_opportunity_penalty", 0.0)), 0.0)
    for legality_key in (
      "air_combat_roe_hold_fire_bonus",
      "air_combat_roe_hold_fire_violation_penalty",
      "air_combat_roe_unauthorized_fire_penalty",
      "air_combat_roe_pending_assessment_penalty",
      "air_combat_roe_premature_second_shot_penalty",
      "air_combat_roe_shot_budget_violation_penalty",
    ):
      self.assertEqual(float(rewards.get(legality_key, 0.0)), 0.0, legality_key)
    self.assertEqual(scenario.get("entities", [])[0].get("ammo", {}).get("missiles_remaining"), 4)
    self.assertEqual(scenario.get("entities", [])[1].get("ammo", {}).get("missiles_remaining"), 0)

  def test_stage1_c2_roe_deadline_bootstrap_probe_keeps_a6_rescope_separate(self) -> None:
    baseline = _load_json(STAGE1_C2_ROE_TEMPORAL_CONFIG)
    deadline = _load_json(STAGE1_C2_ROE_TEMPORAL_DEADLINE_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(deadline.get(key), baseline.get(key), key)
    self.assertEqual(deadline.get("runtime"), baseline.get("runtime"))
    self.assertEqual(deadline.get("env"), baseline.get("env"))
    self.assertEqual(deadline.get("early_stop"), baseline.get("early_stop"))
    self.assertEqual(deadline.get("diagnostics"), baseline.get("diagnostics"))
    self.assertEqual(deadline.get("hmoe"), baseline.get("hmoe"))
    self.assertEqual(deadline.get("wrappers"), baseline.get("wrappers"))

    base_hyper = dict(baseline.get("hyperparameters", {}))
    deadline_hyper = dict(deadline.get("hyperparameters", {}))
    for key in ("a6_first_event_hazard_coef", "a6_first_event_curriculum_coef"):
      base_hyper.pop(key, None)
      deadline_hyper.pop(key, None)
    deadline_weight = deadline_hyper.pop("a6_first_event_deadline_weight", None)
    deadline_min_age = deadline_hyper.pop("a6_first_event_deadline_min_window_age_steps", None)
    base_hyper.pop("a6_first_event_curriculum_decay_fraction", None)
    base_hyper.pop("a6_first_event_curriculum_min_window_age_steps", None)
    self.assertEqual(deadline_hyper, base_hyper)
    self.assertGreater(float(deadline_weight), 0.0)
    self.assertEqual(int(deadline_min_age), 64)
    self.assertEqual(float(deadline.get("hyperparameters", {}).get("a6_first_event_curriculum_coef", 0.0)), 0.0)

  def test_stage1_c2_roe_event_head_probe_is_separate_from_deadline_baseline(self) -> None:
    deadline = _load_json(STAGE1_C2_ROE_TEMPORAL_DEADLINE_CONFIG)
    event_head = _load_json(STAGE1_C2_ROE_TEMPORAL_EVENT_HEAD_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(event_head.get(key), deadline.get(key), key)
    self.assertEqual(event_head.get("runtime"), deadline.get("runtime"))
    self.assertEqual(event_head.get("env"), deadline.get("env"))
    self.assertEqual(event_head.get("early_stop"), deadline.get("early_stop"))
    self.assertEqual(event_head.get("diagnostics"), deadline.get("diagnostics"))
    self.assertEqual(event_head.get("hmoe"), deadline.get("hmoe"))
    self.assertEqual(event_head.get("wrappers"), deadline.get("wrappers"))

    deadline_hyper = dict(deadline.get("hyperparameters", {}))
    event_hyper = dict(event_head.get("hyperparameters", {}))
    deadline_policy_kwargs = dict(deadline_hyper.get("policy_kwargs", {}))
    event_policy_kwargs = dict(event_hyper.get("policy_kwargs", {}))
    self.assertEqual(float(deadline_policy_kwargs.pop("hybrid_event_head_lr_scale", 0.0)), 0.0)
    self.assertAlmostEqual(float(event_policy_kwargs.pop("hybrid_event_head_lr_scale", 0.0)), 10.0, places=6)
    self.assertEqual(deadline_policy_kwargs, event_policy_kwargs)
    deadline_hyper["policy_kwargs"] = deadline_policy_kwargs
    event_hyper["policy_kwargs"] = event_policy_kwargs
    self.assertEqual(event_hyper, deadline_hyper)

  def test_stage1_c2_roe_launch_window_probe_is_separate_from_event_head_baseline(self) -> None:
    event_head = _load_json(STAGE1_C2_ROE_TEMPORAL_EVENT_HEAD_CONFIG)
    launch_window = _load_json(STAGE1_C2_ROE_TEMPORAL_LAUNCH_WINDOW_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(launch_window.get(key), event_head.get(key), key)
    self.assertEqual(launch_window.get("runtime"), event_head.get("runtime"))
    self.assertEqual(launch_window.get("env"), event_head.get("env"))
    self.assertEqual(launch_window.get("early_stop"), event_head.get("early_stop"))
    self.assertEqual(launch_window.get("diagnostics"), event_head.get("diagnostics"))
    self.assertEqual(launch_window.get("hmoe"), event_head.get("hmoe"))
    self.assertEqual(launch_window.get("wrappers"), event_head.get("wrappers"))

    event_hyper = dict(event_head.get("hyperparameters", {}))
    launch_hyper = dict(launch_window.get("hyperparameters", {}))
    launch_knobs = {
      key: launch_hyper.pop(key, None)
      for key in (
        "a6_first_event_launch_window_enabled",
        "a6_first_event_launch_window_min_range_m",
        "a6_first_event_launch_window_max_range_m",
        "a6_first_event_launch_window_max_track_age_s",
        "a6_first_event_launch_window_min_window_age_steps",
        "a6_first_event_launch_window_prewindow_hold_weight",
        "a6_first_event_launch_window_early_accept_weight",
      )
    }
    self.assertEqual(launch_hyper, event_hyper)
    self.assertTrue(bool(launch_knobs["a6_first_event_launch_window_enabled"]))
    self.assertGreater(float(launch_knobs["a6_first_event_launch_window_min_range_m"]), 0.0)
    self.assertGreater(float(launch_knobs["a6_first_event_launch_window_max_range_m"]), 0.0)
    self.assertGreater(float(launch_knobs["a6_first_event_launch_window_prewindow_hold_weight"]), 0.0)

  def test_stage1_c2_roe_a7_event_credit_probe_is_separate_from_a6_launch_window_baseline(self) -> None:
    launch_window = _load_json(STAGE1_C2_ROE_TEMPORAL_LAUNCH_WINDOW_CONFIG)
    a7_credit = _load_json(STAGE1_C2_ROE_TEMPORAL_A7_EVENT_CREDIT_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(a7_credit.get(key), launch_window.get(key), key)
    self.assertEqual(a7_credit.get("runtime"), launch_window.get("runtime"))
    self.assertEqual(a7_credit.get("env"), launch_window.get("env"))
    self.assertEqual(a7_credit.get("early_stop"), launch_window.get("early_stop"))
    self.assertEqual(a7_credit.get("diagnostics"), launch_window.get("diagnostics"))
    self.assertEqual(a7_credit.get("hmoe"), launch_window.get("hmoe"))
    self.assertEqual(a7_credit.get("wrappers"), launch_window.get("wrappers"))

    launch_hyper = dict(launch_window.get("hyperparameters", {}))
    a7_hyper = dict(a7_credit.get("hyperparameters", {}))
    launch_policy_kwargs = dict(launch_hyper.pop("policy_kwargs", {}))
    a7_policy_kwargs = dict(a7_hyper.pop("policy_kwargs", {}))
    self.assertEqual(float(launch_policy_kwargs.get("hybrid_event_credit_head_lr_scale", 0.0)), 0.0)
    self.assertAlmostEqual(float(a7_policy_kwargs.pop("hybrid_event_credit_head_lr_scale", 0.0)), 6.0, places=6)
    self.assertEqual(a7_policy_kwargs, launch_policy_kwargs)

    for key in (
      "a6_first_event_launch_window_enabled",
      "a6_first_event_launch_window_min_range_m",
      "a6_first_event_launch_window_max_range_m",
      "a6_first_event_launch_window_max_track_age_s",
      "a6_first_event_launch_window_min_window_age_steps",
    ):
      self.assertEqual(a7_hyper.get(key), launch_hyper.get(key), key)
    self.assertEqual(float(a7_hyper.get("a6_first_event_hazard_coef", -1.0)), 0.0)
    self.assertEqual(float(a7_hyper.get("a6_first_event_deadline_weight", -1.0)), 0.0)
    self.assertGreater(float(launch_hyper.get("a6_first_event_hazard_coef", 0.0)), 0.0)
    self.assertGreater(float(launch_hyper.get("a6_first_event_deadline_weight", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_credit_value_coef", 0.0)), 0.0)
    self.assertEqual(float(a7_hyper.get("a7_event_credit_delta_align_coef", -1.0)), 0.0)
    self.assertTrue(bool(a7_hyper.get("a7_event_credit_delta_align_positive_only")))
    self.assertGreater(float(a7_hyper.get("a7_event_credit_deadline_weight", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_credit_shadow_quality_weight", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_credit_legal_open_quality_weight", 0.0)), 0.0)
    self.assertGreater(int(a7_hyper.get("a7_event_credit_legal_open_quality_min_window_age_steps", 0)), 1)
    self.assertTrue(bool(a7_hyper.get("a7_event_credit_legal_projection_enabled")))
    self.assertGreater(float(a7_hyper.get("a7_event_credit_projection_value_coef", 0.0)), 0.0)
    self.assertEqual(float(a7_hyper.get("a7_event_credit_projection_delta_align_coef", -1.0)), 0.0)
    self.assertTrue(bool(a7_hyper.get("a7_event_credit_separate_update_enabled")))
    self.assertGreater(float(a7_hyper.get("a7_event_credit_separate_update_max_grad_norm", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_policy_margin_coef", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_policy_margin", 0.0)), 0.0)
    self.assertGreater(float(a7_hyper.get("a7_event_policy_projection_margin_coef", 0.0)), 0.0)
    self.assertTrue(bool(a7_hyper.get("a7_event_policy_separate_update_enabled")))
    self.assertGreater(float(a7_hyper.get("a7_event_policy_separate_update_max_grad_norm", 0.0)), 0.0)
    self.assertGreater(int(a7_hyper.get("a7_event_policy_separate_update_steps", 0)), 1)

  def test_stage1_c2_roe_a7_state_completed_probe_changes_only_mission_obs_mode(self) -> None:
    baseline = _load_json(STAGE1_C2_ROE_TEMPORAL_A7_EVENT_CREDIT_CONFIG)
    state_completed = _load_json(STAGE1_C2_ROE_TEMPORAL_A7_STATE_COMPLETED_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(state_completed.get(key), baseline.get(key), key)
    self.assertEqual(state_completed.get("runtime"), baseline.get("runtime"))
    self.assertEqual(state_completed.get("early_stop"), baseline.get("early_stop"))
    self.assertEqual(state_completed.get("diagnostics"), baseline.get("diagnostics"))
    self.assertEqual(state_completed.get("hmoe"), baseline.get("hmoe"))
    self.assertEqual(state_completed.get("wrappers"), baseline.get("wrappers"))
    self.assertEqual(state_completed.get("hyperparameters"), baseline.get("hyperparameters"))

    env = dict(state_completed.get("env", {}))
    baseline_env = dict(baseline.get("env", {}))
    self.assertEqual(env.pop("mission_obs_mode"), "air_combat_c2_roe_v2")
    self.assertEqual(baseline_env.pop("mission_obs_mode"), "air_combat_c2_roe_v1")
    self.assertEqual(env, baseline_env)

  def test_stage1_m3s1_grouped_stopping_probe_extends_state_completed_config_only(self) -> None:
    state_completed = _load_json(STAGE1_C2_ROE_TEMPORAL_A7_STATE_COMPLETED_CONFIG)
    m3s1 = _load_json(STAGE1_C2_ROE_TEMPORAL_M3S1_GROUPED_STOPPING_CONFIG)

    for key in ("agent_layer", "algo", "policy", "n_envs"):
      self.assertEqual(m3s1.get(key), state_completed.get(key), key)
    self.assertEqual(int(m3s1.get("total_timesteps")), 8192)
    self.assertLess(int(m3s1.get("total_timesteps")), int(state_completed.get("total_timesteps")))
    self.assertEqual(m3s1.get("runtime"), state_completed.get("runtime"))
    self.assertEqual(m3s1.get("env"), state_completed.get("env"))
    self.assertEqual(m3s1.get("early_stop"), state_completed.get("early_stop"))
    self.assertEqual(m3s1.get("diagnostics"), state_completed.get("diagnostics"))
    self.assertEqual(m3s1.get("hmoe"), state_completed.get("hmoe"))
    self.assertEqual(m3s1.get("wrappers"), state_completed.get("wrappers"))

    state_hyper = dict(state_completed.get("hyperparameters", {}))
    m3_hyper = dict(m3s1.get("hyperparameters", {}))
    state_policy_kwargs = dict(state_hyper.pop("policy_kwargs", {}))
    m3_policy_kwargs = dict(m3_hyper.pop("policy_kwargs", {}))
    self.assertAlmostEqual(float(m3_policy_kwargs.pop("m3_stopping_head_lr_scale", 0.0)), 5.0, places=6)
    self.assertNotIn("m3_stopping_head_lr_scale", state_policy_kwargs)
    self.assertEqual(m3_policy_kwargs, state_policy_kwargs)

    m3_knobs = {
      key: m3_hyper.pop(key, None)
      for key in (
        "m3s1_grouped_stopping_coef",
        "m3s1_grouped_stopping_early_mass_coef",
        "m3s1_grouped_stopping_early_mass_budget",
        "m3s1_grouped_stopping_no_event_coef",
        "m3s1_grouped_stopping_boundary_threshold",
        "m3s1_grouped_stopping_detach_latent",
      )
    }
    self.assertEqual(m3_hyper, state_hyper)
    self.assertAlmostEqual(float(m3_knobs["m3s1_grouped_stopping_coef"]), 1.0, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s1_grouped_stopping_early_mass_budget"]), 0.05, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s1_grouped_stopping_boundary_threshold"]), 0.0, places=6)
    self.assertFalse(bool(m3_knobs["m3s1_grouped_stopping_detach_latent"]))

  def test_stage1_m3s2_event_window_probe_extends_state_completed_config_only(self) -> None:
    state_completed = _load_json(STAGE1_C2_ROE_TEMPORAL_A7_STATE_COMPLETED_CONFIG)
    m3s2 = _load_json(STAGE1_C2_ROE_TEMPORAL_M3S2_EVENT_WINDOW_CONFIG)

    for key in ("agent_layer", "algo", "policy", "n_envs"):
      self.assertEqual(m3s2.get(key), state_completed.get(key), key)
    self.assertEqual(int(m3s2.get("total_timesteps")), 8192)
    self.assertLess(int(m3s2.get("total_timesteps")), int(state_completed.get("total_timesteps")))
    self.assertEqual(m3s2.get("runtime"), state_completed.get("runtime"))
    self.assertEqual(m3s2.get("env"), state_completed.get("env"))
    self.assertEqual(m3s2.get("early_stop"), state_completed.get("early_stop"))
    self.assertEqual(m3s2.get("diagnostics"), state_completed.get("diagnostics"))
    self.assertEqual(m3s2.get("hmoe"), state_completed.get("hmoe"))
    self.assertEqual(m3s2.get("wrappers"), state_completed.get("wrappers"))

    state_hyper = dict(state_completed.get("hyperparameters", {}))
    m3_hyper = dict(m3s2.get("hyperparameters", {}))
    state_policy_kwargs = dict(state_hyper.pop("policy_kwargs", {}))
    m3_policy_kwargs = dict(m3_hyper.pop("policy_kwargs", {}))
    self.assertFalse(bool(m3_policy_kwargs.pop("hybrid_event_use_m3_stopping_head", True)))
    self.assertFalse(bool(m3_policy_kwargs.pop("hybrid_event_use_m3_window_classifier_head", True)))
    self.assertEqual(m3_policy_kwargs, state_policy_kwargs)

    m3_knobs = {
      key: m3_hyper.pop(key, None)
      for key in (
        "m3s2_fire_boundary_coef",
        "m3s2_fire_boundary_negative_logit_ceiling_coef",
        "m3s2_fire_boundary_negative_logit_ceiling",
        "m3s2_fire_boundary_positive_logit_floor_coef",
        "m3s2_fire_boundary_positive_logit_floor",
        "m3s2_fire_boundary_separate_update_enabled",
        "m3s2_fire_boundary_dedicated_optimizer_enabled",
        "m3s2_fire_boundary_separate_update_steps",
        "m3s2_fire_boundary_max_grad_norm",
        "m3s2_fire_boundary_support_preserving_collect_enabled",
        "m3s2_fire_boundary_support_preserving_hold_quality_enabled",
      )
    }
    self.assertEqual(m3_hyper, state_hyper)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_coef"]), 20.0, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_negative_logit_ceiling_coef"]), 5.0, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_negative_logit_ceiling"]), -2.0, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_positive_logit_floor_coef"]), 5.0, places=6)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_positive_logit_floor"]), 2.0, places=6)
    self.assertTrue(bool(m3_knobs["m3s2_fire_boundary_separate_update_enabled"]))
    self.assertTrue(bool(m3_knobs["m3s2_fire_boundary_dedicated_optimizer_enabled"]))
    self.assertEqual(int(m3_knobs["m3s2_fire_boundary_separate_update_steps"]), 32)
    self.assertAlmostEqual(float(m3_knobs["m3s2_fire_boundary_max_grad_norm"]), 5.0, places=6)
    self.assertTrue(bool(m3_knobs["m3s2_fire_boundary_support_preserving_collect_enabled"]))
    self.assertTrue(bool(m3_knobs["m3s2_fire_boundary_support_preserving_hold_quality_enabled"]))
    self.assertEqual(_violation_dicts(m3s2), [])

  def test_stage1_m3s2_model_contract_names_fault_localization_gates(self) -> None:
    m3s2 = _load_json(STAGE1_C2_ROE_TEMPORAL_M3S2_EVENT_WINDOW_CONFIG)
    contracts = active_model_contracts_for_config(m3s2)

    self.assertEqual([contract.mechanism_id for contract in contracts], ["m3s2.direct_fire_boundary_event_head"])
    contract = contracts[0]
    self.assertEqual(contract.role, MechanismRole.EXECUTABLE)
    self.assertIn(FaultStage.LABEL, contract.required_probe_stages)
    self.assertIn(FaultStage.OPTIMIZER, contract.required_probe_stages)
    self.assertIn(FaultStage.ADAPTER, contract.required_probe_stages)
    self.assertIn(FaultStage.EVALUATION, contract.required_probe_stages)
    self.assertIn("executable fire boundary", contract.held_boundary)

  def test_stage1_m3s2_contract_blocks_adapter_override(self) -> None:
    m3s2 = _load_json(STAGE1_C2_ROE_TEMPORAL_M3S2_EVENT_WINDOW_CONFIG)
    policy_kwargs = m3s2["hyperparameters"]["policy_kwargs"]
    policy_kwargs["hybrid_event_use_m3_window_classifier_head"] = True

    violations = _violation_dicts(m3s2)

    self.assertIn(
      {
        "mechanism_id": "m3s2.direct_fire_boundary_event_head",
        "path": "hyperparameters.policy_kwargs.hybrid_event_use_m3_window_classifier_head",
        "expected": "false",
        "actual": True,
        "reason": "Direct fire boundary owns executable hold/fire logits and must not be overridden by classifier adapter.",
      },
      violations,
    )

  def test_air_combat_active_training_entries_satisfy_model_contract_gates(self) -> None:
    for config_path in sorted(AIR_COMBAT_ACTIVE_DIR.glob("*.json")):
      with self.subTest(config=config_path.name):
        cfg = _load_json(config_path)
        self.assertEqual(_violation_dicts(cfg), [])

  def test_stage1_c2_roe_temporal_probe_pairs_with_c2_roe_reactive_baseline(self) -> None:
    c2_roe = _load_json(STAGE1_C2_ROE_CONFIG)
    c2_roe_temporal = _load_json(STAGE1_C2_ROE_TEMPORAL_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(c2_roe_temporal.get(key), c2_roe.get(key), key)
    self.assertEqual(c2_roe_temporal.get("runtime"), c2_roe.get("runtime"))
    self.assertEqual(c2_roe_temporal.get("early_stop"), c2_roe.get("early_stop"))
    self.assertEqual(c2_roe_temporal.get("diagnostics"), c2_roe.get("diagnostics"))
    self.assertEqual(c2_roe_temporal.get("hmoe"), c2_roe.get("hmoe"))
    self.assertEqual(c2_roe_temporal.get("wrappers"), c2_roe.get("wrappers"))

    c2_roe_env = dict(c2_roe.get("env", {}))
    c2_roe_temporal_env = dict(c2_roe_temporal.get("env", {}))
    self.assertEqual(int(c2_roe_temporal_env.pop("temporal_history_len")), 16)
    self.assertEqual(c2_roe_temporal_env, c2_roe_env)

    c2_roe_hyper = dict(c2_roe.get("hyperparameters", {}))
    c2_roe_temporal_hyper = dict(c2_roe_temporal.get("hyperparameters", {}))
    c2_roe_policy_kwargs = dict(c2_roe_hyper.pop("policy_kwargs"))
    c2_roe_temporal_policy_kwargs = dict(c2_roe_temporal_hyper.pop("policy_kwargs"))
    self.assertEqual(c2_roe_temporal_hyper, c2_roe_hyper)
    self.assertEqual(c2_roe_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(c2_roe_temporal_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(c2_roe_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
    self.assertEqual(c2_roe_temporal_policy_kwargs.get("features_extractor_class"), "TemporalTransformerExtractor")
    self.assertEqual(
      c2_roe_temporal_policy_kwargs.get("family_subexpert_counts"),
      c2_roe_policy_kwargs.get("family_subexpert_counts"),
    )
    self.assertEqual(c2_roe_temporal_policy_kwargs.get("net_arch"), c2_roe_policy_kwargs.get("net_arch"))
    self.assertEqual(c2_roe_temporal_policy_kwargs.get("log_std_init"), c2_roe_policy_kwargs.get("log_std_init"))
    temporal_extractor = c2_roe_temporal_policy_kwargs.get("features_extractor_kwargs", {})
    reactive_extractor = c2_roe_policy_kwargs.get("features_extractor_kwargs", {})
    self.assertEqual(int(temporal_extractor.get("features_dim")), int(reactive_extractor.get("features_dim")))
    self.assertEqual(int(temporal_extractor.get("n_heads")), int(reactive_extractor.get("n_heads")))
    self.assertEqual(int(temporal_extractor.get("n_layers")), int(reactive_extractor.get("n_layers")))
    self.assertEqual(int(temporal_extractor.get("temporal_n_heads")), 4)
    self.assertEqual(int(temporal_extractor.get("temporal_n_layers")), 2)

  def test_stage1_bvr_hybrid_temporal_shaped_probe_pairs_with_hybrid_shaped_baseline(self) -> None:
    shaped = _load_json(STAGE1_HYBRID_SHAPED_CONFIG)
    temporal_shaped = _load_json(STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG)

    for key in ("agent_layer", "algo", "policy", "total_timesteps", "n_envs", "save_freq"):
      self.assertEqual(temporal_shaped.get(key), shaped.get(key), key)
    self.assertEqual(temporal_shaped.get("runtime"), shaped.get("runtime"))
    self.assertEqual(temporal_shaped.get("early_stop"), shaped.get("early_stop"))
    self.assertEqual(temporal_shaped.get("diagnostics"), shaped.get("diagnostics"))
    self.assertEqual(temporal_shaped.get("hmoe"), shaped.get("hmoe"))
    self.assertEqual(temporal_shaped.get("wrappers"), shaped.get("wrappers"))

    shaped_env = dict(shaped.get("env", {}))
    temporal_shaped_env = dict(temporal_shaped.get("env", {}))
    self.assertEqual(int(temporal_shaped_env.pop("temporal_history_len")), 16)
    self.assertEqual(temporal_shaped_env, shaped_env)

    shaped_hyper = dict(shaped.get("hyperparameters", {}))
    temporal_shaped_hyper = dict(temporal_shaped.get("hyperparameters", {}))
    shaped_policy_kwargs = dict(shaped_hyper.pop("policy_kwargs"))
    temporal_shaped_policy_kwargs = dict(temporal_shaped_hyper.pop("policy_kwargs"))
    self.assertEqual(temporal_shaped_hyper, shaped_hyper)
    self.assertEqual(shaped_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(temporal_shaped_policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
    self.assertEqual(shaped_policy_kwargs.get("features_extractor_class"), "TransformerExtractor")
    self.assertEqual(temporal_shaped_policy_kwargs.get("features_extractor_class"), "TemporalTransformerExtractor")
    self.assertEqual(
      temporal_shaped_policy_kwargs.get("family_subexpert_counts"),
      shaped_policy_kwargs.get("family_subexpert_counts"),
    )
    self.assertEqual(temporal_shaped_policy_kwargs.get("net_arch"), shaped_policy_kwargs.get("net_arch"))
    self.assertEqual(temporal_shaped_policy_kwargs.get("log_std_init"), shaped_policy_kwargs.get("log_std_init"))
    temporal_extractor = temporal_shaped_policy_kwargs.get("features_extractor_kwargs", {})
    shaped_extractor = shaped_policy_kwargs.get("features_extractor_kwargs", {})
    self.assertEqual(int(temporal_extractor.get("features_dim")), int(shaped_extractor.get("features_dim")))
    self.assertEqual(int(temporal_extractor.get("n_heads")), int(shaped_extractor.get("n_heads")))
    self.assertEqual(int(temporal_extractor.get("n_layers")), int(shaped_extractor.get("n_layers")))
    self.assertEqual(int(temporal_extractor.get("temporal_n_heads")), 4)
    self.assertEqual(int(temporal_extractor.get("temporal_n_layers")), 2)

  def test_stage1_bvr_probe_bootstraps_on_current_execution_path(self) -> None:
    entries = [
      (
        "f16_tg_p7_target_geometry_proxy",
        F16_SCRIPTED_RED_TG_P7_PROXY_CONFIG,
        F16_SCRIPTED_RED_SCENARIO,
      ),
      (
        "f16_scripted_red_baseline_32k",
        F16_SCRIPTED_RED_BASELINE_32K_CONFIG,
        F16_SCRIPTED_RED_SCENARIO,
      ),
      (
        "f16_tg_p7_target_geometry_proxy_32k",
        F16_SCRIPTED_RED_TG_P7_PROXY_32K_CONFIG,
        F16_SCRIPTED_RED_SCENARIO,
      ),
      ("reactive", STAGE1_CONFIG, STAGE1_SCENARIO),
      ("temporal", STAGE1_TEMPORAL_CONFIG, STAGE1_SCENARIO),
      ("hybrid", STAGE1_HYBRID_CONFIG, STAGE1_SCENARIO),
      ("hybrid_temporal", STAGE1_HYBRID_TEMPORAL_CONFIG, STAGE1_SCENARIO),
      ("hybrid_shaped", STAGE1_HYBRID_SHAPED_CONFIG, STAGE1_SHAPED_SCENARIO),
      ("hybrid_temporal_shaped", STAGE1_HYBRID_TEMPORAL_SHAPED_CONFIG, STAGE1_SHAPED_SCENARIO),
      ("c2_roe_hybrid_shaped", STAGE1_C2_ROE_CONFIG, STAGE1_C2_ROE_SCENARIO),
      ("c2_roe_hybrid_temporal_shaped", STAGE1_C2_ROE_TEMPORAL_CONFIG, STAGE1_C2_ROE_SCENARIO),
      ("c2_roe_hybrid_temporal_deadline_shaped", STAGE1_C2_ROE_TEMPORAL_DEADLINE_CONFIG, STAGE1_C2_ROE_SCENARIO),
      ("c2_roe_hybrid_temporal_event_head_shaped", STAGE1_C2_ROE_TEMPORAL_EVENT_HEAD_CONFIG, STAGE1_C2_ROE_SCENARIO),
      (
        "c2_roe_hybrid_temporal_launch_window_shaped",
        STAGE1_C2_ROE_TEMPORAL_LAUNCH_WINDOW_CONFIG,
        STAGE1_C2_ROE_SCENARIO,
      ),
      (
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped",
        STAGE1_C2_ROE_TEMPORAL_A7_EVENT_CREDIT_CONFIG,
        STAGE1_C2_ROE_SCENARIO,
      ),
      (
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed",
        STAGE1_C2_ROE_TEMPORAL_A7_STATE_COMPLETED_CONFIG,
        STAGE1_C2_ROE_SCENARIO,
      ),
      (
        "c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed",
        STAGE1_C2_ROE_TEMPORAL_M3S1_GROUPED_STOPPING_CONFIG,
        STAGE1_C2_ROE_SCENARIO,
      ),
      (
        "c2_roe_hybrid_temporal_m3s2_event_window_state_completed",
        STAGE1_C2_ROE_TEMPORAL_M3S2_EVENT_WINDOW_CONFIG,
        STAGE1_C2_ROE_SCENARIO,
      ),
    ]
    for label, config_path, scenario_path in entries:
      with self.subTest(label=label), tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run(
          [
            sys.executable,
            str(REPO_ROOT / "train.py"),
            "--scenario",
            str(scenario_path),
            "--train_config",
            str(config_path),
            "--output_base",
            tmpdir,
            "--run_name",
            f"air_combat_stage1_bvr_{label}_probe_bootstrap",
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
      self.assertIn("World batch runtime:", proc.stdout)
      self.assertIn("Execution reward runtime: requested_backend=compiled effective_backend=compiled", proc.stdout)
      if label in {
        "hybrid",
        "hybrid_temporal",
        "hybrid_shaped",
        "hybrid_temporal_shaped",
        "c2_roe_hybrid_shaped",
        "c2_roe_hybrid_temporal_shaped",
        "c2_roe_hybrid_temporal_deadline_shaped",
        "c2_roe_hybrid_temporal_event_head_shaped",
        "c2_roe_hybrid_temporal_launch_window_shaped",
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped",
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed",
        "c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed",
        "c2_roe_hybrid_temporal_m3s2_event_window_state_completed",
      }:
        self.assertIn("action_mode=air_combat_hybrid_v1", proc.stdout)
      if label in {
        "temporal",
        "hybrid_temporal",
        "hybrid_temporal_shaped",
        "c2_roe_hybrid_temporal_shaped",
        "c2_roe_hybrid_temporal_deadline_shaped",
        "c2_roe_hybrid_temporal_event_head_shaped",
        "c2_roe_hybrid_temporal_launch_window_shaped",
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped",
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed",
        "c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed",
        "c2_roe_hybrid_temporal_m3s2_event_window_state_completed",
      }:
        self.assertIn("temporal_history_len=16", proc.stdout)
      if label in {
        "c2_roe_hybrid_shaped",
        "c2_roe_hybrid_temporal_shaped",
        "c2_roe_hybrid_temporal_deadline_shaped",
        "c2_roe_hybrid_temporal_event_head_shaped",
        "c2_roe_hybrid_temporal_launch_window_shaped",
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped",
      }:
        self.assertIn("mission_obs_mode=air_combat_c2_roe_v1", proc.stdout)
      if label in {
        "c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed",
        "c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed",
        "c2_roe_hybrid_temporal_m3s2_event_window_state_completed",
      }:
        self.assertIn("mission_obs_mode=air_combat_c2_roe_v2", proc.stdout)
      if label in {"f16_tg_p7_target_geometry_proxy", "f16_tg_p7_target_geometry_proxy_32k"}:
        self.assertIn("World batch database: path=", proc.stdout)
        self.assertIn("target_geometry_training_proxy_database_20260613", proc.stdout)
      self.assertIn("Error: --test_only requires --resume_path", proc.stdout)


if __name__ == "__main__":
  unittest.main()
