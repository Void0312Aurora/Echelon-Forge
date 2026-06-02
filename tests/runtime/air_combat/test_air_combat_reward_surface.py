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
    loader.mission_cmd = {
        "assigned_target_id": 2,
        "authorization_to_fire": True,
        "roe_state": 3,
    }
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

    def test_c2_roe_hold_fire_bonus_is_additive_when_no_fire_attempt_occurs(self) -> None:
        loader = _loader(
            {
                "air_combat_c2_roe_release_discipline_enabled": True,
                "air_combat_roe_hold_fire_bonus": 0.25,
            }
        )
        loader.mission_cmd.update(
            {
                "wcs_state": 1,
                "engage_order_state": 3,
                "shot_policy_state": 0,
                "shot_budget_remaining": 0,
                "pending_assessment": False,
                "authorization_to_fire": False,
            }
        )
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

        self.assertAlmostEqual(reward, 0.25, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_hold_fire_bonus"], 0.25, places=6)
        self.assertNotIn("air_combat_invalid_fire_penalty", terms)

    def test_c2_roe_hold_fire_violation_penalizes_fire_attempt_without_release(self) -> None:
        loader = _loader(
            {
                "air_combat_c2_roe_release_discipline_enabled": True,
                "air_combat_roe_hold_fire_violation_penalty": -2.5,
            }
        )
        loader.mission_cmd.update(
            {
                "wcs_state": 1,
                "engage_order_state": 3,
                "shot_policy_state": 0,
                "shot_budget_remaining": 0,
                "pending_assessment": False,
                "authorization_to_fire": False,
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

        self.assertAlmostEqual(reward, -2.5, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_hold_fire_violation_penalty"], -2.5, places=6)

    def test_c2_roe_authorized_salvo_release_gets_valid_and_salvo_terms(self) -> None:
        loader = _loader(
            {
                "air_combat_c2_roe_release_discipline_enabled": True,
                "air_combat_roe_valid_authorized_release_bonus": 1.0,
                "air_combat_roe_authorized_first_release_bonus": 2.0,
                "air_combat_roe_authorized_salvo_bonus": 3.0,
            }
        )
        loader.mission_cmd.update(
            {
                "wcs_state": 2,
                "engage_order_state": 2,
                "shot_policy_state": 2,
                "shot_budget_remaining": 2,
                "pending_assessment": False,
                "authorization_to_fire": True,
            }
        )
        loader._last_effective_action[9] = 1.0
        truth = SimpleNamespace(missiles_remaining=3, health=100.0)

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

        self.assertAlmostEqual(reward, 6.0, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_valid_authorized_release_bonus"], 1.0, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_authorized_first_release_bonus"], 2.0, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_authorized_salvo_bonus"], 3.0, places=6)
        self.assertEqual(loader._air_combat_reward_release_count, 1)

    def test_c2_roe_shot_budget_violation_blocks_authorized_release_bonus(self) -> None:
        loader = _loader(
            {
                "air_combat_c2_roe_release_discipline_enabled": True,
                "air_combat_roe_valid_authorized_release_bonus": 1.0,
                "air_combat_roe_shot_budget_violation_penalty": -4.0,
            }
        )
        loader.mission_cmd.update(
            {
                "wcs_state": 2,
                "engage_order_state": 2,
                "shot_policy_state": 1,
                "shot_budget_remaining": 0,
                "pending_assessment": False,
                "authorization_to_fire": True,
            }
        )
        loader._last_effective_action[9] = 1.0
        truth = SimpleNamespace(missiles_remaining=3, health=100.0)

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

        self.assertAlmostEqual(reward, -4.0, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_shot_budget_violation_penalty"], -4.0, places=6)
        self.assertNotIn("air_combat_roe_valid_authorized_release_bonus", terms)

    def test_c2_roe_pending_assessment_violation_is_separate_from_unauthorized_fire(self) -> None:
        loader = _loader(
            {
                "air_combat_c2_roe_release_discipline_enabled": True,
                "air_combat_roe_pending_assessment_penalty": -3.0,
                "air_combat_roe_unauthorized_fire_penalty": -5.0,
            }
        )
        loader.mission_cmd.update(
            {
                "wcs_state": 2,
                "engage_order_state": 2,
                "shot_policy_state": 1,
                "shot_budget_remaining": 1,
                "pending_assessment": True,
                "authorization_to_fire": True,
            }
        )
        loader._air_combat_reward_release_count = 1
        loader._last_effective_action[9] = 1.0
        truth = SimpleNamespace(missiles_remaining=3, health=100.0)

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

        self.assertAlmostEqual(reward, -3.0, places=6)
        self.assertAlmostEqual(terms["air_combat_roe_pending_assessment_penalty"], -3.0, places=6)
        self.assertNotIn("air_combat_roe_unauthorized_fire_penalty", terms)


if __name__ == "__main__":
    unittest.main()
