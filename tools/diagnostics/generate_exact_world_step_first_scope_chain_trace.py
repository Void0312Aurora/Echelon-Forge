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

from python.testing.runtime import ensure_repo_imports
from tools.diagnostics.generate_exact_world_step_missile_guidance_trace import (
    _packed_b64,
    generate_cpu_exact_world_step_missile_guidance_trace,
    spawn_runtime_from_guidance_trace,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import _record_step
from tools.diagnostics.generate_exact_world_step_system_trace import _traceable_inventory


ensure_repo_imports()

import ef_py  # noqa: E402


def generate_cpu_exact_world_step_first_scope_chain_trace(
    *,
    seed: int = 19,
    time_step_s: float = 0.05,
    database_path: str | None = None,
) -> dict[str, Any]:
    guidance_trace = generate_cpu_exact_world_step_missile_guidance_trace(
        seed=seed,
        time_step_s=time_step_s,
        database_path=database_path,
    )
    runtime, refs, entity_ids = spawn_runtime_from_guidance_trace(guidance_trace)
    initial_packed = base64.b64decode(guidance_trace["initial_exact_state_packed_b64"].encode("ascii"))
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, initial_packed)

    _, traceable_inventory = _traceable_inventory(runtime)
    stage_sequence = [str(stage["name"]) for stage in traceable_inventory]
    final_stage = traceable_inventory[-1]

    world = runtime.world(0)
    world.begin_exact_stage_trace_frame()
    try:
        for stage_name in stage_sequence:
            if not world.run_exact_stage_trace_stage(stage_name):
                raise RuntimeError(f"failed to run exact first-scope stage: {stage_name}")
    finally:
        world.end_exact_stage_trace_frame()

    final_record = _record_step(runtime, refs, entity_ids, int(final_stage["order"]))
    final_record["packed_exact_state_b64"] = _packed_b64(
        runtime.extract_exact_world_step_states_v1_batch_packed(refs)
    )

    return {
        "schema_version": 1,
        "trace_kind": "cpu_exact_first_scope_chain_trace_v1",
        "database_path": guidance_trace["database_path"],
        "seed": int(seed),
        "time_step_s": float(time_step_s),
        "world_setup": dict(guidance_trace["world_setup"]),
        "initial_exact_state_packed_b64": guidance_trace["initial_exact_state_packed_b64"],
        "initial_record": dict(guidance_trace["initial_record"]),
        "stage_sequence": stage_sequence,
        "final_stage_name": str(final_stage["name"]),
        "final_stage_order": int(final_stage["order"]),
        "final_stage_domain": str(final_stage["domain"]),
        "final_record": final_record,
    }


def write_cpu_exact_world_step_first_scope_chain_trace(output_path: str | Path, **kwargs: Any) -> Path:
    trace = generate_cpu_exact_world_step_first_scope_chain_trace(**kwargs)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a mixed aircraft+missile first-scope exact CPU chain trace."
    )
    parser.add_argument("--output", required=True, help="Path to the JSON trace artifact.")
    parser.add_argument("--seed", type=int, default=19, help="World reset seed.")
    parser.add_argument("--time-step", type=float, default=0.05, help="Simulation time step in seconds.")
    parser.add_argument("--database", help="Optional database path override.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_path = write_cpu_exact_world_step_first_scope_chain_trace(
        args.output,
        seed=int(args.seed),
        time_step_s=float(args.time_step),
        database_path=args.database,
    )
    print(
        json.dumps(
            {
                "output": str(output_path),
                "seed": int(args.seed),
                "time_step_s": float(args.time_step),
                "trace_kind": "cpu_exact_first_scope_chain_trace_v1",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
