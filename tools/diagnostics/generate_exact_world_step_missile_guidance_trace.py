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
    _entity_ref,
    _serialize_instrument,
    _serialize_terminal,
    _serialize_truth,
)


def _serialize_detection(det: Any) -> dict[str, Any]:
    return {
        "target_id": int(det.target_id),
        "range": float(det.range),
        "bearing": float(det.bearing),
        "elevation": float(det.elevation),
        "closing_speed": float(det.closing_speed),
        "signal_strength": float(det.signal_strength),
        "timestamp": float(det.timestamp),
    }


def _deserialize_detection(payload: dict[str, Any]) -> Any:
    det = ef_py.Detection()
    det.target_id = int(payload["target_id"])
    det.range = float(payload["range"])
    det.bearing = float(payload["bearing"])
    det.elevation = float(payload["elevation"])
    det.closing_speed = float(payload["closing_speed"])
    det.signal_strength = float(payload["signal_strength"])
    det.timestamp = float(payload["timestamp"])
    return det


def _packed_b64(packed: bytes) -> str:
    return base64.b64encode(bytes(packed)).decode("ascii")


def _record_guidance_step(runtime: Any, refs: list[Any], entity_ids: list[int], step_index: int) -> dict[str, Any]:
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
            _serialize_terminal(
                runtime.world(int(ref.world_index)),
                entity_id,
                entity_slot,
                truth,
                inst,
            )
            for entity_slot, (ref, entity_id, truth, inst) in enumerate(zip(refs, entity_ids, truths, instruments))
        ],
    }


def _default_attacker_spawn() -> dict[str, float | str]:
    return {
        "type_name": "F-16C_Block50",
        "x": 0.0,
        "y": 0.0,
        "z": 1200.0,
        "heading": 18.0,
        "pitch": 0.0,
        "roll": 0.0,
        "vx": 175.0,
        "vy": 55.0,
        "vz": 0.0,
    }


def _default_target_spawn() -> dict[str, float | str]:
    return {
        "type_name": "F-16C_Block50",
        "x": 6200.0,
        "y": 900.0,
        "z": 1250.0,
        "heading": 210.0,
        "pitch": 0.0,
        "roll": 0.0,
        "vx": -140.0,
        "vy": -20.0,
        "vz": 0.0,
    }


