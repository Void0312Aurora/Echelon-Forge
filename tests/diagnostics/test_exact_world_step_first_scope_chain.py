from __future__ import annotations

import base64
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports  # noqa: E402

ensure_repo_imports()

import ef_py  # noqa: E402

from tools.diagnostics.compare_exact_world_step_first_scope_chain import (  # noqa: E402
    compare_exact_world_step_first_scope_chain,
)
from tools.diagnostics.generate_exact_world_step_first_scope_chain_trace import (  # noqa: E402
    generate_cpu_exact_world_step_first_scope_chain_trace,
)
from tools.diagnostics.generate_exact_world_step_missile_guidance_trace import (  # noqa: E402
    spawn_runtime_from_guidance_trace,
)


class ExactWorldStepFirstScopeChainTests(unittest.TestCase):
    def test_first_scope_chain_matches_mixed_trace_final_stage(self) -> None:
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=19, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain(trace, use_gpu_guidance=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["missile_guidance_state_count"]), 2)
        self.assertEqual(int(report["missile_guidance_missile_count"]), 1)
        self.assertEqual(int(report["aircraft_tail_state_count"]), 2)
        self.assertFalse(report["used_cuda"])

    def test_first_scope_chain_with_gpu_guidance_matches_mixed_trace_final_stage(self) -> None:
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=27, time_step_s=0.05)
        report = compare_exact_world_step_first_scope_chain(trace, use_gpu_guidance=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_first_scope_chain_trace_v1")
        self.assertEqual(report["target_stage_name"], "MassUpdate")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertTrue(report["used_cuda"])
        self.assertEqual(int(report["missile_guidance_cuda_state_count"]), 2)
        self.assertEqual(int(report["missile_guidance_cuda_missile_count"]), 1)

    def test_first_scope_chain_matches_live_manual_pipeline(self) -> None:
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=23, time_step_s=0.05)
        runtime_live, refs_live, _ = spawn_runtime_from_guidance_trace(trace)

        packed_initial = base64.b64decode(trace["initial_exact_state_packed_b64"].encode("ascii"))
        packed_exec = bytes(ef_py.step_exact_world_step_first_scope_reference_cpu_packed(packed_initial))

        runtime_live.apply_exact_world_step_states_v1_batch_packed(refs_live, packed_initial)
        live_world = runtime_live.world(0)
        live_world.begin_exact_stage_trace_frame()
        try:
            for stage_name in trace["stage_sequence"]:
                self.assertTrue(live_world.run_exact_stage_trace_stage(str(stage_name)))
        finally:
            live_world.end_exact_stage_trace_frame()

        packed_live = bytes(runtime_live.extract_exact_world_step_states_v1_batch_packed(refs_live))
        sig_exec = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_exec))
        sig_live = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_live))
        self.assertEqual(sig_exec, sig_live)

        digests_exec = list(ef_py.exact_world_step_state_v1_component_digests_packed(packed_exec))
        digests_live = list(ef_py.exact_world_step_state_v1_component_digests_packed(packed_live))
        self.assertEqual(len(digests_exec), len(digests_live))
        for expected, actual in zip(digests_exec, digests_live):
            self.assertEqual(dict(expected), dict(actual))


if __name__ == "__main__":
    unittest.main()
