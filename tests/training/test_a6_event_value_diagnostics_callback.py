from __future__ import annotations

import unittest

import torch as th

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.training_callbacks import CMODiagnosticsCallback


class _DummyLogger:
    def __init__(self) -> None:
        self.records: dict[str, float] = {}

    def record(self, key: str, value, *args, **kwargs) -> None:
        self.records[str(key)] = float(value)


class _DummyModel:
    a6_first_event_hazard_coef = 0.2
    a6_first_event_curriculum_coef = 0.1
    a6_first_event_deadline_weight = 0.4

    def __init__(self, logger: _DummyLogger) -> None:
        self.logger = logger

    def _current_a6_first_event_curriculum_coef(self) -> float:
        return 0.075


class _DummyHybridDistribution:
    def __init__(self, open_mask: bool = True) -> None:
        self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
        self.fire_event_mask = th.tensor([[1, int(open_mask)]], dtype=th.bool)
        self.categorical_logits = [
            (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
        ]

    def _fire_event_logits(self):
        return th.tensor([[1.0, 3.0]], dtype=th.float32)

    def fire_event_logit_delta(self):
        return th.tensor([2.0], dtype=th.float32)

    def fire_event_probability(self):
        return th.sigmoid(self.fire_event_logit_delta())


class _DummyHybridPolicy:
    device = "cpu"

    def __init__(self, open_mask: bool = True) -> None:
        self.open_mask = bool(open_mask)

    def obs_to_tensor(self, obs):
        return obs, False

    def get_distribution(self, obs):
        return _DummyHybridDistribution(open_mask=self.open_mask)


class A6EventValueDiagnosticsCallbackTests(unittest.TestCase):
    def test_records_a6_open_window_event_delta_and_probability(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1)
        logger = _DummyLogger()
        model = _DummyModel(logger)
        model.policy = _DummyHybridPolicy(open_mask=True)
        cb.model = model

        cb._record_policy_distribution_diagnostics({"instruments": [[0.0] * 42]})

        self.assertAlmostEqual(logger.records["a6/open_window_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["a6/event_logit_delta_mean_open"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["a6/event_fire_prob_mean_open"], 0.8807970, places=6)
        self.assertAlmostEqual(logger.records["a6/event_fire_prob_max_open"], 0.8807970, places=6)
        self.assertAlmostEqual(logger.records["diag/pi_wsel_mode_mean"], 1.0, places=6)

    def test_records_a6_stable_zeros_when_window_is_closed(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1)
        logger = _DummyLogger()
        model = _DummyModel(logger)
        model.policy = _DummyHybridPolicy(open_mask=False)
        cb.model = model

        cb._record_policy_distribution_diagnostics({"instruments": [[0.0] * 42]})

        self.assertAlmostEqual(logger.records["a6/open_window_count"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/event_logit_delta_mean_open"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/event_fire_prob_mean_open"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/event_fire_prob_max_open"], 0.0, places=6)

    def test_records_a6_label_counts_from_infos(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1)
        logger = _DummyLogger()
        cb.model = _DummyModel(logger)

        cb._record_a6_first_event_info_diagnostics(
            [
                {
                    "a6_first_event_active": 1,
                    "a6_first_event_target": 0,
                    "a6_first_event_weight": 0.5,
                    "a6_first_event_source": "curriculum",
                    "a6_first_event_window_id": 7,
                },
                {
                    "a6_first_event_active": 1,
                    "a6_first_event_target": 1,
                    "a6_first_event_weight": 0.5,
                    "a6_first_event_source": "curriculum",
                    "a6_first_event_window_id": 7,
                },
                {
                    "a6_first_event_active": 0,
                    "a6_first_event_target": 0,
                    "a6_first_event_weight": 0,
                    "a6_first_event_source": "censored",
                    "a6_first_event_window_id": 8,
                },
                {
                    "a6_first_event_active": 1,
                    "a6_first_event_target": 1,
                    "a6_first_event_weight": 0.4,
                    "a6_first_event_source": "deadline",
                    "a6_first_event_window_id": 8,
                },
            ]
        )

        self.assertAlmostEqual(logger.records["a6/hazard_coef"], 0.2, places=6)
        self.assertAlmostEqual(logger.records["a6/curriculum_coef"], 0.075, places=6)
        self.assertAlmostEqual(logger.records["a6/deadline_weight"], 0.4, places=6)
        self.assertAlmostEqual(logger.records["a6/active_count"], 3.0, places=6)
        self.assertAlmostEqual(logger.records["a6/active_frac"], 3.0 / 4.0, places=6)
        self.assertAlmostEqual(logger.records["a6/target_positive_count"], 2.0, places=6)
        self.assertAlmostEqual(logger.records["a6/target_positive_frac"], 2.0 / 3.0, places=6)
        self.assertAlmostEqual(logger.records["a6/curriculum_positive_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["a6/deadline_positive_count"], 1.0, places=6)
        self.assertAlmostEqual(logger.records["a6/censored_window_count"], 1.0, places=6)

    def test_records_a6_label_stable_zeros_when_enabled_but_absent(self) -> None:
        cb = CMODiagnosticsCallback(log_every_timesteps=1)
        logger = _DummyLogger()
        cb.model = _DummyModel(logger)

        cb._record_a6_first_event_info_diagnostics([{}])

        self.assertAlmostEqual(logger.records["a6/hazard_coef"], 0.2, places=6)
        self.assertAlmostEqual(logger.records["a6/curriculum_coef"], 0.075, places=6)
        self.assertAlmostEqual(logger.records["a6/deadline_weight"], 0.4, places=6)
        self.assertAlmostEqual(logger.records["a6/active_count"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/target_positive_frac"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/deadline_positive_count"], 0.0, places=6)
        self.assertAlmostEqual(logger.records["a6/censored_window_count"], 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
