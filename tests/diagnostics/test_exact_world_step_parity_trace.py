from __future__ import annotations

import base64
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics.generate_exact_world_step_parity_trace import (  # noqa: E402
    generate_cpu_exact_world_step_parity_trace,
)


class ExactWorldStepParityTraceTests(unittest.TestCase):
    def test_trace_generation_is_repeatable_for_fixed_seed_batch(self) -> None:
        trace_a = generate_cpu_exact_world_step_parity_trace(seeds=[11, 17], steps=6, time_step_s=0.05)
        trace_b = generate_cpu_exact_world_step_parity_trace(seeds=[11, 17], steps=6, time_step_s=0.05)

        replay_blob_a = base64.b64decode(trace_a.pop("initial_exact_state_packed_b64"))
        replay_blob_b = base64.b64decode(trace_b.pop("initial_exact_state_packed_b64"))

        self.assertEqual(trace_a, trace_b)
        self.assertEqual(trace_a["trace_kind"], "cpu_exact_world_step_parity_v1")
        self.assertEqual(trace_a["world_count"], 2)
        self.assertEqual(trace_a["steps"], 6)
        self.assertEqual(len(trace_a["step_records"]), 7)
        self.assertEqual(trace_a["initial_apply_signatures"], trace_a["step_records"][0]["apply_signatures"])

        self.assertGreater(len(replay_blob_a), 0)
        self.assertEqual(len(replay_blob_a), len(replay_blob_b))

        self.assertNotEqual(
            trace_a["step_records"][0]["apply_signatures"],
            trace_a["step_records"][-1]["apply_signatures"],
        )


if __name__ == "__main__":
    unittest.main()
