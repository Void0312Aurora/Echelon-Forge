#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path
from tools.diagnostics.common import write_json_output

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

import ef_py  # noqa: E402

from python.scenario_compiler import ScenarioCompiler  # noqa: E402
from python.scenario_compiler import _clone_runtime_mission_command  # noqa: E402
from python.scenario.diagnostics.runtime_setup import apply_world_layouts_to_batch_diagnostics  # noqa: E402
from python.scenario.runtime import (  # noqa: E402
    BatchWorldApplyBuffer,
    apply_world_layout_to_kernel,
    build_compiled_world_layout,
    prepare_scenario_world_layout,
)
from python.rl.runtime.world_batch.command_chain_cache import (  # noqa: E402
    project_world_mission_command_maintained_assignment,
)


def _build_loop_worlds(world_count: int):
    worlds: list[ef_py.SimulationKernel] = []
    db_path = resolve_repo_path("examples", "config", "database")
    for _ in range(int(world_count)):
        sim = ef_py.SimulationKernel()
        sim.load_database(db_path)
        worlds.append(sim)
    return worlds


def _build_batch_world(world_count: int, *, worker_threads: int | None):
    batch = ef_py.WorldBatchRuntime(int(world_count))
    if worker_threads is not None:
        batch.set_worker_threads(max(0, int(worker_threads)))
    db_path = resolve_repo_path("examples", "config", "database")
    batch.load_database(db_path)
    return batch


def _time_call(fn, *, iters: int) -> float:
    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        fn()
    elapsed = time.perf_counter() - start
    return 1000.0 * elapsed / max(1, int(iters))


def _build_refs(applied_worlds):
    refs = []
    for world_index, applied in enumerate(applied_worlds):
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(world_index)
        ref.entity_id = int(applied.agent_id)
        refs.append(ref)
    return refs


def _build_command_payloads(applied_worlds):
    command_shells = []
    maintained_assignments = []
    for world_index, applied in enumerate(applied_worlds):
        cmd = ef_py.MissionCommand()
        cmd.command_code = 2
        cmd.cmd_heading_deg = 90.0
        cmd.cmd_altitude_m = 600.0 + 5.0 * world_index
        cmd.cmd_speed_mps = 120.0 + 1.0 * world_index
        cmd.active = True
        command_shells.append(cmd)
        assignment = ef_py.WorldMissionCommandMaintainedAssignment()
        project_world_mission_command_maintained_assignment(
            assignment,
            world_index=int(world_index),
            entity_id=int(applied.agent_id),
            compatibility_mission_command_shell=cmd,
        )
        maintained_assignments.append(assignment)
    return command_shells, maintained_assignments


