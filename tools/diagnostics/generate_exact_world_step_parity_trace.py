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


def _entity_ref(world_index: int, entity_id: int) -> Any:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _normalized_replay_blob_b64(packed: bytes) -> str:
    state_size = int(ef_py.exact_world_step_state_v1_size_bytes())
    blob = bytearray(bytes(packed))
    for offset in range(0, len(blob), state_size):
        blob[offset:offset + 8] = b"\x00" * 8
    return base64.b64encode(bytes(blob)).decode("ascii")


def _serialize_truth(truth: Any, entity_slot: int) -> dict[str, Any]:
    return {
        "sim_time": float(truth.sim_time),
        "entity_slot": int(entity_slot),
        "x": float(truth.x),
        "y": float(truth.y),
        "z": float(truth.z),
        "vx": float(truth.vx),
        "vy": float(truth.vy),
        "vz": float(truth.vz),
        "heading": float(truth.heading),
        "pitch": float(truth.pitch),
        "roll": float(truth.roll),
        "speed": float(truth.speed),
        "health": float(truth.health),
        "missiles_remaining": int(truth.missiles_remaining),
        "can_fire": bool(truth.can_fire),
        "gear_state": float(truth.gear_state),
        "throttle": float(truth.throttle),
        "total_reward": float(truth.total_reward),
        "contact_count": int(len(truth.contacts)),
        "rwr_count": int(len(truth.rwr_warnings)),
    }


def _serialize_instrument(inst: Any) -> dict[str, Any]:
    return {
        "alt_baro_m": float(inst.alt_baro),
        "alt_radar_m": float(inst.alt_radar),
        "ias_mps": float(inst.ias),
        "mach": float(inst.mach),
        "vvi_mps": float(inst.vvi),
        "pitch_deg": float(inst.pitch),
        "roll_deg": float(inst.roll),
        "heading_deg": float(inst.heading),
        "aoa_deg": float(inst.aoa),
        "beta_deg": float(inst.beta),
        "g_load_normal": float(inst.g_load),
        "g_load_axial": float(inst.g_load_axial),
        "p_deg_s": float(inst.p),
        "q_deg_s": float(inst.q),
        "r_deg_s": float(inst.r),
        "engine_rpm_pct": float(inst.engine_rpm),
        "engine_temp_c": float(inst.engine_temp),
        "fuel_flow_kg_h": float(inst.fuel_flow),
        "throttle_pos": float(inst.throttle_pos),
        "fuel_internal_kg": float(inst.fuel_internal),
        "fuel_external_kg": float(inst.fuel_external),
        "gear_pos": float(inst.gear_pos),
        "flaps_pos": float(inst.flaps_pos),
        "speedbrake_pos": float(inst.speedbrake_pos),
        "master_arm": bool(inst.master_arm),
        "oat_c": float(inst.oat),
        "cmd_heading_deg": float(inst.cmd_heading),
        "cmd_alt_m": float(inst.cmd_alt),
        "cmd_speed_mps": float(inst.cmd_speed),
        "rwr_active": bool(inst.rwr_active),
        "missiles_remaining": int(inst.missiles_remaining),
        "lat_deg": float(inst.lat),
        "lon_deg": float(inst.lon),
        "vn_mps": float(inst.vn),
        "ve_mps": float(inst.ve),
        "vd_mps": float(inst.vd),
        "ground_speed_mps": float(inst.ground_speed),
        "ground_track_deg": float(inst.ground_track),
        "wind_speed_mps": float(inst.wind_speed),
        "wind_dir_deg": float(inst.wind_dir),
        "gps_available": bool(inst.gps_available),
        "position_uncertainty_m": float(inst.position_uncertainty),
        "gear_stress": float(inst.gear_stress),
        "gear_collapsed": bool(inst.gear_collapsed),
        "on_runway": bool(inst.on_runway),
    }


