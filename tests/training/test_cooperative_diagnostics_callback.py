from __future__ import annotations

import unittest

import torch as th

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.training_callbacks import CMODiagnosticsCallback  # noqa: E402
from python.training.diagnostics import (  # noqa: E402
    TrainingEventDiagnosticsWindow,
    record_a5_event_info_diagnostics,
    record_action_diagnostics,
    record_basic_step_diagnostics,
    record_hmoe_policy_diagnostics,
    record_leader_diagnostics,
    record_reward_term_diagnostics,
    record_runway_gear_diagnostics,
)


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
        logger = _DummyLogger()
        window = TrainingEventDiagnosticsWindow(
            terminal_reward_keys=CMODiagnosticsCallback.TERMINAL_REWARD_KEYS,
            preterm_window_steps=4,
        )
        window.episodes_window = 2
        window.term_counts_window["success_waypoint"] = 1
        window.term_counts_window["timeout"] = 1
        window.term_counts_total["success_waypoint"] = 3
        window.term_counts_total["timeout"] = 2
        window.coop_world_done_window = 1
        window.coop_world_success_window = 1
        window.coop_timeout_window = 0
        window.coop_shared_reset_window = 1
        window.coop_world_min_progress_window.append(0.75)
        window.coop_world_max_progress_window.append(1.0)
        window.coop_world_progress_gap_window.append(0.25)
        window.coop_role_episode_counts_window["ElementLead"] = 1
        window.coop_role_success_counts_window["ElementLead"] = 1
        window.coop_role_shared_reset_counts_window["ElementLead"] = 0
        window.coop_role_term_counts_window["ElementLead"]["success_waypoint"] = 1
        window.coop_role_reward_window["ElementLead"].append(3900.0)
        window.coop_role_length_window["ElementLead"].append(5000.0)
        window.coop_role_waypoint_index_window["ElementLead"].append(4.0)
        window.coop_role_waypoint_progress_window["ElementLead"].append(1.0)
        window.coop_role_episode_counts_window["Wingman"] = 1
        window.coop_role_success_counts_window["Wingman"] = 0
        window.coop_role_shared_reset_counts_window["Wingman"] = 1
        window.coop_role_term_counts_window["Wingman"]["running"] = 1
        window.coop_role_reward_window["Wingman"].append(2400.0)
        window.coop_role_length_window["Wingman"].append(5000.0)
        window.coop_role_waypoint_index_window["Wingman"].append(3.0)
        window.coop_role_waypoint_progress_window["Wingman"].append(0.75)
        window.coop_world_slot_progress_values[0] = [1.0, 0.75]

        window.record_and_reset(logger=logger)

        self.assertIn("coop_diag/world_episodes_done_window", logger.records)
        self.assertAlmostEqual(logger.records["coop_diag/world_success_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/shared_reset_per_world_mean"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/world_waypoint_progress_gap_frac_mean"], 0.25, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_elementlead_success_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_elementlead_waypoint_progress_frac_mean"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_shared_reset_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_term_frac_running"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["coop_diag/role_wingman_waypoint_progress_frac_mean"], 0.75, places=6)
        self.assertEqual(window.episodes_window, 0)

    def test_event_window_observes_terminal_failure_and_preterm_snapshot(self) -> None:
        logger = _DummyLogger()
        window = TrainingEventDiagnosticsWindow(
            terminal_reward_keys=("total", "crash_penalty"),
            preterm_window_steps=4,
        )
        window.reset_for_training(1)

        window.observe_step(
            obs={"instruments": [[120.0, 0.0, 0.0, 80.0, 0.0, 3.0, -2.0, 5.0, -20.0, 0.0, 1.1, 0.0, 0.0, 0.0, 4.0]]},
            actions=[[0.0, 0.0, 0.0, 0.6] + [0.0] * 13],
            rewards=[0.5],
            infos=[{}],
            dones=[False],
        )
        window.observe_step(
            obs={"instruments": [[100.0, 0.0, 0.0, 20.0, 0.0, 6.0, -4.0, 10.0, -45.0, 0.0, 2.0, 0.0, 0.0, 0.0, 8.0]]},
            actions=[[0.0, 0.0, 0.0, 0.4] + [0.0] * 13],
            rewards=[-10.0],
            infos=[{"reward_terms": {"total": -10.0, "crash_penalty": -20.0}}],
            dones=[True],
        )

        window.record_and_reset(logger=logger)

        self.assertAlmostEqual(logger.records["diag/episodes_done_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/failure_frac_window"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/term_frac_crash"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/term_rew_total"], -10.0, places=6)
        self.assertAlmostEqual(logger.records["diag/preterm_window_len_steps"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/preterm_min_alt_agl_m"], 20.0, places=6)

    def test_basic_step_helper_records_reward_instrument_and_ils_scalars(self) -> None:
        logger = _DummyLogger()
        row = [0.0] * 42
        row[0] = 110.0
        row[2] = 1200.0
        row[5] = 2.5
        row[7] = -3.0
        row[8] = 4.0
        row[-4] = 1.0
        row[-3] = -0.25

        record_basic_step_diagnostics(
            logger=logger,
            obs={"instruments": [row]},
            rewards=[1.0, 3.0],
        )

        self.assertAlmostEqual(logger.records["diag/reward_mean"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/ias_mean"], 110.0, places=6)
        self.assertAlmostEqual(logger.records["diag/alt_baro_mean"], 1200.0, places=6)
        self.assertAlmostEqual(logger.records["diag/aoa_mean"], 2.5, places=6)
        self.assertAlmostEqual(logger.records["diag/ils_valid_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/ils_loc_abs_mean"], 0.25, places=6)

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

    def test_a5_event_info_helper_records_rates_from_infos(self) -> None:
        logger = _DummyLogger()

        record_a5_event_info_diagnostics(
            logger=logger,
            infos=[
                {
                    "engagement_state": "AuthorizedReady",
                    "fire_mask": "yes",
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
                    "fire_once_rejected_reason": "pending assessment",
                    "release_executed": False,
                    "post_launch_suppressed": True,
                    "fire_mask_components": {"fire_mask_c2_authorized": 1, "fire_mask_not_pending_assessment": 0},
                },
            ],
        )

        self.assertAlmostEqual(logger.records["diag/a5_event_info_count"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_mask_open_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_once_requested_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_fire_once_rejected_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_reject_reason_pending_assessment_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/a5_state_authorizedready_frac"], 0.5, places=6)
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

    def test_leader_helper_records_observation_info_and_reward_metrics(self) -> None:
        logger = _DummyLogger()

        record_leader_diagnostics(
            logger=logger,
            obs={
                "ownship": [[100.0, 0.0, 30.0, 1000.0, -2.0, 180.0, 0.0, -10.0, 5.0, 0.0, 0.0, 1.0]],
                "terminal": [[1200.0, -0.3, 0.2, 0.0, 4.0, -5.0, 1.0, 0.0]],
            },
            infos=[
                {
                    "leader_phase_guarded": 1.0,
                    "leader_bias_guarded": 0.0,
                    "leader_terminal_feasible": 1.0,
                    "leader_phase_bucket": "Approach",
                    "leader_requested_phase_bucket": "Landing",
                    "leader_phase_guard_reason": "Too Steep",
                    "leader_bias_guard_reason": "No Bias",
                    "leader_c2_task_name": "Final Approach",
                    "leader_c2_transition_reason": "Runway Capture",
                    "leader_effective_command": [0.2, 100.0, 2000.0, 250.0],
                    "leader_baseline_command": [0.1, 90.0, 1000.0, 200.0],
                    "leader_report_valid": 1.0,
                    "leader_c2_transitioned": 1.0,
                    "leader_reward_terms": {"execution_reward": 2.0},
                },
                {
                    "leader_phase_guarded": 0.0,
                    "leader_bias_guarded": 1.0,
                    "leader_terminal_feasible": 0.0,
                    "leader_phase_bucket": "Approach",
                    "leader_report_valid": 0.0,
                    "leader_c2_transitioned": 0.0,
                    "leader_reward_terms": {"execution_reward": 4.0, "invalid_phase_penalty": -1.0},
                },
            ],
            reward_keys=("execution_reward", "invalid_phase_penalty"),
        )

        self.assertAlmostEqual(logger.records["leader_diag/ias_mean"], 100.0, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/dme_mean_m"], 1200.0, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/phase_guarded_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/bias_guarded_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/phase_frac_approach"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/request_frac_landing"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/guard_reason_frac_too_steep"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/bias_guard_reason_frac_no_bias"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/c2_task_frac_final_approach"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/c2_transition_reason_frac_runway_capture"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/report_valid_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/reward_execution_reward"], 3.0, places=6)
        self.assertAlmostEqual(logger.records["leader_diag/reward_invalid_phase_penalty"], -1.0, places=6)

    def test_reward_term_helper_records_step_reward_means(self) -> None:
        logger = _DummyLogger()

        record_reward_term_diagnostics(
            logger=logger,
            infos=[
                {"reward_terms": {"total": 1.0, "survival": 0.25}},
                {"reward_terms": {"total": 3.0, "survival": "bad", "untracked": -2.0}},
                {},
            ],
            reward_keys=("total", "survival", "untracked", "missing"),
        )

        self.assertAlmostEqual(logger.records["diag/rew_total"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["diag/rew_survival"], 0.25, places=6)
        self.assertAlmostEqual(logger.records["diag/rew_untracked"], -2.0, places=6)
        self.assertNotIn("diag/rew_missing", logger.records)

    def test_runway_gear_helper_records_step_info_metrics(self) -> None:
        logger = _DummyLogger()

        record_runway_gear_diagnostics(
            logger=logger,
            infos=[
                {
                    "on_runway": 1.0,
                    "on_runway_geom": 1.0,
                    "runway_cross_m": -2.0,
                    "gear_collapsed": 0.0,
                    "gear_stress": 0.25,
                },
                {
                    "on_runway": 0.0,
                    "on_runway_geom": 1.0,
                    "runway_cross_m": 4.0,
                    "gear_collapsed": 1.0,
                    "gear_stress": 0.75,
                },
            ],
        )

        self.assertAlmostEqual(logger.records["diag/on_runway_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/on_runway_geom_frac"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["diag/runway_cross_abs_mean_m"], 3.0, places=6)
        self.assertAlmostEqual(logger.records["diag/runway_cross_abs_p95_m"], 3.9, places=6)
        self.assertAlmostEqual(logger.records["diag/runway_cross_abs_max_m"], 4.0, places=6)
        self.assertAlmostEqual(logger.records["diag/gear_collapsed_frac"], 0.5, places=6)
        self.assertAlmostEqual(logger.records["diag/gear_stress_mean"], 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
