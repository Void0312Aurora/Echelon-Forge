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

from tools.diagnostics.compare_exact_world_step_control_aero_slice import (  # noqa: E402
    compare_exact_world_step_control_aero_slice,
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
    runtime.reset_batch([29])
    runtime.set_time_step(0.05)
    return runtime


def _setup_control_aero_world():
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
    world.set_command(entity_id, 68.0, 240.0, 1325.0)
    world.set_command_lag(entity_id, 0.45, 0.60, 0.85)
    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.stick_roll = 0.35
    pilot.stick_pitch = -0.18
    pilot.rudder = 0.22
    pilot.throttle = 0.74
    pilot.gear_handle = 1.0
    world.set_pilot_action(entity_id, pilot)
    return runtime, _entity_ref(0, entity_id)


def _component_digest_map(packed: bytes) -> dict[str, int]:
    digests = list(ef_py.exact_world_step_state_v1_component_digests_packed(packed))
    if len(digests) != 1:
        raise AssertionError(f"expected one state digest, got {len(digests)}")
    return {str(key): int(value) for key, value in dict(digests[0]).items()}


class ExactWorldStepControlAeroSliceTests(unittest.TestCase):
    def test_control_aero_slice_matches_computeaerostate_stage_in_system_trace(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_control_aero_slice(trace, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["target_stage_name"], "ComputeAeroState")
        self.assertTrue(report["apply_signatures_match"])
        self.assertTrue(report["packed_component_digests_match"])
        self.assertEqual(int(report["mismatch_count"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(int(report["command_lane_state_count"]), 2)
        self.assertEqual(int(report["control_aero_state_count"]), 2)

    def test_control_aero_slice_matches_live_manual_pipeline(self) -> None:
        runtime_live, ref_live = _setup_control_aero_world()
        runtime_exec, ref_exec = _setup_control_aero_world()

        packed_initial = bytes(runtime_exec.extract_exact_world_step_states_v1_batch_packed([ref_exec]))
        packed_after_command = bytes(ef_py.step_exact_world_step_command_lane_reference_cpu_packed(packed_initial))
        packed_exec = bytes(ef_py.step_exact_world_step_control_aero_reference_cpu_packed(packed_after_command))

        live_world = runtime_live.world(0)
        live_world.begin_exact_stage_trace_frame()
        try:
            for stage_name in (
                "CommandLinkMovement",
                "CommandLinkAction",
                "CommandLinkMission",
                "ActionMapping",
                "CommandLag",
                "FlightControl",
                "ClearForces",
                "ComputeAeroState",
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
            "control_law_state.present",
            "control_law_state",
            "force_accumulator.present",
            "force_accumulator",
            "aero_state.present",
            "aero_state",
            "landing_gear.present",
            "landing_gear",
        ):
            self.assertEqual(digest_exec.get(key), digest_live.get(key), key)


if __name__ == "__main__":
    unittest.main()
