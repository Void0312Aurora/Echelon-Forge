from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics import air_combat_stage0_process_probe as probe


class _DummyHybridDistribution:
    def __init__(self) -> None:
        self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
        self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
        self.categorical_logits = [
            (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
        ]
        self._q_values = th.tensor([[1.5, -0.5]], dtype=th.float32)

    def _fire_event_logits(self):
        return th.tensor([[1.0, 3.0]], dtype=th.float32)

    def fire_event_logit_delta(self):
        return th.tensor([2.0], dtype=th.float32)

    def fire_event_probability(self):
        return th.sigmoid(self.fire_event_logit_delta())

    def fire_event_q_values(self):
        return self._q_values

    def fire_event_advantage(self):
        return self._q_values[:, 1] - self._q_values[:, 0]


class _DummyM3Policy:
    def obs_to_tensor(self, obs):
        return obs, False

    def get_distribution(self, _obs):
        return _DummyHybridDistribution()

    def get_m3_stopping(self, _obs, *, detach_latent: bool = False):
        logit = th.tensor([1.5], dtype=th.float32)
        return SimpleNamespace(
            stopping_logit=logit,
            hazard_logit=logit,
            hazard=th.sigmoid(logit),
        )


def _row(
    step: int,
    *,
    state: str = "Hold",
    mask: int = 0,
    event_delta: float = 0.0,
    event_prob: float = 0.0,
    event_mode: int = 0,
    event_advantage: float = 0.0,
    m3_stop_logit: float = 0.0,
    m3_stop_prob: float = 0.0,
    m3_boundary: int = 0,
    target_range_m: float | None = None,
    target_track_age_s: float = 1.0,
) -> dict:
    target_range = (12000.0 - step) if target_range_m is None else float(target_range_m)
    return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": target_range,
        "target_range_track_m": target_range,
        "target_track_age_s": target_track_age_s,
        "target_health": 100.0,
        "can_fire": 1,
        "target_contact": 1,
        "target_active": 1,
        "missiles_remaining": 4,
        "missile_release": 0,
        "missile_release_delta": 0,
        "action_radar_on": 1,
        "action_master_arm_on": 1,
        "action_fire_weapon_on": 0,
        "action_radar_active": 1.0,
        "action_master_arm": 1.0,
        "action_fire_weapon": 0.0,
        "effective_action_fire_weapon": 0.0,
        "authorization_to_fire": int(mask),
        "shot_budget_remaining": 1,
        "pending_assessment": 0,
        "engagement_state": state,
        "fire_mask": mask,
        "fire_once_requested": 0,
        "fire_once_accepted": 0,
        "fire_once_rejected": 0,
        "fire_once_rejected_reason": "",
        "release_executed": 0,
        "post_launch_suppressed": 0,
        "policy_event_logit_delta": event_delta,
        "policy_event_prob_fire_once_unmasked": event_prob,
        "policy_event_prob_fire_once": event_prob,
        "policy_event_logit_fire_once": event_delta,
        "policy_event_mode": event_mode,
        "policy_event_mask_fire_once": mask,
        "policy_event_q_hold": 0.0,
        "policy_event_q_fire_once": event_advantage,
        "policy_event_advantage": event_advantage,
        "policy_m3_stop_logit": m3_stop_logit,
        "policy_m3_stop_prob": m3_stop_prob,
        "policy_m3_boundary_cross": m3_boundary,
        "policy_m3_stopping_head_enabled": 1,
        "effects_event_count": 0,
        "damage_report_count": 0,
        "last_effect_miss_distance_m": math.nan,
        "last_effect_detonation_local_forward_m": math.nan,
        "last_effect_detonation_local_right_m": math.nan,
        "last_effect_detonation_local_up_m": math.nan,
        "last_effect_direct_hitbox_intersection": 0,
        "last_effect_projected_hitbox_count": 0,
        "last_effect_component_hit_count": 0,
        "last_effect_fuze_type": "",
        "last_damage_loss_state": "",
        "last_damage_system_health_delta": math.nan,
        "last_damage_mission_kill": 0,
        "last_damage_mobility_kill": 0,
        "last_damage_sensor_kill": 0,
        "last_damage_destroyed": 0,
    }


