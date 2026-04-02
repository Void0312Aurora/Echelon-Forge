from __future__ import annotations

import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports, resolve_repo_path  # noqa: E402

ensure_repo_imports()

import ef_py  # noqa: E402

from tools.diagnostics.compare_exact_world_step_command_lane_slice import (  # noqa: E402
    compare_exact_world_step_command_lane_slice,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (  # noqa: E402
    _default_spawn,
)
from tools.diagnostics.generate_exact_world_step_system_trace import (  # noqa: E402
    generate_cpu_exact_world_step_system_trace,
)


def _entity_ref(world_index: int, entity_id: int):
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _single_world_runtime():
    db_path = resolve_repo_path("examples", "config", "database")
    runtime = ef_py.WorldBatchRuntime(1)
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch([23])
    runtime.set_time_step(0.05)
    return runtime


def _setup_command_lane_world():
    runtime = _single_world_runtime()
    world = runtime.world(0)
    spawn = _default_spawn(0)
    entity_id = int(world.spawn_unit(
        ef_py.Side.Blue,
        str(spawn["type_name"]),
        float(spawn["x"]),
        float(spawn["y"]),
        float(spawn["z"]),
        float(spawn["heading"]),
        float(spawn["pitch"]),
        float(spawn["roll"]),
        float(spawn["vx"]),
        float(spawn["vy"]),
        float(spawn["vz"]),
    ))
    world.set_command(entity_id, 72.0, 228.0, 1380.0)
    world.set_action(entity_id, 0.55, -0.35, 0.25, 0.0, False, False, False)
    world.set_action_space_config(entity_id, 16.0, 8.0, 32.0, 160.0, 320.0, 500.0, 3200.0)
    world.set_command_lag(entity_id, 0.45, 0.70, 0.90)
    return runtime, _entity_ref(0, entity_id)


def _component_digest_map(packed: bytes) -> dict[str, int]:
    digests = list(ef_py.exact_world_step_state_v1_component_digests_packed(packed))
    if len(digests) != 1:
        raise AssertionError(f"expected one state digest, got {len(digests)}")
    return {str(key): int(value) for key, value in dict(digests[0]).items()}


class ExactWorldStepCommandLaneSliceTests(unittest.TestCase):
    def test_command_lane_slice_matches_commandlag_stage_in_system_trace(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_command_lane_slice(trace, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["target_stage_name"], "CommandLag")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["command_lane_state_count"]), 2)

    def test_command_lane_slice_matches_live_manual_pipeline_for_action_mapping_and_lag(self) -> None:
        runtime_live, ref_live = _setup_command_lane_world()
        runtime_exec, ref_exec = _setup_command_lane_world()

        packed_initial = bytes(runtime_exec.extract_exact_world_step_states_v1_batch_packed([ref_exec]))
        packed_exec = bytes(ef_py.step_exact_world_step_command_lane_reference_cpu_packed(packed_initial))

        live_world = runtime_live.world(0)
        live_world.begin_exact_stage_trace_frame()
        try:
            for stage_name in (
                "CommandLinkMovement",
                "CommandLinkAction",
                "CommandLinkMission",
                "ActionMapping",
                "CommandLag",
            ):
                self.assertTrue(live_world.run_exact_stage_trace_stage(stage_name))
        finally:
            live_world.end_exact_stage_trace_frame()

        packed_live = bytes(runtime_live.extract_exact_world_step_states_v1_batch_packed([ref_live]))
        sig_exec = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_exec))
        sig_live = list(ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_live))
        self.assertEqual(sig_exec, sig_live)

        digest_exec = _component_digest_map(packed_exec)
        digest_live = _component_digest_map(packed_live)
        for key in (
            "movement_command.present",
            "movement_command",
            "action_command.present",
            "action_command",
            "command_lag.present",
            "command_lag",
            "lagged_command.present",
            "lagged_command",
        ):
            self.assertEqual(digest_exec.get(key), digest_live.get(key), key)


if __name__ == "__main__":
    unittest.main()
