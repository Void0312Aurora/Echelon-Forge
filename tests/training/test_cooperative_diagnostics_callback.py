from __future__ import annotations

import unittest

import torch as th

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.training_callbacks import CMODiagnosticsCallback  # noqa: E402
from python.training.diagnostics import record_action_diagnostics, record_hmoe_policy_diagnostics  # noqa: E402


class _DummyLogger:
    def __init__(self) -> None:
        self.records: dict[str, float] = {}

    def record(self, key: str, value, *args, **kwargs) -> None:
        try:
            self.records[str(key)] = float(value)
        except Exception:
            self.records[str(key)] = value


class _DummyModel:
    def __init__(self, logger: _DummyLogger) -> None:
        self.logger = logger


class _DummyPolicy:
    def get_hmoe_route_stats(self) -> dict[str, float]:
        return {
            "hmoe/fam/nav": 0.5,
            "hmoe/sub/nav/route": 0.5,
        }

    def get_hmoe_parameter_stats(self) -> dict[str, float]:
        return {
            "hmoe_params/family/nonzero_frac": 0.25,
            "hmoe_params/sub/nonzero_frac": 0.5,
        }


class _DummyHybridDistribution:
    def __init__(self) -> None:
        self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
        self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
        self.categorical_logits = [
            (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
        ]

    def _fire_event_logits(self):
        return th.tensor([[1.0, 3.0]], dtype=th.float32)


class _DummyHybridPolicy:
    device = "cpu"

    def obs_to_tensor(self, obs):
        return obs, False

    def get_distribution(self, obs):
        return _DummyHybridDistribution()


class CooperativeDiagnosticsCallbackTests(unittest.TestCase):
    def test_records_role_and_world_window_metrics(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1, preterm_window_steps=4)
        logger = _DummyLogger()
        cb.model = _DummyModel(logger)
        cb._episodes_window = 2
        cb._term_counts_window["success_waypoint"] = 1
        cb._term_counts_window["timeout"] = 1
        cb._term_counts_total["success_waypoint"] = 3
        cb._term_counts_total["timeout"] = 2
        cb._coop_world_done_window = 1
        cb._coop_world_success_window = 1
        cb._coop_timeout_window = 0
        cb._coop_shared_reset_window = 1
        cb._coop_world_min_progress_window.append(0.75)
        cb._coop_world_max_progress_window.append(1.0)
        cb._coop_world_progress_gap_window.append(0.25)
        cb._coop_role_episode_counts_window["ElementLead"] = 1
        cb._coop_role_success_counts_window["ElementLead"] = 1
        cb._coop_role_shared_reset_counts_window["ElementLead"] = 0
        cb._coop_role_term_counts_window["ElementLead"]["success_waypoint"] = 1
        cb._coop_role_reward_window["ElementLead"].append(3900.0)
        cb._coop_role_length_window["ElementLead"].append(5000.0)
        cb._coop_role_waypoint_index_window["ElementLead"].append(4.0)
        cb._coop_role_waypoint_progress_window["ElementLead"].append(1.0)
        cb._coop_role_episode_counts_window["Wingman"] = 1
        cb._coop_role_success_counts_window["Wingman"] = 0
        cb._coop_role_shared_reset_counts_window["Wingman"] = 1
        cb._coop_role_term_counts_window["Wingman"]["running"] = 1
        cb._coop_role_reward_window["Wingman"].append(2400.0)
        cb._coop_role_length_window["Wingman"].append(5000.0)
        cb._coop_role_waypoint_index_window["Wingman"].append(3.0)
        cb._coop_role_waypoint_progress_window["Wingman"].append(0.75)
        cb._coop_world_slot_progress_values[0] = [1.0, 0.75]

        cb._record_event_diagnostics()

        self.assertIn("coop_diag/world_episodes_done_window", logger.records)
        self.assertAlmostEqual(logger.records["coop_diag/world_success_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/shared_reset_per_world_mean"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/world_waypoint_progress_gap_frac_mean"], 0.25, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_elementlead_success_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_elementlead_waypoint_progress_frac_mean"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_shared_reset_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_term_frac_running"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_waypoint_progress_frac_mean"], 0.75, places=6)

    def test_records_hmoe_route_stats_when_policy_exposes_them(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1, preterm_window_steps=4)
        logger = _DummyLogger()
        model = _DummyModel(logger)
        model.policy = _DummyPolicy()
        cb.model = model
        cb.locals = {
            "new_obs": {"instruments": [[0.0] * 26]},
            "actions": [[0.0] * 17],
            "rewards": [0.0],
            "infos": [{}],
            "dones": [False],
        }
        cb.num_timesteps = 1
        cb._histories = []
        cb._next_log_t = 1

        self.assertTrue(cb._on_step())
        self.assertAlmostEqual(logger.records["hmoe/fam/nav"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["hmoe/sub/nav/route"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["hmoe_params/family/nonzero_frac"], 0.25, places=6)
        self.assertAlmostEqual(logger.records["hmoe_params/sub/nonzero_frac"], 0.5, places=6)

    def test_hmoe_policy_helper_keeps_parameter_stats_throttled(self) -> None:
        logger = _DummyLogger()
        model = _DummyModel(logger)
        model.policy = _DummyPolicy()

        next_t = record_hmoe_policy_diagnostics(
            model=model,
            logger=logger,
            num_timesteps=4,
            next_param_stats_t=10,
            log_every_timesteps=5,
        )

        self.assertEqual(next_t, 10)
        self.assertAlmostEqual(logger.records["hmoe/fam/nav"], 0.5, places=6)
        self.assertNotIn("hmoe_params/family/nonzero_frac", logger.records)

        next_t = record_hmoe_policy_diagnostics(
            model=model,
            logger=logger,
            num_timesteps=10,
            next_param_stats_t=next_t,
            log_every_timesteps=5,
        )

        self.assertEqual(next_t, 15)
        self.assertAlmostEqual(logger.records["hmoe_params/family/nonzero_frac"], 0.25, places=6)
        self.assertAlmostEqual(logger.records["hmoe_params/sub/nonzero_frac"], 0.5, places=6)

    def test_records_hybrid_policy_binary_logits_when_policy_exposes_distribution(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1, preterm_window_steps=4)
        logger = _DummyLogger()
        model = _DummyModel(logger)
        model.policy = _DummyHybridPolicy()
        cb.model = model
        cb.locals = {
            "new_obs": {"instruments": [[0.0] * 42]},
            "actions": [[0.0, 0.0, 0.0, 0.6, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0]],
            "rewards": [0.0],
            "infos": [{}],
            "dones": [False],
        }
        cb.num_timesteps = 1
        cb._histories = []
        cb._next_log_t = 1

        self.assertTrue(cb._on_step())

        self.assertAlmostEqual(logger.records["diag/pi_bin_tms_logit_mean"], -1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_bin_tms_p_mean"], 0.2689414, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_bin_fire_logit_mean"], -0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_bin_fire_p_mean"], 0.3775407, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_event_fire_p_mean"], 0.8807970, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_event_mode_fire_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_event_fire_mask_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_wsel_mode_mean"], 1.0, places=6)
        self.assertGreater(
            logger.records["diag/pi_wsel_s1_p_mean"],
            logger.records["diag/pi_wsel_s0_p_mean"],
        )

    def test_records_a5_event_info_rates_from_infos(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1, preterm_window_steps=4)
        logger = _DummyLogger()
        cb.model = _DummyModel(logger)
        cb.locals = {
            "new_obs": {"instruments": [[0.0] * 42, [0.0] * 42]},
            "actions": [[0.0] * 12, [0.0] * 12],
            "rewards": [0.0, 0.0],
            "infos": [
                {
                    "engagement_state": "AuthorizedReady",
                    "fire_mask": 1,
                    "fire_once_requested": True,
                    "fire_once_accepted": True,
                    "release_executed": True,
                    "post_launch_suppressed": False,
                    "fire_mask_components": {"fire_mask_c2_authorized": 1},
                },
                {
                    "engagement_state": "FiredAssess",
                    "fire_mask": 0,
                    "fire_once_requested": True,
                    "fire_once_accepted": False,
                    "fire_once_rejected_reason": "pending_assessment",
                    "release_executed": False,
                    "post_launch_suppressed": True,
                    "fire_mask_components": {"fire_mask_c2_authorized": 1, "fire_mask_not_pending_assessment": 0},
                },
            ],
            "dones": [False, False],
        }
        cb.num_timesteps = 1
        cb._histories = []
        cb._next_log_t = 1

        self.assertTrue(cb._on_step())

        self.assertAlmostEqual(logger.records["diag/a5_event_info_count"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_mask_open_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_once_requested_count"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_once_accepted_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_once_rejected_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_post_launch_suppressed_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_reject_reason_pending_assessment_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_state_authorizedready_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_state_firedassess_frac"], 0.5, places=6)
        self.assertAlmostEqual(
            logger.records["diag/a5_mask_component_fire_mask_not_pending_assessment_open_frac"],
            0.0,
            places=6,
        )

    def test_hybrid_air_combat_actions_are_not_logged_as_full_action_brakes(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1, preterm_window_steps=4)
        logger = _DummyLogger()
        cb.model = _DummyModel(logger)
        cb.locals = {
            "new_obs": {"instruments": [[0.0] * 42]},
            "actions": [[0.0, 0.0, 0.0, 0.6, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]],
            "rewards": [0.0],
            "infos": [{}],
            "dones": [False],
        }
        cb.num_timesteps = 1
        cb._histories = []
        cb._next_log_t = 1

        self.assertTrue(cb._on_step())

        self.assertNotIn("diag/action_brake_any_frac", logger.records)
        self.assertNotIn("diag/action_brake_amt_mean", logger.records)
        self.assertAlmostEqual(logger.records["diag/action_radar_active_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/action_master_arm_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/action_fire_weapon_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/action_weapon_select_id_mean"], 1.0, places=6)

    def test_action_helper_records_full_action_brake_and_combat_switches(self) -> None:
        logger = _DummyLogger()

        record_action_diagnostics(
            logger=logger,
            actions=[
                [0.1, -0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.75, 0.1, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.5],
                [-0.1, 0.2, -0.3, 0.6, 0.0, 0.0, 0.0, 0.25, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0],
            ],
        )

        self.assertAlmostEqual(logger.records["diag/action_pitch_mean"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["diag/action_throttle_mean"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/action_brake_any_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/action_brake_amt_mean"], 0.55, places=6)
        self.assertAlmostEqual(logger.records["diag/action_radar_active_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/action_tms_up_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/action_master_arm_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/action_fire_gun_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/action_weapon_select_id_mean"], 5.0, places=6)


if __name__ == "__main__":
    unittest.main()
