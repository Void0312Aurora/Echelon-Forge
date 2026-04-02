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

from tools.diagnostics.compare_exact_world_step_system_trace import (  # noqa: E402
    compare_exact_world_step_system_trace,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (  # noqa: E402
    _default_command,
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


def _make_runtime_pair():
    db_path = resolve_repo_path("examples", "config", "database")
    runtime_a = ef_py.WorldBatchRuntime(2)
    runtime_b = ef_py.WorldBatchRuntime(2)
    for runtime in (runtime_a, runtime_b):
        if not runtime.load_database(db_path):
            raise RuntimeError(f"failed to load database from {db_path}")
        runtime.reset_batch([11, 17])
        runtime.set_time_step(0.05)
    return runtime_a, runtime_b


def _populate_runtime(runtime):
    refs = []
    for world_index in range(2):
        world = runtime.world(world_index)
        spawn = _default_spawn(world_index)
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
        world.set_mission_command(entity_id, _default_command(world_index))
        refs.append(_entity_ref(world_index, entity_id))
    return refs


class ExactWorldStepSystemTraceTests(unittest.TestCase):
    def test_stage_inventory_exposes_manual_gpu_scope_order(self) -> None:
        kernel = ef_py.SimulationKernel()
        inventory = list(kernel.exact_gpu_migration_stage_inventory())
        contracts = list(kernel.exact_gpu_migration_stage_contract_inventory())
        names = [str(item["name"]) for item in inventory]

        self.assertIn("FlightControl", names)
        self.assertIn("ComputeAerodynamics", names)
        self.assertIn("UpdateInstruments", names)

        manual_gpu_scope = [
            str(item["name"])
            for item in inventory
            if bool(item["gpu_migration_scope"]) and bool(item["manual_trace_supported"])
        ]
        self.assertEqual(
            manual_gpu_scope,
            [
                "CommandLinkMovement",
                "CommandLinkAction",
                "CommandLinkMission",
                "ActionMapping",
                "CommandLag",
                "FlightControl",
                "ClearForces",
                "ComputeAeroState",
                "ComputeForces",
                "ComputeAerodynamics",
                "GroundContact",
                "RotationalIntegrate",
                "MissileGuidance",
                "LeapfrogIntegrate",
                "NavigationSystem",
                "UpdateInstruments",
                "FuelConsumption",
                "MassUpdate",
            ],
        )

        self.assertEqual(
            [str(item["name"]) for item in contracts],
            manual_gpu_scope,
        )

        flight_control = next(item for item in contracts if str(item["name"]) == "FlightControl")
        self.assertIn("ForceAccumulator", [str(value) for value in flight_control["writes"]])
        self.assertIn("ControlLawState", [str(value) for value in flight_control["writes"]])
        self.assertIn("CommandLag", [str(value) for value in flight_control["depends_on_stages"]])

        update_instruments = next(item for item in contracts if str(item["name"]) == "UpdateInstruments")
        self.assertIn("InstrumentState", [str(value) for value in update_instruments["writes"]])
        self.assertIn("instrument", [str(value) for value in update_instruments["trace_surfaces"]])

        mass_update = next(item for item in contracts if str(item["name"]) == "MassUpdate")
        self.assertIn("FuelSystem", [str(value) for value in mass_update["reads"]])
        self.assertIn("MassProperties", [str(value) for value in mass_update["writes"]])

    def test_manual_traceable_pipeline_matches_full_step_exact_state(self) -> None:
        runtime_manual, runtime_full = _make_runtime_pair()
        refs_manual = _populate_runtime(runtime_manual)
        refs_full = _populate_runtime(runtime_full)

        for world_index in range(2):
            runtime_manual.world(world_index).step_exact_stage_traceable_pipeline()
        runtime_full.step_batch()

        manual_signatures = list(runtime_manual.extract_exact_world_step_state_v1_apply_signatures_batch(refs_manual))
        full_signatures = list(runtime_full.extract_exact_world_step_state_v1_apply_signatures_batch(refs_full))
        self.assertEqual(manual_signatures, full_signatures)

        manual_hidden = list(runtime_manual.extract_exact_world_step_state_v1_hidden_surfaces_batch(refs_manual))
        full_hidden = list(runtime_full.extract_exact_world_step_state_v1_hidden_surfaces_batch(refs_full))
        self.assertEqual(manual_hidden, full_hidden)

        manual_instruments = list(runtime_manual.get_instrument_states_batch(refs_manual))
        full_instruments = list(runtime_full.get_instrument_states_batch(refs_full))
        self.assertEqual(
            [(float(v.pitch), float(v.roll), float(v.heading), float(v.aoa), float(v.beta)) for v in manual_instruments],
            [(float(v.pitch), float(v.roll), float(v.heading), float(v.aoa), float(v.beta)) for v in full_instruments],
        )

    def test_system_trace_generator_records_stage_sequence(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        self.assertEqual(trace["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(trace["world_count"], 2)
        self.assertEqual(trace["stage_records"][0]["stage_name"], "__initial__")
        self.assertIn("packed_exact_state_b64", trace["stage_records"][0])
        self.assertEqual(len(trace["stage_contract_inventory"]), len(trace["traceable_stage_inventory"]))
        self.assertEqual(trace["final_stage_name"], "MassUpdate")
        self.assertEqual(trace["stage_records"][-1]["stage_name"], "MassUpdate")
        self.assertEqual(
            [record["stage_name"] for record in trace["stage_records"][1:]],
            [stage["name"] for stage in trace["traceable_stage_inventory"]],
        )

    def test_system_trace_comparator_matches_every_stage(self) -> None:
        trace = generate_cpu_exact_world_step_system_trace(seeds=[11, 17], time_step_s=0.05)
        report = compare_exact_world_step_system_trace(trace, abs_tol=1e-6, max_examples=4)

        self.assertEqual(report["trace_kind"], "cpu_exact_system_stage_trace_v1")
        self.assertEqual(report["traceable_stage_count"], len(trace["traceable_stage_inventory"]))
        self.assertEqual(len(report["stage_contract_inventory"]), len(trace["stage_contract_inventory"]))
        self.assertTrue(report["all_apply_signatures_match"])
        self.assertTrue(report["all_packed_component_digests_match"])
        self.assertEqual(int(report["total_mismatches"]), 0)
        self.assertAlmostEqual(float(report["max_abs_diff"]), 0.0, places=9)
        self.assertEqual(report["records"][0]["stage_name"], "__initial__")
        self.assertEqual(report["records"][-1]["stage_name"], "MassUpdate")
        self.assertEqual(report["records"][-1]["differing_components"], [])


if __name__ == "__main__":
    unittest.main()
