from __future__ import annotations

import unittest
from types import SimpleNamespace

from gym_envs.scenario_loader.reward_runtime.air_combat import apply_air_combat_reward_surface


def _loader(rewards: dict) -> SimpleNamespace:
    loader = SimpleNamespace()
    loader.get_rewards_config = lambda: dict(rewards)
    loader.scenario_data = {"realism_gradient": {"domain": "air_combat"}}
    loader._compiled_meta_cfg = {}
    loader._scenario_source_path = "scenarios/air_combat/1v1/test.json"
    loader._air_combat_reward_last_report_id = 0
    loader._air_combat_reward_prev_missiles = 4
    loader._air_combat_reward_release_count = 0
    loader._last_action_mode = "air_combat_hybrid_v1"
    loader._last_effective_action = [0.0, 0.0, 0.0, 0.6, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    loader.agent_id = 1
    loader.primary_target_id = 2
    return loader


def _sim() -> SimpleNamespace:
    return SimpleNamespace(
        export_recent_engagement_events=lambda: SimpleNamespace(damage_reports=[], effects_events=[]),
    )


class AirCombatRewardSurfaceTests(unittest.TestCase):
    def test_first_release_bonus_is_awarded_once_on_missile_count_drop(self) -> None:
        loader = _loader(
            {
                "air_combat_release_shaping_enabled": True,
                "air_combat_first_release_bonus": 300.0,
                "air_combat_repeat_release_penalty": -150.0,
                "air_combat_invalid_fire_penalty": -0.05,
            }
        )
        truth = SimpleNamespace(missiles_remaining=3, health=100.0)

        reward, terminated, truncated, status, terms, reason = apply_air_combat_reward_surface(
            loader,
            _sim(),
            truth,
            reward=0.0,
            terminated=False,
            truncated=False,
            status=[0.0, 0.0, 0.0, 0.0],
            reward_breakdown={},
        )

        self.assertEqual(reward, 300.0)
        self.assertFalse(terminated)
        self.assertFalse(truncated)
        self.assertIsNone(reason)
        self.assertEqual(status, [0.0, 0.0, 0.0, 0.0])
        self.assertEqual(terms["air_combat_first_release_bonus"], 300.0)
        self.assertEqual(loader._air_combat_reward_prev_missiles, 3)
        self.assertEqual(loader._air_combat_reward_release_count, 1)

    def test_invalid_fire_penalty_uses_effective_hybrid_pulse_without_release(self) -> None:
        loader = _loader(
            {
                "air_combat_release_shaping_enabled": True,
                "air_combat_first_release_bonus": 300.0,
                "air_combat_invalid_fire_penalty": -0.05,
            }
        )
        loader._last_effective_action[9] = 1.0
        truth = SimpleNamespace(missiles_remaining=4, health=100.0)

        reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
            loader,
            _sim(),
            truth,
            reward=0.0,
            terminated=False,
            truncated=False,
            status=[0.0, 0.0, 0.0, 0.0],
            reward_breakdown={},
        )

        self.assertAlmostEqual(reward, -0.05, places=6)
        self.assertAlmostEqual(terms["air_combat_invalid_fire_penalty"], -0.05, places=6)
        self.assertEqual(loader._air_combat_reward_prev_missiles, 4)
        self.assertEqual(loader._air_combat_reward_release_count, 0)


if __name__ == "__main__":
    unittest.main()