class A6EventValueProcessProbeTests(unittest.TestCase):
    def test_distribution_diagnostics_include_a6_unmasked_event_delta(self) -> None:
        diagnostics = probe._distribution_policy_diagnostics(_DummyHybridDistribution())

        self.assertAlmostEqual(diagnostics["policy_event_logit_delta"], 2.0, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once_unmasked"], 0.8807970, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once"], 0.8807970, places=6)
        self.assertEqual(int(diagnostics["policy_event_mode"]), 1)
        self.assertEqual(int(diagnostics["policy_event_mask_fire_once"]), 1)
        self.assertAlmostEqual(diagnostics["policy_event_q_hold"], 1.5, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_q_fire_once"], -0.5, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_advantage"], -2.0, places=6)

    def test_model_policy_diagnostics_include_m3_stopping_head_probe(self) -> None:
        diagnostics = probe._model_policy_diagnostics(
            SimpleNamespace(policy=_DummyM3Policy()),
            {"mission": th.zeros((1, 20), dtype=th.float32)},
        )

        self.assertAlmostEqual(diagnostics["policy_m3_stop_logit"], 1.5, places=6)
        self.assertAlmostEqual(
            diagnostics["policy_m3_stop_prob"],
            float(th.sigmoid(th.tensor(1.5)).item()),
            places=6,
        )
        self.assertEqual(int(diagnostics["policy_m3_boundary_cross"]), 1)
        self.assertEqual(int(diagnostics["policy_m3_stopping_head_enabled"]), 1)
        self.assertAlmostEqual(diagnostics["policy_event_logit_delta"], 2.0, places=6)

    def test_episode_summary_reports_a6_open_window_event_metrics(self) -> None:
        summary = probe._summarize_episode(
            [
                _row(0),
                _row(1, state="AuthorizedReady", mask=1, event_delta=1.0, event_prob=0.25),
                _row(2, state="AuthorizedReady", mask=1, event_delta=3.0, event_prob=0.75, event_mode=1),
                _row(3, state="FiredAssess", mask=0, event_delta=10.0, event_prob=0.99, event_mode=1),
            ]
        )

        self.assertEqual(summary["a6_open_window_step_count"], 2)
        self.assertAlmostEqual(summary["a6_event_logit_delta_mean_open"], 2.0, places=6)
        self.assertAlmostEqual(summary["a6_event_fire_prob_mean_open"], 0.5, places=6)
        self.assertAlmostEqual(summary["a6_event_fire_prob_max_open"], 0.75, places=6)
        self.assertEqual(summary["policy_event_mode_fire_once_count"], 2)

    def test_episode_summary_reports_a7_credit_signs_and_prewindow_cumulative_hazard(self) -> None:
        summary = probe._summarize_episode(
            [
                _row(0),
                _row(
                    1,
                    state="AuthorizedReady",
                    mask=1,
                    event_prob=0.1,
                    event_advantage=-1.0,
                    m3_stop_logit=-2.0,
                    m3_stop_prob=0.1,
                ),
                _row(
                    2,
                    state="AuthorizedReady",
                    mask=1,
                    event_prob=0.2,
                    event_advantage=-2.0,
                    m3_stop_logit=-1.0,
                    m3_stop_prob=0.2,
                ),
                _row(
                    3,
                    state="AuthorizedReady",
                    mask=1,
                    event_prob=0.6,
                    event_advantage=1.0,
                    m3_stop_logit=0.5,
                    m3_stop_prob=0.6,
                    m3_boundary=1,
                ),
                _row(
                    4,
                    state="AuthorizedReady",
                    mask=1,
                    event_prob=0.8,
                    event_advantage=2.0,
                    m3_stop_logit=1.0,
                    m3_stop_prob=0.8,
                    m3_boundary=1,
                ),
            ],
            launch_window_config={
                "min_range_m": 8000.0,
                "max_range_m": 30000.0,
                "max_track_age_s": 5.0,
                "min_window_age_steps": 3,
            },
        )

        self.assertEqual(summary["a7_prewindow_step_count"], 2)
        self.assertEqual(summary["a7_quality_window_step_count"], 2)
        self.assertAlmostEqual(summary["a7_prewindow_event_fire_prob_cum"], 0.28, places=6)
        self.assertAlmostEqual(summary["a7_prewindow_event_fire_prob_mean"], 0.15, places=6)
        self.assertAlmostEqual(summary["a7_quality_window_event_fire_prob_mean"], 0.7, places=6)
        self.assertAlmostEqual(summary["a7_prewindow_m3_stop_prob_cum"], 0.28, places=6)
        self.assertAlmostEqual(summary["a7_prewindow_m3_stop_prob_mean"], 0.15, places=6)
        self.assertAlmostEqual(summary["a7_quality_window_m3_stop_prob_mean"], 0.7, places=6)
        self.assertEqual(summary["a7_prewindow_m3_boundary_cross_count"], 0)
        self.assertEqual(summary["a7_quality_window_m3_boundary_cross_count"], 2)
        self.assertEqual(summary["a7_first_quality_window_m3_boundary_cross_step"], 3)
        self.assertEqual(summary["policy_m3_boundary_cross_count"], 2)
        self.assertEqual(summary["policy_m3_first_boundary_cross_step"], 3)
        self.assertAlmostEqual(summary["a7_event_credit_advantage_mean_prewindow"], -1.5, places=6)
        self.assertAlmostEqual(summary["a7_event_credit_advantage_negative_frac_prewindow"], 1.0, places=6)
        self.assertAlmostEqual(summary["a7_event_credit_advantage_mean_quality"], 1.5, places=6)
        self.assertAlmostEqual(summary["a7_event_credit_advantage_positive_frac_quality"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
