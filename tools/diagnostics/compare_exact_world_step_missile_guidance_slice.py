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
from tools.diagnostics.compare_exact_world_step_shadow_trace import (
    _compare_records,
    _load_trace,
)
from tools.diagnostics.compare_exact_world_step_system_trace import (
    _component_digests_match,
    _differing_components,
    _packed_component_digests,
)
from tools.diagnostics.generate_exact_world_step_missile_guidance_trace import (
    _packed_b64,
    _record_guidance_step,
    spawn_runtime_from_guidance_trace,
)


ensure_repo_imports()

import ef_py  # noqa: E402


def _decode_initial_packed(trace: dict[str, Any]) -> bytes:
    payload = trace.get("initial_exact_state_packed_b64")
    if not isinstance(payload, str) or not payload:
        raise ValueError("trace is missing initial_exact_state_packed_b64")
    return base64.b64decode(payload.encode("ascii"))


def _decode_record_packed(record: dict[str, Any]) -> bytes:
    payload = record.get("packed_exact_state_b64")
    if not isinstance(payload, str) or not payload:
        raise ValueError("record is missing packed_exact_state_b64")
    return base64.b64decode(payload.encode("ascii"))


def compare_exact_world_step_missile_guidance_slice(
    trace: str | Path | dict[str, Any],
    *,
    use_gpu: bool = False,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_missile_guidance_trace_v1":
        raise ValueError(
            "compare_exact_world_step_missile_guidance_slice expects trace_kind=cpu_exact_missile_guidance_trace_v1"
        )

    initial_packed = _decode_initial_packed(loaded)
    stepped_packed = bytes(ef_py.step_exact_world_step_missile_guidance_cuda_packed(initial_packed, bool(use_gpu)))
    guidance_stats = ef_py.last_exact_world_step_missile_guidance_stats()
    guidance_cuda_stats = ef_py.last_exact_world_step_missile_guidance_cuda_stats()

    runtime, refs, entity_ids = spawn_runtime_from_guidance_trace(loaded)
    expected_record = dict(loaded["guidance_record"])
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, stepped_packed)
    actual_record = _record_guidance_step(runtime, refs, entity_ids, int(expected_record["step_index"]))
    actual_record["packed_exact_state_b64"] = _packed_b64(stepped_packed)

    compare = _compare_records(expected_record, actual_record, abs_tol=abs_tol, max_examples=max_examples)
    expected_digests = _packed_component_digests(_decode_record_packed(expected_record))
    actual_digests = _packed_component_digests(stepped_packed)

    return {
        "trace_kind": loaded.get("trace_kind"),
        "target_stage_name": "MissileGuidance",
        "use_gpu_requested": bool(use_gpu),
        "used_cuda": bool(getattr(guidance_cuda_stats, "used_cuda", False)),
        "apply_signatures_match": list(expected_record["apply_signatures"]) == list(actual_record["apply_signatures"]),
        "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
        "differing_components": _differing_components(expected_digests, actual_digests),
        "mismatch_count": int(compare["mismatch_count"]),
        "max_abs_diff": float(compare["max_abs_diff"]),
        "max_abs_diff_path": str(compare["max_abs_diff_path"]),
        "first_mismatches": list(compare["first_mismatches"]),
        "missile_guidance_state_count": int(getattr(guidance_stats, "state_count", 0)),
        "missile_guidance_missile_count": int(getattr(guidance_stats, "missile_count", 0)),
        "missile_guidance_total_ms": float(getattr(guidance_stats, "total_ms", 0.0)),
        "missile_guidance_cuda_state_count": int(getattr(guidance_cuda_stats, "state_count", 0)),
        "missile_guidance_cuda_missile_count": int(getattr(guidance_cuda_stats, "missile_count", 0)),
        "missile_guidance_cuda_host_to_device_ms": float(getattr(guidance_cuda_stats, "host_to_device_ms", 0.0)),
        "missile_guidance_cuda_kernel_ms": float(getattr(guidance_cuda_stats, "kernel_ms", 0.0)),
        "missile_guidance_cuda_device_to_host_ms": float(getattr(guidance_cuda_stats, "device_to_host_ms", 0.0)),
        "missile_guidance_cuda_cpu_fallback_ms": float(getattr(guidance_cuda_stats, "cpu_fallback_ms", 0.0)),
        "missile_guidance_cuda_total_ms": float(getattr(guidance_cuda_stats, "total_ms", 0.0)),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the exact CPU missile-guidance slice from packed exact state and compare it against "
            "the archived MissileGuidance stage record."
        )
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON missile-guidance trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument("--max-examples", type=int, default=8, help="Maximum number of mismatch examples.")
    parser.add_argument("--gpu", action="store_true", help="Run the CUDA backend instead of the CPU reference wrapper.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_missile_guidance_slice(
        args.trace,
        use_gpu=bool(args.gpu),
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
                "missile_guidance_cuda_state_count": report["missile_guidance_cuda_state_count"],
                "missile_guidance_cuda_missile_count": report["missile_guidance_cuda_missile_count"],
                "missile_guidance_cuda_total_ms": report["missile_guidance_cuda_total_ms"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
