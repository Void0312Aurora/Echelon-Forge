from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402

from tools.diagnostics.generate_exact_world_step_parity_trace import (  # noqa: E402
    _default_command,
    _default_spawn,
    _entity_ref,
    _normalized_replay_blob_b64,
    _record_step,
)


def _traceable_inventory(runtime: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory = list(runtime.world(0).exact_gpu_migration_stage_inventory())
    traceable = [
        stage for stage in inventory
        if bool(stage["gpu_migration_scope"]) and bool(stage["manual_trace_supported"])
    ]
    return inventory, traceable


def _stage_contract_inventory(runtime: Any) -> list[dict[str, Any]]:
    return list(runtime.world(0).exact_gpu_migration_stage_contract_inventory())


def _record_stage(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
    record = _record_step(runtime, refs, entity_ids, step_index)
    record["packed_exact_state_b64"] = _normalized_replay_blob_b64(
        runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    )
    return record


def generate_cpu_exact_world_step_system_trace(
    *,
    seeds: list[int],
    time_step_s: float = 0.05,
    database_path: str | None = None,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("seeds must not be empty")

    db_path = database_path or resolve_repo_path("examples", "config", "database")
    runtime = ef_py.WorldBatchRuntime(len(seeds))
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch([int(seed) for seed in seeds])
    runtime.set_time_step(float(time_step_s))

    refs: list[Any] = []
    entity_ids: list[int] = []
    setup: list[dict[str, Any]] = []
    for world_index, seed in enumerate(seeds):
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
        cmd = _default_command(world_index)
        world.set_mission_command(entity_id, cmd)
        refs.append(_entity_ref(world_index, entity_id))
        entity_ids.append(entity_id)
        setup.append(
            {
                "world_index": int(world_index),
                "seed": int(seed),
                "entity_slot": int(world_index),
                "spawn": spawn,
                "mission_command": {
                    "command_code": int(cmd.command_code),
                    "cmd_heading_deg": float(cmd.cmd_heading_deg),
                    "cmd_altitude_m": float(cmd.cmd_altitude_m),
                    "cmd_speed_mps": float(cmd.cmd_speed_mps),
                    "active": bool(cmd.active),
                },
            }
        )

    inventory, traceable_inventory = _traceable_inventory(runtime)
    contract_inventory = _stage_contract_inventory(runtime)
    initial_packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    stage_records: list[dict[str, Any]] = []
    initial_record = _record_stage(runtime, refs, entity_ids, 0)
    initial_record["stage_name"] = "__initial__"
    initial_record["stage_order"] = -1
    initial_record["stage_domain"] = "initial"
    stage_records.append(initial_record)

    active_worlds: list[Any] = []
    try:
        for world_index in range(len(seeds)):
            world = runtime.world(world_index)
            world.begin_exact_stage_trace_frame()
            active_worlds.append(world)

        for stage in traceable_inventory:
            stage_name = str(stage["name"])
            for world in active_worlds:
                ok = bool(world.run_exact_stage_trace_stage(stage_name))
                if not ok:
                    raise RuntimeError(f"failed to run exact stage trace stage: {stage_name}")
            record = _record_stage(runtime, refs, entity_ids, int(stage["order"]))
            record["stage_name"] = stage_name
            record["stage_order"] = int(stage["order"])
            record["stage_domain"] = str(stage["domain"])
            stage_records.append(record)
    finally:
        for world in reversed(active_worlds):
            try:
                world.end_exact_stage_trace_frame()
            except Exception:
                pass

    return {
        "schema_version": 1,
        "trace_kind": "cpu_exact_system_stage_trace_v1",
        "database_path": str(db_path),
        "world_count": len(seeds),
        "seeds": [int(seed) for seed in seeds],
        "time_step_s": float(time_step_s),
        "world_setup": setup,
        "initial_exact_state_packed_b64": _normalized_replay_blob_b64(initial_packed),
        "stage_inventory": inventory,
        "stage_contract_inventory": contract_inventory,
        "traceable_stage_inventory": traceable_inventory,
        "stage_records": stage_records,
        "final_stage_name": str(traceable_inventory[-1]["name"]) if traceable_inventory else "__initial__",
    }


def write_cpu_exact_world_step_system_trace(output_path: str | Path, **kwargs: Any) -> Path:
    trace = generate_cpu_exact_world_step_system_trace(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a per-system CPU exact-step trace for the current manual GPU-migration stage inventory."
    )
    parser.add_argument("--output", required=True, help="Path to the JSON trace artifact.")
    parser.add_argument(
        "--seeds",
        default="11,17",
        help="Comma-separated per-world seeds for the replay batch.",
    )
    parser.add_argument(
        "--time-step",
        type=float,
        default=0.05,
        help="Simulation time step in seconds.",
    )
    parser.add_argument(
        "--database",
        default=resolve_repo_path("examples", "config", "database"),
        help="Unit definition database path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    seeds = [int(token.strip()) for token in str(args.seeds).split(",") if token.strip()]
    output_path = write_cpu_exact_world_step_system_trace(
        args.output,
        seeds=seeds,
        time_step_s=float(args.time_step),
        database_path=str(args.database),
    )
    summary = {
        "trace_kind": "cpu_exact_system_stage_trace_v1",
        "output": str(output_path),
        "world_count": len(seeds),
        "time_step_s": float(args.time_step),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
