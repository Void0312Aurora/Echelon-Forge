from __future__ import annotations

import math
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics import air_combat_stage0_process_probe as probe  # noqa: E402


class AirCombatProcessProbeTests(unittest.TestCase):
    def test_build_env_applies_multi_timescale_wrapper_from_train_config(self) -> None:
        class DummyEnv:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.unwrapped = self

        class DummyWrapper:
            def __init__(self, env, **kwargs):
                self.env = env
                self.kwargs = kwargs
                self.unwrapped = env.unwrapped

        old_env = probe.UniversalEnv
        old_wrapper = probe.MultiTimescaleActionWrapper
        old_get_spec = probe.get_action_wrapper_spec
        try:
            probe.UniversalEnv = DummyEnv
            probe.MultiTimescaleActionWrapper = DummyWrapper
            probe.get_action_wrapper_spec = lambda _cfg: (DummyWrapper, {"scripted_blend_indices": [0, 1, 2, 3]})

            env = probe._build_env(
                "scenarios/air_combat/1v1/dummy.json",
                {"env": {"action_mode": "air_combat_hybrid_v1"}},
            )

            self.assertIsInstance(env, DummyWrapper)
            self.assertEqual(env.kwargs["scripted_blend_indices"], [0, 1, 2, 3])
            self.assertIs(probe._base_env(env), env.env)
            self.assertEqual(env.env.kwargs["action_mode"], "air_combat_hybrid_v1")
        finally:
            probe.UniversalEnv = old_env
            probe.MultiTimescaleActionWrapper = old_wrapper
            probe.get_action_wrapper_spec = old_get_spec

    def test_hybrid_forced_fire_action_uses_hybrid_layout(self) -> None:
        action = probe._forced_fire_action(
            {},
            np.random.default_rng(7),
            1,
            action_mode="air_combat_hybrid_v1",
        )

        self.assertEqual(tuple(action.shape), (12,))
        self.assertEqual(float(action[6]), 1.0)
        self.assertEqual(float(action[7]), 1.0)
        self.assertEqual(float(action[8]), 1.0)
        self.assertEqual(float(action[9]), 1.0)
        self.assertEqual(probe._weapon_select_id(action, action_mode="air_combat_hybrid_v1"), 1)

    def test_episode_summary_reports_invalid_effective_fire_attempts(self) -> None:
        def row(step: int, *, fire: int = 0, release: int = 0) -> dict:
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
                "missiles_remaining": 2 - release,
                "missile_release": release,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": fire,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": float(fire),
                "effective_action_fire_weapon": float(fire),
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

        summary = probe._summarize_episode(
            [
                row(0),
                row(1, fire=1, release=1),
                row(2, fire=0, release=0),
                row(3, fire=1, release=0),
            ]
        )

        self.assertEqual(summary["fire_attempt_count"], 2)
        self.assertEqual(summary["release_count"], 1)
        self.assertEqual(summary["invalid_fire_attempt_count"], 1)
        self.assertEqual(summary["invalid_fire_attempt_steps"], [3])
        self.assertEqual(summary["invalid_fire_attempt_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
