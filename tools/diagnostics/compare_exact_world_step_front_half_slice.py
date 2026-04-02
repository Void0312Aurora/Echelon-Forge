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
from tools.diagnostics.compare_exact_world_step_force_ground_slice import (
    _decode_record_packed,
    _strip_runtime_clock_fields,
)
from tools.diagnostics.compare_exact_world_step_shadow_trace import (
    _compare_records,
    _load_trace,
    _record_runtime_surface,
    _spawn_runtime_from_trace,
)
from tools.diagnostics.compare_exact_world_step_system_trace import (
    _component_digests_match,
    _differing_components,
    _packed_component_digests,
)
from tools.diagnostics.generate_exact_world_step_parity_trace import (
    _normalized_replay_blob_b64,
)


ensure_repo_imports()

import ef_py  # noqa: E402


def compare_exact_world_step_front_half_slice(
    trace: str | Path | dict[str, Any],
    *,
    use_gpu: bool = True,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_system_stage_trace_v1":
        raise ValueError(
            "compare_exact_world_step_front_half_slice expects trace_kind=cpu_exact_system_stage_trace_v1"
        )

    stage_records = list(loaded.get("stage_records", []))
    target_record = next((record for record in stage_records if record.get("stage_name") == "GroundContact"), None)
    if target_record is None:
        raise ValueError("system trace does not contain a GroundContact stage record")

    initial_payload = loaded.get("initial_exact_state_packed_b64")
    if not isinstance(initial_payload, str) or not initial_payload:
        raise ValueError("trace is missing initial_exact_state_packed_b64")
    initial_packed = base64.b64decode(initial_payload.encode("ascii"))
    stepped_packed = bytes(ef_py.step_exact_world_step_front_half_packed(initial_packed, bool(use_gpu)))
    stats = ef_py.last_exact_world_step_front_half_stats()

    runtime, refs, entity_ids = _spawn_runtime_from_trace(loaded)
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, stepped_packed)
    actual_record = _record_runtime_surface(runtime, refs, entity_ids, int(target_record["step_index"]))
    actual_record["stage_name"] = "GroundContact"
    actual_record["stage_order"] = int(target_record["stage_order"])
    actual_record["stage_domain"] = str(target_record["stage_domain"])
    actual_record["packed_exact_state_b64"] = _normalized_replay_blob_b64(stepped_packed)

    compare = _compare_records(
        _strip_runtime_clock_fields(target_record),
        _strip_runtime_clock_fields(actual_record),
        abs_tol=abs_tol,
        max_examples=max_examples,
    )
    expected_digests = _packed_component_digests(_decode_record_packed(target_record))
    actual_digests = _packed_component_digests(stepped_packed)

    return {
        "trace_kind": loaded.get("trace_kind"),
        "target_stage_name": "GroundContact",
        "world_count": int(loaded.get("world_count", 0)),
        "use_gpu_requested": bool(use_gpu),
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "apply_signatures_match": list(target_record["apply_signatures"]) == list(actual_record["apply_signatures"]),
        "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
        "differing_components": _differing_components(expected_digests, actual_digests),
        "mismatch_count": int(compare["mismatch_count"]),
        "max_abs_diff": float(compare["max_abs_diff"]),
        "max_abs_diff_path": str(compare["max_abs_diff_path"]),
        "first_mismatches": list(compare["first_mismatches"]),
        "front_half_state_count": int(getattr(stats, "state_count", 0)),
        "front_half_command_lane_ms": float(getattr(stats, "command_lane_ms", 0.0)),
        "front_half_host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "front_half_kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "front_half_device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "front_half_cpu_post_command_ms": float(getattr(stats, "cpu_post_command_ms", 0.0)),
        "front_half_total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the Phase D front-half exact executor (`CommandLinkMovement` through `GroundContact`) "
            "and compare it against the archived GroundContact stage in a system trace."
        )
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON system-stage trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument(
        "--max-examples",
        type=int,
        default=8,
        help="Maximum number of mismatch examples to record.",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force the front-half replay to use the CPU reference path instead of the CUDA backend.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_front_half_slice(
        args.trace,
        use_gpu=not bool(args.cpu),
        abs_tol=float(args.abs_tol),
        max_examples=int(args.max_examples),
    )

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "trace_kind": report["trace_kind"],
                "target_stage_name": report["target_stage_name"],
                "use_gpu_requested": report["use_gpu_requested"],
                "used_cuda": report["used_cuda"],
                "apply_signatures_match": report["apply_signatures_match"],
                "packed_component_digests_match": report["packed_component_digests_match"],
                "mismatch_count": report["mismatch_count"],
                "max_abs_diff": report["max_abs_diff"],
                "max_abs_diff_path": report["max_abs_diff_path"],
                "front_half_total_ms": report["front_half_total_ms"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
