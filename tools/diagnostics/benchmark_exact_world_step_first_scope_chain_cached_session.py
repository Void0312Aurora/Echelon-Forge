from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / float(len(values)))


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(float(denominator)) <= 1e-12:
        return 0.0
    return float(float(numerator) / float(denominator))


def _promotion_thresholds_dict(
    *,
    min_total_wall_speedup: float,
    min_warm_runtime_step_speedup: float,
    max_write_back_share_of_runtime_step: float,
    max_write_back_vs_chain_ratio: float,
) -> dict[str, float]:
    return {
        "min_total_wall_speedup": float(min_total_wall_speedup),
        "min_warm_runtime_step_speedup": float(min_warm_runtime_step_speedup),
        "max_write_back_share_of_runtime_step": float(max_write_back_share_of_runtime_step),
        "max_write_back_vs_chain_ratio": float(max_write_back_vs_chain_ratio),
    }


def _runtime_cached_session_stats_dict(stats: Any) -> dict[str, Any]:
    return {
        "state_count": int(getattr(stats, "state_count", 0)),
        "used_gpu": bool(getattr(stats, "used_gpu", False)),
        "prime_extract_ms": float(getattr(stats, "prime_extract_ms", 0.0)),
        "pilot_update_ms": float(getattr(stats, "pilot_update_ms", 0.0)),
        "mission_update_ms": float(getattr(stats, "mission_update_ms", 0.0)),
        "step_total_ms": float(getattr(stats, "step_total_ms", 0.0)),
        "write_back_ms": float(getattr(stats, "write_back_ms", 0.0)),
        "chain_command_lane_ms": float(getattr(stats, "chain_command_lane_ms", 0.0)),
        "chain_host_to_device_ms": float(getattr(stats, "chain_host_to_device_ms", 0.0)),
        "chain_front_kernel_ms": float(getattr(stats, "chain_front_kernel_ms", 0.0)),
        "chain_guidance_kernel_ms": float(getattr(stats, "chain_guidance_kernel_ms", 0.0)),
        "chain_tail_kernel_ms": float(getattr(stats, "chain_tail_kernel_ms", 0.0)),
        "chain_kernel_ms": float(getattr(stats, "chain_kernel_ms", 0.0)),
        "chain_device_to_host_ms": float(getattr(stats, "chain_device_to_host_ms", 0.0)),
        "chain_cpu_fallback_ms": float(getattr(stats, "chain_cpu_fallback_ms", 0.0)),
        "chain_total_ms": float(getattr(stats, "chain_total_ms", 0.0)),
    }


def _exact_step_backend_enum(*, use_gpu: bool) -> Any:
    return (
        ef_py.WorldBatchExactStepBackend.ExactFirstScopeChainCachedGpu
        if bool(use_gpu)
        else ef_py.WorldBatchExactStepBackend.ExactFirstScopeChainCachedCpu
    )


def _make_runtime(*, seed: int, time_step_s: float, world_count: int) -> tuple[Any, list[Any]]:
    runtime = ef_py.WorldBatchRuntime(int(world_count))
    db_path = resolve_repo_path("examples", "config", "database")
    if not runtime.load_database(db_path):
        raise RuntimeError(f"failed to load database from {db_path}")
    runtime.reset_batch([int(seed + world_index) for world_index in range(int(world_count))])
    runtime.set_time_step(float(time_step_s))
    refs: list[Any] = []
    for world_index in range(int(world_count)):
        world = runtime.world(world_index)
        offset = float(world_index)
        entity_id = int(world.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            -400.0 - 120.0 * offset,
            150.0 + 30.0 * offset,
            1400.0 + 5.0 * float(world_index % 5),
            90.0 + 3.0 * float(world_index % 7),
            0.0,
            0.0,
            190.0 + 1.5 * float(world_index % 11),
            0.0,
            0.0,
        ))
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(world_index)
        ref.entity_id = int(entity_id)
        refs.append(ref)
    return runtime, refs


