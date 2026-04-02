from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics.compare_exact_world_step_shadow_trace import (  # noqa: E402
    compare_exact_world_step_shadow_trace,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (  # noqa: E402
    generate_cpu_exact_world_step_parity_trace,
)


class ExactWorldStepShadowTraceTests(unittest.TestCase):
    def test_shadow_trace_comparator_replays_trace_and_matches_cpu_gpu(self) -> None:
        trace = generate_cpu_exact_world_step_parity_trace(seeds=[11, 17], steps=4, time_step_s=0.05)
        report = compare_exact_world_step_shadow_trace(trace, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_world_step_parity_v1")
        self.assertIn("hidden_dynamics", trace["step_records"][0])
        self.assertEqual(len(trace["step_records"][0]["hidden_dynamics"]), 2)
        self.assertIn("angular_velocity", trace["step_records"][0]["hidden_dynamics"][0])
        self.assertIn("aero_state", trace["step_records"][0]["hidden_dynamics"][0])
        self.assertIn("force_accumulator", trace["step_records"][0]["hidden_dynamics"][0])
        self.assertIn("control_law_state", trace["step_records"][0]["hidden_dynamics"][0])
        self.assertIn("egi", trace["step_records"][0]["hidden_dynamics"][0])
        self.assertEqual(report["cpu_reference"]["step_count"], 5)
        self.assertEqual(report["gpu_shadow"]["step_count"], 5)
        self.assertEqual(report["cpu_vs_gpu"]["step_count"], 5)

        self.assertTrue(report["cpu_reference"]["steps"][0]["packed_apply_signatures_match"])
        self.assertTrue(report["cpu_reference"]["steps"][0]["live_apply_signatures_match"])
        self.assertTrue(report["gpu_shadow"]["steps"][0]["packed_apply_signatures_match"])
        self.assertTrue(report["gpu_shadow"]["steps"][0]["live_apply_signatures_match"])

        self.assertAlmostEqual(float(report["cpu_vs_gpu"]["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["cpu_vs_gpu"]["total_mismatches"]), 0)
        self.assertTrue(report["cpu_vs_gpu"]["all_apply_signatures_match"])


if __name__ == "__main__":
    unittest.main()
