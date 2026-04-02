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

from tools.diagnostics.compare_exact_world_step_missile_guidance_slice import (  # noqa: E402
    compare_exact_world_step_missile_guidance_slice,
)
from tools.diagnostics.generate_exact_world_step_missile_guidance_trace import (  # noqa: E402
    generate_cpu_exact_world_step_missile_guidance_trace,
    spawn_runtime_from_guidance_trace,
)


def _component_digest_map(packed: bytes) -> dict[str, int]:
    digests = list(ef_py.exact_world_step_state_v1_component_digests_packed(packed))
    if len(digests) != 2:
        raise AssertionError(f"expected two state digests, got {len(digests)}")
    return {str(key): int(value) for key, value in dict(digests[0]).items()}


class ExactWorldStepMissileGuidanceSliceTests(unittest.TestCase):
    def test_missile_guidance_slice_matches_guidance_trace(self) -> None:
        trace = generate_cpu_exact_world_step_missile_guidance_trace(seed=19, time_step_s=0.05)
        report = compare_exact_world_step_missile_guidance_slice(trace, use_gpu=False, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_missile_guidance_trace_v1")
        self.assertEqual(report["target_stage_name"], "MissileGuidance")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["missile_guidance_state_count"]), 2)
        self.assertEqual(int(report["missile_guidance_missile_count"]), 1)
        self.assertFalse(report["used_cuda"])

    def test_missile_guidance_cuda_slice_matches_guidance_trace(self) -> None:
        trace = generate_cpu_exact_world_step_missile_guidance_trace(seed=29, time_step_s=0.05)
        report = compare_exact_world_step_missile_guidance_slice(trace, use_gpu=True, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_missile_guidance_trace_v1")
        self.assertEqual(report["target_stage_name"], "MissileGuidance")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["missile_guidance_cuda_state_count"]), 2)
        self.assertEqual(int(report["missile_guidance_cuda_missile_count"]), 1)
        self.assertTrue(report["used_cuda"])

    def test_missile_guidance_slice_matches_live_direct_stage(self) -> None:
        trace = generate_cpu_exact_world_step_missile_guidance_trace(seed=23, time_step_s=0.05)
        runtime, refs, _ = spawn_runtime_from_guidance_trace(trace)

        packed_initial = bytes(ef_py.step_exact_world_step_missile_guidance_reference_cpu_packed(
            bytes(__import__("base64").b64decode(trace["initial_exact_state_packed_b64"].encode("ascii")))
        ))

        runtime.apply_exact_world_step_states_v1_batch_packed(
            refs,
            bytes(__import__("base64").b64decode(trace["initial_exact_state_packed_b64"].encode("ascii"))),
        )
        self.assertTrue(runtime.world(0).run_exact_stage_direct("MissileGuidance"))
        packed_live = bytes(runtime.extract_exact_world_step_states_v1_batch_packed(refs))

        sig_exec = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_initial))
        sig_live = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_live))
        self.assertEqual(sig_exec, sig_live)

        digest_exec = _component_digest_map(packed_initial)
        digest_live = _component_digest_map(packed_live)
        for key in (
            "velocity",
            "missile.present",
            "missile",
            "contact_list_summary.present",
            "contact_list_summary",
        ):
            self.assertEqual(digest_exec.get(key), digest_live.get(key), key)


if __name__ == "__main__":
    unittest.main()
