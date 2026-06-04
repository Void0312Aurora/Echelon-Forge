from __future__ import annotations

import json
import unittest
from pathlib import Path

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()


REPO_ROOT = Path(__file__).resolve().parents[2]
A6_ACTIVE_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_shaped_world_batch_probe_v1.json"
)
A6_DEADLINE_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_shaped_world_batch_probe_v1.json"
)
A6_EVENT_HEAD_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_shaped_world_batch_probe_v1.json"
)
A6_LAUNCH_WINDOW_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_deadline_event_head_launch_window_shaped_world_batch_probe_v1.json"
)
A7_EVENT_CREDIT_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_shaped_world_batch_probe_v1.json"
)
A7_STATE_COMPLETED_CONFIG = (
    REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "air_combat"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_a7_event_credit_launch_window_state_completed_world_batch_probe_v1.json"
)
A6_SCENARIO = (
    REPO_ROOT
    / "scenarios"
    / "air_combat"
    / "1v1"
    / "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json"
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class A6EventValueActiveConfigTests(unittest.TestCase):
    def test_active_c2_roe_temporal_config_carries_a6_hazard_knobs(self) -> None:
        cfg = _load_json(A6_ACTIVE_CONFIG)
        hyper = cfg.get("hyperparameters", {})

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("env", {}).get("action_mode"), "air_combat_hybrid_v1")
        self.assertEqual(cfg.get("env", {}).get("mission_obs_mode"), "air_combat_c2_roe_v1")
        self.assertEqual(cfg.get("env", {}).get("step_info_mode"), "full")
        self.assertEqual(hyper.get("policy_kwargs", {}).get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertGreater(float(hyper.get("a6_first_event_hazard_coef", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_curriculum_coef", 0.0)), 0.0)
        self.assertAlmostEqual(float(hyper.get("a6_first_event_curriculum_decay_fraction")), 0.25, places=6)

    def test_deadline_bootstrap_config_is_separate_a6_rescope_probe(self) -> None:
        cfg = _load_json(A6_DEADLINE_CONFIG)
        hyper = cfg.get("hyperparameters", {})

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("env", {}).get("action_mode"), "air_combat_hybrid_v1")
        self.assertEqual(cfg.get("env", {}).get("mission_obs_mode"), "air_combat_c2_roe_v1")
        self.assertEqual(cfg.get("env", {}).get("step_info_mode"), "full")
        self.assertEqual(hyper.get("policy_kwargs", {}).get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertGreater(float(hyper.get("a6_first_event_hazard_coef", 0.0)), 0.0)
        self.assertEqual(float(hyper.get("a6_first_event_curriculum_coef", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_deadline_weight", 0.0)), 0.0)
        self.assertEqual(int(hyper.get("a6_first_event_deadline_min_window_age_steps", 0)), 64)

    def test_event_head_config_adds_bounded_a6_optimizer_lane(self) -> None:
        baseline = _load_json(A6_DEADLINE_CONFIG)
        cfg = _load_json(A6_EVENT_HEAD_CONFIG)
        hyper = cfg.get("hyperparameters", {})
        policy_kwargs = hyper.get("policy_kwargs", {})
        baseline_policy_kwargs = baseline.get("hyperparameters", {}).get("policy_kwargs", {})

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("env"), baseline.get("env"))
        self.assertEqual(policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertEqual(float(baseline_policy_kwargs.get("hybrid_event_head_lr_scale", 0.0)), 0.0)
        self.assertAlmostEqual(float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0)), 10.0, places=6)
        self.assertGreater(float(hyper.get("a6_first_event_hazard_coef", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_deadline_weight", 0.0)), 0.0)
        self.assertEqual(float(hyper.get("a6_first_event_curriculum_coef", 0.0)), 0.0)

    def test_launch_window_config_separates_legal_authorization_from_timing_labels(self) -> None:
        event_head = _load_json(A6_EVENT_HEAD_CONFIG)
        cfg = _load_json(A6_LAUNCH_WINDOW_CONFIG)
        hyper = cfg.get("hyperparameters", {})

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("env"), event_head.get("env"))
        self.assertEqual(cfg.get("runtime"), event_head.get("runtime"))
        self.assertTrue(bool(hyper.get("a6_first_event_launch_window_enabled")))
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_min_range_m", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_max_range_m", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_max_track_age_s", 0.0)), 0.0)
        self.assertGreater(int(hyper.get("a6_first_event_launch_window_min_window_age_steps", 0)), 1)
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_prewindow_hold_weight", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_early_accept_weight", 0.0)), 0.0)
        self.assertAlmostEqual(
            float(hyper.get("policy_kwargs", {}).get("hybrid_event_head_lr_scale", 0.0)),
            10.0,
            places=6,
        )

    def test_a7_event_credit_config_exposes_credit_head_without_reusing_a6_hazard_loss(self) -> None:
        launch_window = _load_json(A6_LAUNCH_WINDOW_CONFIG)
        cfg = _load_json(A7_EVENT_CREDIT_CONFIG)
        hyper = cfg.get("hyperparameters", {})
        policy_kwargs = hyper.get("policy_kwargs", {})

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("env"), launch_window.get("env"))
        self.assertEqual(cfg.get("runtime"), launch_window.get("runtime"))
        self.assertEqual(policy_kwargs.get("hybrid_action_spec"), "air_combat_hybrid_v1")
        self.assertAlmostEqual(float(policy_kwargs.get("hybrid_event_head_lr_scale", 0.0)), 10.0, places=6)
        self.assertAlmostEqual(float(policy_kwargs.get("hybrid_event_credit_head_lr_scale", 0.0)), 6.0, places=6)

        self.assertEqual(float(hyper.get("a6_first_event_hazard_coef", -1.0)), 0.0)
        self.assertEqual(float(hyper.get("a6_first_event_curriculum_coef", -1.0)), 0.0)
        self.assertEqual(float(hyper.get("a6_first_event_deadline_weight", -1.0)), 0.0)
        self.assertTrue(bool(hyper.get("a6_first_event_launch_window_enabled")))
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_min_range_m", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a6_first_event_launch_window_max_range_m", 0.0)), 0.0)
        self.assertGreater(int(hyper.get("a6_first_event_launch_window_min_window_age_steps", 0)), 1)

        self.assertGreater(float(hyper.get("a7_event_credit_value_coef", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_delta_align_coef", 0.0)), 0.0)
        self.assertTrue(bool(hyper.get("a7_event_credit_delta_align_positive_only")))
        self.assertGreater(float(hyper.get("a7_event_credit_prewindow_hold_weight", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_early_accept_weight", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_deadline_weight", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_shadow_quality_weight", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_legal_open_quality_weight", 0.0)), 0.0)
        self.assertGreater(int(hyper.get("a7_event_credit_legal_open_quality_min_window_age_steps", 0)), 1)
        self.assertTrue(bool(hyper.get("a7_event_credit_legal_projection_enabled")))
        self.assertGreater(float(hyper.get("a7_event_credit_projection_value_coef", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_projection_delta_align_coef", 0.0)), 0.0)
        self.assertTrue(bool(hyper.get("a7_event_credit_separate_update_enabled")))
        self.assertGreater(float(hyper.get("a7_event_credit_separate_update_max_grad_norm", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_positive_mass_cap", 0.0)), 0.0)
        self.assertGreater(float(hyper.get("a7_event_credit_negative_mass_cap", 0.0)), 0.0)

    def test_a7_state_completed_config_changes_only_observation_contract(self) -> None:
        baseline = _load_json(A7_EVENT_CREDIT_CONFIG)
        cfg = _load_json(A7_STATE_COMPLETED_CONFIG)

        self.assertEqual(cfg.get("algo"), "AdaptiveKLPPO")
        self.assertEqual(cfg.get("policy"), "HierarchicalMoEExecutionPolicy")
        self.assertEqual(cfg.get("runtime"), baseline.get("runtime"))
        self.assertEqual(cfg.get("hyperparameters"), baseline.get("hyperparameters"))

        env = dict(cfg.get("env", {}))
        baseline_env = dict(baseline.get("env", {}))
        self.assertEqual(env.pop("mission_obs_mode"), "air_combat_c2_roe_v2")
        self.assertEqual(baseline_env.pop("mission_obs_mode"), "air_combat_c2_roe_v1")
        self.assertEqual(env, baseline_env)

    def test_a6_active_path_keeps_legality_penalties_disabled(self) -> None:
        scenario = _load_json(A6_SCENARIO)
        rewards = scenario.get("rewards", {})
        self.assertTrue(bool(rewards.get("air_combat_c2_roe_release_discipline_enabled")))
        self.assertGreater(float(rewards.get("air_combat_roe_authorized_first_release_bonus", 0.0)), 0.0)
        self.assertEqual(float(rewards.get("air_combat_roe_authorized_fire_opportunity_penalty", 0.0)), 0.0)
        for key in (
            "air_combat_invalid_fire_penalty",
            "air_combat_roe_hold_fire_bonus",
            "air_combat_roe_hold_fire_violation_penalty",
            "air_combat_roe_unauthorized_fire_penalty",
            "air_combat_roe_pending_assessment_penalty",
            "air_combat_roe_premature_second_shot_penalty",
            "air_combat_roe_shot_budget_violation_penalty",
        ):
            self.assertEqual(float(rewards.get(key, 0.0)), 0.0, key)


if __name__ == "__main__":
    unittest.main()
