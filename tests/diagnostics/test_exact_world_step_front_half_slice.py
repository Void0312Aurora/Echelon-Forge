from __future__ import annotations

import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports  # noqa: E402

ensure_repo_imports()

import ef_py  # noqa: E402

from tools.diagnostics.compare_exact_world_step_front_half_slice import (  # noqa: E402
    compare_exact_world_step_front_half_slice,
)
from tools.diagnostics.generate_exact_world_step_system_trace import (  # noqa: E402
    generate_cpu_exact_world_step_system_trace,
)


class ExactWorldStepFrontHalfSliceTests(unittest.TestCase):
    def test_front_half_reference_cpu_matches_groundcontact_stage_in_system_trace(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_front_half_slice(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["target_stage_name"], "GroundContact")
        self.assertFalse(report["used_cuda"])
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["front_half_state_count"]), 2)

    def test_front_half_gpu_backend_runs_against_groundcontact_stage(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_front_half_slice(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["target_stage_name"], "GroundContact")
        self.assertEqual(int(report["front_half_state_count"]), 2)

        info = ef_py.probe_gpu_device()
        if bool(info.cuda_runtime_available):
            self.assertTrue(report["use_gpu_requested"])
            self.assertTrue(report["used_cuda"])
            self.assertGreaterEqual(float(report["front_half_kernel_ms"]), 0.0)
            self.assertTrue(report["apply_signatures_match"])
            self.assertTrue(report["packed_component_digests_match"])
            self.assertEqual(int(report["mismatch_count"]), 0)
            self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        else:
            self.assertFalse(report["used_cuda"])
            self.assertTrue(report["apply_signatures_match"])
            self.assertTrue(report["packed_component_digests_match"])
            self.assertEqual(int(report["mismatch_count"]), 0)


if __name__ == "__main__":
    unittest.main()
