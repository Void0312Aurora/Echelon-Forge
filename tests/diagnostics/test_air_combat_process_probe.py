from __future__ import annotations

import math
import unittest

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics import air_combat_stage0_process_probe as probe  # noqa: E402


class _DummyHybridDistribution:
    def __init__(self) -> None:
        self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
        self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
        self.categorical_logits = [
            (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
        ]

    def _fire_event_logits(self):
        return th.tensor([[1.0, 3.0]], dtype=th.float32)


class AirCombatProcessProbeTests(unittest.TestCase):
    def test_distribution_policy_diagnostics_extract_hybrid_binary_probabilities(self) -> None:
        diagnostics = probe._distribution_policy_diagnostics(_DummyHybridDistribution())

        self.assertAlmostEqual(diagnostics["policy_logit_tms_up"], -1.0, places=6)
        self.assertAlmostEqual(diagnostics["policy_prob_tms_up"], 0.2689414, places=6)
        self.assertAlmostEqual(diagnostics["policy_logit_fire_weapon"], -0.5, places=6)
        self.assertAlmostEqual(diagnostics["policy_prob_fire_weapon"], 0.3775407, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once"], 0.8807970, places=6)
        self.assertEqual(int(diagnostics["policy_event_mode"]), 1)
        self.assertEqual(int(diagnostics["policy_event_mask_fire_once"]), 1)
        self.assertEqual(int(diagnostics["policy_weapon_select_mode"]), 1)
        self.assertGreater(
            diagnostics["policy_weapon_select_station1_prob"],
            diagnostics["policy_weapon_select_station0_prob"],
        )

    def test_a5_event_info_columns_copy_runtime_event_contract_fields(self) -> None:
        columns = probe._a5_event_info_columns(
            {
                "engagement_state": "FiredAssess",
                "fire_mask": 0,
                "event_action_mask": [1, 0],
                "fire_once_requested": True,
                "fire_once_accepted": False,
                "fire_once_rejected_reason": "pending_assessment",
                "release_executed": False,
                "post_launch_suppressed": True,
                "reattack_ready": False,
                "fire_mask_components": {
                    "fire_mask_c2_authorized": 1,
                    "fire_mask_not_pending_assessment": 0,
                },
            }
        )

        self.assertEqual(columns["engagement_state"], "FiredAssess")
        self.assertEqual(columns["fire_mask"], 0)
        self.assertEqual(columns["event_action_mask_json"], "[1,0]")
        self.assertEqual(columns["event_action_mask_hold"], 1)
        self.assertEqual(columns["event_action_mask_fire_once"], 0)
        self.assertEqual(columns["fire_once_requested"], 1)
        self.assertEqual(columns["fire_once_accepted"], 0)
        self.assertEqual(columns["fire_once_rejected"], 1)
        self.assertEqual(columns["fire_once_rejected_reason"], "pending_assessment")
        self.assertEqual(columns["post_launch_suppressed"], 1)
        self.assertEqual(
            columns["fire_mask_components_json"],
            '{"fire_mask_c2_authorized":1,"fire_mask_not_pending_assessment":0}',
        )
        self.assertEqual(columns["fire_mask_c2_authorized"], 1)
        self.assertEqual(columns["fire_mask_not_pending_assessment"], 0)

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

    def test_episode_summary_reports_authorized_window_policy_diagnostics(self) -> None:
        def row(
            step: int,
            *,
            auth: int = 1,
            pending: int = 0,
            shot_budget: int = 1,
            fire_prob: float = 0.2,
            fire_logit: float = -1.0,
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
                "authorization_to_fire": auth,
                "shot_budget_remaining": shot_budget,
                "pending_assessment": pending,
                "c2_roe_hold_fire": 0,
                "c2_roe_hold_fire_obeyed": 0,
                "c2_roe_hold_fire_violation": 0,
                "c2_roe_unauthorized_release_count": 0,
                "c2_roe_authorized_release_count": 0,
                "c2_roe_valid_authorized_release_count": 0,
                "c2_roe_violation_release_count": 0,
                "c2_roe_pending_assessment_release_count": 0,
                "c2_roe_premature_second_shot": 0,
                "c2_roe_shot_budget_violation": 0,
                "c2_roe_authorized_salvo_release_count": 0,
                "c2_roe_authorized_reattack_release_count": 0,
                "c2_roe_legacy_fallback_release_count": 0,
                "policy_prob_tms_up": 0.4,
                "policy_logit_tms_up": -0.25,
                "policy_prob_fire_weapon": fire_prob,
                "policy_logit_fire_weapon": fire_logit,
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
                row(0, auth=0),
                row(1, fire_prob=0.25, fire_logit=-0.8),
                row(2, fire_prob=0.55, fire_logit=0.2),
                row(3, pending=1, shot_budget=0, fire_prob=0.9, fire_logit=1.2),
            ]
        )

        self.assertEqual(summary["authorized_window_step_count"], 2)
        self.assertAlmostEqual(summary["policy_prob_fire_weapon_max"], 0.9, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_mean"], 0.4, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_max"], 0.55, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_logit_fire_weapon_max"], 0.2, places=6)

    def test_episode_summary_reports_a5_event_action_counts(self) -> None:
        def row(
            step: int,
            *,
            state: str = "Hold",
            mask: int = 0,
            requested: int = 0,
            accepted: int = 0,
            executed: int = 0,
            suppressed: int = 0,
            reason: str = "",
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
                "missiles_remaining": 4 - executed,
                "missile_release": executed,
                "missile_release_delta": executed,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": requested,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": float(requested),
                "effective_action_fire_weapon": float(accepted),
                "authorization_to_fire": int(mask),
                "shot_budget_remaining": 1,
                "pending_assessment": int(state == "FiredAssess"),
                "engagement_state": state,
                "fire_mask": mask,
                "fire_once_requested": requested,
                "fire_once_accepted": accepted,
                "fire_once_rejected": int(requested and not accepted),
                "fire_once_rejected_reason": reason,
                "release_executed": executed,
                "post_launch_suppressed": suppressed,
                "policy_event_prob_fire_once": event_prob,
                "policy_event_logit_fire_once": event_prob,
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

        summary = probe._summarize_episode(
            [
                row(0),
                row(1, state="AuthorizedReady", mask=1, requested=1, accepted=1, executed=1, event_prob=0.8, event_mode=1),
                row(2, state="FiredAssess", requested=1, reason="pending_assessment", suppressed=1, event_prob=0.0),
                row(3, state="FiredAssess"),
            ]
        )

        self.assertEqual(summary["fire_mask_open_step_count"], 1)
        self.assertEqual(summary["fire_once_requested_count"], 2)
        self.assertEqual(summary["fire_once_accepted_count"], 1)
        self.assertEqual(summary["fire_once_rejected_count"], 1)
        self.assertEqual(summary["release_executed_count"], 1)
        self.assertEqual(summary["post_launch_suppressed_count"], 1)
        self.assertEqual(summary["fire_once_rejected_reason_counts"], {"pending_assessment": 1})
        self.assertEqual(summary["engagement_state_counts"], {"AuthorizedReady": 1, "FiredAssess": 2})
        self.assertEqual(summary["policy_event_mode_fire_once_count"], 1)
        self.assertEqual(summary["policy_event_mask_fire_once_open_count"], 1)

    def test_c2_roe_event_columns_split_authorized_salvo_and_budget_violation(self) -> None:
        state = {
            "contract_present": True,
            "roe_state": 2,
            "wcs_state": 2,
            "authorization_to_fire": True,
            "engage_order_state": 2,
            "shot_policy_state": 2,
            "shot_budget_remaining": 1,
            "pending_assessment": False,
        }

        columns = probe._c2_roe_event_columns(
            state,
            release_delta=2,
            fire_attempted=True,
            previous_release_count=0,
        )

        self.assertEqual(columns["c2_roe_release_bucket"], "authorized_salvo")
        self.assertEqual(columns["c2_roe_authorized_release_count"], 1)
        self.assertEqual(columns["c2_roe_authorized_salvo_release_count"], 1)
        self.assertEqual(columns["c2_roe_shot_budget_violation"], 1)
        self.assertEqual(columns["c2_roe_violation_release_count"], 1)

    def test_episode_summary_reports_c2_roe_release_discipline_buckets(self) -> None:
        def row(
            step: int,
            *,
            fire: int = 0,
            release_delta: int = 0,
            auth: int = 1,
            wcs: int = 2,
            pending: int = 0,
            authorized: int = 0,
            violation: int = 0,
            unauthorized: int = 0,
            pending_release: int = 0,
            salvo: int = 0,
            reattack: int = 0,
            hold_violation: int = 0,
        ) -> dict:
            return {
                "episode": 0,
                "step": step,
                "reward": 0.0,
                "terminated": int(step == 4),
                "truncated": 0,
                "termination_reason": "combat_timeout" if step == 4 else "",
                "target_range_geom_m": 12000.0 - step,
                "target_health": 100.0,
                "can_fire": 1,
                "target_contact": 1,
                "target_active": 1,
                "missiles_remaining": 4 - release_delta,
                "missile_release": int(release_delta > 0),
                "missile_release_delta": release_delta,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": fire,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": float(fire),
                "effective_action_fire_weapon": float(fire),
                "roe_state": 2,
                "wcs_state": wcs,
                "authorization_to_fire": auth,
                "pending_assessment": pending,
                "c2_roe_hold_fire": int(wcs == 1),
                "c2_roe_hold_fire_obeyed": 0,
                "c2_roe_hold_fire_violation": hold_violation,
                "c2_roe_unauthorized_release_count": unauthorized,
                "c2_roe_authorized_release_count": authorized,
                "c2_roe_valid_authorized_release_count": authorized,
                "c2_roe_violation_release_count": violation,
                "c2_roe_pending_assessment_release_count": pending_release,
                "c2_roe_premature_second_shot": 0,
                "c2_roe_shot_budget_violation": 0,
                "c2_roe_authorized_salvo_release_count": salvo,
                "c2_roe_authorized_reattack_release_count": reattack,
                "c2_roe_legacy_fallback_release_count": 0,
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
                row(0, fire=0, auth=0, wcs=1),
                row(1, fire=1, release_delta=1, authorized=1, salvo=1),
                row(2, fire=0),
                row(3, fire=1, release_delta=1, auth=1, pending=1, violation=1, pending_release=1),
                row(4, fire=1, release_delta=1, auth=0, wcs=1, violation=1, unauthorized=1, hold_violation=1),
            ]
        )

        self.assertEqual(summary["authorized_release_count"], 1)
        self.assertEqual(summary["unauthorized_release_count"], 1)
        self.assertEqual(summary["violation_release_count"], 2)
        self.assertEqual(summary["pending_assessment_release_count"], 1)
        self.assertEqual(summary["authorized_salvo_release_count"], 1)
        self.assertEqual(summary["authorized_reattack_release_count"], 0)
        self.assertEqual(summary["fire_under_hold_count"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["authorized"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["unauthorized"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["violation"], 2)
        self.assertEqual(summary["roe_state_at_fire"], [2, 2])
        self.assertEqual(summary["authorization_to_fire_at_fire"], [1, 1])

    def test_legal_mask_fire_action_waits_for_open_mask_delay_and_one_shot(self) -> None:
        old_open = probe._legal_fire_mask_open
        try:
            probe._legal_fire_mask_open = lambda *args, **kwargs: True

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=30,
                fire_delay_steps=31,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 31)
            self.assertEqual(float(action[9]), 0.0)

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=31,
                fire_delay_steps=31,
            )

            self.assertTrue(fired)
            self.assertEqual(age, 32)
            self.assertEqual(float(action[9]), 1.0)

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=True,
                legal_open_age_steps=32,
                fire_delay_steps=31,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 33)
            self.assertEqual(float(action[9]), 0.0)
        finally:
            probe._legal_fire_mask_open = old_open

    def test_legal_mask_fire_action_resets_age_when_mask_closes(self) -> None:
        old_open = probe._legal_fire_mask_open
        try:
            probe._legal_fire_mask_open = lambda *args, **kwargs: False

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=12,
                fire_delay_steps=0,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 0)
            self.assertEqual(float(action[9]), 0.0)
        finally:
            probe._legal_fire_mask_open = old_open


if __name__ == "__main__":
    unittest.main()
