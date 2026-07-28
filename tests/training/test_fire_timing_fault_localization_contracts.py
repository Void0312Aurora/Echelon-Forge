from __future__ import annotations

import unittest

import torch as th
from torch import nn

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics.fire_timing_fault_localization import learnability_audit as audit # noqa: E402
from tools.diagnostics.fire_timing_fault_localization import window_position_sweep # noqa: E402
from tools.diagnostics import lethality_chain_contract # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.chain_breakpoint import ( # noqa: E402
  _classification_metrics,
  _edge_trigger_summary,
  _fault_localization_summary,
  _head_module,
  _install_head,
  _masks_from_groups,
  _passes_window_classifier,
  _resolve_adapter_head_kind,
)
from tools.diagnostics.fire_timing_fault_localization.real_update import RealM3S2Group # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.real_update import _build_groups_from_rows # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.real_update import _collector_action_for_m3s2 # noqa: E402
from tools.diagnostics.fire_timing_fault_localization.structural_toy import ToyProbeConfig, run_probe # noqa: E402


class AirCombatFireTimingLearnabilityAuditTests(unittest.TestCase):
  def test_verdict_identifies_reachable_release_but_unidentifiable_legal_timing(self) -> None:
    summaries = [
      {
        "case": "hold_fire",
        "mode": "hold_fire",
        "mean_total_reward": 70.0,
        "release_episode_count": 0,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
      {
        "case": "forced_fire_edge_at_reset",
        "mode": "forced_fire",
        "mean_total_reward": 70.0,
        "release_episode_count": 0,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {"no_target": 2},
      },
      {
        "case": "legal_mask_fire_delay_0",
        "mode": "legal_mask_fire",
        "fire_delay_steps": 0,
        "mean_total_reward": 520.0,
        "release_episode_count": 2,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
      {
        "case": "legal_mask_fire_delay_63",
        "mode": "legal_mask_fire",
        "fire_delay_steps": 63,
        "mean_total_reward": 520.25,
        "release_episode_count": 2,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "target_health_drop_episode_count": 0,
        "rejected_reason_counts": {},
      },
    ]

    verdict = audit._learnability_verdict(summaries, reward_epsilon=1.0)

    self.assertEqual(verdict["primary_breakpoint"], "legal_timing_unidentifiable_from_current_return")
    self.assertTrue(verdict["release_reachable_with_legal_oracle"])
    self.assertTrue(verdict["release_vs_hold_reward_distinguishable"])
    self.assertFalse(verdict["post_release_effect_observable"])
    self.assertFalse(verdict["legal_timing_reward_distinguishable"])
    self.assertTrue(verdict["edge_trigger_adapter_hazard"])

  def test_case_summary_counts_release_effects_and_rejection_reasons(self) -> None:
    summary = audit._case_summary(
      "legal_mask_fire_delay_0",
      {
        "mode": "legal_mask_fire",
        "fire_delay_steps": 0,
        "legal_fire_range_m": 0.0,
        "episode_summaries": [
          {
            "total_reward": 10.0,
            "final_target_health": 80.0,
            "release_count": 1,
            "fire_once_accepted_count": 1,
            "fire_once_rejected_count": 0,
            "effects_event_count": 1,
            "damage_report_count": 1,
            "first_release_step": 5,
            "first_effects_event_step": 40,
            "first_target_health_drop_step": 40,
            "release_steps": [5],
            "fire_once_rejected_reason_counts": {},
          },
          {
            "total_reward": 8.0,
            "final_target_health": 100.0,
            "release_count": 0,
            "fire_once_accepted_count": 0,
            "fire_once_rejected_count": 1,
            "effects_event_count": 0,
            "damage_report_count": 0,
            "first_release_step": None,
            "first_effects_event_step": None,
            "first_target_health_drop_step": None,
            "release_steps": [],
            "fire_once_rejected_reason_counts": {"no_target": 1},
          },
        ],
      },
    )

    self.assertEqual(summary["episodes"], 2)
    self.assertAlmostEqual(summary["mean_total_reward"], 9.0)
    self.assertAlmostEqual(summary["mean_release_count"], 0.5)
    self.assertEqual(summary["release_episode_count"], 1)
    self.assertEqual(summary["effects_episode_count"], 1)
    self.assertEqual(summary["damage_episode_count"], 1)
    self.assertEqual(summary["target_health_drop_episode_count"], 1)
    self.assertEqual(summary["release_steps"], [5])
    self.assertEqual(summary["rejected_reason_counts"], {"no_target": 1})


class AirCombatFireTimingWindowPositionSweepTests(unittest.TestCase):
  def test_window_position_uses_standardized_lethality_chain_vocabulary(self) -> None:
    self.assertIn("fuze", lethality_chain_contract.CANONICAL_STAGES)
    self.assertIn("fuze", lethality_chain_contract.DIAGNOSTIC_ROW_STAGES)
    self.assertNotIn(
      "training_projection",
      lethality_chain_contract.DIAGNOSTIC_ROW_STAGES,
    )
    self.assertIn(
      "component_damage",
      lethality_chain_contract.EFFECTIVE_DETONATION_STAGES,
    )
    self.assertIn(
      "miss_outside_trigger_radius",
      lethality_chain_contract.TERMINAL_NEGATIVE_REASONS,
    )

  def test_window_position_verdict_requires_geometry_and_outcome_variation(self) -> None:
    delay_summaries = [
      {
        "delay_steps": 0,
        "release_episode_count": 1,
        "mean_release_range_geom_m": 9000.0,
        "mean_total_reward": 100.0,
        "mean_final_target_health": 100.0,
        "mean_damage_consequence_reward_total": 0.0,
        "mean_component_failure_probability": 0.05,
        "effects_episode_count": 0,
        "damage_episode_count": 0,
        "effective_detonation_episode_count": 0,
        "effective_component_damage_episode_count": 0,
        "effective_system_consequence_episode_count": 0,
        "mission_kill_episode_count": 0,
        "destroyed_episode_count": 0,
      },
      {
        "delay_steps": 512,
        "release_episode_count": 1,
        "mean_release_range_geom_m": 6200.0,
        "mean_total_reward": 112.0,
        "mean_final_target_health": 91.0,
        "mean_damage_consequence_reward_total": 6.0,
        "mean_component_failure_probability": 0.21,
        "effects_episode_count": 1,
        "damage_episode_count": 1,
        "effective_detonation_episode_count": 1,
        "effective_component_damage_episode_count": 1,
        "effective_system_consequence_episode_count": 1,
        "mission_kill_episode_count": 0,
        "destroyed_episode_count": 0,
      },
    ]

    verdict = window_position_sweep._sweep_verdict(
      delay_summaries,
      reward_epsilon=1.0,
      health_epsilon=1.0,
      system_health_delta_epsilon=0.1,
      component_failure_probability_epsilon=0.05,
      miss_distance_epsilon_m=1.0,
      range_epsilon_m=500.0,
    )

    self.assertTrue(verdict["release_position_variation_observed"])
    self.assertTrue(verdict["outcome_variation_observed"])
    self.assertTrue(verdict["categorical_effect_change"])
    self.assertTrue(verdict["learnability_candidate"])

  def test_window_position_record_preserves_release_geometry_snapshot(self) -> None:
    record = window_position_sweep._record_from_episode_summary(
      delay=128,
      payload={"mode": "legal_mask_fire", "seed": 7},
      episode_summary={
        "episode": 3,
        "release_count": 1,
        "first_release_step": 42,
        "first_release_sim_time_s": 8.4,
        "first_release_target_range_geom_m": 7100.0,
        "first_release_target_range_track_m": 7050.0,
        "first_release_target_track_age_s": 0.2,
        "first_release_legal_window_age_steps": 12,
        "first_release_engagement_state": "AuthorizedReady",
        "total_reward": 22.0,
        "final_target_health": 80.0,
        "first_release_target_health": 100.0,
        "effects_event_count": 1,
        "damage_report_count": 1,
        "lethality_chain_row_count": 7,
        "lethality_chain_chain_count": 1,
        "lethality_chain_stages_json": '["fuze","warhead_mechanism","spatial_coverage","component_load"]',
        "lethality_chain_miss_distance_m": 3.0,
        "lethality_chain_fuze_type": "radar_proximity",
        "lethality_chain_fuze_triggered": True,
        "lethality_chain_fuze_failure_reason": "",
        "lethality_chain_fuze_delay_s": 0.015,
        "lethality_chain_fuze_reliability": 0.94,
        "lethality_chain_fuze_sample": 0.58,
        "lethality_chain_fuze_expected_detonation_probability": 0.62,
        "lethality_chain_fuze_sampled_outcome": True,
        "lethality_chain_fuze_trigger_radius_m": 15.0,
        "lethality_chain_projected_hitbox_count": 3,
        "lethality_chain_component_hit_count": 1,
        "lethality_chain_component_name": "right_aileron_actuator",
        "lethality_chain_component_system": "flight_control",
        "lethality_chain_component_damage_count": 0,
        "lethality_chain_component_damage_name": "",
        "lethality_chain_component_damage_system": "",
        "lethality_chain_component_failure_mode": "cut",
        "lethality_chain_component_failure_severity": 0.7,
        "lethality_chain_component_failure_probability": 0.3,
        "lethality_chain_component_failure_sample": 0.8,
        "lethality_chain_component_integrity_before": 1.0,
        "lethality_chain_component_integrity_after": 0.72,
        "lethality_chain_system_health_delta": -20.0,
        "lethality_chain_mission_capability_before": 1.0,
        "lethality_chain_mission_capability_after": 0.8,
        "lethality_chain_mission_capability_delta": -0.2,
        "lethality_chain_mobility_capability_before": 1.0,
        "lethality_chain_mobility_capability_after": 0.9,
        "lethality_chain_sensor_capability_before": 1.0,
        "lethality_chain_sensor_capability_after": 0.7,
        "lethality_chain_survivability_margin_before": 1.0,
        "lethality_chain_survivability_margin_after": 0.95,
        "lethality_chain_control_delta": -0.1,
        "lethality_chain_engine_delta": 0.0,
        "lethality_chain_fuel_leak_delta": 0.2,
        "lethality_chain_fire_state": "fire=0.000000->0.100000",
        "lethality_chain_aircraft_damage_state_delta": "control=-0.100000,fire=0.100000",
      },
    )

    self.assertEqual(record["delay_steps"], 128)
    self.assertTrue(record["released"])
    self.assertAlmostEqual(record["first_release_target_range_geom_m"], 7100.0)
    self.assertAlmostEqual(record["target_health_delta_from_release"], -20.0)
    self.assertEqual(record["lethality_chain_component_name"], "right_aileron_actuator")
    self.assertEqual(record["lethality_chain_component_damage_count"], 0)
    self.assertTrue(record["effective_detonation"])
    self.assertFalse(record["effective_component_damage"])
    self.assertTrue(record["effective_system_consequence"])
    self.assertEqual(record["lethality_chain_fuze_failure_reason"], "")
    self.assertEqual(record["terminal_negative_reason"], "")
    self.assertAlmostEqual(
      record["lethality_chain_fuze_expected_detonation_probability"],
      0.62,
    )
    self.assertEqual(record["lethality_chain_fuze_type"], "radar_proximity")
    self.assertAlmostEqual(record["lethality_chain_fuze_trigger_radius_m"], 15.0)
    self.assertAlmostEqual(record["lethality_chain_fuze_distance_ratio"], 0.2)
    self.assertAlmostEqual(record["lethality_chain_fuze_trigger_quality"], 0.8)
    self.assertAlmostEqual(record["lethality_chain_fuze_sample"], 0.58)
    self.assertEqual(record["lethality_chain_fuze_sample_gate"], "sample_passed")
    self.assertIn("miss 3.000m / trigger 15.000m", record["lethality_chain_fuze_gate_summary"])
    self.assertAlmostEqual(record["lethality_chain_component_failure_probability"], 0.3)
    self.assertAlmostEqual(record["lethality_chain_component_failure_sample"], 0.8)
    self.assertAlmostEqual(record["lethality_chain_mission_capability_before"], 1.0)
    self.assertAlmostEqual(record["lethality_chain_mission_capability_after"], 0.8)
    self.assertEqual(
      record["damage_chain_outcome"],
      "component_sample_rejected_but_system_consequence",
    )
    self.assertEqual(
      record["damage_chain_blocker"],
      "component_sample_rejected_but_system_consequence",
    )
    self.assertEqual(record["damage_chain_primary_channel"], "flight_control")
    self.assertEqual(record["damage_chain_capability_attribution"], "sensor_capability")
    self.assertEqual(record["damage_chain_component_sample_gate"], "sample_rejected")
    self.assertIn("sample 0.800>0.300", record["damage_chain_attribution_summary"])
    self.assertEqual(record["lethality_chain_aircraft_damage_state_delta"], "control=-0.100000,fire=0.100000")

  def test_window_position_summary_reports_unconditional_and_release_conditional_rates(self) -> None:
    records = [
      {
        "released": True,
        "release_count": 1,
        "delay_steps": 32,
        "first_release_step": 10,
        "first_release_target_range_geom_m": 1000.0,
        "first_release_target_range_track_m": 1000.0,
        "first_release_legal_window_age_steps": 0,
        "total_reward": 10.0,
        "final_target_health": 100.0,
        "target_health_delta_from_release": 0.0,
        "damage_consequence_reward_total": 0.0,
        "target_damage_consequence_reward_total": 0.0,
        "lethality_chain_miss_distance_m": 3.0,
        "lethality_chain_closure_mps": 700.0,
        "lethality_chain_component_name": "right_aileron_actuator",
        "lethality_chain_component_system": "flight_control",
        "lethality_chain_component_damage_count": 1,
        "lethality_chain_component_damage_name": "right_aileron_actuator",
        "lethality_chain_component_damage_system": "flight_control",
        "lethality_chain_component_failure_mode": "cut",
        "lethality_chain_component_failure_severity": 0.7,
        "lethality_chain_component_failure_probability": 0.5,
        "lethality_chain_component_failure_sample": 0.2,
        "lethality_chain_component_integrity_before": 1.0,
        "lethality_chain_component_integrity_after": 0.75,
        "lethality_chain_system_health_delta": -1.0,
        "lethality_chain_mission_capability_before": 1.0,
        "lethality_chain_mission_capability_after": 0.0,
        "lethality_chain_mission_capability_delta": -1.0,
        "lethality_chain_mobility_capability_before": 1.0,
        "lethality_chain_mobility_capability_after": 1.0,
        "lethality_chain_mobility_capability_delta": 0.0,
        "lethality_chain_sensor_capability_before": 1.0,
        "lethality_chain_sensor_capability_after": 0.8,
        "lethality_chain_sensor_capability_delta": -0.2,
        "lethality_chain_survivability_margin_before": 1.0,
        "lethality_chain_survivability_margin_after": 1.0,
        "lethality_chain_survivability_margin_delta": 0.0,
        "lethality_chain_control_delta": -0.2,
        "lethality_chain_engine_delta": 0.0,
        "lethality_chain_fuel_leak_delta": 0.3,
        "lethality_chain_fire_state": "fire=0.000000->0.300000",
        "lethality_chain_aircraft_damage_state_delta": "control=-0.200000,fire=0.300000",
        "effects_event_count": 1,
        "damage_report_count": 1,
        "effective_detonation": True,
        "effective_component_damage": True,
        "effective_system_consequence": True,
        "lethality_chain_row_count": 8,
        "lethality_chain_stages_json": '["fuze","warhead_mechanism","component_damage"]',
        "lethality_chain_fuze_failure_reason": "",
        "lethality_chain_fuze_sample": 0.2,
        "lethality_chain_fuze_expected_detonation_probability": 0.8,
        "lethality_chain_fuze_trigger_radius_m": 10.0,
        "lethality_chain_fuze_distance_ratio": 0.3,
        "lethality_chain_fuze_trigger_quality": 0.7,
        "lethality_chain_fuze_sample_gate": "sample_passed",
        "lethality_chain_fuze_gate_summary": "radar_proximity",
        "terminal_negative_reason": "",
        "lethality_chain_mission_kill": True,
        "lethality_chain_destroyed": False,
        "lethality_chain_loss_state": "mission_kill",
        "damage_chain_outcome": "mission_kill",
        "damage_chain_blocker": "kill_observed",
        "damage_chain_primary_channel": "flight_control",
        "damage_chain_capability_attribution": "mission_capability",
        "damage_chain_component_sample_gate": "sample_passed",
        "termination_reason": "running",
      },
      {
        "released": False,
        "release_count": 0,
        "delay_steps": 32,
        "first_release_step": None,
        "first_release_target_range_geom_m": float("nan"),
        "first_release_target_range_track_m": float("nan"),
        "first_release_legal_window_age_steps": 0,
        "total_reward": 1.0,
        "final_target_health": float("nan"),
        "target_health_delta_from_release": float("nan"),
        "damage_consequence_reward_total": 0.0,
        "target_damage_consequence_reward_total": 0.0,
        "lethality_chain_miss_distance_m": float("nan"),
        "lethality_chain_closure_mps": float("nan"),
        "lethality_chain_component_name": "",
        "lethality_chain_component_system": "",
        "lethality_chain_component_damage_count": 0,
        "lethality_chain_component_damage_name": "",
        "lethality_chain_component_damage_system": "",
        "lethality_chain_component_failure_mode": "",
        "lethality_chain_component_failure_severity": float("nan"),
        "lethality_chain_component_failure_probability": float("nan"),
        "lethality_chain_component_failure_sample": float("nan"),
        "lethality_chain_component_integrity_before": float("nan"),
        "lethality_chain_component_integrity_after": float("nan"),
        "lethality_chain_system_health_delta": float("nan"),
        "lethality_chain_mission_capability_before": float("nan"),
        "lethality_chain_mission_capability_after": float("nan"),
        "lethality_chain_mission_capability_delta": float("nan"),
        "lethality_chain_mobility_capability_before": float("nan"),
        "lethality_chain_mobility_capability_after": float("nan"),
        "lethality_chain_mobility_capability_delta": float("nan"),
        "lethality_chain_sensor_capability_before": float("nan"),
        "lethality_chain_sensor_capability_after": float("nan"),
        "lethality_chain_sensor_capability_delta": float("nan"),
        "lethality_chain_survivability_margin_before": float("nan"),
        "lethality_chain_survivability_margin_after": float("nan"),
        "lethality_chain_survivability_margin_delta": float("nan"),
        "lethality_chain_control_delta": float("nan"),
        "lethality_chain_engine_delta": float("nan"),
        "lethality_chain_fuel_leak_delta": float("nan"),
        "lethality_chain_fire_state": "",
        "lethality_chain_aircraft_damage_state_delta": "",
        "effects_event_count": 0,
        "damage_report_count": 0,
        "effective_detonation": False,
        "effective_component_damage": False,
        "effective_system_consequence": False,
        "lethality_chain_row_count": 0,
        "lethality_chain_stages_json": "",
        "lethality_chain_fuze_failure_reason": "",
        "lethality_chain_fuze_sample": float("nan"),
        "lethality_chain_fuze_expected_detonation_probability": float("nan"),
        "lethality_chain_fuze_trigger_radius_m": float("nan"),
        "lethality_chain_fuze_distance_ratio": float("nan"),
        "lethality_chain_fuze_trigger_quality": float("nan"),
        "lethality_chain_fuze_sample_gate": "no_fuze_probability",
        "lethality_chain_fuze_gate_summary": "no fuze observation",
        "terminal_negative_reason": "",
        "lethality_chain_mission_kill": False,
        "lethality_chain_destroyed": False,
        "lethality_chain_loss_state": "",
        "damage_chain_outcome": "no_release",
        "damage_chain_blocker": "no_release",
        "damage_chain_primary_channel": "none",
        "damage_chain_capability_attribution": "none",
        "damage_chain_component_sample_gate": "no_component_probability",
        "termination_reason": "running",
      },
    ]

    summary = window_position_sweep._summarize_delay(32, records)

    self.assertAlmostEqual(summary["release_rate"], 0.5)
    self.assertAlmostEqual(summary["mission_kill_rate"], 0.5)
    self.assertAlmostEqual(summary["mission_kill_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["effects_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["effective_detonation_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["effective_component_damage_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["effective_system_consequence_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["mean_fuze_expected_detonation_probability"], 0.8)
    self.assertAlmostEqual(summary["mean_fuze_trigger_radius_m"], 10.0)
    self.assertAlmostEqual(summary["mean_fuze_distance_ratio"], 0.3)
    self.assertAlmostEqual(summary["mean_fuze_trigger_quality"], 0.7)
    self.assertAlmostEqual(summary["mean_fuze_sample"], 0.2)
    self.assertAlmostEqual(summary["fuze_sample_pass_given_release_rate"], 1.0)
    self.assertAlmostEqual(summary["mean_component_failure_sample"], 0.2)
    self.assertAlmostEqual(summary["mean_component_damage_count"], 0.5)
    self.assertEqual(summary["seed_sample_count"], 2)
    self.assertEqual(summary["release_rate_success_count"], 1)
    self.assertEqual(summary["mission_kill_given_release_rate_success_count"], 1)
    self.assertGreater(summary["release_rate_ci_width"], 0.0)
    self.assertGreater(summary["mission_kill_given_release_rate_ci_width"], 0.0)
    self.assertEqual(summary["component_failure_probability_sample_count"], 1)
    self.assertTrue(summary["seed_high_variance"])
    self.assertIn("release_rate_ci_width_wide", summary["seed_confidence_flags"])
    self.assertAlmostEqual(summary["mean_component_integrity_delta"], -0.25)
    self.assertAlmostEqual(summary["mean_mission_capability_before"], 1.0)
    self.assertAlmostEqual(summary["mean_mission_capability_after"], 0.0)
    self.assertAlmostEqual(summary["mean_control_delta"], -0.2)
    self.assertEqual(
      summary["aircraft_damage_state_delta_counts"],
      {"": 1, "control=-0.200000,fire=0.300000": 1},
    )
    self.assertEqual(
      summary["component_name_counts"],
      {"": 1, "right_aileron_actuator": 1},
    )
    self.assertEqual(summary["damage_chain_outcome_counts"], {"mission_kill": 1, "no_release": 1})
    self.assertEqual(
      summary["damage_chain_blocker_counts"],
      {"kill_observed": 1, "no_release": 1},
    )
    self.assertEqual(
      summary["damage_chain_component_sample_gate_counts"],
      {"no_component_probability": 1, "sample_passed": 1},
    )
    self.assertEqual(
      summary["fuze_sample_gate_counts"],
      {"no_fuze_probability": 1, "sample_passed": 1},
    )

  def test_window_position_record_separates_negative_fuze_event_from_effective_damage(self) -> None:
    record = window_position_sweep._record_from_episode_summary(
      delay=768,
      payload={"mode": "legal_mask_fire", "seed": 20260615},
      episode_summary={
        "episode": 0,
        "release_count": 1,
        "first_release_step": 770,
        "first_release_sim_time_s": 38.5,
        "first_release_target_range_geom_m": 19530.0,
        "first_release_target_range_track_m": 19540.0,
        "first_release_target_track_age_s": 0.1,
        "first_release_legal_window_age_steps": 0,
        "first_release_engagement_state": "FiredAssess",
        "total_reward": 10.0,
        "final_target_health": 100.0,
        "first_release_target_health": 100.0,
        "effects_event_count": 1,
        "damage_report_count": 1,
        "lethality_chain_row_count": 4,
        "lethality_chain_chain_count": 1,
        "lethality_chain_stages_json": '["fuze","lifecycle","nearest_approach","platform_consequence"]',
        "lethality_chain_miss_distance_m": 5.14,
        "lethality_chain_fuze_triggered": False,
        "lethality_chain_fuze_failure_reason": "fuze_no_detonation",
        "lethality_chain_fuze_expected_detonation_probability": 0.41,
        "lethality_chain_fuze_sampled_outcome": True,
        "lethality_chain_component_damage_count": 0,
        "lethality_chain_system_health_delta": 0.0,
        "lethality_chain_mission_kill": False,
        "lethality_chain_mobility_kill": False,
        "lethality_chain_sensor_kill": False,
        "lethality_chain_destroyed": False,
        "lethality_chain_loss_state": "combat_capable",
      },
    )

    self.assertEqual(record["effects_event_count"], 1)
    self.assertEqual(record["damage_report_count"], 1)
    self.assertFalse(record["effective_detonation"])
    self.assertFalse(record["effective_component_damage"])
    self.assertFalse(record["effective_system_consequence"])
    self.assertEqual(record["terminal_negative_reason"], "fuze_no_detonation")
    self.assertAlmostEqual(
      record["lethality_chain_fuze_expected_detonation_probability"],
      0.41,
    )
    self.assertEqual(record["damage_chain_outcome"], "fuze_no_detonation")
    self.assertEqual(record["damage_chain_blocker"], "fuze_no_detonation")
    self.assertEqual(record["damage_chain_primary_channel"], "none")
    self.assertEqual(record["damage_chain_component_sample_gate"], "no_component_probability")
    self.assertIn("blocked at fuze", record["damage_chain_attribution_summary"])

  def test_window_position_confidence_summary_marks_high_seed_variance(self) -> None:
    summary = window_position_sweep._confidence_summary(
      [
        {
          "delay_steps": 32,
          "release_episode_count": 2,
          "seed_high_variance": True,
          "mission_kill_given_release_rate_ci_width": 0.72,
          "system_health_delta_sem": 0.22,
          "mission_capability_delta_sem": 0.18,
        },
        {
          "delay_steps": 768,
          "release_episode_count": 2,
          "seed_high_variance": False,
          "mission_kill_given_release_rate_ci_width": 0.1,
          "system_health_delta_sem": 0.01,
          "mission_capability_delta_sem": 0.01,
        },
      ],
      rate_ci_width_epsilon=0.5,
      outcome_sem_epsilon=0.15,
      range_sem_epsilon_m=500.0,
    )

    self.assertEqual(summary["high_variance_delay_steps"], [32])
    self.assertEqual(summary["mission_kill_uncertain_delay_steps"], [32])
    self.assertEqual(summary["platform_consequence_uncertain_delay_steps"], [32])
    self.assertAlmostEqual(
      summary["max_mission_kill_given_release_rate_ci_width"],
      0.72,
    )


class ChainBreakpointProbeTests(unittest.TestCase):
  def test_model_event_hold_collector_preserves_model_action_except_fire_event(self) -> None:
    class DummyModel:
      def __init__(self) -> None:
        self.calls: list[bool] = []

      def predict(self, _obs, *, deterministic: bool):
        self.calls.append(bool(deterministic))
        return th.arange(12, dtype=th.float32).numpy(), None

    model = DummyModel()

    action = _collector_action_for_m3s2(
      model,
      env=None,
      obs={"dummy": 1},
      collector_action="model_event_hold",
      stochastic=False,
    )

    expected = th.arange(12, dtype=th.float32).numpy()
    expected[9] = 0.0
    self.assertEqual(model.calls, [True])
    self.assertEqual(action.tolist(), expected.tolist())

  def test_masks_from_groups_marks_prewindow_and_quality_rows(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3),
      step_indices=(0, 1, 2, 3),
      legal_mask=(False, True, True, True),
      quality_mask=(False, False, True, True),
      accepted_event=(False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=3,
    )

    masks = _masks_from_groups([group], row_count=5)

    self.assertEqual(masks.legal.tolist(), [False, True, True, True, False])
    self.assertEqual(masks.prewindow.tolist(), [False, True, False, False, False])
    self.assertEqual(masks.quality.tolist(), [False, False, True, True, False])
    self.assertEqual(masks.eligible.tolist(), [False, True, True, True, False])

  def test_classifier_pass_requires_no_prewindow_boundary_and_all_quality_boundary(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3),
      step_indices=(0, 1, 2, 3),
      legal_mask=(True, True, True, True),
      quality_mask=(False, False, True, True),
      accepted_event=(False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=3,
    )
    masks = _masks_from_groups([group], row_count=4)

    good = _classification_metrics(th.tensor([-2.0, -1.0, 1.0, 2.0]), masks)
    bad = _classification_metrics(th.tensor([-2.0, 1.0, 1.0, 2.0]), masks)

    self.assertTrue(_passes_window_classifier(good, min_accuracy=0.99))
    self.assertFalse(_passes_window_classifier(bad, min_accuracy=0.99))

  def test_edge_trigger_counts_first_quality_pulse(self) -> None:
    group = RealM3S2Group(
      group_id="g0",
      episode_id=0,
      row_indices=(0, 1, 2, 3, 4),
      step_indices=(0, 1, 2, 3, 4),
      legal_mask=(True, True, True, True, True),
      quality_mask=(False, False, True, True, True),
      accepted_event=(False, False, False, False, False),
      censoring_kind="timeout",
      censor_step=None,
      support_horizon=4,
    )
    masks = _masks_from_groups([group], row_count=5)

    summary = _edge_trigger_summary(th.tensor([False, False, True, True, True]), masks)

    self.assertEqual(summary["pulse_count"], 1)
    self.assertEqual(summary["quality_pulse_count"], 1)
    self.assertEqual(summary["prewindow_pulse_count"], 0)
    self.assertEqual(summary["first_quality_pulse"]["row"], 2)

  def test_auto_adapter_head_prefers_executable_window_classifier(self) -> None:
    class DummyPolicy:
      _hybrid_event_use_window_classifier_head = True
      _hybrid_event_use_stopping_head = True

      def __init__(self) -> None:
        self.window_classifier_head = nn.Linear(2, 1)
        self.stopping_head = nn.Linear(2, 1)

    policy = DummyPolicy()
    source = nn.Linear(2, 1)
    with th.no_grad():
      source.weight.fill_(3.0)
      source.bias.fill_(1.0)
      policy.stopping_head.weight.fill_(-4.0)
      policy.stopping_head.bias.fill_(-2.0)

    head_kind = _resolve_adapter_head_kind(policy, "auto")
    _install_head(policy, source, head_kind=head_kind)

    self.assertEqual(head_kind, "window_classifier")
    self.assertIs(_head_module(policy, head_kind), policy.window_classifier_head)
    self.assertTrue(th.allclose(policy.window_classifier_head.weight, source.weight))
    self.assertTrue(th.allclose(policy.window_classifier_head.bias, source.bias))
    self.assertTrue(th.all(policy.stopping_head.weight == -4.0))
    self.assertTrue(th.all(policy.stopping_head.bias == -2.0))

  def test_fault_localization_reports_optimizer_breakpoint(self) -> None:
    summary = _fault_localization_summary(
      label_contract={
        "row_count": 4,
        "legal_count": 4,
        "prewindow_count": 2,
        "quality_count": 2,
        "pass": True,
      },
      fresh_latent={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      trained_head={
        "pass": False,
        "accuracy": 0.75,
        "prewindow_boundary_count": 1,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      adapter_from_fresh={
        "pass": True,
        "edge_trigger_pass": True,
        "event_mode_fire_prewindow_count": 0,
        "event_mode_fire_quality_count": 2,
      },
      current_policy_pass=False,
      first_breakpoint="head_optimization_conditioning",
    )

    self.assertEqual(summary["first_failed_stage"], "optimizer")
    self.assertTrue(bool(summary["blocks_feature_addition"]))
    stages = {stage["stage"]: stage for stage in summary["stages"]}
    self.assertFalse(bool(stages["optimizer"]["passed"]))
    self.assertFalse(bool(stages["loss_object"]["checked"]))
    self.assertEqual(summary["legacy_first_breakpoint"], "head_optimization_conditioning")

  def test_fault_localization_reports_evaluation_breakpoint_after_local_chain_passes(self) -> None:
    summary = _fault_localization_summary(
      label_contract={
        "row_count": 4,
        "legal_count": 4,
        "prewindow_count": 2,
        "quality_count": 2,
        "pass": True,
      },
      fresh_latent={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      trained_head={
        "pass": True,
        "accuracy": 1.0,
        "prewindow_boundary_count": 0,
        "quality_boundary_count": 2,
        "quality_count": 2,
      },
      adapter_from_fresh={
        "pass": True,
        "edge_trigger_pass": True,
        "event_mode_fire_prewindow_count": 0,
        "event_mode_fire_quality_count": 2,
      },
      current_policy_pass=False,
      first_breakpoint="online_training_or_learned_parameter_contract",
    )

    self.assertEqual(summary["first_failed_stage"], "evaluation")
    stages = {stage["stage"]: stage for stage in summary["stages"]}
    self.assertTrue(bool(stages["optimizer"]["passed"]))
    self.assertFalse(bool(stages["evaluation"]["passed"]))


class RealUpdatePathProbeTests(unittest.TestCase):
  def test_build_groups_marks_quality_after_launch_and_min_age(self) -> None:
    groups = _build_groups_from_rows(
      fire_mask=[False, True, True, True, True],
      fire_once_accepted=[False, False, False, False, False],
      episode_id=[0, 0, 0, 0, 0],
      launch_window_open=[False, False, True, True, True],
      launch_min_age=3,
    )

    self.assertEqual(len(groups), 1)
    self.assertEqual(groups[0].legal_mask, (False, True, True, True, True))
    self.assertEqual(groups[0].quality_mask, (False, False, False, True, True))
    self.assertEqual(groups[0].censoring_kind, "timeout")

  def test_build_groups_early_accepted_before_quality_is_prefix_censored(self) -> None:
    groups = _build_groups_from_rows(
      fire_mask=[True, True, True, True],
      fire_once_accepted=[False, True, False, False],
      episode_id=[0, 0, 0, 0],
      launch_window_open=[False, False, True, True],
      launch_min_age=3,
    )

    self.assertEqual(groups[0].row_indices, (0, 1))
    self.assertEqual(groups[0].accepted_event, (False, True))
    self.assertEqual(groups[0].censoring_kind, "early_event_prefix")


class StructuralToyProbeTests(unittest.TestCase):
  def _config(self, *, model: str, train_steps: int, learning_rate: float) -> ToyProbeConfig:
    return ToyProbeConfig(
      model=model,
      prewindow_steps=12,
      quality_steps=24,
      train_steps=train_steps,
      learning_rate=learning_rate,
      initial_logit=-6.0,
      hidden_size=16,
      seed=7,
      early_mass_coef=2.0,
      early_mass_budget=0.02,
      early_survival_coef=8.0,
      window_delay_coef=0.5,
      window_deadline_coef=0.5,
      window_deadline_steps=8,
      max_grad_norm=2.0,
      prewindow_risk_gate=0.02,
      window_mass_gate=0.95,
    )

  def test_free_logits_structural_toy_crosses_quality_boundary(self) -> None:
    result = run_probe(self._config(model="free_logits", train_steps=500, learning_rate=0.1))

    self.assertTrue(result["verdict"]["structural_toy_pass"])
    final = result["final"]
    self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
    self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
    self.assertIsNotNone(final["first_quality_boundary_cross_step"])
    self.assertGreaterEqual(float(final["mean_p_window"]), 0.95)

  def test_mlp_structural_toy_learns_with_explicit_quality_feature(self) -> None:
    result = run_probe(self._config(model="mlp", train_steps=800, learning_rate=0.02))

    self.assertTrue(result["verdict"]["structural_toy_pass"])
    final = result["final"]
    self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
    self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
    self.assertIsNotNone(final["first_quality_boundary_cross_step"])
    self.assertGreaterEqual(float(final["quality_prob_max"]), 0.5)


if __name__ == "__main__":
  unittest.main()
