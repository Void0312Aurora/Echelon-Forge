from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports
from tools.diagnostics.compare_exact_world_step_first_scope_chain import (
    _decode_initial_packed,
    _decode_record_packed,
)
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


def compare_exact_world_step_first_scope_chain_cuda(
    trace: str | Path | dict[str, Any],
    *,
    use_gpu: bool = False,
    resident: bool = False,
    runtime_resident: bool = False,
    runtime_cached_session: bool = False,
    abs_tol: float = 1e-6,
    max_examples: int = 8,
) -> dict[str, Any]:
    enabled_modes = sum(1 for flag in (resident, runtime_resident, runtime_cached_session) if flag)
    if enabled_modes > 1:
        raise ValueError("resident, runtime_resident, and runtime_cached_session modes are mutually exclusive")
    loaded = _load_trace(trace)
    if loaded.get("trace_kind") != "cpu_exact_first_scope_chain_trace_v1":
        raise ValueError(
            "compare_exact_world_step_first_scope_chain_cuda expects trace_kind=cpu_exact_first_scope_chain_trace_v1"
        )

    runtime, refs, entity_ids = spawn_runtime_from_guidance_trace(loaded)
    initial_packed = _decode_initial_packed(loaded)
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, initial_packed)
    resident_path_used = bool(resident and use_gpu)
    runtime_resident_path_used = bool(runtime_resident and use_gpu)
    runtime_cached_session_path_used = bool(runtime_cached_session)
    upload_wall_ms = 0.0
    replay_wall_ms = 0.0
    download_wall_ms = 0.0
    if runtime_cached_session_path_used:
        upload_t0 = time.perf_counter()
        runtime.prime_exact_world_step_first_scope_chain_cached_session(refs)
        upload_wall_ms = (time.perf_counter() - upload_t0) * 1000.0
        replay_t0 = time.perf_counter()
        stepped_packed = bytes(
            runtime.step_exact_world_step_first_scope_chain_cached_session_packed(
                bool(use_gpu),
                False,
            )
        )
        replay_wall_ms = (time.perf_counter() - replay_t0) * 1000.0
    elif runtime_resident_path_used:
        upload_t0 = time.perf_counter()
        upload_ok = bool(runtime.upload_exact_world_step_first_scope_chain_experiment_batch(refs))
        upload_wall_ms = (time.perf_counter() - upload_t0) * 1000.0
        if not upload_ok:
            raise RuntimeError("failed to upload runtime resident first-scope CUDA states")
        replay_t0 = time.perf_counter()
        replay_ok = bool(runtime.replay_exact_world_step_first_scope_chain_experiment_device_sequence())
        replay_wall_ms = (time.perf_counter() - replay_t0) * 1000.0
        if not replay_ok:
            raise RuntimeError("failed to replay runtime resident first-scope CUDA device sequence")
        download_t0 = time.perf_counter()
        stepped_packed = bytes(runtime.download_exact_world_step_first_scope_chain_experiment_batch_packed(False))
        download_wall_ms = (time.perf_counter() - download_t0) * 1000.0
    elif resident_path_used:
        upload_ok = bool(ef_py.upload_exact_world_step_first_scope_chain_cuda_states_packed(initial_packed))
        if not upload_ok:
            raise RuntimeError("failed to upload resident first-scope CUDA states")
        replay_ok = bool(ef_py.replay_exact_world_step_first_scope_chain_cuda_device_sequence())
        if not replay_ok:
            raise RuntimeError("failed to replay resident first-scope CUDA device sequence")
        stepped_packed = bytes(ef_py.download_exact_world_step_first_scope_chain_cuda_states_packed())
    else:
        stepped_packed = bytes(
            runtime.step_exact_world_step_first_scope_chain_experiment_batch_packed(
                refs,
                bool(use_gpu),
                False,
            )
        )
    expected_record = dict(loaded["final_record"])
    runtime.apply_exact_world_step_states_v1_batch_packed(refs, stepped_packed)
    actual_record = _record_guidance_step(runtime, refs, entity_ids, int(expected_record["step_index"]))
    actual_record["packed_exact_state_b64"] = _packed_b64(stepped_packed)

    compare = _compare_records(expected_record, actual_record, abs_tol=abs_tol, max_examples=max_examples)
    expected_digests = _packed_component_digests(_decode_record_packed(expected_record))
    actual_digests = _packed_component_digests(stepped_packed)
    chain_stats = ef_py.last_exact_world_step_first_scope_chain_cuda_stats()

    return {
        "trace_kind": loaded.get("trace_kind"),
        "target_stage_name": str(loaded.get("final_stage_name", "MassUpdate")),
        "use_gpu_requested": bool(use_gpu),
        "resident_path_used": resident_path_used,
        "runtime_resident_path_used": runtime_resident_path_used,
        "runtime_cached_session_path_used": runtime_cached_session_path_used,
        "used_cuda": bool(getattr(chain_stats, "used_cuda", False)),
        "apply_signatures_match": list(expected_record["apply_signatures"]) == list(actual_record["apply_signatures"]),
        "packed_component_digests_match": _component_digests_match(expected_digests, actual_digests),
        "differing_components": _differing_components(expected_digests, actual_digests),
        "mismatch_count": int(compare["mismatch_count"]),
        "max_abs_diff": float(compare["max_abs_diff"]),
        "max_abs_diff_path": str(compare["max_abs_diff_path"]),
        "first_mismatches": list(compare["first_mismatches"]),
        "first_scope_chain_state_count": int(getattr(chain_stats, "state_count", 0)),
        "first_scope_chain_missile_count": int(getattr(chain_stats, "missile_count", 0)),
        "first_scope_chain_command_lane_ms": float(getattr(chain_stats, "command_lane_ms", 0.0)),
        "first_scope_chain_host_to_device_ms": float(getattr(chain_stats, "host_to_device_ms", 0.0)),
        "first_scope_chain_front_kernel_ms": float(getattr(chain_stats, "front_kernel_ms", 0.0)),
        "first_scope_chain_guidance_kernel_ms": float(getattr(chain_stats, "guidance_kernel_ms", 0.0)),
        "first_scope_chain_tail_kernel_ms": float(getattr(chain_stats, "tail_kernel_ms", 0.0)),
        "first_scope_chain_kernel_ms": float(getattr(chain_stats, "kernel_ms", 0.0)),
        "first_scope_chain_device_to_host_ms": float(getattr(chain_stats, "device_to_host_ms", 0.0)),
        "first_scope_chain_cpu_fallback_ms": float(getattr(chain_stats, "cpu_fallback_ms", 0.0)),
        "first_scope_chain_total_ms": float(getattr(chain_stats, "total_ms", 0.0)),
        "first_scope_chain_output_device_ptr": int(
            getattr(ef_py, "last_exact_world_step_first_scope_chain_cuda_output_device_ptr")()
        ),
        "first_scope_chain_output_state_count": int(
            getattr(ef_py, "last_exact_world_step_first_scope_chain_cuda_output_state_count")()
        ),
        "runtime_resident_upload_wall_ms": upload_wall_ms,
        "runtime_resident_replay_wall_ms": replay_wall_ms,
        "runtime_resident_download_wall_ms": download_wall_ms,
        "runtime_resident_total_wall_ms": upload_wall_ms + replay_wall_ms + download_wall_ms,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the mixed first-scope exact chain against the archived final MassUpdate record, "
            "using either the CPU fallback or the resident CUDA backend."
        )
    )
    parser.add_argument("--trace", required=True, help="Path to the JSON first-scope chain trace artifact.")
    parser.add_argument("--output", help="Optional path to write the JSON comparison report.")
    parser.add_argument("--abs-tol", type=float, default=1e-6, help="Absolute tolerance for float comparisons.")
    parser.add_argument("--max-examples", type=int, default=8, help="Maximum number of mismatch examples.")
    parser.add_argument("--gpu", action="store_true", help="Run the resident CUDA backend.")
    parser.add_argument(
        "--resident",
        action="store_true",
        help="Use the explicit upload/replay/download resident CUDA carrier instead of the one-shot runtime helper.",
    )
    parser.add_argument(
        "--runtime-resident",
        action="store_true",
        help="Use the new WorldBatchRuntime-level upload/replay/download resident carrier.",
    )
    parser.add_argument(
        "--runtime-cached-session",
        action="store_true",
        help="Use the WorldBatchRuntime cached exact-state session that primes once and then steps without re-extracting from Flecs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = compare_exact_world_step_first_scope_chain_cuda(
        args.trace,
        use_gpu=bool(args.gpu),
        resident=bool(args.resident),
        runtime_resident=bool(args.runtime_resident),
        runtime_cached_session=bool(args.runtime_cached_session),
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
                "resident_path_used": report["resident_path_used"],
                "runtime_resident_path_used": report["runtime_resident_path_used"],
                "runtime_cached_session_path_used": report["runtime_cached_session_path_used"],
                "used_cuda": report["used_cuda"],
                "apply_signatures_match": report["apply_signatures_match"],
                "packed_component_digests_match": report["packed_component_digests_match"],
                "mismatch_count": report["mismatch_count"],
                "max_abs_diff": report["max_abs_diff"],
                "max_abs_diff_path": report["max_abs_diff_path"],
                "first_scope_chain_state_count": report["first_scope_chain_state_count"],
                "first_scope_chain_missile_count": report["first_scope_chain_missile_count"],
                "first_scope_chain_total_ms": report["first_scope_chain_total_ms"],
                "first_scope_chain_output_state_count": report["first_scope_chain_output_state_count"],
                "runtime_resident_total_wall_ms": report["runtime_resident_total_wall_ms"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
