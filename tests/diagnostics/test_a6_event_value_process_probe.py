from __future__ import annotations

import math
import unittest

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

    def _fire_event_logits(self):
        return th.tensor([[1.0, 3.0]], dtype=th.float32)

    def fire_event_logit_delta(self):
        return th.tensor([2.0], dtype=th.float32)

    def fire_event_probability(self):
        return th.sigmoid(self.fire_event_logit_delta())


def _row(
    step: int,
    *,
    state: str = "Hold",
    mask: int = 0,
    event_delta: float = 0.0,
    event_prob: float = 0.0,
    event_mode: int = 0,
) -> dict:
    return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": 12000.0 - step,
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


if __name__ == "__main__":
    unittest.main()