def _build_legacy_layout(compiled, *, seed: int):
    scenario_data = compiled.instantiate_runtime()
    runtime_metadata = getattr(compiled, "runtime_metadata", None)
    if runtime_metadata is not None:
        scenario_data["mission_command"] = _clone_runtime_mission_command(runtime_metadata.mission_command_template)
    rng = np.random.RandomState(int(seed) & 0xFFFFFFFF)
    return prepare_scenario_world_layout(
        scenario_data,
        seed=int(seed),
        rng=rng,
        compiled_template=None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 4 world batch runtime benchmark.")
    parser.add_argument("--world-count", type=int, default=8, help="Number of worlds to include in the benchmark.")
    parser.add_argument("--iters", type=int, default=2000, help="Iterations per timing bucket for step/read path.")
    parser.add_argument("--setup-iters", type=int, default=250, help="Iterations per timing bucket for scenario apply path.")
    parser.add_argument(
        "--world-batch-threads",
        type=int,
        default=None,
        help="Configured worker threads for WorldBatchRuntime. Omit to keep the default (1); set 0 for auto mode.",
    )
    parser.add_argument(
        "--scenario",
        default="scenarios/combined/takeoff_to_landing_continuous_train_v1.json",
        help="Scenario path used to prepare compiled world layouts.",
    )
    parser.add_argument(
        "--sim-log-level",
        default="warn",
        help="Simulation log level for the benchmark process (for example: trace, debug, info, warn, error).",
    )
    parser.add_argument("--json-out", default="", help="Optional path to write JSON results.")
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        scenario_path = resolve_repo_path(args.scenario)
    compiled = ScenarioCompiler.compile_path(scenario_path)
    seeds = [100 + idx for idx in range(int(args.world_count))]

    def _legacy_layout_build_path() -> None:
        for seed in seeds:
            _ = _build_legacy_layout(compiled, seed=int(seed))

    def _compiled_layout_build_path() -> None:
        for seed in seeds:
            _ = build_compiled_world_layout(compiled, seed=int(seed), use_compiled_template=True)

    legacy_layout_build_ms = _time_call(_legacy_layout_build_path, iters=int(args.setup_iters))
    compiled_layout_build_ms = _time_call(_compiled_layout_build_path, iters=int(args.setup_iters))
    layouts = [
        build_compiled_world_layout(compiled, seed=seed)
        for seed in seeds
    ]

    loop_worlds = _build_loop_worlds(int(args.world_count))
    batch = _build_batch_world(int(args.world_count), worker_threads=args.world_batch_threads)
    apply_buffer = BatchWorldApplyBuffer(int(args.world_count))

    def _loop_setup_path() -> None:
        for sim, layout in zip(loop_worlds, layouts):
            apply_world_layout_to_kernel(sim, layout)

    def _batch_setup_path() -> None:
        _ = apply_world_layouts_to_batch_diagnostics(batch, layouts, apply_buffer=apply_buffer)

    loop_setup_ms = _time_call(_loop_setup_path, iters=int(args.setup_iters))
    batch_setup_ms = _time_call(_batch_setup_path, iters=int(args.setup_iters))

    loop_applied = [apply_world_layout_to_kernel(sim, layout) for sim, layout in zip(loop_worlds, layouts)]
    batch_applied = apply_world_layouts_to_batch_diagnostics(
        batch,
        layouts,
        apply_buffer=apply_buffer,
    )
    refs = _build_refs(batch_applied)
    command_shells, maintained_assignments = _build_command_payloads(batch_applied)

    def _loop_path() -> None:
        for applied, command, sim in zip(loop_applied, command_shells, loop_worlds):
            sim.set_mission_command(int(applied.agent_id), command)
        for sim in loop_worlds:
            sim.step()
        for applied, sim in zip(loop_applied, loop_worlds):
            _ = sim.get_agent_observation(int(applied.agent_id))
            _ = sim.get_instrument_state(int(applied.agent_id))

    def _batch_path() -> None:
        batch.set_mission_commands_maintained_batch(maintained_assignments)
        batch.step_batch()
        _ = batch.get_agent_observations_batch(refs)
        _ = batch.get_instrument_states_batch(refs)

    loop_ms = _time_call(_loop_path, iters=int(args.iters))
    batch_ms = _time_call(_batch_path, iters=int(args.iters))
    sample_obs = batch.get_agent_observations_batch(refs)

    results = {
        "scenario": scenario_path,
        "world_count": int(args.world_count),
        "configured_world_batch_threads": (
            None if args.world_batch_threads is None else int(args.world_batch_threads)
        ),
        "effective_world_batch_threads": int(batch.effective_worker_threads()),
        "sim_log_level": str(args.sim_log_level),
        "reuse_apply_buffer": True,
        "iters": int(args.iters),
        "setup_iters": int(args.setup_iters),
        "legacy_layout_build_ms": float(legacy_layout_build_ms),
        "compiled_layout_build_ms": float(compiled_layout_build_ms),
        "layout_build_speedup": float(legacy_layout_build_ms / max(compiled_layout_build_ms, 1.0e-12)),
        "legacy_kernel_apply_ms": float(loop_setup_ms),
        "world_batch_kernel_apply_ms": float(batch_setup_ms),
        "kernel_apply_speedup": float(loop_setup_ms / max(batch_setup_ms, 1.0e-12)),
        "legacy_python_loop_ms": float(loop_ms),
        "world_batch_runtime_ms": float(batch_ms),
        "step_read_speedup": float(loop_ms / max(batch_ms, 1.0e-12)),
        "sample_obs_count": len(sample_obs),
        "sample_first_world_time": float(sample_obs[0].sim_time if sample_obs else 0.0),
    }

    print("World Batch Runtime Phase 4 Benchmark")
    print("=" * 39)
    print(f"scenario                 : {results['scenario']}")
    print(f"world count              : {results['world_count']}")
    print(f"configured threads       : {results['configured_world_batch_threads']}")
    print(f"effective threads        : {results['effective_world_batch_threads']}")
    print(f"legacy layout build      : {results['legacy_layout_build_ms']:.6f} ms")
    print(f"compiled layout build    : {results['compiled_layout_build_ms']:.6f} ms")
    print(f"layout build speedup     : {results['layout_build_speedup']:.2f}x")
    print(f"legacy kernel apply      : {results['legacy_kernel_apply_ms']:.6f} ms")
    print(f"world batch kernel apply : {results['world_batch_kernel_apply_ms']:.6f} ms")
    print(f"kernel apply speedup     : {results['kernel_apply_speedup']:.2f}x")
    print(f"legacy python loop       : {results['legacy_python_loop_ms']:.6f} ms")
    print(f"world batch runtime      : {results['world_batch_runtime_ms']:.6f} ms")
    print(f"step/read speedup        : {results['step_read_speedup']:.2f}x")

    write_json_output(str(args.json_out), results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