def _spawn_entity(world: Any, side: Any, spawn: dict[str, Any]) -> int:
    return int(world.spawn_unit(
        side,
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


def _bearing_relative_deg(observer_heading_deg: float, dx: float, dy: float) -> float:
    los_nav_deg = (90.0 - (180.0 / 3.14159265358979323846) * __import__("math").atan2(dy, dx)) % 360.0
    rel = los_nav_deg - observer_heading_deg
    while rel > 180.0:
        rel -= 360.0
    while rel < -180.0:
        rel += 360.0
    return rel


def _make_detection(world: Any, observer_id: int, target_id: int, *, signal_strength: float) -> Any:
    obs = world.get_agent_observation(observer_id)
    tgt = world.get_agent_observation(target_id)
    obs_pos = (float(obs.x), float(obs.y), float(obs.z))
    obs_vel = (float(obs.vx), float(obs.vy), float(obs.vz))
    obs_hdg = float(obs.heading)
    tgt_pos = (float(tgt.x), float(tgt.y), float(tgt.z))
    tgt_vel = (float(tgt.vx), float(tgt.vy), float(tgt.vz))
    dx = float(tgt_pos[0]) - float(obs_pos[0])
    dy = float(tgt_pos[1]) - float(obs_pos[1])
    dz = float(tgt_pos[2]) - float(obs_pos[2])
    import math

    range_m = math.sqrt(dx * dx + dy * dy + dz * dz)
    horiz = math.sqrt(dx * dx + dy * dy)
    det = ef_py.Detection()
    det.target_id = int(target_id)
    det.range = float(range_m)
    det.bearing = float(_bearing_relative_deg(obs_hdg, dx, dy))
    det.elevation = float(math.degrees(math.atan2(dz, max(horiz, 1.0e-6))))
    rvx = float(tgt_vel[0]) - float(obs_vel[0])
    rvy = float(tgt_vel[1]) - float(obs_vel[1])
    rvz = float(tgt_vel[2]) - float(obs_vel[2])
    det.closing_speed = float(-(dx * rvx + dy * rvy + dz * rvz) / max(range_m, 1.0e-6))
    det.signal_strength = float(signal_strength)
    det.timestamp = 0.0
    return det


def generate_cpu_exact_world_step_missile_guidance_trace(
    *,
    seed: int = 19,
    time_step_s: float = 0.05,
    database_path: str | None = None,
) -> dict[str, Any]:
    db_path = database_path or resolve_repo_path("examples", "config", "database")
    runtime = ef_py.WorldBatchRuntime(1)
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch([int(seed)])
    runtime.set_time_step(float(time_step_s))
    world = runtime.world(0)

    attacker_spawn = _default_attacker_spawn()
    target_spawn = _default_target_spawn()
    attacker_id = _spawn_entity(world, ef_py.Side.Blue, attacker_spawn)
    target_id = _spawn_entity(world, ef_py.Side.Red, target_spawn)

    attacker_det = _make_detection(world, attacker_id, target_id, signal_strength=1500.0)
    world.set_contact_list(attacker_id, [attacker_det])
    missile_id = int(world.fire_missile(attacker_id, target_id))
    if missile_id == 0:
        raise RuntimeError("failed to fire missile for guidance trace setup")

    missile_det = _make_detection(world, missile_id, target_id, signal_strength=1800.0)
    world.set_contact_list(missile_id, [missile_det])
    world.restore_exact_replay_world_time(float(time_step_s))

    refs = [_entity_ref(0, missile_id), _entity_ref(0, target_id)]
    entity_ids = [missile_id, target_id]
    initial_packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    initial_record = _record_guidance_step(runtime, refs, entity_ids, 0)

    if not world.run_exact_stage_direct("MissileGuidance"):
        raise RuntimeError("failed to run MissileGuidance directly")

    guidance_record = _record_guidance_step(runtime, refs, entity_ids, 1)
    guidance_record["packed_exact_state_b64"] = _packed_b64(
        runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    )

    return {
        "schema_version": 1,
        "trace_kind": "cpu_exact_missile_guidance_trace_v1",
        "database_path": str(db_path),
        "seed": int(seed),
        "time_step_s": float(time_step_s),
        "world_setup": {
            "attacker_spawn": attacker_spawn,
            "target_spawn": target_spawn,
            "attacker_detection": _serialize_detection(attacker_det),
            "missile_detection": _serialize_detection(missile_det),
        },
        "initial_exact_state_packed_b64": _packed_b64(initial_packed),
        "initial_record": initial_record,
        "guidance_record": guidance_record,
    }


def spawn_runtime_from_guidance_trace(trace: dict[str, Any]) -> tuple[Any, list[Any], list[int]]:
    db_path = str(trace.get("database_path") or resolve_repo_path("examples", "config", "database"))
    runtime = ef_py.WorldBatchRuntime(1)
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch([int(trace.get("seed", 19))])
    runtime.set_time_step(float(trace.get("time_step_s", 0.05)))
    world = runtime.world(0)
    world_setup = dict(trace["world_setup"])
    attacker_id = _spawn_entity(world, ef_py.Side.Blue, dict(world_setup["attacker_spawn"]))
    target_id = _spawn_entity(world, ef_py.Side.Red, dict(world_setup["target_spawn"]))
    world.set_contact_list(attacker_id, [_deserialize_detection(dict(world_setup["attacker_detection"]))])
    missile_id = int(world.fire_missile(attacker_id, target_id))
    if missile_id == 0:
        raise RuntimeError("failed to fire missile while replaying guidance trace")
    world.set_contact_list(missile_id, [_deserialize_detection(dict(world_setup["missile_detection"]))])
    refs = [_entity_ref(0, missile_id), _entity_ref(0, target_id)]
    return runtime, refs, [missile_id, target_id]


def write_cpu_exact_world_step_missile_guidance_trace(output_path: str | Path, **kwargs: Any) -> Path:
    trace = generate_cpu_exact_world_step_missile_guidance_trace(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a CPU exact missile-guidance trace artifact.")
    parser.add_argument("--output", required=True, help="Path to the JSON trace artifact.")
    parser.add_argument("--seed", type=int, default=19, help="World reset seed.")
    parser.add_argument("--time-step", type=float, default=0.05, help="Simulation time step in seconds.")
    parser.add_argument(
        "--database",
        default=resolve_repo_path("examples", "config", "database"),
        help="Unit definition database path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_path = write_cpu_exact_world_step_missile_guidance_trace(
        args.output,
        seed=int(args.seed),
        time_step_s=float(args.time_step),
        database_path=str(args.database),
    )
    print(
        json.dumps(
            {
                "trace_kind": "cpu_exact_missile_guidance_trace_v1",
                "output": str(output_path),
                "seed": int(args.seed),
                "time_step_s": float(args.time_step),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
