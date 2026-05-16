from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.training_callbacks import CMODiagnosticsCallback  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
