from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from tools.diagnostics.m3s2_structural_toy_probe import ToyProbeConfig, run_probe  # noqa: E402


class M3S2StructuralToyProbeTests(unittest.TestCase):
    def _config(self, *, model: str, train_steps: int, learning_rate: float) -> ToyProbeConfig:
        return ToyProbeConfig(
            model=model,
            prewindow_steps=12,
            quality_steps=24,
            train_steps=train_steps,
            learning_rate=learning_rate,
            initial_logit=-6.0,
            hidden_size=16,
            seed=7,
            early_mass_coef=2.0,
            early_mass_budget=0.02,
            early_survival_coef=8.0,
            window_delay_coef=0.5,
            window_deadline_coef=0.5,
            window_deadline_steps=8,
            max_grad_norm=2.0,
            prewindow_risk_gate=0.02,
            window_mass_gate=0.95,
        )

    def test_free_logits_structural_toy_crosses_quality_boundary(self) -> None:
        result = run_probe(self._config(model="free_logits", train_steps=500, learning_rate=0.1))

        self.assertTrue(result["verdict"]["structural_toy_pass"])
        final = result["final"]
        self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
        self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
        self.assertIsNotNone(final["first_quality_boundary_cross_step"])
        self.assertGreaterEqual(float(final["mean_p_window"]), 0.95)

    def test_mlp_structural_toy_learns_with_explicit_quality_feature(self) -> None:
        result = run_probe(self._config(model="mlp", train_steps=800, learning_rate=0.02))

        self.assertTrue(result["verdict"]["structural_toy_pass"])
        final = result["final"]
        self.assertLessEqual(float(final["prewindow_cumulative_event_risk"]), 0.02)
        self.assertEqual(int(final["prewindow_boundary_cross_count"]), 0)
        self.assertIsNotNone(final["first_quality_boundary_cross_step"])
        self.assertGreaterEqual(float(final["quality_prob_max"]), 0.5)


if __name__ == "__main__":
    unittest.main()