def _step_action(step_index: int, entity_slot: int = 0) -> tuple[float, float, float, float]:
    table = (
        (0.35, 0.10, 0.00, 0.85),
        (-0.20, 0.12, 0.05, 0.65),
        (0.10, -0.15, -0.03, 0.75),
        (-0.30, 0.08, 0.02, 0.70),
    )
    stick_roll, stick_pitch, rudder, throttle = table[int(step_index + entity_slot) % len(table)]
    offset = float(entity_slot % 5) * 0.01
    stick_roll = max(-1.0, min(1.0, stick_roll + offset))
    stick_pitch = max(-1.0, min(1.0, stick_pitch - 0.5 * offset))
    rudder = max(-1.0, min(1.0, rudder + 0.25 * offset))
    throttle = max(0.0, min(1.0, throttle - 0.05 * offset))
    return float(stick_roll), float(stick_pitch), float(rudder), float(throttle)


def _make_pilot_assignment(ref: Any, step_index: int, entity_slot: int) -> Any:
    stick_roll, stick_pitch, rudder, throttle = _step_action(step_index, entity_slot)
    assignment = ef_py.WorldPilotActionAssignment()
    assignment.world_index = int(ref.world_index)
    assignment.entity_id = int(ref.entity_id)
    assignment.action.stick_roll = float(stick_roll)
    assignment.action.stick_pitch = float(stick_pitch)
    assignment.action.rudder = float(rudder)
    assignment.action.throttle = float(throttle)
    assignment.action.active = True
    return assignment


def _make_pilot_assignments(refs: list[Any], step_index: int) -> list[Any]:
    return [
        _make_pilot_assignment(ref, step_index, entity_slot)
        for entity_slot, ref in enumerate(refs)
    ]


def _packed_apply_signatures(packed: bytes) -> list[int]:
    return [int(value) for value in ef_py.exact_world_step_states_v1_apply_signatures_packed(packed)]


def _packed_component_digests(packed: bytes) -> list[dict[str, Any]]:
    return [dict(item) for item in ef_py.exact_world_step_state_v1_component_digests_packed(packed)]


def _should_write_back(step_index: int, steps: int, write_back_every: int, final_write_back: bool) -> bool:
    should = bool(write_back_every > 0 and ((step_index + 1) % write_back_every == 0))
    if final_write_back and step_index == (steps - 1):
        should = True
    return should


