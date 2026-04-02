from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports  # noqa: E402

ensure_repo_imports()

import ef_py  # noqa: E402

from tools.diagnostics.compare_exact_world_step_aircraft_chain_cuda import (  # noqa: E402
    compare_exact_world_step_aircraft_chain_cuda,
)
from tools.diagnostics.generate_exact_world_step_system_trace import (  # noqa: E402
    generate_cpu_exact_world_step_system_trace,
)


class ExactWorldStepAircraftChainCudaTests(unittest.TestCase):
    def test_aircraft_chain_cpu_fallback_matches_mass_update_stage(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_aircraft_chain_cuda(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertFalse(report["used_cuda"])
        self.assertEqual(int(report["aircraft_chain_state_count"]), 2)

    def test_aircraft_chain_gpu_matches_mass_update_stage(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[23, 31], time_step_s=0.05)
        report = compare_exact_world_step_aircraft_chain_cuda(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["aircraft_chain_state_count"]), 2)
        if bool(report["use_gpu_requested"]):
            self.assertTrue(report["used_cuda"])


if __name__ == "__main__":
    unittest.main()
