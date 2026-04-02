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

from tools.diagnostics.compare_exact_world_step_first_scope_chain_cuda import (  # noqa: E402
    compare_exact_world_step_first_scope_chain_cuda,
)
from tools.diagnostics.benchmark_exact_world_step_first_scope_chain_cached_session import (  # noqa: E402
    benchmark_exact_world_step_first_scope_chain_cached_session,
)
from tools.diagnostics.benchmark_exact_world_step_first_scope_chain_cached_session_matrix import (  # noqa: E402
    run_cached_session_matrix,
)
from tools.diagnostics.generate_exact_world_step_first_scope_chain_trace import (  # noqa: E402
    generate_cpu_exact_world_step_first_scope_chain_trace,
)


class ExactWorldStepFirstScopeChainCudaTests(unittest.TestCase):
    def test_first_scope_chain_cpu_fallback_matches_mixed_trace_final_stage(self) -> None:
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=37, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain_cuda(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertFalse(report["used_cuda"])
        self.assertEqual(int(report["first_scope_chain_state_count"]), 2)
        self.assertEqual(int(report["first_scope_chain_missile_count"]), 1)

    def test_first_scope_chain_gpu_matches_mixed_trace_final_stage(self) -> None:
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=41, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain_cuda(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["first_scope_chain_state_count"]), 2)
        self.assertEqual(int(report["first_scope_chain_missile_count"]), 1)
        if bool(report["use_gpu_requested"]):
            self.assertTrue(report["used_cuda"])

    def test_first_scope_chain_resident_gpu_matches_mixed_trace_final_stage(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=43, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain_cuda(
            trace,
            use_gpu=True,
            resident=True,
            abs_tol=1e-6,
            max_examples=4,
        )

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["resident_path_used"])
        self.assertTrue(report["used_cuda"])
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["first_scope_chain_state_count"]), 2)
        self.assertEqual(int(report["first_scope_chain_missile_count"]), 1)
        self.assertEqual(int(report["first_scope_chain_output_state_count"]), 2)
        self.assertGreater(int(report["first_scope_chain_output_device_ptr"]), 0)

    def test_first_scope_chain_runtime_resident_gpu_matches_mixed_trace_final_stage(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=59, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain_cuda(
            trace,
            use_gpu=True,
            runtime_resident=True,
            abs_tol=1e-6,
            max_examples=4,
        )

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertFalse(report["resident_path_used"])
        self.assertTrue(report["runtime_resident_path_used"])
        self.assertTrue(report["used_cuda"])
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["first_scope_chain_state_count"]), 2)
        self.assertEqual(int(report["first_scope_chain_missile_count"]), 1)
        self.assertGreaterEqual(float(report["runtime_resident_total_wall_ms"]), 0.0)
        self.assertEqual(int(report["first_scope_chain_output_state_count"]), 2)
        self.assertGreater(int(report["first_scope_chain_output_device_ptr"]), 0)

    def test_first_scope_chain_runtime_cached_session_gpu_matches_mixed_trace_final_stage(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=67, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain_cuda(
            trace,
            use_gpu=True,
            runtime_cached_session=True,
            abs_tol=1e-6,
            max_examples=4,
        )

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertFalse(report["resident_path_used"])
        self.assertFalse(report["runtime_resident_path_used"])
        self.assertTrue(report["runtime_cached_session_path_used"])
        self.assertTrue(report["used_cuda"])
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["first_scope_chain_state_count"]), 2)
        self.assertEqual(int(report["first_scope_chain_missile_count"]), 1)
        self.assertGreaterEqual(float(report["runtime_resident_upload_wall_ms"]), 0.0)
        self.assertGreaterEqual(float(report["runtime_resident_replay_wall_ms"]), 0.0)

    def test_first_scope_chain_cached_session_multistep_cpu_final_flush_matches_live_world(self) -> None:
        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=4,
            use_gpu=False,
            write_back_every=0,
            final_write_back=True,
        )

        self.assertFalse(report["used_cuda"])
        self.assertEqual(report["write_back_steps"], [4])
        self.assertTrue(report["final_live_synced"])
        self.assertTrue(report["final_cached_apply_signatures_match"])
        self.assertTrue(report["final_cached_component_digests_match"])
        self.assertTrue(report["final_live_apply_signatures_match"])
        self.assertTrue(report["final_live_component_digests_match"])
        self.assertEqual(len(report["step_reports"]), 4)
        self.assertGreaterEqual(float(report["flush_wall_ms"]), 0.0)
        self.assertGreaterEqual(float(report["prime_runtime_stats"]["prime_extract_ms"]), 0.0)
        self.assertGreaterEqual(float(report["step_reports"][0]["cpu_runtime_step_stats"]["step_total_ms"]), 0.0)

    def test_first_scope_chain_cached_session_multistep_gpu_periodic_write_back_matches_cpu(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")
        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=4,
            use_gpu=True,
            write_back_every=2,
            final_write_back=False,
        )

        self.assertTrue(report["used_cuda"])
        self.assertEqual(report["write_back_steps"], [2, 4])
        self.assertTrue(report["final_live_synced"])
        self.assertTrue(report["final_live_apply_signatures_match"])
        self.assertTrue(report["final_live_component_digests_match"])
        self.assertEqual(len(report["step_reports"]), 4)
        self.assertTrue(report["step_reports"][0]["apply_signatures_match"])
        self.assertTrue(report["step_reports"][0]["component_digests_match"])
        self.assertTrue(report["step_reports"][1]["apply_signatures_match"])
        self.assertTrue(report["step_reports"][1]["component_digests_match"])
        self.assertGreater(float(report["last_cuda_step_stats"]["state_count"]), 0)
        self.assertGreaterEqual(float(report["prime_runtime_stats"]["prime_extract_ms"]), 0.0)
        self.assertGreaterEqual(float(report["test_first_runtime_step_total_ms"]), 0.0)
        self.assertGreaterEqual(float(report["test_warm_runtime_step_overhead_ms"]), 0.0)

    def test_first_scope_chain_cached_session_multistep_cpu_multiworld_matches_reference(self) -> None:
        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=4,
            use_gpu=False,
            world_count=3,
            write_back_every=0,
            final_write_back=True,
        )

        self.assertEqual(int(report["world_count"]), 3)
        self.assertEqual(int(report["cached_state_count"]), 3)
        self.assertFalse(report["used_cuda"])
        self.assertEqual(len(report["step_reports"]), 4)
        self.assertTrue(report["final_cached_component_digests_match"])
        self.assertTrue(report["final_live_component_digests_match"])
        self.assertGreaterEqual(float(report["test_warm_chain_command_lane_ms"]), 0.0)
        self.assertGreaterEqual(float(report["test_warm_runtime_step_total_ms_per_state"]), 0.0)

    def test_first_scope_chain_cached_session_runtime_step_batch_cpu_matches_reference(self) -> None:
        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=4,
            use_gpu=False,
            world_count=1,
            write_back_every=1,
            final_write_back=True,
            use_runtime_step_batch_backend=True,
        )

        self.assertFalse(report["used_cuda"])
        self.assertTrue(bool(report["runtime_step_batch_backend_used"]))
        self.assertEqual(report["write_back_steps"], [1, 2, 3, 4])
        self.assertTrue(report["final_live_synced"])
        self.assertEqual(int(report["first_cpu_divergence_step"]), 0)
        self.assertTrue(report["final_cached_component_digests_match"])
        self.assertTrue(report["final_live_component_digests_match"])
        self.assertEqual(len(report["step_reports"]), 4)
        self.assertTrue(bool(report["step_reports"][0]["write_back"]))
        self.assertGreaterEqual(float(report["test_warm_runtime_step_total_ms"]), 0.0)

    def test_first_scope_chain_cached_session_runtime_step_batch_gpu_world_count_16_matches_reference(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=8,
            use_gpu=True,
            world_count=16,
            write_back_every=1,
            final_write_back=True,
            use_runtime_step_batch_backend=True,
        )

        self.assertTrue(report["used_cuda"])
        self.assertTrue(bool(report["runtime_step_batch_backend_used"]))
        self.assertEqual(int(report["world_count"]), 16)
        self.assertEqual(int(report["cached_state_count"]), 16)
        self.assertEqual(report["write_back_steps"], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertTrue(report["final_live_synced"])
        self.assertEqual(int(report["first_cpu_divergence_step"]), 0)
        self.assertTrue(report["final_cached_apply_signatures_match"])
        self.assertTrue(report["final_cached_component_digests_match"])
        self.assertTrue(report["final_live_apply_signatures_match"])
        self.assertTrue(report["final_live_component_digests_match"])
        self.assertEqual(len(report["step_reports"]), 8)
        for step_report in report["step_reports"]:
            self.assertTrue(bool(step_report["write_back"]))
            self.assertTrue(bool(step_report["apply_signatures_match"]))
            self.assertTrue(bool(step_report["component_digests_match"]))
            self.assertEqual(
                int(step_report["cuda_step_stats"]["missile_count"]),
                0,
            )
            self.assertEqual(
                int(step_report["test_runtime_step_stats"]["state_count"]),
                16,
            )
            self.assertEqual(
                float(step_report["test_runtime_step_stats"]["chain_device_to_host_ms"]),
                0.0,
            )
            self.assertEqual(
                float(step_report["test_runtime_step_stats"]["chain_command_lane_ms"]),
                0.0,
            )
        self.assertTrue(bool(report["last_cuda_step_stats"]["used_cuda"]))
        self.assertEqual(int(report["last_cuda_step_stats"]["state_count"]), 16)
        self.assertEqual(int(report["last_cuda_step_stats"]["missile_count"]), 0)
        self.assertGreaterEqual(float(report["test_warm_runtime_step_total_ms"]), 0.0)
        self.assertGreaterEqual(float(report["test_warm_chain_share_of_runtime_step"]), 0.0)
        self.assertLessEqual(float(report["test_warm_chain_share_of_runtime_step"]), 1.0)
        self.assertGreaterEqual(float(report["test_warm_write_back_share_of_runtime_step"]), 0.0)
        self.assertLessEqual(float(report["test_warm_write_back_share_of_runtime_step"]), 1.0)
        self.assertGreaterEqual(float(report["test_warm_runtime_step_overhead_share"]), 0.0)
        self.assertLessEqual(float(report["test_warm_runtime_step_overhead_share"]), 1.0)
        self.assertGreaterEqual(float(report["test_warm_write_back_vs_chain_ratio"]), 0.0)
        self.assertGreaterEqual(float(report["test_vs_cpu_total_wall_speedup"]), 0.0)
        self.assertGreaterEqual(float(report["test_vs_cpu_warm_step_wall_speedup"]), 0.0)
        self.assertGreaterEqual(float(report["test_vs_cpu_warm_runtime_step_speedup"]), 0.0)
        self.assertEqual(float(report["test_warm_write_back_ms"]), 0.0)
        self.assertEqual(float(report["test_warm_write_back_share_of_runtime_step"]), 0.0)
        self.assertEqual(float(report["test_warm_write_back_vs_chain_ratio"]), 0.0)
        self.assertTrue(bool(report["promotion_gate_evaluated"]))
        self.assertTrue(bool(report["promotion_parity_ready"]))
        self.assertTrue(bool(report["promotion_write_back_ready"]))
        self.assertFalse(bool(report["promotion_ready"]))
        self.assertIn("total_wall_speedup", list(report["promotion_blockers"]))
        self.assertIn("warm_runtime_step_speedup", list(report["promotion_blockers"]))
        self.assertNotIn("write_back_share", list(report["promotion_blockers"]))
        self.assertNotIn("write_back_vs_chain_ratio", list(report["promotion_blockers"]))

    def test_first_scope_chain_cached_session_gpu_matrix_reports_multiworld_rows(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        report = run_cached_session_matrix(
            world_counts=[1, 4],
            steps=4,
            use_gpu=True,
            write_back_every=0,
            final_write_back=True,
        )

        self.assertEqual(report["world_counts"], [1, 4])
        self.assertEqual(len(report["runs"]), 2)
        row1, row4 = report["runs"]
        self.assertTrue(bool(row1["used_cuda"]))
        self.assertEqual(int(row1["world_count"]), 1)
        self.assertEqual(int(row1["first_cpu_divergence_step"]), 0)
        self.assertTrue(bool(row1["final_cached_component_digests_match"]))
        self.assertTrue(bool(row1["final_live_component_digests_match"]))
        self.assertTrue(bool(row4["used_cuda"]))
        self.assertEqual(int(row4["world_count"]), 4)
        self.assertEqual(int(row4["first_cpu_divergence_step"]), 0)
        self.assertTrue(bool(row4["final_cached_component_digests_match"]))
        self.assertTrue(bool(row4["final_live_component_digests_match"]))
        for row in (row1, row4):
            self.assertGreaterEqual(float(row["test_warm_chain_total_ms"]), 0.0)
            self.assertGreaterEqual(float(row["test_warm_chain_host_to_device_ms"]), 0.0)
            self.assertGreaterEqual(float(row["test_warm_chain_command_lane_ms"]), 0.0)
            self.assertGreaterEqual(float(row["test_warm_runtime_step_total_ms_per_state"]), 0.0)
            self.assertGreaterEqual(float(row["test_warm_chain_share_of_runtime_step"]), 0.0)
            self.assertLessEqual(float(row["test_warm_chain_share_of_runtime_step"]), 1.0)
            self.assertGreaterEqual(float(row["test_warm_write_back_share_of_runtime_step"]), 0.0)
            self.assertLessEqual(float(row["test_warm_write_back_share_of_runtime_step"]), 1.0)
            self.assertGreaterEqual(float(row["test_warm_write_back_vs_chain_ratio"]), 0.0)
            self.assertGreaterEqual(float(row["test_vs_cpu_total_wall_speedup"]), 0.0)
            self.assertGreaterEqual(float(row["test_vs_cpu_warm_runtime_step_speedup"]), 0.0)

    def test_first_scope_chain_cached_session_gpu_runtime_step_batch_matrix_reports_promotion_ratios(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")

        report = run_cached_session_matrix(
            world_counts=[1, 16],
            steps=4,
            use_gpu=True,
            write_back_every=1,
            final_write_back=True,
            use_runtime_step_batch_backend=True,
        )

        self.assertEqual(report["world_counts"], [1, 16])
        self.assertTrue(bool(report["runtime_step_batch_backend_used"]))
        self.assertEqual(
            report["promotion_thresholds"],
            {
                "min_total_wall_speedup": 1.0,
                "min_warm_runtime_step_speedup": 1.0,
                "max_write_back_share_of_runtime_step": 0.25,
                "max_write_back_vs_chain_ratio": 0.5,
            },
        )
        self.assertEqual(len(report["runs"]), 2)
        expected_promotion_ready_world_counts = [
            int(row["world_count"])
            for row in report["runs"]
            if bool(row["promotion_ready"])
        ]
        expected_promotion_blocked_world_counts = [
            int(row["world_count"])
            for row in report["runs"]
            if not bool(row["promotion_ready"])
        ]
        self.assertEqual(report["promotion_ready_world_counts"], expected_promotion_ready_world_counts)
        self.assertEqual(report["promotion_blocked_world_counts"], expected_promotion_blocked_world_counts)
        self.assertEqual(
            int(report["first_promotion_ready_world_count"]),
            int(expected_promotion_ready_world_counts[0]) if expected_promotion_ready_world_counts else 0,
        )
        self.assertEqual(
            int(report["first_promotion_blocked_world_count"]),
            int(expected_promotion_blocked_world_counts[0]) if expected_promotion_blocked_world_counts else 0,
        )
        expected_dominance_world_counts = [
            int(row["world_count"])
            for row in report["runs"]
            if bool(row["write_back_dominates_warm_chain"])
        ]
        self.assertEqual(report["write_back_dominance_world_counts"], expected_dominance_world_counts)
        self.assertEqual(
            int(report["first_write_back_dominance_world_count"]),
            int(expected_dominance_world_counts[0]) if expected_dominance_world_counts else 0,
        )
        for row in report["runs"]:
            self.assertTrue(bool(row["used_cuda"]))
            self.assertTrue(bool(row["runtime_step_batch_backend_used"]))
            self.assertEqual(int(row["first_cpu_divergence_step"]), 0)
            self.assertTrue(bool(row["final_cached_component_digests_match"]))
            self.assertTrue(bool(row["final_live_component_digests_match"]))
            self.assertEqual(float(row["test_warm_chain_command_lane_ms"]), 0.0)
            self.assertGreaterEqual(float(row["test_warm_chain_share_of_runtime_step"]), 0.0)
            self.assertLessEqual(float(row["test_warm_chain_share_of_runtime_step"]), 1.0)
            self.assertGreaterEqual(float(row["test_warm_write_back_share_of_runtime_step"]), 0.0)
            self.assertLessEqual(float(row["test_warm_write_back_share_of_runtime_step"]), 1.0)
            self.assertGreaterEqual(float(row["test_warm_runtime_step_overhead_share"]), 0.0)
            self.assertLessEqual(float(row["test_warm_runtime_step_overhead_share"]), 1.0)
            self.assertGreaterEqual(float(row["test_warm_write_back_vs_chain_ratio"]), 0.0)
            self.assertGreaterEqual(float(row["test_vs_cpu_total_wall_speedup"]), 0.0)
            self.assertGreaterEqual(float(row["test_vs_cpu_warm_step_wall_speedup"]), 0.0)
            self.assertGreaterEqual(float(row["test_vs_cpu_warm_runtime_step_speedup"]), 0.0)
            self.assertEqual(float(row["test_warm_write_back_ms"]), 0.0)
            self.assertEqual(float(row["test_warm_write_back_share_of_runtime_step"]), 0.0)
            self.assertEqual(float(row["test_warm_write_back_vs_chain_ratio"]), 0.0)
            self.assertNotIn("write_back_share", list(row["promotion_blockers"]))
            self.assertNotIn("write_back_vs_chain_ratio", list(row["promotion_blockers"]))
            self.assertIsInstance(row["promotion_blockers"], list)

if __name__ == "__main__":
    unittest.main()