def _serialize_terminal(world: Any, entity_id: int, entity_slot: int, truth: Any, inst: Any) -> dict[str, Any]:
    return {
        "entity_slot": int(entity_slot),
        "active": bool(world.is_unit_active(int(entity_id))),
        "sim_time": float(truth.sim_time),
        "on_runway": bool(inst.on_runway),
        "gear_collapsed": bool(inst.gear_collapsed),
        "fuel_total_kg": float(inst.fuel_internal + inst.fuel_external),
        "altitude_agl_m": float(inst.alt_radar),
    }


def _default_spawn(world_index: int) -> dict[str, float | str]:
    return {
        "type_name": "F-16C_Block50",
        "x": -900.0 - 250.0 * float(world_index),
        "y": 160.0 * float(world_index),
        "z": 1100.0 + 80.0 * float(world_index),
        "heading": 50.0 + 12.0 * float(world_index),
        "pitch": 0.0,
        "roll": 0.0,
        "vx": 115.0 + 7.5 * float(world_index),
        "vy": 165.0 - 4.0 * float(world_index),
        "vz": 0.0,
    }


def _default_command(world_index: int) -> Any:
    cmd = ef_py.MissionCommand()
    cmd.command_code = 3 if world_index % 2 else 2
    cmd.cmd_heading_deg = 35.0 + 18.0 * float(world_index)
    cmd.cmd_altitude_m = 1450.0 + 120.0 * float(world_index)
    cmd.cmd_speed_mps = 215.0 + 6.0 * float(world_index)
    cmd.active = True
    return cmd


def _record_step(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
    truths = runtime.get_agent_observations_batch(refs)
    instruments = runtime.get_instrument_states_batch(refs)
    return {
        "step_index": int(step_index),
        "apply_signatures": [
            int(value)
            for value in runtime.extract_exact_world_step_state_v1_apply_signatures_batch(refs)
        ],
        "truth": [_serialize_truth(value, entity_slot) for entity_slot, value in enumerate(truths)],
        "instrument": [_serialize_instrument(value) for value in instruments],
        "hidden_dynamics": list(runtime.extract_exact_world_step_state_v1_hidden_surfaces_batch(refs)),
        "terminal": [
            _serialize_terminal(runtime.world(int(ref.world_index)), entity_id, entity_slot, truth, inst)
            for entity_slot, (ref, entity_id, truth, inst) in enumerate(zip(refs, entity_ids, truths, instruments))
        ],
    }


def generate_cpu_exact_world_step_parity_trace(
    *,
    seeds: list[int],
    steps: int,
    time_step_s: float = 0.05,
    database_path: str | None = None,
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("seeds must not be empty")
    if steps < 0:
        raise ValueError("steps must be non-negative")

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

    initial_packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    step_records = [_record_step(runtime, refs, entity_ids, 0)]
    for step_index in range(1, steps + 1):
        runtime.step_batch()
        step_records.append(_record_step(runtime, refs, entity_ids, step_index))

    return {
        "schema_version": 1,
        "trace_kind": "cpu_exact_world_step_parity_v1",
        "database_path": str(db_path),
        "world_count": len(seeds),
        "seeds": [int(seed) for seed in seeds],
        "steps": int(steps),
        "time_step_s": float(time_step_s),
        "world_setup": setup,
        "initial_exact_state_packed_b64": _normalized_replay_blob_b64(initial_packed),
        "initial_apply_signatures": step_records[0]["apply_signatures"],
        "step_records": step_records,
    }


def write_cpu_exact_world_step_parity_trace(output_path: str | Path, **kwargs: Any) -> Path:
    trace = generate_cpu_exact_world_step_parity_trace(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a CPU exact world-step parity trace.")
    parser.add_argument("--output", required=True, help="Path to the JSON trace artifact.")
    parser.add_argument("--steps", type=int, default=16, help="Number of exact CPU steps to record.")
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
    output_path = write_cpu_exact_world_step_parity_trace(
        args.output,
        seeds=seeds,
        steps=int(args.steps),
        time_step_s=float(args.time_step),
        database_path=str(args.database),
    )
    print(json.dumps({"output": str(output_path), "world_count": len(seeds), "steps": int(args.steps)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
