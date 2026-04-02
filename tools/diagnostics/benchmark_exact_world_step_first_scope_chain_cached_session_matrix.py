from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports  # noqa: E402

ensure_repo_imports()

from tools.diagnostics.benchmark_exact_world_step_first_scope_chain_cached_session import (  # noqa: E402
    benchmark_exact_world_step_first_scope_chain_cached_session,
)


def _parse_world_counts(value: str) -> list[int]:
    counts = [int(item.strip()) for item in str(value).split(",") if item.strip()]
    if not counts:
        raise ValueError("world-counts must contain at least one positive integer")
    if any(count <= 0 for count in counts):
        raise ValueError("world-counts must be positive")
    return counts


def run_cached_session_matrix(
    *,
    world_counts: list[int],
    steps: int = 8,
    use_gpu: bool = True,
    seed: int = 101,
    time_step_s: float = 0.05,
    write_back_every: int = 0,
    final_write_back: bool = True,
    use_runtime_step_batch_backend: bool = False,
    promotion_min_total_wall_speedup: float = 1.0,
    promotion_min_warm_runtime_step_speedup: float = 1.0,
    promotion_max_write_back_share_of_runtime_step: float = 0.25,
    promotion_max_write_back_vs_chain_ratio: float = 0.5,
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for world_count in world_counts:
        report = benchmark_exact_world_step_first_scope_chain_cached_session(
            steps=int(steps),
            use_gpu=bool(use_gpu),
            seed=int(seed),
            time_step_s=float(time_step_s),
            world_count=int(world_count),
            write_back_every=int(write_back_every),
            final_write_back=bool(final_write_back),
            use_runtime_step_batch_backend=bool(use_runtime_step_batch_backend),
            promotion_min_total_wall_speedup=float(promotion_min_total_wall_speedup),
            promotion_min_warm_runtime_step_speedup=float(promotion_min_warm_runtime_step_speedup),
            promotion_max_write_back_share_of_runtime_step=float(promotion_max_write_back_share_of_runtime_step),
            promotion_max_write_back_vs_chain_ratio=float(promotion_max_write_back_vs_chain_ratio),
        )
        runs.append(
            {
                "world_count": int(report["world_count"]),
                "cached_state_count": int(report["cached_state_count"]),
                "used_cuda": bool(report["used_cuda"]),
                "runtime_step_batch_backend_used": bool(report["runtime_step_batch_backend_used"]),
                "first_cpu_divergence_step": int(report["first_cpu_divergence_step"] or 0),
                "prime_extract_ms": float(report["prime_runtime_stats"]["prime_extract_ms"]),
                "test_first_runtime_step_total_ms": float(report["test_first_runtime_step_total_ms"]),
                "test_warm_runtime_step_total_ms": float(report["test_warm_runtime_step_total_ms"]),
                "test_warm_runtime_step_overhead_ms": float(report["test_warm_runtime_step_overhead_ms"]),
                "test_warm_chain_total_ms": float(report["test_warm_chain_total_ms"]),
                "test_warm_chain_host_to_device_ms": float(report["test_warm_chain_host_to_device_ms"]),
                "test_warm_chain_command_lane_ms": float(report["test_warm_chain_command_lane_ms"]),
                "test_warm_write_back_ms": float(report["test_warm_write_back_ms"]),
                "test_warm_chain_share_of_runtime_step": float(report["test_warm_chain_share_of_runtime_step"]),
                "test_warm_write_back_share_of_runtime_step": float(report["test_warm_write_back_share_of_runtime_step"]),
                "test_warm_runtime_step_overhead_share": float(report["test_warm_runtime_step_overhead_share"]),
                "test_warm_write_back_vs_chain_ratio": float(report["test_warm_write_back_vs_chain_ratio"]),
                "write_back_dominates_warm_chain": bool(report["write_back_dominates_warm_chain"]),
                "test_vs_cpu_total_wall_speedup": float(report["test_vs_cpu_total_wall_speedup"]),
                "test_vs_cpu_warm_step_wall_speedup": float(report["test_vs_cpu_warm_step_wall_speedup"]),
                "test_vs_cpu_warm_runtime_step_speedup": float(report["test_vs_cpu_warm_runtime_step_speedup"]),
                "promotion_ready": bool(report["promotion_ready"]),
                "promotion_blockers": list(report["promotion_blockers"]),
                "test_warm_runtime_step_total_ms_per_state": float(report["test_warm_runtime_step_total_ms_per_state"]),
                "test_warm_chain_total_ms_per_state": float(report["test_warm_chain_total_ms_per_state"]),
                "test_warm_chain_host_to_device_ms_per_state": float(report["test_warm_chain_host_to_device_ms_per_state"]),
                "test_warm_chain_command_lane_ms_per_state": float(report["test_warm_chain_command_lane_ms_per_state"]),
                "test_warm_write_back_ms_per_state": float(report["test_warm_write_back_ms_per_state"]),
                "test_warm_step_wall_ms": float(report["test_warm_step_wall_ms"]),
                "test_total_wall_ms": float(report["test_total_wall_ms"]),
                "final_cached_component_digests_match": bool(report["final_cached_component_digests_match"]),
                "final_live_component_digests_match": bool(report["final_live_component_digests_match"]),
            }
        )
    promotion_ready_world_counts = [
        int(item["world_count"])
        for item in runs
        if bool(item["promotion_ready"])
    ]
    promotion_blocked_world_counts = [
        int(item["world_count"])
        for item in runs
        if not bool(item["promotion_ready"])
    ]
    write_back_dominance_world_counts = [
        int(item["world_count"])
        for item in runs
        if bool(item["write_back_dominates_warm_chain"])
    ]
    return {
        "steps": int(steps),
        "seed": int(seed),
        "time_step_s": float(time_step_s),
        "use_gpu_requested": bool(use_gpu),
        "runtime_step_batch_backend_used": bool(use_runtime_step_batch_backend),
        "promotion_thresholds": {
            "min_total_wall_speedup": float(promotion_min_total_wall_speedup),
            "min_warm_runtime_step_speedup": float(promotion_min_warm_runtime_step_speedup),
            "max_write_back_share_of_runtime_step": float(promotion_max_write_back_share_of_runtime_step),
            "max_write_back_vs_chain_ratio": float(promotion_max_write_back_vs_chain_ratio),
        },
        "write_back_every": int(write_back_every),
        "final_write_back": bool(final_write_back),
        "world_counts": [int(value) for value in world_counts],
        "promotion_ready_world_counts": list(promotion_ready_world_counts),
        "promotion_blocked_world_counts": list(promotion_blocked_world_counts),
        "first_promotion_ready_world_count": int(
            promotion_ready_world_counts[0] if promotion_ready_world_counts else 0
        ),
        "first_promotion_blocked_world_count": int(
            promotion_blocked_world_counts[0] if promotion_blocked_world_counts else 0
        ),
        "write_back_dominance_world_counts": list(write_back_dominance_world_counts),
        "first_write_back_dominance_world_count": int(
            write_back_dominance_world_counts[0] if write_back_dominance_world_counts else 0
        ),
        "runs": runs,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a cached-session runtime/backend matrix across larger first-scope world batches "
            "and summarize the steady-state timing breakdown."
        )
    )
    parser.add_argument("--output", help="Optional path to write the JSON report.")
    parser.add_argument("--steps", type=int, default=8, help="Number of cached-session steps to run per batch.")
    parser.add_argument("--seed", type=int, default=101, help="Base world reset seed.")
    parser.add_argument("--time-step", type=float, default=0.05, help="Simulation time step in seconds.")
    parser.add_argument(
        "--world-counts",
        default="1,8,32",
        help="Comma-separated cached-session batch sizes to benchmark.",
    )
    parser.add_argument("--gpu", action="store_true", help="Run the matrix on the resident CUDA backend.")
    parser.add_argument(
        "--runtime-step-batch-backend",
        action="store_true",
        help="Run the matrix through the experimental step_batch exact backend switch instead of direct cached-session stepping.",
    )
    parser.add_argument(
        "--promotion-min-total-wall-speedup",
        type=float,
        default=1.0,
        help="Minimum CPU-vs-test total-wall speedup ratio required for the promotion gate.",
    )
    parser.add_argument(
        "--promotion-min-warm-runtime-step-speedup",
        type=float,
        default=1.0,
        help="Minimum CPU-vs-test warm runtime-step speedup ratio required for the promotion gate.",
    )
    parser.add_argument(
        "--promotion-max-write-back-share-of-runtime-step",
        type=float,
        default=0.25,
        help="Maximum warm write-back share of runtime-step cost allowed by the promotion gate.",
    )
    parser.add_argument(
        "--promotion-max-write-back-vs-chain-ratio",
        type=float,
        default=0.5,
        help="Maximum warm write-back-vs-chain ratio allowed by the promotion gate.",
    )
    parser.add_argument(
        "--write-back-every",
        type=int,
        default=0,
        help="Write the cached state back to the live world every N steps; 0 disables periodic write-back.",
    )
    parser.add_argument(
        "--no-final-write-back",
        action="store_true",
        help="Do not flush the cached session back to the live world after the final step.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = run_cached_session_matrix(
        world_counts=_parse_world_counts(args.world_counts),
        steps=int(args.steps),
        use_gpu=bool(args.gpu),
        seed=int(args.seed),
        time_step_s=float(args.time_step),
        write_back_every=int(args.write_back_every),
        final_write_back=not bool(args.no_final_write_back),
        use_runtime_step_batch_backend=bool(args.runtime_step_batch_backend),
        promotion_min_total_wall_speedup=float(args.promotion_min_total_wall_speedup),
        promotion_min_warm_runtime_step_speedup=float(args.promotion_min_warm_runtime_step_speedup),
        promotion_max_write_back_share_of_runtime_step=float(args.promotion_max_write_back_share_of_runtime_step),
        promotion_max_write_back_vs_chain_ratio=float(args.promotion_max_write_back_vs_chain_ratio),
    )

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "steps": report["steps"],
                "world_counts": report["world_counts"],
                "use_gpu_requested": report["use_gpu_requested"],
                "runtime_step_batch_backend_used": report["runtime_step_batch_backend_used"],
                "promotion_thresholds": report["promotion_thresholds"],
                "promotion_ready_world_counts": report["promotion_ready_world_counts"],
                "promotion_blocked_world_counts": report["promotion_blocked_world_counts"],
                "first_promotion_ready_world_count": report["first_promotion_ready_world_count"],
                "first_promotion_blocked_world_count": report["first_promotion_blocked_world_count"],
                "write_back_dominance_world_counts": report["write_back_dominance_world_counts"],
                "first_write_back_dominance_world_count": report["first_write_back_dominance_world_count"],
                "runs": report["runs"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
