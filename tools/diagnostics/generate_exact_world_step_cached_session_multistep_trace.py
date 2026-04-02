from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports
from tools.diagnostics.benchmark_exact_world_step_first_scope_chain_cached_session import (
    _make_pilot_assignments,
    _make_runtime,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import _normalized_replay_blob_b64, _record_step
from tools.diagnostics.generate_exact_world_step_system_trace import _traceable_inventory

ensure_repo_imports()

import ef_py  # noqa: E402


def _record_stage(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
    record = _record_step(runtime, refs, entity_ids, step_index)
    record["packed_exact_state_b64"] = _normalized_replay_blob_b64(
        runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    )
    return record


def _serialize_pilot_assignments(assignments: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "world_index": int(item.world_index),
            "entity_id": int(item.entity_id),
            "stick_roll": float(item.action.stick_roll),
            "stick_pitch": float(item.action.stick_pitch),
            "rudder": float(item.action.rudder),
            "throttle": float(item.action.throttle),
            "active": bool(item.action.active),
        }
        for item in assignments
    ]


def generate_cpu_exact_world_step_cached_session_multistep_trace(
    *,
    steps: int = 8,
    seed: int = 101,
    time_step_s: float = 0.05,
    world_count: int = 1,
) -> dict[str, Any]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if world_count <= 0:
        raise ValueError("world_count must be positive")

    runtime, refs = _make_runtime(seed=seed, time_step_s=time_step_s, world_count=world_count)
    entity_ids = [int(ref.entity_id) for ref in refs]
    _, traceable_inventory = _traceable_inventory(runtime)
    stage_sequence = [str(stage["name"]) for stage in traceable_inventory]

    initial_record = _record_stage(runtime, refs, entity_ids, 0)
    initial_record["stage_name"] = "__initial__"
    initial_record["stage_order"] = -1
    initial_record["stage_domain"] = "initial"

    step_traces: list[dict[str, Any]] = []
    for step_index in range(steps):
        assignments = _make_pilot_assignments(refs, step_index)
        runtime.set_pilot_actions_batch(assignments)
        active_worlds = [runtime.world(world_index) for world_index in range(int(world_count))]

        stage_records: list[dict[str, Any]] = []
        for world in active_worlds:
            world.begin_exact_stage_trace_frame()
        try:
            step_initial = _record_stage(runtime, refs, entity_ids, step_index + 1)
            step_initial["stage_name"] = "__step_initial__"
            step_initial["stage_order"] = -1
            step_initial["stage_domain"] = "initial"
            stage_records.append(step_initial)

            for stage in traceable_inventory:
                stage_name = str(stage["name"])
                for world in active_worlds:
                    if not bool(world.run_exact_stage_trace_stage(stage_name)):
                        raise RuntimeError(f"failed to run exact stage trace stage: {stage_name}")
                record = _record_stage(runtime, refs, entity_ids, step_index + 1)
                record["stage_name"] = stage_name
                record["stage_order"] = int(stage["order"])
                record["stage_domain"] = str(stage["domain"])
                stage_records.append(record)
        finally:
            for world in reversed(active_worlds):
                world.end_exact_stage_trace_frame()

        step_traces.append(
            {
                "step_index": int(step_index + 1),
                "pilot_actions": _serialize_pilot_assignments(assignments),
                "stage_records": stage_records,
                "final_record": dict(stage_records[-1]),
            }
        )

    return {
        "schema_version": 1,
        "trace_kind": "cpu_exact_cached_session_multistep_trace_v1",
        "scenario_kind": "aircraft_cached_session_fixture_v1",
        "seed": int(seed),
        "steps": int(steps),
        "world_count": int(world_count),
        "time_step_s": float(time_step_s),
        "initial_record": initial_record,
        "traceable_stage_inventory": traceable_inventory,
        "stage_sequence": stage_sequence,
        "step_traces": step_traces,
        "final_stage_name": str(traceable_inventory[-1]["name"]) if traceable_inventory else "__initial__",
    }


def write_cpu_exact_world_step_cached_session_multistep_trace(output_path: str | Path, **kwargs: Any) -> Path:
    trace = generate_cpu_exact_world_step_cached_session_multistep_trace(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a fixed-seed multi-step exact CPU trace for the cached-session benchmark fixture."
        )
    )
    parser.add_argument("--output", required=True, help="Path to the JSON trace artifact.")
    parser.add_argument("--steps", type=int, default=8, help="Number of exact CPU steps to record.")
    parser.add_argument("--seed", type=int, default=101, help="World reset seed.")
    parser.add_argument("--world-count", type=int, default=1, help="Number of worlds / cached states to record.")
    parser.add_argument("--time-step", type=float, default=0.05, help="Simulation time step in seconds.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_path = write_cpu_exact_world_step_cached_session_multistep_trace(
        args.output,
        steps=int(args.steps),
        seed=int(args.seed),
        world_count=int(args.world_count),
        time_step_s=float(args.time_step),
    )
    print(
        json.dumps(
            {
                "trace_kind": "cpu_exact_cached_session_multistep_trace_v1",
                "output": str(output_path),
                "steps": int(args.steps),
                "world_count": int(args.world_count),
                "time_step_s": float(args.time_step),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
