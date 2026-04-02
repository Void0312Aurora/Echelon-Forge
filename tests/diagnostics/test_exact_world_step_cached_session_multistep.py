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

from tools.diagnostics.compare_exact_world_step_cached_session_multistep import (  # noqa: E402
    compare_exact_world_step_cached_session_multistep,
)
from tools.diagnostics.generate_exact_world_step_cached_session_multistep_trace import (  # noqa: E402
    generate_cpu_exact_world_step_cached_session_multistep_trace,
)


class ExactWorldStepCachedSessionMultistepTests(unittest.TestCase):
    def test_generate_cached_session_multistep_trace(self) -> None:
        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(steps=4, seed=101, time_step_s=0.05)

        self.assertEqual(trace["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(trace["steps"]), 4)
        self.assertEqual(int(trace["world_count"]), 1)
        self.assertEqual(len(trace["step_traces"]), 4)
        self.assertEqual(str(trace["step_traces"][0]["stage_records"][0]["stage_name"]), "__step_initial__")
        self.assertEqual(str(trace["step_traces"][0]["final_record"]["stage_name"]), "MassUpdate")

    def test_generate_cached_session_multistep_trace_multiworld(self) -> None:
        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(
            steps=2,
            seed=101,
            time_step_s=0.05,
            world_count=4,
        )

        self.assertEqual(trace["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(trace["steps"]), 2)
        self.assertEqual(int(trace["world_count"]), 4)
        self.assertEqual(len(trace["step_traces"]), 2)
        self.assertEqual(len(trace["step_traces"][0]["pilot_actions"]), 4)
        self.assertEqual(len(trace["step_traces"][0]["final_record"]["instrument"]), 4)

    def test_compare_cached_session_multistep_cpu_matches_trace(self) -> None:
        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(steps=4, seed=101, time_step_s=0.05)
        report = compare_exact_world_step_cached_session_multistep(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(report["world_count"]), 1)
        self.assertTrue(report["all_apply_signatures_match"])
        self.assertTrue(report["all_packed_component_digests_match"])
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertFalse(report["used_cuda"])

    def test_compare_cached_session_multistep_cpu_step_batch_backend_matches_trace(self) -> None:
        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(steps=4, seed=101, time_step_s=0.05)
        report = compare_exact_world_step_cached_session_multistep(
            trace,
            use_gpu=False,
            use_runtime_step_batch_backend=True,
            abs_tol=1e-6,
            max_examples=4,
        )

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertTrue(bool(report["runtime_step_batch_backend_used"]))
        self.assertEqual(int(report["world_count"]), 1)
        self.assertTrue(report["all_apply_signatures_match"])
        self.assertTrue(report["all_packed_component_digests_match"])
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertFalse(report["used_cuda"])

    def test_compare_cached_session_multistep_cpu_multiworld_matches_trace(self) -> None:
        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(
            steps=3,
            seed=101,
            time_step_s=0.05,
            world_count=3,
        )
        report = compare_exact_world_step_cached_session_multistep(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(report["world_count"]), 3)
        self.assertTrue(report["all_apply_signatures_match"])
        self.assertTrue(report["all_packed_component_digests_match"])
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertFalse(report["used_cuda"])

    def test_compare_cached_session_multistep_gpu_matches_trace(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(steps=8, seed=101, time_step_s=0.05)
        report = compare_exact_world_step_cached_session_multistep(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertTrue(report["used_cuda"])
        self.assertTrue(report["all_apply_signatures_match"])
        self.assertTrue(report["all_packed_component_digests_match"])
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertFalse(bool(report["first_divergence_localization"]))

    def test_compare_cached_session_multistep_gpu_multiworld_localizes_first_divergence(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(
            steps=2,
            seed=101,
            time_step_s=0.05,
            world_count=4,
        )
        report = compare_exact_world_step_cached_session_multistep(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(report["world_count"]), 4)
        self.assertTrue(report["used_cuda"])
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertTrue(bool(report["all_apply_signatures_match"]))
        self.assertTrue(bool(report["all_packed_component_digests_match"]))
        self.assertIsNone(report["first_divergence_localization"])

    def test_compare_cached_session_multistep_gpu_world_count_16_matches_trace(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(
            steps=8,
            seed=101,
            time_step_s=0.05,
            world_count=16,
        )
        report = compare_exact_world_step_cached_session_multistep(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertEqual(int(report["world_count"]), 16)
        self.assertTrue(report["used_cuda"])
        self.assertTrue(bool(report["all_apply_signatures_match"]))
        self.assertTrue(bool(report["all_packed_component_digests_match"]))
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertIsNone(report["first_divergence_localization"])

    def test_compare_cached_session_multistep_gpu_world_count_16_runtime_step_batch_backend_matches_trace(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        trace = generate_cpu_exact_world_step_cached_session_multistep_trace(
            steps=8,
            seed=101,
            time_step_s=0.05,
            world_count=16,
        )
        report = compare_exact_world_step_cached_session_multistep(
            trace,
            use_gpu=True,
            use_runtime_step_batch_backend=True,
            abs_tol=1e-6,
            max_examples=4,
        )

        self.assertEqual(report["trace_kind"], "cpu_exact_cached_session_multistep_trace_v1")
        self.assertTrue(bool(report["runtime_step_batch_backend_used"]))
        self.assertEqual(int(report["world_count"]), 16)
        self.assertTrue(report["used_cuda"])
        self.assertTrue(bool(report["all_apply_signatures_match"]))
        self.assertTrue(bool(report["all_packed_component_digests_match"]))
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertEqual(int(report["first_divergence_step"]), 0)
        self.assertIsNone(report["first_divergence_localization"])


if __name__ == "__main__":
    unittest.main()
