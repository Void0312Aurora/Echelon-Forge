from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics import air_combat_fire_timing_learnability_audit as audit  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