def benchmark_exact_world_step_first_scope_chain_cached_session(
    *,
    steps: int = 8,
    use_gpu: bool = True,
    seed: int = 101,
    time_step_s: float = 0.05,
    world_count: int = 1,
    write_back_every: int = 0,
    final_write_back: bool = True,
    use_runtime_step_batch_backend: bool = False,
    promotion_min_total_wall_speedup: float = 1.0,
    promotion_min_warm_runtime_step_speedup: float = 1.0,
    promotion_max_write_back_share_of_runtime_step: float = 0.25,
    promotion_max_write_back_vs_chain_ratio: float = 0.5,
) -> dict[str, Any]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if world_count <= 0:
        raise ValueError("world_count must be positive")
    if write_back_every < 0:
        raise ValueError("write_back_every must be non-negative")
    if promotion_min_total_wall_speedup <= 0.0:
        raise ValueError("promotion_min_total_wall_speedup must be positive")
    if promotion_min_warm_runtime_step_speedup <= 0.0:
        raise ValueError("promotion_min_warm_runtime_step_speedup must be positive")
    if promotion_max_write_back_share_of_runtime_step < 0.0:
        raise ValueError("promotion_max_write_back_share_of_runtime_step must be non-negative")
    if promotion_max_write_back_vs_chain_ratio < 0.0:
        raise ValueError("promotion_max_write_back_vs_chain_ratio must be non-negative")
    if use_runtime_step_batch_backend and (write_back_every not in (0, 1) or not final_write_back):
        raise ValueError(
            "runtime_step_batch_backend mode currently writes back every step; "
            "use write_back_every=1 (or 0) with final_write_back=True"
        )

    info = ef_py.probe_gpu_device()
    if use_gpu and not bool(info.cuda_runtime_available):
        raise RuntimeError("CUDA runtime is not available")

    runtime_test, refs_test = _make_runtime(seed=seed, time_step_s=time_step_s, world_count=world_count)
    runtime_cpu, refs_cpu = _make_runtime(seed=seed, time_step_s=time_step_s, world_count=world_count)

    prime_t0 = time.perf_counter()
    runtime_test.prime_exact_world_step_first_scope_chain_cached_session(refs_test)
    if use_runtime_step_batch_backend:
        runtime_test.set_exact_world_step_backend(_exact_step_backend_enum(use_gpu=bool(use_gpu)))
    prime_wall_ms = (time.perf_counter() - prime_t0) * 1000.0
    prime_runtime_stats = _runtime_cached_session_stats_dict(
        runtime_test.last_exact_world_step_first_scope_chain_cached_session_stats()
    )

    cpu_prime_t0 = time.perf_counter()
    runtime_cpu.prime_exact_world_step_first_scope_chain_cached_session(refs_cpu)
    if use_runtime_step_batch_backend:
        runtime_cpu.set_exact_world_step_backend(_exact_step_backend_enum(use_gpu=False))
    cpu_prime_wall_ms = (time.perf_counter() - cpu_prime_t0) * 1000.0
    cpu_prime_runtime_stats = _runtime_cached_session_stats_dict(
        runtime_cpu.last_exact_world_step_first_scope_chain_cached_session_stats()
    )

    step_reports: list[dict[str, Any]] = []
    write_back_steps: list[int] = []
    final_live_synced = False
    last_gpu_stats: dict[str, Any] = {
        "used_cuda": False,
        "missile_count": 0,
        "host_to_device_ms": 0.0,
        "kernel_ms": 0.0,
        "device_to_host_ms": 0.0,
        "total_ms": 0.0,
        "state_count": 0,
    }

    for step_index in range(steps):
        assignments_test = _make_pilot_assignments(refs_test, step_index)
        assignments_cpu = _make_pilot_assignments(refs_cpu, step_index)
        if use_runtime_step_batch_backend:
            runtime_test.set_pilot_actions_batch(assignments_test)
            runtime_cpu.set_pilot_actions_batch(assignments_cpu)
        else:
            runtime_test.set_pilot_actions_exact_world_step_first_scope_chain_cached_session(assignments_test)
            runtime_cpu.set_pilot_actions_exact_world_step_first_scope_chain_cached_session(assignments_cpu)
        test_update_stats = _runtime_cached_session_stats_dict(
            runtime_test.last_exact_world_step_first_scope_chain_cached_session_stats()
        )
        cpu_update_stats = _runtime_cached_session_stats_dict(
            runtime_cpu.last_exact_world_step_first_scope_chain_cached_session_stats()
        )

        do_write_back = (
            True
            if use_runtime_step_batch_backend
            else _should_write_back(step_index, steps, write_back_every, final_write_back)
        )
        if do_write_back:
            write_back_steps.append(int(step_index + 1))
            if step_index == (steps - 1):
                final_live_synced = True

        step_t0 = time.perf_counter()
        if use_runtime_step_batch_backend:
            runtime_test.step_batch()
            test_packed = bytes(runtime_test.extract_exact_world_step_first_scope_chain_cached_session_packed())
        else:
            test_packed = bytes(
                runtime_test.step_exact_world_step_first_scope_chain_cached_session_packed(
                    bool(use_gpu),
                    bool(do_write_back),
                )
            )
        test_step_wall_ms = (time.perf_counter() - step_t0) * 1000.0

        stats = ef_py.last_exact_world_step_first_scope_chain_cuda_stats()
        last_gpu_stats = {
            "used_cuda": bool(getattr(stats, "used_cuda", False)),
            "missile_count": int(getattr(stats, "missile_count", 0)),
            "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
            "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
            "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
            "total_ms": float(getattr(stats, "total_ms", 0.0)),
            "state_count": int(getattr(stats, "state_count", 0)),
        }
        test_runtime_step_stats = _runtime_cached_session_stats_dict(
            runtime_test.last_exact_world_step_first_scope_chain_cached_session_stats()
        )

        cpu_step_t0 = time.perf_counter()
        if use_runtime_step_batch_backend:
            runtime_cpu.step_batch()
            cpu_packed = bytes(runtime_cpu.extract_exact_world_step_first_scope_chain_cached_session_packed())
        else:
            cpu_packed = bytes(
                runtime_cpu.step_exact_world_step_first_scope_chain_cached_session_packed(
                    False,
                    bool(do_write_back),
                )
            )
        cpu_step_wall_ms = (time.perf_counter() - cpu_step_t0) * 1000.0
        cpu_runtime_step_stats = _runtime_cached_session_stats_dict(
            runtime_cpu.last_exact_world_step_first_scope_chain_cached_session_stats()
        )

        step_reports.append(
            {
                "step_index": int(step_index + 1),
                "write_back": bool(do_write_back),
                "test_step_wall_ms": float(test_step_wall_ms),
                "cpu_step_wall_ms": float(cpu_step_wall_ms),
                "apply_signatures_match": _packed_apply_signatures(test_packed) == _packed_apply_signatures(cpu_packed),
                "component_digests_match": _packed_component_digests(test_packed) == _packed_component_digests(cpu_packed),
                "test_update_runtime_stats": dict(test_update_stats),
                "cpu_update_runtime_stats": dict(cpu_update_stats),
                "test_runtime_step_stats": dict(test_runtime_step_stats),
                "cpu_runtime_step_stats": dict(cpu_runtime_step_stats),
                "test_runtime_step_overhead_ms": float(
                    max(
                        0.0,
                        test_runtime_step_stats["step_total_ms"] -
                        test_runtime_step_stats["chain_total_ms"] -
                        test_runtime_step_stats["write_back_ms"],
                    )
                ),
                "cpu_runtime_step_overhead_ms": float(
                    max(
                        0.0,
                        cpu_runtime_step_stats["step_total_ms"] -
                        cpu_runtime_step_stats["chain_total_ms"] -
                        cpu_runtime_step_stats["write_back_ms"],
                    )
                ),
                "cuda_step_stats": dict(last_gpu_stats),
            }
        )

    flush_wall_ms = 0.0
    cpu_flush_wall_ms = 0.0
    if final_write_back and not final_live_synced:
        flush_t0 = time.perf_counter()
        runtime_test.apply_exact_world_step_first_scope_chain_cached_session_to_world()
        flush_wall_ms = (time.perf_counter() - flush_t0) * 1000.0

        cpu_flush_t0 = time.perf_counter()
        runtime_cpu.apply_exact_world_step_first_scope_chain_cached_session_to_world()
        cpu_flush_wall_ms = (time.perf_counter() - cpu_flush_t0) * 1000.0

        write_back_steps.append(int(steps))
        final_live_synced = True

    final_test_packed = bytes(runtime_test.extract_exact_world_step_first_scope_chain_cached_session_packed())
    final_cpu_packed = bytes(runtime_cpu.extract_exact_world_step_first_scope_chain_cached_session_packed())

    live_test_packed = b""
    live_cpu_packed = b""
    if final_live_synced:
        live_test_packed = bytes(runtime_test.extract_exact_world_step_states_v1_batch_packed(refs_test))
        live_cpu_packed = bytes(runtime_cpu.extract_exact_world_step_states_v1_batch_packed(refs_cpu))

    test_step_walls = [float(item["test_step_wall_ms"]) for item in step_reports]
    cpu_step_walls = [float(item["cpu_step_wall_ms"]) for item in step_reports]
    write_back_test_walls = [
        float(item["test_step_wall_ms"]) for item in step_reports if bool(item["write_back"])
    ]
    no_write_back_test_walls = [
        float(item["test_step_wall_ms"]) for item in step_reports if not bool(item["write_back"])
    ]
    warm_write_back_test_walls = [
        float(item["test_step_wall_ms"])
        for item in step_reports
        if bool(item["write_back"]) and int(item["step_index"]) > 1
    ]
    warm_no_write_back_test_walls = [
        float(item["test_step_wall_ms"])
        for item in step_reports
        if (not bool(item["write_back"])) and int(item["step_index"]) > 1
    ]
    test_runtime_step_totals = [float(item["test_runtime_step_stats"]["step_total_ms"]) for item in step_reports]
    test_runtime_overheads = [float(item["test_runtime_step_overhead_ms"]) for item in step_reports]
    test_runtime_chain_totals = [float(item["test_runtime_step_stats"]["chain_total_ms"]) for item in step_reports]
    test_runtime_chain_uploads = [float(item["test_runtime_step_stats"]["chain_host_to_device_ms"]) for item in step_reports]
    test_runtime_chain_commands = [float(item["test_runtime_step_stats"]["chain_command_lane_ms"]) for item in step_reports]
    test_runtime_write_backs = [float(item["test_runtime_step_stats"]["write_back_ms"]) for item in step_reports]
    cpu_runtime_step_totals = [float(item["cpu_runtime_step_stats"]["step_total_ms"]) for item in step_reports]
    warm_runtime_overheads = [
        float(item["test_runtime_step_overhead_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_runtime_totals = [
        float(item["test_runtime_step_stats"]["step_total_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_runtime_chain_totals = [
        float(item["test_runtime_step_stats"]["chain_total_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_runtime_chain_uploads = [
        float(item["test_runtime_step_stats"]["chain_host_to_device_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_runtime_chain_commands = [
        float(item["test_runtime_step_stats"]["chain_command_lane_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_runtime_write_backs = [
        float(item["test_runtime_step_stats"]["write_back_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    warm_cpu_runtime_totals = [
        float(item["cpu_runtime_step_stats"]["step_total_ms"])
        for item in step_reports
        if int(item["step_index"]) > 1
    ]
    test_warm_runtime_step_total_ms = float(_mean(warm_runtime_totals))
    test_warm_runtime_step_overhead_ms = float(_mean(warm_runtime_overheads))
    test_warm_chain_total_ms = float(_mean(warm_runtime_chain_totals))
    test_warm_chain_host_to_device_ms = float(_mean(warm_runtime_chain_uploads))
    test_warm_chain_command_lane_ms = float(_mean(warm_runtime_chain_commands))
    test_warm_write_back_ms = float(_mean(warm_runtime_write_backs))
    cpu_warm_runtime_step_total_ms = float(_mean(warm_cpu_runtime_totals))
    test_warm_runtime_step_total_ms_per_state = float(
        test_warm_runtime_step_total_ms / float(max(len(refs_test), 1))
    )
    test_warm_chain_total_ms_per_state = float(
        test_warm_chain_total_ms / float(max(len(refs_test), 1))
    )
    test_warm_chain_host_to_device_ms_per_state = float(
        test_warm_chain_host_to_device_ms / float(max(len(refs_test), 1))
    )
    test_warm_chain_command_lane_ms_per_state = float(
        test_warm_chain_command_lane_ms / float(max(len(refs_test), 1))
    )
    test_warm_write_back_ms_per_state = float(
        test_warm_write_back_ms / float(max(len(refs_test), 1))
    )
    test_warm_chain_share_of_runtime_step = float(
        _safe_ratio(test_warm_chain_total_ms, test_warm_runtime_step_total_ms)
    )
    test_warm_write_back_share_of_runtime_step = float(
        _safe_ratio(test_warm_write_back_ms, test_warm_runtime_step_total_ms)
    )
    test_warm_runtime_step_overhead_share = float(
        _safe_ratio(test_warm_runtime_step_overhead_ms, test_warm_runtime_step_total_ms)
    )
    test_warm_write_back_vs_chain_ratio = float(
        _safe_ratio(test_warm_write_back_ms, test_warm_chain_total_ms)
    )
    write_back_dominates_warm_chain = bool(test_warm_write_back_ms > test_warm_chain_total_ms)
    test_total_wall_ms = float(prime_wall_ms + sum(test_step_walls) + flush_wall_ms)
    cpu_total_wall_ms = float(cpu_prime_wall_ms + sum(cpu_step_walls) + cpu_flush_wall_ms)
    test_vs_cpu_total_wall_speedup = float(_safe_ratio(cpu_total_wall_ms, test_total_wall_ms))
    test_vs_cpu_warm_step_wall_speedup = float(_safe_ratio(float(_mean(cpu_step_walls[1:])), float(_mean(test_step_walls[1:]))))
    test_vs_cpu_warm_runtime_step_speedup = float(
        _safe_ratio(cpu_warm_runtime_step_total_ms, test_warm_runtime_step_total_ms)
    )
    first_cpu_divergence_step = next(
        (
            int(item["step_index"])
            for item in step_reports
            if (not bool(item["apply_signatures_match"])) or (not bool(item["component_digests_match"]))
        ),
        None,
    )
    final_cached_apply_signatures_match = (
        _packed_apply_signatures(final_test_packed) == _packed_apply_signatures(final_cpu_packed)
    )
    final_cached_component_digests_match = (
        _packed_component_digests(final_test_packed) == _packed_component_digests(final_cpu_packed)
    )
    final_live_apply_signatures_match = (
        _packed_apply_signatures(live_test_packed) == _packed_apply_signatures(final_test_packed)
        if final_live_synced else None
    )
    final_live_component_digests_match = (
        _packed_component_digests(live_test_packed) == _packed_component_digests(final_test_packed)
        if final_live_synced else None
    )
    cpu_live_apply_signatures_match = (
        _packed_apply_signatures(live_cpu_packed) == _packed_apply_signatures(final_cpu_packed)
        if final_live_synced else None
    )
    cpu_live_component_digests_match = (
        _packed_component_digests(live_cpu_packed) == _packed_component_digests(final_cpu_packed)
        if final_live_synced else None
    )
    promotion_thresholds = _promotion_thresholds_dict(
        min_total_wall_speedup=float(promotion_min_total_wall_speedup),
        min_warm_runtime_step_speedup=float(promotion_min_warm_runtime_step_speedup),
        max_write_back_share_of_runtime_step=float(promotion_max_write_back_share_of_runtime_step),
        max_write_back_vs_chain_ratio=float(promotion_max_write_back_vs_chain_ratio),
    )
    promotion_gate_evaluated = bool(use_runtime_step_batch_backend)
    promotion_parity_ready = bool(
        int(first_cpu_divergence_step or 0) == 0
        and bool(final_cached_apply_signatures_match)
        and bool(final_cached_component_digests_match)
        and (final_live_apply_signatures_match is True)
        and (final_live_component_digests_match is True)
    )
    promotion_total_wall_speedup_ready = bool(
        test_vs_cpu_total_wall_speedup >= float(promotion_min_total_wall_speedup)
    )
    promotion_warm_runtime_step_speedup_ready = bool(
        test_vs_cpu_warm_runtime_step_speedup >= float(promotion_min_warm_runtime_step_speedup)
    )
    promotion_write_back_share_ready = bool(
        test_warm_write_back_share_of_runtime_step <= float(promotion_max_write_back_share_of_runtime_step)
    )
    promotion_write_back_vs_chain_ready = bool(
        test_warm_write_back_vs_chain_ratio <= float(promotion_max_write_back_vs_chain_ratio)
    )
    promotion_write_back_ready = bool(
        promotion_write_back_share_ready
        and promotion_write_back_vs_chain_ready
        and (not bool(write_back_dominates_warm_chain))
    )
    promotion_ready = bool(
        promotion_gate_evaluated
        and bool(last_gpu_stats["used_cuda"])
        and promotion_parity_ready
        and promotion_total_wall_speedup_ready
        and promotion_warm_runtime_step_speedup_ready
        and promotion_write_back_ready
    )
    promotion_blockers: list[str] = []
    if not promotion_gate_evaluated:
        promotion_blockers.append("runtime_step_batch_backend_not_used")
    if not bool(last_gpu_stats["used_cuda"]):
        promotion_blockers.append("cuda_not_used")
    if not promotion_parity_ready:
        promotion_blockers.append("parity")
    if not promotion_total_wall_speedup_ready:
        promotion_blockers.append("total_wall_speedup")
    if not promotion_warm_runtime_step_speedup_ready:
        promotion_blockers.append("warm_runtime_step_speedup")
    if not promotion_write_back_share_ready:
        promotion_blockers.append("write_back_share")
    if not promotion_write_back_vs_chain_ready:
        promotion_blockers.append("write_back_vs_chain_ratio")
    if bool(write_back_dominates_warm_chain):
        promotion_blockers.append("write_back_dominates_chain")

    return {
        "steps": int(steps),
        "seed": int(seed),
        "time_step_s": float(time_step_s),
        "world_count": int(world_count),
        "cached_state_count": int(len(refs_test)),
        "use_gpu_requested": bool(use_gpu),
        "used_cuda": bool(last_gpu_stats["used_cuda"]),
        "runtime_step_batch_backend_used": bool(use_runtime_step_batch_backend),
        "write_back_every": int(write_back_every),
        "final_write_back": bool(final_write_back),
        "write_back_steps": list(write_back_steps),
        "final_live_synced": bool(final_live_synced),
        "prime_wall_ms": float(prime_wall_ms),
        "cpu_prime_wall_ms": float(cpu_prime_wall_ms),
        "prime_runtime_stats": dict(prime_runtime_stats),
        "cpu_prime_runtime_stats": dict(cpu_prime_runtime_stats),
        "flush_wall_ms": float(flush_wall_ms),
        "cpu_flush_wall_ms": float(cpu_flush_wall_ms),
        "step_reports": step_reports,
        "test_step_wall_ms": test_step_walls,
        "cpu_step_wall_ms": cpu_step_walls,
        "test_runtime_step_total_ms": test_runtime_step_totals,
        "test_runtime_step_overhead_ms": test_runtime_overheads,
        "test_runtime_chain_total_ms": test_runtime_chain_totals,
        "test_runtime_chain_host_to_device_ms": test_runtime_chain_uploads,
        "test_runtime_chain_command_lane_ms": test_runtime_chain_commands,
        "test_runtime_write_back_ms": test_runtime_write_backs,
        "test_first_step_wall_ms": float(test_step_walls[0]),
        "cpu_first_step_wall_ms": float(cpu_step_walls[0]),
        "test_warm_step_wall_ms": float(_mean(test_step_walls[1:])),
        "cpu_warm_step_wall_ms": float(_mean(cpu_step_walls[1:])),
        "test_first_runtime_step_total_ms": float(test_runtime_step_totals[0]),
        "cpu_first_runtime_step_total_ms": float(cpu_runtime_step_totals[0]),
        "test_warm_runtime_step_total_ms": float(test_warm_runtime_step_total_ms),
        "cpu_warm_runtime_step_total_ms": float(cpu_warm_runtime_step_total_ms),
        "test_warm_runtime_step_overhead_ms": float(test_warm_runtime_step_overhead_ms),
        "test_warm_chain_total_ms": float(test_warm_chain_total_ms),
        "test_warm_chain_host_to_device_ms": float(test_warm_chain_host_to_device_ms),
        "test_warm_chain_command_lane_ms": float(test_warm_chain_command_lane_ms),
        "test_warm_write_back_ms": float(test_warm_write_back_ms),
        "test_warm_runtime_step_total_ms_per_state": float(test_warm_runtime_step_total_ms_per_state),
        "test_warm_chain_total_ms_per_state": float(test_warm_chain_total_ms_per_state),
        "test_warm_chain_host_to_device_ms_per_state": float(test_warm_chain_host_to_device_ms_per_state),
        "test_warm_chain_command_lane_ms_per_state": float(test_warm_chain_command_lane_ms_per_state),
        "test_warm_write_back_ms_per_state": float(test_warm_write_back_ms_per_state),
        "test_warm_chain_share_of_runtime_step": float(test_warm_chain_share_of_runtime_step),
        "test_warm_write_back_share_of_runtime_step": float(test_warm_write_back_share_of_runtime_step),
        "test_warm_runtime_step_overhead_share": float(test_warm_runtime_step_overhead_share),
        "test_warm_write_back_vs_chain_ratio": float(test_warm_write_back_vs_chain_ratio),
        "write_back_dominates_warm_chain": bool(write_back_dominates_warm_chain),
        "test_write_back_step_wall_ms": float(_mean(write_back_test_walls)),
        "test_no_write_back_step_wall_ms": float(_mean(no_write_back_test_walls)),
        "test_warm_write_back_step_wall_ms": float(_mean(warm_write_back_test_walls)),
        "test_warm_no_write_back_step_wall_ms": float(_mean(warm_no_write_back_test_walls)),
        "test_total_wall_ms": float(test_total_wall_ms),
        "cpu_total_wall_ms": float(cpu_total_wall_ms),
        "test_vs_cpu_total_wall_speedup": float(test_vs_cpu_total_wall_speedup),
        "test_vs_cpu_warm_step_wall_speedup": float(test_vs_cpu_warm_step_wall_speedup),
        "test_vs_cpu_warm_runtime_step_speedup": float(test_vs_cpu_warm_runtime_step_speedup),
        "promotion_thresholds": dict(promotion_thresholds),
        "promotion_gate_evaluated": bool(promotion_gate_evaluated),
        "promotion_parity_ready": bool(promotion_parity_ready),
        "promotion_total_wall_speedup_ready": bool(promotion_total_wall_speedup_ready),
        "promotion_warm_runtime_step_speedup_ready": bool(promotion_warm_runtime_step_speedup_ready),
        "promotion_write_back_share_ready": bool(promotion_write_back_share_ready),
        "promotion_write_back_vs_chain_ready": bool(promotion_write_back_vs_chain_ready),
        "promotion_write_back_ready": bool(promotion_write_back_ready),
        "promotion_ready": bool(promotion_ready),
        "promotion_blockers": list(promotion_blockers),
        "first_cpu_divergence_step": int(first_cpu_divergence_step or 0),
        "final_cached_apply_signatures_match": bool(final_cached_apply_signatures_match),
        "final_cached_component_digests_match": bool(final_cached_component_digests_match),
        "final_live_apply_signatures_match": final_live_apply_signatures_match,
        "final_live_component_digests_match": final_live_component_digests_match,
        "cpu_live_apply_signatures_match": cpu_live_apply_signatures_match,
        "cpu_live_component_digests_match": cpu_live_component_digests_match,
        "last_cuda_step_stats": dict(last_gpu_stats),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the WorldBatchRuntime cached exact-state session across multiple first-scope steps, "
            "including pilot-action updates and configurable write-back cadence."
        )
    )
    parser.add_argument("--output", help="Optional path to write the JSON report.")
    parser.add_argument("--steps", type=int, default=8, help="Number of cached-session steps to run.")
    parser.add_argument("--seed", type=int, default=101, help="World reset seed.")
    parser.add_argument("--time-step", type=float, default=0.05, help="Simulation time step in seconds.")
    parser.add_argument("--world-count", type=int, default=1, help="Number of worlds / cached states in the batch.")
    parser.add_argument("--gpu", action="store_true", help="Run the test path on the resident CUDA backend.")
    parser.add_argument(
        "--runtime-step-batch-backend",
        action="store_true",
        help="Run both test/reference paths through the experimental step_batch backend switch instead of direct cached-session stepping.",
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
    report = benchmark_exact_world_step_first_scope_chain_cached_session(
        steps=int(args.steps),
        use_gpu=bool(args.gpu),
        seed=int(args.seed),
        time_step_s=float(args.time_step),
        world_count=int(args.world_count),
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
                "world_count": report["world_count"],
                "cached_state_count": report["cached_state_count"],
                "use_gpu_requested": report["use_gpu_requested"],
                "used_cuda": report["used_cuda"],
                "runtime_step_batch_backend_used": report["runtime_step_batch_backend_used"],
                "write_back_every": report["write_back_every"],
                "final_write_back": report["final_write_back"],
                "write_back_steps": report["write_back_steps"],
                "prime_wall_ms": report["prime_wall_ms"],
                "prime_extract_ms": report["prime_runtime_stats"]["prime_extract_ms"],
                "test_first_step_wall_ms": report["test_first_step_wall_ms"],
                "test_warm_step_wall_ms": report["test_warm_step_wall_ms"],
                "test_first_runtime_step_total_ms": report["test_first_runtime_step_total_ms"],
                "test_warm_runtime_step_total_ms": report["test_warm_runtime_step_total_ms"],
                "test_warm_runtime_step_overhead_ms": report["test_warm_runtime_step_overhead_ms"],
                "test_warm_chain_total_ms": report["test_warm_chain_total_ms"],
                "test_warm_chain_host_to_device_ms": report["test_warm_chain_host_to_device_ms"],
                "test_warm_chain_command_lane_ms": report["test_warm_chain_command_lane_ms"],
                "test_warm_write_back_ms": report["test_warm_write_back_ms"],
                "test_warm_chain_share_of_runtime_step": report["test_warm_chain_share_of_runtime_step"],
                "test_warm_write_back_share_of_runtime_step": report["test_warm_write_back_share_of_runtime_step"],
                "test_warm_runtime_step_overhead_share": report["test_warm_runtime_step_overhead_share"],
                "test_warm_write_back_vs_chain_ratio": report["test_warm_write_back_vs_chain_ratio"],
                "write_back_dominates_warm_chain": report["write_back_dominates_warm_chain"],
                "test_vs_cpu_total_wall_speedup": report["test_vs_cpu_total_wall_speedup"],
                "test_vs_cpu_warm_step_wall_speedup": report["test_vs_cpu_warm_step_wall_speedup"],
                "test_vs_cpu_warm_runtime_step_speedup": report["test_vs_cpu_warm_runtime_step_speedup"],
                "promotion_thresholds": report["promotion_thresholds"],
                "promotion_ready": report["promotion_ready"],
                "promotion_blockers": report["promotion_blockers"],
                "test_warm_runtime_step_total_ms_per_state": report["test_warm_runtime_step_total_ms_per_state"],
                "flush_wall_ms": report["flush_wall_ms"],
                "test_total_wall_ms": report["test_total_wall_ms"],
                "final_cached_component_digests_match": report["final_cached_component_digests_match"],
                "final_live_component_digests_match": report["final_live_component_digests_match"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
